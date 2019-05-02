import numpy as np
import time

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel
from lantz.drivers.toptica import DLC, MotDLpro
from lantz.drivers.bristol import Bristol671

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.repository_widget import RepositoryWidget
from spyre.plotting import LinePlotWidget

from spyre.spyrelets.gotofrequency import GotoFrequencySpyrelet
from spyre.spyrelets.fabryperot import FabryPerotSpyrelet

class TaskVsLaserFrequencySpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'dlc': DLC,
        'mot': MotDLpro,
        'wvm': Bristol671,
    }

    requires_spyrelet = {
        'goto': GotoFrequencySpyrelet,
        'fp': FabryPerotSpyrelet,
    }

    @Task(name='Scan')
    def scan(self, **kwargs):

        def acquire(scan_f, piezo_v):
            amplitude = self.read()
            values = {
                'f': scan_f.to('GHz').m,
                'piezo_v': piezo_v.to('V').m,
                'amplitude': amplitude,
            }
            self.scan.acquire(values)
            return

        fmin, fmax = np.min(self.frequencies), np.max(self.frequencies)
        scan_lower_bounds = Q_(np.arange(fmin.to('GHz').m, fmax.to('GHz').m, self.mhf_scan_size.to('GHz').m), 'GHz')
        for sb_low in self.scan.progress(scan_lower_bounds):
            sb_high = sb_low + self.mhf_scan_size
            sb_target = (sb_low + sb_high) / 2
            goto_params = {
                'target frequency': sb_target.to('Hz').m,
                'run CTR optimizer': True,
                'feedback period':0,
            }
            self.goto.target_parameters.widget.set(**goto_params)
            self.goto.goto_frequency()

            scan_fs = self.frequencies[(sb_low <= self.frequencies) & (self.frequencies < sb_high)]
            self.stabilized_scan(scan_fs, callback=acquire)
        return

    def stabilized_scan(self, scan_frequencies, callback=None):
        fp_params = {
            'active acquisition mode': True,
        }
        self.fp.readout_params.widget.set(**fp_params)
        for scan_f in scan_frequencies:
            piezo_voltage = self.dlc.piezo_voltage
            for iteration in range(self.stabilization_iterations):
                df = self.wvm.frequency - scan_f
                if abs(df) < self.stabilization_tolerance:
                    break
                dpiezo = self.p * df
                piezo_voltage -= dpiezo
                self.dlc.piezo_voltage = piezo_voltage
                time.sleep(abs(dpiezo).to('V').m / 100)
            else:
                continue
            self.fp.single_readout(selectivity=self.selectivity)
            if self.fp.fp.single_mode:
                callback(scan_f, piezo_voltage)
        return


    @scan.initializer
    def initialize(self):
        self.dataset.clear()
        params = self.parameters.widget.get()
        inp_ch = params['acquisition channel']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('TaskVsLaserFrequency_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
            self.read = self.ci_read
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('TaskVsLaserFrequency_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
            self.read = self.ai_read
        else:
            pass
        self.task.start()
        self.frequencies = params['frequencies'].array
        self.mhf_scan_size = params['MHF scan size']
        self.currents = params['current sweep range'].array
        self.ffs = params['feedforward factor sweep range'].array
        self.selectivity = params['fabry-perot selectivity']
        self.interpoint_delay = params['interpoint delay']
        self.stabilization_iterations = params['stabilization iterations']
        self.stabilization_tolerance = params['stabilization tolerance']
        self.p = params['piezo-frequency factor']
        self.sweep_iterations = params['sweep iterations']
        return

    @scan.finalizer
    def finalize(self):
        self.task.clear()
        return

    def ci_read(self):
        t0 = time.time()
        cts0 = self.task.read(samples_per_channel=1)[0]
        time.sleep(self.interpoint_delay)
        t1 = time.time()
        cts1 = self.task.read(samples_per_channel=1)[0]
        cps = (cts1 - cts0) / (t1 - t0)
        return cps

    def ai_read(self):
        amplitude = np.mean(self.task.read(samples_per_channel=1000))
        return amplitude


    @Element(name='Scan parameters')
    def parameters(self):
        ci_channels = list(self.daq.counter_input_channels)
        ai_channels = list(self.daq.analog_input_channels)
        all_channels = ci_channels + ai_channels
        params = [
            ('acquisition channel', {
                'type': list,
                'items': all_channels,
                'default': 'Dev1/ctr2',
            }),
            ('frequencies', {
                'type': range,
                'units': 'GHz',
                'default': {
                    'func': 'linspace',
                    'start': 264.91e12,
                    'stop': 265.31e12,
                    'num': 200,
                },
            }),
            ('MHF scan size', {
                'type': float,
                'units': 'GHz',
                'default': 20e9,
            }),
            ('current sweep range', {
                'type': range,
                'units': 'mA',
                'default': {
                    'func': 'linspace',
                    'start': 220e-3,
                    'stop': 270e-3,
                    'num': 50,
                    'endpoint': False,
                },
            }),
            ('feedforward factor sweep range', {
                'type': range,
                'units': 'mA/V',
                'default': {
                    'func': 'linspace',
                    'start': -0.8e-3,
                    'stop': -2.5e-3,
                    'num': 50,
                    'endpoint': False,
                },
            }),
            ('fabry-perot selectivity', {
                'type': float,
                'nonnegative': True,
                'default': 0.1,
            }),
            ('interpoint delay', {
                'type': float,
                'nonnegative': True,
                'default': 1.0,
            }),
            ('stabilization iterations', {
                'type': int,
                'nonnegative': True,
                'default': 10,
            }),
            ('stabilization tolerance', {
                'type': float,
                'units': 'MHz',
                'default': 50e6,
            }),
            ('piezo-frequency factor', {
                'type': float,
                'units': 'V/GHz',
                'default': 2e-9,
            }),
            ('sweep iterations', {
                'type': int,
                'nonnegative': True,
                'default': 1,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Averaged scan points')
    def averaged_scan_points(self):
        p = LinePlotWidget()
        p.plot('channel amplitude', pen=None)
        return p

    @averaged_scan_points.on(scan.acquired)
    def averaged_scan_points_update(self, ev):
        w = ev.widget
        w.set('channel amplitude', xs=self.data.f, ys=self.data.amplitude)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
