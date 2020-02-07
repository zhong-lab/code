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

from lantz.drivers.attocube import ANC350

class Attocube(Spyrelet):

    requires = {
        'attocube': ANC350
    }

    @Task(name='set position')
    def set_position(self):
        toggle = self.toggle_params.widget.get()
        pos = self.pos_params.widget.get()
        pos0 = pos['axis0_position']
        pos1 = pos['axis1_position']
        pos2 = pos['axis2_position']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle1:
            attocube.position[0] = pos0
        if toggle2:
            attocube.position[1] = pos1
        if toggle3:
            attocube.position[2] = pos2

    @set_position.initializer
    def initialize(self):
        print('initializing move...')
        attocube = ANC350()
        attocube.initialize()
        return

    @set_position.finalizer
    def finalize(self):
        attocube.finalize()
        print('finalizing move...')
        return

    @Task(name='jog')
    def jog(self):
        toggle = self.toggle_params.widget.get()
        jog = self.jog_params.widget.get()
        speed0 = jog['axis0_speed']
        speed1 = jog['axis1_speed']
        speed2 = jog['axis2_speed']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle1:
            attocube.jog[0] = speed0
        if toggle2:
            attocube.jog[1] = speed1
        if toggle3:
            attocube.jog[2] = speed2

    @jog.initializer
    def initialize(self):
        print('initializing jog...')
        attocube = ANC350()
        attocube.initialize()
        return

    @jog.finalizer
    def finalize(self):
        attocube.finalize()
        print('finalizing jog...')
        return

    @Task(name='stop')
    def stop(self):
        attocube.stop()

    @stop.initializer
    def initialize(self):
        print('initializing stop...')
        attocube = ANC350()
        attocube.initialize()
        return

    @stop.finalizer
    def finalize(self):
        attocube.finalize()
        print('finalizing stop...')
        return

    @Element(name='select axis')
    def toggle_params(self):
        params = [
        ('axis0_toggle' {'type': bool}),
        ('axis1_toggle' {'type': bool}),
        ('axis2_toggle' {'type': bool}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='positon parameters')
    def position_params(self):
        params = [
        ('axis0_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis1_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis2_position', {'type': float, 'default': 1, 'units': 'um'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='jog parameters')
    def jog_params(self):
        params = [
        ('axis0_speed', {'type': float, 'default': 1,}),
        ('axis1_speed', {'type': float, 'default': 1,}),
        ('axis2_speed', {'type': float, 'default': 1,}),
        ]
        w = ParamWidget(params)
        return w


