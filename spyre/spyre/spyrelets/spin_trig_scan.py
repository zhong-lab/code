import numpy as np
import pyqtgraph as pg
import time
import random
import matplotlib.pyplot as plt
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget,HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import os

from lantz.drivers.stanford import DG645
from lantz.drivers.mwsource import SynthNVPro
from lantz.drivers.tektronix import TDS5104

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')


class Record(Spyrelet):
    
    requires = {
        'osc': TDS5104,
        'source': SynthNVPro,
        'delaygen': DG645,
    }



    def record(self,tau,pulse1,pulse2,trig):
        self.dataset.clear()
        log_to_screen(DEBUG)

        edge_a = 0
        edge_b = pulse1
        edge_c = edge_b + tau - pulse2*0.5 - pulse1*0.5
        edge_d = pulse2


        self.delaygen.Trigger_Source='Internal'
        self.delaygen.trigger_rate=trig 
        self.delaygen.delay['A']=edge_a
        self.delaygen.delay['B']=edge_b
        self.delaygen.delay['C']=edge_c
        self.delaygen.delay['D']=edge_d

        time.sleep(5)

        print("Delay for a,b,c,d is {}, {}, {}, {}".format(edge_a,edge_b,edge_c,edge_d))

        naverage  = 20     
        sleeptime=(1.0/trig)*naverage  

        self.osc.datasource(2)
        self.osc.setmode('average')
        self.osc.average(naverage)
        
        time.sleep(sleeptime)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('D:/MW data/20191112/Test1/Trig_{}.txt'.format(trig), np.c_[x,y])    


        self.osc.setmode('sample')

        time.sleep(2)
        return


    @Task()
    def Record_Spin_Echo(self):
        # for D in range(11e-6,200e-6,10e-6):
        tau=11e-6
        pulse1=2e-6
        pulse2=4e-6

        for trig in np.arange(0.01,1,0.04):
            self.record(tau,pulse1,pulse2,trig)
        return

    @Record_Spin_Echo.initializer
    def initialize(self):
        return

    @Record_Spin_Echo.finalizer
    def finalize(self):
        return  


