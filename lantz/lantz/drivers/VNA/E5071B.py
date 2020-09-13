#Driver for Keysight E5071B
#Shobhit Gupta 12/2020

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep
import numpy as np
import matplotlib.pyplot as plt

class E5071B(MessageBasedDriver):
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

    # @Feat()
    # def measure_para(self):
    #     return self.query('CALC:MEAS1:PAR?')
    #     # return the measurement parameters
    #     # typical values: "S11","S21","S12","S22"

    # @measure_para.setter
    # def measure_para(self,value):
    #     return self.write('CALC:MEAS1:PAR {}'.format(value))
    #     # set the measurement parameters
    #     # typical values: "S11","S21","S12","S22"

    @Feat(units='Hz')
    def IF_bandwidth(self):
        return self.query('SENS1:BAND?')
        # return the IF bandwidth

    @IF_bandwidth.setter
    def IF_bandwidth(self,value):
        return self.write('SENS1:BAND {}'.format(value))
        # set the IF bandwidth
        # should be these values: 10|20|30|50|100|200|300|500|1k|2k|3k|5k|10k|20k|30k|50k|100k|300k|600k|1.2M

    @Feat(units='Hz')
    def freq_cent(self):
        return self.query('SENS1:FREQ:CENT?')
        # return the center frequency
        # should be in the range from 300 kHz to 6500 MHz

    @freq_cent.setter
    def freq_cent(self,value):
        return self.write('SENS1:FREQ:CENT {}'.format(value))
        # set the center frequency
        # should be in the range from 300 kHz to 6500 MHz

    @Feat(units='Hz')
    def freq_span(self):
        return self.query('SENS1:FREQ:SPAN?')
        # return the frequency span

    @freq_span.setter
    def freq_span(self,value):
        return self.write('SENS1:FREQ:SPAN {}'.format(value))
        # set the frequency span


    @Feat()
    def source_power(self):
        return self.query('SOUR1:POW?')
        # return the power

    @source_power.setter
    def source_power(self,value):
        return self.write('SOUR1:POW {}'.format(value))


    @Feat()
    def s_parameter(self,channel,trace):
        return self.query(':CALC{}:PAR{}:DEF?'.format(channel,trace))
        # return the power

    @Action()
    def set_s_parameter(self,channel,trace,value):
        return self.write(':CALC{}:PAR{}:DEF {}'.format(channel,trace,value))

    @Action()

    def autoscale(self,channel,trace):
        return self.write(":DISP:WIND{}:TRAC{}:Y:AUTO".format(channel,trace))

    @Action()
    def save_csv(self,value):
        return self.write('MMEM:STOR:FDAT "{}"'.format(value))

    @Action()
    def save_img(self,value):
        return self.write('MMEM:STOR:IMAG "{}"'.format(value))

    @Action()
    def get_trace(self,channel):
        a = self.query('CALC{}:DATA:FDAT?'.format(channel))
        # time.sleep(5)                
        answer=np.fromstring(a, dtype=np.float, sep=',')
        answer=np.array(answer)
        data=answer[0:][::2]
        return(data)


    @Action()
    def get_traceX(self,channel):
        a = self.query(':SENS1:FREQ:DATA?'.format(channel))
        # time.sleep(5)                
        answer=np.fromstring(a, dtype=np.float, sep=',')
        data=np.array(answer)
        # data=answer[0:][::2]
        return(data)

    @Action()
    def set_active_trace(self,channel,trace):
        return self.write(':CALC{}:PAR{}:SEL'.format(channel,trace))


    @Action()
    def set_average(self,channel,state):
        return self.write(':SENS{}:AVER {}'.format(channel,state))

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

    # log_to_screen(DEBUG)

    with E5071B('TCPIP0::169.254.137.9::inst0::INSTR') as inst:
        print('The identification number of this instrument is :' + str(inst.idn))
        print('The date of this instrument is :' + str(inst.date))
        print('The day of this instrument is :' + str(inst.day))
        # inst.marker[channel] = 'ON'
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
        print(inst.time)
        print(inst.hours)
        print(inst.minutes)
        print(inst.seconds)
        # inst.target_value[channel] = 8.6*dB
        # print(inst.target_value[channel])
        # inst.marker_min_search[channel]
        # inst.marker_target_left_search[channel]
        # inst.marker_target_right_search[channel]
        # inst.marker_min_search[channel]
        # print(inst.marker_Y[channel].magnitude)
        #inst.save_csv_second('D:/MW data/test/20190809/cavity/test/csv/2/phase/1.csv')
        # inst.save_csv('HAO/test01.csv')
        # inst.save_img('HAO/imag01.bmp')

        # inst.source_power=-30
        inst.IF_bandwidth=3000
        inst.freq_cent=4.9610e9
        # inst.freq_cent=5.5e9
        inst.freq_span=1e6
        inst.set_average(1,'OFF') 

        inst.autoscale(1,1)
        tr1=inst.get_trace(1)
        freq1=inst.get_traceX(1)

        time.sleep(10)

        plt.scatter(freq1,tr1,s=1)
        plt.plot(freq1,tr1,label='Trace1')
        # plt.show()


        # inst.set_active_trace(1,2)

        # tr2=inst.get_trace(1)
        # freq2=inst.get_traceX(1)

        # time.sleep(2)

        # plt.scatter(freq2,tr2,s=1)
        # plt.plot(freq2,tr2,label='Trace2')
        plt.legend()
        plt.show()
        inst.set_s_parameter(1,1,'S21')
        # inst.set_active_trace(1,2)
        # print("  ")
