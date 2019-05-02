import numpy as np

from itertools import count
import struct
import bisect

from spyre import Task, Element, Spyrelet
from spyre.plotting import LinePlotWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from spyre.spyrelets.spatialfeedback import SpatialFeedbackSpyrelet

from lantz.drivers.picoquant import PH300

def pairwise_difference(a1, a2, dt1, dt2):
    a1 = np.array(a1)
    a2 = np.array(a2)
    delta_ts = list()
    for value in a1:
        start = bisect.bisect_left(a2, value + dt1)
        end = bisect.bisect_left(a2, value + dt2)
        sliced = a2[start:end]
        dts = sliced - value
        delta_ts.extend(dts.tolist())
    return sorted(delta_ts)

class CorrelationSpyrelet(Spyrelet):

    requires = {
        'ph': PH300
    }

    requires_spyrelet = {
        'fb': SpatialFeedbackSpyrelet,
    }

    @Task(name='Correlation')
    def correlation(self):
        self.dataset.clear()
        for iteration in self.correlation.progress(count()):
            if self.feedback and (iteration%self.feedback_period) == 0:
                print(iteration%self.feedback_period)
                print("Running feedback")
                self.fb.feedback()
            self.ph.start_measurement(self.acq_period)
            c1, c2 = self.ph.read_timestamps()
            self.ph.stop_measurement()
            c1 = np.array(c1) / 1e12
            c2 = np.array(c2) / 1e12
            diff = pairwise_difference(c1, c2, -self.diffrange, self.diffrange)
            hist_params = {
                'bins': self.hist_range['num'],
                'range': (self.hist_range['start'].m, self.hist_range['stop'].m),
            }
            hist, bins = np.histogram(np.array(diff), **hist_params)
            self.correlation.acquire({
                'diff': diff,
                'iteration': iteration,
                'correlated': hist,
                'xticks': (bins[1:] + bins[:-1]) / 2,
            })

    @correlation.initializer
    def initialize(self):
        self.ph.set_sync_div(1)
        self.ph.set_input_cfd(0, 30, 0)
        self.ph.set_input_cfd(1, 30, 0)
        self.ph.set_binning(0)
        self.ph.set_offset(0)
        params = self.correlation_parameters.widget.get()
        self.acq_period = params['acquisition period']
        self.diffrange = params['pairwise diff range']
        self.hist_range = params['histogram window']
        self.feedback_period = params['feedback period']
        self.feedback = params['feedback']
        return

    @Element(name='Correlation parameters')
    def correlation_parameters(self):
        params = [
            ('acquisition period', {
                'type': float,
                'default': 1e-3,
                'units': 's',
            }),
            ('pairwise diff range', {
                'type': float,
                'default': 1e-5,
            }),
            ('histogram window', {
                'type': range,
                'default': {
                    'func': 'linspace',
                    'start': -1e-5,
                    'stop': 1e-5,
                    'num': 200,
                },
            }),
            ('feedback', {
                'type': bool,
                'default': True,
            }),
            ('feedback period', {
                'type': int,
                'default': 3.6e6,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='average correlation')
    def avg_correlation(self):
        p = LinePlotWidget()
        p.xlabel = 'detection time difference (s)'
        p.ylabel = 'counts'
        p.plot('correlation', pen=None)
        return p

    @avg_correlation.on(correlation.acquired)
    def update_avg_correlation(self, ev):
        p = ev.widget
        latest = self.data.tail(1)
        if len(self.data) <= 1:
            self.avg_corr = latest.correlated.values[0]
            self.avg_n = 1
        else:
            new_val = latest.correlated.values[0]
            self.avg_corr = (self.avg_corr*self.avg_n + new_val)/(self.avg_n+1)
            self.avg_n += 1
        dts = latest.xticks.values[0]
        p.set('correlation', xs=dts, ys=self.avg_corr)
        return

    @Element(name='total correlation')
    def total_correlation(self):
        p = LinePlotWidget()
        p.xlabel = 'detection time difference (s)'
        p.ylabel = 'counts'
        p.plot('correlation', pen=None)
        return p

    @total_correlation.on(correlation.acquired)
    def update_total_correlation(self, ev):
        p = ev.widget
        latest = self.data.tail(1)
        if len(self.data) <= 1:
            self.total_corr = latest.correlated.values[0]
        else:
            self.total_corr += latest.correlated.values[0]
        dts = latest.xticks.values[0]
        p.set('correlation', xs=dts, ys=self.total_corr)
        return

    @Element(name='latest correlation')
    def latest_correlation(self):
        p = LinePlotWidget()
        p.xlabel = 'detection time difference (s)'
        p.ylabel = 'counts'
        p.plot('correlation', pen=None)
        return p

    @latest_correlation.on(correlation.acquired)
    def update_latest_correlation(self, ev):
        p = ev.widget
        latest = self.data.tail(1)
        dts = latest.xticks.values[0]
        corr = latest.correlated.values[0]
        p.set('correlation', xs=dts, ys=corr)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
