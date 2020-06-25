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
from lantz.drivers.thorlabs.pm100d import PM100D

from lantz import Q_
import time

import nidaqmx

class Test(Spyrelet):

    requires = {
        'pmd':PM100D

    }
    """
    daq = nidaqmx.Task()
    daq.ai_channels.add_ai_voltage_chan("Dev1/ai6")
    """
    xs = []
    ys = []

    @Task()
    def HardPull(self):
        param=self.parameters.widget.get()     
        filename = param['Filename']
        F =open(filename+'.dat','w')
        self.xs=[]
        self.ys=[]
        t0 = time.time()
        while True:
            t1 = time.time()
            t = t1 - t0
            self.xs.append(t)
            power=self.pmd.power.magnitude
            #power = self.daq.read()
            self.ys.append(power)

            if(len(self.xs)>400):
                self.xs=[]
                self.ys=[]
            values = {
                  'x': self.xs,
                  'y': self.ys,
                  }

            self.HardPull.acquire(values)
            time.sleep(0.01)
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
        if (len(xs)>len(ys)):
            xs = xs[:len(ys)]
        w.set('Transmission Power', xs=xs, ys=ys)
        return

    def initialize(self):
        return

    def finalize(self):
        return
    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        
        ('Filename', {'type': str, 'default':'D:\\Data\\Fiberpulling\\'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w

