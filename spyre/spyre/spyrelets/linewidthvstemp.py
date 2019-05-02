import numpy as np
from scipy import optimize
import time
import pyqtgraph as pg

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.rangespace import Rangespace
from spyre.plotting import LinePlotWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
from lantz.drivers.montana import Cryostation

from spyre.spyrelets.taskvslaserfrequency import TaskVsLaserFrequencySpyrelet

def lorentzian(xs, a=1, lw=1, x0=0, c=0):
    return a / (1 + np.square(xs - x0) / lw) + c

class LinewidthVsTempSpyrelet(Spyrelet):

    requires = {
        'cryo': Cryostation,
    }

    requires_spyrelet = {
        'tvlf': TaskVsLaserFrequencySpyrelet,
    }

    @Task(name='Temperature sweep')
    def temp_sweep(self):
        for temp_setpoint in self.temp_sweep.progress(self.temp_setpoints):
            self.cryo.temp_setpoint = temp_setpoint
            now = time.time()
            while time.time() < now + 120.0:
                pt = self.platform_temperature
                if np.isclose(temp_setpoint, pt, atol=1e-1):
                    break
                time.sleep(1.0)
            sample_temp = self.sample_temperature
            self.tvlf.fine_scan()
            frequencies = self.tvlf.data.frequency
            amplitudes = self.tvlf.data.amplitude
            p0 = [
                np.max(amplitudes) - np.min(amplitudes), # peak amplitude
                1e-3, # linewidth
                frequencies[np.argmax(amplitudes)], # peak center
                np.min(amplitudes), # background,
            ]
            try:
                popt, pcov = optimize.curve_fit(lorentzian, frequencies, amplitudes, p0=p0)
            except RuntimeError:
                continue
            f_amplitude, f_lw, f_center, f_background = popt
            values = {
                'setpoint': temp_setpoint,
                'platform_actual': pt,
                'sample_actual': sample_temp,
                'f_amplitude': f_amplitude,
                'f_linewidth': f_lw,
                'f_center': f_center,
                'f_background': f_background,
            }
            self.temp_sweep.acquire(values)
        return

    @temp_sweep.initializer
    def initialize(self):
        self.starting_setpoint = self.cryo.temp_setpoint
        params = self.parameters.widget.get()
        self.temp_setpoints = params['temperatures']
        self.setpoint_timeout = params['setpoint timeout']
        return

    @temp_sweep.finalizer
    def finalize(self):
        self.cryo.temp_setpoint = self.starting_setpoint
        return

    @Element(name='Temperature sweep parameters')
    def parameters(self):
        params = [
            ('temperatures', {
                'type': range,
                'units': 'K',
            }),
            ('setpoint timeout', {
                'type': float,
                'units': 's',
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Linewidth vs temperature')
    def lwvstemp(self):
        p = LinePlotWidget()
        p.plot('Linewidth')
        return p

    @Element(name='Amplitude vs temperature')
    def ampvstemp(self):
        p = LinePlotWidget()
        p.plot('Amplitude')
        return p

    @Element(name='Center vs temperature')
    def centervstemp(self):
        p = LinePlotWidget()
        p.plot('Center')
        return p

    @lwvstemp.on(temp_sweep.acquired)
    def update_lwvstemp(self, ev):
        w = ev.widget
        w.set('Linewidth', xs=self.data.sample_actual, ys=self.data.f_linewidth)
        return

    @ampvstemp.on(temp_sweep.acquired)
    def update_ampvstemp(self, ev):
        w = ev.widget
        w.set('Amplitude', xs=self.data.sample_actual, ys=self.data.f_amplitude)
        return

    @centervstemp.on(temp_sweep.acquired)
    def update_centervstemp(self, ev):
        w = ev.widget
        w.set('Center', xs=self.data.sample_actual, ys=self.data.f_center)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
