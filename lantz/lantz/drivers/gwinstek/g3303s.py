# -*- coding: utf-8 -*-

import time
from lantz.messagebased import MessageBasedDriver
from lantz import Feat

class GPD3303S(MessageBasedDriver):
    DEFAULTS = {
        'COMMON': {
            'read_termination': '\r',
            'write_termination': '\n',
        },
    }

    @Feat(read_once=True)
    def idn(self):
        return self.query('*IDN?')

    @Feat
    def voltage(self):
        return self.query('VSET1?')

    def set_voltage(self, value):
        self.write('VSET1:{}'.format(value))

    def set_output(self, value):   
        self.write('OUT{}'.format(value))


if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    log_to_screen(DEBUG)
    with GPD3303S('ASRL22::INSTR') as inst:
        print('The identification of this instrument is:' + inst.idn)
        print('The voltage of this instrument is:' + inst.voltage)
        inst.set_voltage(12)
        print('The voltage of this instrument is:' + inst.voltage)
        inst.set_output(1)
        sleep(2)
        inst.set_output(0)
        



        
