import zhinst.toolkit as tk



hdawg = tk.HDAWG("hdawg1", "dev8345", interface="usb")

hdawg.setup()           # set up data server connection
hdawg.connect_device()  # connect device to data server


print(f"name:        {hdawg.name}")
print(f"serial:      {hdawg.serial}")
print(f"device:      {hdawg.device_type}")
print(f"options:     {hdawg.options}")
print(f"interface:   {hdawg.interface}")
print(f"connected:   {hdawg.is_connected}")

hdawg.nodetree.system.clocks.referenceclock.source(0)
maxvolt=1.0
hdawg.nodetree.sigouts[0].range(maxvolt)
hdawg.nodetree.sigouts[1].range(maxvolt)


hdawg.nodetree.system.awg.oscillatorcontrol(1)



hdawg.awgs[0].set_sequence_params(sequence_type="Custom",path="C:/Program Files/Zurich Instruments/LabOne/WebServer/awg/src/test.seqc",custom_params=[],)
hdawg.awgs[0].compile()



hdawg.nodetree.triggers.out[0].source(4)
hdawg.nodetree.triggers.out[1].source(6)
hdawg.nodetree.triggers.out[2].source(0)

iqfreq=100e6
offset1=0.01
offset2=0.02
hdawg.nodetree.oscs[0].freq(iqfreq)
hdawg.nodetree.oscs[1].freq(iqfreq)
hdawg.awgs[0].gain1=1.0
hdawg.awgs[0].gain2=0.95
hdawg.nodetree.sigouts[0].offset(offset1)
hdawg.nodetree.sigouts[1].offset(offset2)
hdawg.awgs[0].modulation_phase_shift=98
hdawg.awgs[0].enable_iq_modulation()

hdawg.awgs[0].run()


hdawg.awgs[0].output1("on")   
hdawg.awgs[0].output2("on")

# hdawg.awgs[0].output1("off")   
# hdawg.awgs[0].output2("off")


# hdawg.awgs[0].disable_iq_modulation()