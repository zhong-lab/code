import time
import os

from spyre import Spyrelet, Element
from spyre.widgets.axis_control_widget import ControlWidget

from lantz.drivers.arduino.goniometer import Goniometer
from lantz import Q_

from PyQt5 import QtWidgets, QtCore, QtGui

class GoniometerSpyrelet(Spyrelet):
    requires = {
    'g': Goniometer,
    }

    @Element(name='Gonio control buttons')
    def gonio_control(self):
        axes = [
        ('theta', {
            'orientation': 'vertical',
            'limits': [70, 110],
            }),
        ('phi', {
            'orientation': 'horizontal',
            'limits': [30, 135],
            }),
        ('R', {
            'orientation': 'vertical',
            'limits': [0, 150],
            }),
        ]
        c = ControlWidget(axes)
        c.run_state.connect(self.move)
        self.c = c
        self.w = QtWidgets.QWidget()
        self.init_ui()
        return self.w

    def init_ui(self):
        self.state_label = QtWidgets.QLabel()
        self.state_label.setFixedWidth(90)
        origin = QtWidgets.QPushButton('origin')
        origin.clicked.connect(self.set_origin)
        origin.pressed.connect(self.origin_label)
        layout = QtWidgets.QGridLayout(self.w)
        layout.addWidget(self.c, 0 ,0)
        layout.addWidget(self.state_label, 0, 1, QtCore.Qt.AlignTop)
        layout.addWidget(origin, 2, 1)

    def move(self, axis, limit, running):
        # print('theta:', self.g.theta, 'phi:', self.g.phi, 'R:', self.g.R)
        # self.g.stop()
        if running:
            self.theta_init = self.g.theta
            self.phi_init = self.g.phi
            self.check_boundary(axis, limit)
            self.state_label.setText(axis+' moving...')
            if axis == 'theta':
                self.g.theta = limit
            elif axis == 'phi':
                self.g.phi = limit
            elif axis == 'R':
                self.g.R = limit
        else:
            self.g.stop()
            self.state_label.setText('')
            self.restore_angle(axis)

    def restore_angle(self, axis):
        if axis == 'theta':
            self.g.phi = self.phi_init
        elif axis == 'phi':
            self.g.theta = self.theta_init

    def check_boundary(self, axis, limit):
        if axis == 'theta' and limit == self.g.theta or axis == 'phi' and limit == self.g.phi:
            self.state_label.setText(axis+' at limit')
            return self.g.check_error(-1)
        elif axis == 'R' and limit == self.g.R:
            self.state_label.setText(axis+' at limit')
            return self.g.check_error(-9)

    def set_origin(self):
        self.g.stop()
        self.g.theta = 90
        self.g.wait_for_ready()
        self.g.phi = 90
        self.g.wait_for_ready()
        self.g.R = 0
        self.g.wait_for_ready()
        self.state_label.setText('')
        self.g.stop()

    def origin_label(self):
        if (self.g.theta, self.g.phi, self.g.R) == (90, 90, 0):
            self.state_label.setText('at origin')
        else:
            self.state_label.setText('returning to origin')
