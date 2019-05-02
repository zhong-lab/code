from PyQt5 import QtWidgets
import pyqtgraph as pg

import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.rigol.ds1204b import DS1204B

from lantz import Q_



class OscilloscopeSpyrelet(Spyrelet):

    requires = {
        'scope': DS1204B,
    }

    @Task()
    def sweep(self, **kwargs):
        params = self.sweep_parameters.widget.get()

        for a in range(params['accumulations']):

            t, y = self.scope.get_waveform_trace(channel=self.inp_ch)

            values = {
                'accumulation': a,
                't': t,
                'y': y,
            }

            self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.inp_ch = int(params['channel'])
        self.scope.averages = params['averages']
        return

    @sweep.finalizer
    def finalize(self):
        # self.task.clear()
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('channel', {
                'type': list,
                'items': ['1', '2', '3', '4', 'MATH'],
                'default': '1',
            }),
            ('averages', {
                'type': int,
                'default': 256,
                'positive': True,
            }),
            ('accumulations', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest scope trace')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.xlabel = 'Time (s)'
        p.ylabel = 'Voltage (V)'
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.accumulation == self.data.accumulation.max()]
        w.set('Channel 1', xs=latest_data.t.values[0], ys=latest_data.y.values[0])
        #w.set('Channel 1', xs=latest_data.t, ys=latest_data.y)
        return

    @Element(name='Accumulated scope trace')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.xlabel = 'Time (s)'
        p.ylabel = 'Voltage (V)'
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        # average dataset
        ts = self.data['t'].mean()
        ys = self.data['y'].mean()

        if self.data.accumulation.max() > 0:

            std_cts = self.data['y'].values.std()
            w.set('Channel 1', xs=ts, ys=ys, yerrs=std_cts)

        else:
            w.set('Channel 1', xs=ts, ys=ys)

        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
