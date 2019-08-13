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
    }
    atc=ANC350()
    atc.initialize()
    axis_index_x=0
    axis_index_y=1
    axis_index_z=2
    f = open("C:\\Users\\Tian Zhong\\Tao\\test.txt",'w')
    f.write("xPosition/um,yPosition/um,zPosition/um \n")
    ts = []
    xs = []
    ys = []
    zs = []

    @Task()
    def SensorNoise(self):
        print(self.atc.status[1])
        t0 = time.time()
        while True:
            t1 = time.time()
            t = t1 - t0
            self.ts.append(t)
            x = self.atc.position[self.axis_index_x].magnitude
            y = self.atc.position[self.axis_index_y].magnitude
            z = self.atc.position[self.axis_index_z].magnitude
            self.xs.append(x)
            self.ys.append(y)
            self.zs.append(z)
            self.f.write("%f,%f,%f \n" %(x,y,z))

            values = {
                  't': self.ts,
                  'x': self.xs,
                  'y': self.ys,
                  'z': self.zs,
                  }
            self.SensorNoise.acquire(values)
            time.sleep(0.1)
            if len(self.ts)>3600*5:
                break
        return
  
    @Element(name='x')
    def averagedx(self):
        p = LinePlotWidget()
        p.plot('xPosition')
        return p
    @Element(name='y')
    def averagedy(self):
        p = LinePlotWidget()
        p.plot('yPosition')
        return p
    @Element(name='z')
    def averagedz(self):
        p = LinePlotWidget()
        p.plot('zPosition')
        return p

    @averagedx.on(SensorNoise.acquired)
    def averagedx_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        xs = np.array(self.xs)
        self.fluc_x = max(xs)-min(xs)

        w.set('xPosition', xs=ts, ys=xs)

        return

    @averagedy.on(SensorNoise.acquired)
    def averagedy_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        ys = np.array(self.ys)
        self.fluc_y = max(ys)-min(ys)

        w.set('yPosition',xs=ts,ys=ys)
        return

    @averagedz.on(SensorNoise.acquired)
    def averagedz_update(self, ev):
        w = ev.widget
        ts = np.array(self.ts)
        ys = np.array(self.zs)
        self.fluc_z = max(ys)-min(ys)
        w.set('zPosition', xs=ts, ys=ys)
        print('fluc x: %f fluc y: %f fluc z: %f'%(self.fluc_x,self.fluc_y,self.fluc_z))
        return

    @SensorNoise.initializer
    def initialize(self):
        self.atc = ANC350()
        self.atc.initialize()
        return

    @SensorNoise.finalizer
    def finalize(self):
        self.f.close()
        return
