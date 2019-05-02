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
from lantz import Q_

class LockinVsFreqSpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'lockin': SR7265,
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        time_const_in_sec = Q_(params['time_const']).to('s').magnitude
        self.lockin.time_constant = params['time_const']
        def get_xy():
            time.sleep(time_const_in_sec/2)
            return self.lockin.xy
        for sweep in range(params['sweeps']):
            for f in params['frequency'].array:
                self.sg.frequency = f
                time.sleep(time_const_in_sec*3)
                xys = [get_xy() for _ in range(params['lockin_pts'])]
                xs, ys = zip(*xys)
                values = {
                    'sweep_idx': sweep,
                    'f': f,
                    'x': np.mean(xs),
                    'y': np.mean(ys),
                }
                self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.sg.rf_amplitude = params['sg_power']
        self.sg.mod_toggle = params['mod_toggle']
        self.sg.rf_toggle = True
        return

    @sweep.finalizer
    def finalize(self):
        self.sg.rf_toggle = False

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('frequency', {
                'type': range,
                'units': 'GHz',
                'default': {'func': 'linspace',
                            'start': 1.3e9,
                            'stop': 1.4e9,
                            'num': 10},
            }),
            ('lockin_pts', {
                'type': int,
                'default': 30,
                'positive': True,
            }),
            ('sg_power', {
                'type': float,
                'default': -30,
                'suffix':' dBm'
            }),
            ('sweeps', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('time_const', {
                'type': list,
                'items': list(self.lockin.TIME_CONSTANTS.keys()),
            }),
            ('mod_toggle', {
                'type': bool,
                'default': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest counts versus frequency')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 2')
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        w.set('Channel 1', xs=latest_data.f, ys=latest_data.x)
        w.set('Channel 2', xs=latest_data.f, ys=latest_data.y)
        return

    @Element(name='Averaged counts versus frequency')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.plot('Channel 2')
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('f')
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

    # def build(self):
    #     start_element = self.element(QtWidgets.QPushButton("Start"))

    #     @start_element.control('clicked')
    #     def control(w, mediator, args, kwargs):
    #         mediator.namespace.sweeps = int(mediator.elements['Sweeps'].w.text())
    #         mediator.namespace.rf_amplitude = float(mediator.elements['RF amplitude'].w.text())
    #         mediator.namespace.fstart = float(mediator.elements['Frequency start'].w.text())
    #         mediator.namespace.fstop = float(mediator.elements['Frequency stop'].w.text())
    #         mediator.namespace.fsteps = float(mediator.elements['Frequency steps'].w.text())
    #         mediator.run_subroutine('sweep')
    #         return

    #     power = self.element(QtWidgets.QLineEdit(), name='RF amplitude')
    #     sweeps = self.element(QtWidgets.QLineEdit(), name='Sweeps')
    #     frequency_start_element = self.element(QtWidgets.QLineEdit(), name='Frequency start')
    #     frequency_stop_element = self.element(QtWidgets.QLineEdit(), name='Frequency stop')
    #     frequency_step_element = self.element(QtWidgets.QLineEdit(), name='Frequency steps')

    #     latest_plot = LinePlotWidget()
    #     latest_plot.title = 'Lockin vs Frequency (latest)'
    #     latest_plot.xlabel = 'Frequency (Hz)'
    #     latest_plot.ylabel = 'Lockin voltage (V)'
    #     latest_plot.plot('Channel X')
    #     latest_plot.plot('Channel Y')

    #     latest_plot_element = self.element(latest_plot, name='latest', docked=True)
    #     @latest_plot_element.listen('f')
    #     def listen(element, mediator, ns_object):
    #         latest = mediator.data[mediator.data.sweep_idx == mediator.data.sweep_idx.max()]
    #         element.w.set('Channel X', xs=latest.f, ys=latest.x)
    #         element.w.set('Channel Y', xs=latest.f, ys=latest.y)
    #         return

    #     average_plot = LinePlotWidget()
    #     average_plot.title = 'Lockin vs Frequency (average)'
    #     average_plot.xlabel = 'Frequency (Hz)'
    #     average_plot.ylabel = 'Lockin voltage (V)'
    #     average_plot.plot('Channel X')
    #     average_plot.plot('Channel Y')

    #     average_plot_element = self.element(average_plot, name='average', docked=True)
    #     @average_plot_element.listen('f')
    #     def listen(element, mediator, ns_object):
    #         grouped = mediator.data.groupby('f')
    #         xs = grouped.x
    #         ys = grouped.y
    #         element.w.set('Channel X', xs=xs.index, ys=xs.mean(), yerrs=xs.std())
    #         element.w.set('Channel Y', xs=ys.index, ys=ys.mean(), yerrs=ys.std())
    #         return
