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

import nidaqmx

class Test(Spyrelet):
    requires = {

    }
    daq = nidaqmx.Task()
    daq.ai_channels.add_ai_voltage_chan("Dev1/ai6")
    xs = []
    ys = []

    @Task() # task is something you run
    def HardPull(self): # hardpull because this spyrelet was adapted from the
    # fiber-pulling spyrelet
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
            power = self.daq.read() 
            self.ys.append(power)

            if(len(self.xs)>3000): # empty and repeat data collection every 3000 points
            # can this be set as a parameter?
                self.xs=[]
                self.ys=[]
            values = {
                  'x': self.xs,
                  'y': self.ys,
                  }

            self.HardPull.acquire(values)
            time.sleep(0.01) # wait 10ms between the capture of each data point
        return
  
    @Element(name='Histogram') # element is something displayed
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Transmission Power') # setting the name of the figure
        return p

    @averaged.on(HardPull.acquired)
    def averaged_update(self, ev):
        w = ev.widget # what is ev?
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        if (len(xs)>len(ys)): # only consider the points for which data was
        # already captured
            xs = xs[:len(ys)]
        w.set('Transmission Power', xs=xs, ys=ys)
        return

    def initialize(self): 
        # important for turning on/off equipment, etc.
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

