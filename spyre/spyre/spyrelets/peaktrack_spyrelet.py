import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
import os
from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget,LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz import Q_

from lantz.drivers.ando.aq6317b import AQ6317B
from lantz.drivers.artisan.ldt5910b import LDT5910B

class filter(Spyrelet):
    # delete if not using power meter
    requires = {
        'osa':AQ6317B,
        'tc':LDT5910B
    }

    @Task()
    def track(self):
        # unpack the parameters
        params=self.parameters.widget.get()
        filename=params['Filename']
        tracktime=params['Track time'].magnitude #s
        sleep=params['Sleep Interval'].magnitude #s

        # read peak position for a while
        start=time.time()
        t=start
        with open(filename+'.csv','w',newline='') as csvfile:
            writer=csv.writer(
                csvfile,
                delimiter=',',
                quotechar='|',
                quoting=csv.QUOTE_MINIMAL)
            while (t-start)<tracktime:
                pk,pwr=self.osa.read_marker
                temp=self.tc.display('T')
                t=time.time()
                print('t: '+str(t-start)+', '+str(pk)+', '+str(temp))
                writer.writerow([t-start,pk,temp])
                time.sleep(sleep)
        return

    @Element(name='Params')
    def parameters(self):
        params = [
        ('Sleep Interval',{'type':int,'default':10,'units':'s'}),
        ('Track time', {'type': int, 'default': 1200,'units':'s'}),
        ('Filename', {'type': str, 'default':'Q:\\06.02.21_ff\\track1'})
        ]
        w = ParamWidget(params)
        return w
