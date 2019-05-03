
import numpy as np
import pyqtgraph as pg
import time
import csv

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import time

from lantz.drivers.keysight import Arbseq_Class
from lantz.drivers.keysight.seqbuild import SeqBuild


from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.tektronix import TDS2024C

class PhotonEcho(Spyrelet):

    requires = {
        'fungen': Keysight_33622A,
        'osc': TDS2024C
    }

    def create_pulses(self, tau):
        params = self.pulse_parameters.widget.get()
        totaltime = params['period'].magnitude
        shb_time = params['shb time'].magnitude
        tri_time = params['tri time'].magnitude
        ramp_time = params['ramp time'].magnitude
        wait_time = params['wait time'].magnitude
        heterodyne_time = params['heterodyne time'].magnitude
        timestep = params['time step'].magnitude
        step = params['voltage step'].magnitude
        pulse_width = params['pulse widths'].magnitude
        voltage1 = params['ch1 voltage'].magnitude
        voltage2 = params['ch2 voltage'].magnitude
        echo_voltage = params['echo voltage'].magnitude
        step_voltage = params['voltage step'].magnitude

        '''
        chn2_dc = Arbseq_Class('chn2dc', timestep)
        chn2_dc.totaltime = tri_time
        chn2_dc.widths = [chn2_dc.totaltime]
        chn2_dc.delays = [0]
        chn2_dc.heights = [voltage2]
        chn2_dc.create_sequence()
        chn2_dc.nrepeats = int(totaltime/chn2_dc.totaltime)
        chn2_dc.repeatstring = 'repeat'
        chn2_dc.markerstring = 'maintain'
        chn2_dc.markerloc = 0
        '''

    
        '''
        chn2_shb = Arbseq_Class('chn2shb', timestep)
        chn2_shb.totaltime = tri_time
        chn2_shb.widths = [chn2_shb.totaltime]
        chn2_shb.delays = [0]
        chn2_shb.heights = [voltage2]
        chn2_shb.create_sequence()
        chn2_shb.nrepeats = int(shb_time/chn2_shb.totaltime)
        chn2_shb.repeatstring = 'repeat'
        chn2_shb.markerstring = 'maintain'
        chn2_shb.markerloc = 0
       

        
        chn2_shb = Arbseq_Class('chn2shb', 2e-7)
        period = tri_time
        height = voltage2
        heights = list()
        while height <= voltage2 + step_voltage/8:
            heights.append(height)
            height += (4*(step_voltage/8)*timestep)/period
        while height >= voltage2 - step_voltage/8:
            height -= (4*(step_voltage/8)*timestep)/period
            heights.append(height)
        while height <= voltage2:
            height += (4*(step_voltage/8)*timestep)/period
            heights.append(height)
        chn2_shb.heights = heights
        chn2_shb.widths = [timestep] * len(heights)
        chn2_shb.delays = [0] * len(heights)
        chn2_shb.totaltime = period
        chn2_shb.create_sequence()
        chn2_shb.widths = [timestep] * len(heights)
        print('chn2 len(heights) is:' + str(len(heights)))
        chn2_shb.delays = [0] * len(heights)
        chn2_shb.totaltime = len(heights) * timestep
        print('chn2_shb totaltime is:' + str(chn2_shb.totaltime))
        chn2_shb.create_sequence()
        chn2_shb.nrepeats = int(shb_time/tri_time)
        print('chn2_shb nrepeats is:' + str(chn2_shb.nrepeats))
        chn2_shb.repeatstring = 'repeat'
        chn2_shb.markerstring = 'maintain'
        chn2_shb.markerloc = 0
        
              
        freq_rampdown2 = Arbseq_Class('frampdown2', timestep)
        slope = (step_voltage)/(ramp_time)
        height = voltage2
        heights = list()
        while height >= voltage2 - step_voltage:
            height -= (slope * timestep)
            heights.append(height)
        freq_rampdown2.heights = heights
        freq_rampdown2.widths = len(heights) * [timestep]
        freq_rampdown2.delays = [0] * len(heights)
        freq_rampdown2.totaltime = len(heights) * timestep
        freq_rampdown2.create_sequence()
        freq_rampdown2.nrepeats = 0
        freq_rampdown2.repeatstring = 'once'
        freq_rampdown2.markerstring = 'maintain'
        freq_rampdown2.markerloc = 0
        
        
        chn2 = Arbseq_Class('ch2', timestep)
        chn2.totaltime = tau + pulse_width + 2e-6
        chn2.widths = (tau + 2e-6, pulse_width)
        chn2.delays = (0, 0)
        chn2.heights = (voltage2 - step_voltage, voltage2 - step_voltage)
        chn2.create_sequence()
        chn2.nrepeats = 0
        chn2.repeatstring = 'once'
        chn2.markerstring = 'maintain'
        chn2.markerloc = 0

        
        freq_rampup2 = Arbseq_Class('freqrampup2', timestep)
        slope = (step_voltage)/(ramp_time)
        height = voltage2 - step_voltage
        heights = list()
        while height <= voltage2:
            heights.append(height)
            height += (slope * timestep)
        freq_rampup2.heights = heights
        print('voltage length is:' + str(freq_rampup2.heights))
        freq_rampup2.widths = len(heights) * [timestep]
        print('shb widths is:' + str(chn2_shb.totaltime))
        freq_rampup2.delays = [0] * len(heights)
        freq_rampup2.totaltime = len(heights) * timestep
        print('rampup2 totaltime is:' + str(freq_rampup2.totaltime))
        freq_rampup2.create_sequence()
        freq_rampup2.nrepeats = 0
        freq_rampup2.repeatstring = 'once'
        freq_rampup2.markerstring = 'maintain'
        freq_rampup2.markerloc = 0
        


        heterodyne2 = Arbseq_Class('heterodyne2', timestep)
    #    pulses.totaltime = max(4*tau, 10*pulse_width)
        heterodyne2.totaltime = heterodyne_time + 4e-6
        heterodyne2.widths = [4e-6, heterodyne2.totaltime]
        heterodyne2.delays = [0, 0]
        heterodyne2.heights = [voltage2, voltage2]
        heterodyne2.create_sequence()
        heterodyne2.nrepeats = 0
        heterodyne2.repeatstring = 'once'
        heterodyne2.markerstring = 'maintain'
        heterodyne2.markerloc = 0

        chn2_repeat = Arbseq_Class('chn2r', timestep)
        chn2_repeat.totaltime = tri_time
        chn2_repeat.widths = [chn2_repeat.totaltime]
        chn2_repeat.delays = [0]
        chn2_repeat.heights = [voltage2]
        chn2_repeat.create_sequence()
        chn2_repeat.nrepeats = int((totaltime - chn2_shb.totaltime*chn2_shb.nrepeats - freq_rampdown2.totaltime -  chn2.totaltime - freq_rampup2.totaltime - heterodyne2.totaltime)/tri_time) - 1
        chn2_repeat.repeatstring = 'repeat'
        chn2_repeat.markerstring = 'maintain'
        chn2_repeat.markerloc = 0

        end2 = Arbseq_Class('end2', timestep)
        end2.totaltime = totaltime - chn2_shb.totaltime*chn2_shb.nrepeats - freq_rampdown2.totaltime - chn2.totaltime - freq_rampup2.totaltime - heterodyne2.totaltime - chn2_repeat.totaltime*chn2_repeat.nrepeats
        print('end2.totaltime:' + str(end2.totaltime))
        end2.widths = [end2.totaltime]
        end2.delays = [0]
        end2.heights = [voltage2]
        end2.create_sequence()
        end2.nrepeats = 0
        end2.repeatstring = 'once'
        end2.markerstring = 'maintain'
        end2.markerloc = 0
        '''
        

       
     
        chn1_shb = Arbseq_Class('chn1shb', timestep)
        chn1_shb.totaltime = tri_time
        chn1_shb.widths = [chn1_shb.totaltime]
        chn1_shb.delays = [0]
        chn1_shb.heights = [0]
        chn1_shb.create_sequence()
        chn1_shb.nrepeats = int(shb_time/chn1_shb.totaltime)
        chn1_shb.repeatstring = 'repeat'
        chn1_shb.markerstring = 'maintain'
        chn1_shb.markerloc = 0
        
        '''
        freq_rampdown1 = Arbseq_Class('frampdown1', timestep)
        freq_rampdown1.totaltime = freq_rampdown2.totaltime
        freq_rampdown1.widths = [freq_rampdown1.totaltime]
        freq_rampdown1.delays = [0]
        #pulses.heights = (1, 1, basevoltage/voltage1)
        freq_rampdown1.heights = [0]
        freq_rampdown1.create_sequence()
        freq_rampdown1.nrepeats = 0
        freq_rampdown1.repeatstring = 'once'
        freq_rampdown1.markerstring = 'maintain'
        freq_rampdown1.markerloc = 0
        '''
        

        pulses = Arbseq_Class('pulses1', timestep)
    #    pulses.totaltime = max(4*tau, 10*pulse_width)
        pulses.totaltime = tau + pulse_width + 2e-6
        pulses.widths = (pulse_width, pulse_width)
    #    pulses.delays = (2e-6,tau,tau)
    #    pulses.widths = (pulse_width*2, pulse_width*5, pulse_width*5)
    #    pulses.delays = (2e-6,tau - pulse_width*1.5,0)
        pulses.delays = (2e-6, tau - pulse_width)
        #pulses.heights = (1, 1, basevoltage/voltage1)
        pulses.heights = (voltage1*0.6, voltage1)
        pulses.create_sequence()
        pulses.nrepeats = 0
        pulses.repeatstring = 'once'
        pulses.markerstring = 'maintain'
        pulses.markerloc = 0

        '''
        freq_rampup1 = Arbseq_Class('freqrampup1', timestep)
        freq_rampup1.totaltime = freq_rampup2.totaltime
        freq_rampup1.widths = [freq_rampup1.totaltime]
        freq_rampup1.delays = [0]
        #pulses.heights = (1, 1, basevoltage/voltage1)
        freq_rampup1.heights = [0]
        freq_rampup1.create_sequence()
        freq_rampup1.nrepeats = 0
        freq_rampup1.repeatstring = 'once'
        freq_rampup1.markerstring = 'maintain'
        freq_rampup1.markerloc = 0
        '''

        heterodyne1 = Arbseq_Class('heterodyne1', timestep)
        heterodyne1.totaltime = heterodyne_time + 4e-6
        heterodyne1.widths = [4e-6, heterodyne1.totaltime]
        heterodyne1.delays = [0, 0]
        heterodyne1.heights = [0, 0]
        heterodyne1.create_sequence()
        heterodyne1.nrepeats = 0
        heterodyne1.repeatstring = 'once'
        heterodyne1.markerstring = 'maintain'
        heterodyne1.markerloc = 0


        DC = Arbseq_Class('DC1', timestep)
        DC.totaltime = tri_time
        DC.heights = [0]
        DC.delays = [0]
        DC.widths = [DC.totaltime]
        DC.create_sequence()
        DC.nrepeats = int((totaltime - chn1_shb.totaltime*chn1_shb.nrepeats - pulses.totaltime - heterodyne1.totaltime)/tri_time) - 1
        DC.repeatstring = 'repeat'
        DC.markerstring = 'maintain'
        DC.markerloc = 0

        end1 = Arbseq_Class('end1', timestep)
        end1.totaltime = totaltime - chn1_shb.totaltime*chn1_shb.nrepeats - pulses.totaltime - heterodyne1.totaltime - DC.totaltime*DC.nrepeats
        print('end1.totaltime:' + str(end1.totaltime))
        end1.heights = [0]
        end1.delays = [0]
        end1.widths = [end1.totaltime]
        end1.create_sequence()
        end1.nrepeats = 0
        end1.repeatstring = 'once'
        end1.markerstring = 'maintain'
        end1.markerloc = 0


        return chn1_shb, pulses, heterodyne1, DC, end1



