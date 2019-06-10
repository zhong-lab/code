import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz.drivers.anritsu import MS2721B

from lantz import Q_

class ESR(Spyrelet):

	requires = {
        'analyzer': MS2721B
    }

    @Task()
    def takeData(self):
    	for i in range(100):
    		self.analyzer.savefile(i)
    		time.sleep(10)


   	@takeData.initializer
   	def initialize(self):
   		return

   	@takeData.finalizer
   	def finalize(self):
   		return