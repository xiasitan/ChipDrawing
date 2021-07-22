
"""
conda install -c conda-forge gdspy

The units used to represent shapes in the GDSII format are defined by the user. 
The default unit in gdspy is 1 um. But that can be easily changed by the user.
"""

import gdspy
from gdspy import copy
import numpy as np 

pi = np.pi

class DefaultConfig:
    def __init__(self):
        # wafer
        self.waferRadius = 25397 # radius of the wafer
        self.waferSliceAt = -24122 # position of the cut - the waver left from a vertical line at the specified position is removed
        self.waferLayer = 0
        # grid
        self.gridSize = [290, 300] # [x,y]
        self.gridLayer = 15
        # chip 
        self.chipPadding = 195 # Distances between the outwards facing edges of the markers and the boarders of the respective chip
        self.chipMargin = 100 # distance between two chips
        self.chipLayer = 1
        # marker
        self.markerLayer = 12
        # markerL 
        self.markerLSize = [200, 200]
        self.markerLWidth = 20
        self.markerLTextSize = 40
        # markerV
        self.markerVSize = [400, 200]
        # resonator
        self.resonatorSize = [152, 9143] # resonator dimensions [width, length]
        self.resonatorLayer = 12
        #Snake
        self.snakeRadius = 550 
        self.snakeThickness = 200
        self.snakeNeck = 1100 # Starting at the center of the circle!
        self.snakeCenTurnRad = 200 # CentralTurnRadius
        self.snakeHorLineLen = 1400
        self.snakeNumHooks = 4 # Number of full hooks. A hook is a 180 degree turn and a full line segment
        self.snakeLayer = 12 # set to the same layer as resonator
        self.snakeFinHorLineLen = 700 # len of the Final horiz line. Should be smaller then snake.HorLineLen!
        # qubitLead           -- fine --======= corse EEEEEEEE
        self.qubitLeadSizes = ([2, 20], [10, 100], [400, 800 ]) # fine lead, coarse lead, main body
        self.qubitCircLeadSizes =  ([2, 20], [10, 100])
        self.qubitCircRadius = 200
        self.qubitTestSize  =                             80
        self.qubitLeadGaps  = (       10,        40          )
        self.qubitLeadOverlap =       1.5      
        self.qubitLeadLayers = [  11,            12          ] 
        # discharger
        self.dischargerRadius = 400 # seems to be defined as a circle, drawn between the specified angles with the qubit center as its center.
        self.dischargerWidth = 4
        self.dischargerAngles = [pi/2, -pi/2]
        self.dischargerLayer = 12
        # bridgeFreeJJ
        self.bridgeFreeJJSizes = ([0.58, 0.9], [0.5, 0.9], [0.4, 0.7], [1.66, 0.1])
        self.bridgeFreeJJLayers = [8, 10, 9, 7]
        # border
        self.borderWidth = 0.4 # tiny layer sheating every drawn geometry
        self.borderLayer = 6
        # vertical distances:      markerL - markerV - resonator - qubit - markerL - testQubit
        self.verticalDistances = [        6165,    12845,       800,    750,      685,       ]
        # horizontal distances:      marker - marker, testQubit - testQubit
        self.horizontalDistances = [      3500,                415         ]
        # quantities
        self.numTestQubits = 4
        # UNDER TEST
        self.padRadius = 300

# operations

def join(parts): 
    layer = parts[0].layers[0] if isinstance(parts, list) else parts.layers[0]
    return gdspy.boolean(parts,None,'or', layer=layer, max_points=10000)
def cut(a,b): return gdspy.boolean(a,b,'not', layer=a.layers[0], max_points=10000)
def translate(parts, dx, dy): return [a.translate(dx, dy) for a in parts]
def rotate(parts, angle, center): return [a.rotate(angle, center) for a in parts]
def moveToOrigin(parts):
    point1, point2 = join(parts).get_bounding_box()
    dx, dy = -(point1 + point2)/2
    return translate(parts, dx,dy)

def makeBorder(conf: DefaultConfig, parts): 
    # working principle: take an object, expand it, cut the original object from the expanded one and return the result as border.
    return cut(gdspy.offset(parts, conf.borderWidth, layer=conf.borderLayer), parts)
def makeChip(conf: DefaultConfig, parts):
    padding = conf.chipPadding
    point1, point2 = join(parts).get_bounding_box()
    return gdspy.Rectangle(point1 - padding, point2 + padding, layer=conf.chipLayer) 
def makeGrid(conf: DefaultConfig, parts):
    dX, dY = getSize(parts) / 2
    dx, dy = conf.gridSize
    layer = conf.gridLayer
    numX, numY = int(np.ceil(dX/dx)), int(np.ceil(dY/dy))
    rectangles = []
    for i in range(-numX, numX+1):
        for j in range(-numY, numY+1):
            rectangles.append(myRectangle([dx,dy], layer, [i*dx, j*dy]))
    texts = [
        gdspy.Text('Extent %s'     % str([dX, dY]), dy, [-numX*dx, numY*dy + dy*2], layer=layer),
        gdspy.Text('Field Size %s' % str([dx, dy]), dy, [-numX*dx, numY*dy + dy], layer=layer),
    ]
    return rectangles + texts
