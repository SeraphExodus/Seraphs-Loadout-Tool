import matplotlib.pyplot as plt
import numpy as np
import operator

from datetime import datetime
from matplotlib import cm
from PIL import Image, ImageStat, ImageGrab

def get_clipboard():
	image = ImageGrab.grabclipboard()
	return image

def parseLines(image):
    image.show()
    image = np.array(image)
    image = np.flip(image,0)
    vertAvg = [np.average(image[x,:]) for x in range(0,image.shape[0])]
    lineHeight = 12
    lineStarts = []
    onLine = False
    for y in range(0,len(vertAvg)):
        if onLine:
            if y - lineStarts[-1] >= lineHeight:
                onLine = False
        if vertAvg[y] < max(vertAvg)-1 and not onLine: #threshold can't be 255 because of the vertical line on the side of many caps. You can *probably* get around this by using the max average minus some nominal value as a threshold.
            lineStarts.append(y)
            onLine = True
    lineEnds = [x+lineHeight for x in lineStarts]

    lines = []

    for i in range(0,len(lineStarts)):
        line = image[lineStarts[i]:lineEnds[i],:]
        horizStart = 0
        horizEnd = line.shape[1]
        for j in range(0,line.shape[1]-5): # get rough line start and end to remove artifacts
            chunkSum = np.sum(line[:,j:j+5])
            if chunkSum < 12000:
                horizStart = j
                break
        for j in range(line.shape[1],4,-1):
            chunkSum = np.sum(line[:,j-5:j])
            if chunkSum < 12000:
                horizEnd = j
                break
        line = line[:,horizStart:horizEnd]
        horizStart = 0
        horizEnd = line.shape[1]
        for j in range(0, line.shape[1]): #get exact line start and end
            chunkSum = np.average(line[:,j])
            if chunkSum < 255:
                horizStart = j
                break
        for j in range(line.shape[1],-1):
            chunkSum = np.average(line[:,j])
            if chunkSum < 255:
                horizEnd = j
                break
        line = line[:,horizStart:horizEnd-1]
        line = np.flip(line,0)
        line = Image.fromarray(line,mode='L')
        lines.append(line)

    return lines

def getCenterOfMass(array):
    if np.average(array) > 128:
        array = np.array([[255-x for x in y] for y in array])
    mass = np.sum(array)
    massX = 0
    massY = 0
    for x in range(0, array.shape[1]):
        massX += np.sum(array[:,x])*(x+1)
    for y in range(0, array.shape[0]):
        massY += np.sum(array[y,:])*(y+1)
    x = massX/mass
    y = massY/mass
    return x, y

def testSimilarity(sample, character):
    maxSize = sample.size
    matchCount = 0
    for x in range(0,len(sample[:,0])):
        for y in range(0,len(sample[0,:])):
            if sample[x,y] == character[x,y]:
                matchCount += 1
    print(matchCount/maxSize)
    return matchCount/maxSize

fontTex = Image.open("swgfont.jpg")
fn = lambda x : 255 if x > 128 else 0
fontTex = fontTex.convert('L').point(fn)
fontData = open("verdana_bold_12.inc",'r')
fontData = fontData.read()
fontCoords = [x for x in fontData.split('\n') if 'SourceRect=' in x]
fontCoords = [x.split("SourceRect='")[1].split("'")[0] for x in fontCoords]
fontUnicodes = [x for x in fontData.split('\n') if '\t\t\t\tName=' in x]
fontUnicodes = [x.split("Name='")[1].split("'")[0] for x in fontUnicodes]
fontCharacters = [chr(int(x,base=16)) for x in fontUnicodes]

left = []
top = []
right = []
bottom = []
for coord in fontCoords:
    coords = coord.split(',')
    left.append(int(coords[0]))
    top.append(int(coords[1]))
    right.append(int(coords[2]))
    bottom.append(int(coords[3]))

fontTex = np.array(fontTex)
charImages = []
charWidths = []
charCenter = []
for i in range(0,len(fontCoords)):
    charWidth = right[i]-left[i]
    charImage = fontTex[top[i]:bottom[i],left[i]:right[i]]
    charWidths.append(charWidth)
    charImages.append(charImage)

width = max(charWidths)

sortedCharImages = []
sortedCharWidths = []
sortedCharacters = []

while width > 0:
    for i in range(0,len(charImages)):
        image = charImages[i]
        imageWidth = charWidths[i]
        character = fontCharacters[i]
        if image.shape[1] == width:
            sortedCharImages.append(image)
            sortedCharWidths.append(imageWidth)
            sortedCharacters.append(character)
    width -= 1

#okay so we've got all the characters broken up into their own images. Now we need to take an input image and chop it down into lines and try to establish a character grid somehow. Then we compare each grid section to the list of character images to find the one that's most similar.
#gonna have to do something about centers of mass being fractional pixels. Maybe have a relative coordinate thing tracking alongside the array iteration when doing the comparison calc, like y = 0 but yrel = -center of mass. Still comparing discrete pixels though so that might not make sense.
#will dwell on this more.

start = datetime.now()
print('start:',start)

image = get_clipboard()
time1 = datetime.now()
print('get image from clipboard',time1-start)

thresholdShift = 1

thresh = np.average(ImageStat.Stat(image).mean[0:3])
thresh = (thresh+128*thresholdShift)/(1+thresholdShift)
if thresh < 128:
    fn = lambda x : 0 if x > thresh else 255
else:
    fn = lambda x : 255 if x > thresh else 0
image = image.convert('L').point(fn)
time2 = datetime.now()
print('convert to monochrome',time2-time1)

lines = parseLines(image)

lineText = []

for i in lines:
    lineImage = np.array(i)
    newLineText = ''
    mostSimilar = 0
    charIndex = 0
    while lineImage.shape[1] > 0:
        for j in range(0,len(sortedCharImages)):
            sample = lineImage[:,0:sortedCharWidths[j]]
            similarity = testSimilarity(sample,sortedCharImages[j])
            if similarity > mostSimilar:
                mostSimilar = similarity
                chop = sortedCharWidths[j]
                result = sortedCharacters[j]
        newLineText += result
        lineImage = lineImage[:,chop+1:]
    lineText.append(newLineText)
    print(newLineText)
        
