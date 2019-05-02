from lantz.drivers.ni.daqmx import DigitalOutputTask, DigitalOutputChannel
import numpy as np

class DigitalSwitch(object):

    def __init__(self, ch='/dev1/port0/line0'):
        super().__init__()
        self.task = DigitalOutputTask()
        output_channel = DigitalOutputChannel(ch)
        self.task.add_channel(output_channel)
        clock_config = {
            'source': 'OnboardClock',
            'rate': 10000,
            'sample_mode': 'finite',
            'samples_per_channel': 100,
        }
        self.task.configure_timing_sample_clock = clock_config
        self._state = False
        return

    def __del__(self):
        self.task.clear()
        return

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, _state):
        if _state:
            state_pts = np.ones(100)
        else:
            state_pts = np.zeros(100)
        with self.task as task:
            self.task.write(state_pts)
        self._state = _state
        return
