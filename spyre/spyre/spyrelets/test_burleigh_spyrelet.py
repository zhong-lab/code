import numpy as np
import pyqtgraph as pg
import time
import csv
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
# e.g.
# from lantz.drivers.keysight import Keysight_33622A
# The above line will import the AWG driver
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
from lantz.drivers.burleigh import WA7600  # Wavelength meter
from lantz.log import log_to_screen, DEBUG


nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')

class TestBurleigh(Spyrelet):
    requires = {
        'wm': WA7600,
    }

    # rm = pyvisa.ResourceManager()
    # print(rm.list_resources())
    # wavemeter = rm.open_resource('GPIB1::10::INSTR')

    laser = NetworkConnection('1.1.1.2')

    def homelaser(self, start, precision=0.0002, drift_time=4*s):
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

    @Task()
    def testlaser(self):
        # log_to_screen(DEBUG)
        testparams = self.Laser_Frequency_Settings.widget.get()
        # with Client(self.laser) as client:
        #     setting = client.get('laser1:ctl:wavelength-set', float)
        #     # print('Setting is {}.'.format(setting)) # this prints current wl setting on toptica
        target_wl = testparams['target wavelength (nm)']
        precision = testparams['precision(nm): ±']
        drift_time = testparams['drift_time']

        # self.analyzer.freq_span = 0*Hz
        # print(wavemeter.query("*IDN?"))
        # print(wavemeter.query(":MEAS:SCAL:WAV?"))
        # print(type(wl))
        # print(wl)
        # client.set('laser1:ctl:wavelength-set', target_wl)
        # print('Set wavelength to {}'.format(target_wl))
        # setting = client.get('laser1:ctl:wavelength-set', float)
        # print('Setting is now {}.'.format(setting))

        # time.sleep(3)
        # idn = self.wm.idn
        # print(idn)]

        # plt.plot(wl_range)
        # plt.show()
        # print(type(wl))
        #
        # freq = self.wm.meas_freq
        # print("freq is " + str(freq) + "THz")
        #
        # FWHM = self.wm.meas_FWHM
        # print("FWHM is " + str(FWHM) + "nm")
        #
        # power = self.wm.meas_power
        # print("peak power is " + str(power) + "dBm")
        #
        # total_power = self.wm.meas_total_power
        # print("total power is " + str(total_power) + "dBm")


        # print('Actual wavelength is {}'.format(wl))
        # print('1Actual wavelength is '+str(wl))

        # freq = self.wm.meas_freq()
        # print(type(freq))
        # print('Actual optical frequency is {}'.format(freq))


        print("homelaser...\n")
        self.homelaser(target_wl, precision=precision, drift_time=drift_time)


        return

    @testlaser.initializer
    def initialize(self):
        print('Start testlaser')
        return

    @testlaser.finalizer
    def finalize(self):
        return

    @Task()
    def laser_drift_monitor(self):
        # log_to_screen(DEBUG)

        drift_params = self.Laser_Drift_Meas_Settings.widget.get()

        path = drift_params['File Path']
        tot_time = drift_params['Total Drift Time (hr)']
        time_step = drift_params['Time Step (sec)']

        num_steps = int(tot_time*3600/time_step)
        print(num_steps)
        curr = datetime.datetime.now()

        with open(path+'\\'+'Laser_drift_'+curr.strftime("%Y-%m-%d_%H-%M-%S")+'.csv','w') as csv_file:
            writer = csv.writer(csv_file, delimiter=',')

            for i in range(0,num_steps):
                curr = datetime.datetime.now()

                # sleep not needed after these commands bc code will wait to hear back from qurey to wm
                wl = self.wm.meas_wavelength
                power = self.wm.meas_power
                FWHM = self.wm.meas_FWHM

                print(i, curr.strftime("%Y-%m-%d_%H-%M-%S"), wl, power, FWHM)

                writer.writerow([i, curr.strftime("%Y-%m-%d_%H-%M-%S"), wl, power, FWHM])

                time.sleep(time_step-7.5) # 3 commands above takes roughly 7.5 sec
            print('Long term drift measurement done.')

        csv_file.close()

        return

    @laser_drift_monitor.initializer
    def initialize(self):
        print('Start Long Drift Monitoring...')
        return

    @laser_drift_monitor.finalizer
    def finalize(self):
        print('Monitoring Done.')
        return

    @Task()
    def find_wl_range(self):
        # log_to_screen(DEBUG)
        wls = []
        for i in range(300):
            wl = self.wm.meas_wavelength
            wls.append(wl)
            print(wl)
        print("Max is {}".format(max(wls)))
        print("Min is {}".format(min(wls)))

        return

    @find_wl_range.initializer
    def initialize(self):
        print('Start printing wavelength...')
        return

    @find_wl_range.finalizer
    def finalize(self):
        print('Wavelength reading done.')
        return

    @Element()
    def Laser_Frequency_Settings(self):
        laser_freq_params = [
            ('target wavelength (nm)', {'type': float, 'default': 1529}),
            ('precision(nm): ±', {'type': float, 'default': 0.0001}),
            ('drift_time', {'type': float, 'default': 4, 'units': 's'}),
        ]
        w = ParamWidget(laser_freq_params)
        return w

    @Element()
    def Laser_Drift_Meas_Settings(self):
        laser_drift_meas_params = [
            ('File Path', {'type': str, 'default': 'E:\\Data\\6.21.2022_Telerare_Long_Drift'}),
            ('Total Drift Time (hr)', {'type': float, 'default': 8}),
            ('Time Step (sec)', {'type': float, 'default': 60})
        ]
        w = ParamWidget(laser_drift_meas_params)
        return w
