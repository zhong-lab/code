import numpy as np
import pyqtgraph as pg
import csv
import sys
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import time
import random
#import nidaqmx

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import HeatmapPlotWidget,LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget


from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs.pm100d import PM100D

class ALIGNMENT(Spyrelet):
    requires = {
    'pmd': PM100D

    }
    attocube=ANC350()

    attocube.initialize()
    axis_index_x=0
    axis_index_y=1
    axis_index_z=2

    # if you use the daq
    #daq = nidaqmx.Task()
    #daq.ai_channels.add_ai_voltage_chan("Dev1/ai6")

    @Task(name='initialize position')
    def move2start(self):

        # gets the parameters from the scan parameters widget
        fieldValues = self.scan_parameters.widget.get()

        # set the frequency and voltage for each axis
        FREQUENCY_x=fieldValues['X Step Frequency'].magnitude
        FREQUENCY_y=fieldValues['Y Step Frequency'].magnitude
        FREQUENCY_z=fieldValues['Z Step Frequency'].magnitude

        VOLTAGE_x=fieldValues['X Step Voltage'].magnitude
        VOLTAGE_y=fieldValues['Y Step Voltage'].magnitude
        VOLTAGE_z=fieldValues['Z Step Voltage'].magnitude

        self.x_start = fieldValues['X start'].magnitude*1e6
        self.z_start = fieldValues['Z start'].magnitude*1e6

        # send the voltage/frequency settings to the controller
        self.attocube.frequency[self.axis_index_x]=Q_(FREQUENCY_x,'Hz')
        self.attocube.frequency[self.axis_index_y]=Q_(FREQUENCY_y,'Hz')
        self.attocube.frequency[self.axis_index_z]=Q_(FREQUENCY_z,'Hz')
        self.attocube.amplitude[self.axis_index_x]=Q_(VOLTAGE_x,'V')
        self.attocube.amplitude[self.axis_index_y]=Q_(VOLTAGE_y,'V')
        self.attocube.amplitude[self.axis_index_z]=Q_(VOLTAGE_z,'V')

        print('here')
        print('self.zstart:'+str(self.z_start))
        print('driving to: '+str(self.z_start-200))
        self.attocube.position[self.axis_index_z]=self.z_start-200
        time.sleep(1)
        print('driving to: '+str(self.z_start))
        self.attocube.position[self.axis_index_z]=self.z_start

        print('move complete')
        time.sleep(1)
        print('self.xstart:'+str(self.x_start))
        print('driving to: '+str(self.x_start-200))
        self.attocube.position[self.axis_index_x]=self.x_start-200
        time.sleep(1) # sleep time to get feedback from the closed loop
        print('driving to: '+str(self.x_start))
        # The the attocube drives to the starting point.
        self.attocube.position[self.axis_index_x]=self.x_start
        return



    # a task that scans the xz axis
    @Task(name='Scan XZ')
    def ReflectionDistribution(self):
        self.F = open(self.filename+'.dat', 'w')

        self.pw=np.zeros((self.z_steps,self.x_steps)) # make an empty array

        # set the frequency and voltage for the z axis
        self.attocube.frequency[self.axis_index_z]=Q_(self.movef_z,'Hz')
        self.attocube.amplitude[self.axis_index_z]=Q_(self.jogv_z,'V')

        # attocube moves to the starting z point, initially overshoots by 150um
        # and then drives back to the correct location
        print('self.zstart:'+str(self.z_start))
        print('driving to: '+str(self.z_start-200))
        self.attocube.position[self.axis_index_z]=self.z_start-200
        time.sleep(1)
        print('driving to: '+str(self.z_start))
        self.attocube.position[self.axis_index_z]=self.z_start
        time.sleep(1)

        set.attocube.amplitude[self.axis_index_z]=Q(self.movev_z,'V')

        i = 0
        while i<self.z_steps: # the attocube moves to a set of positions
            # the attocube moves to the starting x position and overshoots by
            # -150um. Attocube says this must be at least 100um to make the
            # movement repeatable.

            # set the frequency and voltage for the x axis
            self.attocube.frequency[self.axis_index_x]=Q_(self.movef_x,'Hz')
            self.attocube.amplitude[self.axis_index_x]=Q_(self.jogv_x,'V')

            print('self.xstart:'+str(self.x_start))
            print('driving to: '+str(self.x_start-200))

            self.attocube.position[self.axis_index_x]=self.x_start-200
            time.sleep(1) # sleep time to get feedback from the closed loop
            print('driving to: '+str(self.x_start))
            # The the attocube drives to the starting point.
            self.attocube.position[self.axis_index_x]=self.x_start
            self.attocube.amplitude[self.axis_index_x]=Q_(self.movev_x,'V')

            self.attocube.single_step(self.axis_index_z,1)

            # scan the along the x axis for this row
            j = 0
            while j < self.x_steps:
                self.attocube.single_step(self.axis_index_x,1)
                #self.pw[i,j] = self.daq.read() # save the power at this point
                p1=self.pmd.power.magnitude*1000
                time.sleep(0.1)
                p2=self.pmd.power.magnitude*1000
                time.sleep(0.1)
                p3=self.pmd.power.magnitude*1000
                p=(p1+p2+p3)/3
                time.sleep(0.1)
                self.pw[i,j]=p
                j=j+1 # increment the array index for the x coordinate
            i = i+1 # increment the array index for the z coordinate

            # print some data to the console about scan progress
            #print("%d/%d:%f"%(zpoint,self.z_steps,self.attocube.position[self.axis_index_x].magnitude))

            # write the power array to the reflection distribution variable
            self.F.write('\n')
            values = {
                    'power': self.pw
                }
            self.ReflectionDistribution.acquire(values)
        self.F.close()
        return

    # a task that...
    @Task(name = 'Single Step')
    def ReflectionvsTime(self):

        # gets the parameters from the scan parameters widget
        fieldValues = self.scan_parameters.widget.get()

        # set the frequency and voltage for each axis
        FREQUENCY_x=fieldValues['Drive Frequency'].magnitude
        FREQUENCY_y=fieldValues['Drive Frequency'].magnitude
        FREQUENCY_z=fieldValues['Drive Frequency'].magnitude
        VOLTAGE_x=fieldValues['X Step Voltage'].magnitude
        VOLTAGE_y=fieldValues['Y Step Voltage'].magnitude
        VOLTAGE_z=fieldValues['Z Step Voltage'].magnitude

        # send the voltage/frequency settings to the controller
        self.attocube.frequency[self.axis_index_x]=Q_(FREQUENCY_x,'Hz')
        self.attocube.frequency[self.axis_index_y]=Q_(FREQUENCY_y,'Hz')
        self.attocube.frequency[self.axis_index_z]=Q_(FREQUENCY_z,'Hz')
        self.attocube.amplitude[self.axis_index_x]=Q_(VOLTAGE_x,'V')
        self.attocube.amplitude[self.axis_index_y]=Q_(VOLTAGE_y,'V')
        self.attocube.amplitude[self.axis_index_z]=Q_(VOLTAGE_z,'V')


        self.xs=[]
        self.ys=[]
        t0 = time.time() # time at the start of the task

        while True:
            t1 = time.time() # current time
            t = t1-t0 # time since the task started

            self.xs.append(t) # append the time to the x variable
            #self.ys.append(self.daq.read()) # append the power to the y variable
            self.ys.append(self.pmd.power.magnitude*1000)

            # not really sure what the point of the following is...
            values = {
                'x': self.xs,
                'y': self.ys,
            }

            # if the length of this array exceeds 400 elements, then reset the
            # length of the x and y arrays to be the most recent 300 elements
            if(len(self.xs)>400):
                self.xs=self.xs[300:]
                self.ys=self.ys[300:]

            # not really sure why...
            self.ReflectionvsTime.acquire(values)
            time.sleep(0.05) # the time spacing between each xs data point
        return

    # this task gets the current position of the attocube x,y, and z axes
    @Task(name = 'Position')
    def Position(self):
        while True:
            self.x=self.attocube.position[self.axis_index_x].magnitude
            self.y=self.attocube.position[self.axis_index_y].magnitude
            self.z=self.attocube.position[self.axis_index_z].magnitude

            # don't really understand the point of acquiring the "values"
            values = {
                'x': self.x,
                'y': self.y,
                'z': self.z,
            }
            self.Position.acquire(values)
            time.sleep(0.05)
        return

    #  define 2D plot
    @Element(name='2D plot')
    def plot2d(self):
        p = HeatmapPlotWidget()
        return p

    # updates the 2D plot
    @plot2d.on(ReflectionDistribution.acquired)
    def _plot2d_update(self, ev):
        w = ev.widget
        im = np.array(self.pw)
        # not sure what the "set" function does
        w.set(im)
        return

    # sets up some formatting of x, y, and z positions
    @Element(name='indicator')
    def position_now(self):
        text = QTextEdit()
        text.setPlainText('x: non um \ny: non um \nz: non um \n')
        return text

    # more formatting of the position units
    @position_now.on(Position.acquired)
    def _position_now_update(self,ev):
        w=ev.widget
        w.setPlainText('x: %f um \ny: %f um \nz: %f um \n'%(self.x,self.y,self.z))
        return

    # boxes to enter scan parameters
    @Element(name='Scan Parameters')
    def scan_parameters(self):

        # set the default x axis position to 3000um
        # set the default z axis position to 2500um
        # set the movement voltage to 20V. This is a minimum for actuation
        # at room temperature
        # do not exceed 45V at room temperature
        # set the default step frequency to be 500Hz for both axis
        params = [
        ('File name', {'type': str, 'default': 'D:\\Data\\CW_cavity'}),
        ('X start', {'type': float, 'default': 3000*1e-6, 'units':'m'}),
        ('X steps', {'type': float, 'default': 50}),
        ('Z start', {'type': float, 'default': 2500*1e-6, 'units':'m'}),
        ('Z steps', {'type': float, 'default': 50}),
        ('X Step Voltage',{'type':float,'default':15,'units':'V'}),
        ('Y Step Voltage',{'type':float,'default':15,'units':'V'}),
        ('Z Step Voltage',{'type':float,'default':40,'units':'V'}),
        ('X Step Frequency',{'type':float,'default':500,'units':'V'}),
        ('Y Step Frequency',{'type':float,'default':500,'units':'V'}),
        ('Z Step Frequency',{'type':float,'default':500,'units':'V'}),
        ('Drive Voltage',{'type':float,'default':40,'units':'V'}),
        ('Drive Frequency', {'type': float, 'default': 500, 'units':'Hz'})
        ]
        w = ParamWidget(params)
        return w

    # the 1D plot widget is used for the power vs. time plot
    @Element(name='1D plot')
    def plot1d(self):
        p = LinePlotWidget()
        p.plot('Reflection')
        return p

    # more code for the power vs. time plot
    @plot1d.on(ReflectionvsTime.acquired)
    def _plot1d_update(self, ev):
        w = ev.widget
        xs = np.array(self.xs)
        ys = np.array(self.ys)
        if (len(xs)>len(ys)):
            xs = xs[:len(ys)]
        w.set('Reflection',xs=xs,ys=ys)
        return

    # a function that stops the attocube while it is scanning
    @Element(name='stop')
    def stopbutton(self):
        button7 = QPushButton('STOP')
        button7.move(0,20)
        button7.clicked.connect(self.stopmoving) #direction :-z
        return button7
    def stopmoving(self):
        self.attocube.stop()
        return

    # a button that moves the attocube by 1 step forward in the x direction
    @Element(name='+x')
    def x_forward(self):
        button1 = QPushButton("x +")
        button1.move(0,20)
        button1.clicked.connect(self.move_x1) #direction :+x
        return button1
    def move_x1(self):
        print('x1')
        self.attocube.single_step(self.axis_index_x,+1)
        return

    # a button that moves the attocube by 1 step backward in the x direction
    @Element(name='-x')
    def x_backward(self):
        button2 = QPushButton('x -')
        button2.move(0,20)
        button2.clicked.connect(self.move_x2) #direction :-x
        return button2
    def move_x2(self):
        print('x2')
        self.attocube.single_step(self.axis_index_x,-1)
        return

    # a button that moves the attocube by 1 step up in the z direction
    @Element(name='+z')
    def z_forward(self):
        button3 = QPushButton(" z +")
        button3.move(0,20)
        button3.clicked.connect(self.move_z1) #direction :+z
        return button3
    def move_z1(self):
        print('z1')
        self.attocube.single_step(self.axis_index_z,+1)
        return

    # a button that moves the attocube by 1 step down in the z direction
    @Element(name='-z')
    def z_backward(self):
        button4 = QPushButton('z -')
        button4.move(0,20)
        button4.clicked.connect(self.move_z2) #direction :-z
        return button4
    def move_z2(self):
        print('z2')
        self.attocube.single_step(self.axis_index_z,-1)
        return

    # a button that moves the attocube by 1 step forward in the y direction
    @Element(name='+y')
    def y_forward(self):
        button5 = QPushButton("y +")
        button5.move(0,20)
        button5.clicked.connect(self.move_y1) #direction :+z
        return button5
    def move_y1(self):
        print('y1')
        self.attocube.single_step(self.axis_index_y,+1)
        return

    # a button that moves the attocube by 1 step backward in the y direction
    @Element(name='-y')
    def y_backward(self):
        button6 = QPushButton('y -')
        button6.move(0,20)
        button6.clicked.connect(self.move_y2) #direction :-z
        return button6
    def move_y2(self):
        print('y2')
        self.attocube.single_step(self.axis_index_y,-1)
        return

    # some initialization for the xz scan code
    @ReflectionDistribution.initializer
    def initialize(self):
        print('initializing')
        fieldValues = self.scan_parameters.widget.get()
        self.movef_x=fieldValues['X Step Frequency'].magnitude
        self.movef_y=fieldValues['Y Step Frequency'].magnitude
        self.movef_z=fieldValues['Z Step Frequency'].magnitude

        self.jogf = fieldValues['Drive Frequency'].magnitude

        self.movev_x=fieldValues['X Step Voltage'].magnitude
        self.movev_y=fieldValues['Y Step Voltage'].magnitude
        self.movev_z=fieldValues['Z Step Voltage'].magnitude
        self.jogv_x=fieldValues['Drive Voltage'].magnitude
        self.jogv_y=fieldValues['Drive Voltage'].magnitude
        self.jogv_z=fieldValues['Drive Voltage'].magnitude

        self.x_start = fieldValues['X start'].magnitude*1e6
        self.z_start = fieldValues['Z start'].magnitude*1e6
        self.filename = fieldValues['File name']
        self.x_steps=int(fieldValues['X steps'])
        self.z_steps=int(fieldValues['Z steps'])

        self.pw = np.zeros((self.x_steps,self.z_steps),dtype=float)

        #initialize
        self.attocube.frequency[self.axis_index_x]=Q_(self.movef_x,'Hz')
        self.attocube.frequency[self.axis_index_y]=Q_(self.movef_y,'Hz')
        self.attocube.frequency[self.axis_index_z]=Q_(self.movef_z,'Hz')

        self.attocube.amplitude[self.axis_index_x]=Q_(self.movev_x,'V')
        self.attocube.amplitude[self.axis_index_y]=Q_(self.movev_y,'V')
        self.attocube.amplitude[self.axis_index_z]=Q_(self.movev_z,'V')

        # initialize by driving to the beginning point of the scan
        self.attocube.absolute_move(self.axis_index_x,self.x_start)
        time.sleep(1)
        self.attocube.absolute_move(self.axis_index_z,self.z_start)
        time.sleep(1)
        print('initialized') # print a message to the console
        return

    # finalizes the scan
    @ReflectionDistribution.finalizer
    def finalize(self):
        return
