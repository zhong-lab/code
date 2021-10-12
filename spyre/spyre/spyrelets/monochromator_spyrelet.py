<<<<<<< HEAD
<<<<<<< HEAD
from PyQt5 import QtWidgets
import pyqtgraph as pg
import itertools as it
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

import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments import SpectraPro
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

from lantz import Q_

class MonochromatorSpyrelet(Spyrelet):

	requires = {
		'wm': Bristol_771,
		'fungen': Keysight_33622A,
		'SRS': SRS900,
		'sp': SpectraPro,
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

	@Task()
	def reset_quench(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs1]='ON'
		self.SRS.SIM928_on_off[vs2]='ON'

		return None

	@Task()
	def turn_off_SNSPD(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

		return None
	@Task()
	def scan2D(self, timestep=100e-9):

		self.fungen.output[2]='OFF'
		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']
		self.SRS.clear_status()
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		laserst=wlparams['Laser wavelength start']
		lasersp=wlparams['Laser wavelength stop']
		self.homelaser(laserst)
		print('Laser Homed!')

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.output[1]='ON'
		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],
			expparams['# of spectrometer points'])
		laserTargets=np.linspace(laserst,lasersp,expparams['# of laser points'])
		
		wlTargets=[i-0.605 for i in wlTargets]
		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				2.5*expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))
		print('wlTargets: '+str(wlTargets))
		with Client(self.laser) as client:
			setting=client.get('laser1:ctl:wavelength-set', float)

			client.set('laser1:ctl:wavelength-set', laserst)
			wl=self.wm.measure_wavelength()
			while ((wl<laserst-0.001) or (wl>laserst+0.001)):
					print('correcting for laser drift')
					self.homelaser(laserst)
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(laserst))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)

		# set the grating to #2 - 600g/mm
		self.sp.set_grating(2)
		print('current grating: '+str(self.sp.get_grating()))

		self.wls=wlTargets
		self.spec=[0]*expparams['# of spectrometer points']
		self.image = np.zeros((expparams['# of laser points'],expparams['# of spectrometer points']),dtype=float)

		for j in range(expparams['# of laser points']):

			for i in range(expparams['# of spectrometer points']):
				print(i)
				print('taking data')
				print('current target laser wavelength: '+str(j))
				with Client(self.laser) as client:
					setting=client.get('laser1:ctl:wavelength-set', float)
					client.set('laser1:ctl:wavelength-set', laserTargets[j])
					wl=self.wm.measure_wavelength()
					while ((wl<laserTargets[j]-0.001) or (wl>laserTargets[j]+0.001)):
							print('correcting for laser drift')
							self.homelaser(laserTargets[j])
							wl=self.wm.measure_wavelength()
							print('current target wavelength: '+str(laserTargets[j]))
							print('actual wavelength: '+str(self.wm.measure_wavelength()))
							time.sleep(1)

				print('current target spectrometer wavelength: '+str(wlTargets[i]))
				self.sp.set_wavelength(float(wlTargets[i]))
				print('actual spectrometer wavelength: '+str(self.sp.get_wavelength()))
				time.sleep(1)

				##Wavemeter measurements
				stoparray = []
				startTime = time.time()

				lwls=[]
				wls=[]

				lost = self.qutag.getLastTimestamps(True)
				# open pickle files to save timestamp data
				times=open(PATH+'\\'+str(j)+'_'+str(i)+'_times.p','wb')
				channels=open(PATH+'\\'+str(j)+'_'+str(i)+'_channels.p','wb')
				vals=open(PATH+'\\'+str(j)+'_'+str(i)+'_vals.p','wb')

				self.hist = [0]*bincount
				self.bins=list(range(len(self.hist)))
				stopscheck=[]
				synctimestamp=[]
				looptime=startTime
				while looptime-startTime < expparams['Measurement Time'].magnitude:
					dataloss1 = self.qutag.getDataLost()
					dataloss2 = self.qutag.getDataLost()
					# get the timestamps
					timestamps = self.qutag.getLastTimestamps(True)
					loopstart=time.time()
					time.sleep(2)
					dataloss1 = self.qutag.getDataLost()
					dataloss2 = self.qutag.getDataLost()
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
							synctimestamp.append(False)
							stoptimestamp = tstamp[k]
							stoparray.append(stoptimestamp)
							stopscheck.append(stoptimestamp)

					wl=self.sp.get_wavelength()
					wls.append(str(wl))
					lwl=self.wm.measure_wavelength()
					lwls.append(str(lwl))

					#dump timestamp data to pickle file
					pickle.dump(tstamp,times)
					pickle.dump(tchannel,channels)
					pickle.dump(values,vals)

					while ((lwl<laserTargets[j]-0.001) or (lwl>laserTargets[j]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
						print('correcting for laser drift')
						self.homelaser(laserTargets[j])
						lwl=self.wm.measure_wavelength()

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
					self.scan2D.acquire(values)
				times.flush()
				channels.flush()
				vals.flush()
				# close pickle files with timestamp data
				times.close()
				channels.close()
				vals.close()

				self.createHistogram(stoparray,timebase, bincount, 
					expparams['AWG Pulse Repetition Period'].magnitude,str(j)+'_'+str(i),
					wls,PATH)

				spec=sum([float(i-np.mean(self.hist[-40:])) for i in self.hist[(self.cutoff):]])
				if spec>0:
					self.spec[i]=spec
				else:
					self.spec[i]=0
				self.image[j,i]=self.spec[i] #j is the row, # i is the column
				spectrumvalues={
					'x': [i+0.605 for i in self.wls],
					'y': self.spec,
					'image':self.image
				}
				self.scan2D.acquire(spectrumvalues)

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

	@Task()
	def monoscan(self, timestep=100e-9):

		self.fungen.output[2]='OFF'
		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		laserWL=wlparams['Laser wavelength start']
		self.homelaser(laserWL)
		print('Laser Homed!')

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.output[1]='ON'

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],
			expparams['# of spectrometer points'])
		wlTargets=[i-0.605 for i in wlTargets]

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				2.5*expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

		print('wlTargets: '+str(wlTargets))

		
		with Client(self.laser) as client:
			setting=client.get('laser1:ctl:wavelength-set', float)
			client.set('laser1:ctl:wavelength-set', laserWL)
			wl=self.wm.measure_wavelength()
			while ((wl<laserWL-0.001) or (wl>laserWL+0.001)):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(laserWL))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)
		#print('here')

		# set the grating to #2 - 600g/mm
		self.sp.set_grating(2)
		print('current grating: '+str(self.sp.get_grating()))

		self.wls=wlTargets
		self.spec=[0]*expparams['# of spectrometer points']

		#print('here2')
		for i in range(expparams['# of spectrometer points']):
			print(i)
			print('taking data')
			print('current target laser wavelength: '+str(laserWL))
			#print('actual laser wavelength: '+str(self.wm.measure_wavelength())
			print('current target spectrometer wavelength: '+str(wlTargets[i]))
			self.sp.set_wavelength(float(wlTargets[i]))
			print('actual spectrometer wavelength: '+str(self.sp.get_wavelength()))
			#print('actual spectrometer wavelength: '+str(self.sp.wavelength))
			time.sleep(1)

			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

			# open pickle files to save timestamp data
			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			synctimestamp=[]
			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

				# get the timestamps
				timestamps = self.qutag.getLastTimestamps(True)

				loopstart=time.time()

				time.sleep(2)

				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

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
						synctimestamp.append(False)
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
						stopscheck.append(stoptimestamp)
				wl=self.sp.get_wavelength()
				lwl=self.wm.measure_wavelength()
				wls.append(str(wl))

				#dump timestamp data to pickle file
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)

				while ((lwl<laserWL-0.001) or (lwl>laserWL+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					lwl=self.wm.measure_wavelength()

				for k in range(len(stopscheck)):
					tdiff=stopscheck[k]
					binNumber = int(tdiff*timebase*bincount/(expparams['AWG Pulse Repetition Period'].magnitude))
					if binNumber<bincount:
						self.hist[binNumber]+=1
				stopscheck=[]

				values = {
					'x': self.bins,
					'y': self.hist
				}
				self.monoscan.acquire(values)
				#print('here')

			times.flush()
			channels.flush()
			vals.flush()
			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

			self.spec[i]=sum(self.hist[(self.cutoff):])
			spectrumvalues={
				'x': self.wls,
				'y': self.spec
			}
			self.monoscan.acquire(spectrumvalues)

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

	@Task()
	def darkcounts(self, timestep=100e-9):

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
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
				2.5*expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

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
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

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

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
			('start', {'type': float, 'default': 1535.90}),
			('stop', {'type': float, 'default':  1535.90}),
			('Laser wavelength start',{'type':float,'default':1520}),
			('Laser wavelength stop',{'type':float,'default':1550})

		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
			('# of spectrometer points', {'type': int, 'default': 100}),
			('# of laser points',{'type':int,'default':10}),
			('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
			('File Name', {'type': str}),
			('AWG Pulse Repetition Period',{'type': float,'default': 0.05,'units':'s'}),
			('AWG Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
			('AWG Pulse Width',{'type': float,'default': 200e-6,'units':'s'}),
			('Dither Voltage',{'type':float,'default':2,'units':'V'})
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
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

	# this task gets the current voltage of the SRS voltmeter
	@Task(name = 'Voltmeter')
	def Voltmeter(self):
		while True:
			qutagparams = self.qutag_params.widget.get()
			self.vm1=qutagparams['Voltmeter Channel 1']
			self.vm2=qutagparams['Voltmeter Channel 2']
			self.v1=float(self.SRS.SIM970_voltage[self.vm1].magnitude)
			self.v2=float(self.SRS.SIM970_voltage[self.vm2].magnitude)
			# don't really understand the point of acquiring the "values"
			values = {
				'vm1': self.v1,
				'vm2': self.v2
			}
			self.Voltmeter.acquire(values)
			time.sleep(0.05)
		return

	# sets up some formatting
	@Element(name='indicator')
	def voltmeter_now(self):
		text = QTextEdit()
		text.setPlainText('Voltage 1: non V \nVoltage 2: non V\n')
		return text

	# more formatting
	@voltmeter_now.on(Voltmeter.acquired)
	def _voltmeter_now_update(self,ev):
		w=ev.widget
		w.setPlainText('Voltage 1: %f V \nVoltage 2: %f V \n'%(self.v1,self.v2))
		return

	# the 1D plot widget is used for the live histogram
	@Element(name='Histogram')
	def Histogram(self):
		p = LinePlotWidget()
		p.plot('Histogram')
		p.xlabel = "bin"
		p.ylabel = "counts"
		return p

	# more code for the histogram plot
	@Histogram.on(scan2D.acquired)
	@Histogram.on(monoscan.acquired)
	@Histogram.on(darkcounts.acquired)
	def _Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('Histogram',xs=xs,ys=ys)
		return

	@Element(name='Latest Spectrum')
	def spectrum(self):
		p = LinePlotWidget()
		p.plot('Spectrum')
		p.xlabel = "Wavelength (nm)"
		p.ylabel = "Intensity"
		return p

	@spectrum.on(scan2D.acquired)
	@spectrum.on(monoscan.acquired)
	def _spectrum_update(self, ev):
		w = ev.widget
		xs = np.array(self.wls)
		ys = np.array(self.spec)
		w.set('Spectrum', xs=xs, ys=ys)
		return

	@Element()
	def save(self):
		w = RepositoryWidget(self)
		return w

	#  define 2D plot
	@Element(name='2D plot')
	def plot2d(self):
		p = HeatmapPlotWidget()
		return p

	# updates the 2D plot
	@plot2d.on(scan2D.acquired)
	def _plot2d_update(self, ev):
		w = ev.widget
		im = np.array(self.image)
		# not sure what the "set" function does
		w.set(im)
		return
=======
from PyQt5 import QtWidgets
import pyqtgraph as pg
import itertools as it
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

import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments import SpectraPro
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

from lantz import Q_

class MonochromatorSpyrelet(Spyrelet):

    requires = {
        'wm': Bristol_771,
		'fungen': Keysight_33622A,
		'SRS': SRS900,
        'sp': SpectraPro,
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

    @Task()
	def reset_quench(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs1]='ON'
		self.SRS.SIM928_on_off[vs2]='ON'

		return None

	@Task()
	def turn_off_SNSPD(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

		return None

    @Task()
	def monoscan(self, timestep=100e-9):

		self.fungen.output[2]='OFF'
		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
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

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.output[1]='ON'

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],
            expparams['# of points'])

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

		print('wlTargets: '+str(wlTargets))

        laserWL=wlparams['Laser wavelength']
        with Client(self.laser) as client:
            setting=client.get('laser1:ctl:wavelength-set', float)
            client.set('laser1:ctl:wavelength-set', laserWL)
            wl=self.wm.measure_wavelength()
            while ((wl<laserWL-0.001) or (wl>laserWL+0.001)):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(laserWL))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)

        for i in range(expparams['# of points']):
			print(i)
			print('taking data')
			print('current target laser wavelength: '+str(laserWL)
			print('actual laser wavelength: '+str(self.wm.measure_wavelength())
            print('current target spectrometer wavelength: '+str(wlTargets[i])
			print('actual spectrometer wavelength: '+str(self.sp.wavelength)
			time.sleep(1)

			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

			# open pickle files to save timestamp data
			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

            self.wls=wlTargets
            self.spec=[0]*expparams['# of points']
			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			synctimestamp=[]
			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

				# get the timestamps
				timestamps = self.qutag.getLastTimestamps(True)

				loopstart=time.time()

				time.sleep(2)

				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

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
						synctimestamp.append(False)
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
						stopscheck.append(stoptimestamp)
				wl=self.sp.wavelength
				wls.append(str(wl))

				#dump timestamp data to pickle file
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)

				while ((wl<laserWL-0.001) or (wl>laserWL+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					wl=self.wm.measure_wavelength()

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

			times.flush()
			channels.flush()
			vals.flush()
			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

            self.spec[i]=sum(self.hist[(self.cutoff+1):])
            spectrumvalues={
                'x': self.wls,
                'y': self.spec
            }

            self.monoscan.acquire(values)

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

	@Task()
	def darkcounts(self, timestep=100e-9):

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
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
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

    @Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
    		('start', {'type': float, 'default': 1535.90}),
    		('stop', {'type': float, 'default':  1535.90}),
            ('Laser wavelength',{'type':float,'default':1535})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
    		('# of points', {'type': int, 'default': 1}),
    		('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
    		('File Name', {'type': str}),
    		('AWG Pulse Repetition Period',{'type': float,'default': 0.05,'units':'s'}),
    		('AWG Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
    		('AWG Pulse Width',{'type': float,'default': 200e-6,'units':'s'}),
    		('Dither Voltage',{'type':float,'default':2,'units':'V'})
		]
		w = ParamWidget(params)
		return w

    @Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
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

    # this task gets the current voltage of the SRS voltmeter
	@Task(name = 'Voltmeter')
	def Voltmeter(self):
		while True:
			qutagparams = self.qutag_params.widget.get()
			self.vm1=qutagparams['Voltmeter Channel 1']
			self.vm2=qutagparams['Voltmeter Channel 2']
			self.v1=float(self.SRS.SIM970_voltage[self.vm1].magnitude)
			self.v2=float(self.SRS.SIM970_voltage[self.vm2].magnitude)
			# don't really understand the point of acquiring the "values"
			values = {
				'vm1': self.v1,
				'vm2': self.v2
			}
			self.Voltmeter.acquire(values)
			time.sleep(0.05)
		return

    # sets up some formatting
	@Element(name='indicator')
	def voltmeter_now(self):
		text = QTextEdit()
		text.setPlainText('Voltage 1: non V \nVoltage 2: non V\n')
		return text

	# more formatting
	@voltmeter_now.on(Voltmeter.acquired)
	def _voltmeter_now_update(self,ev):
		w=ev.widget
		w.setPlainText('Voltage 1: %f V \nVoltage 2: %f V \n'%(self.v1,self.v2))
		return

    # the 1D plot widget is used for the live histogram
	@Element(name='Histogram')
	def Histogram(self):
		p = LinePlotWidget()
		p.plot('Histogram')
        p.xlabel = "bin"
        p.ylabel = "counts"
		return p

	# more code for the histogram plot
	@Histogram.on(monoscan.acquired)
    @Histogram.on(darkcounts.acquired)
	def _Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('Histogram',xs=xs,ys=ys)
		return

    @Element(name='Latest Spectrum')
    def spectrum(self):
        p = LinePlotWidget()
        p.plot('Spectrum')
        p.xlabel = "Wavelength (nm)"
        p.ylabel = "Intensity"
        return p

    @spectrum.on(monoscan.acquired)
    def spectrum_update(self, ev):
        w = ev.widget
        try:
            xs = np.array(self.wls)
    		ys = np.array(self.spec)
            w.set('Spectrum', xs=self.wl, ys=latest_data)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
=======
from PyQt5 import QtWidgets
import pyqtgraph as pg
import itertools as it
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

import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments import SpectraPro
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

from lantz import Q_

class MonochromatorSpyrelet(Spyrelet):

    requires = {
        'wm': Bristol_771,
		'fungen': Keysight_33622A,
		'SRS': SRS900,
        'sp': SpectraPro,
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

    @Task()
	def reset_quench(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs1]='ON'
		self.SRS.SIM928_on_off[vs2]='ON'

		return None

	@Task()
	def turn_off_SNSPD(self):
		#A typical quench shows the voltage exceeding 3mV.

		qutagparams = self.qutag_params.widget.get()
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

		return None

    @Task()
	def monoscan(self, timestep=100e-9):

		self.fungen.output[2]='OFF'
		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
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

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.output[1]='ON'

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],
            expparams['# of points'])

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				expparams['AWG Pulse Width'].magnitude/expparams['AWG Pulse Repetition Period'].magnitude*bins))

		print('wlTargets: '+str(wlTargets))

        laserWL=wlparams['Laser wavelength']
        with Client(self.laser) as client:
            setting=client.get('laser1:ctl:wavelength-set', float)
            client.set('laser1:ctl:wavelength-set', laserWL)
            wl=self.wm.measure_wavelength()
            while ((wl<laserWL-0.001) or (wl>laserWL+0.001)):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(laserWL))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)

        for i in range(expparams['# of points']):
			print(i)
			print('taking data')
			print('current target laser wavelength: '+str(laserWL)
			print('actual laser wavelength: '+str(self.wm.measure_wavelength())
            print('current target spectrometer wavelength: '+str(wlTargets[i])
			print('actual spectrometer wavelength: '+str(self.sp.wavelength)
			time.sleep(1)

			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

			# open pickle files to save timestamp data
			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

            self.wls=wlTargets
            self.spec=[0]*expparams['# of points']
			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			synctimestamp=[]
			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

				# get the timestamps
				timestamps = self.qutag.getLastTimestamps(True)

				loopstart=time.time()

				time.sleep(2)

				dataloss1 = self.qutag.getDataLost()
				dataloss2 = self.qutag.getDataLost()

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
						synctimestamp.append(False)
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
						stopscheck.append(stoptimestamp)
				wl=self.sp.wavelength
				wls.append(str(wl))

				#dump timestamp data to pickle file
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)

				while ((wl<laserWL-0.001) or (wl>laserWL+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(laserWL)
					wl=self.wm.measure_wavelength()

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

			times.flush()
			channels.flush()
			vals.flush()
			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

            self.spec[i]=sum(self.hist[(self.cutoff+1):])
            spectrumvalues={
                'x': self.wls,
                'y': self.spec
            }

            self.monoscan.acquire(values)

		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

	@Task()
	def darkcounts(self, timestep=100e-9):

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="Q:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\":
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
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'

    @Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
    		('start', {'type': float, 'default': 1535.90}),
    		('stop', {'type': float, 'default':  1535.90}),
            ('Laser wavelength',{'type':float,'default':1535})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
    		('# of points', {'type': int, 'default': 1}),
    		('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
    		('File Name', {'type': str}),
    		('AWG Pulse Repetition Period',{'type': float,'default': 0.05,'units':'s'}),
    		('AWG Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
    		('AWG Pulse Width',{'type': float,'default': 200e-6,'units':'s'}),
    		('Dither Voltage',{'type':float,'default':2,'units':'V'})
		]
		w = ParamWidget(params)
		return w

    @Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
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

    # this task gets the current voltage of the SRS voltmeter
	@Task(name = 'Voltmeter')
	def Voltmeter(self):
		while True:
			qutagparams = self.qutag_params.widget.get()
			self.vm1=qutagparams['Voltmeter Channel 1']
			self.vm2=qutagparams['Voltmeter Channel 2']
			self.v1=float(self.SRS.SIM970_voltage[self.vm1].magnitude)
			self.v2=float(self.SRS.SIM970_voltage[self.vm2].magnitude)
			# don't really understand the point of acquiring the "values"
			values = {
				'vm1': self.v1,
				'vm2': self.v2
			}
			self.Voltmeter.acquire(values)
			time.sleep(0.05)
		return

    # sets up some formatting
	@Element(name='indicator')
	def voltmeter_now(self):
		text = QTextEdit()
		text.setPlainText('Voltage 1: non V \nVoltage 2: non V\n')
		return text

	# more formatting
	@voltmeter_now.on(Voltmeter.acquired)
	def _voltmeter_now_update(self,ev):
		w=ev.widget
		w.setPlainText('Voltage 1: %f V \nVoltage 2: %f V \n'%(self.v1,self.v2))
		return

    # the 1D plot widget is used for the live histogram
	@Element(name='Histogram')
	def Histogram(self):
		p = LinePlotWidget()
		p.plot('Histogram')
        p.xlabel = "bin"
        p.ylabel = "counts"
		return p

	# more code for the histogram plot
	@Histogram.on(monoscan.acquired)
    @Histogram.on(darkcounts.acquired)
	def _Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('Histogram',xs=xs,ys=ys)
		return

    @Element(name='Latest Spectrum')
    def spectrum(self):
        p = LinePlotWidget()
        p.plot('Spectrum')
        p.xlabel = "Wavelength (nm)"
        p.ylabel = "Intensity"
        return p

    @spectrum.on(monoscan.acquired)
    def spectrum_update(self, ev):
        w = ev.widget
        try:
            xs = np.array(self.wls)
    		ys = np.array(self.spec)
            w.set('Spectrum', xs=self.wl, ys=latest_data)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
