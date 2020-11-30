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
		'delaygen': DG645,
		'source':N5181A,
		'fungen': Keysight_33622A,
	}


	def record(self,tau,freqOpt):
# Set the AWG 
		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)

		self.fungen.wait()

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
		tau_opt=params['Optpulsewidth'].magnitude

		deltaphiiq=98  # Based off calibration
		predelay=50e-9
		postdelay=0.55e-6


# Waves for Spin Echo
		Wavepi2pulse='Square'   # 'Gaussian' or 'Square'
		Wavepipulse='Square'



# Triggering delay

		delay0I = Arbseq_Class_MW('delay0I', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0I=(triggerdelay)
		delay0I.setRepeats(repeatwidthdelay0I)
		delay0I.create_envelope()
		delay0I.repeatstring = 'onceWaitTrig'
		# delay0I.sendTrigger()

		delay0Q = Arbseq_Class_MW('delay0Q', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0Q=(triggerdelay)
		delay0Q.setRepeats(repeatwidthdelay0Q)
		delay0Q.repeatstring = 'onceWaitTrig'
		delay0Q.create_envelope()

# Pi/2 pulse

		pi2PulseI = Arbseq_Class_MW('pi2PulseI', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase)
		pi2PulseI.delays=predelay
		pi2PulseI.postdelay=postdelay
		pi2PulseI.sendTrigger()
		pi2PulseI.create_envelope()

		pi2PulseQ = Arbseq_Class_MW('pi2PulseQ', timestep,Wavepi2pulse,Amp_factor_pi2,pulsewidth,freq,phase+deltaphiiq)
		pi2PulseQ.delays=predelay
		pi2PulseQ.postdelay=postdelay		
		pi2PulseQ.create_envelope()

# Delay of Tau

		delay1 = Arbseq_Class_MW('delay1', timestep,'DC',0,repeatmag,0,0)
		repeatwidthdelay1=(tau-1.0*pulsewidth-predelay-postdelay)
		delay1.setRepeats(repeatwidthdelay1)
		delay1.create_envelope()

# Pi Pulse

		piPulseI = Arbseq_Class_MW('piPulseI', timestep,Wavepipulse,Amp_factor_pi,pulsewidth,freq,phase+deltaphase)
		piPulseI.delays=predelay
		piPulseI.postdelay=postdelay
		piPulseI.sendTrigger()
		piPulseI.create_envelope()


		piPulseQ = Arbseq_Class_MW('piPulseQ', timestep,Wavepipulse,Amp_factor_pi,pulsewidth,freq,phase+deltaphase+deltaphiiq)
		piPulseQ.delays=predelay
		piPulseQ.postdelay=postdelay		
		piPulseQ.create_envelope()

# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth-predelay-postdelay)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Send all the Arbs


		self.fungen.send_arb(delay0I, 1)
		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(piPulseI, 1)
		self.fungen.send_arb(delay2, 1)

		self.fungen.send_arb(delay0Q, 2)
		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(piPulseQ, 2)
		self.fungen.send_arb(delay2, 2)

# Make sequence

		seq = [delay0I,pi2PulseI, delay1, piPulseI]

		seq1 = [delay0Q ,pi2PulseQ, delay1, piPulseQ]

		for i in range(0,npulses-1):
			seq.append(delay2)
			seq.append(piPulseI)


			seq1.append(delay2)
			seq1.append(piPulseQ)

		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.trigger_source[1]='EXTERNAL'
		self.fungen.trigger_source[2]='EXTERNAL'

		self.fungen.wait()
		self.fungen.voltage[1] = 0.500
		self.fungen.offset[1] = 0.000
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = 0.480
		self.fungen.offset[2] = -0.001

		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[2]))

# Sync the two channels 

		self.fungen.sync()
# AWG Output On
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'


