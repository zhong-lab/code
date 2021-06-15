from PyQt5 import QtWidgets
import pyqtgraph as pg
import itertools as it

import numpy as np
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments import Winspec
# from lantz.drivers.attocube.anc350 import ANC350
from lantz import Q_

class OMAVSpyrelet(Spyrelet):

    requires = {
        'cam': Winspec,
    }

    @Task()
    def run_forever(self, **kwargs):
        self.dataset.clear()
        now = time.time()
        for idx in self.run_forever.progress(it.count()):
            try:
                dt = time.time() - now
                xs = self.cam.get_exposure()
                values = {
                    'idx': idx,
                    'y': xs,
                    'wavelengths': self.wl,
                    "time": dt,
                }
                self.run_forever.acquire(values)

            except StopIteration:
                raise
            except Exception as e:
                print('Exception: {}'.format(e))

        return

    @Task()
    def accumulate(self, **kwargs):
        self.dataset.clear()
        for idx in range(self.params['accumulations']):
            try:
                xs = self.cam.get_exposure()
                values = {
                    'idx': idx,
                    'y': xs,
                    'wavelengths': self.wl,
                }
                self.accumulate.acquire(values)

            except StopIteration:
                raise
            except Exception as e:
                print('Exception: {}'.format(e))
        return

    @run_forever.initializer
    @accumulate.initializer
    def initialize(self):
        self.params = self.run_parameters.widget.get()
        if self.params["Calibration_Type"] == "From Camera":
            self.wl = self.cam.get_int_wavelength()
        elif self.params["Calibration_Type"] == "From Spyre":
            self.wl = self.cam.get_cal_wavelength()
        return

    @run_forever.finalizer
    @accumulate.finalizer
    def finalize(self):
        pass

    @Element(name='run parameters')
    def run_parameters(self):
        params = [
            ("Calibration_Type", {
                "type": list,
                "items": ["From Camera", "From Spyre"],
                "default": "From Camera"
            }),
            ('accumulations', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Latest Spectrum')
    def spectrum(self):
        p = LinePlotWidget()
        p.plot('Spectrum')
        p.xlabel = "Wavelength (nm)"
        p.ylabel = "Intensity"
        return p

    @spectrum.on(run_forever.acquired)
    @spectrum.on(accumulate.acquired)
    def spectrum_update(self, ev):
        w = ev.widget
        try:
            latest_data = self.data.y.iloc[-1]
            w.set('Spectrum', xs=self.wl, ys=latest_data)
        except IndexError:
            pass
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w

# class OMAVSpyrelet(Spyrelet):

#     requires = {
#         'cam': Winspec
#     }

#     @Task()
#     def sweep(self, **kwargs):
#         self.dataset.clear()
#         params = self.sweep_parameters.widget.get()
#         now = time.time()
#         for idx in self.sweep.progress(it.count()):
#             dt = time.time() - now
#             xs = self.cam.get_exposure()
#             if params["Kill Dead Pixels"]:
#                 xs = np.delete(xs,502)
#                 xs = xs[:-1]
#             temp = self.cam.temperature
#             integ = self.sum_between_crosshairs(xs)
#             values = {
#                 'idx': idx,
#                 'y': xs,
#                 'wavelengths':self.wl,
#                 "temp": temp,
#                 "dt": dt,
#                 "integ": integ
#             }
#             self.sweep.acquire(values)
#         return

#     @sweep.initializer
#     def initialize(self):
#         params = self.sweep_parameters.widget.get()
#         # self.cam.exposure_time = params["Exposure_Time"]
#         # self.cam.grating = int(params["Grating"])
#         # self.cam.wavelength = params["Wavelength"]
#         if params["Calibration_Type"] == "From Camera":
#             self.wl = self.cam.get_int_wavelength()
#         elif params["Calibration_Type"] == "From Spyre":
#             self.wl = self.cam.get_cal_wavelength()
#         # if params["Kill Dead Pixels"]:
#         #     self.wl = np.delete(self.wl,502)
#         #     self.wl = self.wl[:-1]
#         return

#     @sweep.finalizer
#     def finalize(self):
#         pass

#     @Element(name='Sweep parameters')
#     def sweep_parameters(self):
#         params = [
#             # ("Exposure_Time", {
#             #     "type": float,
#             #     "units": "s",
#             #     "positive": True,
#             #     "default": 1
#             # }),
#             # ("Wavelength", {
#             #     "type": float,
#             #     "units": "nm",
#             #     "positive": True,
#             #     "default": 1120.e-9
#             # }),
#             # ("Grating", {
#             #     "type": list,
#             #     "items": ["1", "2"],
#             #     "default": "2"
#             # }),
#             ("Calibration_Type", {
#                 "type": list,
#                 "items": ["From Camera", "From Spyre"],
#                 "default": "From Camera"
#             }),
#             ("Kill Dead Pixels", {
#                 "type": bool,
#                 "default": False
#             })
#         ]
#         w = ParamWidget(params)
#         return w

#     @Element(name='Latest Spectra')
#     def spectra(self):
#         p = LinePlotWidget()
#         p.plot('Spectra')
#         p.xlabel = "Wavelength (nm)"
#         p.ylabel = "Intensity"
#         return p

#     @spectra.on(sweep.acquired)
#     def spectra_update(self, ev):
#         w = ev.widget
#         try:
#             latest_data = self.data.y.iloc[-1]
#             w.set('Spectra', xs=self.wl, ys=latest_data)
#         except IndexError:
#             pass
#         return

#     @Element(name='Temperature')
#     def temp(self):
#         p = LinePlotWidget()
#         p.plot('Temperature')
#         p.xlabel = "Time (s)"
#         p.ylabel = "Temperature (K)"
#         return p

#     @temp.on(sweep.acquired)
#     def temp_update(self, ev):
#         w = ev.widget
#         w.set('Temperature', xs=self.data.dt, ys=self.data.temp)
#         return

#     @Element(name='Integrated')
#     def Integ(self):
#         p = LinePlotWidget()
#         p.plot('Integrated PL')
#         p.xlabel = "Time (s)"
#         p.ylabel = "Signal"
#         return p

#     @Integ.on(sweep.acquired)
#     def temp_update(self, ev):
#         w = ev.widget
#         w.set('Integrated PL', xs=self.data.dt, ys=self.data.integ)
#         return


#     def sum_between_crosshairs(self,spec):
#         crosshairs = self.spectra.widget.crosshairs
#         num_crosshairs = len(crosshairs)
#         num_coord_pairs = int(num_crosshairs/2)
#         if num_coord_pairs == 0:
#             return np.sum(spec)
#         else:
#             logical = np.array([(self.wl>crosshairs[2*ind][0])*(self.wl<crosshairs[2*ind+1][0]) for ind in range(num_coord_pairs)])
#             return np.sum(spec[np.logical_or.reduce(logical)])

#     @Element()
#     def save(self):
#         w = RepositoryWidget(self)
#         return w

# class OMAVCOOLSpyrelet(Spyrelet):

#     requires = {
#         'cam': Winspec
#     }


#     @Task()
#     def sweep(self, **kwargs):
#         self.dataset.clear()
#         params = self.sweep_parameters.widget.get()
#         now = time.time()
#         for idx in self.sweep.progress(it.count()):
#             dt = time.time() - now
#             xs = self.cam.get_exposure()
#             if params["Kill Dead Pixels"]:
#                 xs = np.delete(xs,502)
#                 self.xs = xs[:-1]
#             else:
#                 self.xs = xs
#             temp = self.cam.temperature
#             values = {
#                 'idx': idx,
#                 "temp": temp,
#                 "dt": dt,
#             }
#             self.sweep.acquire(values)
#         return

#     @sweep.initializer
#     def initialize(self):
#         params = self.sweep_parameters.widget.get()
#         self.cam.exposure_time = params["Exposure_Time"]
#         self.cam.grating = int(params["Grating"])
#         self.cam.wavelength = params["Wavelength"]
#         if params["Calibration_Type"] == "From Camera":
#             self.wl = self.cam.get_int_wavelength()
#         elif params["Calibration_Type"] == "From Spyre":
#             self.wl = self.cam.get_cal_wavelength()
#         # if params["Kill Dead Pixels"]:
#         #     self.wl = np.delete(self.wl,502)
#         #     self.wl = self.wl[:-1]
#         return

#     @sweep.finalizer
#     def finalize(self):
#         pass

#     @Element(name='Sweep parameters')
#     def sweep_parameters(self):
#         params = [
#             ("Exposure_Time", {
#                 "type": float,
#                 "units": "s",
#                 "positive": True,
#                 "default": 1,
#             }),
#             ("Wavelength", {
#                 "type": float,
#                 "units": "nm",
#                 "positive": True,
#                 "default": 1120.e-9,
#             }),
#             ("Grating", {
#                 "type": list,
#                 "items": ["1", "2"],
#                 "default": "2",
#             }),
#             ("Calibration_Type", {
#                 "type": list,
#                 "items": ["From Camera", "From Spyre"],
#                 "default": "From Spyre",
#             }),
#             ("Kill Dead Pixels", {
#                 "type": bool,
#                 "default": False,
#             })
#         ]
#         w = ParamWidget(params)
#         return w

#     @Element(name='Latest Spectra')
#     def spectra(self):
#         p = LinePlotWidget()
#         p.plot('Spectra')
#         p.xlabel = "Wavelength (nm)"
#         p.ylabel = "Intensity"
#         return p

#     @spectra.on(sweep.acquired)
#     def spectra_update(self, ev):
#         w = ev.widget
#         w.set('Spectra', xs=self.wl, ys=self.xs)
#         return

#     @Element(name='Temperature')
#     def temp(self):
#         p = LinePlotWidget()
#         p.plot('Temperature')
#         p.xlabel = "Time (s)"
#         p.ylabel = "Temperature (K)"
#         return p

#     @temp.on(sweep.acquired)
#     def temp_update(self, ev):
#         w = ev.widget
#         w.set('Temperature', xs=self.data.dt, ys=self.data.temp)
#         return

#     @Element()
#     def save(self):
#         w = RepositoryWidget(self)
#         return w


# class OMAVAttoScanSpyrelet(Spyrelet):

#     requires = {
#         'cam': Winspec,
#         'atto': ANC350
#     }


#     @Task()
#     def sweep(self, **kwargs):
#         self.dataset.clear()
#         params = self.sweep_parameters.widget.get()
#         for idx in range(params["sweeps"]):
#             location = params["Location"].array
#             for loc in location:
#                 self.atto.position[2] = loc
#                 xs = self.cam.get_exposure()
#                 if params["Kill Dead Pixels"]:
#                     xs = np.delete(xs,502)
#                     xs = xs[:-1]
#                 temp = self.cam.temperature
#                 values = {
#                     'location': loc,
#                     'y': xs,
#                     "temp": temp
#                 }
#                 self.sweep.acquire(values)
#         return

#     @sweep.initializer
#     def initialize(self):
#         params = self.sweep_parameters.widget.get()
#         self.cam.exposure_time = params["Exposure_Time"]
#         self.cam.wavelength = params["Wavelength"]
#         self.cam.grating = int(params["Grating"])
#         if params["Calibration_Type"] == "From Camera":
#             self.wl = self.cam.get_int_wavelength()
#         elif params["Calibration_Type"] == "From Spyre":
#             self.wl = self.cam.get_cal_wavelength()
#         if params["Kill Dead Pixels"]:
#             self.wl = np.delete(self.wl,502)
#             self.wl = self.wl[:-1]
#         self.handle_2d()
#         return

#     @sweep.finalizer
#     def finalize(self):
#         pass

#     @Element(name='Sweep parameters')
#     def sweep_parameters(self):
#         params = [
#             ("Exposure_Time", {
#                 "type": float,
#                 "units": "s",
#                 "positive": True,
#                 "default": 1
#             }),
#             ("Wavelength", {
#                 "type": float,
#                 "units": "nm",
#                 "positive": True,
#                 "default": 1120.e-9
#             }),
#             ("Grating", {
#                 "type": list,
#                 "items": ["1", "2"],
#                 "default": "2"
#             }),
#             ("Calibration_Type", {
#                 "type": list,
#                 "items": ["From Camera", "From Spyre"],
#                 "default": "From Spyre"
#             }),
#             ("Kill Dead Pixels", {
#                 "type": bool,
#                 "default": True
#             }),
#             ('Location', {
#                 'type': range,
#                 'units': 'um',
#                 'default': {'func': 'linspace',
#                             'start': 2200e-6,
#                             'stop': 3000e-6,
#                             'num': 401},
#             }),
#             ('sweeps', {
#                 'type': int,
#                 'default': 10,
#                 'positive': True,
#             }),
#         ]
#         w = ParamWidget(params)
#         return w

#     @Element(name='Latest Spectra')
#     def spectra(self):
#         p = LinePlotWidget()
#         p.plot('Spectra')
#         p.xlabel = "Wavelength (nm)"
#         p.ylabel = "Intensity"
#         return p

#     @spectra.on(sweep.acquired)
#     def spectra_update(self, ev):
#         w = ev.widget
#         latest_data = self.data.y.iloc[-1]
#         w.set('Spectra', xs=self.wl, ys=latest_data)
#         return

#     @Element(name='Scan')
#     def Scan(self):
#         p = HeatmapPlotWidget()
#         p.xlabel = "Wavelength (nm)"
#         p.ylabel = "Depth (um)"
#         return p

#     @Scan.on(sweep.acquired)
#     def Scan_update(self, ev):
#         w = ev.widget
#         im = np.vstack(self.data.y.values)
#         im = np.pad(im, ((0, self.max_rows - im.shape[0]),(0,0)), mode='constant', constant_values=0)
#         w.set(im)
#         return

#     @Element(name='Scan Average')
#     def Scan_Avg(self):
#         p = HeatmapPlotWidget()
#         p.xlabel = "Wavelength (nm)"
#         p.ylabel = "Depth (um)"
#         return p

#     @Scan_Avg.on(sweep.acquired)
#     def Scan_Avg_update(self, ev):
#         w = ev.widget
#         dat = self.data.groupby('location')['y']
#         averaged = dat.apply(lambda column: np.mean(np.vstack(column), axis=0))
#         im = np.vstack(averaged)
#         w.set(im)
#         return

#     def scale_pos_handler(self,array):
#         diff = array[-1] - array[0]
#         pos = np.mean(array) - diff / 2
#         scale = diff / len(array)
#         return pos, scale

#     def handle_2d(self):
#         w = self.Scan.widget
#         w2 = self.Scan_Avg.widget
#         params = self.sweep_parameters.widget.get()
#         z_pos_scale = self.scale_pos_handler(params["Location"].array)
#         wl_pos_scale = self.scale_pos_handler(self.wl)
#         pos_z, scale_z = [v.to("um").magnitude for v in z_pos_scale]
#         pos_wl, scale_wl = [v for v in wl_pos_scale]
#         w.im_pos = [pos_wl, pos_z]
#         w.im_scale = [scale_wl, scale_z]
#         w2.im_pos = [pos_wl, pos_z]
#         w2.im_scale = [scale_wl, scale_z]

#     @Element()
#     def save(self):
#         w = RepositoryWidget(self)
#         return w
