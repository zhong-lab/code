import gdspy
import math

def waveguide(w,l,layer):
	""" waveguide rectangle """

	wg=gdspy.Rectangle((-l/2,-w/2),(l/2,w/2),**layer)
	return wg

def photonic_crystal(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer): 
	""" define a parabolically tapered photonic crystal cavity. hole size
	and length are tapered simulataneously. a certain number of input taper
	holes can be defined to reduce input scattering loss. 
	also returns the length of the photonic crystal
	"""

	min_spacing=taper_depth*spacing
	dist=min_spacing/2

	holes=[]

	# add taper holes
	for i in range(taper_holes):
		if i>0:
			dist+=spacing*taper_depth+i**2*(1-taper_depth)*spacing/(taper_holes**2)
		rad=taper_depth*radius+((i**2)*(1-taper_depth)*radius/(taper_holes**2))
		hole_pos=gdspy.Round((dist,0),rad,number_of_points=199,**layer)
		hole_neg=gdspy.Round((-dist,0),rad,number_of_points=199,**layer)

		# add all holes to a list
		holes.append(hole_pos)
		holes.append(hole_neg)

	# add untapered holes
	for i in range(normal_holes):
		dist+=spacing
		hole_pos=gdspy.Round((dist,0),radius,number_of_points=199,**layer)
		hole_neg=gdspy.Round((-dist,0),radius,number_of_points=199,**layer)
		holes.append(hole_pos)
		holes.append(hole_neg)

	# add input taper
	for i in range(input_taper_holes):
		dist+=spacing
		rad=radius-radius*(1-input_taper_percent)/input_taper_holes*(i+1)
		hole_neg=gdspy.Round((-dist,0),rad,number_of_points=199,**layer)
		holes.append(hole_neg)

	l_tot=dist*2
	return holes,l_tot

def wg_support(wg_width,w,l,layer):
	""" add a support at the top of the waveguide where it attaches to the
	substrate.
	"""
	support_pts=[(0,-wg_width/2),(0,wg_width/2),(l,wg_width/2+w/2),(l,-wg_width/2-w/2)]
	support=gdspy.Polygon(support_pts,**layer)
	return support

def input_taper(min_width,wg_width,l,layer):
	""" taper the waveguide to a given width. """

	# the origin of the input taper is defined where it contacts the waveguide
	input_pts=[(-l,-min_width/2),(-l,min_width/2),(0,wg_width/2),(0,-wg_width/2)]
	input_shp=gdspy.Polygon(input_pts,**layer)
	return input_shp

def support_tether(width,length,max_width,taper_length,wg_width,layer):
	"""add support tethers along the waveguide. """

	# add the lines for each tether without the triangular support
	tether_l=gdspy.Rectangle((-width/2,-wg_width/2),(width/2,-length-wg_width/2),**layer)
	tether_r=gdspy.Rectangle((-width/2,wg_width/2),(width/2,length+wg_width/2),**layer)

	# add the support taper for each tether
	support_pts_l=[(-width/2,-wg_width/2-length),(width/2,-wg_width/2-length),(max_width/2,-wg_width-length-taper_length),
	(-max_width/2,-wg_width-length-taper_length)]

	support_pts_r=[(-width/2,wg_width/2+length),(width/2,wg_width/2+length),(max_width/2,wg_width+length+taper_length),
	(-max_width/2,wg_width+length+taper_length)]

	# add the points to a polygon
	support_l=gdspy.Polygon(support_pts_l,**layer)
	support_r=gdspy.Polygon(support_pts_r,**layer)
	return [tether_l,tether_r,support_l,support_r]

