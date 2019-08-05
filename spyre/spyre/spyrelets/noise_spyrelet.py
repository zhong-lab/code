'''
a test script for attocube noise
'''
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

from lantz.drivers.attocube import ANC350

class Test(Spyrelet):
    requires = {
        'atc': ANC350
    }

    ts = []
    xs = []
    ys = []
    zs = []

    @Task()
    def SensorNoise(self):
        t0 = time.time()
        while True:
            t1 = time.time()
            t = t1 - t0
            self.ts.append(t)
            self.xs.append(self.atc.position[axis_index_x])
            self.ys.append(self.atc.position[axis_index_y])
            self.zs.append(self.atc.position[axis_index_z])
            values = {
                  't': self.ts,
                  'x': self.xs,
                  'y': self.ys,
                  'z': self.zs,
                  }

            self.SensorNoise.acquire(values)
            time.sleep(1)
        return
  
    @Element(name='x')
    def averagedx(self):
        p = LinePlotWidget()
        p.plot('x Position')
        return p
    @Element(name='y')
    def averagedy(self):
        p = LinePlotWidget()
        p.plot('y Position')
        return p
    @Element(name='z')
    def averagedz(self):
        p = LinePlotWidget()
        p.plot('z Position')
        return p

    @averagedx.on(SensorNoise.acquired)
    def averagedx_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        xs = np.array(self.xs)
        w.set('x Position', xs=ts, ys=xs)
        return

    @averagedy.on(SensorNoise.acquired)
    def averagedy_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        ys = np.array(self.ys)
        w.set('y Position', xs=ts, ys=ys)
        return

    @averagedy.on(SensorNoise.acquired)
    def averagedz_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        ys = np.array(self.zs)
        w.set('z Position', xs=ts, ys=ys)
        return

    def initialize(self):
        return

    def finalize(self):
        return