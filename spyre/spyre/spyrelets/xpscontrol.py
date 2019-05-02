from itertools import count

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.widgets.param_widget import ParamWidget

from lantz.drivers.newport import XPSQ8
from lantz.drivers.microsoft import XInputController

class XPSControlSpyrelet(Spyrelet):

    requires = {
        'xps': XPSQ8,
        'xbox': XInputController,
    }

    def qtz(self, val, divs=5):
        return int(val * divs) / divs

    @Task()
    def xbox_move(self, **kwargs):

        axis_names = ['Group{}.Pos'.format(num) for num in range(1, 4)]
        axis_name = {
            'X': axis_names[0],
            'x': axis_names[0],
            'Y': axis_names[1],
            'y': axis_names[1],
            'Z': axis_names[2],
            'z': axis_names[2],
        }

        params = self.xbox_parameters.widget.get()
        x_step = params['x speed']
        y_step = params['y speed']
        z_step = params['z speed']
        accel = params['acceleration']

        def axis_event(axis, value):
            qtz_vector = self.qtz(value)
            if axis not in {'l_thumb_x', 'l_thumb_y', 'left_trigger', 'right_trigger'}:
                return
            if axis == 'l_thumb_x':
                # reverse x direction
                self.xps.jog(axis_name['x'], -x_step * qtz_vector, accel)
            elif axis == 'l_thumb_y':
                self.xps.jog(axis_name['y'], y_step * qtz_vector, accel)
            elif axis == 'left_trigger':
                self.xps.jog(axis_name['z'], -z_step * qtz_vector, accel)
            elif axis == 'right_trigger':
                self.xps.jog(axis_name['z'], z_step * qtz_vector, accel)
            return

        self.dataset.clear()
        self.xbox.set_axis_callback(axis_event)

        for iteration in self.xbox_move.progress(count()):
            self.xbox.dispatch_events()
            self.xbox_move.acquire({})
        return

    @xbox_move.initializer
    def initialize(self):
        return

    @xbox_move.finalizer
    def finalize(self):
        return
        
    @Element(name='xbox controller parameters')
    def xbox_parameters(self):
        params = [
            ('x speed', {
                'type': float,
                'default': 0.1,
            }),
            ('y speed', {
                'type': float,
                'default': 0.1,
            }),
            ('z speed', {
                'type': float,
                'default': 0.005,
            }),
            ('acceleration', {
                'type': float,
                'default': 10.0,
            })
        ]
        w = ParamWidget(params)
        return w
