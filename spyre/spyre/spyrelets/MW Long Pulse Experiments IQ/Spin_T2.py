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

class Record(Spyrelet):

	requires = {
		'osc': TDS5104,
		'delaygen': DG645,
		'source':N5181A,
		'fungen': Keysight_33622A,
	}


	def record(self,tau):
# Set the AWG 
		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)

		self.fungen.wait()

		params = self.pulse_parameters.widget.get()
		repeatmag=params['dc repeat unit'].magnitude
		timestep=params['timestep'].magnitude
		pulsewidth1=params['pulse1 width'].magnitude
		pulsewidth2=params['pulse2 width'].magnitude
		npulses=params['nPulses'].magnitude
		naverage=params['nAverage'].magnitude
		nmeasurement=params['nMeasurement'].magnitude						
		freq=params['IQFrequency'].magnitude
		phase=params['Phase'].magnitude
		deltaphase=params['DeltaPhase'].magnitude
		PiAmp=params['Pulse2Voltage'].magnitude
		Pi2Amp=params['Pulse1Voltage'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		deltaphiiq=90

# Waves for Spin Echo
		Wavepi2pulse='Square'   # 'Gaussian' or 'Square'
		Wavepipulse='Square'

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

# Pi Pulse

		piPulseI = Arbseq_Class_MW('piPulseI', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase)
		piPulseI.create_envelope()

		piPulseQ = Arbseq_Class_MW('piPulseQ', timestep,Wavepipulse,PiAmp,pulsewidth2,freq,phase+deltaphase+deltaphiiq)
		piPulseQ.create_envelope()

# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth2)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Long delay for setting the trigger rate 	

		longdelay = Arbseq_Class_MW('longdelay', timestep,'DC',0,repeatmag,0,0) # Repetition delay, outside the loop
		repeatwidthlongdelay = ((trigperiod-tau-npulses*(2*tau)-(npulses)*pulsewidth2-pulsewidth1- 2*repeatwidthdelay1 - repeatwidthdelay2))
		longdelay.setRepeats(repeatwidthlongdelay)
		longdelay.create_envelope()

# Send all the Arbs

		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(piPulseI, 1)
		self.fungen.send_arb(delay2, 1)
		self.fungen.send_arb(longdelay, 1)

		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(piPulseQ, 2)
		self.fungen.send_arb(delay2, 2)
		self.fungen.send_arb(longdelay, 2)

# Make sequence

		seq = [delay1, pi2PulseI, delay1, piPulseI]

		seq1 = [delay1, pi2PulseQ, delay1, piPulseQ]

		for i in range(0,npulses-1):
			seq.append(delay2)
			seq.append(piPulseI)


			seq1.append(delay2)
			seq1.append(piPulseQ)

		
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

# Sync the two channels 

		self.fungen.sync()
# AWG Output On
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'


# Set the delay generator for gating 

		self.delaygen.Trigger_Source='External Rising Edge'
		self.delaygen.delay['A']=0
		self.delaygen.delay['B']=pulsewidth1*0.5+tau+(npulses-1)*2*tau+pulsewidth2*0.5+5e-6

		time.sleep(10)

# Set the Source frequency offset from the cavity by IF frequency 
		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()

		time.sleep(5)

		self.osc.delaymode_on()
		self.osc.delay_position(0)
		self.osc.delay_time(pulsewidth1*0.5+ 2*tau-50e-6)  # This makes sure that echo is at center of screen
		self.osc.average(naverage)  

# Start collecting data
		measurementno=0
		while(measurementno<nmeasurement):
			
			measurementno=measurementno+1		
			self.fungen.output[1] = 'ON'
			self.fungen.output[2] = 'ON'

			self.osc.setmode('average')

			time.sleep(naverage*trigperiod)

			self.osc.datasource(3)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			np.savetxt('D:/MW data/20200614/SpinT2/Scan10/ch3/{}/{}.txt'.format(measurementno,tau*1e6), np.c_[x,y])   

			self.osc.datasource(4)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			np.savetxt('D:/MW data/20200614/SpinT2/Scan10/ch4/{}/{}.txt'.format(measurementno,tau*1e6), np.c_[x,y])
			time.sleep(15)   # Sleeptime for saving data

			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'

			self.osc.setmode('sample')
			time.sleep(2)

		self.source.RF_OFF()

	@Task()
	def Record_T2(self):
		params = self.pulse_parameters.widget.get()

		self.osc.delaymode_off()
		self.osc.data_start(1)
		self.osc.data_stop(2000000) 
		self.osc.time_scale(10e-6)
		self.osc.setmode('sample')
		self.source.RF_OFF()

		tau1=params['tau1'].magnitude
		tau2=params['tau2'].magnitude
		npoints=params['nPoints'].magnitude

		for tau in np.linspace(tau1,tau2,npoints):
			self.record(tau)
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
		('dc repeat unit', {'type': float, 'default': 1e-6, 'units':'s'}),
		('timestep', {'type': float, 'default': 1e-9, 'units':'s'}),
		('period', {'type': float, 'default': 1, 'units':'s'}),
		('tau1', {'type': float, 'default': 30e-6, 'units':'s'}),
		('tau2', {'type': float, 'default': 500e-6, 'units':'s'}),
		('nPoints', {'type': int, 'default': 10, 'units':'dimensionless'}),
		('nPulses', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('nAverage', {'type': int, 'default': 5, 'units':'dimensionless'}),
		('nMeasurement', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('DeltaPhase', {'type': float, 'default': 90, 'units':'dimensionless'}),
		('Pulse1Voltage', {'type': float, 'default': 0.1, 'units':'dimensionless'}),
		('Pulse2Voltage', {'type': float, 'default': 0.14, 'units':'dimensionless'}),
		('pulse1 width', {'type': float, 'default': 8e-6, 'units':'s'}),
		('pulse2 width', {'type': float, 'default': 8e-6, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 4.9611e9, 'units':'dimensionless'}),
		]
		w = ParamWidget(params)
		return w
