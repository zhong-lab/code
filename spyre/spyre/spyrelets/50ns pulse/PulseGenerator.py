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

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')
second = Q_(1, 's')

class PulseGeneratorAWG(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
	}

	@Task()
	def startpulse(self):

		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		tau=params['tau'].magnitude
		repeatmag=params['dc repeat unit'].magnitude

		timestep=params['timestep'].magnitude
		pulsewidth=params['pulse width'].magnitude
		triggerdelay=params['trigger delay'].magnitude

		npulses=params['nPulses'].magnitude
		freq=params['Frequency'].magnitude
		phase=params['Phase'].magnitude
		deltaphase=params['DeltaPhase'].magnitude
		PiAmp=params['PiVoltage'].magnitude
		deltaphiiq=93

		Wavepi2pulse='Square'   # 'Gaussian' or 'Square' or 'COMP1',2,3,4
		Wavepipulse='Square'
		Amp_factor_pi2=0.707

		predelay=50e-9
		postdelay=100e-9


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

		piPulseI = Arbseq_Class_MW('piPulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase)
		piPulseI.delays=predelay
		piPulseI.postdelay=postdelay
		piPulseI.sendTrigger()

		piPulseI.create_envelope()

		piPulseQ = Arbseq_Class_MW('piPulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase+deltaphiiq)
		piPulseQ.delays=predelay
		piPulseQ.postdelay=postdelay		
		piPulseQ.create_envelope()

# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth-predelay-postdelay)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Long delay for setting the trigger rate 	

		# longdelay = Arbseq_Class_MW('longdelay', timestep,'DC',0,repeatmag1,0,0) # Repetition delay, outside the loop
		# repeatwidthlongdelay = ((params['period'].magnitude-tau-npulses*(2*tau)-(1+npulses)*pulsewidth- 2*repeatwidthdelay1 - repeatwidthdelay2))
		# longdelay.setRepeats(repeatwidthlongdelay)
		# longdelay.create_envelope()
		# print('repeat number {}'.format(longdelay.nrepeats))

# Send all the Arbs

		self.fungen.send_arb(delay0I, 1)
		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(piPulseI, 1)
		self.fungen.send_arb(delay2, 1)
		# self.fungen.send_arb(longdelay, 1)

		self.fungen.send_arb(delay0Q, 2)
		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(piPulseQ, 2)
		self.fungen.send_arb(delay2, 2)
		# self.fungen.send_arb(longdelay, 2)

# Make sequence

		seq = [delay0I,pi2PulseI, delay1, piPulseI]

		seq1 = [delay0Q ,pi2PulseQ, delay1, piPulseQ]

		for i in range(0,npulses-1):
			seq.append(delay2)
			seq.append(piPulseI)


			seq1.append(delay2)
			seq1.append(piPulseQ)

		
		# seq.append(longdelay)
		# seq1.append(longdelay)	

		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.wait()
		self.fungen.voltage[1] = 0.500*PiAmp
		self.fungen.offset[1] = 0.002
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = 0.480*PiAmp
		self.fungen.offset[2] = -0.001

		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[2]))


		self.fungen.sync()
# Output On
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'

# Sleeptime
		time.sleep(200)


	@startpulse.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.wait()

	@startpulse.finalizer
	def finalize(self):
		print('Two Pulse measurements complete.')
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('trigger delay', {'type': float, 'default': 32e-9, 'units':'s'}),	
		('pulse width', {'type': float, 'default': 100e-9, 'units':'s'}),
		('period', {'type': float, 'default': 1, 'units':'s'}),
		('dc repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		# ('dc repeat unit large', {'type': float, 'default': 1e-6, 'units':'s'}),		
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('tau', {'type': float, 'default': 200e-9, 'units':'s'}),
		('nPulses', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('Frequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('DeltaPhase', {'type': float, 'default': 90, 'units':'dimensionless'}),
		('PiVoltage', {'type': float, 'default': 0.999, 'units':'dimensionless'})
		]
		w = ParamWidget(params)
		return w
