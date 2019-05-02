from PyQt5 import QtWidgets
import pyqtgraph as pg

import numpy as np
from itertools import count
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import FastImageWidget
from spyre.widgets.param_widget import ParamWidget

from lantz.drivers.alliedvision.vimba import VimbaCam
from lantz.drivers.dli.webpowerswitch7 import WebPowerSwitch7
from lantz.drivers.tektronix.awg5000 import AWG5000
from lantz.drivers.thorlabs.ff import FF


class VimbaCamSpyrelet(Spyrelet):

    requires = {
        'cam': VimbaCam,
        'webps': WebPowerSwitch7,
        'awg': AWG5000,
        'ff': FF,
    }

    @Task()
    def video_task(self, **kwargs):
        for iteration in self.video_task.progress(count()):
            #This method is probably not thread safe, but the low camera rate of 30-40 fps should make it ok
            f = self.cam.getFrame()
            if not f is None:
                self.frame = f
                self.video_task.acquire({})
        return

    @video_task.initializer
    def initialize(self):
        if self.input_parameters.widget.get()['Switch to camera mode']:
            self.awg.toggle_all_outputs(False)
            self.webps.state[5] = True
            time.sleep(0.5)
            self.ff.position = 1


    @video_task.finalizer
    def finalize(self):
        if self.input_parameters.widget.get()['Switch to camera mode']:
            self.webps.state[5] = False
            self.ff.position = 2

    @Element(name='Video Stream')
    def stream(self):
        w = FastImageWidget()
        return w

    @stream.on(video_task.acquired)
    def stream_update(self, ev):
        w = ev.widget
        w.set(self.frame.T, autoLevels=False)
        return

    @Element(name='Input parameters')
    def input_parameters(self):
        params = [
            ('Switch to camera mode', {
                'type': bool,
                'default': True,
            }),
        ]
        w = ParamWidget(params)
        return w
