# -*- coding: utf-8 -*-
"""
    lantz.drivers.toptica.dlcpro.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implementation of Toptica DLC-pro laser controller

    Author: Alexandre Bourassa
    Date: 21/04/2017
"""
'''
TIPS: 
If not sure what input values to give, refer to the output the controller returns.
To query, use the same command with 'get' and no input.
To give an input, use 'set'. 

Want more commands than what is listed here? Go to the TOPAS software on the computer,
click on menu, communication. Then do the thing you want the command for in the software, 
and look at the command that shows up on the communication box!!! 
'''


import numpy as np
from lantz import Action, Feat, DictFeat, ureg
from lantz.messagebased import MessageBasedDriver
from toptica.lasersdk.client import NetworkConnection, Client

class DLC(MessageBasedDriver):

        DEFAULTS = {('TCPIP', 'SOCKET'):{'write_termination': '\n', 'read_termination': '\n'}}

        def initialize(self):
            super().initialize()
            # clear welcome message
            # for _ in range(5):
            #     self.resource.read_raw()
            # return

        def set_param(self, param_name, value):
            cmd = "(param-set! '{} {})".format(param_name, value)
            self.write(cmd)
            retval = self.read('\n','utf-8')
            retval = retval.lstrip('> ')
            if retval.startswith('Error: '):
                retval = retval.lstrip('Error: ')
                retparts = retval.split()
                errcode, errmsg = int(retparts[0]), ' '.join(retparts[1:])
                errcode = int(self.read())
                raise DLCException("Error {}: {}".format(errcode, errmsg))
            return retval

        def get_param(self, param_name):
            cmd = "(param-ref '{})".format(param_name)
            self.write(cmd)
            retval = self.read()
            retval = retval.lstrip('> ')
            if retval.startswith('Error: '):
                retval = retval.lstrip('Error: ')
                retparts = retval.split()
                errcode, errmsg = int(retparts[0]), ' '.join(retparts[1:])
                raise DLCException("Error {}: {}".format(errcode, errmsg))
            return retval

        @Feat()
        def idn(self):
            """
            Returns DLCpro
            """
            return self.get_param("system-type")


        ##------------------------
        ##    Current Control
        ##------------------------

        @Feat(values={True: '#t', False: '#f'})
        def output(self):
            return self.get_param('laser1:dl:cc:enabled')

        @output.setter
        def output(self, val):
            return self.set_param('laser1:dl:cc:enabled', val)

        @Feat(values={True: '#t', False: '#f'})
        def feedforward_enabled(self):
            return self.get_param('laser1:dl:cc:feedforward-enabled')

        @feedforward_enabled.setter
        def feedforward_enabled(self, val):
            return self.set_param('laser1:dl:cc:feedforward-enabled', val)

        @Feat(units='mA')
        def current(self):
            return self.get_param('laser1:dl:cc:current-set')

        @current.setter
        def current(self, val):
            return self.set_param('laser1:dl:cc:current-set', val)

        @Feat(units='mA')
        def current_offset(self):
            return self.get_param('laser1:dl:cc:current-offset')

        @current_offset.setter
        def current_offset(self, val):
            return self.set_param('laser1:dl:cc:current-offset', val)

        @Feat(units='mA')
        def current_actual(self):
            return self.get_param('laser1:dl:cc:current-act')

        @Feat(units='mA/V')
        def feedforward_factor(self):
            return self.get_param('laser1:dl:cc:feedforward-factor')

        @feedforward_factor.setter
        def feedforward_factor(self, val):
            return self.set_param('laser1:dl:cc:feedforward-factor', val)

        @Feat()
        def current_external_input_signal(self):
            return int(self.get_param('laser1:dl:cc:external-input:signal'))

        @current_external_input_signal.setter
        def current_external_input_signal(self, val):
            return self.set_param('laser1:dl:cc:external-input:signal', int(val))

        @Feat()
        def current_external_input_factor(self):
            return float(self.get_param('laser1:dl:cc:external-input:factor'))

        @current_external_input_factor.setter
        def current_external_input_factor(self, val):
            return self.set_param('laser1:dl:cc:external-input:factor', float(val))

        @Feat(values={True: '#t', False: '#f'})
        def current_external_input_enabled(self):
            return self.get_param('laser1:dl:cc:external-input:enabled')

        @current_external_input_enabled.setter
        def current_external_input_enabled(self, val):
            return self.set_param('laser1:dl:cc:external-input:enabled', val)


        ##------------------------
        ##    Piezo Control
        ##------------------------
        @Feat(units='V')
        def piezo_voltage_actual(self):
            return self.get_param('laser1:dl:pc:voltage-act')

        @Feat(values={True: '#t', False: '#f'})
        def piezo_enabled(self):
            return self.get_param('laser1:dl:pc:enabled')

        # give True or False, or, 1 or 0 for value.
        @piezo_enabled.setter
        def piezo_enabled(self, val):
            return self.set_param('laser1:dl:pc:enabled', val)

        @Feat(units='V')
        def piezo_vmax(self):
            return self.get_param('laser1:dl:pc:voltage-max')

        @Feat(units='V')
        def piezo_vmin(self):
            return self.get_param('laser1:dl:pc:voltage-min')

        @Feat(units='V')
        def piezo_voltage(self):
            return self.get_param('laser1:dl:pc:voltage-set')

        @piezo_voltage.setter
        def piezo_voltage(self, val):
            return self.set_param('laser1:dl:pc:voltage-set', val)

        @Feat()
        def piezo_external_input_signal(self):
            return int(self.get_param('laser1:dl:pc:external-input:signal'))

        @piezo_external_input_signal.setter
        def piezo_external_input_signal(self, val):
            return self.set_param('laser1:dl:pc:external-input:signal', int(val))

        @Feat()
        def piezo_external_input_factor(self):
            return float(self.get_param('laser1:dl:pc:external-input:factor'))

        @piezo_external_input_factor.setter
        def piezo_external_input_factor(self, val):
            return self.set_param('laser1:dl:pc:external-input:factor', float(val))

        @Feat(values={True: '#t', False: '#f'})
        def piezo_external_input_enabled(self):
            return self.get_param('laser1:dl:pc:external-input:enabled')

        @piezo_external_input_enabled.setter
        def piezo_external_input_enabled(self, val):
            return self.set_param('laser1:dl:pc:external-input:enabled', val)

        ##------------------------
        ##    Scan Control
        ##------------------------

        @Feat(values={True: '#t', False: '#f'})
        def scan_enabled(self):
            return self.get_param('laser1:scan:enabled')

        @scan_enabled.setter
        def scan_enabled(self, val):
            return self.set_param('laser1:scan:enabled', val)

        @Feat()
        def scan_channel(self):
            return int(self.get_param('laser1:scan:output-channel'))

        @scan_channel.setter
        def scan_channel(self, val):
            return self.set_param('laser1:scan:output-channel', int(val))

        @Feat()
        def scan_amplitude(self):
            return float(self.get_param('laser1:scan:amplitude'))

        @scan_amplitude.setter
        def scan_amplitude(self, val):
            return self.set_param('laser1:scan:amplitude', float(val))

        @Feat()
        def scan_offset(self):
            return float(self.get_param('laser1:scan:offset'))

        @scan_offset.setter
        def scan_offset(self, val):
            return self.set_param('laser1:scan:offset', float(val))

        @Feat(units='Hz')
        def scan_frequency(self):
            return self.get_param('laser1:scan:frequency')

        @scan_frequency.setter
        def scan_frequency(self, val):
            return self.set_param('laser1:scan:frequency', val)

        @Feat(values={'sine': 0, 'triangle': 1})
        def scan_signal_type(self):
            return int(self.get_param('laser1:scan:signal-type'))

        @scan_signal_type.setter
        def scan_signal_type(self, val):
            return self.set_param('laser1:scan:signal-type', val)


        ##Set Wavelength
        @Feat()
        def set_wavelength(self):
            return self.get_param('laser1:ctl:wavelength-set')

        @set_wavelength.setter
        def set_wavelength(self, val):
            return self.set_param('laser1:ctl:wavelength-set', val)

        # def set_wavelength(self, val):
        #     return self.set_param('laser1:ctl:wavelength-set', val)

        def set_output(self, val):
            return self.set_param('laser1:dl:cc:enabled', val)


        ##Power Stabilization
        @Feat(values={True: '#t', False: '#f'})
        def power_stabilization_enabled(self):
            return self.get_param('laser1:power-stabilization:enabled')

        # give True or False, or, 1 or 0 for value.
        @power_stabilization_enabled.setter
        def power_stabilization_enabled(self, val):
            return self.set_param('laser1:power-stabilization:enabled', val)

        @Feat()
        def power_setpoint(self):
            return self.get_param('laser1:power-stabilization:setpoint')
        # set power in mW
        @power_setpoint.setter
        def power_setpoint(self, val):
            return self.set_param('laser1:power-stabilization:setpoint', val)

class DLCException(Exception):
    pass

if __name__ == '__main__':
    import time
    conn1=NetworkConnection('1.1.1.1')
    with Client(conn1) as client:
        idn=client.get('serial-number',str)
        print(idn)

        wl=client.set('laser1:ctl:wavelength-set', 1535)
        print(wl)