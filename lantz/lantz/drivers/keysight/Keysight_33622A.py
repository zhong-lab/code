from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from lantz.drivers.keysight.arbseq_class import Arbseq_Class
from time import sleep

class Keysight_33622A(MessageBasedDriver):
	"""This is the driver for the Keysight 36622A."""

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
	def clear_status(self):
		"""This command clears the following registers:
		1. Standard Event Status
		2. Operation Status Event
		3.  Questionable Status Event
		4. Status Byte
		5. Clears the Error Queue

		If this *CLS immediately follows a program message terminator (<NL>),
		then the output queue and teh MAV bit are also cleared.

		Command Syntax: *CLS
		Parameters:     (None)
		Query Syntax:   (None)

		"""
		self.write('*CLS')
		print('Status cleared')

	'''
	@Feat()
	def event_status_enable(self, NRf):
		"""Programs the Standard Event Status Enable register bits. The
		programming determines which events of the Standard Event Status
		Event register are allowed to set the ESB (Event Summary Bit) of the
		Status Byte register. A "1" in the bit position enables the
		corresponding event. All of the enabled events of the Standard Event
		Status Event register are logically ORed to cause the Event Summary
		Bit (ESB) of the Status Byte register to be set.

		Command Syntax:      *ESE<NRf>
		Parameters:          0 to 255
		Suffix:              (None)
		Example:             *ESE 129
		Query Syntax:        *ESE?
		Returned Parameters: <NRI> (Register value)
		Related Commands:    *ESR? *PSC *STB?

		CAUTION: If PSC is programmed to 0, then the *ESE command causes a
		write cycle to nonvolatile memory. The nonvolatille memory has a
		finite maximum number of write cycles. Programs that repeatedly
		cause write cycles to non-volatile memory can eventually exceed the
		maximum number of write cycles and may cause the memory to fail.
		"""
		# NOTE: not sure if the left right angle brackets are necessary here
		return self.query('*ESE {}'.format(NRf))
		'''

	@Feat()
	def read_standard_event_status_register(self):
		"""Reads the Standard Event Status Even register. Reading the
		register clears it.
		Query Syntax:        *ESR?
		Parameters:          (None)
		Returned Parameters: <NR1> (Register binary value)
		Related Commands:    *CLS *ESE *ESE? *OPC
		"""
		return self.query('*ESR?')

	@Action()
	def operation_complete(self):
		"""This command causes the interface to set the OPC bit (bit 0) of
		the Standard Event Status register when the power supply has completed
		all pending operations. Pending operations are complete when:
		- All commands sent before *OPC have been executed. This includes
		overlapped commands. Most commands are sequential and are completed
		before the next command is executed. Overlapped commands are
		executed in parallel with other commands. Commands that affect output
		voltage, current or state, relays, and trigger actions are overlapped
		with subsequent commands sent to the power supply. The *OPC command
		provides notification that all overlapped commands have been completed.
		- Any change in the output level caused by previous commands has been
		completed.
		- All triggered actions are completed.
		*OPC does not prevent processing of subsequent commands, but Bit 0
		will not be set until all pending operations are completed.
		Command Syntax: *OPC
		Parameters:     (None)
		Related Commands *OPC? *WAI
		"""
		self.write('*OPC')

	@Action()
	def operation_completed(self):
		return self.query('*OPC?')

	@Action()
	def trigger(self):
		"""Trigger Command: Triggers a sweep, burst, arbitrary waveform advance,
		or LIST advance from the remote interface if the bus (software)
		trigger source is currently selected (TRIGger[1|2]:SOURce BUS)
		"""
		self.write('*TRG')

	def self_test(self):
		"""Self-Test Query: Performs a complete instrument self-test.
		If test fails, one or more error messages will provide additional information.
		Use SYSTem:ERRor? to read error queue
		"""
		self.write('*TST?')

	@Action()
	def wait(self):
		"""Configures the instrument to wait for all pending operations
		to complete before executing any additional commands over the interface

		For example, you can use this with the *TRG command to ensure that the instrument
		is ready for a trigger: *TRG;*WAI;*TRG
		"""
		self.write('*WAI')

	@DictFeat(units='V', limits=(10,), keys=(1, 2))
	def voltage(self, key):
		"""returns current voltage
		"""
		return float(self.query('SOURCE{}:VOLT?'.format(key)))

	@voltage.setter
	def voltage(self, key, value):
		"""Voltage setter
		"""
		self.write('SOURCE{}:VOLT {}'.format(key, value))
	
	@DictFeat(units='V', limits=(-5, 5, .0001), keys=(1, 2))
	def offset(self, key):
		"""returns current voltage offset
		"""
		return float(self.query('SOURCE{}:VOLT:OFFS?'.format(key)))
	
	@offset.setter
	def offset(self, key, value):
		"""Voltage offset setter
		"""
		self.write('SOURCE{}:VOLT:OFFS {}'.format(key, value))

	@DictFeat(units='Hz', limits=(1e-6, 200e+6), keys=(1, 2))
	def frequency(self, key):
		"""returns current frequency
		"""
		return float(self.query('SOURCE{}:FREQ?'.format(key)))

	@frequency.setter
	def frequency(self, key, value):
		"""frequency setter
		"""
		self.write('SOURCE{}:FREQ {}'.format(key, value))

	@DictFeat(units='s', limits=(1e-9, 10e-3), keys=(1, 2))
	def pulse_width(self, key):
		"""returns current pulse width
		"""
		return float(self.query('SOURCE{}:PULSe:WIDT?'.format(key)))

	@pulse_width.setter
	def pulse_width(self, key, value):
		"""frequency setter
		"""
		self.write('SOURCE{}:PULSe:WIDT {}'.format(key, value))

	@DictFeat(limits=(-360, 360), keys=(1, 2))
	def phase(self, key):
		"""returns current frequency
		"""
		return float(self.query('SOURCE{}:PHASe?'.format(key)))

	@phase.setter
	def phase(self, key, value):
		"""frequency setter
		"""
		self.write('SOURCE{}:PHASe {}'.format(key, value))

	@DictFeat(keys=(1, 2))
	def waveform(self, key):
		"""returns current waveform function
		"""
		return self.query('SOURCE{}:FUNC?'.format(key))
	
	@waveform.setter
	def waveform(self, key, value):
		"""waveform function setter
		"""
		self.write('SOURCE{}:FUNC {}'.format(key, value))

	@DictFeat(keys=(1, 2))
	def awave(self, key):
		"""returns current waveform function
		"""
		return self.query('SOURCE{}:APPL?'.format(key))
	
	@waveform.setter
	def awave(self, key, value):
		"""waveform function setter
		"""
		self.write('SOURCE{}:APPL {}'.format(key, value))
				   
	@Action()
	def abort(self):
		"""Halts a sequence, list, sweep, or burst, even an infinite burst.
		Also causes trigger subsystem to return to idle state.
		If INIT:CONT is ON, instrument immediately
		proceeds to wait-for-trigger state.
		"""
		self.write('ABORT')

	@DictFeat(keys=(1, 2))
	def trigger_source(self, key):
		"""returns trigger source for sequence, list, burst, or sweep
		{IMMEDIATE|EXTERNAL|TIMER|BUS}, default IMMEDIATE
		"""
		return self.query('TRIG{}:SOURCE?'.format(key))

	@trigger_source.setter
	def trigger_source(self, key, value):
		"""Selects the trigger source for sequence, list, burst or sweep.
		The instrument accepts an immediate or timed internal trigger,
		an external hardware trigger from the rear-panel Ext Trig connector,
		or a software (bus) trigger
		"""
		self.write('TRIG{}:SOURCE {}'.format(key, value))


	@DictFeat(keys=(1, 2))
	def force_trigger(self, key):
		"""Forces immediate trigger to initiate sequence, sweep, list, or burst
		"""
		self.query('TRIG{}'.format(key))


	def trigger_delay(self,chn,value):
		self.write('TRIG{}:DELAY {}'.format(chn, value))


	@Feat()
	def get_error(self):
		"""read and clear one error from error queue
		"""
		return self.query('SYSTEM:ERROR?')

	@DictFeat()
	def output(self, key):
		"""Gets output state for specified channel
		"""
		return self.query('OUTPUT{}?'.format(key))

	@output.setter
	def output(self, key, value):
		"""Turns output on/off for specified channel
		"""
		self.write('OUTPUT{} {}'.format(key, value))

	def sync_source(self, chn):
		self.write('OUTP:SYNC:SOUR CH{}'.format(chn))

	def sync_arbs(self, chn):
		self.write('SOURCE{}:FUNC:ARB:SYNC'.format(chn))

	def sync(self):
		self.write('FUNC:ARB:SYNC')

	def send_arb(self,arbseq,chn=1):
		"""Sends and loads an arbseq object to the function generator.
		This stores the arbitrary waveform as a .arb file in internal memory
		"""
		arb = str(arbseq.ydata).strip('[]')
		sRate = 1/(arbseq.timestep)
		name = arbseq.name

		self.write('SOURCE{}:DATA:ARB {}, {}'.format(chn, name, arb))
		self.wait()
		self.waveform[chn] = 'ARB'
		self.write('SOURCE{}:FUNC:ARB {}'.format(chn, name))
		self.write('SOURCE{}:FUNC:ARB:SRATE {}'.format(chn, sRate))
		#self.write('MMEM:STORE:DATA{} "INT:\\{}.arb"'.format(chn, name))
		print('Arb waveform "{}" downloaded to channel {}'.format(name, chn))

		#error checking
		errorstr = self.get_error
		if '+0' in errorstr:
			print('No errors reported')
		else:
			print('Error reported: ' + errorstr)

	def create_arbseq(self,seqname,seqlist,chn=1):
		"""Creates an arbitrary sequence from a given list of arbitrary waveforms.
		Loads each waveform into internal memory, then stores the total sequence
		as "seqname.seq" in internal memory
		"""
		
		seqstring = '"{}"'.format(seqname)

		for i in range(len(seqlist)):
			currentseq = seqlist[i]
			seqstring = seqstring + ',' + currentseq.get_seqstring()
		strlen = len(seqstring.encode('utf-8'))
		numbytes = len(str(strlen))
		# print('SOURCE{}:DATA:SEQ #{}{}{}'.format(chn, numbytes, strlen, seqstring))

		self.write('SOURCE{}:DATA:SEQ #{}{}{}'.format(chn, numbytes, strlen, seqstring))
		self.waveform[chn] = 'ARB'
		self.write('SOURCE{}:FUNC:ARB {}'.format(chn, seqname))
		#self.write('MMEM:STORE:DATA{} "INT:\\{}.seq"'.format(chn, seqname))
		print('Arb sequence "{}" downloaded to channel {}'.format(seqname, chn))

		#error checking
		errorstr = self.get_error
		if "+0" in errorstr:
			print('No errors reported')
		else:
			print('Error reported: ' + errorstr)

	def load_arb(self, name, chn=1):
		"""Loads arbitrary waveform to volatile memory
		which was previously stored in internal memory
		"""
		self.write('MMEM:LOAD:DATA{} "INT:\\{}.arb"'.format(chn, name))
		self.waveform[chn] = 'ARB'
		self.write('SOURCE{}:FUNC:ARB "INT:\\{}.arb"'.format(chn, name))

	def load_seq(self, seqname, chn=1):
		"""Loads arbitrary sequence to volatile memory
		which was previously stored in internal memory
		"""
		self.write('MMEM:LOAD:DATA{} "INT:\\{}.seq"'.format(chn, seqname))
		self.waveform[chn] = 'ARB'
		self.write('SOURCE{}:FUNC:ARB "INT:\\{}.seq"'.format(chn, seqname))

	def clear_mem(self, chn=1):
		"""Clears volatile memory
		"""
		self.write('SOURCE{}:DATA:VOL:CLEAR'.format(chn))

	def delete_arb(self, filename):
		"""Deletes a .arb or .seq file from internal memory
		"""
		self.write('MMEM:DEL "INT:\\{}"'.format(filename))

	def list_arb(self):
		"""Creates a list of all available arbitrary and sequence files
		in internal memory
		"""
		arb_string = self.query('MMEM:CAT:DATA:ARBITRARY? "INT:\\"')
		arb_list = arb_string.split(',')
		ret_val = list()
		del arb_list[0:2]
		for arb in arb_list:
			if '.arb' in arb:
				ls = arb.split(',')
				arb = str(ls[0]).lstrip('"')
				ret_val.append(arb)

		return ret_val

	def get_image(self, value):
		self.write('HCOP:SDUM:DATA:FORMAT {}'.format(value))
		sleep(1)
		return self.query_binary('HCOP:SDUM:DATA?', delay=3)




if __name__ == '__main__':
	from time import sleep
	from lantz import Q_
	from lantz.log import log_to_screen, DEBUG

	volt = Q_(1, 'V')
	milivolt = Q_(1, 'mV')
	Hz = Q_(1, 'Hz')

	log_to_screen(DEBUG)
	# this is the USB VISA Address:
	with Keysight_33622A('USB0::0x0957::0x5707::MY53801461::0::INSTR') as inst:
		print('The identification of this instrument is :' + inst.idn)
		# inst.waveform[2] = 'PULS'
		# inst.frequency[2] = 60 * Hz
		# inst.voltage[2] = 3.5 * V
		# inst.offset[2] = 1.75 * V
		inst.output[2] = 'OFF'

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
