#Driver for Keysight P9371A
#Yuxiang Pei 08/2019

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class P9371A(MessageBasedDriver):
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

    @Feat()
    def date(self):
        return self.query('SYST:DATE?')
        # return the date

    @Feat()
    def day(self):
        buffer_Y = self.query('SYST:DATE?')
        part = buffer_Y.split('+')
        return float(part[3])
        # return the day of date

    @Feat()
    def time(self):
        return self.query('SYST:TIME?')
        # return the time

    @Feat()
    def hours(self):
        buffer_t = self.query('SYST:TIME?')
        part = buffer_t.split(',')
        return float(part[0])
        # return the hours

    @Feat()
    def minutes(self):
        buffer_t = self.query('SYST:TIME?')
        part = buffer_t.split(',')
        return float(part[1])
        # return the minutes

    @Feat()
    def seconds(self):
        buffer_t = self.query('SYST:TIME?')
        part = buffer_t.split(',')
        return float(part[2])
        # return the seconds

    @Feat()
    def measure_para(self):
        return self.query('CALC:MEAS1:PAR?')
        # return the measurement parameters
        # typical values: "S11","S21","S12","S22"

    @measure_para.setter
    def measure_para(self,value):
        return self.write('CALC:MEAS1:PAR {}'.format(value))
        # set the measurement parameters
        # typical values: "S11","S21","S12","S22"

    @Feat(units='Hz')
    def IF_bandwidth(self):
        return self.query('SENS:BWID?')
        # return the IF bandwidth

    @IF_bandwidth.setter
    def IF_bandwidth(self,value):
        return self.write('SENS:BWID {}HZ'.format(value))
        # set the IF bandwidth
        # should be these values: 10|20|30|50|100|200|300|500|1k|2k|3k|5k|10k|20k|30k|50k|100k|300k|600k|1.2M

    @Feat(units='Hz',limits=(300000,6500000000,0.1))
    def freq_cent(self):
        return self.query('SENS:FREQ:CENT?')
        # return the center frequency
        # should be in the range from 300 kHz to 6500 MHz

    @freq_cent.setter
    def freq_cent(self,value):
        return self.write('SENS:FREQ:CENT {}'.format(value))
        # set the center frequency
        # should be in the range from 300 kHz to 6500 MHz

    @Feat(units='Hz',limits=(150000,3250000000,0.1))
    def freq_span(self):
        return self.query('SENS:FREQ:SPAN?')
        # return the frequency span

    @freq_span.setter
    def freq_span(self,value):
        return self.write('SENS:FREQ:SPAN {}'.format(value))
        # set the frequency span

    @DictFeat(values={'ON':'1','OFF':'0'})
    def marker(self,key):
        return self.query('CALC:MEAS1:MARK{}:STAT?'.format(key))
        # return the state of marker
        # using key to decide the number of marker

    @marker.setter
    def marker(self,key,value):
        return self.write('CALC:MEAS1:MARK{}:STAT {}'.format(key,value))
        # set the state of marker to ON/OFF
        # can be used as inst.marker[channel]='ON'

    @DictFeat(values={'ON':'1','OFF':'0'})
    def marker_second(self,key):
        return self.query('CALC:MEAS2:MARK{}:STAT?'.format(key))
        # return the state of marker
        # using key to decide the number of marker

    @marker_second.setter
    def marker_second(self,key,value):
        return self.write('CALC:MEAS2:MARK{}:STAT {}'.format(key,value))
        # set the state of marker to ON/OFF
        # can be used as inst.marker[channel]='ON'


    @DictFeat(units='Hz',limits=(300000,6500000000,0.1))
    def marker_X(self,key):
        return self.query('CALC:MEAS1:MARK{}:X?'.format(key))
        # return the X value of marker
        
    @marker_X.setter
    def marker_X(self,key,value):
        return self.write('CALC:MEAS1:MARK{}:X {}'.format(key,value))
        # set the X value of marker
        # can be used as e.g. inst.marker_X[2]=Q_(3.55,'GHz')
        # measurement number is set to 1, you could change it after 'MEAS'

    @DictFeat(units='Hz',limits=(300000,6500000000,0.1))
    def marker_X_second(self,key):
        return self.query('CALC:MEAS2:MARK{}:X?'.format(key))
        # return the X value of marker
        
    @marker_X_second.setter
    def marker_X_second(self,key,value):
        return self.write('CALC:MEAS2:MARK{}:X {}'.format(key,value))
        # set the X value of marker
        # can be used as e.g. inst.marker_X[2]=Q_(3.55,'GHz')
        # measurement number is set to 1, you could change it after 'MEAS'

    @DictFeat(units='dB')
    def marker_Y(self,key):
        buffer_Y = self.query('CALC:MEAS1:MARK{}:Y?'.format(key))
        part = buffer_Y.split(',')
        return part[0]
        # return the Y value of marker
        # note that it normally returns two values, we split it apart and read the first value
        # measurement number is set to 1, you could change it after 'MEAS'

    @DictFeat(units='dB')
    def marker_Y_second(self,key):
        buffer_Y = self.query('CALC:MEAS2:MARK{}:Y?'.format(key))
        part = buffer_Y.split(',')
        return part[0]
        # return the Y value of marker
        # note that it normally returns two values, we split it apart and read the first value
        # measurement number is set to 1, you could change it after 'MEAS'

    @DictFeat()
    def marker_peak_search(self,key):
        return self.write('CALC:MEAS1:MARK{}:FUNC:EXEC MAX'.format(key))
        # do marker peak search

    @DictFeat()
    def marker_peak_search_second(self,key):
        return self.write('CALC:MEAS2:MARK{}:FUNC:EXEC MAX'.format(key))
        # do marker peak search

    @DictFeat()
    def marker_min_search(self,key):
        return self.write('CALC:MEAS1:MARK{}:FUNC:EXEC MIN'.format(key))
        # do marker minimum search

    @DictFeat()
    def marker_min_search_second(self,key):
        return self.write('CALC:MEAS2:MARK{}:FUNC:EXEC MIN'.format(key))
        # do marker minimum search


    @DictFeat(units='dB')
    def target_value(self,key):
        return self.query('CALC:MEAS1:MARK{}:FUNC:TARG?'.format(key))
        # return the target value

    @target_value.setter
    def target_value(self,key,value):
        return self.write('CALC:MEAS1:MARK{}:FUNC:TARG {}'.format(key,value))
        # sets the target value

    @DictFeat()
    def marker_target_left_search(self,key):
        return self.write('CALC:MEAS1:MARK{}:FUNC:EXEC LTAR'.format(key))
        # do marker target left search

    @DictFeat()
    def marker_target_right_search(self,key):
        return self.write('CALC:MEAS1:MARK{}:FUNC:EXEC RTAR'.format(key))
        # do marker target right search

    @DictFeat()
    def marker_target_left_search_second(self,key):
        return self.write('CALC:MEAS2:MARK{}:FUNC:EXEC LTAR'.format(key))
        # do marker target left search

    @DictFeat()
    def marker_target_right_search_second(self,key):
        return self.write('CALC:MEAS2:MARK{}:FUNC:EXEC RTAR'.format(key))
        # do marker target right search

    @DictFeat()
    def marker_to_center(self,key):
        return self.write('CALC:MEAS1:MARK{}:SET CENT'.format(key))
        # set the key marker to center

    @DictFeat()
    def marker_to_center_second(self,key):
        return self.write('CALC:MEAS2:MARK{}:SET CENT'.format(key))
        # set the key marker to center

    @Action()
    def auto_scale(self):
        return self.write('DISP:MEAS1:Y:AUTO')
        # set the Y axis auto scale
        # can be used as inst.auto_scale()

    @Action()
    def auto_scale_second(self):
        return self.write('DISP:MEAS2:Y:AUTO')
        # set the Y axis auto scale
        # can be used as inst.auto_scale()

    @Action()
    def save_csv(self,value):
        return self.write('MMEMory:STORe:DATA "{}","CSV Formatted Data","Trace","Displayed",1'.format(value))
        # save data in specific path in csv format
        # can be used as inst.save_csv('C:/Users/lenovo/Desktop/Project/program/driver/VNA/data/1.csv')
        # please note that names of csv files could not be the same as existing files in current folder, or could not be saved

    @Action()
    def save_csv_second(self,value):
        return self.write('MMEMory:STORe:DATA "{}","CSV Formatted Data","Trace","Displayed",2'.format(value))
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

    with P9371A('TCPIP0::DESKTOP-ER250Q8::hislip0,4880::INSTR') as inst:
        print('The identification number of this instrument is :' + str(inst.idn))
        print('The date of this instrument is :' + str(inst.date))
        print('The day of this instrument is :' + str(inst.day))
        # inst.save_csv('C:/Users/lenovo/Desktop/Project/program/driver/VNA/data/5.csv')
        inst.marker[channel] = 'ON'
        # print(inst.marker[channel])
        # inst.marker_X[channel] = 4*GHz
        # print(inst.marker_X[channel])
        # print(inst.marker_Y[channel])
        # inst.measure_para='S21'
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
        inst.marker_min_search[channel]
        print(inst.marker_Y[channel].magnitude)
        #inst.save_csv_second('D:/MW data/test/20190809/cavity/test/csv/2/phase/1.csv')