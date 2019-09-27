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

# laser package
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection

# in this spyrelet we set the start wavelength, stop wavelength, and steps as 
# the laser set wavelength is changed

# https://toptica.github.io/python-lasersdk/low_level_api.html

class LaserScan(Spyrelet):
    requires = {

    }

    conn1 = NetworkConnection('1.1.1.2') # these numbers are set on the laser controller
    dlc = Client(conn1)
    daq = nidaqmx.Task()
    daq.ai_channels.add_ai_voltage_chan("Dev1/ai6") # change the number here to set which channel
    
    @Task()
    def scan(self):
        param=self.parameters.widget.get()      
        filename = param['Filename'] 
        F =open(filename+'.dat','w')
        f=filename+'\'.dat'
        F2 = open(f,'w') 
        start_wavelength = param['Start'].magnitude*1e9 # looking at a dictionary of the parameters
        stop_wavelength = param['Stop'].magnitude*1e9
        step = param['Step'].magnitude*1e9
        n = param['Num Scan'] 
        self.wv = np.arange(start_wavelength,stop_wavelength,step) # create a vector of points that the wavelength will tune to for the scan
        self.daq.start() # start collecting data from the DAQ
        with Client(self.conn1) as dlc: # why does this need to be set here when it looks like it is set above?
            for x in range(n):
                xx=[] # this vector stores the value of the power measurements taken in each scan     
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(8) # the wavelength wait time is long because if
                # the laser wavelength is initially set far from this starting point it takes some time to get there
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(0.0001) # after waiting 100us after setting the wavelength read the power from the DAQ
                    xx.append(self.daq.read()) 
                time.sleep(1) # wait 1 second after finishing the scan

                wl = np.linspace(start_wavelength,stop_wavelength,len(xx)) # linearly interpolate between the start and stop wavelengths
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
        ('Start', {'type': float, 'default': 1460*1e-9, 'units':'m'}),
        ('Step', {'type': float, 'default': 0.01*1e-9, 'units':'m'}),
        ('Stop', {'type': float, 'default': 1570*1e-9, 'units':'m'}),
        ('Num Scan', {'type': int, 'default': 1}),
        ('Filename', {'type': str, 'default':'D:\\Data\\09.06.2019\\wavelengthsweep'})

        # ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
        ]
        w = ParamWidget(params)
        return w
