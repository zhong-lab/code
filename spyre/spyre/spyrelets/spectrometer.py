from PyQt5 import QtWidgets
import pyqtgraph as pg

import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.plotting import HeatmapPlotWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments.lightfield import Spectrometer
from lantz.drivers.photonetc.lltf import PhotonEtcFilter
from lantz import Q_


class SpectroscopySpyrelet(Spyrelet):

    requires = {
        'spectro': Spectrometer,
        'lltf': PhotonEtcFilter
    }

    def set_up_measurement(self, **kwargs):

        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        # set up tunable filter
        self.lltf.wavelength[params['filter_name']] = params['excitation']

        # set up spectrometer
        self.spectro.num_frames = params['num_frames']
        self.spectro.center_wavelength = params['center_wavelength']
        self.spectro.integration_time = params['integration_time']

        if params['temp_lock']:

            print('Checking for temperature lock...')

            def setpoint_check(reset_wait=1, tolerance=0.1):

                setpoint = self.spectro.sensor_setpoint

                while abs(setpoint - self.spectro.sensor_temperature) > tolerance:

                    print('Temperature not reached...')
                    time.sleep(reset_wait)


                print('Temperature stabilized')


            setpoint_check()


        # TODO: figure out how to correct background here
        if params['correct_background']:

            print('Need to implement this')







