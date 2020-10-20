# full chip
import gdspy
import sys
sys.path.append("../..")
from photonics import *

# define the layers
# 1 layer for the ebeam lithography
# 1 layer for the optical lithography
ld_ebeam={'layer':1,'datatype':0}
ld_opt={'layer':2,'datatype':0}
ld_phc={'layer':3,'datatype':0}
ld_opt_2={'layer':4,'datatype':0}
ld_box={'layer':6,'datatype':0}

# pattern the disk on a separate layer so it gets its own dose
ld_disc={'layer':5,'datatype':0}

# PUT THE LAST BEST WAVEGUIDE WIDTH AND HOLE RADIUS MEASURED FROM SEM
WG_W=0.486
HOLE_DIAM=0.187
TAPER=0.78 # measurements should be redone
SPACING=0.347 # measurements should be redone

# THE HOLE RADIUS IS HALF THE HOLE DIAMETER
HOLE_RAD=HOLE_DIAM/2

# PARAMETERS TO BIAS THE PHOTONIC CRYSTAL DESIGN DURING A CALIBRATION RUN
HOLE_BIAS=1.04822
WG_W_BIAS=1.0012



SPACING_BIAS=1.01249
RAD_BIAS=1
TAPER_BIAS=1

# PUT THE LAST BEST WAVEGUIDE WIDTH AND HOLE RADIUS MEASURED FROM SEM
WG_W=0.486
HOLE_DIAM=0.187
TAPER=0.78 # measurements should be redone
SPACING=0.347 # measurements should be redone

# define relevant default parameters
params={}
params['wg_len']=200
params['wg_width']=0.550
params['radius']=20*RAD_BIAS
params['disc_loc']=60
params['dist']=0.22
params['ebeam_layer']=ld_ebeam
params['opt_litho_layer']=ld_opt
params['padding']=6
params['clearance']=3
params['supp_width']=2
params['supp_len']=2
params['tether_sp']=25
params['tether_tri']=40
params['min_taper_width']=0.16
params['taper_len']=17.5
params['coupling_sp']=5
params['mirror_holes']=20
params['disc_layer']=ld_disc

# SCALE THE MIRROR HOLE RADIUS BY RATIO OF THE DESIRED WAVEGUIDE WIDTH TO THE
# IDEAL WAVEGUIDE WIDTH
sc=params['wg_width']/WG_W

params['mirror_rad']=sc*HOLE_RAD*HOLE_BIAS

# EVENTUALLY REPLACE THIS WITH THE MEASURED SPACING SCALING FROM SEM
params['mirror_sp']=SPACING*SPACING_BIAS*sc

# define the number of copies of a given ring pattern
COPIES=1

# define the overall scaling parameter (will be set during ebeam calibration)
# 1 means no scaling
SA=1

X_MIN=-8000
Y_MAX=5345

# define a device spacing of 50um + extra space defined by thte radius of the ring
DEVICE_SPACING=200

RING_SPACINGS=[0.1,0.15,0.2]

SUBFIELD_SPACING=1000

DICING=270+150-2*params['padding']

# create the main cell
main=gdspy.Cell('MAIN')


