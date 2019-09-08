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

class ThinFilmHoleBurning(Spyrelet):
	requires = {
		'fungen': Keysight_33622A
	}
	qutag = None
	xs = np.array([])
	ys= np.array([])
	hist=[]
	laser = NetworkConnection('1.1.1.1')

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))

	def homelaser(self,start):
		current=self.wm.measure_wavelength()
		with Client(self.laser) as client:
			while current<start-0.001 or current>start+0.001:
				setting=client.get('laser1:ctl:wavelength-set', float)
				offset=current-start
				client.set('laser1:ctl:wavelength-set', setting-offset)
				time.sleep(3)
				current=self.wm.measure_wavelength()
				print(current, start)

	def createHistogram(self,stoparray, timebase, bincount, totalWidth, tau):
		hist = [0]*bincount
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(totalWidth))
			if binNumber >= bincount:
				continue
				print('error')
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\9.04.2019\\0"
		x=[]
		for i in range(bincount):
			x.append(i*totalWidth/bincount)
		np.savez(os.path.join(out_name,str(int(round(tau*1e6,0)))),hist,x)
		print('Data stored under File Name: ' + str(tau))

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
			chn1buffer.widths = [500e-9]
			chn1buffer.totaltime = 500e-9
			chn1buffer.nrepeats = 0
			chn1buffer.repeatstring = 'once'
			chn1buffer.markerstring = 'highAtStartGoLow'
			chn1buffer.markerloc = 0
			chn1bufferwidth = repeat_unit*chn1buffer.nrepeats
			chn1buffer.create_sequence()

			chn1buffer2 = Arbseq_Class('chn1buffer2', timestep)
			chn1buffer2.delays = [0]
			chn1buffer2.heights = [0]
			chn1buffer2.widths = [500e-9]
			chn1buffer2.totaltime = 500e-9
			chn1buffer2.nrepeats = 5000
			ch1buffer2width=chn1buffer2.nrepeats*pulse_width
			chn1buffer2.repeatstring = 'repeat'
			chn1buffer2.markerstring = 'lowAtStart'
			chn1buffer2.markerloc = 0
			chn1buffer2.create_sequence()

			chn1pulse = Arbseq_Class('chn1pulse', timestep)
			chn1pulse.delays = [0]
			chn1pulse.heights = [1]
			chn1pulse.widths = [repeat_unit]
			chn1pulse.totaltime = repeat_unit
			chn1pulse.nrepeats = 0
			chn1pulse.repeatstring = 'repeat'
			chn1pulserepeats = 20000*20
			chn1pulse.nrepeats = chn1pulserepeats
			chn1pulsewidth=chn1pulserepeats*repeat_unit
			chn1pulse.markerstring = 'lowAtStart'
			chn1pulse.markerloc = 0
			chn1pulsewidth = pulse_width
			chn1pulse.create_sequence()

			chn1dc = Arbseq_Class('chn1dc', timestep)
			chn1dc.delays = [0]
			chn1dc.heights = [0]
			chn1dc.widths = [1e-6]
			chn1dc.totaltime = 1e-6
			chn1dc.repeatstring = 'repeat'
			chn1dc.markerstring = 'lowAtStart'
			chn1dc.markerloc = 0
			chn1dcrepeats = 100e3
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
			chn1dc2.widths = [300e-9*20]
			chn1dc2.totaltime = 300e-9**20
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2repeats = int((0.5-chn1dcwidth-chn1bufferwidth-ch1buffer2width-chn1pulsewidth-pulse_width)/(300e-9*20))
			chn1dc2.nrepeats = chn1dc2repeats
			chn1dc2.markerloc = 0
			chn1dc2.create_sequence()

			## build pulse sequence for AWG channel 2
			chn2buffer = Arbseq_Class('chn2buffer', timestep)
			chn2buffer.delays = [0]
			chn2buffer.heights = [1]
			chn2buffer.widths = [500e-9]
			chn2buffer.totaltime = 500e-9
			chn2bufferwidth=pulse_width
			chn2buffer.nrepeats = 0
			chn2buffer.repeatstring = 'once'
			chn2buffer.markerstring = 'highAtStartGoLow'
			chn2buffer.markerloc = 0
			chn2buffer.create_sequence()

			chn2buffer2 = Arbseq_Class('chn2buffer2', timestep)
			chn2buffer2.delays = [0]
			chn2buffer2.heights = [1]
			chn2buffer2.widths = [500e-9]
			chn2buffer2.totaltime = 500e-9
			chn2buffer2.nrepeats = 5000
			chn2buffer2width=chn2buffer2.nrepeats*pulse_width
			chn2buffer2.repeatstring = 'repeat'
			chn2buffer2.markerstring = 'lowAtStart'
			chn2buffer2.markerloc = 0
			chn2buffer2.create_sequence()

			chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
			chn2pulse1.delays = [0]
			chn2pulse1.heights = [1]
			chn2pulse1.widths = [repeat_unit]
			chn2pulse1.totaltime = repeat_unit
			chn2pulse1.nrepeats = 20000*20
			chn2pulse1width = repeat_unit*chn2pulse1.nrepeats
			chn2pulse1.repeatstring = 'repeat'
			chn2pulse1.markerstring = 'lowAtStart'
			chn2pulse1.markerloc = 0
			chn2pulse1.create_sequence()

			chn2dc1 = Arbseq_Class('chn2dc1', timestep)
			chn2dc1.delays = [0]
			chn2dc1.heights = [-1]
			chn2dc1.widths = [1e-6]
			chn2dc1.totaltime = 1e-6
			chn2dc1.repeatstring = 'repeat'
			chn2dc1.markerstring = 'lowAtStart'
			chn2dc1.markerloc = 0
			chn2dc1repeats =100e3
			chn2dc1.nrepeats = chn2dc1repeats
			chn2dc1width = repeat_unit*chn2dc1repeats
			chn2dc1.create_sequence()
	
			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			chn2pulse2.delays = [0]
			chn2pulse2.heights = [-1]
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
			chn2dc2.heights = [-1]
			chn2dc2.widths = [300e-9*20]
			chn2dc2.totaltime = 300e-9*20
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2repeats = int((0.5-chn2dc1width-chn2bufferwidth-chn2buffer2width-chn2pulse1width-pulse_width)/(300e-9*20))
			chn2dc2.nrepeats = chn2dc2repeats
			chn2dc2.markerloc = 0
			chn2dc2.create_sequence()

			self.fungen.send_arb(chn1buffer, 1)
			self.fungen.send_arb(chn1buffer2, 1)
			self.fungen.send_arb(chn1pulse, 1)
			self.fungen.send_arb(chn1dc, 1)
			self.fungen.send_arb(chn1pulse2, 1)
			self.fungen.send_arb(chn1dc2, 1)
			self.fungen.send_arb(chn2buffer, 2)
			self.fungen.send_arb(chn2buffer2, 2)
			self.fungen.send_arb(chn2pulse1, 2)
			self.fungen.send_arb(chn2dc1, 2)
			self.fungen.send_arb(chn2pulse2, 2)
			self.fungen.send_arb(chn2dc2, 2)

			seq = [chn1buffer,chn1buffer2, chn1pulse, chn1dc, chn1pulse2, chn1dc2]
			seq2 = [chn2buffer,chn2buffer2, chn2pulse1, chn2dc1, chn2pulse2, chn2dc2]
			
			self.fungen.create_arbseq('twoPulse', seq, 1)
			self.fungen.create_arbseq('shutter', seq2, 2)
			self.fungen.wait()
			self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
			
			print(self.fungen.voltage[1], self.fungen.voltage[2])
			#self.fungen.trigger_delay(1,shutter_offset)
			self.fungen.sync()
			time.sleep(1)
			self.fungen.output[1] = 'ON'
			#self.fungen.output[2] = 'OFF'
			

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
				time.sleep(5)
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
					
			self.createHistogram(stoparray, timebase, bincount,0.5,tau.magnitude)


			tau+=params['step tau']
			time.sleep(10000)
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
		# ('File Name', {'type': str})
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
		# ('srs bias', {'type': float, 'default': 1.2, 'units':'V'}),
		('shutter offset', {'type': float, 'default': 500e-9, 'units':'s'}),
		('measuring range', {'type': float, 'default': 70e-6, 'units':'s'}),
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
		print('Two Pulse measurements complete.')
		return