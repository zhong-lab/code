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
from lantz.drivers.stanford.srs900 import SRS900

class Lifetimewithshutter(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'wm': Bristol_771,
		'srs': SRS900
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
				print('lost: ' + str(stoptime))
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\5.15.2019\\T1"
		np.savez(os.path.join(out_name,self.exp_parameters.widget.get()['File Name']+str(index)),hist,wls)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))


	@Task()
	def startpulse(self, timestep=1e-9):
		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		params = self.pulse_parameters.widget.get()
		tau=params['start tau']
		period = params['period'].magnitude

		chn1pulse = Arbseq_Class('chn1pulse', timestep)
		chn1pulse.delays = [0]
		chn1pulse.heights = [1]
		chn1pulse.widths = [params['pulse width'].magnitude]
		chn1pulse.totaltime = params['pulse width'].magnitude
		chn1pulse.nrepeats = 0
		chn1pulse.repeatstring = 'once'
		chn1pulse.markerstring = 'highAtStartGoLow'
		chn1pulse.markerloc = 0
		chn1pulsewidth = params['pulse width'].magnitude
		chn1pulse.create_sequence()

		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [params['repeat unit'].magnitude]
		chn1dc.totaltime = params['repeat unit'].magnitude
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dc.markerloc = 0
		chn1dcrepeats = int((tau.magnitude-params['pulse width'].magnitude)/(params['repeat unit'].magnitude))
		chn1dc.nrepeats = chn1dcrepeats
		chn1dcwidth = (params['repeat unit'].magnitude)*chn1dcrepeats
		print(tau.magnitude, params['pulse width'].magnitude, chn1dcrepeats)
		chn1dc.create_sequence()
		
		chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
		chn1pulse2.delays = [0]
		chn1pulse2.heights = [1]
		chn1pulse2.widths = [params['pulse width'].magnitude]
		chn1pulse2.totaltime = params['pulse width'].magnitude 
		chn1pulse2width = params['pulse width'].magnitude 
		chn1pulse2.nrepeats = 0
		chn1pulse2.repeatstring = 'once'
		chn1pulse2.markerstring = 'lowAtStart'
		chn1pulse2.markerloc = 0
		chn1pulse2.create_sequence()
		
		chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
		chn1pulse3.delays = [0]
		chn1pulse3.heights = [0]
		chn1pulse3.widths = [params['repeat unit'].magnitude]
		chn1pulse3.totaltime = params['repeat unit'].magnitude 
		chn1pulse3width = 400e-9 
		chn1pulse3.nrepeats = 400e-9/params['repeat unit'].magnitude
		chn1pulse3.repeatstring = 'repeat'
		chn1pulse3.markerstring = 'lowAtStart'
		chn1pulse3.markerloc = 0
		chn1pulse3.create_sequence()
		
		chn1dc2 = Arbseq_Class('chn1dc2', timestep)
		chn1dc2.delays = [0]
		chn1dc2.heights = [0]
		chn1dc2.widths = [params['repeat unit'].magnitude]
		chn1dc2.totaltime = params['repeat unit'].magnitude
		chn1dc2.repeatstring = 'repeat'
		chn1dc2.markerstring = 'lowAtStart'
		chn1dc2repeats = int((params['period'].magnitude-tau.magnitude-params['pulse width'].magnitude-chn1pulse3width)/(params['repeat unit'].magnitude))
		chn1dc2.nrepeats = chn1dc2repeats
		chn1dc2.markerloc = 0
		print((chn1dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
		chn1dc2.create_sequence()

		chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
		chn2pulse1.delays = [0]
		chn2pulse1.heights = [1]
		# chn2pulse1width = pulsewidth+pulse2width+dcwidth
		chn2pulse1.widths=[params['pulse width'].magnitude]
		chn2pulse1.totaltime=params['pulse width'].magnitude
		chn2pulse1.nrepeats = 0
		chn2pulse1.repeatstring = 'once'
		chn2pulse1.markerstring = 'highAtStartGoLow'
		chn2pulse1.markerloc = 0
		chn2pulse1.create_sequence()
		chn2dc1 = Arbseq_Class('chn2dc1', timestep)
		chn2dc1.delays = [0]
		chn2dc1.heights = [1]
		chn2dc1.widths = [params['repeat unit'].magnitude]
		chn2dc1.totaltime = params['repeat unit'].magnitude
		chn2dc1.repeatstring = 'repeat'
		chn2dc1.markerstring = 'lowAtStart'
		chn2dc1.markerloc = 0
		chn2dc1repeats = int((tau.magnitude-params['pulse width'].magnitude)/(params['repeat unit'].magnitude))
		chn2dc1.nrepeats = chn2dc1repeats
		chn2dc1width = (params['repeat unit'].magnitude)*chn2dc1repeats
		chn2dc1.create_sequence()
	
		chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
		chn2pulse2.delays = [0]
		chn2pulse2.heights = [1]
		chn2pulse2.widths = [params['pulse width'].magnitude]
		chn2pulse2.totaltime = params['pulse width'].magnitude 
		chn2pulse2width = params['pulse width'].magnitude
		chn2pulse2.nrepeats = 0
		chn2pulse2.repeatstring = 'once'
		chn2pulse2.markerstring = 'lowAtStart'
		chn2pulse2.markerloc = 0
		chn2pulse2.create_sequence()

		chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
		chn2pulse3.delays = [0]
		chn2pulse3.heights = [1]
		chn2pulse3.widths = [params['repeat unit'].magnitude]
		chn2pulse3.totaltime = params['repeat unit'].magnitude 
		chn2pulse3width = 400e-9 
		chn2pulse3.nrepeats = 400e-9/params['repeat unit'].magnitude
		chn2pulse3.repeatstring = 'repeat'
		chn2pulse3.markerstring = 'lowAtStart'
		chn2pulse3.markerloc = 0
		chn2pulse3.create_sequence()

		chn2dc2 = Arbseq_Class('chn2dc2', timestep)
		chn2dc2.delays = [0]
		chn2dc2.heights = [-1]
		chn2dc2.widths = [params['repeat unit'].magnitude]
		chn2dc2.totaltime = params['repeat unit'].magnitude
		chn2dc2.repeatstring = 'repeat'
		chn2dc2.markerstring = 'lowAtStart'
		chn2dc2repeats = int((params['period'].magnitude-tau.magnitude-params['pulse width'].magnitude-chn2pulse3width)/(params['repeat unit'].magnitude))
		chn2dc2.nrepeats = chn2dc2repeats
		chn2dc2.markerloc = 0
		print((chn2dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
		chn2dc2.create_sequence()

		self.fungen.send_arb(chn1pulse, 1)
		self.fungen.send_arb(chn1dc, 1)
		self.fungen.send_arb(chn1pulse2, 1)
		self.fungen.send_arb(chn1pulse3, 1)
		self.fungen.send_arb(chn1dc2, 1)
		self.fungen.send_arb(chn2pulse1, 2)
		self.fungen.send_arb(chn2dc1, 2)
		self.fungen.send_arb(chn2pulse2, 2)
		self.fungen.send_arb(chn2pulse3, 2)
		self.fungen.send_arb(chn2dc2, 2)

		seq = [chn1pulse, chn1dc, chn1pulse2, chn1pulse3, chn1dc2]
		seq2 = [chn2pulse1, chn2dc1, chn2pulse2, chn2pulse3, chn2dc2]
		
		self.fungen.create_arbseq('twoPulse', seq, 1)
		self.fungen.create_arbseq('shutter', seq2, 2)
		self.fungen.wait()
		self.fungen.voltage[1] = params['pulse height'].magnitude+0.000000000001
		self.fungen.voltage[2] = 7.0+0.0000000000001
		
		print(self.fungen.voltage[1], self.fungen.voltage[2])
		self.fungen.output[1] = 'ON'
		self.fungen.output[2] = 'ON'
		#self.fungen.output[2] = 'OFF'
		self.fungen.trigger_delay(1,400e-9)
		self.fungen.sync()
			
		self.srs.module_reset[5]
		self.srs.SIM928_voltage[5]=params['srs bias'].magnitude
		self.srs.SIM928_on[5]



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
			print('Approx. ' + str(int((expparams['# of points']-i)/expparams['Measurement Time'].magnitude)) + ' min left')
			#self.fungen.voltage[2] = self.fungen.voltage[2].magnitude + 2*dcparams['DC step size'].magnitude

		self.fungen.output[1] = 'OFF'
		self.fungen.output[2] = 'OFF'
		startTime = time.time()
		startWl = self.wm.measure_wavelength()
		stoparray = []
		lastwls=[]
		while time.time()-startTime < expparams['Measurement Time'].magnitude:
			time.sleep(period)
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
			lastwls.append(str(self.wm.measure_wavelength()))
		self.createHistogram(stoparray, timebase, bincount, period,'bg', lastwls)

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')
		

	@Element(name='Pulse parameters')
	def pulse_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3, 'units':'V'}),
		('pulse width', {'type': float, 'default': 1000e-9, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('start tau', {'type': float, 'default': 2e-6, 'units':'s'}),
		('stop tau', {'type': float, 'default': 10e-6, 'units':'s'}),
		('step tau', {'type': float, 'default': 1e-6, 'units':'s'}),
		('srs bias', {'type': float, 'default': 1.2, 'units':'V'})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 10}),
		('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
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


