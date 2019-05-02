import numpy as np
import pyqtgraph as pg
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
from lantz.drivers.ni.daqmx import DigitalInputTask, DigitalInputChannel
from lantz.drivers.ni.daqmx import DigitalOutputTask, DigitalOutputChannel

class CountsVsFrequencySpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'daq': Device,
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        for sweep in range(params['sweeps']):
            for f in self.sweep.progress(params['frequency'].array):
                self.sg.frequency = f
                ctrs_start = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in self.ctr_tasks])
                time.sleep(params['interpoint delay'])
                ctrs_end = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in self.ctr_tasks])
                dctrs = ctrs_end - ctrs_start
                ctrs_rates = dctrs[:,0] / dctrs[:,1]
                values = {
                    'sweep_idx': sweep,
                    'f': f,
                    'x': ctrs_rates[0],
                    'y': ctrs_rates[1],
                }

                self.sweep.acquire(values)

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.sg.rf_amplitude = params['rf amplitude']
        self.sg.rf_toggle = True
        self.sg.mod_toggle = False

        self.sample_freq = 1e5

        # self.di_task = DigitalInputTask('dummy_trigger')
        # trig_ch = '/dev1/port0/line31'
        # self.di_task.add_channel(DigitalInputChannel(trig_ch))
        #
        # di_sample_clock = '/dev1/di/SampleClock'
        # clock_config = {
        #     'rate': self.sample_freq,
        #     'sample_mode': 'continuous',
        # }
        # self.di_task.configure_timing_sample_clock(**clock_config)
        #
        # do_trigger_src = '/dev1/pfi15'
        # self.di_task.configure_trigger_digital_edge_start(do_trigger_src,
        #                                                   edge='falling')
        # self.do_task = DigitalOutputTask('starter')
        # starter_ch = '/dev1/pfi15'
        # self.do_task.add_channel(DigitalOutputChannel(starter_ch))

        ctrs = [params['counter 1'], params['counter 2']]
        if len(set(ctrs)) != len(ctrs):
            raise RuntimeError('counter channels 1 and 2 must be different')
        self.ctr_tasks = list()
        for idx, ctr in enumerate(ctrs):
            task = CounterInputTask('counter ch {}'.format(idx))
            ch = CountEdgesChannel(ctr)
            task.add_channel(ch)
            # config = {
            #     'source': 'OnboardClock',
            #     'sample_mode': 'finite',
            # }
            # task.configure_timing_sample_clock(**config)
            # task.arm_start_trigger_source = '/dev1/pfi15'
            # task.arm_start_trigger_type = 'digital_edge'
            task.start()
            self.ctr_tasks.append(task)
        # self.di_task.start()
        # self.do_task.start()
        # data = [0, 1, 0]
        # self.do_task.write(data)
        return

    @sweep.finalizer
    def finalize(self):
        self.sg.rf_toggle = False
        # self.di_task.clear()
        # self.do_task.clear()
        for ctr_task in self.ctr_tasks:
            ctr_task.clear()
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
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
            ('frequency', {
                'type': range,
                'units':'GHz',
            }),
            ('rf amplitude', {
                'type': float,
                'default': -20,
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('interpoint delay', {
                'type': float,
                'default': 1,
                'nonnegative': True,
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

    @Element(name='Differential counts (latest)')
    def diff_latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1-2')
        return p

    @diff_latest.on(sweep.acquired)
    def diff_latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        diff = latest_data.x - latest_data.y
        w.set('Channel 1-2', xs=latest_data.f, ys=diff)
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

    @Element(name='Differential counts (averaged)')
    def diff_average(self):
        p = LinePlotWidget()
        p.plot('Channel 1-2')
        return p

    @diff_average.on(sweep.acquired)
    def diff_average_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('f')
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
