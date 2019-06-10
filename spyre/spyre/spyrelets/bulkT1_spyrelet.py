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
from lantz.drivers.bristol import Bristol_771

class BulkT1(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'wm': Bristol_771
	}

	def saveData(self, wl, x, y,i):
		out_name = "D:\\Data\\5.25.2019\\OpticalT1"  
		np.savez(os.path.join(out_name,str(i)),wl,x,y)

	@Task()
	def background(self):
		##Collect background amplitude for each point
		return

	@Task()
	def data(self):
		##Collect actual data
		self.dataset.clear()
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'ON'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		self.fungen.waveform[1] = 'TRIANGLE'
		self.fungen.waveform[2] = 'DC'
		for i in range(20):
			self.fungen.offset[2] = 0.1*i
			time.sleep(10)
			wl=self.wm.measure_wavelength()
			x,y = self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			self.saveData(wl,x,y,i)


	@background.initializer
	def initialize(self):
		return

	@background.finalizer
	def finalize(self):
		return

	@data.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

	@data.finalizer
	def finalize(self):
		return

	@Element(name='Parameters')
	def parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 500e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

