'''
needs test
for fiber coupling
needs an attocube and a powermeter
scan XZ
might have awful interface
'''
import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton
import time
import random


from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget,LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

#from attocube_spyrelet import Attocube  #has touble with finding this, not used though?

from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs.pm100d import PM100D

class ALIGNMENT(Spyrelet):
	
    requires = {
        'attocube': ANC350()
        'powermeter': PM100D()
    }
    attocube.initialize()
    axis_index_x=0
	axis_index_y=1
	axis_index_z=2


    @Task(name='Scan XY')
    def ReflectionDistribution(self):

        # get scan settings
        fieldValues = self.scan_parameters.widget.get()
        FREQUENCY_x=fieldValues['Frequency']
        FREQUENCY_y=fieldValues['Frequency']
        FREQUENCY_z=fieldValues['Frequency']
        VOLTAGE_x=fieldValues['Voltage']
        VOLTAGE_y=fieldValues['Voltage']
        VOLTAGE_z=fieldValues['Voltage']
        x_range = fieldValues['X range'] 
        z_range = fieldValues['Z range'] 
        step = fieldValues['Step']
        x_start = fieldValues['X start']
        z_start = fieldValues['Z start']
        y_pos = fieldValues['Y position']
        self.xpositions = np.arange(x_start,x_start+x_range+1,step) 
        self.zpositions = np.arange(z_start,z_start+z_range+1,step)
        self.pw = np.zeros((len(xpositions),len(zpositions)),dtype=float)

    	#initialize
    
        self.attocube.frequency[axis_index_x]=Q_(FREQUENCY_x,'Hz')
        self.attocube.frequency[axis_index_y]=Q_(FREQUENCY_y,'Hz')
        self.attocube.frequency[axis_index_z]=Q_(FREQUENCY_z,'Hz')
        self.attocube.amplitude[axis_index_x]=Q_(VOLTAGE_x,'V')
        self.attocube.amplitude[axis_index_y]=Q_(VOLTAGE_y,'V')
        self.attocube.amplitude[axis_index_z]=Q_(VOLTAGE_z,'V')
    	self.attocube.cl_move(self.axis_index_x,Q(x_start,'um'))
		self.attocube.cl_move(self.axis_index_z,Q(z_start,'um'))
		self.attocube.cl_move(self.axis_index_y,Q(y_pos,'um'))

    	#scan XZ
    	for zpoint in range(len(self.zpositions)):
    		self.attocube.cl_move(self.axis_index_z,Q_(zpositions[zpoint],'um'))
    		for xpoint in range(len(self.xpositions)):
    			self.attocube.cl_move(self.axis_index_x,Q_(xpositions[xpoint],'um'))				
    			time.sleep(0.1)  
    			#not sure how long we should wait before measuring the reflection after every attocube movement,
    			#will take 0.1s*600*600 = 1hour now,
    			self.pw[xpoint,zpoint] = self.powermeter.power.magnitude*1000
    			values = {
    				'x': self.xpositions[xpoint],
    				'z': self.zpositions[zpoint],
    				'power': self.pw
    			}
    			self.ReflectionDistribution.acquire(values)
    	#find the position with max reflection
    	(self.xmax,self.zmax)=np.where(self.pw==np.max(self.pw))
        print(self.xmax,self.zmax)

    	return


    @Task(name = 'Single Step')
        def ReflectionvsTime(self):
            self.xs=[]
            self.ys=[]
            t0 = time.time()
            while True:
                t1 = time.time()
                t = t1-t0
                self.xs.append(t)
                self.ys.append(self.powermeter.power.magnitude * 1000)
                values = {
                    'x': self.xs,
                    'y': self.ys,
                }
                self.ReflectionvsTime.acquire(values)
        return
                    


    @Element(name='2D plot')
    def plot2d(self):
        p = HeatmapPlotWidget()
        return p

    @plot2d.on(ReflectionDistribution.acquired)
    def _plot2d_update(self, ev):
        w = ev.widget
        im = self.ReflectionDistribution.pw
        w.set(im.T)
        return


    
    @Element(name='SingleStep Parameter')
    def step_parameters(self):
        param = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Setp', {'type': float, 'default': 0.5, 'units':'um'}),
        ]
        w = ParamWidget(param)
        return w

    @Element(name='+x')
     def x_forward(self):
        button1 = QPushButton('x +')
        button1.clicked.connect(self.move_x1) #direction :+x
        return

    def move_x1(self):
        delta = self.step_parameters.widget.get()
        self.attocube.relative_move(self,axis_index_x,delta,max_move=Q_(10, 'um'))
        return
    
    @Element(name='-x')
     def x_backward(self):
        button2 = QPushButton('x -')
        button2.clicked.connect(self.move_x2) #direction :-x
        return
    def move_x2(self):
        delta = self.step_parameters.widget.get()
        self.attocube.relative_move(self,axis_index_x,-delta,max_move=Q_(10, 'um'))
        return
    
    @Element(name='+z')
     def z_forward(self):
        button3 = QPushButton('z +')
        button3.clicked.connect(self.move_z1) #direction :+z
        return
    def move_z1(self):
        delta = self.step_parameters.widget.get()
        self.attocube.relative_move(self,axis_index_z,delta,max_move=Q_(10, 'um'))
        return

    @Element(name='-z')
     def z_backward(self):
        button4 = QPushButton('z -')
        button4.clicked.connect(self.move_z2) #direction :-z
        return        
    def move_z2(self):
        delta = self.step_parameters.widget.get()
        self.attocube.relative_move(self,axis_index_z,-delta,max_move=Q_(10, 'um'))
        return

    @Element(name='1D plot')
    def plot1d(self):
        p = LinePlotWidget()
        p.plot('Reflection')
        return p

    @plot1d.on(ReflectionvsTime.acquired)
    def _plot1d_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        w.set('Reflection',xs=xs,ys=ys)
        return


    @Element(name='Scan Parameters')
    def pulse_parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Y position', {'type': float, 'default': 1000, 'units':'um'}),
        ('X start', {'type': float, 'default': 0, 'units':'um'}),
        ('X range', {'type': float, 'default': 6000, 'units':'um'}),
        ('Z start', {'type': float, 'default': 0, 'units':'um'}),
        ('Z range', {'type': float, 'default': 6000, 'units':'um'}),
        ('Step', {'type': float, 'default': 10, 'units':'um'}),
        ('Voltage', {'type': float, 'default': 70, 'units':'V'}),
        ('Frequency', {'type': float, 'default': 1000, 'units':'Hz'})
        ]
        w = ParamWidget(params)
        return w

    def initialize(self):
        return
    def finalize(self):
        return