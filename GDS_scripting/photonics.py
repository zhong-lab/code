import gdspy
import math
from math import sqrt

def waveguide(w,l,layer):
	""" waveguide rectangle """

	wg=gdspy.Rectangle((-l/2,-w/2),(l/2,w/2),**layer)
	return wg

def longWg(w,l,extraLen,layer):
	""" Makes a long waveguide. This waveguide has extra space before the
	device to protect the device part from the HF peeling of the resist.

	w: width of waveguide
	l: length of device
	extraLen: the extra length of the waveguide before the device
	layer: layer on which the design is generated
	"""

	# TODO: test longWg
	wg=gdspy.Rectangle((-l/2-extraLen,-w/2),(l/2,w/2),**layer)
	return wg

def photonic_crystal(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer,extra_space,
	asym=False):
	""" define a parabolically tapered photonic crystal cavity. hole size
	and length are tapered simulataneously. a certain number of input taper
	holes can be defined to reduce input scattering loss.
	also returns the length of the photonic crystal

	if asym!=False then the number of holes specified in asym is the number of
	regular mirror hole pairs on the output side and "normal holes" specifies
	the number of input holes which can change
	"""

	min_spacing=taper_depth*spacing
	dist=min_spacing/2

	holes=[]

	# add taper holes
	for i in range(taper_holes):
		# holes are labeled 0,1,2,3,4,5,6...
		# hole 0 placed at min spacing
		# next hole spacing is scaled by 1^2
		# this convention is consistent with lumerical scripting
		# lumerical scripts are offset by 1 because of 1-indexing
		if i>0:
			dist+=spacing*taper_depth+(i**2+(i-1)**2)*(1-taper_depth)*0.5*spacing/(taper_holes**2)
		rad=taper_depth*radius+((i**2)*(1-taper_depth)*radius/(taper_holes**2))
		hole_pos=gdspy.Round((dist,0),rad,number_of_points=199,**layer)
		hole_neg=gdspy.Round((-dist,0),rad,number_of_points=199,**layer)
		print('taper hole: '+str(i)+', radius: '+str(rad))
		print('taper hole: '+str(i)+', location: '+str(dist))
		# add all holes to a list
		holes.append(hole_pos)
		holes.append(hole_neg)

	# add untapered holes

	dist+=spacing/2+taper_depth*spacing/2+0.5*spacing*(1-taper_depth)*(taper_holes-1)**2/(taper_holes**2)
	dist_neg=dist

	if asym!=False:

		for i in range(asym):
			if i>0:
				dist+=spacing
			hole_pos=gdspy.Round((dist,0),radius,number_of_points=199,**layer)
			holes.append(hole_pos)
		for i in range(normal_holes):
			if i>0:
				dist_neg+=spacing
			hole_neg=gdspy.Round((-dist_neg,0),radius,number_of_points=199,**layer)
			holes.append(hole_neg)
			print('normal hole: '+str(i)+', dist: '+str(dist_neg))
			print('normal hole: '+str(i)+', radius: '+str(radius))
	else:
		for i in range(normal_holes):
			if i>0:
				dist+=spacing
			hole_pos=gdspy.Round((dist,0),radius,number_of_points=199,**layer)
			hole_neg=gdspy.Round((-dist,0),radius,number_of_points=199,**layer)
			holes.append(hole_pos)
			holes.append(hole_neg)
			print('normal hole: '+str(i)+', dist: '+str(dist))
			print('normal hole: '+str(i)+', radius: '+str(radius))
		dist_neg=dist

	# add input taper
	for i in range(input_taper_holes):
		if i>0:
			dist_neg+=spacing
		rad=radius-radius*(1-input_taper_percent)/input_taper_holes*(i+1)
		hole_neg=gdspy.Round((-dist_neg,0),rad,number_of_points=199,**layer)
		holes.append(hole_neg)

	l_tot=dist*2+3*extra_space

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
	"""add support tethers along the waveguide.

	-width: width of the tethers
	-length: length of the tethers
	-max_width: the maximum width of the tethers
	-taper_length: the length over which the tethers are tapered
	-wg_width: the width of the waveguide
	-layer: the layer on which the tethers are written
	"""

	# add the lines for each tether without the triangular support
	tether_l=gdspy.Rectangle((-width/2,-wg_width/2),(width/2,-length-wg_width/2),**layer)
	tether_r=gdspy.Rectangle((-width/2,wg_width/2),(width/2,length+wg_width/2),**layer)

	# add the support taper for each tether
	support_pts_l=[(-width/2,-wg_width/2-length),(width/2,-wg_width/2-length),(max_width/2,-wg_width-length-2*taper_length),
	(-max_width/2,-wg_width-length-2*taper_length)]

	support_pts_r=[(-width/2,wg_width/2+length),(width/2,wg_width/2+length),(max_width/2,wg_width+length+2*taper_length),
	(-max_width/2,wg_width+length+2*taper_length)]

	# add the points to a polygon
	support_l=gdspy.Polygon(support_pts_l,**layer)
	support_r=gdspy.Polygon(support_pts_r,**layer)
	return [tether_l,tether_r,support_l,support_r]

def singleTether(w,l,maxWidth,taperLen,wgWidth,layer,dir='up'):
	""" Function which makes a tether on only one side. Can choose the
	orientation of the tethers to be either "up" or "down", (default is up).
	Returns tether geometry object.

	w: width of the tether (um)
	l: length of the tether (um)
	maxWidth: maximum width of the tapered part of the tether (um)
	taperLen: length over which the tether is tapered (um)
	wgWidth: the width of the waveguide being supported (um)
	layer: the layer that the tether is drawn on
	dir: direction of the tether, can be either "up" or "down"
	"""

	# if dir='up' create a vertically oriented tether
	if dir=='up':
		# add the lines for the tether without the triangular support
		tether=gdspy.Rectangle((-w/2,wgWidth/2),(w/2,l+wgWidth/2),**layer)

		# add the support taper for the tether
		suppPts=[(-w/2,wgWidth/2+l),(w/2,wgWidth/2+l),
			(maxWidth/2,wgWidth+l+taperLen),
			(-maxWidth/2,wgWidth+l+taperLen)]
	else:
		# create an upside down tether
		# invert the y coordinates
		tether=gdspy.Rectangle((-w/2,-wgWidth/2),(w/2,-l-wgWidth/2),**layer)

		# add the support taper for the tether
		suppPts=[(-w/2,-wgWidth/2-l),(w/2,-wgWidth/2-l),
			(maxWidth/2,-wgWidth-l-taperLen),
			(-maxWidth/2,-wgWidth-l-taperLen)]

	suppPoly=gdspy.Polygon(suppPts,**layer)

	return tether,suppPoly


