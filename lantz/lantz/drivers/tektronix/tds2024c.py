# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix.tds2024b
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements the drivers to control an oscilloscope.

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

import struct
import matplotlib.pyplot as plt
import numpy as np

from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class TDS2024C(MessageBasedDriver):
    """Tektronix TDS2024 200 MHz 4 Channel Digital Real-Time Oscilloscope
    """

    MANUFACTURER_ID = '0x699'

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
        answer = self.query_ascii('CURV?', delay=3)
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
        self.write('HORizontal:MAIn:POSition {}'.format(time))
        return

    @Action()
    def query_time(self):
        return self.query('HORizontal:MAIn:POSition?')

    @Action()
    def average(self, number):
        if number in (4,16,64,128):
            self.write('ACQ:NUMAV {}'.format(number))
        else:
            print('can only average over 4, 16, 64, or 128 samples!')
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
    parser.add_argument('-p', '--port', default='USB0::0x0699::0x03A6::C030873::INSTR',
                       help='USB port')
    parser.add_argument('-v', '--view', action='store_true', default=False,
                        help='View ')
    parser.add_argument('Channels', metavar='channels', type=int, nargs='*',
                        help='Channels to use')
    parser.add_argument('--output', type=argparse.FileType('w'), default='-')

    args = parser.parse_args()

    log_to_screen(DEBUG)
    with TDS2024C(args.port) as osc:
        #osc.init()
        # print(osc.idn)
        #osc.set_time(0)
        # print(osc.trigger)
        # osc.average(16)
        #osc.position(1,1)
        #osc.scale(1,0.05)
        #osc.datasource=
        #osc.mode = 'sample'
        #x,y = osc.curv()
        #x = np.array(x)
        #x = x-x.min()
        #y = np.array(y)
        #plt.plot(x,y)
        #plt.show()
        # osc.forcetrigger()
        # osc.triggerlevel()
        # osc.trigger = "AUTO"
        # print(osc.trigger)
        # #osc.autoconf()
        # #params = osc.acqparams()

        # if args.view:
        #     import matplotlib.pyplot as plt
        #     import numpy as np
         """
         the following prints the channels to a CSV file and also plots the
         oscilloscope screen.
         """
         filename="max_coupling"
         plotlist=[]
         colors=plt.rcParams["axes.prop_cycle"].by_key()["color"]
         with open(filename+".csv", "w", newline='') as myfile:
             wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
             #wr.writerow(['Channel', 'Freq', 'Max', 'Min', 'Mean'])
             alllists=[]
             for channel in args.Channels:
                 osc.datasource(channel)
                 x,y = osc.curv()
                 xlist=list(x)
                 ylist=list(y)
                 if len(plotlist)==0:
                     fig,ax=plt.subplots()
                 else:
                     ax=ax.twinx()
                 p=ax.plot(xlist,ylist,color=colors[channel])
                 plotlist.append(p)
                 alllists.append(xlist)
                 alllists.append(ylist)
             for i in range(len(x)):
                 wr.writerow(([l[i] for l in alllists]))

         plt.show()
