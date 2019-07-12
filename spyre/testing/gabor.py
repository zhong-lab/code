import numpy as np
import os
import pyqtgraph as pg
import time
import csv
import sys
import msvcrt
import matplotlib.pyplot as plt
import threading
from numpy.fft import fft
import matplotlib.animation as anim
from scipy.signal import spectrogram, stft  

# powermatrix = np.genfromtxt('power.csv', delimiter=',')
powermatrix = np.genfromtxt('pull_4.csv', delimiter=',')[:,:-1]
print(np.shape(powermatrix))
fs = 10e5
f, t, Sxx = spectrogram(np.array(powermatrix[:, 1]), fs, ('gaussian', 0.7), 100000)
pg.setConfigOptions(imageAxisOrder='row-major')
pg.mkQApp()
win = pg.GraphicsLayoutWidget()
p1 = win.addPlot()
img = pg.ImageItem()
p1.addItem(img)
hist = pg.HistogramLUTItem()
hist.setImageItem(img)
win.addItem(hist)
win.show()
hist.setLevels(np.min(Sxx), np.max(Sxx))
hist.gradient.restoreState(
        {'mode': 'rgb',
        'ticks': [(0.5, (0, 182, 188, 255)),
                (1.0, (246, 111, 0, 255)),
                (0.0, (75, 0, 113, 255))]})
img.setImage(Sxx)
img.scale(t[-1]/np.size(Sxx, axis=1), f[-1]/np.size(Sxx, axis=0))
p1.setLimits(xMin=0, xMax=t[-1], yMin=0, yMax=f[-1])
p1.setLabel('bottom', "Time", units='s')
p1.setLabel('left', "Frequency", units='Hz')
pg.Qt.QtGui.QApplication.instance().exec_()
