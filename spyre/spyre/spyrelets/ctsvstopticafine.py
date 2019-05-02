import numpy as np
import pyqtgraph as pg
import time

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget

from lantz.drivers.toptica import DLC
from lantz.drivers.bristol import Bristol671
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel


class CountsVsTopticaFineSpyrelet(Spyrelet):

    requires = {
        'dlc': DLC,
        'wavemeter': Bristol671,
        'daq': Device,
    }

    @Task()
    def sweep(self, **kwargs):
        
