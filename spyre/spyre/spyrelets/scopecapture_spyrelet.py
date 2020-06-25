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

from lantz.drivers.tektronix import TDS2024C

class ScopeCapture(Spyrelet):
	requires = {
		'osc': TDS2024C
	}

	@Task()
	def run(self):
		for i in range(1000000):
			input("Press any key to capture")
			for j in range(5):
				x,y=self.osc.curv()
				x = np.array(x)
				x = x-x.min()
				y = np.array(y)
				time=self.osc.query_time()
				time=float(time)
				out_name = "D:\\Data\\12.5.2019\\0.2T2"
				n=str(time)+'.'+str(j)
				np.savez(os.path.join(out_name,n),x,y)


	@run.initializer
	def initialize(self):
		print('init')

	@run.finalizer
	def finalize(self):
		print('fin')
		return