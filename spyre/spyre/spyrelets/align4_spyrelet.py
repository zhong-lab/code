import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
import nidaqmx

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
	}
	
	attocube=ANC350()
	attocube.initialize()
	axis_index_x=0
	axis_index_y=1
	axis_index_z=2 


	@Task(name='Scan XZ')
	def ReflectionDistribution(self):
		self.F = open(self.filename, 'w')
		self.pw=[]
		for zpoint in range(len(self.zpositions)):
			self.attocube.absolute_move(self.axis_index_z,self.zpositions[zpoint])
			time.sleep(0.1)		
			self.attocube.cl_move(self.axis_index_z,self.zpositions[zpoint])
			self.attocube.frequency[self.axis_index_x]=Q_(self.movef,'Hz')
			self.attocube.amplitude[self.axis_index_x]=Q_(self.movev,'V')
			self.attocube.absolute_move(self.axis_index_x,self.x_start)
			time.sleep(0.1)
			self.attocube.cl_move(self.axis_index_x,self.x_start)
			self.attocube.frequency[self.axis_index_x]=Q_(self.jogf,'Hz')
			self.attocube.amplitude[self.axis_index_x]=Q_(self.movef,'Hz')
			self.attocube.jog(self.axis_index_x,1)
			t0=time.time()
			while time.time()-t0<self.x_time:
				data.append(self.powermeter.power.magnitude*1000)
				time.sleep(1e-3)
			self.attocube.stop()
			time.sleep(0.5)
			print("%d/%d:%f"%(zpoint,len(self.zpositions),self.attocube.position[self.axis_index_x].magnitude))
			for item in data:
				self.F.write("%f,"% item)
			F.write('\n')
			self.pw.append(data)
			values = {
					'power': self.pw
				}
			self.ReflectionDistribution.acquire(values)

		F.close()

		return


	@Task(name = 'Single Step')
	def ReflectionvsTime(self):
		fieldValues = self.scan_parameters.widget.get()
		FREQUENCY_x=fieldValues['Frequency'].magnitude
		FREQUENCY_y=fieldValues['Frequency'].magnitude
		FREQUENCY_z=fieldValues['Frequency'].magnitude
		VOLTAGE_x=fieldValues['Voltage'].magnitude
		VOLTAGE_y=fieldValues['Voltage'].magnitude
		VOLTAGE_z=fieldValues['Voltage'].magnitude
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
		im = np.array(self.pw)
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
	    ('File name', {'type': str, 'default': 'C:\\Users\\Tian Zhong\\Tao\\scan'}),
		('X start', {'type': float, 'default': 2480*1e-6, 'units':'m'}),
		('X seconds', {'type': int, 'default': 2}),
		('Z start', {'type': float, 'default': 1045*1e-6, 'units':'um'}),
		('Z range', {'type': float, 'default': 10*1e-6, 'units':'m'}),
		('Step', {'type': float, 'default': 0.1*1e-6, 'units':'m'}),
		('Jog Voltage', {'type': float, 'default': 30, 'units':'V'}),
		('Move Voltage', {'type': float, 'default': 50, 'units':'V'}),
		('Jog Frequency', {'type': float, 'default': 300, 'units':'Hz'}),
		('Move Frequency', {'type': float, 'default': 300, 'units':'Hz'})
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
		self.movef=fieldValues['Move Frequency'].magnitude
		self.movev=fieldValues['Move Voltage'].magnitude
		self.jogv=fieldValues['Jog Voltage'].magnitude
		self.jogf = fieldValues['Jog Frequency'].magnitude
		self.xsteps = fieldValues['X steps']
		self.nx = fieldValues['X num']
		z_range = fieldValues['Z range'].magnitude *1e6
		step = fieldValues['Step'].magnitude*1e6
		self.x_start = fieldValues['X start'].magnitude*1e6
		z_start = fieldValues['Z start'].magnitude*1e6
		self.filename = fieldValues['File name']
		x_num = fieldValues['X num']
		self.x_time = fieldValues['X seconds']
		self.zpositions = np.arange(z_start,z_start+z_range+step,step)
		#initialize
		self.attocube.frequency[self.axis_index_x]=Q_(self.movef,'Hz')
		self.attocube.frequency[self.axis_index_y]=Q_(self.movef,'Hz')
		self.attocube.frequency[self.axis_index_z]=Q_(self.movef,'Hz')
		self.attocube.amplitude[self.axis_index_x]=Q_(self.movev,'V')
		self.attocube.amplitude[self.axis_index_y]=Q_(self.movev,'V')
		self.attocube.amplitude[self.axis_index_z]=Q_(self.movev,'V')
		self.attocube.absolute_move(self.axis_index_x,self.x_start)
		time.sleep(1)
		self.attocube.absolute_move(self.axis_index_z,z_start)
		time.sleep(1)
		print('initialized')
		return
	@ReflectionDistribution.finalizer     
	def finalize(self):
		return
	
