'''
drawing distribution of our fiber coupling
with a attocube and a fake pwm for testing
'''
import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import time
import random

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

#from attocube_spyrelet import Attocube

from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs.pm100d import PM100D

class Test(Spyrelet):
	'''
	requires = {
		'atc': ANC350
		'pmd': PM100D
	}
	'''
	x_range = 6000
	y_range = 6000
	xs = np.arange(0,6000,10)
	ys = np.arange(0,6000,10)
	pw = np.zeros((len(xs),len(ys)),dtype=float)


	@Task()
	def ReflectionDistribution(self):
		for ypoint in range(len(self.ys)):
			for xpoint in range(len(self.xs)):
				self.pw[xpoint,ypoint] = random.random()
			values = {
				'x': self.xs[xpoint],
				'y': self.ys[ypoint],
				'power': self.pw
			}
			self.ReflectionDistribution.acquire(values)
			time.sleep(0.05) 
		return

  
    @Task(name = 'Single Step')
        def RelectionvsTime(slef):
            self.bs=[]
            self.cs=[]
            t0 = time.time()
            while True:
                t1 = time.time()
                t = t1-t0
                self.bs.append(t)
                self.cs.append(random.random())
                values = {
                    'x': self.bs,
                    'y': self.cs,
                }
                self.ReflectionvsTime.acquire(values)
                if len(self.bs>50):
                    self.bs=np.delete(bs,range(20))
                    self.cs=np.delete(cs,range(20))
        return    

  
    @Element(name='2D plot')
    def plot2d(self):
        p = HeatmapPlotWidget()
        return p

    @plot2d.on(ReflectionDistribution.acquired)
    def _plot2d_update(self, ev):
        w = ev.widget
        im = self.ReflectionDistribution.pw
        w.set(im)
        return


    @Element(name='1D plot')
    def plot1d(self):
        p = LinePlotWidget()
        p.plot('Reflection Power')
        params = [
        ('step', {'type': float, 'default':0.01, '/um'}),
        ]
        w = ParamWidget(params)
        button1 = QPushButton('x +')
        button1.move(40, 20)
        button2 = QPushButton('x -')
        button2.move(0, 40)
        button3 = QPushButton('z +')
        button3.move(20, 0)
        button4 = QPushButton('z -')
        button4.move(20, 40)
        button1.clicked.connect(self.move_x1) #direction :+x
        button2.clicked.connect(self.move_x2) #direction :-x
        button3.clicked.connect(self.move_z1) #direction: +z
        button4.clicked.connect(self.move_z2) #direction :-z
        return p,w

    def move_x1(self):
        delta = self.plot1d.widget.get()
        print("move %f um along +x"%(delta))
    def move_x2(self):
        delta = self.plot1d.widget.get()
        print("move %f um along -x"%(delta))
    def move_z1(self):
        delta = self.plot1d.widget.get()
        print("move %f um along +z"%(delta))
    def move_z2(self):
        delta = self.plot1d.widget.get()
        print("move %f um along -z"%(delta))

    @plot1d.on(RelectionvsTime.acquired)
    def _plot1d_update(self, ev):
        w = ev.widget
        xs = np.array(self.bs)
        ys = np.array(self.cs)
        w.set('Reflection Power',xs=xs,ys=ys)
        return

    @Element(name='Scan Parameters')
    def scan_parameters(self)
        params = [
        ('Y position', {'type': float, 'default':1000, '/um'}),
        ('X start', {'type': float, 'default':0 ,'/um'}),
        ('X range', {'type': float, 'default':6000 ,'/um'}),
        ('Z start', {'type': float, 'default':0 ,'/um'}),
        ('Z range', {'type': float, 'default':6000 ,'/um'}),
        ('Step', {'type': float, 'default':10 ,'/um'}),
        ('Voltage', {'type': float, 'default':70,'/V'}),
        ('Frequency', {'type': float, 'default':1000,'/Hz'}),
        ]
        w = ParamWidget(params)
        return w
    def initialize(self):
	return
    def finalize(self):
	return
