from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from collections import OrderedDict

class Keysight_33622A(MessageBasedDriver):
    """This is the driver for the Keysight 36622A."""

    """For VISA resource types that correspond to a complete 488.2 protocol
    (GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
    generally do not need to use termination characters, because the
    protocol implementation also has a native mechanism to specify the
    end of the of a message.
    """

    DEFAULTS = {'COMMON': {'write_termination': '\n', 'read_termination': '\n'}}

    CHANNELS = OrderedDict([(1, 1),
                           (2,2)])

    TOGGLE = OrderedDict([("ON", 1),
                          ("OFF", 0)])

    WAVEFORMS = OrderedDict([('sine', "SIN"),
                             ('square', "SQU"),
                             ('triangle', "TRI"),
                             ('ramp', "RAMP"),
                             ('pulse', 'PULS'),
                             ('ps random noise', "PRBS"),
                             ('noise', 'NOIS'),
                             ('arbitrary', 'ARB'),
                             ('dc', "DC")])

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Action()
    def clear_status(self):
        """This command clears the following registers:
        1. Standard Event Status
        2. Operation Status Event
        3.  Questionable Status Event
        4. Status Byte
        5. Clears the Error Queue

        If this *CLS immediately follows a program message terminator (<NL>),
        then the output queue and teh MAV bit are also cleared.

        Command Syntax: *CLS
        Parameters:     (None)
        Query Syntax:   (None)

        """
        self.query('*CLS')

    '''
    @Feat()
    def event_status_enable(self, NRf):
        """Programs the Standard Event Status Enable register bits. The
        programming determines which events of the Standard Event Status
        Event register are allowed to set the ESB (Event Summary Bit) of the
        Status Byte register. A "1" in the bit position enables the
        corresponding event. All of the enabled events of the Standard Event
        Status Event register are logically ORed to cause the Event Summary
        Bit (ESB) of the Status Byte register to be set.

        Command Syntax:      *ESE<NRf>
        Parameters:          0 to 255
        Suffix:              (None)
        Example:             *ESE 129
        Query Syntax:        *ESE?
        Returned Parameters: <NRI> (Register value)
        Related Commands:    *ESR? *PSC *STB?

        CAUTION: If PSC is programmed to 0, then the *ESE command causes a
        write cycle to nonvolatile memory. The nonvolatille memory has a
        finite maximum number of write cycles. Programs that repeatedly
        cause write cycles to non-volatile memory can eventually exceed the
        maximum number of write cycles and may cause the memory to fail.
        """
        # NOTE: not sure if the left right angle brackets are necessary here
        return self.query('*ESE'+str(NRf))
    '''

    @Feat()
    def read_standard_event_status_register(self):
        """Reads the Standard Event Status Even register. Reading the
        register clears it.
        Query Syntax:        *ESR?
        Parameters:          (None)
        Returned Parameters: <NR1> (Register binary value)
        Related Commands:    *CLS *ESE *ESE? *OPC
        """
        return self.query('*ESR?')

    @Action()
    def operation_complete(self):
        """This command causes the interface to set the OPC bit (bit 0) of
        the Standard Event Status register when the power supply has completed
        all pending operations. Pending operations are complete when:
        - All commands sent before *OPC have been executed. This includes
        overlapped commands. Most commands are sequential and are completed
        before the next command is executed. Overlapped commands are
        executed in parallel with other commands. Commands that affect output
        voltage, current or state, relays, and trigger actions are overlapped
        with subsequent commands sent to the power supply. The *OPC command
        provides notification that all overlapped commands have been completed.
        - Any change in the output level caused by previous commands has been
        completed.
        - All triggered actions are completed.
        *OPC does not prevent processing of subsequent commands, but Bit 0
        will not be set until all pending operations are completed.
        Command Syntax: *OPC
        Parameters: 	(None)
        Related Commands *OPC? *WAI
        """
        self.query('*OPC')

    @Action()
    def operation_completed(self, delay=2):
        return self.query('*OPC?')

    @Action()
    def trigger(self):
        """Trigger Command: Triggers a sweep, burst, arbitrary waveform advance,
        or LIST advance from the remote interface if the bus (software)
        trigger source is currently selected (TRIGger[1|2]:SOURce BUS)
        """
        self.write('*TRG')

    @Feat()
    def test(self):
        """Self-Test Query: Performs a complete instrument self-test.
        If test fails, one or more error messages will provide additional information.
        Use SYSTem:ERRor? to read error queue
        """
        self.write('*TST?')

    @Action()
    def wait(self):
        """Configures the instrument to wait for all pending operations
        to complete before executing any additional commands over the interface

        For example, you can use this with the *TRG command to ensure that the instrument
        is ready for a trigger: *TRG;*WAI;*TRG
        """
        self.write('*WAI')

    @DictFeat(units='V', limits=(10,), keys=CHANNELS)
    def voltage(self, key):
        """returns current voltage
        """
        return float(self.query('SOURCE{}:VOLT?'.format(key)))

    @voltage.setter
    def voltage(self, key, value):
        """Voltage setter
        """
        self.write('SOURCE{}:VOLT {:1.6f}'.format(key, value))
    
    @DictFeat(units='V', limits=(-5, 5, .01), keys=CHANNELS)
    def offset(self, key):
        """returns current voltage offset
        """
        return float(self.query('SOURCE{}:VOLT:OFFS?'.format(key)))
    
    @offset.setter
    def offset(self, key, value):
        """Voltage offset setter
        """
        self.write('SOURCE{}:VOLT:OFFS {:1.6f}'.format(key, value))

    @DictFeat(units='Hz', limits=(1, 1e+5), keys=CHANNELS)
    def frequency(self, key):
        """returns current frequency
        """
        return float(self.query('SOURCE{}:FREQ?'.format(key)))

    @frequency.setter
    def frequency(self, key, value):
        """frequency setter
        """
        self.write('SOURCE{}:FREQ {:1.6f}'.format(key, value))

    @DictFeat(keys=(1, 2), values=WAVEFORMS)
    def waveform(self, key):
        """returns current waveform function
        """
        return self.query('SOURCE{}:FUNC?'.format(key))
    
    @waveform.setter
    def waveform(self, key, value):
        """waveform function setter
        """
        self.write('SOURCE{}:FUNC {}'.format(key, value))

    @DictFeat(keys=(1, 2))
    def load_arbitrary(self, filename, key):
        """Loads the specified arb segment(.arb/.barb)
        or arb sequence (.seq) file in INTERNAL or USB memory into
        volatile memory for the specified channel and displays arbitrary 
        file to given channel
        """
        self.write('MMEM:LOAD:DATA{} {}'.format(key, filename))
        self.write('SOURCE{}:FUNC:ARB {}'.format(key, filename))
        self.write('SOURCE{}:FUNC ARB'.format(key))

    @DictFeat(keys=(1, 2))
    def load_frequencies(self, filename, key):
        """loads frequency list from file"""
        self.write('MMEM:LOAD:LIST{} {}'.format(key, filename))
                   
    @Action()
    def abort(self):
        """Halts a sequence, list, sweep, or burst, even an infinite burst.
        Also causes trigger subsystem to return to idle state.
        If INIT:CONT is ON, instrument immediately
        proceeds to wait-for-trigger state.
        """
        self.write('ABORT')
               
    @DictFeat(keys=(1, 2))
    def freq_start(self, key):
        """sets start frequency for sweep
        """
        return self.query('SOURCE{}:FREQ:START?'.format(key))

    @freq_start.setter
    def freq_start(self, key, value):
        """sets start frequency for sweep
        """
        self.write('SOURCE{}:FREQ:START {}'.format(key, value))
                   
    @DictFeat(keys=(1, 2))
    def freq_stop(self, key):
        """sets stop frequency for sweep
        """
        return self.query('SOURCE{}:FREQ:STOP?'.format(key))

    @freq_stop.setter
    def freq_stop(self, key, value):
        """sets stop frequency for sweep
        """
        self.write('SOURCE{}:FREQ:STOP {}'.format(key, value))

    @DictFeat(keys=(1, 2))
    def trigger_source(self, key):
        """returns trigger source for sequence, list, burst, or sweep
        {IMMEDIATE|EXTERNAL|TIMER|BUS}, default IMMEDIATE
        """
        return self.query('TRIG{}:SOURCE?'.format(key))

    @trigger_source.setter
    def trigger_source(self, key, value):
        """Selects the trigger source for sequence, list, burst or sweep.
        The instrument accepts an immediate or timed internal trigger,
        an external hardware trigger from the rear-panel Ext Trig connector,
        or a software (bus) trigger
        """
        self.write('TRIG{}:SOURCE {}'.format(key, value))

    @DictFeat(keys=(1, 2))
    def force_trigger(self, key):
        """Forces immediate trigger to initiate sequence, sweep, list, or burst
        """
        self.query('TRIG{}'.format(key))

    @DictFeat(keys=(1, 2))
    def sweep_mode(self, key):
        """returns current sweep mode (LINEAR or LOGARITHMIC)
        """
        return self.query('SOURCE{}:SWEEP:SPAC?'.format(key))

    @sweep_mode.setter
    def sweep_mode(self, key, value):
        """sets sweep mode (LINEAR or LOGARITHMIC)
        """
        self.write('SOURCE{}:SWEEP:SPAC {}'.format(key, value))

    @DictFeat(keys=(1, 2))
    def sweep_time(self, key):
        """returns current set frequency sweep time
        """
        return self.query('SOURCE{}:SWEEP:TIME?'.format(key))

    @sweep_time.setter
    def sweep_time(self, key, value):
        """sets frequency sweep time
        """
        self.write('SOURCE{}:SWEEP:TIME {}'.format(key, value))

    @Feat()
    def get_error(self):
        """read and clear one error from error queue
        """
        return self.query('SYSTEM:ERROR?')

    @DictFeat(keys=CHANNELS)
    def sweep_state(self, key):
        return self.query('SOURCE{}:SWEEP:STATE?'.format(key))

    @sweep_state.setter
    def sweep_state(self, key, value):
        self.write('SOURCE{}:SWEEP:STATE {}'.format(key, value))

    @DictFeat(values=TOGGLE, keys=CHANNELS)
    def output(self, key):
        return self.query('OUTPUT{}?'.format(key))

    @output.setter
    def output(self, key, value):
        self.write('OUTPUT{} {}'.format(key, value))



if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')

    log_to_screen(DEBUG)
    # this is the USB VISA Address:
    with Keysight_36622A('USB0::0x0957::0x5707::MY53801461::0::INSTR') as inst:
        print('The identification of this instrument is :' + inst.idn)
        print(str(inst.read_standard_event_status_register))
        inst.output[1] = 'ON'
        inst.voltage[1] = 5.0 * volt
        inst.offset[1] = 0 * milivolt
        inst.frequency[1] = 50 * Hz
        inst.waveform[1] = 'SIN'
        #print('Current waveform: ' + inst.waveform[1])
        #print('Current voltage: ' + str(inst.voltage[1]))
        #print('Current frequency: ' + str(inst.frequency[1]))
        #print('Current offset: ' + str(inst.offset[1]))
        #print('ERROR: ' + inst.get_error)
        inst.operation_complete
        #inst.clear_status
        #inst.test
        print("BEGIN FREQUENCY SCAN")
        inst.freq_start[1] = 100
        inst.freq_stop[1] = 1000
        inst.sweep_mode[1] = 'LIN'
        inst.sweep_time[1] = 20
        inst.trigger_source[1] = 'BUS'
        inst.sweep_state[1] = 0