def makeFile(filename, parts):
    lib = gdspy.GdsLibrary()
    cell = lib.new_cell('cell')
    cell.add(parts)
    cell.add(gdspy.Label('origin', [0,0]))
    lib.write_gds(filename)
    gdspy.LayoutViewer()

# calculations

def getSize(parts): 
    points = join(parts).get_bounding_box()
    return points[1] - points[0]

# basic parts

def myRectangle(size, layer=0, center=[0,0]):
    point1 = np.array(size) * 0.5
    return gdspy.Rectangle(point1, -point1, layer=layer).translate(*center)

# the following functions all returns a list of gdspy part
# parts that appear once

def wafer(conf: DefaultConfig):
    circle = gdspy.Round([0,0], 1, layer=conf.waferLayer,
        tolerance=1e-3).scale(conf.waferRadius)
    wafer = gdspy.slice(circle, conf.waferSliceAt, 0)[1]
    return [wafer]

# parts that appear many times

def markerL(conf: DefaultConfig, text='', rotation=0):
    dx, w, ts = conf.markerLSize[0], conf.markerLWidth, conf.markerLTextSize
    markerL = gdspy.FlexPath([(0,-dx), (0,0), (dx, 0)], w, layer=conf.markerLayer).to_polygonset()
    text = gdspy.Text(text, ts, [w, w], layer=conf.markerLayer).rotate(-pi/2)
    if rotation == -pi/2:
        text.translate(-dx, 0)
    return [markerL.rotate(rotation), text]

def markerV(conf: DefaultConfig, rotation=0):
    dx, dy = conf.markerVSize
    markerV = gdspy.Polygon([(0,0), (dx, -dy/2), (dx, dy/2)], layer=conf.markerLayer)
    return [markerV.rotate(rotation)]

def resonator(conf: DefaultConfig):
    return [myRectangle(conf.resonatorSize, conf.resonatorLayer)]

def snake(conf: DefaultConfig, direction = True):
    SnakeHead = gdspy.Round([0,0],conf.snakeRadius, layer = conf.snakeLayer)
    SnakeBody = gdspy.Path(conf.snakeThickness, (0, 0))
    # create the neck, first turn and first horizontal line element
    if direction:
        SnakeBody.segment(conf.snakeNeck, "+y")
    else:
        SnakeBody.segment(conf.snakeNeck, "-y")
        
    SnakeBody.turn(conf.snakeCenTurnRad,"r")
    SnakeBody.segment(conf.snakeHorLineLen/2-conf.snakeCenTurnRad)
    
    # create as many full hooks as specified in conf0 plus an additional final turn
    if conf.snakeNumHooks%2 == 0: # if even
        for i in range(math.ceil(conf.snakeNumHooks/2)):
            SnakeBody.turn(conf.snakeCenTurnRad,"ll")
            SnakeBody.segment(conf.snakeHorLineLen)
            SnakeBody.turn(conf.snakeCenTurnRad,"rr")
            SnakeBody.segment(conf.snakeHorLineLen)
        SnakeBody.turn(conf.snakeCenTurnRad,"ll")
    else: # if odd
        SnakeBody.turn(conf.snakeCenTurnRad,"ll")
        SnakeBody.segment(conf.snakeHorLineLen)
        for i in range(math.ceil((conf.snakeNumHooks-1)/2)):
            SnakeBody.turn(conf.snakeCenTurnRad,"rr")
            SnakeBody.segment(conf.snakeHorLineLen)
            SnakeBody.turn(conf.snakeCenTurnRad,"ll")    
            SnakeBody.segment(conf.snakeHorLineLen)
        SnakeBody.turn(conf.snakeCenTurnRad,"rr")        
    # Final Horizontal line segment
    SnakeBody.segment(conf.snakeFinHorLineLen)
    
    Snake = join([SnakeHead] + [SnakeBody])
    return [Snake]

