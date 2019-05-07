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
	qutag = None

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@qutagInit.initializer
	def initialize(self):
		from lantz.drivers.qutools import QuTAG
		self.qutag = QuTAG()
		devType = self.qutag.getDeviceType()
		if (devType == self.qutag.DEVTYPE_QUTAG):
			print("found quTAG!")
		else:
			print("no suitable device found - demo mode activated")
		print("Device timebase:" + str(self.qutag.getTimebase()))
		return

	@qutagInit.finalizer
	def finalize(self):
		return

	@Task()
	def getDarkCounts(self):
		biasVoltageParams = self.bias_voltage.widget.get()
		expParams = self.exp_params.widget.get()
		self.srs.SIM928_voltage[6] = biasVoltageParams['Start Voltage']
		currentVoltage = biasVoltageParams['Start Voltage']
		self.srs.SIM928_on[6]
		points = (biasVoltageParams['Stop Voltage'] - biasVoltageParams['Start Voltage'])/biasVoltageParams['Step Size']
		for i in range(int(points.magnitude)):
			lost = self.qutag.getLastTimestamps(True)
			time.sleep(expParams['Exposure Time'].magnitude)
			timestamps = self.qutag.getLastTimestamps(True)
			counts = timestamps[2]
			print(counts)
			currentVoltage += biasVoltageParams['Step Size']
			print(currentVoltage)
			self.srs.SIM928_voltage[6] = float(currentVoltage.magnitude)
			print(self.srs.SIM928_voltage[6])

		return



	@Element(name = 'Bias Voltage')
	def bias_voltage(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Start Voltage', {'type': float, 'default': 0.5, 'units': 'volt'}),
        ('Step Size', {'type': float, 'default': 0.05, 'units':'volt'}),
        ('Stop Voltage', {'type': float, 'default': 1, 'units':'volt'})
        ]
		w = ParamWidget(params)
		return w

	@Element(name = 'Experimental Parameters')
	def exp_params(self):
		params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('Exposure Time', {'type': int, 'default': 10, 'units': 's'})
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


