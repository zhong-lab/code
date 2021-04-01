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



class AQ6317B(MessageBasedDriver):
    """This is the driver for the SRS SIM900 Mainframe, SRS SIM 928 Isolated Voltage Source module, and SIM 970 Quad Digital Voltmeter module."""

    """For VISA resource types that correspond to a complete 488.2 protocol
    (GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
    generally do not need to use termination characters, because the
    protocol implementation also has a native mechanism to specify the
    end of the of a message.
    """


    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'}}


    def query(self, command, send_args=(None, None), recv_args=(None, None),delay=None):
       answer = super().query(command, send_args=send_args, recv_args=recv_args,delay=delay)
       if answer == 'ERROR':
           raise InstrumentError
       return answer

    @Action()
    def initial(self):
        """ Declares an array of the measuring waveforms data.
        
        Initializes the screen.

        Initializes the GP-IB interface by issuing IFC.

        Sets the REN to True.

        """

        self.write('SCREEN 3: CLS 3: CONSOLE 0,25,0,1')
        print('screen cleared')

        self.write('ISET IFC')
        print('GPIB interface initialized')

        self.write('ISET REN')
        print('REN set to True')

        return None

    @Action()
    def set_CRLF(self,value):
        """Sets the CRLF block delimiter for program code output."""
        self.write('CMD DELIM={}'.format(value))
        print('CRLF block delimiter set to {}'.format(value))
        return None

    @Feat()
    def centerWl(self):
        """ Get the center wavelength."""
        return self.query("CTRWL?")

    @centerWl.setter
    def centerWl(self,value):
      """ Set the center wavelength."""
      self.write("CTRWL{}".format(value))

    @Feat()
    def span(self):
        """ Get the sweep width."""
        return self.query("SPAN?")

    @span.setter
    def span(self,value):
      """ Set the center wavelength."""
      self.write("SPAN{}".format(value))
        
    @Feat()
    def refLevel(self):
        """ Gets the reference level."""
        return self.query("REFL?")

    @refLevel.setter
    def refLevel(self,value):
      """ Set the center wavelength."""
      self.write("REFL{}".format(value))

    @Feat()
    def levelScale(self):
        """ Gets the level scale in dB/div. """
        return self.query("LSCL?".format(value))

    @levelScale.setter
    def levelScale(self,value):
        """ Sets the level scale in dB/div. """
        self.write("LSCL{}".format(value))

    @Feat()
    def resolution(self):
        """ Gets the resolution in nm. """
        return self.query("RESLNO?")

    @resolution.setter
    def resolution(self,value):
        """ Sets the resolution in nm. """
        self.write("RESLNO{}".format(value))

    @Feat()
    def avgCount(self):
        """ Gets the averaging count. """
        return self.query("AVG?")

    @avgCount.setter
    def avgCount(self,value):
        """ Sets the resolution in nm. """
        self.write("AVG{}".format(value))

    @Action()
    def set_measSensitivity(self):
        """ Sets the measuring sensitivity to 'Normal Range Hold.'' """
        self.write("SNHD")

    @Action()
    def samplingPoint(self):
        """ Sets the sampling point."""
        self.write("SMPL1001")

    @Feat()
    def active_trace(self):
        """Gets the active trace."""
        return self.query("ACTV?")

    @active_trace.setter
    def active_trace(self,key):
        """ Sets the active trace."""
        self.write("ACTV{}".format(key))

    @Action()
    def tracing_conditions(self,key,values):
        """ Sends a program code to the AQ6317B and sets the tracing conditions
      
        specify a tupple where strings:

        'WRT'/'FIX' = Write mode / Fixed mode
        'DSP'/'BLK' = Display / No display
        """
        writemode,displaymode=values
        self.write("{}{}".format(writemode,key))
        self.write("{}{}".format(displaymode,key))
        

    def read_status_byte(self):
        """ Read the status byte. """
        S=self.write("\"SRQ1\": POLL 1,S")
        print(S)
        return S

    def sweep(self):
        """ Sweeps for a single time. While loop waits for execution to finish."""
        self.write("SGL")
        S=self.write("POLL 1,S")
        t1=time.time()
        while True:
            check=self.write('SWEEP?')[0]
            if check>0:
                t2=time.time()
                print('sweep time: '+str(t2-t1))
                break
        
    @Action()
    def read_waveform(self):
        """ Sets the CRLF string delimiter for data output, and requests an output of 
        the waveform data. 

        Reads the waveforms data and assigns them in array A. 

        key is 'A'/'B'/'C' for the channel you want to get data from
        """
        #self.query("*IDN?")
        
        self.write("SD1")
        for i in range(500):
            res=self.query("LDATAR{}".format(i))
            print(res)
       

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
    with AQ6317B('GPIB0::1::INSTR') as inst:
      #inst.set_timeout(100)
      #inst.get_spectrum()
      inst.initial()
      inst.set_CRLF(0)

      inst.centerWl=1538.50

      inst.span=14.0
      inst.refLevel=-63.1
      inst.levelScale=2.0
      inst.resolution=0.05
      inst.avgCount=10
      
      inst.set_measSensitivity()

      inst.samplingPoint()
      
      inst.tracing_conditions('A',('WRT','DSP'))
      inst.sweep()

      inst.read_waveform()
      





        