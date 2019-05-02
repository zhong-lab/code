from PyQt5 import QtWidgets
import pyqtgraph as pg

import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.stanford import SG396
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.tektronix.awg5000 import AWG5000, AWGState
from lantz import Q_

class CountsVsLineSpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'daq': Device,
        'awg': AWG5000,
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        for sweep in self.sweep.progress(range(params['sweeps'])):
            for line in params['lines'].array:
                self.awg.jump_to_line(line)
                ctrs_start = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in self.ctr_tasks])
                time.sleep(params['interpoint delay'])
                ctrs_end = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in self.ctr_tasks])
                dctrs = ctrs_end - ctrs_start
                ctrs_rates = dctrs[:,0] / dctrs[:,1]
                values = {
                    'sweep_idx': sweep,
                    'line': line,
                    'x': ctrs_rates[0],
                    'y': ctrs_rates[1],
                }

                self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.awg.toggle_run = 'running'
        self.awg.toggle_all_outputs(True)
        self.sg.rf_amplitude = params['rf amplitude']
        self.sg.frequency = params['frequency']
        self.sg.rf_toggle = True
        self.sg.mod_toggle = params['IQ modulation']

        self.sample_freq = 1e5

        gating_enabled = params['enable gating']
        ctrs = [params['counter 1'], params['counter 2']]
        # gates = [params['counter 1 gate'], params['counter 2 gate']]
        gates = ['/dev1/pfi6', '/dev1/pfi1']
        if len(set(ctrs)) != len(ctrs):
            raise RuntimeError('counter channels 1 and 2 must be different')
        if len(set(gates)) != len(gates) and gating_enabled:
            raise RuntimeError('counter gate channels 1 and 2 must be different')
        self.ctr_tasks = list()
        for idx, (ctr, gate) in enumerate(zip(ctrs, gates)):
            task = CounterInputTask('counter ch {}'.format(idx))
            ch = CountEdgesChannel(ctr)
            task.add_channel(ch)
            if gating_enabled:
                task.pause_trigger_type = 'digital_level'
                task.pause_trigger_source = gate
                task.pause_trigger_when = 'low'
            task.start()
            self.ctr_tasks.append(task)
        return

    @sweep.finalizer
    def finalize(self):
        self.sg.rf_toggle = False
        self.awg.toggle_all_outputs(False)
        self.awg.toggle_run = 'stopped'
        for ctr_task in self.ctr_tasks:
            ctr_task.clear()
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        line_range = Rangespace()
        params = [
            ('counter 1', {
                'type': list,
                'items': list(self.daq.counter_input_channels),
                'default': 'Dev1/ctr3',
            }),
            ('counter 2', {
                'type': list,
                'items': list(self.daq.counter_input_channels),
                'default': 'Dev1/ctr2',
            }),
            ('counter 1 gate', {
                'type': list,
                'items': list(self.daq.digital_input_lines),
                'default':'Dev1/port0/line0',
            }),
            ('counter 2 gate', {
                'type': list,
                'items': list(self.daq.digital_input_lines),
                'default':'Dev1/port1/line6',
            }),
            ('enable gating', {
                'type': bool,
                'default': True,
            }),
            ('lines', {
                'type': range,
            }),
            ('interpoint delay', {
                'type': float,
                'default': 1.0,
                'nonnegative': True,
            }),
            ('frequency', {
                'type': float,
                'default': 1.3e9,
                'units': 'Hz',
            }),
            ('rf amplitude', {
                'type': float,
                'default': -30,
                'suffix':' dBm'
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('IQ modulation', {
                'type': bool,
                'default': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest counts vs line')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 2')
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        w.set('Channel 1', xs=latest_data.line, ys=latest_data.x)
        w.set('Channel 2', xs=latest_data.line, ys=latest_data.y)
        return

    @Element(name='Differential counts vs line (latest)')
    def diff_latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1-2')
        return p

    @diff_latest.on(sweep.acquired)
    def diff_latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        diff = latest_data.x - latest_data.y
        w.set('Channel 1-2', xs=latest_data.line, ys=diff)
        return

    @Element(name='Averaged counts vs line')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 2')
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('line')
        xs = grouped.x
        ys = grouped.y
        xs_averaged = xs.mean()
        ys_averaged = ys.mean()
        w.set('Channel 1', xs=xs_averaged.index, ys=xs_averaged, yerrs=xs.std())
        w.set('Channel 2', xs=ys_averaged.index, ys=ys_averaged, yerrs=ys.std())
        return

    @Element(name='Differential counts vs line (averaged)')
    def diff_average(self):
        p = LinePlotWidget()
        p.plot('Channel 1-2')
        return p

    @diff_average.on(sweep.acquired)
    def diff_average_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('line')
        xs = grouped.x
        ys = grouped.y
        xs_averaged = xs.mean()
        ys_averaged = ys.mean()
        diff_averaged = xs_averaged - ys_averaged
        w.set('Channel 1-2', xs=xs_averaged.index, ys=diff_averaged, yerrs=np.sqrt(xs.var() + ys.var()))
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
