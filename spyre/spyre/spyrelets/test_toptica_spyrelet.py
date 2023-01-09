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
from lantz.log import log_to_screen, DEBUG
from lantz.drivers.bristol import Bristol_771  # Wavelength meter


nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')
mW = Q_(1, 'mW')


class TestToptica(Spyrelet):
    requires = {
        'wm': Bristol_771
    }

    # rm = pyvisa.ResourceManager()
    # print(rm.list_resources())
    # wavemeter = rm.open_resource('GPIB1::10::INSTR')

    laser = NetworkConnection('1.1.1.2')

    def homelaser(self, target, measure_time=15, motor_scan_precision=0.0003, precision=0.00004, drift_time=4*s):
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
            if abs(piezo-70) > 2:
                client.set('laser1:dl:pc:voltage-set', 70)
                print('Piezo Voltage changed to 70V.')
                time.sleep(5)
        wls = []
        for i in range(measure_time):
            wl = self.wm.measure_wavelength()
            wls.append(wl)
            time.sleep(1)
        avg = np.mean(wls)
        print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)

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
                    iter = iter+1
                    if iter > 6:
                        print('Max iteration exceeded.')
                        break
                    setting = client.get('laser1:ctl:wavelength-set', float)
                    offset = current - target
                    client.set('laser1:ctl:wavelength-set', setting - offset)  # this uses motor scan.
                    time.sleep(drift_time.magnitude)
                    current = self.wm.measure_wavelength()
                    print(str(iter)+" current: {} target: {} new wl setting: {} diff: {}".format(current, target, round(setting - offset,6), round(current-target,6)))
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
            print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)
        with Client(self.laser) as client:
            while avg < target - precision or avg > target + precision:
                piezo_adjust = round((avg-target)/0.001338, 3)
                piezo = client.get('laser1:dl:pc:voltage-set')
                new_piezo = piezo+piezo_adjust
                client.set('laser1:dl:pc:voltage-set', new_piezo)
                print('New piezo voltage:', new_piezo, 'V.')
                time.sleep(5)
                wls = []
                for i in range(measure_time):
                    wl = self.wm.measure_wavelength()
                    wls.append(wl)
                    time.sleep(1)
                avg = np.mean(wls)
                print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)
        return avg

    @Task()
    def test(self):
        log_to_screen(DEBUG)

        # convert the start voltage and stop voltage into a voltage
        # and offset to set on the AWG
        laser_power = [5, 3, 1]

        # curent_control_state = client.get('laser1:dl:cc:enabled', bool)
        # print(curent_control_state)
        # piezo=client.get('laser1:dl:pc:enabled')
        # print(piezo)
        # client.set('laser1:dl:pc:enabled', True)
        # client.set('laser1:dl:pc:voltage-set', 70)
        # chnl=client.get('laser1:dl:pc:external-input:signal')
        # print(chnl)
        # client.set('laser1:dl:pc:external-input:signal', 3)
        # chnl = client.get('laser1:dl:pc:external-input:signal')
        # print(chnl)

        # with Client(self.laser) as client:
        #     current_piezo = client.get('laser1:dl:pc:voltage-set')
        #     print(current_piezo)
        #     wls = []
        #     for i in range(30):
        #         wl = self.wm.measure_wavelength()
        #         wls.append(wl)
        #         time.sleep(1)
        #     client.set('laser1:dl:pc:voltage-set', current_piezo+1)
        #     time.sleep(10)
        #     new_wls = []
        #     for i in range(30):
        #         wl = self.wm.measure_wavelength()
        #         new_wls.append(wl)
        #         time.sleep(1)
        #     new_wl = np.mean(new_wls)
        #     wl = np.mean(wls)
        #     change_per_V = (new_wl - wl) / 1
        #     print('Change in wl per V change in piezo:', change_per_V)

            # power = client.get('laser1:power-stabilization:setpoint')
            # print(power)
            # client.set('laser1:power-stabilization:setpoint', setting)
            # power = client.get('laser1:power-stabilization:setpoint')
            # print(power)

        self.homelaser(1530.3724)
        # time.sleep(5)
        # client.get('laser1:dl:cc:enabled', False)  # doesn't work
        # offset = client.get('laser1:dl:pc:voltage-set', float)
        # print(offset)
        # # channel = client.get('laser1:dl:pc:external-input', float)
        # # print(channel)
        # scale_factor = client.get('laser1:dl:pc:external-input:factor', float)
        # print(scale_factor)
        # on_off = client.get('laser1:dl:pc:enabled', bool)
        # print(on_off)
        # input_on_off = client.get('laser1:dl:pc:external-input:enabled', bool)
        # print(input_on_off)
        # print('2')
        # client.set('laser1:dl:pc:voltage-set', 70)
        # print('3')
        # client.set('laser1:dl:pc:external-input', 3)
        # print('4')
        # client.set('laser1:dl:factor', 8)
        # print('5')
        # client.set('laser1:dl:pc:enabled', 1)
        # now loop through the points on the list and record the average DC
        # signal from the oscilloscope

    @Element(name='Piezo scan parameters')
    def piezo_params(self):
        params = [
        ]

        w = ParamWidget(params)
        return w

    @test.initializer
    def initialize(self):
        print('Start Test...')

    @test.finalizer
    def finalize(self):
        print('Done.')
        return
