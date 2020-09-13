import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
import os

.
from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget,LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz import Q_
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.tektronix import TDS2024C

class MotorScan(Spyrelet):
    requires = {
        'fungen': Keysight_33622A,
        'osc': TDS2024C

    }
    
    def saveData(self,x,y):
        out_name = "D:\\Data\\8.13.2019\\1st"
        np.savez(os.path.join(out_name),x,y)
        # index=str(round(index,8))
        # ind='.'+str(ind)
        # np.savez(os.path.join(out_name,str(index+ind)),x,y)

    def stepDown(self,channel,scale):
        scales=[5.0,2.0,1.0,0.5,0.2,0.1,0.05,0.02,0.01,0.005]
        i=scales.index(scale)
        if i+1<len(scales):
            return scales[i+1]
        else:
            return scales[i]



    @Task()
    def scan(self):
        param=self.parameters.widget.get()
        self.fungen.waveform[1]='triangle'
        self.fungen.frequency[1]=param['Frequency']
        self.fungen.voltage[1]=param['Amplitude']
        self.fungen.offset[1]=param['Offset']
        self.fungen.wait()
        self.fungen.output[1]='ON'
        time.sleep(50)

        x,y=self.osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        self.saveData(x,y)
        return

    @scan.initializer
    def initialize(self):
        self.fungen.output[1]='OFF'
        self.fungen.output[2]='OFF'
        return

    @scan.finalizer
    def finalize(self):
        self.fungen.output[1]='OFF'
        self.fungen.output[2]='OFF'
        return

    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Amplitude', {'type': float, 'default': 1, 'units':'V'}),
        ('Frequency', {'type': float, 'default': 10, 'units':'Hz'}),
        ('Offset', {'type': float, 'default': 0.5, 'units':'V'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w