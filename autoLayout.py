
"""
    verticalDistances = [        6165,    12845,       800,    750,      685,        685       ]
    horizontalDistances = [3500,     3500,        0,        0,    3500,       415,      3500  ]
"""

def autoLayout(topology, distances):
    horDist, verDist = distances
    parts = []
    sizes = np.zeros([10, 10, 2])
    for i, row in enumerate(topology):
        for j, column in enumerate(row):
            sizes[i,j] = getSize(column)
    for i, row in enumerate(topology):
        for j, column in enumerate(row):
            if len(row)>1:
                dx = (horDist[i] + sizes[i,j,0]) * (j - (len(row)-1)/2)
            else:
                dx = 0
            dy = -( np.sum(verDist[:i]) + np.sum(sizes[:i,0,1]) + sizes[i,j,1] / 2 )
            parts.extend(translate(column, dx, dy))
    return parts

def testAutoLayoutIndexing():
    sizes = [1, 2, 3]
    dist = [4, 5]
    for i, _ in enumerate(sizes):
        print(i, dist[:i], sizes[:i], sizes[i])
testAutoLayoutIndexing()

"""
    topology = [
        [markerL1, markerL2],
        [markerV1, markerV2],
            [resonator1],
              [qubit1],
        [markerL3, markerL4],
        [qubit2, qubit3, qubit4, qubit5],
        [markerL5, markerL6],
    ]
    distances = [ conf.horizontalDistances, conf.verticalDistances ]
"""