import numpy as np
import pyqtgraph as pg
import time
import random
import matplotlib.pyplot as plt

from scipy import stats
import math
from scipy.optimize import curve_fit

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
second = Q_(1, 's')

class Record(Spyrelet):
    
    requires = {
        'osc': TDS5104,
        'source': SynthNVPro,
        'delaygen': DG645,
    }



    def record(self,tau,tau1,pulse1,pulse2,pulse3):
        params = self.pulse_parameters.widget.get()
        self.dataset.clear()
        log_to_screen(DEBUG)

        edge_a = 0
        if(pulse3>0):
            edge_a = tau1+pulse3*0.5 - pulse1*0.5


        
        edge_b = pulse1
        edge_c = edge_a + edge_b + tau - pulse2*0.5 - pulse1*0.5 
        edge_d = pulse2
        edge_e = 0
        edge_f = pulse3

        trig = params['Trigger'].magnitude

        self.delaygen.Trigger_Source='Internal'
        self.delaygen.trigger_rate=trig*Hz
        self.delaygen.delay['A']=edge_a*second
        self.delaygen.delay['B']=edge_b*second
        self.delaygen.delay['C']=edge_c*second
        self.delaygen.delay['D']=edge_d*second
        self.delaygen.delay['E']=edge_e*second
        self.delaygen.delay['F']=edge_f*second

        time.sleep(5)

        print("Delay for a,b,c,d is {}, {}, {}, {}".format(edge_a,edge_b,edge_c,edge_d))

        naverage = 40
        self.osc.setmode('average')
        self.osc.average(naverage)
        
        time.sleep(naverage/trig)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('D:/MW data/20191120/Test3/pulse.txt', np.c_[x,y])    


        self.delay_s = x
        self.echo_s = y


        values = {
                't': self.delay_s,
                'E':self.echo_s,
            }

        self.Record_Spin_Pulse.acquire(values)

        self.osc.setmode('sample')

        # time.sleep(1)
        return




    @Task()
    def Record_Spin_Pulse(self):
        # for D in range(11e-6,200e-6,10e-6):
        params = self.pulse_parameters.widget.get()
        pulse1=params['Pulse1 Length']*1e-6
        numpulse=params['Num pulse'].magnitude
        print("numpulse {}".format(numpulse))
        pulse2=0
        pulse3=0
        tau=0
        tau1=0
        if numpulse == 2:
            pulse2=params['Pulse2 Length'].magnitude*1e-6
            tau=params['Tau']*1e-6

        if numpulse == 3:
            pulse2=params['Pulse2 Length'].magnitude*1e-6
            pulse3=params['Pulse3 Length'].magnitude*1e-6
            tau1=params['Tau1']*1e-6
            tau=params['Tau']*1e-6


        print(" Pulse2 is {}".format(pulse2))

        

        self.delay_s=[]
        self.echo_s=[]
        self.osc.datasource(2)
        self.osc.data_start(1)
        self.osc.data_stop(400000) 

        timescale = 20e-6
        self.osc.time_scale(timescale)
        self.osc.setmode('sample')


        self.record(tau,tau1,pulse1,pulse2,pulse3)

        # self.source.output = 0 # Turn off the damn source

        return

    @Record_Spin_Pulse.initializer
    def initialize(self):
        return

    @Record_Spin_Pulse.finalizer
    def finalize(self):
        return  


    @Element(name='Pulse parameters')
    # Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
    def pulse_parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Trigger', {'type': float, 'default': 1, 'units':'dimensionless'}),
        ('Pulse1 Length', {'type': float, 'default': 2, 'units':'dimensionless'}),
        ('Pulse2 Length', {'type': float, 'default': 4, 'units':'dimensionless'}),
        ('Pulse3 Length', {'type': float, 'default': 4, 'units':'dimensionless'}),
        ('Tau', {'type': float, 'default': 10, 'units':'dimensionless'}),
        ('Tau1', {'type': float, 'default': 10, 'units':'dimensionless'}),
        ('Num pulse', {'type': int, 'default': 1, 'units':'dimensionless'}),
        ]
        w = ParamWidget(params)
        return w



    @Element(name='Histogram')
    def Pulse_plot(self):
        p = LinePlotWidget()
        p.plot('Pulse')
        return p

    @Pulse_plot.on(Record_Spin_Pulse.acquired)
    def Pulse_plot_update(self, ev):
        w = ev.widget
        ds = np.array(self.delay_s)
        es = np.array(self.echo_s)
        w.set('Pulse', xs=ds, ys=es)
        return