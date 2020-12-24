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

from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford import DG645

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
		'wm': Bristol_771,
		'fungen': Keysight_33622A,
		'delaygen': DG645
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
		print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + '//'+str(index))

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

	@Task()
	def timeTags(self):
		""" Collects time tag data from the SNSPD after the ions are excited.
		Sends a single pulse from the AWG &  triggers time stamp collection only
		until the end of the  measurement period
		"""

		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.wait()

		SD_params=self.timeTag_params.widget.get()
		pulseWidth=timeTag_params['Pulse width'].magnitude
		pulseVoltage=timeTag_params['Pulse voltage'].magnitude
		channel=timeTag_params['Pulse channel'].magnitude
		wl=timeTag_params['Wavelength'].magnitude
		period=timeTag_params['Period'].magnitude
		filename=timeTag_params['File name'].magnitude

		# waveform type for the excitation pulse
		Wavepipulse='Square'

		# set up the pulse on the AWG as a 1 cycle burst with a pulse waveform
		self.fungen.waveform[channel]='PULS'
		self.fungen.voltage[channel]=pulseVoltage
		self.fungen.offset[channel]=0
		self.fungen.phase[channel]=0
		self.fungen.frequency[channel]=1/period
		self.fungen.pulsewidth[channel]=pulseWidth

		# waveform type for the excitation pulse
		Wavepipulse='Square'

		# set the triggering delay0
		delay0=Arbseq_Class_MW('delay0',timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0=(triggerdelay)
		delay0.setRepeats(repeatwidthdelay0)
		delay0.create_envelope()
		delay0.repeatstring='onceWaitTrig'

		# pi pulse
		piPulse=Arbseq_Class_MW('piPulse',timestep,Wavepipulse,1,pulsewidth2,
		0,0)
		piPulse.create_envelope()

		# send all the Arbs
		self.fungen.send_arb(delay0,1)
		self.fungen.send_arb(piPulse,1)

		# Make sequence
		seq=[delay0,piPulse]
		self.fungen.create_arbseq('Pulse',seq,1)
		self.fungen.wait()
		self.fungen.voltage[pulseChannel]=awgvolttage
		self.fungen.offset[pulseChannel]=0
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[pulseChannel]))

		# AWG Output on for the pulse channel
		self.fungen.output[pulseChannel]='ON'

		# set the delay generator for triggering the AWG and scope
		# want to set the start of the trigger for the pulse sequence such that
		# the pulse is centered within the shutter window
		totalSeqLen=pulseWidth
		startTime=(shutterWidth-totalSeqLen)/2
		self.delaygen.delay['A']=startTime
		self.delaygen.delay['B']=startTime+0.1e-3 # plus 100us
		self.delaygen.delay['C']=0
		self.delaygen.delay['D']=shutterWidth
		self.delaygen.delay['E']=shutterWidth
		self.delaygen.delay['F']=trigperiod-0.5e-3 # minus 500us for the delay
		self.delaygen.amplitude['CD']=Q_(shutterAmplitude,'V')
		self.delaygen.amplitude['EF']=Q_(shutterAmplitude,'V')

		# trigger source of 5 corresponds to single-shot triggering
		self.delaygen.Trigger_Source='Single Shot'

		##Qutag Part
		qutagparams = self.qutag_params.widget.get()
		stoptimestamp = 0
		bincount = qutagparams['Bin Count']
		timebase = self.qutag.getTimebase()
		start = qutagparams['Start Channel']
		stop = qutagparams['Stop Channel']

		timestamp_list = []

		startTime = time.time()
		lost = self.qutag.getLastTimestamps(True) # get the lost timestamps
		self.delaygen.send_trigger()

		while time.time()-startTime < runtime:

			#Readback timestamps from the device
	        t_s = device.getLastTimestamps(True)

			tstamp = timestamps[0] # array of timestamps
			tchannel = timestamps[1] # array of channels
			values = timestamps[2] # number of recorded timestamps

			for k in range(values):
				# output all stop events together with the latest start
				# event
				if tchannel[k] != start:
					stoptimestamp = tstamp[k]
					timestamp_list.append(stoptimestamp)

		with open('.csv', 'w') as csvfile:
    		PLwriter= csv.writer(csvfile, delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)
    		for i in range(len(timestamp_list)):
    			PLwriter.writerow([str(timestamplist[i])])


	@Task()
	def spectralDiffusion(self):
		""" Task to measure spectral diffusion on timescales < T1. Assumes that
		1 channel of the keysight AWG is sending a sine wave to an EOM. The
		amplitude of the RF drive for the EOM is set such that the sidebands
		have an equal amplitude to the pump beam. This tasks sweeps the
		frequency of the sine wave (separation of the EOM sidebands) while
		collecting PL, which can be used to determine the spectral diffusion
		linewidth since the saturation of the ions will be determined by how
		much the sidebands overlap with the spectral  diffusion lineshape.
		"""

		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.wait()

		# get the parameters for the experiment from the widget
		SD_params=self.SD_params.widget.get()
		triggerdelay=SD_params['Trigger delay'].magnitude
		startFreq=SD_params['Start frequency'].magnitude
		stopFreq=SD_params['Stop frequency'].magnitude
		trigperiod=SD_params['Period'].magnitude
		pulseWidth=SD_params['Pulse width'].magnitude
		pulseVoltage=SD_params['Pulse voltage'].magnitude
		EOMvoltage=SD_params['EOM voltage'].magnitude
		runtime=SD_params['Runtime'].magnitude
		pulseChannel=SD_params['Pulse channel'].magnitude
		EOMchannel=SD_params['EOM channel'].magnitude
		shutterWidth=SD_params['Shutter width'].magnitude
		shutterAmplitude=SD_params['Shutter amplitude'].magnitude
		wl=SD_params['Wavelength'].magnitude
		timestep=SD_params['Timestep'].magnitude
		points=SD_params['# of points'].magnitude


		# waveform type for the excitation pulse
		Wavepipulse='Square'

		# set the triggering delay0
		delay0=Arbseq_Class_MW('delay0',timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0=(triggerdelay)
		delay0.setRepeats(repeatwidthdelay0)
		delay0.create_envelope()
		delay0.repeatstring='onceWaitTrig'

		# pi pulse
		piPulse=Arbseq_Class_MW('piPulse',timestep,Wavepipulse,1,pulsewidth2,
		0,0)
		piPulse.create_envelope()

		# send all the Arbs
		self.fungen.send_arb(delay0,1)
		self.fungen.send_arb(piPulse,1)

		# Make sequence
		seq=[delay0,piPulse]
		self.fungen.create_arbseq('Pulse',seq,1)
		self.fungen.wait()
		self.fungen.voltage[pulseChannel]=awgvolttage
		self.fungen.offset[pulseChannel]=0
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[pulseChannel]))

		# AWG Output on for the pulse channel
		self.fungen.output[pulseChannel]='ON'

		# set the delay generator for triggering the AWG and scope
		# want to set the start of the trigger for the pulse sequence such that
		# the pulse is centered within the shutter window
		totalSeqLen=pulseWidth
		startTime=(shutterWidth-totalSeqLen)/2
		self.delaygen.delay['A']=startTime
		self.delaygen.delay['B']=startTime+0.1e-3 # plus 100us
		self.delaygen.delay['C']=0
		self.delaygen.delay['D']=shutterWidth
		self.delaygen.delay['E']=shutterWidth
		self.delaygen.delay['F']=trigperiod-0.5e-3 # minus 500us for the delay
		self.delaygen.amplitude['CD']=Q_(shutterAmplitude,'V')
		self.delaygen.amplitude['EF']=Q_(shutterAmplitude,'V')
		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod
		time.sleep(10)

		# set the sine wave driving the EOM on the other channel
		self.fungen.voltage[EOMchannel]=EOMvoltage
		self.fungen.offset[EOMchannel]=0
		self.fungen.phase[EOMchannel]=0
		self.fungen.waveform[EOMchannel]='SIN'

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

		PATH="D:\\Data\\"+self.SD_params.widget.get()['File name']
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)

		# make a vector containing all the frequency setpoints for the EOM
		freqs=np.linspace(startFreq,stopFreq,points)

		# now loop through all the set frequencies of the EOM modulation
		# and record the PL on the qutag
		self.fungen.output[EOMchannel]='ON'
		for i in range points:
			self.fungen.frequency[EOMchannel]=freq[i]


			stoparray = []
			startTime = time.time()
			wls=[]
			lost = self.qutag.getLastTimestamps(True)

			while time.time()-startTime < runtime:
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(5*0.1)
				timestamps = self.qutag.getLastTimestamps(True)

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps
				for k in range(values):
					# output all stop events together with the latest start
					# event
					if tchannel[k] == start:
						synctimestamp = tstamp[k]
					else:
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)
				wls.append(str(self.wm.measure_wavelength()))
				self.createHistogram(stoparray, timebase, bincount,period,
				str(i), wls)
			self.fungen.output[EOMchannel]='OFF'
			self.fungen.output[pulseChannel]='OFF'

	@Task()
	def photonEcho(self):
		""" Task to do a two-pulse photon echo experiment.
		"""

		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.wait()

		# get the parameters for the experiment from the widget
		echo_params=self.photonEcho_params.widget.get()
		repeatmag=echo_params['DC repeat unit'].magnitude
		timestep=echo_params['timestep'].magnitude
		pulsewidth1=echo_params['Pulse width 1'].magnitude
		pulsewidth2=echo_params['Pulse width 2'].magnitude
		trigperiod=echo_params['period'].magnitude
		triggerdelay=echo_params['trigger delay'].magnitude
		awgvoltage=echo_params['Voltage'].magnitude
		runtime=echo_params['Runtime'].magnitude
		tau=echo_params['tau'].magnitude
		channel=echo_params['channel'].magnitude
		shutterWidth=echo_params['shutter width'].magnitude
		shutterAmplitude=echo_params['shutter amplitude'].magnitude
		wavelength=echo_params['wavelength'].magnitude

		# Waveform type for the photon echo
		Wavepi2pulse='Square'
		Wavepipulse='Square'

		# set the triggering delay
		delay0=Arbseq_Class_MW('delay0',timestep,'DC',0,triggerdelay,0,0)
		repeatwidthdelay0=(triggerdelay)
		delay0.setRepeats(repeatwidthdelay0)
		delay0.create_envelope()
		delay0.repeatstring='onceWaitTrig'

		# pi/2 pulse
		pi2Pulse=Arbseq_Class_MW('pi2Pulse',timestep,Wavepi2pulse,1,pulsewidth1,
		0,0)
		pi2Pulse.create_envelope()

		# Delay of Tau

		delay1 = Arbseq_Class_MW('delay1', timestep,'DC',0,repeatmag,0,0)
		repeatwidthdelay1=(tau-1.0*pulsewidth1)
		delay1.setRepeats(repeatwidthdelay1)
		delay1.create_envelope()

		# pi pulse
		piPulse=Arbseq_Class_MW('piPulse',timestep,Wavepipulse,1,pulsewidth2,
		0,0)
		piPulse.create_envelope()

		# send all the Arbs
		self.fungen.send_arb(delay0,1)
		self.fungen.send_arb(pi2Pulse,1)
		self.fungen.send_arb(delay1,1)
		self.fungen.send_arb(piPulse,1)

		# Make sequence
		seq=[delay0,pi2Pulse,delay1,piPulse]
		self.fungen.create_arbseq('twoPulse',seq,1)
		self.fungen.wait()
		self.fungen.voltage[channel]=awgvolttage
		self.fungen.offset[channel]=0
		print("Voltage is {} , don't remove this line else the AWG will set the voltage to 50 mV".format(self.fungen.voltage[channel]))

		# AWG Output on
		self.fungen.output[channel]='ON'

		# set the delay generator for triggering the AWG and scope
		# want to set the start of the trigger for the pulse sequence such that
		# the pulse is centered within the shutter window
		totalSeqLen=pulsewidth1/2+pulsewidth2/2+delay
		startTime=(shutterWidth-totalSeqLen)/2
		self.delaygen.delay['A']=startTime
		self.delaygen.delay['B']=startTime+0.1e-3 # plus 100us
		self.delaygen.delay['C']=0
		self.delaygen.delay['D']=shutterWidth
		self.delaygen.delay['E']=shutterWidth
		self.delaygen.delay['F']=trigperiod-0.5e-3 # minus 500us for the delay
		self.delaygen.amplitude['CD']=Q_(shutterAmplitude,'V')
		self.delaygen.amplitude['EF']=Q_(shutterAmplitude,'V')
		self.delaygen.Trigger_Source='Internal'
		self.delaygen.trigger_rate=1/trigperiod
		time.sleep(10)

		# turn the function generator on
		self.fungen.output[channel]='ON'

		# home the laser
		self.configureQutag()
		self.homelaser(wavelength)
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

		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)

		##Wavemeter measurements
		stoparray = []
		startTime = time.time()
		wls=[]
		lost = self.qutag.getLastTimestamps(True)

		while time.time()-startTime < runtime:
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

		self.createHistogram(stoparray, timebase, bincount,period,str(tau), wls)

		self.fungen.output[channel]='OFF'



	@Task()
	def saturationPL(self,timestep=100e-9):
		""" Task to do a saturation PL measurement."""

		# home the laser
		self.configureQutag()
		expparams = self.exp_parameters.widget.get()
		power_params = self.saturationPL_params.widget.get()
		self.homelaser(power_params['wavelength'])
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

		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)

		# make a vector of all the powers that PL will be collected at
		powerTargets=np.linspace(power_params['power start'],
		powerparams['power stop'],powerparams['points'])

		# loop through powers in list
		for i in range(len(powerTargets)):
			with Client(self.laser) as client:

				# turn the power stabilization on
				client.set('laser1:power-stabilization:enabled',1)

				# change the set power
				client.set('laser1:power-stabilization:setpoint',powerTargets[i])
				print('current target power (at laser): '+str(powerTargets[i]))
				time.sleep(1)

			# collect data from the qutag
			stoparray = []
			startTime = time.time()
			powers=[]
			lost = self.qutag.getLastTimestamps(True)
			while time.time()-startTime<expparams['Measurement Time'].magnitude:
				lost = self.qutag.getLastTimestamps(True)
				time.sleep(5*0.1)
				timestamps = self.qutag.getLastTimestamps(True)

				tstamp = timestamps[0] # array of timestamps
				tchannel = timestamps[1] # array of channels
				values = timestamps[2] # number of recorded timestamps
				for k in range(values):
					# output all stop events together with the latest start
					# event
					if tchannel[k] == start:
						synctimestamp = tstamp[k]
					else:
						stoptimestamp = tstamp[k]
						stoparray.append(stoptimestamp)

				# measure the power at the laser and convert to power at sample
				with Client(self.laser) as client:
					current_power=client.get('laser1:ctl:power:power-act',float)
					sample_power=current_power*power_params['attenuation']
				powers.append(str(sample_power))


			# calculate the target power at sample
			sample_target=powerTargets[i]*attenuation
			filename=str(power_params['wavelength'])+'_'+str(sample_target)

			# write to histogram
			self.createHistogram(stoparray, timebase, bincount,
			expparams['AWG Pulse Repetition Period'].magnitude,filename,wls)



	@Task()
	def piezo_scan(self,timestep=100e-9):


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

		PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
		if (os.path.exists(PATH)):
			print('deleting old directory with same name')
			os.system('rm -rf '+str(PATH))
		print('making new directory')
		Path(PATH).mkdir(parents=True, exist_ok=True)

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


			self.createHistogram(stoparray, timebase, bincount,expparams['AWG Pulse Repetition Period'].magnitude,i, wls)
		# turn off AWG
		self.fungen.output[channel]='OFF'

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
		('AWG Pulse Repetition Period',{'type': float,'default': 0.01,'units':'s'}),
		('# of Passes', {'type': int, 'default': 100})
		]
		w = ParamWidget(params)
		return w

	@Element(name='QuTAG Parameters')
	def qutag_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Start Channel', {'type': int, 'default': 0}),
		('Stop Channel', {'type': int, 'default': 2}),
		('Total Hist Width Multiplier', {'type': int, 'default': 5}),
		('Bin Count', {'type': int, 'default': 1000})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Saturation PL experiment parameters')
	def saturationPL_params(self):
		""" Widget for get the parameters specific to the saturation PL
		measurement.

		points: number of points in the scan

		attenuation: fractional total attenuation from the laser to the sample
		"""
		params=[
		('wavelength',{'type': float,'default':1536.480,'units':'nm'}),
		('start power',{'type':float,'default':5,'units':'mW'}),
		('stop power',{'type':float,'default':55,'units':'mW'}),
		('points',{'type':float,'default':10,'units':'mW'}),
		('attenuation',{'type':float,'default':1})
		]
		w=ParamWidget(params)
		return w

	@Element(name='Photon echo experiment parameters')
	def photonEcho_params(self):
		""" Widget containing the parameters used in the photon echo experiment.

		DC repeat unit: for creating long DC delay a trick is to create small
		delay and then repeat it n number of times to create the whole long
		delay. This saves waveform memory of AWG since you can imagine the case
		when you have a really long delay.
		Dc repeat unit is the smallest dc unit so that the whole dc delay is
		this unit repeated n times

		tau: spacing between the center of each pulse
		"""

		params=[
		('DC repeat unit',{'type':float,'default':50e-6,'units':'s'}),
		('trigger delay',{'type':float,'default':32e-6,'units':'s'}),
		('timestep',{'type':float,'default':1e-6,'units':'s'}),
		('period',{'type':float,'default':100e-3,'units':'s'}),
		('Pulse width 1',{'type':float,'default':500e-6,'units':'s'}),
		('Pulse width 2',{'type':float,'default':1e-3,'units':'s'})
		('Voltage',{'type':float,'default':4,'units':'V'}),
		('Runtime',{'type':float,'default':300,'units':'s'}),
		('tau',{'type':float,'default':1.25,'units':'s'}),
		('channel',{'type':int,'default':1}),
		('shutter width',{'type':float,'default':4e-3,'units':'s'}),
		('shutter amplitude',{'type':float,'default':5,'units':'V'}),
		('wavelength',{'type':float,'default':1536.480,'units':'nm'})
		]
		w=ParamWidget(params)
		return params

	@Element(name='Spectral diffusion experiment parameters')
	def SD_params(self):
		""" Widget containing the parameters used in the spectral diffusion
		experiment.
		"""
		params=[
		('Trigger delay',{'type':float,'default':32e-6,'units':'s'}),
		('Start frequency',{'type':float,'default':5e6,'units':'Hz'}),
		('Stop frequency',{'type':float,'default':200e6,'units':'Hz'}),
		('Pulse width',{'type':float,'default':1e-3,'units','s'}),
		('Pulse voltage',{'type':float,'default':4,'units':'V'}),
		('EOM voltage',{'type':float,'default':4,'units':'V'}),
		('Runtime',{'type':float,'default':10,'units':'s'}),
		('Pulse channel',{'type':int,'default':1}),
		('EOM channel',{'type':int,'default':2}),
		('Shutter width',{'type':float,'default':4e-3,'units':'s'}),
		('Shutter amplitude',{'type':float,'default':5,'units':'V'}),
		('Wavelength',{'type':float,'default':1536.480,'units':'nm'}),
		('Timestep',{'type':float,'default':1e-6,'units':'s'}),
		('Period',{'type':float,'default':100e-3,'units':'s'}),
		('File name',{'type':str,'default':'spectral_diffusion'}),
		('# of points',{'type':int,'default':40})
		]
		w=ParamWidget(params)
		return w

	@Element(name='Time tagging experiment parameters')
	def timeTag_params(self):
		""" Widget containing parameters for the time tag collecting experiment.
		"""
		params=[
		('Trigger delay',{'type':float,'default':32e-6,'units':'s'}),
		('Pulse width',{'type':float,'default':1e-3,'units','s'}),
		('Pulse voltage',{'type':float,'default':4,'units':'V'}),
		('Pulse channel',{'type':int,'default':1}),
		('Wavelength',{'type':float,'default':1536.480,'units':'nm'}),
		('Period',{'type':float,'default':100e-3,'units':'s'}),
		('File name',{'type':str,'default':'spectral_diffusion'})
		]
		w=ParamWidget(params)
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
