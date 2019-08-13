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
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
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
		'powermeter': PM100D
	}
	
	attocube=ANC350()
	attocube.initialize()
	axis_index_x=0
	axis_index_y=1
	axis_index_z=2 
	F = open('C:\\Users\\Tian Zhong\\Tao\\scan2.txt', 'w')


	@Task(name='Scan XZ')
	def ReflectionDistribution(self):
		self.F = open(self.filename, 'w')
		for zpoint in range(len(self.zpositions)):
			self.attocube.absolute_move(self.axis_index_z,self.zpositions[zpoint],self.eps)
			print("%d/%d"%(zpoint,len(self.zpositions)))
			xpoint=0
			self.attocube.absolute_move(self.axis_index_x,self.x_start,self.eps)
			for item in self.pw[zpoint-1,:]:
				self.F.write("%f,"% item)
			self.attocube.absolute_move(self.axis_index_x,self.x_end,self.eps) 
			while xpoint<1000:             				
				self.pw[zpoint][xpoint] = self.powermeter.power.magnitude*1000
				time.sleep(0.0005)
				xpoint=xpoint+1 
			values = {
					'power': self.pw
				}
			self.ReflectionDistribution.acquire(values)
		return


	@Task(name = 'Single Step')
	def ReflectionvsTime(self):
		fieldValues = self.step_parameters.widget.get()
		FREQUENCY_x=fieldValues['x Frequency'].magnitude
		FREQUENCY_y=fieldValues['y Frequency'].magnitude
		FREQUENCY_z=fieldValues['z Frequency'].magnitude
		VOLTAGE_x=fieldValues['x Voltage'].magnitude
		VOLTAGE_y=fieldValues['y Voltage'].magnitude
		VOLTAGE_z=fieldValues['z Voltage'].magnitude
		self.attocube.frequency[self.axis_index_x]=Q_(FREQUENCY_x,'Hz')
		self.attocube.frequency[self.axis_index_y]=Q_(FREQUENCY_y,'Hz')
		self.attocube.frequency[self.axis_index_z]=Q_(FREQUENCY_z,'Hz')
		self.attocube.amplitude[self.axis_index_x]=Q_(VOLTAGE_x,'V')
		self.attocube.amplitude[self.axis_index_y]=Q_(VOLTAGE_y,'V')
		self.attocube.amplitude[self.axis_index_z]=Q_(VOLTAGE_z,'V')
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
			if(len(self.xs)>400):
				self.xs=self.xs[300:]
				self.ys=self.ys[300:]

			self.ReflectionvsTime.acquire(values)
			time.sleep(0.05)
		return

	@Task(name = 'Position')
	def Position(self):
		while True:
			self.x=self.attocube.position[self.axis_index_x].magnitude
			self.y=self.attocube.position[self.axis_index_y].magnitude
			self.z=self.attocube.position[self.axis_index_z].magnitude
			values = {
				'x': self.x,
				'y': self.y,
				'z': self.z,

			}
			self.Position.acquire(values)
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

	@Element(name='indicator')
	def position_now(self):
		text = QTextEdit()
		text.setPlainText('x: non um \ny: non um \nz: non um \n')
		return text
	@position_now.on(Position.acquired)
	def _position_now_update(self,ev):
		w=ev.widget
		w.setPlainText('x: %f um \ny: %f um \nz: %f um \n'%(self.x,self.y,self.z))
		return 


	@Element(name='Scan Parameters')
	def scan_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('File name', {'type': str, 'default': 'C:\\Users\\Tian Zhong\\Tao\\scan'}),
		('X start', {'type': float, 'default': 2488*1e-6, 'units':'m'}),
		('X end', {'type': float, 'default': 2498*1e-6, 'units':'m'}),
		('Z start', {'type': float, 'default': 1062*1e-6, 'units':'m'}),
		('Z range', {'type': float, 'default': 10*1e-6, 'units':'m'}),
		('Step', {'type': float, 'default': 0.1*1e-6, 'units':'m'}),
		('Voltage', {'type': float, 'default': 20, 'units':'V'}),
		('x Voltage', {'type': float, 'default': 50, 'units':'V'}),
		('Frequency', {'type': float, 'default': 200, 'units':'Hz'})
		]
		w = ParamWidget(params)
		return w
	@Element(name='Step Parameters')
	def step_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('File name', {'type': str, 'default': 'C:\\Users\\Tian Zhong\\Tao\\scan2'}),
		('x Voltage', {'type': float, 'default': 40, 'units':'V'}),
		('x Frequency', {'type': float, 'default': 50, 'units':'Hz'}),
		('y Voltage', {'type': float, 'default': 20, 'units':'V'}),
		('y Frequency', {'type': float, 'default': 50, 'units':'Hz'}),
		('z Voltage', {'type': float, 'default': 40, 'units':'V'}),
		('z Frequency', {'type': float, 'default': 50, 'units':'Hz'})
		]
		w = ParamWidget(params)
		return w

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
		if (len(xs)>len(ys)):
			xs = xs[:len(ys)]
		w.set('Reflection',xs=xs,ys=ys)
		return


	@Element(name='stop')
	def stopbutton(self):
		button7 = QPushButton('STOP')
		button7.move(0,20)
		button7.clicked.connect(self.stopmoving) #direction :-z
		return button7       
	def stopmoving(self):
		self.attocube.stop()
		return

	@Element(name='+x')
	def x_forward(self):
		button1 = QPushButton("x +")
		button1.move(0,20)
		button1.clicked.connect(self.move_x1) #direction :+x
		return button1
	def move_x1(self):
		print('x1')
		self.attocube.single_step(self.axis_index_x,+1)
		return  
	@Element(name='-x')
	def x_backward(self):
		button2 = QPushButton('x -')
		button2.move(0,20)
		button2.clicked.connect(self.move_x2) #direction :-x
		return button2
	def move_x2(self):
		print('x2')
		self.attocube.single_step(self.axis_index_x,-1)
		return  
	@Element(name='+z')
	def z_forward(self):
		button3 = QPushButton(" z +")
		button3.move(0,20)
		button3.clicked.connect(self.move_z1) #direction :+z
		return button3
	def move_z1(self):
		print('z1')
		self.attocube.single_step(self.axis_index_z,+1)
		return

	@Element(name='-z')
	def z_backward(self):
		button4 = QPushButton('z -')
		button4.move(0,20)
		button4.clicked.connect(self.move_z2) #direction :-z
		return button4       
	def move_z2(self):
		print('z2')
		self.attocube.single_step(self.axis_index_z,-1)
		return

	@Element(name='+y')
	def y_forward(self):
		button5 = QPushButton("y +")
		button5.move(0,20)
		button5.clicked.connect(self.move_y1) #direction :+z
		return button5
	def move_y1(self):
		print('y1')
		self.attocube.single_step(self.axis_index_y,+1)
		return

	@Element(name='-y')
	def y_backward(self):
		button6 = QPushButton('y -')
		button6.move(0,20)
		button6.clicked.connect(self.move_y2) #direction :-z
		return button6       
	def move_y2(self):
		print('y2')
		self.attocube.single_step(self.axis_index_y,-1)
		return


	@ReflectionDistribution.initializer
	def initialize(self):
		print('initializing')
		fieldValues = self.scan_parameters.widget.get()
		FREQUENCY_x=fieldValues['Frequency'].magnitude
		FREQUENCY_y=fieldValues['Frequency'].magnitude
		FREQUENCY_z=fieldValues['Frequency'].magnitude
		VOLTAGE_x=fieldValues['x Voltage'].magnitude
		VOLTAGE_y=fieldValues['Voltage'].magnitude
		VOLTAGE_z=fieldValues['Voltage'].magnitude
		self.x_end = fieldValues['X end'].magnitude*1e6 
		z_range = fieldValues['Z range'].magnitude *1e6
		step = fieldValues['Step'].magnitude*1e6
		self.x_start = fieldValues['X start'].magnitude*1e6
		z_start = fieldValues['Z start'].magnitude*1e6
		self.filename = fieldValues['File name']
		self.zpositions = np.arange(z_start,z_start+z_range+1,step)
		self.pw = np.zeros((len(self.zpositions),1000),dtype=float)
		self.eps=0.1

		#initialize
		self.attocube.frequency[self.axis_index_x]=Q_(FREQUENCY_x,'Hz')
		self.attocube.frequency[self.axis_index_y]=Q_(FREQUENCY_y,'Hz')
		self.attocube.frequency[self.axis_index_z]=Q_(FREQUENCY_z,'Hz')
		self.attocube.amplitude[self.axis_index_x]=Q_(VOLTAGE_x,'V')
		self.attocube.amplitude[self.axis_index_y]=Q_(VOLTAGE_y,'V')
		self.attocube.amplitude[self.axis_index_z]=Q_(VOLTAGE_z,'V')
		self.attocube.absolute_move(self.axis_index_x,self.x_start,self.eps)
		self.attocube.absolute_move(self.axis_index_z,z_start,self.eps)
		time.sleep(5)
		print('initialized')
		return
	@ReflectionDistribution.finalizer     
	def finalize(self):
		return
	