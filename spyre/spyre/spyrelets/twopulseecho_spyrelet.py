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
from scipy.constants import c

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.bristol import Bristol_771
from lantz.drivers.stanford.srs900 import SRS900
from toptica.lasersdk.client import NetworkConnection, Client  # import the toptica laser
# from lantz.drivers.agilent import N5181A

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz = Q_(1, 'kHz')
MHz = Q_(1.0, 'MHz')
dB = Q_(1, 'dB')
dBm = Q_(1, 'dB')
s = Q_(1, 's')


class TwoPulsePhotonEcho(Spyrelet):
    requires = {
        'wm': Bristol_771,
        'fungen': Keysight_33622A
    }
    qutag = None
    laser = NetworkConnection('1.1.1.2')

    xs = np.array([])
    ys = np.array([])
    hist = []

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

        print('Laser Homed.')
        return avg

    def configureQutag(self):
        qutagparams = self.qutag_params.widget.get()
        start = qutagparams['Start Channel']
        stop = qutagparams['Stop Channel']
        ##True = rising edge, False = falling edge. Final value is threshold voltage
        self.qutag.setSignalConditioning(start, self.qutag.SIGNALCOND_MISC, True, 1)
        self.qutag.setSignalConditioning(stop, self.qutag.SIGNALCOND_MISC, True, 0.1)
        self.qutag.enableChannels((start, stop))


    def createHistogram(self, stoparray, timebase, bincount, totalWidth, index, wls, out_name, extra_data=False):
        print('creating histogram')

        hist = [0] * bincount

        tstart = 0
        for k in range(len(stoparray)):
            tdiff = stoparray[k]

            binNumber = int(tdiff * timebase * bincount / (totalWidth))
            """
            print('tdiff: '+str(tdiff))
            print('binNumber: '+str(binNumber))
            print('stoparray[k]: '+str(stoparray[k]))
            print('tstart: '+str(tstart))
            """
            if binNumber >= bincount:
                continue
            else:
                # print('binNumber: '+str(binNumber))
                hist[binNumber] += 1

        if extra_data == False:
            np.savez(os.path.join(out_name, str(index)), hist, wls)
        if extra_data != False:
            np.savez(os.path.join(out_name, str(index)), hist, wls, extra_data)

        # np.savez(os.path.join(out_name,str(index+40)),hist,wls)
        print('Data stored under File Name: ' + out_name + '\\' + str(index) + '.npz')

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
    def twopulseecho(self, timestep=1e-9):
        params = self.twopulse_parameters.widget.get()
        wlparams = self.wl_parameters.widget.get()

        starttau = params['start tau']
        stoptau = params['stop tau']
        points = params['# of points']
        period = params['period'].magnitude
        repeat_unit = params['repeat unit'].magnitude
        half_pi_pulse_width = params['pi/2 pulse width'].magnitude
        pi_pulse_width = params['pi pulse width'].magnitude
        buffer_time = params['buffer time'].magnitude
        shutter_offset = params['shutter offset'].magnitude
        wholeRange = params['measuring range'].magnitude
        Pulsechannel = params['Pulse channel']
        Shutterchannel = params['Shutter channel']

        foldername = params['File Name']
        runtime = params['Runtime'].magnitude

        wlTarget = wlparams['wavelength (nm)']
        precision = wlparams['precision(nm): ±']
        drift_time = wlparams['drift_time']
        num_AOMs = wlparams['# of AOMs']
        WindfreakFreq = wlparams['Windfreak frequency'].magnitude  # rf freq to AOMs

        curr = datetime.datetime.now()
        PATH = foldername + '_' + curr.strftime("%Y-%m-%d_%H-%M-%S")
        os.mkdir(PATH)
        print('npz file stored under PATH: ' + str(PATH))

        ## turn off the AWG before the measurement
        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'

        # self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
        # time.sleep(3)  ##wait 1s to turn on the SNSPD

        qutagparams = self.qutag_params.widget.get()

        vm1 = qutagparams['Voltmeter Channel 1']
        vm2 = qutagparams['Voltmeter Channel 2']
        vs1 = qutagparams['Battery Port 1']
        vs2 = qutagparams['Battery Port 2']


        # make a vector containing all the tau setpoints for the pulse sequence
        taus = np.linspace(starttau.magnitude, stoptau.magnitude, points)
        print('taus: ' + str(taus))

        # loop through all the set tau value and record the PL on the qutag

        ##Qutag Part
        self.configureQutag()
        qutagparams = self.qutag_params.widget.get()
        lost = self.qutag.getLastTimestamps(True)  # clear Timestamp buffer
        stoptimestamp = 0
        synctimestamp = 0
        bincount = qutagparams['Bin Count']
        timebase = self.qutag.getTimebase()
        start = qutagparams['Start Channel']
        stop = qutagparams['Stop Channel']

        # laser_power = [10, 20, 30, 40, 50]  # mW at TOPAS controller
        laser_power = [50]
        #
        len_laserpower = len(laser_power)

        for i, tau in enumerate(taus):

            self.dataset.clear()
            self.fungen.output[Pulsechannel] = 'OFF'
            self.fungen.output[Shutterchannel] = 'OFF'
            self.fungen.clear_mem(Pulsechannel)
            self.fungen.clear_mem(Shutterchannel)
            self.fungen.wait()
            # self.srs.module_reset[5]
            # self.srs.SIM928_voltage[5]=params['srs bias'].magnitude+0.000000001*i
            # self.srs.SIM928_on[5]

            ## build pulse sequence for AWG channel 1
            chn1buffer = Arbseq_Class('chn1buffer', timestep)
            chn1buffer.delays = [0]
            chn1buffer.heights = [0]
            chn1buffer.widths = [repeat_unit]
            chn1buffer.totaltime = repeat_unit
            chn1buffer.nrepeats = buffer_time / repeat_unit
            chn1buffer.repeatstring = 'repeat'
            chn1buffer.markerstring = 'lowAtStart'
            chn1buffer.markerloc = 0
            chn1bufferwidth = repeat_unit * chn1buffer.nrepeats
            chn1buffer.create_sequence()

            chn1pulse = Arbseq_Class('chn1pulse', timestep)
            chn1pulse.delays = [0]
            chn1pulse.heights = [1]
            chn1pulse.widths = [half_pi_pulse_width]
            chn1pulse.totaltime = half_pi_pulse_width
            chn1pulse.nrepeats = 0
            chn1pulse.repeatstring = 'once'
            chn1pulse.markerstring = 'highAtStartGoLow'
            chn1pulse.markerloc = 0
            chn1pulsewidth = half_pi_pulse_width
            chn1pulse.create_sequence()

            chn1dc = Arbseq_Class('chn1dc', timestep)
            chn1dc.delays = [0]
            chn1dc.heights = [0]
            chn1dc.widths = [repeat_unit]
            chn1dc.totaltime = repeat_unit
            chn1dc.repeatstring = 'repeat'
            chn1dc.markerstring = 'lowAtStart'
            chn1dc.markerloc = 0
            gap = tau - 0.5 * half_pi_pulse_width - 0.5 * pi_pulse_width
            chn1dcrepeats = int(gap / repeat_unit)  # tau-1.5*pulse_width
            print(gap, gap/repeat_unit, chn1dcrepeats)
            chn1dc.nrepeats = chn1dcrepeats
            chn1dcwidth = repeat_unit * chn1dcrepeats
            chn1dc.create_sequence()

            chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
            chn1pulse2.delays = [0]
            chn1pulse2.heights = [1]
            chn1pulse2.widths = [pi_pulse_width]
            chn1pulse2.totaltime = pi_pulse_width
            chn1pulse2width = pi_pulse_width
            chn1pulse2.nrepeats = 0
            chn1pulse2.repeatstring = 'once'
            chn1pulse2.markerstring = 'lowAtStart'
            chn1pulse2.markerloc = 0
            chn1pulse2.create_sequence()

            chn1pulse3 = Arbseq_Class('chn1pulse3', timestep)
            chn1pulse3.delays = [0]
            chn1pulse3.heights = [0]
            chn1pulse3.widths = [repeat_unit]
            chn1pulse3.totaltime = repeat_unit
            chn1pulse3width = shutter_offset
            chn1pulse3.nrepeats = shutter_offset / repeat_unit
            chn1pulse3.repeatstring = 'repeat'
            chn1pulse3.markerstring = 'lowAtStart'
            chn1pulse3.markerloc = 0
            chn1pulse3.create_sequence()

            chn1dc2 = Arbseq_Class('chn1dc2', timestep)
            chn1dc2.delays = [0]
            chn1dc2.heights = [0]
            chn1dc2.widths = [repeat_unit]
            chn1dc2.totaltime = repeat_unit
            chn1dc2.repeatstring = 'repeat'
            chn1dc2.markerstring = 'lowAtStart'
            chn1dc2repeats = int((
                                             period - chn1bufferwidth - chn1pulsewidth - chn1dcwidth - chn1pulse2width - chn1pulse3width) / repeat_unit)
            chn1dc2.nrepeats = chn1dc2repeats
            chn1dc2.markerloc = 0
            chn1dc2width = chn1dc2.nrepeats * repeat_unit
            # print((chn1dc2repeats*params['repeat unit'].magnitude) + tau.magnitude + params['pulse width'].magnitude)
            chn1dc2.create_sequence()

            ## build pulse sequence for AWG channel 2
            chn2buffer = Arbseq_Class('chn2buffer', timestep)
            chn2buffer.delays = [0]
            chn2buffer.heights = [0]
            chn2buffer.widths = [repeat_unit]
            chn2buffer.totaltime = repeat_unit
            chn2buffer.nrepeats = buffer_time / repeat_unit
            chn2buffer.repeatstring = 'repeat'
            chn2buffer.markerstring = 'lowAtStart'
            chn2buffer.markerloc = 0
            chn2bufferwidth = repeat_unit * chn2buffer.nrepeats
            chn2buffer.create_sequence()

            chn2pulse1 = Arbseq_Class('chn2pulse1', timestep)
            chn2pulse1.delays = [0]
            chn2pulse1.heights = [0]
            chn2pulse1.widths = [half_pi_pulse_width]
            chn2pulse1.totaltime = half_pi_pulse_width
            chn2pulse1width = half_pi_pulse_width
            chn2pulse1.nrepeats = 0
            chn2pulse1.repeatstring = 'once'
            chn2pulse1.markerstring = 'highAtStartGoLow'
            chn2pulse1.markerloc = 0
            chn2pulse1.create_sequence()

            chn2dc1 = Arbseq_Class('chn2dc1', timestep)
            chn2dc1.delays = [0]
            chn2dc1.heights = [0]
            chn2dc1.widths = [repeat_unit]
            chn2dc1.totaltime = repeat_unit
            chn2dc1.repeatstring = 'repeat'
            chn2dc1.markerstring = 'lowAtStart'
            chn2dc1.markerloc = 0
            gap = tau - 0.5 * half_pi_pulse_width - 0.5 * pi_pulse_width
            chn2dc1repeats = int(gap / repeat_unit)
            print(gap, gap/repeat_unit, chn2dc1repeats)
            chn2dc1.nrepeats = chn2dc1repeats
            chn2dc1width = repeat_unit * chn2dc1repeats
            chn2dc1.create_sequence()

            chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
            chn2pulse2.delays = [0]
            chn2pulse2.heights = [0]
            chn2pulse2.widths = [pi_pulse_width]
            chn2pulse2.totaltime = pi_pulse_width
            chn2pulse2width = pi_pulse_width
            chn2pulse2.nrepeats = 0
            chn2pulse2.repeatstring = 'once'
            chn2pulse2.markerstring = 'lowAtStart'
            chn2pulse2.markerloc = 0
            chn2pulse2.create_sequence()

            chn2pulse3 = Arbseq_Class('chn2pulse3', timestep)
            chn2pulse3.delays = [0]
            chn2pulse3.heights = [0]
            chn2pulse3.widths = [repeat_unit]
            chn2pulse3.totaltime = repeat_unit
            chn2pulse3width = shutter_offset
            chn2pulse3.nrepeats = shutter_offset / repeat_unit
            chn2pulse3.repeatstring = 'repeat'
            chn2pulse3.markerstring = 'lowAtStart'
            chn2pulse3.markerloc = 0
            chn2pulse3.create_sequence()

            chn2dc2 = Arbseq_Class('chn2dc2', timestep)
            chn2dc2.delays = [0]
            chn2dc2.heights = [1]
            chn2dc2.widths = [repeat_unit]
            chn2dc2.totaltime = repeat_unit
            chn2dc2.repeatstring = 'repeat'
            chn2dc2.markerstring = 'lowAtStart'
            chn2dc2repeats = int((period - chn2bufferwidth - chn2pulse1width - chn2dc1width - chn2pulse2width - chn2pulse3width) / repeat_unit)
            chn2dc2.nrepeats = chn2dc2repeats
            chn2dc2.markerloc = 0
            chn2dc2width = repeat_unit * chn2dc2.nrepeats
            chn2dc2.create_sequence()

            print([buffer_time, half_pi_pulse_width, gap, pi_pulse_width, shutter_offset])
            print([chn1bufferwidth, chn1pulsewidth, chn1dcwidth, chn1pulse2width, chn1pulse3width, chn1dc2width])
            print([chn2bufferwidth, chn2pulse1width, chn2dc1width, chn2pulse2width, chn2pulse3width, chn2dc2width])

            self.fungen.send_arb(chn1buffer, Pulsechannel)
            self.fungen.send_arb(chn1pulse, Pulsechannel)
            self.fungen.send_arb(chn1dc, Pulsechannel)
            self.fungen.send_arb(chn1pulse2, Pulsechannel)
            self.fungen.send_arb(chn1pulse3, Pulsechannel)
            self.fungen.send_arb(chn1dc2, Pulsechannel)
            self.fungen.send_arb(chn2buffer, Shutterchannel)
            self.fungen.send_arb(chn2pulse1, Shutterchannel)
            self.fungen.send_arb(chn2dc1, Shutterchannel)
            self.fungen.send_arb(chn2pulse2, Shutterchannel)
            self.fungen.send_arb(chn2pulse3, Shutterchannel)
            self.fungen.send_arb(chn2dc2, Shutterchannel)

            seq = [chn1buffer, chn1pulse, chn1dc, chn1pulse2, chn1pulse3, chn1dc2]
            seq2 = [chn2buffer, chn2pulse1, chn2dc1, chn2pulse2, chn2pulse3, chn2dc2]

            self.fungen.create_arbseq('twoPulse', seq, Pulsechannel)
            self.fungen.create_arbseq('shutter', seq2, Shutterchannel)
            self.fungen.wait()
            self.fungen.voltage[Pulsechannel] = (params['pulse height'].magnitude+0.000000000001*i)*volt
            # self.fungen.voltage[2] = 7.1+0.0000000000001*i
            self.fungen.voltage[Shutterchannel] = (params['shutter height'].magnitude+0.0000000000001*i)*volt

            print(self.fungen.voltage[Pulsechannel], self.fungen.voltage[Shutterchannel])

            # self.fungen.output[Shutterchannel] = 'ON'  ## turn on the shutter channel before send the laser pulse
            # self.fungen.trigger_delay(Pulsechannel, shutter_offset)
            # self.fungen.sync()
            # time.sleep(2)
            # self.fungen.output[Pulsechannel] = 'ON'
            # time.sleep(2)
            for l, power in enumerate(laser_power):
                # with Client(self.laser) as client:
                #     client.set('laser1:power-stabilization:setpoint', power)
                #     power_now = client.get('laser1:power-stabilization:setpoint')
                #     print(l, power_now)
                if num_AOMs == 2:
                    pulse_power = power * 4.2  # in µW, approximately, after losses in the setup.
                elif num_AOMs == 3:
                    pulse_power = power * 0.9  # in µW

                # wl = self.homelaser(wlTarget, precision=precision, drift_time=drift_time)
                # print('Laser set to:' + str(wlTarget))
                # print('current wavelength: ' + str(wl))

                print('Start taking data')
                print('current tau: ' + str(tau))

                time.sleep(1)

                stoparray = []
                startTime = time.time()
                wls = []
                saveextfreqs = []
                savetaus = []

                self.hist = [0] * bincount
                self.bins = list(range(len(self.hist)))
                self.times = list(
                    np.linspace(0, wholeRange, len(self.hist)))  ## convert the x axis from bin numbers to time
                stopscheck = []

                lost = self.qutag.getLastTimestamps(True)

                looptime = startTime
                while looptime - startTime < runtime:

                    self.fungen.output[Shutterchannel] = 'ON'  ## turn on the shutter channel before send the laser pulse
                    self.fungen.trigger_delay(Pulsechannel, shutter_offset)
                    self.fungen.sync()
                    time.sleep(0.5)

                    # self.homelaser(wlTarget, precision=precision)  # unit: nm)

                    self.fungen.output[Pulsechannel] = 'ON'
                    time.sleep(0.5)

                    dataloss1 = self.qutag.getDataLost()
                    # print("dataloss: " + str(dataloss))

                    dataloss2 = self.qutag.getDataLost()
                    # print("dataloss: " + str(dataloss2SS))

                    # get the timestamps
                    timestamps = self.qutag.getLastTimestamps(True)
                    print("Time left: " + str(runtime - (looptime - startTime)))

                    loopstart = time.time()

                    time.sleep(2)

                    dataloss1 = self.qutag.getDataLost()
                    # print("dataloss: " + str(dataloss))

                    dataloss2 = self.qutag.getDataLost()
                    # print("dataloss: " + str(dataloss))

                    # get the timestamps
                    timestamps = self.qutag.getLastTimestamps(True)

                    looptime += time.time() - loopstart

                    if dataloss1 != 0:
                        print('dataloss: ' + str(dataloss1))

                    self.fungen.output[Pulsechannel] = 'OFF'
                    self.fungen.output[Shutterchannel] = 'OFF'
                    time.sleep(0.2)

                    tstamp = timestamps[0]  # array of timestamps
                    tchannel = timestamps[1]  # array of channels
                    values = timestamps[2]  # number of recorded timestamps

                    for k in range(values):
                        if tchannel[k] == stop:
                            # has photons from start pulse and the emitted photons from electron decay into ground state
                            stoptimestamp = tstamp[k]
                            stopscheck.append(stoptimestamp)

                    print('Elements in stopscheck... (first 10) total: ' + str(len(stopscheck)))
                    print(stopscheck[0:10])

                    wl = self.wm.measure_wavelength()  # unit: nm
                    print("Target Wl: {}; Laser Wl: {}; Tau: {}; Laser Power: {}"
                          .format(wlTarget, wl, tau, power))
                    print("tau ({}/{}), Laser Power ({}/{})"
                          .format((i + 1), points, (l + 1), len_laserpower))
                    wls.append(float(wl))
                    saveextfreqs.append(c / wl + num_AOMs * WindfreakFreq / 1e3)  # GHz

                    savetaus.append(float(tau))

                    for k in range(len(stopscheck)):
                        tdiff = stopscheck[k]
                        binNumber = int(tdiff * timebase * bincount / (wholeRange))
                        if binNumber < bincount:
                            self.hist[binNumber] += 1
                    stopscheck = []

                    values = {
                        # 'x': self.bins,
                        'x': self.times,
                        'y': self.hist,
                    }

                    print('self.startpulse.acquire(values) ....')
                    self.twopulseecho.acquire(values)  # for histogram plotting in GUI

                avewls = np.mean(wls)  ## to get the averaged wavelength
                print('Laser frequency during the measurement: ' + str(c / avewls))

                self.fungen.output[Pulsechannel] = 'OFF'
                self.fungen.output[Shutterchannel] = 'OFF'
                np.savez(os.path.join(PATH, str(i)+str(l) + "_" + str(avewls) + "_" + str(tau) + '_' + str(runtime) + 's'),
                         hist=self.hist, bins=self.times, freq=saveextfreqs, laser_wls=wls, laser_power=power,
                         tau=tau, half_pi_pulse_width=half_pi_pulse_width,
                         pi_pulse_width=pi_pulse_width, measurement_time=runtime)
                time.sleep(5)

        self.fungen.output[Pulsechannel] = 'OFF'  ##turn off the AWG for both channels
        self.fungen.output[Shutterchannel] = 'OFF'


    # the 1D plot widget is used for the live histogram
    @Element(name='twopulseecho Histogram')
    def twopulseecho_Histogram(self):
        p = LinePlotWidget()
        p.plot('twopulseecho Histogram')
        return p

    # more code for the histogram plot
    @twopulseecho_Histogram.on(twopulseecho.acquired)
    def _twopulseecho_Histogram_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        xs = np.array(self.times)
        ys = np.array(self.hist)
        w.set('twopulseecho Histogram', xs=xs, ys=ys)
        return


    @Element(name='QuTAG Parameters')
    def qutag_params(self):
        params = [
            #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
            ('Start Channel', {'type': int, 'default': 0}),
            ('Stop Channel', {'type': int, 'default': 2}),
            ('Bin Count', {'type': int, 'default': 2000}),  ## define bin numbers in the measurement time window
            ('Voltmeter Channel 1', {'type': int, 'default': 1}),
            ('Voltmeter Channel 2', {'type': int, 'default': 2}),
            ('Battery Port 1', {'type': int, 'default': 5}),
            ('Battery Port 2', {'type': int, 'default': 6})
        ]
        w = ParamWidget(params)
        return w

    @Element(name='twopulse parameters')
    def twopulse_parameters(self):
        params = [
            ('Runtime', {'type': float, 'default': 30, 'units': 's'}),
            #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
            ('pulse height', {'type': float, 'default': 3.5, 'units': 'V'}),
            ('shutter height', {'type': float, 'default': 2.0, 'units': 'V'}),
            ('pi/2 pulse width', {'type': float, 'default': 1000e-9, 'units': 's'}),  ## define the pi/2 pulse width
            ('pi pulse width', {'type': float, 'default': 2000e-9, 'units': 's'}),
            ('period', {'type': float, 'default': 50e-3, 'units': 's'}),
            ('repeat unit', {'type': float, 'default': 50e-9, 'units': 's'}),
            ('start tau', {'type': float, 'default': 2e-6, 'units': 's'}),
            ('stop tau', {'type': float, 'default': 30e-6, 'units': 's'}),
            ('step tau', {'type': float, 'default': 1e-6, 'units': 's'}),
            ('# of points', {'type': int, 'default': 29}),
            # ('srs bias', {'type': float, 'default': 1.2, 'units':'V'}),
            ('measuring range', {'type': float, 'default': 90e-6, 'units': 's'}),
            ('shutter offset', {'type': float, 'default': 0e-6, 'units': 's'}),
            ## buffer time & shutter offset is to compensate any delay for the shutter (AOM)
            ('buffer time', {'type': float, 'default': 4e-6, 'units': 's'}),
            ('Shutter channel', {'type': int, 'default': 2}),
            ('Pulse channel', {'type': int, 'default': 1}),
            ('File Name', {'type': str, 'default': "E:\\Data\\7.22.2022_ErLYF_two_pulse_photon_echo\\test"}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Wavelength parameters')
    def wl_parameters(self):
        params = [
            #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
            # ('start', {'type': float, 'default': 1535.665}),
            # ('start', {'type': float, 'default': 1529.420}),
            # ('stop', {'type': float, 'default': 1536}),
            ('wavelength (nm)', {'type': float, 'default': 1529.4695}),
            ('precision(nm): ±', {'type': float, 'default': 0.00024}),
            ('drift_time', {'type': float, 'default': 8, 'units': 's'}),
            ('Windfreak frequency', {'type': float, 'default': 200, 'units': 'MHz'}),
            ('# of AOMs', {'type': int, 'default': 3})
        ]
        w = ParamWidget(params)
        return w

    @twopulseecho.initializer
    def initialize(self):
        self.fungen.output[2] = 'OFF'
        self.fungen.output[1] = 'OFF'
        self.fungen.clear_mem(2)
        self.fungen.clear_mem(1)
        self.fungen.wait()

    @twopulseecho.finalizer
    def finalize(self):
        self.fungen.output[2] = 'OFF'
        self.fungen.output[1] = 'OFF'
        print('Two Pulse measurements complete.')
        return