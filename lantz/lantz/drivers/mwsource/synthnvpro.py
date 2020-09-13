#Driver for SynthNVPro RF Generator
#@Riku Fukumori 5.2019
#Yuxiang Pei modified 8.2019

from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
import time
from time import sleep

class SynthNVPro(MessageBasedDriver):

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

	@Feat(units='MHz', limits=(12.5,7000.0,1e-7))
	def frequency(self):
		"""returns current frequency setting
		"""
		return self.query('f?')

	@frequency.setter
	def frequency(self, value):
		"""sets frequency in range of 12.5 to 6400 MHz, in MHz
		"""
		self.write('f{}'.format(float("{0:.7f}".format(value))))

	@Feat(limits=(-60,20,0.001))
	def power(self):
		"""return current power setting, in dBm
		"""
		return self.query('W?')

	@power.setter
	def power(self, value):
		"""sets power in dBm
		"""
		self.write('W{}'.format(float("{0:.3f}".format(value))))

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


	@Feat(units='MHz', limits=(12.5,7000.0,1e-7))
	def sweep_lower(self):
		return self.query('l?')
		"""return the lower sweep frequency in MHz
		"""	    

	@sweep_lower.setter
	def sweep_lower(self,value):
		self.write('l{}'.format(float("{0:.7f}".format(value))))
		"""set the lower sweep frequency in MHz
		"""	    
		
	@Feat(units='MHz', limits=(12.5,7000.0,1e-7))
	def sweep_upper(self):
		return self.query('u?')
		"""return the lower sweep frequency in MHz
		"""	   

	@sweep_upper.setter
	def sweep_upper(self,value):
		self.write('u{}'.format(float("{0:.7f}".format(value))))
		"""set the lower sweep frequency in MHz
		"""	 

	@Feat(limits=(-60,20,0.001))
	def sweep_power_low(self):
		return self.query('[?')
		"""return the lower sweep power in dBm
		"""	   

	@sweep_power_low.setter
	def sweep_power_low(self,value):
		self.write('[{}'.format(float("{0:.3f}".format(value))))
		"""set the lower sweep power in dBm
		"""	   

	@Feat(limits=(-60,20,0.001))
	def sweep_power_high(self):
		return self.query(']?')
		"""return the higher sweep power in dBm
		"""	   

	@sweep_power_high.setter
	def sweep_power_high(self,value):
		self.write(']{}'.format(float("{0:.3f}".format(value))))
		"""set the higher sweep power in dBm
		"""	  

	@Feat(units='MHz')
	def sweep_size(self):
		return self.query('s?')
		"""return the step sweep frequency in MHz
		"""	   

	@sweep_size.setter
	def sweep_size(self,value):
		self.write('s{}'.format(value))
		"""set the step sweep frequency in MHz
		"""	   

	@Feat(units='ms')
	def sweep_step_time(self):
		return self.query('t?')
		"""returns the sweep step time in ms
		"""	   

	@sweep_step_time.setter
	def sweep_step_time(self,value):
		self.write('t{}'.format(value))
		"""sets the sweep step time in ms
		"""

	@Feat()
	def sweep_direction(self):
		return self.query('^?')
		"""returns the sweep direction
		   0 = from upper frequency to lower frequency
		   1 = from lower frequency to upper frequency
		"""

	@sweep_direction.setter
	def sweep_direction(self,value):
		self.write('^{}'.format(value))	   
		"""sets the sweep direction
		   0 = from upper frequency to lower frequency
		   1 = from lower frequency to upper frequency
		"""

	@Feat()
	def sweep_run(self):
		return int(self.query('g?'))
		"""returns the sweep status
		   0 = not running
		   1 = running
		   further explaination turn to the manual
		"""

	@sweep_run.setter
	def sweep_run(self,value):
		self.write('g{}'.format(value))
		"""sets the sweep status
		   0 = not running
		   1 = running
		   further explaination turn to the manual
		"""

	@Feat()
	def PLL_charge_pump_current(self):
		return self.query('U?')
		"""returns the PLL charge current
		   you could see it on the synthnv Pro GUI->Extras->PLL ICP
		   please set it to 5
		"""	

	@PLL_charge_pump_current.setter
	def PLL_charge_pump_current(self,value):
		self.write('U{}'.format(value))
		"""sets the PLL charge current
		   you could see it on the synthnv Pro GUI->Extras->PLL ICP
		   please set it to 5
		"""	

	@Feat(units='Hz')
	def channel_spacing(self):
		return self.query('i?')
		"""returns the channel spacing
		   you could see it on the synthnv Pro GUI->Extras->Step Size
		   please set it to 100 Hz
		"""

	@channel_spacing.setter
	def channel_spacing(self,value):
		return self.write('i{}'.format(value))
		"""sets the channel spacing
		   you could see it on the synthnv Pro GUI->Extras->Step Size
		   please set it to 100 Hz
		"""

	@Feat()
	def Trigger_Setting(self):
		return self.query('y?')

	@Trigger_Setting.setter
	def Trigger_Setting(self,value):
		return self.write('y{}'.format(value))

	@Feat(units='Hz')
	def Ext_FM_Frquency(self):
		return self.query('<?')

	@Ext_FM_Frquency.setter
	def Ext_FM_Frquency(self,value):
		return self.write('<{}'.format(value))

	@Feat(units='Hz')
	def Ext_FM_Deviation(self):
		return self.query('>?')

	@Ext_FM_Deviation.setter
	def Ext_FM_Deviation(self,value):
		return self.write('>{}'.format(value))

	@Feat()
	def Ext_FM_Type(self):
		return self.query(';?')

	@Ext_FM_Type.setter
	def Ext_FM_Type(self,value):
		return self.write(';{}'.format(value))

	@Feat()
	def Sweep_Continuous(self):
		return self.query('c?')

	@Sweep_Continuous.setter
	def Sweep_Continuous(self,value):
		return self.write('c{}'.format(value))

	@Feat()
	def Default_Setting(self):
		return self.write('e')

