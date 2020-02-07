#Driver for Stanford Research Systems SR865A
#Yuxiang Pei 09/2019

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class SR865A(MessageBasedDriver):
    """This is the driver for Stanford Research Systems SR865A."""

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'}}

    ''' 

    '''

    @Feat()
    def idn(self):
        return self.query('*IDN?')
        # return the identification number

    @Feat()
    def Data_Four(self):
        return self.query('SNAPD?')
        # return the values of four parameters presently displayed as Data 1 through Data 4, at a single instant

    @Feat()
    def Scan_Time(self):
        return self.query('SCNSEC?')

    @Feat()
    def System_Time_Seconds(self):
        return float(self.query('TIME? SEC'))

    @Feat(units='Hz')
    def Internal_Frequency(self):
        return self.query('FREQINT?')

    @Internal_Frequency.setter
    def Internal_Frequency(self,value):
        return self.write('FREQINT {}'.format(value))



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

    Dlist=[]

    log_to_screen(DEBUG)

    with SR865A('GPIB2::4::INSTR') as inst:
        print('The identification number of this instrument is :' + str(inst.idn))
        # t_0 = inst.System_Time_Seconds
        print(inst.Data_Four)

        # while(inst.System_Time_Seconds-t_0>=0):
        #     buffer_D = inst.Data_Four
        #     part = buffer_D.split(',')
        #     t = inst.System_Time_Seconds - t_0
        #     with open('C:/Users/lenovo/Desktop/Project/lock-in/data/20190907/6000k.txt','a') as file:
        #         write_str='%s %s %s %s %f\n'%(part[0],part[1],part[2],part[3],t)
        #         file.write(write_str)
