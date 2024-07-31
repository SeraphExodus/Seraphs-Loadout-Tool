import FreeSimpleGUI as sg
import os
import pyglet
import sqlite3
import win32clipboard

from datetime import datetime, timedelta
from io import BytesIO
from numpy import round, ceil
from PIL import ImageGrab
from requests import get
from webbrowser import open as browserOpen
from win32gui import FindWindow, GetWindowRect

from buildTables import buildTables
from buildCompList import buildComponentList
from createLoadout import createLoadout
from fcCalcUtility import fcCalc
from importBackup import importBackupData
from manageComponents import manageComponents

currentVersion = "2.A.00"

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

headerFont = ("Roboto", 12, "bold")
summaryFont = ("Roboto", 11, "bold")
summaryFontStats = ("Roboto", 11)
baseFont = ("Roboto", 10, "bold")
baseFontStats = ("Roboto", 10, "bold")
buttonFont = ("Roboto", 13, "bold")
fontPadding = 0
elementPadding = 4
bgColor = '#202225'
boxColor = '#313338'
textColor = '#f3f4f5'
compBoxWidth = 215
rightPaneWidth = 250
topRowHeight = 160
row1Height = 210
row2Height = 240
row3Height = 240

theme_definition = {'BACKGROUND': boxColor,
                    'TEXT': textColor,
                    'INPUT': bgColor,
                    'TEXT_INPUT': textColor,
                    'SCROLL': bgColor,
                    'BUTTON': ('#e4f2ff', '#202225'),
                    'PROGRESS': ('#01826B', '#D0D0D0'),
                    'BORDER': 1,
                    'SLIDER_DEPTH': 0,
                    'PROGRESS_DEPTH' : 0}

sg.theme_add_new('Discord_Dark', theme_definition)

sg.theme('Discord_Dark')

###Notes:
#to-do:
#
#clean up functions to be a little more single-task-oriented

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

###Debug Util

def pause():
    alert('Pause',['Paused'],['Continue'],0)

###Debug Util

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

def tryFloat(x):
    try:
        y = float(x)
        return y
    except:
        return 0

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

def alert(headerText, textLines, buttons, timeout, *textSettings):
    Layout = []

    if len(textLines) > 0:
        for i in range(0,len(textLines)):
            try:
                textFont = textSettings[0][0][i]
            except:
                textFont = summaryFont
            try:
                textJust = textSettings[0][1][i]
            except:
                textJust = 'center'
            
            Line = sg.Text(textLines[i],font=textFont, background_color=bgColor)
            if textJust == 'left':
                Layout.append([Line,sg.Push(background_color=bgColor)])
            elif textJust == 'right':
                Layout.append([sg.Push(background_color=bgColor),Line])
            else:
                Layout.append([sg.Push(background_color=bgColor),Line,sg.Push(background_color=bgColor)])

    buttonList = [sg.Push(background_color=bgColor),sg.Push(background_color=bgColor)]
    if len(buttons) > 0:
        for i in buttons:
            buttonList.append(sg.Button(i,font=buttonFont, button_color=boxColor))
            buttonList.append(sg.Push(background_color=bgColor))
        buttonList.append(sg.Push(background_color=bgColor))
        Layout.append(buttonList)

    alertWindow = sg.Window(headerText,Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), background_color=bgColor)

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

def updateParts(*arg):
    #If you pass a chassis in, it updates the dynamic slot lists too. Otherwise it just updates the part lists

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    tables.close()

    return [reactorList, engineList, boosterList, shieldList, armorList, diList, chList, capList, slot1List, slot2List, slot3List, slot4List, slot5List, slot6List, slot7List, slot8List]

def verifyEntries(window):

    chassis = window['chassistype'].get()

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    if not chassis == '':
        headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])
    else:
        headers = [''] * 8
    
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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
            percentMass = round(tryFloat(totalMass)/tryFloat(chassisMass)*100,2)
            massString = str(totalMass) + " of " + str(round(float(chassisMass),1)) + " (" + str(percentMass) + "%)"
            leftoverMass = str(round(float(chassisMass) - float(totalMass),1))# + " (" + str(round(100-percentMass,2)) + "%)"
            if percentMass > 100:
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

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

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
            reactorUtilString+= " (" + str(round(tryFloat(overloadedDrain)/tryFloat(overloadedGen) * 100,2)) + "%)"
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

    tables.close()

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

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()
    headers = list(cur.execute("SELECT * FROM chassis WHERE name = ?", [chassis]).fetchall()[0][2:10])
    tables.close()

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

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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
        window[packList].update(visible=False, size=(28,10))
        window.refresh()

    compdb.close()

