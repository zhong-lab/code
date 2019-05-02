import pyqtgraph as pg
from pyqtgraph.graphicsItems.ROI import ROI
import numpy as np
from PyQt5 import QtWidgets

from spyre import Spyrelet, Task, Element
from spyre.widgets.spinbox import SpinBox
from spyre.widgets.task import TaskWidget
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.rangespace import Rangespace
from spyre.plotting import HeatmapPlotWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
from lantz.drivers.ni.daqmx import Device
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel
from lantz.drivers.ni.daqmx import AnalogInputTask, VoltageInputChannel
from lantz.drivers.ni.daqmx import AnalogOutputTask, VoltageOutputChannel
from lantz.drivers.newport.fsm300 import FSM300

class TaskVsFSMSpyrelet(Spyrelet):

    requires = {
        'daq': Device,
        'fsm': FSM300,
    }

    @Task()
    def scan(self, **kwargs):
        self.dataset.clear()
        params = self.scan_parameters.widget.get()
        x_range = params['x range'].array.to('um').m
        y_range = params['y range'].array.to('um').m
        for sweep in self.scan.progress(range(params['sweeps'])):
            rows = len(y_range)
            for column_idx, x in enumerate(x_range):
                line_scan_params = {
                    'init_point': (x, y_range[0]),
                    'final_point': (x, y_range[-1]),
                    'steps': rows,
                    'acq_task': self.task,
                    'acq_rate': Q_(params['acquisition rate'], 'Hz'),
                    'pts_per_pos': params['acquisition points per pixel'],
                    # 'diff_task': self.diff_task,
                }
                column_data = self.fsm.line_scan(**line_scan_params)
                values = {
                    'sweep_idx': sweep,
                    'column_idx': column_idx,
                    'column_data': column_data,
                }
                self.scan.acquire(values)
        return

    @scan.initializer
    def initialize_scan(self):
        params = self.scan_parameters.widget.get()
        self.max_rows = len(params['y range'].array.to('um').m)
        x_range = params['x range'].array.to('um').m
        y_range = params['y range'].array.to('um').m
        x_diff = x_range[-1] - x_range[0]
        y_diff = y_range[-1] - y_range[0]
        pos = np.mean(y_range) - y_diff / 2, np.mean(x_range) - x_diff / 2
        scale = y_diff / len(y_range), x_diff / len(x_range)
        im_pos = [v for v in pos]
        im_scale = [v for v in scale]

        self.latest_scan.widget.im_pos     = im_pos
        self.latest_scan.widget.im_scale   = im_scale
        self.averaged_scan.widget.im_pos   = im_pos
        self.averaged_scan.widget.im_scale = im_scale

        inp_ch = params['acquisition channel input']
        if inp_ch in self.daq.counter_input_channels:
            self.task = CounterInputTask('TaskVsFSM_CI')
            channel = CountEdgesChannel(inp_ch)
            self.task.add_channel(channel)
            self.diff_task = CounterInputTask('TaskVsFSM_CI_differential')
            # diff_channel = CountEdgesChannel('/dev1/ctr3')
            # self.diff_task.add_channel(diff_channel)
        elif inp_ch in self.daq.analog_input_channels:
            self.task = AnalogInputTask('TaskVsFSM_AI')
            channel = VoltageInputChannel(inp_ch)
            self.task.add_channel(channel)
        else:
            # should never get here
            pass
        return

    @scan.finalizer
    def finalize_scan(self):
        self.fsm.abs_position = (0.0, 0.0)
        self.task.clear()
        self.diff_task.clear()
        return

    @Element()
    def scan_parameters(self):
        params = [
            ('acquisition channel input', {
                'type': list,
                'items': list(self.daq.counter_input_channels)+list(self.daq.analog_input_channels),
                'default': 'Dev1/ctr2',
            }),
            ('x range', {
                'type': range,
                'units': 'um',
                'default': {'func':'linspace', 'start':-15e-6, 'stop':15e-6, 'num':100}
            }),
            ('y range', {
                'type': range,
                'units': 'um',
                'default': {'func':'linspace', 'start':-15e-6, 'stop':15e-6, 'num':100}
            }),
            ('sweeps', {
                'type': int,
                'positive': True,
            }),
            ('acquisition rate', {
                'type': float,
                'nonnegative': True,
                'default': 5000,
            }),
            ('acquisition points per pixel', {
                'type': int,
                'positive': True,
                'default': 10,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element()
    def latest_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'X (um)'
        w.ylabel = 'Y (um)'
        w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @latest_scan.on(scan.acquired)
    def update_latest_scan(self, ev):
        latest = self.data[self.data.sweep_idx == self.data.sweep_idx.max()]
        im = np.vstack(latest.sort_values('column_idx')['column_data'])
        im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)
        ev.widget.set(im)
        return

    @Element()
    def averaged_scan(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'X (um)'
        w.ylabel = 'Y (um)'
        w.toolbox.addItem(Interactive_Widget(plot=w, fsm=self.fsm, scan_params=self.scan_parameters), 'Interactive Tools')
        return w

    @averaged_scan.on(scan.acquired)
    def update_averaged_scan(self, ev):
        grouped = self.data.groupby('column_idx')['column_data']
        averaged = grouped.apply(lambda column: np.mean(np.vstack(column), axis=0))
        im = np.vstack(averaged)
        im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)
        ev.widget.set(im)
        return

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w



class Interactive_Widget(QtWidgets.QWidget):
    def __init__(self, plot, fsm, scan_params, parent=None):
        super().__init__(parent=parent)
        self.layout = QtWidgets.QFormLayout()
        self.plot = plot
        self.fsm = fsm
        self.scan_params = scan_params

        self.add_moveTo_widgets()
        # self.add_setRange_widgets()

        self.setLayout(self.layout)

    def add_moveTo_widgets(self):
        crosshair_combo = QtWidgets.QComboBox()
        crosshair_combo.addItem('zero')
        self.plot.crosshairs.sigCrosshairAdded.connect(lambda: crosshair_combo.addItem('crosshair::{}'.format(crosshair_combo.count())))
        self.plot.crosshairs.sigCrosshairRemoved.connect(lambda: crosshair_combo.removeItem(crosshair_combo.count()-1))

        x_spinbox, y_spinbox = SpinBox(value = 0, dec=True, decimals=4), SpinBox(value = 0, dec=True, decimals=4)
        def update_xy(index):
            if index==0:
                x,y = 0,0
            else:
                x,y = self.plot.crosshairs[index-1]
            x_spinbox.setValue(x)
            y_spinbox.setValue(y)
        crosshair_combo.currentIndexChanged.connect(update_xy)

        def move():
            x, y = x_spinbox.value(), y_spinbox.value()
            self.fsm.abs_position = y,x  # Crrrently the axis are flipped in the graph... For now this will make it consistent.  We may also need to change the fsm drivers
        go_btn = QtWidgets.QPushButton('Go')
        go_btn.clicked.connect(move)

        self.layout.addRow('Crosshair', crosshair_combo)
        self.layout.addRow('x', x_spinbox)
        self.layout.addRow('y', y_spinbox)
        self.layout.addRow('Move to position', go_btn)

    # def add_setRange_widgets(self):
    #     range_roi = ROI((1,1))
    #     self.plot.plot_item.addItem(range_roi)
