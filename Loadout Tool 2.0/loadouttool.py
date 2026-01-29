import ctypes
import FreeSimpleGUI as sg
import jellyfish
import multiprocessing
import multiprocessing.popen_spawn_win32 as forking
import numpy as np
import os
import pyglet
import pytesseract
import shutil
import sqlite3
import sys
import win32clipboard

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageGrab, ImageStat
from requests import get
from webbrowser import open as browserOpen
from win32gui import FindWindow, GetWindowRect

from buildCompList import buildComponentList
from fcCalcUtility import fcCalc
from importBackup import importBackupData
from lootLookupUtility import lootLookup
from reCalcUtility import reCalc

versionOverride = False #Set true to omit version checking for test releases. Set false for any actual release.

throttleProfileCaptureMode = False #Set to false for normal screencapping, true to only capture the throttle profile with wiki background color for updating wiki pages

### Extra code in order to enable multiprocessing support in pyinstaller ###

class _Popen(forking.Popen):
    def __init__(self, *args, **kw):
        if hasattr(sys, 'frozen'):
            # We have to set original _MEIPASS2 value from sys._MEIPASS
            # to get --onefile mode working.
            os.putenv('_MEIPASS2', sys._MEIPASS)
        try:
            super(_Popen, self).__init__(*args, **kw)
        finally:
            if hasattr(sys, 'frozen'):
                # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                # available. In those cases we cannot delete the variable
                # but only set it to the empty string. The bootloader
                # can handle this case.
                if hasattr(os, 'unsetenv'):
                    os.unsetenv('_MEIPASS2')
                else:
                    os.putenv('_MEIPASS2', '')

class Process(multiprocessing.Process):
    _Popen = _Popen

# # ...

# if __name__ == '__main__':
#     # On Windows calling this function is necessary.
#     multiprocessing.freeze_support()

#     # Use your new Process class instead of multiprocessing.Process

###Release Procedure:
###Update VERSION NUMBER FIRST in both this file and on the gist.
###Generate .exe
###Upload new version
###Update gist with new download link

currentVersion = "2.17.0"

versionURL = "https://gist.github.com/SeraphExodus/8ae0b6980e3780e8782847dbe76b0bf5/raw"

fontList = sg.Text.fonts_installed_list()

if "Roboto" not in fontList:
    pyglet.options['win32_gdi_font'] = True
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Black.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-BlackItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Bold.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-BoldItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Italic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Light.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-LightItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Medium.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-MediumItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Regular.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Thin.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-ThinItalic.ttf'))))

displayScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)/100

scaleFactor = 1

if scaleFactor == 1:
    fontFace = 'bold'
else:
    fontFace = ''

headerFont = ("Roboto", int(12*scaleFactor), fontFace)
summaryFont = ("Roboto", int(11*scaleFactor), fontFace)
summaryFontStats = ("Roboto", int(11*scaleFactor))
baseFont = ("Roboto", int(10*scaleFactor), fontFace)
baseFontStats = ("Roboto", int(10*scaleFactor), fontFace)
buttonFont = ("Roboto", int(13*scaleFactor), fontFace)
fontPadding = 0
elementPadding = int(4*scaleFactor)
bgColor = '#202225'
boxColor = '#313338'
textColor = '#f3f4f5'
compBoxWidth = int(215 * scaleFactor)
rightPaneWidth = int(250 * scaleFactor)
topRowHeight = int(160 * scaleFactor)
row1Height = int(210 * scaleFactor)
row2Height = int(240 * scaleFactor)
row3Height = int(240 * scaleFactor)

theme_definition = {'BACKGROUND': boxColor,
                    'TEXT': textColor,
                    'INPUT': bgColor,
                    'TEXT_INPUT': textColor,
                    'SCROLL': bgColor,
                    'BUTTON': ('#f3f4f5', '#202225'),
                    'PROGRESS': ('#01826B', '#D0D0D0'),
                    'BORDER': 1,
                    'SLIDER_DEPTH': 0,
                    'PROGRESS_DEPTH' : 0}

if throttleProfileCaptureMode:
    profileBGColor = '#f8f9fa'
    profileTextColor = bgColor
else:
    profileBGColor = boxColor
    profileTextColor = textColor

sg.theme_add_new('Discord_Dark', theme_definition)

sg.theme('Discord_Dark')

######################Tooltips#####################
fullCapDamageTooltip = """ Approximate damage dealt to a single target by holding 
 down the trigger until your capacitor runs dry. 

 This can vary slightly based on when you start firing 
 relative to the next server recharge tick. """
fireTimeTooltip = """ Approximate time you will be able to hold down the trigger 
 before a shot fails from your capacitor running dry. 

 This can vary slightly based on when you start firing 
 relative to the next server recharge tick. """
capRechargeTimeTooltip = """ Time required to fully recharge your capacitor from zero. """
firingRatioTooltip = """ Starting from an empty capacitor and holding down the trigger, 
 this percentage of your shots would have enough energy to fire 
 successfully. 
 
 Given by the ratio of Fire Time to the sum of Fire Time and 
 Cap Recharge Time. """
speedModTooltip = """ A chassis-specific stat that determines the top speed of the ship 
 relative to the engine top speed. If your ship has s-foils that 
 modify the speed mod, that number is shown in parentheses. """
chassisADTooltip = """ A chassis-specific stat that determines the rate that your ship 
 is able to accelerate and decelerate its speed. 
 
 These numbers are improved with engine overload, and have a 
 significant effect on turning by dictating the rate at which 
 you can reach a more turning-friendly throttle percentage. 
 (See throttle profile below) """
chassisPYRTooltip = """  Chassis-specific stats that determine the responsiveness of 
 your ship to attempted changes in chassis orientation. These 
 numbers are improved with engine overload. """
chassisSlideModTooltip = """ A chassis-specific stat that affects your ship's ability to 
 maintain 'traction' as it moves through space. 
 
 Higher slide mods allow you to maintain tighter turns without 
 losing speed, while lower slide mods will often cause you to 
 decelerate significantly if you attempt to turn too sharply. """
topSpeedTooltip = """ In-game displayed ship top speed. If you have s-foils open, 
 the number displayed in parentheses is the number you will 
 see on-screen. 

 These numbers may vary by ±1 point compared to in-game due 
 to hidden decimals in your engine's top speed. """
boostedTSTooltip = """ In-game displayed ship top speed while using your booster. 
 If you have s-foils open, the number displayed in parentheses 
 is the number you will see on-screen. 

 These numbers may vary by ±1 point compared to in-game due to 
 hidden decimals in your engine and booster's top speeds. """
boostDistTooltip = """ Approximate maximum distance of travel when the booster is 
 activated with full energy and left on until it is depleted. """
boosterUptimeTooltip = """ Booster Burn Time / Booster Recharge Time (Booster Uptime Percentage): 

 Booster burn time is the maximum duration your booster will run 
 starting with full energy. 

 Booster recharge time is the amount of time it will take to return to 
 full energy from zero energy. 

 Booster uptime percentage is the greatest percentage of time possible 
 that your booster can be active, given by the ratio: 
 Uptime / (Uptime + Recharge Time)  """
dpShotTooltip = """ Damage numbers are given as approximate average damage per shot. 

 This is calculated by taking a weighted average of damage vs shields,  
 armor, chassis, and components using the formula:  
 (Max Damage + Min Damage)/2 * (2*VsS + 2*VsS*VsA + 1)/5 """
######################Tooltips#####################

#Debug Util
def pause():
    alert('Pause',['Paused'],['Continue'],0)

def remodalize(window):
    try:
        window.TKroot.grab_set()
    except:
        pass

def move_center(window):
    screen_width, screen_height = window.get_screen_dimensions()
    win_width, win_height = window.size
    screen_height -= 100
    x, y = (screen_width - win_width)//2, (screen_height - win_height)//2
    window.move(x, y)

def toClipboard(type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(type, data)
    win32clipboard.CloseClipboard()

def getImageFromClipboard():
    image = ImageGrab.grabclipboard()
    return image

def parseLines(image):
    image = np.array(image)
    xsum = np.sum(image,axis=1)
    maxValue = max(xsum) - 4 * 255 #(4 pixels of wiggle room) - Identifies the 'blankest' row and uses that as a basis for identifying what isn't part of a text line
    isLine = [False]
    lineStarts = []
    lineEnds = []
    for y in range(0,len(xsum)-1): #Scans every row of pixels along the y-axis
        if xsum[y] < maxValue:
            if isLine[-1] == False:
                lineStarts.append(y) #If the row of pixels has more black than the blank row prototype, and the previous row wasn't part of a line, mark this row as the beginning of a text line
            isLine.append(True)
        else:
            if isLine[-1] == True:
                lineEnds.append(y) #vice versa, if the row of pixels is identified as a blank line, and the previous row was part of a text line, mark this row as the end of a text line
            isLine.append(False)
    if len(lineStarts) < len(lineEnds):
        lineStarts = [0] + lineStarts
    elif len(lineEnds) < len(lineStarts):
        lineEnds.append([len(xsum)-1]) #the number of starts and ends can differ if the top or bottom of an image slices through a text line. This just pads the starting point/ending point lists to make the count match.
    lines = []
    for i in range(0,len(lineStarts)):
        if lineEnds[i] - lineStarts[i] >= 8: #checks if the identified text line is at least 8 pixels vertically. This is the height of the game text, and we can exclude and 'lines' that are narrower as not being text.
            first = lineStarts[i]
            last = lineEnds[i]
            line = image[lineStarts[i]:lineEnds[i],:] #Crops the image vertically to isolate the text line

            leftCrop = 0
            rightCrop = line.shape[1]
            for i in range(10,line.shape[1]): #starting 10 pixels from the left side of the line, scan the vertical columns of pixels left-to-right until you find one with a standard deviation greater than 50 (indicator of text being present) then crop the image 10 pixels to the left of that point.
                if np.std(line[:,i]) > 50:
                    leftCrop = i-10
                    break
            for i in range(line.shape[1]-1,-1,-1): #same process, except starting from the right and working left.
                if np.std(line[:,i]) > 50:
                    rightCrop = i+10
                    break
            line = line[:,leftCrop:rightCrop]

            while last - first < 48: #Pad each line on the top and bottom with rows of white pixels to improve ocr readability
                first -= 1
                last += 1
                pixelRow = np.array([255] * line.shape[1],dtype='uint8')
                line = np.vstack([pixelRow,line,pixelRow])

            newLine = Image.fromarray(line,mode='L')
            #newLine = newLine.resize((newLine.size[0]*1,newLine.size[1]*1),Image.Resampling.LANCZOS)
            lines.append(newLine)
    return lines

def processImage():

    # start = datetime.now()
    # print('start:',start)

    image = getImageFromClipboard()
    # time1 = datetime.now()
    # print('get image from clipboard',time1-start)

    thresholdShift = 1
    thresh = np.average(ImageStat.Stat(image).mean[0:3])
    thresh = (thresh+128*thresholdShift)/(1+thresholdShift)

    if thresh < 128:
        fn = lambda x : 0 if x > thresh else 255
    else:
        fn = lambda x : 255 if x > thresh else 0
    image = image.convert('L').point(fn) #Grayscale the image, making text black and background white.
    # time2 = datetime.now()
    # print('convert to monochrome',time2-time1)
    scale = 3
    
    image = image.resize((int(image.size[0]*scale),int(image.size[1]*scale)),Image.Resampling.LANCZOS)
    # image.show()
    # time3 = datetime.now()
    # print('scale and resample',time3-time2)

    pytesseract.pytesseract.tesseract_cmd= os.path.abspath(os.path.join(os.path.dirname(__file__), 'tesseract\\tesseract.exe'))

    lines = parseLines(image)

    textList = []

    for line in lines: #Runs tesseract on each text line individually and replaces common error characters.
        tex = pytesseract.image_to_string(line,lang='eng',config='--psm 7').replace('\n','')
        tex = tex.replace('$','8').replace('¥','V').replace('\n\n','\n')
        textList.append(tex)

    #print([x for x in textList])

    # time4 = datetime.now()
    # print('run tesseract',time4-time3)
        
    return(textList)

def tryFloat(x):
    try:
        y = float(x)
        return y
    except:
        return 0

def tryFloatRetainPrecision(x):
    try:
        y = float(x)
        return x
    except:
        return ''

def tryInt(x):
    try:
        if x % 1 == 0 and x >= 10:
            return int(x)
        else:
            return x
    except:
        return x

def listify(x):
    xnew = []
    for i in x:
        xnew.append(i[0])
    return xnew

def displayPrecision(stats, decimals, *shift):

    if shift:
        output = []
        index = 0
    else:
        output = [stats[0]]
        index = 1

    for i in range(index, len(stats)):
        output.append(round(tryFloat(stats[i]), decimals[i-index]))

    return output

def getThreeColorGradient(per):
    if per < 50:
        red = str(hex(int((per*2)/100 * (255-221) + 221))).split('x')[1]
        if len(red) < 2:
            red = '0' + red
        green = str(hex(int((per*2)/100 * 204))).split('x')[1]
        if len(green) < 2:
            green = '0' + green
        color = '#' + red + green + '00'
    else:
        red = str(hex(int((1 - ((per-50)*2)/100) * 255))).split('x')[1]
        if len(red) < 2:
            red = '0' + red
        color = '#' + red + 'cc00'
    return color

def ceil(x):
    try:
        y = round(x+0.5)
        return y
    except:
        SyntaxError

def alert(headerText, textLines, buttons, timeout, *settings):
    Layout = []

    try:
        textSettings = settings[0]
        dimensions = settings[1]
    except:
        textSettings = []
        dimensions = []

    if len(textLines) > 0:
        for i in range(0,len(textLines)):
            try:
                textFont = textSettings[0][i]
            except:
                textFont = summaryFont
            try:
                textJust = textSettings[0][i]
            except:
                textJust = 'center'
            
            Line = sg.Text(textLines[i],font=textFont, p=fontPadding)
            if textJust == 'left':
                Layout.append([Line,sg.Push()])
            elif textJust == 'right':
                Layout.append([sg.Push(),Line])
            else:
                Layout.append([sg.Push(),Line,sg.Push()])

    if len(dimensions) == 2 and 0 not in dimensions:
        Layout = [
            [sg.Frame('',[[sg.VPush()],Layout[0],[sg.VPush()]],size=(dimensions[0],dimensions[1]),border_width=0)]
        ]

    buttonList = [sg.Push(),sg.Push()]
    if len(buttons) > 0:
        for i in buttons:
            buttonList.append(sg.Button(i,font=buttonFont, button_color=bgColor))
            buttonList.append(sg.Push())
        buttonList.append(sg.Push())
        Layout.append(buttonList)

    alertWindow = sg.Window(headerText,Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), )

    if timeout > 0:
        startTime = datetime.now()
        currTime = startTime
        while currTime < startTime + timedelta(seconds=timeout):
            event, values = alertWindow.read(timeout=10)
            if event in buttons or event == sg.WIN_CLOSED:
                alertWindow.close()
                return event
            currTime = datetime.now()
        alertWindow.close()
        return
    
    while True:
        event, values = alertWindow.read()
        if event in buttons or event == sg.WIN_CLOSED:
            alertWindow.close()
            return event

def popImage(header, filename):
    Layout = [
        [sg.Image(filename)]
    ]

    imageWindow = sg.Window(header,Layout,modal=False,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), )

    while True:
        event, values = imageWindow.read()

        if event == sg.WIN_CLOSED:
            imageWindow.close()
            break

def updateParts(*arg):
    #If you pass a chassis in, it updates the dynamic slot lists too. Otherwise it just updates the part lists

    reactorList = ["None"] + listify(cur2.execute("SELECT name FROM reactor").fetchall())
    engineList = ["None"] + listify(cur2.execute("SELECT name FROM engine").fetchall())
    boosterList = ["None"] + listify(cur2.execute("SELECT name FROM booster").fetchall())
    shieldList = ["None"] + listify(cur2.execute("SELECT name FROM shield").fetchall())
    armorList = ["None"] + listify(cur2.execute("SELECT name FROM armor").fetchall())
    diList = ["None"] + listify(cur2.execute("SELECT name FROM droidinterface").fetchall())
    chList = ["None"] + listify(cur2.execute("SELECT name FROM cargohold").fetchall())
    capList = ["None"] + listify(cur2.execute("SELECT name FROM capacitor").fetchall())
    weaponList = listify(cur2.execute("SELECT name FROM weapon").fetchall())
    ordList = listify(cur2.execute("SELECT name FROM ordnancelauncher").fetchall())
    cmList = listify(cur2.execute("SELECT name FROM countermeasurelauncher").fetchall())

    slotLists = []

    try:
        chassis = arg[0]
        slots = []
        for i in range(1, 9):
            slots.append(cur.execute("SELECT slot" + str(i) + " FROM chassis WHERE name = ?", [chassis]).fetchall()[0][0])
        for i in range(0, 8):
            holderList = []
            if "Weapon" in slots[i]:
                holderList += weaponList
            if "Countermeasure" in slots[i] or "/ CM" in slots[i]:
                holderList += cmList
            if "Ordnance" in slots[i]:
                holderList += ordList
            slotLists.append(list(holderList))
    except:
        slotLists = [list(),list(),list(),list(),list(),list(),list(),list()]

    slot1List = ["None"] + slotLists[0]
    slot2List = ["None"] + slotLists[1]
    slot3List = ["None"] + slotLists[2]
    slot4List = ["None"] + slotLists[3]
    slot5List = ["None"] + slotLists[4]
    slot6List = ["None"] + slotLists[5]
    slot7List = ["None"] + slotLists[6]
    slot8List = ["None"] + slotLists[7]

    return [reactorList, engineList, boosterList, shieldList, armorList, diList, chList, capList, slot1List, slot2List, slot3List, slot4List, slot5List, slot6List, slot7List, slot8List]

def verifyEntries(window):

    chassis = window['chassistype'].get()

    if not chassis == '':
        headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])
    else:
        headers = [''] * 8

    events, values = window.read(timeout=0)

    slots = ['reactorselection', 'engineselection', 'boosterselection', 'shieldselection', 'frontarmorselection', 'reararmorselection', 'diselection', 'chselection', 'capselection', 'slot1selection', 'slot2selection', 'slot3selection', 'slot4selection', 'slot5selection', 'slot6selection', 'slot7selection', 'slot8selection', 'slot1packselection', 'slot2packselection', 'slot3packselection', 'slot4packselection', 'slot5packselection', 'slot6packselection', 'slot7packselection', 'slot8packselection']
    
    entries = []
    for i in slots:
        entries.append(values[i])

    reactorList = ["None"] + listify(cur2.execute("SELECT name FROM reactor").fetchall())
    engineList = ["None"] + listify(cur2.execute("SELECT name FROM engine").fetchall())
    boosterList = ["None"] + listify(cur2.execute("SELECT name FROM booster").fetchall())
    shieldList = ["None"] + listify(cur2.execute("SELECT name FROM shield").fetchall())
    armorList = ["None"] + listify(cur2.execute("SELECT name FROM armor").fetchall())
    diList = ["None"] + listify(cur2.execute("SELECT name FROM droidinterface").fetchall())
    chList = ["None"] + listify(cur2.execute("SELECT name FROM cargohold").fetchall())
    capList = ["None"] + listify(cur2.execute("SELECT name FROM capacitor").fetchall())
    weaponList = ["None"] + listify(cur2.execute("SELECT name FROM weapon").fetchall())
    ordList = ["None"] + listify(cur2.execute("SELECT name FROM ordnancelauncher").fetchall())
    cmList = ["None"] + listify(cur2.execute("SELECT name FROM countermeasurelauncher").fetchall())
    ordPackList = ["None"] + listify(cur2.execute("SELECT name FROM ordnancepack").fetchall())
    cmPackList = ["None"] + listify(cur2.execute("SELECT name FROM countermeasurepack").fetchall())

    nonSlotLists = [reactorList, engineList, boosterList, shieldList, armorList, armorList, diList, chList, capList]

    weaponCMList = weaponList + cmList

    for i in range(0, 9):
        if not entries[i] in nonSlotLists[i]:
            window[slots[i]].update(value = '', size=(28,10))

    for i in range(9, 17):
        if "Weapon / CM" in headers[i-9]:
            if not entries[i+8] in cmPackList:
                if entries[i] in cmList:
                    window[slots[i+8]].update(value='', visible=True, size=(28,10))
                else:
                    window[slots[i+8]].update(value='', visible=False, size=(28,10))
            if not entries[i] in weaponCMList:
                window[slots[i]].update(value='', size=(28,10))
                window[slots[i+8]].update(value='', visible=False, size=(28,10))
        elif "Weapon" in headers[i-9]:
            if not entries[i] in weaponList:
                window[slots[i]].update(value='', size=(28,10))
        elif "Countermeasure" in headers[i-9]:
            if not entries[i+8] in cmPackList:
                if entries[i] in cmList:
                    window[slots[i+8]].update(value='', visible=True, size=(28,10))
                else:
                    window[slots[i+8]].update(value='', visible=False, size=(28,10))
            if not entries[i] in cmList:
                window[slots[i]].update(value='', size=(28,10))
                window[slots[i+8]].update(value='', visible=False, size=(28,10))
        elif "Ordnance" in headers[i-9]:
            if not entries[i+8] in ordPackList:
                if entries[i] in ordList:
                    window[slots[i+8]].update(value='', visible=True, size=(28,10))
                else:
                    window[slots[i+8]].update(value='', visible=False, size=(28,10))
            if not entries[i] in ordList:
                window[slots[i]].update(value='', size=(28,10))
                window[slots[i+8]].update(value='', visible=False, size=(28,10))
    window.refresh()

    events, values = window.read(timeout=0)

    refreshReactor(window, values[slots[0]])
    refreshEngine(window, values[slots[1]])
    refreshBooster(window, values[slots[2]])
    refreshShield(window, values[slots[3]], values['shieldadjustsetting'])
    refreshFrontArmor(window, values[slots[4]])
    refreshRearArmor(window, values[slots[5]])
    refreshDI(window, values[slots[6]])
    refreshCH(window, values[slots[7]])
    refreshCapacitor(window, values[slots[8]])
    compType1 = refreshSlot(window, values[slots[9]], 1)
    compType2 = refreshSlot(window, values[slots[10]], 2)
    compType3 = refreshSlot(window, values[slots[11]], 3)
    compType4 = refreshSlot(window, values[slots[12]], 4)
    compType5 = refreshSlot(window, values[slots[13]], 5)
    compType6 = refreshSlot(window, values[slots[14]], 6)
    compType7 = refreshSlot(window, values[slots[15]], 7)
    compType8 = refreshSlot(window, values[slots[16]], 8)
    refreshPack(window, values[slots[17]], 1, compType1)
    refreshPack(window, values[slots[18]], 2, compType2)
    refreshPack(window, values[slots[19]], 3, compType3)
    refreshPack(window, values[slots[20]], 4, compType4)
    refreshPack(window, values[slots[21]], 5, compType5)
    refreshPack(window, values[slots[22]], 6, compType6)
    refreshPack(window, values[slots[23]], 7, compType7)
    refreshPack(window, values[slots[24]], 8, compType8)

