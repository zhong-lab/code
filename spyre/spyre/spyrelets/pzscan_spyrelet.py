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
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection

class LaserScan(Spyrelet):
    requires = {
        'wm': Bristol_771
    }
    conn1 = NetworkConnection('1.1.1.2')

    dlc = Client(conn1)
    daq = nidaqmx.Task()
    daq.ai_channels.add_ai_voltage_chan("Dev1/ai6")
    
    @Task()
    def scan(self):
        param=self.parameters.widget.get()     
        filename = param['Filename']
        F =open(filename+'.dat','w')
        f=filename+'\'.dat'
        F2 = open(f,'w')
        start_wavelength = param['Start'].magnitude*1e9
        stop_voltage = param['Stop'].magnitude
        step = param['Step'].magnitude
        n = param['Num Scan']
        self.vt = np.arange(0,stop_voltage,step)
        self.daq.start()
        with Client(self.conn1) as dlc:
            dlc.set("laser1:ctl:wavelength-set",start_wavelength)
            time.sleep(10)
            for x in range(n):
                xx = []
                wl = []            
                dlc.set("laser1:dl:pc:voltage-set",0)
                time.sleep(3)
                act_start = self.wm.measure_wavelength()
                for item in self.vt:
                    dlc.set("laser1:dl:pc:voltage-set",item)
                    time.sleep(0.5)
                    xx.append(self.daq.read())
                time.sleep(5)
                act_stop = self.wm.measure_wavelength()
                wl = np.linspace(act_start,act_stop,len(xx))

                for item in xx:
                    F.write("%f,"%item)
                for item in wl:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")
        self.daq.stop()
        return

    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start', {'type': float, 'default': 1499*1e-9, 'units':'m'}),
        ('Step', {'type': float, 'default': 0.01, 'units':'V'}),
        ('Stop', {'type': float, 'default': 2, 'units':'V'}),
        ('Num Scan', {'type': int, 'default': 1}),
        ('Filename', {'type': str, 'default':'D:\\Data\\CW_cavity\\09.25\\wavelengthsweep'})
        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w
