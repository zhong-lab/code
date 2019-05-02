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

from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel

class TaskVsTimeSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
    }

    @Task()
    def run_forever(self, **kwargs):
        self.dataset.clear()
        run_params = self.run_parameters.widget.get()
        samples = run_params['samples']
        delay = run_params['interpoint delay']
        if self.task.IO_TYPE == 'AI':
            t0 = time.time()
            for idx in self.run_forever.progress(count()):
                time.sleep(delay)
                now = time.time()
                current = np.mean(self.task.read(samples_per_channel=samples), axis=1)
                values = {
                    'idx': idx,
                    't': now - t0,
                    'y': current,
                }
                self.run_forever.acquire(values)
        elif self.task.IO_TYPE == 'CI':
            t0 = time.time()
            prev = self.task.read(samples_per_channel=samples)[-1]
            prev_t = t0
            for idx in self.run_forever.progress(count()):
                time.sleep(delay)
                now = time.time()
                current = self.task.read(samples_per_channel=samples)[-1]
                count_rate = (current - prev) / (now - prev_t)
                prev = current

                prev_t = now
                values = {
                    'idx': idx,
                    't': now - t0,
                    'y': count_rate,
                }
                self.run_forever.acquire(values)
        else:
            # should never get here
            pass
        return

    @run_forever.initializer
    def initialize(self):
        params = self.run_parameters.widget.get()
        inp_ch = params['channel']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('TaskVsTime_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('TaskVsTime_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
        else:
            # should never get here
            pass
        self.task.start()
        return


    @run_forever.finalizer
    def finalize(self):
        self.task.clear()
        return


    @Element(name='Run parameters')
    def run_parameters(self):
        params = [
            ('channel', {
                'type': list,
                'items': list(self.daq.counter_input_channels)+list(self.daq.analog_input_channels),
            }),

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
            })
        ]
        w = ParamWidget(params)
        return w

    @Element()
    def total_history(self):
        p = LinePlotWidget()
        p.plot('Signal', symbol=None)
        return p

    @total_history.on(run_forever.acquired)
    def total_history_update(self, ev):
        w = ev.widget
        w.set('Signal', xs=self.data.t, ys=self.data.y)
        return

    @Element()
    def latest_history(self):
        p = LinePlotWidget()
        p.plot('Signal', symbol=None)
        return p

    @latest_history.on(run_forever.acquired)
    def latest_history_update(self, ev):
        w = ev.widget
        latest_size = self.run_parameters.widget.get()['latest window']
        w.set('Signal', xs=self.data.t.tail(latest_size), ys=self.data.y.tail(latest_size))
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
