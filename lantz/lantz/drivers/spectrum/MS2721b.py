#Driver for anritsu MS2721B
#Yuxiang Pei 07/2019

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class MS2721B(MessageBasedDriver):
    """This is the driver for the anritsu MS2721B."""

    """For VISA resource types that correspond to a complete 488.2 protocol
    (GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
    generally do not need to use termination characters, because the
    protocol implementation also has a native mechanism to specify the
    end of the of a message.
    """

    # DEFAULTS = {'COMMON': {'write_termination': '\n',
    #                         'read_termination': '\n'}}


    @Feat()
    def idn(self):
        return str(self.query('*IDN?'))
        # return the identification number

    @Feat(units='Hz',limits=(0,7099991000))
    def freq_span(self):
        return self.query('FREQ:SPAN?')
        # return the frequency span
        # should be in the range from 1 Hz to 7099.991 MHz

    @freq_span.setter
    def freq_span(self, value):
        return self.write('FREQ:SPAN {}'.format(value))
        # set the frequency span

    @Feat(units='Hz',limits=(9000,7100000000,1))
    def freq_cent(self):
        return self.query('FREQ:CENT?')
        # return the center frequency
        # should be in the range from 9 MHz to 7100 MHz

    @freq_cent.setter
    def freq_cent(self, value):
        return self.write('FREQ:CENT {}'.format(value))
        # set the center frequency

    @Feat(units='Hz',limits=(9000,7100000000,1))
    def freq_star(self):
        return self.query('FREQuency:STARt?')
        # return the start frequency
        # should be in the range from 9 MHz to 7100 MHz

    @freq_star.setter
    def freq_star(self, value):
        return self.write('FREQ:STAR {}'.format(value))
        # set the start frequency

    @Feat(units='Hz',limits=(9000,7100000000,1))
    def freq_stop(self):
        return self.query('FREQuency:STOP?')
        # return the start frequency
        # should be in the range from 9 MHz to 7100 MHz

    @freq_stop.setter
    def freq_stop(self, value):
        return self.write('FREQ:STOP {}'.format(value))
        # set the stop frequency

    @Feat()
    def limit_alarm(self):
        return self.query(':CALCulate:LIMit:ALARm?')
        # return the state of limit alarm
        #----0: OFF
        #----1: ON

    @limit_alarm.setter
    def limit_alarm(self,value):
        return self.write(':CALCulate:LIMit:ALARm {}'.format(value))
        # set the state of limit alarm
        #----0: OFF
        #----1: ON
        # Please not that this operation will only set one in the lower and upper limits

    @Feat()
    def lower_limit_alarm(self):
        return self.query(':CALCulate:LIMit:LOWer:ALARm?')
        # return the state of lower limit line
        #----0: OFF
        #----1: ON

    @lower_limit_alarm.setter
    def lower_limit_alarm(self,value):
        return self.write(':CALCulate:LIMit:LOWer:ALARm {}'.format(value))
        # set the state of lower limit line
        #----0: OFF
        #----1: ON

    @Feat()
    def upper_limit_alarm(self):
        return self.query(':CALCulate:LIMit:UPPer:ALARm?')
        # return the state of lower limit line
        #----0: OFF
        #----1: ON

    @upper_limit_alarm.setter
    def upper_limit_alarm(self,value):
        return self.write(':CALCulate:LIMit:UPPer:ALARm {}'.format(value))
        # set the state of lower limit line
        #----0: OFF
        #----1: ON

    @Feat()
    def lower_limit(self):
        return self.query(':CALCulate:LIMit:TYPe 1;:CALCulate:LIMit:STATe?')
        # return the state of lower limit line
        #----0: OFF
        #----1: ON

    @lower_limit.setter
    def lower_limit(self,value):
        return self.write(':CALCulate:LIMit:TYPe 1;:CALCulate:LIMit:STATe {}'.format(value))
        # set the state of lower limit line
        #----0: OFF
        #----1: ON

    @Feat()
    def upper_limit(self):
        return self.query(':CALCulate:LIMit:TYPe 0;:CALCulate:LIMit:STATe?')
        # return the state of upper limit line
        #----0: OFF
        #----1: ON

    @upper_limit.setter
    def upper_limit(self,value):
        return self.write(':CALCulate:LIMit:TYPe 0;:CALCulate:LIMit:STATe {}'.format(value))
        # set the state of upper limit line
        #----0: OFF
        #----1: ON

    @Feat()
    def marker_off(self):
        return self.write(':CALCulate:MARKer:AOFF')
        # turns off all markers

    @DictFeat(values={'ON':'1','OFF':'0'})
    def marker(self,key):
        return self.query(':CALC:MARK{}:STAT?'.format(key))
        # return the state of marker
        # using key to decide the number of marker

    @marker.setter
    def marker(self,key,value):
        return self.write(':CALC:MARK{}:STAT {}'.format(key,value))
        # set the state of marker to ON/OFF
        # can be used as inst.marker[channel]='ON'

    @DictFeat(units='Hz',limits=(9000,7100000000,1))
    def marker_X(self,key):
        return self.query(':CALCulate:MARKer{}:X?'.format(key))
        # return the X value of marker

    @marker_X.setter
    def marker_X(self,key,value):
        return self.write(':CALC:MARK{}:X {}'.format(key,value))
        # set the X value of marker
        # can be used as e.g. inst.marker_X[2]=Q_(3.55,'GHz')

    @DictFeat(units='dB')
    def marker_Y(self,key):
        return self.query(':CALCulate:MARKer{}:Y?'.format(key))
        # return the Y value of marker

    @DictFeat()
    def marker_peak_search(self,key):
        return self.write(':CALCulate:MARKer{}:MAXimum'.format(key))
        # set the marker at the peak value

    @Feat(units='dB',limits=(1,15))
    def Y_scale(self):
        return self.query(':DISPlay:WINDow:TRACe:Y:PDIVision?')
        # return the Y scale
        # 10 dB means 10 dB/div----(10 dB/division)

    @Y_scale.setter
    def Y_scale(self,value):
        return self.write(':DISPlay:WINDow:TRACe:Y:PDIVision {}'.format(value))
        # set the Y scale
        # unit: dB

    @Feat(units='dB',limits=(-130,30))
    def ref_level(self):
        return self.query(':DISPlay:WINDow:TRACe:Y:RLEVel?')
        # return the reference level

    @ref_level.setter
    def ref_level(self,value):
        return self.write(':DISPlay:WINDow:TRACe:Y:RLEVel {}'.format(value))
        # set the reference level

    @Feat(values={'ON':'1','OFF':'0'})
    def generator(self):
        return self.query(':INITiate:TGENerator?')
        # return the state of track generator

    @generator.setter
    def generator(self,value):
        return self.write(':INITiate:TGENerator {}'.format(value))
        # set the ON/OFF of track generator
        # used as inst.generator='ON'

    @Feat(units='dB',limits=(-40,0,0.1))
    def generator_power(self):
        return self.query(':TGENerator:OUTput:POWer?')
        # return the power of the track generator
        # unit: dBm

    @generator_power.setter
    def generator_power(self,value):
        return self.write(':TGENerator:OUTput:POWer {}'.format(value))
        # set the power of the track generator

    @Action()
    def savefile(self,value):
        return self.write('MMEM:STOR:TRAC 0,"{}"'.format(value))
        # return self.write('MMEM:STOR:TRAC 0,"QvsBz_Rampdown_{}"'.format(value))

    @Action()
    def format_usb_storage(self):
        return self.write(':MMEMory:INITialize USB')
        # Formats the USB Flash drive.

    @Action()
    def save_to_usb(self):
        return self.write(':MMEMory:MSIS USB')
        # Sets the USB Flash drive as the save location for all subsequently saved files.

    @Action()
    def save_to_internal_mem(self):
        return self.write(':MMEMory:MSIS INTernal')
        # Sets the instrument’s internal memory as the save location for all subsequently saved files.

    @Feat()
    def save_to_where(self):
        return self.query(':MMEM:MSIS?')

    @Action()
    def preset(self):
        self.write('*RST')
        # restores parameters in the current application as well as system settings to their factory default values

    @Action()
    def abort(self):
        self.write(':ABORT')
        # restarts the current sweep and/or measurement and resets the trigger system


    @Action()
    def acquireData(self):
        return self.query(':TRACe[:DATA]? 1')

    @Action()
    def format(self):
        self.write(':FORMat:DATA REAL,32')


