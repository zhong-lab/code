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

class LongHole(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}
	out_name = "D:\\Data\\5.27.2019\\HoleBurning"
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

	def pump(self,j):
		params = self.parameters.widget.get()
		self.fungen.waveform[1]='DC'
		self.fungen.waveform[2]='DC'
		self.fungen.wait()
		self.fungen.voltage[1]=0.0+0.00000001*j
		self.fungen.voltage[2]=0.0+0.000001*j
		self.fungen.offset[1]=1.0+0.000001*j
		self.fungen.offset[2]=3.6+0.000001*j
		self.fungen.wait()
		self.fungen.output[2]='ON'
		self.fungen.output[1]='ON'

	def probe(self,timestep):
		params = self.parameters.widget.get()
		per=100e-3
		chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
		tri_time = 100e-6
		height = 0
		heights = list()
		heights.append(height)
		while height > -1:
			height -= (4*timestep)/tri_time
			if height <-1:
				height=-1
			heights.append(height)
		# while height < 0:
		# 	height += (4*timestep)/tri_time
		# 	if height>0:
		# 		height=0
		# 	heights.append(height)
		while height < 1:
			height += (4*timestep)/tri_time
			if height>1:
				height=1
			heights.append(height)
		while height >0:
			height-= (4*timestep)/tri_time
			if height <0:
				height=0
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
		chn2pulse2.nrepeats = int(0.1e-3/tri_time)
		print('chn2_shb nrepeats is:' + str(chn2pulse2.nrepeats))
		chn2pulse2.repeatstring = 'repeat'
		chn2pulse2.markerstring = 'highAtStartGoLow'
		chn2pulse2.markerloc = 0
		chn2pulse2.create_sequence()

		chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
		chn1pulse2.delays = [0]*len(heights)
		chn1pulse2.heights = [0]*30+[1]*(len(heights)-30)
		chn1pulse2.widths = [timestep] * len(heights)
		chn1pulse2.totaltime = tri_time
		chn1pulse2.nrepeats = int(0.1e-3/tri_time)
		chn1pulse2.repeatstring = 'repeat'
		chn1pulse2.markerstring = 'highAtStartGoLow'
		chn1pulse2.markerloc = 0
		chn1pulse2.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [1e-3]
		chn1dc.totaltime = 1e-3
		chn1dc.nrepeats = int(per/1e-3)
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dc.create_sequence()

		chn2dc = Arbseq_Class('chn2dc', timestep)
		chn2dc.delays = [0]
		chn2dc.heights = [0]
		chn2dc.widths = [1e-3]
		chn2dc.totaltime = 1e-3
		chn2dc.nrepeats = int(per/1e-3)
		chn2dc.repeatstring = 'repeat'
		chn2dc.markerstring = 'lowAtStart'
		chn2dc.markerloc = 0
		chn2dc.create_sequence()

		self.fungen.send_arb(chn2pulse2,2)
		self.fungen.send_arb(chn2dc,2)
		self.fungen.send_arb(chn1pulse2,1)
		self.fungen.send_arb(chn1dc,1)
		

		seq2=[chn2pulse2, chn2dc]
		seq=[chn1pulse2, chn1dc]
		
		self.fungen.create_arbseq('probe', seq, 1)
		self.fungen.create_arbseq('freq', seq2, 2)
		self.fungen.sync()
		self.fungen.wait()
		self.fungen.offset[1] = 0.0+0.00000001
		self.fungen.voltage[1] = 0.3
		self.fungen.voltage[2] = 1.3+0.0000001
		self.fungen.offset[2] = 3.6+0.00000001

	def oscSet(self):
		params = self.parameters.widget.get()
		#self.osc.time_scale(0.05/params['triangle frequency'].magnitude)
		#self.osc.scale(3,0.5)
		#self.osc.position(3,-2*params['AOM Voltage'].magnitude)
		return

	def resetAWG(self,j):
		self.fungen.offset[1] = 0.0+0.00000001*j
		self.fungen.voltage[1] = 0.0+0.00000001*j
		self.fungen.voltage[2] = 0.0+0.0000001*j
		self.fungen.offset[2] = 0.0+0.00000001*j
		return

	@Task()
	def run(self):
		timestep = 1e-6
		params = self.parameters.widget.get()
		# self.fungen.waveform[1]='DC'
		# self.fungen.offset[1]=1.0
		# self.fungen.waveform[2]='DC'
		# self.fungen.offset[2]=3.6
		# self.fungen.wait()
		# self.fungen.output[2]='ON'
		# time.sleep(1)
		# self.fungen.output[1]='ON'
		# time.sleep(0.1)
		# self.fungen.output[1]='OFF'
		# self.fungen.output[2]='OFF'
		self.probe(timestep)
		for j in range(10000):
			self.fungen.output[1]='ON'
			self.fungen.output[2]='ON'
			time.sleep(2)
			self.fungen.wait()
			self.fungen.output[1]='OFF'
			self.fungen.output[2]='OFF'
			time.sleep(10) #Wait Time
		# print('passed wait')
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
		('pump width', {'type': float, 'default': 1e-3, 'units':'s'}),
		('triangle height', {'type': float, 'default': 1, 'units':'V'}),
		('AOM Voltage', {'type': float, 'default': 3.6, 'units':'V'}),
		('probe height', {'type': float, 'default': 1.0, 'units':'V'}),
		('triangle frequency', {'type': float, 'default': 10, 'units':'Hz'}),
		('pump time', {'type': float, 'default': 1e-3, 'units':'s'}),
		('wait time', {'type': float, 'default': 10e-3, 'units':'s'}),
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
