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
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client

class Contour(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'wm': Bristol_771
	}
	qutag = None
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

	def createHistogram(self,stoparray, timebase, bincount, period, index, wls):
		hist = [0]*bincount
		for stoptime in stoparray:
			binNumber = int(stoptime*timebase*bincount/(period))
			if binNumber >= bincount:
				continue
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\8.30.2019\\0.1"
		np.savez(os.path.join(out_name,str(index)),hist,wls)
		#np.savez(os.path.join(out_name,str(index+40)),hist,wls)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))


	@Task()
	def startpulse(self, timestep=1e-9):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		params = self.pulse_parameters.widget.get()

		pre1 = Arbseq_Class('pre1', timestep)
		pre1.delays = [0]
		pre1.heights = [0]
		pre1.widths = [params['pulse width'].magnitude]
		pre1.totaltime = params['pulse width'].magnitude
		pre1.nrepeats = 1000
		pre1.repeatstring = 'repeat'
		pre1.markerstring = 'lowAtStart'
		pre1.markerloc = 0
		pre1.create_sequence()

		pulse = Arbseq_Class('pulse', timestep)
		pulse.delays = [0]
		pulse.heights = [1]
		pulse.widths = [params['pulse width'].magnitude]
		pulse.totaltime = params['pulse width'].magnitude
		pulse.nrepeats = 0
		pulse.repeatstring = 'once'
		pulse.markerstring = 'highAtStartGoLow'
		pulse.markerloc = 0
		pulse.create_sequence()

		post1 = Arbseq_Class('post1', timestep)
		post1.delays = [0]
		post1.heights = [0]
		post1.widths = [params['pulse width'].magnitude]
		post1.totaltime = params['pulse width'].magnitude
		post1.nrepeats = 1000
		post1.repeatstring = 'repeat'
		post1.markerstring = 'lowAtStart'
		post1.markerloc = 0
		post1.create_sequence()

		dc = Arbseq_Class('dc', timestep)
		dc.delays = [0]
		dc.heights = [0]
		dc.widths = [params['pulse width'].magnitude]
		dc.totaltime = params['pulse width'].magnitude
		dc.repeatstring = 'repeat'
		dc.markerstring = 'lowAtStart'
		dc.markerloc = 0
		period = params['period'].magnitude
		width = params['pulse width'].magnitude
		repeats = period/width - 1
		dc.nrepeats = repeats
		dc.create_sequence()

		pre2 = Arbseq_Class('pre2', timestep)
		pre2.delays = [0]
		pre2.heights = [1]
		pre2.widths = [params['pulse width'].magnitude]
		pre2.totaltime = params['pulse width'].magnitude
		pre2.nrepeats = 1000
		pre2.repeatstring = 'repeat'
		pre2.markerstring = 'lowAtStart'
		pre2.markerloc = 0
		pre2.create_sequence()

		pulse2 = Arbseq_Class('pulse2', timestep)
		pulse2.delays = [0]
		pulse2.heights = [1]
		pulse2.widths = [params['pulse width'].magnitude]
		pulse2.totaltime = params['pulse width'].magnitude
		pulse2.nrepeats = 0
		pulse2.repeatstring = 'once'
		pulse2.markerstring = 'highAtStartGoLow'
		pulse2.markerloc = 0
		pulse2.create_sequence()

		post2 = Arbseq_Class('post2', timestep)
		post2.delays = [0]
		post2.heights = [1]
		post2.widths = [params['pulse width'].magnitude]
		post2.totaltime = params['pulse width'].magnitude
		post2.nrepeats = 1000
		post2.repeatstring = 'repeat'
		post2.markerstring = 'lowAtStart'
		post2.markerloc = 0
		post2.create_sequence()

		dc2 = Arbseq_Class('dc2', timestep)
		dc2.delays = [0]
		dc2.heights = [-1]
		dc2.widths = [params['pulse width'].magnitude]
		dc2.totaltime = params['pulse width'].magnitude
		dc2.repeatstring = 'repeat'
		dc2.markerstring = 'lowAtStart'
		dc2.markerloc = 0
		period = params['period'].magnitude
		width = params['pulse width'].magnitude
		repeats = period/width - 1
		dc2.nrepeats = repeats
		dc2.create_sequence()

		self.fungen.send_arb(pulse, 1)
		self.fungen.send_arb(dc, 1)
		self.fungen.send_arb(pulse2, 2)
		self.fungen.send_arb(dc2, 2)
		self.fungen.send_arb(pre1, 1)
		self.fungen.send_arb(pre2, 2)
		self.fungen.send_arb(post1, 1)
		self.fungen.send_arb(post2, 2)

		seq1 = [pre1,pulse,post1,dc]
		seq2 = [pre2,pulse2,post2,dc2]

		self.fungen.create_arbseq('pulsetest', seq1, 1)
		self.fungen.wait()
		self.fungen.voltage[1] = params['pulse height']

		self.fungen.create_arbseq('shutter', seq2, 2)
		self.fungen.wait()
		self.fungen.voltage[2] = 7.1
		self.fungen.sync()

		self.configureQutag()

		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		self.homelaser(wlparams['start'])
		print('Laser Homed!')
		self.fungen.output[2] = 'ON'
		self.fungen.output[1] = 'ON'
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		for i in range(expparams['# of points']):
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			while time.time()-startTime < expparams['Measurement Time'].magnitude:
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(30*period)
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
				wls.append(str(self.wm.measure_wavelength()))
			self.createHistogram(stoparray, timebase, bincount, period,i, wls)
			print(i)
			with Client(self.laser) as client:
				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', setting-0.002)
				time.sleep(1)

		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'

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

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('start', {'type': float, 'default': 1535.63}),
		('stop', {'type': float, 'default': 1535.43})
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
		self.wm.start_data()
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()

	@startpulse.finalizer
	def finalize(self):
		self.wm.stop_data()
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


