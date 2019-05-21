import numpy as np
import pyqtgraph as pg
import time
import csv

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.stanford.srs900 import SRS900
from lantz.drivers.qutools import QuTAG

class DarkCount(Spyrelet):
	requires = {
    	'srs': SRS900
    }

	@Task()
	def getIVcurce(self):
		self.srs.module_reset[6]
		self.srs.wait_time(10000)
		biasCurrentParams = self.bias_current.widget.get()
		resistance = 10000
		startCurrent = biasCurrentParams['Start Current'].to('A').magnitude
		stepSize = biasCurrentParams['Step Size'].to('A').magnitude
		stopCurrent = biasCurrentParams['Stop Current'].to('A').magnitude
		print('start current is' + str(startCurrent))
		print('step size is' + str(stepSize))
		print('stop current is'+ str(stopCurrent))
		expParams = self.exp_params.widget.get()
		currentCurrent = startCurrent
		self.srs.SIM928_voltage[6] = currentCurrent*resistance
		self.srs.SIM928_on[6]
		points = (stopCurrent-startCurrent)/stepSize
		BC =[]
		DC =[]
		for i in range(int(points)):
			lost = self.qutag.getLastTimestamps(True)
			time.sleep(expParams['Exposure Time'].magnitude)
			timestamps = self.qutag.getLastTimestamps(True)
			bc = points
			darkcounts = timestamps[2]
			BC.append(currentCurrent)
			DC.append(darkcounts)
			currentCurrent +=stepSize
			self.srs.SIM928_voltage[6] = currentCurrent*resistance
		np.savetxt(expParams['File Name'], (BC,DC))
		print('Data stored under File Name: ' + expParams['File Name'])	
		return



	@Element(name = 'Bias Current')
	def bias_current(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start Current', {'type': float, 'default': 2, 'units': 'uA'}),
        ('Step Size', {'type': float, 'default': 0.2, 'units': 'uA'}),
        ('Stop Current', {'type': float, 'default': 10, 'units': 'uA'})
        ]
		w = ParamWidget(params)
		return w

	@Element(name = 'Experimental Parameters')
	def exp_params(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('File Name', {'type': str})
        ]
		w = ParamWidget(params)
		return w


	@getDarkCounts.initializer
	def initialize(self):
		print('The identification of this instrument is : ' + self.srs.idn)
		print(self.srs.self_test)
		return

	@getDarkCounts.finalizer
	def finalize(self):
		return

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
        ##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.enableChannels((start,stop))


