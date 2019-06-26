""" Script for attocube xy-scanning to image reflected power
written by Christina Wicker on 03/02/19
at a fixed z position, this script scans the x and y axes
and outputs an intensity profile measured on the power meter
"""

import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from lantz.log import log_to_screen, DEBUG
from lantz import Q_
from lantz.drivers.attocube import ANC350
from lantz.drivers.thorlabs import PM100D
from lantz.log import log_to_screen, DEBUG

#log_to_screen(DEBUG)
#from attocube_spyrelet import Attocube
#from anc350 import ANC350

# name of file to write image of reflection spectrum:
FILENAME='FILENAME'

## MAKE SURE TO SET THE FREQUENCY BEFOREHAND ##
# set the frequency that the attocube will drive in open-loop mode
# Christina set this to 1000Hz as default
FREQUENCY_x=1300
FREQUENCY_y=1300
FREQUENCY_z=1000
print('here2')

# CHANGE THESE VALUES ACCORDING TO HOW THE ATTOCUBE IS WIRED #
## MAKE SURE THAT IN ADDITION TO CORRECT CABLING THE CORRECT . LUT FILES ARE
## LOADED ##
## MAY REQUIRE SOME TESTING ##
### in the future may want to write a function that fills these out automatically
#### based on the setting inside the controller ####
axis_index_x=1
axis_index_y=2
axis_index_z=0

# the x,y axes have a range of 6mm #
## making a 600x600 pixel image ##
### 100 points per mm ###
#### 1/10mm=100um,1/100mm=10um ####
##### going to take steps of 10um #####
###### change this for more resolution ######
num_pixels_x=5
num_pixels_y=5

# range of each axis in um
x_range=6000
y_range=5000
z_range=5000

# first try to initialize the attocube
attocube=ANC350()

attocube.initialize()

# VOLTAGE WILL NEED TO BE ADJUSTED AT CRYOGENIC TEMPERATURES #
## VALUES SET TO YIZHONG'S CALIBRATION AT ROOM TEMPERATURE ##
VOLTAGE_x=70
VOLTAGE_y=70
VOLTAGE_z=40

start_pos_x=350
start_pos_y=600
attocube.frequency[axis_index_x]=Q_(FREQUENCY_x,'Hz')
attocube.frequency[axis_index_y]=Q_(FREQUENCY_y,'Hz')
attocube.frequency[axis_index_z]=Q_(FREQUENCY_z,'Hz')


attocube.amplitude[axis_index_x]=Q_(VOLTAGE_x,'V')
attocube.amplitude[axis_index_y]=Q_(VOLTAGE_y,'V')
attocube.amplitude[axis_index_z]=Q_(VOLTAGE_z,'V')

"""
attocube.frequency[axis_index_x]=FREQUENCY_x
attocube.frequency[axis_index_y]=Q_(FREQUENCY_y,'Hz')
attocube.frequency[axis_index_z]=Q_(FREQUENCY_z,'Hz')
"""
# may need to change initialization because it looks like the initialization
# might drive each axis back to zero? Not totally sure

# first thing to do is get the current position of the attocube 
# for the x, y, and z axes
# x axis:
x_init=attocube.position[axis_index_x]

# y axis:
y_init=attocube.position[axis_index_y]

# z axis:
z_init=attocube.position[axis_index_z]

print('X initialize start')
# Use closed loop moves to drive the attocube to 0,0 in the x,y plane
## THIS ASSUMES THAT THE CLOSED LOOP DRIVER MOVES TO ABSOLUTE POSITIONS RATHER 
attocube.cl_move(axis_index_x,Q_(start_pos_x,'um'))
print('X INITIALIZE FINISHED')
print('Y initialize start')
attocube.cl_move(axis_index_y,Q_(start_pos_y,'um'))
print('Y initialize finished')

print('start initialization of power meter')
# measuring the 
# reflectance from the power-meter
with PM100D('USB0::0x1313::0x8078::P0019269::INSTR') as power_meter:
	identification=power_meter.idn
	print(identification)
	time.sleep(5)
	print('end initialization of power meter')
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
	print('ARRAY INITIALIZED')

	# open the image file
	reflection_image=open(FILENAME+'.pgm','w')
	print('FILE OPENED')

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
			print('X,Y: '+str(pos_x)+ ','+str(pos_y))
			attocube.cl_move(axis_index_y,Q_(start_pos_x+pos_y*step_scaling_x,'um'))
			attocube.cl_move(axis_index_x,Q_(start_pos_y+pos_x*step_scaling_y,'um'))
			reflection=power_meter.power
			print('power: {}'.format(reflection))
			reflection_mag=float(reflection.magnitude)
			if reflection_mag<min_pow:
				min_pow=reflection_mag
			reflection_array[pos_y][pos_x]=reflection_mag
	print('ARRAY ITERATION FINISHED')

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