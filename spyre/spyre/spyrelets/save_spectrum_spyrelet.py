import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import os

from lantz.drivers.spectrum import MS2721B
from lantz.log import log_to_screen, DEBUG

class SpectrumAnalyzer(Spyrelet):

    requires = {
        'spa': MS2721B
    }

    @Task()
    def set(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        freq_params = self.Frequency_Settings.widget.get()
        # amp_params = self.Frequency_Settings.widget.get()
        span = freq_params['frequency span']
        center = freq_params['center freq']
        self.spa.freq_span = span
        self.spa.freq_cent = center
        # self.spa.ref_level = ref
        # self.spa.freq_star = start

    @set.initializer
    def initialize(self):
        return

    @set.finalizer
    def finalize(self):
        return



    @Task()
    def save(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        save_params = self.Save_Settings.widget.get()

        t = save_params['sleep time']
        count = save_params['file count']

        for x in range(count):
            self.spa.savefile(x)
            time.sleep(t)

    @save.initializer
    def initialize(self):
        return

    @save.finalizer
    def finalize(self):
        return



    @Element()
    def Frequency_Settings(self):
        freq_params = [
        ('frequency span', {'type': float, 'default': 3000, 'units': 'Hz'}),
        ('center freq', {'type': float, 'default': 30000000, 'units': 'Hz'}),
        ]
        w = ParamWidget(freq_params)
        return w


    @Element()
    def Save_Settings(self):
        save_params = [
        ('sleep time', {'type': float, 'default': 30}),
        ('file count', {'type': int, 'default': 10}),
        ]
        w = ParamWidget(save_params)
        return w
