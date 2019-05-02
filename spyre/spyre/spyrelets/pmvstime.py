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

from lantz.drivers.thorlabs.pm100d import PM100D

class PMVsTimeSpyrelet(Spyrelet):

    requires = {
        'pm100d': PM100D,
    }

    @Task()
    def run_forever(self, **kwargs):
        self.dataset.clear()
        run_params = self.run_parameters.widget.get()
        samples = run_params['samples']
        delay = run_params['interpoint delay']
        t0 = time.time()
        for idx in self.run_forever.progress(count()):
            time.sleep(delay)
            now = time.time()
            # current = np.mean(self.task.read(samples_per_channel=samples), axis=1)
            current = self.pm100d.power
            values = {
                'idx': idx,
                't': now - t0,
                'y': current,
            }
            self.run_forever.acquire(values)
        return

    @run_forever.initializer
    def initialize(self):
        params = self.input_parameters.widget.get()
        self.pm100d.correction_wavelength = params['wavelength']
        return


    @run_forever.finalizer
    def finalize(self):
        return

    @Element(name='Run controls')
    def run_controls(self):
        w = TaskWidget(self.run_forever)
        return w

    @Element(name='Power Meter Parameters')
    def input_parameters(self):
        params = [
            ('wavelength', {
                'type': float,
                'units': 'nm',
                'nonnegative': True,
                'default': 532,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='run parameters')
    def run_parameters(self):
        params = [
            ('samples', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('interpoint delay', {
                'type': float,
                'default': 0.1,
                'nonnegative': True,
            }),
            ('latest window', {
                'type': int,
                'default': 100,
                'positive': True,
            }),
            ('wavelength', {
                'type': float,
                'units': 'nm',
                'nonnegative': True,
                'default': 532,
            })
        ]
        w = ParamWidget(params)
        return w

    @Element()
    def total_history(self):
        p = LinePlotWidget()
        p.plot('channel 1', symbol=None)
        return p

    @total_history.on(run_forever.acquired)
    def total_history_update(self, ev):
        w = ev.widget
        w.set('channel 1', xs=self.data.t, ys=self.data.y)
        return

    @Element()
    def latest_history(self):
        p = LinePlotWidget()
        p.plot('channel 1', symbol=None)
        return p

    @latest_history.on(run_forever.acquired)
    def latest_history_update(self, ev):
        w = ev.widget
        latest_size = self.run_parameters.widget.get()['latest window']
        w.set('channel 1', xs=self.data.t.tail(latest_size), ys=self.data.y.tail(latest_size))
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w

    # @save.on(run_forever.running)
    def save_requested(self, ev):
        w = ev.widget
        state, = ev.event_args
        if state:
            return
        print(self.dataset.data)
        w.save_dataset(self.dataset)
        return
