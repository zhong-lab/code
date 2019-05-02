import itertools as it
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.montana.cryostation import Cryostation

from PyQt5 import QtWidgets

class CryostationSpyrelet(Spyrelet):

    requires = {
        'cryo': Cryostation
    }

    @Task()
    def readout(self, **kwargs):
        self.dataset.clear()
        now = time.time()
        for idx in self.readout.progress(it.count()):
            time.sleep(0.5)
            dt = time.time() - now
            st = self.cryo.sample_temperature
            pt = self.cryo.platform_temperature
            s1t = self.cryo.stage_1_temperature
            s2t = self.cryo.stage_2_temperature
            setpoint = self.cryo.temp_setpoint
            chamber_pressure = self.cryo.chamber_pressure
            ph = self.cryo.platform_heater_pow
            s1h = self.cryo.stage_1_heater_pow
            values = {
                't': dt,
                'st': st,
                'pt': pt,
                's1t': s1t,
                's2t': s2t,
                'setpoint': setpoint,
                'cp': chamber_pressure,
                'ph': ph,
                's1h': s1h,
            }
            self.readout.acquire(values)
        return
        
    @Element()
    def pressure(self):
        p = LinePlotWidget()
        p.title = 'Pressure'
        p.xlabel = 'Time'
        p.ylabel = 'Pressure (mTorr)'
        p.plot('Chamber pressure', symbol=None)
        return p

    @pressure.on(readout.acquired)
    def plot(self, ev):
        w = ev.widget
        w.set('Chamber pressure', xs=self.data.t, ys=self.data.cp)
        return

    @Element()
    def temperatures(self):
        p = LinePlotWidget()
        p.title = 'Temperature'
        p.xlabel = 'Time'
        p.ylabel = 'Temperature (K)'
        p.plot('Sample temperature', symbol=None)
        p.plot('Platform temperature', symbol=None)
        p.plot('Stage 1 temperature', symbol=None)
        p.plot('Stage 2 temperature', symbol=None)
        return p

    @temperatures.on(readout.acquired)
    def plot(self, ev):
        w = ev.widget
        w.set('Sample temperature', xs=self.data.t, ys=self.data.st)
        w.set('Platform temperature', xs=self.data.t, ys=self.data.pt)
        w.set('Stage 1 temperature', xs=self.data.t, ys=self.data.s1t)
        w.set('Stage 2 temperature', xs=self.data.t, ys=self.data.s2t)
        return

    @Element(name='Heater powers')
    def heaters(self):
        p = LinePlotWidget()
        p.title = 'Heater powers'
        p.xlabel = 'Time'
        p.ylabel = 'Power (W)'
        p.plot('Platform heater', symbol=None)
        p.plot('Stage 1 heater', symbol=None)
        return p

    @heaters.on(readout.acquired)
    def plot(self, ev):
        w = ev.widget
        w.set('Platform heater', xs=self.data.t, ys=self.data.ph)
        w.set('Stage 1 heater', xs=self.data.t, ys=self.data.s1h)
        return

    @Element()
    def temperature_setpoint(self):
        w = QtWidgets.QWidget()
        setpoint = QtWidgets.QLCDNumber()
        w.setpoint = setpoint
        kelvin_label = QtWidgets.QLabel('Kelvin')
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(setpoint)
        layout.addWidget(kelvin_label)
        w.setLayout(layout)
        return w

    @temperature_setpoint.on(readout.acquired)
    def setpoint_display(self, ev):
        w = ev.widget
        setpoint = float(self.data.setpoint.tail(1))
        w.setpoint.display(setpoint)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w


