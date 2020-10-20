import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
from lantz.drivers.keysight import Keysight_33622A

from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A

from lantz.drivers.tektronix.tds5104 import TDS5104

from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz=Q_(1,'kHz')
MHz = Q_(1.0,'MHz')
dB = Q_(1,'dB')
dBm = Q_(1,'dB')

class piezoScan(Spyrelet):
    """ Contains a task and widget for running a piezo scan, and saving the data
    from the oscilloscope.
    """
    requires={
        'wm': Bristol_771,
        'fungen':Keysight_33622A,
        'osc': TDS5104
        }
    laser=NetworkConnection('1.1.1.2')

    def homelaser(self,start):
		current=self.wm.measure_wavelength()
		with Client(self.laser) as client:

			while current<start-0.001 or current>start+0.001:
				setting=client.get('laser1:ctl:wavelength-set', float)
				offset=current-start
				client.set('laser1:ctl:wavelength-set', setting-offset)
				time.sleep(3)
				current=self.wm.measure_wavelength()
				print(current, start)

    @Task()
	def pzscan(self):
		""" Task to perform an absorption measurement. Sets a ramp waveform on
		the AWG (assumes the AWG is connected to the piezo input for the laser).
		And records the scan from the oscilloscope.
		"""

		# some initialization of the function generator
		self.fungen.clear_mem(1)
		self.fungen.wait()

		# get the parameters for the experiment from the widget
		piezoParams=self.absorption_params.widget.get()
		wl=piezoParams['Wavelength'].magnitude
		channel=piezoParams['Channel'].magnitude
		Vstart=piezoParams['Start voltage'].magnitude
		Vstop=piezoParams['Stop voltage'].magnitude
		scale=piezoParams['Scale factor'].magnitude
		laserChannel=piezoParams['Laser input channel'].magnitude
		piezoOffset=piezoParams['Piezo voltage offset'].magnitude
        measChannel=piezoParams['Oscilloscope measurement channel'].magnitude
        points=piezoParams['# of points'].magnitude
        filename=piezoParams['Filename']

		# convert the start voltage and stop voltage into a voltage
		# and offset to set on the AWG
		offset=(Vstart+Vstop)/2
		Vpp=Vstart-Vstop

        # home the laser
		self.configureQutag()
		self.homelaser(wl)
		print('Laser Homed!')

        # create a list of voltages to loop through
        Vpoints=np.linspace(Vstart,Vstop,points)

		# AWG Output on
		self.fungen.output[channel]='ON'
        self.fungen.waveform[channel]='DC'

		# set the piezo scan voltage scale factor on the laser
		with Client(self.laser) as client:
			client.set('laser1:dl:pc:voltage-set',piezoOffset)
			client.set('laser1:dl:pc:external-input',laserChannel)
			client.set('laser1:dl:factor',scale)

        # now loop through the points on the list and record the average DC
        # signal from the oscilloscope
        for i in points:
            self.fungen.offset[channel]=Vpoints[i]
            time.sleep(3)
            # measure the wavelength
            wl_meas=self.wm.measure_wavelength()

            # average the voltage measured on the oscilloscope
            t,V=self.osc.curv()
            Vavg=np.mean(V)

            # write this to a .CSV file
            with open(filename+'.csv', 'w') as csvfile:
                CSVwriter= csv.writer(csvfile, delimiter=' ',quotechar='|',
                quoting=csv.QUOTE_MINIMAL)
                CSVwriter.writerow(wl_meas,Vavg)

        @Element(name='Piezo scan parameters')
    	def piezo_params(self):
    		""" Widget for piezo scan parameters.

    		Note that when setting the start and stop voltage on the AWG there
            is a limit of +/-2V on the laser piezo, (reduced by half due to
            impedance matching). If a voltage is set beyond these bounds then
            that part of the ramp gets cut off.

    		Laser input channel: the channel on the laser controller that you
            plug the AWG output into.
    			Channel #2: "Fast in 3"
    		"""

    		params=[
    		('Wavelength',{'type':float,'default':1536.480,'units':'nm'}),
    		('Channel',{'type':int,'default':2}),
    		('Start voltage',{'type':float,'default':-2,'units':V}),
    		('Stop voltage',{'type':float,'default':2,'units':V}),
    		('Scale factor',{'type':float,'default':17}),
    		('Laser input channel',{'type':int,'default':2}),
    		('Piezo voltage offset',{'type':float,'default':70}),
            ('Oscilloscope measurement channel',{'type':int,'default':3}),
            ('# of points',{'type':int,'default',100})
            ('Filename',{'type':str,'default':'piezo_scan'})
    		]

    		w=ParamWidget(params)
    		return w

        @pzscan.initializer
    	def initialize(self):
    		self.wm.start_data()

    	@pzscan.finalizer
    	def finalize(self):
    		self.wm.stop_data()
    		return
