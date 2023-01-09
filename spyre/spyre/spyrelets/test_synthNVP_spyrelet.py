import numpy as np
import pyqtgraph as pg
import time
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
from lantz.drivers.windfreak import SynthNVPro

from lantz.log import log_to_screen, DEBUG


class TestSynthNVP(Spyrelet):
    requires = {
        'windfreak': SynthNVPro
    }

    @Task()
    def test(self):
        log_to_screen(DEBUG)
        WindfreakFreq = 200  # in MHz
        rf_powers = [11.8,10.8, 9.5]  # in dBm
        self.windfreak.output = 1  # turn on the windfreak
        time.sleep(5)  ## wait 5s to turn on the windfreak
        self.windfreak.frequency = WindfreakFreq  # set the windfreak frequency to the windfreak frequency
        for i in rf_powers:
            self.windfreak.power = i  # set the windfreak power to 14.5 dBm
            time.sleep(5)

        self.windfreak.output = 0
        time.sleep(5)

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