import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
import os
import nidaqmx

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
from toptica.lasersdk.client import SerialConnection
class LaserScan(Spyrelet):
    requires = {
        'wm': Bristol_771
    }
    conn1 = NetworkConnection('1.1.1.1')
    #conn1 = conn1 = SerialConnection('COM1') 
    dlc = Client(conn1)
    daq = nidaqmx.Task()
    daq.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    
    @Task()
    def scan(self):
        param=self.parameters.widget.get()     
        filename = param['Filename']
        F =open(filename+'.dat','w')
        f = filename+'wavelength.dat'
        F2 =open(f,'w')
        start_wavelength = param['Start'].magnitude*1e9
        stop_wavelength = param['Stop'].magnitude*1e9
        speed = param['Speed'].magnitude*1e9
        n = param['Num Scan']
        self.spec=[]
        self.dlc.set("laser1:ctl:scan:wavelength-begin",start_wavelength)
        self.dlc.set("laser1:ctl:scan:wavelength-end",start_wavelength)
        self.dlc.set("laser1:ctl:scan:speed",speed)
        self.dlc.set("laser1:ctl:scan:microsteps",True)
        self.dlc.set("laser1:ctl:scan:shaple",1) #0=Sawtooth,1=Triangle
        self.dlc.set("laser1:ctl:scan:trigger:output-enabled",True)
        for x in range(n-1):            
            self.dlc.set("laser1:ctl:wavelength-set",start_wavelength)
            self.dlc.set("laser1:ctl:scan:trigger:output-threshold",start_wavelength+0.1)
            while True:
                st = dlc.get("io:digital-out2:value-act+0.1")
                if st==False:
                    break 
            self.dlc.set("laser1:ctl:scan:trigger:output-threshold",stop_wavelength)  
            time.sleep(0.5)
            act_start = self.wm.measure_wavelength()
            self.dlc.exec("laser1:ctl:scan:start")
            daq.start()
            if dlc.get("io:digital-out2:value-act"):
                self.dlc.exec("laser1:ctl:scan:pause")
                data = daq.read(nidaqmx.constants.READ_ALL_AVAILABLE)
                daq.wait_until_done()
                self.xs.append(data)
                daq.stop()
                act_stop = self.wm.measure_wavelength()
                print('%d scan: act start = %f, act stop = %f'%(n,act_start,act_stop))
        for i in range(n-1):
            self.spec = self.spec + 1/n*self.xs[i,:]
        self.wl = np.linspace(act_start,act_stop,len(self.spec))
        plt.plot(self.wl,self.spec)
        plt.xlable('wavelength/nm')
        plt.ylable('transmission')
        return

    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start', {'type': float, 'default': 1460*1e-9, 'units':'m'}),
        ('Speed', {'type': float, 'default': 0.5*1e-9, 'units':'m'}),
        ('Stop', {'type': float, 'default': 1570*1e-9, 'units':'m'}),
        ('Num Scan', {'type': int, 'default': 5}),
        ('Filename', {'type': str, 'default':'D:\\Data\\09.2019\\wavelengthsweep'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w