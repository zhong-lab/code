import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget

from lantz import Q_
from lantz.drivers.newport import FSM300, XPSQ8
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CountEdgesChannel, CounterInputTask
from lantz.drivers.ni.daqmx import VoltageInputChannel, AnalogInputTask

def gaussian(xs, a=1, x=0, width=1, b=0):
    return a * np.exp(-np.square((xs - x) / width ** 2)) + b

class XPSFeedbackSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'xps': XPSQ8,
    }

    @Task(name='XPS Feedback')
    def feedback(self):
        self.dataset.clear()
        feedback_params = self.feedback_parameters.widget.get()
        init_x = feedback_params['x initial'].to('um').m
        init_y = feedback_params['y initial'].to('um').m
        search_x = feedback_params['x range'].to('um').m
        search_y = feedback_params['y range'].to('um').m
        scan_steps = feedback_params['scan steps']
        iterations = feedback_params['xy iterations']
        x_center = init_x
        y_center = init_y
        for iteration in self.feedback.progress(range(iterations)):
            x_steps = np.linspace(x_center - search_x, x_center + search_x, scan_steps)
            x_scan_data = list()
            for x_step in x_steps:
                self.xps.abs_position[self.x_positioner_name] = x_step
                x_scan_datum = self.read()
                x_scan_data.append(x_scan_datum)
            p0 = [np.max(x_scan_data), x_steps[np.argmax(x_scan_data)], 1, np.min(x_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, x_steps, x_scan_data, p0=p0)
            except RuntimeError:
                continue
            x_fitted = gaussian(x_steps, *popt)
            x_center = popt[1]

            y_steps = np.linspace(y_center - search_y, y_center + search_y, scan_steps)
            y_scan_data = list()
            for y_step in y_steps:
                self.xps.abs_position[self.y_positioner_name] = y_step
                y_scan_datum = self.read()
                y_scan_data.append(y_scan_datum)
            p0 = [np.max(y_scan_data), y_steps[np.argmax(y_scan_data)], 1, np.min(y_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, y_steps, y_scan_data, p0=p0)
            except RuntimeError:
                continue
            y_fitted = gaussian(y_steps, *popt)
            y_center = popt[1]

            self.x_center = x_center
            self.y_center = y_center

            # self.xps.abs_position[self.x_positioner_name] = x_center
            # self.xps.abs_position[self.y_positioner_name] = y_center

            values = {
                'iteration': iteration,
                'x_scan_range': x_steps,
                'y_scan_range': y_steps,
                'x_data': x_scan_data,
                'y_data': y_scan_data,
                'x_fitted': x_fitted,
                'y_fitted': y_fitted,
                'x_center': x_center,
                'y_center': y_center,
            }
            self.feedback.acquire(values)
        return

    @feedback.initializer
    def initialize_feedback(self):
        params = self.feedback_parameters.widget.get()
        self.x_positioner_name = params['x positioner name']
        self.y_positioner_name = params['y positioner name']
        self.z_positioner_name = params['z positioner name']
        self.initial_x_pos = self.xps.abs_position[self.x_positioner_name]
        self.initial_y_pos = self.xps.abs_position[self.y_positioner_name]
        self.initial_z_pos = self.xps.abs_position[self.z_positioner_name]
        self.delay = params['interpoint delay']
        self.x_center = self.initial_x_pos
        self.y_center = self.initial_y_pos
        acq_ch = params['acquisition channel']
        if acq_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('XPSFeedback_CI')
            channel = CountEdgesChannel(acq_ch)
            self.task.add_channel(channel)
            self.read = self.ci_read
        return

    @feedback.finalizer
    def finalize_feedback(self):
        self.task.clear()
        if feedback_params['move to optimum']:
            final_x_pos = self.x_center
            final_y_pos = self.y_center
        else:
            final_x_pos = self.initial_x_pos
            final_y_pos = self.initial_y_pos
        self.xps.abs_position[self.x_positioner_name] = final_x_pos
        self.xps.abs_position[self.y_positioner_name] = final_y_pos
        return

    def ci_read(self):
        ctr_start = self.task.read(samples_per_channel=1)[-1]
        t0 = time.time()
        time.sleep(self.delay)
        ctr_end = self.task.read(samples_per_channel=1)[-1]
        tf = time.time()
        ct_rate = (ctr_end - ctr_start) / (tf - t0)
        return ct_rate

    @Element()
    def feedback_parameters(self):
        params = [
            ('acquisition channel', {
                'type': list,
                'items': list(self.daq.counter_input_channels), # + list(self.daq.analog_input_channels),
            }),
            ('x initial', {
                'units': 'um',
                'type': float,
                'default': 0.0,
            }),
            ('y initial', {
                'units': 'um',
                'type': float,
                'default': 0.0,
            }),
            ('x range', {
                'units': 'um',
                'type': float,
                'default': 2.0e-6,
                'nonnegative': True,
            }),
            ('y range', {
                'units': 'um',
                'type': float,
                'default': 2.0e-6,
                'nonnegative': True,
            }),
            ('scan steps', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('interpoint delay', {
                'type': float,
                'default': 1.0,
                'positive': True,
            }),
            ('xy iterations', {
                'type': int,
                'default': 5,
                'nonnegative': True,
            }),
            ('x positioner name', {
                'type': str,
            }),
            ('y positioner name', {
                'type': str,
            }),
            ('z positioner name', {
                'type': str,
            }),
            ('move to optimum', {
                'type': bool,
                'default': False,
            })
        ]
        w = ParamWidget(params)
        return w

    @Element('X scan')
    def x_scan(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 1 (fit)', symbol=None)
        return p

    @Element('Y scan')
    def y_scan(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 1 (fit)', symbol=None)
        return p

    @x_scan.on(feedback.acquired)
    def update_x_scan(self, ev):
        w = ev.widget
        latest_data = self.data.tail(1)
        w.set('Channel 1', xs=list(latest_data.x_scan_range)[0], ys=list(latest_data.x_data)[0])
        w.set('Channel 1 (fit)', xs=list(latest_data.x_scan_range)[0], ys=list(latest_data.x_fitted)[0])
        return

    @y_scan.on(feedback.acquired)
    def update_y_scan(self, ev):
        w = ev.widget
        latest_data = self.data.tail(1)
        w.set('Channel 1', xs=list(latest_data.y_scan_range)[0], ys=list(latest_data.y_data)[0])
        w.set('Channel 1 (fit)', xs=list(latest_data.y_scan_range)[0], ys=list(latest_data.y_fitted)[0])
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
