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

class ThreePulsePhotonEcho(Spyrelet):
	requires = {
		'fungen': Keysight_33622A
		# 'srs': SRS900
	}
	qutag = None
	xs = np.array([])
	ys= np.array([])
	hist=[]

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))

	def createHistogram(self,stoparray, timebase, bincount, totalWidth, tau):
		hist = [0]*bincount
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(totalWidth))
			if binNumber >= bincount:
				continue
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\7.29.2019\\no3rdpulse"
		x=[]
		for i in range(bincount):
			x.append(i*totalWidth/bincount)
		np.savez(os.path.join(out_name,self.exp_parameters.widget.get()['File Name']+str(int(round(tau*1e6,0)))),hist,x)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(tau))

	def createPlottingHist(self, stoparray, timebase, bincount, totalWidth):
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(totalWidth))
			if binNumber >= bincount:
				continue
			else:
				self.hist[binNumber]+=1

	def initHist(self, bincount):
		self.hist=[0]*bincount

	@Task()
	def startpulse(self, timestep=1e-9):
		params = self.pulse_parameters.widget.get()
		tau=params['start tau']
		period = params['period'].magnitude
		repeat_unit = params['repeat unit'].magnitude
		pulse_width = params['pulse width'].magnitude
		buffer_time = params['buffer time'].magnitude
		shutter_offset = params['shutter offset'].magnitude
		wholeRange=params['measuring range'].magnitude
		waitTime = params['wait time'].magnitude

		self.configureQutag()
		for i in range(int((params['stop tau']-params['start tau'])/params['step tau'])+1):
			xs = np.array([])
			ys= np.array([])
			hist=[]
			self.dataset.clear()
			self.fungen.output[1] = 'OFF'
			self.fungen.output[2] = 'OFF'
			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()
			# self.srs.module_reset[5]
			# self.srs.SIM928_voltage[5]=params['srs bias'].magnitude+0.000000001*i
			# self.srs.SIM928_on[5]

			## build pulse sequence for AWG channel 1
			chn1buffer = Arbseq_Class('chn1buffer', timestep)
			chn1buffer.delays = [0]
			chn1buffer.heights = [0]
			chn1buffer.widths = [repeat_unit]
			chn1buffer.totaltime = repeat_unit
			chn1buffer.nrepeats = buffer_time/repeat_unit
			chn1buffer.repeatstring = 'repeat'
			chn1buffer.markerstring = 'lowAtStart'
			chn1buffer.markerloc = 0
			chn1bufferwidth = repeat_unit*chn1buffer.nrepeats
			chn1buffer.create_sequence()

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
			chn1dcrepeats = int((tau.magnitude-pulse_width)/repeat_unit)
			chn1dc.nrepeats = chn1dcrepeats
			chn1dcwidth = repeat_unit*chn1dcrepeats
			print(tau.magnitude, pulse_width, chn1dcrepeats)
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
		
			chn1pulse4 = Arbseq_Class('chn1pulse4', timestep)
			chn1pulse4.delays = [0]
			chn1pulse4.heights = [0]
			chn1pulse4.widths = [repeat_unit]
			chn1pulse4.totaltime = repeat_unit 
			chn1pulse4width = shutter_offset
			chn1pulse4.nrepeats = shutter_offset/repeat_unit
			chn1pulse4.repeatstring = 'repeat'
			chn1pulse4.markerstring = 'lowAtStart'
			chn1pulse4.markerloc = 0
			chn1pulse4.create_sequence()
		
			chn1dc3 = Arbseq_Class('chn1dc3', timestep)
			chn1dc3.delays = [0]
			chn1dc3.heights = [0]
			chn1dc3.widths = [repeat_unit]
			chn1dc3.totaltime = repeat_unit
			chn1dc3.repeatstring = 'repeat'
			chn1dc3.markerstring = 'lowAtStart'
			chn1dc3repeats = int((period-chn1bufferwidth-3*chn1pulsewidth-chn1dcwidth-chn1dc2width-chn1pulse4width)/repeat_unit)
			chn1dc3.nrepeats = chn1dc3repeats
			chn1dc3.markerloc = 0
			chn1dc3.create_sequence()

			## build pulse sequence for AWG channel 2
			chn2buffer = Arbseq_Class('chn2buffer', timestep)
			chn2buffer.delays = [0]
			chn2buffer.heights = [1]
			chn2buffer.widths = [repeat_unit]
			chn2buffer.totaltime = repeat_unit
			chn2buffer.nrepeats = buffer_time/repeat_unit
			chn2buffer.repeatstring = 'repeat'
			chn2buffer.markerstring = 'lowAtStart'
			chn2buffer.markerloc = 0
			chn2bufferwidth = repeat_unit*chn2buffer.nrepeats
			chn2buffer.create_sequence()

			chn2pulse = Arbseq_Class('chn2pulse', timestep)
			chn2pulse.delays = [0]
			chn2pulse.heights = [1]
			chn2pulse.widths = [pulse_width]
			chn2pulse.totaltime = pulse_width
			chn2pulse.nrepeats = 0
			chn2pulse.repeatstring = 'once'
			chn2pulse.markerstring = 'highAtStartGoLow'
			chn2pulse.markerloc = 0
			chn2pulsewidth = pulse_width
			chn2pulse.create_sequence()

			chn2dc = Arbseq_Class('chn2dc', timestep)
			chn2dc.delays = [0]
			chn2dc.heights = [1]
			chn2dc.widths = [repeat_unit]
			chn2dc.totaltime = repeat_unit
			chn2dc.repeatstring = 'repeat'
			chn2dc.markerstring = 'lowAtStart'
			chn2dc.markerloc = 0
			chn2dcrepeats = int((tau.magnitude-pulse_width)/repeat_unit)
			chn2dc.nrepeats = chn2dcrepeats
			chn2dcwidth = repeat_unit*chn2dcrepeats
			chn2dc.create_sequence()
		
			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			chn2pulse2.delays = [0]
			chn2pulse2.heights = [1]
			chn2pulse2.widths = [pulse_width]
			chn2pulse2.totaltime = pulse_width
			chn2pulse2width = pulse_width
			chn2pulse2.nrepeats = 0
			chn2pulse2.repeatstring = 'once'
			chn2pulse2.markerstring = 'lowAtStart'
			chn2pulse2.markerloc = 0
			chn2pulse2.create_sequence()

			chn2dc2 = Arbseq_Class('chn2dc2', timestep)
			chn2dc2.delays = [0]
			chn2dc2.heights = [1]
			chn2dc2.widths = [repeat_unit]
			chn2dc2.totaltime = repeat_unit
			chn2dc2width = repeat_unit
			chn2dc2repeats=int((waitTime-pulse_width)/repeat_unit)
			chn2dc2.nrepeats = chn2dc2repeats
			chn2dc2width = repeat_unit*chn2dc2repeats
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2.markerloc = 0
			chn2dc2.create_sequence()

			chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
			chn2pulse3.delays = [0]
			chn2pulse3.heights = [1]
			chn2pulse3.widths = [pulse_width]
			chn2pulse3.totaltime = pulse_width 
			chn2pulse3width = pulse_width
			chn2pulse3.nrepeats = 0
			chn2pulse3.repeatstring = 'once'
			chn2pulse3.markerstring = 'lowAtStart'
			chn2pulse3.markerloc = 0
			chn2pulse3.create_sequence()
		
			chn2pulse4 = Arbseq_Class('chn2pulse4', timestep)
			chn2pulse4.delays = [0]
			chn2pulse4.heights = [1]
			chn2pulse4.widths = [repeat_unit]
			chn2pulse4.totaltime = repeat_unit 
			chn2pulse4width = shutter_offset
			chn2pulse4.nrepeats = shutter_offset/repeat_unit
			chn2pulse4.repeatstring = 'repeat'
			chn2pulse4.markerstring = 'lowAtStart'
			chn2pulse4.markerloc = 0
			chn2pulse4.create_sequence()
		
			chn2dc3 = Arbseq_Class('chn2dc3', timestep)
			chn2dc3.delays = [0]
			chn2dc3.heights = [-1]
			chn2dc3.widths = [repeat_unit]
			chn2dc3.totaltime = repeat_unit
			chn2dc3.repeatstring = 'repeat'
			chn2dc3.markerstring = 'lowAtStart'
			chn2dc3repeats = int((period-chn1bufferwidth-3*chn1pulsewidth-chn1dcwidth-chn1dc2width-chn1pulse4width)/repeat_unit)
			chn2dc3.nrepeats = chn1dc3repeats
			chn2dc3.markerloc = 0
			chn2dc3.create_sequence()

			self.fungen.send_arb(chn1buffer, 1)
			self.fungen.send_arb(chn1pulse, 1)
			self.fungen.send_arb(chn1dc, 1)
			self.fungen.send_arb(chn1pulse2, 1)
			self.fungen.send_arb(chn1pulse3, 1)
			self.fungen.send_arb(chn1pulse4, 1)
			self.fungen.send_arb(chn1dc2, 1)
			self.fungen.send_arb(chn1dc3, 1)
			self.fungen.send_arb(chn2buffer, 2)
			self.fungen.send_arb(chn2pulse, 2)
			self.fungen.send_arb(chn2dc, 2)
			self.fungen.send_arb(chn2pulse2, 2)
			self.fungen.send_arb(chn2pulse3, 2)
			self.fungen.send_arb(chn2pulse4, 2)
			self.fungen.send_arb(chn2dc2, 2)
			self.fungen.send_arb(chn2dc3, 2)

			seq = [chn1buffer, chn1pulse, chn1dc, chn1pulse2,chn1dc2, chn1pulse3,chn1pulse4, chn1dc3]
			seq2 = [chn2buffer, chn2pulse, chn2dc, chn2pulse2,chn2dc2, chn2pulse3,chn2pulse4, chn2dc3]
			
			self.fungen.create_arbseq('threepulse', seq, 1)
			self.fungen.create_arbseq('shutter', seq2, 2)
			self.fungen.wait()
			self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
			self.fungen.voltage[2] = 7.1+0.0000000000001*i
			print(self.fungen.voltage[1], self.fungen.voltage[2])
			self.fungen.output[2] = 'ON'
			self.fungen.trigger_delay(1,shutter_offset)
			self.fungen.sync()
			time.sleep(1)
			self.fungen.output[1] = 'ON'
			#self.fungen.output[2] = 'OFF'
			# time.sleep(10000)

			##Qutag Part
			self.configureQutag()
			qutagparams = self.qutag_params.widget.get()
			lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
			stoptimestamp = 0
			synctimestamp = 0
			bincount = qutagparams['Bin Count']
			timebase = self.qutag.getTimebase()
			start = qutagparams['Start Channel']
			stop = qutagparams['Stop Channel']
			stoparray = []
			tempStopArray = []
			histCounter = 0
			quenchCounter = 0
			self.initHist(bincount)
			for j in range(int(self.exp_parameters.widget.get()['# of Passes'])):
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(period)
				timestamps = self.qutag.getLastTimestamps(True)

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps
				# print(values)
				for k in range(values):
					# output all stop events together with the latest start event
					# if tchannel[k] == start:
					# 	synctimestamp = tstamp[k]
					if tchannel[k]==stop:
						#stoptimestamp = tstamp[k]
					# if tstamp[k]*1e-6>2*tau.magnitude-1 and tstamp[k]*1e-6<2*tau.magnitude+2:
						stoparray.append(tstamp[k])
						#tempStopArray.append(stoptimestamp)
				# histCounter+=1
				# if histCounter%20==0:
				# 	self.createPlottingHist(tempStopArray, timebase, bincount,qutagparams['Total Hist Width Multiplier']*tau.magnitude)
				# 	self.xs = np.asarray(range(len(self.hist)))
				# 	self.ys=np.asarray(self.hist)
				# 	values = {
				# 	't': np.asarray(range(len(self.hist))),
				# 	'y': np.asarray(self.hist),
				# 	}
				# 	self.startpulse.acquire(values)
				# 	tempStopArray = []
					# TODO: quench protection
					# if self.srs.SIM928_voltage[???] >= qunech threshold and quenchCounter<=10:
					# 	self.srs.SIM928_off[6]
					# 	time.sleep(period*10)
					# 	self.srs.SIM928_on[6]
					# 	quenchCounter+=1
					# elif quenchCounter>10:
					# 	print('quenched more than 10 times')
					# 	break
					# else:
					# 	continue
					
			self.createHistogram(stoparray, timebase, bincount,wholeRange,tau.magnitude)


			tau+=params['step tau']
			#self.fungen.output[1] = 'OFF'

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 1}),
		('Total Hist Width Multiplier', {'type': int, 'default': 5}),
		('Bin Count', {'type': int, 'default': 1000})
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

	@Element(name='Histogram')
	def averaged(self):
		p = LinePlotWidget()
		p.plot('Channel 1')
		return p

	@averaged.on(startpulse.acquired)
	def averaged_update(self, ev):
		w = ev.widget
		xs = self.xs
		ys = self.ys
		w.set('Channel 1', xs=xs, ys=ys)
		return

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 300e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('start tau', {'type': float, 'default': 3e-6, 'units':'s'}),
		('stop tau', {'type': float, 'default': 10e-6, 'units':'s'}),
		('step tau', {'type': float, 'default': 1e-6, 'units':'s'}),
		('srs bias', {'type': float, 'default': 1.2, 'units':'V'}),
		('shutter offset', {'type': float, 'default': 500e-9, 'units':'s'}),
		('measuring range', {'type': float, 'default': 70e-6, 'units':'s'}),
		('wait time', {'type': float, 'default': 1e-6, 'units':'s'}),
		('buffer time', {'type': float, 'default': 100e-6, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@qutagInit.initializer
	def initialize(self):
		from lantz.drivers.qutools import QuTAG
		self.qutag = QuTAG()
		devType = self.qutag.getDeviceType()
		if (devType == self.qutag.DEVTYPE_QUTAG):
			print("found quTAG!")
		else:
			print("no suitable device found - demo mode activated")
		print("Device timebase:" + str(self.qutag.getTimebase()))
		return

	@qutagInit.finalizer
	def finalize(self):
		return

	@startpulse.initializer
	def initialize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

	@startpulse.finalizer
	def finalize(self):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		print('Three Pulse measurements complete.')
		return