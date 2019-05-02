import importlib

from PyQt5 import QtCore
from lantz.driver import _DriverType

from .spyrelet import Spyrelet
from .persist import Persister

class Spyre(QtCore.QObject):

    spyrelet_added = QtCore.pyqtSignal(object)
    spyrelet_removed = QtCore.pyqtSignal(int)

    instrument_added = QtCore.pyqtSignal(object)
    instrument_removed = QtCore.pyqtSignal(int)

    def add_spyrelet(self, spyrelet_cls):
        pass

    def remove_spyrelet(self, spyrelet_name, index=None):
        pass

    def add_instrument(self, instr_cls, resource, alias=None):
        pass

    def remove_instrument(self, instrument, index=None):
        pass

#
# class Spyre(QtCore.QObject):
#
#     spyrelet_added = QtCore.pyqtSignal(str, object)
#     spyrelet_removed = QtCore.pyqtSignal(str)
#
#     def __init__(self, instrument_mediator, parent=None):
#         super().__init__(parent=parent)
#         self.persister = Persister()
#         self.im = instrument_mediator
#         self.spyrelets = dict()
#         self._spyrelet_classes = dict()
#         return
#
#     def add_spyrelet(self, spyrelet_cls):
#         name = spyrelet_cls.name
#         if name in self.spyrelets:
#             print('spyrelet "{}" already loaded...skipping...'.format(name))
#             return
#         spyrelet = spyrelet_cls()
#         self.spyrelets[name] = spyrelet
#         self.spyrelet_added.emit(name, spyrelet.widget)
#         return
#
#     def add_spyrelet(self, spyrelet_cls):
#         name = spyrelet_cls.name
#         if name in self.spyrelets:
#             print('spyrelet "{}" already loaded...skipping...'.format(name))
#             return
#         spyrelet = spyrelet_cls()
#         presenter = spyrelet(self)
#         self.spyrelets[name] = presenter.mediator
#         self._spyrelet_classes[name] = spyrelet_cls
#         self.spyrelet_added.emit(name, presenter.w)
#         return
#
#
#     def remove_spyrelet(self, spyrelet_name):
#         spyrelet = self.spyrelets.get(spyrelet_name)
#         if spyrelet is not None:
#             spyrelet._finalize()
#             self.spyrelet_removed.emit(spyrelet_name)
#             del self.spyrelets[spyrelet_name]
#
#     @property
#     def instruments(self):
#         return self.im.instruments
#
#     def add_instrument(self, driver, resource=None, alias=None):
#         if isinstance(driver, str):
#             driver_path = driver
#         elif isinstance(driver, _DriverType):
#             driver_path = '{}.{}'.format(driver.__module__, driver.__name__)
#         else:
#             print('driver type not recognized...')
#             return
#         self.im.add_instrument(driver_path, resource=resource, alias=alias)
#         return
#
#     def add_instrument(self, driver, resource=None, alias=None):
#         self.im.add_instrument(driver, resource=resource, alias=alias)
#         return
#
#     def remove_instrument(self, index):
#         self.im.remove_instrument(index=index)
#         return
#
#     def save_config(self):
#         instrument_entries = list()
#         for instrument in self.instruments:
#             entry = {
#                 'driver_name': instrument.driver,
#                 'resource': instrument.resource,
#                 'alias': instrument.alias,
#             }
#             instrument_entries.append(entry)
#
#
#         spyrelet_entries = list()
#         for spyrelet_name, spyrelet in self._spyrelet_classes.items():
#             entry = {
#                 'name': spyrelet_name,
#                 'spyrelet': '.'.join((spyrelet.__module__, spyrelet.__qualname__)),
#             }
#             spyrelet_entries.append(entry)
#
#         self.persister.config['instruments'] = instrument_entries
#         self.persister.config['spyrelets'] = spyrelet_entries
#         self.persister.dump()
#         return
#
#     def load_config(self):
#         instrument_entries = self.persister.config.get('instruments', list())
#         for instrument_entry in instrument_entries:
#             driver_path = instrument_entry['driver_name']
#             resource = instrument_entry['resource']
#             alias = instrument_entry['alias']
#             mod_path, class_name = driver_path.rsplit('.', 1)
#             mod = importlib.import_module(mod_path)
#             klass = getattr(mod, class_name)
#             self.add_instrument(klass, resource, alias)
#
#         spyrelet_entries = self.persister.config.get('spyrelets', list())
#         for spyrelet_entry in spyrelet_entries:
#             spyrelet_name = spyrelet_entry['name']
#             spyrelet_path = spyrelet_entry['spyrelet']
#             mod_path, class_name = spyrelet_path.rsplit('.', 1)
#             mod = importlib.import_module(mod_path)
#             klass = getattr(mod, class_name)
#             self.add_spyrelet(klass)
#         return