def bounding_rectangle(pattern_w,pattern_l,padding,layer,rect_shift,clearance,opt_litho_layer):
	""" creates a rectangle of a predefined width bounding the pattern. 
	Rect shift is a tuple of coordinates specifying the offset of the
	rectangle
	"""
	print('pattern_w :'+str(pattern_w))
	print('pattern_l: '+str(pattern_l))
	print('padding: '+str(padding))
	print('layer: '+str(layer))
	print('rect shift: '+str(rect_shift))
	xshift,yshift=rect_shift

	interior_rectangle=gdspy.Rectangle((-pattern_l/2+xshift,-pattern_w/2+yshift),
		(pattern_l/2+xshift,pattern_w/2+yshift),**layer)
	exterior_rectangle=gdspy.Rectangle((-pattern_l/2-padding+xshift,-pattern_w/2-padding+yshift),
		(pattern_l/2+padding+xshift,pattern_w/2+padding+yshift),layer)

	# define the rectangle used for optical lithography
	opt_rectangle=gdspy.Rectangle((-pattern_l/2-padding+xshift+clearance,-pattern_w/2-padding+yshift+clearance),
		(pattern_l/2+padding+xshift-clearance,pattern_w/2+padding+yshift-clearance),**opt_litho_layer)

	# subtract the interior rectangle from the exterior rectangle
	sub=gdspy.boolean(exterior_rectangle,interior_rectangle,'not')
	return sub,pattern_l,opt_rectangle

def phc_wg(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer_phc,
	wg_width,extra_space,layer_wg,support_width,support_length,
	taper_width,taper_length,tether_width,tether_length,tip_space,
	clearance,opt_litho_layer,padding):
	""" generates a photonic crystal on top of a waveguide which 
	is long enough to match the length of the photonic crystal cavity. 
	Returns a cell containing the photonic crystal geometry with support
	structures. 
	extra space is the extra space beyond the photonic crystal that 
	the waveguide extends on each side.
	"""
	phc_geom,wg_l=photonic_crystal(normal_holes,taper_holes,radius,
		taper_depth,spacing,cell_name,input_taper_holes,input_taper_percent,layer_phc)

	wg_geom=waveguide(wg_width,wg_l+extra_space*2,layer_wg)

	# subtract the photonic crystal from the waveguide
	phc_wg=gdspy.boolean(wg_geom,phc_geom,'not')

	# add a reference to the end support but shift it to the end of the waveguide
	# add this object to the same layer as the waveguide
	supp_geom=wg_support(wg_width,support_width,support_length,layer_wg)
	# create a reference for the support structure and shift it to the end of the waveguide
	# create the cell holding the support structure
	supp_cell=gdspy.Cell('support structure '+cell_name)
	supp_cell.add(supp_geom)
	supp_ref=gdspy.CellReference(supp_cell,(wg_l/2+extra_space,0))

	# add a reference to the waveguide taper
	taper_geom=input_taper(taper_width,wg_width,taper_length,layer_wg)
	taper_cell=gdspy.Cell('input taper cell '+cell_name)
	taper_cell.add(taper_geom)
	taper_ref=gdspy.CellReference(taper_cell,(-wg_l/2-extra_space,0))

	# add a reference to the support tethers
	tether_geom=support_tether(tether_width,tether_length,support_width,support_length,
		wg_width,layer_wg)
	tether_cell=gdspy.Cell('tether '+cell_name)
	tether_cell.add(tether_geom)

	# place the tether between the waveguide taper and photonic crystal
	tether_ref=gdspy.CellReference(tether_cell,(-wg_l/2-extra_space/2,0))

	# add the bounding box
	# calculate the total pattern length
	# add extra space to account for distance past tip
	total_len=wg_l+extra_space*2+support_length+taper_length+tip_space

	# locate pattern center
	#center=-(taper_length/2+support_length+2*extra_space
	center=-taper_length/2+support_length/2-tip_space/2

	# calculate the total width of pattern
	total_w=wg_width+tether_length*2+support_length*2

	rect_shift=(center,0)

	# create a bounding rectangle
	bounding_rect,pattern_l,opt_rectangle=bounding_rectangle(total_w,total_len,padding,layer_wg,rect_shift,clearance,opt_litho_layer)

	# add the geometries to a cell
	device_cell=gdspy.Cell('device '+cell_name)
	device_cell.add([phc_wg])

	# add the support tethers to a cell
	device_cell.add([tether_ref,supp_ref,tether_ref,taper_ref])

	return device_cell,bounding_rect,total_len,total_w,rect_shift,opt_rectangle

