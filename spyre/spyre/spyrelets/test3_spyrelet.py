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
# e.g.
# from lantz.drivers.keysight import Keysight_33622A
# The above line will import the AWG driver
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
class Test(Spyrelet):
    requires = {
        'analyzer': MS2721B,
    }


    @Task()
    def sweep_frequency(self):
        print('11')
        log_to_screen(DEBUG)

        print('here1')
        sweep_frequency_params = self.Sweep_Frequency_Settings.widget.get()
        laser_freq_params = self.Laser_Frequency_Settings.widget.get()
        print('here 4')
        carrier_wl = laser_freq_params['carrier wavelength (nm)']
        carrier_precision = laser_freq_params['precision(nm): ±']
        drift_time = laser_freq_params['drift_time']
        print("here2")
        chnl = sweep_frequency_params['marker channel']
        fr_low = sweep_frequency_params['start frequency']
        fr_high = sweep_frequency_params['stop frequency']
        fr_stp = sweep_frequency_params['step']
        t_stp = sweep_frequency_params['step time']
        pw = sweep_frequency_params['sweep power']
        folder_name = sweep_frequency_params['File Name']
        num_scan = sweep_frequency_params['Num Scan']

        print("here3")
        # self.analyzer.freq_span = 0 * Hz
        self.analyzer.generator_power = pw
        # self.analyzer.marker[chnl] = 'ON'

        for i in range(num_scan):
            print('3 This is scan repeat {}'.format(i))

            # Get file storage location
            path = "E:\\Data\\" + folder_name
            print('here!')
            print('PATH: ' + str(path))
            if path != "E:\\Data\\":
                if os.path.exists(path):
                    print('Saving data under \n' + str(path))
                else:
                    print('making new directory : \n' + str(path))
                    # Path(PATH).mkdir(parents=True, exist_ok=True)
                    os.mkdir(path)
            else:
                print("Specify a folder name & rerun task.")
                return


            print('here2!')

            curr = datetime.datetime.now()
            self.analyzer.freq_star = fr_low
            self.analyzer.freq_span = fr_high - fr_low
            # self.analyzer.ref_level = -30
            self.analyzer.savefile('modulation_data_' + curr.strftime("%Y-%m-%d_%H-%M-%S") + "_" + str(i))


            # with Client(self.laser) as client:
            #     # setting = client.get('laser1:ctl:wavelength-set', float)
            #     client.set('laser1:ctl:wavelength-set', carrier_wl)

            # Correct for laser drift  \pm 0.00001 nm ~ \pm 1MHz
            print('correcting for laser drift')
            # self.homelaser(carrier_wl, carrier_precision, drift_time)
            # print('actual carrier wavelength: ' + str(self.wm.measure_wavelength()))
            # carrier_wl = self.wm.measure_wavelength()

            # self.analyzer.generator = 'ON'


            # self.analyzer.generator = 'OFF'
            print('repeat '+str(i)+" is done.")

        #     freq = []
        #     power = []

        #     with open(path + "\\modulation_data_" + curr.strftime("%Y-%m-%d_%H-%M-%S") + '_' + str(i+1) + ".csv", mode='r') as csv_file:
        #         reader = csv.reader(csv_file, delimiter=',')
        #         print('1')
        #         for row in reader:
        #             if len(row) > 1:
        #                 print(row)
        #                 freq.append(row[0])
        #                 power.append(row[1])
        #     print('3')
        #     print(freq)
        #     print(power)
        #
        #     fig, ax = plt.subplots()
        #     ax.plot(freq, power)
        #     print('4')
        #     ax.set_xlabel('Freq (Hz)')
        #     ax.set_ylabel('Power (dBm)')
        #     print(freq[0],freq[-1])
        #     # ax.set_xticklabels(ax.get_xticks(), rotation = 50)
        #     ax.set_title('Modulation Data')
        #     fig.savefig(path + '\\modulation_data_' + curr.strftime("%Y-%m-%d_%H-%M-%S") + '_' + str(i+1) + '.png', dpi=300)
        #
        # self.analyzer.marker[chnl] = 'OFF'
        return

    @sweep_frequency.initializer
    def initialize(self):
        # self.wm.start_data()
        return

    @sweep_frequency.finalizer
    def finalize(self):
        # self.wm.stop_data()
        print('Data Collection complete.')
        return


    ###Elements###########################################################

    @Element()
    def Laser_Frequency_Settings(self):
        laser_freq_params = [
            ('carrier wavelength (nm)', {'type': float, 'default': 1530}),
            ('precision(nm): ±', {'type': float, 'default': 0.001}),
            ('drift_time', {'type': float, 'default': 5, 'units': 's'}),
            ('current', {'type': float, 'default': 0, 'units': 'mA'})
        ]
        w = ParamWidget(laser_freq_params)
        return w

    @Element()
    def Sweep_Frequency_Settings(self):
        sweep_freq_params = [
            ('start frequency', {'type': float, 'default': 9000, 'units': 'Hz'}),
            ('stop frequency', {'type': float, 'default': 9010, 'units': 'Hz'}),
            ('step', {'type': float, 'default': 1, 'units': 'MHz'}),
            ('step time', {'type': float, 'default': 0.3, 'units': 's'}),
            ('sweep power', {'type': float, 'default': 0}),
            ('Num Scan', {'type': int, 'default': 3}),
            ('marker channel', {'type': int, 'default': 1}),
            ('File Name', {'type': str, 'default': 'Er_LiYF_Modulation_Spectroscopy'}),
        ]
        w = ParamWidget(sweep_freq_params)
        return w
