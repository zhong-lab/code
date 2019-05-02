from PyQt5 import QtCore, QtWidgets
import inspect

from spyre.dataset import Dataset

pyqtWrapperType = type(QtCore.QObject)

class SpyreletMeta(pyqtWrapperType):

    def __new__(cls, class_name, bases, class_dict):
        element_names = set()
        task_names = set()
        requires = dict()
        requires_spyrelet = dict()
        for key, value in class_dict.items():
            if key == 'requires':
                requires = value
            if key == 'requires_spyrelet':
                requires_spyrelet = value
            if hasattr(value, '_spyre_element'):
                element_names.add(key)
            if hasattr(value, '_spyre_task'):
                task_names.add(key)

        class_dict['element_names'] = element_names
        class_dict['task_names'] = task_names
        class_dict['requires'] = requires
        class_dict['requires_spyrelet'] = requires_spyrelet
        return super().__new__(cls, class_name, bases, class_dict)

class Spyrelet(QtCore.QObject, metaclass=SpyreletMeta):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.dataset = Dataset()
        self._instruments = dict()
        self._spyrelets = dict()
        self.runnable = False if self.requires else True
        return

    def __getattr__(self, key):
        try:
            value = super().__getattr__(key)
        except AttributeError:
            combined = dict()
            combined.update(self.instruments)
            combined.update(self.spyrelets)
            value = combined[key]
        return value

    @property
    def spyrelets(self):
        return self._spyrelets

    @spyrelets.setter
    def spyrelets(self, _spyrelets):
        new_spyrelets = dict()
        for name, spyrelet_type in self.requires_spyrelet.items():
            try:
                spyrelet_inst = _spyrelets[name]
            except KeyError:
                raise SpyreletRequirementException(
                    "no spyrelet satisfying '{}' found".format(name)
                )
            if not isinstance(spyrelet_inst, spyrelet_type):
                raise SpyreletRequirementException(
                    "spyrelet type '{}' needed for '{}'; received '{}'".format(
                        spyrelet_type.__name__, name, type(spyrelet_inst).__name__,
                    )
                )
            new_spyrelets[name] = spyrelet_inst
        self._spyrelets = new_spyrelets
        self.runnable = True
        return

    @property
    def instruments(self):
        return self._instruments

    @instruments.setter
    def instruments(self, _instruments):
        instrs = dict()
        for name, instrument_type in self.requires.items():
            try:
                instr_inst = _instruments[name]
            except KeyError:
                raise InstrumentRequirementException(
                    "no instrument satisfying '{}' found".format(name)
                )
            if not isinstance(instr_inst, instrument_type):
                raise InstrumentRequirementException(
                    "instrument type '{}' needed for '{}'; received '{}'".format(
                        instrument_type.__name__, name, type(instr_inst).__name__,
                    )
                )
            instrs[name] = instr_inst
        self._instruments = instrs
        self.runnable = True
        return

    def element(self, f):
        e = Element()
        e(f)
        self.element_names.add(f.__name__)
        return e

    @property
    def elements(self):
        return {element_name: getattr(self, element_name) for element_name in self.element_names}

    @property
    def tasks(self):
        return {task_name: getattr(self, task_name) for task_name in self.task_names}

    @QtCore.pyqtSlot(int, int, object, float)
    def progressed(self, depth, n, total, elapsed):
        return

    @QtCore.pyqtSlot(object)
    def acquire(self, value):
        task = self.sender()
        self.dataset.add_row(value)
        task.acquired.emit(value)
        return

    @property
    def data(self):
        return self.dataset.data

    def __repr__(self):
        rep = "<Spyrelet '{}' (running: {})>".format(self.__class__.__name__, self.runnable)
        return rep

class InstrumentRequirementException(Exception):
    pass

class SpyreletRequirementException(Exception):
    pass
