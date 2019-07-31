
from collections import OrderedDict

snippets = {
'get_counts':OrderedDict([
('helper',"""
import time as time
import numpy as np
from lantz.drivers.ni.daqmx import CounterInputTask, CountEdgesChannel

def get_counts(ctr_tasks, delay=1.0):
     ctrs_start = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in ctr_tasks])
     time.sleep(delay)
     ctrs_end = np.array([(task.read(samples_per_channel=1)[-1], time.time()) for task in self.ctr_tasks])
     dctrs = ctrs_end - ctrs_start
     ctrs_rates = dctrs[:,0] / dctrs[:,1]
     return ctrs_rates

def clear_ctr_tasks(ctr_tasks):
    for ctr_task in ctr_tasks:
        ctr_task.clear()

def setup_ctr_tasks(ctrs = ['Dev1/ctr2', 'Dev1/ctr3']):
    if len(set(ctrs)) != len(ctrs):
        raise RuntimeError('counter channels 1 and 2 must be different')
    ctr_tasks = list()
    for idx, ctr in enumerate(ctrs):
        task = CounterInputTask('otf ch {}'.format(idx))
        ch = CountEdgesChannel(ctr)
        task.add_channel(ch)
        task.start()
        ctr_tasks.append(task)
    return ctr_tasks
"""),
('initialize',"""self.ctr_tasks = setup_ctr_tasks(ctrs = ['Dev1/ctr2', 'Dev1/ctr3'])"""),
('finalize',"""clear_ctr_tasks(self.ctr_tasks)"""),
('sweep',"""counts = get_counts(self.ctr_tasks, delay=1.0)"""),
]),

'smu_setup':OrderedDict([
('helper',"""
def setup_smu(smu):
    smu.source_function = 'voltage'
    smu.source_voltage_range = 21
    smu.source_voltage = 0
    smu.current_compliance = 100e-6
    smu.sense_current_range = 100e-6
    smu.source_current_range = 100e-6

    smu.sense_function['current'] = 'ON'
    smu.sense_function['voltage'] = 'ON'
    
def clear_smu(smu):
    smu.source_voltage = 0
    smu.output = False
"""),
('initialize',"setup_smu(self.smu)"),
('finalize',"clear_smu(self.smu)"),
]),

'spectrometer_setup':OrderedDict([
('helper',"""
def get_spectrometer_data(spectrometer):
    cts, wls = spectrometer.acquire_frame()
    print(cts.shape, wls.shape)
    if len(cts.shape)==3:
        cts = cts.mean(axis=2)
    cts = cts.flatten()
    print(cts.shape, wls.shape)
    return cts, wls
    
def setup_spectometer(spectrometer, exposure_time = 1000, n_frame = 5):
    spectrometer.exposure_time = exposure_time
    spectrometer.num_frames = n_frame
    spectrometer.timeout = 2*exposure_time*n_frame
"""),
('initialize',"setup_spectometer(self.spectrometer, exposure_time = 1000, n_frame = 5)"),
('sweep',"""cts, wls = get_spectrometer_data(self.spectrometer)"""),
]),

}


default_snippet = """
import time
def initialize(self):
    #INITIALIZE CODE HERE
    print('initialize...')
    return

def finalize(self):
    #FINALIZE CODE HERE
    print('finalize...')
    return

def sweep(self):
    #SWEEP CODE HERE
    self.dataset.clear()
    for i in self._sweep.progress(range(10)):
        print(i)
        time.sleep(0.1)
        values = {
                    'idx': i,
                 }
        self._sweep.acquire(values)
    return

def plot1d_update(self, ev):
    xs, ys= 'idx', 'idx'
    get_data = lambda prop_name: getattr(self.dataset.data, prop_name).values
    idx = self.dataset.data.idx.values
    ev.widget.set('Signal', xs=get_data(xs), ys=get_data(ys))
    return

def plot2d_update(self, ev):
#    ev.widget.set(im)
    return
"""