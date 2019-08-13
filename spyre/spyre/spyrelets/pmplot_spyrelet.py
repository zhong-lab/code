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

	requires = {
   
        'powermeter': PM100D
    }

	@Task(name = 'Single Step')
	def ReflectionvsTime(self):
		self.bs=[]
		self.cs=[]
		t0 = time.time()
		while True:
			t1 = time.time()
			t = t1-t0
			self.bs.append(t)
			self.cs.append(self.powermeter.power.magnitude*1000)
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