# sweep the spacing of the disc from the waveguide
for i in range(len(RING_SPACINGS)):
	params['dist']=RING_SPACINGS[i]


	# add reference 3 copies of the same ring pattern
	for j in range(COPIES):
		# pass in parameter to give a unique name to each cell
		# the name should be a string
		if (i==0 or i==2):
			continue


		disc_args={}
		params['wg_width']=0.550*WG_W_BIAS*sc
		params['radius']=20
		params['mirror_rad']=sc*HOLE_RAD*HOLE_BIAS
		params['mirror_sp']=SPACING*SPACING_BIAS*sc

		params['name']=[i,j,params['radius']]


		# add the disc to a cell

		# regenerate the pattern with the different spacings
		# call generate the ring-resonator geometry
		#wg,disc,rect,opt_rect,supp_ref,tether_list,taper_ref,l_tot,shift=boxed_ring(**params)
		sub,disc,wg,suppRef,tetherRefList,taper,txtRect,opt_rectangle=discWg(20,(0,0),3,RING_SPACINGS[i],0.5,20,0.1,0.4,(0,0),1,1,6.8,0.1,1,1,6,5,1,str(RING_SPACINGS[i]),1,ld_disc,ld_ebeam,0.16,17.5,ld_opt,ld_disc)

		# add all these parameters to a cell
		pat=gdspy.Cell('pattern'+' '+str(params['name']))
		pat.add([sub,disc,wg,suppRef,taper,txtRect,opt_rectangle])
		pat.add(tetherRefList)

		# pat.add([wg,disc])
		# pat.add(rect)
		# pat.add(opt_rect)
		# pat.add(supp_ref)
		# pat.add(tether_list)
		# pat.add(taper_ref)


		# now rotate the cell by 90 degrees and offset to the cell position
		pat_ref=gdspy.CellReference(pat,
			(X_MIN+500+j*DEVICE_SPACING+i*SUBFIELD_SPACING,Y_MAX),rotation=90)

		# old line for adding a disc without a waveguide
		#disc_ref=gdspy.CellReference(disc_cell,(X_MIN+j*DEVICE_SPACING+i*SUBFIELD_SPACING,Y_MAX-DICING-160))
		main.add(pat_ref)

	for k in range(COPIES):
		# pass in parameter to give a unique name to each cell
		# the name should be a string

		disc_args={}
		params['wg_width']=0.550*WG_W_BIAS*sc
		params['radius']=20
		params['mirror_rad']=sc*HOLE_RAD*HOLE_BIAS
		params['mirror_sp']=SPACING*SPACING_BIAS*sc

		params['name']=[i,k,params['radius']]


		# add the disc to a cell

		# regenerate the pattern with the different spacings
		# call generate the ring-resonator geometry
		#wg,disc,rect,opt_rect,supp_ref,tether_list,taper_ref,l_tot,shift=boxed_ring(**params)
		sub,disc,wg,suppRef,tetherRefList,taper,txtRect,opt_rectangle=discWg_NS(20,(0,0),3,RING_SPACINGS[i],0.5,20,0.1,0.4,(0,0),1,1,6.8,0.1,1,1,6,5,1,str(RING_SPACINGS[i])+'NS',1,ld_disc,ld_ebeam,0.16,17.5,ld_opt,ld_disc)

		# add all these parameters to a cell
		pat=gdspy.Cell('pattern_NS'+' '+str(params['name']))
		pat.add([sub,disc,wg,suppRef,taper,txtRect,opt_rectangle])
		pat.add(tetherRefList)

		# pat.add([wg,disc])
		# pat.add(rect)
		# pat.add(opt_rect)
		# pat.add(supp_ref)
		# pat.add(tether_list)
		# pat.add(taper_ref)


		# now rotate the cell by 90 degrees and offset to the cell position
		pat_ref=gdspy.CellReference(pat,
			(X_MIN+500+k*DEVICE_SPACING+i*SUBFIELD_SPACING+SUBFIELD_SPACING/2,Y_MAX),rotation=90)

		# old line for adding a disc without a waveguide
		#disc_ref=gdspy.CellReference(disc_cell,(X_MIN+j*DEVICE_SPACING+i*SUBFIELD_SPACING,Y_MAX-DICING-160))
		main.add(pat_ref)

# add text
microdisk_fiber_label=gdspy.Text('MICRODISK+LENSED FIBER',128,(X_MIN+1500,Y_MAX+1000),**ld_opt)
# microdisk_label=gdspy.Text('MICRODISK',128,(X_MIN+2500,Y_MAX-DICING-1000),**ld_opt)
main.add(microdisk_fiber_label)
#main.add(microdisk_label)