def bounding_rectangle(pattern_w,pattern_l,padding,layer,rect_shift,clearance,opt_litho_layer):
	""" creates a rectangle of a predefined width bounding the pattern.

	rect_shift: a tuple of coordinates specifying the offset of the
	rectangle

	padding: this is the width of the bounding rectangle
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
		(pattern_l/2+padding+xshift,pattern_w/2+padding+yshift),**layer)

	# define the rectangle used for optical lithography
	opt_rectangle=gdspy.Rectangle((-pattern_l/2-padding+xshift-clearance,-pattern_w/2-padding+yshift+1*clearance),
		(pattern_l/2+padding+xshift-2*clearance,pattern_w/2+padding+yshift-1*clearance),**opt_litho_layer)

	# subtract the interior rectangle from the exterior rectangle
	sub=gdspy.boolean(exterior_rectangle,interior_rectangle,'not',**layer)
	return sub,pattern_l,opt_rectangle

def tipTether(tetherLen,tetherWidth,layer):
	""" Creates a tether at the tip of the tapered waveguide. This tether
	connects the tip of the tapered waveguide to the substrate.

	This is ideal for wet HF etching because the tether prevents collapse due
	to surface tension.

	The object returned is a geometric object rather than a cell or cell
	reference.
	"""

	tether=gdspy.Rectangle((-tetherWidth/2,-tetherLen/2),
		(tetherWidth/2,tetherLen/2))
	return tether

def phc_wg(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer_phc,
	wg_width,extra_space,layer_wg,support_width,support_length,
	taper_width,taper_length,tether_width,tether_length,tip_space,
	clearance,opt_litho_layer,padding,boxLayer,asym=False):
	""" generates a photonic crystal on top of a waveguide which
	is long enough to match the length of the photonic crystal cavity.
	Returns a cell containing the photonic crystal geometry with support
	structures.
	extra space is the extra space beyond the photonic crystal that
	the waveguide extends on each side.

	if asym!=False then the number of holes specified in asym is the number of
	regular mirror hole pairs on the output side and "normal holes" specifies
	the number of input holes which can change
	"""
	phc_geom,wg_l=photonic_crystal(normal_holes,taper_holes,radius,
		taper_depth,spacing,cell_name,input_taper_holes,input_taper_percent,
		layer_phc,extra_space,asym)

	wg_geom=waveguide(wg_width,wg_l+extra_space*4,layer_wg)

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
	taper_ref=gdspy.CellReference(taper_cell,(-wg_l/2-2*extra_space,0))

	# add a reference to the support tethers
	tether_geom=support_tether(tether_width,tether_length,support_width,support_length,
		wg_width,layer_wg)
	tether_cell=gdspy.Cell('tether '+cell_name)
	tether_cell.add(tether_geom)

	# place the tether between the waveguide taper and photonic crystal
	tether_ref=gdspy.CellReference(tether_cell,(-wg_l/2-1.5*extra_space,0))

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
	bounding_rect,pattern_l,opt_rectangle=bounding_rectangle(total_w,total_len,
		padding,boxLayer,rect_shift,clearance,opt_litho_layer)

	# add the geometries to a cell
	device_cell=gdspy.Cell('device '+cell_name)
	device_cell.add([phc_wg])

	# add the support tethers to a cell
	device_cell.add([tether_ref,supp_ref,tether_ref,taper_ref])

	return device_cell,bounding_rect,total_len,total_w,rect_shift,opt_rectangle

def photonic_crystal_long_wg(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer,extra_space,
	asym=False,longWg=False,meander=False):
	""" define a parabolically tapered photonic crystal cavity. hole size
	and length are tapered simulataneously. a certain number of input taper
	holes can be defined to reduce input scattering loss.
	also returns the length of the photonic crystal

	if asym!=False then the number of holes specified in asym is the number of
	regular mirror hole pairs on the output side and "normal holes" specifies
	the number of input holes which can change
	"""

	min_spacing=taper_depth*spacing
	dist=min_spacing/2
	if longWg!=False:
		extra=longWg-6

	if meander!=False:
		x=meander
	else:
		x=0

	holes=[]

	# add taper holes
	for i in range(taper_holes):
		# holes are labeled 0,1,2,3,4,5,6...
		# hole 0 placed at min spacing
		# next hole spacing is scaled by 1^2
		# this convention is consistent with lumerical scripting
		# lumerical scripts are offset by 1 because of 1-indexing
		if i>0:
			dist+=spacing*taper_depth+(i**2+(i-1)**2)*(1-taper_depth)*0.5*spacing/(taper_holes**2)
		rad=taper_depth*radius+((i**2)*(1-taper_depth)*radius/(taper_holes**2))
		hole_pos=gdspy.Round((dist+extra,x),rad,number_of_points=199,**layer)
		hole_neg=gdspy.Round((-dist+extra,x),rad,number_of_points=199,**layer)
		#print('taper hole: '+str(i)+', radius: '+str(rad))
		#print('taper hole: '+str(i)+', location: '+str(dist))
		# add all holes to a list
		holes.append(hole_pos)
		holes.append(hole_neg)

	# add untapered holes

	dist+=spacing/2+taper_depth*spacing/2+0.5*spacing*(1-taper_depth)*(taper_holes-1)**2/(taper_holes**2)
	dist_neg=dist

	if asym!=False:

		for i in range(asym):
			if i>0:
				dist+=spacing
			hole_pos=gdspy.Round((dist+extra,x),radius,number_of_points=199,**layer)
			holes.append(hole_pos)
		for i in range(normal_holes):
			if i>0:
				dist_neg+=spacing
			hole_neg=gdspy.Round((-dist_neg+extra,x),radius,number_of_points=199,**layer)
			holes.append(hole_neg)
			#print('normal hole: '+str(i)+', dist: '+str(dist_neg))
			#print('normal hole: '+str(i)+', radius: '+str(radius))
	else:
		for i in range(normal_holes):
			if i>0:
				dist+=spacing
			hole_pos=gdspy.Round((dist+extra,x),radius,number_of_points=199,**layer)
			hole_neg=gdspy.Round((-dist+extra,x),radius,number_of_points=199,**layer)
			holes.append(hole_pos)
			holes.append(hole_neg)
			#print('normal hole: '+str(i)+', dist: '+str(dist))
			#print('normal hole: '+str(i)+', radius: '+str(radius))
		dist_neg=dist

	# add input taper
	for i in range(input_taper_holes):
		if i>0:
			dist_neg+=spacing
		rad=radius-radius*(1-input_taper_percent)/input_taper_holes*(i+1)
		hole_neg=gdspy.Round((-dist_neg+extra,x),rad,number_of_points=199,**layer)
		holes.append(hole_neg)

	l_tot=dist*2+3*extra_space
	if longWg!=False:
		l_tot+=longWg

	return holes,l_tot

def phc_path(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer_phc,
	wg_width,extra_space,layer_wg,support_width,support_length,
	taper_width,taper_length,tether_width,tether_length,tip_space,
	clearance,opt_litho_layer,padding,boxLayer,asym=False,longWg=False,meander=False):

	""" generates a photonic crystal on top of a waveguide which
	is long enough to match the length of the photonic crystal cavity.
	Returns a cell containing the photonic crystal geometry with support
	structures.
	extra space is the extra space beyond the photonic crystal that
	the waveguide extends on each side.

	if asym!=False then the number of holes specified in asym is the number of
	regular mirror hole pairs on the output side and "normal holes" specifies
	the number of input holes which can change
	"""

	
	segments=int(floor(longWg/(2*4500)))
	print('segments: '+str(segments))
	pathlist=[]

	tether_reflist=[]
	# add a reference to the support tethers
	tether_geom=support_tether(tether_width,tether_length,support_width,support_length,
		wg_width,layer_wg)
	tether_cell=gdspy.Cell('tether '+cell_name)
	tether_cell.add(tether_geom)

	if segments<1:

		phc_geom,wg_l=photonic_crystal_long_wg(normal_holes,taper_holes,radius,
			taper_depth,spacing,cell_name,input_taper_holes,input_taper_percent,
			layer_phc,extra_space,asym,longWg,meander)

		#print('segment<1')
		wg_geom=gdspy.Path(wg_width,(-100,meander))
		wg_geom.segment(longWg+extra_space*4+100,'+x',**layer_wg)

		# add a segment for the release window
		release=gdspy.Path(6+wg_width,(-100-taper_length-10,meander))
		release.segment(longWg-1.5+extra_space*4+100+taper_length+10,'+x',**opt_litho_layer)
		pathlist.append(release)

		num_tethers=floor((longWg+100)/20)
		for j in range(num_tethers):
			#print('adding tether to straight waveguide')
			tether_ref=gdspy.CellReference(tether_cell,(j*20-100,meander))
			tether_reflist.append(tether_ref)

			tether_ref2=gdspy.CellReference(tether_cell,(j*20-100,meander))
			tether_reflist.append(tether_ref2)

		# add a reference to the waveguide taper
		taper_geom=input_taper(taper_width,wg_width,taper_length,layer_wg)
		taper_cell=gdspy.Cell('input taper cell '+cell_name)
		taper_cell.add(taper_geom)
		taper_ref=gdspy.CellReference(taper_cell,(-100,meander))

		# subtract the photonic crystal from the waveguide
		phc_wg=gdspy.boolean(wg_geom,phc_geom,'not',**layer_wg)
		pathlist.append(phc_wg)

		# add a reference to the end support but shift it to the end of the waveguide
		# add this object to the same layer as the waveguide
		supp_geom=wg_support(wg_width,support_width,support_length,layer_wg)
		# create a reference for the support structure and shift it to the end of the waveguide
		# create the cell holding the support structure
		supp_cell=gdspy.Cell('support structure '+cell_name)
		supp_cell.add(supp_geom)
		supp_ref=gdspy.CellReference(supp_cell,(longWg+extra_space,meander))

	else:
		phc_geom,wg_l=photonic_crystal_long_wg(normal_holes,taper_holes,radius,
			taper_depth,spacing,cell_name,input_taper_holes,input_taper_percent,
			layer_phc,extra_space,asym,4500,meander)

		#print('segment>1')
		# make first path slightly longer for tapered waveguide
		wg_geom=gdspy.Path(wg_width,(-100,-meander*(segments-1)))
		wg_geom.segment(4600+extra_space*4,'+x',**layer_wg)
		wg_geom.turn(50,'rr',**layer_wg)
		wg_geom.segment(4500+extra_space*4,'-x',**layer_wg)
		wg_geom.turn(50,'ll',**layer_wg)
		pathlist.append(wg_geom)

		# add a segment for the release window
		release=gdspy.Path(6+wg_width,(-100-taper_length-10,-meander*(segments-1)))
		release.segment(4600+extra_space*4+taper_length+10,'+x',**opt_litho_layer)
		release.turn(50,'rr',**opt_litho_layer)
		release.segment(4500+extra_space*4,'-x',**opt_litho_layer)
		release.turn(50,'ll',**opt_litho_layer)
		pathlist.append(release)

		num_tethers=floor(4600/20)
		for j in range(num_tethers+1):
			#print('adding tether to straight waveguide')
			tether_ref=gdspy.CellReference(tether_cell,(j*20-100,-meander*(segments-1)))
			tether_reflist.append(tether_ref)

			tether_ref2=gdspy.CellReference(tether_cell,(j*20-100,-meander*(segments-1)))
			tether_reflist.append(tether_ref2)

		for i in range(segments):
			wg_geom=gdspy.Path(wg_width,(0,-meander*i))
			wg_geom.segment(4500+extra_space*4,'+x',**layer_wg)
			wg_geom.turn(50,'rr',**layer_wg)
			#print('-minus x')
			wg_geom.segment(4500+extra_space*4,'-x',**layer_wg)
			wg_geom.turn(50,'ll',**layer_wg)

			pathlist.append(wg_geom)

			# add a segment for the release window
			release=gdspy.Path(6+wg_width,(0,-meander*i))
			release.segment(4500+extra_space*4,'+x',**opt_litho_layer)
			release.turn(50,'rr',**opt_litho_layer)
			#print('minus x release')
			release.segment(4500+extra_space*4,'-x',**opt_litho_layer)
			release.turn(50,'ll',**opt_litho_layer)
			pathlist.append(release)

			num_tethers=floor(4500/20)
			for j in range(num_tethers+1):
				tether_ref=gdspy.CellReference(tether_cell,(j*20,-meander*i))
				tether_reflist.append(tether_ref)

				tether_ref2=gdspy.CellReference(tether_cell,(j*20,-meander*i-100))
				tether_reflist.append(tether_ref2)

				curve_tethers=int(math.floor(50*pi/20))
				#print('curve tethers: '+str(curve_tethers))
				for k in range(1,curve_tethers):
					tether_ref=gdspy.CellReference(tether_cell,
					(4500+extra_space*4+sin(k/curve_tethers*pi)*50,-meander*i-50-cos(k/curve_tethers*pi)*50),
					rotation=k/curve_tethers*180)
					tether_reflist.append(tether_ref)

					tether_ref2=gdspy.CellReference(tether_cell,
					(-sin(k/curve_tethers*pi)*50,-meander*i-150+cos(k/curve_tethers*pi)*50),
					rotation=k/curve_tethers*180)
					tether_reflist.append(tether_ref2)

		# add one last path at the end
		last_path=gdspy.Path(wg_width,(0,meander))
		last_path.segment(4500+extra_space*4,'+x',**layer_wg)

		# add a segment for the release window
		last_release=gdspy.Path(6+wg_width,(0,meander))
		last_release.segment(4498.5+extra_space*4,'+x',**opt_litho_layer)
		pathlist.append(last_release)

		for j in range(num_tethers):
			tether_ref=gdspy.CellReference(tether_cell,(j*20,meander))
			tether_reflist.append(tether_ref)

		# subtract the photonic crystal from the waveguide
		phc_wg=gdspy.boolean(last_path,phc_geom,'not',**layer_wg)
		pathlist.append(phc_wg)

	if segments>=1:
		# add a reference to the end support but shift it to the end of the waveguide
		# add this object to the same layer as the waveguide
		supp_geom=wg_support(wg_width,support_width,support_length,layer_wg)
		# create a reference for the support structure and shift it to the end of the waveguide
		# create the cell holding the support structure
		supp_cell=gdspy.Cell('support structure '+cell_name)
		supp_cell.add(supp_geom)
		supp_ref=gdspy.CellReference(supp_cell,(4500+extra_space,-200))

		# add a reference to the waveguide taper
		taper_geom=input_taper(taper_width,wg_width,taper_length,layer_wg)
		taper_cell=gdspy.Cell('input taper cell '+cell_name)
		taper_cell.add(taper_geom)
		taper_ref=gdspy.CellReference(taper_cell,(-100,-meander*(segments-1)))

	# add the bounding box
	# calculate the total pattern length
	# add extra space to account for distance past tip
	total_len=wg_l+extra_space*2+support_length+taper_length+tip_space

	# locate pattern center
	#center=-(taper_length/2+support_length+2*extra_space
	center=-taper_length/2+support_length/2-tip_space/2

	# calculate the total width of pattern
	total_w=wg_width+tether_length*2+support_length*2

	if longWg!=False:
		total_w=6

	rect_shift=(center,0)

	# add the geometries to a cell
	device_cell=gdspy.Cell('device '+cell_name)
	device_cell.add(pathlist)

	# add the support tethers to a cell
	device_cell.add(tether_reflist)
	device_cell.add([supp_ref,tether_ref,taper_ref])

	#device_cell_ref=gdspy.CellReference(device_cell,rotation=90)

	return device_cell,total_len,total_w,rect_shift

# TODO: test phc_wg_LHF
def phcWgLHF(normal_holes,taper_holes,radius,spacing,wg_width,extra_space,
	input_taper_holes,input_taper_percent,support_width,support_length,
	taper_width,taper_length,tether_width,tether_length,tip_space,clearance,
	layer_phc,layer_wg,opt_litho_layer,cell_name,extraLen,tetherSp,taperDepth,
	padding,label,text):
	""" Generates a function to make the photonic crystal design with an
	additional tether added to the waveguide tip. It also has an extra long
	waveguide for devices on oxide.


	-normal_holes: the number of untapered holes in each mirror of the photonic
	crystal
	-taper_holes:  the number of tapered holes on one side of the mirror
	radius:  the radius of the holes in the photonic crystal
	-taper_depth: the depth of the spacing and hole diameter taper
	-spacing: the spacing between holes in the photonic crystal
	-wg_width: the width of the waveguide


	-input_taper_holes: the number of holes in the waveguide input taper. This
	-input taper reduces scattering off of the input mirror of the photonic
	crystal.
	-input_taper_percent: the percent by which the input taper holes are tapered
	-extra_space: extra space between the photonic crystal and the end of the
	waveguide.
	-support_width: the width of the support structure at the end of the
	end of the waveguide.
	-support_length: length of support structure at end of the waveguide
	-taper_width: width of waveguide taper
	-taper_length: length of tapered waveguide
	-tether_width: width of tethers
	-tether_length: length of tethers
	-tip_space: space past the end of the tapered waveguide
	-clearance: amount of overlap between optical lithography layer and box
	enclosing the design
	-padding: width of box enclosing the design
	-tetherSp: spacing between tethers along the long part of the waveguide


	-layer_phc: the layer that the photonic crystal is generated on. The photonic
	crystal is generated on a separate layer from the waveguide for a later
	boolean subtraction to make the holes.
	-layer_wg: the layer on which the waveguide is generated. The photonic
	crystal is generated on a separate layer from the waveguide for a later
	boolean subtraction to make the holes.
	-opt_litho_layer: layer for any optical lithography
	-cell_name: name of the cell on which the pattern is generated
	-extraLen: extra length of the waveguide before the device to protect the
	-device from the HF peeling of the resist
	-label: labels the device
	-text: height of text in labeled part of cavity
	"""

	# add photonic crystal params to a dictionary
	phcParams={}
	phcParams['normal_holes']=normal_holes
	phcParams['taper_holes']=taper_holes
	phcParams['radius']=radius
	phcParams['taper_depth']=taperDepth
	phcParams['spacing']=spacing
	phcParams['cell_name']=cell_name
	phcParams['input_taper_holes']=input_taper_holes
	phcParams['input_taper_percent']=input_taper_percent
	phcParams['layer']=layer_phc

	# add support structure params to a dictionary
	suppParams={}
	suppParams['wg_width']=wg_width
	suppParams['w']=support_width
	suppParams['l']=support_length
	suppParams['layer']=layer_wg

	# tapered waveguide parameters
	taperParams={}
	taperParams['min_width']=taper_width
	taperParams['wg_width']=wg_width
	taperParams['l']=taper_length
	taperParams['layer']=layer_wg

	# dictionary containing tether params
	tetherParams={}
	tetherParams['width']=tether_width
	tetherParams['length']=tether_length
	tetherParams['max_width']=support_width
	tetherParams['taper_length']=support_length
	tetherParams['wg_width']=wg_width
	tetherParams['layer']=layer_wg

	# collect the params for the tether for the tapered waveguide tip
	tipParams={}
	tipParams['tetherLen']=tip_space
	tipParams['tetherWidth']=tether_width
	tipParams['layer']=layer_wg

	# create a list to store tether references
	tetherList=[]

	# create a list to store all of the cell references generated
	refList=[]

	# generate the negative of the photonic crystal part of the design
	phc_geom,wg_l=photonic_crystal(**phcParams)

	# add waveguide params to a dictionary
	wgParams={}
	wgParams['w']=wg_width
	wgParams['l']=wg_l+extra_space*2
	wgParams['extraLen']=extraLen
	wgParams['layer']=layer_wg

	# generate the waveguide that the photonic crystal will sit on
	wg_geom=longWg(**wgParams)

	# subtract the photonic crystal from the waveguide
	phc_wg=gdspy.boolean(wg_geom,phc_geom,'not')

	# add a reference to the end support but shift it to the end of the
	# waveguide
	# add this object to the same layer as the waveguide
	supp_geom=wg_support(**suppParams)

	# how much to offset the support structure
	suppOffset=wg_l/2+extra_space

	# create a reference for the support structure and shift it to the end of
	# the waveguide
	# create the cell holding the support structure
	supp_cell=gdspy.Cell('support structure '+cell_name)
	supp_cell.add(supp_geom)
	supp_ref=gdspy.CellReference(supp_cell,(suppOffset,0))
	refList.append(supp_ref)

	# add a reference to the waveguide taper
	taper_geom=input_taper(**taperParams)
	taper_cell=gdspy.Cell('input taper cell '+cell_name)
	taper_cell.add(taper_geom)

	taperOffset=-wg_l/2-extra_space-extraLen

	# position the tapered waveguide at the end of the long waveguide
	taper_ref=gdspy.CellReference(taper_cell,(taperOffset,0))
	refList.append(taper_ref)

	# add the bounding box
	# calculate the total pattern length
	# add extra space to account for distance past tip
	total_len=wg_l+extra_space*2+support_length+taper_length+tip_space+extraLen

	# add a reference to the support tethers
	tether_geom=support_tether(**tetherParams)
	tether_cell=gdspy.Cell('tether '+cell_name)
	tether_cell.add(tether_geom)

	interval=math.floor(total_len/tetherSp)
	for i in range(interval):
		loc=-wg_l/2-extra_space-i*tetherSp

		# now check if the tether is going to run through the disc
		# determine the points around the disc
		# keep a 5um space around the disc

		deviceMin=-wg_l/2-extra_space
		if not((loc>-deviceMin) or (loc<-extraLen)):
			tether_ref=gdspy.CellReference(tether_cell,(loc,0))
			tetherList.append(tether_ref)

	# add the tether at the tapered waveguide tip
	tipGeom=tipTether(**tipParams)
	tipCell=gdspy.Cell('tip tether '+cell_name)
	tipCell.add(tipGeom)

	# create a cell reference to shift the tether to the tip of the tapered
	# waveguide
	# figure out how much to offset the tether to place it at the end of the
	# tapered waveguide
	tipOffset=-wg_l/2-extra_space-taper_length-extraLen-tip_space/2

	tipRef=gdspy.CellReference(tipCell,(tipOffset,0),rotation=90)
	refList.append(tipRef)

	# locate pattern center
	#center=-(taper_length/2+support_length+2*extra_space
	center=-taper_length/2+support_length/2-tip_space/2-extraLen/2

	# calculate the total width of pattern
	total_w=wg_width+tether_length*2+support_length*2

	rect_shift=(center,0)

	# dictionary containing rectangle params
	rectParams={}
	rectParams['pattern_w']=total_w
	rectParams['pattern_l']=total_len
	rectParams['padding']=padding
	rectParams['layer']=layer_wg
	rectParams['rect_shift']=rect_shift
	rectParams['clearance']=clearance
	rectParams['opt_litho_layer']=opt_litho_layer

	# create a bounding rectangle
	bounding_rect,pattern_l,opt_rectangle=bounding_rectangle(**rectParams)

	# create a dictionary to store the parameters for the rectangle with text
	# added
	textParams={}
	textParams['bounding_box']=bounding_rect
	textParams['box_length']=pattern_l
	textParams['box_width']=total_w
	textParams['txt_label']=label
	textParams['txt_height']=text
	textParams['layer']=layer_phc # use layer phc since the text will subtract
	textParams['rect_shift']=rect_shift

	# subtract the label from the box using the text_rect FUNCTIONS
	labeledRect=text_rect(**textParams)

	# add the geometries to a cell
	device_cell=gdspy.Cell('device '+cell_name)
	device_cell.add([phc_wg])

	# add the support tethers to cell
	device_cell.add(refList)
	device_cell.add(tetherList)

	# use cavity_text function to combine the labeled rectangle with the cavity
	# make a list to store those parameters
	cavityTxtParams={}
	cavityTxtParams['text_box']=labeledRect
	cavityTxtParams['cavity_cell']=device_cell
	cavityTxtParams['cell_name']=cell_name
	cavityTxtParams['opt_rectangle']=opt_rectangle

	totalCell=cavity_text(**cavityTxtParams)

	# make reference for the totalCell
	totalRef=gdspy.CellReference(totalCell)

	# return a cell instead of a cell reference
	outputCell=gdspy.Cell('output '+cell_name)
	outputCell.add(totalRef)

	# function returns total_len to use for lining up all the cavities
	return outputCell,opt_rectangle,total_len

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

def text_rect(bounding_box,box_length,box_width,txt_label,txt_height,layer,
	rect_shift,extra_text=None):
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
	vtext=gdspy.Text(txt_label,txt_height,(offset+xshift,box_width/2+yshift),
	horizontal=False,**layer)

	# first subtract the interior rectangle from the exterior rectangle
	sub=gdspy.boolean(bounding_box,vtext,'not',**layer)
	return sub


def cavity_text(text_box,cavity_cell,cell_name,opt_rectangle):

	"""
	outputs a cell with a cavity labeled by it's number of mirror hole
	pairs and taper hole pairs. Returns a cell containing the text and cavity
	"""

	txtcell=gdspy.Cell('text '+cell_name)
	txtcell.add([opt_rectangle])
	txtref=gdspy.CellReference(txtcell,(0,0),rotation=90)

	# create a cell reference for the cavity cell
	cavity_ref=gdspy.CellReference(cavity_cell,(0,0),rotation=90)

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

def ring_wg(wg_len,wg_width,radius,disc_loc,dist,layer,disc_layer):
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
	disc=disc_resonator(radius,center,disc_layer)

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
	name,disc_layer):

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
	disc_args['disc_layer']=disc_layer
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
def boxedRingLHF(wg_len,wg_width,radius,ringLoc,dist,ebeam_layer,
	opt_litho_layer,padding,clearance,supp_width,supp_len,tether_sp,tether_tri,
	min_taper_width,taper_len,coupling_sp,mirror_holes,mirror_rad,mirror_sp,
	name,ringLayer,tetherMaxWidth,tetherTaperLen,tetherWidth):

	""" #this function creates a ring resonator next to a waveguide, adds
	support tethers, and a bounding box for HSQ patterning.

	-wg_len: length of the waveguide
	-wg_width: width of the waveguide

	-mirror_holes: number of mirror holes
	-mirror_rad: radius of mirror holes
	-mirror_sp: spacing between holes in Bragg mirror

	# TODO: make a function for generating rings instead of just disks.
	-radius: radius of the ring
	-ringLoc: location of the ring along the waveguide
	-dist: distance between edge of ring and edge of waveguide

	-padding: is the width of the bounding rectangle.
	-clearance: is how much the PR pattern overlaps with the ebeam pattern
	-tether_tri: refers to the length of the tapered part of the support tether
	-coupling_sp: is the space left past the end of the taper tip
	-name: is a list with parameters that identify the pattern
	-supp_width: width of support structure at the end of the waveguide
	-supp_len: length of the support structure at the end of the waveguide
	-min_taper_width: the minimum width of the tapered waveguide
	-taper_len: length of the tapered part of the waveguide

	-ebeam_layer: layer which has the ebeam pattern
	-opt_litho_layer: layer which has the optical lithography pattern
	-name: label for this pattern
	-ringLayer: layer which has the ring pattern

	-tetherMaxWidth: maximum width of tethers
	-tetherTaperLen: length over which the tethers are tapered
	-tetherWidth: the width of the tethers
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

	# create a dictionary to store all the tip tether params
	tipParams={}
	tipParams['tetherLen']=coupling_sp
	tipParams['tetherWidth']=tetherWidth
	tipParams['layer']=ebeam_layer

	# create a list to compile all of the cell references
	refList=[]

	# create a list to compile all of the geometry objects:
	geomList=[]

	rect,length,opt_rect=bounding_rectangle(**rect_args)
	geomList.append(opt_rect)

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
	geomList.append(txt_rect)

	# create the disc and the waveguide
	disc_args={}
	disc_args['wg_len']=wg_len
	disc_args['wg_width']=wg_width
	disc_args['radius']=radius
	disc_args['disc_loc']=disc_loc
	disc_args['dist']=dist
	disc_args['layer']=ebeam_layer
	disc_args['disc_layer']=disc_layer

	# TODO: make a function that returns rings instead of discs
	wg,disc=ring_wg(**disc_args)
	geomList.append(disc)

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
	supp_ref=gdspy.CellReference(supp_cell,
		(l_tot/2-supp_len-(taper_len+coupling_sp)/2,0))
	refList.append(supp_ref)

	# now add tethers to support the waveguide
	tether_args={}
	tether_args['width']=tetherWidth

	# length is full length of tether less the length of the triangular part
	tether_args['length']=w_tot-tether_tri

	# create a 1um wide tether
	tether_args['max_width']=tetherMaxWidth
	tether_args['taper_length']=tetherTaperLen
	tether_args['wg_width']=wg_width
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
		if not(((loc>disc_min) and (loc<disc_max)) or (loc<-wg_len/2) or
			(loc>wg_len/2)):
			tether_ref=gdspy.CellReference(tether_cell,(loc,0))
			tether_list.append(tether_ref)

	# add support tether to the tip of the tapered waveguide
	tipGeom=tipTether(**tipParams)
	tipCell=gdspy.Cell('tip tether'+name)
	tipCell.add(tipGeom)

	# create a cell reference to shift the tether to the tip of the tapered
	# waveguide. Figure out howm uch to offset the tether to place it at the end
	# of the tapered waveguide

	# calculate the center of the waveguide
	wgCenter=-(taper_len+coupling_sp)/2

	# calculate the location of the tip tether
	tipOffset=wgCenter-wg_len-taper_len-tipParams['tetherLen']/2

	tipRef=gdspy.CellReference(tipCell,(tipOffset,0),rotation=90)
	refList.append(tipRef)

	# now add tapered waveguide
	# returns an input taper
	taper_args={}
	taper_args['min_width']=min_taper_width
	taper_args['wg_width']=wg_width
	taper_args['l']=taper_len
	taper_args['layer']=ebeam_layer
	taper=input_taper(**taper_args)

	# need to create another cell reference too shift the taper to the end of
	# the waveguide
	taper_cell=gdspy.Cell('taper'+' '+str(name))
	taper_cell.add(taper)
	taper_ref=gdspy.CellReference(taper_cell,(-wg_len/2,0))
	refList.append(taper_ref)

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
	geomList.append(wg_sub)

	# add everything to one cell at the end
	outputCell=gdspy.Cell('output '+name)
	outputCell.add(refList)
	outputCell.add(geomList)
	outputCell.add(tether_list)

	# return the output cell
	return outputCell,opt_rect,l_tot,shift

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