def qubitLead(conf: DefaultConfig, test = False, isCirc = False ):
    """Create the Qubit Pad, Coarse Lead and Fine Lead. The Pad and Coarse Lead are added together into Corse Lead.

    Args:
        conf (DefaultConfig): dictionary holding all geometric variables
        test (bool, optional): Decides if the Junction is a test junction. Defaults to False.
        isCirc (bool, optional): To turn the qubitPad into a circle. Defaults to False.

    Returns:
        list[polygon, polygon]: [description]
    """
    # Here, I want to either load the dimensions for the circular qubit or the rec one.
    # Also, if it is a test qubit as we mainly care about the junction.
    
    if isCirc:
        sizes = conf.qubitCircLeadSizes
        radius = conf.qubitCircRadius
    else: 
        sizes = conf.qubitLeadSizes
    if test: 
        sizes = conf.qubitLeadSizes
        sizes[2][1] = conf.qubitTestSize
        
    gaps = conf.qubitLeadGaps
    layers = conf.qubitLeadLayers
    curve = gdspy.Curve(0)
    # This part takes care of drawing out the fineLead, CoraseLead and if isCirc = False the pad.
    # The way it works is by drawing half the structure (vertical cut) and then mirroring it over.
    for i, size in enumerate(sizes):
        w1, h1 = size
        if i == 0:
            dx = dy = w1/2
            curve.c(dx,0, dx,0, dx,dy).v(h1-dy)
        else:
            dx, dy = (w1-sizes[i-1][0])/2, gaps[i-1]
            curve.c(0,dy/2, dx,dy/2, dx,dy).v(h1)
    curve.h(-sizes[-1][0]/2)
    # Mirror operation.
    halfLead = gdspy.Polygon(curve.get_points())
    lead = join([ halfLead, copy(halfLead).mirror([0,1]) ])
    # Seperating the single gdspy object into coarse and fine lead
    slice1 = sizes[0][1]+gaps[0]
    slice2 = slice1 + conf.qubitLeadOverlap
    coarseLead = gdspy.slice(lead, slice1, 1, layer=layers)[1]
    fineLead   = gdspy.slice(lead, slice2, 1, layer=layers)[0]
    if isCirc and not test:
        CirclePad = gdspy.Round(center=[0,sizes[0][1]+sizes[1][1]+radius+gaps[0]-conf.qubitLeadOverlap], radius=radius,layer=layers[1])
        coarseLead = join([coarseLead,CirclePad])   
    return coarseLead, fineLead

def discharger(conf: DefaultConfig):
    w, r, angles = conf.dischargerWidth, conf.dischargerRadius, conf.dischargerAngles
    return [gdspy.Path(w, [0, r]).arc(r, *angles, layer=conf.dischargerLayer)]

def bridgeFreeJJ(conf: DefaultConfig):
    sizes = conf.bridgeFreeJJSizes
    layers = conf.bridgeFreeJJLayers
    rectangles = [myRectangle(size, layers[i]) for i,size in enumerate(sizes)]
    dy0 = ( sizes[0][1] + sizes[3][1] ) / 2
    dx1 = ( sizes[0][0] - sizes[1][0] ) / 2
    dx2 = ( sizes[0][0] - sizes[2][0] ) / 2
    rectangles[0].translate(0, dy0)
    rectangles[1].translate(dx1, dy0)
    rectangles[2].translate(dx2, dy0)
    rectangles[0] = cut(rectangles[0], rectangles[1])
    rectangles[1] = cut(rectangles[1], rectangles[2])
    for i in range(3):
        rectangles.append(copy(rectangles[i]).rotate(pi))
    return rectangles

def snake(conf: DefaultConfig, direction = True):
    SnakeHead = gdspy.Round([0,0],conf.snakeRadius, layer = conf.snakeLayer)
    SnakeBody = gdspy.Path(conf.snakeThickness, (0, 0))
    # create the neck, first turn and first horizontal line element
    if direction:
        SnakeBody.segment(conf.snakeNeck, "+y")
    else:
        SnakeBody.segment(conf.snakeNeck, "-y")
        
    SnakeBody.turn(conf.snakeCenTurnRad,"r")
    SnakeBody.segment(conf.snakeHorLineLen/2-conf.snakeCenTurnRad)
    
    # create as many full hooks as specified in conf0 plus an additional final turn
    if conf.snakeNumHooks%2 == 0: # if even
        for i in range(math.ceil(conf.snakeNumHooks/2)):
            SnakeBody.turn(conf.snakeCenTurnRad,"ll")
            SnakeBody.segment(conf.snakeHorLineLen)
            SnakeBody.turn(conf.snakeCenTurnRad,"rr")
            SnakeBody.segment(conf.snakeHorLineLen)
        SnakeBody.turn(conf.snakeCenTurnRad,"ll")
    else: # if odd
        SnakeBody.turn(conf.snakeCenTurnRad,"ll")
        SnakeBody.segment(conf.snakeHorLineLen)
        for i in range(math.ceil((conf.snakeNumHooks-1)/2)):
            SnakeBody.turn(conf.snakeCenTurnRad,"rr")
            SnakeBody.segment(conf.snakeHorLineLen)
            SnakeBody.turn(conf.snakeCenTurnRad,"ll")    
            SnakeBody.segment(conf.snakeHorLineLen)
        SnakeBody.turn(conf.snakeCenTurnRad,"rr")        
    # Final Horizontal line segment
    SnakeBody.segment(conf.snakeFinHorLineLen)
    
    Snake = join([SnakeHead] + [SnakeBody])
    return [Snake]