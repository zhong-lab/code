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
        #'wm': Bristol_771,
        #'fungen': Keysight_33622A
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
        print('Data stored under File Name: ' + self.exp_parameters.widget.get()['File Name'] + str(index))

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
    def piezo_scan(self,timestep=100e-9):
        

        piezo_params=self.piezo_parameters.widget.get()
        Vstart=piezo_params['voltage start']
        Vstop=piezo_params['voltage end']
        pts=piezo_params['scan points']

        voltageTargets=np.linspace(Vstart,Vstop,pts)
        reversedTargets=voltageTargets[::-1]
        voltageTargets=reversedTargets
        filename=str(Vstart)+str(Vstop)

        print('voltageTargets: '+str(voltageTargets))


        channel=piezo_params['AWG channel']

        # # turn off AWG
        # self.fungen.output[channel]='OFF'

        # ##Qutag Part
        # self.configureQutag()
        # expparams = self.exp_parameters.widget.get()
        # wlparams = self.wl_parameters.widget.get()

        # # AWG Output on
        # self.fungen.output[channel]='ON'
        #self.fungen.waveform[channel]='DC'
        for i in range(len(voltageTargets)):
            print(voltageTargets[i])
            #self.fungen.offset[channel]=voltageTargets[i]
            time.sleep(1)
            # measure the wavelength
            #wl_meas=self.wm.measure_wavelength()
            # write this to a .CSV file
            with open(filename+'.csv', 'w') as csvfile:
                CSVwriter= csv.writer(csvfile, delimiter=' ',quotechar='|',quoting=csv.QUOTE_MINIMAL)
                CSVwriter.writerow(voltageTargets[i])
        #self.fungen.output[channel]='OFF'











        # drive to the offset estimated by the piezo voltage
        # 1MOhm impedance of laser mismatch with 50Ohm impedance of AWG
        # multiplies voltage 2x
        # 140V ~ 40GHz ~ 315pm

        # piezo_range=(Vstop.magnitude-Vstart.magnitude)*0.315/(140)*piezo_params['Scale factor'] #pm
        # print('piezo_range: '+str(piezo_range)+str(' nm'))

        # wl_start=wlparams['start']-piezo_range
        # wl_stop=wlparams['stop']+piezo_range
        # wlpts=np.linspace(wl_start,wl_stop,pts)

        # self.homelaser(wlparams['start']-piezo_range)
        # print('Laser Homed!')
        # qutagparams = self.qutag_params.widget.get()
        # lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
        # stoptimestamp = 0
        # synctimestamp = 0
        # bincount = qutagparams['Bin Count']
        # timebase = self.qutag.getTimebase()
        # start = qutagparams['Start Channel']
        # stop = qutagparams['Stop Channel']

        # PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']
        # if (os.path.exists(PATH)):
        #   print('deleting old directory with same name')
        #   os.system('rm -rf '+str(PATH))
        # print('making new directory')
        # Path(PATH).mkdir(parents=True, exist_ok=True)

        # # turn on AWG
        # self.fungen.output[channel]='ON'

        # last_wl=self.wm.measure_wavelength()
        # wls=[]
        # totalShift=0

        # for i in range(pts):
        #   print(i)
        #   if (voltageTargets[i]>5) or (voltageTargets[i]<-5):
        #       newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
        #       voltageTargets=newTargets
        #       totalShift=newShift

        #   self.fungen.offset[channel]=Q_(voltageTargets[i],'V')
        #   wl=self.wm.measure_wavelength()
        #   counter=0
        #   if len(wls)!=0:
        #       last_wl=np.mean(np.array(wls).astype(np.float))
            
        #   print('i: '+str(i)+', initializing')

        #   while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)):
        #           offset=wl-wlpts[i]
        #           Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
        #           if offset<0:
        #               if voltageTargets[i]+Voff<-5:
        #                   newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
        #                   voltageTargets=newTargets
        #                   totalShift=newShift
        #                   print('AWG limit exceeded, resetting voltage targets')
        #               else:
        #                   newTargets=[j+Voff for j in voltageTargets]
        #                   voltageTargets=newTargets
        #                   self.fungen.offset[channel]=Q_(newTargets[i],'V')
        #                   time.sleep(3)
        #                   wl=self.wm.measure_wavelength()
        #                   counter+=Voff
        #                   totalShift+=Voff
        #           else:
        #               if voltageTargets[i]+Voff>5:
        #                   newTargets,newShift,wl=self.resetTargets(voltageTargets,totalShift,i,channel)
        #                   voltageTargets=newTargets
        #                   totalShift=newShift
        #                   print('AWG limit exceeded, resetting voltage targets')
        #               else:
        #                   newTargets=[j+Voff for j in voltageTargets]
        #                   voltageTargets=newTargets
        #                   self.fungen.offset[channel]=Q_(newTargets[i],'V')
        #                   time.sleep(3)
        #                   wl=self.wm.measure_wavelength()
        #                   counter+=Voff
        #                   totalShift+=Voff

        #   print('taking data')
        #   print('current target wavelength: '+str(wlpts[i]))
        #   print('current set voltage: '+str(voltageTargets[i]))
        #   print('actual wavelength: '+str(self.wm.measure_wavelength()))
            
        #   time.sleep(1)
        #   ##Wavemeter measurements
        #   stoparray = []
        #   startTime = time.time()
        #   wls=[]
        #   lost = self.qutag.getLastTimestamps(True)
        #   counter2=0

        #   looptime=startTime
        #   while looptime-startTime < expparams['Measurement Time'].magnitude:
        #       loopstart=time.time()
        #       # get the lost timestamps
        #       lost = self.qutag.getLastTimestamps(True)
        #       # wait half a milisecond
        #       time.sleep(5*0.1)
        #       # get thte timestamps in the last half milisecond
        #       timestamps = self.qutag.getLastTimestamps(True)

        #       tstamp = timestamps[0] # array of timestamps
        #       tchannel = timestamps[1] # array of channels
        #       values = timestamps[2] # number of recorded timestamps

        #       for k in range(values):
        #           # output all stop events together with the latest start event
        #           if tchannel[k] == start:
        #               synctimestamp = tstamp[k]
        #           else:
        #               stoptimestamp = tstamp[k]
        #               stoparray.append(stoptimestamp)
        #       wl=self.wm.measure_wavelength()
        #       wls.append(str(wl))
        #       looptime+=time.time()-loopstart
        #       #print('i: '+str(i)+', looptime-startTime: '+str(looptime-startTime))

                
        #       while ((wl<wlpts[i]-0.0002) or (wl>wlpts[i]+0.0002)) and (time.time()-startTime < expparams['Measurement Time'].magnitude):
        #           offset=wl-wlpts[i]
        #           Voff=offset/0.315*140/(piezo_params['Scale factor']*2)
        #           if offset<0:
        #               if voltageTargets[i]+Voff<-5:
        #                   break
        #               else:
        #                   newTargets=[j+Voff for j in voltageTargets]
        #                   voltageTargets=newTargets
        #                   self.fungen.offset[channel]=Q_(newTargets[i],'V')
        #                   time.sleep(3)
        #                   wl=self.wm.measure_wavelength()
        #                   counter2+=Voff
        #                   totalShift+=Voff
        #           else:
        #               if voltageTargets[i]+Voff>5:
        #                   break
        #               else:
        #                   newTargets=[j+Voff for j in voltageTargets]
        #                   voltageTargets=newTargets
        #                   self.fungen.offset[channel]=Q_(newTargets[i],'V')
        #                   time.sleep(3)
        #                   wl=self.wm.measure_wavelength()
        #                   counter2+=Voff
        #                   totalShift+=Voff
                
        #   print('actual  wavelength: '+str(wl))
        #   print('targets shift during measurement:  '+str(counter2)+'V')
                

        #   self.createHistogram(stoparray, timebase, bincount,expparams['AWG Pulse Repetition Period'].magnitude,i, wls)
        # # turn off AWG
        

        #####don't need pulse for fiber filter
    # @Task()
    # def startpulse(self, timestep=100e-9):

    #   ##Qutag Part
    #   self.configureQutag()
    #   expparams = self.exp_parameters.widget.get()
    #   wlparams = self.wl_parameters.widget.get()
    #   self.homelaser(wlparams['start'])
    #   print('Laser Homed!')
    #   qutagparams = self.qutag_params.widget.get()
    #   lost = self.qutag.getLastTimestamps(True) # clear Timestamp buffer
    #   stoptimestamp = 0
    #   synctimestamp = 0
    #   bincount = qutagparams['Bin Count']
    #   timebase = self.qutag.getTimebase()
    #   start = qutagparams['Start Channel']
    #   stop = qutagparams['Stop Channel']

    #   PATH="D:\\Data\\"+self.exp_parameters.widget.get()['File Name']+"\\motor_scan"
    #   if (os.path.exists(PATH)):
    #       print('deleting old directory with same name')
    #       os.system('rm -rf '+str(PATH))
    #   print('making new directory')
    #   Path(PATH).mkdir(parents=True, exist_ok=True)
    #   #os.mkdir(PATH)

    #   wlTargets=np.linspace(wlparams['start'],wlparams['stop'],expparams['# of points'])
        

    #   print('wlTargets: '+str(wlTargets))
    #   for i in range(expparams['# of points']):
    #       print(i)
    #       with Client(self.laser) as client:

    #           setting=client.get('laser1:ctl:wavelength-set', float)
    #           client.set('laser1:ctl:wavelength-set', wlTargets[i])
    #           print('current target wavelength: '+str(wlTargets[i]))
    #           print('actual wavelength: '+str(self.wm.measure_wavelength()))
    #           time.sleep(1)
    #       ##Wavemeter measurements
    #       stoparray = []
    #       startTime = time.time()
    #       wls=[]
    #       lost = self.qutag.getLastTimestamps(True)
    #       while time.time()-startTime < expparams['Measurement Time'].magnitude:
    #           lost = self.qutag.getLastTimestamps(True)
    #           time.sleep(5*0.1)
    #           timestamps = self.qutag.getLastTimestamps(True)

    #           tstamp = timestamps[0] # array of timestamps
    #           tchannel = timestamps[1] # array of channels
    #           values = timestamps[2] # number of recorded timestamps
    #           for k in range(values):
    #               # output all stop events together with the latest start event
    #               if tchannel[k] == start:
    #                   synctimestamp = tstamp[k]
    #               else:
    #                   stoptimestamp = tstamp[k]
    #                   stoparray.append(stoptimestamp)
    #           wls.append(str(self.wm.measure_wavelength()))

    #       self.createHistogram(stoparray, timebase, bincount,expparams['AWG Pulse Repetition Period'].magnitude,i, wls)
            

    @Task()
    def qutagInit(self):
        print('qutag successfully initialized')

    # @Element(name='Wavelength parameters')
    # def wl_parameters(self):
    #     params = [
    # #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
    #     ('start', {'type': float, 'default': 1535}),
    #     ('stop', {'type': float, 'default': 1536})
    #     ]
    #     w = ParamWidget(params)
    #     return w

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

    # @Element(name='Experiment Parameters')
    # def exp_parameters(self):
    #     params = [
    # #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
    #     ('# of points', {'type': int, 'default': 100}),
    #     ('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
    #     ('File Name', {'type': str}),
    #     ('AWG Pulse Repetition Period',{'type': float,'default': 0.01,'units':'s'}),
    #     ('# of Passes', {'type': int, 'default': 100})
    #     ]
    #     w = ParamWidget(params)
    #     return w

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

    # @startpulse.initializer
    # def initialize(self):
    #     self.wm.start_data()

    # @startpulse.finalizer
    # def finalize(self):
    #     self.wm.stop_data()
    #     print('Lifetime measurements complete.')
    #     return

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