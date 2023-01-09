<<<<<<< HEAD
<<<<<<< HEAD
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
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

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
		'SRS': SRS900
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
				time.sleep(3)
				current=self.wm.measure_wavelength()
				print(current, start)

	def createHistogram(self,stoparray, timebase, bincount, period, index, wls,out_name,extra_data=False):
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
		self.homelaser(current)
		wl=self.wm.measure_wavelength()
		return voltageTargets,totalShift,wl

	def reset_quench(self):
		"""
		A typical quench shows the voltage exceeding 2mV.
		"""
		qutagparams = self.qutag_params.widget.get()
		# vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		# vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		# self.SRS.clear_status()
		# V1=self.SRS.SIM970_voltage[vm1].magnitude
		self.SRS.clear_status()
		V2=self.SRS.SIM970_voltage[vm2].magnitude

		quenchfix='YES'

		# i=0
		# while (float(V1)>=0.010):
		# 	i+=1
		# 	print('Voltage 1 higher than 10mV, resetting')
		# 	self.SRS.SIM928_on_off[vs1]='OFF'
		# 	self.SRS.SIM928_on_off[vs2]='OFF'
		# 	self.SRS.SIM928_on_off[vs1]='ON'
		# 	self.SRS.SIM928_on_off[vs2]='ON'
		# 	print('checking Voltage 1 again')
		# 	self.SRS.clear_status()
		# 	time.sleep(1)
		# 	V1=self.SRS.SIM970_voltage[vm1].magnitude
		# 	print('Voltage 1: '+str(V1)+'V')
		# 	if i>10:
		# 		self.fungen.output[1]='OFF'
		# 		self.fungen.output[2]='OFF'
		# 		quenchfix='NO'
		# 		break

		i=0
		while (float(V2)>=0.010):
			i+=1
			print('Voltage 2 higher than 10mV, resetting')
			self.SRS.SIM928_on_off[vs1]='OFF'
			self.SRS.SIM928_on_off[vs2]='OFF'
			self.SRS.SIM928_on_off[vs1]='ON'
			self.SRS.SIM928_on_off[vs2]='ON'
			print('checking Voltage 2 again')
			self.SRS.clear_status()
			time.sleep(1)
			V2=self.SRS.SIM970_voltage[vm2].magnitude
			print('Voltage 2: '+str(V2)+'V')
			if i>10:
				self.fungen.output[1]='OFF'
				self.fungen.output[2]='OFF'
				quenchfix='NO'
				break
		return quenchfix
	
	@Task()
	def piezo_scan(self,timestep=100e-9):
		
		#self.fungen.output[1]='ON'
		piezo_params=self.piezo_parameters.widget.get()
		Vstart=piezo_params['voltage start']
		Vstop=piezo_params['voltage end']
		pts=piezo_params['scan points']

		voltageTargets=np.linspace(Vstart,Vstop,pts)
		reversedTargets=voltageTargets[::-1]
		voltageTargets=reversedTargets

		print('voltageTargets: '+str(voltageTargets))


		channel=piezo_params['AWG channel']

		# turn off AWG
		self.fungen.output[channel]='OFF'

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		# drive to the offset estimated by the piezo voltage
		# 1MOhm impedance of laser mismatch with 50Ohm impedance of AWG
		# multiplies voltage 2x
		# 140V ~ 40GHz ~ 315pm

		piezo_range=(Vstop.magnitude-Vstart.magnitude)*0.315/(140)*piezo_params['Scale factor'] #pm
		print('piezo_range: '+str(piezo_range)+str(' nm'))

		wl_start=wlparams['start']-piezo_range
		wl_stop=wlparams['stop']+piezo_range
		wlpts=np.linspace(wl_start,wl_stop,pts)

		self.homelaser(wlparams['start']-piezo_range)
		print('Laser Homed!')
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\"+self.exp_parameters.widget.get()['File Name']

		if PATH!="C:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# turn on AWG
		self.fungen.output[channel]='ON'

		last_wl=self.wm.measure_wavelength()
		wls=[]
		totalShift=0

		for i in range(pts):
			print(i)
			if (voltageTargets[i]>5) or (voltageTargets[i]<-5):

				newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
				voltageTargets=newTargets
				totalShift=newShift

			self.fungen.offset[channel]=Q_(voltageTargets[i],'V')
			wl=self.wm.measure_wavelength()
			counter=0
			if len(wls)!=0:
				last_wl=np.mean(np.array(wls).astype(np.float))
			
			print('i: '+str(i)+', initializing')

			while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff

			print('taking data')
			print('current target wavelength: '+str(wlpts[i]))
			print('current set voltage: '+str(voltageTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				#print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				quenchfix=self.reset_quench()
				if quenchfix!='YES':
					print('SNSPD quenched and could not be reset')
					self.fungen.output[1]='OFF'
					self.fungen.output[2]='OFF'
					endloop

				
				while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
				
			print('actual  wavelength: '+str(wl))
			print('targets shift during measurement:  '+str(counter2)+'V')
				

			self.createHistogram(stoparray, timebase, bincount,
				expparams['AWG Pulse Repetition Period'].magnitude,i, wls,
				"C:\\Data\\"+self.exp_parameters.widget.get()['File Name'])
		# turn off AWG
		self.fungen.output[channel]='OFF'
	

	@Task()
	def startpulse(self, timestep=100e-9):

		self.fungen.output[1]='OFF'
		#self.fungen.output[2]='OFF'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(3)  ##wait 1s to turn on the SNSPD

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

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=0   
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="Q:\\Data\\5.28.2021_ffpc\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\5.28.2021_ffpc\\":
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
		

		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			print(i)
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				wl=self.wm.measure_wavelength()
				

			while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)


			print('taking data')
			print('current target wavelength: '+str(wlTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			#counter2=0

			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				loopstart=time.time()
				# get the lost timestamps
				lost = self.qutag.getLastTimestamps(True)
				# wait half a milisecond
				time.sleep(5*0.1)   #
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	# self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				
				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray, timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i), wls,PATH)
			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
		self.fungen.output[1]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

	#@Task()
	#def spectralDiffusion_wRFsource(self):
		""" Task to measure spectral diffusion on timescales < T1. Assumes that
		1 channel of the keysight AWG is sending a sine wave to an EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam. This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		This task is good for modulating between 1MHz and 200MHz. 
		JDSU EOM amplifier has nonlinear performance below 1MHz (amplification
		increases), but the N5181A works down to 100kHz if desired.
		"""

		# get the parameters for the experiment from the widget
		"""
		SD_wRFparams=self.SD_wRFparams.widget.get()
		startFreq=SD_wRFparams['Start frequency']
		stopFreq=SD_wRFparams['Stop frequency']

		power=SD_wRFparams['RF Power']

		runtime=SD_wRFparams['Runtime']
		wl=SD_wRFparams['Wavelength']
		points=SD_wRFparams['# of points']
		period=SD_wRFparams['Period']
		foldername=self.SD_wRFparams.widget.get()['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude

		# set the amplitude of the RF signal
		self.source.set_RF_Power(power)

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="D:\\Data\\"+foldername
		if PATH!="D:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag

		# turn on the RF source & set it in CW mode
		self.source.FM_ON()
		self.source.set_CW_mode()

		for i in range(points):

			#set the frequency on the RF source
			self.source.set_CW_Freq(freqs[i])
			

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),
				wls,PATH,savefreqs)

		# turnn off the RF output of the N5181A whenn done
		self.source.RF_OFF()
		"""
	@Task()
	def spectralDiffusion_wAWG(self):
		""" Task to measure spectral diffusion on timescales < T1. Uses the 
		Agilent N5181A RF source to send a sine wave to the phase EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam (Calibrated on 11/19/20 to 
		be 6Vpp for the JDSU phase EOM). This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		The Keysight AWG only works up to 80MHz. 

		Could potentially modify code to use Siglent AWG which can go up to 120MHz
		"""
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		#self.fungen.output[1]='ON'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(1)  ##wait 1s to turn on the SNSPD


		# get the parameters for the experiment from the widget
		SD_wAWGparams=self.SD_wAWGparams.widget.get()
		startFreq=SD_wAWGparams['Start frequency']
		stopFreq=SD_wAWGparams['Stop frequency']
		EOMvoltage=SD_wAWGparams['EOM voltage']
		runtime=SD_wAWGparams['Runtime']
		EOMchannel=SD_wAWGparams['EOM channel']
		Pulsechannel=SD_wAWGparams['Pulse channel']
		Pulsefreq=SD_wAWGparams['Pulse Frequency']
		Pulsewidth=SD_wAWGparams['Pulse Width']
		period=SD_wAWGparams['Pulse Repetition Period']
		wl=SD_wAWGparams['Wavelength']
		points=SD_wAWGparams['# of points']
		foldername=SD_wAWGparams['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude
		self.fungen.clear_mem(EOMchannel)
		self.fungen.clear_mem(Pulsechannel)
		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.waveform[EOMchannel]='SIN'


		# set the sine wave driving the EOM on the other channel
		self.fungen.waveform[EOMchannel]='SIN'
		self.fungen.voltage[EOMchannel]=EOMvoltage
		self.fungen.offset[EOMchannel]=0
		self.fungen.phase[EOMchannel]=0


		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.frequency[Pulsechannel]=Pulsefreq
		self.fungen.voltage[Pulsechannel]=3.5
		self.fungen.offset[Pulsechannel]=1.75
		self.fungen.phase[Pulsechannel]=0
		self.fungen.pulse_width[Pulsechannel]=Pulsewidth


		self.fungen.output[EOMchannel]='ON'
		self.fungen.output[Pulsechannel]='ON'
		

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\"+str(foldername)
		print('PATH: '+str(PATH))
		if PATH!="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
				print('PATH: '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag


		for i in range(points):
			self.fungen.frequency[EOMchannel]=freqs[i]

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),wls,PATH,savefreqs)

		self.fungen.output[EOMchannel]='OFF'  ##turn off the AWG for both channels
		self.fungen.output[Pulsechannel]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement


	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		# ('start', {'type': float, 'default': 1535.665}),
		('start', {'type': float, 'default': 1535.527}),
		('stop', {'type': float, 'default':  1535.685})
		# ('stop', {'type': float, 'default': 1535.61})
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
		('# of points', {'type': int, 'default': 40}),
		('Measurement Time', {'type': int, 'default': 180, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 300e-9,'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Bin Count', {'type': int, 'default': 1000}),
		# ('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		# ('Battery Port 1',{'type':int,'default':5}),
		('Battery Port 2',{'type':int,'default':6})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Spectral diffusion experiment parameters')
	def SD_wAWGparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		params=[
		('Start frequency',{'type':float,'default':3.1e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':3.3e6,'units':'Hz'}),
		('EOM voltage',{'type':float,'default':6,'units':'V'}),
		('Runtime',{'type':float,'default':300,'units':'s'}),
		('EOM channel',{'type':int,'default':1}),
		('Pulse channel',{'type':int,'default':2}),
		('Pulse Repetition Period',{'type': float,'default': 0.001,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 1000,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 500e-9,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.61}),
		('# of points',{'type':int,'default':2}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w

	#@Element(name='Spectral diffusion experiment parameters')
	#def SD_wRFparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		"""
		params=[
		('Start frequency',{'type':float,'default':5e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':200e6,'units':'Hz'}),
		('RF Power',{'type':float,'default':-1.30,'units':'dBm'}),
		('Runtime',{'type':float,'default':10,'units':'s'}),
		('Wavelength',{'type':float,'default':1536.480}),
		('Period',{'type':float,'default':100e-3,'units':'s'}),
		('# of points',{'type':int,'default':40}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w
		"""

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
=======
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
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

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
		'SRS': SRS900
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
				time.sleep(3)
				current=self.wm.measure_wavelength()
				print(current, start)

	def createHistogram(self,stoparray, timebase, bincount, period, index, wls,out_name,extra_data=False):
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
		self.homelaser(current)
		wl=self.wm.measure_wavelength()
		return voltageTargets,totalShift,wl

	def reset_quench(self):
		"""
		A typical quench shows the voltage exceeding 2mV.
		"""
		qutagparams = self.qutag_params.widget.get()
		# vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		# vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		# self.SRS.clear_status()
		# V1=self.SRS.SIM970_voltage[vm1].magnitude
		self.SRS.clear_status()
		V2=self.SRS.SIM970_voltage[vm2].magnitude

		quenchfix='YES'

		# i=0
		# while (float(V1)>=0.010):
		# 	i+=1
		# 	print('Voltage 1 higher than 10mV, resetting')
		# 	self.SRS.SIM928_on_off[vs1]='OFF'
		# 	self.SRS.SIM928_on_off[vs2]='OFF'
		# 	self.SRS.SIM928_on_off[vs1]='ON'
		# 	self.SRS.SIM928_on_off[vs2]='ON'
		# 	print('checking Voltage 1 again')
		# 	self.SRS.clear_status()
		# 	time.sleep(1)
		# 	V1=self.SRS.SIM970_voltage[vm1].magnitude
		# 	print('Voltage 1: '+str(V1)+'V')
		# 	if i>10:
		# 		self.fungen.output[1]='OFF'
		# 		self.fungen.output[2]='OFF'
		# 		quenchfix='NO'
		# 		break

		i=0
		while (float(V2)>=0.010):
			i+=1
			print('Voltage 2 higher than 10mV, resetting')
			self.SRS.SIM928_on_off[vs1]='OFF'
			self.SRS.SIM928_on_off[vs2]='OFF'
			self.SRS.SIM928_on_off[vs1]='ON'
			self.SRS.SIM928_on_off[vs2]='ON'
			print('checking Voltage 2 again')
			self.SRS.clear_status()
			time.sleep(1)
			V2=self.SRS.SIM970_voltage[vm2].magnitude
			print('Voltage 2: '+str(V2)+'V')
			if i>10:
				self.fungen.output[1]='OFF'
				self.fungen.output[2]='OFF'
				quenchfix='NO'
				break
		return quenchfix
	
	@Task()
	def piezo_scan(self,timestep=100e-9):
		
		#self.fungen.output[1]='ON'
		piezo_params=self.piezo_parameters.widget.get()
		Vstart=piezo_params['voltage start']
		Vstop=piezo_params['voltage end']
		pts=piezo_params['scan points']

		voltageTargets=np.linspace(Vstart,Vstop,pts)
		reversedTargets=voltageTargets[::-1]
		voltageTargets=reversedTargets

		print('voltageTargets: '+str(voltageTargets))


		channel=piezo_params['AWG channel']

		# turn off AWG
		self.fungen.output[channel]='OFF'

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		# drive to the offset estimated by the piezo voltage
		# 1MOhm impedance of laser mismatch with 50Ohm impedance of AWG
		# multiplies voltage 2x
		# 140V ~ 40GHz ~ 315pm

		piezo_range=(Vstop.magnitude-Vstart.magnitude)*0.315/(140)*piezo_params['Scale factor'] #pm
		print('piezo_range: '+str(piezo_range)+str(' nm'))

		wl_start=wlparams['start']-piezo_range
		wl_stop=wlparams['stop']+piezo_range
		wlpts=np.linspace(wl_start,wl_stop,pts)

		self.homelaser(wlparams['start']-piezo_range)
		print('Laser Homed!')
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\"+self.exp_parameters.widget.get()['File Name']

		if PATH!="C:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# turn on AWG
		self.fungen.output[channel]='ON'

		last_wl=self.wm.measure_wavelength()
		wls=[]
		totalShift=0

		for i in range(pts):
			print(i)
			if (voltageTargets[i]>5) or (voltageTargets[i]<-5):

				newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
				voltageTargets=newTargets
				totalShift=newShift

			self.fungen.offset[channel]=Q_(voltageTargets[i],'V')
			wl=self.wm.measure_wavelength()
			counter=0
			if len(wls)!=0:
				last_wl=np.mean(np.array(wls).astype(np.float))
			
			print('i: '+str(i)+', initializing')

			while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff

			print('taking data')
			print('current target wavelength: '+str(wlpts[i]))
			print('current set voltage: '+str(voltageTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				#print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				quenchfix=self.reset_quench()
				if quenchfix!='YES':
					print('SNSPD quenched and could not be reset')
					self.fungen.output[1]='OFF'
					self.fungen.output[2]='OFF'
					endloop

				
				while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
				
			print('actual  wavelength: '+str(wl))
			print('targets shift during measurement:  '+str(counter2)+'V')
				

			self.createHistogram(stoparray, timebase, bincount,
				expparams['AWG Pulse Repetition Period'].magnitude,i, wls,
				"C:\\Data\\"+self.exp_parameters.widget.get()['File Name'])
		# turn off AWG
		self.fungen.output[channel]='OFF'
	

	@Task()
	def startpulse(self, timestep=100e-9):

		self.fungen.output[1]='OFF'
		#self.fungen.output[2]='OFF'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(3)  ##wait 1s to turn on the SNSPD

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

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=0   
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="Q:\\Data\\5.28.2021_ffpc\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\5.28.2021_ffpc\\":
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
		

		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			print(i)
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				wl=self.wm.measure_wavelength()
				

			while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)


			print('taking data')
			print('current target wavelength: '+str(wlTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			#counter2=0

			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				loopstart=time.time()
				# get the lost timestamps
				lost = self.qutag.getLastTimestamps(True)
				# wait half a milisecond
				time.sleep(5*0.1)   #
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	# self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				
				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray, timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i), wls,PATH)
			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
		self.fungen.output[1]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

	#@Task()
	#def spectralDiffusion_wRFsource(self):
		""" Task to measure spectral diffusion on timescales < T1. Assumes that
		1 channel of the keysight AWG is sending a sine wave to an EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam. This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		This task is good for modulating between 1MHz and 200MHz. 
		JDSU EOM amplifier has nonlinear performance below 1MHz (amplification
		increases), but the N5181A works down to 100kHz if desired.
		"""

		# get the parameters for the experiment from the widget
		"""
		SD_wRFparams=self.SD_wRFparams.widget.get()
		startFreq=SD_wRFparams['Start frequency']
		stopFreq=SD_wRFparams['Stop frequency']

		power=SD_wRFparams['RF Power']

		runtime=SD_wRFparams['Runtime']
		wl=SD_wRFparams['Wavelength']
		points=SD_wRFparams['# of points']
		period=SD_wRFparams['Period']
		foldername=self.SD_wRFparams.widget.get()['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude

		# set the amplitude of the RF signal
		self.source.set_RF_Power(power)

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="D:\\Data\\"+foldername
		if PATH!="D:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag

		# turn on the RF source & set it in CW mode
		self.source.FM_ON()
		self.source.set_CW_mode()

		for i in range(points):

			#set the frequency on the RF source
			self.source.set_CW_Freq(freqs[i])
			

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),
				wls,PATH,savefreqs)

		# turnn off the RF output of the N5181A whenn done
		self.source.RF_OFF()
		"""
	@Task()
	def spectralDiffusion_wAWG(self):
		""" Task to measure spectral diffusion on timescales < T1. Uses the 
		Agilent N5181A RF source to send a sine wave to the phase EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam (Calibrated on 11/19/20 to 
		be 6Vpp for the JDSU phase EOM). This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		The Keysight AWG only works up to 80MHz. 

		Could potentially modify code to use Siglent AWG which can go up to 120MHz
		"""
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		#self.fungen.output[1]='ON'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(1)  ##wait 1s to turn on the SNSPD


		# get the parameters for the experiment from the widget
		SD_wAWGparams=self.SD_wAWGparams.widget.get()
		startFreq=SD_wAWGparams['Start frequency']
		stopFreq=SD_wAWGparams['Stop frequency']
		EOMvoltage=SD_wAWGparams['EOM voltage']
		runtime=SD_wAWGparams['Runtime']
		EOMchannel=SD_wAWGparams['EOM channel']
		Pulsechannel=SD_wAWGparams['Pulse channel']
		Pulsefreq=SD_wAWGparams['Pulse Frequency']
		Pulsewidth=SD_wAWGparams['Pulse Width']
		period=SD_wAWGparams['Pulse Repetition Period']
		wl=SD_wAWGparams['Wavelength']
		points=SD_wAWGparams['# of points']
		foldername=SD_wAWGparams['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude
		self.fungen.clear_mem(EOMchannel)
		self.fungen.clear_mem(Pulsechannel)
		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.waveform[EOMchannel]='SIN'


		# set the sine wave driving the EOM on the other channel
		self.fungen.waveform[EOMchannel]='SIN'
		self.fungen.voltage[EOMchannel]=EOMvoltage
		self.fungen.offset[EOMchannel]=0
		self.fungen.phase[EOMchannel]=0


		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.frequency[Pulsechannel]=Pulsefreq
		self.fungen.voltage[Pulsechannel]=3.5
		self.fungen.offset[Pulsechannel]=1.75
		self.fungen.phase[Pulsechannel]=0
		self.fungen.pulse_width[Pulsechannel]=Pulsewidth


		self.fungen.output[EOMchannel]='ON'
		self.fungen.output[Pulsechannel]='ON'
		

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\"+str(foldername)
		print('PATH: '+str(PATH))
		if PATH!="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
				print('PATH: '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag


		for i in range(points):
			self.fungen.frequency[EOMchannel]=freqs[i]

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),wls,PATH,savefreqs)

		self.fungen.output[EOMchannel]='OFF'  ##turn off the AWG for both channels
		self.fungen.output[Pulsechannel]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement


	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		# ('start', {'type': float, 'default': 1535.665}),
		('start', {'type': float, 'default': 1535.527}),
		('stop', {'type': float, 'default':  1535.685})
		# ('stop', {'type': float, 'default': 1535.61})
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
		('# of points', {'type': int, 'default': 40}),
		('Measurement Time', {'type': int, 'default': 180, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 300e-9,'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Bin Count', {'type': int, 'default': 1000}),
		# ('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		# ('Battery Port 1',{'type':int,'default':5}),
		('Battery Port 2',{'type':int,'default':6})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Spectral diffusion experiment parameters')
	def SD_wAWGparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		params=[
		('Start frequency',{'type':float,'default':3.1e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':3.3e6,'units':'Hz'}),
		('EOM voltage',{'type':float,'default':6,'units':'V'}),
		('Runtime',{'type':float,'default':300,'units':'s'}),
		('EOM channel',{'type':int,'default':1}),
		('Pulse channel',{'type':int,'default':2}),
		('Pulse Repetition Period',{'type': float,'default': 0.001,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 1000,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 500e-9,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.61}),
		('# of points',{'type':int,'default':2}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w

	#@Element(name='Spectral diffusion experiment parameters')
	#def SD_wRFparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		"""
		params=[
		('Start frequency',{'type':float,'default':5e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':200e6,'units':'Hz'}),
		('RF Power',{'type':float,'default':-1.30,'units':'dBm'}),
		('Runtime',{'type':float,'default':10,'units':'s'}),
		('Wavelength',{'type':float,'default':1536.480}),
		('Period',{'type':float,'default':100e-3,'units':'s'}),
		('# of points',{'type':int,'default':40}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w
		"""

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
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
=======
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
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

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
		'SRS': SRS900
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
				time.sleep(3)
				current=self.wm.measure_wavelength()
				print(current, start)

	def createHistogram(self,stoparray, timebase, bincount, period, index, wls,out_name,extra_data=False):
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
		self.homelaser(current)
		wl=self.wm.measure_wavelength()
		return voltageTargets,totalShift,wl

	def reset_quench(self):
		"""
		A typical quench shows the voltage exceeding 2mV.
		"""
		qutagparams = self.qutag_params.widget.get()
		# vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		# vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		# self.SRS.clear_status()
		# V1=self.SRS.SIM970_voltage[vm1].magnitude
		self.SRS.clear_status()
		V2=self.SRS.SIM970_voltage[vm2].magnitude

		quenchfix='YES'

		# i=0
		# while (float(V1)>=0.010):
		# 	i+=1
		# 	print('Voltage 1 higher than 10mV, resetting')
		# 	self.SRS.SIM928_on_off[vs1]='OFF'
		# 	self.SRS.SIM928_on_off[vs2]='OFF'
		# 	self.SRS.SIM928_on_off[vs1]='ON'
		# 	self.SRS.SIM928_on_off[vs2]='ON'
		# 	print('checking Voltage 1 again')
		# 	self.SRS.clear_status()
		# 	time.sleep(1)
		# 	V1=self.SRS.SIM970_voltage[vm1].magnitude
		# 	print('Voltage 1: '+str(V1)+'V')
		# 	if i>10:
		# 		self.fungen.output[1]='OFF'
		# 		self.fungen.output[2]='OFF'
		# 		quenchfix='NO'
		# 		break

		i=0
		while (float(V2)>=0.010):
			i+=1
			print('Voltage 2 higher than 10mV, resetting')
			self.SRS.SIM928_on_off[vs1]='OFF'
			self.SRS.SIM928_on_off[vs2]='OFF'
			self.SRS.SIM928_on_off[vs1]='ON'
			self.SRS.SIM928_on_off[vs2]='ON'
			print('checking Voltage 2 again')
			self.SRS.clear_status()
			time.sleep(1)
			V2=self.SRS.SIM970_voltage[vm2].magnitude
			print('Voltage 2: '+str(V2)+'V')
			if i>10:
				self.fungen.output[1]='OFF'
				self.fungen.output[2]='OFF'
				quenchfix='NO'
				break
		return quenchfix
	
	@Task()
	def piezo_scan(self,timestep=100e-9):
		
		#self.fungen.output[1]='ON'
		piezo_params=self.piezo_parameters.widget.get()
		Vstart=piezo_params['voltage start']
		Vstop=piezo_params['voltage end']
		pts=piezo_params['scan points']

		voltageTargets=np.linspace(Vstart,Vstop,pts)
		reversedTargets=voltageTargets[::-1]
		voltageTargets=reversedTargets

		print('voltageTargets: '+str(voltageTargets))


		channel=piezo_params['AWG channel']

		# turn off AWG
		self.fungen.output[channel]='OFF'

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		# drive to the offset estimated by the piezo voltage
		# 1MOhm impedance of laser mismatch with 50Ohm impedance of AWG
		# multiplies voltage 2x
		# 140V ~ 40GHz ~ 315pm

		piezo_range=(Vstop.magnitude-Vstart.magnitude)*0.315/(140)*piezo_params['Scale factor'] #pm
		print('piezo_range: '+str(piezo_range)+str(' nm'))

		wl_start=wlparams['start']-piezo_range
		wl_stop=wlparams['stop']+piezo_range
		wlpts=np.linspace(wl_start,wl_stop,pts)

		self.homelaser(wlparams['start']-piezo_range)
		print('Laser Homed!')
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\"+self.exp_parameters.widget.get()['File Name']

		if PATH!="C:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# turn on AWG
		self.fungen.output[channel]='ON'

		last_wl=self.wm.measure_wavelength()
		wls=[]
		totalShift=0

		for i in range(pts):
			print(i)
			if (voltageTargets[i]>5) or (voltageTargets[i]<-5):

				newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
				voltageTargets=newTargets
				totalShift=newShift

			self.fungen.offset[channel]=Q_(voltageTargets[i],'V')
			wl=self.wm.measure_wavelength()
			counter=0
			if len(wls)!=0:
				last_wl=np.mean(np.array(wls).astype(np.float))
			
			print('i: '+str(i)+', initializing')

			while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
							voltageTargets=newTargets
							totalShift=newShift
							print('AWG limit exceeded, resetting voltage targets')
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter+=Voff
							totalShift+=Voff

			print('taking data')
			print('current target wavelength: '+str(wlpts[i]))
			print('current set voltage: '+str(voltageTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				#print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				quenchfix=self.reset_quench()
				if quenchfix!='YES':
					print('SNSPD quenched and could not be reset')
					self.fungen.output[1]='OFF'
					self.fungen.output[2]='OFF'
					endloop

				
				while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
					else:
						if voltageTargets[i]+Voff>5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(3)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
				
			print('actual  wavelength: '+str(wl))
			print('targets shift during measurement:  '+str(counter2)+'V')
				

			self.createHistogram(stoparray, timebase, bincount,
				expparams['AWG Pulse Repetition Period'].magnitude,i, wls,
				"C:\\Data\\"+self.exp_parameters.widget.get()['File Name'])
		# turn off AWG
		self.fungen.output[channel]='OFF'
	

	@Task()
	def startpulse(self, timestep=100e-9):

		self.fungen.output[1]='OFF'
		#self.fungen.output[2]='OFF'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(3)  ##wait 1s to turn on the SNSPD

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

		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=0   
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="Q:\\Data\\5.28.2021_ffpc\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\5.28.2021_ffpc\\":
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
		

		print('wlTargets: '+str(wlTargets))
		for i in range(expparams['# of points']):
			print(i)
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				wl=self.wm.measure_wavelength()
				

			while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)


			print('taking data')
			print('current target wavelength: '+str(wlTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)
			#counter2=0

			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				loopstart=time.time()
				# get the lost timestamps
				lost = self.qutag.getLastTimestamps(True)
				# wait half a milisecond
				time.sleep(5*0.1)   #
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
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))
				looptime+=time.time()-loopstart
				print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	# self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				
				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray, timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i), wls,PATH)
			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
		self.fungen.output[1]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

	#@Task()
	#def spectralDiffusion_wRFsource(self):
		""" Task to measure spectral diffusion on timescales < T1. Assumes that
		1 channel of the keysight AWG is sending a sine wave to an EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam. This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		This task is good for modulating between 1MHz and 200MHz. 
		JDSU EOM amplifier has nonlinear performance below 1MHz (amplification
		increases), but the N5181A works down to 100kHz if desired.
		"""

		# get the parameters for the experiment from the widget
		"""
		SD_wRFparams=self.SD_wRFparams.widget.get()
		startFreq=SD_wRFparams['Start frequency']
		stopFreq=SD_wRFparams['Stop frequency']

		power=SD_wRFparams['RF Power']

		runtime=SD_wRFparams['Runtime']
		wl=SD_wRFparams['Wavelength']
		points=SD_wRFparams['# of points']
		period=SD_wRFparams['Period']
		foldername=self.SD_wRFparams.widget.get()['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude

		# set the amplitude of the RF signal
		self.source.set_RF_Power(power)

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="D:\\Data\\"+foldername
		if PATH!="D:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag

		# turn on the RF source & set it in CW mode
		self.source.FM_ON()
		self.source.set_CW_mode()

		for i in range(points):

			#set the frequency on the RF source
			self.source.set_CW_Freq(freqs[i])
			

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),
				wls,PATH,savefreqs)

		# turnn off the RF output of the N5181A whenn done
		self.source.RF_OFF()
		"""
	@Task()
	def spectralDiffusion_wAWG(self):
		""" Task to measure spectral diffusion on timescales < T1. Uses the 
		Agilent N5181A RF source to send a sine wave to the phase EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam (Calibrated on 11/19/20 to 
		be 6Vpp for the JDSU phase EOM). This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		
		The Keysight AWG only works up to 80MHz. 

		Could potentially modify code to use Siglent AWG which can go up to 120MHz
		"""
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		#self.fungen.output[1]='ON'
		self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(1)  ##wait 1s to turn on the SNSPD


		# get the parameters for the experiment from the widget
		SD_wAWGparams=self.SD_wAWGparams.widget.get()
		startFreq=SD_wAWGparams['Start frequency']
		stopFreq=SD_wAWGparams['Stop frequency']
		EOMvoltage=SD_wAWGparams['EOM voltage']
		runtime=SD_wAWGparams['Runtime']
		EOMchannel=SD_wAWGparams['EOM channel']
		Pulsechannel=SD_wAWGparams['Pulse channel']
		Pulsefreq=SD_wAWGparams['Pulse Frequency']
		Pulsewidth=SD_wAWGparams['Pulse Width']
		period=SD_wAWGparams['Pulse Repetition Period']
		wl=SD_wAWGparams['Wavelength']
		points=SD_wAWGparams['# of points']
		foldername=SD_wAWGparams['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude
		self.fungen.clear_mem(EOMchannel)
		self.fungen.clear_mem(Pulsechannel)
		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.waveform[EOMchannel]='SIN'


		# set the sine wave driving the EOM on the other channel
		self.fungen.waveform[EOMchannel]='SIN'
		self.fungen.voltage[EOMchannel]=EOMvoltage
		self.fungen.offset[EOMchannel]=0
		self.fungen.phase[EOMchannel]=0


		self.fungen.waveform[Pulsechannel]='PULS'
		self.fungen.frequency[Pulsechannel]=Pulsefreq
		self.fungen.voltage[Pulsechannel]=3.5
		self.fungen.offset[Pulsechannel]=1.75
		self.fungen.phase[Pulsechannel]=0
		self.fungen.pulse_width[Pulsechannel]=Pulsewidth


		self.fungen.output[EOMchannel]='ON'
		self.fungen.output[Pulsechannel]='ON'
		

		# home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		synctimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		PATH="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\"+str(foldername)
		print('PATH: '+str(PATH))
		if PATH!="C:\\Data\\12.29.2020_ffpc\\SD0.1mW20dBatt195227GHz\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
				print('PATH: '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag


		for i in range(points):
			self.fungen.frequency[EOMchannel]=freqs[i]

			# want to actively stabilize the laser frequency since it can
			# drift on the MHz scale
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wl)
				currentwl=self.wm.measure_wavelength()
				

			while ((currentwl<wl-0.001) or (currentwl>wl+0.001)):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wl))
					print('actual wavelength: '+str(currentwl))
					time.sleep(1)


			print('taking data')
			print('current frequency: '+str(freqs[i]))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			savefreqs=[]
			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
				currentwl=self.wm.measure_wavelength()
				wls.append(str(currentwl))
				savefreqs.append(float(freqs[i]))
				looptime+=time.time()-loopstart

				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()
			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount,period,str(i),wls,PATH,savefreqs)

		self.fungen.output[EOMchannel]='OFF'  ##turn off the AWG for both channels
		self.fungen.output[Pulsechannel]='OFF'
		self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement


	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		# ('start', {'type': float, 'default': 1535.665}),
		('start', {'type': float, 'default': 1535.527}),
		('stop', {'type': float, 'default':  1535.685})
		# ('stop', {'type': float, 'default': 1535.61})
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
		('# of points', {'type': int, 'default': 40}),
		('Measurement Time', {'type': int, 'default': 180, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 300e-9,'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Bin Count', {'type': int, 'default': 1000}),
		# ('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		# ('Battery Port 1',{'type':int,'default':5}),
		('Battery Port 2',{'type':int,'default':6})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Spectral diffusion experiment parameters')
	def SD_wAWGparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		params=[
		('Start frequency',{'type':float,'default':3.1e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':3.3e6,'units':'Hz'}),
		('EOM voltage',{'type':float,'default':6,'units':'V'}),
		('Runtime',{'type':float,'default':300,'units':'s'}),
		('EOM channel',{'type':int,'default':1}),
		('Pulse channel',{'type':int,'default':2}),
		('Pulse Repetition Period',{'type': float,'default': 0.001,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 1000,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 500e-9,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.61}),
		('# of points',{'type':int,'default':2}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w

	#@Element(name='Spectral diffusion experiment parameters')
	#def SD_wRFparams(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		"""
		params=[
		('Start frequency',{'type':float,'default':5e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':200e6,'units':'Hz'}),
		('RF Power',{'type':float,'default':-1.30,'units':'dBm'}),
		('Runtime',{'type':float,'default':10,'units':'s'}),
		('Wavelength',{'type':float,'default':1536.480}),
		('Period',{'type':float,'default':100e-3,'units':'s'}),
		('# of points',{'type':int,'default':40}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w
		"""

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