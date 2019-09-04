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

from lantz.drivers.spectrum import MS2721B
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
        'analyzer': MS2721B,
        'source': SynthNVPro
    }
    qutag = None



    @Task()
    def set_analyzer_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        analyzer_freq_params = self.Analyzer_Frequency_Settings.widget.get()

        span = analyzer_freq_params['frequency span']
        center = analyzer_freq_params['center freq']

        self.analyzer.freq_span = span
        self.analyzer.freq_cent = center   

        print('Setting frequency done!')
        
    @set_analyzer_freq.initializer
    def initialize(self):
        return

    @set_analyzer_freq.finalizer
    def finalize(self):
        return

    @Task()
    def set_analyzer_amp(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        analyzer_amp_params = self.Analyzer_Amplitude_Settings.widget.get()
        ref = analyzer_amp_params['ref level']
        scale = analyzer_amp_params['scale']

        self.analyzer.ref_level = ref*dBm
        self.analyzer.Y_scale = scale*dBm


    @set_analyzer_amp.initializer
    def initialize(self):
        print('set_amp initialize')
        print('idn: {}'.format(self.analyzer.idn))
        return

    @set_analyzer_amp.finalizer
    def finalize(self):
        print('set_amp finalize')
        return


    @Task()
    def set_analyzer_marker(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        analyzer_marker_params = self.Analyzer_Marker_Settings.widget.get()
        chnl = analyzer_marker_params['channel']
        stat = analyzer_marker_params['state']

        self.analyzer.marker[chnl] = stat


    @set_analyzer_marker.initializer
    def initialize(self):
        return

    @set_analyzer_marker.finalizer
    def finalize(self):
        return   

        

    @Task()
    def sweep_frequency(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        sweep_frequency_params = self.Sweep_frequency_Settings.widget.get()
        chnl = sweep_frequency_params['marker channel']
        mk_freq = sweep_frequency_params['marker frequency']
        fr_low = sweep_frequency_params['start frequency']
        fr_high = sweep_frequency_params['stop frequency']
        fr_stp = sweep_frequency_params['step']
        t_stp = sweep_frequency_params['step time']
        pw = sweep_frequency_params['sweep power']
        name = sweep_frequency_params['txt name']

        self.analyzer.marker[chnl] = 'ON'
        self.analyzer.marker_X[chnl] = mk_freq

        self.source.sweep_lower=fr_low
        self.source.sweep_upper=fr_high
        self.source.sweep_size=fr_stp
        self.source.sweep_step_time=t_stp
        self.source.power=pw

        self.source.output=1
        self.source.sweep_run=1


        while(int(self.source.sweep_run)==1):
            power=self.analyzer.marker_Y[chnl].magnitude
            frequency=self.source.frequency.magnitude

            with open('D:/MW data/test/20190813/JTWPA/scan_1/{}.txt'.format(name),'a') as file:
                write_str='%f %f\n'%(frequency,power)
                file.write(write_str)

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

        chnl = sweep_pw_fr_params['marker channel']
        mk_freq = sweep_pw_fr_params['marker frequency']
        p_low = sweep_pw_fr_params['start power']
        p_high = sweep_pw_fr_params['stop power']
        p_stp = sweep_pw_fr_params['step power']
        fr_low = sweep_pw_fr_params['start frequency']
        fr_high = sweep_pw_fr_params['stop frequency']
        fr_stp = sweep_pw_fr_params['step frequency']
        stp_t = sweep_pw_fr_params['step time']
        name = sweep_pw_fr_params['txt name']

        self.analyzer.marker[chnl] = 'ON'
        self.analyzer.marker_X[chnl] = mk_freq

        self.source.sweep_lower=fr_low
        self.source.sweep_upper=fr_high
        self.source.sweep_size=fr_stp
        self.source.sweep_step_time=stp_t

        self.source.output=1

        pw_count=(p_high-p_low)/p_stp
        for pw_point in range(int(pw_count)):
            pw_current_value=p_low+pw_point*p_stp
            self.source.sweep_power_low=pw_current_value
            self.source.sweep_power_high=pw_current_value
            self.source.sweep_run=1
            while(int(self.source.sweep_run)==1):
                S=self.analyzer.marker_Y[chnl].magnitude
                frequency=self.source.frequency.magnitude
                power=float(self.source.power)
                with open('D:/MW data/test/20190805/power sweep/{}.txt'.format(name),'a') as file:
                    write_str='%f %f %f\n'%(frequency,power,S)
                    file.write(write_str)
                time.sleep(0.2)
        return




    @sweep_power_frequency.initializer
    def initialize(self):
        return

    @sweep_power_frequency.finalizer
    def finalize(self):
        return


    @Task()
    def set_source_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        source_freq_params = self.Source_Frequency_Settings.widget.get()

        stat = source_freq_params['output state']
        freq = source_freq_params['frequency']

        self.source.output=stat
        self.source.frequency=freq  

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


    @Element()
    def Analyzer_Frequency_Settings(self):
        analyzer_freq_params = [
        ('frequency span', {'type': float, 'default': 3000, 'units': 'Hz'}),
        ('center freq', {'type': float, 'default': 30000000, 'units': 'Hz'}),
        ]
        w = ParamWidget(analyzer_freq_params)
        return w

    @Element()
    def Analyzer_Amplitude_Settings(self):
        analyzer_amp_params = [
        ('ref level', {'type': float, 'default': 0}),
        ('scale', {'type': float, 'default': 0}),
        ]
        w = ParamWidget(analyzer_amp_params)
        return w

    @Element()
    def Analyzer_Marker_Settings(self):
        analyzer_marker_params = [
        ('channel', {'type': int, 'default': 1}),
        ('state', {'type': str, 'default': 'OFF'}),
        ]
        w = ParamWidget(analyzer_marker_params)
        return w

    @Element()
    def Source_Frequency_Settings(self):
        source_freq_params = [
        ('output state', {'type': int, 'default': 0}),
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
        ('measure times', {'type': int, 'default': 3}),
        ('marker channel', {'type': int, 'default': 1}),
        ('marker frequency', {'type': float, 'default': 30,'units':'MHz'}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(sweep_freq_params)
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
        ('marker channel', {'type': int, 'default': 1}),
        ('marker frequency', {'type': float, 'default': 30,'units':'MHz'}),
        ('txt name', {'type': str, 'default': '11'}),
        ]
        w = ParamWidget(sweep_pw_fr_params)
        return w