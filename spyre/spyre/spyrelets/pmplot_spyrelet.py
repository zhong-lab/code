'''
drawing distribution of our fiber coupling
with a attocube and a fake pwm for testing
'''
import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import time
import random

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

#from attocube_spyrelet import Attocube

from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs.pm100d import PM100D

class Test(Spyrelet):
	'''
	requires = {
		'atc': ANC350
		'pmd': PM100D
	}
	'''
	nx = 600
	ny = 600
	x_range = 6000
	y_range = 6000
	xs = np.arange(0,6000,10)
	ys = np.arange(0,6000,10)
	pw = np.zeros((nx,ny),dtype=float)


	@Task()
	def ReflectionDistribution(self):
		xpoint = 0
		ypoint = 0
		for pos_y in self.ys:
			if xpoint>=600: xpoint=599
			if ypoint>=600: ypoint=599
			for pos_x in self.xs:
				if xpoint>=600: xpoint=599
				if ypoint>=600: ypoint=599
				self.pw[xpoint,ypoint] = random.random()
				xpoint = xpoint+1
			ypoint = ypoint+1
			if xpoint>=600: xpoint=599
			if ypoint>=600: ypoint=599
			values = {
				'x': self.xs[xpoint],
				'y': self.ys[ypoint],
				'power': self.pw
			}
			self.ReflectionDistribution.acquire(values)
			time.sleep(2) 
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
	    def buttons(self):

            button1 = QPushButton('x +',self)
            button1.move(0, 20)
            button2 = QPushButton('x -',self)
            button2.move(0, 30)
            button3 = QPushButton('z +',self)
            button3.move(0, 40)
            button4 = QPushButton('z -',self)
            button4.move(0, 50)
            button1.clicked.connect(self.move_x1)
            button2.clicked.connect(self.move_x2)
            button3.clicked.connect(self.move_z1)
            button4.clicked.connect(self.move_z2)
        return
    	def move_x1(self):
        	print("PyQt5 button click")
	
	def initialize(self):
		return

	def finalize(self):
		return
