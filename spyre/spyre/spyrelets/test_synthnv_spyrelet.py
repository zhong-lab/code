import numpy as np
import pyqtgraph as pg
import csv
import os
from pathlib import Path
import pickle # for saving large arrays
import math

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
from lantz.drivers.windfreak import SynthNV
from lantz.drivers.bristol import Bristol_771
from scipy.constants import c
from lantz.log import log_to_screen, DEBUG

MHz = Q_(1.0, 'MHz')

class TestSynthNV(Spyrelet):
    requires = {
        # 'windfreak': SynthNV
        'wm': Bristol_771
    }

    def check_laser_lock(self, target, freqs, sample_size=50, precision=2):
        if len(freqs) < 50:
            print('Laser lock check: Accumulating statistics')
        else:
            avg = sum(freqs[-sample_size:])/sample_size
            print("Laser lock check: Average: ", avg)
            if abs(avg - target)*1e3 > precision:
                diff = int((avg - target)*1e3)  # just correct to 1 MHz
                step = diff/abs(diff)
                print("Diff: {} MHz, Step: {} MHz".format(diff, step))
                with SynthNV('ASRL11::INSTR') as inst:
                    curr_rf = inst.frequency*1e-3
                    print("Current synthNV freq: ", curr_rf)
                    for i in range(int(abs(diff))):
                        new_rf = (curr_rf.magnitude - step) * MHz
                        inst.frequency = new_rf
                        time.sleep(1)
                        curr_rf = inst.frequency*1e-3
                        print("New synthNV freq: ", new_rf, curr_rf)
                freqs = []
                # actually the adjustment in laser frequency is pretty accurate
                # error signal is shifted by a few MHz and the locking should allow the laser to follow
                # so after adjustment, just get some new statistics so that the average isn't affected
                # by the old data
                # doesn't need to do a while loop and keep adjusting until the wavelength is correct
        return freqs

    @Task()
    def test(self):
        # log_to_screen(DEBUG)
        freqs = []
        for i in range(30):
            freq = c/self.wm.measure_wavelength()
            freqs.append(freq)
            time.sleep(1)

        for i in range(5*3600):
            freq = c/self.wm.measure_wavelength()
            freqs.append(freq)
            freqs = self.check_laser_lock(193967.997, freqs)
            time.sleep(1)
        # with SynthNV('ASRL11::INSTR') as inst:
        #     print(inst.output)
        #     inst.output = 0
        #     time.sleep(5)
        #     inst.output = 1
        #     print(inst.frequency)   # returns in kHz with the unit of kHz
        #     print(inst.output_level)
        #     inst.frequency = 460
        #     time.sleep(5)
        #     inst.frequency = 450
        #     time.sleep(5)
        #     print(inst.frequency)
        #     # inst.output = 0
        #
        # # self.windfreak.output = 0
        # # time.sleep(2)
        # # self.windfreak.output = 1
        # # time.sleep(2)
        # # # print(self.windfreak.output)
        # # #
        # # self.windfreak.frequency = 450.001
        # # time.sleep(1)
        # # print(self.windfreak.frequency)
        #
        #     # sweeps frequency
        #     steps = 10
        #     for i in range(steps):
        #         curr_freq = inst.frequency*1e-3
        #         inst.frequency = (curr_freq.magnitude + 1)*MHz
        #         print('Current frequency: ', inst.frequency*1e-3)
        #         time.sleep(1)
        #     inst.output = 0

    @test.initializer
    def initialize(self):
        print('Start Test...')

    @test.finalizer
    def finalize(self):
        print('Done.')
        return

    @Element(name='Piezo scan parameters')
    def piezo_params(self):
        params = [
        ]

        w = ParamWidget(params)
        return w