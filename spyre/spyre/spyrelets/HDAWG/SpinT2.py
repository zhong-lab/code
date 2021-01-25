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

from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford import DG645
from lantz.drivers.tektronix import TDS5104
from lantz.drivers.keysight import N5181A
from lantz.drivers.tektronix import TDS5104
from lantz.log import log_to_screen, DEBUG

import zhinst.toolkit as tk

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')


class Record(Spyrelet):

	requires = {
		'osc': TDS5104,
		'source':N5181A,
	}


	def record(self,tau):
# Set the AWG 
		self.dataset.clear()




		params = self.pulse_parameters.widget.get()
		repeatmag=params['dc repeat unit'].magnitude
		timestep=params['timestep'].magnitude
		npulses=params['nPulses'].magnitude
		pulsewidth=params['pulse width'].magnitude
		naverage=params['nAverage'].magnitude
								
		freq=params['IQFrequency'].magnitude
		phase=params['Phase'].magnitude
		deltaphase=params['DeltaPhase'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		triggerdelay=params['trigger delay'].magnitude
		Amp_factor_pi2=params['Pi2voltage'].magnitude
		Amp_factor_pi=params['Pivoltage'].magnitude

		deltaphiiq=98  # Based off calibration


		hdawg = tk.HDAWG("hdawg1", "dev8345", interface="usb")

		hdawg.setup()           # set up data server connection
		hdawg.connect_device()  # connect device to data server


		print(f"name:        {hdawg.name}")
		print(f"serial:      {hdawg.serial}")
		print(f"device:      {hdawg.device_type}")
		print(f"options:     {hdawg.options}")
		print(f"interface:   {hdawg.interface}")
		print(f"connected:   {hdawg.is_connected}")

		hdawg.nodetree.system.clocks.referenceclock.source(0)
		maxvolt=1.0
		hdawg.nodetree.sigouts[0].range(maxvolt)
		hdawg.nodetree.sigouts[1].range(maxvolt)


		hdawg.nodetree.system.awg.oscillatorcontrol(1)



		hdawg.awgs[0].set_sequence_params(sequence_type="Custom",path="C:/Program Files/Zurich Instruments/LabOne/WebServer/awg/src/test.seqc",custom_params=[],)
		hdawg.awgs[0].compile()

		hdawg.nodetree.triggers.out[0].source(4)
		hdawg.nodetree.triggers.out[1].source(6)
		hdawg.nodetree.triggers.out[2].source(0)

		iqfreq=100e6
		offset1=0.01
		offset2=0.02
		hdawg.nodetree.oscs[0].freq(iqfreq)
		hdawg.nodetree.oscs[1].freq(iqfreq)
		hdawg.awgs[0].gain1=1.0
		hdawg.awgs[0].gain2=0.95
		hdawg.nodetree.sigouts[0].offset(offset1)
		hdawg.nodetree.sigouts[1].offset(offset2)
		hdawg.awgs[0].modulation_phase_shift=98
		hdawg.awgs[0].enable_iq_modulation()

		hdawg.awgs[0].run()


		hdawg.awgs[0].output1("on")   
		hdawg.awgs[0].output2("on")

		# self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

# Set the Source frequency offset from the cavity by IF frequency 
		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()


		self.osc.delaymode_on()
		self.osc.delay_position(0)
		self.osc.delay_time(2*tau-800e-9)  # This makes sure that echo is at center of screen

		time.sleep(5)

		self.osc.average(naverage)  

# Start collecting data
		
		# self.fungen.output[1] = 'ON'
		# self.fungen.output[2] = 'ON'

		self.osc.setmode('average')

		time.sleep(naverage*trigperiod)

		self.osc.datasource(3)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20201111/SpinT2/Scan18/ch3/{}.txt'.format(tau*1e6), np.c_[x,y])   

		self.osc.datasource(4)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20201111/SpinT2/Scan18/ch4/{}.txt'.format(tau*1e6), np.c_[x,y])
		time.sleep(15)   # Sleeptime for saving data

		# self.fungen.output[1] = 'OFF'
		# self.fungen.output[2] = 'OFF'

		self.osc.setmode('sample')
		time.sleep(2)

		self.source.RF_OFF()

	@Task()
	def Record_T2(self):
		params = self.pulse_parameters.widget.get()

		self.osc.delaymode_off()
		self.osc.data_start(1)
		self.osc.data_stop(2000000)  # max resolution ius 4e6, the resolution for 200 ns scale is 5e5
		self.osc.time_scale(400e-9)
		self.osc.setmode('sample')
		self.source.RF_OFF()
		self.source.Mod_OFF()
		self.source.set_RF_Power(-3) 

		# tau1=params['tau1'].magnitude
		# taustep=params['taustep'].magnitude
		# npoints=params['nPoints'].magnitude

		# for tau in np.linspace(tau1,tau1+(npoints)*taustep,npoints,endpoint=False):
		# 	self.record(tau)
		# return

		# start=5
		# step=1
		# num=25

		# tauarray=np.arange(0,num)*step+start


		# tauarray=tauarray*1e-6

		tauarray=[5e-6]   # for long T2 species
		#tauarray=[5e-6,10e-6,25e-6,50e-6,100e-6,150e-6,200e-6,250e-6,300e-6,350e-6,400e-6]   # for short T2 species
		#tauarray=[5e-6,10e-6,20e-6,30e-6,40e-6,50e-6,70e-6,90e-6,100e-6,125e-6,150e-6,175e-6]   # for short T2 species
		#tauarray=[6.5e-6,6.75e-6,9.5e-6,11e-6,12e-6,13e-6]   # for long T2 species

		#tauarray=[1e-3]

		for tau in tauarray:
			self.record(tau)
		return

	@Record_T2.initializer
	def initialize(self):
		return

	@Record_T2.finalizer
	def finalize(self):

		hdawg.awgs[0].output1("off")   
		hdawg.awgs[0].output2("off")

		hdawg.awgs[0].disable_iq_modulation()
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('dc repeat unit', {'type': float, 'default': 1e-7, 'units':'s'}),
		('trigger delay', {'type': float, 'default': 32e-9, 'units':'s'}),	
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('period', {'type': float, 'default': 2, 'units':'s'}),
		('nPulses', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('nAverage', {'type': int, 'default': 25, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('DeltaPhase', {'type': float, 'default': 90, 'units':'dimensionless'}),
		('pulse width', {'type': float, 'default': 1e-6, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 5.69758e9, 'units':'dimensionless'}),
		('Pi2voltage', {'type': float, 'default': 0.707, 'units':'dimensionless'}),
		('Pivoltage', {'type': float, 'default': 1.0, 'units':'dimensionless'}),
		]
		
		w = ParamWidget(params)
		return w
