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

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from scipy.signal import spectrogram 
from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time
import subprocess

from lantz.drivers.gwinstek.g3303s import GPD3303S
from lantz.drivers.thorlabs.pm100d import PM100D
from numpy.fft import fft

#import thorlabs_apt as apt
import time

class FiberPulling(Spyrelet):
	xs = []
	ys = []

	requires = {
		'pmd': PM100D
	}

	@Task()
	def Pull(self):
		#os.system('python process.py')

		# display motors and assign them to Motor objects
		import thorlabs_apt as apt
		elements = apt.list_available_devices()
		serials = [x[1] for x in elements]
		serial1 = serials[0]
		serial2 = serials[1]
		print('\n')
		print("Present motor devices:", elements, '\n')

		motor1 = apt.Motor(serial1)
		motor2 = apt.Motor(serial2)

		# home motors
		print("Motor 1 homing parameters:", motor1.get_move_home_parameters())
		print("Motor 2 homing parameters:", motor2.get_move_home_parameters())
		motor1.move_home()
		motor2.move_home()
		print("Homing...\n")

		while (not motor1.has_homing_been_completed or not motor2.has_homing_been_completed):
			continue

		time.sleep(1)
		input("Press any key to start readying")

		# ready motors and then pull on user input
		print("Motor 1 velocity parameters:", motor1.get_velocity_parameters())
		print("Motor 2 velocity parameters:", motor2.get_velocity_parameters())
		motor1.move_to(20)
		motor2.move_to(20)
		print("Readying...\n")

		while (motor1.is_in_motion or motor2.is_in_motion):
			continue

		time.sleep(1)
		input("Press any key to start pulling")

		# pull
		print("Pulling...\n")
		motor1.set_velocity_parameters(0, 0.01, 0.05) #(minimum_velocity, acceleration, maximum_velocity) in mm
		motor2.set_velocity_parameters(0, 0.01, 0.05)
		motor1.move_velocity(2)
		motor1.move_to(10) # move to relative/absolute position
		motor2.move_velocity(2)
		motor2.move_to(10)


		#input("Press any key to stop pulling")

		#motor1.stop_profiled()
		#motor2.stop_profiled()

		#print("motors have stopped")

		t0 = time.time()
		print("Press Enter to stop")

		while True:
			t1 = time.time()
			t = t1 - t0
			self.xs.append(t)
			self.ys.append(self.pmd.power.magnitude * 1000)
			while len(self.xs) != len(self.ys):
				del self.xs[-1]

			if len(self.xs) < len(self.ys):
				offset=len(self.xs)-len(self.ys)
				self.ys = self.ys[offset]
			if len(self.xs) > len(self.ys):
				offset=len(self.ys)-len(self.xs)
				self.xs= self.xs[offset]

			#print(len(self.xs),len(self.ys))


			values = {
				  'x': self.xs,
				  'y': self.ys,
				}
			self.Pull.acquire(values)

			if msvcrt.kbhit():
				if msvcrt.getwche() == '\r':
					motor1.stop_profiled()
					motor2.stop_profiled()
					print("motors have stopped")
					break

			
			time.sleep(0.1)
		return

		
	@Element(name='Histogram')
	def averaged(self):
		p = LinePlotWidget()
		p.plot('Transmission Power')
		return p

	@averaged.on(Pull.acquired)
	def averaged_update(self, ev):
		w = ev.widget
		xs = np.array(self.xs)
		ys = np.array(self.ys)
		if (len(xs)==len(ys)):
			w.set('Transmission Power', xs=xs, ys=ys)
		return

	def initialize(self):
		return

	def finalize(self):
		return

