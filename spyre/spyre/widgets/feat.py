from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
from lantz import Q_
from collections import OrderedDict, Iterable

from .lineedit import LineEdit
from .spinbox import SpinBox

class BaseFeatItemWidget(QtWidgets.QWidget):

    set_requested = QtCore.pyqtSignal(object)
    # activated = QtCore.pyqtSignal(object)
    activated = QtCore.pyqtSignal()
    refreshed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.value_display)
        self.value_display.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        go_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogOkButton)
        self.go_button = QtWidgets.QPushButton()
        self.go_button.setIcon(go_icon)
        read_icon = self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        self.read_button = QtWidgets.QPushButton()
        self.read_button.setIcon(read_icon)
        layout.addWidget(self.go_button)
        layout.addWidget(self.read_button)
        self.go_button.clicked.connect(self.activated)
        self.read_button.clicked.connect(self.refreshed)
        self.set_requested.connect(self.setter)
        self.setLayout(layout)
        return
        
    def set_readonly(self, readonly):
        if readonly:
            self.value_display.setEnabled(False)
            self.go_button.setEnabled(False)
        else:
            self.value_display.setEnabled(True)
            self.go_button.setEnabled(True)
        return

class SpinBoxFeatItemWidget(BaseFeatItemWidget):

    def __init__(self, opts=None, parent=None):
        if opts is None:
            opts = dict()
        self.value_display = SpinBox(**opts)
        super().__init__(parent=parent)
        return

    def setter(self, value):
        if isinstance(value, Q_):
            value = value.magnitude
        self.value_display.setValue(value)
        return

    def getter(self):
        return self.value_display.value()

class ComboBoxFeatItemWidget(BaseFeatItemWidget):

    def __init__(self, values, parent=None):
        self.values = values
        self.value_display = pg.ComboBox()
        if isinstance(self.values, OrderedDict):
            for key, value in self.values.items():
                self.value_display.addItem(str(key), str(value))
        elif isinstance(self.values, dict):
            for key, value in sorted(self.values.items()):
                self.value_display.addItem(str(key), str(value))
        elif isinstance(self.values, set):
            for value in sorted(self.values):
                self.value_display.addItem(str(value), str(value))
        elif isinstance(self.values, Iterable):
            for value in self.values:
                self.value_display.addItem(str(value), str(value))
        else:
            raise TypeError('invalid type encountered while populating values')
        super().__init__(parent=parent)
        return

    def setter(self, value):
        index = self.value_display.findText(str(value))
        self.value_display.setCurrentIndex(index)
        return

    def getter(self):
        index = self.value_display.currentIndex()
        values = self.values
        if isinstance(values, OrderedDict):
            key = list(values.keys())[index]
        elif isinstance(values, dict):
            key = list(sorted(values.keys()))[index]
        elif isinstance(values, set):
            key = list(sorted(values))[index]
        else:
            key = values[index]
        return key

class LineEditFeatItemWidget(BaseFeatItemWidget):

    def __init__(self, parent=None):
        self.value_display = QtWidgets.QLineEdit()
        super().__init__(parent=parent)
        return

    def setter(self, value):
        self.value_display.setText(str(value))
        return

    def getter(self):
        value = self.value_display.text()
        return value
