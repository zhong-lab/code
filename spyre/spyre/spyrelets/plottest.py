'''
drawing distribution of our fiber coupling
wfor testing
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

#from attocube_spyrelet import Attocube  #have touble with finding this, not necessary though

from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs.pm100d import PM100D

class ScanXY(Spyrelet):
	
    requires = {
        #'attocube': ANC350()
        'powermeter': PM100D()
    }
    
    x_range = 6000 #x scan range (um)
    y_range = 6000 #um
    step = 10 #resolution 10um
    xs = np.arange(0,x_range+1,step) 
    ys = np.arange(0,y_range+1,step)
    pw = np.zeros((len(xs),len(ys)),dtype=float)
    axis_index_x=0
	axis_index_y=1
	axis_index_z=2

	zpos = 1000 # set z position in um


    @Task(name='scan XY')
    def ReflectionDistribution(self):
    	#initialize
        '''
    	self.attocube.initialize()
    	self.attocube.cl_move(self.axis_index_x,Q(0,'nm'))
		self.attocube.cl_move(self.axis_index_y,Q(0,'nm'))
		self.attocube.cl_move(self.axis_index_z,Q(self.zpos,'um'))
        '''
    	#scan XY
    	for ypoint in range(len(self.ys)):
    		#self.attocube.cl_move(self.axis_index_y,Q_(ys[ypoint],'um'))
    		for xpoint in range(len(self.xs)):
    			#self.attocube.cl_move(self.axis_index_x,Q_(xs[xpoint],'um'))				
    			time.sleep(0.01)  
    			#not sure how long we should wait before measuring reflection after every attocube movement,
    			#set this to 0.1s, will take 0.1s*600*600=1hour
    			#need to ask Christina
    			self.pw[xpoint,ypoint] = power_meter.power
    			values = {
    				'x': self.xs[xpoint],
    				'y': self.ys[ypoint],
    				'power': self.pw
    			}
    			self.ReflectionDistribution.acquire(values)
    	
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