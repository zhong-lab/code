from collections import Iterable

from PyQt5 import QtWidgets, QtGui
import pyqtgraph as pg

from ..instrument import FeatItem, DictFeatItem, ActionItem
from .feat import *

class BaseItemWidget(QtWidgets.QWidget):

    def __init__(self, item, refresh_rate=1.0, parent=None):
        super().__init__(parent=parent)
        self.refresh_rate = refresh_rate
        self.item = item
        return

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, _item):
        self._item = _item
        self.init_ui()
        return

class FeatItemWidget(BaseItemWidget):

    def init_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        value = self.item.getter()
        values = self.item.values
        if values is not None:
            self.value_display = ComboBoxFeatItemWidget(values)
        elif isinstance(value, bool):
            self.value_display = ComboBoxFeatItemWidget({True, False})
        # elif isinstance(value, Iterable):
        #     pass
        elif isinstance(value, (int, float, Q_)):
            opts = dict()
            if self.item.units is not None:
                opts['unit'] = self.item.units
            if self.item.limits is not None:
                opts['bounds'] = self.item.limits
            opts['dec'] = True
            opts['minStep'] = 1e-3
            opts['decimals'] = 5
            if isinstance(value, int):
                opts['int'] = True
                opts['minStep'] = 1
                opts['decimals'] = 10
            self.value_display = SpinBoxFeatItemWidget(opts)
        else:
            self.value_display = LineEditFeatItemWidget()

        self.value_display.activated.connect(self.feat_update)
        self.value_display.refreshed.connect(self.feat_reload)
        self.changed_proxy = pg.SignalProxy(self.item.changed,
                                            rateLimit=self.refresh_rate,
                                            slot=self.feat_changed)
        self.value_display.setter(value)

        self.value_display.set_readonly(self.item.readonly)

        layout.addWidget(self.value_display)
        self.setLayout(layout)
        return

    @QtCore.pyqtSlot(object)
    def feat_changed(self, values):
        new_value, old_value = values
        self.value_display.set_requested.emit(new_value)
        return

    @QtCore.pyqtSlot()
    def feat_update(self):
        value = self.value_display.getter()
        self.item.set_requested.emit(value)
        return
        
    @QtCore.pyqtSlot()
    def feat_reload(self):
        value = self.item.getter()
        self.value_display.set_requested.emit(value)
        return

class DictFeatItemWidget(BaseItemWidget):

    def init_ui(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if self.item.keys is not None:
            self.key_display = ComboBoxFeatItemWidget(self.item.keys)
        else:
            self.key_display = LineEditFeatItemWidget()
        if self.item.values is not None:
            self.value_display = ComboBoxFeatItemWidget(self.item.values)
        else:
            self.value_display = LineEditFeatItemWidget()

        self.key_activated_proxy = pg.SignalProxy(self.key_display.activated,
                                                  rateLimit=self.refresh_rate,
                                                  slot=self.dictfeat_keyupdate)
        self.value_activated_proxy = pg.SignalProxy(self.value_display.activated,
                                                    rateLimit=self.refresh_rate,
                                                    slot=self.dictfeat_update)
        self.changed_proxy = pg.SignalProxy(self.item.changed,
                                            rateLimit=self.refresh_rate,
                                            slot=self.dictfeat_changed)

        self.key_display.set_readonly(self.item.readonly)
        self.value_display.set_readonly(self.item.readonly)

        layout.addWidget(self.key_display)
        layout.addWidget(self.value_display)
        self.setLayout(layout)
        return

    @QtCore.pyqtSlot(object)
    def dictfeat_changed(self, args):
        new_value, old_value, etc = args
        key = etc['key']
        if self.key_display.getter() == key:
            self.value_display.set_requested.emit(new_value)
        return

    @QtCore.pyqtSlot()
    def dictfeat_keyupdate(self):
        key = self.key_display.getter()
        value = self.item.getter(key)
        self.value_display.setter(value)
        return

    @QtCore.pyqtSlot()
    def dictfeat_update(self):
        key = self.key_display.getter()
        value = self.value_display.getter()
        self.item.set_requested.emit(key, value)
        return

class ActionItemWidget(QtWidgets.QWidget):

    def __init__(self, item, parent=None):
        super().__init__(parent=parent)
        self.item = item
        return

    @property
    def item(self):
        return self._item

    @item.setter
    def item(self, _item):
        self._item = _item
        self.init_ui()
        return

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.call_button = QtWidgets.QPushButton('execute {}'.format(self.item.name))
        layout.addWidget(self.call_button)
        self.call_button.clicked.connect(self.toggle_call)
        self.setLayout(layout)
        return

    def toggle_call(self):
        self.item.call()
