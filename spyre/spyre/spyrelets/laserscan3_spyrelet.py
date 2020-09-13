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


from lantz import Q_
from lantz.drivers.thorlabs.pm100d import PM100D
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client,SerialConnection
from lantz.drivers.thorlabs.pm100d import PM100D
class LaserScan(Spyrelet):
    requires = {
        'wm': Bristol_771,
        'pmd': PM100D
    }
    conn1 = SerialConnection('COM10') 

    dlc = Client(conn1)

    
    @Task()
    def scan(self):
        param=self.parameters.widget.get()     
        filename = param['Filename']
        F =open(filename+'.dat','w')
        f=filename+'\'.dat'
        F2 = open(f,'w')
        start_wavelength = param['Start'].magnitude*1e9
        stop_wavelength = param['Stop'].magnitude*1e9
        step = param['Step'].magnitude*1e9
        n = param['Num Scan']
        self.wv = np.arange(start_wavelength,stop_wavelength+step,step)

        with Client(self.conn1) as dlc:
            for x in range(n):
                xx=[]            
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(10)
                act_start = self.wm.measure_wavelength()
                time.sleep(0.5)
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(0.000001)
                    xx.append(self.pmd.power.magnitude * 1000)
                act_stop = self.wm.measure_wavelength()
                print('%f,%f'%(act_start,act_stop))
                wl = np.linspace(start_wavelength,stop_wavelength,len(xx))
                for item in xx:
                    F.write("%f,"%item)
                for item in wl:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")
            dlc.set("laser1:ctl:wavelength-set",start_wavelength)
        return

    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start', {'type': float, 'default': 1460*1e-9, 'units':'m'}),
        ('Step', {'type': float, 'default': 0.001*1e-9, 'units':'m'}),
        ('Stop', {'type': float, 'default': 1570*1e-9, 'units':'m'}),
        ('Num Scan', {'type': int, 'default': 1}),
        ('Filename', {'type': str, 'default':'D:\\Data\\CW_cavity\\09.12'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w
