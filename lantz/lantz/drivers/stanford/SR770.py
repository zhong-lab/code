"""
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	Implementation of SRS900 Mainframe

	Author: Hong Qiao
	Date: 5/13/2021
"""

from lantz import Feat, DictFeat, Action, ureg
from lantz.messagebased import MessageBasedDriver
from time import sleep
from lantz.errors import InstrumentError
from collections import OrderedDict
import sys
import numpy as np
import matplotlib.pyplot as plt
import time

class SR770(MessageBasedDriver):
	"""This is the driver for the Stanford Research Systems DG645."""

	DEFAULTS = {'COMMON': {'write_termination': '\n',
						   'read_termination': '\r\n'}}

	@Feat()
	def idn(self):
		return self.query('*IDN?')
		# return the identification number

	@Action()
	def clear_status(self):
		self.write('*CLS')
		#print('Status cleared')

	@Feat()
	def self_test(self):
	  return self.query('*TST?')

	@Feat()
	def self_standard_event_status(self):
	  return self.query('*ESR?')

	@Feat()
	def read_standard_event_status_register(self):
	  return self.query('*ESR?')

	@Action()
	def reset(self):
	  self.write('*RST')
	  print('System Reset')

	@Action()
	def auto_range(self):
		self.write('ARNG 1')
		return

	@Action()
	def get_trace(self,channel):
		a = self.query('SPEC? {}'.format(channel))
		#b = self.query('BVAL? {}, 1'.format(channel))
		# time.sleep(5)
		#import pdb; pdb.set_trace()
		xmin=np.float(self.query('BVAL? {}, 1'.format(channel)))
		#print(xmin)

		xmax=np.float(self.query('BVAL? {}, 399'.format(channel)))
		#import pdb; pdb.set_trace()
		ydata=np.fromstring(a, dtype=np.float, sep=',')
		# answer=np.array(answer)
		# data=answer[0:][::2]
		return np.linspace(xmin,xmax,400), ydata


	@Action()
	def set_freq(self, start_freq, span):
		#import pdb; pdb.set_trace()
		# print(self.query('SPAN ? {}'.format(span)))
		# print(self.query('STRF ? {}'.format(start_freq)))
		print(self.write('SPAN {}'.format(span)))
		print(self.write('STRF {}'.format(start_freq)))
		return
	@Action()
	def start(self):
		self.write('STRT')
		return


	# @Action()
	# def meas_spectrum(self):
	#   #import pdb; pdb.set_trace()
	#   # print(self.query('SPAN ? {}'.format(span)))
	#   # print(self.query('STRF ? {}'.format(start_freq)))
	#   self.write('MEAS g {,0}')
	#   return
	# @Action()
	# def meas_PSD(self):
	#   #import pdb; pdb.set_trace()
	#   # print(self.query('SPAN ? {}'.format(span)))
	#   # print(self.query('STRF ? {}'.format(start_freq)))
	#   self.write('MEAS g {,1}')
	#   return
	# def curv(self):
	#     """Get data.
	#         Returns:
	#         xdata, ydata as list
	#     """
	#     # self.dataencoding()
	#     # self.write('DATa:STARt 1')
	#     # self.write('DATa:STOP 1500000')
	#     # answer = self.query_ascii('CURV?', delay=0)
	#     # params = self.acqparams()
	#     ydata = self.query_ascii('SPEC? 0')
	#     xdata = self.query_ascii('BVAL? 0')
	#     #print('data',data)    
	#     return xdata,ydata




if __name__ == '__main__':
	from time import sleep
	from lantz import Q_
	from lantz.log import log_to_screen, DEBUG
	# from gpib_ctypes import make_default_gpib
	# make_default_gpib()

	volt = Q_(1, 'V')
	milivolt = Q_(1, 'mV')

	log_to_screen(DEBUG)
	# this is the GPIB Address:
	with SR770('GPIB2::10::INSTR') as inst:
	  print(inst.idn)
	  #inst.reset()
	  #inst.clear_status()
	  #inst.set_freq(10000,17)
	  #inst.meas_PSD()
	  x,y=inst.get_trace(0)
	  #import pdb; pdb.set_trace()
	  x = np.array(x)
	  y = np.array(y)
	  np.savetxt('Q:\\Data\\8.23.21_laser_locking\\yizhong.txt', np.c_[y])
	  np.savetxt('Q:\\Data\\8.23.21_laser_locking\\yizhong_f.txt', np.c_[x])
	  plt.plot(x,y)
	  plt.show()

##combine data in squence i
	  x_full=[]
	  y_full=[]
	  x_max=0

# i span i span
# 0 191 mHz 10 195 Hz
# 1 382 mHz 11 390 Hz
# 2 763 mHz 12 780 Hz
# 3 1.5 Hz 13 1.56 kHz
# 4 3.1 Hz 14 3.125 kHz
# 5 6.1 Hz 15 6.25 kHz
# 6 12.2 Hz 16 12.5 kHz
# 7 24.4 Hz 17 25 kHz
# 8 48.75 Hz 18 50 kHz
# 9 97.5 Hz 19 100 kHz

	#   for i in range(5):
	#       inst.set_freq(x_max,13)
	#       inst.start()
	#       #time.sleep(2)
	#       #inst.auto_range()
	#       time.sleep(5)

	#       x,y=inst.get_trace(0)
	#       #import pdb; pdb.set_trace()
	#       x = np.array(x)
	#       y = np.array(y)
	#       x_full=np.concatenate([x_full,x])
	#       y_full=np.concatenate([y_full,y])
		
		
	#       #plt.plot(x,y)
	#       x_max=max(x)

	#       print(x_max)
	# np.savetxt('Q:\\Data\\8.4.21_laser_locking\\Rp_20kR_t_500k.txt', np.c_[y_full])
	# #np.savetxt('Q:\\Data\\7.18.21_laser_locking\\locked_f.txt', np.c_[x_full])
	#     #import pdb; pdb.set_trace()
	#     #print(x,y)
	# #plt.show()
	# plt.plot(x_full,y_full)
	# plt.show()
	  # v2=inst.SIM970_voltage[1]

	  

