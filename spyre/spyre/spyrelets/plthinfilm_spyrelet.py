##Script that automatically does PL measurements by adjusting the laser frequency
##This measurement applies long excitation pulses up to 100 us
##Chnl sends the excitation pulse, and sync the delay generator to drive the optical switch as a shutter

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
from lantz.drivers.SRS import DG645 
from toptica.lasersdk.client import NetworkConnection, Client

class PLThinFilm(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'wm': Bristol_771,
		'dg': DG645
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
		out_name = "D:\\Data\\9.04.2019\\0"
		np.savez(os.path.join(out_name,str(index)),hist,wls)
		#np.savez(os.path.join(out_name,str(index+40)),hist,wls)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))


	@Task()
	def startpulse(self, timestep=100e-9):
		params = self.pulse_parameters.widget.get()
		period = params['period'].magnitude
		repeat_unit = params['repeat unit'].magnitude
		pulse_width = params['pulse width'].magnitude
		pulse_height = params['pulse height'].magnitude

		self.configureQutag()
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
		chn1buffer.widths = [10e-6]
		chn1buffer.totaltime = 10e-6
		chn1buffer.repeatstring = 'once'
		chn1buffer.markerstring = 'highAtStartGoLow'
		chn1buffer.markerloc = 0
		chn1bufferwidth = 10e-6
		chn1buffer.create_sequence()

		chn1buffer2 = Arbseq_Class('chn1buffer2', timestep)
		chn1buffer2.delays = [0]
		chn1buffer2.heights = [0]
		chn1buffer2.widths = [10e-6]
		chn1buffer2.totaltime = 10e-6
		chn1buffer2.nrepeats = 50 #buffer time 5000*100e-9=500 us
		chn1buffer2width=chn1buffer2.nrepeats*10e-6
		chn1buffer2.repeatstring = 'repeat'
		chn1buffer2.markerstring = 'lowAtStart'
		chn1buffer2.markerloc = 0
		chn1buffer2.create_sequence()

		chn1pulse = Arbseq_Class('chn1pulse', timestep)
		chn1pulse.delays = [0]
		chn1pulse.heights = [1]
		chn1pulse.widths = [50e-6]
		chn1pulse.totaltime = 50e-6
		chn1pulse.repeatstring = 'once'
		chn1pulsewidth=50e-6 #pulse width 100 us
		chn1pulse.markerstring = 'lowAtStart'
		chn1pulse.markerloc = 0
		chn1pulse.create_sequence()


		chn1buffer3 = Arbseq_Class('chn1buffer3', timestep)
		chn1buffer3.delays = [0]
		chn1buffer3.heights = [0]
		chn1buffer3.widths = [10e-6]
		chn1buffer3.totaltime = 10e-6
		chn1buffer3.nrepeats = 20 #buffer time 200 us used for the optical switch rising time
		chn1buffer3width=chn1buffer3.nrepeats*10e-6
		chn1buffer3.repeatstring = 'repeat'
		chn1buffer3.markerstring = 'lowAtStart'
		chn1buffer3.markerloc = 0
		chn1buffer3.create_sequence()

		
		chn1dc = Arbseq_Class('chn1dc', timestep)
		chn1dc.delays = [0]
		chn1dc.heights = [0]
		chn1dc.widths = [10e-6]
		chn1dc.totaltime = 10e-6
		chn1dc.repeatstring = 'repeat'
		chn1dc.markerstring = 'lowAtStart'
		chn1dcrepeats = int((period-chn1bufferwidth-chn1buffer2width-chn1pulsewidth-chn1buffer3width)/(10e-6))
		chn1dc.nrepeats=chn1dcrepeats
		chn1dc.markerloc = 0
		chn1dc.create_sequence()

		self.fungen.send_arb(chn1buffer, 1)
		self.fungen.send_arb(chn1buffer2, 1)
		self.fungen.send_arb(chn1pulse, 1)
		self.fungen.send_arb(chn1buffer3, 1)
		self.fungen.send_arb(chn1dc, 1)

		seq1 = [chn1buffer, chn1buffer2, chn1pulse, chn1buffer3, chn1dc]
		
		self.fungen.create_arbseq('pulse', seq1, 1)
		self.fungen.wait()
		self.fungen.voltage[1] = pulse_height

		##setting the delay generator
		self.dg.Trigger_Source = 'External rising edges'
		self.dg.Delay_Channel[2] = 0
		self.dg.Delay_Channel[3] = chn1bufferwidth+chn1buffer2width+chn1pulsewidth+chn1buffer3width
		self.dg.Delay_Channel[4] = chn1bufferwidth+chn1buffer2width+chn1pulsewidth+chn1buffer3width
		self.dg.Delay_Channel[5] = period - (chn1bufferwidth+chn1buffer2width+chn1pulsewidth)

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		self.homelaser(wlparams['start'])
		print('Laser Homed!')
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
				time.sleep(5*period)
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
				client.set('laser1:ctl:wavelength-set', setting-0.0048)
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
		('pulse width', {'type': float, 'default': 100e-6, 'units':'s'}),
		('period', {'type': float, 'default': 0.1, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 100e-9, 'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('start', {'type': float, 'default': 1535.74}),
		('stop', {'type': float, 'default': 1535.50})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 50}),
		('Measurement Time', {'type': int, 'default': 100, 'units':'s'}),
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


