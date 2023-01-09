import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle  # for saving large arrays
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
import datetime

# from lantz.drivers.bristol import Bristol_771
from lantz.drivers.burleigh import WA7600  # Wavelength meter
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
# from lantz.drivers.agilent import N5181A
from lantz.drivers.windfreak import SynthNVPro
# import nidaqmx
# from nidaqmx import AnalogInputTask


# from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
# from lantz.drivers.attocube import ANC350

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz = Q_(1, 'kHz')
MHz = Q_(1.0, 'MHz')
dB = Q_(1, 'dB')
dBm = Q_(1, 'dB')
s = Q_(1, 's')


class Test(Spyrelet):
    requires = {
        'fungen': Keysight_33622A
    }

    @Task()
    def test_awg(self):
        self.fungen.pulse_width[2] = 1e-6*s
        pulse_width = self.fungen.pulse_width[2]
        print(pulse_width)
        return

    @test_awg.initializer
    def initialize(self):
        print('Start test')
        return

    @test_awg.finalizer
    def finalize(self):
        return
