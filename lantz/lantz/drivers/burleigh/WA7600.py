# Author: Shawn Liu
# 06/2022
from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

"""
Check VISA Resource Name of the wavemeter and update the config file accordingly
before each use.

Wavemeter connects via GPIB. The VISA Resource Name may change depending on how
many GPIB devices are connected. (?)
Name of the instrument can be found in the NI MAX application, or with
pyvisa's ResourceManager() and query("*IDN?") to verify.

i.e.
>>> import pyvisa
>>> rm = pyvisa.ResourceManager()
>>> print(rm.list_resources())
('USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR', 'TCPIP0::A-33622A-01461.local::inst0::INSTR', 'ASRL1::INSTR', 'ASRL3::INSTR', 'ASRL7::INSTR', 'GPIB1::10::INSTR')
>>> instrument = rm.open_resource('GPIB1::10::INSTR')
>>> instrument.query("*IDN?")
'BURLEIGH WAVEMETERS, WA-7600, 15415, 02.27.00, 02.00.00\n'
>>> instrument.query("meas:scal?")
'1529.1581\n'
>>> instrument.query("MEAS:SCAL?")
'1529.1581\n'

SCPI commands are case insensitive.

For way more SCPI commands and options than what's listed below, see
https://www.artisantg.com/info/Burleigh_WA7600_WA7100_Operating_Manual.pdf
starting on page 4-3: SCPI Command Summary.
"""

class WA7600(MessageBasedDriver):
    """Burleigh WA-7600 Wavemeter
    """
    DEFAULTS = {'COMMON': {'write_termination': '\n',
                           'read_termination': '\n'}}

    @Feat()
    def idn(self):
        """Identification.
        """
        return self.query("*IDN?")

    @Feat()
    def meas_total_power(self):
        """Returns the total power of the last scan. Default: (dBm)
        """
        return float(self.query(":MEAS:TPOW?"))

    @Feat()
    def meas_wavelength(self):
        """Measures current wavelength value for a single channel. Default: (nm)
        """
        return float(self.query(":MEAS:SCAL:WAV?"))

    @Feat()
    def fetc_wavelength(self):
        """Fetches last wavelength measurement. Default: (nm)
        """
        return float(self.query(":FETC:SCAL:WAV?"))

    @Feat()
    def meas_power(self):
        """Queries max power measured during the last scan. Default: (dBm)
        """
        return float(self.query(":MEAS:SCAL:POW?"))

    @Feat()
    def meas_WPO(self):
        """Measures current wavelength, power, and optical signal to noise
        radio. Returns a string ie. '1529.1883,-16.99,4.048687E+01\n'
        """
        return self.query(":MEAS:SCAL:WPO?")

    @Feat()
    def meas_FWHM(self):
        """Measures current full width, half max of the optical spectrum.
        """
        return float(self.query(":MEAS:SCAL:FWHM?"))

    @Feat()
    def meas_freq(self):
        """Returns a single channel's frequency measured during the last scan.
        Unit is always in THz.
        """
        return float(self.query(":MEAS:SCAL:FREQ?"))

    @Feat()
    def meas_multi_chan_wavelength(self):
        """Returns an array of wavelength readings for each channel that was
        captured during the last scan. The array is preceed by the number of \
        channels in the array, ie. '1,1529.1881\n' if num of channel = 1.
        """
        return self.query(":MEAS:ARR:WAV?")

    @Feat()
    def fetc_multi_chan_wavelength(self):
        return self.query(":FETC:ARR:WAV?")

    @Feat()
    def meas_multi_chan_power(self):
        return self.query(":MEAS:ARR:POW?")

    @Feat()
    def meas_multi_chan_WPO(self):
        return self.query(":MEAS:ARR:WPO?")

    @Feat()
    def meas_multi_chan_FWHM(self):
        return float(self.query(":MEAS:SCAL:FWHM?"))

    @Feat()
    def time(self):
        """Queries the elapsed time during which the CALC3 subsystem has been in
        either the STAR or PAUS state.
        """
        return float(self.query(":CALC3:TIME?"))


if __name__ == '__main__':
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    nm = Q_(1, 'nm')
    THz = Q_(1, 'THz')
    dB = Q_(1,'dB')
    dBm = Q_(1,'dB')

    log_to_screen(DEBUG)
    # this is the VISA Resource Name:
    with WA7600('GPIB1::10::INSTR') as inst:
        print('The identification of this instrument is : ' + inst.idn)
        print('Current wavelength is ' + str(inst.meas_wavelength))
