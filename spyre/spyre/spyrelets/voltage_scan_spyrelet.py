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
from lantz.drivers.keysight import SDG2122X
from lantz.drivers.qutools import QuTAG


#from lantz.drivers.keysight import Arbseq_Class_MW
#from lantz.drivers.keysight import Keysight_33622A
#from lantz.drivers.stanford import DG645

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

class fiberfilter_scan(Spyrelet):
    requires = {
        #'wm': Bristol_771,
        'fungen': SDG2122X
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


    def volt_to_wavelength(volt):
        return (1530.3614+volt*5.489)



    @Task()
    def qutagInit(self):
        print('qutag successfully initialized')

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


    @Task()
    def piezo_scan(self,timestep=100e-9):
        

        piezo_params=self.piezo_parameters.widget.get()
        Vstart=piezo_params['voltage start']
        Vstop=piezo_params['voltage end']
        pts=piezo_params['scan points']

        voltageTargets=np.linspace(Vstart,Vstop,pts)
        wavelength=1530.3614+voltageTargets*5.489
        filename=piezo_params['Filename']
        F =open(filename+'.dat','w')
        f=filename+'\'.dat'
        F2 = open(f,'w')

        #print('voltageTargets: '+str(voltageTargets))


        channel=piezo_params['AWG channel']
        self.fungen.waveform(channel,'DC')
        self.fungen.turnon(channel)



        ##Qutag Part
        #self.configureQutag()
        qutagparams = self.qutag_params.widget.get()
        start = qutagparams['Start Channel']
        stop_1 = qutagparams['Stop Channel']
        self.qutag.setSignalConditioning(start,self.qutag.SIGNALCOND_MISC,True,0.1)
        self.qutag.enableChannels((start,stop_1))

        # # AWG Output on
        # self.fungen.output[channel]='ON'
        #self.fungen.waveform[channel]='DC'
        for i in range(len(voltageTargets)):
            print(voltageTargets[i],wavelength[i])
            F.write("%f,"%wavelength[i])
            lost = self.qutag.getLastTimestamps(True)
            #self.fungen.offset[channel]=voltageTargets[i]
            self.fungen.offset(channel,voltageTargets[i])
            time.sleep(0.1)
            timestamps = self.qutag.getLastTimestamps(True)
            tstamp = timestamps[0] # array of timestamps
            tchannel = timestamps[1] # array of channels
            values = timestamps[2] # number of recorded timestamps
            countrate=values
            print(values)
            F2.write("%f,"%countrate)
            # measure the wavelength
            #wl_meas=self.wm.measure_wavelength()
            # write this to a .CSV file
            # with open(filename+'.csv', 'w') as csvfile:
            #     CSVwriter= csv.writer(csvfile, delimiter=' ',quotechar='|',quoting=csv.QUOTE_MINIMAL)
            #     CSVwriter.writerow(voltageTargets[i])
        #self.fungen.output[channel]='OFF'
        return


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
            ('voltage start',{'type': float,'default':0,'units':'V'}),
            ('voltage end',{'type': float,'default':1,'units':'V'}),
            ('scan points',{'type':int,'default':100}),
            ('AWG channel',{'type':int,'default':1}),
            ('Scale factor',{'type':float,'default':17}),
            ('Filename', {'type': str, 'default':'D:\\Data\\11.04.2020_fiberfilterscan\\test'})
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
        ('Stop Channel', {'type': int, 'default': 1}),
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

    # @qutagInit.initializer
    # def initialize(self):
    #     from lantz.drivers.qutools import QuTAG
    #     self.qutag = QuTAG()
    #     devType = self.qutag.getDeviceType()
    #     print('devType: '+str(devType))
    #     if (devType == self.qutag.DEVTYPE_QUTAG):
    #         print("found quTAG!")
    #     else:
    #         print("no suitable device found - demo mode activated")
    #     print("Device timebase:" + str(self.qutag.getTimebase()))
    #     return

    # @qutagInit.finalizer
    # def finalize(self):
    #     return