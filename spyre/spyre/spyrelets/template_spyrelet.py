###Template for making a spyrelet
##DON'T MODIFY THIS FILE! COPY INTO ANOTHER FILE AND MAKE CHANGES

import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from lantz import Q_

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

###Import lantz drivers files for all instruments you use.
#e.g.
#from lantz.drivers.keysight import Keysight_33622A
#The above line will import the AWG driver

class ExperimentName(Spyrelet):
	#Replace ExperimentName with the name of your experiment
	requires = {
		#add all instruments here, with aliases that match whatever you set in the config file
		#'fungen': Keysight_33622A
	}
	#.dll instruments can be initialized as None, and connected to later
	#qutag = None

###Tasks##############################################################
	@Task()
	def firstTask(self):
		print('This is the first task')
		#Get the parameters to use
		params = self.example_params.widget.get()
		someInt = params['Some integer']
		#here is the task main body

	@firstTask.initializer
	def initialize(self):
		#task initializer
		return

	@firstTask.finalizer
	def finalize(self):
		#task finalizer
		return

	##If you need more tasks, just add more
	@Task()
	def secondTask(self):
		print('This is the first task')
		#here is the task main body

	@secondTask.initializer
	def initialize(self):
		#task initializer
		return

	@secondTask.finalizer
	def finalize(self):
		#task finalizer
		return
###Tasks##############################################################

###Elements###########################################################
	@Element(name='Example Parameters')
	def example_params(self):
		params = [
	#    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
		('Some integer', {'type': int, 'default': 0}),
		('Some float with units', {'type': float, 'default': 0.5, 'units':'V'}),
		('Some string', {'type': str, 'default': 'some string'})
		]
		w = ParamWidget(params)
		return w
###Elements###########################################################