def updateMassStrings(chassisMass, window):
    totalMass = str(round(tryFloat(window['reactormass'].get()) + tryFloat(window['enginemass'].get()) + tryFloat(window['boostermass'].get()) + tryFloat(window['shieldmass'].get()) + tryFloat(window['frontarmormass'].get()) + tryFloat(window['reararmormass'].get()) + tryFloat(window['dimass'].get()) + tryFloat(window['chmass'].get()) + tryFloat(window['capacitormass'].get()) + tryFloat(window['slot1stat2'].get()) + tryFloat(window['slot2stat2'].get()) + tryFloat(window['slot3stat2'].get()) + tryFloat(window['slot4stat2'].get()) + tryFloat(window['slot5stat2'].get()) + tryFloat(window['slot6stat2'].get()) + tryFloat(window['slot7stat2'].get()) + tryFloat(window['slot8stat2'].get()),1))
    try:
        if float(chassisMass) > 0:
            percentMass = round(tryFloat(totalMass)/tryFloat(chassisMass)*100,1)
            massString = str(totalMass) + " of " + str(round(float(chassisMass),1)) + " (" + str(percentMass) + "%)"
            leftoverMass = str(round(float(chassisMass) - float(totalMass),1))
            if tryFloat(totalMass)/tryFloat(chassisMass) > 1:
                window['loadoutmass'].update(massString, text_color = "#dd0000")
            else:
                window['loadoutmass'].update(massString, text_color = textColor)
            window['massremaining'].update(leftoverMass)
        else:
            window['loadoutmass'].update("", text_color = textColor)
            window['massremaining'].update("")
    except:
        window['loadoutmass'].update("", text_color = textColor)
        window['massremaining'].update("")

def getTotalSlotDrain(values, woEff):
    selections = [values['slot1selection'], values['slot2selection'], values['slot3selection'], values['slot4selection'], values['slot5selection'], values['slot6selection'], values['slot7selection'], values['slot8selection']]
    compTypes = []
    drains = []
    for selection in selections:
        [compType, stats] = getSlotStats(selection)
        compTypes.append(compType)
        drains.append(stats[0])

    compTypes.reverse()

    cmIndex = 0

    for i in range(0, len(compTypes)):
        if compTypes[i] == "Countermeasure":
            cmIndex = 7 - i
            break
        if compTypes[i] != "Null":
            cmIndex = 0
            break
    compTypes.reverse()

    drain = []

    for i in range(0, len(compTypes)):
        drain.append(tryFloat(drains[i]) / woEff)

    return drain, cmIndex
        
def updateDrainStrings(window):
    event, values = window.read(timeout=0)

    roLevel = values['reactoroverloadlevel']
    eoLevel = values['engineoverloadlevel']
    coLevel = values['capacitoroverchargelevel']
    woLevel = values['weaponoverloadlevel']

    overloads = cur.execute("SELECT name,energyefficiency,genefficiency FROM fcprogram").fetchall()[0:16]

    if roLevel == "None":
        roEff = 1
    else:
        roEff = tryFloat(overloads[roLevel-1][2])

    if eoLevel == "None":
        eoEff = 1
    else:
        eoEff = tryFloat(overloads[eoLevel+3][1])
    
    if coLevel == "None":
        coEff = 1
    else:    
        coEff = tryFloat(overloads[coLevel+7][1])

    if woLevel == "None":
        woEff = 1
    else:
        woEff = tryFloat(overloads[woLevel+11][1])

    poweredComponents = [values['engineselection'], values['shieldselection'], values['capselection'], values['boosterselection'], values['diselection'], values['slot1selection'], values['slot2selection'], values['slot3selection'], values['slot4selection'], values['slot5selection'], values['slot6selection'], values['slot7selection'], values['slot8selection']]
    overloadedGen = round(tryFloat(window['reactorgen'].get()) * roEff, 1)
    slotDrains, cmIndex = getTotalSlotDrain(values, woEff)
    drains = [tryFloat(window['enginered'].get()) / eoEff, tryFloat(window['shieldred'].get()), tryFloat(window['capacitorred'].get()) / coEff, tryFloat(window['boosterred'].get()), tryFloat(window['dired'].get())] + slotDrains
    boxKeys = ['enginepowerboxcolor', 'shieldpowerboxcolor', 'cappowerboxcolor', 'boosterpowerboxcolor', 'dipowerboxcolor', 'slot1powerboxcolor', 'slot2powerboxcolor', 'slot3powerboxcolor', 'slot4powerboxcolor', 'slot5powerboxcolor', 'slot6powerboxcolor', 'slot7powerboxcolor', 'slot8powerboxcolor']
    frameKeys = ['enginepowerboxframecolor', 'shieldpowerboxframecolor', 'cappowerboxframecolor', 'boosterpowerboxframecolor', 'dipowerboxframecolor', 'slot1powerboxframecolor', 'slot2powerboxframecolor', 'slot3powerboxframecolor', 'slot4powerboxframecolor', 'slot5powerboxframecolor', 'slot6powerboxframecolor', 'slot7powerboxframecolor', 'slot8powerboxframecolor']
    
    reactorDecrement = overloadedGen
    overloadedDrain = 0

    for i in range(0, len(poweredComponents)):
        if not poweredComponents[i] == "None" and not poweredComponents[i] == "":
            currentDrain = drains[i]
            if reactorDecrement <= 0:
                window[boxKeys[i]].update(background_color='#dd0000',text_color="#000000", font=("Roboto", 10))
                window[frameKeys[i]].Widget.config(background='#dd0000')
            elif currentDrain > reactorDecrement:
                if reactorDecrement < 0.1 * currentDrain:
                    window[boxKeys[i]].update(background_color='#dd0000',text_color="#000000", font=("Roboto", 10))
                    window[frameKeys[i]].Widget.config(background='#dd0000')
                elif i == cmIndex + 5 and cmIndex != 0 and reactorDecrement >= 0.1 * currentDrain:
                    window[boxKeys[i]].update(background_color='#00cc00',text_color="#000000", font=("Roboto", 10))
                    window[frameKeys[i]].Widget.config(background='#00cc00')
                else:
                    window[boxKeys[i]].update(background_color='#ffcc00',text_color="#000000", font=("Roboto", 10))
                    window[frameKeys[i]].Widget.config(background='#ffcc00')
            else:
                window[boxKeys[i]].update(background_color='#00cc00',text_color="#000000", font=("Roboto", 10))
                window[frameKeys[i]].Widget.config(background='#00cc00')

            if i == cmIndex + 5 and cmIndex != 0:
                overloadedDrain += currentDrain/10
                reactorDecrement -= currentDrain/10
            else:
                overloadedDrain += currentDrain
                reactorDecrement -= currentDrain
        else:
            currentDrain = 0
            window[boxKeys[i]].update(background_color=boxColor, text_color=boxColor)
            window[frameKeys[i]].Widget.config(background=boxColor)


    overloadedDrain = round(overloadedDrain,1)

    if not overloadedGen == 0 or not overloadedDrain == 0:
        reactorUtilString = str(overloadedDrain) + " of " + str(overloadedGen)
        if overloadedGen > 0:
            reactorUtilString+= " (" + str(round(tryFloat(overloadedDrain)/tryFloat(overloadedGen) * 100,1)) + "%)"
        reactorMinGenString = str(round(overloadedDrain / roEff, 1))
        if overloadedDrain > overloadedGen:
            window['totaldrain'].update(reactorUtilString, text_color='#dd0000')
        else:
            window['totaldrain'].update(reactorUtilString, text_color=textColor)
        window['minimumgen'].update(reactorMinGenString)
    else:
        window['totaldrain'].update("", text_color=textColor)
        window['minimumgen'].update("")
    window.refresh()

def updateDropdowns(lists, window, windowValues, disable, *headers):

    reactorList = lists[0]
    engineList = lists[1]
    boosterList = lists[2]
    shieldList = lists[3]
    armorList = lists[4]
    diList = lists[5]
    chList = lists[6]
    capList = lists[7]
    slot1List = lists[8]
    slot2List = lists[9]
    slot3List = lists[10]
    slot4List = lists[11]
    slot5List = lists[12]
    slot6List = lists[13]
    slot7List = lists[14]
    slot8List = lists[15]

    slotDisables = []
    try:
        for i in range(0, 8):
            if len(headers[0][i]) == 0 or disable:
                slotDisables.append(True)
            else:
                slotDisables.append(False)
    except:
        slotDisables = [disable] * 8

    window['reactorselection'].update(value = windowValues['reactorselection'], values = reactorList, size=(28,10), disabled=disable)
    window['engineselection'].update(value = windowValues['engineselection'], values = engineList, size=(28,10), disabled=disable)
    window['boosterselection'].update(value = windowValues['boosterselection'], values = boosterList, size=(28,10), disabled=disable)
    window['shieldselection'].update(value = windowValues['shieldselection'], values = shieldList, size=(28,10), disabled=disable)
    window['frontarmorselection'].update(value = windowValues['frontarmorselection'], values = armorList, size=(28,10), disabled=disable)
    window['reararmorselection'].update(value = windowValues['reararmorselection'], values = armorList, size=(28,10), disabled=disable)
    window['diselection'].update(value = windowValues['diselection'], values = diList, size=(28,10), disabled=disable)
    window['chselection'].update(value = windowValues['chselection'], values = chList, size=(28,10), disabled=disable)
    window['capselection'].update(value = windowValues['capselection'], values = capList, size=(28,10), disabled=disable)
    window['slot1selection'].update(value = windowValues['slot1selection'], values = slot1List, size=(28,10), disabled=slotDisables[0])
    window['slot2selection'].update(value = windowValues['slot2selection'], values = slot2List, size=(28,10), disabled=slotDisables[1])
    window['slot3selection'].update(value = windowValues['slot3selection'], values = slot3List, size=(28,10), disabled=slotDisables[2])
    window['slot4selection'].update(value = windowValues['slot4selection'], values = slot4List, size=(28,10), disabled=slotDisables[3])
    window['slot5selection'].update(value = windowValues['slot5selection'], values = slot5List, size=(28,10), disabled=slotDisables[4])
    window['slot6selection'].update(value = windowValues['slot6selection'], values = slot6List, size=(28,10), disabled=slotDisables[5])
    window['slot7selection'].update(value = windowValues['slot7selection'], values = slot7List, size=(28,10), disabled=slotDisables[6])
    window['slot8selection'].update(value = windowValues['slot8selection'], values = slot8List, size=(28,10), disabled=slotDisables[7])
    window['reactoroverloadlevel'].update(value = windowValues['reactoroverloadlevel'], size=(28,10), disabled=disable)
    window['engineoverloadlevel'].update(value = windowValues['engineoverloadlevel'], size=(28,10), disabled=disable)
    window['capacitoroverchargelevel'].update(value = windowValues['capacitoroverchargelevel'], size=(28,10), disabled=disable)
    window['weaponoverloadlevel'].update(value = windowValues['weaponoverloadlevel'], size=(28,10), disabled=disable)
    window['shieldadjustsetting'].update(value = windowValues['shieldadjustsetting'], size=(28,10), disabled=disable)
    window.refresh()

def updateSlotHeaders(chassis, window):

    headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])

    window['slot1header'].update(headers[0])
    window['slot2header'].update(headers[1])
    window['slot3header'].update(headers[2])
    window['slot4header'].update(headers[3])
    window['slot5header'].update(headers[4])
    window['slot6header'].update(headers[5])
    window['slot7header'].update(headers[6])
    window['slot8header'].update(headers[7])
    window.refresh()

    return headers

def updatePacks(window, component, slot, togglevis):

    event, values = window.read(timeout=0)
    [compType, stats] = getSlotStats(component)
    query = stats[2]

    packList = slot + 'packselection'
    try:
        preValue = values[packList]
    except:
        preValue = ""

    if compType == "Ordnance" or compType == "Ordnance Pack":
        slotPacks = ["None"] + listify(cur2.execute("SELECT name FROM ordnancepack WHERE type = ?", [query]).fetchall())
        if preValue not in slotPacks:
            preValue = ''
        if togglevis:
            window[packList].update(value = preValue, values = slotPacks, visible=True, size=(28,10))
        else:
            window[packList].update(value = preValue, values = slotPacks, size=(28,10))
    elif compType == "Countermeasure" or compType == "Countermeasure Pack":
        slotPacks = ["None"] + listify(cur2.execute("SELECT name FROM countermeasurepack").fetchall())
        if togglevis:
            window[packList].update(value = preValue, values = slotPacks, visible=True, size=(28,10))
        else:
            window[packList].update(value = preValue, values = slotPacks, size=(28,10))
    else:
        slotPacks = []
        window[packList].update(visible=False, size=(28,10))
        window.refresh()
    
    return slotPacks

def getSlotStats(selection):

    ###This method is vulnerable to non-uniquely-named weap/cm/ordnance. Need to solve this somehow.
    
    compType = "Null"

    try:
        stats = cur2.execute("SELECT * FROM weapon WHERE name = ?", [selection]).fetchall()[0]
        compType = "Weapon"
    except:
        try:
            stats = cur2.execute("SELECT * FROM countermeasurelauncher WHERE name = ?", [selection]).fetchall()[0]
            compType = "Countermeasure"
        except:
            try:
                stats = cur2.execute("SELECT * FROM ordnancelauncher WHERE name = ?", [selection]).fetchall()[0]
                compType = "Ordnance"
            except:
                pass
    
    output = []

    for i in range(1,9):
        try:
            output.append(stats[i])
        except:
            output.append("")

    return [compType, output]

def refreshReactor(window, component):

    if type(component) == str and not component == "None" and not component == "":
        reactor = cur2.execute("SELECT * FROM reactor WHERE name = ?", [component]).fetchall()[0]
        reactor = displayPrecision(reactor, [1, 1])
        window['reactormass'].update(reactor[1])
        window['reactorgen'].update(reactor[2])
    else:
        window['reactormass'].update("")
        window['reactorgen'].update("")
    
    window.refresh()

def refreshEngine(window, component):

    if type(component) == str and not component == "None" and not component == "":
        engine = cur2.execute("SELECT * FROM engine WHERE name = ?", [component]).fetchall()[0]
        engine = displayPrecision(engine, [1, 1, 1, 1, 1, 1])
        window['enginered'].update(engine[1])
        window['enginemass'].update(engine[2])
        window['enginepitch'].update(engine[3])
        window['engineyaw'].update(engine[4])
        window['engineroll'].update(engine[5])
        window['enginets'].update(engine[6])
    else:
        window['enginered'].update("")
        window['enginemass'].update("")
        window['enginepitch'].update("")
        window['engineyaw'].update("")
        window['engineroll'].update("")
        window['enginets'].update("")

    window.refresh()

def refreshBooster(window, component):

    if type(component) == str and not component == "None" and not component == "":
        booster = cur2.execute("SELECT * FROM booster WHERE name = ?", [component]).fetchall()[0]
        booster = displayPrecision(booster, [1, 1, 1, 1, 1, 1, 1])
        window['boosterred'].update(booster[1])
        window['boostermass'].update(booster[2])
        window['boosterenergy'].update(booster[3])
        window['boosterrr'].update(booster[4])
        window['boostercons'].update(booster[5])
        window['boosteraccel'].update(booster[6])
        window['boosterts'].update(booster[7])
    else:
        window['boosterred'].update("")
        window['boostermass'].update("")
        window['boosterenergy'].update("")
        window['boosterrr'].update("")
        window['boostercons'].update("")
        window['boosteraccel'].update("")
        window['boosterts'].update("")

    window.refresh()

def refreshShield(window, component, adjust):

    if adjust == "None" or not type(adjust) == str:
        adjustFrontRatio = 1
    else:
        halves = adjust.split(' - ', 1)
        name = "Shield " + halves[0] + " Adjust - " + halves[1]
        adjustFrontRatio = tryFloat(cur.execute("SELECT frontshieldratio FROM fcprogram WHERE name = ?", [name]).fetchall()[0][0])

    if type(component) == str and not component == "None" and not component == "":
        shield = cur2.execute("SELECT * FROM shield WHERE name = ?", [component]).fetchall()[0]
        shield = displayPrecision(shield, [1, 1, 1, 2])
        window['shieldred'].update(shield[1])
        window['shieldmass'].update(shield[2])
        window['shieldhp'].update(round(tryFloat(shield[3]),1))
        window['shieldrr'].update("{:.2f}".format(shield[4]))

        if adjustFrontRatio != 1:
            window['adjusttext'].update("Adjust:")
            window['adjustfronttext'].update("Front HP:")
            window['adjustbacktext'].update("Back HP:")
            window['shieldadjust'].update(halves[0][0] + ' | ' + halves[1])
            window['shieldfront'].update(round(tryFloat(shield[3]) * adjustFrontRatio,1))
            window['shieldback'].update(round(tryFloat(shield[3]) * (2 - adjustFrontRatio),1))
        else:
            window['adjusttext'].update("")
            window['adjustfronttext'].update("")
            window['adjustbacktext'].update("")
            window['shieldadjust'].update("")
            window['shieldfront'].update("")
            window['shieldback'].update("")
    else:
        window['shieldred'].update("")
        window['shieldmass'].update("")
        window['shieldhp'].update("")
        window['shieldrr'].update("")
        window['adjusttext'].update("")
        window['adjustfronttext'].update("")
        window['adjustbacktext'].update("")
        window['shieldadjust'].update("")
        window['shieldfront'].update("")
        window['shieldback'].update("")

    window.refresh()

def refreshFrontArmor(window, component):

    if type(component) == str and not component == "None" and not component == "":
        armor = cur2.execute("SELECT * FROM armor WHERE name = ?", [component]).fetchall()[0]
        armor = displayPrecision(armor, [1, 1])
        window['frontarmorahp'].update(armor[1])
        window['frontarmormass'].update(armor[2])
    else:
        window['frontarmorahp'].update("")
        window['frontarmormass'].update("")

    window.refresh()

def refreshRearArmor(window, component): 

    if type(component) == str and not component == "None" and not component == "":
        armor = cur2.execute("SELECT * FROM armor WHERE name = ?", [component]).fetchall()[0]
        armor = displayPrecision(armor, [1, 1])
        window['reararmorahp'].update(armor[1])
        window['reararmormass'].update(armor[2])
    else:
        window['reararmorahp'].update("")
        window['reararmormass'].update("")

    window.refresh()

def refreshDI(window, component):

    if type(component) == str and not component == "None" and not component == "":
        di = cur2.execute("SELECT * FROM droidinterface WHERE name = ?", [component]).fetchall()[0]
        di = displayPrecision(di, [1, 1, 1])
        window['dired'].update(di[1])
        window['dimass'].update(di[2])
        window['didcs'].update(di[3])
    else:
        window['dired'].update("")
        window['dimass'].update("")
        window['didcs'].update("")

    window.refresh()

def refreshCH(window, component):

    if type(component) == str and not component == "None" and not component == "":
        ch = cur2.execute("SELECT * FROM cargohold WHERE name = ?", [component]).fetchall()[0]
        ch = displayPrecision(ch, [1])
        window['chmass'].update(ch[1])
    else:
        window['chmass'].update("")

    window.refresh()

def refreshCapacitor(window, component):

    if type(component) == str and not component == "None" and not component == "":
        cap = cur2.execute("SELECT * FROM capacitor WHERE name = ?", [component]).fetchall()[0]
        cap = displayPrecision(cap, [1, 1, 1, 1])
        window['capacitorred'].update(cap[1])
        window['capacitormass'].update(cap[2])
        window['capacitorce'].update(cap[3])
        window['capacitorrr'].update(cap[4])
    else:
        window['capacitorred'].update("")
        window['capacitormass'].update("")
        window['capacitorce'].update("")
        window['capacitorrr'].update("")

    window.refresh()

def refreshSlot(window, component, slotID):

    slot = 'slot' + str(slotID)

    weaponList = listify(cur2.execute("SELECT name FROM weapon").fetchall())
    ordList = listify(cur2.execute("SELECT name FROM ordnancelauncher").fetchall())
    cmList = listify(cur2.execute("SELECT name FROM countermeasurelauncher").fetchall())

    if component in weaponList:
        statsList = ['Drain:', 'Mass:', 'Min Damage:', 'Max Damage:', 'Vs. Shields:', 'Vs. Armor:', 'Energy/Shot:', 'Refire Rate:']
        compType = "Weapon"
    elif component in ordList:
        statsList = ['Drain:', 'Mass:', 'Min Damage:', 'Max Damage:', 'Vs. Shields:', 'Vs. Armor:', 'Ammo:', 'PvE Multiplier:']
        compType = "Ordnance"
    elif component in cmList:
        statsList = ['Drain:', 'Mass:', 'Ammo:', '', '', '', '', '']
        compType = "Countermeasure"
    else:
        statsList = ['', '', '', '', '', '', '', '']
        compType = ""

    if type(component) == str and not component == "None" and not component == "":
        
        window[slot + 'stat1text'].update(statsList[0])
        window[slot + 'stat2text'].update(statsList[1])
        window[slot + 'stat3text'].update(statsList[2])
        window[slot + 'stat4text'].update(statsList[3])
        window[slot + 'stat5text'].update(statsList[4])
        window[slot + 'stat6text'].update(statsList[5])
        window[slot + 'stat7text'].update(statsList[6])
        window[slot + 'stat8text'].update(statsList[7])

        [compType, stats] = getSlotStats(component)
        if compType == "Ordnance":
            multiplier = cur.execute("SELECT multiplier FROM ordnance WHERE type = ?", [stats[2]]).fetchall()[0][0]
            window[slot + 'stat1'].update(stats[0])
            window[slot + 'stat2'].update(stats[1])
            window[slot + 'stat3'].update("")
            window[slot + 'stat4'].update("")
            window[slot + 'stat5'].update("")
            window[slot + 'stat6'].update("")
            window[slot + 'stat7'].update("")
            window[slot + 'stat8'].update(round(tryFloat(multiplier),1))

        elif compType == "Countermeasure":
            window[slot + 'stat1'].update(stats[0])
            window[slot + 'stat2'].update(stats[1])
            window[slot + 'stat3'].update("")
            window[slot + 'stat4'].update("")
            window[slot + 'stat5'].update("")
            window[slot + 'stat6'].update("")
            window[slot + 'stat7'].update("")
            window[slot + 'stat8'].update("")

        else:
            stats = displayPrecision(stats, [1, 1, 1, 1, 3, 3, 1, 3], True)
            window[slot + 'stat1'].update(stats[0])
            window[slot + 'stat2'].update(stats[1])
            window[slot + 'stat3'].update(stats[2])
            window[slot + 'stat4'].update(stats[3])
            window[slot + 'stat5'].update("{:.3f}".format(stats[4]))
            window[slot + 'stat6'].update("{:.3f}".format(stats[5]))
            window[slot + 'stat7'].update(stats[6])
            window[slot + 'stat8'].update("{:.3f}".format(stats[7]))
            window[slot + 'packselection'].update("")
    else:
        window[slot + 'stat1text'].update("")
        window[slot + 'stat2text'].update("")
        window[slot + 'stat3text'].update("")
        window[slot + 'stat4text'].update("")
        window[slot + 'stat5text'].update("")
        window[slot + 'stat6text'].update("")
        window[slot + 'stat7text'].update("")
        window[slot + 'stat8text'].update("")
        window[slot + 'stat1'].update("")
        window[slot + 'stat2'].update("")
        window[slot + 'stat3'].update("")
        window[slot + 'stat4'].update("")
        window[slot + 'stat5'].update("")
        window[slot + 'stat6'].update("")
        window[slot + 'stat7'].update("")
        window[slot + 'stat8'].update("") 
        window[slot + 'packselection'].update("")

    window.refresh()

    slotPacks = updatePacks(window, component, slot, True)

    currentPack = window[slot + 'packselection'].get()
    if currentPack in slotPacks:
        refreshPack(window,currentPack,slotID)

    return compType

