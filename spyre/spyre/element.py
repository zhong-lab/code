from PyQt5 import QtCore, QtWidgets

from functools import partial, wraps, update_wrapper

class ElementEvent(object):

    def __init__(self, instance, widget, *args):
        self.instance = instance
        self.widget = widget
        self.event_args = args
        return

class ElementDecorator(object):

    def __init__(self, decor, instance):
        self.decor = decor
        self.instance = instance
        return

    def __call__(self, *args, **kwargs):
        return self.decor(self.instance, *args, **kwargs)

    def __getattr__(self, key):
        return getattr(self.decor, key)

    def __repr__(self):
        return '<bound method {} of {}>'.format(self.decor, type(self))

class ElementWrapper(object):

    _spyre_element = True

    def __init__(self, element_init_func, name=None):
        self.element_init_func = element_init_func
        update_wrapper(self, element_init_func)
        self.ons = dict()
        self.widget = None
        self.name = element_init_func.__name__ if name is None else name
        return

    def get_on_handler(self, signal, func, instance, force_process_all=False):
        app = QtWidgets.QApplication.instance()
        def handler(*args):
            if not force_process_all:
                signal.disconnect(handler)
            ev = ElementEvent(instance, self.widget, *args)
            func(instance, ev)
            if not force_process_all:
                app.processEvents()
                signal.connect(handler)
            return
        signal.connect(handler)
        return

    def on(self, trigger, force_process_all=False):
        def inner(func):
            def deferred(instance):
                nonlocal trigger
                if isinstance(trigger, str):
                    trigger = getattr(self.widget, trigger)
                self.get_on_handler(trigger, func, instance, force_process_all=force_process_all)
                return
            self.ons[trigger] = deferred
            return func
        return inner

    def __call__(self, instance, *args, **kwargs):
        if self.widget is not None:
            w = self.widget
        else:
            w = self.element_init_func(instance)
            self.widget = w
            for trigger, deferred in self.ons.items():
                deferred(instance)
        return w

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return ElementDecorator(self, instance)

    def save_state(self):
        if issubclass(self.widget.__class__, Element_QWidget):
            return self.widget.save_state()
        else:
            return None

    def load_state(self, state):
        if issubclass(self.widget.__class__, Element_QWidget):
            return self.widget.load_state(state)

class Element(object):

    def __init__(self, name=None):
        self.name = name
        return

    def __call__(self, element_init_func):
        wrapper = ElementWrapper(element_init_func, name=self.name)
        return wrapper



class Element_QWidget(QtWidgets.QWidget):

    # Subclasses can overwrite these two methods to save/load information upon closing/openning
    def save_state(self):
        return None
    def load_state(self, state):
        pass