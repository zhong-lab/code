import numpy as np
import pyqtgraph as pg
import time
import csv
import os
import msvcrt

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

from lantz.drivers.tektronix.tds5104 import TDS5104

class PrintScope(Spyrelet):
	requires = {
		'osc': TDS5104
	}
	xs=[]
	ys=[]
	x1s=[]
	y1s=[]
	field='2'

	def saveData(self,x,y,x1,y1,index,field):
		out_name = "D:\\Data\\12.16.2020_YSO_absorption"
		np.savez(os.path.join(out_name,"trace"),x,y)
		#out_name = "D:\\Data\\1.16.2020\\ch2"
		np.savez(os.path.join(out_name,"sweep"),x1,y1)
		print('Data stored')

	@Task()
	def save(self):
		print('Press Enter for Save Screen')
		index=0
		while True:
			if msvcrt.kbhit():
				if msvcrt.getwche() == '\r':
					self.osc.datasource(1)
					self.xs,self.ys=self.osc.curv()
					self.osc.datasource(3)
					self.x1s,self.y1s=self.osc.curv()
					values = {
							'x': self.xs,
							 'y': self.ys,
							 'x1': self.x1s,
							 'y1': self.y1s
							}
					self.save.acquire(values)
					self.saveData(self.xs,self.ys,self.x1s,self.y1s,str(index),self.field)
					print('Press Enter for Save Screen')
					index=index+1

	@Element(name='Histogram')
	def averaged(self):
		p = LinePlotWidget()
		p.plot('Ch1')
		p.plot('Ch3')
		return p

	@averaged.on(save.acquired)
	def averaged_update(self, ev):
		w = ev.widget
		xs = np.array(self.xs)
		ys = np.array(self.ys)
		x1s = np.array(self.x1s)
		y1s = np.array(self.y1s)
		w.set('Ch1', xs=xs, ys=ys)
		w.set('Ch3', xs=x1s, ys=y1s)
		return

	@save.initializer
	def initialize(self):
		return

	@save.finalizer
	def finalize(self):
		return