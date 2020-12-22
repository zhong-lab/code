"""
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of SRS900 Mainframe

    Author: Noah Johnson
    Date: 2/4/2019
"""

from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver
from lantz.errors import InstrumentError
from collections import OrderedDict
import sys



class SRS900(MessageBasedDriver):
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

    @Feat()
    def idn(self):
      return self.query('*IDN?')

    @Action()
    def clear_status(self):
        self.write('*CLS')
        #print('Status cleared')

    @Feat()
    def self_test(self):
      return self.query('*TST?')

    @Feat()
    def self_standard_event_status(self):
      return self.query('*ESR?')

    @Feat()
    def read_standard_event_status_register(self):
      return self.query('*ESR?')

    @Action()
    def reset(self):
      self.write('*RST')
      print('System Reset')

    @Action()
    def flush(self):
      self.write('FLSH')
      #print('Buffers Flushed')

    @Action()
    def flushoutput(self):
      self.write('FLOQ')
      #print('Output Queue Flushed')   

    @Action()
    def wait(self):
      self.write('*WAI')
      print('Waiting to Continue')	

    @Action()
    def wait_time(self, value):
      self.write('WAIT {}'.format(value))		

    @DictFeat(keys=list(range(1,8)))
    def SIMmodule_on(self,key):
      self.write('SNDT {},"OPON"'.format(key))
      print("Output On")

    @DictFeat(keys=list(range(1,8)))
    def SIMmodule_off(self,key):
      self.write('SNDT {},"OPOF"'.format(key))
      print("Output Off") 	  


    @DictFeat(values={'OFF': 0, 'ON': 1},keys=list(range(1,8)))
    def SIM928_on_off(self,key):
      return self.query('SNDT {},"EXON?"'.format(key))

    @SIM928_on_off.setter
    def SIM928_on_off(self,key,value):
      """key is the port being uused. """
      self.write('SNDT {},"EXON {}"'.format(key,value))

    @DictFeat(keys=list(range(1,8)))
    def module_reset(self,key):
   	  self.write('SNDT {},"*RST"'.format(key))
   	  print("Reset")

    @DictFeat(keys=list(range(1,8)))
    def module_clear_status(self,key):
      self.write('SNDT {},"*CLS"'.format(key))
      #print("Status Cleared")   

    @DictFeat(keys=list(range(1,8)))
    def module_identify(self,key):
      self.write('SNDT {},"*IDN?"'.format(key))
      return self.query('GETN? {},80'.format(key)) 

    @DictFeat(units='V',limits=(-20,20,0.001),keys=list(range(1,8)))
    def SIM928_voltage(self,key):
      self.flushoutput
      self.wait_time(100)
      self.write('SNDT {},"VOLT?"'.format(key))
      self.wait_time(10)
      return self.query('GETN? {},80'.format(key))
      
    @SIM928_voltage.setter
    def SIM928_voltage(self,key,value):
   	  self.write('SNDT {},"VOLT {}"'.format(key, float(round(value,3))))

    """
    @DictFeat(units='V',keys=list(range(1,9)))
    def SIM970_voltage(self,key):
      self.flush
      self.flushoutput
      self.wait_time(1e6)
      #self.write('SNDT {},"VOLT? 1"'.format(key))
      return self.query('GETN? {},80'.format(key),delay=2)
    """
    def split_msg(self,msg,key):
      """ gets rid of header and returns term in response of GETN? command.

      converts term into a float"""

      msglist=msg.split(' ')
      term=msglist[key]
      nocom=term[:-1]
      num=float(nocom)
      return num

    @DictFeat(units='V',keys=list(range(1,5)))
    def SIM970_voltage(self,key):
      """ port manually set to 7 (8 will work as well since voltmeter occupies both ports). 
      Key is the channel of the voltmeter being read. 
      """
      self.flush()
      self.flushoutput()
      self.wait_time(100)
      msg=''
      while len(msg.split(' '))<2:
        self.write('SNDT 7,"VOLT? 0"')
        msg=self.query('GETN? 7, 80',delay=2)

      num=self.split_msg(msg,key)
      return num
    
    # @DictFeat(units = 'V',keys = list(range(1,4)))
    # def SIM970_voltage(self,key):
    #   self.reset()
    #   self.clear_status()
    #   self.flushoutput()
    #   self.wait_time(1e6)
    #   return self.query('SNDT {},"VOLT?"'.format(key))

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
    with SRS900('GPIB0::2::INSTR') as inst:
      inst.clear_status()
      # v2=inst.SIM970_voltage[1]

      inst.clear_status()
      v2=inst.SIM970_voltage[2]

      
      # inst.SIM928_on_off[5]='OFF'
      # inst.SIM928_on_off[5]='ON'
      inst.SIM928_on_off[6]='OFF'
      #inst.SIM928_on_off[6]='ON'
      

      #inst.SIMmodule_on[6]
      #inst.SIMmodule_off[6]
      #inst.SIM970_voltage[5]
      





        