""" FUNCTIONS FOR CONSTANT HOLE SIZE AND SPACING TAPER ONLY. """

def photonic_crystal_const_holes(normal_holes,taper_holes,radius,taper_depth,spacing,
	cell_name,input_taper_holes,input_taper_percent,layer):
	""" define a parabolically tapered photonic crystal cavity. a certain number of input taper
	holes can be defined to reduce input scattering loss.
	also returns the length of the photonic crystal

	hole spacing is tapered but hole radius remains constant
	"""

	min_spacing=taper_depth*spacing
	dist=min_spacing/2

	holes=[]

	# add taper holes
	for i in range(taper_holes):
		if i>0:
			dist+=spacing*taper_depth+i**2*(1-taper_depth)*spacing/(taper_holes**2)
		#rad=taper_depth*radius+((i**2)*(1-taper_depth)*radius/(taper_holes**2))
		hole_pos=gdspy.Round((dist,0),radius,number_of_points=199,**layer)
		hole_neg=gdspy.Round((-dist,0),radius,number_of_points=199,**layer)

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

def phc_wg_const_holes(normal_holes,taper_holes,radius,taper_depth,spacing,
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

	hole size of photonic crystal is constant but spacing is modified
	"""
	phc_geom,wg_l=photonic_crystal_const_holes(normal_holes,taper_holes,radius,
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

def subCircle(radius,w,l,pos,layerRect,layerCircle,layer):
	""" This function takes a rectangle and subtracts a circle from it. Returns
	a geometric object

	radius: radius of circle

	w: width of rectangle (vertical)

	l: length of rectangle (horizontal)

	pos: tuple giving a relative offset of the circle to the rectangle. If pos
	is (x,y)=(0,0), then the circle is in the center of the rectangle

	layerRect: layer on which the rectangle is specified

	layerCircle: layer on which the circle is specified

	"""
	rect=gdspy.Rectangle((-l/2,-w/2),(l/2,w/2),**layerRect)
	circle=gdspy.Round(pos,radius,number_of_points=199,**layerCircle)

	sub=gdspy.boolean(rect,circle,'not',**layer)

	return sub

def discRect(radius,w,l,pos,gap,layerRect,layerCircle,layer):
	"""
	This function creates a disc that is recessed inside of a rectangle. The
	amount that the disc is recessed is determined by a gap that surrounds the
 	perimeter of the disc. This much hangs out past the rectangle to couple to
	a bus waveguide.Calls subCircle(...) in order to accomplish the subtraction
	This function returns the disc and the surrounding rectangle

	radius: radius of circle

	w: width of rectangle (vertical)

	l: length of rectangle (horizontal)

	pos: tuple giving a relative offset of the circle. The offset is determined
	by the gap specified, but it can also be added to this other offset. The
	default is no additional recession into the rectangle and just a shift
	along the length of the rectangle.

	gap: the gap surrounding the disc

	layerRect: the layer on which the rectangle is written

	layerCircle: the layer on which the disc subtracted from the rectangle is
	written. This layer is temporarily used for the boolean operation since
	ultimately the disc is returned on the same layer on which the rectangle is
	drawn.
	"""
	newRad=radius+gap

	# the circle is offset by the gap width away from the rect
	posx,posy=pos
	pos=(posx,w/2-radius+posy+gap)
	print('pos: '+str(pos))
	sub=subCircle(newRad,w,l,pos,layerRect,layerCircle,layer)

	# add the disc
	disc=gdspy.Round(pos,radius,number_of_points=199,**layerRect)

	return sub,disc

def discBorder(radius,pos,gap,padding,clearance,label,txtHeight,
	layerRect,layerCircle,layerOpt,wgLen,layer,extraWidth=0,extraLen=0):
	""" Makes a disc which is set inside a bordering rectangle. The rectangle
	has a smaller region which surrounds the disc. Uses the function text_rect
	to create a bounding box with a text label.

	radius: radius of the rectangle

	pos: position of the disc inside the surrounding rectangle, given as a tuple

	gap:  the gap surrounding the disc (um)

	padding: width of surrounding rectangle (um)

	clearance: distance (in um) that the HSQ pattern overlaps with the optical
	lithography pattern

	label: a label for the disc pattern, given as a string

	txtHeight: the height of the text label on the bounding box (um)

	layerRect: layer on which everything is drawn

	layerCircle: auxiliary layer used for the boolean operation

	layerOpt: layer for the optical lithography pattern

	wgLen: the length of the waveguide

	extraWidth: extra space to add on the side (in um) to accomodate the
	waveguide (optional, normally is 0)

	extraLen: extra space to add to accomodate the waveguide length (um)
	"""

	w=2*radius
	l=wgLen

	posx,posy=pos

	rectOffset=(posx-extraLen/2,posy)
	# first make the disc and surrounding rectangle
	sub,disc=discRect(radius,w,l,rectOffset,gap,layerRect,layerCircle,layer)

	# now add the surrounding rectangle
	# first create the bounding rectangle

	# create a dictionary to store the parameters for the bounding rectangle
	# function
	boundingParams={}
	# the pattern width is the width of the disc + 3x the gap distance
	# 2x the gap distance for where the waveguide goes, 1x the gap distance to
	# border the disc on the opposite side

	boundingParams['pattern_w']=w+2*gap+extraWidth
	# pattern length is just the width of the disc + 2x the gap distance

	boundingParams['pattern_l']=l
	boundingParams['padding']=padding
	boundingParams['layer']=layerRect
	# shift this bounding rectangle since it is slightly off-center
	boundingParams['rect_shift']=(0,gap+extraWidth/2)
	boundingParams['clearance']=clearance
	boundingParams['opt_litho_layer']=layerOpt

	rectSub,rectLen,opt_rectangle=bounding_rectangle(**boundingParams)

	# now add a text label to the bounding rectangle

	# create a dictionary to store the arguments
	txtParams={}

	txtParams['bounding_box']=rectSub
	txtParams['box_length']=rectLen
	txtParams['box_width']=boundingParams['pattern_w']
	txtParams['txt_label']=label
	txtParams['txt_height']=txtHeight
	txtParams['layer']=layerRect
	txtParams['rect_shift']=boundingParams['rect_shift']

	txtRect=text_rect(**txtParams)

	return sub,disc,txtRect,opt_rectangle

def discWg(radius,pos,gap,couplingSp,wgWidth,numHoles,holeRad,spacing,offset,
	suppWidth,suppLen,tetherSp,tetherWidth,tetherMaxWidth,tetherTaper,tipSp,
	padding,clearance,label,txtHeight,layer1,layer2,taperMinWidth,
	taperLen,layerOpt,layer,taperDepth=0.25,taperHoles=3):
	""" The same as discBorder(...), but now adds a bus waveguide with tethers.

	radius:  radius of disc

	pos: position of the disc inside the surrounding rectangle, given as a tuple

	gap: the gap surrounding the disc (um)

	couplingSp: the coupling distance between the disc and the bus waveguide(um)

	wgWidth: the width of the bus waveguide

	numHoles: number of holes in photonic crystal mirror (um)

	holeRad: radius of holes in photonic crystal mirror (um)

	spacing: spacing of holes in photonic crystal mirror (um)

	offset: tuple specifying an offset of the photonic crystal mirror

	suppWidth: width of suppoort structure attaching the waveguide to box

	suppLen: length of support structure attaching the waveguide to box

	tetherSp: spacing between support tethers along the waveguide

	tetherWidth: width of the tethers

	tetherLen: length of the tethers (not including the tapered part)

	tetherMaxWidth: the width of the tapered part of the tether

	tetherTaper: the length of the tapered part of the tether

	tipSp: the space after the tip

	padding: width of surrounding rectangle (um)

	clearance: distance (in um) that the HSQ pattern overlaps with the optical
	lithography pattern

	label: a label for the disc pattern, given as a string

	txtHeight: the height of the text label on the bounding box (um)

	layer1: layer on which large patterns are drawn (require low dose)

	layer2: layer on which small pattterns are drawn (higher dose)

	layerOpt: layer for the optical lithography pattern

	taperDepth: the depth of the input taper of the photonic crystal mirror
	(default is 0.25=25%)

	taperHoles: number of input taper holes of photonic crystal mirror (default
	is 3)


	"""

	posx,posy=pos

	# estimate the length of the photonic crystal
	mirrorLen=spacing*(numHoles)

	# create the disc with bounding box

	wgLen=2*radius+gap+mirrorLen+2*tetherSp # make waveguide slightly longer by tetherSp

	# create a dictionary to store these parameters
	discParams={}
	discParams['extraLen']=mirrorLen+suppLen+tetherSp+tipSp # make waveguide slightly longer

	discParams['radius']=radius

	discCenter=posx-discParams['extraLen']/2
	discParams['pos']=(-discCenter,posy)

	discParams['gap']=gap
	discParams['padding']=padding
	discParams['clearance']=clearance
	discParams['label']=label
	discParams['txtHeight']=txtHeight
	discParams['layerRect']=layer1
	discParams['layerCircle']=layer1
	discParams['layerOpt']=layerOpt
	discParams['wgLen']=wgLen+suppLen+taperLen+tipSp
	discParams['extraWidth']=wgWidth+couplingSp
	discParams['layer']=layer


	sub,disc,txtRect,opt_rectangle=discBorder(**discParams)

	# now create the waveguide

	# the length of the waveguide should be at minimum the length of the disc

	# add the length of the photonic crystal to the waveguide length

	wg=waveguide(wgWidth,wgLen,layer1)

	# make a list to hold arguments of phc_mirror:
	mirrorParams={}
	mirrorParams['numholes']=numHoles
	mirrorParams['radius']=holeRad
	mirrorParams['spacing']=spacing
	mirrorParams['layer']=layer1 # use layer 1 since will subtract from layer 2

	# want to modify the vertical offset to be the same as the waveguide
	offx,offy=offset

	# start the photonic crystal at the end of the disk
	#mirrorOffset=(offx+radius-mirrorLen/2,offy+wgOffset)
	mirrorOffset=(offx+radius-mirrorLen/2+tetherSp,0)

	mirrorParams['offset']=mirrorOffset
	mirrorParams['taper_depth']=taperDepth
	mirrorParams['taper_holes']=taperHoles

	mirror=phc_mirror(**mirrorParams)

	# now subtract mirror from the waveguide
	# cannot offset the waveguide before subtracting mirror
	wgSub=gdspy.boolean(wg,mirror,'not')

	# calculate the offset of the waveguide:
	wgOffset=radius+gap+couplingSp+wgWidth/2

	wgCell=gdspy.Cell('waveguide '+label) # add label to the name of the cell
	wgCell.add(wgSub)
	wgRef=gdspy.CellReference(wgCell,(posx-suppLen/2+taperLen/2+tipSp/2,posy+wgOffset))

	# now add the support structure to attach the waveguide to the bounding box
	support=wg_support(wgWidth,suppWidth,suppLen,layer2)

	# now move the support structure to the end of the waveguide
	# TODO: modify cell name to be unique for every time this is called
	suppCell=gdspy.Cell('support structure '+label)
	suppCell.add(support)

	suppOffset=(posx+wgLen/2-suppLen/2+taperLen/2+tipSp/2,posy+wgOffset)
	suppRef=gdspy.CellReference(suppCell,suppOffset)

	# now add support tethers to the waveguide
	# want to add a support tether after the photonic crystal mirror
	# part where disc intersects rectangle has length 2*sqrt(rg)
	# first get the coordinates of end of photonic crystal mirror
	location0=offx+radius+gap
	location=location0

	#discWidth=2*sqrt(radius*gap)

	# the tether length is the gap width less the length of the tapered part
	tetherLen=gap-tetherTaper

	# add the arguments for generating the tether to a dictionary
	tetherParams={}

	tetherParams['w']=tetherWidth
	tetherParams['l']=tetherLen
	tetherParams['maxWidth']=tetherMaxWidth
	tetherParams['taperLen']=tetherTaper
	tetherParams['wgWidth']=wgWidth
	tetherParams['layer']=layer2

	# add generated tethers to a list
	tetherRefList=[]

	# the position of the tapered waveguide combines the offset of the waveguide
	# with the end of the waveguide
	taperx=posx-suppLen/2-wgLen/2+taperLen/2
	tapery=posy+wgOffset


	# start adding support tethers until you reach the end of the waveguide
	while (location>=posx+gap/2-suppLen/2-wgLen/2-gap):
		# now check that this is not in the overlap region of the disk
		if (location>(4/5*radius)) or \
			((location<(-3/4*radius)) and (location>(taperx))):
			# add a tether on both sides
			# make a tether
			tetherParams['dir']='up'
			tether1,suppPoly1=singleTether(**tetherParams)

			tetherParams['dir']='down'
			tether2,suppPoly2=singleTether(**tetherParams)

			# now offset the tether to the correct location

			# TODO: add some condition that checks that the tether support is
			# less than the gap length

			# want to add tether and tether support to a cell
			tetherCell=gdspy.Cell('tether '+str(location)+label)
			tetherCell.add([tether1,suppPoly1])
			tetherCell.add([tether2,suppPoly2])

			# offset the tether by the position
			# now offset the tether vertically to place it in the gap
			tetherRef=gdspy.CellReference(tetherCell,(location,posy+wgOffset))
			tetherRefList.append(tetherRef)

		elif ((location<(radius)) and (location>(-radius)) and abs(location)>radius/3):
			# add a tether only on the top
			tetherParams['dir']='up'
			tether1,suppPoly1=singleTether(**tetherParams)
			tetherCell=gdspy.Cell('tether '+str(location)+label)
			tetherCell.add([tether1,suppPoly1])
			tetherRef=gdspy.CellReference(tetherCell,(location,posy+wgOffset))
			tetherRefList.append(tetherRef)

		print('location',location)
		location-=tetherSp

	# now add tapered waveguide
	taper=input_taper(taperMinWidth,wgWidth,taperLen,layer2)

	# now move the tapered waveguide to the end of the bus waveguide
	# create a cell to store the taper
	taperCell=gdspy.Cell('taper'+label)
	taperCell.add(taper)

	taperRef=gdspy.CellReference(taperCell,(taperx+tipSp/2,tapery))

	return sub,disc,wgRef,suppRef,tetherRefList,taperRef,txtRect,opt_rectangle





def discWg_NS(radius,pos,gap,couplingSp,wgWidth,numHoles,holeRad,spacing,offset,
	suppWidth,suppLen,tetherSp,tetherWidth,tetherMaxWidth,tetherTaper,tipSp,
	padding,clearance,label,txtHeight,layer1,layer2,taperMinWidth,
	taperLen,layerOpt,layer,taperDepth=0.25,taperHoles=3):
	""" The same as discBorder(...), but now adds a bus waveguide with tethers.

	radius:  radius of disc

	pos: position of the disc inside the surrounding rectangle, given as a tuple

	gap: the gap surrounding the disc (um)

	couplingSp: the coupling distance between the disc and the bus waveguide(um)

	wgWidth: the width of the bus waveguide

	numHoles: number of holes in photonic crystal mirror (um)

	holeRad: radius of holes in photonic crystal mirror (um)

	spacing: spacing of holes in photonic crystal mirror (um)

	offset: tuple specifying an offset of the photonic crystal mirror

	suppWidth: width of suppoort structure attaching the waveguide to box

	suppLen: length of support structure attaching the waveguide to box

	tetherSp: spacing between support tethers along the waveguide

	tetherWidth: width of the tethers

	tetherLen: length of the tethers (not including the tapered part)

	tetherMaxWidth: the width of the tapered part of the tether

	tetherTaper: the length of the tapered part of the tether

	tipSp: the space after the tip

	padding: width of surrounding rectangle (um)

	clearance: distance (in um) that the HSQ pattern overlaps with the optical
	lithography pattern

	label: a label for the disc pattern, given as a string

	txtHeight: the height of the text label on the bounding box (um)

	layer1: layer on which large patterns are drawn (require low dose)

	layer2: layer on which small pattterns are drawn (higher dose)

	layerOpt: layer for the optical lithography pattern

	taperDepth: the depth of the input taper of the photonic crystal mirror
	(default is 0.25=25%)

	taperHoles: number of input taper holes of photonic crystal mirror (default
	is 3)


	"""

	posx,posy=pos

	# estimate the length of the photonic crystal
	mirrorLen=spacing*(numHoles)

	# create the disc with bounding box

	wgLen=2*radius+gap+mirrorLen+2*tetherSp # make waveguide slightly longer by tetherSp

	# create a dictionary to store these parameters
	discParams={}
	discParams['extraLen']=mirrorLen+suppLen+tetherSp+tipSp # make waveguide slightly longer

	discParams['radius']=radius

	discCenter=posx-discParams['extraLen']/2
	discParams['pos']=(-discCenter,posy)

	discParams['gap']=gap
	discParams['padding']=padding
	discParams['clearance']=clearance
	discParams['label']=label
	discParams['txtHeight']=txtHeight
	discParams['layerRect']=layer1
	discParams['layerCircle']=layer1
	discParams['layerOpt']=layerOpt
	discParams['wgLen']=wgLen+suppLen+taperLen+tipSp
	discParams['extraWidth']=wgWidth+couplingSp
	discParams['layer']=layer


	sub,disc,txtRect,opt_rectangle=discBorder(**discParams)

	# now create the waveguide

	# the length of the waveguide should be at minimum the length of the disc

	# add the length of the photonic crystal to the waveguide length

	wg=waveguide(wgWidth,wgLen,layer1)

	# make a list to hold arguments of phc_mirror:
	mirrorParams={}
	mirrorParams['numholes']=numHoles
	mirrorParams['radius']=holeRad
	mirrorParams['spacing']=spacing
	mirrorParams['layer']=layer1 # use layer 1 since will subtract from layer 2

	# want to modify the vertical offset to be the same as the waveguide
	offx,offy=offset

	# start the photonic crystal at the end of the disk
	#mirrorOffset=(offx+radius-mirrorLen/2,offy+wgOffset)
	mirrorOffset=(offx+radius-mirrorLen/2+tetherSp,0)

	mirrorParams['offset']=mirrorOffset
	mirrorParams['taper_depth']=taperDepth
	mirrorParams['taper_holes']=taperHoles

	mirror=phc_mirror(**mirrorParams)

	# now subtract mirror from the waveguide
	# cannot offset the waveguide before subtracting mirror
	wgSub=gdspy.boolean(wg,mirror,'not')

	# calculate the offset of the waveguide:
	wgOffset=radius+gap+couplingSp+wgWidth/2

	wgCell=gdspy.Cell('waveguide '+label) # add label to the name of the cell
	wgCell.add(wgSub)
	wgRef=gdspy.CellReference(wgCell,(posx-suppLen/2+taperLen/2+tipSp/2,posy+wgOffset))

	# now add the support structure to attach the waveguide to the bounding box
	support=wg_support(wgWidth,suppWidth,suppLen,layer2)

	# now move the support structure to the end of the waveguide
	# TODO: modify cell name to be unique for every time this is called
	suppCell=gdspy.Cell('support structure '+label)
	suppCell.add(support)

	suppOffset=(posx+wgLen/2-suppLen/2+taperLen/2+tipSp/2,posy+wgOffset)
	suppRef=gdspy.CellReference(suppCell,suppOffset)

	# now add support tethers to the waveguide
	# want to add a support tether after the photonic crystal mirror
	# part where disc intersects rectangle has length 2*sqrt(rg)
	# first get the coordinates of end of photonic crystal mirror
	location0=offx+radius+gap
	location=location0

	#discWidth=2*sqrt(radius*gap)

	# the tether length is the gap width less the length of the tapered part
	tetherLen=gap-tetherTaper

	# add the arguments for generating the tether to a dictionary
	tetherParams={}

	tetherParams['w']=tetherWidth
	tetherParams['l']=tetherLen
	tetherParams['maxWidth']=tetherMaxWidth
	tetherParams['taperLen']=tetherTaper
	tetherParams['wgWidth']=wgWidth
	tetherParams['layer']=layer2

	# add generated tethers to a list
	tetherRefList=[]

	# the position of the tapered waveguide combines the offset of the waveguide
	# with the end of the waveguide
	taperx=posx-suppLen/2-wgLen/2+taperLen/2
	tapery=posy+wgOffset


	# start adding support tethers until you reach the end of the waveguide
	while (location>=posx+gap/2-suppLen/2-wgLen/2-gap):
		# now check that this is not in the overlap region of the disk
		if (location>(4/5*radius)) or \
			((location<(-3/4*radius)) and (location>(taperx))):
			# add a tether on both sides
			# make a tether
			tetherParams['dir']='up'
			tether1,suppPoly1=singleTether(**tetherParams)

			tetherParams['dir']='down'
			tether2,suppPoly2=singleTether(**tetherParams)

			# now offset the tether to the correct location

			# TODO: add some condition that checks that the tether support is
			# less than the gap length

			# want to add tether and tether support to a cell
			tetherCell=gdspy.Cell('tether '+str(location)+label)
			tetherCell.add([tether1,suppPoly1])
			tetherCell.add([tether2,suppPoly2])

			# offset the tether by the position
			# now offset the tether vertically to place it in the gap
			tetherRef=gdspy.CellReference(tetherCell,(location,posy+wgOffset))
			tetherRefList.append(tetherRef)
			'''

		elif ((location<(radius)) and (location>(-radius)) and abs(location)>radius/3):
			# add a tether only on the top
			tetherParams['dir']='up'
			tether1,suppPoly1=singleTether(**tetherParams)
			tetherCell=gdspy.Cell('tether '+str(location)+label)
			tetherCell.add([tether1,suppPoly1])
			tetherRef=gdspy.CellReference(tetherCell,(location,posy+wgOffset))
			tetherRefList.append(tetherRef)
'''
		print('location',location)
		location-=tetherSp

	# now add tapered waveguide
	taper=input_taper(taperMinWidth,wgWidth,taperLen,layer2)

	# now move the tapered waveguide to the end of the bus waveguide
	# create a cell to store the taper
	taperCell=gdspy.Cell('taper'+label)
	taperCell.add(taper)

	taperRef=gdspy.CellReference(taperCell,(taperx+tipSp/2,tapery))

	return sub,disc,wgRef,suppRef,tetherRefList,taperRef,txtRect,opt_rectangle

def ring(r,w,layer1,layer2,offset=(0,0)):
	"""Makes a ring of defined radius and width. Radius is defined with respect
	to the center of the ring waveguide.

	r: radius of ring (um)

	w: width of ring waveguide (um)

	layer1: the layer on which the ring is created

	layer2:  the layer which is used to write the inner circle for the subtract

	offset: (optional) a tuple specifying a way to offset the ring
	"""


	outerRad=r+w/2
	innerRad=r-w/2

	circleOuter=gdspy.Round(offset,outerRad,number_of_points=199,**layer1)
	circleInner=gdspy.Round(offset,innerRad,number_of_points=199,**layer2)

	ring=gdspy.boolean(circleOuter,circleInner,'not')

	return ring

"""
ld_ebeam={'layer':1,'datatype':0}
layerRect={'layer':2,'datatype':0}

ring=ring(40,0.4,)
"""
"""
layerOpt={'layer':3,'datatype':0}


sub,disc,wg,suppRef,tetherRefList,taper,txtRect,opt_rectangle=discWg(20,(0,0),5,0.2,0.5,
	20,0.1,0.4,(0,0),1,1,10,0.1,1,1,6,5,1,'test',1,layerRect,ld_ebeam,0.16,17.5,layerOpt)


tether,suppPoly=singleTether(0.1,5,1,1,0.5,ld_ebeam)

final=gdspy.Cell('Final')

final.add([sub,disc,wg,suppRef,taper,txtRect,opt_rectangle])
final.add(tetherRefList)

#final.add(tether)
#final.add(suppPoly)

gdspy.write_gds('test.gds')
gdspy.LayoutViewer()
"""

if __name__ == "__main__":
	ld_test={'layer':1,'datatype':0}

	# create the test  cell
	main=gdspy.Cell('test')

	phc,length=photonic_crystal(6,9,0.107,0.8,0.392,'test',0,0.05,ld_test,1,asym=False)
	main.add(phc)
	gdspy.LayoutViewer()
