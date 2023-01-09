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
from lantz.drivers.keysight import Keysight_33622A
from lantz.log import log_to_screen, DEBUG

nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')


class FindPiezoScanRange(Spyrelet):
    requires = {
        'wm': WA7600,
        'fungen': Keysight_33622A
    }

    # rm = pyvisa.ResourceManager()
    # print(rm.list_resources())
    # wavemeter = rm.open_resource('GPIB1::10::INSTR')

    laser = NetworkConnection('1.1.1.2')

    def homelaser(self, start, precision, drift_time):
        current = self.wm.meas_wavelength
        # print('here')
        iter = 0
        with Client(self.laser) as client:
            while current < start - precision or current > start + precision:
                # print('here1')
                iter = iter + 1
                if iter > 30:
                    print('Max iteration exeeded.')
                    break
                setting = client.get('laser1:ctl:wavelength-set', float)
                offset = current - start
                client.set('laser1:ctl:wavelength-set', setting - offset)
                time.sleep(drift_time.magnitude)
                current = self.wm.meas_wavelength
                print(str(iter) + " current: {} target: {} new wl setting: {} diff: {}".format(current, start,round(setting - offset, 6), round(current - start, 6)))
        if iter <= 30:
            print("Laser homed.")
        else:
            print("Laser not homed.")

        return current, iter

    @Task()
    def pzscan(self):
        log_to_screen(DEBUG)
        self.fungen.clear_mem(1)
        self.fungen.wait()

        print('1')
        # get the parameters for the experiment from the widget
        piezoParams = self.piezo_params.widget.get()
        wl = piezoParams['Wavelength']
        precision = piezoParams['precision(nm): ±']
        drift_time = piezoParams['drift_time']
        channel = piezoParams['Channel']
        Vstart = piezoParams['Start voltage'].magnitude
        Vstop = piezoParams['Stop voltage'].magnitude
        voltage_scale_factor = piezoParams['Scale factor']
        piezoOffset = piezoParams['Piezo voltage offset']
        points = piezoParams['# of points']
        filename = piezoParams['Filename']
        wait = piezoParams['Wait time after V update'].magnitude

        print('2')
        # convert the start voltage and stop voltage into a voltage
        # and offset to set on the AWG
        offset = (Vstart + Vstop) / 2
        Vpp = Vstart - Vstop

        # home the laser
        self.fungen.output[channel] = 'OFF'
        print("homelaser...\n")
        self.homelaser(wl, precision, drift_time)

        # create a list of voltages to loop through
        Vpoints = np.linspace(Vstart, Vstop, points)

        # AWG Output on

        self.fungen.output[channel] = 'ON'
        self.fungen.waveform[channel] = 'DC'
        # self.fungen.waveform[channel] = 'RAMP'
		# self.fungen.frequency[Pulsechannel] = 0.005
		# self.fungen.voltage[Pulsechannel] = 2
		# self.fungen.offset[Pulsechannel] = 0
		# self.fungen.phase[Pulsechannel] = 0
        print('3')
        # set the piezo scan voltage scale factor on the laser
        with Client(self.laser) as client:
            client.set('laser1:dl:pc:voltage-set', piezoOffset)
            client.set('laser1:dl:pc:external-input:factor', voltage_scale_factor)
            client.set('laser1:dl:pc:enabled', True)
            client.set('laser1:dl:pc:external-input:enabled', True)

        print('4')
        # now loop through the points on the list and record the average DC
        # signal from the oscilloscope
        curr = datetime.datetime.now()
        with open(filename + curr.strftime("%Y-%m-%d_%H-%M-%S") + '.csv', 'w') as csvfile:
            CSVwriter = csv.writer(csvfile, delimiter=',')
            for i in range(points):
                print(i)
                self.fungen.offset[channel] = Vpoints[i]
                time.sleep(wait)
                # measure the wavelength
                wl_meas = self.wm.meas_wavelength
                # write this to a .CSV file
                CSVwriter.writerow([Vpoints[i], wl_meas])

        self.fungen.output[channel] = 'OFF'

        with Client(self.laser) as client:
            client.set('laser1:dl:pc:enabled', False)
            client.set('laser1:dl:pc:external-input:enabled', False)

    @Element(name='Piezo scan parameters')
    def piezo_params(self):
        params = [
            ('Wavelength', {'type': float, 'default': 1530.400}),
            ('precision(nm): ±', {'type': float, 'default': 0.0002}),
            ('drift_time', {'type': float, 'default': 4, 'units': 's'}),
            ('Channel', {'type': int, 'default': 1}),
            ('Start voltage', {'type': float, 'default': -2, 'units': 'V'}),
            ('Stop voltage', {'type': float, 'default': 2, 'units': 'V'}),
            ('Scale factor', {'type': float, 'default': 8}),
            ('Piezo voltage offset', {'type': float, 'default': 70}),
            ('Wait time after V update', {'type': int, 'default': 0, 'units': 's'}),
            ('# of points', {'type': int, 'default': 200}),
            ('Filename', {'type': str,
                          'default': "E:\\Data\\6.14.2022_ErLYF_Modulation\\06_21_22_direct_transmission\\piezo_scan_"})
        ]

        w = ParamWidget(params)
        return w

    @pzscan.initializer
    def initialize(self):
        print('Start Scanning...')

    @pzscan.finalizer
    def finalize(self):
        print('Done.')
        return
