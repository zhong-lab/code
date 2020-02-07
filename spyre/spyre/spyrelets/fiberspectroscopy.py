import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget
from lantz.log import log_to_screen, DEBUG

from lantz import Q_

from lantz.drivers.attocube import ANC350

class Attocube(Spyrelet):

    requires = {
        'attocube': ANC350
    }

    @Task(name='set position')
    def set_position(self):
        toggle = self.toggle_params.widget.get()
        pos = self.position_params.widget.get()
        pos0 = pos['axis0_position']
        pos1 = pos['axis1_position']
        pos2 = pos['axis2_position']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.position[0] = pos0
        if toggle1:
            self.attocube.position[1] = pos1
        if toggle2:
            self.attocube.position[2] = pos2

    @set_position.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing move...')
        self.attocube = ANC350()
        self.attocube.initialize()
        return

    @set_position.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing move...')
        return

    @Task(name='move by')
    def move_by(self):
        toggle = self.toggle_params.widget.get()
        move = self.moveby_params.widget.get()
        move0 = move['axis0_move']
        move1 = move['axis1_move']
        move2 = move['axis2_move']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.relative_move(0, move0)
        if toggle1:
            self.attocube.relative_move(1, move1)
        if toggle2:
            self.attocube.relative_move(2, move2)

    @move_by.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing move...')
        self.attocube = ANC350()
        self.attocube.initialize()
        return

    @move_by.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing move...')
        return

    @Task(name='closed loop')
    def cl_move(self):
        toggle = self.toggle_params.widget.get()
        move = self.moveby_params.widget.get()
        move0 = move['axis0_move']
        move1 = move['axis1_move']
        move2 = move['axis2_move']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.cl_move(0, move0)
        if toggle1:
            self.attocube.cl_move(1, move1)
        if toggle2:
            self.attocube.cl_move(2, move2)

    @move_by.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing move...')
        self.attocube = ANC350()
        self.attocube.initialize()
        return

    @move_by.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing move...')
        return

    @Task(name='jog')
    def jog(self):
        toggle = self.toggle_params.widget.get()
        jog = self.jog_params.widget.get()
        speed0 = jog['axis0_speed']
        speed1 = jog['axis1_speed']
        speed2 = jog['axis2_speed']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle1:
            self.attocube.jog[0] = speed0
        if toggle2:
            self.attocube.jog[1] = speed1
        if toggle3:
            self.attocube.jog[2] = speed2

    @jog.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing jog...')
        attocube = ANC350()
        self.attocube.initialize()
        return

    @jog.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing jog...')
        return

    @Task(name='stop')
    def stop(self):
        self.attocube.stop()

    @stop.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing stop...')
        attocube = ANC350()
        self.attocube.initialize()
        return

    @stop.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing stop...')
        return

    @Task()
    def scan(self):
        start = time.time()
        params = self.scan_params.widget.get()
        FILENAME = params['filename']

        FREQUENCY_x=['xfreq']
        FREQUENCY_y=['yfreq']
        FREQUENCY_z=params['zfreq']


        axis_index_x=params['xaxis']
        axis_index_y=params['yaxis']
        axis_index_z=params['zaxis']

        num_pixels_x=600
        num_pixels_y=600

        # range of each axis in um
        x_range=6000
        y_range=6000
        z_range=5000

        VOLTAGE_x=45
        VOLTAGE_y=40
        VOLTAGE_z=40

        start_pos_x=360
        start_pos_y=0

        attocube.frequency[axis_index_x]=Q_(FREQUENCY_x,'Hz')
        attocube.frequency[axis_index_y]=Q_(FREQUENCY_y,'Hz')
        attocube.frequency[axis_index_z]=Q_(FREQUENCY_z,'Hz')

        x_init=attocube.position[axis_index_x]

        # y axis:
        y_init=attocube.position[axis_index_y]

        # z axis:
        z_init=attocube.position[axis_index_z]

        # Use closed loop moves to drive the attocube to 0,0 in the x,y plane
        ## THIS ASSUMES THAT THE CLOSED LOOP DRIVER MOVES TO ABSOLUTE POSITIONS RATHER 
        attocube.cl_move(axis_index_x,Q_(start_pos_x,'um'))
        print('X INITIALIZE FINISHED')
        attocube.cl_move(axis_index_y,Q_(start_pos_y,'um'))


        # measuring the 
        # reflectance from the power-meter
        power_meter=PM100D()

        # first want to raster the whole area to get an image of the reflectivity
        # will use closed-loop moves 

        x_pos=attocube.position[axis_index_x]
        y_pos=attocube.position[axis_index_y]
        z_pos=attocube.position[axis_index_z]

        # the x,y axes have a range of 6mm #
        ## making a 600x600 pixel image ##
        ### 100 points per mm ###
        #### 1/10mm=100um,1/100mm=10um ####
        ##### going to take steps of 10um #####

        # make a list of positions to make closed-loop moves to #
        ## the positions are going to be specified in um ##
        x_list=list(range(0,num_pixels_x))
        y_list=list(range(0,num_pixels_y))

        step_scaling_x=int(round(x_range/num_pixels_x))
        step_scaling_y=int(round(y_range/num_pixels_y))

        # make an array where the measurements from the power-meter will be stored and
        ## then converted into an image
        reflection_array=[[0]*len(x_list)]*len(y_list)

        # open the image file
        reflection_image=open(FILENAME+'.pgm','w')


        # THIS IMAGE WILL BE SPECIFIED IN THE PGM FILE FORMAT #
        ## LOOK UP NETPBM FORMAT ##


        # This line specifies the use of raw PGM, which accepts more characters than
        ## plain PGM images
        ### takes ASCII decimal characters which is good for handling the output from
        #### the power meter
        reflection_image.write('P5 \n')

        # write the dimensions of the image as part of the PGM file format
        reflection_image.write(str(num_pixels_x)+' '+str(num_pixels_y)+' \n')

        ## min pow is used for normalizing the powers to positive integers
        min_pow=100

        # this rasters the xy-area over which we expect to see a device
        for pos_y in range(len(y_list)):
            for pos_x in range(len(x_list)):
                attocube.cl_move(axis_index_y,Q_(pos_y*step_scaling_x,'um'))
                attocube.cl_move(axis_index_x,Q_(pos_x*step_scaling_y,'um'))
                reflection=power_meter.power

                #send values to plot
                values = {'x': time.time()-start, 'y': reflection}
                self.scan.acquire(values)


                if reflection<min_pow:
                    min_pow=reflection
                reflection_array[pos_y][pos_x]=reflection

        # max value in the array to be calculated
        ## this specification is part of the PGM format
        max_pow=0

        # since the file is specified in binary file type, need to change all of the
        # values to integers greater than 0
        # first normalize to the minimum power and round all values to nearest integer
        for pos_y in range(len(y_list)):
            for pos_x in range(len(x_list)):
                raw_val=reflection_array[pos_y][pos_x]
                rounded=int(round(raw_val/min_pow))

                # change powers to 16-digit binary for the PGM file format
                # may need more digits depending on power values
                # this is because for maximum powers >256, the values must be specified 
                # as 2-byte
                # not sure if this may need to be changed to 8
                reflection_array[pos_y][pos_x]='{0:016b}'.format(rounded)
                if rounded>max_pow:
                    max_pow=rounded

        # write the max pixel value in ASCII as part of the PGM format
        reflection_image.write(str(max_pow)+' \n')

        # write a newline before the image
        reflection_image.write('\n')

        # export this line of the rastered image of the reflection to a file
        image_string=' '.join(str(e) for e in reflection_array)

        reflection_image.close() 

    @scan.initializer
    def initialize(self):
        log_to_screen(DEBUG)
        print('initializing jog...')
        attocube = ANC350()
        self.attocube.initialize()
        return

    @scan.finalizer
    def finalize(self):
        self.attocube.finalize()
        print('finalizing jog...')
        return

    @Element(name='select axis')
    def toggle_params(self):
        params = [
        ('axis0_toggle', {'type': bool}),
        ('axis1_toggle', {'type': bool}),
        ('axis2_toggle', {'type': bool}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='positon parameters')
    def position_params(self):
        params = [
        ('axis0_position', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ('axis1_position', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ('axis2_position', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='moveby parameters')
    def moveby_params(self):
        params = [
        ('axis0_move', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ('axis1_move', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ('axis2_move', {'type': float, 'default': 1e-6, 'units': 'm'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='jog parameters')
    def jog_params(self):
        params = [
        ('axis0_speed', {'type': float, 'default': 1,}),
        ('axis1_speed', {'type': float, 'default': 1,}),
        ('axis2_speed', {'type': float, 'default': 1,}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='scan parameters')
    def scan_params(self):
        params = [
        ('filename', {'type':str, 'default':'fiberspectroscopy'}),
        ('xaxis', {'type': list, 'values': (0,1,2), 'default':1}),
        ('yaxis', {'type': list, 'values': (0,1,2), 'default':2}),
        ('zaxis', {'type': list, 'values': (0,1,2), 'default':0}),
        ('xfreq', {'type': float, 'default': 1001, 'units':'Hz'}),
        ('yfreq', {'type': float, 'default': 1000, 'units':'Hz'}),
        ('zfreq', {'type': float, 'default': 1000, 'units':'Hz'})
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Power')
    def latest(self):
        p = LinePlotWidget()
        p.plot('Power')
        return p

    @latest.on(scan.acquired)
    def latest_update(self, ev):
        w = ev.widget
        data = self.data
        w.set('Power', xs=data.x, ys=data.y)
        return