class SpectrometerSpyrelet(Spyrelet):

    requires = {
        'spectro': Spectrometer,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def sweep(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        # set up tunable filter
        self.lltf.wavelength[params['filter_name']] = params['excitation']

        # set up spectrometer
        self.spectro.num_frames = params['num_frames']
        self.spectro.center_wavelength = params['center_wavelength']
        self.spectro.integration_time = params['integration_time']

        if params['temp_lock']:

            print('Checking for temperature lock...')

            def setpoint_check(reset_wait=1, tolerance=0.1):

                setpoint = self.spectro.sensor_setpoint

                while abs(setpoint - self.spectro.sensor_temperature) > tolerance:

                    print('Temperature not reached...')
                    time.sleep(reset_wait)


                print('Temperature stabilized')


            setpoint_check()


        # TODO: figure out how to correct background here
        if params['correct_background']:

            print('Need to implement this')


        for sweep in range(params['sweeps']):

            data, wavelength = self.spectro.acquire_frame()


            values = {
                'sweep_idx': sweep,
                'excitation': self.lltf.wavelength[params['filter_name']],
                'wavelength': wavelength,
                'cts': np.mean(data,axis=1)
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
            ('center_wavelength', {
                'type': float,
                'default': 900.0e-9,
                'units': 'm',
            }),
            ('sweeps', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('integration_time', {
                'type': float,
                'default': 100e-3,
                'units': 's',
                'positive': True,
            }),
            ('num_frames', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('grating', {
                'type': list,
                'items': [self.spectro.grating] #TODO: update to pull all gratings
            }),
            ('correct_background', {
                'type': bool,
            }),
            ('temp_lock', {
                'type': bool,
                'default': True,
            }),
            ('excitation', {
                'type': float,
                'units': 'm',
                'default': 905.0e-9,
                'positive': True
            }),
            ('filter_name', {
                'type': list,
                'items': list(self.lltf.filters.keys())
            })
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest spectrum')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Spectrum')
        p.xlabel = 'Wavelength (nm)'
        p.ylabel = 'Cts (a.u.)'
        return p

    @latest.on(sweep.acquired)
    def latest_update(self, ev):
        w = ev.widget
        latest_data = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        w.set('Spectrum', xs=latest_data.wavelength.values[0], ys=latest_data.cts.values[0])
        return

    @Element(name='Averaged spectrum')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Spectrum')
        p.xlabel = 'Wavelength (nm)'
        p.ylabel = 'Cts (a.u.)'
        return p

    @averaged.on(sweep.acquired)
    def averaged_update(self, ev):
        w = ev.widget

        # average dataset
        wavelength = self.data['wavelength'].mean()
        avg_cts = self.data['cts'].mean()

        if self.data.sweep_idx.max() > 0:

            std_cts = self.data['cts'].values.std()
            w.set('Spectrum', xs=wavelength, ys=avg_cts, yerrs=std_cts)

        else:
            w.set('Spectrum', xs=wavelength, ys=avg_cts)

        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w



class PLTometerSpyrelet(Spyrelet):

    requires = {
        'spectro': Spectrometer,
        'lltf': PhotonEtcFilter
    }

    @Task()
    def scan(self, **kwargs):
        self.dataset.clear()
        params = self.sweep_parameters.widget.get()

        # set up spectrometer
        self.spectro.num_frames = params['num_frames']
        self.spectro.center_wavelength = params['center_wavelength']
        self.spectro.integration_time = params['integration_time']

        y_range = params['excitation'].array.to('nm').m


        # TODO: add code to check that camera locked at setpoint
        if params['temp_lock']:

            print('Checking for temperature lock...')

            def setpoint_check(reset_wait=1, tolerance=0.1):

                setpoint = self.spectro.sensor_setpoint

                while abs(setpoint - self.spectro.sensor_temperature) > tolerance:

                    print('Temperature not reached...')
                    time.sleep(reset_wait)


                print('Temperature stabilized')


            setpoint_check()



        # TODO: add in code to measure background spectrum + correct
        if params['correct_background']:

            print('Need to implement this')



        for sweep in self.scan.progress(range(params['sweeps'])):

            for col_idx, w in enumerate(y_range):

                self.lltf.wavelength[params['filter_name']] = w

                from time import sleep
                sleep(1)

                print('next frame')

                data, wavelength = self.spectro.acquire_frame()


                values = {
                    'sweep_idx': sweep,
                    'col_idx': col_idx,
                    'excitation': self.lltf.wavelength[params['filter_name']],
                    'wavelength': wavelength,
                    'cts': np.mean(data, axis=1)
                }

                self.scan.acquire(values)

        return

    @scan.initializer
    def initialize(self):
        params = self.sweep_parameters.widget.get()

        self.max_rows = len(params['excitation'].array.to('nm').m)
        x_range = self.spectro.get_wavelengths()
        y_range = params['excitation'].array.to('nm').m
        x_diff = x_range[-1] - x_range[0]
        y_diff = y_range[-1] - y_range[0]
        pos = np.mean(x_range) - x_diff / 2, np.mean(y_range) - y_diff / 2
        scale = x_diff / len(x_range), y_diff / len(y_range)
        im_pos = [v for v in pos]
        im_scale = [v for v in scale]

        self.latest_scan.widget.im_pos = im_pos
        self.latest_scan.widget.im_scale = im_scale
        self.averaged_scan.widget.im_pos = im_pos
        self.averaged_scan.widget.im_scale = im_scale





        return

    @scan.finalizer
    def finalize(self):
        return

    @Element(name='Sweep parameters')
    def sweep_parameters(self):
        params = [
            ('center_wavelength', {
                'type': float,
                'default': 900.0e-9,
                'units': 'm',
            }),
            ('sweeps', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('integration_time', {
                'type': float,
                'default': 100e-3,
                'units': 's',
                'positive': True,
            }),
            ('num_frames', {
                'type': int,
                'default': 1,
                'positive': True,
            }),
            ('grating', {
                'type': list,
                'items': [self.spectro.grating] #TODO: update to pull all gratings
            }),
            ('correct_background', {
                'type': bool,
                'default': True,
            }),
            ('temp_lock', {
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
        w.xlabel = 'Spectrometer (nm)'
        w.ylabel = 'Excitation (nm)'

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @latest_scan.on(scan.acquired)
    def update_latest_scan(self, ev):
        latest = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        im = np.vstack(latest.sort_values('col_idx')['cts'])
        #im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)
        ev.widget.set(im)#, pos=self.pos, scale=self.scale)

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return

    @Element()
    def averaged_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'Spectrometer (nm)'
        w.ylabel = 'Excitation (nm)'

        #w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @averaged_scan.on(scan.acquired)
    def update_averaged_scan(self, ev):
        grouped = self.data.groupby('col_idx')['cts']
        averaged = grouped.apply(lambda column: np.mean(np.vstack(column), axis=0))
        im = np.vstack(averaged)
        #im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)

        ev.widget.set(im)#, pos=self.pos, scale=self.scale)
        return


    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
