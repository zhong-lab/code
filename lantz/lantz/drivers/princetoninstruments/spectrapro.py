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
<<<<<<< HEAD
<<<<<<< HEAD
    def get_grating(self):
        return int(self.query("get grating"))

    def set_grating(self, grating):
        res=self.query("set grating {}".format(grating))
        if res == 0:
            raise Exception
        return res

    def get_wavelength(self):
        return float(self.query("get wavelength"))

    def set_wavelength(self, wl):
        res=self.query("set wavelength {}".format(wl))
        if res == 0:
            raise Exception
        return res

if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG
    # from gpib_ctypes import make_default_gpib
    # make_default_gpib()

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')

    log_to_screen(DEBUG)
    # this is the GPIB Address:
    with SpectraPro('TCPIP::169.254.48.177::12345::SOCKET') as inst:
        inst.set_grating(1)
        inst.get_grating()
        inst.set_wavelength(1500.0)
        inst.get_wavelength()
=======
=======
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d

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
<<<<<<< HEAD
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
=======
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
