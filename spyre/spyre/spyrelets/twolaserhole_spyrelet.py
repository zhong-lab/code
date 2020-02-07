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
		out_name = "D:\\Data\\1.19.2020\\twolaser\\0.7T"
		np.savez(os.path.join(out_name,str(t)),x,y)
		print('Data stored under File Name:')

	@Task()
	def run(self):
		params = self.parameters.widget.get()
		self.fungen.phase[1] = float(params['initialPhase'])
		curPhase = self.fungen.phase[1]
		time.sleep(2)
		for i in range(int(params['totalPoints'])):
			self.osc.mode='sample'
			self.osc.mode='average'
			print("Phase is: ", curPhase)
			time.sleep(125)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			self.saveData(x,y,curPhase)
			time.sleep(1)
			curPhase+=float(params['stepPhase'])
			self.fungen.phase[1]=curPhase
			time.sleep(2)



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