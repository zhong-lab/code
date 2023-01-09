import wave
import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from lantz import Q_

import matplotlib.pyplot as plt
import datetime
from scipy.constants import c

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

###Import lantz drivers files for all instruments you use.
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
from lantz.drivers.burleigh import WA7600  # Wavelength meter
from lantz.drivers.spectrum import MS2721B  # Anritsu spectrum analyzer
from lantz.log import log_to_screen, DEBUG

nm = Q_(1, 'nm')
s = Q_(1, 's')

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz = Q_(1, 'kHz')
MHz = Q_(1.0, 'MHz')
dB = Q_(1, 'dB')


# Sweep EOM modulation signal
class SweepSignal(Spyrelet):
    requires = {
        'analyzer': MS2721B,
        'wm': WA7600
    }

    qutag = None

    laser = NetworkConnection('1.1.1.2')

    def homelaser(self, start, precision, drift_time):
        current = self.wm.meas_wavelength
        # print('here')
        iter = 0
        with Client(self.laser) as client:
            while current < start - precision or current > start + precision:
                # print('here1')
                iter = iter+1
                if iter > 30:
                    print('Max iteration exeeded.')
                    break
                setting = client.get('laser1:ctl:wavelength-set', float)
                offset = current - start
                client.set('laser1:ctl:wavelength-set', setting - offset)
                time.sleep(drift_time.magnitude)
                current = self.wm.meas_wavelength
                print(str(iter)+" current: {} target: {} new wl setting: {} diff: {}".format(current, start, round(setting - offset,6), round(current-start,6)))
        if iter <= 30:
            print("Laser homed.")
        else:
            print("Laser not homed.")
            
        return current, iter
    ##Tasks##############################################################
    @Task()
    def set_laser_wavelength(self):
        # log_to_screen(DEBUG)
        testparams = self.Laser_Frequency_Settings.widget.get()
        # with Client(self.laser) as client:
            # setting = client.get('laser1:ctl:wavelength-set', float)
            # print('Setting is {}.'.format(setting)) # this prints current wl setting on toptica
        target_wl = testparams['carrier wavelength (nm)']
        precision = testparams['precision(nm): ±']
        drift_time = testparams['drift_time']

            # client.set('laser1:ctl:wavelength-set', target_wl)
            # print('Set wavelength to {}'.format(target_wl))
            # # setting = client.get('laser1:ctl:wavelength-set', float)
            # # print('Setting is now {}.'.format(setting))
            # time.sleep(3)
            # wl = self.wm.meas_wavelength
            # print('Actual wavelength is {}'.format(wl))
        print("homelaser...\n")
        self.homelaser(target_wl, precision, drift_time)
            # target_current = testparams['current']
            # client.set('laser1:dl:cc:current-set', target_current)
            # current = client.get('laser1:dl:cc:current-set', float)
            # print('current is set to ' + str(current))

        return

    @set_laser_wavelength.initializer
    def initialize(self):
        print("Start setting laser wavelength.")
        return

    @set_laser_wavelength.finalizer
    def finalize(self):
        print('End of setting laser wavelength.')
        return

    @Task()
    def sweep_frequency(self):
        self.dataset.clear()
        # log_to_screen(DEBUG)

        # print('here 1')
        sweep_frequency_params = self.Sweep_Frequency_Settings.widget.get()
        laser_freq_params = self.Laser_Frequency_Settings.widget.get()

        carrier_wl = laser_freq_params['carrier wavelength (nm)']
        carrier_wl2 = laser_freq_params['carrier wavelength 2 (nm)']
        carrier_precision = laser_freq_params['precision(nm): ±']
        drift_time = laser_freq_params['drift_time']

        fr_low1 = sweep_frequency_params['start frequency1']
        fr_high1 = sweep_frequency_params['stop frequency1']

        # dip 1
        fr_low2 = sweep_frequency_params['start frequency2']
        fr_high2 = sweep_frequency_params['stop frequency2']

        fr_low3 = sweep_frequency_params['start frequency3']
        fr_high3 = sweep_frequency_params['stop frequency3']

        fr_low4 = sweep_frequency_params['start frequency4']
        fr_high4 = sweep_frequency_params['stop frequency4']

        # dip 2
        fr_low5 = sweep_frequency_params['start frequency5']
        fr_high5 = sweep_frequency_params['stop frequency5']

        fr_low6 = sweep_frequency_params['start frequency6']
        fr_high6 = sweep_frequency_params['stop frequency6']


        fr_low = [fr_low2, fr_low1, fr_low3, fr_low5, fr_low4, fr_low6]
        fr_high = [fr_high2, fr_high1, fr_high3, fr_high5, fr_high4, fr_high6]


        pw = sweep_frequency_params['TG sweep power (dBm)']
        file_name = sweep_frequency_params['File Name']
        num_scan = sweep_frequency_params['Num Scan']
        ref_level = sweep_frequency_params['ref level (dBm)']  # for analyzer display only, not important

        # print("here 2")
        self.analyzer.generator_power = pw
        self.analyzer.ref_level = ref_level
        self.analyzer.generator = 'ON'
        # set laser freq to carrier wavelength
        # with Client(self.laser) as client:
        #     # setting = client.get('laser1:ctl:wavelength-set', float)
        #     client.set('laser1:ctl:wavelength-set', carrier_wl)
        where = self.analyzer.save_to_where
        for i in range(0,10):
            print("Saving file to "+where)


        for j in range(0,6):
            start = fr_low[j]
            end = fr_high[j]
            self.analyzer.freq_star = start
            time.sleep(2)
            self.analyzer.freq_stop = end
            time.sleep(25)

            # if j == 3:
            #     carrier_wl = carrier_wl2

            for i in range(num_scan):
                print('This is scan #{} on freq range {} - {}'.format(i, start, end))

                # Correct for laser drift each run \pm 0.00001 nm ~ \pm 1MHz
                print('correcting for laser drift...')
                current_wl, iter=self.homelaser(carrier_wl, carrier_precision, drift_time)
                if i == 0:
                    time.sleep(10)
                    current_wl, iter=self.homelaser(carrier_wl, carrier_precision, drift_time)
                if iter <= 30:
                    curr = datetime.datetime.now()

                    self.analyzer.savefile(str(start) + file_name + curr.strftime("%Y-%m-%d_%H-%M-%S") + "_#" + str(i) + "_" + str(current_wl))
                    time.sleep(14)
            # print('here 4!')

            # print('Scan repeat ' + str(i) + " is done.")
            # print('Actual carrier wavelength: ' + str(carrier_wl))

        return

    @sweep_frequency.initializer
    def initialize(self):
        print("Start of sweep_frequency.")
        return

    @sweep_frequency.finalizer
    def finalize(self):
        print('Data Collection Complete.')
        return

    ###Elements###########################################################
    @Element()
    def Laser_Frequency_Settings(self):
        laser_freq_params = [
            ('carrier wavelength (nm)', {'type': float, 'default': 1529.5275}),
            ('carrier wavelength 2 (nm)', {'type': float, 'default': 1529.5275}),
            ('precision(nm): ±', {'type': float, 'default': 0.0001}),
            ('drift_time', {'type': float, 'default': 4, 'units': 's'}),
            # ('current', {'type': float, 'default': 0, 'units': 'mA'})
        ]
        w = ParamWidget(laser_freq_params)
        return w

    @Element()
    def Sweep_Frequency_Settings(self):
        sweep_freq_params = [
            ('start frequency1', {'type': float, 'default': 9000, 'units': 'Hz'}),
            ('stop frequency1', {'type': float, 'default': 2700e6, 'units': 'Hz'}),
            ('start frequency2', {'type': float, 'default': 2700e6, 'units': 'Hz'}),
            ('stop frequency2', {'type': float, 'default': 3400e6, 'units': 'Hz'}),
            ('start frequency3', {'type': float, 'default': 3400e6, 'units': 'Hz'}),
            ('stop frequency3', {'type': float, 'default': 7100e6, 'units': 'Hz'}),
            ('start frequency4', {'type': float, 'default': 9000, 'units': 'Hz'}),
            ('stop frequency4', {'type': float, 'default': 1600e6, 'units': 'Hz'}),
            ('start frequency5', {'type': float, 'default': 1600e6, 'units': 'Hz'}),
            ('stop frequency5', {'type': float, 'default': 1860e6, 'units': 'Hz'}),
            ('start frequency6', {'type': float, 'default': 1860e6, 'units': 'Hz'}),
            ('stop frequency6', {'type': float, 'default': 3e9, 'units': 'Hz'}),
            ('TG sweep power (dBm)', {'type': float, 'default': -5.5}),
            ('ref level (dBm)', {'type': float, 'default': -10.6}),
            ('Num Scan', {'type': int, 'default': 3}),
            ('File Name', {'type': str, 'default': '_Er_LYF_Modulation_Z1_Y2_'}),
        ]
        w = ParamWidget(sweep_freq_params)
        return w
