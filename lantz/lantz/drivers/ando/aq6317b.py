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


class AQ6317B(MessageBasedDriver):
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
        return self.query("RESLN?")

    @resolution.setter
    def resolution(self,value):
        """ Sets the resolution in nm. """
        self.write("RESLN{}".format(value))

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
        return S

    @Feat()
    def sweep_check(self):
      ans=''
      while len(ans)==0:
        ans=self.query('SWEEP?')
        time.sleep(3)
      return int(ans)

    @Action()
    def sweep(self):
        """ Sweeps for a single time. While loop waits for execution to finish."""
        print('starting sweep')
        self.write("SGL")
        S=self.write("POLL 1,S")
        t1=time.time()
        check=1
        while check!=0:
            check=self.sweep_check
        t2=time.time()
        print('sweep time: '+str(t2-t1))
        return None


    @Action()
    def dataencoding(self):
        self.write(':DAT:ENC ascii;WID 2;')

    @Feat()
    def start_wl(self):
        return self.query("STAWL?")

    @Feat()
    def stop_wl(self):
        return self.query("STPWL?")

    @start_wl.setter
    def start_wl(self,value):
        """ Get the center wavelength."""
        self.write("STAWL{}".format(value))

    @stop_wl.setter
    def stop_wl(self,value):
      """ Set the center wavelength."""
      self.write("STPWL{}".format(value))
        
    @Action()
    def read_waveform(self,key):
        """
        Reads the waveforms data. 

        key is 'A'/'B'/'C' for the channel you want to get data from
        """
        #self.query("*IDN?")
        #self.write("ISET IFC")
        #self.write("ISET REN")
        #self.write("INIT")
        #self.dataencoding()
        #wllist=np.linspace(wlsta,wlstp,1001)
        #print(wllist)

        self.write("SD0") # make sure to set the delimiter to comma
        #self.write("HD0") # get rid of the unit header
        # or set to HD1 if you want to do something with the unit
        #self.write("B=A")
        #self.write("SAVEB1")
        p=self.raw_query("LDAT{}".format(key))
        wl=self.raw_query("WDAT{}".format(key))

        plist=np.fromstring(p,dtype=np.float,sep=',')[1:]
        wllist=np.fromstring(wl,dtype=np.float,sep=',')[1:]

        return plist,wllist

    @Feat()
    def read_marker(self):
        """ Reads the first peak value. """
        pk,pwr=self.query('MKR?').split(',')
        return pk,pwr

if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG
    # from gpib_ctypes import make_default_gpib
    # make_default_gpib()

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')

    #log_to_screen(DEBUG)
    # this is the GPIB Address:
    with AQ6317B('GPIB1::1::INSTR') as inst:
      
      
      #inst.set_timeout(100)
      
      inst.initial()
      inst.set_CRLF(0)
      #inst.read_peak
      #inst.centerWl=1400
      #inst.span=400.0
      #inst.start_wl=start
      #inst.stop_wl=stop
      #inst.levelScale=0.8
      #inst.resolution=2
      #inst.avgCount=3
      #inst.set_measSensitivity()
      #inst.tracing_conditions('A',('WRT','DSP'))
      #inst.tracing_conditions('B',('WRT','DSP'))
      #inst.sweep()
      #p,wl=inst.read_waveform('A')"""

      # read peak position for a while
      start=time.time()
      t=start
      
      with open('peak_drift_60min.csv','w',newline='') as csvfile:
        writer=csv.writer(
            csvfile,
            delimiter=',',
            quotechar='|',
            quoting=csv.QUOTE_MINIMAL)
        while (t-start)<3600:
            pk,pwr=inst.read_marker
            t=time.time()
            print('t: '+str(t-start)+', '+str(pk))
            writer.writerow([t-start,pk])
            time.sleep(1)
            

    """
    plt.plot(wl,p,'k')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Power (nW)')
    plt.show()

    with open('SC_DWDM_BPF_AOM.csv','w',newline='') as csvfile:
        writer=csv.writer(
              csvfile,
              delimiter=',',
              quotechar='|',
              quoting=csv.QUOTE_MINIMAL)
        for i in range(len(p)):
            writer.writerow([str(wl[i]),str(p[i])])
    """





        