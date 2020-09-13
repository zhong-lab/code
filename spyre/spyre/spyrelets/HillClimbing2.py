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


class HillClimbing(Spyrelet):
	requires = {
		'pmd': PM100D

	}
	daq = nidaqmx.Task()
	attocube=ANC350()
	attocube.initialize()
	axis_index_x=0
	axis_index_y=1
	axis_index_z=2 

	@Task(name='HillClimbing')
	def Reflection(self):
		self.flag=0
		self.daq.start()
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
		c0 = self.pmd.power.magnitude * 1000
		while True:
			self.ratio = self.pmd.power.magnitude * 1000/c0
			while ratio < 0.95:
				self.state = "searching"
				n = search_around()
				if n ==0:
					break
			couple_power = self.pmd.power.magnitude * 1000
			self.state = "Monitoring"
			values = {
				'ratio' = self.ratio
				'state' = self.state
				}
			self.Reflection.acquire(values)
			time.sleep(0.05)
		self.daq.stop()
	def search_around(self):
		pw = []
		pw.append(self.pmd.power.magnitude * 1000)
		self.attocube.single_step(self.axis_index_x,1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)
		self.attocube.single_step(self.axis_index_z,1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)
		self.attocube.single_step(self.axis_index_x,-1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)
		self.attocube.single_step(self.axis_index_x,-1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)	
		self.attocube.single_step(self.axis_index_z,-1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)					
		self.attocube.single_step(self.axis_index_z,-1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)	
		self.attocube.single_step(self.axis_index_x,+1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)	
		self.attocube.single_step(self.axis_index_x,+1)
		time.sleep(0.2)
		pw.append(self.pmd.power.magnitude * 1000)
		n = pw.find(max(pw))
		if n == 7:
			self.attocube.single_step(self.axis_index_x,-1)
		else if n == 6:
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_x,-1)
		else if n == 5:
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_z,1)
		else if n == 4:
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_z,1)
			self.attocube.single_step(self.axis_index_z,1)
		else if n == 3:
			self.attocube.single_step(self.axis_index_x,-1)
			self.attocube.single_step(self.axis_index_z,1)
			self.attocube.single_step(self.axis_index_z,1)
		else if n == 2:
			self.attocube.single_step(self.axis_index_z,1)
			self.attocube.single_step(self.axis_index_z,1)
		else if n == 1:
			self.attocube.single_step(self.axis_index_z,1)
		else if n == 0:
			self.attocube.single_step(self.axis_index_z,1)
			self.attocube.single_step(self.axis_index_x,-1)
		return n

	@Element(name='indicator')
	def CouplingRatio(self):
		text = QTextEdit()
		text.setPlainText('State: non\nCouple: non % ')
		return text
	@CouplingRatio.on(Reflection.acquired)
	def _couplingratio_update(self,ev):
		w=ev.widget
		w.setPlainText('State: %s\nCouple: %f % '%(self.state,self.ratio))
		return 
	@Element(name='Parameters')
	def parameters(self):
		params = [
		('Voltage', {'type': float, 'default': 25, 'units':'V'}),
		('Frequency', {'type': float, 'default': 500, 'units':'Hz'})
		]
		w = ParamWidget(params)
		return w
	@Element(name='stop')
	def stopbutton(self):
		button7 = QPushButton('STOP')
		button7.move(0,20)
		button7.clicked.connect(self.stopmoving) #direction :-z
		return button7       
	def stopmoving(self):
		self.flag=1
		self.attocube.stop()
		return