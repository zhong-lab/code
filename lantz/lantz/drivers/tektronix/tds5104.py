# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.tds5104
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.
"""

import struct
import matplotlib.pyplot as plt
import numpy as np
import os
import time

from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class TDS5104(MessageBasedDriver):
    """Tektronix TDS2024 200 MHz 4 Channel Digital Real-Time Oscilloscope
    """

    #DEFAULTS = {'COMMON': {'write_termination': '\n', 'read_termination': '\n'}}

    @Action()
    def autoconf(self):
        """Autoconfig oscilloscope.
        """
        self.write(':AUTOS EXEC')

    def init(self):
        """initiate.
        """
        self.write(':ACQ:STATE ON')
        return "Init"

    @Feat()
    def idn(self):
        """IDN.
        """
        return self.query('ID?')

    @Feat()
    def trigger(self):
        """Trigger state.
        """
        return self.query(':TRIG:STATE?')

    @trigger.setter
    def trigger(self, mode):
        """Set trigger state.
        """
        self.write('TRIG:MAIN:MODE {}'.format(mode))

    @Feat()
    def mode(self):
        """Trigger state.
        """
        return self.query('ACQ?')

    @mode.setter
    def mode(self, mode):
        """Set trigger state.
        """
        temp = ''
        if mode == 'sample':
            temp = 'SAMP'
        elif mode == 'average':
            temp = 'AVE'
        elif mode == 'peak detect':
            temp = 'PEAK'
        if temp=='':
            print('cant set mode. keywords are: sample, average, peak detect')
        else:
            self.write('ACQ:MODE {}'.format(temp))

    @Action()
    def triggerlevel(self):
        """Set trigger level to 50% of the minimum adn maximum
        values of the signal.
        """
        self.write('TRIG:MAIn SATLevel')

    @Action()
    def forcetrigger(self):
        """Force trigger event.
        """
        self.write('TRIG FORCe')

    @Action()
    def datasource(self, chn):
        """Selects channel.
        """
        self.write(':DATA:SOURCE CH{}'.format(chn))

    @Action()
    def acqparams(self):
        """ X/Y Increment Origin and Offset.
        """
        commands = 'XZE?;XIN?;YZE?;YMU?;YOFF?'
        #params = self.query(':WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?')
        params = self.query(':WFMPRE:{}'.format(commands))
        params = {k: float(v) for k, v in zip(commands.split(';'), params.split(';'))}
        return params

    @Action()
    def dataencoding(self):
        """Set data encoding.
        """
        self.write(':DAT:ENC ascii;WID 2;')
        return "Set data encoding"

    # @Action()
    def curv(self):
        """Get data.

            Returns:
            xdata, ydata as list
        """
        self.dataencoding()
        self.write('DATa:STARt 1')
        self.write('DATa:STOP 1500000')
        answer = self.query_ascii('CURV?', delay=0)
        params = self.acqparams()
        data = np.array(answer)
        yoff = params['YOFF?']
        ymu = params['YMU?']
        yze = params['YZE?']
        xin = params['XIN?']
        xze = params['XZE?']
        ydata = (data - yoff) * ymu + yze
        xdata = np.arange(len(data)) * xin + xze
        return list(xdata), list(ydata)

    def _measure(self, typ, source):
        self.write('MEASUrement:IMMed:TYPe {}'.format(typ))
        self.write('MEASUrement:IMMed:SOUrce1 CH{}'.format(source))
        return self.query('MEASUrement:IMMed:VALue?')

    @Action()
    def measure_frequency(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('FREQuency', channel)

    @Action()
    def measure_min(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('MINImum', channel)

    @Action()
    def measure_max(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('MAXImum', channel)

    @Action()
    def measure_mean(self, channel):
        """Get immediate measurement result.
        """
        return self._measure('MEAN', channel)

    @Action()
    def set_time(self, time):
        self.write('HORizontal:MAIn:DELay:TIMe {}'.format(time))
        return

    @Action()
    def query_time(self):
        return self.query('HORizontal:MAIn:DELay:TIMe?')

    @Action()
    def average(self, number):
        self.write('ACQ:NUMAV {}'.format(number))   
        return

    @Action()
    def position(self, channel, position):
        self.write('CH{}:POS {}'.format(channel,position))
        return

    @Action()
    def scale_query(self, channel):
        return self.query('CH{}:SCA?'.format(channel))

    @Action()
    def scale(self, channel, scale):
        self.write('CH{}:SCA {}'.format(channel,scale))
        return

    @Action()
    def time_scale(self, scale):
        self.write('HORizontal:MAIn:SCAle {}'.format(scale))
        return

if __name__ == '__main__':
    import argparse
    import csv
    from lantz.log import log_to_screen, DEBUG

    parser = argparse.ArgumentParser(description='Measure using TDS2024 and dump to screen')
    parser.add_argument('-p', '--port', default='GPIB1::15::INSTR',
                       help='USB port')
    parser.add_argument('-v', '--view', action='store_true', default=False,
                        help='View ')
    parser.add_argument('Channels', metavar='channels', type=int, nargs='*',
                        help='Channels to use')
    parser.add_argument('--output', type=argparse.FileType('w'), default='-')

    args = parser.parse_args()

    log_to_screen(DEBUG)
    with TDS5104(args.port) as osc:
        osc.init()
        # print(osc.idn)
        #osc.set_time(0)
        # print(osc.trigger)
        # osc.average(16)
        #osc.datasource(1)
        #osc.position(1,1)
        #osc.scale(1,0.05)
        '''
        osc.mode = 'sample'
        x,y = osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        plt.plot(x,y)
        plt.show()
        '''
        osc.datasource(2)
        x,y=osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('chn21.txt', np.c_[x,y])
        time.sleep(1)

        osc.datasource(3)
        x,y=osc.curv()
        x = np.array(x)
        x = x-x.min()
        y = np.array(y)
        np.savetxt('chn31.txt', np.c_[x,y])

        # osc.forcetrigger()
        # osc.triggerlevel()
        # osc.trigger = "AUTO"
        # print(osc.trigger)
        # #osc.autoconf()
        # #params = osc.acqparams()

        # if args.view:
        #     import matplotlib.pyplot as plt
        #     import numpy as np

        # with args.output as fp:
        #     writer = csv.writer(fp, dialect='excel')
        #     writer.writerow(['Channel', 'Freq', 'Max', 'Min', 'Mean'])
        #     for channel in args.Channels:
        #         osc.datasource(channel)
        #         writer.writerow(([channel, osc.measure_frequency(channel),
        #                             osc.measure_max(channel),
        #                             osc.measure_min(channel),
        #                             osc.measure_mean(channel)]))

        #         if args.view:
        #             x, y = osc.curv()
        #             x = np.array(x)
        #             x = x - x.min()
        #             y = np.array(y)
        #             plt.plot(x, y)

        # if args.view:
        #     plt.show()
