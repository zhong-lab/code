import pya
from math import cos,pi,sin,ceil
from numpy import arcsin

"""
This sample PCell implements a library called "MyLib" with a single PCell that
draws a circle. It demonstrates the basic implementation techniques for a PCell 
and how to use the "guiding shape" feature to implement a handle for the circle
radius.

NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell 
when KLayout is run.
"""

class base(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the circle
  """

  def __init__(self):

    # Important: initialize the super class
    super(base, self).__init__()

    # declare the parameters
    self.param("l", self.TypeLayer, "Layer", default = pya.LayerInfo(1, 0))
    
    
    self.param("n", self.TypeInt, "Number of points", default = 64)     
    
    self.param("rd", self.TypeDouble, "Double radius", readonly = True)
    
    # this hidden parameter is used to determine whether the radius has changed
    # or the "s" handle has been moved
    self.param("ru", self.TypeDouble, "Radius", default = 0.0, hidden = True)
    self.param("s", self.TypeShape, "", default = pya.DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = 0.1)
    
    # radius of input section
    self.param("radius", self.TypeDouble,"Width",default=56)
    
    # y span
    self.param("yspan", self.TypeDouble,"",default=4.8889)
    
    # waveguide width
    self.param("waveguidewidth", self.TypeDouble,"",default=0.667)
    
    # m
    self.param("m",self.TypeDouble,"",default=0.966667)
    
    # define the number of points used
    self.param("n", self.TypeInt, "Number of points per curve", default = 64)
    
    # define the radius
    self.param("radius",self.TypeDouble,"",default=56)
    
    # define L_extra (the area beyond the grating)
    self.param("L_extra",self.TypeDouble,"",default=10)
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Circle(L=" + str(self.l) + ",R=" + ('%.3f' % self.r) + ")"
  
  def coerce_parameters_impl(self):
  
    # We employ coerce_parameters_impl to decide whether the handle or the 
    # numeric parameter has changed (by comparing against the effective 
    # radius ru) and set ru to the effective radius. We also update the 
    # numerical value or the shape, depending on which on has not changed.
    rs = None
    if isinstance(self.s, pya.DPoint): 
      # compute distance in micron
      rs = self.s.distance(pya.DPoint(0, 0))
    if rs != None and abs(self.r-self.ru) < 1e-6:
      self.ru = rs
      self.r = rs 
    else:
      self.ru = self.r
      self.s = pya.DPoint(-self.r, 0)
    
    self.rd = 2*self.r
    
    # n must be larger or equal than 4
    if self.n <= 4:
      self.n = 4
  
  def can_create_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we can use any shape which 
    # has a finite bounding box
    return self.shape.is_box() or self.shape.is_polygon() or self.shape.is_path()
  
  def parameters_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we set r and l from the shape's 
    # bounding box width and layer
    self.r = self.shape.bbox().width() * self.layout.dbu / 2
    self.l = self.layout.get_info(self.layer)
  
  def transformation_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we use the center of the shape's
    # bounding box to determine the transformation
    return pya.Trans(self.shape.bbox().center())
  
  def produce_impl(self):
  
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu;
    ly = self.layout
    shapes = self.cell.shapes
    
    theta=arcsin(0.5*self.yspan/self.radius)*180/pi
    xmax=self.radius*cos(theta*pi/180)
    w1=self.waveguidewidth/2
    w2=self.yspan/2
    L=xmax
    
    
    # divide lengths by database unit
    xmax=xmax/dbu
    w1=w1
    print("w1 "+str(w1))
    w2=w2
    print("w2 "+str(w2))
    #print("m "+str(self.m))
    L=L
    print("L "+str(L))    
    
    #radius of outer edge
    rad=self.radius*cos(theta*pi/180)
    
    alpha=(w1-w2)/(L**self.m)
    #print("alpha "+str(alpha))
    
    # vector to store widths of each point along taper section
    pts=[]
    taper_widths=[]
    
    # spacing between each point
    dx1=rad/(self.n)
    
    # calculate the width of taper section at each point
    
    for i in range(0, self.n):
        print("i: "+str(i))
        pts.append(pya.Point.from_dpoint(pya.DPoint(i*dx1/dbu, (alpha*(rad-i*dx1)**self.m+w2)/dbu)))
        num=(alpha*(rad-i*dx1)**self.m+w2)/dbu
        taper_widths.append(num)
    
    # now define the points that make up the outer edge of the taper section
    
    #radius of outer edge
    rad=self.radius*cos(theta*pi/180)
    
    print("theta "+str(theta))
    print("theta/180 "+str(theta/180*pi))
    print("rad "+str(rad))
    
    #arc length of outer edge
    # theta is given in units of degrees
    arc=theta/180*pi*rad
    print("arc "+str(arc))
    print("alpha "+str(alpha))
    print("w1 "+str(w1))
    print("w2 "+str(w2))
    
    # spacing between each point
    dx2=arc/self.n
  
    # top part of outer arc
    for i in range(0,self.n+1):
     pts.append(pya.Point.from_dpoint(pya.DPoint(rad*cos(theta*pi/180*(self.n-i)/self.n)/dbu,(rad*sin(theta*pi/180*(self.n-i)/self.n)/dbu))))
    
    # bottom part of outer arc
    for i in range(0,self.n):
       pts.append(pya.Point.from_dpoint(pya.DPoint((rad*cos(theta*pi/180*i/self.n))/dbu,(-rad*sin(theta*pi/180*i/self.n))/dbu)))
      
    # returning points along taper
    #taper_widths.reverse()
    for i in range(1,self.n+1):
       pts.append(pya.Point.from_dpoint(pya.DPoint((rad-i*dx1)/dbu,-taper_widths[-(i)])))
    
    # points connecting input part of taper
    #dx3=w1/2
    #for i in range(0,self.n+1):
     #   pts.append(pya.Point.from_dpoint(pya.DPoint(0,i*dx3)))
    
    # add section for lower layer below grating
    pts_below=[]
    
    # add one point at the upper corner of taper section
    pts_below.append(pya.Point.from_dpoint(pya.DPoint(rad*cos(theta*pi/180)/dbu,rad*sin(theta*pi/180)/dbu)))
    
    # create the outer arc of the taper section
    
    # define the radius of the outer part of the taper section
    outer_rad=rad+L+self.L_extra
    
    # upper part of outer arc
    for i in range(0,self.n):
        pts_below.append(pya.Point.from_dpoint(pya.DPoint(outer_rad*cos(theta*pi/180*(self.n-i)/self.n)/dbu,(outer_rad*sin(theta*pi/180*(self.n-i)/self.n)/dbu))))
      #x1=outer_rad*cos(theta*pi*(self.n-i)/self.n/180)/dbu
      #y1=outer_rad*sin(theta*pi*(self.n-i)/self.n/180)/dbu
      #pts_below.append(pya.Point.from_dpoint(pya.DPoint(x1,y1)))
    
    # lower part of outer arc
    for i in range(0,self.n):
        pts_below.append(pya.Point.from_dpoint(pya.DPoint(outer_rad*cos(theta*pi/180*i/self.n)/dbu,-(outer_rad*sin(theta*pi/180*i/self.n)/dbu))))
     # x2=outer_rad*cos(theta*pi*i/self.n)/dbu
      #y2=-outer_rad*sin(theta*pi*i/self.n)/dbu
      #pts_below.append(pya.Point.from_dpoint(pya.DPoint(x2,y2)))
      
    # add one point at the bottom corner of taper section
    pts_below.append(pya.Point.from_dpoint(pya.DPoint(rad*cos(theta*pi/180)/dbu,-rad*sin(theta*pi/180)/dbu)))
    
    # taper section
    taper=pya.Polygon(pts)
    
    # grating section
    grating=pya.Polygon(pts_below)
    
    # create the shape
    self.cell.shapes(self.l_layer).insert(taper)
    self.cell.shapes(self.l_layer).insert(grating)
  
class Ridges(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the circle
  """

  def __init__(self):

    # Important: initialize the super class
    super(Ridges, self).__init__()

    # declare the parameters
    self.param("l", self.TypeLayer, "Layer", default = pya.LayerInfo(1, 0))
    
    
    self.param("n", self.TypeInt, "Number of points", default = 64)     
    
    self.param("rd", self.TypeDouble, "Double radius", readonly = True)
    
    # this hidden parameter is used to determine whether the radius has changed
    # or the "s" handle has been moved
    self.param("ru", self.TypeDouble, "Radius", default = 0.0, hidden = True)
    self.param("s", self.TypeShape, "", default = pya.DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = 0.1)
    
    # y span
    self.param("yspan", self.TypeDouble,"",default=4.8889)
    
    # number of periods
    self.param("target_length",self.TypeDouble,"",default=40)
    
    # pitch
    self.param("pitch",self.TypeDouble,"",default=0.704153)
    
    # radius
    self.param("radius",self.TypeDouble,"",default=56)
    
    # duty cycle
    self.param("duty_cycle",self.TypeDouble,"",default=0.279887)
    
    # extra length added to the grating coupler ridges
    self.param("theta_ext",self.TypeDouble,"",default=2)
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Circle(L=" + str(self.l) + ",R=" + ('%.3f' % self.r) + ")"
  
  def coerce_parameters_impl(self):
  
    # We employ coerce_parameters_impl to decide whether the handle or the 
    # numeric parameter has changed (by comparing against the effective 
    # radius ru) and set ru to the effective radius. We also update the 
    # numerical value or the shape, depending on which on has not changed.
    rs = None
    if isinstance(self.s, pya.DPoint): 
      # compute distance in micron
      rs = self.s.distance(pya.DPoint(0, 0))
    if rs != None and abs(self.r-self.ru) < 1e-6:
      self.ru = rs
      self.r = rs 
    else:
      self.ru = self.r
      self.s = pya.DPoint(-self.r, 0)
    
    self.rd = 2*self.r
    
    # n must be larger or equal than 4
    if self.n <= 4:
      self.n = 4
  
  def can_create_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we can use any shape which 
    # has a finite bounding box
    return self.shape.is_box() or self.shape.is_polygon() or self.shape.is_path()
  
  def parameters_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we set r and l from the shape's 
    # bounding box width and layer
    self.r = self.shape.bbox().width() * self.layout.dbu / 2
    self.l = self.layout.get_info(self.layer)
  
  def transformation_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we use the center of the shape's
    # bounding box to determine the transformation
    return pya.Trans(self.shape.bbox().center())
  
  def produce_impl(self):
  
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu;
    ly = self.layout
    shapes = self.cell.shapes
    theta=arcsin(0.5*self.yspan/self.radius)*180/pi+self.theta_ext
    rad=self.radius*cos(theta*pi/180)
    
    n_periods=int(ceil(self.target_length/self.pitch))
    print("n_periods "+str(n_periods))
    
    etch_width=self.pitch*(1-self.duty_cycle)
    
    # for each grating ridge
    for i in range(1,n_periods):
        
        pts=[]
        # create the points for the inside of the grating
        
        # inner radius of the ridge
        rad_inner=rad+self.pitch*(i-1)+etch_width
        
        # outer radius of the ridge
        rad_outer=rad+self.pitch*i
        
        # do the top part of the inner arc
        for i in range(0,self.n):
            pts.append(pya.Point.from_dpoint(pya.DPoint(rad_inner*cos(theta*pi/180*(self.n-i)/self.n)/dbu,(rad_inner*sin(theta*pi/180*(self.n-i)/self.n)/dbu))))
        
        # bottom part of inner arc
        for i in range(0,self.n):
             pts.append(pya.Point.from_dpoint(pya.DPoint(rad_inner*cos(theta*pi/180*i/self.n)/dbu,-rad_inner*sin(theta*pi/180*i/self.n)/dbu)))
             
        # bottom part of outer arc
        for i in range(0,self.n):
          pts.append(pya.Point.from_dpoint(pya.DPoint(rad_outer*cos(theta*pi/180*(self.n-i)/self.n)/dbu,-rad_outer*sin(theta*pi/180*(self.n-i)/self.n)/dbu)))
          
        #top part of outer arc
        for i in range(0,self.n):
          pts.append(pya.Point.from_dpoint(pya.DPoint(rad_outer*cos(theta*pi/180*i/self.n)/dbu,rad_outer*sin(theta*pi/180*i/self.n)/dbu)))
              
        ridge=pya.Polygon(pts)
        self.cell.shapes(self.l_layer).insert(ridge)
        
class Bragg(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the circle
  """

  def __init__(self):

    # Important: initialize the super class
    super(Bragg, self).__init__()

    # declare the parameters
    self.param("l", self.TypeLayer, "Layer", default = pya.LayerInfo(1, 0))
    self.param("s", self.TypeShape, "", default = pya.DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = 0.1)
    self.param("n", self.TypeInt, "Number of points", default = 64)     
    # this hidden parameter is used to determine whether the radius has changed
    # or the "s" handle has been moved
    self.param("ru", self.TypeDouble, "Radius", default = 0.0, hidden = True)
    self.param("rd", self.TypeDouble, "Double radius", readonly = True)
    
    # define the number of holes in the taper section
    self.param("taper", self.TypeInt, "number of taper holes",default=9)
    
    # define the percentage smaller that the smallest hole is
    self.param("depth", self.TypeDouble, "taper depth", default=0.8)    
    
    # define the radius of untapered holes
    self.param("radius", self.TypeDouble, "radius", default=0.200)
    
    # define the spacing between untapered holes
    self.param("spacing", self.TypeDouble, "spacing", default=0.600)
    
    # define the number of untapered holes
    self.param("normal",self.TypeInt, "number of normal holes", default=20)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Circle(L=" + str(self.l) + ",R=" + ('%.3f' % self.r) + ")"
  
  def coerce_parameters_impl(self):
  
    # We employ coerce_parameters_impl to decide whether the handle or the 
    # numeric parameter has changed (by comparing against the effective 
    # radius ru) and set ru to the effective radius. We also update the 
    # numerical value or the shape, depending on which on has not changed.
    rs = None
    if isinstance(self.s, pya.DPoint): 
      # compute distance in micron
      rs = self.s.distance(pya.DPoint(0, 0))
    if rs != None and abs(self.r-self.ru) < 1e-6:
      self.ru = rs
      self.r = rs 
    else:
      self.ru = self.r
      self.s = pya.DPoint(-self.r, 0)
    
    self.rd = 2*self.r
    
    # n must be larger or equal than 4
    if self.n <= 4:
      self.n = 4
  
  def can_create_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we can use any shape which 
    # has a finite bounding box
    return self.shape.is_box() or self.shape.is_polygon() or self.shape.is_path()
  
  def parameters_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we set r and l from the shape's 
    # bounding box width and layer
    self.r = self.shape.bbox().width() * self.layout.dbu / 2
    self.l = self.layout.get_info(self.layer)
  
  def transformation_from_shape_impl(self):
    # Implement the "Create PCell from shape" protocol: we use the center of the shape's
    # bounding box to determine the transformation
    return pya.Trans(self.shape.bbox().center())
  
  def produce_impl(self):
  
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    ru_dbu = self.ru / self.layout.dbu
    
    dist=0
    da = math.pi * 2 / self.n

    for i in range(0,self.taper):
    
      pts=[]
      
      rad_dbu=self.radius/self.layout.dbu
      
      # calculate the size of the hole
      rad=self.depth*rad_dbu+(i**2)/float(self.taper-1)**2*(1-self.depth)*rad_dbu
      
      print('rad: '+str(rad))
      print('i: '+str(i))
      # calculate the spacing between the last taper hole
      sp=self.depth*self.spacing+(i**2)/float(self.taper-1)**2*(1-self.depth)*self.spacing
      
      # add to the total distance along mirror
      dist+=sp
      
      # create a circle at the correct position
      # iterate through all the points on each circle
      for j in range(0,self.n):
        pts.append(pya.Point.from_dpoint(pya.DPoint((rad*math.cos(j*da)+dist/self.layout.dbu),(rad*math.sin(j*da)))))
    
      # create the shape for this circle
      self.cell.shapes(self.l_layer).insert(pya.Polygon(pts))
      
    print('self.normal: '+str(self.normal))
    
    # now create the untapered holes
    for i in range(0,int(self.normal)):
      pts=[]
      rad_dbu=self.radius/self.layout.dbu
      
      # add the total distance along mirror
      dist+=self.spacing
      
      # create a circle at the correct position
      # iterate through all the points on each circle
      for j in range(0,self.n):
        pts.append(pya.Point.from_dpoint(pya.DPoint((rad*math.cos(j*da)+dist/self.layout.dbu),(rad*math.sin(j*da)))))
        
      # create the shape for this circle
      self.cell.shapes(self.l_layer).insert(pya.Polygon(pts))
    
class photonics(pya.Library):
  """
  The library where we will put the PCell into 
  """

  def __init__(self):
  
    # Set the description
    self.description = "photonics_library"
    
    # Create the PCell declarations
    self.layout().register_pcell("grating coupler base", base())
    self.layout().register_pcell("grating coupler ridges",Ridges())
    self.layout().register_pcell("Bragg mirror",Bragg())
    # That would be the place to put in more PCells ...
    
    # Register us with the name "MyLib".
    # If a library with that name already existed, it will be replaced then.
    self.register("photonics")


# Instantiate and register the library
photonics()