import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from spyre.plotting import HeatmapPlotWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.newport import FSM300, XPSQ8

class XPSXZSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'fsm': FSM300,
        'xps': XPSQ8,
    }

    @Task(name='XZ scan')
    def xz_scan(self):
        self.dataset.clear()
        params = self.xz_scan_parameters.widget.get()
        for sweep in self.xz_scan.progress(range(params['sweeps'])):
            for column_idx, z in enumerate(self.z_steps):
                abs_position = self.initial_z_pos + z
                self.xps.abs_position[self.z_positioner_name] = abs_position.to('mm')
                time.sleep(0.5)
                line_scan_params = {
                    'init_point': (self.x_start, self.y_start),
                    'final_point': (self.x_end, self.y_end),
                    'steps': self.xy_steps,
                    'acq_task': self.task,
                    'acq_rate': Q_(params['acquisition rate'], 'Hz'),
                    'pts_per_pos': params['acquisition points per pixel'],
                }
                column_data = self.fsm.line_scan(**line_scan_params)
                self.fsm.abs_position = (self.x_start, self.y_start)
                values = {
                    'sweep_idx': sweep,
                    'z': z.to('mm').m,
                    'column_idx': column_idx,
                    'column_data': column_data,
                }
                self.xz_scan.acquire(values)
        return

    @xz_scan.initializer
    def initialize_xz_scan(self):
        params = self.xz_scan_parameters.widget.get()
        self.z_positioner_name = params['z positioner name']
        self.initial_z_pos = self.xps.abs_position[self.z_positioner_name]
        self.x_start = params['x start'].to('um').m
        self.y_start = params['y start'].to('um').m
        self.x_end = params['x end'].to('um').m
        self.y_end = params['y end'].to('um').m
        self.xy_steps = params['xy steps']
        self.xy_dist = np.sqrt(np.square(params['x start'] - params['x end']) +
                       np.square(params['y start'] - params['y end'])).to('um').m
        self.xy_step_dist = self.xy_dist / self.xy_steps
        self.z_steps = params['z range'].array.to('mm')
        self.max_rows = len(self.z_steps)

        z_diff = np.max(self.z_steps) - np.min(self.z_steps)
        # im_pos = [np.mean(self.z_steps).to('um').m, 0]
        im_pos = [-self.xy_dist / 2, 0]
        im_scale = [self.xy_step_dist, z_diff.to('um').m / self.max_rows]
        # im_scale = [self.max_rows / z_diff.to('um').m, self.xy_step_dist]

        self.latest_scan.widget.im_pos     = im_pos
        self.latest_scan.widget.im_scale   = im_scale
        self.averaged_scan.widget.im_pos   = im_pos
        self.averaged_scan.widget.im_scale = im_scale

        inp_ch = params['acquisition channel input']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('TaskVsFSM_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('TaskVsFSM_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
        else:
            # should never get here
            pass
        return

    @xz_scan.finalizer
    def finalize_xz_scan(self):
        self.fsm.abs_position = (0.0, 0.0)
        self.xps.abs_position[self.z_positioner_name] = self.initial_z_pos
        self.task.clear()
        return

    @Element()
    def xz_scan_parameters(self):
        params = [
            ('acquisition channel input', {
                'type': list,
                'items': list(self.daq.counter_input_channels)+list(self.daq.analog_input_channels),
                'default': 'Dev1/ctr2',
            }),
            ('x start', {
                'type': float,
                'units': 'um',
            }),
            ('y start', {
                'type': float,
                'units': 'um',
            }),
            ('x end', {
                'type': float,
                'units': 'um',
            }),
            ('y end', {
                'type': float,
                'units': 'um',
            }),
            ('xy steps', {
                'type': int,
                'positive': True,
            }),
            ('z range', {
                'type': range,
                'units': 'mm',
                'default': {'func':'linspace', 'start': 0e-6, 'stop': 5e-6, 'num': 50}
            }),
            ('z positioner name', {
                'type': str,
            }),
            ('sweeps', {
                'type': int,
                'positive': True,
            }),
            ('acquisition rate', {
                'type': float,
                'nonnegative': True,
                'default': 5000,
            }),
            ('acquisition points per pixel', {
                'type': int,
                'positive': True,
                'default': 10,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element()
    def latest_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'X (um)'
        w.ylabel = 'Z (um)'
        return w

    @latest_scan.on(xz_scan.acquired)
    def update_latest_scan(self, ev):
        latest = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        im = np.vstack(latest.sort_values('column_idx')['column_data'])
        ev.widget.set(im)
        return

    @Element()
    def averaged_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'X (um)'
        w.ylabel = 'Z (um)'
        return w

    @averaged_scan.on(xz_scan.acquired)
    def update_averaged_scan(self, ev):
        grouped = self.data.groupby('column_idx')['column_data']
        averaged = grouped.apply(lambda column: np.mean(np.vstack(column), axis=0))
        im = np.vstack(averaged)
        ev.widget.set(im)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
