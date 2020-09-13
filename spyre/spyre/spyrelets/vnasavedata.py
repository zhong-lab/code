import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import os

from lantz.drivers.VNA import E5071B
from lantz.log import log_to_screen, DEBUG

class VNASaveData(Spyrelet):
    
    requires = {
        'vna': E5071B
    }

    @Task()
    def set(self):
        self.dataset.clear()
        log_to_screen(DEBUG)

        print('The identification number of this instrument is :' + str(self.vna.idn))

        day = self.vna.day     
        hours = self.vna.hours
        minutes = self.vna.minutes    

        time0 = float(day)*24*60 + float(hours)*60 + float(minutes)

        print("Time0 {}".format(time0))


        totaltime = 48*60  #Total time in hours
        sleeptime = 10   # Sleep time in minutes
        deltatime = 0
        self.vna.set_average(1,'OFF')   
        self.vna.set_average(1,'ON')
        time.sleep(sleeptime*60)

        while (deltatime<totaltime):       


            day = self.vna.day     
            hours = self.vna.hours
            minutes = self.vna.minutes  

            currentime = float(day)*24*60 + float(hours)*60 + float(minutes)
            deltatime = currentime - time0

            trace = 1

            self.vna.set_active_trace(1,trace)


            filename='HAO/port_14_{}_{}_{}_{}.csv'.format(trace,day,hours,minutes)

            self.vna.save_csv(filename)

            trace = 2

            self.vna.set_active_trace(1,trace)

            filename='HAO/port_24_{}_{}_{}_{}.csv'.format(trace,day,hours,minutes)

            self.vna.save_csv(filename)

            self.vna.set_average(1,'OFF')
            self.vna.set_average(1,'ON')

            time.sleep(sleeptime*60)



    @set.initializer
    def initialize(self):
        print('initialize')
        print('idn: {}'.format(self.vna.idn))
        return

    @set.finalizer
    def finalize(self):
        print('finalize')
        return

  