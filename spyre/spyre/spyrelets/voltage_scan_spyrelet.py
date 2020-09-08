##Script that automatically does PL measurements by adjusting the laser frequency
##This measurement applies long excitation pulses up to 100 us
##Chnl sends the excitation pulse, and sync the delay generator to drive the optical switch as a shutter

import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path

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


from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client

class PLThinFilm(Spyrelet):
	requires = {
		'wm': Bristol_771
	}
	qutag = None
	laser = NetworkConnection('1.1.1.2')



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
		print('creating histogram')
		hist = [0]*bincount
		for stoptime in stoparray:
			# stoptime=ps
			# timebase = converts to seconds
			# bincount: # of bins specified by user
			# period: measurement time specified by user
			binNumber = int(stoptime*timebase*bincount/(period))
			if binNumber >= bincount:
				continue
			else:
				hist[binNumber]+=1
		out_name = "D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		np.savez(os.path.join(out_name,str(index)),hist,wls)
		#np.savez(os.path.join(out_name,str(index+40)),hist,wls)
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))


	@Task()
	def startpulse(self, timestep=100e-9):

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		self.homelaser(wlparams['start'])
		print('Laser Homed!')
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)
		#os.mkdir(PATH)

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],expparams['# of points'])
		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			print(i)
			with Client(self.laser) as client:
				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				print('current target wavelength: '+str(wlTargets[i]))
				print('actual wavelength: '+str(self.wm.measure_wavelength()))
				time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			while time.time()-startTime < expparams['Measurement Time'].magnitude:
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(5*0.1)
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

			self.createHistogram(stoparray, timebase, bincount,expparams['AWG Pulse Repetition Period'].magnitude,i, wls)
			

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('start', {'type': float, 'default': 1535.71}),
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
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 0.01,'units':'s'})
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Bin Count', {'type': int, 'default': 1000})
		]
		w = ParamWidget(params)
		return w

	@startpulse.initializer
	def initialize(self):
		self.wm.start_data()

	@startpulse.finalizer
	def finalize(self):
		self.wm.stop_data()
		print('Lifetime measurements complete.')
		return

	@qutagInit.initializer
	def initialize(self):
		from lantz.drivers.qutools import QuTAG
		self.qutag = QuTAG()
		devType = self.qutag.getDeviceType()
		print('devType: '+str(devType))
		if (devType == self.qutag.DEVTYPE_QUTAG):
			print("found quTAG!")
		else:
			print("no suitable device found - demo mode activated")
		print("Device timebase:" + str(self.qutag.getTimebase()))
		return

	@qutagInit.finalizer
	def finalize(self):
		return


