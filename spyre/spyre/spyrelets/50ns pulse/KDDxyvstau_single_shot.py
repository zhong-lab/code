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
		npulses=params['nPulses'].magnitude
		pulsewidth=params['pulse width'].magnitude
		naverage=params['nAverage'].magnitude
		# nmeasurement=params['nMeasurement'].magnitude						
		freq=params['IQFrequency'].magnitude
		phase=params['Phase'].magnitude
		cavityfreq=params['CavityFreq'].magnitude
		trigperiod=params['period'].magnitude
		triggerdelay=params['trigger delay'].magnitude
		Amp=params['Voltage'].magnitude
		Amp_factor_pi2=params['Pi2factor'].magnitude
		deltaphiiq=93  # Based off calibration
		predelay=50e-9
		postdelay=150e-9

		deltaphase1=0  #X
		deltaphase2=90 #Y
		deltaphase3=30 #Th, 30 degree
		deltaphase4=120 #OT, 120 degree
		deltaphase5=180 #OE, 180 degree

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

# Pix Pulse

		pixPulseI = Arbseq_Class_MW('pixPulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase1)
		pixPulseI.delays=predelay
		pixPulseI.postdelay=postdelay
		pixPulseI.sendTrigger()
		pixPulseI.create_envelope()


		pixPulseQ = Arbseq_Class_MW('pixPulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase1+deltaphiiq)
		pixPulseQ.delays=predelay
		pixPulseQ.postdelay=postdelay		
		pixPulseQ.create_envelope()


# Piy Pulse

		piyPulseI = Arbseq_Class_MW('piyPulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase2)
		piyPulseI.delays=predelay
		piyPulseI.postdelay=postdelay
		piyPulseI.sendTrigger()
		piyPulseI.create_envelope()


		piyPulseQ = Arbseq_Class_MW('piyPulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase2+deltaphiiq)
		piyPulseQ.delays=predelay
		piyPulseQ.postdelay=postdelay		
		piyPulseQ.create_envelope()


# PiTh Pulse

		piThPulseI = Arbseq_Class_MW('piThPulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase3)
		piThPulseI.delays=predelay
		piThPulseI.postdelay=postdelay
		piThPulseI.sendTrigger()
		piThPulseI.create_envelope()


		piThPulseQ = Arbseq_Class_MW('piThPulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase3+deltaphiiq)
		piThPulseQ.delays=predelay
		piThPulseQ.postdelay=postdelay		
		piThPulseQ.create_envelope()

# PiOt Pulse

		piOtPulseI = Arbseq_Class_MW('piOtPulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase4)
		piOtPulseI.delays=predelay
		piOtPulseI.postdelay=postdelay
		piOtPulseI.sendTrigger()
		piOtPulseI.create_envelope()


		piOtPulseQ = Arbseq_Class_MW('piOtPulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase4+deltaphiiq)
		piOtPulseQ.delays=predelay
		piOtPulseQ.postdelay=postdelay		
		piOtPulseQ.create_envelope()

# PiOe Pulse

		piOePulseI = Arbseq_Class_MW('piOePulseI', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase5)
		piOePulseI.delays=predelay
		piOePulseI.postdelay=postdelay
		piOePulseI.sendTrigger()
		piOePulseI.create_envelope()


		piOePulseQ = Arbseq_Class_MW('piOePulseQ', timestep,Wavepipulse,1,pulsewidth,freq,phase+deltaphase5+deltaphiiq)
		piOePulseQ.delays=predelay
		piOePulseQ.postdelay=postdelay		
		piOePulseQ.create_envelope()

# Delay of 2 tau

		delay2 = Arbseq_Class_MW('delay2', timestep,'DC',0,repeatmag,0,0) #Block for 2 tau
		repeatwidthdelay2=(2*tau-pulsewidth-predelay-postdelay)
		delay2.setRepeats(repeatwidthdelay2)
		delay2.create_envelope()


# Send all the Arbs


		self.fungen.send_arb(delay0I, 1)
		self.fungen.send_arb(pi2PulseI, 1)
		self.fungen.send_arb(delay1, 1)
		self.fungen.send_arb(pixPulseI, 1)
		self.fungen.send_arb(delay2, 1)
		self.fungen.send_arb(piyPulseI, 1)
		self.fungen.send_arb(piThPulseI, 1)
		self.fungen.send_arb(piOtPulseI, 1)
		self.fungen.send_arb(piOePulseI, 1)

		self.fungen.send_arb(delay0Q, 2)
		self.fungen.send_arb(pi2PulseQ, 2)
		self.fungen.send_arb(delay1, 2)
		self.fungen.send_arb(pixPulseQ, 2)
		self.fungen.send_arb(delay2, 2)
		self.fungen.send_arb(piyPulseQ, 2)
		self.fungen.send_arb(piThPulseQ, 2)
		self.fungen.send_arb(piOtPulseQ, 2)
		self.fungen.send_arb(piOePulseQ, 2)

# Make sequence

		seq = [delay0I,pi2PulseI, delay1]

		seq1 = [delay0Q ,pi2PulseQ, delay1]

		for i in range(0,2*npulses):

			seq.append(piThPulseI)
			seq.append(delay2)
			seq.append(pixPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(pixPulseI)
			seq.append(delay2)
			seq.append(piThPulseI)
			seq.append(delay2)
			seq.append(piOtPulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(piOePulseI)
			seq.append(delay2)
			seq.append(piyPulseI)
			seq.append(delay2)
			seq.append(piOtPulseI)
			seq.append(delay2)

			seq1.append(piThPulseQ)
			seq1.append(delay2)
			seq1.append(pixPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(pixPulseQ)
			seq1.append(delay2)
			seq1.append(piThPulseQ)
			seq1.append(delay2)
			seq1.append(piOtPulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(piOePulseQ)
			seq1.append(delay2)
			seq1.append(piyPulseQ)
			seq1.append(delay2)
			seq1.append(piOePulseQ)
			seq1.append(delay2)

		self.fungen.create_arbseq('twoPulseI', seq, 1)
		self.fungen.create_arbseq('twoPulseQ',seq1,2)

		self.fungen.wait()
		self.fungen.voltage[1] = 0.500*Amp
		self.fungen.offset[1] = 0.000
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))

		self.fungen.voltage[2] = 0.480*Amp
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
		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod

		time.sleep(10)

# Set the Source frequency offset from the cavity by IF frequency 
		self.source.set_CW_Freq(cavityfreq+freq)
		self.source.RF_ON()

		time.sleep(5)

		self.osc.average(naverage)  

# Start collecting data
		# measurementno=0
		# while(measurementno<nmeasurement):
			
		# 	measurementno=measurementno+1		
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'

		self.osc.setmode('average')

		time.sleep(naverage*trigperiod)

		self.osc.datasource(3)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20200806/KDDxy/Scan1/ch3/{}_{}.txt'.format(tau*1e6,npulses), np.c_[x,y])   

		self.osc.datasource(4)
		x,y=self.osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		np.savetxt('D:/MW data/20200806/KDDxy/Scan1/ch4/{}_{}.txt'.format(tau*1e6,npulses), np.c_[x,y])
		time.sleep(15)   # Sleeptime for saving data

		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'

		self.osc.setmode('sample')
		time.sleep(2)

		self.source.RF_OFF()

	@Task()
	def Record_KDD(self):
		params = self.pulse_parameters.widget.get()
		npulses=params['nPulses'].magnitude

		self.osc.delaymode_off()
		self.osc.data_start(1)
		self.osc.data_stop(2000000)  # max resolution ius 4e6, the resolution for 200 ns scale is 5e5
		self.osc.setmode('sample')
		self.source.RF_OFF()
		self.source.Mod_OFF()
		self.source.set_RF_Power(10) 

		# tau1=params['tau1'].magnitude
		# taustep=params['taustep'].magnitude
		# npoints=params['nPoints'].magnitude

		# for tau in np.linspace(tau1,tau1+(npoints)*taustep,npoints,endpoint=False):
		# 	self.record(tau)
		# return

		tauarray=[2e-6,4e-6,6e-6,8e-6]

		minreadpulses=8			# Minimum number of pulses that have to be read for having enough datapoints
		oscscale=200e-6         # These two values were chose since I was measuring at 100 MHz so with these settings the sampling resolution is 0.8 ns which is ~ 12 sample per waveform
        						 # This is an optimum choice between keeping the timescale same for all measurements and having enough samples to detect  100 MHz
		maxscale=1e-3            # Based on resolution of 100 MHz with 2M points
								# With this I can read 7 echoes with 0.5 ms
		timescale=oscscale
		sc1=5e-6
		sc2=10e-6
		for tau in tauarray:

			if(tau>=sc1):
				oscscale=400e-6

			if(tau>=sc2):
				oscscale=1e-3

			self.osc.time_scale(oscscale)
			self.record(tau)


		return

	@Record_KDD.initializer
	def initialize(self):
		return

	@Record_KDD.finalizer
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
		# ('tau1', {'type': float, 'default': 500e-9, 'units':'s'}),
		# ('taustep', {'type': float, 'default': 50e-6, 'units':'s'}),
		# ('nPoints', {'type': int, 'default': 10, 'units':'dimensionless'}),
		('nPulses', {'type': int, 'default': 8, 'units':'dimensionless'}),
		('nAverage', {'type': int, 'default': 5, 'units':'dimensionless'}),
		# ('nMeasurement', {'type': int, 'default': 1, 'units':'dimensionless'}),
		('IQFrequency', {'type': float, 'default': 1e8, 'units':'dimensionless'}),
		('Phase', {'type': float, 'default': 0, 'units':'dimensionless'}),
		('pulse width', {'type': float, 'default': 50e-9, 'units':'s'}),
		('CavityFreq', {'type': float, 'default': 4.9849e9, 'units':'dimensionless'}),
		('Voltage', {'type': float, 'default': 1.0, 'units':'dimensionless'}),
		('Pi2factor', {'type': float, 'default': 0.707, 'units':'dimensionless'}),
		]
		
		w = ParamWidget(params)
		return w
