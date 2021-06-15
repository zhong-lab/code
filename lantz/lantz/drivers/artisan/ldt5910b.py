"""
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of ANDOR AQ6317 OSA
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


class LDT5910B(MessageBasedDriver):
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

    @Action()
    def initial(self):
      return None

    
    @Feat()
    def SHconst(self):
        """ Used to read back the Steinhart-Hart constants for R-T conversion. """
        #return self.query("CONST?")

    @SHconst.setter
    def SHconst(self,values):
        """ Used to enter teh Steinhart-Hart constants for R-T conversion. 
        Takes an iterable of SH values
        """
        #self.write("CONST {} {} {}".format(values))


    def display(self,code):
      """ Turns on the display.
      Returns the display value. 
      code can be 'T','R'
      """
      self.write("DIS:{}".format(code))
      val=self.query("DIS?").strip('\"')
      return float(val)
  
    def idn(self):
      """ Turns on the display.
      Returns the display value. 
      code can be 'T','R'
      """
      #self.write("DIS:{}".format(code))
      val=self.query("IDN?")
      return float(val)

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
    with LDT5910B('GPIB1::2::INSTR') as inst:
      #inst.idn()
      inst.display('T')


