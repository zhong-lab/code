from PyQt5 import QtCore
import pandas as pd
from lantz import Q_

class Dataset(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.data = pd.DataFrame()
        self._parameters = dict()
        self.index = 0
        return

    @property
    def parameters(self):
        return self._parameters

    def add_row(self, values):
        formatted_row = {k: [v.magnitude] if isinstance(v, Q_) else [v] for k, v in values.items()}
        pd_row = pd.DataFrame(formatted_row, index=[self.index])
        self.data = pd.concat([self.data, pd_row])
        self.index += 1
        return

    def get_frame_copy(self, deep=True):
        return self.data.copy(deep=deep)

    def clear(self):
        self.data.drop(self.data.index, inplace=True)
        self.index = 0
        return