if __name__=='__main__':
	from lantz.log import log_to_screen, DEBUG
	from lantz import Q_
	volt = Q_(1, 'V')
	milivolt = Q_(1, 'mV')
	Hz = Q_(1, 'Hz')
	kHz=Q_(1,'kHz')
	MHz = Q_(1.0,'MHz')
	dB = Q_(1,'dB')
	dBm = Q_(1,'dB')
	ms = Q_(1,'ms')
	log_to_screen(DEBUG)
	with SynthNVPro('ASRL8::INSTR') as inst:
		inst.frequency=70.2*MHz
		inst.output=0 
		inst.sweep_lower=5093*MHz
		inst.sweep_upper=5100*MHz
		inst.sweep_size= 0.1*MHz
		# print(inst.frequency)
		# print(inst.sweep_size)
		inst.sweep_step_time= 3*ms
		# # print(inst.sweep_step_time)
		inst.sweep_direction = 1
		# # print(inst.sweep_direction)
		# print(inst.sweep_run)
		# inst.PLL_charge_pump_current=5
		# print(inst.PLL_charge_pump_current)
		# inst.channel_spacing=100*Hz
		# print(inst.channel_spacing)
		#inst.sweep_power_high=-5
		# inst.power=5.800
		# print(inst.power)
		# print(inst.sweep_power_high)
		inst.sweep_run = 0
		inst.Sweep_Continuous = 0
		# print(inst.sweep_run)
		inst.Trigger_Setting= 0
		print(inst.Trigger_Setting)
		inst.Ext_FM_Frquency= 1 * Hz
		print(inst.Ext_FM_Frquency)
		inst.Ext_FM_Deviation = 4000000 * Hz
		print(inst.Ext_FM_Deviation)
		inst.Ext_FM_Type = 1
		print(inst.Ext_FM_Type)
		print(inst.Default_Setting)
		inst.power=0
		print(inst.power)

