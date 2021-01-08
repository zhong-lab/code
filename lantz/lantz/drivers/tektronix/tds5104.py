# -*- coding: utf-8 -*-
"""
	lantz.drivers.tektronix.tds5104
	~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

	Implements the drivers to control an oscilloscope.
"""

import struct
import matplotlib.pyplot as plt
import numpy as np
import os
import time

from lantz.feat import Feat
from lantz.action import Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class TDS5104(MessageBasedDriver):
	"""Tektronix TDS5104 1 GHz 4 Channel Digital Real-Time Oscilloscope
	"""

	#DEFAULTS = {'COMMON': {'write_termination': '\n', 'read_termination': '\n'}}

	@Action()
	def autoconf(self):
		"""Autoconfig oscilloscope.
		"""
		self.write(':AUTOS EXEC')

	def init(self):
		"""initiate.
		"""
		self.write(':ACQ:STATE ON')
		return "Init"

	@Feat()
	def idn(self):
		"""IDN.
		"""
		return self.query('ID?')

	@Feat()
	def trigger(self):
		"""Trigger state.
		"""
		return self.query(':TRIG:STATE?')

	@trigger.setter
	def trigger(self, typemode):
		"""Set trigger state.
		"""
		self.write('TRIG:MAIN:MODE {}'.format(typemode))

	@Feat()
	def mode(self):
		"""Trigger state.
		"""
		return self.query('ACQ?')

	@Feat()
	def query_chn(self,channel):
		"""Trigger state.
		"""
		return self.query('CH{}?'.format(channel))

	# @mode.setter
	# def mode(self, typemode):
	#     """Set trigger state.
	#     """
	#     temp = ''
	#     if typemode == 'sample':
	#         temp = 'SAM'
	#     elif typemode == 'average':
	#         temp = 'AVE'
	#     elif typemode == 'peak detect':
	#         temp = 'PEAK'
	#     elif typemode == 'envelope':
	#         temp = 'ENV'

	#     if typemode=='':
	#         print('cant set mode. keywords are: sample, average, peak detect, envelope')
	#     else:
	#         self.write('ACQ:MOD {}'.format(temp))

	@Action()
	def triggerlevel(self):
		"""Set trigger level to 50% of the minimum adn maximum
		values of the signal.
		"""
		self.write('TRIG:MAIn SATLevel')

	@Action()
	def setmode(self, typemode):

		temp = ''
		if typemode == 'sample':
			temp = 'SAM'
		elif typemode == 'average':
			temp = 'AVE'
		elif typemode == 'peak detect':
			temp = 'PEAK'
		elif typemode == 'envelope':
			temp = 'ENV'

		if typemode=='':
			print('cant set mode. keywords are: sample, average, peak detect, envelope')
		else:
			self.write('ACQ:MOD {}'.format(temp))

	@Action()
	def forcetrigger(self):
		"""Force trigger event.
		"""
		self.write('TRIG FORCe')

	@Action()
	def datasource(self, chn):
		"""Selects channel.
		"""
		self.write(':DATA:SOURCE CH{}'.format(chn))

	@Action()
	def acqparams(self):
		""" X/Y Increment Origin and Offset.
		"""
		commands = 'XZE?;XIN?;YZE?;YMU?;YOFF?'
		#params = self.query(':WFMPRE:XZE?;XIN?;YZE?;YMU?;YOFF?')
		params = self.query(':WFMPRE:{}'.format(commands))
		params = {k: float(v) for k, v in zip(commands.split(';'), params.split(';'))}
		return params

	@Action()
	def dataencoding(self):
		"""Set data encoding.
		"""
		self.write(':DAT:ENC ascii;WID 2;')
		return "Set data encoding"

	# @Action()
	def curv(self):
		"""Get data.

			Returns:
			xdata, ydata as list
		"""
		self.dataencoding()
		# self.write('DATa:STARt 1')
		# self.write('DATa:STOP 400000')
		answer = self.query_ascii('CURV?', delay=3)
		params = self.acqparams()
		data = np.array(answer)
		yoff = params['YOFF?']
		ymu = params['YMU?']
		yze = params['YZE?']
		xin = params['XIN?']
		xze = params['XZE?']
		ydata = (data - yoff) * ymu + yze
		xdata = np.arange(len(data)) * xin + xze
		return list(xdata), list(ydata)

	def _measure(self, typ, source):
		self.write('MEASUrement:IMMed:TYPe {}'.format(typ))
		self.write('MEASUrement:IMMed:SOUrce1 CH{}'.format(source))
		return self.query('MEASUrement:IMMed:VALue?')

	@Action()
	def measure_frequency(self, channel):
		"""Get immediate measurement result.
		"""
		return self._measure('FREQuency', channel)

	@Action()
	def measure_min(self, channel):
		"""Get immediate measurement result.
		"""
		return self._measure('MINImum', channel)

	@Action()
	def measure_max(self, channel):
		"""Get immediate measurement result.
		"""
		return self._measure('MAXImum', channel)

	@Action()
	def measure_pk2pk(self, channel):
		"""Get immediate measurement result.
		"""
		return self._measure('PK2Pk', channel)

	@Action()
	def data_start(self, start):
		return self.write('DATa:STARt {}'.format(start))
		
	@Action()
	def data_stop(self, stop):
		return self.write('DATa:STOP {}'.format(stop))
		

	@Action()
	def measure_mean(self, channel):
		"""Get immediate measurement result.
		"""
		return self._measure('MEAN', channel)

	@Action()
	def set_time(self, time):
		self.write('HORizontal:MAIn:DELay:TIMe {}'.format(time))
		return

	@Action()
	def query_time(self):
		return self.query('HORizontal:MAIn:DELay:TIMe?')

	@Action()
	def average(self, number):
		# if number in (4,16,64,128): 
		#     self.write('ACQ:NUMAV {}'.format(number))
		# else:
		#     print('can only average over 4, 16, 64, or 128 samples!')
		self.write('ACQ:NUMAV {}'.format(number))
		return

	@Action()
	def position(self, channel, position):
		self.write('CH{}:POS {}'.format(channel,position))
		return

	@Action()
	def scale_query(self, channel):
		return self.query('CH{}:SCA?'.format(channel))

	@Action()
	def scale(self, channel, scale):
		self.write('CH{}:SCA {}'.format(channel,scale))
		return

	@Action()
	def screensaver_off(self):
		self.write('DISplay:INTENSITy:SCREENSAVER OFF')

	@Action()
	def set_50ohm(self, channel):
		self.write('CH{}:TERmination 50.0E+0'.format(channel))

	@Action()
	def time_scale(self, scale):
		self.write('HORizontal:MAIn:SCAle {}'.format(scale))
		return


	@Action()
	def set_horizontal_resolution(self,resolution):
		self.write('HORizontal:RESOlution {}'.format(resolution))