# sweep the spacing of the ring from the waveguide
for i in range(len(RING_SPACINGS)):
	params['dist']=RING_SPACINGS[i]


	# add reference 3 copies of the same ring pattern
	for j in range(COPIES):
		# pass in parameter to give a unique name to each cell
		# the name should be a string


		disc_args={}
		params['wg_width']=0.550*WG_W_BIAS*sc
		params['radius']=20
		params['mirror_rad']=sc*HOLE_RAD*HOLE_BIAS
		params['mirror_sp']=SPACING*SPACING_BIAS*sc

		params['name']=[i,j,params['radius']]


		# add the disc to a cell

		# regenerate the pattern with the different spacings
		# call generate the ring-resonator geometry
		#wg,disc,rect,opt_rect,supp_ref,tether_list,taper_ref,l_tot,shift=boxed_ring(**params)
		#sub,disc,wg,suppRef,tetherRefList,taper,txtRect,opt_rectangle=discWg(20,(0,0),3,RING_SPACINGS[i],0.5,20,0.1,0.4,(0,0),1,1,6.8,0.1,1,1,6,5,1,str(RING_SPACINGS[i]),1,ld_disc,ld_ebeam,0.16,17.5,ld_opt,ld_disc)

		ring,wg,taper=ring_wg(100,0.528,ld_ebeam,ld_opt,0,RING_SPACINGS[i],0.5,20,0.1,0.4,(0,0),1,1,10,0.1,1,1,6,5,1,str(RING_SPACINGS[i])+'ring',1,0.16,17.5,ld_opt,ld_disc)

		# add all these parameters to a cell
		pat=gdspy.Cell('pattern_ring'+' '+str(params['name']))
		pat.add([ring,wg,taper])

		# pat.add([wg,disc])
		# pat.add(rect)
		# pat.add(opt_rect)
		# pat.add(supp_ref)
		# pat.add(tether_list)
		# pat.add(taper_ref)


		# now rotate the cell by 90 degrees and offset to the cell position
		pat_ref=gdspy.CellReference(pat,
			(X_MIN+500+j*DEVICE_SPACING+i*SUBFIELD_SPACING+10000,Y_MAX),rotation=90)

		# old line for adding a disc without a waveguide
		#disc_ref=gdspy.CellReference(disc_cell,(X_MIN+j*DEVICE_SPACING+i*SUBFIELD_SPACING,Y_MAX-DICING-160))
		main.add(pat_ref)


# add text
microring_taper_label=gdspy.Text('MICRORING+TAPERED FIBER',128,(X_MIN+1500+10000,Y_MAX+1000),**ld_opt)
# microdisk_label=gdspy.Text('MICRODISK',128,(X_MIN+2500,Y_MAX-DICING-1000),**ld_opt)
main.add(microring_taper_label)






# sCavity_params={}

# # to bias the hole diameter add a parameter that scales the hole radius
# sCavity_params['radius']=0.107*HOLE_BIAS # radius from simulation
# sCavity_params['taper_depth']=0.8*TAPER_BIAS # taper from simulation

# # EVENTUALLY REPLACE THIS WITH THE HOLE SPACING MEASURED FROM SEM
# sCavity_params['spacing']=0.397*SPACING_BIAS # spacing from simulation

# sCavity_params['input_taper_holes']=3
# sCavity_params['input_taper_percent']=0.25
# sCavity_params['layer_phc']=ld_phc
# sCavity_params['wg_width']=0.536*WG_W_BIAS # width from simulation
# sCavity_params['extra_space']=1
# sCavity_params['layer_wg']=ld_ebeam
# sCavity_params['support_width']=1
# sCavity_params['support_length']=1
# sCavity_params['taper_width']=0.16
# sCavity_params['taper_length']=17.5
# sCavity_params['tether_width']=0.11
# sCavity_params['tether_length']=5
# sCavity_params['tip_space']=5
# sCavity_params['clearance']=2
# sCavity_params['opt_litho_layer']=ld_opt
# sCavity_params['padding']=1.5
# sCavity_params['boxLayer']=ld_box

