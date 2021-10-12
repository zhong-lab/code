<<<<<<< HEAD
<<<<<<< HEAD
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
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.thorlabs.pm100d import PM100D
class LaserScan(Spyrelet):
    requires = {
        'pmd': PM100D,
        'wm':Bristol_771
    }
    conn1 = NetworkConnection('1.1.1.2')

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
                wls=[]            
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(10)
                #act_start = self.wm.measure_wavelength()
                time.sleep(2)
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(3)
                    xx.append(self.pmd.power.magnitude * 1000)
                    wl_curr=self.wm.measure_wavelength()
                    wls.append(wl_curr)
                #act_stop = self.wm.measure_wavelength()
                #print('%f,%f'%(act_start,act_stop))
                wl = np.linspace(start_wavelength,stop_wavelength,len(xx))
                for item in xx:
                    F.write("%f,"%item)
                for item in wls:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")

        return

    @scan.initializer
    def initialize(self):
        self.wm.start_data()

    @scan.finalizer
    def finalize(self):
        self.wm.stop_data()
        print('Scan complete!')
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
=======
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
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.thorlabs.pm100d import PM100D
class LaserScan(Spyrelet):
    requires = {
        'pmd': PM100D,
        'wm':Bristol_771
    }
    conn1 = NetworkConnection('1.1.1.2')

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
                wls=[]            
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(10)
                #act_start = self.wm.measure_wavelength()
                time.sleep(2)
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(3)
                    xx.append(self.pmd.power.magnitude * 1000)
                    wl_curr=self.wm.measure_wavelength()
                    wls.append(wl_curr)
                #act_stop = self.wm.measure_wavelength()
                #print('%f,%f'%(act_start,act_stop))
                wl = np.linspace(start_wavelength,stop_wavelength,len(xx))
                for item in xx:
                    F.write("%f,"%item)
                for item in wls:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")

        return

    @scan.initializer
    def initialize(self):
        self.wm.start_data()

    @scan.finalizer
    def finalize(self):
        self.wm.stop_data()
        print('Scan complete!')
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
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
=======
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
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.thorlabs.pm100d import PM100D
class LaserScan(Spyrelet):
    requires = {
        'pmd': PM100D,
        'wm':Bristol_771
    }
    conn1 = NetworkConnection('1.1.1.2')

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
                wls=[]            
                dlc.set("laser1:ctl:wavelength-set",start_wavelength)
                time.sleep(10)
                #act_start = self.wm.measure_wavelength()
                time.sleep(2)
                for item in self.wv:
                    dlc.set("laser1:ctl:wavelength-set",item)
                    time.sleep(3)
                    xx.append(self.pmd.power.magnitude * 1000)
                    wl_curr=self.wm.measure_wavelength()
                    wls.append(wl_curr)
                #act_stop = self.wm.measure_wavelength()
                #print('%f,%f'%(act_start,act_stop))
                wl = np.linspace(start_wavelength,stop_wavelength,len(xx))
                for item in xx:
                    F.write("%f,"%item)
                for item in wls:
                    F2.write("%f,"%item)
                F.write("\n")
                F2.write("\n")

        return

    @scan.initializer
    def initialize(self):
        self.wm.start_data()

    @scan.finalizer
    def finalize(self):
        self.wm.stop_data()
        print('Scan complete!')
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
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
        return w