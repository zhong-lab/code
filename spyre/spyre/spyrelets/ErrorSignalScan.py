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


    def slope(self,freq,dev,center,span,step):
        self.dataset.clear()
        log_to_screen(DEBUG)

        self.lockin.Internal_Frequency=freq * Hz
        

        frequency_start = center-span*0.5
        frequency_stop = center+span*0.5
        frequency_step = step 
        rf_power=-20  #Power in dBm
        time_constant=0.1 # Use 0.3, 0.1 , 1 or 3 sec only
        self.lockin.Set_Time_Constant(time_constant)  



        self.source.set_CW_mode()
        
        self.source.FM_ON()
        self.source.FM_Deviation(dev)
        self.source.external_FM()
        self.source.set_RF_Power(rf_power)

        self.source.RF_ON()
        self.source.Mod_ON()

        time.sleep(5)

        file = open('D:/MW data/20200127/slope/2/{}_{}.txt'.format(freq,dev),'w') 


        frequency=frequency_start
        while(frequency<frequency_stop):

            self.source.set_CW_Freq(frequency)
            time.sleep(3*time_constant)    #Wait long enough for the averaging due to lock in amplifier time constant to complete. in 5 time constant the capacitor is at least 99% discharged
            buffer_D = self.lockin.Data_Four
            part = buffer_D.split(',')

            XValue = part[0]
            YValue = part[1]
            RValue = part[2]
            thetaValue = part[3]

            write_str='%s %s %s %s %f\n'%(part[0],part[1],part[2],part[3],frequency)
            file.write(write_str)

            time.sleep(0.2)    #Wait for file IO to complete
            frequency=frequency+frequency_step
        file.close()  

        return



    @Task()
    def Scan_Dev_Freq(self):

        # devStart=50e3
        # devStop=3e6
        # devStep=100e3
        # freqStart=1e3
        # freqStop=3e6
        # freqStep=1e3
        devStart=250e3
        devStop=260e3
        devStep=100e3
        freqStart=1e3
        freqStop=2e3
        freqStep=1e3        
        center=4.9605e9
        span=2e6
        step=0.025e6
        # for dev in np.logspace(5,6.47,10):            
        #     for freq in np.logspace(3,5.3,10):
        #         self.slope(freq,dev,center,span,step)

        self.slope(61e3,655e3,center,span,step)       
        return

    @Scan_Dev_Freq.initializer
    def initialize(self):
        return

    @Scan_Dev_Freq.finalizer
    def finalize(self):
        return  
