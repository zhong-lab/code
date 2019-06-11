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
from lantz.drivers.stanford.srs900 import SRS900

class TwoPulse(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'srs': SRS900
	}

	@Task()
	def startpulse(self, timestep=1e-9):
		params = self.pulse_parameters.widget.get()
		tau=params['start tau']
		for i in range(int((params['stop tau']-params['start tau'])/params['step tau'])+1):
			self.dataset.clear()
			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'
			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()

			chn1pulse = Arbseq_Class('chn1pulse', timestep)
			chn1pulse.delays = [0]
			chn1pulse.heights = [0]
			chn1pulse.widths = [params['pulse width'].magnitude]
			chn1pulse.totaltime = params['pulse width'].magnitude
			chn1pulse.nrepeats = 0
			chn1pulse.repeatstring = 'once'
			chn1pulse.markerstring = 'highAtStartGoLow'
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
			chn1dcrepeats = int((tau.magnitude-params['pulse width'].magnitude)/(params['repeat unit'].magnitude))
			chn1dc.nrepeats = chn1dcrepeats
			chn1dcwidth = (params['repeat unit'].magnitude)*chn1dcrepeats
			print(tau.magnitude, params['pulse width'].magnitude, chn1dcrepeats)
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

			chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
			chn1pulse3.delays = [0]
			chn1pulse3.heights = [0]
			chn1pulse3.widths = [params['repeat unit'].magnitude]
			chn1pulse3.totaltime = params['repeat unit'].magnitude 
			chn1pulse3width = 400e-9 
			chn1pulse3.nrepeats = 400e-9/params['repeat unit'].magnitude
			chn1pulse3.repeatstring = 'repeat'
			chn1pulse3.markerstring = 'lowAtStart'
			chn1pulse3.markerloc = 0
			chn1pulse3.create_sequence()

			chn1dc2 = Arbseq_Class('chn1dc2', timestep)
			chn1dc2.delays = [0]
			chn1dc2.heights = [0]
			chn1dc2.widths = [params['repeat unit'].magnitude]
			chn1dc2.totaltime = params['repeat unit'].magnitude
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2repeats = int((params['period'].magnitude-tau.magnitude-params['pulse width'].magnitude-chn1pulse3width)/(params['repeat unit'].magnitude))
			chn1dc2.nrepeats = chn1dc2repeats
			chn1dc2.markerloc = 0
			print((chn1dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
			chn1dc2.create_sequence()

			chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
			chn2pulse1.delays = [0]
			chn2pulse1.heights = [0]
			# chn2pulse1width = pulsewidth+pulse2width+dcwidth
			chn2pulse1.widths=[params['pulse width'].magnitude]
			chn2pulse1.totaltime=params['pulse width'].magnitude
			chn2pulse1.nrepeats = 0
			chn2pulse1.repeatstring = 'once'
			chn2pulse1.markerstring = 'highAtStartGoLow'
			chn2pulse1.markerloc = 0
			chn2pulse1.create_sequence()

			chn2dc1 = Arbseq_Class('chn2dc1', timestep)
			chn2dc1.delays = [0]
			chn2dc1.heights = [1]
			chn2dc1.widths = [params['repeat unit'].magnitude]
			chn2dc1.totaltime = params['repeat unit'].magnitude
			chn2dc1.repeatstring = 'repeat'
			chn2dc1.markerstring = 'lowAtStart'
			chn2dc1.markerloc = 0
			chn2dc1repeats = int((tau.magnitude-params['pulse width'].magnitude)/(params['repeat unit'].magnitude))
			chn2dc1.nrepeats = chn2dc1repeats
			chn2dc1width = (params['repeat unit'].magnitude)*chn2dc1repeats
			chn2dc1.create_sequence()
	
			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			chn2pulse2.delays = [0]
			chn2pulse2.heights = [1]
			chn2pulse2.widths = [params['pulse width'].magnitude]
			chn2pulse2.totaltime = params['pulse width'].magnitude 
			chn2pulse2width = params['pulse width'].magnitude
			chn2pulse2.nrepeats = 0
			chn2pulse2.repeatstring = 'once'
			chn2pulse2.markerstring = 'lowAtStart'
			chn2pulse2.markerloc = 0
			chn2pulse2.create_sequence()

			chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
			chn2pulse3.delays = [0]
			chn2pulse3.heights = [0]
			chn2pulse3.widths = [params['repeat unit'].magnitude]
			chn2pulse3.totaltime = params['repeat unit'].magnitude 
			chn2pulse3width = 400e-9 
			chn2pulse3.nrepeats = 400e-9/params['repeat unit'].magnitude
			chn2pulse3.repeatstring = 'repeat'
			chn2pulse3.markerstring = 'lowAtStart'
			chn2pulse3.markerloc = 0
			chn2pulse3.create_sequence()

			chn2dc2 = Arbseq_Class('chn2dc2', timestep)
			chn2dc2.delays = [0]
			chn2dc2.heights = [0]
			chn2dc2.widths = [params['repeat unit'].magnitude]
			chn2dc2.totaltime = params['repeat unit'].magnitude
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2repeats = int((params['period'].magnitude-tau.magnitude-params['pulse width'].magnitude-chn2pulse3width)/(params['repeat unit'].magnitude))
			chn2dc2.nrepeats = chn2dc2repeats
			chn2dc2.markerloc = 0
			print((chn2dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
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
			self.fungen.create_arbseq('shutter', seq2, 2)
			self.fungen.wait()
			self.fungen.voltage[1] = 3.3+0.000000000001*i
			self.fungen.voltage[2]=0.6
			self.fungen.offset[2] = 3.0
			
			print(self.fungen.voltage[1], self.fungen.voltage[2])
			self.fungen.output[1] = 'ON'
			self.fungen.output[2] = 'ON'
			self.fungen.trigger_delay(1,400e-9)
			self.fungen.sync()

			time.sleep(10000)

		# pulse = Arbseq_Class('pulse', timestep)
		# pulse.delays = [0]
		# pulse.heights = [1]
		# pulse.widths = [params['pulse width'].magnitude/2]
		# pulsewidth = params['pulse width'].magnitude/2
		# pulse.totaltime = params['pulse width'].magnitude/2
		# pulse.nrepeats = 0
		# pulse.repeatstring = 'once'
		# pulse.markerstring = 'highAtStartGoLow'
		# pulse.markerloc = 0
		# pulse.create_sequence()

		# dc = Arbseq_Class('dc', timestep)
		# dc.delays = [0]
		# dc.heights = [0]
		# dc.widths = [params['pulse width'].magnitude/4]
		# dc.totaltime = params['pulse width'].magnitude/4
		# dc.repeatstring = 'repeat'
		# dc.markerstring = 'lowAtStart'
		# dc.markerloc = 0
		# dcrepeats = int((tau.magnitude-(3/4)*params['pulse width'].magnitude)/(params['pulse width'].magnitude/4))
		# dc.nrepeats = dcrepeats
		# dcwidth = (params['pulse width'].magnitude/4)*dcrepeats
		# print(tau.magnitude, 0.75*params['pulse width'].magnitude, dcrepeats)
		# dc.create_sequence()

		# pulse2 = Arbseq_Class('pulse2', timestep)
		# pulse2.delays = [0]
		# pulse2.heights = [1]
		# pulse2.widths = [params['pulse width'].magnitude]
		# pulse2width = params['pulse width'].magnitude
		# pulse2.totaltime = params['pulse width'].magnitude
		# pulse2.nrepeats = 0
		# pulse2.repeatstring = 'once'
		# pulse2.markerstring = 'lowAtStart'
		# pulse2.markerloc = 0
		# pulse2.create_sequence()

		# dc2 = Arbseq_Class('dc2', timestep)
		# dc2.delays = [0]
		# dc2.heights = [0]
		# dc2.widths = [params['pulse width'].magnitude/4]
		# dc2.totaltime = params['pulse width'].magnitude/4
		# dc2.repeatstring = 'repeat'
		# dc2.markerstring = 'lowAtStart'
		# dc2repeats = int((params['period'].magnitude-tau.magnitude-(3/4)*params['pulse width'].magnitude)/(params['pulse width'].magnitude/4))
		# dc2.nrepeats = dc2repeats
		# dc2.markerloc = 0
		# print((dc2repeats*params['pulse width'].magnitude/4) + tau.magnitude + 0.75*params['pulse width'].magnitude)
		# dc2.create_sequence()

		# pulse3 = Arbseq_Class('pulse3', timestep)
		# pulse3.delays = [0]
		# pulse3.heights = [1]
		# pulse3width = pulsewidth+pulse2width+dcwidth
		# pulse3.widths=[pulse3width]
		# pulse3.totaltime=pulse3width
		# pulse3.nrepeats = 0
		# pulse3.repeatstring = 'once'
		# pulse3.markerstring = 'highAtStartGoLow'
		# pulse3.markerloc = 0
		# pulse3.create_sequence()

		# dc3 = Arbseq_Class('dc3', timestep)
		# dc3.delays = [0]
		# dc3.heights = [-1]
		# dc3.widths = [params['pulse width'].magnitude/4]
		# dc3.totaltime = params['pulse width'].magnitude/4
		# dc3.repeatstring = 'repeat'
		# dc3.markerstring = 'lowAtStart'
		# dc3.markerloc = 0
		# dc3repeats = int((params['period'].magnitude-pulse3width)/(params['pulse width'].magnitude/4))
		# dc3.nrepeats = dc3repeats
		# print((dc3repeats*params['pulse width'].magnitude/4) + pulse3width)
		# dc3.create_sequence()

		# self.fungen.send_arb(pulse, 1)
		# self.fungen.send_arb(pulse2, 1)
		# self.fungen.send_arb(dc, 1)
		# self.fungen.send_arb(dc2, 1)
		# self.fungen.send_arb(pulse3, 2)
		# self.fungen.send_arb(dc3, 2)

		# seq = [pulse, dc, pulse2,dc2]
		# seq2 = [pulse3, dc3]

		# self.fungen.create_arbseq('twoPulse', seq, 1)
		# self.fungen.create_arbseq('shutter', seq2, 2)
		# self.fungen.wait()
		# self.fungen.voltage[1] = params['pulse height'].magnitude
		# self.fungen.voltage[2] = 3.55*2
			
		# print(self.fungen.voltage[1])
		# self.fungen.output[1] = 'ON'
		# self.fungen.output[2] = 'ON'

		# while True:
		# 	self.fungen.sync_arbs(2)
		# 	time.sleep(0.5)


		#self.fungen.output[1] = 'OFF'


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

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 500e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.05, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('start tau', {'type': float, 'default': 2e-6, 'units':'s'}),
		('stop tau', {'type': float, 'default': 10e-6, 'units':'s'}),
		('step tau', {'type': float, 'default': 1e-6, 'units':'s'}),
		('srs bias', {'type': float, 'default': 0.7, 'units':'V'})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of Passes', {'type': int, 'default': 100}),
		('File Name', {'type': str})
		]
		w = ParamWidget(params)
		return w