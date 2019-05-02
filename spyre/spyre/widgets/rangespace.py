from PyQt5 import QtWidgets
import pyqtgraph as pg
import numpy as np
from collections import OrderedDict

from lantz import Q_
import inspect

from .spinbox import SpinBox
from collections import OrderedDict
import yaml


def arange(start, stop, step, dtype=None):
    return np.arange(start, stop, step, dtype=dtype)

class RangeDict(dict):
    FUNCS = {'linspace':np.linspace, 'arange':arange, 'logspace':np.logspace}

    def __init__(self, **initial_dict):
        self._verify_valid(initial_dict)
        dict.__setitem__(self, 'func', initial_dict.pop('func'))
        for k in initial_dict:
            self[k] = initial_dict[k]

    def _verify_valid(self, d):
        # Make sure there is a valid func argument
        if not 'func' in d or d['func'] not in self.FUNCS:
            raise ValueError('RangeDict must have a element <func> in: {}'.format(self.FUNCS.keys()))
        
        # Make sure all required args are define
        signature = inspect.signature(self.FUNCS[d['func']])
        for param in signature.parameters.keys():
            if signature.parameters[param].default == inspect._empty and not param in d:
                raise ValueError('RangeDict does not define required <{}> argument'.format(param))

    def __setitem__(self, key, val):
        if key == 'func':
            raise KeyError('Cannot redefine the func, you should reinstanciate with new parametters')
        elif key in inspect.signature(self.FUNCS[self['func']]).parameters:
            return dict.__setitem__(self, key, val)

    @property
    def array(self):
        d = self.copy()
        func_name = d.pop('func')
        units = None
        for p in d:
            if type(d[p])==Q_:
                if units is None:
                    units = d[p].units
                d[p] = d[p].to(units).m
        if units is None or units == Q_(1, 'dimensionless').units:
            return self.FUNCS[func_name](**d)
        else:
            return self.FUNCS[func_name](**d)*units


def represent_rangedict(dumper, val):
    return dumper.represent_mapping(u'!RangeDict', dict(val))

def construct_rangedict(loader, node):
    return RangeDict(**loader.construct_mapping(node))

yaml.add_representer(RangeDict, represent_rangedict)
yaml.add_constructor(u'!RangeDict', construct_rangedict)


class Rangespace(QtWidgets.QWidget):
    def __init__(self, units=None, parent=None, default=None):
        super().__init__(parent=parent)
        if units is None:
            units = 'dimensionless'
        self.units = units
        self.params_layout = QtWidgets.QStackedLayout()
        self.generate_range_widgets(units=units)
        self.range_func_combo = pg.ComboBox(items=list(self.range_widgets.keys()))
        self.range_func_combo.currentIndexChanged[str].connect(self.set_widget)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Function', self.range_func_combo)
        select = QtWidgets.QWidget()
        select.setLayout(layout)
        params = QtWidgets.QWidget()
        params.setLayout(self.params_layout)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(select)
        layout.addWidget(params)
        self.setLayout(layout)
        if not default is None:
            self.set(default)

    def get(self):
        func = self.range_func_combo.value()
        params = self.range_widgets[func].get()
        params['func'] = func
        return RangeDict(**params)

    def set(self, rangedict):
        d = RangeDict(**rangedict)
        func = d.pop('func')
        self.range_func_combo.setValue(func)
        fields = self.range_widgets[func].setter_methods.keys()
        for name in d:
            if not name in fields:
                d.pop(name)
        self.range_widgets[func].set(**d)

    def set_widget(self, name):
        self.params_layout.setCurrentWidget(self.range_widgets[name])

    def generate_range_widgets(self, units=None):
        self.range_widgets = OrderedDict()
        from spyre.widgets.param_widget import ParamWidget
        def add(name, params):
            self.range_widgets[name] = ParamWidget(params)
            self.params_layout.addWidget(self.range_widgets[name])

        f_param = lambda default:   {
                                    'type': float,
                                    'units': units,
                                    'default':default,
                                    }
        i_param_dimless = lambda default:   {
                                                'type': int,
                                                'default':default,
                                                'positive': True,
                                            }
        i_param = lambda default:   {
                                        'type': int,
                                        'default':default,
                                        'units':units,
                                    }

        default_val = 1 if units is None else Q_(1, units).to_base_units().m

        params = [
            ('start', f_param(0)),
            ('stop',  f_param(default_val)),
            ('num', i_param_dimless(10)),
            ('endpoint', {'type':bool, 'default':True})
        ]
        add('linspace', params)

        params = [
            ('start', i_param(0)),
            ('stop', i_param(10*int(default_val))),
            ('step', i_param(1))
        ]
        add('arange', params)

        params = [
            ('start', f_param(default_val)),
            ('stop', f_param(10*default_val)),
            ('num', i_param_dimless(10))
        ]
        add('logspace', params)

if __name__ == '__main__':
    main()
