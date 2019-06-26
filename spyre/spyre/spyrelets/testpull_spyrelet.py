import numpy as np
import pyqtgraph as pg
import time
import csv
import sys
import thorlabs_apt as apt
import msvcrt

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.gwinstek.g3303s import GPD3303S
from lantz.drivers.thorlabs.pm100d import PM100D

class FiberPulling(Spyrelet):
    xs = []
    ys = []

    requires = {
        'gpd': GPD3303S,
        'pmd': PM100D
    }

    @Task()
    def readVoltage(self):
        print(str(self.gpd.voltage()))
        return

    @Element()
    def setVoltage(self, value):
        self.gpd.set_voltage(value)
        return

    @Element()
    def setOutput(self, value):
        self.gpd.set_output(value)
        return

    @Element()
    def HardPull(self):
        elements = apt.list_available_devices()
        serials = [x[1] for x in elements]
        serial1 = serials[0]
        serial2 = serials[1]
        print(elements)
        motor1 = apt.Motor(serial1)
        motor2 = apt.Motor(serial2)
        motor1.move_home()
        motor2.move_home(True)
        print("homed")
        time.sleep(2)
        motor1.move_to(50)
        motor2.move_to(50, True)
        print("ready")

        input("Press any key to start pulling")
        print("pulling")
        motor1.move_velocity(0.002)
        motor1.move_to(20)
        motor2.move_velocity(0.002)
        motor2.move_to(20)

        while True:
            t1 = time.time()
            t = t1 - t0
            self.xs.append(t)
            self.ys.append(self.pmd.power.magnitude * 1000)
            values = {
                  'x': self.xs,
                  'y': self.ys,
                  }

            self.HardPull.acquire(values)
            time.sleep(1)
            
            if msvcrt.kbhit():
                if msvcrt.getwche() == '\r':
                    self.gpd.set_voltage(12)
                    self.gpd.set_output(1)
                    self.gpd.set_output(0)
                    break

        return

    
    @Element(name='Histogram')
    def averaged(self):
        p = LinePlotWidget()
        p.plot('Transmission Power')
        return p

    @averaged.on(startpulse.acquired)
    def averaged_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        w.set('Transmission Power', xs=xs, ys=ys)
        return


    def initialize(self):
        return

    def finalize(self):
        return

