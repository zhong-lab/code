from collections import OrderedDict

from lantz.messagebased import Driver
from lantz import Feat, DictFeat, Action

import numpy as np

import time

class TestDriver(Driver):

    values = OrderedDict([
        ('High', 100),
        ('Med', 20),
        ('Lo', -20),
    ])

    restriction = set([
        42,
        100,
        1024,
    ])

    def __init__(self, resource):
        if resource is None:
            raise RuntimeError('invalid resource')
        self.resource = resource
        self.settable_value = 42
        self.valued_value = -20
        self.restricted_value = 1024
        self.settable_dictvalue = {'a': 'd', 'b': 'c'}
        self.valued_settable_dictvalue = {'a': 'd', 'b': 'c'}
        self.snr = 5
        return

    def initialize(self):
        pass

    def finalize(self):
        pass

    @Feat(units='V')
    def ro_feat(self):
        return np.random.exponential(5)

    @Feat(units='V/m')
    def feat(self):
        return self.settable_value

    @feat.setter
    def feat(self, value):
        self.settable_value = value
        return

    @Feat(units='V/m', limits=(-100, 100))
    def limited_feat(self):
        return self.settable_value

    @limited_feat.setter
    def limited_feat(self, value):
        self.settable_value = value

    @Feat(values=values)
    def valued_feat(self):
        return self.valued_value

    @valued_feat.setter
    def valued_feat(self, value):
        self.valued_value = value

    @Feat(values=restriction)
    def restricted_feat(self):
        return self.restricted_value

    @restricted_feat.setter
    def restricted_feat(self, value):
        self.restricted_value = value

    @Feat()
    def delayed_feat(self):
        time.sleep(1)
        return self.settable_value

    @delayed_feat.setter
    def delayed_feat(self, value):
        time.sleep(1)
        self.settable_value = value

    @DictFeat()
    def dictfeat(self, key):
        return self.settable_dictvalue[key]

    @dictfeat.setter
    def dictfeat(self, key, value):
        print('setting {} to {}'.format(key, value))
        self.settable_dictvalue[key] = value
        return

    @DictFeat(keys={1: 'a', 2: 'b'}, values={3: 'c', 4: 'd'})
    def valued_dictfeat(self, key):
        return self.valued_settable_dictvalue[key]

    @valued_dictfeat.setter
    def valued_dictfeat(self, key, value):
        print('setting {} to {}'.format(key, value))
        self.valued_settable_dictvalue[key] = value
        return

    @Feat()
    def xy(self):
        time.sleep(0.05)
        now = time.time()
        x = np.cos(now) * self.snr
        y = np.sin(now) * self.snr
        x_noise, y_noise = np.random.normal(size=2)
        return x + x_noise, y + y_noise

    @Feat()
    def signal_to_noise(self):
        return self.snr

    @signal_to_noise.setter
    def signal_to_noise(self, snr):
        self.snr = snr