def refreshPack(window, component, slotID, *arg):

    try:
        compType = arg[0]
    except:
        compType = "Null"

    slot = 'slot' + str(slotID)

    if type(component) == str and not component == "None" and not component == "":
        try:
            packStats = cur2.execute("SELECT * FROM countermeasurepack WHERE name = ?", [component]).fetchall()[0]
        except:
            packStats = cur2.execute("SELECT * FROM ordnancepack WHERE name = ?", [component]).fetchall()[0]
    
        stats = []

        for i in range(1,6):
            try:
                stats.append(packStats[i])
            except:
                stats.append("")
        try:
            ordnanceStats = cur.execute("SELECT * FROM ordnance WHERE type = ?", [packStats[4]]).fetchall()[0]
            stats[4] = int(tryFloat(stats[2]))
            stats[2] = "{:.3f}".format(tryFloat(ordnanceStats[2]))
            stats[3] = "{:.3f}".format(tryFloat(ordnanceStats[3]))
            window[slot + 'stat3'].update(round(tryFloat(stats[0]),1))
            window[slot + 'stat4'].update(round(tryFloat(stats[1]),1))
            window[slot + 'stat5'].update(stats[2])
            window[slot + 'stat6'].update(stats[3])
            window[slot + 'stat7'].update(stats[4])
        except:
            window[slot + 'stat3'].update(int(tryFloat(stats[0])))
            window[slot + 'stat4'].update(stats[1])
            window[slot + 'stat5'].update(stats[2])
            window[slot + 'stat6'].update(stats[3])
            window[slot + 'stat7'].update(stats[4])
    elif not compType == "Weapon":
        window[slot + 'stat3'].update("")
        window[slot + 'stat4'].update("")
        window[slot + 'stat5'].update("")
        window[slot + 'stat6'].update("")
        window[slot + 'stat7'].update("")

    window.refresh()

def updateOverloadMults(window):

    event, values = window.read(timeout=0)

    roLevel = values['reactoroverloadlevel']
    eoLevel = values['engineoverloadlevel']
    coLevel = values['capacitoroverchargelevel']
    woLevel = values['weaponoverloadlevel']
    adjust = values['shieldadjustsetting']

    overloads = cur.execute("SELECT name,energyefficiency,genefficiency FROM fcprogram").fetchall()[0:16]

    if roLevel == "None":
        roGenEff = 1
        window['reactoroverloaddesc1'].update("")
        window['reactoroverloaddesc2'].update("")
    else:
        roGenEff = tryInt(tryFloat(overloads[roLevel-1][2]))
        window['reactoroverloaddesc1'].update("Generation:")
        window['reactoroverloaddesc2'].update(str(roGenEff) + "x")

    if eoLevel == "None":
        eoEff = 1
        eoGenEff = 1
        window['engineoverloaddesc1'].update("")
        window['engineoverloaddesc2'].update("")
        window['engineoverloaddesc3'].update("")
        window['engineoverloaddesc4'].update("")
    else:
        eoEff = tryInt(round(1/tryFloat(overloads[eoLevel+3][1]),2))
        eoGenEff = tryInt(tryFloat(overloads[eoLevel+3][2]))
        window['engineoverloaddesc1'].update("TS/PYR:")
        window['engineoverloaddesc2'].update(str(eoGenEff) + 'x')
        window['engineoverloaddesc3'].update("Drain:")
        window['engineoverloaddesc4'].update(str(eoEff) + 'x')
    
    if coLevel == "None":
        coEff = 1
        coGenEff = 1
        window['capoverloaddesc1'].update("")
        window['capoverloaddesc2'].update("")
        window['capoverloaddesc3'].update("")
        window['capoverloaddesc4'].update("")
    else:    
        coEff = tryInt(round(1/tryFloat(overloads[coLevel+7][1]),2))
        coGenEff = tryInt(tryFloat(overloads[coLevel+7][2]))
        window['capoverloaddesc1'].update("CE/RR:")
        window['capoverloaddesc2'].update(str(coGenEff) + 'x')
        window['capoverloaddesc3'].update("Drain:")
        window['capoverloaddesc4'].update(str(coEff) + 'x')

    if woLevel == "None":
        woEff = 1
        woGenEff = 1
        window['weaponoverloaddesc1'].update("")
        window['weaponoverloaddesc2'].update("")
        window['weaponoverloaddesc3'].update("")
        window['weaponoverloaddesc4'].update("")
        
    else:
        woEff = tryInt(round(1/tryFloat(overloads[woLevel+11][1]),2))
        woGenEff = tryInt(tryFloat(overloads[woLevel+11][2]))
        window['weaponoverloaddesc1'].update("Damage:")
        window['weaponoverloaddesc2'].update(str(woGenEff) + 'x')
        window['weaponoverloaddesc3'].update("Drain/EPS:")
        window['weaponoverloaddesc4'].update(str(woEff) + 'x')

    if adjust == "None" or not type(adjust) == str:
        adjustFrontRatio = 1
        window['shieldadjustdesc1'].update("")
        window['shieldadjustdesc2'].update("")
        window['shieldadjustdesc3'].update("")
        window['shieldadjustdesc4'].update("")
    else:
        halves = adjust.split(' - ', 1)
        name = "Shield " + halves[0] + " Adjust - " + halves[1]
        adjustFrontRatio = tryFloat(cur.execute("SELECT frontshieldratio FROM fcprogram WHERE name = ?", [name]).fetchall()[0][0])
        window['shieldadjustdesc1'].update("Front HP:")
        window['shieldadjustdesc2'].update(str(adjustFrontRatio) + 'x')
        window['shieldadjustdesc3'].update("Back HP:")
        window['shieldadjustdesc4'].update(str((2-adjustFrontRatio)) + 'x')

    window.refresh()

def doWeaponCalculations(window):
    event, values = window.read(timeout=0)

    overloads = cur.execute("SELECT name,energyefficiency,genefficiency FROM fcprogram").fetchall()[0:16]
    
    coLevel = values['capacitoroverchargelevel']
    woLevel = values['weaponoverloadlevel']

    if coLevel == "None":
        coGenEff = 1
    else:    
        coGenEff = tryFloat(overloads[coLevel+7][2])

    if woLevel == "None":
        woEff = 1
        woGenEff = 1
    else:
        woEff = tryFloat(overloads[woLevel+11][1])
        woGenEff = tryFloat(overloads[woLevel+11][2])
    
    chassis = window['chassistype'].get()
    try:
        headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])
    except:
        headers = [''] * 8
    slotKeys = ['slot1selection', 'slot2selection', 'slot3selection', 'slot4selection', 'slot5selection', 'slot6selection', 'slot7selection', 'slot8selection']
    packKeys = ['slot1packselection', 'slot2packselection', 'slot3packselection', 'slot4packselection', 'slot5packselection', 'slot6packselection', 'slot7packselection', 'slot8packselection']

    dpShotListPvE = []
    dpShotListPvP = []
    epsList = []
    refireList = []
    loadedWeapons = []
    weaponOwner = []
    loadedOrdnance = []
    ordnanceDamageListPvE = []
    ordnanceDamageListPvP = []
    pilotWeaponDPShotPvE = 0
    pilotWeaponDPShotPvP = 0

    for i in range(0, 8):
        [compType, stats] = getSlotStats(values[slotKeys[i]])
        if compType == "Weapon":
            avgDamage = (tryFloat(stats[2]) + tryFloat(stats[3]))/2 * woGenEff
            vss = tryFloat(stats[4])
            vsa = tryFloat(stats[5])
            dpShot = avgDamage * (2 * vss + 2 * vss * vsa + 1)/5
            dpShotListPvE.append(dpShot)
            dpShotListPvP.append(dpShot * 0.375)
            epsList.append(tryFloat(stats[6]) / woEff)
            refireList.append(tryFloat(stats[7]))
            loadedWeapons.append(headers[i])
            if "Turret" in headers[i]:
                weaponOwner.append("Turret")
                dpShotListPvE[-1] *= 2.75
            else:
                weaponOwner.append("Pilot")
                pilotWeaponDPShotPvE += dpShot
                pilotWeaponDPShotPvP += dpShot * 0.375
            
        elif compType == "Ordnance":
            if not values[packKeys[i]] == "None" and not values[packKeys[i]] == "":
                stats = cur2.execute("SELECT * FROM ordnancepack WHERE name = ?", [values[packKeys[i]]]).fetchall()[0]
                avgDamage = (tryFloat(stats[1]) + tryFloat(stats[2]))/2 * woGenEff
                typeStats = cur.execute("SELECT * FROM ordnance WHERE type = ?", [stats[4]]).fetchall()[0]
                vss = tryFloat(typeStats[2])
                vsa = tryFloat(typeStats[3])
                ordnanceDamage = avgDamage * (2 * vss + 2 * vss * vsa + 1)/5
                ordnanceDamageListPvE.append(ordnanceDamage * tryFloat(typeStats[1]))
                ordnanceDamageListPvP.append(ordnanceDamage * 0.5)
                loadedOrdnance.append(headers[i])

    capEnergy = tryFloat(window['capacitorce'].get()) * coGenEff
    capRecharge = tryFloat(window['capacitorrr'].get()) * coGenEff

    window['overloadedce'].update('')
    window['overloadedrr'].update('')
    window['fullcapdamage'].update('')
    window['firetime'].update('')
    window['caprecharge'].update('')
    window['firingratio'].update('')

    for i in range(1,9):
        window['slot' + str(i) + 'damagepve'].update('')
        window['slot' + str(i) + 'damagepvp'].update('')
        window['slot' + str(i) + 'damagetext'].update('')
    window['pveheader'].update('')
    window['pvpheader'].update('')
    window['pilotguntext'].update('')
    window['pilotweapondamagepve'].update('')
    window['pilotweapondamagepvp'].update('')

    if not capEnergy == 0 and not len(epsList) == 0:
        t = 0
        lastRechargeTick = 0
        currentEnergy = capEnergy
        serverTickrate = 30
        lastShot = [-1] * len(epsList)
        refireAdjustment = 0.11
        fireTime = 0
        damageDealtPerWeapon = [0] * len(epsList)

        while t < 300:
            if t - lastRechargeTick >= 1.5:
                lastRechargeTick = t
                currentEnergy += capRecharge * 1.5
                if currentEnergy > capEnergy:
                    currentEnergy = capEnergy
            for i in range(0, len(epsList)):
                eps = epsList[i]
                refire = refireList[i] + refireAdjustment
                if t - lastShot[i] > refire:
                    lastShot[i] = t
                    currentEnergy -= eps
                    damageDealtPerWeapon[i] += dpShotListPvE[i]
            if currentEnergy < 0:
                fireTime = t
                break
            t += 1/serverTickrate
        
        fullCapDamage = 0
        for i in damageDealtPerWeapon:
            fullCapDamage += i
        fullCapDamage = round(fullCapDamage,1)

        try:
            capRechargeTime = round(ceil(capEnergy/(1.5*capRecharge))*1.5,1)
        except:
            capRechargeTime = ''

        if not tryFloat(fireTime) == 0:
            firingRatio = str(round(fireTime/(fireTime + capRechargeTime) * 100,1)) + '%'
        else:
            firingRatio = ''

        if fireTime == 0:
            fireTime = ">300s"
        else:
            fireTime = str(round(fireTime,1)) + 's'

        capRechargeTime = str(capRechargeTime) + 's'

        if coGenEff == 1:
            window['overloadedcetext'].update('Cap Energy:')
            window['overloadedrrtext'].update('Cap Recharge:')
        else:
            window['overloadedcetext'].update('Overloaded CE:')
            window['overloadedrrtext'].update('Overloaded RR:')

        window['overloadedce'].update(capEnergy)
        window['overloadedrr'].update(capRecharge)
        window['fullcapdamage'].update(fullCapDamage)
        window['firetime'].update(fireTime)
        window['caprecharge'].update(capRechargeTime)
        window['firingratio'].update(firingRatio)

    if not len(epsList) == 0:

        loadedCombined = loadedWeapons + loadedOrdnance
        dpShotCombinedPvE = dpShotListPvE + ordnanceDamageListPvE
        dpShotCombinedPvP = dpShotListPvP + ordnanceDamageListPvP

        if len(loadedCombined) < 8:
            loadedCombined += [''] * (8-len(loadedCombined))
            dpShotCombinedPvE += [''] * (8-len(dpShotCombinedPvE))
            dpShotCombinedPvP += [''] * (8-len(dpShotCombinedPvP))

        window['pveheader'].update('PvE')
        window['pvpheader'].update('PvP')
        window['pilotguntext'].update('Pilot Gun Total:')
        pilotPvE = round(pilotWeaponDPShotPvE,1)
        pilotPvP = round(pilotWeaponDPShotPvP,1)
        window['pilotweapondamagepve'].update(pilotPvE)
        window['pilotweapondamagepvp'].update(pilotPvP)

        for i in range(1,9):
            if loadedCombined[i-1] == '':
                loadedWeapon = ''
            else:
                loadedWeapon = loadedCombined[i-1] + ':'
            window['slot' + str(i) + 'damagetext'].update(loadedWeapon)
            pveDamage = round(tryFloat(dpShotCombinedPvE[i-1]),1)
            pvpDamage = round(tryFloat(dpShotCombinedPvP[i-1]),1)
            if pveDamage == 0:
                window['slot' + str(i) + 'damagepve'].update('')
                window['slot' + str(i) + 'damagepvp'].update('')
            else:
                window['slot' + str(i) + 'damagepve'].update(pveDamage)
                window['slot' + str(i) + 'damagepvp'].update(pvpDamage)

    window.refresh()

def doPropulsionCalculations(window):
    event, values = window.read(timeout=0)

    overloads = cur.execute("SELECT name,energyefficiency,genefficiency FROM fcprogram").fetchall()[0:16]

    eoLevel = values['engineoverloadlevel']

    try:
        chassisName = window['chassistype'].get()
        chassisData = cur.execute("SELECT * FROM chassis WHERE name = ?", [chassisName]).fetchall()
        speedMod = tryFloat(chassisData[0][15])
        speedModFoils = tryFloat(chassisData[0][16])
        accel = tryFloat(chassisData[0][10])
        decel = tryFloat(chassisData[0][11])
        chassisPitch = tryFloat(chassisData[0][12])
        chassisYaw = tryFloat(chassisData[0][13])
        chassisRoll = tryFloat(chassisData[0][14])
        chassisSlide = tryFloat(chassisData[0][20])
    except:
        return

    if eoLevel == "None":
        eoGenEff = 1
    else:
        eoGenEff = tryFloat(overloads[eoLevel+3][2])

    try:
        engine = cur2.execute("SELECT * FROM engine WHERE name = ?", [values['engineselection']]).fetchall()[0]
    except:
        engine = "None"
    try:
        booster = cur2.execute("SELECT * FROM booster WHERE name = ?", [values['boosterselection']]).fetchall()[0]
    except:
        booster = "None"

    if speedMod == 1:
        speedModStr = "{:.2f}".format(speedMod)
    else:
        speedModStr = speedMod
    
    if speedModFoils == 1:
        speedModFoilsStr = "{:.2f}".format(speedModFoils)
    else:
        speedModFoilsStr = speedModFoils

    if not speedModFoils == 0 and not speedModFoils == speedMod:
        window['chassisspeedmod'].update(str(speedModStr) + ' (' + str(speedModFoilsStr) + ')')
    else:
        window['chassisspeedmod'].update(str(speedModStr))

    window['chassisad'].update(str(int(accel)) + ' / ' + str(int(decel)))
    window['chassispyr'].update(str(int(chassisPitch)) + ' / ' + str(int(chassisYaw)) + ' / ' + str(int(chassisRoll)))
    window['chassisslide'].update(str(chassisSlide))
    window['topspeed'].update('')
    window['boostedtopspeed'].update('')
    window['boostdistance'].update('')
    window['boosteruptime'].update('')

    if not engine == "None":
        engineTS = tryFloat(engine[6])
        speed = engineTS * eoGenEff * speedMod * 10
        if not speedModFoils == 0 and not speedModFoils == speedMod:
            speedFoils = engineTS * eoGenEff * speedModFoils * 10
            window['topspeed'].update(str(int(speed)) + ' (' + str(int(speedFoils)) + ')')
        else:
            window['topspeed'].update(str(int(speed)))

    if not booster == "None":
        boosterEnergy = tryFloat(booster[3])
        boosterRecharge = tryFloat(booster[4])
        boosterCons = tryFloat(booster[5])
        boosterAccel = tryFloat(booster[6]) + accel
        boosterTS = tryFloat(booster[7])

        boosterUptime = ceil(boosterEnergy / (boosterCons * 1.5)) * 1.5
        boosterRechargeTime = ceil(boosterEnergy / (boosterRecharge * 1.5)) * 1.5
        boosterUptimePercentage = round(boosterUptime/(boosterUptime + boosterRechargeTime) * 100,1)
        window['boosteruptime'].update(str(boosterUptimePercentage) + '%')

    if not engine == "None" and not booster == "None":
        boostedTS = (engineTS * eoGenEff + boosterTS) * speedMod * 10
        accelTime = (boosterTS * speedMod) / (boosterAccel + accel)
        decelTime = (boosterTS * speedMod) / decel
        accelLoss = accelTime * boosterTS * speedMod / 2
        decelGain = decelTime * boosterTS * speedMod / 2
        boostedDist = round(boostedTS/10 * boosterUptime - accelLoss + decelGain,0)

        if not speedModFoils == 0 and not speedModFoils == speedMod:
            boostedTSFoils = (engineTS * eoGenEff + boosterTS) * speedModFoils * 10
            accelTime = (boosterTS * speedModFoils) / (boosterAccel + accel)
            decelTime = (boosterTS * speedModFoils) / decel
            accelLoss = accelTime * boosterTS * speedModFoils / 2
            decelGain = decelTime * boosterTS * speedModFoils / 2
            boostedDistFoils = round(boostedTSFoils/10 * boosterUptime - accelLoss + decelGain)
            window['boostedtopspeed'].update(str(int(boostedTS)) + ' (' + str(int(boostedTSFoils)) + ')')
            window['boostdistance'].update(str(int(boostedDist)) + 'm (' + str(int(boostedDistFoils)) + 'm)')
        else:
            window['boostedtopspeed'].update(str(int(boostedTS)))
            window['boostdistance'].update(str(int(boostedDist)) + 'm')

    window.refresh()

def clearLoadout(window, clearType):

    if clearType == "all":
        window['slot1header'].update('')
        window['slot2header'].update('')
        window['slot3header'].update('')
        window['slot4header'].update('')
        window['slot5header'].update('')
        window['slot6header'].update('')
        window['slot7header'].update('')
        window['slot8header'].update('')
        window['loadoutname'].update('')
        window['chassistype'].update('')
        window['loadoutmass'].update('')
        window['chassisspeedmod'].update('')
        window['chassisad'].update('')
        window['chassispyr'].update('')
        window['chassisslide'].update('')
        window['frontarmorselection'].update(disabled=True)
        window['reararmorselection'].update(disabled=True)
        window['boosterselection'].update(disabled=True)
        window['capselection'].update(disabled=True)
        window['chselection'].update(disabled=True) 
        window['diselection'].update(disabled=True)
        window['engineselection'].update(disabled=True)
        window['reactorselection'].update(disabled=True)
        window['shieldselection'].update(disabled=True)  
        window['slot1selection'].update(disabled=True)
        window['slot2selection'].update(disabled=True)
        window['slot3selection'].update(disabled=True)
        window['slot4selection'].update(disabled=True)
        window['slot5selection'].update(disabled=True)
        window['slot6selection'].update(disabled=True)
        window['slot7selection'].update(disabled=True)
        window['slot8selection'].update(disabled=True)
        window['reactoroverloadlevel'].update(disabled=True)
        window['engineoverloadlevel'].update(disabled=True)
        window['capacitoroverchargelevel'].update(disabled=True)
        window['weaponoverloadlevel'].update(disabled=True)
        window['shieldadjustsetting'].update(disabled=True)
    window['frontarmorselection'].update("None")
    window['reararmorselection'].update("None")
    window['boosterselection'].update("None")
    window['capselection'].update("None")
    window['chselection'].update("None") 
    window['diselection'].update("None")
    window['engineselection'].update("None")
    window['reactorselection'].update("None")
    window['shieldselection'].update("None")  
    window['slot1selection'].update("None")
    window['slot2selection'].update("None")
    window['slot3selection'].update("None")
    window['slot4selection'].update("None")
    window['slot5selection'].update("None")
    window['slot6selection'].update("None")
    window['slot7selection'].update("None")
    window['slot8selection'].update("None")
    window['reactoroverloadlevel'].update("None")
    window['engineoverloadlevel'].update("None")
    window['capacitoroverchargelevel'].update("None")
    window['weaponoverloadlevel'].update("None")
    window['shieldadjustsetting'].update("None")

    refreshReactor(window, "None")
    refreshEngine(window, "None")
    refreshBooster(window, "None")
    refreshShield(window, "None", "None")
    refreshFrontArmor(window, "None")
    refreshRearArmor(window, "None")
    refreshDI(window, "None")
    refreshCH(window, "None")
    refreshCapacitor(window, "None")
    compType1 = refreshSlot(window, "None", 1)
    compType2 = refreshSlot(window, "None", 2)
    compType3 = refreshSlot(window, "None", 3)
    compType4 = refreshSlot(window, "None", 4)
    compType5 = refreshSlot(window, "None", 5)
    compType6 = refreshSlot(window, "None", 6)
    compType7 = refreshSlot(window, "None", 7)
    compType8 = refreshSlot(window, "None", 8)
    window['slot1packselection'].update(value = "None", visible=False) 
    window['slot2packselection'].update(value = "None", visible=False) 
    window['slot3packselection'].update(value = "None", visible=False) 
    window['slot4packselection'].update(value = "None", visible=False) 
    window['slot5packselection'].update(value = "None", visible=False)  
    window['slot6packselection'].update(value = "None", visible=False) 
    window['slot7packselection'].update(value = "None", visible=False) 
    window['slot8packselection'].update(value = "None", visible=False) 
    refreshPack(window, "None", 1, compType1)
    refreshPack(window, "None", 2, compType2)
    refreshPack(window, "None", 3, compType3)
    refreshPack(window, "None", 4, compType4)
    refreshPack(window, "None", 5, compType5)
    refreshPack(window, "None", 6, compType6)
    refreshPack(window, "None", 7, compType7)
    refreshPack(window, "None", 8, compType8)
    event, values = window.read(timeout=0)

    if not clearType == "all":
        try:
            chassisMass = cur2.execute("SELECT mass FROM loadout WHERE name = ?", [window['loadoutname'].get()]).fetchall()[0][0]
        except:
            chassisMass = 0
    else:
        chassisMass = 0

    updateMassStrings(chassisMass, window)
    updateDrainStrings(window)
    doWeaponCalculations(window)
    doPropulsionCalculations(window)
    updateOverloadMults(window)
    updateProfile(window)
    window.refresh()

def updateLoadoutPreview(loadout):

    loadoutData = cur2.execute("SELECT * FROM loadout WHERE name = ?",[loadout]).fetchall()[0]
    chassis = loadoutData[1]
    try:
        headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])
        headers = [x + ':' for x in headers if x != '']
        slotText = ["Chassis:", "Mass:", "Reactor:", "Engine:", "Booster:", "Shield:", "Front Armor:", "Rear Armor:", "Droid Interface:", "Cargo Hold:", "Capacitor:"] + headers
        slotText += [''] * (19 - len(slotText))
        indices = [1, 2, 10, 9, 5, 11, 3, 4, 8, 7, 6, 12, 13, 14, 15, 16, 17, 18, 19] #Hate this shit. Why did I make it like this.
        statText = []
        for i in indices:
            if loadoutData[i] == 'None':
                statText.append('')
            else:
                statText.append(loadoutData[i])
    except:
        slotText = [''] * 19
        statText = slotText
        alert('Error',['Error: Invalid loadout selected. This is probably due to an issue with imported loadout data.','I recommend you delete the loadout and rebuild it.'],[],5)

    return slotText, statText

