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



    def record(self,tau1,tau2,pulse1,pulse2,trig):
        self.dataset.clear()
        log_to_screen(DEBUG)

        edge_a = tau2  + pulse2*0.5 - pulse1*0.5
        edge_b = pulse1
        edge_c = edge_a + edge_b + tau1 - pulse2*0.5 - pulse1*0.5
        edge_d = pulse2
        edge_e = 0
        edge_f = pulse2

        self.delaygen.Trigger_Source='Internal'
        self.delaygen.delay['A']=edge_a
        self.delaygen.delay['B']=edge_b
        self.delaygen.delay['C']=edge_c
        self.delaygen.delay['D']=edge_d
        self.delaygen.delay['E']=edge_e
        self.delaygen.delay['F']=edge_f
        self.delaygen.trigger_rate=trig
        time.sleep(5)

        # print("Delay for a,b,c,d is {}, {}, {}, {}".format(edge_a,edge_b,edge_c,edge_d))

        self.osc.delaymode_on()
        self.osc.delay_position(0)
        self.osc.delay_time(tau2)

        naverage=100
        self.osc.setmode('average')
        self.osc.average(naverage)
        wait_time = naverage*1.1/trig
        time.sleep(wait_time)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('D:/MW data/20191118/Test6/Tau_{}.txt'.format(tau2), np.c_[x,y])    


        self.osc.setmode('sample')

        time.sleep(5)
        return


    @Task()
    def Record_Spin_Inversion(self):
        # for D in range(11e-6,200e-6,10e-6):
        pulse1=2e-6
        pulse2=4e-6
        tau1=20e-6
        trig=0.1

        self.osc.datasource(2)
        self.osc.data_start(1)
        self.osc.data_stop(500000)
        self.osc.time_scale((pulse1+pulse2 + tau1)*0.5)  
              
        for tau2 in np.logspace(1,-4,40):
        # for tau2 in np.linspace(1e-3,10000e-3,20):

            self.record(tau1,tau2,pulse1,pulse2,trig)
        return

    @Record_Spin_Inversion.initializer
    def initialize(self):
        return

    @Record_Spin_Inversion.finalizer
    def finalize(self):
        return  


