'''
drawing distribution of our fiber coupling
with a reak attocube and a fake pwm for testing
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

from attocube_spyrelet import Attocube

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
    xs = np.arrange(0,6000,10)
    ys = np.arrange(0,6000,10)
    pw = np.zeros((nx,ny),dtype=float)


    @Task()
    def ReflectionDistribution(self):
    	xpoint = 0
    	ypoint = 0
    	for pos_y in ys:
    		for pos_x in xs:
    			pw[xpoint,ypoint] = random.random()
    			xpoint = xpoint+1
    		ypoint = ypoint+1
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

    def initialize(self):
        return

    def finalize(self):
        return