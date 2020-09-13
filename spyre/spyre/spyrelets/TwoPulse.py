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
# from lantz.drivers.tektronix import TDS5104
# from lantz.drivers.keysight import N5181A
# from lantz.drivers.tektronix import TDS5104
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
		# 'osc': TDS5104,
		'delaygen': DG645,
		# 'source':N5181A,
		'fungen': Keysight_33622A,
	}


	def record(self):
# Set the AWG 
		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)

		self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		repeatmag=params['dc repeat unit'].magnitude
		timestep=params['timestep'].magnitude
		pulsewidth1=params['pulse width1'].magnitude								
		pulsewidth1=params['pulse width2'].magnitude								
		freq=params['IFFrequency'].magnitude
		phase=params['Phase'].magnitude
		trigperiod=params['period'].magnitude
		triggerdelay=params['trigger delay'].magnitude
		awgvoltage=params['Voltage'].magnitude
		runtime=params['Runtime'].magnitude
		tau=params['tau'].magnitude

# Waveform type for Spin Echo
		Wavepi2pulse='Square'   # 'Gaussian' or 'Square'
		Wavepipulse='Square'



# Triggering delay

		delay0I = Arbseq_Class_MW('delay0I', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0I=(triggerdelay)
		delay0I.setRepeats(repeatwidthdelay0I)
		delay0I.create_envelope()
		delay0I.repeatstring = 'onceWaitTrig'

		delay0Q = Arbseq_Class_MW('delay0Q', timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0Q=(triggerdelay)
		delay0Q.setRepeats(repeatwidthdelay0Q)
		delay0Q.repeatstring = 'onceWaitTrig'
		delay0Q.create_envelope()

# Pi/2 pulse

		pi2PulseI = Arbseq_Class_MW('pi2PulseI', timestep,Wavepi2pulse,1,pulsewidth1,freq,phase)
		pi2PulseI.create_envelope()

		pi2PulseQ = Arbseq_Class_MW('pi2PulseQ', timestep,Wavepi2pulse,1,pulsewidth1,freq,phase)	
		pi2PulseQ.create_envelope()

# Delay of Tau

		delay1 = Arbseq_Class_MW('delay1', timestep,'DC',0,repeatmag,0,0)
		repeatwidthdelay1=(tau-1.0*pulsewidth-predelay-postdelay)
		delay1.setRepeats(repeatwidthdelay1)
		delay1.create_envelope()

# Pi Pulse

		piPulseI = Arbseq_Class_MW('piPulseI', timestep,Wavepipulse,1,pulsewidth2,freq,phase)
		piPulseI.create_envelope()


		piPulseQ = Arbseq_Class_MW('piPulseQ', timestep,Wavepipulse,1,pulsewidth2,freq,phase)		
		piPulseQ.create_envelope()

# Send all the Arbs


		self.fungen.send_arb(delay0I, 1)
		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(piPulseI, 1)

		self.fungen.send_arb(delay0Q, 2)
		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(piPulseQ, 2)

# Make sequence

		seq = [delay0I,pi2PulseI, delay1, piPulseI]

		seq1 = [delay0Q ,pi2PulseQ, delay1, piPulseQ]


		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.wait()
		self.fungen.voltage[1] = awgvoltage*volt
		self.fungen.offset[1] = 0
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = awgvoltage*volt
		self.fungen.offset[2] = 0

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
		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'

		time.sleep(runtime)

		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'

	@Task()
	def Record_T2(self):
		self.record()


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
		('dc repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('trigger delay', {'type': float, 'default': 32e-9, 'units':'s'}),	
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('period', {'type': float, 'default': 2, 'units':'s'}),
		('IFFrequency', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('pulse width1', {'type': float, 'default': 200e-9, 'units':'s'}),
		('pulse width2', {'type': float, 'default': 200e-9, 'units':'s'}),
		('Voltage', {'type': float, 'default': 0.5, 'units':'dimensionless'}),
		('Runtime', {'type': float, 'default': 1000, 'units':'s'}),				
		('tau', {'type': float, 'default': 1e-6, 'units':'s'}),				
		]
		
		w = ParamWidget(params)
		return w
