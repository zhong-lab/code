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

from lantz.drivers.stanford import DG645
from lantz.drivers.VNA import E5071B

from lantz.log import log_to_screen, DEBUG


volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')


class Record(Spyrelet):

	requires = {
		'delaygen': DG645,
		'vna': E5071B,
	}


	def record(self):
# Set the AWG 
		self.dataset.clear()
		# self.fungen.clear_mem(1)
		# self.fungen.clear_mem(2)

		# self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		naverage=params['nAverage'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		tau_mw=params['MWpulsewidth'].magnitude
		tau_opt=params['Optpulsewidth'].magnitude
		tau_wait=params['Waitingtime'].magnitude

# Set VNA Parameters

		self.vna.set_s_parameter(1,1,'S42')
		self.vna.freq_cent=cavityfreq
		self.vna.freq_span=1e3
		self.vna.IF_bandwidth=1e3
		self.vna.source_power=-15



# Set the delay generator for triggering the AWG and scope

		self.delaygen.delay['A']=0
		self.delaygen.delay['B']=0
		self.delaygen.delay['C']=0
		self.delaygen.delay['D']=tau_mw		# RF Pulse
		self.delaygen.delay['E']=tau_wait   # Optical pulse + waiting time
		self.delaygen.delay['F']=tau_opt    
		self.delaygen.delay['G']=0          # Trigger  for VNA
		self.delaygen.delay['H']=tau_opt


		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

		self.vna.set_average(1,'OFF')   
		self.vna.set_average(1,'ON')

		time.sleep(naverage*trigperiod)

		tr1=self.vna.get_trace(1)
		freq1=self.vna.get_traceX(1)

		# time.sleep(10)

		np.savetxt('D:/MW data/20201020/RamanHeterodyne/scan1.txt', np.c_[freq1,tr1])

		return


	@Task()
	def RamanHeterodyne(self):
		params = self.pulse_parameters.widget.get()

		# self.osc.delaymode_off()


		# tau1=params['tau1'].magnitude
		# taustep=params['taustep'].magnitude
		# npoints=params['nPoints'].magnitude

		# for tau in np.linspace(tau1,tau1+(npoints)*taustep,npoints,endpoint=False):
		# 	self.record(tau)
		# return

		# tauarray=[1.5e-6,2e-6,2.5e-6,3e-6,3.5e-6,4e-6,4.5e-6]
		# tauarray=[1.8e-6,2.2e-6,2.6e-6,3.3e-6,3.8e-6,4.3e-6]
		# tauarray=[1.5e-6,1.8e-6,2.1e-6,2.4e-6,2.7e-6,3.0e-6,3.3e-6,3.6e-6,3.9e-6,4.2e-6,4.5e-6]

		# tauarray=[10e-6]

		self.record()


	@RamanHeterodyne.initializer
	def initialize(self):
		return

	@RamanHeterodyne.finalizer
	def finalize(self):
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('period', {'type': float, 'default': 5, 'units':'s'}),
		('nAverage', {'type': int, 'default': 200, 'units':'dimensionless'}),
		('MWpulsewidth', {'type': float, 'default': 100.0e-3, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 5.69758e9, 'units':'dimensionless'}),
		('Optpulsewidth', {'type': float, 'default': 100.0e-3, 'units':'s'}),
		('Waitingtime', {'type': float, 'default': 0e-3, 'units':'s'}),
		]
		
		w = ParamWidget(params)
		return w

