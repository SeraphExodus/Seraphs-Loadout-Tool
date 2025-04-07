import itertools
import matplotlib.pyplot as plt
import numpy as np

def precisionRounding(x,precision,dir):
    if dir == 'floor':
        return round((x-precision/2) * 1/precision,0) * precision
    elif dir == 'ceil':
        return round((x+precision/2) * 1/precision,0) * precision
    else:
        return round(x * 1/precision,0) * precision

def analyzeBoxes(boxes,offsets):
    verticesList = []
    edgesList = []
    edgePairsList = []
    counterOffset = 0
    for b in range(0,len(boxes)):
        box = boxes[b]
        offset = offsets[boxes.index(box)]
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

#start with 8 vertices dictated by center, lwh:
boxes = [[15.16,14.02,78.24],[45.04,7.91,54.7],[1.64,59.02,16.74]]
offsets = [[0,0,0],[0,0,-11.7],[0,0,-30.75]]
boxColors = ['#00ff00','#0000ff','#00ffff']

fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot()
ax.set_aspect('equal')

areaList = []

spherePoints = []
n = 250
for p in range(-n,n):
    phi = np.arcsin(2*p/(2*n+1)) + np.pi/2
    theta = (2*np.pi*p*1/1.61803398875) #golden ratio
    x = np.cos(theta) * np.sin(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(phi)
    spherePoints.append([x, y, z])

# ax = fig.add_subplot(projection='3d')
# ax.scatter([x[0] for x in spherePoints],[x[1] for x in spherePoints],[x[2] for x in spherePoints])
# plt.show()

spherePoints = [[0,0,1]]

counter = 0

vertices, edgePairs, edgesList = analyzeBoxes(boxes,offsets)


for observer in spherePoints:
    ax.cla()
    counter += 1

    observer = observer/np.linalg.norm(observer)

    pointCount = [[],[]]
        
    #okay so we have all our faces with pairs of parallel edges. Now we sweep through points. Check for each face if the point is between pair 1 lines and also between pair 2 lines. If so, it intersects the face and gets counted. Do this after getting the projected points though obv so it happens in 2d.
            
    #so now I have a list of point pairs representing the edges of the box. How do I check which side an arbitrary point is on?
    #well first I need a projection.

    zAxis = [0, 0, 1]
    rotAxis = np.cross(observer,zAxis)
    theta = np.arccos(np.dot(observer,zAxis))

    kMatrix = np.array([[0,-rotAxis[2],rotAxis[1]],[rotAxis[2],0,-rotAxis[0]],[-rotAxis[1],rotAxis[0],0]])
    identity = np.array([[1,0,0],[0,1,0],[0,0,1]])
    rMatrix = identity + kMatrix*np.sin(theta) + np.matmul(kMatrix,kMatrix)*(1-np.cos(theta))

    vertexProjection = []
    distances = []

    for i in vertices:
        obsVector = [observer[x] - i[x] for x in range(0,3)]
        distances.append(np.linalg.norm(obsVector))
        #rotatedProjection = [i[x] * np.cos(theta) for x in range(0,3)] + np.cross(rotAxis,i) * np.sin(theta) + rotAxis * np.dot(rotAxis,i)*(1-np.cos(theta)) #Rodrigues' rotation formula
        rotatedProjection = np.matmul(rMatrix,i)
        vertexProjection.append(rotatedProjection)
    rotatedOffsets = []
    for offset in offsets:
        rotatedOffsets.append([offset[x] * np.cos(theta) for x in range(0,3)] + np.cross(rotAxis,offset) * np.sin(theta) + rotAxis * np.dot(rotAxis,offset)*(1-np.cos(theta)))
    relDist = [x/max(distances) for x in distances]

    #heres where we check surface intersection
    precision = max([max(x) for x in boxes])/500
    
    for edgePair in edgePairs: #now how do we check if a point is between two arbitrary lines in r2? First represent the line as an equation, then compare to see if the point is above or below using inequalities. May need to apply absval depending on which side of the centerpoint the line is on
        for face in edgePair: #okay we need to invert this loop. It should cycle through random points and then go through each face and check for intersection.
            firstPair = [[vertexProjection[face[0][0][0]][0:2],vertexProjection[face[0][0][1]][0:2]],[vertexProjection[face[0][1][0]][0:2],vertexProjection[face[0][1][1]][0:2]]]
            secondPair = [[vertexProjection[face[1][0][0]][0:2],vertexProjection[face[1][0][1]][0:2]],[vertexProjection[face[1][1][0]][0:2],vertexProjection[face[1][1][1]][0:2]]]
            firstPairLine1Slope = (firstPair[0][1][1] - firstPair[0][0][1]) / (firstPair[0][1][0] - firstPair[0][0][0])
            firstPairLine2Slope = (firstPair[1][1][1] - firstPair[1][0][1]) / (firstPair[1][1][0] - firstPair[1][0][0])
            secondPairLine1Slope = (secondPair[0][1][1] - secondPair[0][0][1]) / (secondPair[0][1][0] - secondPair[0][0][0])
            secondPairLine2Slope = (secondPair[1][1][1] - secondPair[1][0][1]) / (secondPair[1][1][0] - secondPair[1][0][0])
            lowestX = precisionRounding(min([firstPair[0][0][0],firstPair[0][1][0],firstPair[1][0][0],firstPair[1][1][0],secondPair[0][0][0],secondPair[0][1][0],secondPair[1][0][0],secondPair[1][1][0]]),precision,'floor')
            highestX = precisionRounding(max([firstPair[0][0][0],firstPair[0][1][0],firstPair[1][0][0],firstPair[1][1][0],secondPair[0][0][0],secondPair[0][1][0],secondPair[1][0][0],secondPair[1][1][0]]),precision,'ceil')
            lowestY = precisionRounding(min([firstPair[0][0][1],firstPair[0][1][1],firstPair[1][0][1],firstPair[1][1][1],secondPair[0][0][1],secondPair[0][1][1],secondPair[1][0][1],secondPair[1][1][1]]),precision,'floor')
            highestY = precisionRounding(max([firstPair[0][0][1],firstPair[0][1][1],firstPair[1][0][1],firstPair[1][1][1],secondPair[0][0][1],secondPair[0][1][1],secondPair[1][0][1],secondPair[1][1][1]]),precision,'ceil')
            for x in np.arange(lowestX,highestX+precision,precision):
                for y in np.arange(lowestY,highestY+precision,precision):

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

    #I need to also rotate the view frame to align with the observer's viewing angle or some shit. Break out ye olde rotation matrix
    #if you want to show the points as they'd appear in the x-y plane, you have to rotate until the observer vector aligns with the z-axis

    limit = max(max(boxes))
    ax.set_xlim(-limit,limit)
    ax.set_ylim(-limit,limit)
    for edges in edgesList:
        edgeColor = boxColors[edgesList.index(edges)]
        offset = rotatedOffsets[edgesList.index(edges)]
        ax.scatter(offset[0],offset[1],color='#ff0000')
        for i in edges:
            point1 = vertexProjection[i[0]]
            point2 = vertexProjection[i[1]]
            ax.plot([point1[0],point2[0]],[point1[1],point2[1]],color=edgeColor)

        #okay so we need to sweep through points in x and y and figure out which ones are on each face. Faces will be determined by four PROJECTED vertices.
        #I also need to know which edges oppose one another to establish bounds.
    pointCount = [[precisionRounding(pointCount[0][x],precision,''), precisionRounding(pointCount[1][x],precision,'')] for x in range(0,len(pointCount[0]))]
    uniquePoints = [list(x) for x in set(tuple(x) for x in pointCount)]
    area = len(uniquePoints)*(precision**2)
    areaList.append(area)
    ax.scatter([x[0] for x in uniquePoints],[x[1] for x in uniquePoints],color='#333333',s=1)
    print(counter, observer, area)
    plt.pause(0.07)
print('Min: ', min(areaList))
print('Average: ', np.average(areaList))
print('Max: ', max(areaList))
plt.show()