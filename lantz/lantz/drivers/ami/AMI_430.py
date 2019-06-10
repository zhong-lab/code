##Riku FUkumori 2019
##Driver for magnet controller AMI 430
#Not all commands are added. Refer to programming manual and
#add any necessary additional commands

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class AMI_430(MessageBasedDriver):

	DEFAULTS = {'COMMON':{'write_termination': '\n', 'read_termination': '\n'}}

	@Feat()
	def idn(self):
		#Gets ID of controller
		return self.query('*IDN?')

	@Action()
	def remote(self):
		#disables front panel controls for remote control
		self.write('SYSTem:REMote')

	@Action()
	def local(self):
		#enables front panel access for local control
		self.write('SYSTem:LOCal')

	@Feat()
	def time(self):
		#returns system time
		return self.query('SYSTem:TIME?')

	@Feat()
	def error(self):
		#queries errors loaded in buffer. Calling them will clear the errors
		return self.query('SYSTem:ERRor?')

	@Feat()
	def rampRateUnits(self):
		#queries ramp rate units, returns 1 for minutes and 0 for seconds
		return self.query('RAMP:RATE:UNITS?')

	@rampRateUnits.setter
	def rampRateUnits(self, value):
		#sets ramp rate units, 1 for minutes, 0 for seconds
		if value==0 or value==1:
			self.write('CONFigure:RAMP:RATE:UNITS {}'.format(value))
		else
			self.write('CONFigure:RAMP:RATE:UNITS 1')

	@Feat()
	def fieldUnits(self):
		#queries field units, 0 for kilogauss or 1 for Tesla
		return self.query('FIELD:UNITS?')

	@fieldUnits.setter
	def fieldUnits(self, value)
		#sets field units
		self.write('CONFigure:FIELD:UNITS {}'.format(value))

	@Feat()
	def fieldTarget(self):
		#queries the target field
		return self.query('FIELD:TARGet?')

	@fieldTarget.setter
	def fieldTarget(self, value):
		#sets the target field, in whatever units specified
		self.write('CONFigure:FIELD:TARGet {}'.format(value))

	@Feat()
	def rampSeg(self):
		#returns the number of ramp segments
		return self.query('RAMP:RATE:SEGments?')
	
	@rampSeg.setter
	def rampSeg(self, value):
		#sets the number of ramp segments
		self.write('CONFigure:RAMP:RATE:SEGments {}'.format(value))

	@Feat()
	def rampRateField(self, segment):
		#returns the ramp rate in field/time for specified units, for
		#specified segment. segment is 1 to however many segments you made.
		#if you only have 1 segment, then use 1
		return self.query('RAMP:RATE:FIELD:{}?'.format(segment))

	@rampRateField.setter
	def rampRateField(self, segment, rate, bound):
		#sets ramp rate in field for a specific segment, upper bound is the target field for
		#that particular segment
		self.write('CONFigure:RAMP:RATE:FIELD {},{},{}'.format(segment,rate,bound))

	@Feat()
	def field(self):
		#return the calculated field at the time of query
		return self.query('FIELD:MAGnet?')


	###THE BELOW COMMANDS SET THE MAGNET MODE
	@Action()
	def ramp(self):
		self.write('RAMP')

	@Action()
	def pause(self):
		self.write('PAUSE')

	@Action()
	def zero(self):
		#zeroes current
		self.write('ZERO')

	@Feat()
	def status(self):
		#Returns the state of the controller in the following way:
		#1-Ramping to target, 2-Holding at target, 3-Paused,
		#4-Ramping in manual up mode, 5-Ramping in manual down mode
		#6-In the middle of zeroing current 7-Quench detected
		#8-At 0 current 9-Heating persistent switch 10-cooling persistent switch
		return self.query('STATE?')

	@Feat()
	def persistent(self):
		#returns if magnet is in persistent mode or not. 0 for off, 1 for on
		return self.query('PERSistent?')

	#SWITCH HEATER COMMANDS
	@Feat()
	def pSwitch(self):
		#returns the state of the heater, 1 for on 0 for off
		return self.query('PSwitch?')

	@pSwitch.setter
	def pSwitch(self, value):
		#1 to turn heater on, 0 to turn it off
		self.write('PSwitch {}'.format(value))

	#QUENCH COMMANDS
	@Feat()
	def quench(self):
		#returns if magnet quenched. 0 for no quench, 1 for quench
		return self.query('QUench?')

	@quench.setter
	def quench(self, value):
		#0 to reset quench status, 1 to set quench status
		self.write('QUench {}'.format(value))


if __name__ == '__main__':
	from time import sleep
	from lantz import Q_
	from lantz.log import log_to_screen, DEBUG
	log_to_screen(DEBUG)
	# this is the USB VISA Address:
	with AMI_430('') as inst:
		print('The identification of this instrument is :' + inst.idn)
