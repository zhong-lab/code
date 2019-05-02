
import time
from spyre import Spyrelet, Task, Element
from spyre.repository import Node
from spyre.spyrelets import (TaskVsFSMSpyrelet, SpatialFeedbackSpyrelet,
    CountsVsFrequencySpyrelet, CountsVsLineSpyrelet, TaskVsLaserFrequencySpyrelet, GotoFrequencySpyrelet)
from spyre.widgets.task import TaskWidget
from spyre.widgets.repository_widget import RepositoryWidget


from spyre.widgets.rangespace import Rangespace
from spyre.widgets.spinbox import SpinBox
from spyre.widgets.param_widget import ParamWidget
from lantz.drivers.newport.fsm300 import FSM300
from PyQt5 import QtWidgets
import pyqtgraph as pg

class PlaylistSpyrelet(Spyrelet):

    requires = {
        'fsm': FSM300,
    }

    requires_spyrelet = {
        'taskvsfsm': TaskVsFSMSpyrelet,
        'feedback': SpatialFeedbackSpyrelet,
        'ctsvsfreq': CountsVsFrequencySpyrelet,
        'ctsvsline': CountsVsLineSpyrelet,
        'taskvslaserfreq': TaskVsLaserFrequencySpyrelet,
        'gotolaserfreq': GotoFrequencySpyrelet,
    }

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

    @Task()
    def run_playlist(self, **kwargs):
        self.child_nodes = dict()
        self.dataset.clear()
        pos = self.pts_list.widget.get_pos()
        actions = self.parameters.widget.get()
        feedback = actions['feedback enabled']
        esr = actions['esr enabled']
        ple = actions['ple enabled']
        autosave = actions['autosave']
        goto_laser_freq = actions['goto laser freq']
        laser_freq = actions['laser frequency']
        # if autosave:
        #     node_name = self.save.widget.get_entry_name()
        for idx, coord in enumerate(pos):
            x, y = coord
            name = 'defect {}'.format(idx)
            self.fsm.abs_position = y, x
            self.child_nodes[name] = list()
            ret_vals = {'name':name, 'initial_x':x, 'initial_y':y}
            if goto_laser_freq:
                goto_params = {
                    'target frequency': laser_freq.to('Hz').m,
                    'run CTR optimizer': True,
                    'feedback period':10,
                }
                self.gotolaserfreq.target_parameters.widget.set(**goto_params)
                self.gotolaserfreq.goto_frequency()
            if feedback:
                feedback_params = {
                    'x initial': x * 1e-6,
                    'y initial': y * 1e-6,
                }
                self.feedback.feedback_parameters.widget.set(**feedback_params)
                self.feedback.feedback()
                fb_node = self.feedback.save.widget.generate_node(name_overwrite='feedback')
                self.child_nodes[name].append(fb_node)
                self.run_playlist.acquire({})
            if esr:
                self.ctsvsfreq.sweep()
                esr_node = self.ctsvsfreq.save.widget.generate_node(name_overwrite='esr')
                self.child_nodes[name].append(esr_node)
                self.run_playlist.acquire({})
            if ple:
                self.taskvslaserfreq.scan()
                ple_node = self.taskvslaserfreq.save.widget.generate_node(name_overwrite='ple')
                self.child_nodes[name].append(ple_node)
                self.run_playlist.acquire({})
            self.run_playlist.acquire(ret_vals)
        return

    @Element(name='Playlist actions')
    def parameters(self):
        params = [
            ('goto laser freq',{
                'type': bool,
                'default':True,
            }),
            ('laser frequency', {
                'units': 'GHz',
                'type': float,
                'default': 265300.0e9,
            }),
            ('feedback enabled', {
                'type': bool,
                'default':True,
            }),
            ('esr enabled', {
                'type': bool,
                'default':True,
            }),
            ('ple enabled', {
                'type': bool,
                'default':True,
            }),
            ('autosave', {
                'type': bool,
                'default':False,
            }),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Points list')
    def pts_list(self):
        w = QtWidgets.QWidget()

        def get_pos():
            table = self.pts_list.widget.table
            l = list()
            for row in range(table.rowCount()):
                l.append([table.cellWidget(row,1).value(), table.cellWidget(row,2).value()])
            return l
        w.get_pos = get_pos

        w.table = QtWidgets.QTableWidget()
        def clear_table(_w):
            _w.table.clear()
            _w.table.setRowCount(0)
            _w.table.setColumnCount(4)
            _w.table.setHorizontalHeaderLabels(['Del','x','y','PL line'])
            _w.table.setColumnWidth(0,30)
        clear_table(w)

        def _find_row(del_btn):
            for row in range(self.pts_list.widget.table.rowCount()):
                if del_btn == self.pts_list.widget.table.cellWidget(row, 0):
                    return row
            return None

        def add_line(pos):
            row = self.pts_list.widget.table.rowCount()
            self.pts_list.widget.table.insertRow(row)
            for i in range(2):
                w = SpinBox(value = pos[i], decimals=4)
                self.pts_list.widget.table.setCellWidget(row, i+1, w)

            # Add a combobox
            pl_combo = QtWidgets.QComboBox()
            pl_list = ['N/A','PL 1','PL 2','PL 3','PL 4','noise']
            pl_combo.addItems(pl_list)
            def set_line(_line_name):
                pl_combo.setCurrentIndex(pl_list.index(_line_name))
            def pl_line_changed(_line_name):
                print(_line_name)
            self.set_pl_line = set_line
            pl_combo.currentIndexChanged[str].connect(pl_line_changed)
            self.pts_list.widget.table.setCellWidget(row, 3, pl_combo)

            # Add a remove button
            btn = QtWidgets.QPushButton('X')
            btn.clicked.connect(lambda: self.pts_list.widget.table.removeRow(_find_row(btn)))
            self.pts_list.widget.table.setCellWidget(row, 0, btn)

        def get_fsm_cross():
            for cross_list in [self.taskvsfsm.averaged_scan.widget.crosshairs,
                               self.taskvsfsm.latest_scan.widget.crosshairs]:
                for cross in cross_list:
                    add_line(cross.pos)


        #Add controls
        ctrl_layout = QtWidgets.QHBoxLayout()
        ctrl_widget = QtWidgets.QWidget()
        ctrl_widget.setLayout(ctrl_layout)

        #Add button
        add_btn = QtWidgets.QPushButton('Add')
        add_btn.clicked.connect(lambda: add_line([0,0]))
        ctrl_layout.addWidget(add_btn)

        #Clear btn
        clr_btn = QtWidgets.QPushButton('Clear')
        clr_btn.clicked.connect(lambda: clear_table(w))
        ctrl_layout.addWidget(clr_btn)

        #Fetch from averaged fsm crosshairs
        fsm_cross_btn = QtWidgets.QPushButton('Get FSM Cross')
        fsm_cross_btn.clicked.connect(lambda: get_fsm_cross())
        ctrl_layout.addWidget(fsm_cross_btn)


        layout = QtWidgets.QGridLayout()
        layout.addWidget(ctrl_widget)
        layout.addWidget(w.table)
        layout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(layout)
        return w
