##Driver for SynthNVPro RF Generator
##@Riku Fukumori 5.2019

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from time import sleep

class SynthNVPro(MessageBasedDriver):
	"""
	IMPORTANT NOTE:
	Communication port number could change from time to time or if the device is
	unplugged and plugged in again. Under incorrect port number will get TMO time
	out error. To find the port number the computer assigns to it, either run
	python from terminal,

	import pyvisa
	rm = pyvisa.ResourceManager()
	rm.list_resources()
	# here unplug the device and run the above command again to identify the
	address of SynthNVP.
	quit()

	Could also go to device manager and do the plug and unplug to see port number.
	Then go to NIMax and find the address of with that port number.

    For SynthNVP make sure you can connect via the GUI first, then the COM port
    number should also show up in the maximized window of the GUI.

	NOTE:
	If device is connected via software GUI or the pyvisa from python terminal,
	it is occupied and cannot be accessed via the spyrelet. Quit those processes
	first.

	-- Shawn
	"""
	# Synth NVP doesn't have these write or read terminations for purpose of speed
	# Details see programming manual from website

	# DEFAULTS = {'COMMON': {'write_termination': '\n',
	#                         'read_termination': '\n'}}

	@Feat()
	def output(self):
		"""returns if output is on or off
		"""
		return self.query('E?')

	@output.setter
	def output(self, value):
		"""sets output to on: 1, or off: 0
		"""
		self.write('E{}r{}'.format(value,value))

	@Feat(units='MHz', limits=(12.5,6400.0,1e-7))
	def frequency(self):
		"""returns current frequency setting
		"""
		return self.query('f?')

	@frequency.setter
	def frequency(self, value):
		"""sets frequency in range of 12.5 to 6400 MHz, in MHz
		"""
		self.write('f{}'.format(value))

	@Feat(limits=(-60,20,0.001))
	def power(self):
		"""return current power setting, in dBm
		"""
		return self.query('W?')

	@power.setter
	def power(self, value):
		"""sets power in dBm
		"""
		self.write('W{}'.format(value))

	@Feat()
	def calibration(self):
		"""queries device if calibration was successful
		   1 for success, 0 for failure
		"""
		return self.query('V')


	@Feat()
	def temperature_comp(self):
		"""query if temperature compensation is on
		   0=off, 1=on setting frequency/power,
		   2=every 1 second, 3=every 10 seconds
		   3 is default setting on power up
		"""
		return self.query('Z?')

	@temperature_comp.setter
	def temperature_comp(self, value):
		self.write('Z{}'.format(value))

	@Action()
	def phase(self, value):
		"""Can adjust phase of output
		   However, device has no way of knowing it's current phase
		   Only able to adjust phase relative to current phase
		"""
		self.write('~{}'.format(value))

	@Feat()
	def reference(self):
		"""queries the internal reference setting
		   0=external, 1=internal 27MHz, 2=internal 10MHz
		"""
		return self.query('x?')

	@reference.setter
	def reference(self, value):
		self.write('x{}'.format(value))

	@Feat()
	def trigger(self):
		"""returns trigger setting
		   refer to manual for all setting info
		"""
		return self.query('w?')

	@trigger.setter
	def trigger(self, value):
		self.write('w{}'.format(value))

if __name__=='__main__':
	from lantz.log import log_to_screen, DEBUG
	log_to_screen(DEBUG)
	with SynthNVPro('ASRL3::INSTR') as inst:
		print(inst.output)
		inst.frequency=200
		inst.power=17
		inst.output=0