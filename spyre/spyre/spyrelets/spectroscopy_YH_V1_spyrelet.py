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
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900
from lantz.drivers.attocube import ANC350

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

	attocube=ANC350()
	attocube.initialize()
	axis_index_x=0
	axis_index_y=1
	axis_index_z=2


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
		self.homelaser(current)
		wl=self.wm.measure_wavelength()
		return voltageTargets,totalShift,wl

	# def reset_quench(self):
	# 	"""
	# 	A typical quench shows the voltage exceeding 2mV.
	# 	"""
	# 	qutagparams = self.qutag_params.widget.get()
	# 	# vm1=qutagparams['Voltmeter Channel 1']
	# 	vm2=qutagparams['Voltmeter Channel 2']
	# 	# vs1=qutagparams['Battery Port 1']
	# 	vs2=qutagparams['Battery Port 2']

	# 	# self.SRS.clear_status()
	# 	# V1=self.SRS.SIM970_voltage[vm1].magnitude
	# 	self.SRS.clear_status()
	# 	V2=self.SRS.SIM970_voltage[vm2].magnitude

	# 	quenchfix='YES'

	# 	# i=0
	# 	# while (float(V1)>=0.010):
	# 	# 	i+=1
	# 	# 	print('Voltage 1 higher than 10mV, resetting')
	# 	# 	self.SRS.SIM928_on_off[vs1]='OFF'
	# 	# 	self.SRS.SIM928_on_off[vs2]='OFF'
	# 	# 	self.SRS.SIM928_on_off[vs1]='ON'
	# 	# 	self.SRS.SIM928_on_off[vs2]='ON'
	# 	# 	print('checking Voltage 1 again')
	# 	# 	self.SRS.clear_status()
	# 	# 	time.sleep(1)
	# 	# 	V1=self.SRS.SIM970_voltage[vm1].magnitude
	# 	# 	print('Voltage 1: '+str(V1)+'V')
	# 	# 	if i>10:
	# 	# 		self.fungen.output[1]='OFF'
	# 	# 		self.fungen.output[2]='OFF'
	# 	# 		quenchfix='NO'
	# 	# 		break

	# 	i=0
	# 	while (float(V2)>=0.010):
	# 		i+=1
	# 		print('Voltage 2 higher than 10mV, resetting')
	# 		self.SRS.SIM928_on_off[vs1]='OFF'
	# 		self.SRS.SIM928_on_off[vs2]='OFF'
	# 		self.SRS.SIM928_on_off[vs1]='ON'
	# 		self.SRS.SIM928_on_off[vs2]='ON'
	# 		print('checking Voltage 2 again')
	# 		self.SRS.clear_status()
	# 		time.sleep(1)
	# 		V2=self.SRS.SIM970_voltage[vm2].magnitude
	# 		print('Voltage 2: '+str(V2)+'V')
	# 		if i>10:
	# 			self.fungen.output[1]='OFF'
	# 			self.fungen.output[2]='OFF'
	# 			quenchfix='NO'
	# 			break
	# 	return quenchfix


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
	def piezo_scan(self,timestep=100e-9):
		## To scan the laser frequency with the laser piezo instead by setting the laser wavelength with the motor

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()
		self.SRS.SIM928_on_off[vs1]='OFF'		
		self.SRS.SIM928_on_off[vs1]='ON'
		
		# get the parameters for the piezo_scan experiment from the widget
		piezo_params=self.piezo_parameters.widget.get()
		filename=piezo_params['File Name']
		runtime=piezo_params['Runtime']
		wl=piezo_params['Wavelength']

		Piezochannel=piezo_params['Piezo channel']
		Vstart=piezo_params['Voltage start']
		Vstop=piezo_params['Voltage end']
		pts=piezo_params['Scan points']

		voltageTargets=np.linspace(Vstart,Vstop,pts)
		reversedTargets=voltageTargets[::-1]
		voltageTargets=reversedTargets

		print('voltageTargets: '+str(voltageTargets))


		Pulsechannel=piezo_params['Pulse channel']
		Pulsefreq=piezo_params['Pulse Frequency']
		Pulsewidth=piezo_params['Pulse Width']
		period=piezo_params['Pulse Repetition Period']



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

		##Qutag Part
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		# turn off AWG
		self.fungen.output[channel]='OFF'
		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']

		#self.fungen.voltage[1]=3.5
		#self.fungen.offset[1]=1.75
		#self.fungen.phase[1]=-3
		 
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']

		# drive to the offset estimated by the piezo voltage
		# 1MOhm impedance of laser mismatch with 50Ohm impedance of AWG
		# multiplies voltage 2x
		# 140V ~ 40GHz ~ 315pm

		piezo_range=(Vstop.magnitude-Vstart.magnitude)*0.315/(140)*piezo_params['Scale factor'] #pm
		print('piezo_range: '+str(piezo_range)+str(' nm'))

		wl_start=wlparams['start']-piezo_range
		wl_stop=wlparams['stop']+piezo_range
		wlpts=np.linspace(wl_start,wl_stop,pts)

		self.fungen.offset[channel]=Q_(voltageTargets[0],'V')
		# turn on AWG
		self.fungen.output[channel]='ON'

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

		PATH="Q:\\Data\\"+self.piezo_parameters.widget.get()['File Name']
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
			print(wl)
			counter=0
			if len(wls)!=0:
				last_wl=np.mean(np.array(wls).astype(np.float))
			
			print('i: '+str(i)+', initializing')
			print('target wavelength: '+str(wlpts[i]))

			while ((wl<wlpts[i]-0.0004) or (wl>wlpts[i]+0.0004)):
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
							time.sleep(2)
							wl=self.wm.measure_wavelength()
							print(wl)
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
							time.sleep(2)
							wl=self.wm.measure_wavelength()
							print(wl)
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

			# open pickle files to save timestamp data

			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

			looptime=startTime
			while looptime-startTime < expparams['Measurement Time'].magnitude:
				dataloss1 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss))

				dataloss2 = self.qutag.getDataLost()
				#print("dataloss: " + str(dataloss))

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
				"""
				print('timestamps')
				print(tstamp[:100])

				print('channels')
				print(tchannel[:100])
				"""
				for k in range(values):
					# output all stop events together with the latest start event
					if tchannel[k] == 2: # 104 is the index of the start channel
						#print('synctimestamp: '+str(synctimestamp))
						#print('stoptimestamp: '+str(stoptimestamp))
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
				wl=self.wm.measure_wavelength()
				wls.append(str(wl))

				# dump timestamp data to pickle file
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)
							
				while ((wl<wlpts[i]-0.0004) or (wl>wlpts[i]+0.0004)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					offset=wl-wlpts[i]
					Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
					if offset<0:
						if voltageTargets[i]+Voff<-5:
							break
						else:
							newTargets=[j+Voff for j in voltageTargets]
							voltageTargets=newTargets
							self.fungen.offset[channel]=Q_(newTargets[i],'V')
							time.sleep(2)
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
							time.sleep(2)
							wl=self.wm.measure_wavelength()
							counter2+=Voff
							totalShift+=Voff
				
				
			print('actual  wavelength: '+str(wl))
			print('targets shift during measurement:  '+str(counter2)+'V')
				
			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)

		# turn off AWG
		self.fungen.output[channel]='OFF'
		self.SRS.SIM928_on_off[vs1]='OFF'
	

	@Task()
	def startpulse(self, timestep=100e-9):

		self.fungen.output[1]='OFF'
		# self.fungen.output[2]='OFF'
		
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		#time.sleep(3)  ##wait 1s to turn on the SNSPD
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
		#ditherV=expparams['Dither Voltage'].magnitude
		print('here')
		
		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']

		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=0
		 
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']

		self.fungen.waveform[1]='PULS'
		#self.fungen.output[1]='ON'
		

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="Q:\\Data\\6.15.2021_ffpc\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\6.15.2021_ffpc\\":
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
				
			
			while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)
					
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

				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
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

				self.startpulse.acquire(values)

			# very important to flush the buffer
			# if you don't do this, or don't close the files,
			# then data stored for writing will use up RAM space
			# and affect saving timestamps if the program is interrupted
			# times.flush() 
			# channels.flush()
			# vals.flush()

			# # close pickle files with timestamp data
			# times.close()
			# channels.close()
			# vals.close()

			#print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray,timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.fungen.output[1]='OFF'
			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
			#self.fungen.output[2]='OFF'
		#self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

	@Task()
	def Inhomolwscan(self, timestep=100e-9):

		self.fungen.output[1]='OFF'
		# self.fungen.output[2]='OFF'
		
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		#time.sleep(3)  ##wait 1s to turn on the SNSPD
		self.fungen.output[2]='OFF'
		qutagparams = self.qutag_params.widget.get()
		inhomolwscan = self.inhomolwscan_parameters.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'		
		self.SRS.SIM928_on_off[vs2]='ON'
		##Qutag Part
		self.configureQutag()
		#expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()
		self.homelaser(wlparams['start'])
		print('Laser Homed!')

		lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		startVdc = inhomolwscan['att voltage start'].magnitude
		stopVdc = inhomolwscan['att voltage stop'].magnitude
		#ditherV=expparams['Dither Voltage'].magnitude
		print('here')
		
		self.fungen.frequency[1]=inhomolwscan['AWG Pulse Frequency']

		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=0
		 
		self.fungen.pulse_width[1]=inhomolwscan['AWG Pulse Width']

		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="Q:\\Data\\5.29.2021_ffpc\\"+self.inhomolwscan_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\5.29.2021_ffpc\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'], inhomolwscan['# of points'])
		VdcTargets = np.linspace(startVdc, stopVdc, inhomolwscan['# of points'])
		
		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count']
		self.cutoff=int(
			math.ceil(
				inhomolwscan['AWG Pulse Width'].magnitude/inhomolwscan['AWG Pulse Repetition Period'].magnitude*bins))

		#self.fungen.voltage[2]=ditherV
		print('wlTargets: '+str(wlTargets))
		print('VdcTargets:'+str(VdcTargets))
		for i in range(inhomolwscan['# of points']):
			print(i)
			#self.fungen.output[2]='OFF'

			## setting the attocube Z axis dc voltage
			#self.attocube.DCvoltage[self.axis_index_z]=Q_(self.Vdc,'V')
			self.attocube.dc_bias(self.axis_index_z, VdcTargets[i])
			print('current VdcTargets:'+str(VdcTargets[i]))
			time.sleep(2)


			## setting laser wavelength
			with Client(self.laser) as client:

				setting=client.get('laser1:ctl:wavelength-set', float)
				client.set('laser1:ctl:wavelength-set', wlTargets[i])
				wl=self.wm.measure_wavelength()
				
			## stablize laser wavelength if there is any drift
			while ((wl<wlTargets[i]-0.0005) or (wl>wlTargets[i]+0.0005)):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					print('current target wavelength: '+str(wlTargets[i]))
					print('actual wavelength: '+str(self.wm.measure_wavelength()))
					time.sleep(1)
					
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

			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			synctimestamp=[]
			looptime=startTime
			while looptime-startTime < inhomolwscan['Measurement Time'].magnitude:
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
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)

				while ((wl<wlTargets[i]-0.0005) or (wl>wlTargets[i]+0.0005)) and (time.time()-startTime < inhomolwscan['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()

				for k in range(len(stopscheck)):
					tdiff=stopscheck[k]
					binNumber = int(tdiff*timebase*bincount/(inhomolwscan['AWG Pulse Repetition Period'].magnitude))
					if binNumber<bincount:
						self.hist[binNumber]+=1
				stopscheck=[]

				values = {
					'x': self.bins,
					'y': self.hist,
				}

				self.Inhomolwscan.acquire(values)

			# very important to flush the buffer
			# if you don't do this, or don't close the files,
			# then data stored for writing will use up RAM space
			# and affect saving timestamps if the program is interrupted
			times.flush() 
			channels.flush()
			vals.flush()

			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			#print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray,timebase, bincount, inhomolwscan['AWG Pulse Repetition Period'].magnitude,str(i),wls,PATH)
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'
		self.attocube.dc_bias(self.axis_index_z, startVdc)
		time.sleep(2)

			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
			#self.fungen.output[2]='OFF'
		#self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

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
		""" Task to measure spectral diffusion on timescales < T1. Uses Keysight AWG to send a sine wave to the phase EOM. 
		The amplitude of the RF drive for the EOM is set such that the sidebands have an equal amplitude to the carrier 
		wave (4.5 Vpp for the IXBlue phase EOM). This tasks sweeps the frequency of the sine wave (separation of the EOM 
		sidebands) while collecting PL, which can be used to determine the spectral diffusion linewidth since the saturation 
		of the ions will be determined by how much the sidebands overlap with the spectral  diffusion lineshape.
		
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

		
		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']


		self.SRS.SIM928_on_off[vs2]='ON'

		PATH="Q:\\Data\\6.15.2021_ffpc\\"+foldername
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\6.15.2021_ffpc\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag

		qutagparams = self.qutag_params.widget.get()
		bins=qutagparams['Bin Count'] # read the bin numbers 
		self.cutoff=int(math.ceil(Pulsewidth.magnitude/period*bins))

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

			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))
			stopscheck=[]

			# open pickle files to save timestamp data
			# times=open(PATH+'\\'+str(i)+'_times.p','wb')
			# channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			# vals=open(PATH+'\\'+str(i)+'_vals.p','wb')
			####################################################

			lost = self.qutag.getLastTimestamps(True)

			looptime=startTime
			while looptime-startTime < runtime:
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
					if tchannel[k] == start:
						synctimestamp = tstamp[k]
					else:
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
						stopscheck.append(stoptimestamp)
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

				#dump timestamp data to pickle file
				# pickle.dump(tstamp,times)
				# pickle.dump(tchannel,channels)
				# pickle.dump(values,vals)
				###############################

				while ((currentwl<wl-0.001) or (currentwl>wl+0.001)) and (time.time()-startTime < runtime):
					print('correcting for laser drift')
					self.homelaser(wl)
					currentwl=self.wm.measure_wavelength()

				for k in range(len(stopscheck)):
					tdiff=stopscheck[k]
					binNumber = int(tdiff*timebase*bincount/(period))
					if binNumber<bincount:
						self.hist[binNumber]+=1
				stopscheck=[]

				values = {
					'x': self.bins,
					'y': self.hist,
				}

				self.spectralDiffusion_wAWG.acquire(values)

			# very important to flush the buffer
			# if you don't do this, or don't close the files,
			# then data stored for writing will use up RAM space
			# and affect saving timestamps if the program is interrupted
			# times.flush() 
			# channels.flush()
			# vals.flush()

			# # close pickle files with timestamp data
			# times.close()
			# channels.close()
			# vals.close()
			##################################################

			print('actual  wavelength: '+str(currentwl))

			self.createHistogram(stoparray, timebase, bincount, period, str(i), wls, PATH, savefreqs)

		self.fungen.output[EOMchannel]='OFF'  ##turn off the AWG for both channels
		self.fungen.output[Pulsechannel]='OFF'
		self.SRS.SIM928_on_off[vs1]='OFF'
		self.SRS.SIM928_on_off[vs2]='OFF'		
	

	# this task gets the current value of SRS voltmeter, to check the SNSPD quench
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
			#print(values)
			time.sleep(0.05)
			#print(self.Voltmeter.acquired)
		return 
	# sets up some formatting of the voltmeter
	@Element(name='indicator')
	def voltmeter_now(self):
		text = QTextEdit()
		text.setPlainText('Voltage 1: non V \nVoltage 2: non V\n')
		return text

	# more formatting of the voltage units
	@voltmeter_now.on(Voltmeter.acquired)
	def _voltmeter_now_update(self,ev):
		w=ev.widget
		w.setPlainText('Voltage 1: %f V \nVoltage 2: %f V \n'%(self.v1,self.v2))
		return


	# the 1D plot widget is used for the live histogram
	@Element(name='startpulse Histogram')
	def startpulse_Histogram(self):
		p = LinePlotWidget()
		p.plot('startpulse Histogram')
		return p

	# more code for the histogram plot
	@startpulse_Histogram.on(startpulse.acquired)
	def _startpulse_Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[self.cutoff:]
		ys = np.array(self.hist)[self.cutoff:]
		w.set('startpulse Histogram',xs=xs,ys=ys)
		return

	# the 1D plot widget is used for the live histogram
	@Element(name='SD Histogram')
	def SD_Histogram(self):
		p = LinePlotWidget()
		p.plot('SD Histogram')
		return p

	# more code for the histogram plot
	@SD_Histogram.on(spectralDiffusion_wAWG.acquired)
	def _SD_Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('SD Histogram',xs=xs,ys=ys)
		return

	# the 1D plot widget is used for the live histogram
	@Element(name='Inhomolwscan Histogram')
	def Inhomolwscan_Histogram(self):
		p = LinePlotWidget()
		p.plot('Inhomolwscan Histogram')
		return p

	# more code for the histogram plot
	@Inhomolwscan_Histogram.on(Inhomolwscan.acquired)
	def _Inhomolwscan_Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.bins)[(self.cutoff+1):]
		ys = np.array(self.hist)[(self.cutoff+1):]
		w.set('Inhomolwscan Histogram',xs=xs,ys=ys)
		return


	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		# ('start', {'type': float, 'default': 1535.665}),
		('start', {'type': float, 'default': 1535.7591}),
		('stop', {'type': float, 'default':  1535.7591})
		# ('stop', {'type': float, 'default': 1535.61})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Piezo scan parameters')
	def piezo_parameters(self):
		params=[
		('Voltage start',{'type': float,'default':-3,'units':'V'}),
		('Voltage end',{'type': float,'default':3,'units':'V'}),
		('Scale factor',{'type':float,'default':2}),
		('Scan points',{'type':int,'default':20}),
		('Piezo channel',{'type':int,'default':2}),
		('Pulse channel',{'type':int,'default':1}),
		('Pulse Repetition Period',{'type': float,'default': 0.001,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 1000,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 150e-9,'units':'s'}),	
		('Runtime',{'type':float,'default':300,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.6105}),
		('File Name',{'type':str}),
		]
		w=ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 1}),
		('Measurement Time', {'type': int, 'default': 200, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 300e-9,'units':'s'}),
		]
		w = ParamWidget(params)
		return w

	@Element(name='Inhomolwscan Parameters')
	def inhomolwscan_parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('# of points', {'type': int, 'default': 26}),
		('Measurement Time', {'type': int, 'default': 180, 'units':'s'}),
		('File Name', {'type': str}),
		('AWG Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('AWG Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('AWG Pulse Width',{'type': float,'default': 500e-9,'units':'s'}),
		('att voltage start',{'type': float,'default':0,'units':'V'}),
		('att voltage stop',{'type': float,'default':25,'units':'V'}),

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
		('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		('Battery Port 1',{'type':int,'default':5}),
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
		('Start frequency',{'type':float,'default':1e3,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':20e6,'units':'Hz'}),
		('EOM voltage',{'type':float,'default':4.5,'units':'V'}),
		('Runtime',{'type':float,'default':200,'units':'s'}),
		('EOM channel',{'type':int,'default':2}),
		('Pulse channel',{'type':int,'default':1}),
		('Pulse Repetition Period',{'type': float,'default': 2e-3,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 500,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 300e-9,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.7591}),
		('# of points',{'type':int,'default':20}),
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

	@Inhomolwscan.initializer
	def initialize(self):
		self.wm.start_data()
		# inhomolwscan = self.inhomolwscan_parameters.widget.get()
		# self.startVdc = inhomolwscan['att voltage start'].magnitude
		# self.stopVdc = inhomolwscan['att voltage stop'].magnitude
		# self.VdcTargets = np.linspace(self.startVdc, self.stopVdc, inhomolwscan['# of points'])

	@Inhomolwscan.finalizer
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