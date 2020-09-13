import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
import os


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
from lantz.drivers.thorlabs.pm100d import PM100D
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client
class MotorScan(Spyrelet):
    requires = {
        'fungen': Keysight_33622A,
        'pmd': PM100D,
        'wm': Bristol_771
    }
    #conn1 = NetworkConnection('1.1.1.1')
    
    @Task()
    def scan(self):
        param=self.parameters.widget.get()
        '''
        with Client(self.conn1) as client:
            client.exec('laser1:ctl:wavelength-set', param['Start'].magnitude*1e9)
        '''
        param=self.parameters.widget.get()
        self.fungen.waveform[1]='triangle'
        self.fungen.frequency[1]=param['Frequency']
        T=1/param['Frequency'].magnitude
        self.fungen.voltage[1]=param['Amplitude']
        self.fungen.offset[1]=param['Offset']
        filename = param['Filename']
        F =open(filename+'.dat','w')
        f = filename+'wavelength.dat'
        F2 =open(f,'w')
        self.fungen.wait()
        self.fungen.output[1]='ON'
        self.xs = []
        self.ys = []
        self.zs=[]
        t0 = time.time()
        t = time.time()
        while t-t0<=3*T:
            t = time.time()
            self.xs.append(t)
            self.ys.append(self.pmd.power.magnitude * 1000)
            self.zs.append(str(self.wm.measure_wavelength()))
            time.sleep(0.001)
        values = {
                'y': self.ys,
                'z': self.zs,
                'x': self.xs
                  }

        self.scan.acquire(values)
        for item in self.zs:
            F2.write("%s,"% item)
        for item in self.ys:
            F.write("%f,"% item)
        return

    @Element(name='Histogram')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Transmission Power')
        return p

    @averaged.on(scan.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)       
        w.set('Transmission Power', xs=xs, ys=ys)
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
        ('Start', {'type': float, 'default': 1460*1e-9, 'units':'m'}),
        ('Amplitude', {'type': float, 'default': 1, 'units':'V'}),
        ('Frequency', {'type': float, 'default': 0.01, 'units':'Hz'}),
        ('Offset', {'type': float, 'default': 0.5, 'units':'V'}),
        ('Filename', {'type': str, 'default':'D:\\Data\\8.13.2019\\wavelengthsweep'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w