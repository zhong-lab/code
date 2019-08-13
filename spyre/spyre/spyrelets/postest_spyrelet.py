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

class POS(Spyrelet):
	requires = {
	}
	
	attocube=ANC350()
	attocube.initialize()
	axis_index_x=0
	axis_index_y=1
	axis_index_z=2 
	F1 = open('C:\\Users\\Tian Zhong\\Tao\\pos_x.txt', 'w')
	F2 = open('C:\\Users\\Tian Zhong\\Tao\\pos_y.txt', 'w')
	F3 = open('C:\\Users\\Tian Zhong\\Tao\\pos_z.txt', 'w')

	@Task(name='Scan XZ')
	def ReflectionDistribution(self):
		for zpoint in range(len(self.zpositions)):
			self.attocube.absolute_move(self.axis_index_z,self.zpositions[zpoint])
			print("%d/%d"%(zpoint+1,len(self.zpositions)))
			for xpoint in range(len(self.xpositions)):
				self.attocube.absolute_move(self.axis_index_x,self.xpositions[xpoint])
				if xpoint ==0:
					time.sleep(0.5)            				
				self.pos_x[zpoint][xpoint] = self.attocube.position[self.axis_index_x].magnitude
				self.pos_y[zpoint][xpoint] = self.attocube.position[self.axis_index_y].magnitude
				self.pos_z[zpoint][xpoint] = self.attocube.position[self.axis_index_z].magnitude
				if xpoint ==0:
					time.sleep(0.5)
					self.F1.write("\n")  
					self.F2.write("\n")
					self.F3.write("\n") 
				time.sleep(0.001)
			for item in self.pos_x[zpoint,:]:
				self.F1.write("%f,"% item)
			for item in self.pos_y[zpoint,:]:
				self.F2.write("%f,"% item)
			for item in self.pos_z[zpoint,:]:
				self.F3.write("%f,"% item)
		print("finished")
		return


	
	@ReflectionDistribution.initializer
	def initialize(self):
		print('initializing')
		fieldValues = self.scan_parameters.widget.get()
		FREQUENCY_x=fieldValues['Frequency'].magnitude
		FREQUENCY_y=fieldValues['Frequency'].magnitude
		FREQUENCY_z=fieldValues['Frequency'].magnitude
		VOLTAGE_x=fieldValues['Voltage'].magnitude
		VOLTAGE_y=fieldValues['Voltage'].magnitude
		VOLTAGE_z=fieldValues['Voltage'].magnitude
		x_range = fieldValues['X range'].magnitude*1e6 
		z_range = fieldValues['Z range'].magnitude *1e6
		step = fieldValues['Step'].magnitude*1e6
		x_start = fieldValues['X start'].magnitude*1e6
		z_start = fieldValues['Z start'].magnitude*1e6
		y_pos = fieldValues['Y position'].magnitude*1e6
		print(x_start)
		self.xpositions = np.arange(x_start,x_start+x_range+step,step) 
		self.zpositions = np.arange(z_start,z_start+z_range+step,step)
		self.pos_x = np.zeros((len(self.zpositions),len(self.xpositions)),dtype=float)
		self.pos_y = np.zeros((len(self.zpositions),len(self.xpositions)),dtype=float)		
		self.pos_z = np.zeros((len(self.zpositions),len(self.xpositions)),dtype=float)
		#initialize
		self.attocube.frequency[self.axis_index_x]=Q_(FREQUENCY_x,'Hz')
		self.attocube.frequency[self.axis_index_y]=Q_(FREQUENCY_y,'Hz')
		self.attocube.frequency[self.axis_index_z]=Q_(FREQUENCY_z,'Hz')
		self.attocube.amplitude[self.axis_index_x]=Q_(VOLTAGE_x,'V')
		self.attocube.amplitude[self.axis_index_y]=Q_(VOLTAGE_y,'V')
		self.attocube.amplitude[self.axis_index_z]=Q_(VOLTAGE_z,'V')
		self.attocube.absolute_move(self.axis_index_x,x_start)
		self.attocube.absolute_move(self.axis_index_z,z_start)
		time.sleep(5)
		print('initialized')
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
	@Element(name='Scan Parameters')
	def scan_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Y position', {'type': float, 'default': 1000*1e-6, 'units':'m'}),
		('X start', {'type': float, 'default': 1*1e-6, 'units':'m'}),
		('X range', {'type': float, 'default': 6000*1e-6, 'units':'m'}),
		('Z start', {'type': float, 'default': 0, 'units':'um'}),
		('Z range', {'type': float, 'default': 6000*1e-6, 'units':'m'}),
		('Step', {'type': float, 'default': 0.1*1e-6, 'units':'m'}),
		('Voltage', {'type': float, 'default': 20, 'units':'V'}),
		('Frequency', {'type': float, 'default': 200, 'units':'Hz'})
		]
		w = ParamWidget(params)
		return w
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
	@Element(name='stop')
	def stopbutton(self):
		button7 = QPushButton('STOP')
		button7.move(0,20)
		button7.clicked.connect(self.stopmoving) #direction :-z
		return button7       
	def stopmoving(self):
		self.attocube.stop()
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