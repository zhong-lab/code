import numpy as np
from itertools import count
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.rangespace import Rangespace
from spyre.plotting import LinePlotWidget

from lantz import Q_
from lantz.drivers.toptica import DLC, MotDLpro
from lantz.drivers.bristol import Bristol671

from spyre.spyrelets.ctroptimize import CTROptimizeSpyrelet
from spyre.spyrelets.laserfrequencyfeedback import LaserFrequencyFeedbackSpyrelet

c = Q_(299792458, 'm/s')

def inverse_quadratic_interpolation(a, b, c, ya, yb, yc):
    x = a * yb * yc / ((ya - yb) * (ya - yc))
    y = b * ya * yc / ((yb - ya) * (yb - yc))
    z = c * ya * yb / ((yc - ya) * (yc - yb))
    return x + y + z

def secant(a, b, ya, yb):
    return b - yb * (b - a) / (yb - ya)

def bisection(a, b):
    return (a + b) / 2

def brent_search(f, a, b, ya=None, yb=None, dta=1, xtol=0.01, ytol=0.01, integer=True, callback=None):
    if ya is None:
        ya = f(a)
    if yb is None:
        yb = f(b)
    if ya * yb >= 0:
        raise ValueError('root is not bracketed by ya={} and yb={}'.format(ya, yb))
    if abs(ya) < abs(yb):
        a, b = b, a
        ya, yb = yb, ya
    c = a
    yc = ya
    m = True
    for iteration in count():
        if ya != yc and yc != yb:
            s = inverse_quadratic_interpolation(a, b, c, ya, yb, yc)
        else:
            s = secant(a, b, ya, yb)
        g, h = (3 * a + b) / 4, b
        if g > h:
            g, h = h, g
        conds = [
            not g < s < h,
            m and abs(s - b) >= (b - c) / 2,
            not m and abs(s - b) >= (c - d) / 2,
            m and abs(b - c) < dta,
            not m and abs(c - d) < dta,
        ]
        if any(conds):
            s = bisection(a, b)
            m = True
        else:
            m = False
        ys = f(s)
        d = c
        c = b
        yc = yb
        if ya * ys < 0:
            b = s
            yb = ys
        else:
            a = s
            ya = ys
        if abs(ya) < abs(yb):
            a, b = b, a
            ya, yb = yb, ya
        if callback is not None:
            callback(iteration, ys)
        if np.isclose(yb, 0, atol=ytol) or np.isclose(ys, 0, atol=ytol) or np.abs(a - b) < xtol:
            return b
        if integer and int(a) == int(b):
            return b

class GotoFrequencySpyrelet(Spyrelet):

    requires = {
        'dlc': DLC,
        'mot': MotDLpro,
        'wavemeter': Bristol671,
    }

    requires_spyrelet = {
        'ctropt': CTROptimizeSpyrelet,
        'laserfreqfb':LaserFrequencyFeedbackSpyrelet,
    }

    @Task(name='Goto target frequency')
    def goto_frequency(self, **kwargs):
        self.dataset.clear()
        params = self.target_parameters.widget.get()
        target_frequency = params['target frequency']
        # center the piezo voltage
        self.dlc.piezo_voltage = Q_(70, 'V')
        self.dlc.feedforward_enabled = True
        # set some sensible starting FF factor
        self.dlc.feedforward_factor = Q_(-1.5, 'mA / V')
        # set some sensible starting current
        self.dlc.current = Q_(250, 'mA')

        target_wavelength = c / target_frequency

        # initiate coarse move
        position = self.mot.wavelength_to_step(target_wavelength.to('nm').magnitude)
        self.mot.precision_move(position)

        # obtain coarse frequency and wavelength after one motor step
        coarse_frequency = self.wavemeter.frequency
        coarse_wavelength = c / coarse_frequency

        p0, p1, p2 = self.mot.p_coeffs
        delta_wavelength = target_wavelength - coarse_wavelength
        # determine other bracket point from existing error
        # we'll assume linear behavior at this point
        position2 = int(position + 2 * delta_wavelength.to('nm').magnitude * p1)
        if position > position2:
            position, position2 = position2, position

        def acquire(iteration, error):
            values = {
                'iteration': iteration,
                'error': error,
                'stable_current': self.dlc.current.magnitude,
            }
            self.goto_frequency.acquire(values)
            return

        def df(position, coarse_attempts=5):
            self.mot.precision_move(position)
            time.sleep(0.5)
            measured_frequency = self.wavemeter.frequency
            delta_frequency = measured_frequency - target_frequency
            return delta_frequency.to('GHz').m

        brent_kwargs = {
            'ya': (coarse_frequency - target_frequency).to('GHz').m,
            'yb': None,
            'ytol': params['tolerance'].to('GHz').m,
            'callback': acquire,
        }

        target_position = brent_search(df, position, position2, **brent_kwargs)

        if params['run CTR optimizer']:
            self.ctropt.optimize()
        if params['feedback period']:
            fb_params = {
                'target frequency': params['target frequency'],
                'number of period': params['feedback period'],
                'continuous': False,
            }
            self.laserfreqfb.feedback_parameters.widget.set(**fb_params)
            self.laserfreqfb.feedback()
        return

    @goto_frequency.initializer
    def initialize(self):
        return

    @Element(name='Target parameters')
    def target_parameters(self):
        params = [
            ('target frequency', {
                'units': 'GHz',
                'type': float,
                'default': 265300.0e9,
            }),
            ('tolerance', {
                'units': 'GHz',
                'type': float,
                'default': 5.0e9,
            }),
            ('run CTR optimizer', {
                'type': bool,
            }),
            ('feedback period', {
                'type':int,
                'nonnegative':True,
            })
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Frequency error')
    def freq_error(self):
        p = LinePlotWidget()
        p.xlabel = 'Iteration'
        p.ylabel = 'Error (GHz)'
        p.plot('Error')
        return p

    @freq_error.on(goto_frequency.acquired)
    def update_freq_error(self, ev):
        w = ev.widget
        w.set('Error', xs=self.data.iteration, ys=self.data.error)
        return
