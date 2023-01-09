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
#import nidaqmx

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
#from lantz.drivers.thorlabs.pm100d import PM100D

class LaserScan(Spyrelet):
    # delete if not using power meter
    requires = {
        'pmd':PM100D

    }
    conn1 = NetworkConnection('1.1.1.2')

    dlc = Client(conn1)

    #daq = nidaqmx.Task()
    #daq.ai_channels.add_ai_voltage_chan("Dev1/ai3")

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
        self.wv = np.arange(start_wavelength,stop_wavelength,step)
        #self.daq.start()
        print('here')
        with Client(self.conn1) as dlc:
            print('here')
            for x in range(n):
                xx=[]
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(8)
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(0.005)
                    #xx.append(self.daq.read())

                    xx.append(self.pmd.power.magnitude*1000000)
                time.sleep(1)

                wl = np.linspace(start_wavelength,stop_wavelength,len(xx))
                for item in xx:
                    F.write("%f,"%item)
                for item in wl:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")
        #self.daq.stop()
        return

    @Element(name='Params')
    def parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start', {'type': float, 'default': 1460*1e-9, 'units':'m'}),
        ('Step', {'type': float, 'default': 0.01*1e-9, 'units':'m'}),
        ('Stop', {'type': float, 'default': 1570*1e-9, 'units':'m'}),
        ('Num Scan', {'type': int, 'default': 1}),
        ('Filename', {'type': str, 'default':'D:\\Data\\09.06.2019\\wavelengthsweep'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w
