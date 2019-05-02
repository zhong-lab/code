import numpy as np
import time
from itertools import count

from spyre import Spyrelet, Task, Element
from spyre.widgets.param_widget import ParamWidget
from pyqtgraph import ValueLabel

from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.microsoft import XInputController

class AttocubeSpyrelet(Spyrelet):

    requires = {
        'atto': ANC350,
        'xbox': XInputController,
    }

    def qtz(self, val, divs=5):
        return int(val * divs) / divs

    @Task(name='Piezo control via xbox')
    def xbox_move(self):
        params = self.xbox_parameters.widget.get()
        x_step = params['x speed']
        y_step = params['y speed']
        z_step = params['z speed']

        def axis_event(axis, value):
            qtz_vector = self.qtz(value)
            if axis not in {'l_thumb_x', 'l_thumb_y', 'left_trigger', 'right_trigger'}:
                return
            if axis == 'l_thumb_x':
                # reverse x direction
                self.atto.jog(0, -x_step * qtz_vector)
            elif axis == 'l_thumb_y':
                self.atto.jog(1, y_step * qtz_vector)
            elif axis == 'left_trigger':
                self.atto.jog(2, -z_step * qtz_vector)
            elif axis == 'right_trigger':
                self.atto.jog(2, z_step * qtz_vector)
            return

        def button_event(button, pressed):
            if not pressed:
                return
            if button == 1:
                self.atto.single_step(0, True)
            if button == 3:
                self.atto.single_step(0, False)
            if button == 2:
                self.atto.single_step(1, True)
            if button == 4:
                self.atto.single_step(1, False)


        self.dataset.clear()
        self.xbox.set_axis_callback(axis_event)
        for iteration in self.xbox_move.progress(count()):
            time.sleep(0.1)
            self.xbox.dispatch_events()
            x = self.atto.position(0)
            y = self.atto.position(1)
            z = self.atto.position(2)
            values = {
                'x': x,
                'y': y,
                'z': z,
            }
            self.xbox_move.acquire(values)
        return

    @xbox_move.initializer
    def initialize(self):
        return

    @xbox_move.finalizer
    def finalize(self):
        return

    @Element(name='xbox controller parameters')
    def xbox_parameters(self):
        params = [
            ('x speed', {
                'type': float,
                'default': 0.1,
            }),
            ('y speed', {
                'type': float,
                'default': 0.1,
            }),
            ('z speed', {
                'type': float,
                'default': 0.005,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='XYZ position')
    def xyz_position(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        w.setLayout(layout)
        x = ValueLabel()
        y = ValueLabel()
        z = ValueLabel()
        w.x = x
        w.y = y
        w.z = z
        layout.addWidget(x)
        layout.addWidget(y)
        layout.addWidget(z)
        return w

    @xyz_position.on(xbox_move.acquired)
    def xyz_position_update(self, ev):
        w = ev.widget
        data = self.data.tail(1)
        w.x.setValue(data.x)
        w.y.setValue(data.y)
        w.z.setValue(data.z)
        return
