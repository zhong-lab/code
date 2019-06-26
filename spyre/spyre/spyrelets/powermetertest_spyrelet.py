import numpy as np
import pyqtgraph as pg
import time
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.thorlabs.pm100d import PM100D

class Test(Spyrelet):
    requires = {
        'pmd': PM100D
    }

    xs = []
    ys = []

    @Task()
    def HardPull(self):
        t0 = time.time()
        while True:
            t1 = time.time()
            t = t1 - t0
            self.xs.append(t)
            self.ys.append(self.pmd.power.magnitude * 1000)
            values = {
                  'x': self.xs,
                  'y': self.ys,
                  }

            self.HardPull.acquire(values)
            time.sleep(1)
        return
  
    @Element(name='Histogram')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Transmission Power')
        return p

    @averaged.on(HardPull.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        w.set('Transmission Power', xs=xs, ys=ys)
        # print(xs)
        # print(ys)
        return

    def initialize(self):
        return

    def finalize(self):
        return

