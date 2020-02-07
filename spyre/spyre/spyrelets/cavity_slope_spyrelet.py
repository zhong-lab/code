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

from lantz.drivers.lockin import SR865A
from lantz.drivers.mwsource import SynthNVPro
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
        'lockin': SR865A,
        'source':SynthNVPro,
    }
    time_s=[]
    X_s=[]
    Y_s=[]
    R_s=[]
    theta_s=[]


    def slope(self,value):
        self.dataset.clear()
        log_to_screen(DEBUG)

        frequency_start = 5094 * MHz
        frequency_stop = 5100 * MHz
        frequency_step = 0.05 * MHz

        self.source.output = 1
        self.source.power = 0
        self.source.Trigger_Setting = 9
        self.source.Ext_FM_Type = 1
        self.source.Ext_FM_Deviation = value * Hz
        self.source.frequency = frequency_start
        time.sleep(5)

        with open('D:/MW data/test/20191012/slope/scan8/{}.txt'.format(value),'a') as file:
            write_str='%f %f %f %f %f\n'%(0,0,0,0,0)
            file.write(write_str)

        while(self.source.frequency<frequency_stop):
            buffer_D = self.lockin.Data_Four
            part = buffer_D.split(',')

            XValue = part[0]
            YValue = part[1]
            RValue = part[2]
            thetaValue = part[3]

            with open('D:/MW data/test/20191012/slope/scan8/{}.txt'.format(value),'a') as file:
                write_str='%s %s %s %s %f\n'%(part[0],part[1],part[2],part[3],self.source.frequency.magnitude)
                file.write(write_str)

            a = np.loadtxt('D:/MW data/test/20191012/slope/scan8/{}.txt'.format(value))
            self.X_s = a[1:,0]
            self.Y_s = a[1:,1]
            self.R_s = a[1:,2]
            self.theta_s = a[1:,3]
            self.time_s = a[1:,4]

            values = {
                    't': self.time_s,
                    'Y':self.Y_s,
                    'R':self.R_s,
                    'X': self.X_s,
                    'theta':self.theta_s,
                }

            self.Record_data_time.acquire(values)
            self.source.frequency = self.source.frequency + frequency_step
        return

    @Task()
    def Record_data_time(self):
        for D in range(100000,3000000,200000):
            self.slope(D)

        # for x in range(1,21):
        #     self.slope(x)
        return

    @Record_data_time.initializer
    def initialize(self):
        return

    @Record_data_time.finalizer
    def finalize(self):
        return  

    @Element(name='Histogram')
    def X_plot(self):
        p = LinePlotWidget()
        p.plot('X')
        return p

    @X_plot.on(Record_data_time.acquired)
    def X_plot_update(self, ev):
        w = ev.widget
        ts = np.array(self.time_s)
        Xs = np.array(self.X_s)
        w.set('X', xs=ts, ys=Xs)
        return

    @Element(name='Histogram')
    def Y_plot(self):
        p = LinePlotWidget()
        p.plot('Y')
        return p

    @Y_plot.on(Record_data_time.acquired)
    def Y_plot_update(self, ev):
        w = ev.widget
        ts = np.array(self.time_s)
        Ys = np.array(self.Y_s)
        w.set('Y', xs=ts, ys=Ys)
        return

    @Element(name='Histogram')
    def R_plot(self):
        p = LinePlotWidget()
        p.plot('R')
        return p

    @R_plot.on(Record_data_time.acquired)
    def R_plot_update(self, ev):
        w = ev.widget
        ts = np.array(self.time_s)
        Rs = np.array(self.R_s)
        w.set('R', xs=ts, ys=Rs)
        return

    @Element(name='Histogram')
    def theta_plot(self):
        p = LinePlotWidget()
        p.plot('R')
        return p

    @theta_plot.on(Record_data_time.acquired)
    def theta_plot_update(self, ev):
        w = ev.widget
        ts = np.array(self.time_s)
        thetas = np.array(self.theta_s)
        w.set('R', xs=ts, ys=thetas)
        return