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

class QutagGraph(Spyrelet):
	qutag = None
	xs=[]
	ys=[]

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))


	@Task()
	def graph(self):
		self.configureQutag()
		qutagparams = self.qutag_params.widget.get()
		lost
		while True:
			time.sleep(10)
			timestamps = self.qutag.getLastTimestamps(True)

			tstamp = timestamps[0] # array of timestamps
			tchannel = timestamps[1] # array of channels
			values = timestamps[2] # number of recorded timestamps
			for k in range(values):
				# output all stop events together with the latest start event
				if tchannel[k] == start:
					synctimestamp = tstamp[k]
				else:
					stoptimestamp = tstamp[k]
					stoparray.append(stoptimestamp)
					tempStopArray.append(stoptimestamp)
			histCounter+=1
			if histCounter%30==0:
				self.createPlottingHist(tempStopArray, timebase, bincount,qutagparams['Total Hist Width Multiplier']*tau.magnitude)
				self.xs = np.asarray(range(len(self.hist)))
				self.ys=np.asarray(self.hist)
				values = {
				't': np.asarray(range(len(self.hist))),
				'y': np.asarray(self.hist),
				}
				self.startpulse.acquire(values)
				tempStopArray = []


	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 1}),
		('Bin Count', {'type': int, 'default': 1000})
		]
		w = ParamWidget(params)
		return w