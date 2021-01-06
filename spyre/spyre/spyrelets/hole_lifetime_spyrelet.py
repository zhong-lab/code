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

class Holeburing(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS5104
	}

	def saveData(self,x,y,index,ind):
		out_name = "D:\\Data\\1.6.2021_YSO_holeburning\\1T\\195110\\lifetime"
		index=str(round(index,8))
		ind='.'+str(ind)
		np.savez(os.path.join(out_name,str(index+ind)),x,y)
		print('Data stored under File Name: ' + str(index) + '.'+str(ind))


	@Task()
	def startpulse(self,timestep=1e-8):
		params = self.pulse_parameters.widget.get()
		burning_switch1 = params['burning_switch1']
		burning_switch2 = params['burning_switch2']
		detection_switch1 = params['detection_switch1']
		detection_switch2 = params['detection_switch2']
		detect_time = params['detection time'].magnitude
		buffer_time = params['buffer time'].magnitude
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

		burn_width = params['burn_width'].magnitude
		wait_time = params['wait_time'].magnitude
		burn_rep=int(burn_width/1e-5)
		buffer_rep=int(buffer_time/1e-5)
		detect_rep=int(detect_time/1e-5)
		#import pdb; pdb.set_trace()

		## build pulse sequence for AWG channel 1
		chn1pulse = Arbseq_Class('chn1pulse', timestep)
		chn1pulse.delays = [0]
		chn1pulse.heights = [burning_switch1]
		chn1pulse.widths = [1e-5]
		chn1pulse.totaltime = 1e-5
		chn1pulse.nrepeats = burn_rep
		chn1pulse.repeatstring = 'repeat'
		chn1pulse.markerstring = 'lowAtStart'
		chn1pulse.markerloc = 0
		chn1pulse.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [wait_time]
		chn1dc.totaltime = wait_time
		chn1dc.repeatstring = 'once'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dc.nrepeats = 0
		chn1dc.create_sequence()	

		chn1dc3 = Arbseq_Class('chn1dc3', timestep)
		chn1dc3.delays = [0]
		chn1dc3.heights = [detection_switch1]
		chn1dc3.widths = [1e-5]
		chn1dc3.totaltime = 1e-5
		chn1dc3.nrepeats = detect_rep
		chn1dc3.repeatstring = 'repeat'
		chn1dc3.markerstring = 'lowAtStart'
		chn1dc3.markerloc = 0
		chn1dc3.create_sequence()

		chn1pulse4 = Arbseq_Class('chn1pulse4', timestep)
		chn1pulse4.delays = [0]
		chn1pulse4.heights = [detection_switch1]
		chn1pulse4.widths = [1e-5]
		chn1pulse4.totaltime = 1e-5
		chn1pulse4.nrepeats = 0
		chn1pulse4.repeatstring = 'once'
		chn1pulse4.markerstring = 'highAtStartGoLow'
		chn1pulse4.markerloc = 0
		chn1pulse4.create_sequence()

		chn1dc4 = Arbseq_Class('chn1dc4', timestep)
		chn1dc4.delays = [0]
		chn1dc4.heights = [0]
		chn1dc4.widths = [1e-5]
		chn1dc4.totaltime = 1e-5
		chn1dc4.nrepeats = buffer_rep
		chn1dc4.repeatstring = 'repeat'
		chn1dc4.markerstring = 'lowAtStart'
		chn1dc4.markerloc = 0
		chn1dc4.create_sequence()

		chn2pulse = Arbseq_Class('chn2pulse', timestep)
		chn2pulse.delays = [0]
		chn2pulse.heights = [burning_switch2]
		chn2pulse.widths = [1e-5]
		chn2pulse.totaltime = 1e-5
		chn2pulse.nrepeats = burn_rep
		chn2pulse.repeatstring = 'repeat'
		chn2pulse.markerstring = 'lowAtStart'
		chn2pulse.markerloc = 0
		chn2pulse.create_sequence()

		chn2dc = Arbseq_Class('chn2dc', timestep)
		chn2dc.delays = [0]
		chn2dc.heights = [0]
		chn2dc.widths = [wait_time]
		chn2dc.totaltime = wait_time
		chn2dc.repeatstring = 'once'
		chn2dc.markerstring = 'lowAtStart'
		chn2dc.markerloc = 0
		chn2dc.nrepeats = 0
		chn2dc.create_sequence()

		chn2dc3 = Arbseq_Class('chn2dc3', timestep)
		chn2dc3.delays = [0]
		chn2dc3.heights = [detection_switch2]
		chn2dc3.widths = [1e-5]
		chn2dc3.totaltime = 1e-5
		chn2dc3.nrepeats = detect_rep
		chn2dc3.repeatstring = 'repeat'
		chn2dc3.markerstring = 'lowAtStart'
		chn2dc3.markerloc = 0
		chn2dc3.create_sequence()

		chn2pulse4 = Arbseq_Class('chn2pulse4', timestep)
		chn2pulse4.delays = [0]
		chn2pulse4.heights = [detection_switch2]
		chn2pulse4.widths = [1e-5]
		chn2pulse4.totaltime = 1e-5
		chn2pulse4.nrepeats = 0
		chn2pulse4.repeatstring = 'once'
		chn2pulse4.markerstring = 'highAtStartGoLow'
		chn2pulse4.markerloc = 0
		chn2pulse4.create_sequence()

		chn2dc4 = Arbseq_Class('chn2dc4', timestep)
		chn2dc4.delays = [0]
		chn2dc4.heights = [0]
		chn2dc4.widths = [1e-5]
		chn2dc4.totaltime = 1e-5
		chn2dc4.nrepeats = buffer_rep
		chn2dc4.repeatstring = 'repeat'
		chn2dc4.markerstring = 'lowAtStart'
		chn2dc4.markerloc = 0
		chn2dc4.create_sequence()

		self.fungen.send_arb(chn1pulse, 1)
		self.fungen.send_arb(chn1dc, 1)
		self.fungen.send_arb(chn1dc3, 1)
		self.fungen.send_arb(chn1pulse4, 1)
		self.fungen.send_arb(chn1dc4, 1)

		self.fungen.send_arb(chn2pulse, 2)
		self.fungen.send_arb(chn2dc, 2)
		self.fungen.send_arb(chn2dc3, 2)
		self.fungen.send_arb(chn2pulse4, 2)
		self.fungen.send_arb(chn2dc4, 2)

		seq = [chn1pulse, chn1dc, chn1dc4, chn1pulse4, chn1dc3, chn1dc4]
		seq2 = [chn2pulse, chn2dc, chn2dc4, chn2pulse4, chn2dc3, chn2dc4]
		
		self.fungen.create_arbseq('twoPulse', seq, 1)
		self.fungen.create_arbseq('twoPulse2', seq2, 2)

		self.fungen.wait()
		self.fungen.voltage[1] = 1.75
		self.fungen.voltage[2] = 1.75
		self.fungen.sync()
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'

		print("start hole burning for 60s")

		time.sleep(30)
		
		self.osc.datasource(3)

		self.fungen.output[2] = 'OFF'
		print("hole burning stop")
		start=time.time()

		for j in range(50):
			t=time.time()-start
			x,y=self.osc.curv()
			x = np.array(x)
			y = np.array(y)
			self.saveData(x,y,t,j)
			print(time.time()-start)




		# self.fungen.output[1] = 'ON'
		# self.fungen.output[2] = 'ON'
		#self.fungen.trigger_delay(2,burn_width+wait_time+2*pi_width+2*tau)
		# for _ in range(10):
		# 	self.fungen.trigger()
		# 	self.fungen.wait()
		# 	print("triggered")
		# 	time.sleep(1)


		#self.fungen.wait()


	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
		('detection time', {'type': float, 'default': 100e-3, 'units':'s'}),
		('burning_switch1', {'type': int, 'default': 0}),
		('burning_switch2', {'type': int, 'default': 1}),
		('detection_switch1', {'type': int, 'default': 1}),
		('detection_switch2', {'type': int, 'default': 0}),
		('burn_width', {'type': float, 'default': 1e-3, 'units':'s'}),
		('wait_time', {'type': float, 'default': 10e-6, 'units':'s'}),
		('buffer time', {'type': float, 'default': 100e-3, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	# @Element(name='Histogram')
	# def averaged(self):
	# 	p = LinePlotWidget()
	# 	p.plot('Ch4')
	# 	p.plot('Ch3')
	# 	return p

	@startpulse.initializer
	def initialize(self):
		print

	@startpulse.finalizer
	def finalize(self):
		# self.fungen.output[1] = 'OFF'
		# self.fungen.output[2] = 'OFF'
		# self.fungen.clear_mem(1)
		# self.fungen.clear_mem(2)
		print('Two Pulse measurements complete.')
		return