# PHC_COPIES=3
# INPUT_TAPERS=[5,6,7,8,9]
# CAVITY_TAPERS=[9]
# PHC_SPACING=50
X_RIGHT=2000
Y_MIN=-5000+345
# PHC_DICING=270+150-2*sCavity_params['padding']
PHC_TXT_HEIGHT=1

# # keep a list of the lengths of each cavity to make sure that they all end up by the edge
# lenlist=[]
# slenlist=[]

# for i in INPUT_TAPERS:
# 	# create 3 copies of each device spaced 50nm apart
# 	for j in range(PHC_COPIES):
# 		for k in range(len(CAVITY_TAPERS)):
# 			offset=(j-1)*PHC_SPACING+(i-1)*(4*PHC_SPACING)+(k-1)*(42*PHC_SPACING)

# 			sCavity_params['normal_holes']=i
# 			sCavity_params['taper_holes']=CAVITY_TAPERS[k]
# 			sCavity_params['cell_name']=str(i)+'-'+str(j)+'-'+str(k)+'-SIM'
# 			# first call the phc_wg function to get the cavity cell, bounding box geometry, and length of pattern
# 			scavity,sbounding_rect,stotal_len,stotal_width,srect_shift,sopt_rectangle=phc_wg(**sCavity_params)



# 			slabel=txt_label([i,k,j])

# 			sbounding_text=text_rect(sbounding_rect,stotal_len,stotal_width,slabel,PHC_TXT_HEIGHT,ld_box,srect_shift)

# 			slabeled_cavity=cavity_text(sbounding_text,scavity,str(i)+'-'+str(j)+'-'+str(k)+'-SIM',sopt_rectangle)

# 			# keep a list of the length of each cavity
# 			slenlist.append(stotal_len)

# 			# want to shift the location of each cavity according to the length
# 			# of each so the tips are all the same distance form the edge of the
# 			# chip
# 			# the cavities should get longer according to this scheme so they are
# 			# shifted up to compensate
# 			if i==1:
# 				diff=0
# 			else:
# 				print(i)
# 				print(len(slenlist))
# 				diff=(slenlist[-1]-slenlist[0])

# 			# make the rectangle for
# 			slabeled_cav_ref=gdspy.CellReference(slabeled_cavity,(offset+1000+X_RIGHT+2000,diff/2+Y_MAX+3.5))

# 			# now rotate the set and translate down 420um
# 			#cav_flipped_ref=gdspy.CellReference(labeled_cavity,(offset+X_RIGHT+2000,-diff/2+Y_MAX-DICING-64),rotation=180)

# 			# now copy the pattern to the lower left hand corner for the test involving a lower oxygen flow
# 			#lowerO2_ref=gdspy.CellReference(labeled_cavity,(offset+X_MIN+2000,diff/2+Y_MIN))

# 			#lowerO2_flipped_ref=gdspy.CellReference(labeled_cavity,(offset+X_MIN+2000,-diff/2+Y_MIN-DICING-64),rotation=180)

# 			main.add([slabeled_cav_ref])
# 			#main.add([lowerO2_ref,lowerO2_flipped_ref])



# # add the dicing street pattern to each set of devices
# dicing_params={}
# dicing_params['w']=270+150
# dicing_params['l']=6000
# dicing_params['offset']=(X_MIN+2900,Y_MAX-339+sCavity_params['padding'])
# dicing_params['layer']=ld_opt_2
# dicing1=dicing_street(**dicing_params)
# dicing_params['offset']=(X_RIGHT+2900,Y_MAX-241+sCavity_params['padding']+5)
# dicing_params['l']=7000
# dicing2=dicing_street(**dicing_params)
# dicing_params['offset']=(X_MIN+2900,Y_MIN-241+sCavity_params['padding'])
# dicing3=dicing_street(**dicing_params)
# #main.add(dicing1)
# main.add(dicing2)
# main.add(dicing3)

dicing_params={}
dicing_params['w']=270+150
dicing_params['l']=6000
dicing_params['offset']=(X_MIN+2900,Y_MAX-259+params['padding'])
dicing_params['layer']=ld_opt_2
dicing1=dicing_street(**dicing_params)
main.add(dicing1)

