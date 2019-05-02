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
from lantz.drivers.signalrecovery import SR7265
from lantz.drivers.tektronix.awg5000 import AWG5000
from lantz import Q_

class LockinVsLineSpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'lockin': SR7265,
        'awg': AWG5000,
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        time_const_in_sec = Q_(params['time constant']).to('s').magnitude
        def get_xy():
            time.sleep(time_const_in_sec/2)
            return self.lockin.xy
        for sweep in range(params['sweeps']):
            for line in params['lines'].array:
                self.awg.jump_to_line(line)
                time.sleep(time_const_in_sec*3)
                xys = [get_xy() for _ in range(params['lockin points'])]
                xs, ys = zip(*xys)
                values = {
                    'sweep_idx': sweep,
                    'line': line,
                    'x': np.mean(xs),
                    'y': np.mean(ys),
                }
                self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.sg.frequency = params['frequency']
        self.sg.rf_amplitude = params['sg power']
        self.sg.mod_toggle = params['IQ modulation']
        self.sg.rf_toggle = True
        return

    @sweep.finalizer
    def finalize(self):
        self.sg.rf_toggle = False

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('lines', {
                'type': range,
            }),
            ('lockin points', {
                'type': int,
                'default': 30,
                'positive': True,
            }),
            ('frequency', {
                'type': float,
                'default': 1.3e9,
                'units': 'Hz',
            }),
            ('sg power', {
                'type': float,
                'default': -30,
                'suffix':' dBm'
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('time constant', {
                'type': list,
                'items': list(self.lockin.TIME_CONSTANTS.keys()),
                'default':'100 ms',
            }),
            ('IQ modulation', {
                'type': bool,
                'default': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest lockin vs line')
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

    @Element(name='Averaged lockin vs line')
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

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
