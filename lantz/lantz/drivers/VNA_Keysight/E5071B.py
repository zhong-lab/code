#Driver for Keysight E5071B

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class E5071B(MessageBasedDriver):
    """This is the driver for the Keysight E5071B."""

    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'}}

    ''' 

    '''

    @Feat()
    def idn(self):
        return self.query('*IDN?')
        #return the identification number

    @Feat()
    def date(self):
        return self.query(':SYSTem:DATE?')
        # return the date

    @Feat()
    def day(self):
        buffer_Y = self.query(':SYSTem:DATE?')
        part = buffer_Y.split('+')
        return float(part[3])
        # return the day of date

    @Feat()
    def time(self):
        return self.query('SYST:TIME?')
        # return the time

    @Feat()
    def hours(self):
        buffer_t = self.query(':SYSTem:TIME?')
        part = buffer_t.split(',')
        return float(part[0])
        # return the hours

    @Feat()
    def minutes(self):
        buffer_t = self.query(':SYSTem:TIME?')
        part = buffer_t.split(',')
        return float(part[1])
        # return the minutes

    @Feat()
    def seconds(self):
        buffer_t = self.query(':SYSTem:TIME?')
        part = buffer_t.split(',')
        return float(part[2])
        # return the seconds


    @DictFeat(values={'ON':'1','OFF':'0'})
    def marker(self,key):
        return self.query(':CALC1:MARK{}?'.format(key))
        # return the state of marker
        # using key to decide the number of marker

    @marker.setter
    def marker(self,key,value):
        return self.write(':CALC1:MARK{} {}'.format(key,value))
        # set the state of marker to ON/OFF
        # can be used as inst.marker[channel]='ON'

    @DictFeat(units='Hz',limits=(300000,6500000000,0.1))
    def marker_X(self,key):
        return self.query(':CALC1:MARK{}:X?'.format(key))
        # return the X value of marker
        
    @marker_X.setter
    def marker_X(self,key,value):
        return self.write(':CALC1:MARK{}:X {}'.format(key,value))
        # set the X value of marker
        # can be used as e.g. inst.marker_X[2]=Q_(3.55,'GHz')
        # measurement number is set to 1, you could change it after 'MEAS'

    @DictFeat(units='dB')
    def marker_Y(self,key):
        buffer_Y = self.query(':CALC1:MARK{}:Y?'.format(key))
        part = buffer_Y.split(',')
        return part[0]
        # return the Y value of marker
        # note that it normally returns two values, we split it apart and read the first value
        # measurement number is set to 1, you could change it after 'MEAS'

    @Action()
    def save_csv(self,value):
        return self.write(':MMEM:STOR:FDAT "{}"'.format(value))
        # save data in specific path in csv format
        # can be used as inst.save_csv('C:/Users/lenovo/Desktop/Project/program/driver/VNA/data/1.csv')
        # please note that names of csv files could not be the same as existing files in current folder, or could not be saved


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

    with E5071B('TCPIP0::A-E5071B-03400::inst0::INSTR') as inst:
        print('The identification number of this instrument is :' + str(inst.idn))
        print('The date of this instrument is :' + str(inst.date))
        print('The day of this instrument is :' + str(inst.day))
        print('The hour of this instrument is :' + str(inst.hours))
        print('The minute of this instrument is :' + str(inst.minutes))
        print('The second of this instrument is :' + str(inst.seconds))
        # inst.save_csv('D:/20190923/5.csv')
        print(inst.marker[channel])
        inst.marker[channel] = 'ON'
        inst.marker_X[channel] = 4*GHz
        print(inst.marker_X[channel])
        print(inst.marker_Y[channel])
        # inst.measure_para='S11'
        # print(inst.measure_para)
        # inst.auto_scale()
        # inst.IF_bandwidth = 23*kHz
        # print(inst.IF_bandwidth)
        # inst.freq_cent = 4.1*GHz
        # print(inst.freq_cent)
        # inst.freq_span = 100*MHz
        # print(inst.freq_span)
        # inst.marker_peak_search[channel]
        # print(inst.time)
        # print(inst.hours)
        # print(inst.minutes)
        # print(inst.seconds)
        # inst.target_value[channel] = 8.6*dB
        # print(inst.target_value[channel])
        # inst.marker_min_search[channel]
        # inst.marker_target_left_search[channel]
        # inst.marker_target_right_search[channel]
        # inst.marker_min_search[channel]
        # print(inst.marker_Y[channel].magnitude)
        #inst.save_csv_second('D:/MW data/test/20190809/cavity/test/csv/2/phase/1.csv')