#        return chn2_shb, freq_rampdown2, chn2, freq_rampup2, heterodyne2, chn2_repeat, end2, chn1_shb, freq_rampdown1, pulses, freq_rampup1, heterodyne1, DC, end1



    @Task()
    def startpulses(self):
        self.dataset.clear()

        params = self.pulse_parameters.widget.get()
        period = params['period']
        shb_time = params['shb time']
        tri_time = params['tri time']
        ramp_time = params['ramp time']
        wait_time = params['wait time']
        heterodyne_time = params['heterodyne time']
        timestep = params['time step']
        voltage1 = params['ch1 voltage']
        voltage2 = params['ch2 voltage']
        echo_voltage = params['echo voltage'].magnitude
        start = params['tau start'].magnitude
        stop = params['tau stop'].magnitude
        taustep = params['tau step'].magnitude
        step_voltage = params['voltage step']
        pulse_width = params['pulse widths']
        filename = params['filename']

        f = open(filename, "w")
        writer = csv.writer(f, delimiter=',', quotechar='"')
        writer.writerow(['Tau', 'Intensity'])

        
        self.osc.datasource(1)
        tau = start
        while tau <= stop:
            self.fungen.output[1] = 'OFF'
            self.fungen.output[2] = 'OFF'
            self.fungen.clear_mem(1)
            self.fungen.clear_mem(2)


            chn1_shb, pulses, heterodyne1, DC, end1 = self.create_pulses(tau)
