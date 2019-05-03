import numpy as np
import pyqtgraph as pg
import time
import csv

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.qutools import QuTAG

class QutagHistogram(Spyrelet):
	requires = {'qutag': QuTAG}

	@Task()
	def getHist(self):
		print('ok')

	@getHist.initializer
	def initialize(self):
		qutag = self.qutag.QuTAG()
		devType = self.qutag.getDeviceType()

		if (devType == qutag.DEVTYPE_QUTAG):
			print("found quTAG!")
		else:
			print("no suitable device found - demo mode activated")

		print("Device timebase:" + str(qutag.getTimebase()))

	@getHist.finalizer
	def finalize(self):
		return

