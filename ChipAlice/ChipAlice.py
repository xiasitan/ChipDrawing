
from QubitEBLDesignV1 import *
from copy import deepcopy
import os
#  I want to save the generated file in the directory of the script.
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

def qubit(conf: DefaultConfig, test, isCirc = False, cLlayer = 6, fLlayer = 13 ):
    bridgeFreeJJ1 = bridgeFreeJJ(conf)
    size1 = getSize(bridgeFreeJJ1)
    
    coarseLead1, fineLead1 = translate(qubitLead(conf, test, isCirc), 0, size1[1]/2)
    coarseLead2, fineLead2 = rotate(copy([coarseLead1, fineLead1]), pi, [0,0])
    discharger1 = [] if test else discharger(conf)
    
    # added some mmodifications to allow adjusting fineLead and CoarseLead border layer
    # Create a mask of the joined coarselead + fine lead border to use for boolean and
    _joinedLead = [join([coarseLead1, coarseLead2] + discharger1), fineLead1, fineLead2]
    _border = makeBorder(conf, _joinedLead)
    _border = cut(_border, myRectangle([size1[0]*10, size1[1]]))#.fillet(10, max_points=1000)
    
    joinedcoarseLead = [join([coarseLead1, coarseLead2] + discharger1)]
    joinedfineLead = [fineLead1, fineLead2]
    
    # Create border for coarseLead (large rectangles and Pads)
    bordercL = makeBorder(conf, joinedcoarseLead)
    bordercL = cut(bordercL, myRectangle([size1[0]*10, size1[1]]))#.fillet(10, max_points=1000)
    bordercL = gdspy.boolean(_border,bordercL,"and", layer= cLlayer)
    
    # Create border for fine lead
    borderfL = makeBorder(conf,joinedfineLead)
    borderfL = cut(borderfL, myRectangle([size1[0]*10, size1[1]]))#.fillet(10, max_points=1000)
    borderfL = gdspy.boolean(_border,borderfL,"and", layer= fLlayer)
    borderfL = gdspy.boolean(borderfL,bordercL,"not", layer= fLlayer)
    
    joinedLead = joinedcoarseLead + joinedfineLead
    borders = [bordercL, borderfL]
    return bridgeFreeJJ1 + joinedLead + borders

def filledChip(conf: DefaultConfig, texts):
    verDist, horDist = conf.verticalDistances, conf.horizontalDistances
    # make elements
    markerL1 = markerL(conf, text=texts[0])
    markerL2 = markerL(conf, text=texts[1], rotation= -pi/2)
    markerV1 = markerV(conf)
    markerV2 = markerV(conf, rotation= pi)
    resonator1 = resonator(conf)
    qubit1 = qubit(conf, test=False, isCirc = True)
    snake1 = snake(conf, direction = False)
    markerV3 = markerV(conf, rotation = pi)
    markerV4 = markerV(conf)
    markerV5 = markerV(conf)
    markerV6 = markerV(conf, rotation= pi)
    markerL3, markerL4 = copy(markerL1), copy(markerL2)
    testQubit1 = qubit(conf, test=True, isCirc=True)
    markerL5 = markerL(conf, rotation= pi/2)
    markerL6 = markerL(conf, rotation= pi)
    # calculate positions
    sizes = getSize(resonator1), getSize(qubit1), getSize(snake1), getSize(testQubit1)
    yMarkerV1 = verDist[0]
    yResonator = yMarkerV1 + verDist[1] + sizes[0][1] / 2
    yQubit = yResonator + sizes[0][1] / 2 + verDist[2] + sizes[1][1] / 2
    ySnake = yQubit + sizes[1][1] / 2 + verDist[3] + conf.snakeRadius
    yMarkerV3 = ySnake + sizes[2][1]-conf.snakeRadius + verDist[4]
    yMarkerV5 = yMarkerV3 + verDist[5]
    
    yMarkerL1 = yMarkerV5 + verDist[6]
    yTestQubit = yMarkerL1 + verDist[7] + sizes[3][1] / 2
    yMarkerL2 = yTestQubit + verDist[7] + sizes[3][1] / 2
    xMarker = horDist[0] / 2
    xTestQubit = lambda i: (sizes[3][0] + horDist[1]) * (i- (conf.numTestQubits-1)/2 )
    # translate elements
    translate(markerL1 + markerL3 + markerL5 + markerV1 + markerV3 + markerV5, -xMarker, 0)
    translate(markerL2 + markerL4 + markerL6 + markerV2 + markerV4 + markerV6,  xMarker, 0)
    testQubits = []
    for i in range(conf.numTestQubits):
        testQubits += translate(copy(testQubit1), xTestQubit(i), -yTestQubit) 
    translate(markerV1 + markerV2, 0, -yMarkerV1)
    translate(resonator1         , 0, -yResonator)
    translate(qubit1             , 0, -yQubit)
    translate(snake1             , 0, -ySnake)
    translate(markerV3 + markerV4, 0, -yMarkerV3)
    translate(markerV5 + markerV6, 0, -yMarkerV5)
    translate(markerL3 + markerL4, 0, -yMarkerL1)
    translate(markerL5 + markerL6, 0, -yMarkerL2)
    parts = (
        markerL1 + markerL2 + markerL3 + markerL4 + markerL5 + markerL6
        + markerV1 + markerV2 + resonator1 + qubit1 + snake1 + markerV3 
        + markerV4+ markerV5 + markerV6+ testQubits
    )
    borders = [makeBorder(conf, parts) for parts in [
        markerL1, markerL2, markerL3, markerL4, markerL5, markerL6,
        markerV1, markerV2, resonator1, snake1, markerV3, markerV4, 
        markerV5, markerV6
    ]]
    return parts + [makeChip(conf, parts)] + borders

def filledWafer():
    conf0 = DefaultConfig()
    # modification for Alice
    # resonator
    conf0.resonatorSize = [150, 9800]
    # qubitLead            -- fine --======= corse EEEEEEEE
    conf0.qubitCircRadius = 300
    conf0.qubitCircLeadSizes = ([10, 40], [40, 100])
    conf0.qubitTestSize  =                            80
    conf0.qubitLeadGaps  = (       0,        0         )
    conf0.qubitLeadOverlap =      10      
    # discharger
    conf0.dischargerRadius = 250
    conf0.dischargerWidth = 6
    conf0.dischargerAngles = [pi/2, -pi/2]
    # snake
    conf0.snakeNumHooks = 7
    conf0.snakeFinHorLineLen = 700
    # vertical distances:      markerL - markerV - resonator - qubit - snake - markerV - markerV - markerL - testQubit
    conf0.verticalDistances = [        2500,    800,       2500,    3000,   1960,      5360,          580,     590,       ]
    # horizontal distances:      marker - marker, testQubit - testQubit
    conf0.horizontalDistances = [      3200,                415         ]
    
    chips = []
    parts = []
    for i, JJWidth in enumerate(np.linspace(1.52, 1.66, 8)):
        confI = deepcopy(conf0)
        confI.bridgeFreeJJSizes[3][0] = JJWidth
        chips.append( filledChip(confI, texts=['Col%d' % (i+1), 'W%.2f' % JJWidth]) )
    size = getSize(chips[0])
    for i, chip in enumerate(chips):
        parts += translate(chip, (size[0] + conf0.chipMargin)*i , 0) 
    moveToOrigin(parts)
    grid = makeGrid(conf0, parts)
    makeFile('ChipAlice.gds', parts + grid + wafer(conf0))

filledWafer()
    
    