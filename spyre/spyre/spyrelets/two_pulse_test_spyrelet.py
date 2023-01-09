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
import time

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
        'fungen': Keysight_33622A
    }
    qutag = None
    laser = NetworkConnection('1.1.1.2')

    xs = np.array([])
    ys = np.array([])
    hist = []

    def homelaser(self, start):
        current = self.wm.measure_wavelength()
        with Client(self.laser) as client:
            while current < start - 0.001 or current > start + 0.001:
                setting = client.get('laser1:ctl:wavelength-set', float)
                offset = current - start
                client.set('laser1:ctl:wavelength-set', setting - offset)
                time.sleep(3)
                current = self.wm.measure_wavelength()
                print(current, start)


    # def createHistogram(self,stoparray, timebase, bincount, totalWidth, tau):
    # 	# lowBound=1.9*tau
    # 	# highBound=2.1*tau
    # 	hist = [0]*bincount
    # 	for stoptime in stoparray:
    # 		binNumber = int(stoptime*timebase*bincount/(totalWidth))
    # 		if binNumber >= bincount:
    # 			continue
    # 			print('error')
    # 		else:
    # 			hist[binNumber]+=1
    # 	out_name = "Q:\\Data\\6.23.2021_ffpc\\Echotest\\"
    # 	x=[]
    # 	for i in range(bincount):
    # 		x.append(i*totalWidth/bincount)
    # 	np.savez(os.path.join(out_name,str(int(round(tau*1e6,0)))),hist,x)
    # 	print('Data stored under File Name: ' + str(tau))

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
    def twopulseecho(self, timestep=1e-9):
        params = self.twopulse_parameters.widget.get()
        # starttau = params['start tau']
        # stoptau = params['stop tau']
        gap = params['gap'].magnitude
        points = params['# of points']
        period = params['period'].magnitude
        repeat_unit = params['repeat unit'].magnitude
        half_pi_len_start = params['pi/2 pulse width start'].magnitude
        half_pi_len_end = params['pi/2 pulse width end'].magnitude
        buffer_time = params['buffer time'].magnitude
        shutter_offset = params['shutter offset'].magnitude
        wholeRange = params['measuring range'].magnitude
        Pulsechannel = params['Pulse channel']
        Shutterchannel = params['Shutter channel']

        ## turn off the AWG before the measurement
        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'

        # self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
        # time.sleep(3)  ##wait 1s to turn on the SNSPD



        # make a vector containing all the tau setpoints for the pulse sequence
        half_pi_lengths = np.linspace(half_pi_len_start, half_pi_len_end, points)
        pi_lengths = half_pi_lengths * 2
        print('half_pi_lengths: ' + str(half_pi_lengths))

        # loop through all the set tau value and record the PL on the qutag

        for i, half_pi_len in enumerate(half_pi_lengths):
            pi_len = pi_lengths[i]

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
            chn1pulse.widths = [half_pi_len]
            chn1pulse.totaltime = half_pi_len
            chn1pulse.nrepeats = 0
            chn1pulse.repeatstring = 'once'
            chn1pulse.markerstring = 'highAtStartGoLow'
            chn1pulse.markerloc = 0
            chn1pulsewidth = half_pi_len
            chn1pulse.create_sequence()

            chn1dc = Arbseq_Class('chn1dc', timestep)
            chn1dc.delays = [0]
            chn1dc.heights = [0]
            chn1dc.widths = [repeat_unit]
            chn1dc.totaltime = repeat_unit
            chn1dc.repeatstring = 'repeat'
            chn1dc.markerstring = 'lowAtStart'
            chn1dc.markerloc = 0
            chn1dcrepeats = int(gap / repeat_unit)  # tau-1.5*pulse_width
            print(gap, gap/repeat_unit, chn1dcrepeats)
            chn1dc.nrepeats = chn1dcrepeats
            chn1dcwidth = repeat_unit * chn1dcrepeats
            chn1dc.create_sequence()

            chn1pulse2 = Arbseq_Class('chn1pulse2', timestep)
            chn1pulse2.delays = [0]
            chn1pulse2.heights = [1]
            chn1pulse2.widths = [pi_len]
            chn1pulse2.totaltime = pi_len
            chn1pulse2width = pi_len
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
            chn1dc2repeats = int((period - chn1bufferwidth - chn1pulsewidth - chn1dcwidth - chn1pulse2width - chn1pulse3width) / repeat_unit)
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
            chn2pulse1.widths = [half_pi_len]
            chn2pulse1.totaltime = half_pi_len
            chn2pulse1width = half_pi_len
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
            chn2dc1repeats = int(gap / repeat_unit)
            print(gap, gap/repeat_unit, chn2dc1repeats)
            chn2dc1.nrepeats = chn2dc1repeats
            chn2dc1width = repeat_unit * chn2dc1repeats
            chn2dc1.create_sequence()

            chn2pulse2 = Arbseq_Class('chn2pulse2', timestep)
            chn2pulse2.delays = [0]
            chn2pulse2.heights = [0]
            chn2pulse2.widths = [pi_len]
            chn2pulse2.totaltime = pi_len
            chn2pulse2width = pi_len
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

            print([buffer_time, half_pi_len, gap, pi_len, shutter_offset])
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
            self.fungen.voltage[Pulsechannel] = params['pulse height'].magnitude + 0.000000000001 * i
            # self.fungen.voltage[2] = 7.1+0.0000000000001*i
            self.fungen.voltage[Shutterchannel] = params['shutter height'].magnitude + 0.0000000000001 * i

            print(self.fungen.voltage[Pulsechannel], self.fungen.voltage[Shutterchannel])

            self.fungen.output[Shutterchannel] = 'ON'  ## turn on the shutter channel before send the laser pulse
            self.fungen.trigger_delay(Pulsechannel, shutter_offset)
            self.fungen.sync()
            time.sleep(2)
            self.fungen.output[Pulsechannel] = 'ON'
            time.sleep(2)

            time.sleep(20)

            self.fungen.output[Pulsechannel] = 'OFF'
            self.fungen.output[Shutterchannel] = 'OFF'

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
            ('Bin Count', {'type': int, 'default': 500}),  ## define bin numbers in the measurement time window
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
            ('Runtime', {'type': float, 'default': 20, 'units': 's'}),
            #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
            ('pulse height', {'type': float, 'default': 3.5, 'units': 'V'}),
            ('shutter height', {'type': float, 'default': 2.0, 'units': 'V'}),
            ('pi/2 pulse width start', {'type': float, 'default': 500e-9, 'units': 's'}),
            ## define the pi/2 pulse width
            ('pi/2 pulse width end', {'type': float, 'default': 3000e-9, 'units': 's'}),
            ('period', {'type': float, 'default': 50e-3, 'units': 's'}),
            ('repeat unit', {'type': float, 'default': 50e-9, 'units': 's'}),
            ('gap', {'type': float, 'default': 2e-6, 'units': 's'}),  # duration between two pulses
            # ('stop tau', {'type': float, 'default': 40e-6, 'units': 's'}),
            # ('step tau', {'type': float, 'default': 1e-6, 'units': 's'}),
            ('# of points', {'type': int, 'default': 6}),
            # ('srs bias', {'type': float, 'default': 1.2, 'units':'V'}),
            ('measuring range', {'type': float, 'default': 20e-6, 'units': 's'}),
            ('shutter offset', {'type': float, 'default': 0e-6, 'units': 's'}),
            ## buffer time & shutter offset is to compensate any delay for the shutter (AOM)
            ('buffer time', {'type': float, 'default': 4e-6, 'units': 's'}),
            ('Shutter channel', {'type': int, 'default': 2}),
            ('Pulse channel', {'type': int, 'default': 1}),
            ('File Name', {'type': str, 'default': "E:\\Data\\7.22.2022_ErLYF_two_pulse_photon_echo\\test"}),
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