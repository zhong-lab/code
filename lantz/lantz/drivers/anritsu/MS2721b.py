from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class MS2721B(MessageBasedDriver):
    """This is the driver for the Keysight 36622A."""

    """For VISA resource types that correspond to a complete 488.2 protocol
    (GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
    generally do not need to use termination characters, because the
    protocol implementation also has a native mechanism to specify the
    end of the of a message.
    """

    DEFAULTS = {'COMMON': {'write_termination': '\n', 'read_termination': '\n'}}

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    '''
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
        self.write('*CLS')
        print('Status cleared')


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
        Parameters:     (None)
        Related Commands *OPC? *WAI
        """
        self.write('*OPC')

    @Action()
    def operation_completed(self):
        return self.query('*OPC?')

    @Action()
    def trigger(self):
        """Trigger Command: Triggers a sweep, burst, arbitrary waveform advance,
        or LIST advance from the remote interface if the bus (software)
        trigger source is currently selected (TRIGger[1|2]:SOURce BUS)
        """
        self.write('*TRG')

    def self_test(self):
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
    '''

    @Feat(units='Hz')
    def freq_span(self):
        return self.query('FREQ:SPAN?')

    @freq_span.setter
    def freq_span(self, value):
        return self.write('FREQ:SPAN {}'.format(value))

    @Feat(units='Hz')
    def freq_cent(self):
        return self.query('FREQ:CENT?')

    @freq_cent.setter
    def freq_cent(self, value):
        return self.write('FREQ:CENT {}'.format(value))

    # @Feat(units='Hz')
    # def freq_cent(self):
    #     return self.query('FREQ:CENT?')

    # @freq_cent.setter
    # def freq_cent(self, value):
    #     return self.write('FREQ:CENT {}'.format(value))

    @Feat(units='Hz')
    def freq_star(self):
        return self.query('FREQ:STAR?')

    @freq_star.setter
    def freq_star(self, value):
        return self.write('FREQ:STAR {}'.format(value))

    @Action()
    def savefile(self,value):
        return self.write('MMEM:STOR:TRAC 0,"Filename_{}"'.format(value))
        # return self.write('MMEM:STOR:TRAC 0,"QvsBz_Rampdown_{}"'.format(value))

    # @Feat(units='W')
    # def ref_level(self):
    #     return self.query('DISP:WIND:TRAC:Y:RLEV?')

    # @ref_level.setter
    # def ref_level(self, value):
    #     return self.write('DISP:WIND:TRAC:Y:RLEV {}'.format(value))

    @Action()
    def acquireData(self):
        return self.query(':TRACe[:DATA]? 1')

    @Action()
    def format(self):
        self.write(':FORMat:DATA REAL,32')


if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    volt = Q_(1, 'V')
    milivolt = Q_(1, 'mV')
    Hz = Q_(1, 'Hz')

    log_to_screen(DEBUG)
    # this is the USB VISA Address:
    with MS2721B('USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR') as inst:
        print('The identification of this instrument is :' + inst.idn)
        # inst.format()
        # print(inst.acquireData())

