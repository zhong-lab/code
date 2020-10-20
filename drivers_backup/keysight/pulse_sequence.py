from lantz.drivers.keysight.Keysight_66322A import Keysight_33622A
from lantz.drivers.keysight.arbseq_class import Arbseq_Class

class PulseSequence(object):

	def __init__(self, name, timestep):
		self.timestep = timestep
		self.repeat_unit = None
		self.arbseq = None

	def build_pulse(self):


		pulse = [off(0) for 1 sec, on(amp, trigger) for 2 sec, on(amp) for 5 sec, off(0) for 5 sec,]
		for loop over items in pulse:
			find the smallest segment, 

	def off(self, time):
		arbseq = Arbseq_Class(name, timestep)


if __name__=='main':
	pulse = PulseSequence('Test Pulse', 1e-9)
	pulse.build_pulse(off(1e-6))