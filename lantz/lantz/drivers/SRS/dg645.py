##@Yuxinag
##Driver for Stanford Research Systems DG645

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class DG645(MessageBasedDriver):
    """This is the driver for the Stanford Research Systems DG645."""

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\r\n'}}

    @Feat()
    def idn(self):
        return self.query('*IDN?')
        # return the identification number

    @Feat()
    def Clear_Status(self):
        return self.write('*CLS')
        # immediately clears the ESR and INSR registers as well as the LERR error buffer
        # e.g. inst.Clear_Status

#################### This is trigger setting part.######################

    @Feat(values={'Internal':'0','External rising edges':'1','External falling edges':'2','Single shot external rising edges':'3',\
        'Single shot external falling edges':'4','Single shot':'5','Line':'6'})
    def Trigger_Source(self):
        return self.query('TSRC?')
        # return the trigger source

    @Trigger_Source.setter
    def Trigger_Source(self,value):
        return self.write('TSRC {}'.format(value))
        # set the trigger source

    @Feat(values={'ON':'1','OFF':'0'})
    def Trigger_Advance_Mode(self):
        return self.query('ADVT?')
        # return the state of trigger advance mode: if it is ON or OFF

    @Trigger_Advance_Mode.setter
    def Trigger_Advance_Mode(self,value):
        return self.write('ADVT {}'.format(value))
        # set the state of trigger advance mode: if it is ON or OFF

    @Feat(units='s')
    def Trigger_Holdoff(self):
        return self.query('HOLD?')
        # return the value of trigger holdoff
        # e.g. Holdoff triggers for 1 µs after each delay cycle is initiated

    @Trigger_Holdoff.setter
    def Trigger_Holdoff(self,value):
        return self.write('HOLD {}'.format(value))
        # set trigger holdoff time

    @Feat(units='Hz')
    def Trigger_Rate(self):
        return self.query('TRAT?')
        # return the internal trigger rate

    @Trigger_Rate.setter
    def Trigger_Rate(self,value):
        return self.write('TRAT {}'.format(value))
        # set the internal trigger rate

    @Feat(units='volt')
    def Trigger_Level(self):
        return self.query('TLVL?')
        # return the external trigger level

    @Trigger_Level.setter
    def Trigger_Level(self,value):
        return self.write('TLVL {}'.format(value))
        # set the external trigger level

    @Feat()
    def Step_Size_Trigger_Rate(self):
        return self.query('SSTR?')
        # return the current step size for the internal trigger rate

    @Action()
    def Trigger_A_Delay(self):
        return self.write('*TRG')
        # When the DG645 is configured for single shot triggers, this command initiates a single trigger.
        # When it is configured for externally triggered single shots, 
        # this command arms the DG645 to trigger on the next detected external trigger. 


#################### This is burst setting part.########################

    @Feat(values={'ON':'1','OFF':'0'})
    def Burst_Mode(self):
        return self.query('BURM?')
        # return the state of burst mode: if it is ON or OFF

    @Burst_Mode.setter
    def Burst_Mode(self,value):
        return self.write('BURM {}'.format(value))
        # set the state of burst mode: ON or OFF

    @Feat()
    def Burst_Count(self):
        return self.query('BURC?')
        # return the number of burst count
        #  Burst count can be any number from 1 to 2^32 − 1

    @Burst_Count.setter
    def Burst_Count(self,value,limits=(1,4294967295,1)):
        return self.write('BURC {}'.format(value))
        # set the number of burst count

    @Feat(units='s')
    def Burst_Delay(self):
        return self.query('BURD?')
        # return the value of burst delay

    @Burst_Delay.setter
    def Burst_Delay(self,value):
        return self.write('BURD {}'.format(value))
        # set the value of burst delay

    @Feat(units='s')
    def Burst_Period(self):
        return self.query('BURP?')
        # return the value of burst period

    @Burst_Period.setter
    def Burst_Period(self,value):
        return self.write('BURP {}'.format(value))
        # set the value of burst period


