from PyQt5 import QtWidgets
import pyqtgraph as pg

import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.stanford import SG396
from lantz.drivers.signalrecovery import SR7265
from lantz.drivers.photonetc import PhotonEtcFilter
from lantz.drivers.thorlabs.pm100d import PM100D

from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel

from lantz import Q_



class TaskvsWavelengthSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        samples = params['samples']
        delay = params['interpoint delay']

        for sweep in range(params['sweeps']):

            for wavelength in params['excitation'].array:

                self.lltf.wavelength[params['filter_name']] = wavelength


                if self.task.IO_TYPE == 'AI':
                    t0 = time.time()

                    time.sleep(delay)
                    now = time.time()
                    current = np.mean(self.task.read(samples_per_channel=samples), axis=1)[0]

                    values = {
                        'sweep_idx': sweep,
                        'wavelength': wavelength,
                        'y': current,
                    }

                    self.sweep.acquire(values)

                elif self.task.IO_TYPE == 'CI':
                    t0 = time.time()
                    prev = self.task.read(samples_per_channel=samples)[-1]
                    prev_t = t0

                    time.sleep(delay)
                    now = time.time()
                    current = self.task.read(samples_per_channel=samples)[-1]
                    count_rate = (current - prev) / (now - prev_t)

                    values = {
                        'sweep_idx': sweep,
                        'wavelength': wavelength,
                        'y': count_rate,
                    }

                    self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        inp_ch = params['channel']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('TaskVsTime_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('TaskVsTime_AI')
            channel = VoltageInputChannel(inp_ch, terminal='rse')
            self.task.add_channel(channel)
        else:
            # should never get here
            pass
        self.task.start()
        return

    @sweep.finalizer
    def finalize(self):
        self.task.clear()
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('channel', {
                'type': list,
                'items': list(self.daq.counter_input_channels)+list(self.daq.analog_input_channels),
                'default': 'Dev1/ai0',
            }),
            ('excitation', {
                'type': range,
                'units': 'm',
                'default': {'func': 'linspace',
                            'start': 850.0e-9,
                            'stop': 1050.0e-9,
                            'num': 50}
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('filter_name', {
                'type': list,
                'items': list(self.lltf.filters.keys())
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
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest counts versus frequency')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        w.set('Channel 1', xs=latest_data.wavelength, ys=latest_data.y)
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
        grouped = self.data.groupby('wavelength')
        ys = grouped.y
        ys_averaged = ys.mean()
        w.set('Channel 1', xs=ys_averaged.index, ys=ys_averaged, yerrs=ys.std())
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w




class ODMRvsWavelengthSpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'lockin': SR7265,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        time_const_in_sec = Q_(params['time_const']).to('s').magnitude
        self.lockin.time_constant = params['time_const']

        #self.sg.f = params['frequency']

        def get_xy():
            time.sleep(time_const_in_sec/2)
            return float(self.lockin.xy)
        for sweep in range(params['sweeps']):
            for wavelength in params['excitation'].array:
                self.lltf.wavelength[params['filter_name']] = wavelength
                time.sleep(time_const_in_sec*3)
                xys = [get_xy() for _ in range(params['lockin_pts'])]
                xs, ys = zip(*xys)
                values = {
                    'sweep_idx': sweep,
                    'wavelength': wavelength,
                    'x': np.mean(xs),
                    'y': np.mean(ys),
                }
                self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        self.sg.rf_amplitude = params['sg_power']
        self.sg.mod_toggle = params['mod_toggle']
        self.sg.rf_toggle = True
        return

    @sweep.finalizer
    def finalize(self):
        self.sg.rf_toggle = False
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('excitation', {
                'type': range,
                'units': 'm',
                'default': {'func': 'linspace',
                            'start': 850.0e-9,
                            'stop': 1050.0e-9,
                            'num': 50}
            }),
            ('frequency', {
                'type': float,
                'units': 'Hz',
                'default': 2.87e9,
                'positive': True,
            }),
            ('lockin_pts', {
                'type': int,
                'default': 30,
                'positive': True,
            }),
            ('sg_power', {
                'type': float,
                'default': -30,
                'suffix':' dBm'
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('time_const', {
                'type': list,
                'items': list(self.lockin.TIME_CONSTANTS.keys()),
            }),
            ('mod_toggle', {
                'type': bool,
                'default': True,
            }),
            ('filter_name', {
                'type': list,
                'items': list(self.lltf.filters.keys())
            })
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
        w.set('Channel 1', xs=latest_data.wavelength, ys=latest_data.x)
        w.set('Channel 2', xs=latest_data.wavelength, ys=latest_data.y)
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
        grouped = self.data.groupby('wavelength')
        xs = grouped.x
        ys = grouped.y
        xs_averaged = xs.mean()
        ys_averaged = ys.mean()
        w.set('Channel 1', xs=xs_averaged.index, ys=xs_averaged, yerrs=xs.std())
        w.set('Channel 2', xs=ys_averaged.index, ys=ys_averaged, yerrs=ys.std())
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w



class ODMRvsWavelength2DSpyrelet(Spyrelet):

    requires = {
        'sg': SG396,
        'lockin': SR7265,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def scan(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()
        time_const_in_sec = Q_(params['time_const']).to('s').magnitude
        self.lockin.time_constant = params['time_const']

        def get_xy():
            time.sleep(time_const_in_sec/2)
            return self.lockin.xy


        for sweep in range(params['sweeps']):

            for col_idx, wavelength in enumerate(params['excitation'].array):

                self.lltf.wavelength[params['filter_name']] = wavelength

                xfs = np.empty(params['frequency'].array.shape)
                yfs = np.empty(xfs.shape)


                for row_idx, f in enumerate(params['frequency'].array):

                    self.sg.f = f

                    time.sleep(time_const_in_sec*3)

                    xys = [get_xy() for _ in range(params['lockin_pts'])]
                    xs, ys = zip(*xys)
                    # values = {
                    #     'sweep_idx': sweep,
                    #     'wavelength': wavelength,
                    #     'x': np.mean(xs),
                    #     'y': np.mean(ys),
                    # }

                    xfs[row_idx] = np.mean(xs)
                    yfs[row_idx] = np.mean(ys)
                    # TODO: figure out how to handle acquire routine, may need to do this a level up

                    # this could be used to run a single line sweep plotting within larger 2D scan
                    #self.sweep.acquire(values)


                values = {
                    'sweep_idx': sweep,
                    'col_idx': col_idx,
                    'excitation': self.lltf.wavelength[params['filter_name']],
                    'frequency': params['frequency'].array,
                    'x': xfs,
                    'y': yfs,
                }

                self.scan.acquire(values)

        return

    @scan.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()

        self.max_rows = len(params['excitation'].array.to('nm').m)
        x_range = params['frequency'].array.to('MHz').m
        y_range = params['excitation'].array.to('nm').m
        x_diff = x_range[-1] - x_range[0]
        y_diff = y_range[-1] - y_range[0]
        pos = np.mean(x_range) - x_diff / 2.0, np.mean(y_range) - y_diff / 2.0
        scale = x_diff / len(x_range), y_diff / len(y_range)
        im_pos = [v for v in pos]
        im_scale = [v for v in scale]

        print(im_pos)
        print(im_scale)

        self.latest_scan.widget.im_pos = im_pos
        self.latest_scan.widget.im_scale = im_scale
        self.averaged_scan.widget.im_pos = im_pos
        self.averaged_scan.widget.im_scale = im_scale

        return

    @scan.finalizer
    def finalize(self):
        return

    @Element(name='Scan parameters')
    def sweep_parameters(self):
        params = [
            ('frequency', {
                'type': range,
                'units': 'GHz',
                'default': {'func': 'linspace',
                            'start': 1.0e9,
                            'stop': 1.2e9,
                            'num': 50}
            }),
            ('lockin_pts', {
                'type': int,
                'default': 30,
                'positive': True,
            }),
            ('sg_power', {
                'type': float,
                'default': -30,
                'suffix':' dBm'
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
            ('time_const', {
                'type': list,
                'items': list(self.lockin.TIME_CONSTANTS.keys()),
            }),
            ('mod_toggle', {
                'type': bool,
                'default': True,
            }),
            ('excitation', {
                'type': range,
                'units': 'm',
                'default': {'func': 'linspace',
                            'start': 850.0e-9,
                            'stop': 1050.0e-9,
                            'num': 50}
            }),
            ('filter_name', {
                'type': list,
                'items': list(self.lltf.filters.keys())
            })
        ]
        w = ParamWidget(params)
        return w

    @Element()
    def latest_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'Frequency (MHz)'
        w.ylabel = 'Excitation (nm)'

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @latest_scan.on(scan.acquired)
    def update_latest_scan(self, ev):
        latest = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        im = np.vstack(latest.sort_values('excitation')['x'])
        #im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)
        ev.widget.set(im)#, pos=self.pos, scale=self.scale)

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return

    @Element()
    def averaged_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'Frequency (MHz)'
        w.ylabel = 'Excitation (nm)'

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @averaged_scan.on(scan.acquired)
    def update_averaged_scan(self, ev):
        grouped = self.data.groupby('excitation')['x']
        averaged = grouped.apply(lambda column: np.mean(np.vstack(column), axis=0))
        im = np.vstack(averaged)
        #im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)

        ev.widget.set(im)#, pos=self.pos, scale=self.scale)
        return


    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w



class PMvsWavelengthSpyrelet(Spyrelet):

    requires = {
        'pm100d': PM100D,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        samples = params['samples']
        delay = params['interpoint delay']

        for sweep in range(params['sweeps']):

            for wavelength in params['excitation'].array:

                self.lltf.wavelength[params['filter_name']] = wavelength
                self.pm100d.correction_wavelength = wavelength

                def read_power():
                    time.sleep(delay)
                    return self.pm100d.power.magnitude

                power = np.fromiter((read_power() for s in range(samples)), float)

                values = {
                    'sweep_idx': sweep,
                    'wavelength': wavelength,
                    'y': np.mean(power),
                }

                self.sweep.acquire(values)
        return

    @sweep.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()
        return

    @sweep.finalizer
    def finalize(self):

        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('excitation', {
                'type': range,
                'units': 'm',
                'default': {'func': 'linspace',
                            'start': 850.0e-9,
                            'stop': 1050.0e-9,
                            'num': 50}
            }),
            ('filter_name', {
                'type': list,
                'items': list(self.lltf.filters.keys())
            }),
            ('sweeps', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('samples', {
                'type': int,
                'default': 2,
                'positive': True,
            }),
            ('interpoint delay', {
                'type': float,
                'default': 0.1,
                'nonnegative': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest power versus wavelength')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.xlabel = 'Wavelength (nm)'
        p.ylabel = 'Power (W)'
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        w.set('Channel 1', xs=latest_data.wavelength, ys=latest_data.y)
        return

    @Element(name='Averaged power vs wavelength')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        p.xlabel = 'Wavelength (nm)'
        p.ylabel = 'Power (W)'
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        grouped = self.data.groupby('wavelength')
        ys = grouped.y
        ys_averaged = ys.mean()
        w.set('Channel 1', xs=ys_averaged.index, ys=ys_averaged, yerrs=ys.std())
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
