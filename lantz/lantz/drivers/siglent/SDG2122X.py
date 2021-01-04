from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from lantz.drivers.keysight.arbseq_class import Arbseq_Class
from time import sleep

class SDG2122X(MessageBasedDriver):
	"""This is the driver for the Keysight SDG2122X."""

	"""For VISA resource types that correspond to a complete 488.2 protocol
	(GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
	generally do not need to use termination characters, because the
	protocol implementation also has a native mechanism to specify the
	end of the of a message.
	"""
 
	DEFAULTS = {'COMMON':{'write_termination': '\n', 'read_termination': '\n'}}

	@Feat()
	def idn(self):
		return self.query('*IDN?')

	@Action()
	def operation_completed(self):
		return self.query('*OPC?')


	@Action()
	def turnon(self, key):
		self.write('C{}:OUTP ON'.format(key))

	@Action()
	def waveform(self, key, waveform):
		self.write('C{}:BSWV WVTP,{}'.format(key, waveform))

	@Action()
	def setfreq(self, key, freq):
		self.write('C{}:BSWV FRQ,{}'.format(key, freq))

	@Action()
	def DCvotage(self, key, volt):
		self.write('C{}:BSWV WVTP,DC OFST,{}V'.format(key, volt))

	@Action()
	def offset(self, key, volt):
		self.write('C{}:BSWV OFST,{}V'.format(key, volt))


	

if __name__ == '__main__':
	from time import sleep
	from lantz import Q_
	from lantz.log import log_to_screen, DEBUG

	volt = Q_(1, 'V')
	milivolt = Q_(1, 'mV')
	Hz = Q_(1, 'Hz')

	log_to_screen(DEBUG)
	# this is the USB VISA Address:
	with SDG2122X('USB0::0xF4EC::0xEE38::SDG2XCAX2R1612::INSTR') as inst:
		print('The identification of this instrument is :' + inst.idn)
		inst.waveform(1,'DC')
		#inst.setfreq(1,0.01)
		inst.turnon(1)
		sleep(1)
		inst.offset(1,0.2)
		sleep(1)
		inst.offset(1,0.3)
		sleep(1)
		inst.offset(1,0.4)
		sleep(1)
		inst.offset(1,0.5)

		#print(str(inst.read_standard_event_status_register))
		#inst.output[1] = 'ON'
		#inst.voltage[1] = 3.0 * volt
		#inst.offset[1] = 0 * milivolt
		#inst.frequency[1] = 20 * Hz
		#inst.waveform[1] = 'SQUARE'
		#print('Current waveform: ' + inst.waveform[1])
		#print('Current voltage: ' + str(inst.voltage[1]))
		#print('Current frequency: ' + str(inst.frequency[1]))
		#print('Current offset: ' + str(inst.offset[1]))
		#print('ERROR: ' + inst.get_error)
		#inst.operation_complete
		#inst.clear_status
		#inst.test
		#image = inst.get_image('BMP')
		#inst.sync()
		#print(inst.get_image('PNG'))