def txt_label(list):
	""" This function takes a list of items to be added to a text label and
	creates a vertical label where the text is separated by dashes (-).
	"""
	label=''
	for i in list:
		if i==list[0]:
			label+=str(i)
		else:
			label+='-'+str(i)
	return label

def text_rect(bounding_box,box_length,box_width,txt_label,txt_height,layer,rect_shift,extra_text=None):
	"""creates a bounding rectangle with text subtracted from it. 
	returns a cell.
	"""
	# get the bounding box
	# add a 1um offset from the rest of the pattern
	offset=box_length/2+1

	xshift,yshift=rect_shift

	print(xshift)

	test1=offset+xshift
	# add the text
	vtext=gdspy.Text(txt_label,txt_height,(offset+xshift,box_width/2+yshift),horizontal=False,**layer)

	# first subtract the interior rectangle from the exterior rectangle
	sub=gdspy.boolean(bounding_box,vtext,'not')
	return sub


def cavity_text(text_box,cavity_cell,cell_name,opt_rectangle):

	"""
	outputs a cell with a cavity labeled by it's number of mirror hole
	pairs and taper hole pairs. Returns a cell containing the text and cavity
	"""

	# the location of the bounding box will be shifted by the support length and the taper length
	# locate pattern center
	
	txtcell=gdspy.Cell('text '+cell_name)
	txtcell.add([text_box,opt_rectangle])
	txtref=gdspy.CellReference(txtcell,(0,0),rotation=90)

	# create a cell reference for the cavity cell
	cavity_ref=gdspy.CellReference(cavity_cell,(0,0),rotation=90)

	# add the bounding rectangle to the cavity cell

	total=gdspy.Cell('total cell '+cell_name)
	total.add([cavity_ref,txtref])

	return total

def alignment_mark(xw,xl,layer):
	""" creates a cross alignment mark geometry, by taking the  union of 2 
	rectangles.
	"""
	horizontal=gdspy.Rectangle((-xl/2,-xw/2),(xl/2,xw/2),**layer)
	vertical=gdspy.Rectangle((-xw/2,-xl/2),(xw/2,xl/2),**layer)
	cross=gdspy.boolean(horizontal,vertical,'or',**layer)
	return cross

def disc_resonator(radius,center,layer):
	""" Creates a disk geometry at the specified location, given 
	radius, center, and layer. 
	"""
	return gdspy.Round(center,radius,number_of_points=199,**layer)

def ring_wg(wg_len,wg_width,radius,disc_loc,dist,layer):
	""" creates a disk geometry next to a waveguide. disc_loc, is the
	location along the length of the waveguide where the disc is placed,
	dist is the distance from the edge of the disc to the waveguide. 
	disc_loc is relative to the left edge of the waveguide. 
	"""

	# first create the waveguide
	wg=waveguide(wg_width,wg_len,layer)

	# next calculate the location of the center of the circle relative to the 
	# waveguide's origin is it's center, and disc_loc is relative to the left 
	# edge of the waveguide
	x=wg_len/2-disc_loc

	# calculate the location of the center of the circle relative to the 
	# waveguide's origin
	y=wg_width/2+dist+radius

	# package the coordinates of the disc center
	center=(x,y)

	# create the disk geometry
	disc=disc_resonator(radius,center,layer)

	# return the two geometries
	return wg,disc

