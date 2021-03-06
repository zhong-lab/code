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

# create the main cell
main=gdspy.Cell('MAIN')

sCavity_params={}

sCavity_params['taper_depth']=1 # taper from simulation

sCavity_params['input_taper_holes']=0
sCavity_params['layer_phc']=ld_phc
sCavity_params['wg_width']=0.536 # width from simulation
sCavity_params['extra_space']=1
sCavity_params['layer_wg']=ld_ebeam
sCavity_params['support_width']=3
sCavity_params['support_length']=4
sCavity_params['taper_width']=0.16
sCavity_params['taper_length']=17.5
sCavity_params['tether_width']=0.13
sCavity_params['tether_length']=2
sCavity_params['tip_space']=5
sCavity_params['clearance']=2
sCavity_params['opt_litho_layer']=ld_opt
sCavity_params['padding']=1.5
sCavity_params['boxLayer']=ld_box
sCavity_params['asym']=6
sCavity_params['taper_holes']=9
sCavity_params['spacing']=0.395
sCavity_params['meander']=-200

PHC_COPIES=3

CAVITY_TAPERS=[9]
PHC_SPACING=600
Y_MIN=-5000+345
Y_MAX=5345
X_MIN=-8000
PHC_DICING=270+150-2*sCavity_params['padding']
PHC_TXT_HEIGHT=1

TOTAL_BIAS=[0.936]
LENGTHS=[30000,15000,5000,3000,1000]
COPIES=1

# keep a list of the lengths of each cavity to make sure that they all end up by the edge
lenlist=[]
slenlist=[]

for m in range(len(TOTAL_BIAS)):
		for i in range(len(LENGTHS)):
			for j in range(COPIES):
				offset=PHC_SPACING*(j+(COPIES+1)*(i+(len(LENGTHS)+1)*m))+2000

				sCavity_params['wg_width']=0.536*TOTAL_BIAS[m] # width from simulation
				sCavity_params['radius']=0.107*TOTAL_BIAS[m] # radius from simulation
				sCavity_params['normal_holes']=6
				sCavity_params['input_taper_percent']=0.025/sCavity_params['radius']
				sCavity_params['longWg']=LENGTHS[i]

				sCavity_params['cell_name']=str(m)+'-'+str(i)+'-'+str(j)

				# first call the phc_wg function to get the cavity cell, bounding box geometry, and length of pattern
				scavity,stotal_len,stotal_width,srect_shift=phc_path(**sCavity_params)

				slabel=txt_label([m,i,j])

				#sbounding_text=text_rect(sbounding_rect,stotal_len,stotal_width,slabel,PHC_TXT_HEIGHT,ld_box,srect_shift)

				#slabeled_cavity=cavity_text(sbounding_text,scavity,sCavity_params['cell_name'],sopt_rectangle)

				# keep a list of the length of each cavity
				slenlist.append(stotal_len)

				# want to shift the location of each cavity according to the length
				# of each so the tips are all the same distance form the edge of the
				# chip
				# the cavities should get longer according to this scheme so they are
				# shifted up to compensate
				if i==1:
					diff=0
				else:
					diff=(slenlist[-1]-slenlist[0])

				# make the rectangle for
				#slabeled_cav_ref=gdspy.CellReference(slabeled_cavity,(offset+5000,diff/2+Y_MAX+3.5))
				scavity_ref=gdspy.CellReference(scavity,(6000+offset,5239),rotation=90)
				main.add([scavity_ref])

# add the dicing street pattern to each set of devices
dicing_params={}
dicing_params['w']=270+150
dicing_params['l']=7000
dicing_params['layer']=ld_opt_2
dicing_params['offset']=(10500,Y_MAX-441+sCavity_params['padding']+2)
dicing2=dicing_street(**dicing_params)
main.add(dicing2)


cavity_label=gdspy.Text('Er:SOI WAVEGUIDE / 10-04-20 ',
	128,(7000,Y_MAX+4000),horizontal=False,**ld_opt)

main.add(cavity_label)

alignment_cross=alignment_mark(10,100,ld_opt)
alignment_cross_ebeam=alignment_mark(10,100,ld_ebeam)

# give the disks an alignment mark since they will be written with a different dose
#alignment_cross_disc=alignment_mark(10,100,ld_disc)

align_cell=gdspy.Cell('alignment marks')
align_cell.add([alignment_cross_ebeam])
alignment_cell=gdspy.CellArray(align_cell,2,2,(14000,9000),(3500,3000))
main.add(alignment_cell)

# now add alignment marks for the dicing street for each chip
DSE_alignment_cross=alignment_mark(20,200,ld_opt)
DSE_cell=gdspy.Cell('DSE alignment marks')
DSE_cell.add(DSE_alignment_cross)
#DSE1=gdspy.CellArray(DSE_cell,2,2,(7000,4000),(X_MIN-500,Y_MAX-2000))
DSE2=gdspy.CellArray(DSE_cell,2,2,(13000,8000),(4000,Y_MAX-2000))
#DSE3=gdspy.CellArray(DSE_cell,2,2,(7000,4000),(X_MIN-500,Y_MIN-2000))
main.add([DSE2])

main_ref=gdspy.CellReference(main)

final=gdspy.Cell('Final')
final.add(main_ref)
#gdspy.top_level()

gdspy.write_gds('../gds/10-04-20_ErSOIwaveguide.gds')
gdspy.LayoutViewer()
