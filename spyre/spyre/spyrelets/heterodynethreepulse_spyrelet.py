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

class HeterodyneThreePulse(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}

	def saveData(self,x,y,index,ind):
		out_name = "D:\\Data\\7.31.2019\\0.7T\\0.2ms"
		index=str(round(index,8))
		ind='.'+str(ind)
		np.savez(os.path.join(out_name,str(index+ind)),x,y)
		print('Data stored under File Name: ' + str(index) + '.'+str(ind))

	def stepDown(self,channel,scale):
		scales=[5.0,2.0,1.0,0.5,0.2,0.1,0.05,0.02,0.01,0.005]
		i=scales.index(scale)
		if i+1<len(scales):
			return scales[i+1]
		else:
			return scales[i]

	@Task()
	def startpulse(self,timestep=1e-9):
		params = self.pulse_parameters.widget.get()
		tau=params['start tau'].magnitude
		period = params['period'].magnitude
		repeat_unit = params['repeat unit'].magnitude
		pulse_width = params['pulse width'].magnitude
		echo = params['echo'].magnitude
		step_tau=params['step tau'].magnitude
		waitTime=0.2e-3
		for i in range(100):
			self.dataset.clear()
			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'
			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()

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
			chn1dcrepeats = int((tau-pulse_width)/repeat_unit)
			chn1dc.nrepeats = chn1dcrepeats
			chn1dcwidth = repeat_unit*chn1dcrepeats
			chn1dc.create_sequence()
		
			chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
			chn1pulse2.delays = [0]
			chn1pulse2.heights = [1]
			chn1pulse2.widths = [pulse_width]
			chn1pulse2.totaltime = pulse_width
			chn1pulse2width = pulse_width
			chn1pulse2.nrepeats = 0
			chn1pulse2.repeatstring = 'once'
			chn1pulse2.markerstring = 'lowAtStart'
			chn1pulse2.markerloc = 0
			chn1pulse2.create_sequence()

			chn1dc2 = Arbseq_Class('chn1dc2', timestep)
			chn1dc2.delays = [0]
			chn1dc2.heights = [0]
			chn1dc2.widths = [repeat_unit]
			chn1dc2.totaltime = repeat_unit
			chn1dc2width = repeat_unit
			chn1dc2repeats=int((waitTime-pulse_width)/repeat_unit)
			chn1dc2.nrepeats = chn1dc2repeats
			chn1dc2width = repeat_unit*chn1dc2repeats
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2.markerloc = 0
			chn1dc2.create_sequence()

			chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
			chn1pulse3.delays = [0]
			chn1pulse3.heights = [1]
			chn1pulse3.widths = [pulse_width]
			chn1pulse3.totaltime = pulse_width 
			chn1pulse3width = pulse_width
			chn1pulse3.nrepeats = 0
			chn1pulse3.repeatstring = 'once'
			chn1pulse3.markerstring = 'lowAtStart'
			chn1pulse3.markerloc = 0
			chn1pulse3.create_sequence()
		
			chn1dc3 = Arbseq_Class('chn1dc3', timestep)
			chn1dc3.delays = [0]
			chn1dc3.heights = [0]
			chn1dc3.widths = [repeat_unit]
			chn1dc3.totaltime = repeat_unit
			chn1dc3.repeatstring = 'repeat'
			chn1dc3.markerstring = 'lowAtStart'
			chn1dc3repeats = int((period-3*chn1pulsewidth-chn1dcwidth-chn1dc2width)/repeat_unit)
			chn1dc3.nrepeats = chn1dc3repeats
			chn1dc3.markerloc = 0
			chn1dc3.create_sequence()

			self.fungen.send_arb(chn1pulse, 1)
			self.fungen.send_arb(chn1dc, 1)
			self.fungen.send_arb(chn1pulse2, 1)
			self.fungen.send_arb(chn1pulse3, 1)
			self.fungen.send_arb(chn1dc2, 1)
			self.fungen.send_arb(chn1dc3, 1)
			seq = [chn1pulse, chn1dc, chn1pulse2,chn1dc2, chn1pulse3, chn1dc3]
			
			self.fungen.create_arbseq('twoPulse', seq, 1)

			self.fungen.wait()
			self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
			
			print(self.fungen.voltage[1])
			self.fungen.sync()
			self.fungen.output[1] = 'ON'
			# self.osc.set_time(tau*2+pulse_width*3-tau/20)
			#time.sleep(100000)
			# if tau>6.0e-6:
			# 	if tau>60e-6:
			# 		self.osc.scale(1,0.01)
			# 	elif tau>30.0e-6:
			# 		self.osc.scale(1,0.02)
			# 	else:
			# 		self.osc.scale(1,0.02)
			# 	if tau>100e-6:
			# 		self.osc.scale(1,0.01)
			# else:
			# 	self.osc.scale(1,0.02)
			x,y=self.osc.curv()
			y = np.array(y)
			curTime=float(self.osc.query_time())
			maxIndex=np.argmax(y)
			if maxIndex<800:
				self.osc.set_time(curTime-500e-9)
			if np.max(y)<1.1*float(self.osc.scale_query(1)):
				self.osc.scale(1,self.stepDown(1,float(self.osc.scale_query(1))))

			for j in range(5):
				x,y=self.osc.curv()
				x = np.array(x)
				x = x-x.min()
				y = np.array(y)
				self.saveData(x,y,tau,j)
				time.sleep(0.1)
			#time.sleep(1)

			tau=tau+step_tau
			curTime=float(self.osc.query_time())
			self.osc.set_time(curTime+1.98*step_tau)

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