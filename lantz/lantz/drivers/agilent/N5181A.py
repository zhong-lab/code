#Driver for Keysight N5181A
#Shobhit Gupta 22/2020

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class N5181A(MessageBasedDriver):
    """This is the driver for the Keysight P9371A."""

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'}}

    ''' 
        Measurement number is set to 1 by default, you could change it after 'MEAS'.
        Data readout is based on display on screen by default.
        You could change "displayed" to others, please refer to the manual for more details
    '''

    @Feat()
    def idn(self):
        return self.query('*IDN?')
        #return the identification number

    @Action()
    def set_CW_mode(self):
        return self.write(':FREQ:MODE CW')

    @Action()
    def set_CW_Freq(self,freq):
        return self.write(':FREQ {} Hz'.format(freq))  

    @Action()
    def internal_FM(self):
    	return self.write(':FM:SOUR INT')

    @Action()
    def external_FM(self):
        return self.write(':FM:SOUR EXT')	

    @Action()
    def FM_ON(self):
        return self.write('FM:STAT ON')


    @Action()
    def FM_OFF(self):
        return self.write('FM:STAT OFF')


    @Action()
    def FM_Deviation(self,deviation):
        return self.write(':FM {} Hz'.format(deviation))

    @Action()
    def RF_ON(self):
        return self.write(':OUTPut ON')

    @Action()
    def RF_OFF(self):
        return self.write(':OUTPut OFF')

    @Action()
    def set_RF_Power(self,pow):
        return self.write(':POWer {}dBm'.format(pow))

    @Action()
    def Mod_ON(self):
        return self.write(':OUTPut:MODulation ON')

    @Action()
    def Mod_OFF(self):
        return self.write(':OUTPut:MODulation OFF')

if __name__ == '__main__':
    import time
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')
    kHz = Q_(1,'kHz')
    MHz = Q_(1.0,'MHz')
    GHz = Q_(1.0,'GHz')
    dB = Q_(1,'dB')
    dBm = Q_(1,'dB')

    channel=1

    log_to_screen(DEBUG)

    with N5181A('TCPIP0::A-N5181A-41097::inst0::INSTR') as inst:
        print('The identification number of this instrument is :' + str(inst.idn))


        inst.RF_OFF()
        # inst.Mod_ON()
        # inst.set_CW_mode()
        # inst.set_CW_Freq(5.0994e9)
        # inst.FM_ON()
        # inst.FM_Deviation(2e4)
        # inst.external_FM()
        # inst.set_RF_Power(-9)

        
 




