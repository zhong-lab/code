##Driver for SynthNV RF Generator
##@Shawn Liu 1.2023

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep


class SynthNV(MessageBasedDriver):
    """
    IMPORTANT NOTE:
    The query commands below work inside the driver file when running this file
    with spyre, but the same queries don't work if connecting it from a config
    file and using it in a spyrelet, even though same commands ie 'o?' is written
    to the instrument. In spyrelet it somehow thinks all the queries are asking
    for help and returns options of commands on RF output.

    For example:
    14:40:11 INFO     Getting frequency
    INFO:lantz.driver:Getting frequency
    14:40:11 DEBUG    Writing 'f?'
    DEBUG:lantz.driver:Writing 'f?'
    14:40:11 DEBUG    Read 'o) set RF On(1) or Off(0) 1\r\n'
    DEBUG:lantz.driver:Read 'o) set RF On(1) or Off(0) 1\r\n'
    14:40:11 DEBUG    (raw) Got o) set RF On(1) or Off(0) 1
     for frequency

    A workaround is to not include the instrument in config, but directly connect
    it in spyre.
    See test_synthnv_spyrelet.py

    Communication port number could change from time to time or if the device is
    unplugged and plugged in again. Under incorrect port number will get TMO time
    out error. To find the port number the computer assigns to it, either run
    python from terminal,

    import pyvisa
    rm = pyvisa.ResourceManager()
    rm.list_resources()
    # here unplug the device and run the above command again to identify the
    address of SynthNVP.
    quit()

    Could also go to device manager and do the plug and unplug to see port number.
    Then go to NIMax and find the address of with that port number.

    For synthNV make sure you can connect via the GUI first, then the COM port
    number should also show up in the maximized window of the GUI.

    NOTE:
    If device is connected via software GUI or pyvisa from python terminal, it is
    occupied and cannot be accessed via the spyrelet. Quit those processes first.

    -- Shawn
    """


    @Feat()
    def output(self):
        """returns if output is on or off
        """
        return self.query("o?")

    @output.setter
    def output(self, value):
        """sets output to on: 1, or off: 0
        """
        self.write("o{}".format(value))

    @Feat()
    def output_level(self):
        """returns whether rf output is high or low
        """
        return self.query("h?")

    @output_level.setter
    def output_level(self, value):
        """sets output to high: 1, or low: 0
        """
        self.write("h{}".format(value))

    @Feat(units='MHz', limits=(34, 4400.0, 1e-3))
    def frequency(self):
        """returns current frequency setting in kHz, not MHz
        """
        return self.query("f?")

    @frequency.setter
    def frequency(self, value):
        """sets frequency in range of 34 to 4400 MHz, in MHz
        """
        self.write("f{}".format(value))

    @Feat(limits=(0, 63, 1))
    def power(self):
        """return current power setting, in dBm
        Reading and setting the power are a little funky.
        Doesn't work as predicted.
        """
        return self.query("w?")

    @power.setter
    def power(self, value):
        """sets attenuation in dB 0 to 63.
        0 least rf power, correspond to attenuation at -31.5 dB.
        63 most rf power, correspond to attenuation at 0 dB.
        Each level up corresponds to 0.5 dB less attenuation.
        See attenuation in the GUI.
        """
        self.write("a{}".format(value))

    @Feat()
    def reference(self):
        """queries the internal reference setting
           0=external, 1=internal
        """
        return self.query("x?")

    @reference.setter
    def reference(self, value):
        self.write("x{}".format(value))



if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    import time
    log_to_screen(DEBUG)
    with SynthNV('ASRL11::INSTR') as inst:
        print(inst.output)
        inst.output = 0
        time.sleep(5)
        inst.output = 1
        freq = inst.frequency*1e-3  # in MHz
        print(freq)
        # print(inst.output_level)
        # print(inst.power)
        # inst.power = 0
        # time.sleep(1)
        # print(inst.power)
        # inst.power = 20
        # time.sleep(1)
        # print(inst.power)
        for i in range(10):
            inst.frequency = freq.magnitude - 2
            freq = inst.frequency*1e-3
            print(freq)
            sleep(1)
        # inst.frequency = 460
        # time.sleep(5)
        # inst.frequency = 470
        # time.sleep(5)
        # print(inst.frequency)
        # inst.output = 0

