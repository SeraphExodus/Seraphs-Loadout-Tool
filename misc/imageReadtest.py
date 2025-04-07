import FreeSimpleGUI as sg
import numpy as np
import pytesseract
import win32clipboard

from datetime import datetime
from PIL import Image,ImageGrab,ImageStat,ImageEnhance,ImageFilter,ImageOps

def get_clipboard():
	image = ImageGrab.grabclipboard()
	return image

def toClipboard(data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(data, win32clipboard.CF_TEXT)
    win32clipboard.CloseClipboard()

def parseLines(image):
    image = np.array(image)
    xsum = np.sum(image,axis=1)
    maxValue = max(xsum) - 4 * 255 #(4 pixels of wiggle room)
    isLine = [False]
    lineStarts = []
    lineEnds = []
    for y in range(0,len(xsum)-1):
        if xsum[y] < maxValue:
            if isLine[-1] == False:
                lineStarts.append(y)
            isLine.append(True)
        else:
            if isLine[-1] == True:
                lineEnds.append(y)
            isLine.append(False)
    if len(lineStarts) < len(lineEnds):
        lineStarts = [0] + lineStarts
    elif len(lineEnds) < len(lineStarts):
        lineEnds.append([len(xsum)-1])
    lines = []
    for i in range(0,len(lineStarts)):
        if lineEnds[i] - lineStarts[i] >= 8:
            first = lineStarts[i]
            last = lineEnds[i]
            line = image[lineStarts[i]:lineEnds[i],:]

            leftCrop = 0
            rightCrop = line.shape[1]
            for i in range(10,line.shape[1]):
                if np.std(line[:,i]) > 50:
                    leftCrop = i-10
                    break
            for i in range(line.shape[1]-1,-1,-1):
                if np.std(line[:,i]) > 50:
                    rightCrop = i+10
                    break
            line = line[:,leftCrop:rightCrop]

            while last - first < 48:
                first -= 1
                last += 1
                pixelRow = np.array([255] * line.shape[1],dtype='uint8')
                line = np.vstack([pixelRow,line,pixelRow])

            newLine = Image.fromarray(line,mode='L')
            newLine = newLine.resize((newLine.size[0]*2,newLine.size[1]*2),Image.Resampling.LANCZOS)
            lines.append(newLine)
    return lines

def processImage(lineParse):
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
    
    image = image.resize((image.size[0]*2,image.size[1]*2),Image.Resampling.LANCZOS)
    time3 = datetime.now()
    print('scale and resample',time3-time2)



    pytesseract.pytesseract.tesseract_cmd= 'C:\\Program Files (x86)\\Tesseract-OCR\\distrotest\\tesseract.exe'

    tex = []

    if lineParse:

        lines = parseLines(image)
        time4 = datetime.now()
        print('parse and crop lines',time4-time3)

        for line in lines:
            tex.append(pytesseract.image_to_string(line,lang='eng',config='--psm 7').replace('\n',''))
        #tex = tex.replace('$','8').replace('¥','V').replace('\n\n','\n')
    else:
        tex = pytesseract.image_to_string(image,lang='eng')
        time4 = time3

    time5 = datetime.now()
    print('run tesseract',time5-time4)
    return(tex)

print(processImage(True))