def createLoadout(*editArgs):

    chassisRaw= cur.execute("SELECT name FROM chassis").fetchall()
    massRaw = cur.execute("SELECT mass FROM chassis").fetchall()
    chassisList = []
    massList = []

    if len(editArgs) > 0:
        editing = True
        oldName = editArgs[0]
        titleString = "Editing Loadout: " + oldName
        oldLoadout = cur2.execute("SELECT * FROM loadout WHERE name = ?",[oldName]).fetchall()[0]
        oldChassis = oldLoadout[1]
        oldMass = oldLoadout[2]
        chassisDisable = True
    else:
        editing = False
        oldName = ''
        titleString = "Create New Loadout"
        oldChassis = 'Select Chassis'
        oldMass = ''
        chassisDisable = False

    for i in range(0, len(chassisRaw)):
        chassisList.append(chassisRaw[i][0])
        massList.append(massRaw[i][0])

    textColumn = [
        [sg.Push(), sg.Text("Loadout Name:", font=baseFont)],
        [sg.Push(), sg.Text("Select Chassis:", font=baseFont)],
        [sg.Push(), sg.Text("Chassis Mass:", font=baseFont)],
    ]

    inputColumn = [
        [sg.Input(oldName, font=baseFont, key='name', s=26)],
        [sg.Combo(chassisList, default_value=oldChassis, font=baseFont, key='chassis', s=24, enable_events=True, readonly=True, disabled=chassisDisable)],
        [sg.Input(oldMass, font=baseFont, key='mass', s=11, enable_events=True), sg.Text("", key='maxmass', font=baseFont), sg.Push()],
    ]

    layout = [
        [sg.Push(), sg.Text(titleString, font=headerFont), sg.Push()],
        [sg.Text("",font=baseFont,p=fontPadding)],
        [sg.Column(textColumn), sg.Column(inputColumn)],
        [sg.Text("",font=baseFont,p=fontPadding)],
        [sg.Push(),sg.Push(),sg.Button("Save", font=buttonFont, bind_return_key=True), sg.Push(), sg.Button("Cancel", font=buttonFont),sg.Push(),sg.Push()]
    ]

    createLoadoutWindow = sg.Window('Create Loadout',layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    createLoadoutWindow['name'].set_focus()
    createLoadoutWindow.bind('<Escape>', 'Cancel')

    valueList = ['', '', '']

    while True:
        event, values = createLoadoutWindow.read()
        if event == 'chassis':
            if not values['chassis'] == "":
                maxMass = massList[chassisList.index(values['chassis'])]
                createLoadoutWindow['maxmass'].update("Max: " + "{:,.0f}".format(float(maxMass)))
        if event == 'mass':
            try:
                float(values['mass'])
            except:
                createLoadoutWindow['mass'].update(values['mass'][:-1])
        if event == 'Save':
            valueList = [values['name'], values['chassis'], values['mass']]
            if valueList[0] == "":
                alert('Error',["Error: You must enter a name for this loadout."],[],3)
                remodalize(createLoadoutWindow)
            elif valueList[1] == "Select Chassis" or valueList[1] == "":
                alert('Error',["Error: You must select a chassis."],[],3)
                remodalize(createLoadoutWindow)
            elif tryFloat(valueList[2]) == 0:
                alert('Error',["Error: You must enter a value for the chassis mass."],[],3)
                remodalize(createLoadoutWindow)
            else:
                if not editing:
                    valueList += ['None'] * 30
                    try:
                        cur2.execute("INSERT INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",valueList)
                        break
                    except:
                        decision = alert('Alert',["A loadout with this name already exists. Do you wish to overwrite it?"],['Proceed','Cancel'],0)
                        remodalize(createLoadoutWindow)
                        if decision == "Proceed":
                            try:
                                cur2.execute("INSERT OR REPLACE INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",valueList)
                            except:
                                alert('Error',['Error: An unknown issue occurred when attempting to save this loadout. Make a post on my Discord detailing what happened so I can investigate.','-Seraph'],[],10)
                                remodalize(createLoadoutWindow)
                            break
                elif editing:
                    valueList += oldLoadout[3:]
                    if valueList != oldLoadout:
                        decision = alert("Alert",["You are about to overwrite your existing loadout. Do you wish to continue?"],['Proceed', 'Cancel'],0)
                        remodalize(createLoadoutWindow)
                        if decision == 'Proceed':
                            try:
                                cur2.execute("DELETE FROM loadout WHERE name = ?",[oldName])
                                cur2.execute("INSERT INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",valueList)
                            except:
                                alert('Error',['Error: An unknown issue occurred when attempting to save this loadout. Make a post on my Discord detailing what happened so I can investigate.','-Seraph'],[],10)
                                remodalize(createLoadoutWindow)
                            break

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            break

    createLoadoutWindow.close()
    compdb.commit()

    return valueList[0:3]

def duplicateLoadout(selection):
    
    loadoutList = [x for x in cur2.execute("SELECT * FROM loadout").fetchall()]
    chassisType = [x[1] for x in loadoutList if x[0] == selection][0]
    chassisMass = [x[2] for x in loadoutList if x[0] == selection][0]

    cmList = [x[0] for x in cur2.execute("SELECT name FROM countermeasurelauncher").fetchall()]
    ordList = [x[0] for x in cur2.execute("SELECT name FROM ordnancelauncher").fetchall()]
    weaponList = [x[0] for x in cur2.execute("SELECT name FROM weapon").fetchall()]

    slotCompList = [x[12:28] for x in loadoutList if x[0] == selection][0]
    slotCompTypes = []
    for i in range(0,8):
        if slotCompList[i] in ['None','']:
            slotCompTypes.append(0)
        elif slotCompList[i] in cmList:
            slotCompTypes.append(3)
        elif slotCompList[i] in ordList:
            slotCompTypes.append(2)
        elif slotCompList[i] in weaponList:
            slotCompTypes.append(1)
        else:
            slotCompTypes.append(0)

    chassisData = cur.execute("SELECT * FROM chassis").fetchall()
    chassisList = [chassisType] + [x[0] for x in chassisData if x[0] != chassisType]
    selectionMax = [x[1] for x in chassisData if x[0] == chassisType][0]

    leftCol = [
        [sg.Push(),sg.Text('Loadout to Duplicate:',font=baseFont,p=elementPadding)],
        [sg.Push(),sg.Text('New Loadout Name:',font=baseFont,p=elementPadding)],
        [sg.Push(),sg.Text('New Chassis Type:',font=baseFont,p=elementPadding)],
        [sg.Push(),sg.Text('New Chassis Mass:',font=baseFont,p=elementPadding)],
    ]

    rightCol = [
        [sg.Text(selection,font=baseFont,p=elementPadding),sg.Push()],
        [sg.Input(selection,font=baseFont, key='newname', s=26,p=elementPadding),sg.Push()],
        [sg.Combo(chassisList,default_value=chassisType,font=baseFont, key='chassisselect', s=24,p=elementPadding,readonly=True,enable_events=True),sg.Push()],
        [sg.Input(chassisMass, font=baseFont, key='mass', s=11, enable_events=True), sg.Text('Max Mass: ' + selectionMax, key='maxmass', font=baseFont), sg.Push()],
    ]

    Layout = [
        [sg.Push(),sg.Text('Duplicate Loadout',font=headerFont),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',leftCol,border_width=0,p=elementPadding),sg.Frame('',rightCol,border_width=0,p=elementPadding)],
        [sg.VPush()],
        [sg.Push(),sg.Button('Duplicate',font=buttonFont),sg.Push(),sg.Button('Cancel',font=buttonFont),sg.Push()]        
    ]

    dupeWindow = sg.Window('Duplicate Loadout', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True)
    dupeWindow['newname'].set_focus()
    dupeWindow.bind('<Escape>', 'Cancel')

    dupeName = selection

    while True:
        event, values = dupeWindow.read()

        if event == 'chassisselect':
            newChassis = values['chassisselect']
            newMaxMass = [x[1] for x in chassisData if x[0] == newChassis][0]
            dupeWindow['maxmass'].update("Max Mass: " + newMaxMass)

        if event == "Duplicate":

            newChassis = values['chassisselect']
            newSlots = [x[2:10] for x in chassisData if x[0] == newChassis][0] #important: we don't care about the selection's *slots*, only the types of components that are loaded.
            slotCompatibility = []
            for i in range(0,8):
                currSlot = []
                if 'CM' in newSlots[i] or 'Countermeasures' in newSlots[i]:
                    currSlot.append(3)
                if 'Ordnance' in newSlots[i]:
                    currSlot.append(2)
                if 'Weapon' in newSlots[i]:
                    currSlot.append(1)
                slotCompatibility.append(currSlot)

            compOrder = [3, 2, 1]

            newSlotList = [''] * 16 #we'll also move packs as appropriate

            remainingSlots = [0,1,2,3,4,5,6,7]

            for k in compOrder:
                for j in range(0,8):
                    if slotCompTypes[j] == k:
                        for i in remainingSlots:
                            if slotCompTypes[j] in slotCompatibility[i]:
                                newSlotList[i] = slotCompList[j] #map slots
                                newSlotList[i+8] = slotCompList[j+8] #map associated packs if any
                                remainingSlots.remove(i)
                                break

            droppedCompFlag = False
            for i in slotCompList:
                if i not in newSlotList and i not in ['', 'None']:
                    droppedCompFlag = True

            newName = values['newname']
            if newName in [x[0] for x in loadoutList]:
                alert('Error',['Error: A loadout with this name already exists.','You must enter a unique name for the duplicate loadout.'],[],3)
                remodalize(dupeWindow)
            elif newName == '':
                alert('Error',['Error: You must enter a name for the duplicate loadout.'],[],3)
                remodalize(dupeWindow)
            else:
                response = ''
                if droppedCompFlag:
                    response = alert('Warning',["Warning: The target chassis doesn't have slots to accommodate all of the source loadout's components.","Incompatible components will be unslotted. Continue anyway?"],['Proceed','Cancel'],0)
                if response == 'Proceed' or not droppedCompFlag:
                    loadoutData = [[newName] + list(x[1:]) for x in loadoutList if x[0] == selection][0]
                    loadoutData[1:3] = [values['chassisselect'],values['mass']]
                    loadoutData[12:28] = newSlotList
                    try:
                        cur2.execute("INSERT INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",loadoutData)
                        dupeName = newName
                    except:
                        alert('Error',['Error: An unknown issue occurred when attempting to duplicate this loadout. Make a post on my Discord detailing what happened so I can investigate.','-Seraph'],[],10)
                        remodalize(dupeWindow)
                    break

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            break
    
    dupeWindow.close()
    return dupeName

def loadLoadout(window):

    loadoutList = listify(cur2.execute("SELECT name FROM loadout ORDER BY name ASC").fetchall())

    leftCol = [
        [sg.Push(),sg.Text("Select a Loadout", font=baseFont),sg.Push()],
        [sg.Listbox(values=loadoutList, size=(30, 24), enable_events=True, key='loadoutname', font=baseFont, select_mode="single", justification='center')]
    ]

    rightColLeft = []
    rightColRight = []

    for i in range(0,20):
        rightColLeft.append([sg.Push(),sg.Text("", font=baseFont, key='text'+str(i), p=fontPadding)])
        rightColRight.append([sg.Text("", font=baseFont, key='data'+str(i), p=fontPadding),sg.Push()])

    rightCol = [
        [sg.Push(),sg.Text("Loadout Preview", font=baseFont),sg.Push()],
        [sg.Frame('',rightColLeft,border_width=0,p=elementPadding,s=(117,425)), sg.Frame('',rightColRight,border_width=0,p=elementPadding,s=(267,425))]
    ]

    Layout = [
        [sg.Push(),sg.Text('Loadout Management',font=headerFont,p=elementPadding),sg.Push()],
        [sg.vtop(sg.Column(leftCol)), sg.vtop(sg.Frame('', rightCol, border_width=0, s=(450,425)))],
        [sg.VPush()],
        [sg.Push(),sg.Button("Load", font=buttonFont),sg.Push(),sg.Button("Edit",font=buttonFont),sg.Push(),sg.Button("Duplicate",font=buttonFont),sg.Push(),sg.Button("Delete", font=buttonFont),sg.Push(),sg.Button("Exit", font=buttonFont),sg.Push()]
    ]

    loadWindow = sg.Window('Loadout Management', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True)
    sg.theme('Discord_Dark')
    loadWindow.bind('<Escape>', 'Cancel')

    loadoutData = [''] * 34

    loaded = False

    while True:
        event, values = loadWindow.read()
        
        if event == 'loadoutname':
            slotText, statText = updateLoadoutPreview(values['loadoutname'][0])
            remodalize(loadWindow)
            loadWindow['text0'].update("Loadout Name:")
            loadWindow['data0'].update(values['loadoutname'][0])
            for i in range(1,20):
                loadWindow['text' + str(i)].update(slotText[i-1])
                if slotText[i-1] == 'Mass:':
                    loadWindow['data' + str(i)].update("{:.1f}".format(tryFloat(statText[i-1])))
                else:
                    loadWindow['data' + str(i)].update(statText[i-1])
            loadWindow.refresh()

        if event == "Load":
            try:
                loadout = values['loadoutname'][0]
            except:
                loadout = ''
            if loadout == '':
                alert('Error',['Please select a loadout.'],['Okay'],0)
                remodalize(loadWindow)
                pass
            else:
                loadoutData = cur2.execute("SELECT * FROM loadout WHERE name = ?", [loadout]).fetchall()[0]
                updateSlotHeaders(loadoutData[1], window)

                window['loadoutname'].update(value = loadoutData[0])
                window['chassistype'].update(value = loadoutData[1])
                window['loadoutmass'].update(value = loadoutData[2])
                window['frontarmorselection'].update(value = loadoutData[3])
                window['reararmorselection'].update(value = loadoutData[4])
                window['boosterselection'].update(value = loadoutData[5]) 
                window['capselection'].update(value = loadoutData[6])
                window['chselection'].update(value = loadoutData[7])  
                window['diselection'].update(value = loadoutData[8]) 
                window['engineselection'].update(value = loadoutData[9]) 
                window['reactorselection'].update(value = loadoutData[10]) 
                window['shieldselection'].update(value = loadoutData[11])  
                window['slot1selection'].update(value = loadoutData[12]) 
                window['slot2selection'].update(value = loadoutData[13]) 
                window['slot3selection'].update(value = loadoutData[14]) 
                window['slot4selection'].update(value = loadoutData[15]) 
                window['slot5selection'].update(value = loadoutData[16]) 
                window['slot6selection'].update(value = loadoutData[17]) 
                window['slot7selection'].update(value = loadoutData[18]) 
                window['slot8selection'].update(value = loadoutData[19])
                window['reactoroverloadlevel'].update(value = loadoutData[28]) 
                window['engineoverloadlevel'].update(value = loadoutData[29]) 
                window['capacitoroverchargelevel'].update(value = loadoutData[30]) 
                window['weaponoverloadlevel'].update(value = loadoutData[31]) 
                window['shieldadjustsetting'].update(value = loadoutData[32])

                refreshReactor(window, loadoutData[10])
                refreshEngine(window, loadoutData[9])
                refreshBooster(window, loadoutData[5])
                refreshShield(window, loadoutData[11], loadoutData[32])
                refreshFrontArmor(window, loadoutData[3])
                refreshRearArmor(window, loadoutData[4])
                refreshDI(window, loadoutData[8])
                refreshCH(window, loadoutData[7])
                refreshCapacitor(window, loadoutData[6])
                compType1 = refreshSlot(window, loadoutData[12], 1)
                compType2 = refreshSlot(window, loadoutData[13], 2)
                compType3 = refreshSlot(window, loadoutData[14], 3)
                compType4 = refreshSlot(window, loadoutData[15], 4)
                compType5 = refreshSlot(window, loadoutData[16], 5)
                compType6 = refreshSlot(window, loadoutData[17], 6)
                compType7 = refreshSlot(window, loadoutData[18], 7)
                compType8 = refreshSlot(window, loadoutData[19], 8)
                window['slot1packselection'].update(value = loadoutData[20]) 
                window['slot2packselection'].update(value = loadoutData[21]) 
                window['slot3packselection'].update(value = loadoutData[22]) 
                window['slot4packselection'].update(value = loadoutData[23]) 
                window['slot5packselection'].update(value = loadoutData[24]) 
                window['slot6packselection'].update(value = loadoutData[25]) 
                window['slot7packselection'].update(value = loadoutData[26]) 
                window['slot8packselection'].update(value = loadoutData[27]) 
                refreshPack(window, loadoutData[20], 1, compType1)
                refreshPack(window, loadoutData[21], 2, compType2)
                refreshPack(window, loadoutData[22], 3, compType3)
                refreshPack(window, loadoutData[23], 4, compType4)
                refreshPack(window, loadoutData[24], 5, compType5)
                refreshPack(window, loadoutData[25], 6, compType6)
                refreshPack(window, loadoutData[26], 7, compType7)
                refreshPack(window, loadoutData[27], 8, compType8)

                window.refresh()
                
                loaded = True
                break

        if event == 'Edit':
            try:
                loadout = values['loadoutname'][0]
            except:
                loadout = ''
            if loadout == '':
                alert('Error',['Please select a loadout.'],['Okay'],0)
                remodalize(loadWindow)
            else:
                oldName = loadout
                newValues = createLoadout(loadout)
                if [loadWindow['data0'],loadWindow['data1'],loadWindow['data2']] != newValues and newValues != ['', '', '']:
                    slotText, statText = updateLoadoutPreview(newValues[0])
                    remodalize(loadWindow)
                    loadoutList = listify(cur2.execute("SELECT name FROM loadout ORDER BY name ASC").fetchall())
                    loadWindow['loadoutname'].update(values=loadoutList)
                    loadWindow['text0'].update("Loadout Name:")
                    loadWindow['data0'].update(newValues[0])
                    for i in range(1,20):
                        loadWindow['text' + str(i)].update(slotText[i-1])
                        if slotText[i-1] == 'Mass:':
                            loadWindow['data' + str(i)].update("{:.1f}".format(tryFloat(statText[i-1])))
                        else:
                            loadWindow['data' + str(i)].update(statText[i-1])
                    loadWindow['loadoutname'].update(set_to_index=loadoutList.index(newValues[0]))
                    loadWindow.refresh()
                    if window['loadoutname'].get() == oldName:
                        window['loadoutname'].update(newValues[0])
                        updateMassStrings(newValues[2], window)
                        window.refresh()

        if event == "Duplicate":
            try:
                selection = values['loadoutname'][0]
                dupeName = duplicateLoadout(selection)
                remodalize(loadWindow)
                loadoutList = listify(cur2.execute("SELECT name FROM loadout ORDER BY name ASC").fetchall())
                loadWindow['loadoutname'].update(values=loadoutList, set_to_index=loadoutList.index(dupeName))
                slotText, statText = updateLoadoutPreview(dupeName) #probably redundant to bother updating anything aside from the name but it could be futureproofing so why not.
                remodalize(loadWindow)
                loadWindow['text0'].update("Loadout Name:")
                loadWindow['data0'].update(dupeName)
                for i in range(1,20):
                    loadWindow['text' + str(i)].update(slotText[i-1])
                    if slotText[i-1] == 'Mass:':
                        loadWindow['data' + str(i)].update("{:.1f}".format(tryFloat(statText[i-1])))
                    else:
                        loadWindow['data' + str(i)].update(statText[i-1])
                loadWindow.refresh()
            except:
                alert('Error',['Error: Please select a chassis to duplicate.'],[],3)
                remodalize(loadWindow)

        if event == "Delete":
            try:
                loadout = values['loadoutname'][0]
            except:
                loadout = ''
            if loadout == '':
                alert('Error',['Please select a loadout.'],['Okay'],0)
                remodalize(loadWindow)
            else:
                currentLoadout = window['loadoutname'].get()
                result = alert('Alert',['You are attempting to delete the loadout named "' + values['loadoutname'][0] + '."','Are you sure? This action cannot be undone.'],['Yes', 'Cancel'],0)
                remodalize(loadWindow)
                if result == "Yes":
                    cur2.execute("DELETE FROM loadout WHERE name = ?", [values['loadoutname'][0]])
                    if values['loadoutname'][0] == currentLoadout:
                        clearLoadout(window,"all")
                        window.refresh()
                    loadoutList = listify(cur2.execute("SELECT name FROM loadout ORDER BY name ASC").fetchall())
                    loadWindow['loadoutname'].update(values=loadoutList)
                    for i in range(0,20):
                        loadWindow['text' + str(i)].update("")
                        loadWindow['data' + str(i)].update("")
                    loadWindow.refresh()

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    compdb.commit()
    loadWindow.close()

    return loadoutData[1], loadoutData[2], loaded

def saveLoadout(window, *saveAs):
    event, values = window.read(timeout=0)

    loadoutName = window['loadoutname'].get()

    loadout = list(cur2.execute("SELECT * FROM loadout WHERE name = ?", [loadoutName]).fetchall()[0])

    try:
        loadout[0] = saveAs[0]
    except:
        pass

    newLoadout = loadout[:3] + [
        values['frontarmorselection'], 
        values['reararmorselection'], 
        values['boosterselection'], 
        values['capselection'], 
        values['chselection'],  
        values['diselection'], 
        values['engineselection'], 
        values['reactorselection'], 
        values['shieldselection'],  
        values['slot1selection'], 
        values['slot2selection'], 
        values['slot3selection'], 
        values['slot4selection'], 
        values['slot5selection'], 
        values['slot6selection'], 
        values['slot7selection'], 
        values['slot8selection'], 
        values['slot1packselection'], 
        values['slot2packselection'], 
        values['slot3packselection'], 
        values['slot4packselection'], 
        values['slot5packselection'], 
        values['slot6packselection'], 
        values['slot7packselection'], 
        values['slot8packselection'], 
        values['reactoroverloadlevel'], 
        values['engineoverloadlevel'], 
        values['capacitoroverchargelevel'], 
        values['weaponoverloadlevel'], 
        values['shieldadjustsetting']
        ]
    
    cur2.execute("INSERT OR REPLACE INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", newLoadout)
    compdb.commit()

def saveLoadoutAs(window):

    loadoutList = [x[0] for x in cur2.execute('SELECT name FROM loadout').fetchall()]

    event, values = window.read(timeout=0)

    loadoutName = window['loadoutname'].get()
    
    Layout = [
        [sg.Push(),sg.Text('Save Loadout As',font=headerFont,p=elementPadding),sg.Push()],
        [sg.Text('',font=baseFont,p=fontPadding)],
        [sg.Push(),sg.Text('Loadout Name:',font=baseFont,p=fontPadding),sg.Input(default_text=loadoutName,key='name',font=baseFont,p=fontPadding,s=26),sg.Push()],
        [sg.Text('',font=baseFont,p=fontPadding)],
        [sg.Push(),sg.Button('Save',font=buttonFont),sg.Push(),sg.Button('Cancel',font=buttonFont),sg.Push()]
    ]

    saveAsWindow = sg.Window('Save Loadout As', Layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    saveAsWindow.bind('<Escape>', 'Cancel')

    newName = ''

    while True:
        event, values = saveAsWindow.read()

        if event == 'Save':
            newName = values['name']
            if newName not in loadoutList or newName == loadoutName:
                saveLoadout(window,newName)
                break
            elif newName in loadoutList and newName != loadoutName:
                result = alert('Alert',['A loadout with that name already exists. Do you wish to overwrite it?'],['Confirm','Cancel'],0)
                if result == 'Confirm':
                    saveLoadout(window,newName)
                    break
                else:
                    pass
            else:
                alert('Error',['An unknown error occurred. Contact me so I can look into it. -Seraph'],[],3)

        if event == sg.WIN_CLOSED or event == 'Cancel':
            break

    saveAsWindow.close()

    return newName

def ordnanceCheck(stats, compName):
    if compName == "Ordnance Launcher":
        if stats[2] == '':
            return False
        else:
            return True
    elif compName == "Ordnance Pack":
        if stats[3] == '':
            return False
        else:
            return True
    else:
        return True

def createComponent(componentName, *editArgs):

    lookup = cur.execute("SELECT * FROM component WHERE type = '" + componentName + "'").fetchall()[0]
    fullStats = cur.execute("SELECT stat1,stat2,stat3,stat4,stat5,stat6,stat7,stat8 FROM component").fetchall()
    fullStats = [list(x) for x in fullStats]
    fullStatsList = []
    for stats in fullStats:
        fullStatsList.extend([x for x in stats if x != ''])
    fullStatsList = set(fullStatsList)

    statColumn = []
    inputColumn = []

    try:   
        editArgs = editArgs[0]
        editingName = editArgs[0]
        editing = True  
    except:
        editing = False
        editingName = ''
        editArgs = [""] * 9

    for i in range(1, 9):
        if lookup[i] != '':
            if lookup[i] == 'Booster Energy Consumption Rate':
                statColumn.append([sg.Push(), sg.Text("Booster Energy Consumption:", font=baseFont)]) #Truncates this stat since it's the only one that's too long to fit
            else:
                statColumn.append([sg.Push(), sg.Text(lookup[i] + ":", font=baseFont)])
            if lookup[i] == "Type":
                ordnance = cur.execute("SELECT * FROM ordnance").fetchall()
                types = []
                for j in ordnance:
                    types.append(j[0])
                inputColumn.append([sg.Combo(values = types, s=(25,14), key="stat" + str(i), font=baseFont, readonly=True, default_value=editArgs[i])])
            else:
                inputColumn.append([sg.Input(s = 10, key="stat" + str(i), font=baseFont, default_text=editArgs[i])])

    statColumn.insert(0,[sg.Push(), sg.Text('Component Name:', font=baseFont)])

    inputColumn.insert(0,[sg.Input(key='name', font=baseFont, s=25, default_text=editArgs[0], disabled_readonly_background_color=boxColor)])

    if editing:
        statColumn.insert(0,[sg.Push(),sg.Text('Editing Component:',font=baseFont)])
        inputColumn.insert(0,[sg.Text(editingName,font=baseFont),sg.Push()])

    tessLines = [
        [sg.Push(),sg.Text('Tesseract OCR is Enabled   ',font=baseFont,p=0),sg.Button(' ? ',font=("Roboto",10,"bold"),p=0),sg.Push()],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('Use the Windows Snipping Tool (Win+Shift+S) to capture your',font=baseFont,p=0),sg.Push()],
        [sg.Push(),sg.Text('component stats, and Ctrl-V to paste them into this window.',font=baseFont,p=0),sg.Push(),],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('This feature is experimental, so double-check the stats before saving!',font=baseFont,p=0),sg.Push()],
    ]

    layout = [
        [sg.Push(),sg.Text('Input Component Stats', font=headerFont),sg.Push()],
        [sg.Push(),sg.Text(componentName,font=baseFont),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',statColumn,border_width=0,s=(200,275)), sg.Frame('',inputColumn,border_width=0,s=(200,275))],
        [sg.VPush()],
        [sg.Push(),sg.Button("Save", font=buttonFont, bind_return_key=True), sg.Button("Cancel", font=buttonFont),sg.Push()]
    ]

    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), "tesseract"))):
        layout.insert(4,tessLines)
        winSize = tuple([450,525])
    else:
        winSize = tuple([450,475])

    addComponentWindow = sg.Window('Create Component',layout, modal=True, finalize=True, size=winSize, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    addComponentWindow['name'].set_focus()
    addComponentWindow.bind('<Escape>', 'Cancel')
    addComponentWindow.bind('<Control-v>', 'pastecompstats')

    compUpdate = False
    newName = ''

    while True:
        event, values = addComponentWindow.read()

        if event == ' ? ':
            tessPopup = alert('Tesseract',["Tesseract OCR (optical character recognition) is an open-source engine that can identify text in an image and turn it into something that is machine-readable.","By combining this functionality with the snipping tool (Win-Shift-S), you can now capture your component stats directly from SWG without having to manually input everything.","","While it is mostly accurate, it still occasionally mixes up some numbers that look similar (3, 8, 0 in particular). Always double-check for accuracy when using this feature.",""],['Show Example','Close'],0)
            if tessPopup == 'Show Example':
                popImage('Tesseract Example',os.path.abspath(os.path.join(os.path.dirname(__file__), 'tessdemo.png')))
                
        if event == 'pastecompstats' and getImageFromClipboard() != None and os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), "tesseract"))):
            try:
                textLines = processImage()
                textLines = [x for x in textLines if 'Type' not in x]
                textStats = []
                textValues = []
                for i in range(0,len(textLines)):
                    if textLines[i] != '':
                        try:
                            float(textLines[i])
                            tester = True
                        except:
                            tester = False
                        if textLines[i][0] == ':':
                            textLines[i-1] += textLines[i]
                        elif tester: #covers weird case where parts loaded in ships might have stat text and value separated with line 2 beginning with a colon (or number if the colon gets chopped off)
                            textLines[i-1] += ': ' + textLines[i]
                for line in textLines:
                    if ':' not in line:
                        pass
                    else:
                        textStats.append(line.split(':')[0])
                        try: #prevents it from failing when non-stat lines with colons are captured (e.g. ship equipment certification)
                            value = line.split(': ')[1]
                        except:
                            value = ''
                        if ' ' in value:
                            value = value.split(' ')[0]
                        if '/' in value:
                            value = value.split('/')[1]
                        textValues.append(value)
                for i in range(0,len(textValues)):
                    if textValues[i] != '':
                        try:
                            try:
                                textValues[i] = float(textValues[i])
                            except:
                                entry = str(textValues[i])
                                j = 1
                                maxLength = len(entry)
                                while j < maxLength:
                                    try:
                                        float(entry[0:j])
                                        j += 1
                                    except:
                                        entry = entry.replace(entry[j-1],'')
                                        maxLength -= 1
                                try:
                                    textValues[i] = float(entry)
                                except:
                                    pass
                        except:
                            pass
                partStats = list(lookup[1:9]) + ['Damage Modifier Against NPCs'] #adds this for ordnance ID to be removed later
                #go over textStats and attempt to align the strings to the actual stat names using jellyfish
                for i in range(0,len(textStats)):
                    textStats[i] = textStats[i].replace('*','').replace('^','') #removes any extraneous carats and asterisks which can cause trouble down the line
                    for j in partStats:
                        if textStats[i] != '' and j != '':
                            if jellyfish.damerau_levenshtein_distance(textStats[i],j)/len(j) <= 0.25 and j not in textStats:
                                textStats[i] = j
                                break
                            elif jellyfish.damerau_levenshtein_distance(textStats[i],'Damage - Maximum')/16 <= 0.25 or jellyfish.damerau_levenshtein_distance(textStats[i],'Damage - Minimum')/16 <= 0.25: #If it looks like either of these, get finer since the distinction between the two is small
                                if 'Minimum Damage' not in textStats and jellyfish.damerau_levenshtein_distance(textStats[i],'Damage - Minimum')/16 <= 0.0625:
                                    textStats[i] = 'Minimum Damage'
                                    break
                                elif 'Maximum Damage' not in textStats and jellyfish.damerau_levenshtein_distance(textStats[i],'Damage - Maximum')/16 <= 0.0625:
                                    textStats[i] = 'Maximum Damage'
                                    break
                    if jellyfish.damerau_levenshtein_distance(textStats[i],'Ammo') <= 1: #Little extra translation since it's ammo in-game
                        textStats.append('Ammunition')
                        textValues.append(textValues[i])
                for i in textStats:
                    if i in fullStatsList and i not in partStats and componentName not in ['Ordnance Launcher','Ordnance Pack']:
                        alert("Alert",["You appear to have pasted stats from a different component type than the one selected."],[],3)
                        break
                if componentName in ['Ordnance Launcher','Ordnance Pack']:
                    ordnanceData = cur.execute("SELECT * FROM ordnance").fetchall()
                    massValue = 0
                    maxDam = 0
                    vssValue = 0
                    vsaValue = 0
                    refireValue = 0
                    pvemultValue = 0
                    if 'Mass' in textStats:
                        massValue = tryFloat(textValues[textStats.index('Mass')])
                    if 'Damage - Maximum' in textStats:
                        maxDam = tryFloat(textValues[textStats.index('Damage - Maximum')])
                    elif 'Maximum Damage' in textStats:
                        maxDam = tryFloat(textValues[textStats.index('Maximum Damage')])
                    if 'Vs. Shields' in textStats:
                        vssValue = tryFloat(textValues[textStats.index('Vs. Shields')])
                    elif 'Shield Effectiveness' in textStats:
                        vssValue = tryFloat(textValues[textStats.index('Shield Effectiveness')])
                    if 'Vs. Armor' in textStats:
                        vsaValue = tryFloat(textValues[textStats.index('Vs. Armor')])
                    elif 'Armor Effectiveness' in textStats:
                        vsaValue = tryFloat(textValues[textStats.index('Armor Effectiveness')])
                    if 'Refire Rate' in textStats:
                        refireValue = tryFloat(textValues[textStats.index('Refire Rate')])
                    if 'Damage Modifier Against NPCs' in textStats:
                        pvemultValue = tryFloat(textValues[textStats.index('Damage Modifier Against NPCs')])
                    if not (maxDam == 0 and massValue == 0) and not (vssValue == 0 and vsaValue == 0):
                        ordnanceData = cur.execute("SELECT * FROM ordnance").fetchall()
                        if refireValue == 0.5:
                            for i in ordnanceData:
                                if massValue >= tryFloat(i[4]) and massValue <= tryFloat(i[5]) and pvemultValue == tryFloat(i[1]):
                                    textStats.append('Type')
                                    textValues.append(i[0])
                                    break
                        else:
                            ordTypeGuess = '' #While possible, I'm kinda just hoping it doesn't guess two different ordnance types here. If it does, it'll just use the second one for the time being. I don't really wanna have to come up with a priority system.
                            if massValue > 0:
                                for i in ordnanceData:
                                    if vssValue == tryFloat(i[2]) and vsaValue == tryFloat(i[3]) and massValue >= tryFloat(i[4]) and massValue <= tryFloat(i[5]):
                                        ordTypeGuess = i[0]
                                        break
                            if maxDam > 0:
                                for i in ordnanceData:
                                    if vssValue == tryFloat(i[2]) and vsaValue == tryFloat(i[3]) and maxDam >= tryFloat(i[6]) and maxDam <= tryFloat(i[7]):
                                        ordTypeGuess = i[0]
                                        break
                            if ordTypeGuess != '':
                                textStats.append('Type')
                                textValues.append(ordTypeGuess)

                partStats = lookup[1:9] #removes the entry added for ordnance ID

                try:
                    armorValue = float(textValues[textStats.index('Armor')])
                except:
                    armorValue = 0
                try:
                    hpValue = float(textValues[textStats.index('Hitpoints')])
                except:
                    hpValue = 0

                ahpValue = max(armorValue,hpValue)
                textStats.append('Armor/Hitpoints')
                textValues.append(str(ahpValue))

                try:
                    fshpValue = float(textValues[textStats.index('Front Shield Hitpoints')])
                except:
                    fshpValue = 0
                try:
                    bshpValue = float(textValues[textStats.index('Back Shield Hitpoints')])
                except:
                    bshpValue = 0
                
                shpValue = max(fshpValue,bshpValue)
                textStats.append('Shield Hitpoints')
                textValues.append(str(shpValue))
                for i in range(0,len(partStats)):
                    for j in [x for x in textStats if x != '']:
                        if j == partStats[i]:
                            addComponentWindow['stat' + str(i+1)].update(value=textValues[textStats.index(j)])
            except:
                alert("Error",['Unable to perform stat grab operation.','Try getting a better screencapture using the snipping tool.','(Win + Shift + S)'],[],3)
                remodalize(addComponentWindow)

        if event == "Save":
            stats = []
            for i in range(1, 9):
                try:
                    stats.append(float(values['stat' + str(i)]))
                except:
                    try:
                        stats.append(values['stat' + str(i)])
                    except:
                        pass

            statsReduced = [x for x in stats if x != '' and x != 0]

            try:
                weaponList = cur2.execute("SELECT name FROM weapon").fetchall()[0]
            except:
                weaponList = []
            try:
                ordList = cur2.execute("SELECT name FROM ordnancelauncher").fetchall()[0]
            except:
                ordList = []
            try:
                cmList = cur2.execute("SELECT name FROM countermeasurelauncher").fetchall()[0]
            except:
                cmList = []

            if editing:
                diff = 2
            else:
                diff = 1

            if values['name'] == "":
                alert("Error",["Error: You must enter a name for this component."],[],3)
                remodalize(addComponentWindow)
            elif componentName == "Weapon" and (values['name'] in ordList or values['name'] in cmList):
                alert("Error",["Error: This name is already in use for an ordnance launcher or countermeasure launcher. Please use a different name."],[],3)
                remodalize(addComponentWindow)
            elif componentName == "Ordnance Launcher" and (values['name'] in weaponList or values['name'] in cmList):
                alert("Error",["Error: This name is already in use for a weapon or countermeasure launcher. Please use a different name."],[],3)
                remodalize(addComponentWindow)
            elif componentName == "Countermeasure Launcher" and (values['name'] in weaponList or values['name'] in ordList):
                alert("Error",["Error: This name is already in use for a weapon or ordnance launcher. Please use a different name."],[],3)
                remodalize(addComponentWindow)
            elif ordnanceCheck(stats, componentName) == False:
                alert("Error",["Error: You must select an ordnance type."],[],3)
                remodalize(addComponentWindow)
            elif len(statsReduced) < len(inputColumn)-diff:
                alert("Error",["Error: You must enter a non-zero numerical value for every stat."],[],3)
                remodalize(addComponentWindow)
            else:
                bindings = ""
                stats.insert(0, values['name'])
                statString = ""
                for i in range(0, len(stats)):
                    bindings += "?, "
                    if i > 0:
                        statString += lookup[i].lower().replace(" ","").replace("/","").replace(".","") + ", "
                bindings = bindings[:-2]
                statString = "name, " + statString[:-2]
                compName = componentName.lower().replace(" ","").replace("/","").replace(".","")

                if editing:
                    decision = alert("Alert",["You are about to overwrite your part with the new stats entered below. Do you wish to continue?"],['Proceed', 'Cancel'],0)
                    remodalize(addComponentWindow)
                    if decision == "Proceed":
                        decision2 = "Proceed"
                        sameName = cur2.execute('SELECT * FROM ' + compName + ' WHERE name = ?', [stats[0]]).fetchall()
                        if sameName != [] and stats[0] != editArgs[0]:
                            decision2 = alert("Alert",["A part with this name already exists. Do you wish to overwrite it?"],['Proceed', 'Cancel'],0)
                            remodalize(addComponentWindow)
                            if decision == "Proceed" and decision2 == "Proceed":
                                cur2.execute("DELETE FROM " + compName + " WHERE name = ?", [editArgs[0]])
                                cur2.execute("INSERT OR REPLACE INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                                if compName == 'armor':
                                    slots = ['armor1','armor2']
                                elif compName in ['weapon', 'ordnancelauncher', 'countermeasurelauncher']:
                                    slots = ['slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8']
                                elif compName in ['ordnancepack', 'countermeasurepack']:
                                    slots = ['pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                                else:
                                    slots = [compName]
                                for i in slots:
                                    #escape apostrophes and quotes so they don't break the db call
                                    cur2.execute('UPDATE loadout SET ' + i + ' = "' + stats[0].replace("'","''").replace('"','""') + '" WHERE ' + i + ' = ?', [editArgs[0]])
                                compUpdate = True
                                newName = stats[0]
                                break
                        else:
                            cur2.execute("DELETE FROM " + compName + " WHERE name = ?", [editArgs[0]])
                            cur2.execute("INSERT INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                            if compName == 'armor':
                                slots = ['armor1','armor2']
                            elif compName in ['weapon', 'ordnancelauncher', 'countermeasurelauncher']:
                                slots = ['slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8']
                            elif compName in ['ordnancepack', 'countermeasurepack']:
                                slots = ['pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                            else:
                                slots = [compName]
                            for i in slots:
                                cur2.execute('UPDATE loadout SET ' + i + ' = "' + stats[0].replace("'","''").replace('"','""') + '" WHERE ' + i + ' = ?', [editArgs[0]])
                            compUpdate = True
                            newName = stats[0]
                            break
                else:
                    try:
                        cur2.execute("INSERT INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                        newName = stats[0]
                        compUpdate = True
                        break
                    except:
                        decision = alert("Alert",["A part with this name already exists. Do you wish to overwrite it?"],['Proceed', 'Cancel'],0)
                        remodalize(addComponentWindow)
                        if decision == "Proceed":
                            try:
                                cur2.execute("INSERT OR REPLACE INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                                newName = stats[0]
                                compUpdate = True
                            except:
                                alert('Error',['Error: An unknown issue occurred when attempting to save this component. Make a post on my Discord detailing what happened so I can investigate.','-Seraph'],[],10)
                                remodalize(addComponentWindow)
                            break

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            addComponentWindow.close()
            try:
                editArgs[0]
            except:
                pass
            break

    compdb.commit()
    addComponentWindow.close()
    return compUpdate, newName

def getComponentStats():

    components = listify(cur.execute("SELECT type FROM component").fetchall())
    componentArray = []
    componentNames = []
    for i in components:
        i = i.lower().replace(" ", "").replace("/", "").replace(".", "")
        componentArray.append(cur2.execute("SELECT * FROM " + i + " ORDER BY name ASC").fetchall())
        componentNames.append(listify(componentArray[-1]))

    return components, componentNames, componentArray

def updateStatPreview(componentWindow, values):

    [components, componentNames, componentArray] = getComponentStats()

    componentName = values['complistbox'][0]
    componentType = values['comptypeselect'][0]
    partList = componentNames[components.index(componentType)]
    index1 = components.index(componentType)
    index2 = partList.index(componentName)
    componentWindow['partname'].update(componentName)
    componentWindow['parttype'].update(componentType)
    statList = list(cur.execute("SELECT * FROM component WHERE type = ?", [componentType]).fetchall()[0][17:35])
    statValues = componentArray[index1][index2][1:]
    for i in range(1, 9):
        try:
            componentWindow['stat' + str(i) + 'text'].update(statList[i-1])
            if statList[i-1] in ["Vs. Shields:", "Vs. Armor:", "Refire Rate:"]:
                componentWindow['stat' + str(i)].update("{:.3f}".format(tryFloat(statValues[i-1])))
            elif statList[i-1] == "Recharge:" and componentType == "Shield":
                componentWindow['stat' + str(i)].update("{:.2f}".format(tryFloat(statValues[i-1])))
            elif statList[i-1] == "Ammo:":
                componentWindow['stat' + str(i)].update(int(tryFloat(statValues[i-1])))
            else:
                componentWindow['stat' + str(i)].update(statValues[i-1])
        except:
            pass
    if componentType == "Shield":
        event, values = componentWindow.read(timeout = 0)
        componentWindow['stat5'].update(componentWindow['stat4'].get())
        componentWindow['stat4'].update(componentWindow['stat3'].get())

    entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
    loadoutList = ""
    for i in entries:
        loadouts = cur2.execute("SELECT name FROM loadout WHERE " + i + "= ?", [componentName]).fetchall()
        for j in loadouts:
            if j[0] not in loadoutList:
                loadoutList += j[0] + "\n"
    componentWindow['loadoutlist'].update(loadoutList)

    componentWindow.refresh()

    return componentType, statValues

def clearStatPreview(componentWindow):
    componentWindow['parttype'].update("")
    componentWindow['partname'].update("")
    for i in range(1, 9):
        componentWindow['stat' + str(i) + 'text'].update("")
        componentWindow['stat' + str(i)].update("")
    componentWindow['loadoutlist'].update("")
    componentWindow.refresh()

def componentLibrary():
    sg.theme('Discord_Dark')

    compLib = [list(x) for x in cur.execute("SELECT * FROM complib").fetchall()]

    components = [x[0] for x in cur.execute('SELECT type FROM component').fetchall()]
    componentStats = [list(x) for x in cur.execute('SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component').fetchall()]

    leftColumn = [
        [sg.Push(),sg.Text("Select Component Type", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=components, size=(24, 13), enable_events=True, key='comptypeselect', justification='center', no_scrollbar=True, font=baseFont, select_mode="single")],
        [sg.VPush()],
    ]
    centerColumn = [
        [sg.Push(),sg.Text("Select Component", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=[], key='complistbox', size=(40,13), font=baseFont, enable_events=True, select_mode='extended')],
        [sg.VPush()],
    ]

    statPreviewText = [
        [sg.Push(),sg.Text("",font=baseFont,key='stat1text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat2text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat3text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat4text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat5text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat6text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat7text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat8text', p=fontPadding, justification='right')],
    ]

    statPreviewStats = [
        [sg.Text("",font=baseFont,key='stat1', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat2', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat3', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat4', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat5', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat6', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat7', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat8', p=fontPadding)],
    ]

    statFrame = [
        [sg.Push(),sg.Text("",font=baseFont,key='parttype'), sg.Push()],
        [sg.Frame('', statPreviewText, border_width=0, s=(110,250), p=elementPadding),sg.Frame('', statPreviewStats, border_width=0, s=(134,250), p=elementPadding)]
    ]

    rightCenterColumn = [
        [sg.Push(),sg.Text("Stat Preview", font=baseFont), sg.Push()],
        [sg.VPush()],
        [sg.Frame('', statFrame, border_width=0, s=(235,250))],
        [sg.VPush()]
    ]

    Layout = [
        [sg.Push(), sg.Text("Component Library", font=headerFont), sg.Push()],
        [sg.vtop(sg.Frame('',leftColumn, border_width=0,p=elementPadding,s=(200,250),element_justification='center')), sg.vtop(sg.Frame('',centerColumn, border_width=0,p=elementPadding,s=(300,250),element_justification='center')), sg.vtop(sg.Frame('',rightCenterColumn, border_width=0,p=elementPadding,s=(250,250),element_justification='center'))],
        [sg.VPush()],
        [sg.Push(),sg.Push(),sg.Button("Add Selected Components",font=buttonFont),sg.Push(),sg.Button("Exit",font=buttonFont),sg.Push(),sg.Push()],
        [sg.VPush()]
    ]

    compLibWindow = sg.Window('Component Library', Layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    compLibWindow.bind('<Escape>', 'Exit')

    compSelectBuffer = []

    while True:
        event, values = compLibWindow.read()

        if event == 'comptypeselect':
            selectedCompType = values['comptypeselect'][0]
            compType = values['comptypeselect'][0].lower().replace(" ","").replace("/","").replace(".","")
            inUseList = [x[2:] for x in [y[0] for y in cur2.execute("SELECT name FROM " + compType).fetchall()] if '¤' in x]
            compList = [x[1] for x in compLib if x[0] == selectedCompType and x[1] not in inUseList]
            compLibWindow['complistbox'].update(compList)
            compSelectBuffer = []

        if event == 'complistbox':
            try:
                selections = [compList.index(x) for x in values['complistbox']]
                newSelections = [x for x in selections if x not in compSelectBuffer]
                if newSelections != [] and compSelectBuffer != [] and any([x for x in selections if x in compSelectBuffer]):
                    if min(newSelections) < min(compSelectBuffer):
                        compSelectBuffer = compSelectBuffer + newSelections[::-1]
                    else:
                        compSelectBuffer = compSelectBuffer + newSelections
                elif compSelectBuffer != []:
                    if len(compSelectBuffer) == 1 and len(selections) == 1 and compSelectBuffer != selections:
                        compSelectBuffer = selections
                    elif len(selections) == 1 and selections[0] not in compSelectBuffer:
                        compSelectBuffer = selections
                    elif min(selections) < min(compSelectBuffer) and compSelectBuffer != []:
                        compSelectBuffer = [x for x in compSelectBuffer if x in selections][::-1]
                    else:
                        compSelectBuffer = [x for x in compSelectBuffer if x in selections]                
                else:
                    compSelectBuffer = selections

                selectedComp = compSelectBuffer[-1]
                compName = compList[selectedComp]
                compStatNames = componentStats[components.index(values['comptypeselect'][0])]
                compLibWindow['parttype'].update(compName)
                compStats = [tryFloatRetainPrecision(x) if tryFloat(x) > 0  else x for x in [x[2:] for x in compLib if x[1] == compName][0]]
                for i in range(1,9):
                    try:
                        compLibWindow['stat' + str(i) + 'text'].update(compStatNames[i-1])
                        if compStats[i-1] not in [0, '']:
                            if compStatNames[i-1] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
                                statValue = '{:.3f}'.format(tryFloat(compStats[i-1]))
                            elif compStatNames[i-1] == 'Ammo:':
                                statValue = int(tryFloat(compStats[i-1]))
                            elif compStatNames[i-1] == 'Type:':
                                statValue = compStats[i-1]
                            else:
                                statValue = '{:.1f}'.format(tryFloat(compStats[i-1]))
                        else:
                            statValue = ''
                        compLibWindow['stat' + str(i)].update(statValue)
                    except:
                        pass

                if values['comptypeselect'][0] == 'Shield':
                    compLibWindow['stat4'].update(compStats[2])
                    compLibWindow['stat5'].update('{:.2f}'.format(tryFloat(compStats[3])))
            except:
                pass

        if event == 'Add Selected Components':
            compType = values['comptypeselect'][0].lower().replace(" ","").replace("/","").replace(".","")
            compList = values['complistbox']
            compStatNames = [x.lower().replace(" ", "").replace("/", "").replace(".", "") for x in cur.execute('SELECT * FROM component WHERE type = ?',values['comptypeselect']).fetchall()[0][1:] if (x != '' and len(x) > 2 and ':' not in x)]
            bindings = ('?, ' * (len(compStatNames)+1))[:-2]
            statString = 'name, '
            for i in compStatNames:
                statString += i + ', '
            statString = statString[:-2]
            addList = [[y for y in x[1:] if y != ''] for x in compLib if x[1] in compList]
            for i in range(len(addList)):
                addList[i][0] = '¤ ' + addList[i][0]
            cur2.executemany("INSERT OR REPLACE INTO " + compType + "(" + statString + ") VALUES(" + bindings + ")", addList)
            compdb.commit()

            inUseList = [x[2:] for x in [y[0] for y in cur2.execute("SELECT name FROM " + compType).fetchall()] if '¤' in x]
            compList = [x[1] for x in compLib if x[0] == selectedCompType and x[1] not in inUseList]
            compLibWindow['complistbox'].update(compList)

        if event == "Exit" or event == sg.WIN_CLOSED:
            break
    
    compLibWindow.close()

def manageComponents():
    sg.theme('Discord_Dark')

    [components, componentNames, componentArray] = getComponentStats()

    leftColumn = [
        [sg.Push(),sg.Text("Select Component Type", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=components, size=(24, 13), enable_events=True, key='comptypeselect', justification='center', no_scrollbar=True, font=baseFont, select_mode="single")],
        [sg.VPush()],
    ]
    centerColumn = [
        [sg.Push(),sg.Text("Select Component", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=[], key='complistbox', size=(40,13), font=baseFont, enable_events=True, select_mode='extended')], #extended select mode allows for selecting multiple items with ctrl/shift as in windows explorer
        [sg.VPush()],
    ]

    statPreviewText = [
        [sg.Push(),sg.Text("",font=baseFont,key='stat1text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat2text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat3text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat4text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat5text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat6text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat7text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat8text', p=fontPadding, justification='right')],
    ]

    statPreviewStats = [
        [sg.Text("",font=baseFont,key='stat1', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat2', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat3', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat4', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat5', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat6', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat7', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat8', p=fontPadding)],
    ]

    statFrame = [
        [sg.Push(),sg.Text("",font=baseFont,key='partname',p=fontPadding), sg.Push()],
        [sg.Push(),sg.Text("",font=baseFont,key='parttype',p=fontPadding), sg.Push()],
        [sg.VPush()],
        [sg.Frame('', statPreviewText, border_width=0, s=(110,250), p=elementPadding),sg.Frame('', statPreviewStats, border_width=0, s=(134,250), p=elementPadding)]
    ]

    rightCenterColumn = [
        [sg.Push(),sg.Text("Stat Preview", font=baseFont), sg.Push()],
        [sg.VPush()],
        [sg.Frame('', statFrame, border_width=0, s=(235,250))],
        [sg.VPush()]
    ]

    loadoutColumn = [
        [sg.Push(), sg.Text("Used in These Loadouts", font=baseFont), sg.Push()],
        [sg.VPush()],
        [sg.Frame('',[[sg.Push(),sg.Text("", font=baseFont, key='loadoutlist', justification='center'),sg.Push()]],border_width=0,p=elementPadding,size=(225,250))],
        [sg.VPush()]
    ]

    Layout = [
        [sg.Push(), sg.Text("Manage Components", font=headerFont), sg.Push()],
        [sg.vtop(sg.Frame('',leftColumn, border_width=0,p=elementPadding,s=(200,250),element_justification='center')), sg.vtop(sg.Frame('',centerColumn, border_width=0,p=elementPadding,s=(300,250),element_justification='center')), sg.vtop(sg.Frame('',rightCenterColumn, border_width=0,p=elementPadding,s=(250,250),element_justification='center')),sg.vtop(sg.Frame('',loadoutColumn, border_width=0,p=elementPadding,s=(225,250),element_justification='center'))],
        [sg.VPush()],
        [sg.Push(),sg.Push(),sg.Button("Add New",font=buttonFont),sg.Push(),sg.Button("Add from Library",font=buttonFont),sg.Push(),sg.Button("Edit",font=buttonFont),sg.Push(),sg.Button("Delete",font=buttonFont),sg.Push(),sg.Button("Exit",font=buttonFont),sg.Push(),sg.Push()],
        [sg.VPush()]
    ]

    componentWindow = sg.Window('Manage Components', Layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    componentWindow.bind('<Escape>', 'Exit')

    modified = False
    compSelectBuffer = []

    [components, componentNames, componentArray] = getComponentStats()

    while True:
        event, values = componentWindow.read()
        if event == 'comptypeselect':
            partList = componentNames[components.index(values['comptypeselect'][0])]
            componentWindow['complistbox'].update(values=partList)
            compSelectBuffer = []
            clearStatPreview(componentWindow)

        if event == 'complistbox':
            try:
                componentType = values['comptypeselect'][0]
                selections = [partList.index(x) for x in values['complistbox']]
                newSelections = [x for x in selections if x not in compSelectBuffer]
                if newSelections != [] and compSelectBuffer != [] and any([x for x in selections if x in compSelectBuffer]):
                    if min(newSelections) < min(compSelectBuffer):
                        compSelectBuffer = compSelectBuffer + newSelections[::-1]
                    else:
                        compSelectBuffer = compSelectBuffer + newSelections
                elif compSelectBuffer != []:
                    if len(compSelectBuffer) == 1 and len(selections) == 1 and compSelectBuffer != selections:
                        compSelectBuffer = selections
                    elif len(selections) == 1 and selections[0] not in compSelectBuffer:
                        compSelectBuffer = selections
                    elif min(selections) < min(compSelectBuffer) and compSelectBuffer != []:
                        compSelectBuffer = [x for x in compSelectBuffer if x in selections][::-1]
                    else:
                        compSelectBuffer = [x for x in compSelectBuffer if x in selections]                
                else:
                    compSelectBuffer = selections

                selectedComp = compSelectBuffer[-1]
                compName = partList[selectedComp]

                index1 = components.index(componentType)
                index2 = partList.index(compName)
                componentWindow['partname'].update(compName)
                componentWindow['parttype'].update(componentType)
                statList = list(cur.execute("SELECT * FROM component WHERE type = ?", [componentType]).fetchall()[0][17:35])
                statValues = componentArray[index1][index2][1:]

                for i in range(1,9):
                    try:
                        componentWindow['stat' + str(i) + 'text'].update(statList[i-1])
                        if statList[i-1] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
                            statValue = '{:.3f}'.format(tryFloat(statValues[i-1]))
                        elif statList[i-1] == 'Ammo:':
                            statValue = int(tryFloat(statValues[i-1]))
                        elif statList[i-1] == 'Type:':
                            statValue = statValues[i-1]
                        else:
                            statValue = '{:.1f}'.format(tryFloat(statValues[i-1]))
                        componentWindow['stat' + str(i)].update(statValue)
                    except:
                        pass

                if values['comptypeselect'][0] == 'Shield':
                    componentWindow['stat4'].update(statValues[2])
                    componentWindow['stat5'].update('{:.2f}'.format(tryFloat(statValues[3])))

                entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                loadoutList = ""
                for i in entries:
                    loadouts = cur2.execute("SELECT name FROM loadout WHERE " + i + "= ?", [compName]).fetchall()
                    for j in loadouts:
                        if j[0] not in loadoutList:
                            loadoutList += j[0] + "\n"
                componentWindow['loadoutlist'].update(loadoutList)
            except:
                pass

        if event == "Add New":
            try:
                lastSelection = componentWindow['partname'].get()
                modified, newName = createComponent(values['comptypeselect'][0])
                [components, componentNames, componentArray] = getComponentStats()
                partList = componentNames[components.index(values['comptypeselect'][0])]
                componentWindow['complistbox'].update(partList)
                if modified:
                    componentWindow['complistbox'].set_value(newName)
                else:
                    try:
                        componentWindow['complistbox'].set_value(lastSelection)
                    except:
                        pass
                event, values = componentWindow.read(timeout=0)
                if values['complistbox'] != []:
                    updateStatPreview(componentWindow, values)
            except:
                 alert('Error',['Error: Please select a component type.'],[],3)
            remodalize(componentWindow)
        
        if event == "Add from Library":
            lastSelection = componentWindow['partname'].get()
            componentLibrary()
            remodalize(componentWindow)
            [components, componentNames, componentArray] = getComponentStats() 
            try:
                partList = componentNames[components.index(values['comptypeselect'][0])]
                componentWindow['complistbox'].update(partList)
            except:
                pass
            try:
                componentWindow['complistbox'].set_value(lastSelection)
            except:
                pass

        if event == "Edit":
            if len(values['complistbox']) > 1:
                alert('Error',['Error: You may only edit one component at a time.'],[],3)
            elif len(values['complistbox']) == 0:
                alert('Error',['Error: Please select a component to edit.'],[],3)
            elif '¤' in values['complistbox'][0]:
                alert('Error',['Error: You cannot edit library components.'],[],3)
            else:
                try:
                    [componentType, statValues] = updateStatPreview(componentWindow, values)
                    try: 
                        event, values = componentWindow.read(timeout=0)
                        editArgs = [componentWindow['partname'].get(),componentWindow['stat1'].get(),componentWindow['stat2'].get(),componentWindow['stat3'].get(),componentWindow['stat4'].get(),componentWindow['stat5'].get(), componentWindow['stat6'].get(),componentWindow['stat7'].get(),componentWindow['stat8'].get()]
                        if componentType == 'Shield':
                            editArgs[4] = editArgs[5]
                            editArgs[5] = ''
                        modified, newName = createComponent(componentType, editArgs)
                        [components, componentNames, componentArray] = getComponentStats() 
                        partList = componentNames[components.index(values['comptypeselect'][0])]
                        componentWindow['complistbox'].update(partList)
                        componentWindow['complistbox'].set_value(newName)
                        event, values = componentWindow.read(timeout=0)
                        updateStatPreview(componentWindow, values)
                    except:
                        pass
                except:
                    alert('Error',['Error: Please select a component to edit.'],[],3)
            remodalize(componentWindow)

        if event == "Delete":
            event, values = componentWindow.read(timeout=0)
            componentType = componentWindow['parttype'].get()
            if len(values['complistbox']) == 1:
                try:
                    componentName = values['complistbox'][0]
                    if '¤' not in componentName:
                        result = alert('Alert',["You are about to delete the component named '" + componentName + ".'",'This cannot be undone. Do you wish to proceed?'],['Proceed','Cancel'],0)
                        remodalize(componentWindow)
                    else:
                        result = 'Proceed'
                    if result == "Proceed":
                        componentType = componentType.lower().replace(" ","").replace("/","").replace(".","")
                        cur2.execute("DELETE FROM " + componentType + " WHERE name = ?", [componentName])
                        if componentType == 'ordnancepack' or componentType == 'countermeasurepack':
                            for i in range(1, 9):
                                cur2.execute("UPDATE loadout SET pack" + str(i) + " = '' WHERE pack" + str(i) + " = ?", [componentName])
                        elif componentType == 'ordnancelauncher' or componentType == 'countermeasurelauncher' or componentType == 'weapon':
                            for i in range(1, 9):
                                cur2.execute("UPDATE loadout SET pack" + str(i) + " = '' WHERE slot" + str(i) + " = ?", [componentName])
                                cur2.execute("UPDATE loadout SET slot" + str(i) + " = '' WHERE slot" + str(i) + " = ?", [componentName])
                        else:
                            entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                            for i in entries:    
                                cur2.execute("UPDATE loadout SET " + i + " = '' WHERE " + i + " = ?", [componentName])
                    compdb.commit()

                    [components, componentNames, componentArray] = getComponentStats() 
                    partList = componentNames[components.index(values['comptypeselect'][0])]
                    componentWindow['complistbox'].update(values=partList)
                    clearStatPreview(componentWindow)
                    modified = True
                except:
                    pass
            elif len(values['complistbox']) > 1:
                try:
                    compNames = values['complistbox']
                    if any(['¤' not in x for x in compNames]):
                        result = alert('Alert',['You are about to delete ALL of the selected components.','This cannot be undone. Do you wish to proceed?'],['Proceed','Cancel'],0)
                        remodalize(componentWindow)
                    else:
                        result = 'Proceed'
                    if result == "Proceed":
                        componentType = componentType.lower().replace(" ","").replace("/","").replace(".","")
                        for componentName in compNames:
                            cur2.execute("DELETE FROM " + componentType + " WHERE name = ?", [componentName])
                            if componentType == 'ordnancepack' or componentType == 'countermeasurepack':
                                for i in range(1, 9):
                                    cur2.execute("UPDATE loadout SET pack" + str(i) + " = '' WHERE pack" + str(i) + " = ?", [componentName])
                            elif componentType == 'ordnancelauncher' or componentType == 'countermeasurelauncher' or componentType == 'weapon':
                                for i in range(1, 9):
                                    cur2.execute("UPDATE loadout SET pack" + str(i) + " = '' WHERE slot" + str(i) + " = ?", [componentName])
                                    cur2.execute("UPDATE loadout SET slot" + str(i) + " = '' WHERE slot" + str(i) + " = ?", [componentName])
                            else:
                                entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                                for i in entries:    
                                    cur2.execute("UPDATE loadout SET " + i + " = '' WHERE " + i + " = ?", [componentName])
                    compdb.commit()

                    [components, componentNames, componentArray] = getComponentStats()
                    partList = componentNames[components.index(values['comptypeselect'][0])]
                    componentWindow['complistbox'].update(values=partList)
                    clearStatPreview(componentWindow)
                    modified = True
                except:
                    pass

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    componentWindow.close()
    return modified

def doExitSave(window):
    event, values = window.read(timeout=0)

    chassis = window['loadoutname'].get()

    try:
        loadout = list(cur2.execute("SELECT * FROM loadout WHERE name = ?", [chassis]).fetchall()[0])
        exitSave = loadout[:3] + [
            values['frontarmorselection'], 
            values['reararmorselection'], 
            values['boosterselection'], 
            values['capselection'], 
            values['chselection'],  
            values['diselection'], 
            values['engineselection'], 
            values['reactorselection'], 
            values['shieldselection'],  
            values['slot1selection'], 
            values['slot2selection'], 
            values['slot3selection'], 
            values['slot4selection'], 
            values['slot5selection'], 
            values['slot6selection'], 
            values['slot7selection'], 
            values['slot8selection'], 
            values['slot1packselection'], 
            values['slot2packselection'], 
            values['slot3packselection'], 
            values['slot4packselection'], 
            values['slot5packselection'], 
            values['slot6packselection'], 
            values['slot7packselection'], 
            values['slot8packselection'], 
            values['reactoroverloadlevel'], 
            values['engineoverloadlevel'], 
            values['capacitoroverchargelevel'], 
            values['weaponoverloadlevel'], 
            values['shieldadjustsetting']
            ]

        cur2.execute("DROP TABLE IF EXISTS exitsave")
        cur2.execute("CREATE TABLE exitsave(name, chassis, mass, armor1, armor2, booster, capacitor, cargohold, droidinterface, engine, reactor, shield, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, pack1, pack2, pack3, pack4, pack5, pack6, pack7, pack8, rolevel, eolevel, colevel, wolevel, adjust)")
        cur2.execute("INSERT INTO exitsave VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", exitSave)

        compdb.commit()
        print('Exit save successful.')

        return True
    except:
        return False

def loadExitSave(window):

    try:
        loadoutData = cur2.execute("SELECT * FROM exitsave").fetchall()[0]

        updateSlotHeaders(loadoutData[1], window)

        window['loadoutname'].update(value = loadoutData[0])
        window['chassistype'].update(value = loadoutData[1])
        window['loadoutmass'].update(value = loadoutData[2])
        window['frontarmorselection'].update(value = loadoutData[3])
        window['reararmorselection'].update(value = loadoutData[4])
        window['boosterselection'].update(value = loadoutData[5]) 
        window['capselection'].update(value = loadoutData[6])
        window['chselection'].update(value = loadoutData[7])  
        window['diselection'].update(value = loadoutData[8]) 
        window['engineselection'].update(value = loadoutData[9]) 
        window['reactorselection'].update(value = loadoutData[10]) 
        window['shieldselection'].update(value = loadoutData[11])  
        window['slot1selection'].update(value = loadoutData[12]) 
        window['slot2selection'].update(value = loadoutData[13]) 
        window['slot3selection'].update(value = loadoutData[14]) 
        window['slot4selection'].update(value = loadoutData[15]) 
        window['slot5selection'].update(value = loadoutData[16]) 
        window['slot6selection'].update(value = loadoutData[17]) 
        window['slot7selection'].update(value = loadoutData[18]) 
        window['slot8selection'].update(value = loadoutData[19])
        window['reactoroverloadlevel'].update(value = loadoutData[28]) 
        window['engineoverloadlevel'].update(value = loadoutData[29]) 
        window['capacitoroverchargelevel'].update(value = loadoutData[30]) 
        window['weaponoverloadlevel'].update(value = loadoutData[31]) 
        window['shieldadjustsetting'].update(value = loadoutData[32])

        refreshReactor(window, loadoutData[10])
        refreshEngine(window, loadoutData[9])
        refreshBooster(window, loadoutData[5])
        refreshShield(window, loadoutData[11], loadoutData[32])
        refreshFrontArmor(window, loadoutData[3])
        refreshRearArmor(window, loadoutData[4])
        refreshDI(window, loadoutData[8])
        refreshCH(window, loadoutData[7])
        refreshCapacitor(window, loadoutData[6])
        compType1 = refreshSlot(window, loadoutData[12], 1)
        compType2 = refreshSlot(window, loadoutData[13], 2)
        compType3 = refreshSlot(window, loadoutData[14], 3)
        compType4 = refreshSlot(window, loadoutData[15], 4)
        compType5 = refreshSlot(window, loadoutData[16], 5)
        compType6 = refreshSlot(window, loadoutData[17], 6)
        compType7 = refreshSlot(window, loadoutData[18], 7)
        compType8 = refreshSlot(window, loadoutData[19], 8)
        window['slot1packselection'].update(value = loadoutData[20]) 
        window['slot2packselection'].update(value = loadoutData[21]) 
        window['slot3packselection'].update(value = loadoutData[22]) 
        window['slot4packselection'].update(value = loadoutData[23]) 
        window['slot5packselection'].update(value = loadoutData[24]) 
        window['slot6packselection'].update(value = loadoutData[25]) 
        window['slot7packselection'].update(value = loadoutData[26]) 
        window['slot8packselection'].update(value = loadoutData[27]) 
        refreshPack(window, loadoutData[20], 1, compType1)
        refreshPack(window, loadoutData[21], 2, compType2)
        refreshPack(window, loadoutData[22], 3, compType3)
        refreshPack(window, loadoutData[23], 4, compType4)
        refreshPack(window, loadoutData[24], 5, compType5)
        refreshPack(window, loadoutData[25], 6, compType6)
        refreshPack(window, loadoutData[26], 7, compType7)
        refreshPack(window, loadoutData[27], 8, compType8)

        window.refresh()

        return loadoutData[1], loadoutData[2], True
    
    except:
        return "", "", False

def updateProfile(window):
    events, values = window.read(timeout=0)

    chassis = window['chassistype'].get()

    if chassis != '':
        [minThrottle, optThrottle, maxThrottle] = cur.execute("SELECT minthrottle, optthrottle, maxthrottle FROM chassis WHERE name = ?", [chassis]).fetchall()[0]
        
        minThrottle = tryFloat(minThrottle)
        optThrottle = tryFloat(optThrottle)
        maxThrottle = tryFloat(maxThrottle)

        span = np.linspace(1,0,101)

        percents = []

        for i in span:
            if i < optThrottle:
                percentToOptimal = i / optThrottle
                per = ((1 - minThrottle) * percentToOptimal + minThrottle)
                per = np.floor((per*10) + 0.5) / 10
                percents.append(per)
            else:
                percentFromOptimal = (i - optThrottle)/(1 - optThrottle)
                per = ((maxThrottle - 1) * percentFromOptimal + 1)
                per = np.floor((per*10) + 0.5) / 10
                percents.append(per)

        #Code to print throttle mod breakpoints in terms of throttle percent

        # profileByPercent = [[str(int(span[i]*100))+'%', str(int(percents[i]*100))+'%'] for i in range(100)]
        # breakpoints = []

        # for i in range(1,len(profileByPercent)):
        #     if profileByPercent[i][1] != profileByPercent [i-1][1]:
        #         breakpoints.append(profileByPercent[i-1])

        # breakpoints.append(['0%',str(int(minThrottle*100))+'%'])

        # print([b for b in breakpoints])


        percents = [int(percents[i]*100) for i in range(0,len(percents)) if i%10 == 0]

        span = np.linspace(1,0,11)

        for i in range(0, 11):
            per = percents[i]
            color = getThreeColorGradient(per)
            window['text' + str(i * 10)].update(' ' + str(int(round(span[i],1) * 100)) + '%',text_color=profileTextColor)
            window['pyr' + str(i * 10)].update(' ' + str(per) + '%', text_color=bgColor, background_color=color)
            window['frame' + str(i * 10)].Widget.config(background=color, borderwidth=1)
            window['textframe' + str(i * 10)].Widget.config(borderwidth=1)

        window['throttlemods'].update('Min: ' + str(minThrottle) + ' / Opt: ' + str(optThrottle) + ' / Max: ' + str(maxThrottle),text_color=profileTextColor)
        window['profilepercentheader'].update("Throttle",text_color=profileTextColor)
        window['profilepyrheader'].update("Max PY",text_color=profileTextColor)
    else:
        window['throttlemods'].update("")
        window['profilepercentheader'].update("")
        window['profilepyrheader'].update("")
        for i in range(0, 11):
            window['text' + str(i * 10)].update('')
            window['pyr' + str(i * 10)].update('',text_color=bgColor, background_color=boxColor)
            window['frame' + str(i * 10)].Widget.config(background=boxColor, borderwidth=0)
            window['textframe' + str(i * 10)].Widget.config(borderwidth=0)

    window.refresh()

def setMenus(menuEnables):

    [openLoadoutEnable,saveAsEnable,saveEnable] = menuEnables

    if openLoadoutEnable:
        openLoadoutString = '&Open Loadout'
    else:
        openLoadoutString = '!&Open Loadout'
    
    if saveAsEnable:
        saveAsString = '&Save Loadout As'
        clearCompString = '&Clear All Components'
    else:
        saveAsString = '!&Save Loadout As'
        clearCompString = '!&Clear All Components'

    if saveEnable:
        saveString = '&Save Loadout'
    else:
        saveString = '!&Save Loadout'

    menu_def = [
            ['&Loadout', ['&New Loadout', openLoadoutString, saveString, saveAsString, '&Quit']],
            ['&Components', ['Add and &Manage Components', clearCompString]],
            ['&Tools', ['&Reverse Engineering Calculator','&Flight Computer Calculator','&Loot Lookup Tool','&Import v1.x Data', '&Check for Updates']],
            ['&Help', ['&About','&Keyboard Shortcuts']]
        ]
        
    return menu_def

def main():

    ### Updates deprecated file structure and sets up saved data storage if needed ###

    #Checks for existing Data\savedata.db files and moves them to their new home in Appdata. If there is no active savedata.db file, creates a new one in appdata. Deletes deprecated Data folder if it exists and has a tables.db file in it.
    try:
        dataDir = os.getenv('APPDATA') + "\\Seraph's Loadout Tool"

        if not os.path.exists(dataDir):
            os.makedirs(dataDir)

        if os.path.exists('Data\\savedata.db'):
            shutil.move('Data\\savedata.db', dataDir + '\\savedata.db')
        else:
            buildComponentList(dataDir)
    except:
        alert('Fatal Error',['Fatal error when attempting to create or relocate savedata.db. Unable to find destination folder','If you are seeing this message, please contact me ASAP - Seraph'],['Okay',0])
        return

    if os.path.exists('Data\\tables.db'): #Clears tables.db as it will now be included in the exe.
        os.remove('Data\\tables.db')
        empty = True
        for x in os.scandir('Data'): #Deletes the Data folder if it's empty (which by now it should be assuming the user didn't put anything else in there)
            empty = False
            break
        if empty:
            os.removedirs("Data")

    #Connect to databases

    global tables
    global cur
    global compdb
    global cur2

    tables = sqlite3.connect('file:tables.db?mode=ro', uri=True)
    cur = tables.cursor()

    compdb = sqlite3.connect('file:'+ dataDir +'\\savedata.db?mode=rw', uri=True)
    cur2 = compdb.cursor()

    if __name__ == '__main__':
        multiprocessing.freeze_support()

        #Cludgy catch to try and see if there are any read-write permission errors on the user's computer at launch before it becomes a hang or crash.

        try:
            cur2.execute("CREATE TABLE test (test)")
            cur2.execute("DROP TABLE test")
        except:
            alert('Fatal Error',["Fatal Error: You do not appear to have permission to write data to the tool's database files.","Try right-clicking the application icon and selecting 'Run as Administrator'."],[],10)
            return

        menuEnables = [False, False, False]

        menu_def = setMenus(menuEnables)

        Lists = updateParts()

        reactorText = [
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Generation:", font=baseFont, p=fontPadding)],
        ]

        reactorStats = [
            [sg.Text("", key='reactormass', font=baseFontStats, p=fontPadding),sg.Push()],
            [sg.Text("", key='reactorgen', font=baseFontStats, p=fontPadding),sg.Push()],
        ]

        reactorBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Reactor", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',[[]],border_width=0,s=(20,20),p=5),],
            [sg.Frame('',reactorText,border_width=0,p=0,s=(compBoxWidth/2,row1Height-65)), sg.Push(),sg.Frame('',reactorStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height-65))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='reactorselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        engineText = [
            [sg.Push(),sg.Text("Drain:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Pitch Rate:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Yaw Rate:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Roll Rate:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Top Speed:", font=baseFont, p=fontPadding)],
        ]

        engineStats = [
            [sg.Text("", key='enginered', font=baseFontStats, p=fontPadding), sg.Push()],
            [sg.Text("", key='enginemass', font=baseFontStats, p=fontPadding), sg.Push()],
            [sg.Text("", key='enginepitch', font=baseFontStats, p=fontPadding), sg.Push()],
            [sg.Text("", key='engineyaw', font=baseFontStats, p=fontPadding), sg.Push()],
            [sg.Text("", key='engineroll', font=baseFontStats, p=fontPadding), sg.Push()],
            [sg.Text("", key='enginets', font=baseFontStats, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutEngine = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='enginepowerboxcolor', text_color=boxColor)]
        ]

        engineBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Engine", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutEngine,border_width=0,background_color=boxColor, s=(20,20), p=5, key='enginepowerboxframecolor')],
            [sg.Frame('',engineText,border_width=0,p=0,s=(compBoxWidth/2,row1Height-65)), sg.Push(),sg.Frame('',engineStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height-65))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='engineselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        boosterText = [
            [sg.Push(),sg.Text("Drain:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Energy:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Recharge:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Consumption:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Acceleration:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Top Speed:", font=baseFont, p=fontPadding)],
        ]

        boosterStats = [
            [sg.Text("", key='boosterred', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boostermass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boosterenergy', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boosterrr', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boostercons', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boosteraccel', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='boosterts', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutBooster = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='boosterpowerboxcolor', text_color=boxColor)]
        ]

        boosterBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Booster", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutBooster,border_width=0,background_color=boxColor, s=(20,20), p=5, key='boosterpowerboxframecolor')],
            [sg.Frame('',boosterText,border_width=0,p=0,s=(compBoxWidth/2,row1Height-65)), sg.Push(),sg.Frame('',boosterStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height-65))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='boosterselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        shieldText = [
            [sg.Push(),sg.Text("Drain:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Shield HP:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Recharge:", font=baseFont, p=fontPadding)],
            [sg.VPush()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding,key='adjusttext')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding,key='adjustfronttext')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding,key='adjustbacktext')],
        ]

        shieldStats = [
            [sg.Text("", key='shieldred', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='shieldmass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='shieldhp', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='shieldrr', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.VPush()],
            [sg.Text("", key='shieldadjust', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='shieldfront', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='shieldback', font=baseFontStats, s=10, p=fontPadding), sg.Push()],

        ]

        powerBoxLayoutShield = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='shieldpowerboxcolor', text_color=boxColor)]
        ]

        shieldBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Shield", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutShield,border_width=0,background_color=boxColor, s=(20,20), p=5, key='shieldpowerboxframecolor')],
            [sg.Frame('',shieldText,border_width=0,p=0,s=(compBoxWidth/2,row1Height-64)), sg.Push(),sg.Frame('',shieldStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height-64))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='shieldselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        frontArmorText = [
            [sg.Push(),sg.Text("Armor/HP:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
        ]

        frontArmorStats = [
            [sg.Text("", key='frontarmorahp', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='frontarmormass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        rearArmorText = [
            [sg.Push(),sg.Text("Armor/HP:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
        ]

        rearArmorStats = [
            [sg.Text("", key='reararmorahp', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='reararmormass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        frontArmorBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Front Armor", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',[[]],border_width=0,s=(20,20),p=5),],
            [sg.Frame('',frontArmorText,border_width=0,p=0,s=(compBoxWidth/2,row1Height/2-65-2*elementPadding+1)), sg.Push(),sg.Frame('',frontArmorStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height/2-65-2*elementPadding+1))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='frontarmorselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        rearArmorBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Rear Armor", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',[[]],border_width=0,s=(20,20),p=5),],
            [sg.Frame('',rearArmorText,border_width=0,p=0,s=(compBoxWidth/2,row1Height/2-65-2*elementPadding+1)), sg.Push(),sg.Frame('',rearArmorStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height/2-65-2*elementPadding+1))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='reararmorselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        armorBoxFrame = [
            [sg.Frame('', frontArmorBox, border_width=0, expand_x=True, expand_y=True, p=0, size=(compBoxWidth, (row1Height/2-2*elementPadding+2)))],
            [sg.VPush(background_color=bgColor)],
            [sg.Frame('', rearArmorBox, border_width=0, expand_x=True, expand_y=True, p=0, size=(compBoxWidth, (row1Height/2-2*elementPadding+1)))],
        ]

        diText = [
            [sg.Push(),sg.Text("Drain:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Cmd Speed:", font=baseFont, p=fontPadding)],
        ]

        diStats = [
            [sg.Text("", key='dired', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='dimass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],  
            [sg.Text("", key='didcs', font=baseFontStats, s=10, p=fontPadding), sg.Push()],  
        ]

        powerBoxLayoutDI = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='dipowerboxcolor', text_color=boxColor)]
        ]

        diBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Droid Interface", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutDI,border_width=0,background_color=boxColor, s=(20,20), p=5, key='dipowerboxframecolor')],
            [sg.Frame('',diText,border_width=0,p=0,s=(compBoxWidth/2,row2Height/2-65+elementPadding+1)), sg.Push(),sg.Frame('',diStats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height/2-65+elementPadding+1))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='diselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        chText = [
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
        ]

        chStats = [
            [sg.Text("", key='chmass', font=baseFontStats, s=10, p=fontPadding), sg.Push()], 
        ]

        chBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Cargo Hold", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',[[]],border_width=0,s=(20,20),p=5),],
            [sg.Frame('',chText,border_width=0,p=0,s=(compBoxWidth/2,row2Height/2-65-5*elementPadding+1)), sg.Push(),sg.Frame('',chStats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height/2-65-5*elementPadding+1))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='chselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        diBoxFrame = [
            [sg.Frame('', diBox, border_width=0, expand_x=True, expand_y=True, p=0, size=(compBoxWidth, (row2Height/2+elementPadding+1)))],
            [sg.VPush(background_color=bgColor)],
            [sg.Frame('', chBox, border_width=0, expand_x=True, expand_y=True, p=0, size=(compBoxWidth, (row2Height/2-5*elementPadding+1)))],
        ]

        capacitorText = [
            [sg.Push(),sg.Text("Drain:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Energy:", font=baseFont, p=fontPadding)],
            [sg.Push(),sg.Text("Recharge:", font=baseFont, p=fontPadding)],
        ]

        capacitorStats = [
            [sg.Text("", key='capacitorred', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='capacitormass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='capacitorce', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='capacitorrr', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutCapacitor = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='cappowerboxcolor', text_color=boxColor)]
        ]

        capacitorBox = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Capacitor", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutCapacitor,border_width=0,background_color=boxColor, s=(20,20), p=5, key='cappowerboxframecolor')],
            [sg.Frame('',capacitorText,border_width=0,p=0,s=(compBoxWidth/2,row2Height-65)), sg.Push(),sg.Frame('',capacitorStats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height-65))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='capselection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)]
        ]

        slot1Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1stat8text')],
        ]

        slot1Stats = [
            [sg.Text("", key='slot1stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot1stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot1 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot1powerboxcolor', text_color=boxColor)]
        ]

        slot1Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot1header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot1,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot1powerboxframecolor')],
            [sg.Frame('',slot1Text,border_width=0,p=0,s=(compBoxWidth/2,row2Height-85)), sg.Push(),sg.Frame('',slot1Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot1packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot1selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot2Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2stat8text')],
        ]

        slot2Stats = [
            [sg.Text("", key='slot2stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot2stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot2 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot2powerboxcolor', text_color=boxColor)]
        ]

        slot2Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot2header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot2,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot2powerboxframecolor')],
            [sg.Frame('',slot2Text,border_width=0,p=0,s=(compBoxWidth/2,row2Height-85)), sg.Push(),sg.Frame('',slot2Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot2packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot2selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot3Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3stat8text')],
        ]

        slot3Stats = [
            [sg.Text("", key='slot3stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot3stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot3 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot3powerboxcolor', text_color=boxColor)]
        ]

        slot3Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot3header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot3,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot3powerboxframecolor')],
            [sg.Frame('',slot3Text,border_width=0,p=0,s=(compBoxWidth/2,row2Height-85)), sg.Push(),sg.Frame('',slot3Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row2Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot3packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot3selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot4Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4stat8text')],
        ]

        slot4Stats = [
            [sg.Text("", key='slot4stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot4stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot4 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot4powerboxcolor', text_color=boxColor)]
        ]

        slot4Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot4header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot4,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot4powerboxframecolor')],
            [sg.Frame('',slot4Text,border_width=0,p=0,s=(compBoxWidth/2,row3Height-85)), sg.Push(),sg.Frame('',slot4Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row3Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot4packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot4selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot5Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5stat8text')],
        ]

        slot5Stats = [
            [sg.Text("", key='slot5stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot5stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot5 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot5powerboxcolor', text_color=boxColor)]
        ]

        slot5Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot5header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot5,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot5powerboxframecolor')],
            [sg.Frame('',slot5Text,border_width=0,p=0,s=(compBoxWidth/2,row3Height-85)), sg.Push(),sg.Frame('',slot5Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row3Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot5packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot5selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot6Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6stat8text')],
        ]

        slot6Stats = [
            [sg.Text("", key='slot6stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot6stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot6 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot6powerboxcolor', text_color=boxColor)]
        ]

        slot6Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot6header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot6,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot6powerboxframecolor')],
            [sg.Frame('',slot6Text,border_width=0,p=0,s=(compBoxWidth/2,row3Height-85)), sg.Push(),sg.Frame('',slot6Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row3Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot6packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot6selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot7Text = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat1text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat2text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat3text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat4text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat5text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat6text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat7text')],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7stat8text')],
        ]

        slot7Stats = [
            [sg.Text("", key='slot7stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
            [sg.Text("", key='slot7stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        ]

        powerBoxLayoutSlot7 = [
            [sg.Text("⚡", background_color=boxColor, p=0, key='slot7powerboxcolor', text_color=boxColor)]
        ]

        slot7Box = [
            [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot7header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot7,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot7powerboxframecolor')],
            [sg.Frame('',slot7Text,border_width=0,p=0,s=(compBoxWidth/2,row3Height-85)), sg.Push(),sg.Frame('',slot7Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row3Height-85))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot7packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(28,10), readonly=True, key='slot7selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        slot8Text = []
        slot8Stats = []

        for i in range(1,9):
            slot8Text.append([sg.Push(),sg.Text("", key='slot8stat' + str(i) + 'text', font=baseFontStats, p=fontPadding)])
            slot8Stats.append([sg.Text("", key='slot8stat' + str(i), font=baseFontStats, p=fontPadding), sg.Push()])

        powerBoxLayoutSlot8 = [
            [sg.Text("⚡", background_color=boxColor, p=0, font=int(10*scaleFactor), key='slot8powerboxcolor', text_color=boxColor)]
        ]

        slot8Box = [
            [sg.Frame('',[[]],border_width=0,s=(int(20*scaleFactor),int(20*scaleFactor)),p=int(5*scaleFactor)),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot8header'),sg.Push()]],border_width=0,p=0,s=(int(compBoxWidth-65*scaleFactor),int(28*scaleFactor))),sg.Frame('',powerBoxLayoutSlot8,border_width=0,background_color=boxColor, s=(int(20*scaleFactor),int(20*scaleFactor)), p=int(5*scaleFactor), key='slot8powerboxframecolor')],
            [sg.Frame('',slot8Text,border_width=0,p=0,s=(int(compBoxWidth/2),int(row3Height-85*scaleFactor))), sg.Push(),sg.Frame('',slot8Stats,border_width=0,p=0,s=(int(compBoxWidth/2-5*scaleFactor),int(row3Height-85*scaleFactor)))],
            [sg.VPush()],
            [sg.Combo(values = [], size=(int(28*scaleFactor),int(10*scaleFactor)), readonly=True, key='slot8packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
            [sg.Combo(values = [], size=(int(28*scaleFactor),int(10*scaleFactor)), readonly=True, key='slot8selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
        ]

        loadoutCol1 = [
            [sg.Frame('', reactorBox, border_width=0, size=(compBoxWidth, row1Height), p=elementPadding)],
            [sg.Frame('', diBoxFrame, border_width=0, size=(compBoxWidth, row2Height), p=elementPadding, background_color=bgColor)],
            [sg.Frame('', slot4Box, border_width=0, p=elementPadding, size=(compBoxWidth, row3Height))]
        ]

        loadoutCol2 = [
            [sg.Frame('', engineBox, border_width=0, size=(compBoxWidth, row1Height), p=elementPadding)],
            [sg.Frame('', capacitorBox, border_width=0, size=(compBoxWidth, row2Height), p=elementPadding)],
            [sg.Frame('', slot5Box, border_width=0, size=(compBoxWidth, row3Height), p=elementPadding)]
        ]

        loadoutCol3 = [
            [sg.Frame('', boosterBox, border_width=0, size=(compBoxWidth, row1Height), p=elementPadding)],
            [sg.Frame('', slot1Box, border_width=0, size=(compBoxWidth, row2Height), p=elementPadding)],
            [sg.Frame('', slot6Box, border_width=0, size=(compBoxWidth, row3Height), p=elementPadding)]
        ]

        loadoutCol4 = [
            [sg.Frame('', shieldBox, border_width=0, size=(compBoxWidth, row1Height), p=elementPadding)],
            [sg.Frame('', slot2Box, border_width=0, size=(compBoxWidth, row2Height), p=elementPadding)],
            [sg.Frame('', slot7Box, border_width=0, size=(compBoxWidth, row3Height), p=elementPadding)]
        ]

        loadoutCol5 = [
            [sg.Frame('', armorBoxFrame, border_width=0, size=(compBoxWidth, row1Height), p=elementPadding, background_color=bgColor)],
            [sg.Frame('', slot3Box, border_width=0, size=(compBoxWidth, row2Height), p=elementPadding)],
            [sg.Frame('', slot8Box, border_width=0, size=(compBoxWidth, row3Height), p=elementPadding, key='slot8frame')],
        ]

        loadoutBank = [
            [sg.Column(loadoutCol1, background_color=bgColor, p=0), sg.Column(loadoutCol2, background_color=bgColor, p=0), sg.Column(loadoutCol3, background_color=bgColor, p=0), sg.Column(loadoutCol4, background_color=bgColor, p=0), sg.Column(loadoutCol5, background_color=bgColor, p=0)]
        ]

        chassisBoxLeft = [
            [sg.Push(), sg.Text("Loadout Name:", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("Chassis Type:", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("Ship Mass Utilization:", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("Leftover Mass:", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("Reactor Utilization:", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("Minimum Gen Required:", font=baseFont, p=fontPadding)]
        ]

        chassisBoxRight = [
            [sg.Text("", font=baseFont, key='loadoutname', s=30, p=fontPadding)],
            [sg.Text("", font=baseFont, key='chassistype', s=30, p=fontPadding)],
            [sg.Text("", font=baseFont, key='loadoutmass', s=30, p=fontPadding)],
            [sg.Text("", font=baseFont, key='massremaining', s=30, p=fontPadding)],
            [sg.Text("", font=baseFont, key='totaldrain', s=30, p=fontPadding)],
            [sg.Text("", font=baseFont, key='minimumgen', s=30, p=fontPadding)],
        ]

        chassisBox = [
            [sg.Push(), sg.Text("Loadout Details", font=headerFont), sg.Push()],
            [sg.Frame('', chassisBoxLeft,border_width=0,p=elementPadding,s=(int(211*scaleFactor),topRowHeight)), sg.Frame('', chassisBoxRight,border_width=0,p=elementPadding,s=(int(211*scaleFactor),topRowHeight))]
        ]

        overloadsTextColumn = [
            [sg.Push(), sg.Text("Reactor Overload:", font=baseFont, p=1)],
            [sg.Push(), sg.Text("Engine Overload:", font=baseFont, p=1)],
            [sg.Push(), sg.Text("Capacitor Overcharge:", font=baseFont, p=1)],
            [sg.Push(), sg.Text("Weapon Overload:", font=baseFont, p=1)],
        ]

        overloadsDropdowns = [
            [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(int(5*scaleFactor),int(5*scaleFactor)), readonly=True, key='reactoroverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=1), sg.Push()],
            [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(int(5*scaleFactor),int(5*scaleFactor)), readonly=True, key='engineoverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=1), sg.Push()],
            [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(int(5*scaleFactor),int(5*scaleFactor)), readonly=True, key='capacitoroverchargelevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=1), sg.Push()],
            [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(int(5*scaleFactor),int(5*scaleFactor)), readonly=True, key='weaponoverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=1), sg.Push()],
        ]

        overloadDescriptions1 = [
            [sg.Push(),sg.Text("",font=baseFont,key='reactoroverloaddesc1',p=1)],
            [sg.Push(),sg.Text("",font=baseFont,key='engineoverloaddesc1',p=1)],
            [sg.Push(),sg.Text("",font=baseFont,key='capoverloaddesc1',p=1)],
            [sg.Push(),sg.Text("",font=baseFont,key='weaponoverloaddesc1',p=1)],
        ]

        overloadDescriptions2 = [
            [sg.Text("",font=baseFont,key='reactoroverloaddesc2',p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='engineoverloaddesc2',p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='capoverloaddesc2',p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='weaponoverloaddesc2',p=1),sg.Push()],
        ]

        overloadDescriptions3 = [
            [sg.Push(),sg.Text("",font=baseFont,p=1),sg.Push()],
            [sg.Push(),sg.Text("",font=baseFont,key='engineoverloaddesc3',p=1)],
            [sg.Push(),sg.Text("",font=baseFont,key='capoverloaddesc3',p=1)],
            [sg.Push(),sg.Text("",font=baseFont,key='weaponoverloaddesc3',p=1)],
        ]

        overloadDescriptions4 = [
            [sg.Text("",font=baseFont,p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='engineoverloaddesc4',p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='capoverloaddesc4',p=1),sg.Push()],
            [sg.Text("",font=baseFont,key='weaponoverloaddesc4',p=1),sg.Push()],
        ]

        adjSubframeLeft = [
            [sg.Push(), sg.Text("Shield Adjust:", font=baseFont, p=fontPadding)]
        ]

        adjSubframeMid = [
            [sg.Combo(["Front - Extreme", "Front - Heavy", "Front - Moderate", "Front - Light", "None", "Rear - Light", "Rear - Moderate", "Rear - Heavy", "Rear - Extreme"], default_value="None", s=(int(14*scaleFactor),int(9*scaleFactor)), readonly=True, key='shieldadjustsetting', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()]
        ]

        adjSubframeRight1 = [
            [sg.Push(),sg.Text("",font=baseFont,key='shieldadjustdesc1',p=fontPadding)],
        ]

        adjSubframeRight2 = [
            [sg.Text("",font=baseFont,key='shieldadjustdesc2',p=fontPadding),sg.Push()],
        ]

        adjSubframeRight3 = [
            [sg.Push(),sg.Text("",font=baseFont,key='shieldadjustdesc3',p=fontPadding)],
        ]

        adjSubframeRight4 = [
            [sg.Text("",font=baseFont,key='shieldadjustdesc4',p=fontPadding),sg.Push()],
        ]

        overloadsFrame = [
            [sg.Push(), sg.Text("Flight Computer", font=headerFont),sg.Push()],
            [
                sg.Frame('',overloadsTextColumn, border_width=0, p=elementPadding, s=(int(150*scaleFactor),int(topRowHeight-75*scaleFactor))), 
                sg.Frame('',overloadsDropdowns, border_width=0, p=0,s=(int(60*scaleFactor),int(topRowHeight-75*scaleFactor))), 
                sg.Frame('',overloadDescriptions1, border_width=0, p=0,s=(int(75*scaleFactor),int(topRowHeight-75*scaleFactor))), 
                sg.Frame('',overloadDescriptions2, border_width=0, p=0,s=(int(35*scaleFactor),int(topRowHeight-75*scaleFactor))), 
                sg.Frame('',overloadDescriptions3, border_width=0, p=0,s=(int(70*scaleFactor),int(topRowHeight-75*scaleFactor))), 
                sg.Frame('',overloadDescriptions4, border_width=0, p=0,s=(int(35*scaleFactor),int(topRowHeight-75*scaleFactor))),
            ],
            [
                sg.Frame('',adjSubframeLeft,border_width=0,p=elementPadding,s=(int(87*scaleFactor),int(30*scaleFactor))),
                sg.Frame('',adjSubframeMid,border_width=0,p=0,s=(int(123*scaleFactor),int(30*scaleFactor))),
                sg.Frame('',adjSubframeRight1,border_width=0,p=0,s=(int(75*scaleFactor),int(30*scaleFactor))),
                sg.Frame('',adjSubframeRight2,border_width=0,p=0,s=(int(35*scaleFactor),int(30*scaleFactor))),
                sg.Frame('',adjSubframeRight3,border_width=0,p=0,s=(int(70*scaleFactor),int(30*scaleFactor))),
                sg.Frame('',adjSubframeRight4,border_width=0,p=0,s=(int(35*scaleFactor),int(30*scaleFactor)))]
        ]

        capSummaryLeft = [
            [sg.Push(),sg.Text("Overloaded CE:", font=baseFont, p=fontPadding, key='overloadedcetext')],
            [sg.Push(),sg.Text("Overloaded RR:", font=baseFont, p=fontPadding, key='overloadedrrtext')],
            [sg.Push(),sg.Text("Full Cap Damage:", font=baseFont, p=fontPadding, tooltip=fullCapDamageTooltip)],
            [sg.Push(),sg.Text("Fire Time:", font=baseFont,p=fontPadding, tooltip=fireTimeTooltip)],
            [sg.Push(),sg.Text("Recharge Time:", font=baseFont, p=fontPadding, tooltip=capRechargeTimeTooltip)],
            [sg.Push(),sg.Text("Firing Ratio:", font=baseFont, p=fontPadding, tooltip=firingRatioTooltip)]
        ]

        capSummaryRight = [
            [sg.Text("", font=baseFont, p=fontPadding, key='overloadedce'),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='overloadedrr'),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='fullcapdamage', tooltip=fullCapDamageTooltip),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='firetime', tooltip=fireTimeTooltip), sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='caprecharge', tooltip=capRechargeTimeTooltip), sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='firingratio', tooltip=firingRatioTooltip), sg.Push()]
        ]

        capSummaryBox = [
            [sg.Push(),sg.Text("Capacitor Summary", font=headerFont),sg.Push()],
            [sg.Frame('',capSummaryLeft,border_width=0,p=elementPadding,s=(int(compBoxWidth/2+12),topRowHeight)),sg.Frame('',capSummaryRight,border_width=0,p=elementPadding,s=(int(compBoxWidth/2-28),topRowHeight))],
        ]

        weaponSummaryBoxLeft = [
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='pilotguntext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot1damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot2damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot3damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot4damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot5damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot6damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot7damagetext', tooltip=dpShotTooltip)],
            [sg.Push(), sg.Text("", font=baseFont, p=fontPadding, key='slot8damagetext', tooltip=dpShotTooltip)]
        ]

        weaponSummaryBoxCenter = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='pveheader'),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='pilotweapondamagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7damagepve', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8damagepve', tooltip=dpShotTooltip),sg.Push()],
        ]

        weaponSummaryBoxRight = [
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='pvpheader'), sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='pilotweapondamagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot1damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot2damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot3damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot4damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot5damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot6damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot7damagepvp', tooltip=dpShotTooltip),sg.Push()],
            [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8damagepvp', tooltip=dpShotTooltip),sg.Push()],
        ]

        weaponSummaryTitleFrame = [
            [sg.Push(),sg.Text('Weapons Summary',font=headerFont, p=fontPadding),sg.Push()]
        ]

        weaponSummaryBox = [
            [sg.Frame('',weaponSummaryTitleFrame,border_width=0,p=elementPadding,s=(rightPaneWidth,25))],
            [sg.Frame('',weaponSummaryBoxLeft,border_width=0,p=elementPadding,s=(int(rightPaneWidth/2-12*scaleFactor),int(200*scaleFactor))), sg.Frame('',weaponSummaryBoxCenter,border_width=0,p=(0,elementPadding),s=(int(rightPaneWidth/5+8*scaleFactor),int(200*scaleFactor))),sg.Frame('',weaponSummaryBoxRight,border_width=0,p=(0,4),s=(int(rightPaneWidth/5+8*scaleFactor),int(200*scaleFactor))), sg.Frame('',[[]],border_width=0,p=0,s=(int(rightPaneWidth/10-12*scaleFactor),int(200*scaleFactor)))],
        ]

        propulsionSummaryLeft = [
            [sg.Push(),sg.Text("Top Speed:", font=baseFont, p=fontPadding, tooltip=topSpeedTooltip)],
            [sg.Push(),sg.Text("Boosted TS:", font=baseFont,p=fontPadding, tooltip=boostedTSTooltip)],
            [sg.Push(),sg.Text("Boost Distance:", font=baseFont, p=fontPadding, tooltip=boostDistTooltip)],
            [sg.Push(),sg.Text("Booster Uptime:", font=baseFont, p=fontPadding, tooltip=boosterUptimeTooltip)],
            [sg.Push(),sg.Text("Speed Mod:", font=baseFont, p=fontPadding, tooltip=speedModTooltip)],
            [sg.Push(),sg.Text("Accel/Decel:", font=baseFont, p=fontPadding, tooltip=chassisADTooltip)],
            [sg.Push(),sg.Text("P/Y/R Accel:", font=baseFont, p=fontPadding, tooltip=chassisPYRTooltip)],
            [sg.Push(),sg.Text("Slide Mod:", font=baseFont, p=fontPadding, tooltip=chassisSlideModTooltip)],
        ]

        propulsionSummaryRight = [
            [sg.Text("", font=baseFont, p=fontPadding, key='topspeed', tooltip=topSpeedTooltip),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='boostedtopspeed', tooltip=boostedTSTooltip), sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='boostdistance', tooltip=boostDistTooltip), sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='boosteruptime', tooltip=boosterUptimeTooltip), sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='chassisspeedmod', tooltip=speedModTooltip),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='chassisad', tooltip=chassisADTooltip),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='chassispyr', tooltip=chassisPYRTooltip),sg.Push()],
            [sg.Text("", font=baseFont, p=fontPadding, key='chassisslide', tooltip=chassisSlideModTooltip),sg.Push()],
        ]

        propulsionSummaryBox = [
            [sg.Push(),sg.Text("Propulsion Summary", font=headerFont),sg.Push()],
            [sg.Frame('',propulsionSummaryLeft, border_width=0, p=elementPadding, s=(rightPaneWidth/2-int(12*scaleFactor),int(170*scaleFactor))),sg.Frame('',propulsionSummaryRight, border_width=0, p=elementPadding, s=(rightPaneWidth/2-int(4*scaleFactor),int(170*scaleFactor)))],
        ]

        profilePercentCol = [
            [sg.Push(background_color=profileBGColor),sg.Text("",font=baseFont,p=1, key='profilepercentheader',text_color=profileTextColor,background_color=profileBGColor),sg.Push(background_color=profileBGColor)],
        ]

        profilePYRCol = [
            [sg.Push(background_color=profileBGColor),sg.Text("",font=baseFont,p=1, key='profilepyrheader',text_color=profileTextColor,background_color=profileBGColor),sg.Push(background_color=profileBGColor)],
        ]

        for i in range(0,11):
            profilePercentCol.append([sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text'+str(i*10),text_color=profileTextColor,background_color=profileBGColor)]],border_width=0,p=1,s=(int(80*scaleFactor),int(20*scaleFactor)),key='textframe'+str(i*10), element_justification='center',background_color=profileBGColor)])        
            profilePYRCol.append([sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr'+str(i*10),text_color=profileTextColor,background_color=profileBGColor)]],border_width=0,p=1,s=(int(80*scaleFactor),int(20*scaleFactor)),key='frame'+str(i*10), element_justification='center',background_color=profileBGColor)])

        profileFrame = [
            [sg.Push(background_color=profileBGColor),sg.Text("Throttle Profile",font=headerFont,p=elementPadding,text_color=profileTextColor,background_color=profileBGColor),sg.Push(background_color=profileBGColor)],
            [sg.Push(background_color=profileBGColor),sg.Text("",font=baseFont,p=fontPadding, key='throttlemods',text_color=profileTextColor,background_color=profileBGColor),sg.Push(background_color=profileBGColor)],
            [sg.VPush(background_color=profileBGColor)],
            [sg.Push(background_color=profileBGColor),sg.Frame('',profilePercentCol,border_width=0,p=0, s=(int(rightPaneWidth/3),int(300*scaleFactor)),background_color=profileBGColor),sg.Frame('',profilePYRCol,border_width=0,p=0,s=(int(rightPaneWidth/3),int(300*scaleFactor)),background_color=profileBGColor),sg.Push(background_color=profileBGColor)],
            [sg.VPush(background_color=profileBGColor)]
        ]

        signatureFrame = [
            [sg.VPush()],
            [sg.Push(),sg.Text("Seraph's Loadout Tool v" + currentVersion, font=baseFont, p=fontPadding),sg.Push()],
            [sg.Push(),sg.Text("©2026 SeraphExodus", font=baseFont, p=fontPadding),sg.Push()],
            [sg.VPush()],
            [sg.Push(),sg.Text("Use Ctrl + C to take a screenshot!", font=baseFont, p=fontPadding),sg.Push()],
            [sg.VPush()]
        ]

        rightPane = [
            [sg.Frame('', weaponSummaryBox, border_width=0, p=elementPadding, s=(rightPaneWidth,int(235*scaleFactor)))],
            [sg.Frame('', propulsionSummaryBox, border_width=0, p=elementPadding, s=(rightPaneWidth,int(195*scaleFactor)))],
            [sg.Frame('', profileFrame, border_width=0, p=elementPadding, s=(rightPaneWidth, int(333*scaleFactor)),background_color=profileBGColor)],
            [sg.Frame('', signatureFrame, border_width=0, p=elementPadding, s=(rightPaneWidth,int(87*scaleFactor)))]
        ]

        leftPane = [
            [sg.Frame('', chassisBox, border_width=0, p=elementPadding, s=(int(438*scaleFactor), topRowHeight)),sg.Frame('', overloadsFrame, border_width=0, p=elementPadding, s=(int(438*scaleFactor),topRowHeight)),sg.Frame('', capSummaryBox, border_width=0, p=elementPadding, s=(compBoxWidth,topRowHeight)),],
            [sg.Column(loadoutBank, background_color=bgColor, expand_y=True, p=0)],
        ]
        
        layout = [
            [sg.Menu(menu_def, key='menu', text_color='#000000', disabled_text_color="#999999", background_color='#ffffff')],
            [sg.vtop(sg.Column(leftPane, background_color=bgColor, p=0)),sg.vtop(sg.Column(rightPane, background_color=bgColor, p=0))],
        ]

        window = sg.Window("Seraph's Loadout Tool V" + currentVersion,layout, finalize=True, background_color=bgColor, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), margins=(elementPadding, elementPadding), enable_close_attempted_event=True)
        move_center(window)

        chassis = ''
        chassisMass = 0
        headers = [] * 8

        newChassis, newChassisMass, loaded = loadExitSave(window)

        window.bind('<Control-s>', "Save Loadout")
        window.bind('<Control-n>', "New Loadout")
        window.bind('<Control-o>', "Open Loadout")
        window.bind('<Control-a>', "Add and Manage Components")
        window.bind('<Control-m>', "Add and Manage Components")
        window.bind('<Control-x>', 'Clear All Components')
        window.bind('<Control-c>', 'Capture Screenshot')

        loadouts = cur2.execute("SELECT * from loadout").fetchall()
        if loadouts != []:
            menuEnables[0] = True
        else:
            menuEnables[0] = False

        if loaded:
            event, values = window.read(timeout=0)
            headers = updateSlotHeaders(newChassis, window)
            Lists = updateParts(newChassis)
            updateDropdowns(Lists, window, values, False, headers)
            updateMassStrings(newChassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)
            doPropulsionCalculations(window)
            updateOverloadMults(window)
            chassis = newChassis
            chassisMass = newChassisMass
            updateProfile(window)
            menuEnables[1] = True

        window['menu'].update(setMenus(menuEnables))

        try:
            gist = get(versionURL).text.split('\n\n')
            latestVersion = gist[0]
            latestURL = gist[1]
        except:
            latestVersion = 0
            latestURL = ''

        if not latestVersion == 0 and not versionOverride:
            if latestVersion != currentVersion:
                result = alert("Alert",['Your version of the Loadout Tool appears to be out of date.', 'Click below to get the most recent version.',""],['Get Newest Version','Continue Anyway'],0)
                if result == 'Get Newest Version':
                    browserOpen(latestURL)
                    window.close()
                    return

        while True:
            event, values = window.read(timeout=250)

            Lists = updateParts(window['chassistype'].get())
            if chassis == '':
                updateDropdowns(Lists, window, values, True)
            else:
                updateDropdowns(Lists, window, values, False, headers)

            if event == 'New Loadout':
                [newName, newChassis, newChassisMass] = createLoadout()
                if not newName == '':
                    clearLoadout(window, "all")
                    event, values = window.read(timeout=0)
                    window['loadoutname'].update(newName)
                    window['chassistype'].update(newChassis)
                    headers = updateSlotHeaders(newChassis, window)
                    updateMassStrings(newChassisMass, window)
                    Lists = updateParts(newChassis)
                    updateDropdowns(Lists, window, values, False, headers)
                    chassis = newChassis
                    chassisMass = newChassisMass
                    doPropulsionCalculations(window)
                    updateProfile(window)

            if event == 'Save Loadout':
                saveLoadout(window)

            if event == 'Save Loadout As':
                newName = saveLoadoutAs(window)
                window['loadoutname'].update(newName)

            if event == 'Open Loadout':
                [newChassis, newChassisMass, loaded] = loadLoadout(window)
                if loaded:
                    event, values = window.read(timeout=0)
                    headers = updateSlotHeaders(newChassis, window)
                    Lists = updateParts(newChassis)
                    updateDropdowns(Lists, window, values, False, headers)
                    updateMassStrings(newChassisMass, window)
                    updateDrainStrings(window)
                    doWeaponCalculations(window)
                    doPropulsionCalculations(window)
                    updateOverloadMults(window)
                    chassis = newChassis
                    chassisMass = newChassisMass
                    updateProfile(window)                

            if event == 'Add and Manage Components':
                modified = manageComponents()
                if modified:
                    verifyEntries(window)
                    event, values = window.read(timeout=0)
                    for i in range(1, 9):
                        updatePacks(window, values['slot' + str(i) + 'selection'], 'slot' + str(i), False)
                    Lists = updateParts(window['chassistype'].get())
                    if chassis == '':
                        updateDropdowns(Lists, window, values, True)
                    else:
                        updateDropdowns(Lists, window, values, False, headers)
                    try:
                        chassisMass = cur2.execute("SELECT mass FROM loadout WHERE name = ?", [window['loadoutname'].get()]).fetchall()[0][0]
                    except:
                        chassisMass = 0
                    updateMassStrings(chassisMass, window)
                    updateDrainStrings(window)
                    doWeaponCalculations(window)
                    doPropulsionCalculations(window)

            if event == 'Import v1.x Data':
                confirm = alert('Notice', [
                    'Preparing to import version 1.x loadout and component data.',
                    '',
                    "• In order to import your data, you must use the Google Sheets tool to generate an export backup file from the 'Options' Tab",
                    "• Navigate to the export file in your Google Drive, which should be titled something like 'Backup Data (Seraph's Loadout Tool)...'",
                    "• Open the file, and go to File -> Download -> Microsoft Excel (.xlsx).",
                    '',
                    'Please be aware:',
                    'Due to implementation differences, ordnance and countermeasures will not be imported.',
                    'You must remake these components using this version of the tool and add them back to your loadouts.',
                    ''], ['Proceed','Cancel'],0,[[headerFont] + [summaryFont] * 9, ['center','left','left','left','left','left','center','center','center','center']])
                if confirm == "Proceed":
                    verify = importBackupData()
                    if verify:
                        window['menu'].update(menu_def_save_enabled)

            if event == 'Check for Updates':
                try:
                    gist = get(versionURL).text.split('\n\n')
                    latestVersion = gist[0]
                    latestURL = gist[1]
                except:
                    alert("Alert",["Unable to reach the server. Check your internet connection and try again."],['Okay'],0)
                    latestVersion = 0
                    latestURL = ''
                if latestVersion != 0:
                    if currentVersion != latestVersion:
                        result = alert("Alert",['Your version of the Loadout Tool appears to be out of date.', 'Click below to get the most recent version.',""],['Get Newest Version','Continue Anyway'],0)
                        if result == 'Get Newest Version':
                            browserOpen(latestURL)
                            window.close()
                            return
                    else:
                        alert("Alert",["Your version (" + latestVersion + ") is up to date."],[],5)

            if event == 'Clear All Components':
                result = alert("Alert", ['Are you sure? This will overwrite all currently-inputted components and FC program settings.'], ['Yes','Cancel'], 0)
                if result == "Yes":
                    clearLoadout(window, "parts")

            if event == 'Capture Screenshot':
                appWindow = FindWindow(None, "Seraph's Loadout Tool V" + currentVersion)
                rect = GetWindowRect(appWindow)
                if throttleProfileCaptureMode:
                    rect = (rect[0]+8+1123+36, rect[1]+51+235+195+8+8+8+1+28, rect[2]-8-8-35, rect[3]-8-87-8-8-7)
                else:
                    rect = (rect[0]+8, rect[1]+51, rect[2]-8, rect[3]-8)
                rect = [displayScaleFactor * x for x in rect]
                rect = [np.ceil(rect[0]),np.ceil(rect[1]),np.floor(rect[2]),np.floor(rect[3])]
                grab = ImageGrab.grab(bbox=rect, all_screens=True)
                screencapOutput = BytesIO()
                grab.convert("RGB").save(screencapOutput,"BMP")
                data = screencapOutput.getvalue()[14:]
                screencapOutput.close()
                toClipboard(win32clipboard.CF_DIB, data)

            if event == 'reactorselection':
                refreshReactor(window, values['reactorselection'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)

            if event == 'engineselection':
                refreshEngine(window, values['engineselection'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)
                doPropulsionCalculations(window)

            if event == 'boosterselection':
                refreshBooster(window, values['boosterselection'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)
                doPropulsionCalculations(window)

            if event == 'shieldselection':
                refreshShield(window, values['shieldselection'], values['shieldadjustsetting'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)

            if event == 'frontarmorselection':
                refreshFrontArmor(window, values['frontarmorselection'])
                updateMassStrings(chassisMass, window)
            
            if event == 'reararmorselection':
                refreshRearArmor(window, values['reararmorselection'])
                updateMassStrings(chassisMass, window)

            if event == 'diselection':
                refreshDI(window, values['diselection'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)

            if event == 'chselection':
                refreshCH(window, values['chselection'])
                updateMassStrings(chassisMass, window)

            if event == 'capselection':
                refreshCapacitor(window, values['capselection'])
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)
                doWeaponCalculations(window)

            if 'pack' in event:
                refreshPack(window, values[event], int(event[4]))
                doWeaponCalculations(window)
            elif 'slot' in event:
                refreshSlot(window, values[event], int(event[4]))
                updateMassStrings(chassisMass, window)
                updateDrainStrings(window)
                doWeaponCalculations(window)

            if event == 'reactoroverloadlevel' or event == 'engineoverloadlevel' or event == 'capacitoroverchargelevel' or event == 'weaponoverloadlevel':
                updateOverloadMults(window)
                updateDrainStrings(window)
                doWeaponCalculations(window)
                doPropulsionCalculations(window)
            
            if event == 'shieldadjustsetting':
                updateOverloadMults(window)
                refreshShield(window, values['shieldselection'], values['shieldadjustsetting'])

            if event == 'About':
                #Need to update the alert function somehow to allow making clickable hyperlinks. Looks like it's gonna be a pain, though.
                alert("About",["Seraph's Loadout Tool Version " + currentVersion + " ALPHA ",'©2024 SeraphExodus','','My Discord: seraphexodus','My Channel: https://discord.gg/nyXhfa5YkG'],['Got it!'],0)

            if event == 'Keyboard Shortcuts':
                alert("Keyboard Shortcuts",['• Ctrl+N - New loadout', '• Ctrl+S - Save loadout', '• Ctrl+O - Open and manage loadouts','• Ctrl+A/Ctrl+M - Add and manage components','• Ctrl+X - Clear components from loadout','• Ctrl+C - Copy loadout screencap to clipboard',''],["Got it!"],0)

            if event == 'Flight Computer Calculator':
                dcs = window['didcs'].get()
                fcCalcProcess = multiprocessing.Process(target=fcCalc,args=(dcs))
                fcCalcProcess.daemon = True
                fcCalcProcess.start()

            if event == 'Reverse Engineering Calculator':
                reCalcProcess = multiprocessing.Process(target=reCalc,args=())
                reCalcProcess.daemon = True
                reCalcProcess.start()

            if event == 'Loot Lookup Tool':
                lootLookupProcess = multiprocessing.Process(target=lootLookup,args=())
                lootLookupProcess.daemon = True
                lootLookupProcess.start()

            if event == "Quit" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
                doExitSave(window)
                break

            currLoadout = window['loadoutname'].get()

            loadoutStats = [
                values['frontarmorselection'], 
                values['reararmorselection'], 
                values['boosterselection'], 
                values['capselection'], 
                values['chselection'],  
                values['diselection'], 
                values['engineselection'], 
                values['reactorselection'], 
                values['shieldselection'],  
                values['slot1selection'], 
                values['slot2selection'], 
                values['slot3selection'], 
                values['slot4selection'], 
                values['slot5selection'], 
                values['slot6selection'], 
                values['slot7selection'], 
                values['slot8selection'], 
                values['slot1packselection'], 
                values['slot2packselection'], 
                values['slot3packselection'], 
                values['slot4packselection'], 
                values['slot5packselection'], 
                values['slot6packselection'], 
                values['slot7packselection'], 
                values['slot8packselection'], 
                values['reactoroverloadlevel'], 
                values['engineoverloadlevel'], 
                values['capacitoroverchargelevel'], 
                values['weaponoverloadlevel'], 
                values['shieldadjustsetting']
                ]

            savedLoadouts = cur2.execute('SELECT * FROM loadout').fetchall()
            if savedLoadouts != []:
                menuEnables[0] = True
            else:
                menuEnables[0] = False

            try:
                loadoutLastSave = [x for x in cur2.execute('SELECT * FROM loadout WHERE name = ?', [currLoadout]).fetchall()[0]][3:]
                if loadoutStats != loadoutLastSave:
                    menuEnables[1] = True
                    menuEnables[2] = True
                elif currLoadout != '':
                    menuEnables[1] = True
                    menuEnables[2] = False
                else:
                    menuEnables[1] = False
                    menuEnables[2] = False
            except:
                menuEnables[1] = False
                menuEnables[2] = False

            window['menu'].update(setMenus(menuEnables))

        window.close()
        tables.close()
        compdb.close()

main()