# Extra delay commands added here

	@Feat()
	def delaymode_query(self):
		return self.query('HORizontal:DELay:MODe?')

	@Action()
	def delaymode_on(self):
		return self.write('HORizontal:DELay:MODe ON')

	@Action()
	def delaymode_off(self):
		return self.write('HORizontal:DELay:MODe OFF')

	@Action()
	def delay_position(self, position):

		if (position<0) or (position>100):
			print(' Incorrect value for position,  it must be a number between 0 and 100')
			return
		return self.write('HORizontal:DELay:POSition {}'.format(position))

	@Action()
	def delay_time(self, time):

		return self.write('HORizontal:DELay:TIMe {}'.format(time))
	@Action()
	def bandwidth_query(self, channel):

		return self.query('CH{}:BANdwidth?'.format(channel))

	@Action()
	def bandwidth_full(self, channel):

		return self.write('CH{}:BANdwidth FULl'.format(channel))


# End of extra delay commands

if __name__ == '__main__':
	import argparse
	import csv
	from lantz.log import log_to_screen, DEBUG

	parser = argparse.ArgumentParser(description='Measure using TDS5104 and dump to screen')
	parser.add_argument('-p', '--port', default='GPIB1::15::INSTR',
					   help='USB port')
	parser.add_argument('-v', '--view', action='store_true', default=False,
						help='View ')
	parser.add_argument('Channels', metavar='channels', type=int, nargs='*',
						help='Channels to use')
	parser.add_argument('--output', type=argparse.FileType('w'), default='-')

	args = parser.parse_args()

	log_to_screen(DEBUG)
	with TDS5104(args.port) as osc:
		osc.init()
		print(osc.idn)
		osc.screensaver_off()
		#osc.scale(1,0.005)
		#osc.scale(4,0.05)
		# #osc.set_time(0)
		# print(osc.trigger)
		# print(osc.delaymode_query)
		print(osc.scale_query(3))

		# osc.delaymode_on()
		# osc.delay_position(0)
		# osc.delay_time(4.99e-3)

		# osc.average(16)
		#osc.datasource(1)
		#osc.position(1,1)
		#osc.scale(1,0.05)
		'''
		osc.mode = 'sample'
		x,y = osc.curv()
		x = np.array(x)
		x = x-x.min()
		y = np.array(y)
		plt.plot(x,y)
		plt.show()
		'''
		# osc.datasource(2)
		# x,y=osc.curv()
		# x = np.array(x)
		# x = x-x.min()
		# y = np.array(y)
		# np.savetxt('chn21.txt', np.c_[x,y])
		# time.sleep(1)

		# pk2pk=osc.measure_pk2pk(2)

		# print("Peak to peak amplitude {}".format(pk2pk))

		# osc.datasource(2)
		# osc.data_start(1)
		# osc.data_stop(1000000)   
		# # osc.setmode('sample')

		# osc.setmode('average')
		# osc.average(50)

		# time.sleep(50*2)     

		# x,y=osc.curv()
		# x = np.array(x)
		# x = x-x.min()
		# y = np.array(y)
		# np.savetxt('D:/MW data/20201109/Optical/c3i_1uw_0field.txt', np.c_[x,y])

