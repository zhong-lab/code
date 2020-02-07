from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

from spyre.repository import Repository
from spyre.plotting import LinePlotWidget,HeatmapPlotWidget
from spyre.widgets.splitter_widget import Splitter, SplitterOrientation

import numpy as np
import pandas as pd

class DataExplorer(QtWidgets.QWidget):
    def __init__(self, parent=None, filename=None):
        super().__init__(parent=parent)
        self.repo = None
        self.item_list = list()
        self.filename = filename
        self.build_ui()
        if not filename is None:
            self.reload()

    def build_ui(self):

        # Build file loading widgets
        ctrl_panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        ctrl_panel.setLayout(layout)
        select_filename_btn = QtWidgets.QPushButton('Select File...')
        self.filename_label = QtWidgets.QLabel('No file selected' if self.filename is None else self.filename)
        select_filename_btn.clicked.connect(self.select_filename)
        reload_btn = QtWidgets.QPushButton('Reload')
        reload_btn.clicked.connect(self.reload)
        layout.addWidget(select_filename_btn)
        layout.addWidget(self.filename_label)
        layout.addWidget(reload_btn)

        #Navigation function
        def move_index_down(_self, _ev):
            if type(_ev)==QtGui.QKeyEvent:
                if _ev.matches(QtGui.QKeySequence.MoveToPreviousPage):
                    inc = -1
                elif _ev.matches(QtGui.QKeySequence.MoveToNextPage):
                    inc = 1
                else:
                    return QtWidgets.QTreeWidget.keyPressEvent(_self, _ev)
                cur = self.tree.currentItem()
                if not cur is None:
                    name = cur.text(0)
                    i = self.item_list.index(cur)
                    found_match = False
                    while not found_match:
                        i+=inc
                        if i >=len(self.item_list) or i<0:
                            found_match = True
                        elif self.item_list[i].text(0)==name:
                            self.tree.setCurrentItem(self.item_list[i])
                            found_match = True
                _ev.accept()

        # Build tree
        self.tree = QtWidgets.QTreeWidget()
        self.tree.currentItemChanged.connect(lambda cur, prev: self._new_table_selection(cur))
        layout.addWidget(self.tree)
        self.tree.keyPressEvent = lambda ev: move_index_down(self.tree, ev)

        # Build plot widgets
        self.plot_layout = QtWidgets.QStackedLayout()
        self.line_plot = LinePlotWidget()
        self.img_plot = HeatmapPlotWidget()
        self.plot_layout.addWidget(self.line_plot)
        self.plot_layout.addWidget(self.img_plot)
        self.plot_container = QtWidgets.QWidget()
        self.plot_container.setLayout(self.plot_layout)

        #Build dataframe table
        self.df_table = QtWidgets.QTableView()
        
        self.tab_container = QtWidgets.QTabWidget()
        self.tab_container.addTab(self.plot_container, 'Plot')
        self.tab_container.addTab(self.df_table, 'Table')

        #Set the main layout
        splitter_config = {
            'main_w': ctrl_panel,
            'side_w': self.tab_container,
            'orientation': SplitterOrientation.vertical_right_button,
        }
        splitter = Splitter(**splitter_config)

        splitter.setSizes([1, 400])
        splitter.setHandleWidth(10)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _new_table_selection(self, item):
        if not item is None:
            self._tabulate_item(item)
            self._plot_item(item)

    def _tabulate_item(self, item):
        path = item.data(0,QtCore.Qt.ToolTipRole)
        if path=='/':
            df = self.repo.get_index(col_order=['uid', 'name', 'spyrelet', 'date', 'time', 'description'])
            pd_model = PandasModel(df)
            model = QtCore.QSortFilterProxyModel()
            model.setSourceModel(pd_model)
            self.df_table.setSortingEnabled(True)
            self.tab_container.setCurrentWidget(self.df_table)
        else:
            df = self.repo[path].get_data()
            self.df_table.setSortingEnabled(False)
            if df is None:
                model = PandasModel(pd.DataFrame({}))
            else:
                model = PandasModel(df)
        self.df_table.setModel(model)

    def _plot_item(self, item):
        path = item.data(0,QtCore.Qt.ToolTipRole)
        self.plot_node(self.repo[path])

    def plot_node(self, node):
        meta = node.get_meta()
        if 'BasePlotWidget_type' in meta:
            if node.get_data() is None or node.get_data().empty:
                return
            if meta['BasePlotWidget_type'] == self.line_plot.plot_type_str:
                self.plot_layout.setCurrentWidget(self.line_plot)
                self.line_plot.load_node(node)
            elif meta['BasePlotWidget_type'] == self.img_plot.plot_type_str:
                self.plot_layout.setCurrentWidget(self.img_plot)
                self.img_plot.load_node(node)
            self.tab_container.setCurrentWidget(self.plot_container)


    def select_filename(self):
        filename, other = QtWidgets.QFileDialog.getOpenFileName(None, 'Save repository to...', '', 'HDF5 files (*.h5)')
        if filename:
            self.filename_label.setText(filename)
            self.filename = filename
            self.reload()
        return

    def reload(self):
        if self.filename is None:
            raise Exception('No file selected.  Please select a filename')
        self.repo = Repository(self.filename)
        self._plot_item = lambda _s,_i: None
        self.tree.clear()
        self.tree.addChild = self.tree.addTopLevelItem
        self.item_list = list()
        def add_child(node, parent, path_prefix):
            for name in node.get_child_names(sort=True):
                child = node.get_child(name)
                path = path_prefix + '/' + name
                tree_item = QtWidgets.QTreeWidgetItem([name])
                tree_item.setData(0, QtCore.Qt.ToolTipRole, path)
                parent.addChild(tree_item)
                self.item_list.append(tree_item)
                add_child(child, tree_item, path)
        tree_item = QtWidgets.QTreeWidgetItem(['root'])
        tree_item.setData(0, QtCore.Qt.ToolTipRole, '/')
        self.tree.addChild(tree_item)
        self.item_list.append(tree_item)
        add_child(self.repo.root, self.tree, '')
        self._plot_item = lambda item: self.__class__._plot_item(self, item)

    def get_selection_str(self, col_sep='\t', row_sep='\n'):
        indexes = self.df_table.selectedIndexes()
        model = self.df_table.model()
        if model is None:
            return
        if len(indexes) == 0:
            df = model._data
            return df.to_csv(sep=col_sep)
        else:
            indexes = sorted(indexes, key=lambda idx:(idx.row(),idx.column()))
            nb_column = indexes[-1].column()-indexes[0].column()+1
            model = self.df_table.model()
            ans = ''
            for i, index in enumerate(indexes):
                ans += model.data(index)
                if (i+1)%nb_column == 0:
                    ans += row_sep
                else:
                    ans += col_sep
            return ans


    def keyPressEvent(self, ev):
        if type(ev)==QtGui.QKeyEvent:
            if ev.matches(QtGui.QKeySequence.Copy):
                app = QtWidgets.QApplication.instance()
                app.clipboard().setText(self.get_selection_str())
                ev.accept()
            if ev.matches(QtGui.QKeySequence.Save):
                filename, other = QtWidgets.QFileDialog.getSaveFileName(None, 'Save this table to...', '', 'Comma Separated Value (*.csv)')
                if filename:
                    df = self.df_table.model()._data
                    df.to_csv(path_or_buf=filename, sep=',')
                ev.accept()


## This model was found here: https://stackoverflow.com/questions/31475965/fastest-way-to-populate-qtableview-from-pandas-data-frame
class PandasModel(QtCore.QAbstractTableModel):
    """
    Class to populate a table view with a pandas dataframe
    """
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None


def main():
    w = DataExplorer()
    w.show()
    return w


if __name__ == '__main__':
    from spyre.widgets.spyre_widget import SpyreApp
    app = SpyreApp([])
    w = main()
    app.exec_()
