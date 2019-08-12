'''
drawing distribution of our fiber coupling
with a attocube and a fake pwm for testing
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

#from attocube_spyrelet import Attocube

from lantz import Q_


class Test(Spyrelet):

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

	@Element(name='2D plot')
	def plot2d(self):
		p = HeatmapPlotWidget()
		return p

	@plot2d.on(ReflectionDistribution.acquired)
	def _plot2d_update(self, ev):
		w = ev.widget
		im = self.pw
		w.set(im)
		return
	def initialize(self):
		return
	def finalize(self):
		return


  
	@Task(name = 'Single Step')
	def ReflectionvsTime(self):
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
		return    

	@Element(name='1D plot')
	def plot1d(self):
		p = LinePlotWidget()
		p.plot('Reflection Power')
		return p

	@plot1d.on(ReflectionvsTime.acquired)
	def _plot1d_update(self, ev):
		w = ev.widget
		xs = np.array(self.bs)
		ys = np.array(self.cs)
		w.set('Reflection Power',xs=xs,ys=ys)
		return

	def initialize(self):
		return
	def finalize(self):
		return


	@Element(name='botton')
	def button1(self):
		button1 = QPushButton('x-')
		button1.move(0, 20)
		button1.clicked.connect(self.move_x1)
		return button1
	@Element(name='botton2')
	def button2(self):
		button2 = QPushButton('x+')
		button2.move(0, 20)
		button2.clicked.connect(self.move_x1)
		return button2



	def move_x1(self):
		print("PyQt5 button click")
	def move_x1(self):
		delta = self.plot1d.widget.get()
		print("move %f um along +x"%(delta))
		return
	def move_x2(self):
		delta = self.plot1d.widget.get()
		print("move %f um along -x"%(delta))
		return
	def move_z1(self):
		delta = self.plot1d.widget.get()
		print("move %f um along +z"%(delta))
		return
	def move_z2(self):
		delta = self.plot1d.widget.get()
		print("move %f um along -z"%(delta))
		return

	@Element(name='Parameters')
	def parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Y position', {'type': float, 'default': 1000, 'units':'um'}),
		('X start', {'type': float, 'default': 0, 'units':'um'}),
		]
		w = ParamWidget(params)
		return w
'''
	@Element(name='Scan Parameters')
	def scan_parameters(self):
		params = [
		('Y position', {'type': float, 'default':1000, 'units':'/um'}),
		('X start', {'type': float, 'default':0 ,'units':'/um'}),
		('X range', {'type': float, 'default':6000 ,'units':'/um'}),
		('Z start', {'type': float, 'default':0 ,'units':'/um'}),
		('Z range', {'type': float, 'default':6000 ,'units':'/um'}),
		('Step', {'type': float, 'default':10 ,'units':'/um'}),
		('Voltage', {'type': float, 'default':70,'units':'/V'}),
		('Frequency', {'type': float, 'default':1000,'units':'/Hz'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='step p')
	def step_parameters(self):
		params = [
		('step', {'type': float, 'default':0.01,'units': '/um'}),
		]
		w = ParamWidget(params)
		return w
	def initialize(self):
		return
	def finalize(self):
		return
'''