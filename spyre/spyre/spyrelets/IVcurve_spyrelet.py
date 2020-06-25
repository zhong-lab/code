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

class IV_Curve(Spyrelet):
	requires = {
		'srs': SRS900
	}
	currents=[]
	voltages=[]
	volt = Q_(1, 'V')

	@Task()
	def getIVCurve(self):
		self.srs.SIM928_voltage[5]=0
		self.srs.module_reset[5]
		self.srs.module_reset[7]
		self.srs.wait_time(100000)
		biasCurrentParams = self.current.widget.get()
		resistance = 10000
		startCurrent = biasCurrentParams['Start Current'].to('A').magnitude
		stepSize = biasCurrentParams['Step Size'].to('A').magnitude
		stopCurrent = biasCurrentParams['Stop Current'].to('A').magnitude
		print('start current is' + str(startCurrent))
		print('step size is' + str(stepSize))
		print('stop current is'+ str(stopCurrent))
		expParams = self.exp_params.widget.get()
		currentCurrent = startCurrent
		self.srs.clear_status
		self.srs.SIM928_voltage[5] = currentCurrent*resistance
		self.srs.SIMmodule_on[5]
		self.srs.SIMmodule_on[7]
		self.srs.wait_time(100000)
		points = ((stopCurrent-startCurrent)/stepSize)+(1+stepSize)
		for i in range(int(points)):
			self.currents.append(currentCurrent*resistance)
			print(self.srs.SIM970_voltage[7].magnitude)
			self.voltages.append(self.srs.SIM970_voltage[7].magnitude)
			currentCurrent += stepSize
			self.srs.SIM928_voltage[5] = currentCurrent*resistance
		self.srs.SIM928_voltage[5]=0
		self.srs.module_reset[5]
		values = {
			  'cs': self.currents,
			  'V': self.voltages,
			}
		self.getIVCurve.acquire(values)
		#datadir = 'D:\Data\\'
		#np.savetxt(datadir+expParams['File Name']+'.csv', (BC,V), delimiter=',')
		#print('Data stored under File Name: ' + expParams['File Name'])	
		return

	@Element(name = 'Experimental Parameters')
	def exp_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('File Name', {'type': str})
		]
		w = ParamWidget(params)
		return w

	@Element(name = ' Current')
	def current(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Current', {'type': float, 'default': 0, 'units': 'uA'}),
		('Step Size', {'type': float, 'default': 0.1, 'units': 'uA'}),
		('Stop Current', {'type': float, 'default': 10, 'units': 'uA'})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Histogram')
	def ivcurveplot(self):
		p=LinePlotWidget()
		p.plot('IV Curve')
		return p

	@ivcurveplot.on(getIVCurve.acquired)
	def ivcurveplot_update(self, ev):
		w=ev.widget
		cs=np.array(self.currents)
		vs=np.array(self.voltages)
		w.set('IV Curve', xs=cs, ys=vs)
		return		

	@getIVCurve.initializer
	def initialize(self):
		print('The identification of this instrument is : ' + self.srs.idn)
		print(self.srs.self_test)
		return

	@getIVCurve.finalizer
	def finalize(self):
		return

