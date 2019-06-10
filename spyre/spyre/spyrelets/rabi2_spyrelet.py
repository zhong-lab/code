##@Riku Fukumori 2019
##Script that automatically does PL lifetime measurements by adjusting the piezo
##voltage of the laser with a DC voltage through the AWG.
##Channel 1 sends the excitation pulse, and Channel 2 sends the slowly ramping
##DC voltage to the piezo input of the laser.

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

class Rabi2(Spyrelet):
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
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))

	def createHistogram(self,stoparray, timebase, bincount, period, index):
		hist = [0]*bincount
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(period))
			if binNumber >= bincount:
				continue
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\5.27.2019\\Rabi2\\Round5"
		np.savez(os.path.join(out_name,str(index*50+200)),hist)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))

	def makePulse(self, pulse_width, i):
		timestep=1e-9
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		params = self.pulse_parameters.widget.get()
		period = params['period'].magnitude
		repeat_unit = 50e-9
		
		buffer1 = Arbseq_Class('buffer1', timestep)
		buffer1.delays = [0]
		buffer1.heights = [0]
		buffer1.widths = [pulse_width]
		buffer1.totaltime = pulse_width
		buffer1.nrepeats = 0
		buffer1.repeatstring = 'once'
		buffer1.markerstring = 'highAtStartGoLow'
		buffer1.markerloc = 0
		buffer1.create_sequence()

		pulse = Arbseq_Class('pulse', timestep)
		pulse.delays = [0]
		pulse.heights = [1]
		pulse.widths = [pulse_width]
		pulse.totaltime = pulse_width
		pulse.nrepeats = 0
		pulse.repeatstring = 'once'
		pulse.markerstring = 'lowAtStart'
		pulse.markerloc = 0
		pulse.create_sequence()

		offset1 = Arbseq_Class('offset1', timestep)
		offset1.delays = [0]
		offset1.heights = [0]
		offset1.widths = [pulse_width]
		offset1.totaltime = pulse_width
		offset1.nrepeats = 0
		offset1.repeatstring = 'once'
		offset1.markerstring = 'lowAtStart'
		offset1.markerloc = 0
		offset1.create_sequence()

		dc = Arbseq_Class('dc', timestep)
		dc.delays = [0]
		dc.heights = [0]
		dc.widths = [params['pulse width'].magnitude]
		dc.totaltime = params['pulse width'].magnitude
		dc.repeatstring = 'repeat'
		dc.markerstring = 'lowAtStart'
		dc.markerloc = 0
		width = params['pulse width'].magnitude
		repeats = period/width - 3
		dc.nrepeats = repeats
		dc.create_sequence()

		buffer2 = Arbseq_Class('buffer2', timestep)
		buffer2.delays = [0]
		buffer2.heights = [1]
		buffer2.widths = [pulse_width]
		buffer2.totaltime = pulse_width
		buffer2.nrepeats = 0
		buffer2.repeatstring = 'once'
		buffer2.markerstring = 'lowAtStart'
		buffer2.markerloc = 0
		buffer2.create_sequence()

		pulse2 = Arbseq_Class('pulse2', timestep)
		pulse2.delays = [0]
		pulse2.heights = [1]
		pulse2.widths = [pulse_width]
		pulse2.totaltime = pulse_width
		pulse2.nrepeats = 0
		pulse2.repeatstring = 'once'
		pulse2.markerstring = 'lowAtStart'
		pulse2.markerloc = 0
		pulse2.create_sequence()

		offset2 = Arbseq_Class('offset2', timestep)
		offset2.delays = [0]
		offset2.heights = [1]
		offset2.widths = [pulse_width]
		offset2.totaltime = pulse_width
		offset2.nrepeats = 0
		offset2.repeatstring = 'once'
		offset2.markerstring = 'lowAtStart'
		offset2.markerloc = 0
		offset2.create_sequence()

		dc2 = Arbseq_Class('dc2', timestep)
		dc2.delays = [0]
		dc2.heights = [-1]
		dc2.widths = [params['pulse width'].magnitude]
		dc2.totaltime = params['pulse width'].magnitude
		dc2.repeatstring = 'repeat'
		dc2.markerstring = 'lowAtStart'
		dc2.markerloc = 0
		period2 = params['period'].magnitude
		width2 = params['pulse width'].magnitude
		repeats = period2/width2 - 3
		dc2.nrepeats = repeats
		dc2.create_sequence()
		
		self.fungen.send_arb(buffer1, 1)
		self.fungen.send_arb(pulse, 1)
		self.fungen.send_arb(offset1, 1)
		self.fungen.send_arb(dc, 1)
		self.fungen.send_arb(buffer2, 2)
		self.fungen.send_arb(pulse2, 2)
		self.fungen.send_arb(offset2, 2)
		self.fungen.send_arb(dc2, 2)
		

		seq = [buffer1, pulse, offset1, dc]
		seq2=[buffer2, pulse2, offset2, dc2]
			
		self.fungen.create_arbseq('twoPulse', seq, 1)
		self.fungen.create_arbseq('shutter', seq2, 2)
		self.fungen.wait()
		self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001*i
		self.fungen.voltage[2] = 7.1+0.000000000001*i
		self.fungen.sync()
			
		print(self.fungen.voltage[1])
		self.fungen.output[2] = 'ON'
		self.fungen.output[1] = 'ON'


	@Task()
	def startpulse(self, timestep=1e-9):
		self.configureQutag()

		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		pulse_width=200e-9
		expparams = self.exp_parameters.widget.get()
		period = self.pulse_parameters.widget.get()['period'].magnitude
		for i in range(expparams['# of points']):
			self.makePulse(pulse_width, i)
			stoparray = []
			startTime = time.time()
			lost = self.qutag.getLastTimestamps(True)
			while time.time()-startTime < expparams['Measurement Time'].magnitude:
				time.sleep(10*period)
				timestamps = self.qutag.getLastTimestamps(True)

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps
				print(values)
				for k in range(values):
					# output all stop events together with the latest start event
					# if tchannel[k] == start:
					# 	synctimestamp = tstamp[k]
					# else:
					# 	stoptimestamp = tstamp[k]
						stoparray.append(tstamp[k])
			self.createHistogram(stoparray, timebase, bincount, period,i)
			pulse_width+=50e-9

		self.fungen.output[1] = 'OFF'

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')
		

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 300e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 20}),
		('Measurement Time', {'type': int, 'default': 10, 'units':'s'}),
		('File Name', {'type': str})
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 1}),
		('Bin Count', {'type': int, 'default': 1000})
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
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		print('Lifetime measurements complete.')
		return

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


