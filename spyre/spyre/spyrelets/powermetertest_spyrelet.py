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
    f = open('D:\\Data\\8.19.2019\\powertest.dat','w')

    @Task()
    def HardPull(self):
        t0 = time.time()
        while True:
            t1 = time.time()
            t = t1 - t0
            self.xs.append(t)
            power = self.pmd.power.magnitude * 1000
            self.ys.append(power)
            values = {
                  'x': self.xs,
                  'y': self.ys,
                  }

            self.HardPull.acquire(values)
            time.sleep(0.005)
            self.f.write('%f,'%power)

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
        
        if(len(self.xs)>1000):
            self.xs=[]
            self.ys=[]
        if len(xs)>len(ys):
            xs=xs[:len(ys)]
        if len(ys)>len(xs):
            ys=ys[:len(xs)]        
        w.set('Transmission Power', xs=xs, ys=ys)
        return

    def initialize(self):
        return

    def finalize(self):
        return

