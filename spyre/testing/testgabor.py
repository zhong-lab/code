import numpy as np
import os
import pyqtgraph as pg
import time
import csv
import sys
import numpy as np
import os
from warnings import warn
from nsgt import NSGT_sliced, LogScale, LinScale, MelScale, OctScale
from argparse import ArgumentParser
import matplotlib.pyplot as pl

parser = ArgumentParser()
parser.add_argument("input", type=str, help="Input file")
parser.add_argument("--output", type=str, help="Output data file (.npz, .hd5, .pkl)")
parser.add_argument("--sr", type=int, default=44100, help="Sample rate used for the NSGT (default=%(default)s)")
parser.add_argument("--data-times", type=str, default='times', help="Data name for times (default='%(default)s')")
parser.add_argument("--data-frqs", type=str, default='f', help="Data name for frequencies (default='%(default)s')")
parser.add_argument("--data-qs", type=str, default='q', help="Data name for q factors (default='%(default)s')")
parser.add_argument("--data-coefs", type=str, default='coefs', help="Data name for coefficients (default='%(default)s')")
parser.add_argument("--fps", type=float, default=0, help="Approx. time resolution for features in fps (default=%(default)s)")
parser.add_argument("--fps-pooling", choices=('max','mean','median'), default='max', help="Temporal pooling function for features (default='%(default)s')")
parser.add_argument("--fmin", type=float, default=50, help="Minimum frequency in Hz (default=%(default)s)")
parser.add_argument("--fmax", type=float, default=22050, help="Maximum frequency in Hz (default=%(default)s)")
parser.add_argument("--scale", choices=('oct','log','mel'), default='log', help="Frequency scale oct, log, lin, or mel (default='%(default)s')")
parser.add_argument("--bins", type=int, default=50, help="Number of frequency bins (total or per octave, default=%(default)s)")
parser.add_argument("--mag-scale", choices=('dB','log'), default='dB', help="Magnitude scale dB or log (default='%(default)s')")
parser.add_argument("--sllen", type=int, default=2**20, help="Slice length in samples (default=%(default)s)")
parser.add_argument("--trlen", type=int, default=2**18, help="Transition area in samples (default=%(default)s)")
parser.add_argument("--real", action='store_true', help="Assume real signal")
parser.add_argument("--matrixform", action='store_true', help="Use regular time division over frequency bins (matrix form)")
parser.add_argument("--reducedform", type=int, default=0, help="If real, omit bins for f=0 and f=fs/2 (--reducedform=1), or also the transition bands (--reducedform=2) (default=%(default)s)")
parser.add_argument("--recwnd", action='store_true', help="Use reconstruction window")
parser.add_argument("--multithreading", action='store_true', help="Use multithreading")
parser.add_argument("--downmix-after", action='store_true', help="Downmix signal after spectrogram generation")
parser.add_argument("--plot", action='store_true', help="Plot transform (needs installed matplotlib package)")

args = parser.parse_args()
if not os.path.exists(args.input):
    parser.error("Input file '%s' not found"%args.input)

fs = args.sr
scales = {'log':LogScale, 'lin':LinScale, 'mel':MelScale, 'oct':OctScale}
try:
    scale = scales[args.scale]
except KeyError:
    parser.error('Scale unknown (--scale option)')

scl = scale(args.fmin, args.fmax, args.bins, beyond=int(args.reducedform == 2))
slicq = NSGT_sliced(scl, args.sllen, args.trlen, fs, 
                    real=args.real, recwnd=args.recwnd, 
                    matrixform=args.matrixform, reducedform=args.reducedform, 
                    multithreading=args.multithreading,
                    multichannel=True
                    )

signal = np.genfromtxt(args.input, delimiter=',')[:,1]

print(np.shape(signal))
dur = signal.size/float(fs)
ncoefs = int(signal.size*slicq.coef_factor)
c = slicq.forward(signal)
coefs = assemble_coeffs(c, ncoefs)
fs_coef = fs*slicq.coef_factor
mls_dur = len(mls)/fs_coef
times = np.linspace(0, mls_dur, endpoint=True, num=len(mls)+1)
mls_max = np.percentile(mls, 99.9)
pl.imshow(mls.T, aspect=mls_dur/mls.shape[1]*0.2, interpolation='nearest', origin='bottom', vmin=mls_max-60., vmax=mls_max, extent=(0,mls_dur,0,mls.shape[1]))
pl.show()