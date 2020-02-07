# -*- coding: utf-8 -*-
"""
    lantz.drivers.alliedvision
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation for a single vimba cam (could be modified to work with multiple camera if need be)

    Requires pymba

    Author: AlexBourassa and Kevin Miao
    Date: 24/07/2017
"""

from lantz.driver import Driver
from lantz import Feat, DictFeat, Action
from pymba import Vimba
import numpy as np


class VimbaCam(Driver):

    def initialize(self):
        self.vimba = Vimba()
        self.vimba.startup()
        self.cam = self.vimba.getCamera(self.vimba.getCameraIds()[0])
        self.cam.openCamera()

        self.cam.PixelFormat = 'Mono8'
        self.frame = self.cam.getFrame()
        self.frame.announceFrame()
        self.cam.startCapture()
        return

    def finalize(self):
        self.vimba.shutdown()
        return

    @Action()
    def getFrame(self):
        try:
            self.frame.queueFrameCapture()
            success = True
        except:
            success = False

        self.cam.runFeatureCommand('AcquisitionStart')
        self.cam.runFeatureCommand('AcquisitionStop')
        self.frame.waitFrameCapture(0)
        frame_data = self.frame.getBufferByteData()
        if success:
            img_config = {
                'buffer': frame_data,
                'dtype': np.uint8,
                'shape': (self.frame.height, self.frame.width, 1),
            }
            img = np.ndarray(**img_config)
            return img[...,0]
        else:
            return None