dicing_params={}
dicing_params['w']=270+150
dicing_params['l']=6000
dicing_params['offset']=(X_MIN+2900+10000,Y_MAX-259+params['padding']-25-60)
dicing_params['layer']=ld_opt_2
dicing2=dicing_street(**dicing_params)
main.add(dicing2)




# cavity_label=gdspy.Text('PHOTONIC CRYSTAL CAVITIES / 12-19-19 / BATCH 1 / CHIP 1',
# 	128,(X_RIGHT,Y_MAX+1000),**ld_opt)
# cavity_label_bottom=gdspy.Text('PHOTONIC CRYSTAL CAVITIES / 12-19-19 / BATCH 1 / CHIP 2',
# 	128,(X_RIGHT,Y_MAX-DICING-1000),**ld_opt)
# lowO2_label=gdspy.Text('PHOTONIC CRYSTAL CAVITIES / 12-19-19 / BATCH 2 / CHIP 1',
# 	128,(X_MIN,Y_MIN+1000),**ld_opt)
# lowO2_label_bottom=gdspy.Text('PHOTONIC CRYSTAL CAVITIES / 12-19-19 / BATCH 2 / CHIP 2',
# 	128,(X_MIN,Y_MIN-DICING-1000),**ld_opt)
# main.add(cavity_label)
# main.add(cavity_label_bottom)
# main.add(lowO2_label)
# main.add(lowO2_label_bottom)

# now create the etch test patterns
# these will just be photonic_crystal patterns without the surrounding box
# test_params={}
# test_params['taper_holes']=9
# test_params['radius']=0.107
# test_params['taper_depth']=0.8
# test_params['spacing']=0.396
# test_params['input_taper_holes']=3
# test_params['input_taper_percent']=0.25
# test_params['layer_phc']=ld_phc
# test_params['wg_width']=0.536
# test_params['extra_space']=1
# test_params['layer_wg']=ld_ebeam
# test_params['support_width']=1
# test_params['support_length']=1
# test_params['taper_width']=0.16
# test_params['taper_length']=17.5
# test_params['tether_width']=0.1
# test_params['tether_length']=5
# test_params['tip_space']=5
# test_params['clearance']=2
# test_params['opt_litho_layer']=ld_opt
# test_params['padding']=0
# test_params['normal_holes']=6
# test_params['cell_name']='test'

# now need to add alignment marks between the ebeam and optical pattern for HSQ
# add alignment marks to pattern
alignment_cross=alignment_mark(10,100,ld_opt)
alignment_cross_ebeam=alignment_mark(10,100,ld_ebeam)

# give the disks an alignment mark since they will be written with a different dose
alignment_cross_disc=alignment_mark(10,100,ld_disc)

align_cell=gdspy.Cell('alignment marks')
align_cell.add([alignment_cross,alignment_cross_ebeam,alignment_cross_disc])
alignment_cell=gdspy.CellArray(align_cell,2,2,(18000,16000),(-9000,-8000))
main.add(alignment_cell)

# now add alignment marks for the dicing street for each chip
DSE_alignment_cross=alignment_mark(20,200,ld_opt)
DSE_cell=gdspy.Cell('DSE alignment marks')
DSE_cell.add(DSE_alignment_cross)
DSE1=gdspy.CellArray(DSE_cell,2,2,(7000,4000),(X_MIN-500,Y_MAX-2000))
DSE2=gdspy.CellArray(DSE_cell,2,2,(7000,4000),(X_RIGHT-500,Y_MAX-2000))
DSE3=gdspy.CellArray(DSE_cell,2,2,(7000,4000),(X_MIN-500,Y_MIN-2000))
main.add([DSE1,DSE2,DSE3])

main_ref=gdspy.CellReference(main)

final=gdspy.Cell('Final')
final.add(main_ref)
#gdspy.top_level()

gdspy.write_gds('07-19-20_disks_rings.gds')
gdspy.LayoutViewer()
