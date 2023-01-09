# -*- coding: utf-8 -*-

import numpy as np
from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver

class SDS1204X(MessageBasedDriver):
    DEFAULTS = {'COMMON': {'write_termination': '\n', 'read_termination': '\n'}}

    @Feat()
    def idn(self):
        """
        Returns
        "Siglent Technologies,SDS1204X-E,SDSMMFCX5R6581,8.1.6.1.35R2"

        """
        return self.query('*IDN?')

    @Feat()
    def save(self):
        return self.query('WFDA?')

    @Action()
    def save_waveform(self, where):
        return self.write('WFDA {}'.format(where))

    # @Action()
    # def save_waveform(self, state):
    #     return self.write('CSV_SAVE SAVE {}'.format(state))

    @Action()
    def save_waveform(self):
        return self.write('CSVS')



if __name__ == '__main__':
    import time
    with SDS1204X('USB0::0xF4EC::0xEE38::SDSMMFCX5R6581::INSTR') as inst:
        idn=inst.idn
        print(idn)
        inst.save_waveform('C:\\Users\\QNet\\Downloads')
        time.sleep(30)
