import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle  # for saving large arrays
import math

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import datetime

from lantz.drivers.bristol import Bristol_771
# from lantz.drivers.burleigh import WA7600  # Wavelength meter
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
# from lantz.drivers.agilent import N5181A
from lantz.drivers.windfreak import SynthNVPro
# import nidaqmx
# from nidaqmx import AnalogInputTask

# from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.spectrum import MS2721B  # Anritsu spectrum analyzer
from lantz.drivers.stanford.srs900 import SRS900
# from lantz.drivers.attocube import ANC350

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz = Q_(1, 'kHz')
MHz = Q_(1.0, 'MHz')
dB = Q_(1, 'dB')
dBm = Q_(1, 'dB')
s = Q_(1, 's')


class PLThinFilm(Spyrelet):
    requires = {
        'wm': Bristol_771,
        'fungen': Keysight_33622A,
        'analyzer': MS2721B
    }

    qutag = None
    laser = NetworkConnection('1.1.1.2')

    def configureQutag(self):
        qutagparams = self.qutag_params.widget.get()
        start = qutagparams['Start Channel']
        stop = qutagparams['Stop Channel']
        ##True = rising edge, False = falling edge. Final value is threshold voltage
        self.qutag.setSignalConditioning(start, self.qutag.SIGNALCOND_MISC, True, 1)
        self.qutag.setSignalConditioning(stop, self.qutag.SIGNALCOND_MISC, True, 0.1)
        self.qutag.enableChannels((start, stop))

    def homelaser(self, target, measure_time=15, motor_scan_precision=0.0003, precision=0.00004, drift_time=4*s):
        """
        Motor scan of the Toptica CTL is suitable for large range wavelength adjustments.
        Using motor scan to move wavelength up to plus minus 0.0003nm, beyond this a bit hard, corrections may overshoot
        the wavelength target.
        So we adjust piezo voltage to fine tune wavelength beyond this point.
        In the neighborhood of 70V, 1V increase in piezo voltage changes wavelength by -0.001338nm.
        """
        with Client(self.laser) as client:
            client.set('laser1:dl:pc:enabled', True)
            piezo = client.get('laser1:dl:pc:voltage-set')
            print('Piezo is at', piezo, 'V.')
            if abs(piezo-70) > 2:
                client.set('laser1:dl:pc:voltage-set', 70)
                print('Piezo Voltage changed to 70V.')
                time.sleep(5)
        wls = []
        for i in range(measure_time):
            wl = self.wm.measure_wavelength()
            wls.append(wl)
            time.sleep(1)
        avg = np.mean(wls)
        print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)

        motor_scan = False
        if abs(avg - target) > motor_scan_precision:
            motor_scan = True
            with Client(self.laser) as client:
                piezo = client.get('laser1:dl:pc:voltage-set')
                if piezo != 70:
                    client.set('laser1:dl:pc:voltage-set', 70)
                    print('Piezo Voltage changed to 70V.')
                    time.sleep(5)
            current = self.wm.measure_wavelength()
            iter = 0
            with Client(self.laser) as client:
                while current < target - motor_scan_precision or current > target + motor_scan_precision:
                    # print('here1')
                    iter = iter+1
                    if iter > 6:
                        print('Max iteration exceeded.')
                        break
                    setting = client.get('laser1:ctl:wavelength-set', float)
                    offset = current - target
                    client.set('laser1:ctl:wavelength-set', setting - offset)  # this uses motor scan.
                    time.sleep(drift_time.magnitude)
                    current = self.wm.measure_wavelength()
                    print(str(iter)+" current: {} target: {} new wl setting: {} diff: {}".format(current, target, round(setting - offset,6), round(current-target,6)))
            if iter <= 6:
                print("Laser homed to within", motor_scan_precision, 'nm with motor scan.')
            else:
                print("Laser NOT homed to within", motor_scan_precision, 'nm with motor scan.')
        if motor_scan:
            print('Piezo scan to fine tune wavelength.')
            wls = []
            for i in range(measure_time):
                wl = self.wm.measure_wavelength()
                wls.append(wl)
                time.sleep(1)
            avg = np.mean(wls)
            print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)
        with Client(self.laser) as client:
            while avg < target - precision or avg > target + precision:
                piezo_adjust = round((avg-target)/0.001338, 3)
                piezo = client.get('laser1:dl:pc:voltage-set')
                new_piezo = piezo+piezo_adjust
                client.set('laser1:dl:pc:voltage-set', new_piezo)
                print('New piezo voltage:', new_piezo, 'V.')
                time.sleep(5)
                wls = []
                for i in range(measure_time):
                    wl = self.wm.measure_wavelength()
                    wls.append(wl)
                    time.sleep(1)
                avg = np.mean(wls)
                print('Average Wavelength:', avg, 'target:', target, 'diff:', avg-target)
        return avg

    @Task()
    def qutagInit(self):

        from lantz.drivers.qutools import QuTAG
        self.qutag = QuTAG()
        devType = self.qutag.getDeviceType()
        print('devType: ' + str(devType))
        if (devType == self.qutag.DEVTYPE_QUTAG):
            print("found quTAG!")
        else:
            print("no suitable device found - demo mode activated")
        print("Device timebase:" + str(self.qutag.getTimebase()))

        print('qutag successfully initialized')

    @Task()
    def startpulse(self, timestep=100e-9):
        # log_to_screen(DEBUG)

        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'
        # # some initialization of the function generator
        self.fungen.clear_mem(1)
        self.fungen.clear_mem(2)
        self.fungen.wait()

        # self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
        # time.sleep(3)  ##wait 1s to turn on the SNSPD
        qutagparams = self.qutag_params.widget.get()

        vm1 = qutagparams['Voltmeter Channel 1']
        vm2 = qutagparams['Voltmeter Channel 2']
        vs1 = qutagparams['Battery Port 1']
        vs2 = qutagparams['Battery Port 2']

        time.sleep(1)  # Wait 1s to turn on SNSPD

        ##Qutag Part
        self.configureQutag()  # need to first run the qutagInit task before configuring qutag.

        expparams = self.exp_parameters.widget.get()
        wlparams = self.wl_parameters.widget.get()

        # Don't home the laser if the laser is locked to the reference
        # self.homelaser(wlparams['start'], precision=wlparams['precision(nm): ±'], drift_time=wlparams['drift_time'])
        # print('Laser Homed to the start wavelength!')

        lost = self.qutag.getLastTimestamps(True)  # clear Timestamp buffer

        bincount = qutagparams['Bin Count']
        timebase = self.qutag.getTimebase()
        start_channel = qutagparams['Start Channel']
        stop_channel = qutagparams['Stop Channel']

        pulse_channel = expparams['Excitation Pulse channel']
        Pulsefreq = expparams['Excitation Pulse Frequency']  # signal to TTL switch to repeat laser start pulse
        # For excitation pulse duration scan
        Pulse_width_start = expparams['Excitation Pulse Width Scan Start']
        Pulse_width_end = expparams['Excitation Pulse Width Scan End']
        num_widths = expparams['# of scanned pulse widths']
        EOM_vpp_start = expparams['EOM Driving Vpp Scan Start']
        EOM_vpp_end = expparams['EOM Driving Vpp Scan End']
        EOM_vpp_step = expparams['Driving Voltage step']

        runtime = expparams['Measurement Time'].magnitude
        num_AOMs = expparams['# of AOMs']
        WindfreakFreq = expparams['Windfreak frequency'].magnitude  # rf freq to AOMs
        rf_power = expparams['RF source power']

        wl_points = expparams['# of wl points']
        path_name = expparams['File Name']
        c = 299792458  # speed of light, unit: m/s

        period = float(1 / Pulsefreq.magnitude)  # period of repeating laser pulse in sec

        # Signal to TTL switch, carrier to RF signal.
        self.fungen.frequency[pulse_channel] = Pulsefreq
        '''
        If signal voltage is HIGH, TTL is ON, then RF is sent to fiber AOM's in low insertion loss mode,
        we have excitation laser pulse.
        Frequency of this signal controls the frequency of turning on excitation pulses.
        Length of signal crossing TTL ON threshold determines length of pulse.
        If signal voltage is LOW, TTL is OFF, or isolation state, RF signal does not go through. No laser pulse.
        '''
        self.fungen.voltage[pulse_channel] = 3.5 * volt  # If don't specify unit fine will just give warning saying it assumed the unit is in Volts.
        self.fungen.offset[pulse_channel] = 1.75 * volt
        self.fungen.phase[pulse_channel] = 0

        # self.fungen.pulse_width[pulse_channel] = Pulsewidth

        self.fungen.waveform[pulse_channel] = 'PULS'
        self.analyzer.freq_span = 0
        # self.fungen.output[pulse_channel] = 'ON'

        curr = datetime.datetime.now()
        PATH = path_name + '_' + curr.strftime("%Y-%m-%d_%H-%M-%S")
        os.mkdir(PATH)
        print('npz file stored under PATH: ' + str(PATH))

        ## generate the wavelength points for the scan
        wlTargets = np.linspace(wlparams['start'], wlparams['stop'], expparams['# of wl points'])
        # wlTargets = [1535.6077268493461, 1536.259558963267, 1537.900105692305]
        # wlTargets = [1535.6077268493461, 1536.259558963267]
        # wlTargets = [1535.4970327, 1535.55321671, 1535.60940073, 1535.66558474, 1535.72176875]

        # wlTargets = [1529.4706817857023, 1529.4234814967422]
        # wlTargets = [1529.4710419899582, 1529.4247871869354]

        widthTargets = np.linspace(Pulse_width_start.magnitude, Pulse_width_end.magnitude, num_widths)
        # widthTargets = [2000e-6, 1500e-6, 1000e-6, 700e-6, 500e-6, 200e-6, 100e-6, 10e-6]  # unit: sec
        # widthTargets = [100e-6, 300e-6, 500e-6, 700e-6, 1000e-6, 1500e-6, 7000e-6]
        # widthTargets = [200e-9, 500e-9, 700e-9, 1e-6] + list(np.linspace(10e-6, 90e-6, 9)) + list(np.linspace(100e-6, 500e-6, 41))
        # widthTargets = list(np.linspace(100e-9, 900e-9, 5)) + list(np.linspace(1e-6, 9e-6, 9)) + \
                       # list(np.linspace(10e-6, 90e-6, 9))

        # widthTargets = list(np.linspace(3000e-6, 10000e-6, 1))
        widthTargets = [300e-6]

        laser_power = [55]  # mW of laser power at the DLC controller
        # laser_power = [20]

        # Phase EOM driving
        driving_voltages = np.arange(EOM_vpp_start, EOM_vpp_end+EOM_vpp_step, EOM_vpp_step)
        # rf_freqs = [1e3, 10e3, 100e3, 1e6, 10e6]
        rf_freqs = [100, 300, 500, 1e3, 10e3, 30e3, 50e3, 70e3, 100e3, 500e3, 1e6, 30e6, 100e6, 200e3]
        # rf_freqs = [30e3, 70e3]
        # rf_freqs = [100,500,900, 1e3,5e3,9e3, 1e4,3e4,5e4, 1e5,3e5,5e5, 1e6,3e6,5e6, 1e7,3e7,5e7]

        len_wlTargets = len(wlTargets)
        len_widthTargets = len(widthTargets)
        len_laserpower = len(laser_power)
        len_voltage = len(driving_voltages)
        len_rf = len(rf_freqs)


        for l, power in enumerate(laser_power):
            # with Client(self.laser) as client:
            #     client.set('laser1:power-stabilization:setpoint', power)
            #     power_now = client.get('laser1:power-stabilization:setpoint')
            #     print(l, power_now)
            # if num_AOMs == 2:
            #     pulse_power = power*4.2  # in µW, approximately, after losses in the setup.
            # elif num_AOMs == 3:
            #     pulse_power = power*0.9  # in µW
            for j, width in enumerate(widthTargets):
                self.fungen.pulse_width[pulse_channel] = width * s
                for k, driving_voltage in enumerate(driving_voltages):
                    for m, rf_freq in enumerate(rf_freqs):
                        self.fungen.frequency[pulse_channel] = Pulsefreq
                        self.fungen.voltage[pulse_channel] = 3.5 * volt
                        self.fungen.offset[pulse_channel] = 1.75 * volt
                        self.fungen.phase[pulse_channel] = 0

                        self.analyzer.freq_cent = rf_freq
                        self.analyzer.generator_power = -1.1

                        for i, wlTarget in enumerate(wlTargets):

                            wl, iter = self.homelaser(wlTarget, precision=wlparams['precision(nm): ±'], drift_time=wlparams['drift_time'])  # home laser to new wl with more precision the first time
                            print('Laser set to:' + str(wlTarget))
                            print('current wavelength: ' + str(wl))

                            # self.fungen.output[pulse_channel] = 'ON'
                            # time.sleep(0.2)
                            print('Start taking data...')
                            # print('current target wavelength: '+str(wlTarget))
                            # print('actual wavelength in the beginning of the measurement: '+str(self.wm.measure_wavelength()))

                            # Wavemeter measurements
                            stoparray = []
                            startTime = time.time()
                            wls = []
                            saveextfreqs = []
                            # saveRFpower = []
                            lost = self.qutag.getLastTimestamps(True)

                            self.hist = [0] * bincount
                            self.bins = list(timevec * period * 1000 / bincount for timevec in range(bincount))  ## unit: ms
                            # time in ms of each bin

                            stopscheck = []

                            self.fungen.output[pulse_channel] = 'ON'
                            self.fungen.output[rf_channel] = 'ON'

                            loopTime = startTime
                            while loopTime - startTime < runtime:
                                # correct laser frequency before every 2 sec measurement window
                                # self.homelaser(wlTarget, precision=0.0003)  # unit: nm)

                                # self.fungen.output[pulse_channel] = 'ON'
                                # time.sleep(0.2)
                                # dataloss1 = self.qutag.getDataLost()
                                # # #print("dataloss: " + str(dataloss1))
                                # #
                                # dataloss2 = self.qutag.getDataLost()
                                # # #print("dataloss: " + str(dataloss2))

                                print("Time left: "+str(runtime - (loopTime-startTime)))
                                # get the timestamps
                                timestamps = self.qutag.getLastTimestamps(True)

                                loopStart = time.time()

                                time.sleep(0.5)

                                dataloss1 = self.qutag.getDataLost()
                                # print("dataloss: " + str(dataloss))

                                dataloss2 = self.qutag.getDataLost()
                                # print("dataloss: " + str(dataloss))

                                # get the timestamps
                                timestamps = self.qutag.getLastTimestamps(True)

                                loopTime += time.time() - loopStart

                                if dataloss1 != 0:
                                    print('dataloss: ' + str(dataloss1))

                                # turn off AWG signal after each round of measurement to prevent saturating SNSPD with photons from start pulses.
                                # self.fungen.output[pulse_channel] = 'OFF'
                                # time.sleep(0.2)

                                tstamp = timestamps[0]  # array of timestamps  (time diff between stop event and the start event, contain internal timer tick)
                                tchannel = timestamps[1]  # array of channels  (channel number (1 to 4) where stop event occurred, also channel 104, timer tick channel).
                                values = timestamps[2]  # number of recorded timestamps

                                print('Values = ' + str(values))

                                for val in range(values):
                                    # output all stop events together with the latest start event
                                    if tchannel[val] == stop_channel:
                                        # has photons from start pulse and the emitted photons from electron decay into ground state
                                        stoptimestamp = tstamp[val]
                                        stopscheck.append(stoptimestamp)

                                print('Elements in stopscheck... (first 10) total: ' + str(len(stopscheck)))
                                print(stopscheck[0:10])

                                wl = self.wm.measure_wavelength()  # unit: nm
                                print("Laser Power: {} mW; Pulse Width: {} s; Target Wl: {}; Laser Wl: {}; "
                                      "Driving Voltage: {} Vpp; rf freq: {} Hz"
                                      .format(power, width, wlTarget, wl, driving_voltage, rf_freq))
                                print("Laser Power ({}/{}), Pulse Width ({}/{}), Driving Voltage ({}/{}), rf freq ({}/{}), "
                                      "Wavelength ({}/{})"
                                      .format((l+1), len_laserpower, (j+1), len_widthTargets, (k+1), len_voltage, (m+1), len_rf,
                                              (i+1), len_wlTargets))
                                wls.append(float(wl))  # unit: nm
                                saveextfreqs.append(c / wl + num_AOMs * WindfreakFreq / 1e3)  # GHz

                                for stop in range(len(stopscheck)):
                                    # print('In stopscheck: '+str(k))
                                    tdiff = stopscheck[stop]
                                    binNumber = int(tdiff * timebase * bincount / (period))
                                    if binNumber < bincount:
                                        self.hist[binNumber] += 1
                                stopscheck = []

                                values = {
                                    'x': self.bins,
                                    'y': self.hist,
                                }

                                print('self.startpulse.acquire(values) ....')
                                self.startpulse.acquire(values)  # for histogram plotting in GUI

                            avewls = np.mean(wls)  ## to get the averaged wavelength
                            print('Laser frequency during the measurement: ' + str(c / avewls))

                            self.fungen.output[pulse_channel] = 'OFF'
                            self.fungen.output[pulse_channel] = 'ON'
                            np.savez(os.path.join(PATH, str(j)+str(k)+str(m) + "_" + str(avewls) + "_" +
                                                  str(power) + 'mW_' + str(width) + 's_' + str(driving_voltage) + 'Vpp'
                                                  + str(rf_freq) + 'Hz_'+str(runtime) + 's'),
                                     hist=self.hist, bins=self.bins, freq=saveextfreqs, laser_wls=wls,
                                     laser_power=power, pulse_length=width, driving_voltage=driving_voltage,
                                     rf_freq=rf_freq, exc_pulse_freq=Pulsefreq.magnitude, measurement_time=runtime)
                            print('Tallest bin:', max(self.hist), '\n')
                            time.sleep(15)

        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'


    # the 1D plot widget is used for the live histogram
    @Element(name='startpulse Histogram')
    def startpulse_Histogram(self):
        p = LinePlotWidget()
        p.plot('startpulse Histogram')
        return p

    # more code for the histogram plot
    @startpulse_Histogram.on(startpulse.acquired)
    def _startpulse_Histogram_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        # xs = np.array(self.bins)[self.cutoff:]
        # ys = np.array(self.hist)[self.cutoff:]
        xs = np.array(self.bins)
        ys = np.array(self.hist)
        w.set('startpulse Histogram', xs=xs, ys=ys)
        return

    @Element(name='Wavelength parameters')
    def wl_parameters(self):
        params = [
            #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
            # ('start', {'type': float, 'default': 1535.665}),
            ('start', {'type': float, 'default': 1529.420}),
            ('stop', {'type': float, 'default': 1536}),
            ('precision(nm): ±', {'type': float, 'default': 0.0004}),
            ('drift_time', {'type': float, 'default': 5, 'units': 's'}),
            # ('stop', {'type': float, 'default': 1535.61})
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Experiment Parameters')
    def exp_parameters(self):
        params = [
            ('Windfreak frequency', {'type': float, 'default': 200, 'units': 'MHz'}),
            ('RF source power', {'type': float, 'default': 14.5}),  ## unit: dBm, the RF source power
            ('# of wl points', {'type': int, 'default': 1}),
            ('# of AOMs', {'type': int, 'default': 2}),
            ('Measurement Time', {'type': int, 'default': 30, 'units': 's'}),
            ('Lasermeasuretime', {'type': float, 'default': 10, 'units': 's'}),
            ('Excitation Pulse channel', {'type': int, 'default': 1}),  # the AWG channel to generate the laser pulses
            ('Phase EOM rf channel', {'type': int, 'default': 2}),  # the AWG channel to generate rf signal for EOM
            ('Excitation Pulse Frequency', {'type': int, 'default': 10, 'units': 'Hz'}),
            ('Excitation Pulse Width Scan Start', {'type': float, 'default': 1e-6, 'units': 's'}),
            ('Excitation Pulse Width Scan End', {'type': float, 'default': 5e-6, 'units': 's'}),
            ('# of scanned pulse widths', {'type': int, 'default': 1}),
            ('EOM Driving Vpp Scan Start', {'type': float, 'default': 6}),
            ('EOM Driving Vpp Scan End', {'type': float, 'default': 6}),
            ('Driving Voltage step', {'type': float, 'default': 0.5}),
            ('File Name', {'type': str, 'default': "E:\\Data\\8.3.2022_ErLYF_transient_holeburning\\test"}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='QuTAG Parameters')
    def qutag_params(self):
        params = [
            ('Start Channel', {'type': int, 'default': 0}),
            ('Stop Channel', {'type': int, 'default': 2}),
            ('Bin Count', {'type': int, 'default': 1000}),
            ('Voltmeter Channel 1', {'type': int, 'default': 1}),
            ('Voltmeter Channel 2', {'type': int, 'default': 2}),
            ('Battery Port 1', {'type': int, 'default': 5}),
            ('Battery Port 2', {'type': int, 'default': 6})
        ]
        w = ParamWidget(params)
        return w

    @startpulse.initializer
    def initialize(self):
        self.wm.start_data()
        return

    @startpulse.finalizer
    def finalize(self):
        self.fungen.output[1] = 'OFF'  ##turn off the AWG for both channels
        self.fungen.output[2] = 'OFF'
        self.wm.stop_data()
        print('Lifetime measurements complete.')
        return

    @qutagInit.initializer
    def initialize(self):
        return

    @qutagInit.finalizer
    def finalize(self):
        return