#            chn2_shb, freq_rampdown2, chn2, freq_rampup2, heterodyne2, chn2_repeat, end2, chn1_shb, freq_rampdown1, pulses, freq_rampup1, heterodyne1, DC, end1 = self.create_pulses(tau)

#            chn2 = [chn2_shb, freq_rampdown2, chn2, freq_rampup2, heterodyne2, chn2_repeat, end2]
#            chn2 = [chn2_dc]
#            self.fungen.create_arbseq('chn2',chn2,chn=2)
#            self.fungen.wait()
            

#            chn1 = [chn1_shb, freq_rampdown1, pulses, freq_rampup1, heterodyne1, DC, end1]
            chn1 = [chn1_shb, pulses, heterodyne1, DC, end1]
            self.fungen.create_arbseq('chn1',chn1,chn=1)
            self.fungen.wait()


            self.fungen.vpp[1] = 5 
#            self.fungen.vpp[2] = 5 
            self.fungen.output[1] = 'ON'
#            self.fungen.output[2] = 'ON'
            self.fungen.trigger_source[1] = 'Timer'
#            self.fungen.trigger_source[2] = 'Timer'
            self.fungen.sync() 

            print('chn1 output voltage is:' + str(self.fungen.vpp[1]))
 #           print(self.fungen.offset[2])
 #           print('chn2 output voltage is:' + str(self.fungen.vpp[2]))

            self.osc.forcetrigger()
            x, y = self.osc.curv()
            print(x)
            tau_file=open(str(round(tau,8))+'.csv','w')
            for i in range(len(x)):
                tau_file.write(str(x[i])+', '+str(y[i])+' \n')
            tau_file.close()
            x = np.array(x)
            y = np.array(y)
            x = x - x.min()

            

            '''
            for i in range(len(x)):
                values = {'x': x[i], 'y': y[i]}
                self.dataset.add_row(values)
            '''
            
            #export to csv
            fft = np.fft.fft(y)
            fft.real[0] = 0
            fft_max = max(abs(fft.real))
            writer.writerow([tau, fft_max])
            values = {'x':tau, 'y':fft_max}

            #send data to plotter element
            self.startpulses.acquire(values)
            #self.startpulses.acquired.emit(values)

            tau += taustep
            tau = round(tau,8)
            print('tau changed to {}'.format(tau))
            time.sleep(3)

        f.close()

    @startpulses.initializer
    def initialize(self):
        params = self.pulse_parameters.widget.get()
        period = params['period']
        shb_time = params['shb time']
        tri_time = params['tri time']
        ramp_time = params['ramp time']
        wait_time = params['wait time']
        heterodyne_time = params['heterodyne time']
        timestep = params['time step']
        voltage1 = params['ch1 voltage']
        voltage2 = params['ch2 voltage']
        echo_voltage = params['echo voltage'].magnitude
        start = params['tau start'].magnitude
        stop = params['tau stop'].magnitude
        taustep = params['tau step'].magnitude
        step_voltage = params['voltage step']
        pulse_width = params['pulse widths']

        self.fungen.wait()


        self.fungen.output[1] = 'ON'
