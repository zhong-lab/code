import inspect

from PyQt5 import QtCore

from lantz.feat import MISSING, Feat, DictFeat

class BaseFeatItem(QtCore.QObject):

    def __init__(self, featproxy, parent=None):
        super().__init__(parent=parent)
        self.instance = featproxy.instance
        self.name = featproxy.name
        self.readonly = featproxy.feat.fset is None

        modifiers = list(featproxy.modifiers.items())
        properties = modifiers[0][1][MISSING]
        self.limits = properties.get('limits')
        self.units = properties.get('units')
        self.keys = properties.get('keys')
        self.values = properties.get('values')

        changed_signal_name = '{}_changed'.format(self.name)
        self.changed = getattr(self.instance, changed_signal_name)

        return

class FeatItem(BaseFeatItem):

    set_requested = QtCore.pyqtSignal([object], [object, dict])

    def __init__(self, featproxy, parent=None):
        super().__init__(featproxy, parent=parent)
        self._set = featproxy.set
        self._get = featproxy.get
        self.set_requested.connect(self.setter)
        return

    @QtCore.pyqtSlot(object)
    @QtCore.pyqtSlot(object, dict)
    def setter(self, value, kwargs=dict()):
        if not self.readonly:
            self._set(self.instance, value, **kwargs)
        return

    @QtCore.pyqtSlot()
    @QtCore.pyqtSlot(dict)
    def getter(self, kwargs=dict()):
        value = self._get(self.instance, **kwargs)
        return value

class DictFeatItem(BaseFeatItem):

    set_requested = QtCore.pyqtSignal([object, object], [object, object, dict])

    def __init__(self, featproxy, parent=None):
        super().__init__(featproxy, parent=parent)
        self._setitem = featproxy.setitem
        self._getitem = featproxy.getitem
        self.set_requested.connect(self.setter)
        return

    @QtCore.pyqtSlot(object, object)
    @QtCore.pyqtSlot(object, object, dict)
    def setter(self, key, value, kwargs=dict()):
        if not self.readonly:
            self._setitem(self.instance, key, value, **kwargs)
        return

    @QtCore.pyqtSlot(object)
    @QtCore.pyqtSlot(object, dict)
    def getter(self, key, kwargs=dict()):
        value = self._getitem(self.instance, key, **kwargs)
        return value

class ActionItem(QtCore.QObject):

    def __init__(self, actionproxy, parent=None):
        super().__init__(parent=parent)
        self.name = actionproxy.action.name
        self._call = actionproxy.action.call
        self.instance = actionproxy.instance
        self.signature = inspect.getargspec(actionproxy.action.call)
        return

    def call(self, *args, **kwargs):
        self._call(self.instance, *args, **kwargs)
        return

class Instrument(QtCore.QObject):

    def __init__(self, driver, *resource, alias=None, parent=None):
        super().__init__(parent=parent)

        self.feats = dict()
        self.actions = dict()

        self._driver_class = driver
        self._driver = repr(driver).split("'")[1]
        self._instance = None
        self.resource = resource
        if alias is None:
            alias = ''
        self.alias = alias

        self.feats = self.get_feats()
        self.actions = self.get_actions()
        return

    @property
    def driver(self):
        return self._driver

    @property
    def driver_class(self):
        return self._driver_class

    @property
    def instance(self):
        return self._instance

    @property
    def resource(self):
        return self._resource

    @resource.setter
    def resource(self, _resource):
        if self._instance is not None:
            self._instance.finalize()
        try:
            instance = self._driver_class(*_resource)
            instance.initialize()
            self._resource = _resource
        except Exception as e:
            instance = self._instance
            if instance is not None:
                instance.initialize()
        finally:
            self._instance = instance
        return

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, _alias):
        self._alias = _alias
        return

    def get_feats(self):
        feats = dict()
        for feat_name, featproxy in sorted(self.instance.feats.items()):
            if isinstance(featproxy.feat, DictFeat):
                feat_item = DictFeatItem(featproxy)
            elif isinstance(featproxy.feat, Feat):
                feat_item = FeatItem(featproxy)
            else:
                continue
            feats[feat_name] = feat_item
        return feats

    def get_actions(self):
        exclude = {
            'initialize',
            'finalize',
        }
        actions = dict()
        for action_name, actionproxy in sorted(self.instance.actions.items()):
            if action_name not in exclude:
                action_item = ActionItem(actionproxy)
                actions[action_name] = action_item
        return actions
