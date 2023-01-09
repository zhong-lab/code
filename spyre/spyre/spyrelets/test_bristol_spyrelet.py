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
from lantz.drivers.bristol import Bristol_771  # Wavelength meter
from lantz.log import log_to_screen, DEBUG


nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')

class Test(Spyrelet):
    requires = {
        'wm': Bristol_771
    }

    laser = NetworkConnection('1.1.1.2')

    def homelaser(self, start, precision=0.0002, drift_time=4*s):
        current = self.wm.measure_wavelength()
        # print('here')
        iter = 0
        with Client(self.laser) as client:
            while current < start - precision or current > start + precision:
                # print('here1')
                iter = iter + 1
                if iter > 30:
                    print('Max iteration exceeded.')
                    break
                setting = client.get('laser1:ctl:wavelength-set', float)
                offset = current - start
                client.set('laser1:ctl:wavelength-set', setting - offset)
                time.sleep(drift_time.magnitude)
                current = self.wm.measure_wavelength()
                print(str(iter) + " current: {} target: {} new wl setting: {} diff: {}".format(current, start, round(setting - offset, 6), round(current - start, 6)))
        if iter <= 30:
            print("Laser homed.")
        else:
            print("Laser not homed.")

        return current, iter

    def homelaser_piezo(self, target, measure_time=15, motor_scan_precision=0.0003, precision=0.00004, drift_time=4 * s):
        """
        Motor scan of the Toptica CTL is suitable for large range wavelength adjustments.
        Using motor scan to move wavelength up to plus minus 0.0003nm, beyond this a bit hard, corrections may overshoot
        the wavelength target.
        So we adjust piezo voltage to fine tune wavelength beyond this point.
        In the neighborhood of 70V, 1V increase in piezo voltage changes wavelength by -0.001338nm.
        """
        with Client(self.laser) as client:
            client.set('laser1:dl:pc:enabled', True)
            piezo = client.get('laser1:dl:pc:voltage-set')
            print('Piezo is at', piezo, 'V.')
            if abs(piezo - 70) > 2:
                client.set('laser1:dl:pc:voltage-set', 70)
                print('Piezo Voltage changed to 70V.')
                time.sleep(5)
        wls = []
        for i in range(measure_time):
            wl = self.wm.measure_wavelength()
            wls.append(wl)
            time.sleep(1)
        avg = np.mean(wls)
        print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)

        motor_scan = False
        if abs(avg - target) > motor_scan_precision:
            motor_scan = True
            with Client(self.laser) as client:
                piezo = client.get('laser1:dl:pc:voltage-set')
                if piezo != 70:
                    client.set('laser1:dl:pc:voltage-set', 70)
                    print('Piezo Voltage changed to 70V.')
                    time.sleep(5)
            current = self.wm.measure_wavelength()
            iter = 0
            with Client(self.laser) as client:
                while current < target - motor_scan_precision or current > target + motor_scan_precision:
                    # print('here1')
                    iter = iter + 1
                    if iter > 6:
                        print('Max iteration exceeded.')
                        break
                    setting = client.get('laser1:ctl:wavelength-set', float)
                    offset = current - target
                    client.set('laser1:ctl:wavelength-set', setting - offset)  # this uses motor scan.
                    time.sleep(drift_time.magnitude)
                    current = self.wm.measure_wavelength()
                    print(str(iter) + " current: {} target: {} new wl setting: {} diff: {}".format(current, target,
                                                                                                   round(
                                                                                                       setting - offset,
                                                                                                       6), round(
                            current - target, 6)))
            if iter <= 6:
                print("Laser homed to within", motor_scan_precision, 'nm with motor scan.')
            else:
                print("Laser NOT homed to within", motor_scan_precision, 'nm with motor scan.')
        if motor_scan:
            print('Piezo scan to fine tune wavelength.')
            wls = []
            for i in range(measure_time):
                wl = self.wm.measure_wavelength()
                wls.append(wl)
                time.sleep(1)
            avg = np.mean(wls)
            print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)
        with Client(self.laser) as client:
            while avg < target - precision or avg > target + precision:
                piezo_adjust = round((avg - target) / 0.001338, 3)
                piezo = client.get('laser1:dl:pc:voltage-set')
                new_piezo = piezo + piezo_adjust
                client.set('laser1:dl:pc:voltage-set', new_piezo)
                print('New piezo voltage:', new_piezo, 'V.')
                time.sleep(5)
                wls = []
                for i in range(measure_time):
                    wl = self.wm.measure_wavelength()
                    wls.append(wl)
                    time.sleep(1)
                avg = np.mean(wls)
                print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)
        print('Laser Homed.')
        return avg

    @Task()
    def test_wavemeter(self):
        # log_to_screen(DEBUG)
        # testparams = self.Laser_Frequency_Settings.widget.get()
        # # with Client(self.laser) as client:
        # #     setting = client.get('laser1:ctl:wavelength-set', float)
        # #     # print('Setting is {}.'.format(setting)) # this prints current wl setting on toptica
        # target_wl = testparams['target wavelength (nm)']
        # precision = testparams['precision(nm): ±']
        # drift_time = testparams['drift_time']
        # wl = self.wm.measure_wavelength()
        # power = self.wm.measure_power()
        # print(wl, power)
        #
        # print("homelaser...\n")
        # self.homelaser(target_wl, precision=precision, drift_time=drift_time)
        wls = []
        # avgs = []
        # for j in range(4):
        for i in range(10):
            print("sleep...")
            time.sleep(1)  # if don't sleep somewhere in 
            print('1')
            wl = self.wm.measure_wavelength()
            wls.append(c/wl)
            print(c/wl)
            print('2')

            print('HEY')
            # time.sleep(1)
        #     avgs.append(np.mean(wls))
        # print(avgs)
        return

    @test_wavemeter.initializer
    def initialize(self):
        print('Start testlaser')
        self.wm.start_data()
        return

    @test_wavemeter.finalizer
    def finalize(self):
        self.wm.stop_data()
        return

    @Task()
    def homelaser_with_piezo(self):
        params = self.homelaser_with_piezo_Settings.widget.get()
        # with Client(self.laser) as client:
        #     setting = client.get('laser1:ctl:wavelength-set', float)
        #     # print('Setting is {}.'.format(setting)) # this prints current wl setting on toptica
        target_wl = params['target wavelength (nm)']
        precision = params['precision(nm): ±']
        drift_time = params['drift_time']

        print("homelaser...\n")
        self.homelaser_piezo(target_wl, precision=precision, drift_time=drift_time)

    @homelaser_with_piezo.initializer
    def initialize(self):
        print('Start testlaser')
        self.wm.start_data()
        return

    @homelaser_with_piezo.finalizer
    def finalize(self):
        self.wm.stop_data()
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
                wl = self.wm.measure_wavelength
                power = self.wm.measure_power

                print(i, curr.strftime("%Y-%m-%d_%H-%M-%S"), wl, power)

                writer.writerow([i, curr.strftime("%Y-%m-%d_%H-%M-%S"), wl, power])

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
            ('precision(nm): ±', {'type': float, 'default': 0.0004}),
            ('drift_time', {'type': float, 'default': 4, 'units': 's'}),
        ]
        w = ParamWidget(laser_freq_params)
        return w

    @Element()
    def homelaser_with_piezo_Settings(self):
        laser_freq_params = [
            ('target wavelength (nm)', {'type': float, 'default': 1529}),
            ('precision(nm): ±', {'type': float, 'default': 0.00004}),
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
