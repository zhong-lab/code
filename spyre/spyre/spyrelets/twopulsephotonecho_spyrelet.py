import numpy as np
import pyqtgraph as pg
import time
import csv

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

class TwoPulsePhotonEcho(Spyrelet):
	requires = {
		'fungen': Keysight_33622A
	}
	qutag = None

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.enableChannels((start,stop))

	# def createHistogram(self,stoparray, timebase, bincount, period, tau):
	# 	hist = [0]*bincount
	# 	for stoptime in stoparray:
	# 		normalizedTime = int(stoptime*timebase*bincount/(period))
	# 		hist[normalizedTime]+=1
	# 	values = {'x':[0,1,2,3,4,5,6,7,8,9], 'y':np.asarray(hist)}

	@Task()
	def startpulse(self, timestep=1e-6):
		params = self.pulse_parameters.widget.get()
		tau=params['start tau']
		for i in range(int((params['stop tau']-params['start tau'])/params['step tau'])+1):
			self.dataset.clear()
			self.fungen.clear_mem(1)
			self.fungen.clear_mem(2)
			self.fungen.wait()

			pulse = Arbseq_Class('pulse', timestep)
			pulse.delays = [0]
			pulse.heights = [0.5]
			pulse.widths = [params['pulse width'].magnitude]
			pulse.totaltime = params['pulse width'].magnitude
			pulse.nrepeats = 0
			pulse.repeatstring = 'once'
			pulse.markerstring = 'highAtStartGoLow'
			pulse.markerloc = 0
			pulse.create_sequence()

			dc = Arbseq_Class('dc', timestep)
			dc.delays = [0]
			dc.heights = [0]
			dc.widths = [params['pulse width'].magnitude]
			dc.totaltime = params['pulse width'].magnitude
			dc.repeatstring = 'repeat'
			dc.markerstring = 'lowAtStart'
			dc.markerloc = 0
			dc.nrepeats = (tau-params['pulse width'])/params['pulse width']
			dc.create_sequence()

			pulse2 = Arbseq_Class('pulse2', timestep)
			pulse2.delays = [0]
			pulse2.heights = [1]
			pulse2.widths = [params['pulse width'].magnitude]
			pulse2.totaltime = params['pulse width'].magnitude
			pulse2.nrepeats = 0
			pulse2.repeatstring = 'once'
			pulse2.markerstring = 'lowAtStart'
			pulse2.markerloc = 0
			pulse2.create_sequence()

			dc2 = Arbseq_Class('dc2', timestep)
			dc2.delays = [0]
			dc2.heights = [0]
			dc2.widths = [params['pulse width'].magnitude]
			dc2.totaltime = params['pulse width'].magnitude
			dc2.repeatstring = 'repeat'
			dc2.markerstring = 'lowAtStart'
			dc2.markerloc = 0
			dc2.nrepeats = (params['period'].magnitude-tau.magnitude-params['pulse width'].magnitude)/params['pulse width'].magnitude
			dc2.create_sequence()

			self.fungen.send_arb(pulse, 1)
			self.fungen.send_arb(pulse2, 1)
			self.fungen.send_arb(dc, 1)
			self.fungen.send_arb(dc2, 1)

			seq = [pulse, dc, pulse2,dc2]

			self.fungen.create_arbseq('twoPulse', seq, 1)
			self.fungen.wait()
			self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
			
			print(self.fungen.voltage[1])
			self.fungen.output[1] = 'ON'

			##Qutag Part
			qutagparams = self.qutag_params.widget.get()
			lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
			stoptimestamp = 0
			synctimestamp = 0
			bincount = qutagparams['Bin Count']
			timebase = self.qutag.getTimebase()
			start = qutagparams['Start Channel']
			stop = qutagparams['Stop Channel']
			stoparray = []
			for j in range(self.exp_parameters.widget.get()['# of Passes']):
				time.sleep(params['period'].magnitude)
				timestamps = self.qutag.getLastTimestamps(True)

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps
				for k in range(values):
					# output all stop events together with the latest start event
					if tchannel[k] == start:
						synctimestamp = tstamp[k]
					else:
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
			#self.createHistogram(stoparray, timebase, bincount,params['period'].magnitude,tau)
			hist = [0]*bincount
			for stoptime in stoparray:
				normalizedTime = int(stoptime*timebase*bincount/(params['period'].magnitude))
				hist[normalizedTime]+=1
			values = {'x':tau, 'y':max(hist)}
			self.startpulse.acquire(values)


			tau+=params['step tau']
			self.fungen.output[1] = 'OFF'

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 1}),
		('Bin Count', {'type': int, 'default': 10})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of Passes', {'type': int, 'default': 100}),
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
		xs = self.data.x
		ys = self.data.y
		w.set('Channel 1', xs=xs, ys=ys)
		return

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 1, 'units':'V'}),
		('pulse width', {'type': float, 'default': 500e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		('start tau', {'type': float, 'default': 1, 'units':'us'}),
		('stop tau', {'type': float, 'default': 10, 'units':'us'}),
		('step tau', {'type': float, 'default': 1, 'units':'us'}),
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