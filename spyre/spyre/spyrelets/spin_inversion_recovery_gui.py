import numpy as np
import pyqtgraph as pg
import time
import random
import matplotlib.pyplot as plt
from PyQt5.Qsci import QsciScintilla, QsciLexerPython


from scipy import stats
import math
from scipy.optimize import curve_fit

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



    def record(self,tau1,tau2,pulse1,pulse2,trig):
        self.dataset.clear()
        # log_to_screen(DEBUG)

        edge_a = tau2  + pulse2*0.5 - pulse1*0.5
        edge_b = pulse1
        edge_c = edge_a + edge_b + tau1 - pulse2*0.5 - pulse1*0.5
        edge_d = pulse2
        edge_e = 0
        edge_f = pulse2

        self.delaygen.Trigger_Source='Internal'
        self.delaygen.delay['A']=edge_a*second
        self.delaygen.delay['B']=edge_b*second
        self.delaygen.delay['C']=edge_c*second
        self.delaygen.delay['D']=edge_d*second
        self.delaygen.delay['E']=edge_e*second
        self.delaygen.delay['F']=edge_f*second
        self.delaygen.trigger_rate=trig*Hz
        time.sleep(6)

        # print("Delay for a,b,c,d is {}, {}, {}, {}".format(edge_a,edge_b,edge_c,edge_d))

        self.osc.delaymode_on()
        self.osc.delay_position(0)
        self.osc.delay_time(tau2)

        # naverage=100
        # self.osc.setmode('average')
        # self.osc.average(naverage)
        # wait_time = naverage*1.1/trig
        time.sleep(2)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('D:/MW data/20191120/Test2/Tau_{}.txt'.format(tau2), np.c_[x,y])    

        echoarea=self.ComputeEcho(tau1,pulse1,x,y)



        self.delay_s.append(tau2*1e3)
        self.echo_s.append(echoarea)

        print(" Delay array  {}  echo array {}".format(self.delay_s,self.echo_s))

        values = {
                't': self.delay_s,
                'E':self.echo_s,
            }

        self.Record_Spin_Inversion.acquire(values)


        # self.osc.setmode('sample')

        # time.sleep(5)
        return

    def ComputeEcho(self,tau1,pulse1,T_list_k,V_list_k):


        tau1=tau1*1e6
        echo_int_area=20 #Echo integration area in microsecond
        echo_center=0.5*pulse1 + 2*tau1    

        offset=0
        offsetflag=True


        T_list_k=T_list_k*1e6
        V_list_k=V_list_k*1e3

        for x in range(0,len(T_list_k)):
            
            time = T_list_k[x]

            if (abs(V_list_k[x])>10) and (offsetflag):
                offset=T_list_k[x]
                # print(" offset is {}".format(offset))
                offsetflag=False


        echo_center=echo_center+offset

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


        print("Echo center is {}".format(echo_center))


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

        return(-1*echoarea)


    @Task()
    def Record_Spin_Inversion(self):
        params = self.pulse_parameters.widget.get()
        pulse1=0.5*params['Pi Length']*1e-6
        pulse2=params['Pi Length']*1e-6

        tau1=params['Tau1'].magnitude*1e-6
        trig = params['Trigger'].magnitude

        self.delay_s=[]
        self.echo_s=[]

        self.osc.datasource(2)
        self.osc.data_start(1)
        self.osc.data_stop(200000)
        self.osc.time_scale((pulse1+pulse2 + tau1)*0.5)  
        self.osc.setmode('sample')

        tau2_start=params['Tau2 start'].magnitude
        tau2_end=params['Tau2 end'].magnitude
        tau2_nstep=int(params['NStep'].magnitude)           
        # for tau2 in np.logspace(1,-4,40):
        for tau2 in np.linspace(tau2_start,tau2_end,tau2_nstep):

            self.record(tau1,tau2*1e-3,pulse1,pulse2,trig)

        self.osc.delaymode_off()
        return

    @Record_Spin_Inversion.initializer
    def initialize(self):
        return

    @Record_Spin_Inversion.finalizer
    def finalize(self):
        return  


    @Element(name='Pulse parameters')
    # Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
    def pulse_parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Trigger', {'type': float, 'default': 1, 'units':'dimensionless'}),
        ('Pi Length', {'type': float, 'default': 4, 'units':'dimensionless'}),
        ('Tau2 start', {'type': float, 'default': 12, 'units':'dimensionless'}),
        ('Tau2 end', {'type': float, 'default': 20, 'units':'dimensionless'}),
        ('Tau1', {'type': float, 'default': 11, 'units':'dimensionless'}),
        ('NStep', {'type': float, 'default': 5, 'units':'dimensionless'}),
        ('Num average', {'type': int, 'default': 1, 'units':'dimensionless'}),
        ]
        w = ParamWidget(params)
        return w




    @Element(name='Histogram')
    def T1_plot(self):
        p = LinePlotWidget()
        p.plot('T1')
        return p

    @T1_plot.on(Record_Spin_Inversion.acquired)
    def T1_plot_update(self, ev):
        w = ev.widget
        ds = np.array(self.delay_s)
        es = np.array(self.echo_s)
        w.set('T1', xs=ds, ys=es)
        return