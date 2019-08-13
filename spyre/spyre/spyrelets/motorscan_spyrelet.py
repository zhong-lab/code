import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random


from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget,LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.tektronix import TDS2024C

class MotorScan(Spyrelet):
	requires = {
		'fungen': Keysight_33622A,
		'osc': TDS2024C
	}

	@Task()
	def scan(self):
		self.fungen.waveform[1]='TRI'

		self.fungen.output[1]='ON'
		return

	@scan.initializer
	def initialize(self):
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		return

	@scan.finalizer
	def finalize(self):
		self.fungen.output[1]='OFF'
		self.fungen.output[2]='OFF'
		return

	@Element(name='Params')
	def parameters(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Amplitude', {'type': float, 'default': 1, 'units':'V'}),
		('Frequency', {'type': float, 'default': 10, 'units':'Hz'})
		# ('Amplitude', {'type': float, 'default': 1, 'units':'V'})
		]
		w = ParamWidget(params)
		return w