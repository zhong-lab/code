
import time
from spyre import Spyrelet, Task, Element
from spyre.repository import Node
from spyre.spyrelets import LockinVsFreqSpyrelet
from spyre.widgets.task import TaskWidget
from spyre.widgets.repository_widget import RepositoryWidget


from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from lantz.drivers.arduino.goniometer import Goniometer
from PyQt5 import QtWidgets
import pyqtgraph as pg

class GonioVsSpyrelet(Spyrelet):

    requires = {
        'gonio': Goniometer,
    }

    requires_spyrelet = {
        'lockinvsfreq': LockinVsFreqSpyrelet,
    }

    @Task()
    def gonio_vs_lockinvsfreq(self, **kwargs):
        self.child_nodes = dict()
        self.dataset.clear()
        params = self.parameters.widget.get()
        self.max_rows = len(params['z range'])
        dz = params['z range'][-1] - params['z range'][0]
        fs = self.lockinvsfreq.sweep_parameters.widget.get()['frequency']
        df = fs[-1] - f[0]
        self.scale = [df.to('GHz').m, dz.to('mm').m]

        for idx in range(params['sweep']):
            for z in self.sweep.progress(params['z range']):
                print(z)
                # self.gonio.R = z
                self.lockinvsfreq.sweep()
                esr_node = self.lockinvsfreq.save.widget.generate_node(name_overwrite='z_{}'.format(z))
                self.child_nodes[name].append(esr_node)
                aveg_x = self.lockinvsfreq.data.groupby('f').x.mean()
                ret_vals = {
                    'z':z,
                    'data_x':aveg_x.index,
                    'data_y':aveg_x,
                }
                self.gonio_vs_lockinvsfreq.acquire(ret_vals)
        return

    @gonio_vs_lockinvsfreq.initializer
    def gonio_vs_lockinvsfreq_init(self):
        

    @Element(name='Parameters')
    def parameters(self):
        fs_range = Rangespace(unit='GHz')
        params = [
            ('z range', {
                'type': range,
                'units': 'mm',
                'default': {'func':'linspace', 'start':0, 'stop':10e-3, 'num':50},
            }),
            ('sweeps', {
                'type': int,
                'default': 10,
                'positive': True,
            }),
        ]
        w = ParamWidget(params)
        return w

    
    @Element()
    def average_plot(self):
        w = HeatmapPlotWidget()
        w.xlabel = 'f (Hz)'
        w.ylabel = 'z (mm)'
        return w

    @average_plot.on(gonio_vs_lockinvsfreq.acquired)
    def average_plot_update(self):
        grouped = self.data.groupby('idx')['data_y']
        averaged = grouped.apply(lambda esr_row: np.mean(np.vstack(esr_row), axis=0))
        im = np.vstack(averaged)
        im = np.pad(im, (0, self.max_rows - im.shape[1]), mode='constant', constant_values=0)
        ev.widget.set(im, pos=self.pos, scale=self.scale)

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        def generate_node(name_overwrite=None):
            if name_overwrite is None:
                name = 'uid{}'.format(w.repo.get_uid())
            else:
                name = name_overwrite
            main_node = Node(name, dataframe = self.dataset.get_frame_copy())
            for defect_name in self.child_nodes.keys():
                child_node = Node(name=defect_name)
                for n in self.child_nodes[defect_name]:
                    child_node.add_node(node=n)
                main_node.add_node(node=child_node)
            return main_node
        w.generate_node = generate_node
        return w