#        self.fungen.output[2] = 'ON'
        print(self.fungen.vpp[1])
#        print(self.fungen.offset[2])
#        print(self.fungen.vpp[2])


        self.osc.init()
        print(self.osc.trigger)
        self.osc.forcetrigger()
        self.osc.triggerlevel()
        self.osc.trigger = "AUTO"
        print(self.osc.trigger)
        self.osc.triggersource = 'CH3'
    #    self.osc.set_averages(16)
        return

    @startpulses.finalizer
    def finalize(self):
        self.fungen.output[1] = 'OFF'
#        self.fungen.output[2] = 'OFF'
        print('finalize')
        return


    @Element(name='Pulse parameters')
    def pulse_parameters(self):
        params = [
    #    ('arbname', {'type': str, 'default': 'arbitrary_name'}),,
        ('ch1 voltage', {'type': float, 'default': 0.4, 'units':'V'}),
        ('ch2 voltage', {'type': float, 'default': 0.652, 'units':'V'}),
        ('period', {'type': float, 'default': 0.1, 'units':'s'}),
        ('shb time', {'type': float, 'default': 400e-6, 'units':'s'}),
        ('tri time', {'type': float, 'default': 10e-6, 'units':'s'}),
        ('heterodyne time', {'type': float, 'default': 10e-6, 'units':'s'}),
        ('ramp time', {'type': float, 'default': 2e-6, 'units':'s'}),
        ('wait time', {'type': float, 'default': 10e-6, 'units':'s'}),
        ('time step', {'type': float, 'default': 1e-8, 'units':'s'}),
        ('tau start', {'type': float, 'default': 1.5e-6, 'units':'s'}),
        ('tau stop', {'type': float, 'default': 20.5e-6, 'units':'s'}),
        ('tau step', {'type': float, 'default': 1e-6, 'units':'s'}),
        ('voltage step', {'type': float, 'default': 0.0212, 'units':'V'}),
        ('echo voltage', {'type': float, 'default': 0.04, 'units':'V'}),
        ('pulse widths', {'type': float, 'default': 0.38e-6, 'units':'s'}),
        ('filename', {'type': str, 'default': 'sweeptau.csv'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Oscilloscope Reading')
    def rawdata(self):
        p = LinePlotWidget()
        p.plot('Amplitude')
        return p

    @rawdata.on(startpulses.acquired)
    def data_update(self, ev):
        w = ev.widget
        data = self.data
        w.set('Amplitude', xs=data.x, ys=data.y)
        return

    '''
    @Element(name='Fourier Transform')
    def FFT(self):
        p = LinePlotWidget()
        p.plot('Real')
        p.plot('Imag')
        return p

    @FFT.on(startpulses.acquired)
    def FFT_update(self, ev):
        w = ev.widget
        data = self.data
        scale = float(self.osc.get_scale())
        timestep = 10*scale/2500

        y = np.array(data.y)
        fft = np.fft.fft(y)
        fft.real[0] = 0
        print(fft.real)
        print(fft.imag)
        freq = np.fft.fftfreq(y.size, d=timestep)
        w.set('Real', xs=freq, ys=fft.real)
        w.set('Imag', xs=freq, ys=fft.imag)
        fft_max = max(abs(fft.real))
        print(fft_max)
    '''

    @Element()
    def save(self):
        w = RepositoryWidget(self)
        return w



