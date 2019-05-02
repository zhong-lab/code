import time
import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from spyre.plotting import LinePlotWidget

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.toptica import DLC

from spyre.spyrelets.fabryperot import FabryPerotSpyrelet

import cma

class CTROptimizeSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'dlc': DLC,
    }

    requires_spyrelet = {
        'fp': FabryPerotSpyrelet,
    }


    @Task(name='Optimize CTR')
    def optimize(self):

        initial_current = Q_(250, 'mA')
        initial_ff = Q_(-1.5, 'mA / V')

        def f(x):
            current, ff = x
            # print(current * self.current_scaling, ff)
            self.dlc.current = Q_(current * self.current_scaling, 'mA')
            self.dlc.feedforward_factor = Q_(ff, 'mA / V')
            time.sleep(5 / 110)
            self.fp.single_readout(selectivity=0.05)
            peak_mags = self.fp.fp.peak_magnitudes
            sq_err = np.sum(np.square(1 - peak_mags))
            return sq_err

        x0 = [
            (initial_current / self.current_scaling).to('mA').m,
            initial_ff.to('mA / V').m,
        ]
        sigma0 = 0.1
        cmaopts = {
            'tolfun': 1e-3,
            'tolx': 1e-2,
            'maxfevals': 100,
            'bounds': [
                (200 / self.current_scaling, -2.3),
                (280 / self.current_scaling, -1.0),
            ],
        }

        for retry_idx in range(self.max_retries):
            # print(retry_idx)
            self.toggle_scan(True)
            result = cma.fmin(f, x0, sigma0, options=cmaopts)
            xopt = result[0]
            f(xopt)
            self.fp.single_readout(selectivity=0.05)
            peak_mags = self.fp.fp.peak_magnitudes
            restart = False
            if len(peak_mags) > self.peak_threshold:
                restart = True
            ssr = np.sum(np.square(1 - peak_mags))
            if ssr > self.ssr_threshold:
                restart = True
            if not restart:
                break
        self.toggle_scan(False)
        return

    @optimize.initializer
    def initialize(self):
        fp_params = {
            'Fabry-Perot acquisition points': 5000,
        }
        self.fp.readout_params.widget.set(**fp_params)
        params = self.opt_params.widget.get()
        self.ctr_pp = params['peak to peak ctr']
        self.dlc.piezo_external_input_factor = self.ctr_pp.to('V').m
        self.current_scaling = params['current scaling'].to('mA').m
        self.ff_scaling = params['ff scaling'].to('mA / V').m
        self.max_retries = params['max retries']
        self.ssr_threshold = params['ssr threshold']
        self.peak_threshold = params['peak number threshold']
        return

    @optimize.finalizer
    def finalize(self):
        self.toggle_scan(False)
        return

    def toggle_scan(self, scan_enabled):
        fp_params = {
            'active acquisition mode': not scan_enabled,
        }
        self.fp.readout_params.widget.set(**fp_params)
        self.fp.single_readout()

        self.dlc.scan_enabled = scan_enabled
        self.dlc.piezo_external_input_enabled = scan_enabled
        return

    @Element(name="Optimization parameters")
    def opt_params(self):
        params = [
            ('peak to peak ctr', {
                'type': float,
                'units': 'V',
                'default': 100,
            }),
            ('current scaling', {
                'type': float,
                'units': 'mA',
                'default': 50e-3,
            }),
            ('ff scaling', {
                'type': float,
                'units': 'mA / V',
                'default': 50e-3,
            }),
            ('max retries', {
                'type': int,
                'nonnegative': True,
                'default': 2,
            }),
            ('ssr threshold', {
                'type': float,
                'default': 1.1,
            }),
            ('peak number threshold', {
                'type': int,
                'default': 30,
            }),
        ]
        w = ParamWidget(params)
        return w
