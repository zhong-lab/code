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

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.tektronix import TDS5104
from lantz.drivers.lockin import SR865A

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')
second = Q_(1, 's')

class EPR(Spyrelet):
	requires = {
		'osc': TDS5104,
		'fungen': Keysight_33622A,
		'lockin': SR865A
	}

	@Task()
	def startpulse(self, timestep=1e-9):
		params = self.pulse_parameters.widget.get()
		tau0=params['tau']
		repeatmag=params['repeat unit'].magnitude
		scantime=params['scantime'].magnitude

		npulses=1


		time0 = self.lockin.System_Time_Day*24*3600+self.lockin.System_Time_Hours*3600+self.lockin.System_Time_Min*60+self.lockin.System_Time_Seconds
		t = 0
		tau=tau0.magnitude 

		self.dataset.clear()
		self.fungen.clear_mem(1)
		self.fungen.wait()
		self.osc.time_scale(10*1e-6) 

		chn1pulse = Arbseq_Class('chn1pulse', timestep)
		chn1pulse.delays = [0]
		chn1pulse.heights = [0.25]
		chn1pulse.widths = [params['pulse width'].magnitude]
		chn1pulse.totaltime = params['pulse width'].magnitude
		chn1pulse.nrepeats = 0
		chn1pulse.repeatstring = 'once'
		chn1pulse.markerstring = 'highAtStartGoLow'   # This means the trigger pulse
		chn1pulse.markerloc = 0
		chn1pulsewidth = params['pulse width'].magnitude
		chn1pulse.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [params['repeat unit'].magnitude]
		chn1dc.totaltime = params['repeat unit'].magnitude
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dcrepeats = int((tau-1.0*params['pulse width'].magnitude)/(params['repeat unit'].magnitude)) # 1.5
		chn1dc.nrepeats = chn1dcrepeats
		chn1dcwidth = (params['repeat unit'].magnitude)*chn1dcrepeats
		print(tau, params['pulse width'].magnitude, chn1dcrepeats)
		chn1dc.create_sequence()

		chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
		chn1pulse2.delays = [0]
		chn1pulse2.heights = [1]
		chn1pulse2.widths = [params['pulse width'].magnitude]
		chn1pulse2.totaltime = params['pulse width'].magnitude
		chn1pulse2width = params['pulse width'].magnitude
		chn1pulse2.nrepeats = 0
		chn1pulse2.repeatstring = 'once'
		chn1pulse2.markerstring = 'lowAtStart'
		chn1pulse2.markerloc = 0
		chn1pulse2.create_sequence()


		chn1dc1 = Arbseq_Class('chn1dc1', timestep) #Block for 2 tau
		chn1dc1.delays = [0]
		chn1dc1.heights = [0]
		chn1dc1.widths = [params['repeat unit'].magnitude]
		chn1dc1.totaltime = params['repeat unit'].magnitude
		chn1dc1.repeatstring = 'repeat'
		chn1dc1.markerstring = 'lowAtStart'
		chn1dc1.markerloc = 0
		chn1dcrepeats1 = int((2*tau-params['pulse width'].magnitude)/(params['repeat unit'].magnitude)) # 1.5
		chn1dc1.nrepeats = chn1dcrepeats1
		chn1dcwidth = (params['repeat unit'].magnitude)*chn1dcrepeats1
		print(tau, params['pulse width'].magnitude, chn1dcrepeats1)
		chn1dc1.create_sequence()


		chn1dc2 = Arbseq_Class('chn1dc2', timestep) # Repetition delay, outside the loop
		chn1dc2.delays = [0]
		chn1dc2.heights = [0]
		chn1dc2.widths = [params['repeat unit'].magnitude]
		chn1dc2.totaltime = params['repeat unit'].magnitude
		chn1dc2.repeatstring = 'repeat'
		chn1dc2.markerstring = 'lowAtStart'
		chn1dc2repeats = int((params['period'].magnitude-tau-npulses*(2*tau)-(1+npulses)*params['pulse width'].magnitude- 2*chn1dcrepeats1*repeatmag - chn1dcrepeats*repeatmag)/(params['repeat unit'].magnitude))
		chn1dc2.nrepeats = chn1dc2repeats
		print(" Pulse delay {}".format(chn1dc2repeats*params['repeat unit'].magnitude))
		chn1dc2.markerloc = 0
		print((chn1dc2repeats*params['repeat unit'].magnitude) + tau + params['pulse width'].magnitude)
		chn1dc2.create_sequence()


		self.fungen.send_arb(chn1pulse, 1)
		self.fungen.send_arb(chn1dc, 1)
		self.fungen.send_arb(chn1pulse2, 1)
		self.fungen.send_arb(chn1dc2, 1)
		self.fungen.send_arb(chn1dc1, 1)

		seq = [chn1pulse, chn1dc, chn1pulse2]

		for i in range(0,npulses-1):
			seq.append(chn1dc1)
			seq.append(chn1pulse2)
		
		seq.append(chn1dc2)	

		self.fungen.create_arbseq('twoPulse', seq, 1)

		self.fungen.wait()
		self.fungen.voltage[1] = 1.0
		self.fungen.offset[1] = 0.0

		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[1]))



		while(t<scantime):
			
 
		

			self.fungen.output[1] = 'ON'

			naverage = 10
			self.osc.setmode('average')
			t = (self.lockin.System_Time_Day*24*3600+self.lockin.System_Time_Hours*3600+self.lockin.System_Time_Min*60+self.lockin.System_Time_Seconds) - time0	
			self.osc.average(naverage)       
			time.sleep(11)

			self.osc.datasource(2)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			np.savetxt('D:/MW data/20200205/ESR/2/{}.txt'.format(t), np.c_[x,y])   

			self.osc.datasource(3)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			np.savetxt('D:/MW data/20200205/ESR/3/{}.txt'.format(t), np.c_[x,y])
			time.sleep(15)   # Sleeptime for saving data

			self.fungen.output[1] = 'OFF'

			self.osc.setmode('sample')
			time.sleep(2)


	@startpulse.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.wait()

		
		self.osc.data_start(1)
		self.osc.data_stop(500000)
		self.osc.setmode('sample')	

	@startpulse.finalizer
	def finalize(self):
		print('Two Pulse measurements complete.')
		return

	@Element(name='Pulse parameters')
	# Remove the 'config' file from this location everytime you modify the widget:  'C:\Users\zhong\AppData\Roaming\Spyre\main'
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse width', {'type': float, 'default': 4e-6, 'units':'s'}),
		('period', {'type': float, 'default': 1, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 1e-6, 'units':'s'}),
		('tau', {'type': float, 'default': 12e-6, 'units':'s'}),
		('scantime', {'type': int, 'default': 36000, 'units':'dimensionless'})
		]
		w = ParamWidget(params)
		return w
