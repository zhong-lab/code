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

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.bristol import Bristol_771
from lantz.drivers.stanford.srs900 import SRS900
from toptica.lasersdk.client import NetworkConnection, Client  # import the toptica laser
#from lantz.drivers.agilent import N5181A

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')
s = Q_(1,'s')


class TwoPulsePhotonEcho(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'wm': Bristol_771,
		'SRS': SRS900
	}
	qutag = None
	laser = NetworkConnection('1.1.1.2')

	xs = np.array([])
	ys= np.array([])
	hist=[]


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

	def configureQutag(self):
		qutagparams = self.qutag_params.widget.get()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']
		##True = rising edge, False = falling edge. Final value is threshold voltage
		self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,1)
		self.qutag.setSignalConditioning(stop,self.qutag.SIGNALCOND_MISC,True,0.1)
		self.qutag.enableChannels((start,stop))

	# def createHistogram(self,stoparray, timebase, bincount, totalWidth, tau):
	# 	# lowBound=1.9*tau
	# 	# highBound=2.1*tau
	# 	hist = [0]*bincount
	# 	for stoptime in stoparray:
	# 		binNumber = int(stoptime*timebase*bincount/(totalWidth))
	# 		if binNumber >= bincount:
	# 			continue
	# 			print('error')
	# 		else:
	# 			hist[binNumber]+=1
	# 	out_name = "Q:\\Data\\6.23.2021_ffpc\\Echotest\\"
	# 	x=[]
	# 	for i in range(bincount):
	# 		x.append(i*totalWidth/bincount)
	# 	np.savez(os.path.join(out_name,str(int(round(tau*1e6,0)))),hist,x)
	# 	print('Data stored under File Name: ' + str(tau))


	def createHistogram(self, stoparray, timebase, bincount, totalWidth, index, wls, out_name, extra_data=False):
		print('creating histogram')

		hist = [0]*bincount

		tstart=0
		for k in range(len(stoparray)):
				tdiff=stoparray[k]

				binNumber = int(tdiff*timebase*bincount/(totalWidth))
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
		# A typical quench shows the voltage exceeding 3 mV. This part is to turn the SNSPDs back on
		
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
	def twopulseecho(self, timestep=1e-9):
		params = self.twopulse_parameters.widget.get()
		starttau=params['start tau']
		stoptau=params['stop tau']
		points=params['# of points']
		period = params['period'].magnitude
		repeat_unit = params['repeat unit'].magnitude
		pulse_width = params['pulse width'].magnitude
		buffer_time = params['buffer time'].magnitude
		shutter_offset = params['shutter offset'].magnitude
		wholeRange = params['measuring range'].magnitude
		Pulsechannel = params['Pulse channel']
		Shutterchannel = params['Shutter channel']
		wl = params['Wavelength']
		foldername=params['File Name']
		runtime=params['Runtime'].magnitude



		## turn off the AWG before the measurement
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		
		#self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
		#time.sleep(3)  ##wait 1s to turn on the SNSPD

		qutagparams = self.qutag_params.widget.get()

		vm1=qutagparams['Voltmeter Channel 1']
		vm2=qutagparams['Voltmeter Channel 2']
		vs1=qutagparams['Battery Port 1']
		vs2=qutagparams['Battery Port 2']

		self.SRS.clear_status()

		self.SRS.SIM928_on_off[vs2]='OFF'		
		self.SRS.SIM928_on_off[vs2]='ON'

			## setting the data storage path
		PATH="Q:\\Data\\6.24.2021_ffpc\\"+foldername
		print('here')
		print('PATH: '+str(PATH))
		if PATH!="Q:\\Data\\6.24.2021_ffpc\\":
			if (os.path.exists(PATH)):
				print('deleting old directory with same name')
				os.system('rm -rf '+str(PATH))
			print('making new directory')
			Path(PATH).mkdir(parents=True, exist_ok=True)
			#os.mkdir(PATH)
		else:
			print("Specify a foldername & rerun task.")
			print("Task will error trying to saving data.")

		# make a vector containing all the tau setpoints for the pulse sequence
		taus=np.linspace(starttau,stoptau,points)
		print('taus: '+str(taus))

		# loop through all the set tau value and record the PL on the qutag

		self.configureQutag()


		for i in range(points):

			tau=taus[i]

			self.dataset.clear()
			self.fungen.output[Pulsechannel] = 'OFF'
			self.fungen.output[Shutterchannel] = 'OFF'
			self.fungen.clear_mem(Pulsechannel)
			self.fungen.clear_mem(Shutterchannel)
			self.fungen.wait()
			# self.srs.module_reset[5]
			# self.srs.SIM928_voltage[5]=params['srs bias'].magnitude+0.000000001*i
			# self.srs.SIM928_on[5]

			## build pulse sequence for AWG channel 1
			chn1buffer = Arbseq_Class('chn1buffer', timestep)
			chn1buffer.delays = [0]
			chn1buffer.heights = [0]
			chn1buffer.widths = [repeat_unit]
			chn1buffer.totaltime = repeat_unit
			chn1buffer.nrepeats = buffer_time/repeat_unit
			chn1buffer.repeatstring = 'repeat'
			chn1buffer.markerstring = 'lowAtStart'
			chn1buffer.markerloc = 0
			chn1bufferwidth = repeat_unit*chn1buffer.nrepeats
			chn1buffer.create_sequence()

			chn1pulse = Arbseq_Class('chn1pulse', timestep)
			chn1pulse.delays = [0]
			chn1pulse.heights = [1]
			chn1pulse.widths = [pulse_width]
			chn1pulse.totaltime = pulse_width
			chn1pulse.nrepeats = 0
			chn1pulse.repeatstring = 'once'
			chn1pulse.markerstring = 'highAtStartGoLow'
			chn1pulse.markerloc = 0
			chn1pulsewidth = pulse_width
			chn1pulse.create_sequence()

			chn1dc = Arbseq_Class('chn1dc', timestep)
			chn1dc.delays = [0]
			chn1dc.heights = [0]
			chn1dc.widths = [repeat_unit]
			chn1dc.totaltime = repeat_unit
			chn1dc.repeatstring = 'repeat'
			chn1dc.markerstring = 'lowAtStart'
			chn1dc.markerloc = 0
			chn1dcrepeats = int((tau-1.5*pulse_width)/repeat_unit)   # tau-1.5*pulse_width 
			chn1dc.nrepeats = chn1dcrepeats
			chn1dcwidth = repeat_unit*chn1dcrepeats
			print(tau, pulse_width, chn1dcrepeats)
			chn1dc.create_sequence()
		
			chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
			chn1pulse2.delays = [0]
			chn1pulse2.heights = [1]
			chn1pulse2.widths = [pulse_width*2]
			chn1pulse2.totaltime = pulse_width*2 
			chn1pulse2width = pulse_width*2
			chn1pulse2.nrepeats = 0
			chn1pulse2.repeatstring = 'once'
			chn1pulse2.markerstring = 'lowAtStart'
			chn1pulse2.markerloc = 0
			chn1pulse2.create_sequence()
		
			chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
			chn1pulse3.delays = [0]
			chn1pulse3.heights = [0]
			chn1pulse3.widths = [repeat_unit]
			chn1pulse3.totaltime = repeat_unit 
			chn1pulse3width = shutter_offset
			chn1pulse3.nrepeats = shutter_offset/repeat_unit
			chn1pulse3.repeatstring = 'repeat'
			chn1pulse3.markerstring = 'lowAtStart'
			chn1pulse3.markerloc = 0
			chn1pulse3.create_sequence()
		
			chn1dc2 = Arbseq_Class('chn1dc2', timestep)
			chn1dc2.delays = [0]
			chn1dc2.heights = [0]
			chn1dc2.widths = [repeat_unit]
			chn1dc2.totaltime = repeat_unit
			chn1dc2.repeatstring = 'repeat'
			chn1dc2.markerstring = 'lowAtStart'
			chn1dc2repeats = int((period-chn1bufferwidth-chn1pulsewidth-chn1dcwidth-chn1pulse2width-chn1pulse3width)/repeat_unit)
			chn1dc2.nrepeats = chn1dc2repeats
			chn1dc2.markerloc = 0
			#print((chn1dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
			print(params['repeat unit'].magnitude*chn1dc2.nrepeats)
			chn1dc2.create_sequence()

			## build pulse sequence for AWG channel 2
			chn2buffer = Arbseq_Class('chn2buffer', timestep)
			chn2buffer.delays = [0]
			chn2buffer.heights = [0]
			chn2buffer.widths = [repeat_unit]
			chn2buffer.totaltime = repeat_unit
			chn2buffer.nrepeats = buffer_time/repeat_unit
			chn2buffer.repeatstring = 'repeat'
			chn2buffer.markerstring = 'lowAtStart'
			chn2buffer.markerloc = 0
			chn2bufferwidth = repeat_unit*chn2buffer.nrepeats
			chn2buffer.create_sequence()

			chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
			chn2pulse1.delays = [0]
			chn2pulse1.heights = [0]
			chn2pulse1.widths = [pulse_width]
			chn2pulse1.totaltime = pulse_width
			chn2pulse1width = pulse_width
			chn2pulse1.nrepeats = 0
			chn2pulse1.repeatstring = 'once'
			chn2pulse1.markerstring = 'highAtStartGoLow'
			chn2pulse1.markerloc = 0
			chn2pulse1.create_sequence()

			chn2dc1 = Arbseq_Class('chn2dc1', timestep)
			chn2dc1.delays = [0]
			chn2dc1.heights = [0]
			chn2dc1.widths = [repeat_unit]
			chn2dc1.totaltime = repeat_unit
			chn2dc1.repeatstring = 'repeat'
			chn2dc1.markerstring = 'lowAtStart'
			chn2dc1.markerloc = 0
			chn2dc1repeats = int((tau-1.5*pulse_width)/repeat_unit)
			chn2dc1.nrepeats = chn2dc1repeats
			chn2dc1width = repeat_unit*chn2dc1repeats
			chn2dc1.create_sequence()
	
			chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
			chn2pulse2.delays = [0]
			chn2pulse2.heights = [0]
			chn2pulse2.widths = [pulse_width*2]
			chn2pulse2.totaltime = pulse_width*2
			chn2pulse2width = pulse_width*2
			chn2pulse2.nrepeats = 0
			chn2pulse2.repeatstring = 'once'
			chn2pulse2.markerstring = 'lowAtStart'
			chn2pulse2.markerloc = 0
			chn2pulse2.create_sequence()

			chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
			chn2pulse3.delays = [0]
			chn2pulse3.heights = [0]
			chn2pulse3.widths = [repeat_unit]
			chn2pulse3.totaltime = repeat_unit
			chn2pulse3width = shutter_offset
			chn2pulse3.nrepeats = shutter_offset/repeat_unit
			chn2pulse3.repeatstring = 'repeat'
			chn2pulse3.markerstring = 'lowAtStart'
			chn2pulse3.markerloc = 0
			chn2pulse3.create_sequence()

			chn2dc2 = Arbseq_Class('chn2dc2', timestep)
			chn2dc2.delays = [0]
			chn2dc2.heights = [1]
			chn2dc2.widths = [repeat_unit]
			chn2dc2.totaltime = repeat_unit
			chn2dc2.repeatstring = 'repeat'
			chn2dc2.markerstring = 'lowAtStart'
			chn2dc2repeats = int((period-chn2bufferwidth-chn2pulse1width-chn2dc1width-chn2pulse2width-chn2pulse3width)/repeat_unit)
			chn2dc2.nrepeats = chn2dc2repeats
			chn2dc2.markerloc = 0
			print(repeat_unit*chn2dc2.nrepeats)
			chn2dc2.create_sequence()

			self.fungen.send_arb(chn1buffer, Pulsechannel)
			self.fungen.send_arb(chn1pulse, Pulsechannel)
			self.fungen.send_arb(chn1dc, Pulsechannel)
			self.fungen.send_arb(chn1pulse2, Pulsechannel)
			self.fungen.send_arb(chn1pulse3, Pulsechannel)
			self.fungen.send_arb(chn1dc2, Pulsechannel)
			self.fungen.send_arb(chn2buffer, Shutterchannel)
			self.fungen.send_arb(chn2pulse1, Shutterchannel)
			self.fungen.send_arb(chn2dc1, Shutterchannel)
			self.fungen.send_arb(chn2pulse2, Shutterchannel)
			self.fungen.send_arb(chn2pulse3, Shutterchannel)
			self.fungen.send_arb(chn2dc2, Shutterchannel)

			seq = [chn1buffer, chn1pulse, chn1dc, chn1pulse2, chn1pulse3, chn1dc2]
			seq2 = [chn2buffer, chn2pulse1, chn2dc1, chn2pulse2, chn2pulse3, chn2dc2]
			
			self.fungen.create_arbseq('twoPulse', seq, Pulsechannel)
			self.fungen.create_arbseq('shutter', seq2, Shutterchannel)
			self.fungen.wait()
			self.fungen.voltage[Pulsechannel] = params['pulse height'].magnitude+0.000000000001*i
			# self.fungen.voltage[2] = 7.1+0.0000000000001*i
			self.fungen.voltage[Shutterchannel] = params['shutter height'].magnitude+0.0000000000001*i

			
			print(self.fungen.voltage[Pulsechannel], self.fungen.voltage[Shutterchannel])


			self.fungen.output[Shutterchannel] = 'ON' ## turn on the shutter channel before send the laser pulse
			self.fungen.trigger_delay(Pulsechannel,shutter_offset)
			self.fungen.sync()
			time.sleep(2)
			self.fungen.output[Pulsechannel] = 'ON'
			time.sleep(2)
			


			# home the laser
			self.homelaser(wl)
			print('Laser Homed!')

			##Qutag Part
			self.configureQutag()
			qutagparams = self.qutag_params.widget.get()
			lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
			stoptimestamp = 0
			synctimestamp = 0
			bincount = qutagparams['Bin Count']
			timebase = self.qutag.getTimebase()
			start = qutagparams['Start Channel']
			stop = qutagparams['Stop Channel']

			# stoparray = []
			# tempStopArray = []
			# histCounter = 0
			# quenchCounter = 0
			
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
			print('current tau: '+str(tau))
			print('current target wavelength: '+str(wl))
			print('actual wavelength: '+str(self.wm.measure_wavelength()))
			time.sleep(1)

			stoparray = []
			startTime = time.time()
			wls=[]
			savetaus=[]

			self.hist = [0]*bincount
			self.bins=list(range(len(self.hist)))			
			self.times=list(np.linspace(0,wholeRange,len(self.hist)))   ## convert the x axis from bin numbers to time 
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
				savetaus.append(float(tau))
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
					binNumber = int(tdiff*timebase*bincount/(wholeRange))
					if binNumber<bincount:
						self.hist[binNumber]+=1
				stopscheck=[]

				values = {
					#'x': self.bins,
					'x': self.times,
					'y': self.hist,
				}

				self.twopulseecho.acquire(values)

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

			self.createHistogram(stoparray, timebase, bincount, wholeRange, str(i), wls, PATH, savetaus)


			# self.initHist(bincount)
			# for j in range(int(self.exp_parameters.widget.get()['# of Passes'])):
			# 	lost = self.qutag.getLastTimestamps(True)
			# 	time.sleep(period)
			# 	timestamps = self.qutag.getLastTimestamps(True)

			# 	tstamp = timestamps[0] # array of timestamps
			# 	tchannel = timestamps[1] # array of channels
			# 	values = timestamps[2] # number of recorded timestamps
			# 	# print(values)
			# 	for k in range(values):
			# 		# output all stop events together with the latest start event
			# 		# if tchannel[k] == start:
			# 		# 	synctimestamp = tstamp[k]
			# 		if tchannel[k]==stop:
			# 			#stoptimestamp = tstamp[k]
			# 		# if tstamp[k]*1e-6>2*tau.magnitude-1 and tstamp[k]*1e-6<2*tau.magnitude+2:
			# 			stoparray.append(tstamp[k])
			# 			#tempStopArray.append(stoptimestamp)
			# 	# histCounter+=1
			# 	# if histCounter%20==0:
			# 	# 	self.createPlottingHist(tempStopArray, timebase, bincount,qutagparams['Total Hist Width Multiplier']*tau.magnitude)
			# 	# 	self.xs = np.asarray(range(len(self.hist)))
			# 	# 	self.ys=np.asarray(self.hist)
			# 	# 	values = {
			# 	# 	't': np.asarray(range(len(self.hist))),
			# 	# 	'y': np.asarray(self.hist),
			# 	# 	}
			# 	# 	self.startpulse.acquire(values)
			# 	# 	tempStopArray = []
			# 		# TODO: quench protection
			# 		# if self.srs.SIM928_voltage[???] >= qunech threshold and quenchCounter<=10:
			# 		# 	self.srs.SIM928_off[6]
			# 		# 	time.sleep(period*10)
			# 		# 	self.srs.SIM928_on[6]
			# 		# 	quenchCounter+=1
			# 		# elif quenchCounter>10:
			# 		# 	print('quenched more than 10 times')
			# 		# 	break
			# 		# else:
			# 		# 	continue
					
			# self.createHistogram(stoparray, timebase, bincount,wholeRange,tau.magnitude)
			# print("here")


			self.fungen.output[Pulsechannel] = 'OFF'
			self.fungen.output[Shutterchannel] = 'OFF'

		self.fungen.output[Pulsechannel]='OFF'  ##turn off the AWG for both channels
		self.fungen.output[Shutterchannel]='OFF'
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
			time.sleep(0.5)
			#print(self.Voltmeter.acquired)
		return 

	# sets up some formatting of the voltmeter
	@Element(name='indicator')
	def voltmeter(self):
		text = QTextEdit()
		text.setPlainText('Voltage 1: non V \nVoltage 2: non V\n')
		return text

	# more formatting of the voltage units
	@voltmeter.on(Voltmeter.acquired)
	def _voltmeter_update(self,ev):
		w=ev.widget
		w.setPlainText('Voltage 1: %f V \nVoltage 2: %f V \n'%(self.v1,self.v2))
		return

	# the 1D plot widget is used for the live histogram
	@Element(name='twopulseecho Histogram')
	def twopulseecho_Histogram(self):
		p = LinePlotWidget()
		p.plot('twopulseecho Histogram')
		return p

	# more code for the histogram plot
	@twopulseecho_Histogram.on(twopulseecho.acquired)
	def _twopulseecho_Histogram_update(self, ev):
		w = ev.widget
		# cut off pulse in display
		xs = np.array(self.times)
		ys = np.array(self.hist)
		w.set('twopulseecho Histogram',xs=xs,ys=ys)
		return


	@Task()
	def qutagInit(self):
		print('qutag successfully initialized')


	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Bin Count', {'type': int, 'default': 500}),   ## define bin numbers in the measurement time window
		('Voltmeter Channel 1',{'type':int,'default':1}),
		('Voltmeter Channel 2',{'type':int,'default':2}),
		('Battery Port 1',{'type':int,'default':5}),
		('Battery Port 2',{'type':int,'default':6})
		]
		w = ParamWidget(params)
		return w

	@Element(name='twopulse parameters')
	def twopulse_parameters(self):
		params = [
		('Runtime',{'type':float,'default':600,'units':'s'}),
		#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('pulse height', {'type': float, 'default': 3.5, 'units':'V'}),
		('shutter height', {'type': float, 'default': 2.0, 'units':'V'}),
		('pulse width', {'type': float, 'default': 400e-9, 'units':'s'}),  ## define the pi/2 pulse width
		('period', {'type': float, 'default': 1e-3, 'units':'s'}),
		('repeat unit', {'type': float, 'default': 50e-9, 'units':'s'}),
		('start tau', {'type': float, 'default': 5e-6, 'units':'s'}),
		('stop tau', {'type': float, 'default': 20e-6, 'units':'s'}),
		('step tau', {'type': float, 'default': 1e-6, 'units':'s'}),
		('# of points',{'type':int,'default':16}),
		# ('srs bias', {'type': float, 'default': 1.2, 'units':'V'}),
		('measuring range', {'type': float, 'default': 50e-6, 'units':'s'}),
		('shutter offset', {'type': float, 'default': 1e-6, 'units':'s'}), ## buffer time & shutter offset is to compensate any delay for the shutter (AOM)
		('buffer time', {'type': float, 'default': 4e-6, 'units':'s'}),
		('Shutter channel',{'type':int,'default':2}),
		('Pulse channel',{'type':int,'default':1}),
		('Wavelength',{'type':float,'default':1535.6324}),
		('File Name',{'type':str}),
		]
		w = ParamWidget(params)
		return w

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

	@twopulseecho.initializer
	def initialize(self):
		self.fungen.output[2] = 'OFF'
		self.fungen.output[1] = 'OFF'
		self.fungen.clear_mem(2)
		self.fungen.clear_mem(1)
		self.fungen.wait()

	@twopulseecho.finalizer
	def finalize(self):
		self.fungen.output[2] = 'OFF'
		self.fungen.output[1] = 'OFF'
		print('Two Pulse measurements complete.')
		return