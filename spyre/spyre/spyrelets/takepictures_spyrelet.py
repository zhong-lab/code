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
from lantz.drivers.tektronix.tds5104 import TDS5104

class TwoLaserHole(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS5104
	}

	def saveData(self,x,y,t):
		out_name = "D:\\Data\\1.19.2020\\twolaser\\0.125T"
		np.savez(os.path.join(out_name,str(round(t,2))),x,y)
		print('Data stored under File Name:')

	@Task()
	def run(self):
		params = self.parameters.widget.get()
		time.sleep(5)
		time0=time.time()
		while True:
			x,y=self.osc.curv()
			stopTime=time.time()-time0
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			self.saveData(x,y,stopTime)
			time.sleep(1.1)

	@Element(name='Parameters')
	def parameters(self):
		params = [
		('initialPhase', {'type': float, 'default': 30.0}),
		('stepPhase', {'type': float, 'default': 2.0}),
		('totalPoints', {'type': int, 'default': 50}),
		('points', {'type': int, 'default': 5}),
		]
		w = ParamWidget(params)
		return w

	@run.initializer
	def initialize(self):
		print('init')

	@run.finalizer
	def finalize(self):
		print('fin')
		return