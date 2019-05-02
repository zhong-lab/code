from itertools import count
import time
import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from spyre.plotting import LinePlotWidget

from lantz import Q_
from lantz.drivers.toptica import DLC
from lantz.drivers.bristol import Bristol671

class LaserFrequencyFeedbackSpyrelet(Spyrelet):

    requires = {
        'dlc': DLC,
        'wavemeter': Bristol671,
    }

    @Task(name='Laser frequency feedback')
    def feedback(self):
        self.dataset.clear()
        piezo_value = self.dlc.piezo_voltage
        for iteration in self.feedback.progress(self.iterator()):
            current_frequency = self.wavemeter.frequency.to('GHz')
            dfrequency = current_frequency - self.target_frequency
            dpiezo = self.p * dfrequency
            values = {
                'iteration': iteration,
                'time': iteration * self.feedback_period.to('s').m,
                'frequency_error': dfrequency.to('MHz').m,
                'piezo_value': piezo_value.to('V').m
            }
            self.feedback.acquire(values)
            piezo_value -= dpiezo
            if not Q_(0, 'V') <= piezo_value <= Q_(140, 'V'):
                # piezo value out of range
                return
            self.dlc.piezo_voltage = piezo_value
            time.sleep(self.feedback_period.to('s').m)
        return

    @feedback.initializer
    def initializer(self):
        params = self.feedback_parameters.widget.get()
        self.target_frequency = params['target frequency']
        self.frequency_tolerance = params['frequency tolerance']
        self.p = params['P']
        self.feedback_period = params['feedback period']
        self.iterator = count if params['continuous'] else lambda : range(params['number of period'])
        return

    @Element(name='Feedback parameters')
    def feedback_parameters(self):
        params = [
            ('target frequency', {
                'type': float,
                'units': 'GHz',
            }),
            ('frequency tolerance', {
                'type': float,
                'units': 'GHz',
                'default': 50e6,
            }),
            ('P', {
                'type': float,
                'units': 'V / GHz',
                'default': 3e-9,
            }),
            ('feedback period', {
                'type': float,
                'units': 's',
                'default': 1,
            }),
            ('continuous', {
                'type': bool,
            }),
            ('number of period', {
                'type': int,
                'nonnegative':True
            })
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Laser frequency error')
    def laser_frequency_error(self):
        p = LinePlotWidget()
        p.plot('error', symbol=None)
        p.xlabel = 'time (s)'
        p.ylabel = 'error (MHz)'
        return p

    @laser_frequency_error.on(feedback.acquired)
    def update_laser_frequency_error(self, ev):
        w = ev.widget
        w.set('error', xs=self.data.time, ys=self.data.frequency_error)
        return
