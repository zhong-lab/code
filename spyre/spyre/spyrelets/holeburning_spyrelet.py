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

class HoleBurning(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}
	out_name = "D:\\Data\\6.7.2019\\HoleBurning"
	xs = []
	ys = []
	finalys = []
	# def makeTriangle(self,timestep):
	# 	params = self.parameters.widget.get()
	# 	frequency = params['triangle frequency']
	# 	maxHeight = 0.9
	# 	totalTime = 1/frequency.magnitude
	# 	heights = []
	# 	initHeight = params['AOM Voltage'].magnitude/params['triangle height'].magnitude
	# 	height = initHeight
	# 	while height <= maxHeight:
	# 		heights.append(height)
	# 		height+=(maxHeight-initHeight)*4*timestep/(totalTime)
	# 	while height > maxHeight-initHeight:
	# 		heights.append(height)
	# 		height-=(maxHeight-initHeight)*4*timestep/(totalTime)
	# 	while height <= maxHeight:
	# 		heights.append(height)
	# 		height+=(maxHeight-initHeight)*4*timestep/(totalTime)
	# 	print(heights)
	# 	return heights

	# def pump(self, timestep):
	# 	params = self.parameters.widget.get()
	# 	per=200e-3

	# 	chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
	# 	tri_time = 1000e-6
	# 	offset=0.1
	# 	height = 0.73-offset
	# 	heights = list()
	# 	heights.append(height)
	# 	while height > 0.44-offset:
	# 		height -= 0.28*(4*timestep)/tri_time
	# 		if height <0.44-offset:
	# 			height=0.44-offset
	# 		heights.append(height)
	# 	# while height < 0:
	# 	# 	height += (4*timestep)/tri_time
	# 	# 	if height>0:
	# 	# 		height=0
	# 	# 	heights.append(height)
	# 	while height < 1-offset:
	# 		height += 0.28*(4*timestep)/tri_time
	# 		if height>1-offset:
	# 			height=1-offset
	# 		heights.append(height)
	# 	while height >0.73-offset:
	# 		height-= 0.28*(4*timestep)/tri_time
	# 		if height <0.73-offset:
	# 			height=0.73-offset
	# 		heights.append(height)
	# 	print(heights)
	# 	chn2pulse2.heights = heights
	# 	chn2pulse2.delays = [0] * len(heights)
	# 	chn2pulse2.totaltime = tri_time
	# 	chn2pulse2.widths = [timestep] * len(heights)
	# 	chn2pulse2width=[timestep] * len(heights)
	# 	print('chn2 len(heights) is:' + str(len(heights)))
	# 	chn2pulse2.totaltime = len(heights) * timestep
	# 	print('chn2_shb totaltime is:' + str(chn2pulse2.totaltime))
	# 	chn2pulse2.nrepeats = 3
	# 	print('chn2_shb nrepeats is:' + str(chn2pulse2.nrepeats))
	# 	chn2pulse2.repeatstring = 'repeat'
	# 	chn2pulse2.markerstring = 'lowAtStart'
	# 	chn2pulse2.markerloc = 0
	# 	chn2pulse2.create_sequence()

	# 	# chn2trioff = Arbseq_Class('chn2trioff', timestep)
	# 	# chn2trioff.heights = heights
	# 	# chn2trioff.delays = [0] * len(heights)
	# 	# chn2trioff.totaltime = tri_time
	# 	# chn2trioff.widths = [timestep] * len(heights)
	# 	# chn2trioffwidth=[timestep] * len(heights)
	# 	# print('chn2 len(heights) is:' + str(len(heights)))
	# 	# chn2trioff.totaltime = len(heights) * timestep
	# 	# chn2trioff.nrepeats = int(0.1e-3/tri_time)
	# 	# chn2trioff.repeatstring = 'repeat'
	# 	# chn2trioff.markerstring = 'lowAtStart'
	# 	# chn2trioff.markerloc = 0
	# 	# chn2trioff.create_sequence()

	# 	chn1off1 = Arbseq_Class('chn1off1', timestep)
	# 	chn1off1.delays = [0]
	# 	chn1off1.heights = [0]
	# 	chn1off1.widths = [params['ramp time'].magnitude]
	# 	chn1off1.totaltime = params['ramp time'].magnitude
	# 	chn1off1.nrepeats = 0
	# 	chn1off1.repeatstring = 'once'
	# 	chn1off1.markerstring = 'highAtStartGoLow'
	# 	chn1off1.markerloc = 0
	# 	chn1off1.create_sequence()

	# 	chn1pulse = Arbseq_Class('chn1pulse', timestep)
	# 	chn1pulse.delays = [0]
	# 	chn1pulse.heights = [1]
	# 	chn1pulse.widths = [params['pump width'].magnitude]
	# 	chn1pulse.totaltime = params['pump width'].magnitude
	# 	chn1pulse.nrepeats = 10
	# 	chn1pulse.repeatstring = 'repeat'
	# 	chn1pulse.markerstring = 'lowAtStart'
	# 	chn1pulse.markerloc = 0
	# 	chn1pulse.create_sequence()

	# 	chn1off2 = Arbseq_Class('chn1off2', timestep)
	# 	chn1off2.delays = [0]
	# 	chn1off2.heights = [0]
	# 	chn1off2.widths = [params['ramp time'].magnitude]
	# 	chn1off2.totaltime = params['ramp time'].magnitude
	# 	chn1off2.nrepeats = 0
	# 	chn1off2.repeatstring = 'once'
	# 	chn1off2.markerstring = 'lowAtStart'
	# 	chn1off2.markerloc = 0
	# 	chn1off2.create_sequence()

	# 	# chn1trioff = Arbseq_Class('chn1trioff', timestep)
	# 	# chn1trioff.delays = [0]*len(heights)
	# 	# chn1trioff.heights = [1]*len(heights)
	# 	# chn1trioff.widths = [timestep] * len(heights)
	# 	# chn1trioff.totaltime = tri_time
	# 	# chn1trioff.nrepeats = int(0.1e-3/tri_time)
	# 	# chn1trioff.repeatstring = 'repeat'
	# 	# chn1trioff.markerstring = 'lowAtStart'
	# 	# chn1trioff.markerloc = 0
	# 	# chn1trioff.create_sequence()


	# 	chn1dc = Arbseq_Class('dc1', timestep)
	# 	chn1dc.delays = [0]
	# 	chn1dc.heights = [0]
	# 	chn1dc.widths = [params['wait time unit'].magnitude]
	# 	chn1dc.totaltime = params['wait time unit'].magnitude
	# 	chn1dc.nrepeats = int(params['wait time'].magnitude/params['wait time unit'].magnitude)
	# 	chn1dc.repeatstring = 'repeat'
	# 	chn1dc.markerstring = 'lowAtStart'
	# 	chn1dc.markerloc = 0
	# 	chn1dc.create_sequence()

	# 	chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
	# 	chn1pulse2.delays = [0]*len(heights)
	# 	chn1pulse2.heights = [0.35]*10+ [0.35]*(len(heights)-10)
	# 	chn1pulse2.widths = [timestep] * len(heights)
	# 	chn1pulse2.totaltime = tri_time
	# 	chn1pulse2.nrepeats = 3
	# 	chn1pulse2.repeatstring = 'repeat'
	# 	chn1pulse2.markerstring = 'lowAtStart'
	# 	chn1pulse2.markerloc = 0
	# 	chn1pulse2.create_sequence()

	# 	chn1dc2 = Arbseq_Class('chn1dc2', timestep)
	# 	chn1dc2.delays = [0]
	# 	chn1dc2.heights = [0]
	# 	chn1dc2.widths = [params['pump width'].magnitude]
	# 	chn1dc2.totaltime = params['pump width'].magnitude
	# 	chn1dc2.repeatstring = 'repeat'
	# 	chn1dc2.markerstring = 'lowAtStart'
	# 	chn1dc2.markerloc = 0
	# 	chn1dc2.nrepeats = int((per-tri_time-params['wait time'].magnitude-10*params['pump width'].magnitude)/params['pump width'].magnitude)
	# 	chn1dc2.create_sequence()

	# 	chn2off1 = Arbseq_Class('chn2off1', timestep)
	# 	chn2off1.delays = [0]
	# 	chn2off1.heights = [0]
	# 	chn2off1.widths = [params['ramp time'].magnitude]
	# 	chn2off1.totaltime = params['ramp time'].magnitude
	# 	chn2off1.nrepeats = 0
	# 	chn2off1.repeatstring = 'once'
	# 	chn2off1.markerstring = 'lowAtStart'
	# 	chn2off1.markerloc = 0
	# 	chn2off1.create_sequence()

	# 	chn2pulse = Arbseq_Class('chn2pulse', timestep)
	# 	chn2pulse.delays = [0]
	# 	chn2pulse.heights = [0.7]
	# 	chn2pulse.widths = [params['pump width'].magnitude]
	# 	chn2pulse.totaltime = params['pump width'].magnitude
	# 	chn2pulse.nrepeats = 10
	# 	chn2pulse.repeatstring = 'repeat'
	# 	chn2pulse.markerstring = 'highAtStartGoLow'
	# 	chn2pulse.markerloc = 0
	# 	chn2pulse.create_sequence()

	# 	chn2off2 = Arbseq_Class('chn2off2', timestep)
	# 	chn2off2.delays = [0]
	# 	chn2off2.heights = [0]
	# 	chn2off2.widths = [params['ramp time'].magnitude]
	# 	chn2off2.totaltime = params['ramp time'].magnitude
	# 	chn2off2.nrepeats = 0
	# 	chn2off2.repeatstring = 'once'
	# 	chn2off2.markerstring = 'lowAtStart'
	# 	chn2off2.markerloc = 0
	# 	chn2off2.create_sequence()

	# 	chn2dc = Arbseq_Class('chn2dc', timestep)
	# 	chn2dc.delays = [0]
	# 	chn2dc.heights = [0]
	# 	chn2dc.widths = [params['wait time unit'].magnitude]
	# 	chn2dc.totaltime = params['wait time unit'].magnitude
	# 	chn2dc.nrepeats = int(params['wait time'].magnitude/params['wait time unit'].magnitude)
	# 	chn2dc.repeatstring = 'repeat'
	# 	chn2dc.markerstring = 'lowAtStart'
	# 	chn2dc.markerloc = 0
	# 	chn2dc.create_sequence()


	# 	chn2dc2 = Arbseq_Class('chn2dc2', timestep)
	# 	chn2dc2.delays = [0]
	# 	chn2dc2.heights = [0]
	# 	chn2dc2.widths = [params['pump width'].magnitude]
	# 	chn2dc2.totaltime = params['pump width'].magnitude
	# 	chn2dc2.repeatstring = 'repeat'
	# 	chn2dc2.markerstring = 'lowAtStart'
	# 	chn2dc2.markerloc = 0
	# 	chn2dc2.nrepeats = int((per-tri_time-params['wait time'].magnitude-10*params['pump width'].magnitude)/params['pump width'].magnitude)
	# 	chn2dc2.create_sequence()

	# 	self.fungen.send_arb(chn1off1,1)
	# 	self.fungen.send_arb(chn1pulse, 1)
	# 	self.fungen.send_arb(chn1off2,1)
	# 	self.fungen.send_arb(chn1dc, 1)
	# 	# self.fungen.send_arb(chn1trioff, 1)
	# 	self.fungen.send_arb(chn1pulse2, 1)
	# 	self.fungen.send_arb(chn1dc2, 1)
	# 	self.fungen.send_arb(chn2off1,2)
	# 	self.fungen.send_arb(chn2pulse, 2)
	# 	self.fungen.send_arb(chn2off2,2)
	# 	self.fungen.send_arb(chn2dc, 2)
	# 	self.fungen.send_arb(chn2pulse2, 2)
	# 	self.fungen.send_arb(chn2dc2, 2)
	# 	# self.fungen.send_arb(chn2trioff, 2)


	# 	seq = [chn1off1, chn1pulse,chn1off2, chn1dc, chn1pulse2, chn1dc2]
	# 	seq2 = [chn2off1,chn2pulse,chn2off2, chn2dc, chn2pulse2, chn2dc2]
	# 	self.fungen.create_arbseq('pumpPulse', seq, 1)
	# 	self.fungen.create_arbseq('freq', seq2, 2)
	# 	self.fungen.sync()
	# 	self.fungen.wait()
	# 	self.fungen.voltage[1] = 1
	# 	self.fungen.voltage[2] = 3.6
	# 	self.fungen.offset[2] = 0
	# 	self.fungen.wait()
	# 	self.fungen.output[2] = 'ON'
	# 	time.sleep(1)
	# 	self.fungen.output[1] = 'ON'
	# 	# self.osc.init()
	# 	# self.osc.forcetrigger()
	# 	# self.osc.triggerlevel()
	# 	# self.osc.triggersource = 'CH3'
	# 	time.sleep(100000)

	def pump(self, timestep):
		for i in range(70):
			params = self.parameters.widget.get()
			per=200e-3

			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			tri_time = 1000e-6
			offset=0.2
			height = 0.73-offset
			heights = list()
			heights.append(height)
			while height > 0.44-offset:
				height -= 0.28*(4*timestep)/tri_time
				if height <0.44-offset:
					height=0.44-offset
				heights.append(height)
			# while height < 0:
			# 	height += (4*timestep)/tri_time
			# 	if height>0:
			# 		height=0
			# 	heights.append(height)
			while height < 1-offset:
				height += 0.28*(4*timestep)/tri_time
				if height>1-offset:
					height=1-offset
				heights.append(height)
			while height >0.73-offset:
				height-= 0.28*(4*timestep)/tri_time
				if height <0.73-offset:
					height=0.73-offset
				heights.append(height)
			print(heights)
			chn2pulse2.heights = heights
			chn2pulse2.delays = [0] * len(heights)
			chn2pulse2.totaltime = tri_time
			chn2pulse2.widths = [timestep] * len(heights)
			chn2pulse2width=[timestep] * len(heights)
			print('chn2 len(heights) is:' + str(len(heights)))
			chn2pulse2.totaltime = len(heights) * timestep
			print('chn2_shb totaltime is:' + str(chn2pulse2.totaltime))
			chn2pulse2.nrepeats = 3
			print('chn2_shb nrepeats is:' + str(chn2pulse2.nrepeats))
			chn2pulse2.repeatstring = 'repeat'
			chn2pulse2.markerstring = 'lowAtStart'
			chn2pulse2.markerloc = 0
			chn2pulse2.create_sequence()

			# chn2trioff = Arbseq_Class('chn2trioff', timestep)
			# chn2trioff.heights = heights
			# chn2trioff.delays = [0] * len(heights)
			# chn2trioff.totaltime = tri_time
			# chn2trioff.widths = [timestep] * len(heights)
			# chn2trioffwidth=[timestep] * len(heights)
			# print('chn2 len(heights) is:' + str(len(heights)))
			# chn2trioff.totaltime = len(heights) * timestep
			# chn2trioff.nrepeats = int(0.1e-3/tri_time)
			# chn2trioff.repeatstring = 'repeat'
			# chn2trioff.markerstring = 'lowAtStart'
			# chn2trioff.markerloc = 0
			# chn2trioff.create_sequence()

			chn1off1 = Arbseq_Class('chn1off1', timestep)
			chn1off1.delays = [0]
			chn1off1.heights = [0]
			chn1off1.widths = [params['ramp time'].magnitude]
			chn1off1.totaltime = params['ramp time'].magnitude
			chn1off1.nrepeats = 0
			chn1off1.repeatstring = 'once'
			chn1off1.markerstring = 'highAtStartGoLow'
			chn1off1.markerloc = 0
			chn1off1.create_sequence()

			chn1pulse = Arbseq_Class('chn1pulse', timestep)
			chn1pulse.delays = [0]
			chn1pulse.heights = [1]
			chn1pulse.widths = [params['pump width'].magnitude]
			chn1pulse.totaltime = params['pump width'].magnitude
			chn1pulse.nrepeats = 10
			chn1pulse.repeatstring = 'repeat'
			chn1pulse.markerstring = 'lowAtStart'
			chn1pulse.markerloc = 0
			chn1pulse.create_sequence()

			chn1off2 = Arbseq_Class('chn1off2', timestep)
			chn1off2.delays = [0]
			chn1off2.heights = [0]
			chn1off2.widths = [params['ramp time'].magnitude]
			chn1off2.totaltime = params['ramp time'].magnitude
			chn1off2.nrepeats = 0
			chn1off2.repeatstring = 'once'
			chn1off2.markerstring = 'lowAtStart'
			chn1off2.markerloc = 0
			chn1off2.create_sequence()

			# chn1trioff = Arbseq_Class('chn1trioff', timestep)
			# chn1trioff.delays = [0]*len(heights)
			# chn1trioff.heights = [1]*len(heights)
			# chn1trioff.widths = [timestep] * len(heights)
			# chn1trioff.totaltime = tri_time
			# chn1trioff.nrepeats = int(0.1e-3/tri_time)
			# chn1trioff.repeatstring = 'repeat'
			# chn1trioff.markerstring = 'lowAtStart'
			# chn1trioff.markerloc = 0
			# chn1trioff.create_sequence()


			chn1dc = Arbseq_Class('dc1', timestep)
			chn1dc.delays = [0]
			chn1dc.heights = [0]
			chn1dc.widths = [params['wait time unit'].magnitude]
			chn1dc.totaltime = params['wait time unit'].magnitude
			chn1dc.nrepeats = i+1
			chn1dc.repeatstring = 'repeat'
			chn1dc.markerstring = 'lowAtStart'
			chn1dc.markerloc = 0
			chn1dc.create_sequence()

			chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
			chn1pulse2.delays = [0]*len(heights)
			chn1pulse2.heights = [0.4]*10+ [0.4]*(len(heights)-10)
			chn1pulse2.widths = [timestep] * len(heights)
			chn1pulse2.totaltime = tri_time
			chn1pulse2.nrepeats = 3
			chn1pulse2.repeatstring = 'repeat'
			chn1pulse2.markerstring = 'lowAtStart'
			chn1pulse2.markerloc = 0
			chn1pulse2.create_sequence()

			chn1dc2 = Arbseq_Class('chn1dc2', timestep)
			chn1dc2.delays = [0]
			chn1dc2.heights = [0]
			chn1dc2.widths = [params['pump width'].magnitude]
			chn1dc2.totaltime = params['pump width'].magnitude
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2.markerloc = 0
			chn1dc2.nrepeats = int((per-tri_time-(i+1)*params['wait time unit'].magnitude-10*params['pump width'].magnitude)/params['pump width'].magnitude)
			chn1dc2.create_sequence()

			chn2off1 = Arbseq_Class('chn2off1', timestep)
			chn2off1.delays = [0]
			chn2off1.heights = [0]
			chn2off1.widths = [params['ramp time'].magnitude]
			chn2off1.totaltime = params['ramp time'].magnitude
			chn2off1.nrepeats = 0
			chn2off1.repeatstring = 'once'
			chn2off1.markerstring = 'lowAtStart'
			chn2off1.markerloc = 0
			chn2off1.create_sequence()

			chn2pulse = Arbseq_Class('chn2pulse', timestep)
			chn2pulse.delays = [0]
			chn2pulse.heights = [0.65]
			chn2pulse.widths = [params['pump width'].magnitude]
			chn2pulse.totaltime = params['pump width'].magnitude
			chn2pulse.nrepeats = 10
			chn2pulse.repeatstring = 'repeat'
			chn2pulse.markerstring = 'highAtStartGoLow'
			chn2pulse.markerloc = 0
			chn2pulse.create_sequence()

			chn2off2 = Arbseq_Class('chn2off2', timestep)
			chn2off2.delays = [0]
			chn2off2.heights = [0]
			chn2off2.widths = [params['ramp time'].magnitude]
			chn2off2.totaltime = params['ramp time'].magnitude
			chn2off2.nrepeats = 0
			chn2off2.repeatstring = 'once'
			chn2off2.markerstring = 'lowAtStart'
			chn2off2.markerloc = 0
			chn2off2.create_sequence()

			chn2dc = Arbseq_Class('chn2dc', timestep)
			chn2dc.delays = [0]
			chn2dc.heights = [0]
			chn2dc.widths = [params['wait time unit'].magnitude]
			chn2dc.totaltime = params['wait time unit'].magnitude
			chn2dc.nrepeats = i+1
			chn2dc.repeatstring = 'repeat'
			chn2dc.markerstring = 'lowAtStart'
			chn2dc.markerloc = 0
			chn2dc.create_sequence()


			chn2dc2 = Arbseq_Class('chn2dc2', timestep)
			chn2dc2.delays = [0]
			chn2dc2.heights = [0]
			chn2dc2.widths = [params['pump width'].magnitude]
			chn2dc2.totaltime = params['pump width'].magnitude
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2.markerloc = 0
			chn2dc2.nrepeats = int((per-tri_time-(i+1)*params['wait time unit'].magnitude-10*params['pump width'].magnitude)/params['pump width'].magnitude)
			chn2dc2.create_sequence()

			self.fungen.send_arb(chn1off1,1)
			self.fungen.send_arb(chn1pulse, 1)
			self.fungen.send_arb(chn1off2,1)
			self.fungen.send_arb(chn1dc, 1)
			# self.fungen.send_arb(chn1trioff, 1)
			self.fungen.send_arb(chn1pulse2, 1)
			self.fungen.send_arb(chn1dc2, 1)
			self.fungen.send_arb(chn2off1,2)
			self.fungen.send_arb(chn2pulse, 2)
			self.fungen.send_arb(chn2off2,2)
			self.fungen.send_arb(chn2dc, 2)
			self.fungen.send_arb(chn2pulse2, 2)
			self.fungen.send_arb(chn2dc2, 2)
			# self.fungen.send_arb(chn2trioff, 2)


			seq = [chn1off1, chn1pulse,chn1off2, chn1dc, chn1pulse2, chn1dc2]
			seq2 = [chn2off1,chn2pulse,chn2off2, chn2dc, chn2pulse2, chn2dc2]
			self.fungen.create_arbseq('pumpPulse', seq, 1)
			self.fungen.create_arbseq('freq', seq2, 2)
			self.fungen.sync()
			self.fungen.wait()
			self.fungen.voltage[1] = 1+0.00000001*i
			self.fungen.voltage[2] = 3.6+0.00000001*i
			self.fungen.wait()
			self.fungen.output[2] = 'ON'
			time.sleep(1)
			self.fungen.output[1] = 'ON'
			self.osc.triggersource = 'CH4'
			self.osc.set_time((i+1)*params['wait time unit'].magnitude + 0.0208)
			# time.sleep(10000)

			time.sleep(10)
			x,y=self.osc.curv()
			x = np.array(x)
			x = x-x.min()
			y = np.array(y)
			np.savez(os.path.join("D:\\Data\\6.12.2019\\HoleBurning0T",str(i)),x,y)

			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()
			self.fungen.output[2] = 'OFF'
			self.fungen.output[1] = 'OFF'


	def probe(self,timestep):
		params = self.parameters.widget.get()
		# triangle = Arbseq_Class('triangle', timestep)
		# triangle.heights = self.makeTriangle(timestep)
		# triangle.totaltime = 1/params['triangle frequency'].magnitude
		# triangle.widths = [timestep] * len(triangle.heights)
		# triangle.delays=[0]*len(triangle.heights)
		# triangle.repeatstring = 'once'
		# triangle.markerstring = 'lowAtStart'
		# triangle.markerloc = 0
		# triangle.nrepeats = 0
		# triangle.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]*len(triangle.heights)
		chn1dc.heights = [1]*len(triangle.heights)
		chn1dc.widths = [timestep] * len(triangle.heights)
		chn1dc.totaltime = params['pump width'].magnitude
		chn1dc.repeatstring = 'once'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dc.nrepeats = 0
		chn1dc.create_sequence()

		self.fungen.send_arb(chn1dc, 1)
		# self.fungen.send_arb(triangle, 2)

		seq=[chn1dc]
		# seq2=[triangle]

		self.fungen.create_arbseq('probe', seq, 1)
		# self.fungen.create_arbseq('triangle', seq2, 2)
		self.fungen.wait()
		self.fungen.voltage[1] = params['probe height']*2
		# self.fungen.voltage[2] = params['triangle height']*2

	def oscSet(self):
		params = self.parameters.widget.get()
		#self.osc.time_scale(0.05/params['triangle frequency'].magnitude)
		#self.osc.scale(3,0.5)
		#self.osc.position(3,-2*params['AOM Voltage'].magnitude)
		return


	@Task()
	def run(self):
		timestep = 1e-6
		self.pump(timestep)
		# timestep = 10e-6
		# params = self.parameters.widget.get()
		# for i in range(1000):
		# 	# self.fungen.waveform[1]='DC'
		# 	# self.fungen.offset[1]=1.0
		# 	# self.fungen.waveform[2]='DC'
		# 	# self.fungen.offset[2]=3.6
		# 	# self.fungen.wait()
		# 	self.fungen.output[1]='ON'
		# 	self.fungen.output[2]='ON'
		# 	# self.pump(timestep)
		# 	time.sleep(params['pump time'].magnitude)
		# 	self.fungen.output[1]='OFF'
		# 	time.sleep(params['wait time'].magnitude)
		# 	print('passed sleep')
		# 	# self.probe(1e-3)
		# 	self.fungen.output[2]='OFF'
		# 	self.fungen.wait()
		# 	self.fungen.waveform[2] = 'TRIANGLE'
		# 	self.fungen.offset[2] = params['AOM Voltage'].magnitude
		# 	self.fungen.frequency[2] = 20
		# 	self.fungen.voltage[2] = params['triangle height']
		# 	self.oscSet()
		# 	self.fungen.waveform[1] = 'DC'
		# 	self.fungen.offset[1]=params['probe height']
		# 	self.fungen.output[1]='ON'
		# 	self.fungen.output[2]='ON'
		# 	time.sleep(2)
		# print('passed probe')
		# for i in range(100):
		# 	x,y = self.osc.curv()
		# 	x = np.array(x)
		# 	x = x-x.min()
		# 	y = np.array(y)
		# 	self.xs = x
		# 	self.ys = y
		# 	values = {
		# 		'x': np.asarray(range(len(self.xs))),
		# 		'y': np.asarray(self.ys),
		# 	}
		# 	self.run.acquire(values)
		# 	for j in range(100000):
		# 		self.fungen.output[1]='OFF'
		# 		self.fungen.output[2]='OFF' 
		# 		time.sleep(20)
		# 		self.fungen.output[1]='ON'
		# 		self.fungen.output[2]='ON'
		# 		time.sleep(2) # get values every 5 seconds
		# 	np.savez(os.path.join(out_name,params['File Name']+str(index)),xs,ys)


	@run.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.sync_source(2)
		self.fungen.wait()
		print('init')

	@run.finalizer
	def finalize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		# self.fungen.clear_mem(1)
		# self.fungen.clear_mem(2)
		print('fin')
		return

	@Element(name='Pulse parameters')
	def parameters(self):
		params = [
		('pump height', {'type': float, 'default': 3, 'units':'V'}),
		('pump width', {'type': float, 'default': 2e-3, 'units':'s'}),
		('triangle height', {'type': float, 'default': 1, 'units':'V'}),
		('AOM Voltage', {'type': float, 'default': 3.6, 'units':'V'}),
		('probe height', {'type': float, 'default': 1.0, 'units':'V'}),
		('triangle frequency', {'type': float, 'default': 10, 'units':'Hz'}),
		('pump time', {'type': float, 'default': 1e-3, 'units':'s'}),
		('wait time unit', {'type': float, 'default': 0.5e-3, 'units':'s'}),
		('wait time', {'type': float, 'default': 50e-3, 'units':'s'}),
		('ramp time', {'type': float, 'default': 100e-6, 'units':'s'}),
		('File Name', {'type': str}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='Hole')
	def graph(self):
		p = LinePlotWidget()
		p.plot('Channel 1')
		return p

	@graph.on(run.acquired)
	def graph_update(self, ev):
		w = ev.widget
		xs = self.xs
		ys = self.ys
		w.set('Channel 1', xs=xs, ys=ys)
		return
