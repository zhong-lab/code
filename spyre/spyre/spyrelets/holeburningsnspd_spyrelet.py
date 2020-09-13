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

class HoleBurningSNSPD(Spyrelet):
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

	def createHistogram(self,stoparray, timebase, bincount, period, index, wls):
		hist = [0]*bincount
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(period))
			if binNumber >= bincount:
				continue
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\8.2.2019\\thinfilm\\holeburning\\test"
		np.savez(os.path.join(out_name,str(index)),hist,wls)
		#np.savez(os.path.join(out_name,str(index+40)),hist,wls)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))


	@Task()
	def startpulse(self, timestep=1e-9):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		repeat_unit = 50e-9
		buffer_time = 100e-6
		pulse_width = 500e-9
		period = 200e-3
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		params = self.pulse_parameters.widget.get()

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

		pulse = Arbseq_Class('pulse', timestep)
		pulse.delays = [0]
		pulse.heights = [0]
		pulse.widths = [repeat_unit]
		pulse.totaltime = repeat_unit
		pulserepeat = 400000
		pulse.nrepeats = pulserepeat
		chn1pulsewidth=pulserepeat*repeat_unit
		pulse.repeatstring = 'repeat'
		pulse.markerstring = 'lowAtStart'
		pulse.markerloc = 0
		pulse.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [repeat_unit]
		chn1dc.totaltime = repeat_unit
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dcrepeats = 200000
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
		chn1pulse2.markerstring = 'highAtStartGoLow'
		chn1pulse2.markerloc = 0
		chn1pulse2.create_sequence()

		# chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
		# chn1pulse3.delays = [0]
		# chn1pulse3.heights = [0]
		# chn1pulse3.widths = [repeat_unit]
		# chn1pulse3.totaltime = repeat_unit 
		# chn1pulse3width = shutter_offset
		# chn1pulse3.nrepeats = shutter_offset/repeat_unit
		# chn1pulse3.repeatstring = 'repeat'
		# chn1pulse3.markerstring = 'lowAtStart'
		# chn1pulse3.markerloc = 0
		# chn1pulse3.create_sequence()

		chn1dc2 = Arbseq_Class('chn1dc2', timestep)
		chn1dc2.delays = [0]
		chn1dc2.heights = [0]
		chn1dc2.widths = [pulse_width]
		chn1dc2.totaltime = pulse_width
		chn1dc2.repeatstring = 'repeat'
		chn1dc2.markerstring = 'lowAtStart'
		chn1dc2repeats = 2e5
		ch1dc2width=chn1dc2repeats*pulse_width
		chn1dc2.nrepeats = chn1dc2repeats
		chn1dc2.markerloc = 0
		#print((chn1dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
		chn1dc2.create_sequence()

		totalTime=chn1bufferwidth+chn1pulsewidth+chn1dcwidth+chn1pulse2width+ch1dc2width

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

		chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
		chn2pulse1.delays = [0]
		chn2pulse1.heights = [1]
		chn2pulse1.widths = [repeat_unit]
		chn2pulse1.totaltime = repeat_unit
		chn2pulse1.nrepeats = pulserepeat
		chn2pulse1width = pulse_width
		chn2pulse1.repeatstring = 'repeat'
		chn2pulse1.markerstring = 'lowAtStart'
		chn2pulse1.markerloc = 0
		chn2pulse1.create_sequence()

		chn2dc1 = Arbseq_Class('chn2dc1', timestep)
		chn2dc1.delays = [0]
		chn2dc1.heights = [1]
		chn2dc1.widths = [repeat_unit]
		chn2dc1.totaltime = repeat_unit
		chn2dc1.repeatstring = 'repeat'
		chn2dc1.markerstring = 'lowAtStart'
		chn2dc1.markerloc = 0
		chn2dc1repeats = chn1dcrepeats
		chn2dc1.nrepeats = chn1dcrepeats
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
		chn2pulse2.markerstring = 'highAtStartGoLow'
		chn2pulse2.markerloc = 0
		chn2pulse2.create_sequence()

		chn2dc2 = Arbseq_Class('chn2dc2', timestep)
		chn2dc2.delays = [0]
		chn2dc2.heights = [-1]
		chn2dc2.widths = [pulse_width]
		chn2dc2.totaltime = pulse_width
		chn2dc2.repeatstring = 'repeat'
		chn2dc2.markerstring = 'lowAtStart'
		chn2dc2repeats = chn1dc2repeats
		chn2dc2.nrepeats = chn2dc2repeats
		chn2dc2.markerloc = 0
		chn2dc2.create_sequence()


		self.fungen.send_arb(chn1buffer, 1)
		self.fungen.send_arb(pulse, 1)
		self.fungen.send_arb(chn1dc, 1)
		self.fungen.send_arb(chn1pulse2, 1)
		self.fungen.send_arb(chn1dc2, 1)
		self.fungen.send_arb(chn2buffer, 2)
		self.fungen.send_arb(chn2pulse1, 2)
		self.fungen.send_arb(chn2dc1, 2)
		self.fungen.send_arb(chn2pulse2, 2)
		self.fungen.send_arb(chn2dc2, 2)

		seq = [chn1buffer, pulse, chn1dc, chn1pulse2, chn1dc2]
		seq2=[chn2buffer,chn2pulse1,chn2dc1,chn2pulse2,chn2dc2]

		self.fungen.create_arbseq('pulsetest', seq2, 2)
		self.fungen.wait()
		self.fungen.voltage[2] = 7.1
		self.fungen.output[2] = 'ON'
		#self.fungen.sync()

		self.fungen.create_arbseq('pulsetest', seq, 1)
		self.fungen.wait()
		self.fungen.voltage[1] = params['pulse height']
		self.fungen.sync()
		self.fungen.output[1] = 'ON'

		#time.sleep(100000)

		self.configureQutag()

		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		expparams = self.exp_parameters.widget.get()
		for i in range(expparams['# of points']):
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			while time.time()-startTime < expparams['Measurement Time'].magnitude:
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(30*totalTime)
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
			self.createHistogram(stoparray, timebase, bincount, totalTime,i, wls)
			print(i)
			#self.fungen.voltage[2] = self.fungen.voltage[2].magnitude + 2*dcparams['DC step size'].magnitude

		self.fungen.output[1] = 'OFF'

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')
		

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 500e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='DC parameters')
	def DC_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('DC height', {'type': float, 'default': 0, 'units':'V'}),
		('DC step size', {'type': float, 'default': 0.1, 'units':'V'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 10}),
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


