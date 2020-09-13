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
        'vna': P9371A
    }
    qutag = None
    freqs=[]
    powers=[]

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

            with open('D:/MW data/test/20190813/JTWPA/scan_1/save/{}.txt'.format(file_name),'a') as file:
                write_str='%f %f\n'%(power,delta_time)
                file.write(write_str)
            self.vna.save_csv('D:/MW data/test/20190813/JTWPA/scan_1/save/{}.csv'.format(delta_time))
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
    def save_Settings(self):
        save_params = [
        ('sleep time', {'type': float, 'default': 1}),
        ('name', {'type': str, 'default': '1'}),
        ]
        w = ParamWidget(save_params)
        return w