import numpy as np
import pyqtgraph as pg
import time
import csv
import os

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

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild

from lantz.drivers.keysight import Keysight_33622A

class DontDelete(Spyrelet):
	requires = {
		'fungen': Keysight_33622A
	}

	@Task()
	def startpulse(self):
		self.fungen.trigger_source[1] = 'BUS'
		for _ in range(200):
			self.fungen.trigger()
			self.fungen.wait()
			time.sleep(0.5)
		