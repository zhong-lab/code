<<<<<<< HEAD
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

    @Feat()
    def short_range(self):
        """ Get the range of the short scan for
        the peak search function. 
        """
        self.query("WS")

    @short_range.setter
    def short_range(self,value):
        """ Set the range of the short scan for
        the peak search function. 
        format is xxx.xx
        """
        self.write("WS {}".format(value))

    @Feat()
    def long_range(self):
        """ Get the range of the long scan for
        the peak search function.
        """
        self.query("WL")

    @long_range.setter
    def long_range(self,value):
        """ Set the range of the long scan for
        the peak search function. 
        format is xxx.xx
        """
        self.write("WL {}".format(value))

    @Action()
    def peak_search(self,option='O'):
        """ Executes the peak search function. 
        options are: 
        'O': set rapid mode
        'F': cancel rapid mode
        """
        self.write("P{}".format(option))
        self.write("PS")
        tuning=00
        while tuning!=20:
            tuning=float(self.query("SU")[-2:])
        return self.query("WA")

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
      
      inst.wavelength=1529
      inst.short_range=1
      inst.long_range=20
      inst.peak_search('O')
=======
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
      
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
