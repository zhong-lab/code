import numpy as np
import os
import pyqtgraph as pg
import time
import csv
import sys
import msvcrt
import matplotlib.pyplot as plt
import threading
from numpy.fft import fft
import matplotlib.animation as anim

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from scipy.signal import spectrogram 
from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import subprocess

from lantz.drivers.gwinstek.g3303s import GPD3303S
from lantz.drivers.thorlabs.pm100d import PM100D
from numpy.fft import fft

class FiberPulling(Spyrelet):
    xs = []
    ys = []

    requires = {
        'gpd': GPD3303S,
        'pmd': PM100D
    }

    @Task()
    def Pull(self):
        os.system('python process.py')
        t0 = time.time()
        print("Press Enter for hard pull")

        while True:
            t1 = time.time()
            t = t1 - t0
            self.xs.append(t)
            self.ys.append(self.pmd.power.magnitude * 1000)

            values = {
                  'x': self.xs,
                  'y': self.ys,
                }

            if msvcrt.kbhit():
                if msvcrt.getwche() == '\r':
                    np.savetxt("power.csv", self.ys, delimiter=",")
                    self.gpd.set_voltage(12)
                    self.gpd.set_output(1)
                    self.gpd.set_output(0)
                    break

            self.Pull.acquire(values)
            time.sleep(0.05)
        return


    @Task()
    def Transform(self):
        while True:
            values1 = {
                  'y1': fft(self.ys),
                }
            self.Transform.acquire(values1)
            time.sleep(0.05)
        return
        
    @Element(name='Histogram')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Transmission Power')
        return p

    @averaged.on(Pull.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        w.set('Transmission Power', xs=xs, ys=ys)
        return

    @Element(name='Histogram')
    def transf(self):
        p1 = LinePlotWidget()
        p1.plot('Fast Fourier Transform')
        return p1

    @transf.on(Transform.acquired)
    def transf_update(self, ev1):
        w1 = ev1.widget
        xs1 = np.arange(len(self.ys))
        ys1 = np.array((self.ys)).real
        w1.set('Fast Fourier Transform', xs=xs1, ys=ys1)
        return

    def initialize(self):
        return

    def finalize(self):
        return