# Set the delay generator for triggering the AWG and scope

		self.delaygen.delay['A']=0
		self.delaygen.delay['B']=10e-9
		self.delaygen.delay['C']=0
		self.delaygen.delay['D']=0
		self.delaygen.delay['E']=np.maximum(2*tau+0.8e-6-0.5*tau_opt,0)
		self.delaygen.delay['F']=tau_opt

		# self.delaygen.delay['A']=0
		# self.delaygen.delay['B']=10e-9
		# self.delaygen.delay['C']=0
		# self.delaygen.delay['D']=0
		# self.delaygen.delay['E']=0+tau_opt+tau_wait
		# self.delaygen.delay['F']=tau_opt

		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

# Set the Source frequency offset from the cavity by IF frequency 
		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()


		self.osc.delaymode_on()
		self.osc.delay_position(0)
		self.osc.delay_time(2*tau-800e-9)  # This makes sure that echo is at center of screen
		# self.osc.delay_time(2*tau-800e-9)  # This makes sure that echo is at center of screen

		time.sleep(5)

		# self.osc.average(naverage)  

# Start collecting data
		
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'

		self.osc.setmode('average')

		time.sleep(naverage*trigperiod)

		self.osc.datasource(3)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20201026/RamanHeterodyne/Scan2/ch3/{}.txt'.format(freqOpt), np.c_[x,y])   

		self.osc.datasource(4)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20201026/RamanHeterodyne/Scan2/ch4/{}.txt'.format(freqOpt), np.c_[x,y])
		time.sleep(15)   # Sleeptime for saving data

		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'

		self.osc.setmode('sample')
		time.sleep(2)

		self.source.RF_OFF()

	@Task()
	def Record_T2(self):
		params = self.pulse_parameters.widget.get()
		freqOpt=params['FreqOPT'].magnitude

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

		# tauarray=[1.5e-6,2e-6,2.5e-6,3e-6,3.5e-6,4e-6,4.5e-6]
		# tauarray=[1.8e-6,2.2e-6,2.6e-6,3.3e-6,3.8e-6,4.3e-6]
		# tauarray=[1.5e-6,1.8e-6,2.1e-6,2.4e-6,2.7e-6,3.0e-6,3.3e-6,3.6e-6,3.9e-6,4.2e-6,4.5e-6]
		tauarray=[5e-6]

		# tauarray=[10e-6]

		for tau in tauarray:
			self.record(tau,freqOpt)
		return

	@Record_T2.initializer
	def initialize(self):
		return

	@Record_T2.finalizer
	def finalize(self):
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
		('nAverage', {'type': int, 'default': 200, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('DeltaPhase', {'type': float, 'default': 90, 'units':'dimensionless'}),
		('pulse width', {'type': float, 'default': 1e-6, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 5.69758e9, 'units':'dimensionless'}),
		('Pi2voltage', {'type': float, 'default': 0.707, 'units':'dimensionless'}),
		('Pivoltage', {'type': float, 'default': 1.0, 'units':'dimensionless'}),
		('Optpulsewidth', {'type': float, 'default': 4.0e-6, 'units':'s'}),
		('FreqOPT', {'type': float, 'default': 195216.5, 'units':'dimensionless'}),
		]
		
		w = ParamWidget(params)
		return w

# This is for short, high power pulse
	# 	params = [
	# #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
	# 	('dc repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
	# 	('trigger delay', {'type': float, 'default': 32e-9, 'units':'s'}),	
	# 	('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
	# 	('period', {'type': float, 'default': 2, 'units':'s'}),
	# 	('nPulses', {'type': int, 'default': 1, 'units':'dimensionless'}),
	# 	('nAverage', {'type': int, 'default': 50, 'units':'dimensionless'}),
	# 	('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
	# 	('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
	# 	('DeltaPhase', {'type': float, 'default': 90, 'units':'dimensionless'}),
	# 	('pulse width', {'type': float, 'default': 200e-9, 'units':'s'}),
	# 	('CavityFreq', {'type': float, 'default': 4.9849e9, 'units':'dimensionless'}),
	# 	('Pi2factor', {'type': float, 'default': 0.06, 'units':'dimensionless'}),
	# 	]