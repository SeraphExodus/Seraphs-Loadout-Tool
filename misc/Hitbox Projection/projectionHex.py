import itertools
import matplotlib.pyplot as plt
import numpy as np
import operator

from datetime import datetime

def precisionRounding(x,precision,dir):
    if dir == 'floor':
        return round((x-precision/2) * 1/precision,0) * precision
    elif dir == 'ceil':
        return round((x+precision/2) * 1/precision,0) * precision
    else:
        return round(x * 1/precision,0) * precision

def generatePointGrid(vertexProjection,spacing):

    quadrant1 = [0,0]
    quadrant2 = [0,0]
    quadrant3 = [0,0]
    quadrant4 = [0,0]

    for i in vertexProjection:
        if i[0] >= 0:
            if i[1] > quadrant1[1]:
                quadrant1 = i[0:2]
            elif i[1] < quadrant2[1]:
                quadrant2 = i[0:2]
        else:
            if i[1] < quadrant3[1]:
                quadrant3 = i[0:2]
            elif i[1] > quadrant4[1]:
                quadrant4 = i[0:2]

    try:
        axis1 = np.linalg.norm(quadrant1-quadrant3)
    except:
        axis1 = 0
    try:
        axis2 = np.linalg.norm(quadrant2-quadrant4)
    except:
        axis2 = 0

    if axis1 >= axis2:
        majorAxis = np.array(quadrant1)-np.array(quadrant3)
    else:
        majorAxis = np.array(quadrant2)-np.array(quadrant4)

    theta = np.arctan(majorAxis[1]/majorAxis[0])#rotates the grid in line with the longest axis
    rotation = [[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]
    reverseRotation = [[np.cos(-theta),-np.sin(-theta)],[np.sin(-theta),np.cos(-theta)]]
    rotatedVertices = [np.matmul(reverseRotation,x[0:2]) for x in vertexProjection]

    minX = precisionRounding(min([x[0] for x in rotatedVertices])-spacing/2,spacing,'floor')
    maxX = precisionRounding(max([x[0] for x in rotatedVertices])+spacing/2,spacing,'ceil')
    minY = precisionRounding(min([x[1] for x in rotatedVertices])-spacing/2,spacing,'floor')
    maxY = precisionRounding(max([x[1] for x in rotatedVertices])+spacing/2,spacing,'ceil')

    #generates a hexagonal grid of points.
    points = [np.matmul(rotation,[minX,minY])]
    vertSpacing = 1/2 * spacing
    horizSpacing = np.sqrt(3)/2 * spacing
    xcoord = minX
    ycoord = minY
    alter = 0
    while ycoord < maxY:
        if alter == 0:
            xcoord = minX
            alter = 1
        else:
            xcoord = minX + horizSpacing
            alter = 0
        while xcoord < maxX:
            points.append(np.matmul(rotation,[xcoord,ycoord]))
            xcoord += 2 * horizSpacing
        ycoord += vertSpacing

    simPoints = len(points)
    simArea = (maxX-minX)*(maxY-minY)

    minX = precisionRounding(min([x[0] for x in vertexProjection])-spacing/2,spacing,'floor')
    maxX = precisionRounding(max([x[0] for x in vertexProjection])+spacing/2,spacing,'ceil')
    minY = precisionRounding(min([x[1] for x in vertexProjection])-spacing/2,spacing,'floor')
    maxY = precisionRounding(max([x[1] for x in vertexProjection])+spacing/2,spacing,'ceil')

    pointsOut = []

    for i in points:
        if i[0] <= maxX and i[0] >= minX and i[1] <= maxY and i[1] >= minY:
            pointsOut.append(i)
            
    return pointsOut, simArea, simPoints

def analyzeBoxes(boxes,offsets):
    verticesList = []
    edgesList = []
    edgePairsList = []
    counterOffset = 0
    for b in range(0,len(boxes)):
        box = boxes[b]
        offset = offsets[b]
        length = box[0]
        width = box[1]
        height = box[2]

        vertices = []
        for i in [-1,1]:
            for j in [-1,1]:
                for k in [-1,1]:
                    vertices.append([i*length/2+offset[0],j*width/2+offset[1],k*height/2+offset[2]])
        edges = []
        combinations = list(itertools.combinations(vertices,2))
        for i in combinations: #Oh, note that this only works if the box's edges are aligned with the axes. You'll need a more general method later.
            diffCount = 0
            if i[1][0]-i[0][0] != 0:
                diffCount += 1
            if i[1][1]-i[0][1] != 0:
                diffCount += 1
            if i[1][2]-i[0][2] != 0:
                diffCount += 1
            if diffCount == 1:
                edges.append([vertices.index(i[0])+counterOffset,vertices.index(i[1])+counterOffset])
        
        faces = [] #pick a combination of four vertices. all four must be equal in exactly one coordinate
        combinations = list(itertools.combinations(vertices,4))
        for i in combinations:
            sameCount = 0
            if i[0][0] == i[1][0] and i[1][0] == i[2][0] and i[2][0] == i[3][0]:
                sameCount += 1
            if i[0][1] == i[1][1] and i[1][1] == i[2][1] and i[2][1] == i[3][1]:
                sameCount += 1
            if i[0][2] == i[1][2] and i[1][2] == i[2][2] and i[2][2] == i[3][2]:
                sameCount += 1
            if sameCount == 1:
                faces.append([vertices.index(i[0])+counterOffset,vertices.index(i[1])+counterOffset,vertices.index(i[2])+counterOffset,vertices.index(i[3])+counterOffset])
        edgePairs = []
        for i in faces:
            combinations = list(itertools.combinations(i,2))
            faceEdges = []
            for j in combinations:
                if [x for x in j] in edges:
                    faceEdges.append([x for x in j])
            edgeCombs = list(itertools.combinations(faceEdges,2))
            facePair = []
            for k in edgeCombs:
                if not any(i in k[0] for i in k[1]):
                    facePair.append([k[0],k[1]])
            edgePairs.append(facePair)
        verticesList += vertices
        edgesList.append(edges)
        edgePairsList.append(edgePairs)
        counterOffset += len(vertices)

    return verticesList, edgePairsList, edgesList

def coords2BoxOffset(coords):
    boxes = []
    offsets = []
    for i in range(0,len(coords)):
        min = coords[i][1]
        max = coords[i][0]

        x = max[0]-min[0]
        y = max[1]-min[1]
        z = max[2]-min[2]

        boxes.append([x,y,z])

        center = [(max[0]+min[0])/2,(max[1]+min[1])/2,(max[2]+min[2])/2]

        if i == 0:
            offsets.append([0,0,0])
            relativeCenter = center
        else:
            offsets.append([center[x]-relativeCenter[x] for x in range(0,3)])
    
    print(boxes)
    print(offsets)
    return boxes, offsets

def main():
    startTime = datetime.now()

    # /// Sim Configuration ///
    boxes = [[7.25, 3.6, 12.75], [3.125, 3.6, 16.375], [3.125, 3.6, 16.375]]
    offsets = [[0, 0, 0], [5.1875, 0.0, 7.4375], [-5.1875, 0.0, 7.4375]]
    #boxes, offsets = coords2BoxOffset([[[3.625,2.05,3.15],[-3.625,-1.55,-9.6]],[[6.75,2.05,12.4],[3.625,-1.55,-3.975]],[[-3.625,2.05,12.4],[-6.75,-1.55,-3.975]]]) #use this function for converting from .lod box coordinates to this script's system
    boxColors = ['#ff9900','#0000ff','#ff00ff','#00ff99']
    showGraphs = True #Tends to be a lot faster when you turn off the graphing.
    precisionMultiplier = 1 #1 is default. Increasing precision raises time complexity significantly O(n^2)
    n = 250 #Number of views is this number times 2
    # /// Sim Configuration ///

    maxDim = max([max(x) for x in boxes])
    minDim = min([min(x) for x in boxes])
        
    areaList = []

    spherePoints = [] #generates a sphere made up of fibonacci spirals to provide roughly evenly-spaced points on its surface
    for p in range(-n,n):
        phi = np.arcsin(2*p/(2*n+1)) + np.pi/2
        theta = (2*np.pi*p*1/1.61803398875) #golden ratio
        x = np.cos(theta) * np.sin(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(phi)
        spherePoints.append([x, y, z])

    spherePoints += [[1,0,0],[0,1,0],[0,0,1]] #makes sure we capture all of the front/top/side views
    spherePoints = [list(x) for x in set(tuple(x) for x in spherePoints)]

    spherePoints.sort(key=operator.itemgetter(2))
    spherePoints.reverse()

    # ax = fig.add_subplot(projection='3d')
    # ax.scatter([x[0] for x in spherePoints],[x[1] for x in spherePoints],[x[2] for x in spherePoints])
    # plt.show()

    #spherePoints = [[1,1,1]] #Update this and turn graphing on to plot a single view. Comment to sim normally.

    counter = 0

    vertices, edgePairs, edgesList = analyzeBoxes(boxes,offsets)

    if showGraphs:
        fig = plt.figure(figsize=(24,12))
        ax = fig.add_subplot(1,2,1)
        ax.set_aspect('equal')
        ax2 = fig.add_subplot(1,2,2,projection='3d')
        displayVertices = []
        sphereDisplay = []

        observer = [0, 0, 1]
        zAxis = [0, -1 ,0]
        rotAxis = np.cross(observer,zAxis)
        rotAxis = rotAxis/np.linalg.norm(rotAxis)
        theta = np.arccos(np.dot(observer,zAxis))

        kMatrix = np.array([[0,-rotAxis[2],rotAxis[1]],[rotAxis[2],0,-rotAxis[0]],[-rotAxis[1],rotAxis[0],0]])
        identity = np.array([[1,0,0],[0,1,0],[0,0,1]])
        rMatrix = identity + kMatrix*np.sin(theta) + np.matmul(kMatrix,kMatrix)*(1-np.cos(theta))

        for i in vertices:
            rotatedProjection = np.matmul(rMatrix,i)
            displayVertices.append(rotatedProjection)
        for i in spherePoints:
            rotatedProjection = np.matmul(rMatrix,i)
            sphereDisplay.append(rotatedProjection)

    for observer in spherePoints:
        cycleStart = datetime.now()
        if showGraphs:
            ax.cla()
            ax2.cla()
            ax2.set_aspect('equal')
            ax2.set_xlim(-maxDim,maxDim)
            ax2.set_ylim(-maxDim,maxDim)
            ax2.set_zlim(-maxDim,maxDim)
            for b in edgesList:
                for e in b:
                    vertex1 = displayVertices[e[0]]
                    vertex2 = displayVertices[e[1]]
                    ax2.plot([vertex1[0],vertex2[0]],[vertex1[1],vertex2[1]],[vertex1[2],vertex2[2]],color=boxColors[edgesList.index(b)])
            ax2.scatter([x[0]*maxDim for x in sphereDisplay],[x[1]*maxDim for x in sphereDisplay],[x[2]*maxDim for x in sphereDisplay],color='#0000ff',s=2)
            observerHere = sphereDisplay[spherePoints.index(observer)]
            ax2.plot([observerHere[0]*maxDim,0],[observerHere[1]*maxDim,0],[observerHere[2]*maxDim,0],color='#ff0000')
        counter += 1

        observer = observer/np.linalg.norm(observer)

        pointCount = [[],[]]
            
        #okay so we have all our faces with pairs of parallel edges. Now we sweep through points. Check for each face if the point is between pair 1 lines and also between pair 2 lines. If so, it intersects the face and gets counted. Do this after getting the projected points though obv so it happens in 2d.
                
        #so now I have a list of point pairs representing the edges of the box. How do I check which side an arbitrary point is on?
        #well first I need a projection.

        zAxis = [0, 0, 1]
        if not all([observer[x] == zAxis[x] for x in range(0,3)]) and not all([observer[x] == -zAxis[x] for x in range(0,3)]):
            rotAxis = np.cross(observer,zAxis)
            rotAxis = rotAxis/np.linalg.norm(rotAxis)
            theta = np.arccos(np.dot(observer,zAxis))

            kMatrix = np.array([[0,-rotAxis[2],rotAxis[1]],[rotAxis[2],0,-rotAxis[0]],[-rotAxis[1],rotAxis[0],0]])
            identity = np.array([[1,0,0],[0,1,0],[0,0,1]])
            rMatrix = identity + kMatrix*np.sin(theta) + np.matmul(kMatrix,kMatrix)*(1-np.cos(theta))

            vertexProjection = []

            for i in vertices:
                rotatedProjection = np.matmul(rMatrix,i)
                vertexProjection.append(rotatedProjection)
            rotatedOffsets = []
            for offset in offsets:
                rotatedOffsets.append([offset[x] * np.cos(theta) for x in range(0,3)] + np.cross(rotAxis,offset) * np.sin(theta) + rotAxis * np.dot(rotAxis,offset)*(1-np.cos(theta)))
        else:
            vertexProjection = vertices
            rotatedOffsets = offsets

        #heres where we check surface intersection
        precision = min(maxDim/25,minDim/10)*1/precisionMultiplier

        points, simArea, simPoints = generatePointGrid(vertexProjection,precision)
        facechecks=0
        for edgePair in edgePairs:
            for face in edgePair:
                facechecks+= 1
                firstPair = [[vertexProjection[face[0][0][0]][0:2],vertexProjection[face[0][0][1]][0:2]],[vertexProjection[face[0][1][0]][0:2],vertexProjection[face[0][1][1]][0:2]]]
                secondPair = [[vertexProjection[face[1][0][0]][0:2],vertexProjection[face[1][0][1]][0:2]],[vertexProjection[face[1][1][0]][0:2],vertexProjection[face[1][1][1]][0:2]]]
                try:
                    firstPairLine1Slope = (firstPair[0][1][1] - firstPair[0][0][1]) / (firstPair[0][1][0] - firstPair[0][0][0])
                except:
                    firstPairLine1Slope = np.inf
                try:
                    firstPairLine2Slope = (firstPair[1][1][1] - firstPair[1][0][1]) / (firstPair[1][1][0] - firstPair[1][0][0])
                except:
                    firstPairLine2Slope = np.inf
                try:
                    secondPairLine1Slope = (secondPair[0][1][1] - secondPair[0][0][1]) / (secondPair[0][1][0] - secondPair[0][0][0])
                except:
                    secondPairLine1Slope = np.inf
                try:   
                    secondPairLine2Slope = (secondPair[1][1][1] - secondPair[1][0][1]) / (secondPair[1][1][0] - secondPair[1][0][0])
                except:
                    secondPairLine2Slope = np.inf
                for p in points:
                    x = p[0]
                    y = p[1]

                    firstPairLine1y = firstPairLine1Slope * (x - firstPair[0][0][0]) + firstPair[0][0][1]
                    firstPairLine2y = firstPairLine2Slope * (x - firstPair[1][0][0]) + firstPair[1][0][1]
                    secondPairLine1y = secondPairLine1Slope * (x - secondPair[0][0][0]) + secondPair[0][0][1]
                    secondPairLine2y = secondPairLine2Slope * (x - secondPair[1][0][0]) + secondPair[1][0][1]
                    check1 = False
                    check2 = False
                    if (firstPairLine1y > firstPairLine2y) and y <= firstPairLine1y and y >= firstPairLine2y:
                        check1 = True
                    elif firstPairLine1y <= firstPairLine2y and y <= firstPairLine2y and y >= firstPairLine1y:
                        check1 = True
                    if (secondPairLine1y > secondPairLine2y) and y <= secondPairLine1y and y >= secondPairLine2y:
                        check2 = True
                    elif secondPairLine1y <= secondPairLine2y and y <= secondPairLine2y and y >= secondPairLine1y:
                        check2 = True
                    if check1 and check2:
                        pointCount[0].append(x)
                        pointCount[1].append(y)

        pointCount = [tuple([round(pointCount[0][x],5),round(pointCount[1][x],5)]) for x in range(0,len(pointCount[0]))]
        uniquePoints = [list(x) for x in set(tuple(x) for x in pointCount)]
        area = len(uniquePoints)/simPoints * simArea
        areaList.append(area)
        if showGraphs:
            centerOfMass = [np.average([x[0] for x in rotatedOffsets]),np.average([x[1] for x in rotatedOffsets])]
            limit = max([max([abs(y) for y in x]) for x in vertexProjection])
            ax.set_xlim(centerOfMass[0]-limit,centerOfMass[0]+limit)
            ax.set_ylim(centerOfMass[1]-limit,centerOfMass[1]+limit)
            for edges in edgesList:
                edgeColor = boxColors[edgesList.index(edges)]
                offset = rotatedOffsets[edgesList.index(edges)]
                ax.scatter(offset[0],offset[1],color='#ff0000')
                for i in edges:
                    point1 = vertexProjection[i[0]]
                    point2 = vertexProjection[i[1]]
                    ax.plot([point1[0],point2[0]],[point1[1],point2[1]],color=edgeColor)
            ax.scatter([x[0] for x in points],[x[1] for x in points],color='#ff0000',s=1)
            ax.scatter([x[0] for x in uniquePoints],[x[1] for x in uniquePoints],color='#00ff00',s=1)
            plt.pause(0.1)
        cycleEnd = datetime.now()
        cycleLength = cycleEnd-cycleStart
        print(counter, observer, str(round(area,1)) + 'm²', str(round(cycleLength.total_seconds(),3)) + 's')
    simLength = datetime.now()-startTime
    print('Min: ', min(areaList), spherePoints[areaList.index(min(areaList))])
    print('Average: ', np.average(areaList))
    print('Max: ', max(areaList), spherePoints[areaList.index(max(areaList))])
    print('Simulation Time: ' + str(round(simLength.total_seconds(),3)) + 's')
    if showGraphs:
        plt.show()

main()