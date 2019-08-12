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
    def set_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        freq_params = self.Analyzer_Frequency_Settings.widget.get()

        span = freq_params['frequency span']
        center = freq_params['center freq']

        self.analyzer.freq_span = span
        self.analyzer.freq_cent = center   

        print('Setting frequency done!')
        
    @set_freq.initializer
    def initialize(self):
        print('set_freq initialize')
        print('idn: {}'.format(self.analyzer.idn))
        return

    @set_freq.finalizer
    def finalize(self):
        print('set_freq finalize')
        return

    @Task()
    def set_amp(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        amp_params = self.Analyzer_Amplitude_Settings.widget.get()
        ref = amp_params['ref level']
        scale = amp_params['scale']

        self.analyzer.ref_level = ref*dBm
        self.analyzer.Y_scale = scale*dBm
        print('Setting amplitude done!')


    @set_amp.initializer
    def initialize(self):
        print('set_amp initialize')
        print('idn: {}'.format(self.analyzer.idn))
        return

    @set_amp.finalizer
    def finalize(self):
        print('set_amp finalize')
        return

    # @Task()
    # def plot(self):
    #     a = np.loadtxt('D:/MW data/test/20190804/1.txt')
    #     x_list=a[:,0]
    #     y_list=a[:,1]
    #     plt.plot(x_list,y_list, label='center:10.7kHz')
    #     plt.xlabel('frequency/MHz')
    #     plt.ylabel('amplitude/dBm')
    #     plt.title("title")
    #     plt.legend()
    #     plt.show()
    #     return

    @Task()
    def marker(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        marker_params = self.Analyzer_Marker_Settings.widget.get()
        chnl = marker_params['channel']
        stat = marker_params['state']

        self.analyzer.marker[chnl]=stat
        # value = float(self.analyzer.marker_Y[chnl])

        #print(self.analyzer.marker_X[chnl])

    @marker.initializer
    def initialize(self):
        return

    @marker.finalizer
    def finalize(self):
        return   

        

    @Task()
    def savetxt(self):
        chnl = 2
        power=float(self.analyzer.marker_Y[chnl])
        #frequency=float(self.analyzer.marker_X[chnl])
        with open('D:/MW data/test/20190804/3.txt','a') as file:
            write_str='%s %f\n'%('frequency',power)
            file.write(write_str)
        return

    @savetxt.initializer
    def initialize(self):
        return

    @savetxt.finalizer
    def finalize(self):
        return

    @Task()
    def set_freq(self):
        self.dataset.clear()
        log_to_screen(DEBUG)
        freq_params = self.Source_Frequency_Settings.widget.get()

        key = freq_params['output state']
        freq = freq_params['frequency']

        self.source.output = key
        self.source.frequency = freq 

        print('Setting source done!')

    @set_freq.initializer
    def initialize(self):
        pass

    @set_freq.finalizer
    def finalize(self):
        pass


    @Element()
    def Analyzer_Frequency_Settings(self):
        freq_params = [
        ('frequency span', {'type': float, 'default': 3000, 'units': 'Hz'}),
        ('center freq', {'type': float, 'default': 30000000, 'units': 'Hz'}),
        ]
        w = ParamWidget(freq_params)
        return w

    @Element()
    def Analyzer_Amplitude_Settings(self):
        amp_params = [
        ('ref level', {'type': float, 'default': 0}),
        ('scale', {'type': float, 'default': 0}),
        ]
        w = ParamWidget(amp_params)
        return w

    @Element()
    def Analyzer_Marker_Settings(self):
        marker_params = [
        ('channel', {'type': int, 'default': 1}),
        ('state', {'type': str, 'default': 'OFF'}),
        ]
        w = ParamWidget(marker_params)
        return w

    @Element()
    def Source_Frequency_Settings(self):
        freq_params = [
        ('output state', {'type': int, 'default': 0}),
        ('frequency', {'type': float, 'default': 200, 'units': 'MHz'}),
        ]
        w = ParamWidget(freq_params)
        return w       

  