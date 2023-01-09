import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle # for saving large arrays
import math

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
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
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.thorlabs.pm100d import PM100D
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')
s = Q_(1,'s')

class PLThinFilm(Spyrelet):
	requires = {
		'wm': Bristol_771,
		'fungen': Keysight_33622A,
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

	def homelaser(self,start):
		current=self.wm.measure_wavelength()
		with Client(self.laser) as client:

			while current<start-0.001 or current>start+0.001:
				setting=client.get('laser1:ctl:wavelength-set', float)
				offset=current-start
				client.set('laser1:ctl:wavelength-set', setting-offset)
				time.sleep(5)
				current=self.wm.measure_wavelength()
				print(current, start, setting-offset)

	def createHistogram(self,stoparray,timebase, bincount, period,
		index, wls,out_name,extra_data=False):
		print('creating histogram')

		hist = [0]*bincount

		tstart=0
		for k in range(len(stoparray)):
				tdiff=stoparray[k]

				binNumber = int(tdiff*timebase*bincount/(period))
				"""
				print('tdiff: '+str(tdiff))
				print('binNumber: '+str(binNumber))
				print('stoparray[k]: '+str(stoparray[k]))
				print('tstart: '+str(tstart))
				"""
				if binNumber >= bincount:
					continue
				else:
					#print('binNumber: '+str(binNumber))
					hist[binNumber]+=1

		if extra_data==False:
			np.savez(os.path.join(out_name,str(index)),hist,wls)
		if extra_data!=False:
			np.savez(os.path.join(out_name,str(index)),hist,wls,extra_data)

		#np.savez(os.path.join(out_name,str(index+40)),hist,wls)
		print('Data stored under File Name: ' + out_name +'\\'+str(index)+'.npz')

	def resetTargets(self,targets,totalShift,i,channel):
		print('AWG limit exceeded, resetting voltage targets')

		# get the current wavelength
		current=self.wm.measure_wavelength()

		# adjust all targets to be lower again
		# reset totalShift
		print('totalShift: '+str(totalShift))
		newTargets=[j-totalShift for j in targets]
		print('newTargets')
		voltageTargets=newTargets
		totalShift=0

		# bring voltage back to ideal

		self.fungen.offset[channel]=Q_(voltageTargets[i-1],'V')
		# drive to last wavelength again
		#self.homelaser(current)
		wl=self.wm.measure_wavelength()
		return voltageTargets,totalShift,wl

	@Task()
	def startpulse(self, timestep=100e-9):

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		self.homelaser(wlparams['start'])
		print('Laser Homed!')

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		#ditherV=expparams['Dither Voltage'].magnitude
		print('here')

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']

		#self.fungen.voltage[1]=3.5
		#self.fungen.offset[1]=1.75
		#self.fungen.phase[1]=-3

		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']

		#self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'


		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="E:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="E:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],expparams['# of points'])

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

		#self.fungen.voltage[2]=ditherV
		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			print(i)
			#self.fungen.output[2]='OFF'

			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				wl=self.wm.measure_wavelength()

			"""
			while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)
					"""
			#self.fungen.output[2]='ON'

			print('taking data')
			print('current target wavelength: '+str(wlTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))

			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

			# open pickle files to save timestamp data

			# times=open(PATH+'\\'+str(i)+'_times.p','wb')
			# channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			# vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			synctimestamp=[]
			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				dataloss1 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss))

				dataloss2 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss2SS))

				# get the timestamps
				timestamps = self.qutag.getLastTimestamps(True)

				loopstart=time.time()

				time.sleep(2)

				dataloss1 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss))

				dataloss2 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss))

				# get the timestamps
				timestamps = self.qutag.getLastTimestamps(True)

				looptime+=time.time()-loopstart

				if dataloss1!=0:
					print('dataloss: '+str(dataloss1))

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps

				for k in range(values):
					# output all stop events together with the latest start event
					if tchannel[k] == 0:
						synctimestamp.append(tstamp[k])
						stoparray.append(False)
					else:
						#print('synctimestamp: '+str(synctimestamp))
						#print('stoptimestamp: '+str(stoptimestamp))
						synctimestamp.append(False)
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
						stopscheck.append(stoptimestamp)
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))

				#dump timestamp data to pickle file
				# pickle.dump(tstamp,times)
				# pickle.dump(tchannel,channels)
				# pickle.dump(values,vals)

				"""
				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					"""
				for k in range(len(stopscheck)):
					tdiff=stopscheck[k]
					binNumber = int(tdiff*timebase*bincount/(expparams['AWG Pulse Repetition Period'].magnitude))
					if binNumber<bincount:
						self.hist[binNumber]+=1
				stopscheck=[]

				values = {
					'x': self.bins,
					'y': self.hist,
				}

				self.startpulse.acquire(values)

			# very important to flush the buffer
			# if you don't do this, or don't close the files,
			# then data stored for writing will use up RAM space
			# and affect saving timestamps if the program is interrupted
			# times.flush()
			# channels.flush()
			# vals.flush()

			# close pickle files with timestamp data
			# times.close()
			# channels.close()
			# vals.close()

			#print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

	@Task()
	def darkcounts(self, timestep=100e-9):

		qutagparams = self.qutag_params.widget.get()

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="E:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="E:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

		print('taking data')

		time.sleep(1)
		##Wavemeter measurements
		stoparray = []
		startTime = time.time()
		wls=[]
		lost = self.qutag.getLastTimestamps(True)

		# open pickle files to save timestamp data

		times=open(PATH+'\\_times.p','wb')
		channels=open(PATH+'\\_channels.p','wb')
		vals=open(PATH+'\\_vals.p','wb')

		self.hist = [0]*bincount
		self.bins=list(range(len(self.hist)))
		stopscheck=[]

		synctimestamp=[]
		looptime=startTime
		while looptime-startTime < expparams['Measurement Time'].magnitude:
			dataloss1 = self.qutag.getDataLost()
			#print("dataloss: " + str(dataloss))

			dataloss2 = self.qutag.getDataLost()
			#print("dataloss: " + str(dataloss2SS))

			# get the timestamps
			timestamps = self.qutag.getLastTimestamps(True)

			loopstart=time.time()

			time.sleep(2)

			dataloss1 = self.qutag.getDataLost()
			#print("dataloss: " + str(dataloss))

			dataloss2 = self.qutag.getDataLost()
			#print("dataloss: " + str(dataloss))

			# get the timestamps
			timestamps = self.qutag.getLastTimestamps(True)

			looptime+=time.time()-loopstart

			if dataloss1!=0:
				print('dataloss: '+str(dataloss1))

			tstamp = timestamps[0] # array of timestamps
			tchannel = timestamps[1] # array of channels
			values = timestamps[2] # number of recorded timestamps

			for k in range(values):
				# output all stop events together with the latest start event
				if tchannel[k] == 0:
					synctimestamp.append(tstamp[k])
					stoparray.append(False)
				else:
					#print('synctimestamp: '+str(synctimestamp))
					#print('stoptimestamp: '+str(stoptimestamp))
					synctimestamp.append(False)
					stoptimestamp = tstamp[k]
					stoparray.append(stoptimestamp)
					stopscheck.append(stoptimestamp)

			#dump timestamp data to pickle file
			pickle.dump(tstamp,times)
			pickle.dump(tchannel,channels)
			pickle.dump(values,vals)

			for k in range(len(stopscheck)):
				tdiff=stopscheck[k]
				binNumber = int(tdiff*timebase*bincount/(expparams['AWG Pulse Repetition Period'].magnitude))
				if binNumber<bincount:
					self.hist[binNumber]+=1
			stopscheck=[]

			values = {
				'x': self.bins,
				'y': self.hist,
			}

			self.darkcounts.acquire(values)

		times.flush()
		channels.flush()
		vals.flush()

		# close pickle files with timestamp data
		times.close()
		channels.close()
		vals.close()

		self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

	# the 1D plot widget is used for the live histogram
	@Element(name='Histogram')
	def Histogram(self):
		p = LinePlotWidget()
		p.plot('Histogram')
		return p

	# more code for the histogram plot
	@Histogram.on(startpulse.acquired)
	def _Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('Histogram',xs=xs,ys=ys)
		return

	# the 1D plot widget is used for the live histogram
	@Element(name='dark count Histogram')
	def dc_Histogram(self):
		p = LinePlotWidget()
		p.plot('dark count Histogram')
		return p

	# more code for the histogram plot
	@dc_Histogram.on(darkcounts.acquired)
	def _dc_Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('dark count Histogram',xs=xs,ys=ys)
		return

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		# ('start', {'type': float, 'default': 1535.665}),
		('start', {'type': float, 'default': 1535.90}),
		('stop', {'type': float, 'default':  1535.90})
		# ('stop', {'type': float, 'default': 1535.61})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 1}),
		('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 0.05,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 200e-6,'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 4}),
		('Bin Count', {'type': int, 'default': 1000}),
		('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		('Battery Port 1',{'type':int,'default':5}),
		('Battery Port 2',{'type':int,'default':6})
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
