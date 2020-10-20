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
from lantz.drivers.tektronix.tds5104 import TDS5104

class SpinEcho(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS5104
	}

	@Task()
	def startpulse(self,timestep=10e-9):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

		burn_width = 100e-3
		wait_time = 10e-6
		pi_width = 2e-6
		tau = 10e-6

		## build pulse sequence for AWG channel 1
		chn1pulse = Arbseq_Class('chn1pulse', timestep)
		chn1pulse.delays = [0]
		chn1pulse.heights = [1]
		chn1pulse.widths = [1e-4]
		chn1pulse.totaltime = 1e-4
		chn1pulse.nrepeats = 1e3
		chn1pulse.repeatstring = 'repeat'
		chn1pulse.markerstring = 'lowAtStart'
		chn1pulse.markerloc = 0
		chn1pulse.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [1]
		chn1dc.widths = [wait_time]
		chn1dc.totaltime = wait_time
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dc.nrepeats = 100
		chn1dc.create_sequence()

		chn1dc2 = Arbseq_Class('chn1dc2', timestep)
		chn1dc2.delays = [0]
		chn1dc2.heights = [0]
		chn1dc2.widths = [wait_time]
		chn1dc2.totaltime = wait_time
		chn1dc2.repeatstring = 'once'
		chn1dc2.markerstring = 'lowAtStart'
		chn1dc2.markerloc = 0
		chn1dc2.nrepeats = 0
		chn1dc2.create_sequence()
	
		chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
		chn1pulse2.delays = [0]
		chn1pulse2.heights = [1]
		chn1pulse2.widths = [pi_width/2]
		chn1pulse2.totaltime = pi_width/2
		chn1pulse2.nrepeats = 0
		chn1pulse2.repeatstring = 'once'
		chn1pulse2.markerstring = 'highAtStartGoLow'
		chn1pulse2.markerloc = 0
		chn1pulse2.create_sequence()

		chn1dc3 = Arbseq_Class('chn1dc3', timestep)
		chn1dc3.delays = [0]
		chn1dc3.heights = [0]
		chn1dc3.widths = [tau]
		chn1dc3.totaltime = tau
		chn1dc3.repeatstring = 'once'
		chn1dc3.markerstring = 'lowAtStart'
		chn1dc3.nrepeats = 0
		chn1dc3.markerloc = 0
		chn1dc3.create_sequence()
	
		chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
		chn1pulse3.delays = [0]
		chn1pulse3.heights = [1]
		chn1pulse3.widths = [pi_width]
		chn1pulse3.totaltime = pi_width 
		chn1pulse3.nrepeats = 0
		chn1pulse3.repeatstring = 'once'
		chn1pulse3.markerstring = 'lowAtStart'
		chn1pulse3.markerloc = 0
		chn1pulse3.create_sequence()

		chn1dc4 = Arbseq_Class('chn1dc4', timestep)
		chn1dc4.delays = [0]
		chn1dc4.heights = [0]
		chn1dc4.widths = [tau/2]
		chn1dc4.totaltime = tau/2
		chn1dc4.repeatstring = 'once'
		chn1dc4.markerstring = 'lowAtStart'
		chn1dc4.nrepeats = 0
		chn1dc4.markerloc = 0
		chn1dc4.create_sequence()

		chn1dc5 = Arbseq_Class('chn1dc5', timestep)
		chn1dc5.delays = [0]
		chn1dc5.heights = [0]
		chn1dc5.widths = [tau/2-pi_width]
		chn1dc5.totaltime = tau/2-pi_width
		chn1dc5.repeatstring = 'once'
		chn1dc5.markerstring = 'lowAtStart'
		chn1dc5.nrepeats = 0
		chn1dc5.markerloc = 0
		chn1dc5.create_sequence()

		chn1pulse4 = Arbseq_Class('chn1pulse4', timestep)
		chn1pulse4.delays = [0]
		chn1pulse4.heights = [1]
		chn1pulse4.widths = [pi_width*4]
		chn1pulse4.totaltime = pi_width*4
		chn1pulse4.nrepeats = 0
		chn1pulse4.repeatstring = 'once'
		chn1pulse4.markerstring = 'lowAtStart'
		chn1pulse4.markerloc = 0
		chn1pulse4.create_sequence()

		chn1dc6 = Arbseq_Class('chn1dc6', timestep)
		chn1dc6.delays = [0]
		chn1dc6.heights = [0]
		chn1dc6.widths = [1e-4]
		chn1dc6.totaltime = 1e-4
		chn1dc6.nrepeats = 1e3
		chn1dc6.repeatstring = 'repeat'
		chn1dc6.markerstring = 'lowAtStart'
		chn1dc6.markerloc = 0
		chn1dc6.create_sequence()

		chn2pulse = Arbseq_Class('chn2pulse', timestep)
		chn2pulse.delays = [0]
		chn2pulse.heights = [1]
		chn2pulse.widths = [1e-4]
		chn2pulse.totaltime = 1e-4
		chn2pulse.nrepeats = 1e3
		chn2pulse.repeatstring = 'repeat'
		chn2pulse.markerstring = 'lowAtStart'
		chn2pulse.markerloc = 0
		chn2pulse.create_sequence()

		chn2dc = Arbseq_Class('chn2dc', timestep)
		chn2dc.delays = [0]
		chn2dc.heights = [0]
		chn2dc.widths = [wait_time]
		chn2dc.totaltime = wait_time
		chn2dc.repeatstring = 'repeat'
		chn2dc.markerstring = 'lowAtStart'
		chn2dc.markerloc = 0
		chn2dc.nrepeats = 100
		chn2dc.create_sequence()

		chn2dc2 = Arbseq_Class('chn2dc2', timestep)
		chn2dc2.delays = [0]
		chn2dc2.heights = [0]
		chn2dc2.widths = [wait_time]
		chn2dc2.totaltime = wait_time
		chn2dc2.repeatstring = 'once'
		chn2dc2.markerstring = 'lowAtStart'
		chn2dc2.markerloc = 0
		chn2dc2.nrepeats = 0
		chn2dc2.create_sequence()
	
		chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
		chn2pulse2.delays = [0]
		chn2pulse2.heights = [1]
		chn2pulse2.widths = [pi_width/2]
		chn2pulse2.totaltime = pi_width/2
		chn2pulse2.nrepeats = 0
		chn2pulse2.repeatstring = 'once'
		chn2pulse2.markerstring = 'highAtStartGoLow'
		chn2pulse2.markerloc = 0
		chn2pulse2.create_sequence()

		chn2dc3 = Arbseq_Class('chn2dc3', timestep)
		chn2dc3.delays = [0]
		chn2dc3.heights = [0]
		chn2dc3.widths = [tau]
		chn2dc3.totaltime = tau
		chn2dc3.repeatstring = 'once'
		chn2dc3.markerstring = 'lowAtStart'
		chn2dc3.nrepeats = 0
		chn2dc3.markerloc = 0
		chn2dc3.create_sequence()
	
		chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
		chn2pulse3.delays = [0]
		chn2pulse3.heights = [1]
		chn2pulse3.widths = [pi_width]
		chn2pulse3.totaltime = pi_width 
		chn2pulse3.nrepeats = 0
		chn2pulse3.repeatstring = 'once'
		chn2pulse3.markerstring = 'lowAtStart'
		chn2pulse3.markerloc = 0
		chn2pulse3.create_sequence()

		chn2dc4 = Arbseq_Class('chn2dc4', timestep)
		chn2dc4.delays = [0]
		chn2dc4.heights = [0]
		chn2dc4.widths = [tau/2]
		chn2dc4.totaltime = tau/2
		chn2dc4.repeatstring = 'once'
		chn2dc4.markerstring = 'lowAtStart'
		chn2dc4.nrepeats = 0
		chn2dc4.markerloc = 0
		chn2dc4.create_sequence()

		chn2dc5 = Arbseq_Class('chn2dc5', timestep)
		chn2dc5.delays = [0]
		chn2dc5.heights = [0]
		chn2dc5.widths = [tau/2-pi_width]
		chn2dc5.totaltime = tau/2-pi_width
		chn2dc5.repeatstring = 'once'
		chn2dc5.markerstring = 'lowAtStart'
		chn2dc5.nrepeats = 0
		chn2dc5.markerloc = 0
		chn2dc5.create_sequence()

		chn2pulse4 = Arbseq_Class('chn2pulse4', timestep)
		chn2pulse4.delays = [0]
		chn2pulse4.heights = [0]
		chn2pulse4.widths = [pi_width*4]
		chn2pulse4.totaltime = pi_width*4
		chn2pulse4.nrepeats = 0
		chn2pulse4.repeatstring = 'once'
		chn2pulse4.markerstring = 'lowAtStart'
		chn2pulse4.markerloc = 0
		chn2pulse4.create_sequence()

		chn2dc6 = Arbseq_Class('chn2dc6', timestep)
		chn2dc6.delays = [0]
		chn2dc6.heights = [0]
		chn2dc6.widths = [1e-4]
		chn2dc6.totaltime = 1e-4
		chn2dc6.nrepeats = 1e3
		chn2dc6.repeatstring = 'repeat'
		chn2dc6.markerstring = 'lowAtStart'
		chn2dc6.markerloc = 0
		chn2dc6.create_sequence()

		self.fungen.send_arb(chn1pulse, 1)
		self.fungen.send_arb(chn1dc, 1)
		self.fungen.send_arb(chn1dc2, 1)
		self.fungen.send_arb(chn1pulse2, 1)
		self.fungen.send_arb(chn1dc3, 1)
		self.fungen.send_arb(chn1pulse3, 1)
		self.fungen.send_arb(chn1dc4, 1)
		self.fungen.send_arb(chn1dc5, 1)
		self.fungen.send_arb(chn1pulse4, 1)
		self.fungen.send_arb(chn1dc6, 1)

		self.fungen.send_arb(chn2pulse, 2)
		self.fungen.send_arb(chn2dc, 2)
		self.fungen.send_arb(chn2dc2, 2)
		self.fungen.send_arb(chn2pulse2, 2)
		self.fungen.send_arb(chn2dc3, 2)
		self.fungen.send_arb(chn2pulse3, 2)
		self.fungen.send_arb(chn2dc4, 2)
		self.fungen.send_arb(chn2dc5, 2)
		self.fungen.send_arb(chn2pulse4, 2)
		self.fungen.send_arb(chn2dc6, 2)

		seq = [chn1pulse,chn1dc,chn1dc2,chn1pulse2,chn1dc3,chn1pulse3,chn1dc4,chn1dc5,chn1pulse4,chn1dc6]
		seq2 = [chn2pulse,chn2dc,chn2dc2,chn2pulse2,chn2dc3,chn2pulse3,chn2dc4,chn2dc5,chn2pulse4,chn2dc6]
		
		self.fungen.create_arbseq('twoPulse', seq, 1)
		self.fungen.create_arbseq('twoPulse2', seq2, 2)

		self.fungen.wait()
		self.fungen.voltage[1] = 3.0
		self.fungen.voltage[2] = 3.0
		self.fungen.sync()

	@startpulse.initializer
	def initialize(self):
		print

	@startpulse.finalizer
	def finalize(self):
		#self.fungen.output[1] = 'OFF'
		#self.fungen.output[2] = 'OFF'
		print('Two Pulse measurements complete.')
		return