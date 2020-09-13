#Spyrelet for Scanning FM Freq and FM Deviation for getting the optimum settings for EPR
import numpy as np
import pyqtgraph as pg
import time
import random
import matplotlib.pyplot as plt
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget,HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import os

from lantz.drivers.lockin import SR865A
from lantz.drivers.keysight import N5181A
from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

class Record(Spyrelet):
    
    requires = {
        'lockin': SR865A,
        'source':N5181A,
    }
    time_s=[]
    X_s=[]
    Y_s=[]
    R_s=[]
    theta_s=[]


    def Record_ESR(self,FMfreq,dev,center,scantime,time_constant,rf_power):
        self.dataset.clear()
        log_to_screen(DEBUG)

        time0 = self.lockin.System_Time_Day*24*3600+self.lockin.System_Time_Hours*3600+self.lockin.System_Time_Min*60+self.lockin.System_Time_Seconds

        t = 0

        self.lockin.Internal_Frequency=FMfreq * Hz
        self.lockin.Set_Time_Constant(time_constant)  

        
        self.source.set_CW_mode()
        self.source.set_CW_Freq(center)
        self.source.FM_ON()
        self.source.FM_Deviation(dev)
        self.source.external_FM()
        self.source.set_RF_Power(rf_power)

        self.source.RF_ON()
        self.source.Mod_ON()

        time.sleep(5)

        file = open('D:/MW data/20200614/ESR/esr/3/scan.txt','w') 


        
        while(t<scantime):

            
            time.sleep(5*time_constant)    #Wait long enough for the averaging due to lock in amplifier time constant to complete. in 5 time constant the capacitor is at least 99% discharged
 
            t = (self.lockin.System_Time_Day*24*3600+self.lockin.System_Time_Hours*3600+self.lockin.System_Time_Min*60+self.lockin.System_Time_Seconds) - time0
            buffer_D = self.lockin.Data_Four
            part = buffer_D.split(',')

            XValue = part[0]
            YValue = part[1]
            RValue = part[2]
            thetaValue = part[3]

            write_str='%s %s %s %s %f\n'%(part[0],part[1],part[2],part[3],t)
            file.write(write_str)
            time.sleep(0.2)    #Wait for file IO to complete
        file.close()  

        self.source.RF_OFF()
        self.source.Mod_OFF()
        return



    @Task()

    def Record_data(self):

        time_constant=0.3 # Use 0.3, 0.1 , 1 or 3 sec only 
        rf_power=-10  #Power in dBm  

        dev=655e3
        freq=61e3    
        center=4.961096660e9
        scantime=10*60*60 #Scantime in seconds
        B0=0
        B1=600
        self.Record_ESR(freq,dev,center,scantime,time_constant,rf_power)

        file = open('D:/MW data/20200614/ESR/esr/3/simulationdata.txt','w') 
        file.write('FMFreq(Hz)\tFMDev(Hz)\tCenterFreq(Hz)\tScantime(s)\tBi(mT)\tBf(mT)\tTime_Constant(s)\tRF_Power(dBm)\n')
        write_str='{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(freq,dev,center,scantime,B0,B1,time_constant,rf_power)
        file.write(write_str)
        file.close()
        return




    @Record_data.initializer
    def initialize(self):
        return

    @Record_data.finalizer
    def finalize(self):
        return  