#################### This is delay setting part.#######################

    @DictFeat(units='s')
    def Delay_Channel(self,key):
        buffer_D = self.query('DLAY?{}'.format(key))
        part = buffer_D.split(',')
        return part[1]
        # return the delay of each channel
        # 0--T0   # 5--D
        # 1--T1   # 6--E
        # 2--A    # 7--F
        # 3--B    # 8--G
        # 4--C    # 9--H

    @Delay_Channel.setter
    def Delay_Channel(self,key,value):
        return self.write('DLAY {},0,{}'.format(key,value))
        # set the delay of each channel

#################### This is output setting part.#######################

    @DictFeat(units='volt')
    def Level_Amplitude(self,key):
        return self.query('LAMP?{}'.format(key))
        # return the output amplitude of output channel
        # 0--T0   # 3--EF
        # 1--AB   # 4--GH
        # 2--CD

    @Level_Amplitude.setter
    def Level_Amplitude(self,key,value):
        return self.write('LAMP{},{}'.format(key,value))
        # set the output amplitude of output channel


    @DictFeat(units='volt')
    def Level_Offset(self,key):
        return self.query('LAMP?{}'.format(key))
        # return the offset for output channel
        # 0--T0   # 3--EF
        # 1--AB   # 4--GH
        # 2--CD

    @Level_Offset.setter
    def Level_Offset(self,key,value):
        return self.write('LAMP{},{}'.format(key,value))
        # set the offset for output channel




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
    s = Q_(1,'s')
    ms = Q_(1,'ms')
    us = Q_(1,'us')

    log_to_screen(DEBUG)

    with DG645('TCPIP0::169.254.29.167::inst0::INSTR') as inst:
        # print('The identification number of this instrument is :' + str(inst.idn))
        inst.Clear_Status
        # inst.Trigger_Source='Single shot'
        # inst.Trigger_Source='Internal'
        # inst.Trigger_Source='External falling edges'
        inst.Trigger_Source='External rising edges'
        # print(inst.Trigger_Source)
        # inst.Burst_Mode='ON'
        # print(inst.Burst_Mode)
        # inst.Burst_Count=3
        # print(inst.Burst_Count)
        # inst.Burst_Delay=0*s
        # print(inst.Burst_Delay)
        # inst.Burst_Period=0.1*ms
        # print(inst.Burst_Period)
        # inst.Trigger_Advance_Mode='OFF'
        # print(inst.Trigger_Advance_Mode)
        # inst.Trigger_Holdoff=0*s
        # print(inst.Trigger_Holdoff)
        # inst.Trigger_Rate=1000*Hz
        # print(inst.Trigger_Rate)
        # inst.Trigger_Level=1.5*volt
        # print(inst.Trigger_Level)
        # print(inst.Step_Size_Trigger_Rate)
        # inst.Delay_Channel[5] = 0.05*us
        # print('\nChannel Delay:\nT0:{}\nT1:{}\nA:{}\nB:{}\nC:{}\nD:{}\nE:{}\nF:{}\nG:{}\nH:{}\n'.format(inst.Delay_Channel[0],\
        #     inst.Delay_Channel[1],inst.Delay_Channel[2],inst.Delay_Channel[3],inst.Delay_Channel[4],inst.Delay_Channel[5],\
        #     inst.Delay_Channel[6],inst.Delay_Channel[7],inst.Delay_Channel[8],inst.Delay_Channel[9]))
        # inst.Level_Amplitude[2]=2.5*volt
        # inst.Level_Offset[1]=2.0*volt
        # inst.Level_Amplitude[1]=2.5*volt
        # print('\nChannel Amplitude:\nT0:{}\nAB:{}\nCD:{}\nEF:{}\nGH:{}\n'.format(inst.Level_Amplitude[0],inst.Level_Amplitude[1],\
        #     inst.Level_Amplitude[2],inst.Level_Amplitude[3],inst.Level_Amplitude[4]))
        # print('\nChannel Level Offset:\nT0:{}\nAB:{}\nCD:{}\nEF:{}\nGH:{}\n'.format(inst.Level_Offset[0],inst.Level_Offset[1],\
        #     inst.Level_Offset[2],inst.Level_Offset[3],inst.Level_Offset[4]))
        # inst.Trigger_A_Delay()
        # time.sleep(1)
        # inst.Trigger_A_Delay()
        # time.sleep(1)
        # inst.Trigger_A_Delay()
        # time.sleep(1)

