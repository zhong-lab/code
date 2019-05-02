import numpy as np
import time
from itertools import count
import pyqtgraph as pg

from spyre import Spyrelet, Task, Element
from spyre.repository import Repository
from spyre.plotting import LinePlotWidget
from spyre.widgets.task import TaskWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.keithley.smu2400 import SMU2400

class IVCurveSpyrelet(Spyrelet):

    requires = {
        'smu': SMU2400
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        def get_iv():
                time.sleep(0.05)
                d = self.smu.get_data()
                return d['current'], d['voltage']

        self.smu.output = True


        for sweep_idx in range(params['sweeps']):

            for v in self.sweep.progress(params['voltages'].array):


                self.smu.source_voltage = v
                time.sleep(0.1)
                i_s, v_s = zip(*(get_iv() for _ in range(params['points'])))
                i_avg, v_avg = np.mean(i_s), np.mean(v_s)
                values = {
                    'sweep_idx': sweep_idx,
                    'set_v': v,
                    'v': v_avg,
                    'i': i_avg,
                }
                self.sweep.acquire(values)



        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()

        #self.smu.reset()
        self.smu.source_function = 'voltage'
        self.smu.source_voltage_range = params['voltage_limit']
        self.smu.source_voltage = 0
        self.smu.current_compliance = params['current_limit']
        self.smu.sense_current_range = params['current_limit']
        self.smu.source_current_range = params['current_limit']

        self.smu.sense_function['current'] = 'ON'
        self.smu.sense_function['voltage'] = 'ON'

        return

    @sweep.finalizer
    def finalize(self):
        self.smu.source_voltage = 0
        self.smu.output = False
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):

        params = [

            ('voltages', {
                'type': range,
                'units': 'V',
                'default': {'func': 'linspace',
                            'start': -1,
                            'stop': 3,
                            'num': 101},
            }),
            ('sweeps', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('points', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('current_limit', {
                'type': float,
                'units': 'amps',
                'default': 0.002,
                'positive': True,
            }),
            ('voltage_limit', {
                'type': float,
                'units': 'V',
                'default': 5,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest counts versus frequency')
    def latest(self):
        p = LinePlotWidget()
        #p.plot('Voltage (V)')
        p.plot('Current (A)')
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        #w.set('Voltage (V)', xs=latest_data.set_v, ys=latest_data.v)
        w.set('Current (A)', xs=latest_data.set_v, ys=latest_data.i)
        return

    @Element(name='Averaged counts versus frequency')
    def averaged(self):
        p = LinePlotWidget()
        #p.plot('Voltage (V)')
        p.plot('Current (A)')
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('set_v')
        xs = grouped.v
        ys = grouped.i
        xs_averaged = xs.mean()
        ys_averaged = ys.mean()
        #w.set('Voltage (V)', xs=xs_averaged.index, ys=xs_averaged, yerrs=xs.std())
        w.set('Current (A)', xs=ys_averaged.index, ys=ys_averaged, yerrs=ys.std())
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
