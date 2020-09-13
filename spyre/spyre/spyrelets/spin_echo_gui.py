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



    def record(self,tau,pulse1,pulse2):
        params = self.pulse_parameters.widget.get()
        self.dataset.clear()
        # log_to_screen(DEBUG)

        edge_a = 0
        edge_b = pulse1
        edge_c = edge_b + tau - pulse2*0.5 - pulse1*0.5 
        edge_d = pulse2


        trig = params['Trigger'].magnitude

        self.delaygen.Trigger_Source='Internal'
        self.delaygen.trigger_rate=trig*Hz
        self.delaygen.delay['A']=edge_a*second
        self.delaygen.delay['B']=edge_b*second
        self.delaygen.delay['C']=edge_c*second
        self.delaygen.delay['D']=edge_d*second

        time.sleep(5)

        print("Delay for a,b,c,d is {}, {}, {}, {}".format(edge_a,edge_b,edge_c,edge_d))

        # naverage = params['Num average'].magnitude
        # self.osc.setmode('average')
        # self.osc.average(naverage)
        
        time.sleep(1/trig)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('D:/MW data/20191120/Test1/Tau_{}.txt'.format(tau*1e6), np.c_[x,y])    

        echoarea=self.ComputeEcho(tau,pulse1,pulse2,x,y)



        self.delay_s.append(tau*1e6)
        self.echo_s.append(echoarea)

        print(" Delay array  {}  echo array {}".format(self.delay_s,self.echo_s))

        values = {
                't': self.delay_s,
                'E':self.echo_s,
            }

        self.Record_Spin_Echo.acquire(values)

        # self.osc.setmode('sample')

        # time.sleep(1)
        return


    def ComputeEcho(self,tau,pulse1,pulse2,T_list_k,V_list_k):
        
    


        tau=tau*1e6
        pulse1=pulse1*1e6
        pulse2=pulse2*1e6
        a_edge=0 #Rising edge of Pi/2 pulse
        b_edge=a_edge+pulse1 #Falling edge of Pi/2 pulse
        c_edge=(a_edge+b_edge)*0.5 + tau - pulse2*0.5 #Rising edge of Pi pulse
        d_edge=c_edge+pulse2   # Falling edge -of Pi pulse


        T_list_k= T_list_k*1e6
        V_list_k= V_list_k*1e3

        echo_int_area=10.5 #Echo integration area in microsecond
        echo_center=(c_edge+d_edge)*0.5+tau 

        offset=0
        offsetflag=True

        for x in range(0,len(T_list_k)):
            
            time = T_list_k[x]

            if (abs(V_list_k[x])>200) and (offsetflag):
                offset=T_list_k[x]
                # print(" offset is {}".format(offset))
                offsetflag=False


        echo_center=echo_center+offset


        print("******** Echo center is {}  *************".format(echo_center))

        echo_offset=0

        echo_edge1=echo_center-0.5*echo_int_area
        echo_edge2=echo_center+0.5*echo_int_area

        back_int_width=0.5

        back_edge1 = echo_edge1 - back_int_width
        back_edge2 = echo_edge2 + back_int_width

        echoarray=[]
        echotimearray=[]

        backarray=[]
        backtimearray=[]

        for x in range(0,len(T_list_k)):
            
            time = T_list_k[x]

            if (time>echo_edge1) and (time<echo_edge2):
                echoarray.append(V_list_k[x])
                echotimearray.append(time)
            elif ((time>back_edge1) and (time<echo_edge1)) or ((time<back_edge2) and (time>echo_edge2)) :

                backarray.append(V_list_k[x])
                backtimearray.append(time)



        echoarray=np.array(echoarray)
        echotimearray=np.array(echotimearray)   

        backarray=np.array(backarray)
        backtimearray=np.array(backtimearray)

        slope, intercept, r_value, p_value, std_err = stats.linregress(backtimearray,backarray)


        echoarea=0
        for x in range(1,len(echotimearray)):
            
            time=echotimearray[x]
            backgnd=slope*time + intercept
            echoarea=echoarea + (echoarray[x]-backgnd)

        return(abs(echoarea))


    @Task()
    def Record_Spin_Echo(self):
        # for D in range(11e-6,200e-6,10e-6):
        params = self.pulse_parameters.widget.get()
        pulse1=0.5*params['Pi Length']*1e-6
        pulse2=params['Pi Length']*1e-6

        # pulse1=2e-6
        # pulse2=4e-6
        self.delay_s=[]
        self.echo_s=[]
        self.osc.datasource(2)
        self.osc.data_start(1)
        self.osc.data_stop(400000) 
        self.osc.time_scale(40e-6)
        self.osc.setmode('sample')
        tau_start=params['Tau start'].magnitude
        tau_end=params['Tau end'].magnitude
        tau_step=params['Step Tau'].magnitude

        for tau in np.arange(tau_start,tau_end,tau_step):
            self.record(tau*1e-6,pulse1,pulse2)

        # self.source.output = 0 # Turn off the damn source

        return

    @Record_Spin_Echo.initializer
    def initialize(self):
        return

    @Record_Spin_Echo.finalizer
    def finalize(self):
        return  


    @Element(name='Pulse parameters')
    # Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
    def pulse_parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Trigger', {'type': float, 'default': 1, 'units':'dimensionless'}),
        ('Pi Length', {'type': float, 'default': 4, 'units':'dimensionless'}),
        ('Tau start', {'type': float, 'default': 12, 'units':'dimensionless'}),
        ('Tau end', {'type': float, 'default': 20, 'units':'dimensionless'}),
        ('Step Tau', {'type': float, 'default': 5, 'units':'dimensionless'}),
        ('Num average', {'type': int, 'default': 1, 'units':'dimensionless'}),
        ]
        w = ParamWidget(params)
        return w



    @Element(name='Histogram')
    def T2_plot(self):
        p = LinePlotWidget()
        p.plot('T2')
        return p

    @T2_plot.on(Record_Spin_Echo.acquired)
    def T2_plot_update(self, ev):
        w = ev.widget
        ds = np.array(self.delay_s)
        es = np.array(self.echo_s)
        w.set('T2', xs=ds, ys=es)
        return