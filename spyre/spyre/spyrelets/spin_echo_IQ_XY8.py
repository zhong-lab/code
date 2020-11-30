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

from lantz.log import log_to_screen, DEBUG

class Record(Spyrelet):

	requires = {
		'osc': TDS5104,
		'delaygen': DG645,
		'source':N5181A,
		'fungen': Keysight_33622A,
	}


	def record(self):
		self.dataset.clear()
		log_to_screen(DEBUG)

		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		tau=params['tau'].magnitude
		repeatmag=params['dc repeat unit'].magnitude
		timestep=params['timestep'].magnitude
		pulsewidth1=params['pulse1 width'].magnitude
		pulsewidth2=params['pulse2 width'].magnitude
		npulses=params['nPulses'].magnitude
		freq=params['IQFrequency'].magnitude
		phase=params['Phase'].magnitude
		PiAmp=params['Pulse2Voltage'].magnitude
		Pi2Amp=params['Pulse1Voltage'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		deltaphiiq=90

		Wavepi2pulse='Square'   # 'Gaussian' or 'Square'
		Wavepipulse='Square'

		deltaphase1=0  #X
		deltaphase2=90 #Y
		deltaphase3=180 #-X
		deltaphase4=270  #-Y

# Pi/2 pulse

		pi2PulseI = Arbseq_Class_MW('pi2PulseI', timestep,Wavepi2pulse,Pi2Amp,pulsewidth1,freq,phase)
		pi2PulseI.sendTrigger()
		pi2PulseI.create_envelope()

		pi2PulseQ = Arbseq_Class_MW('pi2PulseQ', timestep,Wavepi2pulse,Pi2Amp,pulsewidth1,freq,phase+deltaphiiq)
		pi2PulseQ.create_envelope()

# Delay of Tau

		delay1 = Arbseq_Class_MW('delay1', timestep,'DC',0,repeatmag,0,0)
		repeatwidthdelay1=(tau-1.0*pulsewidth1)
		delay1.setRepeats(repeatwidthdelay1)
		delay1.create_envelope()

# Pix Pulse

		pixPulseI = Arbseq_Class_MW('pixPulseI', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase1)
		pixPulseI.create_envelope()

		pixPulseQ = Arbseq_Class_MW('pixPulseQ', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase1+deltaphiiq)
		pixPulseQ.create_envelope()

# Piy Pulse

		piyPulseI = Arbseq_Class_MW('piyPulseI', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase2)
		piyPulseI.create_envelope()

		piyPulseQ = Arbseq_Class_MW('piyPulseQ', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase2+deltaphiiq)
		piyPulseQ.create_envelope()

# Pimx Pulse

		pimxPulseI = Arbseq_Class_MW('pimxPulseI', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase3)
		pimxPulseI.create_envelope()

		pimxPulseQ = Arbseq_Class_MW('pimxPulseQ', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase3+deltaphiiq)
		pimxPulseQ.create_envelope()

# Pimy Pulse

		pimyPulseI = Arbseq_Class_MW('pimyPulseI', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase4)
		piyPulseI.create_envelope()

		pimyPulseQ = Arbseq_Class_MW('pimyPulseQ', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase2+deltaphiiq)
		pimyPulseQ.create_envelope()


# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth2)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Long delay for setting the trigger rate 	

		longdelay = Arbseq_Class_MW('longdelay', timestep,'DC',0,repeatmag,0,0) # Repetition delay, outside the loop
		repeatwidthlongdelay = ((trigperiod- 2*(repeatwidthdelay1) - pulsewidth1 - npulses*(16*pulsewidth2) - 16*repeatwidthdelay2 ))  # For XY4

		longdelay.setRepeats(repeatwidthlongdelay)
		longdelay.create_envelope()
		print('repeat number {}'.format(longdelay.nrepeats))

# Send all the Arbs

		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(pixPulseI, 1)
		self.fungen.send_arb(piyPulseI, 1)
		self.fungen.send_arb(pimxPulseI, 1)
		self.fungen.send_arb(pimyPulseI, 1)
		self.fungen.send_arb(delay2, 1)
		self.fungen.send_arb(longdelay, 1)

		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(pixPulseQ, 2)
		self.fungen.send_arb(piyPulseQ, 2)
		self.fungen.send_arb(pimxPulseQ, 2)
		self.fungen.send_arb(pimyPulseQ, 2)
		self.fungen.send_arb(delay2, 2)
		self.fungen.send_arb(longdelay, 2)

# Make sequence

		seq = [delay1, pi2PulseI, delay1]

		seq1 = [delay1, pi2PulseQ, delay1]

		for i in range(0,npulses):

			seq.append(pixPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(pixPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(pixPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(pixPulseI)
			seq.append(delay2)

			seq.append(pimxPulseI)
			seq.append(delay2)
			seq.append(pimyPulseI)
			seq.append(delay2)
			seq.append(pimxPulseI)
			seq.append(delay2)
			seq.append(pimyPulseI)
			seq.append(delay2)
			seq.append(pimyPulseI)
			seq.append(delay2)
			seq.append(pimxPulseI)
			seq.append(delay2)
			seq.append(pimyPulseI)
			seq.append(delay2)
			seq.append(pimxPulseI)
			seq.append(delay2)

			seq1.append(pixPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(pixPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(pixPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(pixPulseQ)
			seq1.append(delay2)

			seq1.append(pimxPulseQ)
			seq1.append(delay2)
			seq1.append(pimyPulseQ)
			seq1.append(delay2)
			seq1.append(pimxPulseQ)
			seq1.append(delay2)
			seq1.append(pimyPulseQ)
			seq1.append(delay2)
			seq1.append(pimyPulseQ)
			seq1.append(delay2)
			seq1.append(pimxPulseQ)
			seq1.append(delay2)
			seq1.append(pimyPulseQ)
			seq1.append(delay2)
			seq1.append(pimxPulseQ)
			seq1.append(delay2)


		seq.append(longdelay)
		seq1.append(longdelay)	

		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.wait()
		self.fungen.voltage[1] = 1.0
		self.fungen.offset[1] = 0.0
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = 1.0
		self.fungen.offset[2] = 0.0

		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[2]))


		self.fungen.sync()
# Output On
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'





		self.delaygen.Trigger_Source='External Rising Edge'
		self.delaygen.delay['A']=0
		self.delaygen.delay['B']=pulsewidth1*0.5+tau+(16*npulses-1)*(2*tau) + pulsewidth2*0.5 + 5e-6  # For XY4

		time.sleep(5)

		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()


		self.osc.delaymode_on()
		self.osc.delay_position(0)
		self.osc.delay_time(pulsewidth1*0.5-50e-6+(16*npulses)*(2*tau))  # For XY4

		# time.sleep(5)

		naverage = 10
		self.osc.setmode('average')
		self.osc.average(naverage)

		time.sleep(naverage*trigperiod)

		self.osc.datasource(3)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20200614/ch3/test.txt', np.c_[x,y])

		# self.osc.datasource(4)
		# x,y=self.osc.curv()
		# x = np.array(x)
		# x = x-x.min()
		# y = np.array(y)
		# np.savetxt('D:/MW data/20200606/Optimization/SNR/Test1/ch4.txt', np.c_[x,y])
		time.sleep(5)



		return


	@Task()
	def Record_Spin_Echo_IQ_DD(self):
		self.osc.delaymode_off()
		self.osc.data_start(1)
		self.osc.data_stop(4000000) 
		self.osc.time_scale(10e-6)
		self.osc.setmode('sample')
		self.source.RF_OFF()
		self.record()
		self.source.RF_OFF()


	@Record_Spin_Echo_IQ_DD.initializer
	def initialize(self):
		return

	@Record_Spin_Echo_IQ_DD.finalizer
	def finalize(self):
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('dc repeat unit', {'type': float, 'default': 1e-6, 'units':'s'}),
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('period', {'type': float, 'default': 1, 'units':'s'}),
		('tau', {'type': float, 'default': 40e-6, 'units':'s'}),
		('nPulses', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('Pulse1Voltage', {'type': float, 'default': 0.1, 'units':'dimensionless'}),
		('Pulse2Voltage', {'type': float, 'default': 0.14, 'units':'dimensionless'}),
		('pulse1 width', {'type': float, 'default': 8e-6, 'units':'s'}),
		('pulse2 width', {'type': float, 'default': 8e-6, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 4.9611e9, 'units':'dimensionless'})
		]
		w = ParamWidget(params)
		return w
