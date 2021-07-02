from PyQt5 import QtWidgets
import pyqtgraph as pg
import itertools as it
import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle # for saving large arrays
import math
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import matplotlib.pyplot as plt

import numpy as np

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.princetoninstruments import SpectraPro
from lantz.drivers.bristol import Bristol_771
from toptica.lasersdk.client import NetworkConnection, Client
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900

from lantz import Q_

class MonochromatorSpyrelet(Spyrelet):

	requires = {
		'sp': SpectraPro,
	}

	@Task()
	def monoscan(self, timestep=100e-9):

		expparams = self.exp_parameters.widget.get()
		wlparams = self.wl_parameters.widget.get()

		wlTargets=np.linspace(wlparams['start'],wlparams['stop'],
			expparams['# of points'])

		print('wlTargets: '+str(wlTargets))

		for i in range(expparams['# of points']):
			print(i)
			print('current target spectrometer wavelength: '+str(wlTargets[i]))
			self.sp.set_wavelength(float(wlTargets[i]))
			print('actual spectrometer wavelength: '+str(self.sp.get_wavelength()))
			time.sleep(10)

	@Element(name='Wavelength parameters')
	def wl_parameters(self):
		params = [
			('start', {'type': float, 'default': 1535.90}),
			('stop', {'type': float, 'default':  1535.90}),
			('Laser wavelength',{'type':float,'default':1535})
		]
		w = ParamWidget(params)
		return w

	@Element(name='Experiment Parameters')
	def exp_parameters(self):
		params = [
			('# of points', {'type': int, 'default': 1}),
			('Measurement Time', {'type': int, 'default': 300, 'units':'s'}),
			('File Name', {'type': str}),
			('AWG Pulse Repetition Period',{'type': float,'default': 0.05,'units':'s'}),
			('AWG Pulse Frequency',{'type': int,'default': 20,'units':'Hz'}),
			('AWG Pulse Width',{'type': float,'default': 200e-6,'units':'s'}),
			('Dither Voltage',{'type':float,'default':2,'units':'V'})
		]
		w = ParamWidget(params)
		return w