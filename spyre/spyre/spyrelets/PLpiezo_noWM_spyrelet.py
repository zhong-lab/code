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

from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.stanford import DG645

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

class PLThinFilm(Spyrelet):
	requires = {
		'fungen': Keysight_33622A
		#'delaygen': DG645
	}
	qutag = None
	laser = NetworkConnection('1.1.1.2')
	xs=np.array([])
	ys=np.array([])
	hist=[]

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))

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
				print('error')
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
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)
		#os.mkdir(PATH)

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],expparams['# of points'])
		

		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			
			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			counter2=0

			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				loopstart=time.time()
				# get the lost timestamps
				lost = self.qutag.getLastTimestamps(True)
				# wait half a milisecond
				time.sleep(5*0.1)
				# get thte timestamps in the last half milisecond
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
				looptime+=time.time()-loopstart

			self.createHistogram(stoparray, timebase, bincount,expparams['AWG Pulse Repetition Period'].magnitude,i,wls)
			

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('start', {'type': float, 'default': 1535}),
		('stop', {'type': float, 'default': 1536})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Piezo scan parameters')
	def piezo_parameters(self):
		params=[
			('voltage start',{'type': float,'default':-3,'units':'V'}),
			('voltage end',{'type': float,'default':3,'units':'V'}),
			('scan points',{'type':int,'default':100}),
			('AWG channel',{'type':int,'default':0}),
			('Scale factor',{'type':float,'default':2})
		]
		w=ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 100}),
		('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
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
		return

	@startpulse.finalizer
	def finalize(self):
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