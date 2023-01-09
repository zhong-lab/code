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
from lantz.drivers.stanford.srs900 import SRS900

from lantz.log import log_to_screen, DEBUG


nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')
mW = Q_(1, 'mW')


class TestSRS(Spyrelet):
    requires = {
        'SRS': SRS900
    }

    @Task()
    def test(self):
        log_to_screen(DEBUG)

        self.SRS.clear_status()

        self.SRS.SIM928_on_off[5] = 'OFF'
        self.SRS.SIM928_on_off[6] = 'OFF'

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
