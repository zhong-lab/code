# -*- coding: utf-8 -*-
"""
    lantz.drivers.princetoninstruments.spectrapro
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of SpectraPro over a Socket
    Author: Christina Wicker
    Date: 06/14/2021
"""

from collections import OrderedDict
from lantz import Action, Feat, DictFeat, Q_
from lantz.messagebased import MessageBasedDriver
import json
import numpy as np

class SpectraPro(MessageBasedDriver):

    DEFAULTS = {
        'COMMON': {
            'write_termination': '',
            'read_termination': '\r\n',
            "timeout": None
        }
    }

    @Feat(units="s")
    def grating(self):
        return float(self.query("get grating"))

    @grating.setter
    def grating(self, grating):
        res=self.query("set grating {:1.3e}".format(grating))
        if res == 0:
            raise Exception

    @Feat(units="nm")
    def wavelength(self):
        return float(self.query("get wavelength"))

    @wavelength.setter
    def wavelength(self, wl):
        res=self.query("set wavelength {:1.3e}".format(wl))
        if res == 0:
            raise Exception
