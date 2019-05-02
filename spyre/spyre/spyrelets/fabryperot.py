import numpy as np
from itertools import count
import time

from spyre import Spyrelet, Task, Element
from spyre.plotting import LinePlotWidget
from spyre.widgets.task import TaskWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.utils.doswitch import DigitalSwitch

import pyqtgraph as pg

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel

def peakdet(arr, delta=0.1):
    mintab, maxtab = list(), list()
    arr = np.asarray(arr)
    x = np.arange(len(arr))
    if delta <= 0:
        return maxtab, mintab
    mn, mx = np.Inf, -np.Inf
    mnpos, mxpos = np.NaN, np.NaN
    lookformax = True
    for idx in range(len(arr)):
        this = arr[idx]
        if this > mx:
            mx = this
            mxpos = x[idx]
        if this < mn:
            mn = this
            mnpos = x[idx]
        if lookformax:
            if this < mx - delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[idx]
                lookformax = False
        else:
            if this > mn + delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[idx]
                lookformax = True
    return np.array(maxtab), np.array(mintab)

class FabryPerot(object):

    def __init__(self, fp_ch, trig_ch, fp_points=1000, fp_period=Q_(10, 'ms')):
        self.acq_task = AnalogInputTask('fp_readout')
        self.acq_task.add_channel(VoltageInputChannel(fp_ch))
        self.acq_task.configure_trigger_digital_edge_start(trig_ch, edge='rising')

        rate = fp_points / fp_period
        self.fp_points = fp_points
        self.fp_period = fp_period
        clock_config = {
            'source': 'OnboardClock',
            'rate': rate.to('Hz').magnitude,
            'sample_mode': 'finite',
            'samples_per_channel': fp_points,
        }
        self.acq_task.configure_timing_sample_clock(**clock_config)

        self._single_mode = True
        self._peak_locations = list()
        self._trace = np.zeros(self.fp_points)
        return

    @property
    def single_mode(self):
        return self._single_mode

    @property
    def peak_locations(self):
        return self._peak_locations

    @property
    def peak_magnitudes(self):
        return self._peak_magnitudes

    @property
    def trace(self):
        return self._trace

    def refresh(self, selectivity=0.3, xvar=0.1, yvar=0.1):
        self.acq_task.start()
        data = self.acq_task.read(samples_per_channel=self.fp_points).flatten()
        self.acq_task.stop()
        data = data.flatten()

        # remove spurious edge signals
        display_data = data
        data = data[10:-10]

        # normalize signal
        data /= np.max(data)
        peak_info, valley_info = peakdet(data, delta=selectivity)
        if not peak_info.size:
            self._single_mode = False
            self._peak_locations = list()
            self._trace = np.zeros(self.fp_points)
            return
        peak_locations = peak_info[:,0]
        peak_magnitudes = peak_info[:,1]

        # normalize peak magnitudes
        peak_magnitudes /= np.max(peak_magnitudes)

        filtered_locations = list()
        for peak_location in peak_locations:
            if np.sum(np.abs(peak_locations - peak_location) > xvar * len(peak_locations)):
                filtered_locations.append(peak_location)
        peak_locations = np.array(filtered_locations)
        peaks = len(peak_locations)
        self._single_mode = 1 < peaks < 4 and np.var(peak_magnitudes) < yvar
        self._peak_locations = peak_locations
        self._peak_magnitudes = peak_magnitudes
        self._trace = display_data
        return

    def finalize(self):
        self.acq_task.clear()
        return

class FabryPerotSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
    }

    @Task()
    def continuous_readout(self):
        self.dataset.clear()
        for idx in self.continuous_readout.progress(count()):
            self.fp.refresh()
            now = time.time()
            trace = self.fp.trace
            single_mode = self.fp.single_mode
            peak_locations = self.fp.peak_locations
            values = {
                'idx': idx,
                't': now,
                'trace': trace,
                'single_mode': single_mode,
                'peak_locations': peak_locations,
            }
            self.continuous_readout.acquire(values)
        return

    @Task()
    def single_readout(self, **kwargs):
        selectivity = kwargs.get('selectivity', 0.3)
        self.dataset.clear()
        self.fp.refresh(selectivity=selectivity)
        trace = self.fp.trace
        single_mode = self.fp.single_mode
        peak_locations = self.fp.peak_locations

        values = {
            'idx': 0,
            't': time.time(),
            'trace': trace,
            'single_mode': single_mode,
            'peak_locations': peak_locations,
        }
        self.single_readout.acquire(values)

    @single_readout.initializer
    @continuous_readout.initializer
    def initialize(self):
        self.params = self.readout_params.widget.get()
        fp_ch = self.params['Fabry-Perot channel']
        # trig_ch = self.params['trigger channel']
        trig_ch = '/dev1/pfi4'
        active_mode = self.params['active acquisition mode']
        fp_points = self.params['Fabry-Perot acquisition points']
        fp_period = self.params['Fabry-Perot acquisition period']
        active_mode_switch = DigitalSwitch()
        active_mode_switch.state = active_mode
        self.fp = FabryPerot(fp_ch, trig_ch, fp_points, Q_(fp_period, 'ms'))
        self.ts = np.linspace(0, fp_period, fp_points)
        return

    @Task()
    def mhftr_maximize(self):
        self.dataset.clear()
        for idx in self.mhftr_maximize.progress(count()):
            self.task.start()
            # data = self.task.read(samples_per_channel=10000, timeout=Q_(5, 's'))
            data = self.task.read(samples_per_channel=1000, timeout=5)
            self.task.stop()
            piezo_values = data[0]
            pd_values = data[1]
            norm_piezo_values = 1 - (piezo_values - np.min(piezo_values)) / (np.max(piezo_values) - np.min(piezo_values))
            norm_pd_values = (pd_values - np.min(pd_values)) / (np.max(pd_values) - np.min(pd_values))
            values = {
                'idx': idx,
                'piezos': norm_piezo_values,
                'pds': norm_pd_values,
                'trace': data[2],
            }
            self.mhftr_maximize.acquire(values)

        return


    @mhftr_maximize.initializer
    def initialize(self):
        piezo_ch = '/dev1/ai20'
        pd_ch = '/dev1/ai22'
        fp_ch = '/dev1/ai21'
        trig_ch = '/dev1/pfi7'

        task = AnalogInputTask('mhftr_maximizer')
        task.add_channel(VoltageInputChannel(piezo_ch))
        task.add_channel(VoltageInputChannel(pd_ch))
        task.add_channel(VoltageInputChannel(fp_ch))
        task.configure_trigger_digital_edge_start(trig_ch, edge='rising')

        sweep_rate = 110
        points = 1000
        sweeps = 1

        acq_rate = points * sweep_rate / sweeps

        clock_config = {
            'source': 'OnboardClock',
            'rate': acq_rate,
            'sample_mode': 'finite',
            'samples_per_channel': points,
        }

        task.configure_timing_sample_clock(**clock_config)
        self.task = task
        self.ts = np.linspace(0, 1, points)
        return

    @mhftr_maximize.finalizer
    def finalize(self):
        self.task.clear()
        return




    @single_readout.finalizer
    @continuous_readout.finalizer
    def finalize(self):
        self.fp.finalize()
        return

    @Element()
    def fp_trace(self):
        p = LinePlotWidget()
        p.plot('Fabry-Perot trace', symbol=None)
        return p

    @fp_trace.on(single_readout.acquired)
    @fp_trace.on(continuous_readout.acquired)
    @fp_trace.on(mhftr_maximize.acquired)
    def fp_trace_update(self, ev):
        w = ev.widget
        w.set('Fabry-Perot trace', xs=self.ts, ys=self.data.tail(1).trace.values[0])
        return

    @Element()
    def mhftr_maximize_traces(self):
        p = LinePlotWidget()
        p.plot('Piezo trace', symbol=None)
        p.plot('PD trace', symbol=None)
        return p

    @mhftr_maximize_traces.on(mhftr_maximize.acquired)
    def mhftr_maximize_traces_update(self, ev):
        w = ev.widget
        piezos = self.data.tail(1).piezos.values[0]
        pds = self.data.tail(1).pds.values[0]
        w.set('Piezo trace', xs=self.ts, ys=piezos)
        w.set('PD trace', xs=self.ts, ys=pds)
        return

    @Element()
    def readout_params(self):
        params = [
            ('Fabry-Perot channel', {
                'type': list,
                'items': list(self.daq.analog_input_channels),
                'default':'Dev1/ai21',
            }),
            ('trigger channel', {
                'type': list,
                'items': list(self.daq.digital_input_lines),
                # 'default': '/dev1/pfi3'
            }),
            ('active acquisition mode', {
                'type': bool,
                'default': True,
            }),
            ('Fabry-Perot acquisition points', {
                'type': int,
                'default': 1000,
                'positive': True,
            }),
            ('Fabry-Perot acquisition period', {
                'type': float,
                'default': 10.0,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w