# This part is normally not commented out for dumping data on screen with average
#### SOrry Yizhong commented it out on Dec.15th, 2020
	########################################################################################################################	
		# wavelength=1952444
		# for i in range(1,6):
			

		# 	osc.datasource(3)

		# 	osc.data_start(1)
		# 	osc.data_stop(2000000)   

		# 	osc.setmode('average')
		# 	osc.average(25)

		# 	time.sleep(25*2)     

		# 	x,y=osc.curv()
		# 	x = np.array(x)
		# 	x = x-x.min()
		# 	y = np.array(y)
		# 	np.savetxt('D:/MW data/20201111/OpticalSaturation/Scan8/ch3/1952277_{}.txt'.format(i), np.c_[x,y])

		# 	osc.datasource(4)


		# 	x1,y1=osc.curv()

		# 	x1 = np.array(x1)
		# 	x1 = x1-x1.min()
		# 	y1 = np.array(y1)
		# 	np.savetxt('D:/MW data/20201111/OpticalSaturation/Scan8/ch4/1952277_{}.txt'.format(i), np.c_[x1,y1])

		# 	osc.setmode('sample')

		# 	time.sleep(5)
		#osc.query_chn(3)
		osc.bandwidth_query(3)
		osc.bandwidth_full(3)
		osc.set_horizontal_resolution(100000)
		###############################################################################################################
		path='D:\\Data\\1.7.2021_spinecho\\beatsignal testing\\'
		#osc.setmode('average')
		# osc.average(200) 
		# time.sleep(30)
		osc.datasource(3)
		#osc.screensaver_off()
		#osc.measure_frequency(3)
		
 
		time.sleep(0)     
		x,y=osc.curv()
		x = np.array(x)
		y = np.array(y)
		np.savetxt(path+'time.txt', np.c_[x])
		np.savetxt(path+'beat.txt', np.c_[y])
		plt.plot(x,y)
		#osc.datasource(1)
		plt.show()
		osc.setmode('sample')
		
 
		# time.sleep(0)     
		# x,y=osc.curv()
		# x = np.array(x)
		# y = np.array(y)
		# #np.savetxt('D:\\Data\\1.5.2021_YSO_holeburning\\1T\\voltage_sweep.txt', np.c_[x])
		# #np.savetxt(path+'sweep.txt', np.c_[y])
		# plt.plot(x,y)
		# plt.show()

		# osc.setmode('sample')
		

		# osc.datasource(3)

		# osc.data_start(1)
		# osc.data_stop(8000000)   
		# time.sleep(0)     
		# x1,y1=osc.curv()
		# x1 = np.array(x1)
		# y1 = np.array(y1)
		# np.savetxt('D:\\Data\\12.16.2020_YSO_absorption\\1T_absorption_sweep.txt', np.c_[y1])
		# osc.setmode('sample')
		# time.sleep(1)
		# plt.plot(x1,y1)
		# plt.show()
#  1570   ,  1561,   1551,  1535.5 ,1535.48,1535.455,1535.438,1535.407, 1521,  
# 190936.8, 192000, 193500, *195220, 195223, 195226, 195228 ,195230*, 197000 , 199000 
# End of the part that is normally not commented out for dumping data on screen with average



		# osc.forcetrigger()
		# osc.triggerlevel()
		# osc.trigger = "AUTO"
		# print(osc.trigger)
		# #osc.autoconf()
		# #params = osc.acqparams()

		# if args.view:
		#     import matplotlib.pyplot as plt
		#     import numpy as np

		# with args.output as fp:
		#     writer = csv.writer(fp, dialect='excel')
		#     writer.writerow(['Channel', 'Freq', 'Max', 'Min', 'Mean'])
		#     for channel in args.Channels:
		#         osc.datasource(channel)
		#         writer.writerow(([channel, osc.measure_frequency(channel),
		#                             osc.measure_max(channel),
		#                             osc.measure_min(channel),
		#                             osc.measure_mean(channel)]))

		#         if args.view:
		#             x, y = osc.curv()
		#             x = np.array(x)
		#             x = x - x.min()
		#             y = np.array(y)
		#             plt.plot(x, y)

		# if args.view:
		#     plt.show()
