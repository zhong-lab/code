"""
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of santec OTF-930 tunable filter
    Author: Christina Wicker
    Date: 03/31/21
"""

from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver
from lantz.errors import InstrumentError
from collections import OrderedDict
import sys
import time
import numpy as np
import csv
import matplotlib.pyplot as plt


class OTF930(MessageBasedDriver):
    """This is the driver for the SRS SIM900 Mainframe, SRS SIM 928 Isolated Voltage Source module, and SIM 970 Quad Digital Voltmeter module."""

    """For VISA resource types that correspond to a complete 488.2 protocol
    (GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
    generally do not need to use termination characters, because the
    protocol implementation also has a native mechanism to specify the
    end of the of a message.
    """


    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\r\n'}}


    def query(self, command, send_args=(None, None), recv_args=(None, None),delay=None):
       answer = super().query(command, send_args=send_args, recv_args=recv_args,delay=delay)
       if answer == 'ERROR':
           raise InstrumentError
       return answer

    @Feat()
    def wavelength(self):
        """ Get the center wavelength."""
        return self.query("WA")

    @wavelength.setter
    def wavelength(self,value):
      """ Set the center wavelength.
      The format is xxxx.xxx
      """
      tuning=1
      self.write("WA {}".format(value))
      while tuning!=0:
        tuning=float(self.query("SU")[-1])

    @Feat()
    def offset(self):
        """ Get the sweep width."""
        return self.query("CW")

    @offset.setter
    def offset(self,value):
        """Set the center wavelength offset.
        format is xxxx.xx
        """
        self.write("CW {}".format(value))

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
    with OTF930('GPIB2::17::INSTR') as inst:
      
      inst.wavelength=1530
      