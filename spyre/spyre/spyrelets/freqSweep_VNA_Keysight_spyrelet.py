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

from lantz.drivers.VNA_Keysight import E5071B
from lantz.drivers.mwsource import SynthNVPro
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


class Sweep(Spyrelet):
    
    requires = {
        'vna': E5071B,
        'source': SynthNVPro
    }
    qutag = None
    freqs=[]
    powers=[]
     

    @Task()
    def sweep_frequency(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        sweep_frequency_params = self.Sweep_frequency_Settings.widget.get()
        mk_freq = sweep_frequency_params['marker frequency']
        fr_low = sweep_frequency_params['start frequency']
        fr_high = sweep_frequency_params['stop frequency']
        fr_stp = sweep_frequency_params['step']
        t_stp = sweep_frequency_params['step time']
        pw = sweep_frequency_params['sweep power']
        name = sweep_frequency_params['txt name']
        t = sweep_frequency_params['sleep time']
        chnl = sweep_frequency_params['marker channel']

        self.vna.marker[chnl] = 'ON'
        self.vna.marker_X[chnl] = mk_freq

        self.source.sweep_lower=fr_low
        self.source.sweep_upper=fr_high
        self.source.sweep_size=fr_stp
        self.source.sweep_step_time=t_stp
        self.source.power=pw
        self.source.sweep_power_high = pw
        self.source.sweep_power_low = pw

        self.source.sweep_run=0
        time.sleep(5)

        self.source.output=1
        self.source.sweep_run=1

        time_0 = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds

        while(int(self.source.sweep_run)!=0):
            power=self.vna.marker_Y[chnl].magnitude
            frequency=self.source.frequency.magnitude

            time_now = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds
            delta_time = time_now-time_0

            self.freqs.append(frequency)
            self.powers.append(power)

            with open('D:/MW data/test/20191008/JTWPA/frequency sweep/scan_5/{}.txt'.format(name),'a') as file:
                write_str='%f %f\n'%(frequency,power)
                file.write(write_str)
            self.vna.save_csv('D:/20191008/{}.csv'.format(delta_time))
            #self.vna.save_csv_second('D:/MW data/test/20190813/JTWPA/scan_1/phase/{}.csv'.format(delta_time))
            time.sleep(t)
        return

    @sweep_frequency.initializer
    def initialize(self):
        return

    @sweep_frequency.finalizer
    def finalize(self):
        return

    @Task()
    def sweep_power_frequency(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        sweep_pw_fr_params = self.Sweep_Power_and_Frequency_Settings.widget.get()

        mk_freq = sweep_pw_fr_params['marker frequency']
        p_low = sweep_pw_fr_params['start power']
        p_high = sweep_pw_fr_params['stop power']
        p_stp = sweep_pw_fr_params['step power']
        fr_low = sweep_pw_fr_params['start frequency']
        fr_high = sweep_pw_fr_params['stop frequency']
        fr_stp = sweep_pw_fr_params['step frequency']
        stp_t = sweep_pw_fr_params['step time']
        name = sweep_pw_fr_params['txt name']
        t = sweep_pw_fr_params['sleep time']
        chnl = sweep_pw_fr_params['marker channel']

        self.vna.marker[chnl] = 'ON'
        self.vna.marker_X[chnl] = mk_freq

        self.source.sweep_lower=fr_low
        self.source.sweep_upper=fr_high
        self.source.sweep_size=fr_stp
        self.source.sweep_step_time=stp_t

        self.source.Trigger_Setting = 0
        self.source.output=1

        pw_count=(p_high-p_low)/p_stp
        self.source.sweep_run=0
        time.sleep(5)
        for pw_point in range(int(pw_count)):
            pw_current_value=p_low+pw_point*p_stp
            self.source.sweep_power_low=pw_current_value
            self.source.sweep_power_high=pw_current_value
            self.source.sweep_run=1
            while(int(self.source.sweep_run)!=0):
                #self.vna.marker_peak_search[chnl]
                S=self.vna.marker_Y[chnl].magnitude
                frequency=self.source.frequency.magnitude
                power=float(self.source.power)
                with open('D:/MW data/test/20191008/JTWPA/scan_1/freq and pw/{}.txt'.format(name),'a') as file:
                    write_str='%f %f %f\n'%(frequency,power,S)
                    file.write(write_str)
                time.sleep(t)
        return


    @sweep_power_frequency.initializer
    def initialize(self):
        return

    @sweep_power_frequency.finalizer
    def finalize(self):
        return


    @Task()
    def sweep_power(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        sweep_pw_params = self.Sweep_power_Settings.widget.get()

        freq = sweep_pw_params['sweep frequency']
        mk_freq = sweep_pw_params['marker frequency']
        pw_low = sweep_pw_params['start power']
        pw_high = sweep_pw_params['stop power']
        pw_stp = sweep_pw_params['step power']
        name = sweep_pw_params['txt name']
        t = sweep_pw_params['sleep time']
        chnl = sweep_pw_params['marker channel']

        self.vna.marker[chnl] = 'ON'
        self.vna.marker_X[chnl] = mk_freq

        self.source.frequency = freq
        self.source.output = 1
        self.source.Trigger_Setting = 0

        time_0 = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds

        pw_count = int((pw_high - pw_low)/pw_stp)

        for p in range(0,pw_count):
            self.source.power = pw_low + p*pw_stp
            amplitude=self.vna.marker_Y[chnl].magnitude
            frequency=self.source.frequency.magnitude

            time_now = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds
            delta_time = time_now-time_0

            with open('D:/MW data/test/20191008/JTWPA/power sweep/scan4/{}.txt'.format(name),'a') as file:
                write_str='%f %f %s\n'%(frequency,amplitude,self.source.power)
                file.write(write_str)
            self.vna.save_csv('D:/20191008/{}.csv'.format(delta_time))
            #self.vna.save_csv_second('D:/MW data/test/20190813/JTWPA/scan_1/phase/{}.csv'.format(delta_time))
            time.sleep(t)
        return

    @sweep_power.initializer
    def initialize(self):
        return

    @sweep_power.finalizer
    def finalize(self):
        return

    @Task()
    def set_source_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        source_freq_params = self.Source_Frequency_Settings.widget.get()

        stat = source_freq_params['output state']
        pw = source_freq_params['power']
        freq = source_freq_params['frequency']
        run = source_freq_params['sweep state']

        self.source.output=stat
        self.source.frequency=freq
        self.source.power = pw
        self.source.sweep_run = run

        print('Setting frequency done!')
        
    @set_source_freq.initializer
    def initialize(self):
        return

    @set_source_freq.finalizer
    def finalize(self):       
        return

    @Task()
    def set_source_stb(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        source_stb_params = self.Source_Stability_Settings.widget.get()

        pll = source_stb_params['pll pump current']
        spc = source_stb_params['channel spacing']

        self.source.PLL_charge_pump_current=pll
        self.source.channel_spacing=spc 

        
    @set_source_freq.initializer
    def initialize(self):
        return

    @set_source_freq.finalizer
    def finalize(self):       
        return

    @Task()
    def save(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        save_params = self.save_Settings.widget.get()
        t = save_params['sleep time']
        file_name = save_params['name']
        chnl = 1

        time_0 = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds

        while(1):
            power=self.vna.marker_Y[chnl].magnitude

            time_now = self.vna.day*3600*24+self.vna.hours*3600+self.vna.minutes*60+self.vna.seconds
            delta_time = time_now-time_0

            with open('D:/MW data/test/20190923/JTWPA/scan_1/save/{}.txt'.format(file_name),'a') as file:
                write_str='%f %f\n'%(power,delta_time)
                file.write(write_str)
            self.vna.save_csv('D:/MW data/test/20190923/JTWPA/scan_1/save/{}.csv'.format(delta_time))
            #self.vna.save_csv_second('D:/MW data/test/20190813/JTWPA/scan_1/phase/{}.csv'.format(delta_time))
            time.sleep(t)
        return

    @save.initializer
    def initialize(self):
        return

    @save.finalizer
    def finalize(self):
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
    def Source_Frequency_Settings(self):
        source_freq_params = [
        ('output state', {'type': int, 'default': 0}),
        ('sweep state', {'type': int, 'default': 0}),
        ('power', {'type': float, 'default': 0}),
        ('frequency', {'type': float, 'default': 200,'units': 'MHz'}),
        ]
        w = ParamWidget(source_freq_params)
        return w

    @Element()
    def Source_Stability_Settings(self):
        source_stb_params = [
        ('pll pump current', {'type': int, 'default': 5}),
        ('channel spacing', {'type': float, 'default': 100,'units': 'Hz'}),
        ]
        w = ParamWidget(source_stb_params)
        return w       

    @Element()
    def Sweep_frequency_Settings(self):
        sweep_freq_params = [
        ('start frequency', {'type': float, 'default': 20,'units':'MHz'}),
        ('stop frequency', {'type': float, 'default': 40,'units': 'MHz'}),
        ('step', {'type': float, 'default': 1,'units': 'MHz'}),
        ('step time', {'type': float, 'default': 1,'units': 'ms'}),
        ('sweep power', {'type': float, 'default': 0}),
        ('sleep time', {'type': float, 'default': 1}),
        ('marker channel', {'type': int, 'default': 1}),
        ('measure times', {'type': int, 'default': 3}),
        ('marker frequency', {'type': float, 'default': 4000,'units':'MHz'}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(sweep_freq_params)
        return w

    @Element()
    def Sweep_power_Settings(self):
        sweep_pw_params = [
        ('sweep frequency', {'type': float, 'default': 6000,'units':'MHz'}),
        ('start power', {'type': float, 'default': -10}),
        ('stop power', {'type': float, 'default': 5}),
        ('step power', {'type': float, 'default': 1}),
        ('sleep time', {'type': float, 'default': 5}),
        ('marker channel', {'type': int, 'default': 1}),
        ('marker frequency', {'type': float, 'default': 4000,'units':'MHz'}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(sweep_pw_params)
        return w

    @Element()
    def Sweep_Power_and_Frequency_Settings(self):
        sweep_pw_fr_params = [
        ('start frequency', {'type': float, 'default': 20,'units':'MHz'}),
        ('stop frequency', {'type': float, 'default': 40,'units': 'MHz'}),
        ('step frequency', {'type': float, 'default': 1,'units':'MHz'}),
        ('start power', {'type': float, 'default': -10}),
        ('stop power', {'type': float, 'default': 8}),
        ('step power', {'type': float, 'default': 0.1}),
        ('step time', {'type': float, 'default': 1,'units': 'ms'}),
        ('sleep time', {'type': float, 'default': 1}),
        ('marker channel', {'type': int, 'default': 1}),
        ('marker frequency', {'type': float, 'default': 30,'units':'MHz'}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(sweep_pw_fr_params)
        return w

    @Element()
    def save_Settings(self):
        save_params = [
        ('sleep time', {'type': float, 'default': 1}),
        ('name', {'type': str, 'default': '1'}),
        ]
        w = ParamWidget(save_params)
        return w