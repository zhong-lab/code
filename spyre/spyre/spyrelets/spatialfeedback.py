import numpy as np
from scipy import optimize

from spyre import Spyrelet, Task, Element
from spyre.plotting import LinePlotWidget
from spyre.widgets.task import TaskWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel
from lantz.drivers.newport.fsm300 import FSM300
# from lantz.drivers.attocube.anc350 import ANC350

import pyqtgraph as pg

def gaussian(xs, a=1, x=0, width=1, b=0):
    return a * np.exp(-np.square((xs - x) / width)) + b

class SpatialFeedbackSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        # 'atto': ANC350,
        'fsm': FSM300,
    }

    @Task()
    def feedback(self, **kwargs):
        self.dataset.clear()
        feedback_params = self.feedback_parameters.widget.get()
        init_x = feedback_params['x initial'].to('um').m
        init_y = feedback_params['y initial'].to('um').m
        search_x = feedback_params['x range'].to('um').m
        search_y = feedback_params['y range'].to('um').m
        scan_steps = feedback_params['scan steps']
        iterations = feedback_params['xy iterations']
        scan_points = feedback_params['scan points']
        x_center = init_x
        y_center = init_y
        for iteration in self.feedback.progress(range(iterations)):

            x_steps = np.linspace(x_center - search_x, x_center + search_x, scan_steps)
            x_scan_config = {
                'init_point': (y_center, x_steps[0]),
                'final_point': (y_center, x_steps[-1]),
                'steps': scan_steps,
                'acq_task': self.task,
                'acq_rate': Q_(20, 'kHz'),
                'pts_per_pos': scan_points,
            }
            x_scan_data = self.fsm.line_scan(**x_scan_config)
            p0 = [np.max(x_scan_data), x_steps[np.argmax(x_scan_data)], 1, np.min(x_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, x_steps, x_scan_data, p0=p0)
            except RuntimeError:
                continue
            x_fitted = gaussian(x_steps, *popt)
            x_center = popt[1]

            y_steps = np.linspace(y_center - search_y, y_center + search_y, scan_steps)
            y_scan_config = {
                'init_point': (y_steps[0], x_center),
                'final_point': (y_steps[-1], x_center),
                'steps': scan_steps,
                'acq_task': self.task,
                'acq_rate': Q_(20, 'kHz'),
                'pts_per_pos': scan_points,
            }
            y_scan_data = self.fsm.line_scan(**y_scan_config)
            p0 = [np.max(y_scan_data), y_steps[np.argmax(y_scan_data)], 1, np.min(y_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, y_steps, y_scan_data, p0=p0)
            except RuntimeError:
                continue
            y_fitted = gaussian(y_steps, *popt)
            y_center = popt[1]

            self.fsm.abs_position = y_center, x_center

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

    # def ai_z(self):
    #     self.task.start()
    #     for z in zs:
    #         self.atto.cl_move(Q_(z, 'um'))
    #         p0 = self.task.read()[-1]

    @feedback.initializer
    def initialize(self):
        params = self.feedback_parameters.widget.get()
        inp_ch = params['acquisition channel']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('Feedback3D_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('Feedback3D_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
        else:
            pass
        return

    @feedback.finalizer
    def finalize(self):
        self.task.clear()
        return

    @Element()
    def feedback_parameters(self):
        params = [
            ('acquisition channel', {
                'type': list,
                'items': list(self.daq.counter_input_channels) + list(self.daq.analog_input_channels),
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
            ('scan points', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('xy iterations', {
                'type': int,
                'default': 5,
                'nonnegative': True,
            }),
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