if __name__ == '__main__':
    import time
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')
    kHz=Q_(1,'kHz')
    MHz = Q_(1.0,'MHz')
    dB = Q_(1,'dB')
    dBm = Q_(1,'dB')

    log_to_screen(DEBUG)
    # this is the USB VISA Address:
    with MS2721B('USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR') as inst:
        print('The identification of this instrument is :' + str(inst.idn))
        #inst.freq_span=Q_(10,'kHz')
        #print('The frequency span of this instrument is : {}'.format(inst.freq_span))#怎么把显示变成MHz单位
        #inst.marker_off
        #print('lower limit alarm: {}'.format(int(inst.lower_limit_alarm)))
        #print('upper limit alarm: {}'.format(int(inst.upper_limit_alarm)))
        #print('limit alarm: {}'.format(int(inst.limit_alarm)))
        #print('upper limit: {}'.format(int(inst.upper_limit)))
        #channel=2
        #inst.marker[channel]='ON'
        #print('Marker[{}]: {}'.format(channel,inst.marker[channel]))
        #print('Marker_Y[{}]: {}'.format(channel,inst.marker_Y[channel]))
        #inst.marker_peak_search[2]
        #print('Marker_Y[{}]: {}'.format(channel,inst.marker_Y[channel]))
        #print('Y scale: {}'.format(inst.Y_scale))
        #inst.ref_level = 10*dB
        #inst.Y_scale=10*dB
        #print('Y level: {}'.format(inst.ref_level))
        #inst.preset()
        #time.sleep(120)
        #inst.freq_cent=10*MHz
        #inst.freq_span=0*MHz

        #inst.generator_power=-1*dBm
        #inst.generator='ON'
        #time.sleep(5)
        #print('generator power: {}'.format(inst.generator_power))
        #print('Marker_peak[{}]: {}'.format(channel,inst.marker_peak[channel]))
