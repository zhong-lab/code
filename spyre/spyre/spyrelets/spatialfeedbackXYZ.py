import numpy as np
from scipy import optimize
import time

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
from lantz.drivers.newport.xpsq8 import XPSQ8
# from lantz.drivers.attocube.anc350 import ANC350

import pyqtgraph as pg

def gaussian(xs, a=1, x=0, width=1, b=0):
    return a * np.exp(-np.square((xs - x) / width)) + b

class SpatialFeedbackXYZSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'fsm': FSM300,
        'xps': XPSQ8,
    }

    @Task()
    def feedback(self, **kwargs):
        self.dataset.clear()
        feedback_params = self.feedback_parameters.widget.get()
        iterations = feedback_params['xyz iterations']
        # xy parameters
        init_x = feedback_params['x initial'].to('um').m
        init_y = feedback_params['y initial'].to('um').m
        search_x = feedback_params['x range'].to('um').m
        search_y = feedback_params['y range'].to('um').m
        fsm_scan_steps = feedback_params['fsm scan steps']
        fsm_scan_points = feedback_params['fsm scan points']
        x_center = init_x
        y_center = init_y
        # z parameters
        z_center = self.initial_z_pos
        search_z = feedback_params['z range'].to('mm').m
        z_scan_steps = feedback_params['xps scan steps']
        xps_settle_time = 10e-3
        max_x_drift = 10.0 # 10 um
        max_y_drift = max_x_drift 
        max_z_drift = 50e-3 # 50 um
        x_drift_data = list()
        y_drift_data = list()
        z_drift_data = list()
        iteration_data = list()

        for iteration in self.feedback.progress(range(iterations)):
            #x scan
            x_steps = np.linspace(x_center - search_x, x_center + search_x, fsm_scan_steps)
            x_scan_config = {
                'init_point': (y_center, x_steps[0]),
                'final_point': (y_center, x_steps[-1]),
                'steps': fsm_scan_steps,
                'acq_task': self.task,
                'acq_rate': Q_(20, 'kHz'),
                'pts_per_pos': fsm_scan_points,
            }
            x_scan_data = self.fsm.line_scan(**x_scan_config)
            p0 = [np.max(x_scan_data), x_steps[np.argmax(x_scan_data)], 1, np.min(x_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, x_steps, x_scan_data, p0=p0)
            except RuntimeError:
                continue
            x_fitted = gaussian(x_steps, *popt)
            x_center_fit = popt[1]
            if np.min(x_steps) < x_center_fit < np.max(x_steps):
                if np.abs(x_center_fit - init_x) < max_x_drift:
                    x_center = x_center_fit
                else:
                    print("X drift limit reached. Setting to previous value.")
            else:
                print('Optimum X out of scan range. Setting to previous value.')
            
            # y scan
            y_steps = np.linspace(y_center - search_y, y_center + search_y, fsm_scan_steps)
            y_scan_config = {
                'init_point': (y_steps[0], x_center),
                'final_point': (y_steps[-1], x_center),
                'steps': fsm_scan_steps,
                'acq_task': self.task,
                'acq_rate': Q_(20, 'kHz'),
                'pts_per_pos': fsm_scan_points,
            }
            y_scan_data = self.fsm.line_scan(**y_scan_config)
            p0 = [np.max(y_scan_data), y_steps[np.argmax(y_scan_data)], 1, np.min(y_scan_data)]
            try:
                popt, pcov = optimize.curve_fit(gaussian, y_steps, y_scan_data, p0=p0)
            except RuntimeError:
                continue
            y_fitted = gaussian(y_steps, *popt)
            y_center_fit = popt[1]
            if np.min(y_steps) < y_center_fit < np.max(y_steps):
                if np.abs(y_center_fit - init_y) < max_y_drift:
                    y_center = y_center_fit
                else:
                    print("Y drift limit reached. Setting to previous value.")
            else:
                print('Optimum Y out of scan range. Setting to previous value.')
            
            self.fsm.abs_position = y_center, x_center

            #z scan
            self.task.clear()
            self.task = CounterInputTask('Feedback3D_CI')
            channel = CountEdgesChannel(self.inp_ch)
            self.task.add_channel(channel)
            self.task.start()

            z_steps = np.linspace(z_center - search_z, z_center + search_z, z_scan_steps)
            z_scan_data = list()
            for z_step in z_steps:
                self.xps.abs_position[self.z_positioner_name] = Q_(z_step, 'mm')
                time.sleep(xps_settle_time)
                z_scan_datum = self.read()
                z_scan_data.append(z_scan_datum)
            self.task.stop()
            z_scan_data = np.array(z_scan_data)
            p0 = [np.max(z_scan_data), z_steps[np.argmax(z_scan_data)], 1e-3, np.min(z_scan_data)]
            try:
                popt_z, pcov_z = optimize.curve_fit(gaussian, z_steps, z_scan_data, p0=p0)
            except RuntimeError:
                continue
            z_fitted = gaussian(z_steps, *popt_z)
            z_center_fit = popt_z[1]
            if feedback_params['move to z optimum']:
                if np.min(z_steps) < z_center_fit < np.max(z_steps):
                    if np.abs(z_center_fit - self.initial_z_pos) < max_z_drift:
                        # print('New optimum, delta_z={} um'.format((z_center_fit-z_center)*1e3))
                        z_center = z_center_fit
                    else:
                        print('Z drift limit reached. Setting to previous value.')
                else:
                    print('Optimum Z out of scan range. Setting to previous value.')
            self.xps.abs_position[self.z_positioner_name] = Q_(z_center, 'mm')
            time.sleep(xps_settle_time)
            # print("initial_z_pos:", self.initial_z_pos, "z_center:", z_center, "xps.z:", self.xps.abs_position[self.z_positioner_name].to('mm').m)
            
            # drift data
            x_drift_data.append(x_center - init_x)
            y_drift_data.append(y_center - init_y)
            z_drift_data.append((z_center - self.initial_z_pos)*1e3)
            iteration_data.append(iteration)

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
                'z_scan_range': z_steps,
                'z_data': z_scan_data,
                'z_fitted': z_fitted,
                'z_center': z_center,
                'x_drift_data': np.array(x_drift_data),
                'y_drift_data': np.array(y_drift_data),
                'z_drift_data': np.array(z_drift_data),
                'iteration_data': np.array(iteration_data),
            }

            self.pos = [Q_(x_center,'um'), Q_(y_center,'um'), z_center]
            self.feedback.acquire(values)

    @feedback.initializer
    def initialize(self):
        params = self.feedback_parameters.widget.get()

        self.z_positioner_name = 'Group3.Pos'
        self.initial_z_pos = self.xps.abs_position[self.z_positioner_name].to('mm').m
        self.delay = params['xps interpoint delay']
        inp_ch = params['acquisition channel']
        self.inp_ch = inp_ch
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('Feedback3D_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
            self.read = self.ci_read
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('Feedback3D_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
        else:
            pass
        self.pos = [params['x initial'], params['y initial'], self.initial_z_pos]
        return

    @feedback.finalizer
    def finalize(self):
        if self.feedback_parameters.widget.get()['update xy initial values']:
            kwargs = {'x initial': self.pos[0],
                      'y initial': self.pos[1],
                     }
            self.feedback_parameters.widget.set(**kwargs)
        self.task.clear()
        return

    def ci_read(self):
        ctr_start = self.task.read(samples_per_channel=1)[0]
        t0 = time.time()
        time.sleep(self.delay)
        ctr_end = self.task.read(samples_per_channel=1)[0]
        tf = time.time()
        ct_rate = (ctr_end - ctr_start) / (tf - t0)
        return ct_rate

    @Element()
    def feedback_parameters(self):
        params = [
            ('acquisition channel', {
                'type': list,
                'items': list(self.daq.counter_input_channels), # + list(self.daq.analog_input_channels),
                'default': 'DAQ6363/ctr2',
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
            ('z range', {
                'units': 'm',
                'type': float,
                'default': 10.0e-6,
                # 'nonnegative': True,
                'bounds': [0.0, 10e-6],
            }),
            ('fsm scan steps', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('fsm scan points', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('xps scan steps', {
                'type': int,
                'default': 50,
                'positive': True,
            }),
            ('xps interpoint delay', {
                'type': float,
                'default': 0.1,
                'positive': True,
            }),
            ('xyz iterations', {
                'type': int,
                'default': 1,
                'nonnegative': True,
            }),
            ('move to z optimum', {
                'type': bool,
                'default': True,
            }),
            ('update xy initial values', {
                'type': bool,
                'default': True,
            })
            # ('z feedback enabled', {
            #     'type': bool,
            #     'default': True,
            # })
        ]
        w = ParamWidget(params)
        return w

    @Element('X scan')
    def x_scan(self):
        p = LinePlotWidget()
        p.xlabel = "X (um)"
        p.ylabel = "Count rate (Hz)"
        p.plot('Channel 1')
        p.plot('Channel 1 (fit)', symbol=None)
        return p

    @Element('Y scan')
    def y_scan(self):
        p = LinePlotWidget()
        p.xlabel = "Y (um)"
        p.ylabel = "Count rate (Hz)"
        p.plot('Channel 1')
        p.plot('Channel 1 (fit)', symbol=None)
        return p

    @Element('Z scan')
    def z_scan(self):
        p = LinePlotWidget()
        p.xlabel = "Z (mm)"
        p.ylabel = "Count rate (Hz)"
        p.plot('Channel 1')
        p.plot('Channel 1 (fit)', symbol=None)
        return p

    @Element('Drift')
    def drift(self):
        p = LinePlotWidget()
        p.xlabel = "Iterations"
        p.ylabel = "Drift (um)"
        p.plot('X')
        p.plot('Y')
        p.plot('Z')
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

    @z_scan.on(feedback.acquired)
    def update_z_scan(self, ev):
        w = ev.widget
        latest_data = self.data.tail(1)
        w.set('Channel 1', xs=list(latest_data.z_scan_range)[0], ys=list(latest_data.z_data)[0])
        w.set('Channel 1 (fit)', xs=list(latest_data.z_scan_range)[0], ys=list(latest_data.z_fitted)[0])
        return

    @drift.on(feedback.acquired)
    def update_drift(self, ev):
        w = ev.widget
        latest_data = self.data.tail(1)
        w.set('X', xs=list(latest_data.iteration_data)[0], ys=list(latest_data.x_drift_data)[0])
        w.set('Y', xs=list(latest_data.iteration_data)[0], ys=list(latest_data.y_drift_data)[0])
        w.set('Z', xs=list(latest_data.iteration_data)[0], ys=list(latest_data.z_drift_data)[0])
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
