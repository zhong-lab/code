import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle # for saving large arrays

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
from lantz.drivers.thorlabs.pm100d import PM100D
#from lantz.drivers.agilent import N5181A

#from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.stanford.srs900 import SRS900

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
		#'SRS': SRS900,
		'pmd':PM100D
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

	def avgPower(self):
		plist=[]
		while len(plist)<50:
			p=self.pmd.power.magnitude
			plist.append(p)
		pcurr=np.mean(plist)
		return pcurr

	def stabilizePower(self,power_target,pcurr):
		while abs(pcurr-power_target)>0.03*power_target:
				with Client(self.laser) as client:
					setpoint=client.get('laser1:power-stabilization:setpoint',float)
					newsetpoint=setpoint+(power_target-pcurr)/float(pcurr)*setpoint
					rsetpoint=round(newsetpoint,2)
					print('difference: '+str(pcurr-power_target))
					print('powers: '+str(power_target)+' '+str(pcurr))
					print('power stabilization: '+str(setpoint)+', '+str(rsetpoint))
					if (rsetpoint==setpoint):
						'quitting because no more stabilization possible'
						break
					if (rsetpoint>56.00) or (rsetpoint<0):
						'quitting because target power is out of bounds'
						break
					client.set('laser1:power-stabilization:setpoint',rsetpoint)
					pcurr=self.avgPower()
					
		return pcurr

	"""
	def reset_quench(self):
		#A typical quench shows the voltage exceeding 2mV.
		
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
		"""
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

		#self.fungen.output[1]='OFF'
		#self.fungen.output[2]='OFF'
		
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
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
		ditherV=expparams['Dither Voltage'].magnitude

		"""
		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=-3
		"""   
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		"""
		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		"""

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="D:\\Data\\":
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
			times=open(PATH+'\\'+str(i)+'_times.p','wb')
			channels=open(PATH+'\\'+str(i)+'_channels.p','wb')
			vals=open(PATH+'\\'+str(i)+'_vals.p','wb')

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
				#print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
				# quenchfix=self.reset_quench()
				# if quenchfix!='YES':
				# 	print('SNSPD quenched and could not be reset')
				# 	# self.fungen.output[1]='OFF'
				# 	self.fungen.output[2]='OFF'
				# 	endloop

				# dump timestamp data to pickle file
				pickle.dump(tstamp,times)
				pickle.dump(tchannel,channels)
				pickle.dump(values,vals)
				
				while ((wl<wlTargets[i]-0.001) or (wl>wlTargets[i]+0.001)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
					print('correcting for laser drift')
					self.homelaser(wlTargets[i])
					wl=self.wm.measure_wavelength()
					
			# close pickle files with timestamp data
			times.close()
			channels.close()
			vals.close()

			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray, timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,
				str(i), wls,PATH)
			# self.createHistogram(stoparray, timebase, bincount,period,str(i),
			# 	wls,PATH,savefreqs)
			#self.fungen.output[2]='OFF'
		#self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement

	@Task()
	def startpulse_wPM(self, timestep=100e-9):

		#self.fungen.output[1]='OFF'
		#self.fungen.output[2]='OFF'
		
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
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
		ditherV=expparams['Dither Voltage'].magnitude

		"""
		self.fungen.frequency[1]=expparams['AWG Pulse Frequency']
		self.fungen.voltage[1]=3.5
		self.fungen.offset[1]=1.75
		self.fungen.phase[1]=-3
		"""   
		self.fungen.pulse_width[1]=expparams['AWG Pulse Width']
		"""
		self.fungen.waveform[1]='PULS'
		self.fungen.output[1]='ON'
		"""

		#PATH="C:\\Data\\12.18.2020_ffpc\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="C:\\Data\\2.26.2021_GNR_Er\\bare_Er2O3_76\\":
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
		
		power_target=0
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
			if power_target==0:
				power_target=self.avgPower()
				print('power target: '+str(power_target))

			print('taking data')
			print('current target wavelength: '+str(wlTargets[i]))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			
			time.sleep(1)
			##Wavemeter measurements
			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

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
				#print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))
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

				pcurr=self.avgPower()
				self.stabilizePower(power_target,pcurr)
				
			print('actual  wavelength: '+str(wl))
			#print('I am here')
			self.createHistogram(stoparray, timebase, bincount, expparams['AWG Pulse Repetition Period'].magnitude,str(i), wls,PATH)
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
	def fiberFilter(self):

		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'

		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.clear_mem(2)
		self.fungen.wait()
		#self.fungen.output[1]='ON'
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		time.sleep(1)  ##wait 1s to turn on the SNSPD


		# get the parameters for the experiment from the widget
		fiberFilter_params=self.fiberFilter_params.widget.get()
		startV=fiberFilter_params['Start voltage']
		stopV=fiberFilter_params['Stop voltage']
		runtime=fiberFilter_params['Runtime']
		filterChannel=fiberFilter_params['Filter channel']
		Pulsechannel=fiberFilter_params['Pulse channel']
		Pulsefreq=fiberFilter_params['Pulse Frequency']
		Pulsewidth=fiberFilter_params['Pulse Width']
		period=fiberFilter_params['Pulse Repetition Period']
		wl=fiberFilter_params['Wavelength']
		points=fiberFilter_params['# of points']
		foldername=fiberFilter_params['File Name']

		# convert the period & runtime to floats
		period=period.magnitude
		runtime=runtime.magnitude

		self.fungen.offset[filterChannel]=0

		self.fungen.pulse_width[Pulsechannel]=Pulsewidth


		self.fungen.output[filterChannel]='ON'
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

		PATH="D:\\Data\\"+str(foldername)
		print('PATH: '+str(PATH))
		if PATH!="D:\\Data\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
				print('PATH: '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		voltages=np.linspace(startV,stopV,points)

		for i in range(points):
			self.fungen.offset[filterChannel]=voltages[i]

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
			print('current target voltage: '+str(voltages[i]))
			
			time.sleep(1)


			stoparray = []
			startTime = time.time()
			wls=[]
			saveVoltages=[]
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
				saveVoltages.append(float(voltages[i]))
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

			self.createHistogram(stoparray, timebase, bincount,period,str(i),wls,PATH,saveVoltages)

		self.fungen.output[filterChannel]='OFF'  ##turn off the AWG for both channels
		#self.SRS.SIMmodule_off[6] ##turn off the SNSPD power suppy after the measurement
		

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
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 4}),
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


	@Element(name='fiber filter scan params ')
	def fiberFilter_params(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.

		Default EOM voltage calibrated by Christina and Yizhong on 11/19/20.
		(rough estimate for equal amplitude sidebands)
		"""
		params=[
		('Start voltage',{'type':float,'default':0,'units':'V'}),
		('Stop voltage',{'type':float,'default':1.366,'units':'V'}),
		('Runtime',{'type':float,'default':600,'units':'s'}),
		('Filter channel',{'type':int,'default':2}),
		('Pulse channel',{'type':int,'default':1}),
		('Pulse Repetition Period',{'type': float,'default': 0.050,'units':'s'}),
		('Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
		('Pulse Width',{'type': float,'default': 8e-3,'units':'s'}),
		('Wavelength',{'type':float,'default':1535.61}),
		('# of points',{'type':int,'default':15}),
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