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

from lantz.drivers.VNA import P9371A
from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

channel=1
freq_low=5070
freq_size=0.02
freq_list=[]
S12_list=[]
x_count=1000
y_count=1
power=-40


class Record(Spyrelet):
    
    requires = {
        'vna': P9371A
    }
    qutag = None
    times=[]
    freqs=[]
    Qs=[]
    Qis=[]
    Qes=[]
    dips=[]

    @Task()
    def set_vna_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        vna_freq_params = self.VNA_Frequency_Settings.widget.get()

        span = vna_freq_params['frequency span']
        center = vna_freq_params['center freq']

        self.vna.freq_span = span
        self.vna.freq_cent = center
        
    @set_vna_freq.initializer
    def initialize(self):
        return

    @set_vna_freq.finalizer
    def finalize(self):
        return

    @Task()
    def set_vna_marker(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        vna_marker_params = self.VNA_Marker_Settings.widget.get()
        chnl = vna_marker_params['channel']
        stat = vna_marker_params['state']

        self.vna.marker[chnl] = stat


    @set_vna_marker.initializer
    def initialize(self):
        return

    @set_vna_marker.finalizer
    def finalize(self):
        return   

        

    @Task()
    def Record_data_time(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        record_cavity_params = self.Record_cavity_Settings.widget.get()
        f_cent = record_cavity_params['center frequency']
        f_span = record_cavity_params['span']
        t = record_cavity_params['sleep time in second']
        stop = record_cavity_params['stop time in second']
        name = record_cavity_params['txt name']

        v_chnl = 1
        l_chnl = 2
        r_chnl = 3    


        time_0 = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds

        #while(self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds-time_0 <= stop):
        while(1):
            # self.vna.freq_cent = f_cent
            # self.vna.freq_span = f_span

            self.vna.auto_scale()
            self.vna.auto_scale_second()
        

            self.vna.marker[v_chnl] = 'ON'
            self.vna.marker[l_chnl] = 'ON'
            self.vna.marker[r_chnl] = 'ON'
            self.vna.marker_second[v_chnl] = 'ON'
            self.vna.marker_second[l_chnl] = 'ON'
            self.vna.marker_second[r_chnl] = 'ON'

            self.vna.marker_peak_search[v_chnl]
            max_value = self.vna.marker_Y[v_chnl]
            A_0 = self.vna.marker_Y[v_chnl].magnitude

            self.vna.marker_min_search[v_chnl]
            min_value = self.vna.marker_Y[v_chnl]
            A_1 = self.vna.marker_Y[v_chnl].magnitude

            target = (max_value + min_value)/2
            A = A_0 - A_1
            portion = 10**((A_1 - A_0)/20)

            self.vna.target_value[l_chnl] = target
            self.vna.target_value[r_chnl] = target
            self.vna.marker_min_search[l_chnl]
            self.vna.marker_target_left_search[l_chnl]
            self.vna.marker_min_search[r_chnl]
            self.vna.marker_target_right_search[r_chnl]

            half = self.vna.marker_X[r_chnl].magnitude - self.vna.marker_X[l_chnl].magnitude
            larger = (portion*half + half)/2
            smaller = half - larger

            time_now = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds
            delta_time = time_now-time_0
            power = self.vna.marker_Y[v_chnl].magnitude
            frequency = self.vna.marker_X[v_chnl].magnitude

            start_field = 240
            ramp_rate = 0.2/60
            field = start_field + delta_time*ramp_rate

            Q = frequency/half
            Q_smaller = frequency/larger
            Q_larger = frequency/smaller

            self.vna.marker_peak_search_second[r_chnl]
            self.vna.marker_min_search_second[l_chnl]
            L_x = self.vna.marker_X_second[l_chnl].magnitude
            L_y = self.vna.marker_Y_second[l_chnl].magnitude
            R_x = self.vna.marker_X_second[r_chnl].magnitude
            R_y = self.vna.marker_Y_second[r_chnl].magnitude
            delta_x = R_x - L_x
            delta_y = R_y - L_y
            self.vna.marker_X_second[v_chnl]=(L_x+R_x)/2*Hz

            self.times.append(delta_time)
            self.freqs.append(frequency)
            self.Qs.append(Q)
            self.Qis.append(Q_smaller)
            self.Qes.append(Q_larger)
            self.dips.append(A)
            values = {
                    't': self.times,
                    'f': self.freqs,
                    'Q': self.Qs,
                    'Qi': self.Qis,
                    'Qe': self.Qes,
                    'dip': self.dips,
                }
            self.Record_data_time.acquire(values)

            with open('D:/MW data/test/20190810/cavity/scan_5/YZscan/scan10/{}.txt'.format(name),'a') as file:
                write_str='%f %f %f %f %f %f %f %f %f %f %f %f %f %f %f\n'%(frequency,power,delta_time,A,half,Q,Q_smaller,Q_larger,L_x,L_y,R_x,R_y,field,delta_x,delta_y)
                file.write(write_str)
            self.vna.save_csv('D:/MW data/test/20190810/cavity/scan_5/YZscan/scan10/amplitude/{}.csv'.format(field))
            self.vna.save_csv_second('D:/MW data/test/20190810/cavity/scan_5/YZscan/scan10/phase/{}.csv'.format(field))
            time.sleep(t)
        return

    @Record_data_time.initializer
    def initialize(self):
        return

    @Record_data_time.finalizer
    def finalize(self):
        return

    @Element(name='Histogram')
    def Resonance_frequency(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        return p

    @Resonance_frequency.on(Record_data_time.acquired)
    def Resonance_frequency_update(self, ev):
        w = ev.widget
        ts = np.array(self.times)
        fs = np.array(self.freqs)
        w.set('Channel 1', xs=ts, ys=fs)
        return

    @Element(name='Histogram')
    def Q(self):
        p = LinePlotWidget()
        p.plot('Q')
        p.plot('Qi')
        p.plot('Qe')
        return p

    @Q.on(Record_data_time.acquired)
    def Q_update(self, ev):
        w = ev.widget
        ts = np.array(self.times)
        Qs = np.array(self.Qs)
        Qes = np.array(self.Qes)
        Qis = np.array(self.Qis)
        w.set('Q', xs=ts, ys=Qs)
        w.set('Qe', xs=ts, ys=Qes)
        w.set('Qi', xs=ts, ys=Qis)         
        return


    @Element(name='Histogram')
    def cavity_dip(self):
        p = LinePlotWidget()
        p.plot('Channel 1')
        return p

    @cavity_dip.on(Record_data_time.acquired)
    def cavity_dip_update(self, ev):
        w = ev.widget
        ts = np.array(self.times)
        dips = np.array(self.dips)
        w.set('Channel 1', xs=ts, ys=dips)
        return

    @Element()
    def VNA_Frequency_Settings(self):
        vna_freq_params = [
        ('frequency span', {'type': float, 'default': 1000000, 'units': 'Hz'}),
        ('center freq', {'type': float, 'default': 4000000000, 'units': 'Hz'}),
        ]
        w = ParamWidget(vna_freq_params)
        return w


    @Element()
    def VNA_Marker_Settings(self):
        vna_marker_params = [
        ('channel', {'type': int, 'default': 1}),
        ('state', {'type': str, 'default': 'OFF'}),
        ]
        w = ParamWidget(vna_marker_params)
        return w
  

    @Element()
    def Record_cavity_Settings(self):
        record_cavity_params = [
        ('center frequency', {'type': float, 'default': 5000,'units':'MHz'}),
        ('span', {'type': float, 'default': 40,'units': 'MHz'}),        
        ('sleep time in second', {'type': float, 'default': 1}),
        ('stop time in second', {'type': float, 'default': 1000}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(record_cavity_params)
        return w

    # @Element(name='Histogram')
    # def Q(self):
    #     p = LinePlotWidget()
    #     p.plot('Channel 1')
    #     return p

    # @Q.on(Record_data_time.acquired)
    # def Q_update(self, ev):
    #     w = ev.widget
    #     ts = np.array(self.times)
    #     Qs = np.array(self.Qs)
    #     w.set('Channel 1', xs=ts, ys=Qs)    
    #     return

    # @Element(name='Histogram')
    # def Qi(self):
    #     p = LinePlotWidget()
    #     p.plot('Channel 1')
    #     return p

    # @Qi.on(Record_data_time.acquired)
    # def Qi_update(self, ev):
    #     w = ev.widget
    #     ts = np.array(self.times)
    #     Qis = np.array(self.Qis)
    #     w.set('Channel 1', xs=ts, ys=Qis)
    #     return

    # @Element(name='Histogram')
    # def Qe(self):
    #     p = LinePlotWidget()
    #     p.plot('Channel 1')
    #     return p

    # @Qe.on(Record_data_time.acquired)
    # def Qe_update(self, ev):
    #     w = ev.widget
    #     ts = np.array(self.times)
    #     Qes = np.array(self.Qes)
    #     w.set('Channel 1', xs=ts, ys=Qes)
    #     return