def getSlotStats(selection):

    ###This method is vulnerable to non-uniquely-named weap/cm/ordnance. Need to solve this somehow.

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    
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

    compdb.close()

    return [compType, output]

def refreshReactor(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    if type(component) == str and not component == "None" and not component == "":
        reactor = cur2.execute("SELECT * FROM reactor WHERE name = ?", [component]).fetchall()[0]
        reactor = displayPrecision(reactor, [1, 1])
        window['reactormass'].update(reactor[1])
        window['reactorgen'].update(reactor[2])
    else:
        window['reactormass'].update("")
        window['reactorgen'].update("")
    
    compdb.close()
    window.refresh()

def refreshEngine(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    window.refresh()

def refreshBooster(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    window.refresh()

def refreshShield(window, component, adjust):

    tables = sqlite3.connect("file:Data\\tables.db?more=ro", uri=True)
    cur = tables.cursor()

    if adjust == "None" or not type(adjust) == str:
        adjustFrontRatio = 1
    else:
        halves = adjust.split(' - ', 1)
        name = "Shield " + halves[0] + " Adjust - " + halves[1]
        adjustFrontRatio = tryFloat(cur.execute("SELECT frontshieldratio FROM fcprogram WHERE name = ?", [name]).fetchall()[0][0])

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    if type(component) == str and not component == "None" and not component == "":
        shield = cur2.execute("SELECT * FROM shield WHERE name = ?", [component]).fetchall()[0]
        shield = displayPrecision(shield, [1, 1, 1, 2])
        window['shieldred'].update(shield[1])
        window['shieldmass'].update(shield[2])
        window['shieldfshp'].update(round(tryFloat(shield[3]) * adjustFrontRatio,1))
        window['shieldbshp'].update(round(tryFloat(shield[3]) * (2 - adjustFrontRatio),1))
        window['shieldrr'].update("{:.2f}".format(shield[4]))
    else:
        window['shieldred'].update("")
        window['shieldmass'].update("")
        window['shieldfshp'].update("")
        window['shieldbshp'].update("")
        window['shieldrr'].update("")

    compdb.close()
    tables.close()
    window.refresh()

def refreshFrontArmor(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    if type(component) == str and not component == "None" and not component == "":
        armor = cur2.execute("SELECT * FROM armor WHERE name = ?", [component]).fetchall()[0]
        armor = displayPrecision(armor, [1, 1])
        window['frontarmorahp'].update(armor[1])
        window['frontarmormass'].update(armor[2])
    else:
        window['frontarmorahp'].update("")
        window['frontarmormass'].update("")

    compdb.close()
    window.refresh()

def refreshRearArmor(window, component): 

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    if type(component) == str and not component == "None" and not component == "":
        armor = cur2.execute("SELECT * FROM armor WHERE name = ?", [component]).fetchall()[0]
        armor = displayPrecision(armor, [1, 1])
        window['reararmorahp'].update(armor[1])
        window['reararmormass'].update(armor[2])
    else:
        window['reararmorahp'].update("")
        window['reararmormass'].update("")

    compdb.close()
    window.refresh()

def refreshDI(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    window.refresh()

def refreshCH(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    if type(component) == str and not component == "None" and not component == "":
        ch = cur2.execute("SELECT * FROM cargohold WHERE name = ?", [component]).fetchall()[0]
        ch = displayPrecision(ch, [1])
        window['chmass'].update(ch[1])
    else:
        window['chmass'].update("")

    compdb.close()
    window.refresh()

def refreshCapacitor(window, component):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    window.refresh()

def refreshSlot(window, component, slotID):

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    compdb.close()
    window.refresh()

    updatePacks(window, component, slot, True)

    return compType

def refreshPack(window, component, slotID, *arg):

    try:
        compType = arg[0]
    except:
        compType = "Null"

    slot = 'slot' + str(slotID)

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()
    
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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
            stats[4] = int(stats[2])
            stats[2] = "{:.3f}".format(tryFloat(ordnanceStats[2]))
            stats[3] = "{:.3f}".format(tryFloat(ordnanceStats[3]))
            window[slot + 'stat3'].update(round(tryFloat(stats[0]),1))
            window[slot + 'stat4'].update(round(tryFloat(stats[1]),1))
            window[slot + 'stat5'].update(stats[2])
            window[slot + 'stat6'].update(stats[3])
            window[slot + 'stat7'].update(stats[4])
        except:
            window[slot + 'stat3'].update(int(stats[0]))
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
    
    compdb.close()
    window.refresh()

def updateOverloadMults(window):

    event, values = window.read(timeout=0)

    roLevel = values['reactoroverloadlevel']
    eoLevel = values['engineoverloadlevel']
    coLevel = values['capacitoroverchargelevel']
    woLevel = values['weaponoverloadlevel']
    adjust = values['shieldadjustsetting']

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

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
    tables.close()

def doWeaponCalculations(window):
    event, values = window.read(timeout=0)

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

    tables.close()
    compdb.close()

def doPropulsionCalculations(window):
    event, values = window.read(timeout=0)

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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
    tables.close()
    compdb.close()

def clearLoadout(window, clearType):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    if clearType == "all":
        window['loadoutname'].update("")
        window['chassistype'].update("")
        window['loadoutmass'].update("")
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
    window.refresh()

def updateLoadoutPreview(loadout):
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    loadoutData = cur2.execute("SELECT * FROM loadout WHERE name = ?",[loadout]).fetchall()[0]
    chassis = loadoutData[1]
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

    compdb.close()
    tables.close()

    return slotText, statText

def loadLoadout(window):
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    loadoutList = listify(cur2.execute("SELECT name FROM loadout ORDER BY name ASC").fetchall())

    leftCol = [
        [sg.Push(),sg.Text("Select a Loadout", font=headerFont),sg.Push()],
        [sg.Listbox(values=loadoutList, size=(30, 24), enable_events=True, key='loadoutname', font=baseFont, select_mode="single", justification='center')]
    ]

    rightColLeft = [
        [sg.Push(),sg.Text("", font=baseFont, key='text0', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text1', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text2', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text3', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text4', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text5', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text6', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text7', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text8', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text9', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text10', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text11', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text12', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text13', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text14', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text15', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text16', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text17', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text18', p=fontPadding)],
        [sg.Push(),sg.Text("", font=baseFont, key='text19', p=fontPadding)],
    ]

    rightColRight = [
        [sg.Text("", font=baseFont, key='data0', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data1', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data2', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data3', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data4', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data5', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data6', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data7', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data8', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data9', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data10', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data11', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data12', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data13', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data14', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data15', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data16', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data17', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data18', p=fontPadding), sg.Push()],
        [sg.Text("", font=baseFont, key='data19', p=fontPadding), sg.Push()],
    ]

    rightCol = [
        [sg.Push(),sg.Text("Loadout Preview", font=headerFont),sg.Push()],
        [sg.Frame('',rightColLeft,border_width=0,p=elementPadding,s=(117,425)), sg.Frame('',rightColRight,border_width=0,p=elementPadding,s=(267,425))]
    ]

    Layout = [
        [sg.vtop(sg.Column(leftCol)), sg.vtop(sg.Frame('', rightCol, border_width=0, s=(450,425)))],
        [sg.VPush()],
        [sg.Push(),sg.Push(),sg.Button("Load", font=buttonFont),sg.Push(),sg.Button("Delete", font=buttonFont),sg.Push(),sg.Button("Cancel", font=buttonFont),sg.Push(),sg.Push()]
    ]

    loadWindow = sg.Window('Loadout Management', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    sg.theme('Discord_Dark')
    window.bind('<Escape>', 'Cancel')

    loadoutData = [''] * 34

    loaded = False

    while True:
        event, values = loadWindow.read()
        
        if event == 'loadoutname':
            slotText, statText = updateLoadoutPreview(values['loadoutname'][0])
            loadWindow['text0'].update("Loadout Name:")
            loadWindow['data0'].update(values['loadoutname'][0])
            for i in range(1,20):
                loadWindow['text' + str(i)].update(slotText[i-1])
                loadWindow['data' + str(i)].update(statText[i-1])
            loadWindow.refresh()

        if event == "Load":
            try:
                loadout = values['loadoutname'][0]
            except:
                loadout = ''
            if loadout == '':
                alert('Error',['Please select a loadout.'],['Okay'],0)
                loadWindow.TKroot.grab_set()
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

        if event == "Delete":
            try:
                loadout = values['loadoutname'][0]
            except:
                loadout = ''
            if loadout == '':
                alert('Error',['Please select a loadout.'],['Okay'],0)
                loadWindow.TKroot.grab_set()
            else:
                currentLoadout = window['loadoutname'].get()
                result = alert('Alert',['You are attempting to delete the loadout named "' + values['loadoutname'][0] + '."','Are you sure? This action cannot be undone.'],['Yes', 'Cancel'],0)
                loadWindow.TKroot.grab_set()
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

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            break

    compdb.commit()
    compdb.close()
    loadWindow.close()

    return loadoutData[1], loadoutData[2], loaded

def saveLoadout(window):
    event, values = window.read(timeout=0)

    chassis = window['loadoutname'].get()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    loadout = list(cur2.execute("SELECT * FROM loadout WHERE name = ?", [chassis]).fetchall()[0])
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
    alert('',['Save Successful!'],[],1.5)
    compdb.commit()
    compdb.close()

def doExitSave(window):
    event, values = window.read(timeout=0)

    chassis = window['loadoutname'].get()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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
        compdb.close()

        return True
    except:
        return False

def loadExitSave(window):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

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

        compdb.close()
        return loadoutData[1], loadoutData[2], True
    
    except:
        compdb.close()
        return "", "", False

def updateProfile(window):
    events, values = window.read(timeout=0)

    chassis = window['chassistype'].get()

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()

    [minThrottle, optThrottle, maxThrottle] = cur.execute("SELECT minthrottle, optthrottle, maxthrottle FROM chassis WHERE name = ?", [chassis]).fetchall()[0]
    
    minThrottle = tryFloat(minThrottle)
    optThrottle = tryFloat(optThrottle)
    maxThrottle = tryFloat(maxThrottle)

    span = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
    percents = []

    for i in span:
        if i < optThrottle:
            percentToOptimal = i / optThrottle
            per = ((1 - minThrottle) * percentToOptimal + minThrottle)
            per = int(round(per,1) * 100)
            percents.append(per)
        else:
            percentFromOptimal = (i - optThrottle)/(1 - optThrottle)
            per = ((maxThrottle - 1) * percentFromOptimal + 1)
            per = int(round(per,1) * 100)
            percents.append(per)

    for i in range(0, 11):
        per = percents[i]
        color = getThreeColorGradient(per)
        window['text' + str(i * 10)].update(' ' + str(i * 10) + '%')
        window['pyr' + str(i * 10)].update(' ' + str(per) + '%', text_color=bgColor, background_color=color)
        window['frame' + str(i * 10)].Widget.config(background=color, borderwidth=1)
        window['textframe' + str(i * 10)].Widget.config(borderwidth=1)

    window['throttlemods'].update('Min: ' + str(minThrottle) + ' / Opt: ' + str(optThrottle) + ' / Max: ' + str(maxThrottle))
    window['profilepercentheader'].update("Throttle")
    window['profilepyrheader'].update("Max PYR")

    window.refresh()

    tables.close()

def main():

    if not os.path.exists("Data\\tables.db"):
        buildTables()

    if not os.path.exists("Data\\savedata.db"):
        buildComponentList()

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    loadouts = cur2.execute("SELECT * from loadout").fetchall()
    if loadouts == []:
        openLoadoutString = '!&Open Loadout'
    else:
        openLoadoutString = '&Open Loadout'

    Lists = updateParts()

    menu_def = [
        ['&Loadout', ['&New Loadout', openLoadoutString, '!&Save Loadout', 'E&xit']],
        ['&Components', ['Add and &Manage Components', '!&Clear All Components']],
        ['&Tools', ['&Flight Computer Calculator','&Import v1.x Data', '&Check for Updates']],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    menu_def_save_enabled = [
        ['Loadout', ['&New Loadout', '&Open Loadout', '&Save Loadout', 'E&xit']],
        ['Components', ['Add and &Manage Components', '&Clear All Components']],
        ['&Tools', ['&Flight Computer Calculator','&Import v1.x Data', '&Check for Updates']],
        ['Help', ['&Keyboard Shortcuts']]
    ]

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
        [sg.Push(),sg.Text("Front HP:", font=baseFont, p=fontPadding)],
        [sg.Push(),sg.Text("Back HP:", font=baseFont, p=fontPadding)],
        [sg.Push(),sg.Text("Recharge:", font=baseFont, p=fontPadding)],
    ]

    shieldStats = [
        [sg.Text("", key='shieldred', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='shieldmass', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='shieldfshp', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='shieldbshp', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='shieldrr', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
    ]

    powerBoxLayoutShield = [
        [sg.Text("⚡", background_color=boxColor, p=0, key='shieldpowerboxcolor', text_color=boxColor)]
    ]

    shieldBox = [
        [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("Shield", font=headerFont),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutShield,border_width=0,background_color=boxColor, s=(20,20), p=5, key='shieldpowerboxframecolor')],
        [sg.Frame('',shieldText,border_width=0,p=0,s=(compBoxWidth/2,row1Height-65)), sg.Push(),sg.Frame('',shieldStats,border_width=0,p=0,s=(compBoxWidth/2-5,row1Height-65))],
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

    slot8Text = [
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat1text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat2text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat3text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat4text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat5text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat6text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat7text')],
        [sg.Push(),sg.Text("", font=baseFont, p=fontPadding, key='slot8stat8text')],
    ]

    slot8Stats = [
        [sg.Text("", key='slot8stat1', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat2', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat3', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat4', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat5', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat6', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat7', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
        [sg.Text("", key='slot8stat8', font=baseFontStats, s=10, p=fontPadding), sg.Push()],
    ]

    powerBoxLayoutSlot8 = [
        [sg.Text("⚡", background_color=boxColor, p=0, key='slot8powerboxcolor', text_color=boxColor)]
    ]

    slot8Box = [
        [sg.Frame('',[[]],border_width=0,s=(20,20),p=5),sg.Frame('',[[sg.Push(),sg.Text("", font=headerFont, key='slot8header'),sg.Push()]],border_width=0,p=0,s=(compBoxWidth-65,28)),sg.Frame('',powerBoxLayoutSlot8,border_width=0,background_color=boxColor, s=(20,20), p=5, key='slot8powerboxframecolor')],
        [sg.Frame('',slot8Text,border_width=0,p=0,s=(compBoxWidth/2,row3Height-85)), sg.Push(),sg.Frame('',slot8Stats,border_width=0,p=0,s=(compBoxWidth/2-5,row3Height-85))],
        [sg.VPush()],
        [sg.Combo(values = [], size=(28,10), readonly=True, key='slot8packselection', enable_events=True, font=baseFont, visible=False, background_color=bgColor)],
        [sg.Combo(values = [], size=(28,10), readonly=True, key='slot8selection', enable_events=True, font=baseFont, disabled=True, background_color=bgColor)],
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
        [sg.Frame('', chassisBoxLeft,border_width=0,p=elementPadding,s=(211,topRowHeight)), sg.Frame('', chassisBoxRight,border_width=0,p=elementPadding,s=(211,topRowHeight))]
    ]

    overloadsTextColumn = [
        [sg.Push(), sg.Text("Reactor Overload:", font=baseFont, p=fontPadding)],
        [sg.Push(), sg.Text("Engine Overload:", font=baseFont, p=fontPadding)],
        [sg.Push(), sg.Text("Capacitor Overcharge:", font=baseFont, p=fontPadding)],
        [sg.Push(), sg.Text("Weapon Overload:", font=baseFont, p=fontPadding)],
    ]

    overloadsDropdowns = [
        [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(5,5), readonly=True, key='reactoroverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()],
        [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(5,5), readonly=True, key='engineoverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()],
        [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(5,5), readonly=True, key='capacitoroverchargelevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()],
        [sg.Combo([4, 3, 2, 1, "None"], default_value="None", s=(5,5), readonly=True, key='weaponoverloadlevel', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()],
    ]

    overloadDescriptions1 = [
        [sg.Push(),sg.Text("",font=baseFont,key='reactoroverloaddesc1',p=fontPadding)],
        [sg.Push(),sg.Text("",font=baseFont,key='engineoverloaddesc1',p=fontPadding)],
        [sg.Push(),sg.Text("",font=baseFont,key='capoverloaddesc1',p=fontPadding)],
        [sg.Push(),sg.Text("",font=baseFont,key='weaponoverloaddesc1',p=fontPadding)],
    ]

    overloadDescriptions2 = [
        [sg.Text("",font=baseFont,key='reactoroverloaddesc2',p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='engineoverloaddesc2',p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='capoverloaddesc2',p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='weaponoverloaddesc2',p=fontPadding),sg.Push()],
    ]

    overloadDescriptions3 = [
        [sg.Push(),sg.Text("",font=baseFont,p=fontPadding),sg.Push()],
        [sg.Push(),sg.Text("",font=baseFont,key='engineoverloaddesc3',p=fontPadding)],
        [sg.Push(),sg.Text("",font=baseFont,key='capoverloaddesc3',p=fontPadding)],
        [sg.Push(),sg.Text("",font=baseFont,key='weaponoverloaddesc3',p=fontPadding)],
    ]

    overloadDescriptions4 = [
        [sg.Text("",font=baseFont,p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='engineoverloaddesc4',p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='capoverloaddesc4',p=fontPadding),sg.Push()],
        [sg.Text("",font=baseFont,key='weaponoverloaddesc4',p=fontPadding),sg.Push()],
    ]

    adjSubframeLeft = [
        [sg.Push(), sg.Text("Shield Adjust:", font=baseFont, p=fontPadding)]
    ]

    adjSubframeMid = [
        [sg.Combo(["Front - Extreme", "Front - Heavy", "Front - Moderate", "Front - Light", "None", "Rear - Light", "Rear - Moderate", "Rear - Heavy", "Rear - Extreme"], default_value="None", s=(14,9), readonly=True, key='shieldadjustsetting', enable_events=True, font=baseFont, disabled=True, background_color=bgColor, p=fontPadding), sg.Push()]
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
        [sg.Frame('',overloadsTextColumn, border_width=0, p=elementPadding, s=(150,topRowHeight-75)), sg.Frame('',overloadsDropdowns, border_width=0, p=0,s=(60,topRowHeight-75)), sg.Frame('',overloadDescriptions1, border_width=0, p=0,s=(75,topRowHeight-75)), sg.Frame('',overloadDescriptions2, border_width=0, p=0,s=(35,topRowHeight-75)), sg.Frame('',overloadDescriptions3, border_width=0, p=0,s=(70,topRowHeight-75)), sg.Frame('',overloadDescriptions4, border_width=0, p=0,s=(35,topRowHeight-75))],
        [sg.Frame('',adjSubframeLeft,border_width=0,p=elementPadding,s=(87,30)),sg.Frame('',adjSubframeMid,border_width=0,p=0,s=(123,30)),sg.Frame('',adjSubframeRight1,border_width=0,p=0,s=(75,30)),sg.Frame('',adjSubframeRight2,border_width=0,p=0,s=(35,30)),sg.Frame('',adjSubframeRight3,border_width=0,p=0,s=(70,30)),sg.Frame('',adjSubframeRight4,border_width=0,p=0,s=(35,30))]
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
        [sg.Frame('',capSummaryLeft,border_width=0,p=elementPadding,s=(compBoxWidth/2+12,topRowHeight)),sg.Frame('',capSummaryRight,border_width=0,p=elementPadding,s=(compBoxWidth/2-28,topRowHeight))],
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
        [sg.Frame('',weaponSummaryBoxLeft,border_width=0,p=elementPadding,s=(rightPaneWidth/2-12,200)), sg.Frame('',weaponSummaryBoxCenter,border_width=0,p=(0,4),s=(rightPaneWidth/5+8,200)),sg.Frame('',weaponSummaryBoxRight,border_width=0,p=(0,4),s=(rightPaneWidth/5+8,200)), sg.Frame('',[[]],border_width=0,p=0,s=(rightPaneWidth/10-12,200))],
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
        [sg.Frame('',propulsionSummaryLeft, border_width=0, p=elementPadding, s=(rightPaneWidth/2-12,170)),sg.Frame('',propulsionSummaryRight, border_width=0, p=elementPadding, s=(rightPaneWidth/2-4,170))],
    ]

    profilePercentCol = [
        [sg.Push(),sg.Text("",font=baseFont,p=1, key='profilepercentheader'),sg.Push()],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text0')]],border_width=0,p=1,s=(80,20),key='textframe0', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text10')]],border_width=0,p=1,s=(80,20),key='textframe10', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text20')]],border_width=0,p=1,s=(80,20),key='textframe20', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text30')]],border_width=0,p=1,s=(80,20),key='textframe30', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text40')]],border_width=0,p=1,s=(80,20),key='textframe40', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text50')]],border_width=0,p=1,s=(80,20),key='textframe50', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text60')]],border_width=0,p=1,s=(80,20),key='textframe60', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text70')]],border_width=0,p=1,s=(80,20),key='textframe70', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text80')]],border_width=0,p=1,s=(80,20),key='textframe80', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text90')]],border_width=0,p=1,s=(80,20),key='textframe90', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='text100')]],border_width=0,p=1,s=(80,20),key='textframe100', element_justification='center')],
    ]

    profilePYRCol = [
        [sg.Push(),sg.Text("",font=baseFont,p=1, key='profilepyrheader'),sg.Push()],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr0')]],border_width=0,p=1,s=(80,20),key='frame0', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr10')]],border_width=0,p=1,s=(80,20),key='frame10', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr20')]],border_width=0,p=1,s=(80,20),key='frame20', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr30')]],border_width=0,p=1,s=(80,20),key='frame30', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr40')]],border_width=0,p=1,s=(80,20),key='frame40', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr50')]],border_width=0,p=1,s=(80,20),key='frame50', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr60')]],border_width=0,p=1,s=(80,20),key='frame60', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr70')]],border_width=0,p=1,s=(80,20),key='frame70', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr80')]],border_width=0,p=1,s=(80,20),key='frame80', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr90')]],border_width=0,p=1,s=(80,20),key='frame90', element_justification='center')],
        [sg.Frame('',[[sg.Text("",font=baseFont,p=fontPadding,key='pyr100')]],border_width=0,p=1,s=(80,20),key='frame100', element_justification='center')],
    ]

    profileFrame = [
        [sg.Push(),sg.Text("Throttle Profile",font=headerFont,p=elementPadding),sg.Push()],
        [sg.Push(),sg.Text("",font=baseFont,p=fontPadding, key='throttlemods'),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',profilePercentCol,border_width=0,p=0, s=(rightPaneWidth/3,300)),sg.Frame('',profilePYRCol,border_width=0,p=0,s=(rightPaneWidth/3,300)),sg.Push()],
        [sg.VPush()]
    ]

    signatureFrame = [
        [sg.VPush()],
        [sg.Push(),sg.Text("Seraph's Loadout Tool v2.0 ::ALPHA::", font=baseFont, p=fontPadding),sg.Push()],
        [sg.Push(),sg.Text("©2024 SeraphExodus", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Text("Use Ctrl + C to take a screenshot!", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()]
    ]

    rightPane = [
        [sg.Frame('', weaponSummaryBox, border_width=0, p=elementPadding, s=(rightPaneWidth,235))],
        [sg.Frame('', propulsionSummaryBox, border_width=0, p=elementPadding, s=(rightPaneWidth,195))],
        [sg.Frame('', profileFrame, border_width=0, p=elementPadding, s=(rightPaneWidth, 333))],
        [sg.Frame('', signatureFrame, border_width=0, p=elementPadding, s=(rightPaneWidth,87))]
    ]

    leftPane = [
        [sg.Frame('', chassisBox, border_width=0, p=elementPadding, s=(438, topRowHeight)),sg.Frame('', overloadsFrame, border_width=0, p=elementPadding, s=(438,topRowHeight)),sg.Frame('', capSummaryBox, border_width=0, p=elementPadding, s=(compBoxWidth,topRowHeight)),],
        [sg.Column(loadoutBank, background_color=bgColor, expand_y=True, p=0)],
    ]
    
    layout = [
        [sg.Menu(menu_def, key='menu', text_color='#000000', disabled_text_color="#999999", background_color='#ffffff')],
        [sg.vtop(sg.Column(leftPane, background_color=bgColor, p=0)),sg.vtop(sg.Column(rightPane, background_color=bgColor, p=0))],
    ]

    window = sg.Window("Seraph's Loadout Tool v2.0 Alpha",layout, finalize=True, background_color=bgColor, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), margins=(10, 10), enable_close_attempted_event=True)
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
        window['menu'].update(menu_def_save_enabled)
        chassis = newChassis
        chassisMass = newChassisMass
        updateProfile(window)

    try:
        gist = get(versionURL).text.split('\n\n')
        latestVersion = gist[0]
        latestURL = gist[1]
    except:
        latestVersion = 0
        latestURL = ''

    if not latestVersion == 0:
        if latestVersion != currentVersion:
            result = alert("Alert",['Your version of the Loadout Tool appears to be out of date.', 'Click below to get the most recent version.',""],['Get Newest Version','Continue Anyway'],0)
            if result == 'Get Newest Version':
                browserOpen(latestURL)
                window.close()
                return

    while True:
        event, values = window.read()
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
                window['menu'].update(menu_def_save_enabled)
                chassis = newChassis
                chassisMass = newChassisMass
                updateProfile(window)

        if event == 'Save Loadout':
            saveLoadout(window)

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
                window['menu'].update(menu_def_save_enabled)
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
                        webbrowser.open(latestURL)
                        window.close()
                        return
                else:
                    alert("Alert",["Your version (" + latestVersion + ") is up to date."],[],5)

        if event == 'Clear All Components':
            result = alert("Alert", ['Are you sure? This will overwrite all currently-inputted components and FC program settings.'], ['Yes','Cancel'], 0)
            if result == "Yes":
                clearLoadout(window, "parts")

        if event == 'Capture Screenshot':
                appWindow = FindWindow(None, "Seraph's Loadout Tool v2.0 Alpha")
                rect = GetWindowRect(appWindow)
                rect = (rect[0]+8, rect[1]+51, rect[2]-8, rect[3]-8)
                grab = ImageGrab.grab(bbox=rect)
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

        if event == 'slot1selection':
            refreshSlot(window, values['slot1selection'], 1)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)

        if event == 'slot1packselection':
            refreshPack(window, values['slot1packselection'], 1)
            doWeaponCalculations(window)

        if event == 'slot2selection':
            refreshSlot(window, values['slot2selection'], 2)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)

        if event == 'slot2packselection':
            refreshPack(window, values['slot2packselection'], 2)
            doWeaponCalculations(window)

        if event == 'slot3selection':
            refreshSlot(window, values['slot3selection'], 3)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)
        
        if event == 'slot3packselection':
            refreshPack(window, values['slot3packselection'], 3)
            doWeaponCalculations(window)

        if event == 'slot4selection':
            refreshSlot(window, values['slot4selection'], 4)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)
        
        if event == 'slot4packselection':
            refreshPack(window, values['slot4packselection'], 4)

        if event == 'slot5selection':
            refreshSlot(window, values['slot5selection'], 5)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)

        if event == 'slot5packselection':
            refreshPack(window, values['slot5packselection'], 5)
            doWeaponCalculations(window)

        if event == 'slot6selection':
            refreshSlot(window, values['slot6selection'], 6)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)

        if event == 'slot6packselection':
            refreshPack(window, values['slot6packselection'], 6)
            doWeaponCalculations(window)

        if event == 'slot7selection':
            refreshSlot(window, values['slot7selection'], 7)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)

        if event == 'slot7packselection':
            refreshPack(window, values['slot7packselection'], 7)
            doWeaponCalculations(window)

        if event == 'slot8selection':
            refreshSlot(window, values['slot8selection'], 8)
            updateMassStrings(chassisMass, window)
            updateDrainStrings(window)
            doWeaponCalculations(window)

        if event == 'slot8packselection':
            refreshPack(window, values['slot8packselection'], 8)
            doWeaponCalculations(window)

        if event == 'reactoroverloadlevel' or event == 'engineoverloadlevel' or event == 'capacitoroverchargelevel' or event == 'weaponoverloadlevel':
            updateOverloadMults(window)
            updateDrainStrings(window)
            doWeaponCalculations(window)
        
        if event == 'shieldadjustsetting':
            updateOverloadMults(window)
            refreshShield(window, values['shieldselection'], values['shieldadjustsetting'])

        if event == 'Keyboard Shortcuts':
            alert("Keyboard Shortcuts",['• Ctrl+N - New loadout', '• Ctrl+S - Save loadout', '• Ctrl+O - Open and manage loadouts','• Ctrl+A/Ctrl+M - Add and manage components','• Ctrl+X - Clear components from loadout','• Ctrl+C - Copy loadout screencap to clipboard',''],["Got it!"],0)

        if event == 'Flight Computer Calculator':
            fcCalc(window)

        if event == "Quit" or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            doExitSave(window)
            break

    window.close()

main()