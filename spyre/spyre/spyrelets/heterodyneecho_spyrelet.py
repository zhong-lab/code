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
from lantz.drivers.tektronix import TDS2024C

class HeterodyneEcho(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}

	def saveData(self,x,y,index):
		out_name = "D:\\Data\\5.27.2019\\Rabi4"
		np.savez(os.path.join(out_name,str(index)),x,y)
		print('Data stored under File Name: ' + str(index))

	@Task()
	def startpulse(self,timestep=1e-9):
		params = self.pulse_parameters.widget.get()
		tau=params['start tau']
		period = params['period'].magnitude
		repeat_unit = params['repeat unit'].magnitude
		pulse_width = params['pulse width'].magnitude
		echo = params['echo'].magnitude
		varwidth=200e-9
		for i in range(60):
			self.dataset.clear()
			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'
			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()

			## build pulse sequence for AWG channel 1
			chn1pulse = Arbseq_Class('chn1pulse', timestep)
			chn1pulse.delays = [0]
			chn1pulse.heights = [1]
			chn1pulse.widths = [pulse_width]
			chn1pulse.totaltime = pulse_width
			chn1pulse.nrepeats = 0
			chn1pulse.repeatstring = 'once'
			chn1pulse.markerstring = 'highAtStartGoLow'
			chn1pulse.markerloc = 0
			chn1pulsewidth = pulse_width
			chn1pulse.create_sequence()

			chn1dc = Arbseq_Class('chn1dc', timestep)
			chn1dc.delays = [0]
			chn1dc.heights = [0]
			chn1dc.widths = [repeat_unit]
			chn1dc.totaltime = repeat_unit
			chn1dc.repeatstring = 'repeat'
			chn1dc.markerstring = 'lowAtStart'
			chn1dc.markerloc = 0
			chn1dcrepeats = int((tau.magnitude-0.5*pulse_width-0.5*varwidth)/repeat_unit)
			chn1dc.nrepeats = chn1dcrepeats
			chn1dcwidth = repeat_unit*chn1dcrepeats
			print(tau.magnitude, pulse_width, chn1dcrepeats)
			chn1dc.create_sequence()
		
			chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
			chn1pulse2.delays = [0]
			chn1pulse2.heights = [1]
			chn1pulse2.widths = [varwidth]
			chn1pulse2.totaltime = varwidth
			chn1pulse2width = varwidth
			chn1pulse2.nrepeats = 0
			chn1pulse2.repeatstring = 'once'
			chn1pulse2.markerstring = 'lowAtStart'
			chn1pulse2.markerloc = 0
			chn1pulse2.create_sequence()
		
			chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
			chn1pulse3.delays = [0]
			chn1pulse3.heights = [0]
			chn1pulse3.widths = [repeat_unit]
			chn1pulse3.totaltime = repeat_unit 
			chn1pulse3width = echo
			chn1pulse3.nrepeats = echo/repeat_unit
			chn1pulse3.repeatstring = 'repeat'
			chn1pulse3.markerstring = 'lowAtStart'
			chn1pulse3.markerloc = 0
			chn1pulse3.create_sequence()
		
			chn1dc2 = Arbseq_Class('chn1dc2', timestep)
			chn1dc2.delays = [0]
			chn1dc2.heights = [0]
			chn1dc2.widths = [repeat_unit]
			chn1dc2.totaltime = repeat_unit
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2repeats = int((period-chn1pulsewidth-chn1dcwidth-chn1pulse2width-chn1pulse3width)/repeat_unit)
			chn1dc2.nrepeats = chn1dc2repeats
			chn1dc2.markerloc = 0
			chn1dc2.create_sequence()

			chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
			chn2pulse1.delays = [0]
			chn2pulse1.heights = [1]
			chn2pulse1.widths = [pulse_width]
			chn2pulse1.totaltime = pulse_width
			chn2pulse1width = pulse_width
			chn2pulse1.nrepeats = 0
			chn2pulse1.repeatstring = 'once'
			chn2pulse1.markerstring = 'lowAtStart'
			chn2pulse1.markerloc = 0
			chn2pulse1.create_sequence()

			chn2dc1 = Arbseq_Class('chn2dc1', timestep)
			chn2dc1.delays = [0]
			chn2dc1.heights = [1]
			chn2dc1.widths = [repeat_unit]
			chn2dc1.totaltime = repeat_unit
			chn2dc1.repeatstring = 'repeat'
			chn2dc1.markerstring = 'lowAtStart'
			chn2dc1.markerloc = 0
			chn2dc1repeats = int((tau.magnitude-1.5*pulse_width)/repeat_unit)
			chn2dc1.nrepeats = chn2dc1repeats
			chn2dc1width = repeat_unit*chn2dc1repeats
			chn2dc1.create_sequence()
	
			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			chn2pulse2.delays = [0]
			chn2pulse2.heights = [1]
			chn2pulse2.widths = [pulse_width*2]
			chn2pulse2.totaltime = pulse_width*2
			chn2pulse2width = pulse_width*2
			chn2pulse2.nrepeats = 0
			chn2pulse2.repeatstring = 'once'
			chn2pulse2.markerstring = 'lowAtStart'
			chn2pulse2.markerloc = 0
			chn2pulse2.create_sequence()

			chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
			chn2pulse3.delays = [0]
			chn2pulse3.heights = [1]
			chn2pulse3.widths = [repeat_unit]
			chn2pulse3.totaltime = repeat_unit
			chn2pulse3width = echo
			chn2pulse3.nrepeats = echo/repeat_unit
			chn2pulse3.repeatstring = 'repeat'
			chn2pulse3.markerstring = 'lowAtStart'
			chn2pulse3.markerloc = 0
			chn2pulse3.create_sequence()

			chn2dc2 = Arbseq_Class('chn2dc2', timestep)
			chn2dc2.delays = [0]
			chn2dc2.heights = [0]
			chn2dc2.widths = [repeat_unit]
			chn2dc2.totaltime = repeat_unit
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2repeats = int((period-chn2pulse1width-chn2dc1width-chn2pulse2width-chn2pulse3width)/repeat_unit)
			chn2dc2.nrepeats = chn2dc2repeats
			chn2dc2.markerloc = 0
			print(repeat_unit*chn2dc2.nrepeats)
			chn2dc2.create_sequence()


			self.fungen.send_arb(chn1pulse, 1)
			self.fungen.send_arb(chn1dc, 1)
			self.fungen.send_arb(chn1pulse2, 1)
			self.fungen.send_arb(chn1pulse3, 1)
			self.fungen.send_arb(chn1dc2, 1)
			self.fungen.send_arb(chn2pulse1, 2)
			self.fungen.send_arb(chn2dc1, 2)
			self.fungen.send_arb(chn2pulse2, 2)
			self.fungen.send_arb(chn2pulse3, 2)
			self.fungen.send_arb(chn2dc2, 2)
			seq = [chn1pulse, chn1dc, chn1pulse2, chn1pulse3, chn1dc2]
			seq2 = [chn2pulse1, chn2dc1, chn2pulse2, chn2pulse3, chn2dc2]
			
			self.fungen.create_arbseq('twoPulse', seq, 1)
			self.fungen.create_arbseq('local', seq2, 2)

			self.fungen.wait()
			self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
			self.fungen.voltage[2] = 1.0+0.000000000001*i
			
			print(self.fungen.voltage[1], self.fungen.voltage[2])
			self.fungen.sync()
			self.fungen.output[1] = 'ON'
			self.fungen.output[2] = 'ON'
			self.osc.set_time(tau.magnitude*2+500e-9)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			self.saveData(x,y,i)
			time.sleep(2)
			
			varwidth+=100e-9

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 500e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('start tau', {'type': float, 'default': 3e-6, 'units':'s'}),
		('stop tau', {'type': float, 'default': 10e-6, 'units':'s'}),
		('step tau', {'type': float, 'default': 1e-6, 'units':'s'}),
		('echo', {'type': float, 'default': 100e-6, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@startpulse.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

	@startpulse.finalizer
	def finalize(self):
		#self.fungen.output[1] = 'OFF'
		#self.fungen.output[2] = 'OFF'
		print('Two Pulse measurements complete.')
		return