def phc_mirror(numholes,radius,spacing,layer,offset,taper_depth=0.25,taper_holes=3):
	"""
	creates a list of circle shapes specifying a photonic_crystal_mirror.
	
	Also returns the length of the mirror. 
	"""
	holes=[]

	dist=0

	# unpack the offset vector
	x,y=offset

	for i in range(taper_holes):
		print('here')
		rad=radius*taper_depth+(1-taper_depth)*radius*i/(taper_holes)
		print('radius: '+str(rad))
		hole=gdspy.Round((dist+x,0+y),rad,number_of_points=199,**layer)
		dist+=spacing
		holes.append(hole)

	for j in range(taper_holes,numholes):
		hole=gdspy.Round((dist+x,0+y),radius,number_of_points=199,**layer)
		dist+=spacing
		holes.append(hole)
	# WANT TO ADD AN INPUT TAPER SECTION

	return holes

def boxed_ring(wg_len,wg_width,radius,disc_loc,dist,ebeam_layer,
	opt_litho_layer,padding,clearance,supp_width,supp_len,tether_sp,tether_tri,
	min_taper_width,taper_len,coupling_sp,mirror_holes,mirror_rad,mirror_sp,
	name):
	
	""" #this function creates a disc resonator next to a waveguide, as in
	#ring_wg, but also adds support tethers, and a bounding box for HSQ 
	#patterning. 
	#Calls txt_rect function and bounding_box function. 
	#Padding is the width of the bounding rectangle. 
	#Clearance is how much the PR pattern overlaps with the ebeam pattern

	tether_tri refers to the length of the tapered part of the support tether
	coupling_sp is the space left past the end of the taper tip

	name is a list with parameters that identify the pattern
	"""
	
	# Calculate the total pattern width and length
	# add 5um of extra space on each side of the waveguide and disc
	w_tot=wg_width+2*radius+dist+10
	l_tot=wg_len+taper_len+coupling_sp+supp_len

	# Calculate how much to shift the rectangle relative to the center of the
	# pattern
	shift=(-(taper_len+coupling_sp)/2,0)

	# put all the relevant parameters in a dictonary
	rect_args={}
	rect_args['pattern_w']=2*w_tot
	rect_args['pattern_l']=l_tot
	rect_args['padding']=padding
	rect_args['layer']=ebeam_layer
	rect_args['rect_shift']=shift
	rect_args['clearance']=clearance
	rect_args['opt_litho_layer']=opt_litho_layer
	rect,length,opt_rect=bounding_rectangle(**rect_args)

	# create a text label for the pattern based on the spacing of the waveguide
	# and name of pattern
	# first cast the items in name into strings
	str_name=[str(i) for i in name]
	label=txt_label([str(dist)]+str_name)

	txt_rect_args={}
	txt_rect_args['bounding_box']=rect
	txt_rect_args['box_length']=l_tot
	txt_rect_args['box_width']=2*w_tot
	txt_rect_args['txt_label']=label
	txt_rect_args['layer']=ebeam_layer
	txt_rect_args['rect_shift']=shift
	txt_rect_args['txt_height']=1

	txt_rect=text_rect(**txt_rect_args)

	# create the disc and the waveguide
	disc_args={}
	disc_args['wg_len']=wg_len
	disc_args['wg_width']=wg_width
	disc_args['radius']=radius
	disc_args['disc_loc']=disc_loc
	disc_args['dist']=dist
	disc_args['layer']=ebeam_layer
	wg,disc=ring_wg(**disc_args)

	# now add support structures
	# support is a polygon
	# because support is a polygon, it needs to be converted to a cell to be 
	# properly offset relative to the waveguide
	supp_args={}
	supp_args['wg_width']=wg_width
	supp_args['w']=supp_width
	supp_args['l']=supp_len
	supp_args['layer']=ebeam_layer
	supp=wg_support(**supp_args)

	supp_cell=gdspy.Cell('support structure'+' '+str(name))
	supp_cell.add(supp)
	supp_ref=gdspy.CellReference(supp_cell,(l_tot/2-supp_len-(taper_len+coupling_sp)/2,0))

	# now add tethers to support the waveguide
	tether_args={}
	tether_args['width']=0.1

	# length is full length of tether less the length of the triangular part
	tether_args['length']=w_tot-tether_tri

	# create a 1um wide tether
	tether_args['max_width']=1
	tether_args['taper_length']=tether_tri
	tether_args['wg_width']=0.525
	tether_args['layer']=ebeam_layer
	supp_tether=support_tether(**tether_args)

	# create a cell for the support tether
	tether_cell=gdspy.Cell('support tether'+' '+str(name))
	tether_cell.add(supp_tether)

	# want to repeat this geoemtry so add a list of cell references every 
	# tether_sp apart
	# divide the waveguide length into a number of segments determined by
	# tether spacing
	# tether_list holds references to all the tethers
	tether_list=[]

	interval=math.floor(l_tot/tether_sp)
	for i in range(interval):
		loc=l_tot/2-taper_len/2-i*tether_sp

		# now check if the tether is going to run through the disc
		# determine the points around the disc
		# keep a 5um space around the disc
		disc_min=l_tot/2-disc_loc-radius-5
		disc_max=l_tot/2-disc_loc+radius+5
		if not(((loc>disc_min) and (loc<disc_max)) or (loc<-wg_len/2) or (loc>wg_len/2)):
			tether_ref=gdspy.CellReference(tether_cell,(loc,0))
			tether_list.append(tether_ref)

	# now add tapered waveguide
	# returns an input taper
	taper_args={}
	taper_args['min_width']=min_taper_width
	taper_args['wg_width']=wg_width
	taper_args['l']=taper_len
	taper_args['layer']=ebeam_layer
	taper=input_taper(**taper_args)

	# need to create another cell reference too shift the taper to the end of the waveguide
	taper_cell=gdspy.Cell('taper'+' '+str(name))
	taper_cell.add(taper)
	taper_ref=gdspy.CellReference(taper_cell,(-wg_len/2,0))

	# add photonic crystal mirror
	mirror_args={}
	mirror_args['numholes']=mirror_holes
	mirror_args['radius']=mirror_rad
	mirror_args['spacing']=mirror_sp
	mirror_args['layer']=opt_litho_layer

	# define the offset of the mirror
	# need to estimate the length of the mirror
	# leave 1um of space between end of mirror from edge
	mirror_len=mirror_args['spacing']*mirror_args['numholes']

	mirror_args['offset']=(wg_len/2-mirror_len-1,0)

	mirror=phc_mirror(**mirror_args)

	# now subtract the mirror geometry from the waveguide
	wg_sub=gdspy.boolean(wg,mirror,'not')

	return wg_sub,disc,txt_rect,opt_rect,supp_ref,tether_list,taper_ref,l_tot,shift
def dicing_street(w,l,offset,layer,rect_width=90,alignment_sp=40):
	"""creates a trench for DSE etching with alingnment marks for the dicing
	saw

	offset is an iterable holding the x and y offset
	"""
	x,y=offset

	# calculate the height of the alignment marks
	h=(w-40)/2
	DSE=gdspy.Rectangle((-l/2+x,-w/2+y),(l/2+x,w/2+y),**layer)
	UL=gdspy.Rectangle((-l/2-rect_width+x-alignment_sp,alignment_sp/2+y),(-l/2-alignment_sp+x,alignment_sp/2+h+y),**layer)
	LL=gdspy.Rectangle((-l/2-rect_width+x-alignment_sp,-alignment_sp/2-h+y),(-l/2-alignment_sp+x,-alignment_sp/2+y),**layer)
	UR=gdspy.Rectangle((l/2+x+alignment_sp,alignment_sp/2+y),(l/2+x+alignment_sp+rect_width,alignment_sp/2+h+y),**layer)
	LR=gdspy.Rectangle((l/2+x+alignment_sp,-alignment_sp/2-h+y),(l/2+x+alignment_sp+rect_width,-alignment_sp/2+y),**layer)
	return DSE,UL,LL,UR,LR