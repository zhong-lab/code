from lantz.drivers.keysight.Keysight_66322A import Keysight_33622A
from lantz.drivers.keysight.arbseq_class import Arbseq_Class

class SeqBuild(object):

    def __init__(self, seqtype, params):
        self.seqtype = seqtype
        self.params = params
        self.arbseq = None

    def build_arbseq(self, name, timestep):
        arbseq = Arbseq_Class(name, timestep)
        seqtype = self.seqtype
        
        if seqtype == 'dc':
            totaltime = self.params['totaltime']
            arbseq.totaltime = totaltime
            arbseq.heights = [1]
            arbseq.delays = [0]
            arbseq.widths = [totaltime]
            arbseq.create_sequence()
        elif seqtype == 'pulse':
            totaltime = self.params['totaltime']
            period = self.params['period']
            width = self.params['width']
            delay = period - width
            pulses = int(totaltime / period)
            arbseq.totaltime = totaltime
            arbseq.heights = [1] * pulses
            arbseq.delays = [delay] * pulses
            arbseq.widths = [width] * pulses
            arbseq.create_sequence()
        elif seqtype == 'ramp':
            slope = self.params['slope']
            height = 0
            heights = list()
            while height <= 1:
                heights.append(height)
                height += (slope * timestep)
            arbseq.heights = heights
            arbseq.widths = [timestep] * len(heights)
            arbseq.delays = [0] * len(heights)
            arbseq.totaltime = len(heights) * timestep
            arbseq.create_sequence()

        """
        arbseq.nrepeats = self.params['nrepeats']
        arbseq.repeatstring = self.params['repeatstring']
        arbseq.markerstring = self.params['markerstring']
        arbseq.markerloc = self.params['markerloc']
        """

        self.arbseq = arbseq



if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    testseq = Arbseq_Class('testseq', 1)
    testseq.totaltime = 10e4
    testseq.widths = (5, 5, 5, 5)
    testseq.delays = (5, 20, 20, 20)
    testseq.heights = (0.25, 0.5, 0.75, 1)
    testseq.create_sequence()
    #print('testseq: ' + testseq.ydata)
    testseq.nrepeats = 10
    testseq.repeatstring = 'repeat'
    testseq.markerstring = 'lowAtStart'
    testseq.markerloc = 10

    testseq2 = Arbseq_Class('testseq2', 1)
    testseq2.totaltime = 100
    testseq2.widths = (5, 5, 5, 5)
    testseq2.delays = (5, 20, 20, 20)
    testseq2.heights = (1, 0.75, 0.5, 0.25)
    testseq2.create_sequence()
    #print('testseq2: ' + testseq2.ydata)
    testseq2.nrepeats = 10
    testseq2.repeatstring = 'repeat'
    testseq2.markerstring = 'lowAtStart'
    testseq2.markerloc = 10

    params = {'totaltime': 100, 'period': 20, 'width': 10,
                'nrepeats': 10, 'repeatstring': 'repeat', 'markerstring': 'lowAtStart', 'markerloc': 10}
    
    seqbuild1 = SeqBuild('dc', params)
    seqbuild1.build_arbseq('testseq3', 1)
    testseq3 = seqbuild1.arbseq

    seqbuild2 = SeqBuild('pulse', params)
    seqbuild2.build_arbseq('testseq4', 1)
    testseq4 = seqbuild2.arbseq

    fulltestseq = [testseq3, testseq4]

    with Keysight_33622A('USB0::0x0957::0x5707::MY53801461::0::INSTR') as inst:
        print('The identification of this instrument is :' + inst.idn)
        inst.clear_status()
        inst.output[1] = 'ON'
        inst.clear_mem()
        inst.send_arb(testseq)
        #inst.clear_mem()
        inst.load_arb('testseq')

        #inst.clear_mem()
        #inst.create_arbseq('fulltestseq',fulltestseq)


