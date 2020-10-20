# -*- coding: utf-8 -*-
"""
    lantz.drivers.bristol.bristol771.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implementation of Bristol 771A-NIR Laser Spectrometer
    Author: Peter Bevington
    Date: 8/10/2018
"""
##Note: After starting start_data(), time.sleep at least 5 seconds to let
##wavemeter get at least one wavelength, or else it will throw an error.
from lantz.foreign import LibraryDriver
from lantz import Feat, DictFeat, Action, Q_

import time
from ctypes import *

class tsDeviceIPInfo(Structure):
    __fields__ = [('u_ipaddr', c_uint), 
        ('s_ipaddr', c_wchar_p), 
        ('port', c_uint), 
        ('snum', c_uint), 
        ('model', c_wchar_p)]

class tsDataMeas(Structure):
    __fields__ = [('wlen', c_double), 
        ('scan_index', c_uint32),
        ('stat', c_uint32),
        ('ipwr', c_float),
        ('pres', c_float),
        ('temp', c_float),
        ('ref_gain_dac', c_float),
        ('imp_gain_dac', c_float),
        ('ref_gain_bits', c_uint16),
        ('imp_gain_bits', c_uint16),
        ('lrdelta', c_double)]

class Bristol_771(LibraryDriver):

    LIBRARY_NAME = 'libbristol.dll'
    LIBRARY_PREFIX = 'CL'

    def __init__(self, serialnum):
        super().__init__()

        create_inst = self.lib.CreateInstance
        create_inst.restype = c_void_p
        handle = create_inst()

        snum = c_uint(serialnum)
        model = create_string_buffer(20)
        maxlen = c_int(20)

        err = self.lib.OpenDevice(handle, snum, model, maxlen)
        if err != 0:
            raise Exception('Instrument not loaded')
        else:
            print('Instrument loaded: ' + str(model.value).strip('b'))

        self.device = handle

        #Function definitions
        #CL FUNCTIONS
        self.lib.GetMeasWLen.argtypes = [c_void_p, POINTER(c_double)]
        self.lib.GetMeasIPwr.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.GetMeasPres.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.GetMeasTemp.argtypes = [c_void_p, POINTER(c_float)]
        self.lib.GetMeas.argtypes = [c_void_p, POINTER(tsDataMeas)]

        self.lib.GetRawData.argtypes = [c_void_p, POINTER(c_int),c_int]

        self.lib.StartRawData.argtypes = [c_void_p, c_int]
        self.lib.StopRawData.argtypes = [c_void_p]
        self.lib.StartSpectrumData.argtypes = [c_void_p, c_int, c_int, c_int]
        self.lib.StopSpectrumData.argtypes = [c_void_p]

        """

        #LV FUNCTIONS
        self.lib.SpecData_GetGlob.argtypes = [c_void_p, c_int]
        self.lib.RawData_GetGlob.argtypes = [c_void_p, c_int]
        self.lib.SpecData_WaveLength.argtypes = [c_void_p]
        self.lib.SpecData_InputPower.argtypes = [c_void_p]
        self.lib.SpecData_Pressure.argtypes = [c_void_p]
        self.lib.SpecData_Temperature.argtypes = [c_void_p]
        return
        """


    def check_error(self, ret):
        if ret != 0:
            raise Exception('Measurement failed')
        return

    def start_data(self, count=0):
        return self.lib.StartRawData(self.device, c_int(count))

    def stop_data(self):
        return self.lib.StopRawData(self.device)


    """
    #LV FUNCTIONS
    def get_data(self):
        getglob = self.lib.SpecData_GetGlob
        getglob.restype = c_void_p
        return getglob(self.device, c_int(10000))

    def measure_wavelength(self):
        data = self.get_data()
        wavelength = self.lib.SpecData_WaveLength
        wavelength.restype = c_double
        ret_val = wavelength(data)
        return ret_val

    def measure_power(self):
        data = self.get_data()
        power = self.lib.SpecData_InputPower
        power.restype = c_double
        ret_val = power(data)
        return ret_val

    def measure_pressure(self):
        data = self.get_data()
        pres = self.lib.SpecData_Pressure
        pres.restype = c_double
        ret_val = pres(data)
        return ret_val

    def measure_temperature(self):
        data = self.get_data()
        temp = self.lib.SpecData_Temperature
        temp.restype = c_double
        ret_val = temp(data)
        return ret_val

    """
    #CL FUNCTIONS
    def measure_wavelength(self):
        ret_val = c_double()
        self.check_error(self.lib.GetMeasWLen(self.device, pointer(ret_val)))
        return ret_val.value

    def measure_power(self):
        ret_val = c_float()
        self.check_error(self.lib.GetMeasIPwr(self.device, pointer(ret_val)))
        return ret_val.value

    def measure_pressure(self):
        ret_val = c_float()
        self.check_error(self.lib.GetMeasPres(self.device, pointer(ret_val)))
        return ret_val.value

    def measure_temperature(self):
        ret_val = c_float()
        self.check_error(self.lib.GetMeasTemp(self.device, pointer(ret_val)))
        return ret_val.value

    def get_data(self):
        data = tsDataMeas()
        self.check_error(self.lib.GetMeas(self.device, pointer(data)))
        return data

    def get_status(self):
        data = self.get_data()
        status = data.stat
        return status

    def get_rawData(self, buf, size):
        ret_val=c_int()
        self.lib.GetRawData(self.device, pointer(ret_val),c_int(size) )
        return ret_val.value

if __name__ == '__main__':
    from time import sleep
    from lantz import Q_
    from lantz.log import log_to_screen, DEBUG

    log_to_screen(DEBUG)

    inst = Bristol_771(6535)
    print(inst.start_data())
    time.sleep(3)
    print(inst.get_rawData(10,10))
    #inst.measure_temperature()
    #inst.measure_pressure()
    #inst.measure_power()
    inst.stop_data()




