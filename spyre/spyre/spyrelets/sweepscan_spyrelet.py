import numpy as np
import pyqtgraph as pg
import time
import csv
import os

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.tektronix import TDS2024C

class SweepScan(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}

	def saveData(self,filename,data):
		out_name = "D:\\Data\\8.7.2019\\box"
		np.savetxt(os.path.join(out_name,filename),data)

	def stepDown(self,channel,scale):
		scales=[5.0,2.0,1.0,0.5,0.2,0.1,0.05,0.02,0.01,0.005]
		i=scales.index(scale)
		if i+1<len(scales):
			return scales[i+1]
		else:
			return scales[i]

	@Task()
	def run(self):
		outputs=[]
		freqs=[]
		params=self.parameters.widget.get()
		self.fungen.waveform[1]='sin'
		self.fungen.voltage[1]=params['amplitude']
		self.fungen.frequency[1]=params['frequency start']
		self.fungen.output[1]='ON'
		self.osc.time_scale(5.0/(2.0*np.pi*self.fungen.frequency[1]).magnitude)
		self.osc.position(3,0)
		while self.fungen.frequency[1].magnitude<params['frequency stop'].magnitude:
			outputs.append(float(self.osc._measure('PK2pk',3)))
			freqs.append(self.fungen.frequency[1].magnitude)
			time.sleep(1)
			self.fungen.frequency[1]=self.fungen.frequency[1]+params['frequency step']
			self.osc.time_scale(5.0/(2.0*np.pi*self.fungen.frequency[1]).magnitude)
		self.saveData('output2.txt',np.c_[freqs,outputs])
		

	@Element(name='Parameters')
	def parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('amplitude', {'type': float, 'default': 1, 'units':'V'}),
		('frequency start', {'type': float, 'default': 1000, 'units':'Hz'}),
		('frequency stop', {'type': float, 'default': 20000, 'units':'Hz'}),
		('frequency step', {'type': float, 'default': 1000, 'units':'Hz'}),
		]
		w = ParamWidget(params)
		return w

	@run.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

	@run.finalizer
	def finalize(self):
		print('Scan finished.')
		return