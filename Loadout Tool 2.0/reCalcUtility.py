import FreeSimpleGUI as sg
import math
import os
import sqlite3
import win32clipboard

from datetime import datetime, timedelta
from io import BytesIO
from PIL import ImageGrab
from win32gui import FindWindow, GetWindowRect

import pyglet

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

sg.theme_add_new('Discord_Dark', theme_definition)

sg.theme('Discord_Dark')

global tables
global cur
global compdb
global cur2

tables = sqlite3.connect("file:tables.db?mode=ro", uri=True)
cur = tables.cursor()

compdb = sqlite3.connect("file:"+os.getenv("APPDATA")+"\\Seraph's Loadout Tool\\savedata.db?mode=rw", uri=True)
cur2 = compdb.cursor()

def remodalize(window):
    try:
        window.TKroot.grab_set()
    except:
        pass

def listify(x):
    xnew = []
    for i in x:
        xnew.append(i[0])
    return xnew

def tryFloat(x):
    try:
        return float(x)
    except:
        return 0
    
def tryInt(x):
    try:
        return int(x)
    except:
        return 0
    
def generateThreshold(partLevel, unicornStat, unicornPost):

    means, mods, stdevs, weights = pullStatsData(partLevel)

    compTypes = ['Armor', 'Booster', 'Capacitor', 'Droid Interface', 'Engine', 'Reactor', 'Shield', 'Weapon']
    for i in compTypes:
        if i[0] == partLevel[0]:
            compType = i

    if unicornStat == 0:
        tail = 1
    elif unicornStat == 1 and partLevel[0] == 'A':
        tail = -1
    else:
        tailStat = 'stat' + str(unicornStat) + 're'
        tail = int(cur.execute('SELECT ' + tailStat + ' FROM component WHERE type = ?', [compType]).fetchall()[0][0])

    reLevel = tryInt(partLevel[1])
    if reLevel == 0:
        reLevel = 10
    reLevel -= 1

    reMults = [0.02, 0.03, 0.03, 0.04, 0.04, 0.05, 0.05, 0.06, 0.07, 0.07]
    reMult = reMults[reLevel]

    reMult = 1 + tail * reMult

    threshold = getRarity(unicornPost/reMult, means[unicornStat], stdevs[unicornStat], weights)

    count = sum([tryInt(x[0]) for x in cur.execute('SELECT weight FROM brands WHERE relevel = ?', [partLevel]).fetchall()])

    if tail == 1:
        threshold = (1 - threshold) * count
    else:
        threshold *= count

    return threshold
    
def delta2Hex(logDeltas, threshold):

    points = [0.5, 2, 3, 4, 5]

    points = [x * threshold for x in points]

    colors = ['00ff00', '88ff00', 'ffff00', 'ff8800', 'ff0000']

    reds = []
    greens = []
    blues = []

    hexColors = []

    for i in colors:
        reds.append(int(i[0:2],16))
        greens.append(int(i[2:4],16))
        blues.append(int(i[4:6],16))

    for i in logDeltas:
        try:
            logDelta = abs(i)
            if logDelta <= points[0]:
                red = reds[0]
                green = greens[0]
                blue = blues[0]
            elif logDelta >= points[-1]:
                red = reds[-1]
                green = greens[-1]
                blue = blues[-1]
            else:
                for j in range(0,len(points)-1):
                    if logDelta > points[j] and logDelta <= points[j+1]:
                        percentage = (logDelta - points[j])/(points[j+1]-points[j])
                        red = round((reds[j+1]-reds[j])*percentage + reds[j])
                        green = round((greens[j+1]-greens[j])*percentage + greens[j])
                        blue = round((blues[j+1]-blues[j])*percentage + blues[j])
            red = hex(red)[2:]
            green = hex(green)[2:]
            blue = hex(blue)[2:]
            if len(red) < 2:
                    red = '0' + red
            elif red == '':
                red = '00'
            if len(green) < 2:
                green = '0' + green
            elif green == '':
                green = '00'            
            if len(blue) < 2:
                blue = '0' + blue
            elif blue == '':
                blue = '00'
            color = '#' + red + green + blue
            hexColors.append(color)
        except:
            hexColors.append('#ffffff')
        
    return hexColors
        
def normalCDF(Z):
    try:
        y = 0.5 * (1 + math.erf(Z/math.sqrt(2)))
        return y
    except:
        SyntaxError
    
def logMean(values):
    total = 0
    for i in values:
        try:
            total += math.log10(i)/len(values)
        except:
            pass
    output = math.pow(10,total)
    return output
    
def toClipboard(type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(type, data)
    win32clipboard.CloseClipboard()

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

def pause():
    alert('Pause',['Paused'],['Continue'],0)

def pullStatsData(reLevel):

    brandWeights = listify(cur.execute("SELECT weight FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    rawMeans = cur.execute("SELECT stat1mean, stat2mean, stat3mean, stat4mean, stat5mean, stat6mean, stat7mean, stat8mean, stat9mean FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    rawMods = cur.execute("SELECT stat1mod, stat2mod, stat3mod, stat4mod, stat5mod, stat6mod, stat7mod, stat8mod, stat9mod FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    means = []
    mods = []
    stdevs = []
    
    for i in range(0,len(rawMeans[0])):
        newRowStdevs = []
        newRowMeans = []
        newRowMods = []
        for j in range(0,len(rawMeans)):
            newRowStdevs.append(tryFloat(rawMeans[j][i]) * tryFloat(rawMods[j][i]) / 2)
            newRowMeans.append(tryFloat(rawMeans[j][i]))
            newRowMods.append(tryFloat(rawMods[j][i]))
        stdevs.append(newRowStdevs)
        means.append(newRowMeans)
        mods.append(newRowMods)

    mixtureWeights = []
    totalCount = 0
    
    for i in brandWeights:
        totalCount += tryInt(i)

    for i in brandWeights:
        mixtureWeights.append(tryFloat(i)/totalCount)

    return means, mods, stdevs, mixtureWeights

def getRarity(x, means, stdevs, mixtureWeights):
    rarity = 0
    try:
        for i in range(0,len(means)):
            mean = means[i]
            stdev = stdevs[i]
            zScore = (x - mean) / stdev
            cdf = normalCDF(zScore)
            rarity += cdf * mixtureWeights[i]
        rarity = float(rarity)
    except:
        rarity = ''
    return rarity

def bestCaseWorstCase(x,digits,tail,reMult,means,stdevs,mixtureWeights):

    if float(tail) > 0:
        add = 0.49999999 * math.pow(10,-digits)
        subtract = 0.5 * math.pow(10,-digits)
    else:
        add = -0.5 * math.pow(10,-digits)
        subtract = -0.49999999 * math.pow(10,-digits)

    best = x + add
    worst = x - subtract

    roundingDigits = min(digits,2)

    bestPost = round(best * reMult,roundingDigits)
    midPost = round(x * reMult,roundingDigits)
    worstPost = round(worst * reMult,roundingDigits)

    if digits == 3:
        bestPostRaw = (bestPost - subtract*10) / reMult
        midPostRaw = (midPost - subtract*10) / reMult
    else:
        bestPostRaw = (bestPost - subtract) / reMult
        midPostRaw = (midPost - subtract) / reMult

    bestCutoff = getRarity(best,means,stdevs,mixtureWeights)
    bestPostCutoff = getRarity(bestPostRaw,means,stdevs,mixtureWeights)
    midPostCutoff = getRarity(midPostRaw,means,stdevs,mixtureWeights)
    worstCutoff = getRarity(worst,means,stdevs,mixtureWeights)

    span = bestCutoff - worstCutoff

    if span == 0:
        posts = ['', '']
        percents = ['', '']
    elif worstPost == bestPost:
        posts = [bestPost, bestPost]
        percents = [float(100), float(100)]
    elif midPost == worstPost or midPost == bestPost:
        posts = [worstPost, bestPost]
        percentLow = (bestPostCutoff-worstCutoff)/span * 100
        percentHigh = (bestCutoff-bestPostCutoff)/span * 100
        percents = [percentLow, percentHigh]
    else:
        posts = [worstPost, midPost, bestPost]
        percentLow = (midPostCutoff-worstCutoff)/span * 100
        percentMid = (bestPostCutoff-midPostCutoff)/span * 100
        percentHigh = (bestCutoff-bestPostCutoff)/span * 100
        percents = [percentLow, percentMid, percentHigh]

    return bestPost, worstPost, posts, percents

def bestCaseWorstCaseVsRefire(x,tail,reMult,means,stdevs,mixtureWeights):

    if float(tail) > 0:
        add = 0.49999999 * math.pow(10,-3)
        subtract = 0.5 * math.pow(10,-3)
    else:
        add = 0.5 * math.pow(10,-3)
        subtract = 0.49999999 * math.pow(10,-3)

    bestCasePreRounded = round(x + add,2)
    worstCasePreRounded = round(x - subtract,2)

    bestPost = round(bestCasePreRounded * reMult,2)
    worstPost = round(worstCasePreRounded * reMult,2)

    if worstPost != bestPost:
        posts = [worstPost, bestPost]
        bestRarity = getRarity(x+add,means,stdevs,mixtureWeights)
        midRarity = getRarity(x,means,stdevs,mixtureWeights)
        worstRarity = getRarity(x-subtract,means,stdevs,mixtureWeights)
        span = bestRarity-worstRarity
        percentLow = (midRarity-worstRarity)/span * 100
        percentHigh = (bestRarity-midRarity)/span * 100
        percents = [percentLow, percentHigh]
    else:
        posts = [bestPost, bestPost]
        percents = [float(100), float(100)]

    return bestPost, worstPost, posts, percents

def formatRarity(rarity):
    if type(rarity) == str or rarity == 0:
        return ''
    if rarity > 0 and rarity <= 1:
        rarity = 1
    else:
        rarity = int(rarity)
    if rarity >= 100000000000:
        rarity = 'Improbable'
    elif rarity >= 10000000000:
        rarity = '1 in ' + str(int(round(rarity/1000000000,0))) + 'B'
    elif rarity >= 1000000000:
        rarity = '1 in ' + str(round(rarity/1000000000,1)) + 'B'
    elif rarity >= 10000000:
        rarity = '1 in ' + str(int(round(rarity/1000000,0))) + 'M'
    elif rarity >= 1000000:
        rarity = '1 in ' + str(round(rarity/1000000,1)) + 'M'
    elif rarity >= 10000:
        rarity = '1 in ' + str(int(round(rarity/1000,0))) + 'k'
    elif rarity >= 1000:
        rarity = '1 in ' + str(round(rarity/1000,1)) + 'k'
    else:
        rarity = '1 in ' + str(int(round(rarity,0)))
    return rarity

def worstCaseVsRefire(x,stat,reMult):
    if "Refire" in stat:
        reMult = 1-reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = min([preRound, postRound])
        worstCasePost = target + 0.00499999
        toRaw = worstCasePost/reMult
        if round(toRaw,2) < toRaw:
            worstCase = float(round(toRaw,2)+ 0.00499999)
        else:
            worstCase = float(toRaw)
    elif "Vs. Shields" in stat or "Vs. Armor" in stat:
        reMult = 1+reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = max([preRound, postRound])
        worstCasePost = target - 0.005
        toRaw = worstCasePost/reMult
        if round(toRaw,2) > toRaw:
            worstCase = float(round(toRaw,2)-0.005)
        else:
            worstCase = float(toRaw)
    else:
        worstCase = x
    return worstCase

def worstCaseVsRefireMin(x,stat,reMult):
    if "Refire" in stat:
        reMult = 1-reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = min([preRound, postRound])
        worstCasePost = target + 0.00499999
        toRaw = worstCasePost/reMult
        if round(toRaw,2) < toRaw:
            worstCase = float(round(toRaw,2)+ 0.004)
        else:
            worstCase = float(toRaw)
    elif "Vs. Shields" in stat or "Vs. Armor" in stat:
        reMult = 1+reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = max([preRound, postRound])
        worstCasePost = target - 0.005
        toRaw = worstCasePost/reMult
        if round(toRaw,2) > toRaw:
            worstCase = float(round(toRaw,2)-0.005)
            worstCase += 0.001
        else:
            worstCase = float(toRaw)
    else:
        worstCase = x
    return worstCase

def bestCaseVsRefireMax(x,stat,reMult):
    if "Refire" in stat:
        reMult = 1-reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = min([preRound, postRound])
        bestCasePost = target - 0.005
        toRaw = bestCasePost/reMult
        if round(toRaw,2) < toRaw:
            bestCase = float(round(toRaw,2) + 0.006)
        else:
            bestCase = float(toRaw)
    elif "Vs. Shields" in stat or "Vs. Armor" in stat:
        reMult = 1+reMult
        preRound = round(round(x,2) * reMult,2)
        postRound = round(x * reMult,2)
        target = max([preRound, postRound])
        bestCasePost = target + 0.004999999
        toRaw = bestCasePost/reMult
        if round(toRaw,2) > toRaw:
            bestCase = float(round(toRaw,2)-0.006)
        else:
            bestCase = float(toRaw)
    else:
        bestCase = x
    return bestCase

def getNextBestVsRefire(input,stat,mean,stdev,mixtureWeights,reMult):
    if input == '':
        return input
    if stat in ['Vs. Shields', 'Vs. Armor']:
        nextBest = max([round(input * (1 + reMult),2), round(round(input,2) * (1 + reMult),2)]) + 0.01
        nextBestRaw = worstCaseVsRefire(nextBest/(1+reMult),stat,reMult)
        nextBestRarity = 1 - getRarity(nextBestRaw,mean,stdev,mixtureWeights)
    elif stat == 'Refire Rate':
        nextBest = min([round(input * (1 - reMult),2), round(round(input,2) * (1 - reMult),2)]) - 0.01
        nextBestRaw = worstCaseVsRefire(nextBest/(1-reMult),stat,reMult)
        nextBestRarity = getRarity(nextBestRaw,mean,stdev,mixtureWeights)
    else:
        return input
    
    return nextBestRarity
    
def getLogDelta(a,b):
    if b <= 0:
        if a <= 0:
            return 0
        else:
            return math.log10(a)
    elif a <= 0:
        if b <= 0:
            return 0
        else:
            return math.log10(b)
    else:
        return math.log10(a) - math.log10(b)

def matchStat(means, stdevs, weights, initial, target):

    testMin = -6 * initial
    testMax = 6 * initial
    delta = 1
    value = initial
    zeroRarity = tryFloat(getRarity(0,means,stdevs,weights))

    loopCount = 0

    while delta > 0.000000000001:
        
        if loopCount > 10000:
            break

        testRarity = tryFloat(getRarity(value,means,stdevs,weights)) - zeroRarity
        if testRarity < 0:
            testRarity = 0

        if testRarity < target:
            testMin = value
            value = (testMin + testMax) / 2
        else:
            testMax = value
            value = (testMin + testMax) / 2
        
        delta = abs(testRarity - target)

        loopCount += 1
        
    return value

def getMatches(reCalcWindow):
    event, values = reCalcWindow.read(timeout=0)

    compType = values['componentselect']
    level = values['relevelselect']
    rawStats = []
    for i in range(0,9):
        if values['statinput' + str(i)] == '':
            rawStats.append('')
        else:
            if reCalcWindow['statsheader'].get() == "Input Raw Component Stats":
                rawStats.append(tryFloat(values['statinput' + str(i)]))
            else:
                rawStats.append(tryFloat(reCalcWindow['statoutput' + str(i)].get()))
    target = values['matchingtarget']

    emptyOutput = [''] * 9, [''] * 9, '', [''] * 9, [''] * 9, [''] * 9, [''] * 9, [''] * 9

    #if all input stats are blanks, return
    inputStats = 0
    for i in rawStats:
        if i != '':
            inputStats += 1
    if inputStats == 0:
        return emptyOutput

    reLevel = compType[0] + str(level%10)

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    compStats = [x[:-1] for x in compStats if x != '']
    compStatsDropdown = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][1:9])
    tails = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][9:17])
    if 'A/HP' not in compStats:
        compStats.insert(0,'A/HP')
        compStatsDropdown.insert(0,'Armor/Hitpoints')
        tails.insert(0,'1')
    
    if target == 'Shield Recharge Rate':
        target = 'Recharge'
    elif target in compStatsDropdown:
        target = compStats[compStatsDropdown.index(target)]
    elif 'Shield Hitpoints' in target:
        target = target.replace('Shield Hitpoints', 'HP')

    tails = [tryFloat(y) for y in tails if y != '']

    brandNames = listify(cur.execute("SELECT name FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    
    means, mods, stdevs, mixtureWeights = pullStatsData(reLevel)

    statMeans = []

    for i in range(0,len(compStats)):
        statMean = 0
        for j in range(0,len(brandNames)):
            statMean += means[i][j]*mixtureWeights[j]
        statMeans.append(statMean)

    ###here's where I start the targeted matching
    #cases are: average, best, worst, then per-stat. Before we do anything, we need to iterate across all input stats and get their respective rarities.
    #need to apply a rectify operation I think to make everything work generally

    reMults = [0.02, 0.03, 0.03, 0.04, 0.04, 0.05, 0.05, 0.06, 0.07, 0.07]
    reMult = reMults[level-1]

    #Convert any inputted vs/refire to their worst-case value

    #Reward Cutoffs - There need to be exceptions in some cases, like w8 eps. Round the cutoff to the nearest 0.1. If vs/refire/srr, 0.01
    rewards = []
    cutoffsHigh = []
    cutoffsLow = []

    for i in range(0,len(compStats)):
        reward, lowHigh = isReward(rawStats[i],compType,level,compStats[i] + ':')
        rewards.append(reward)
        cutoffsHigh.append(lowHigh[1])
        cutoffsLow.append(lowHigh[0])

    stats = []

    for i in range(0,len(rawStats)):
        if rawStats[i] != '':
            if rewards[i]:
                stats.append(cutoffsHigh[i])
            else:
                worstCase = worstCaseVsRefire(rawStats[i],compStats[i],reMult)
                stats.append(worstCase)
        else:
            stats.append('')

    rarityList = []
    rarityList1inx = []

    for i in range(0,len(compStats)):
        if tails[i] < 0: #removes negative values from the distribution for left-tailed stats
            zeroCheck = getRarity(0,means[i],stdevs[i],mixtureWeights)
        else:
            zeroCheck = 0
        rarity = tryFloat(getRarity(stats[i],means[i],stdevs[i],mixtureWeights)) - zeroCheck
        if rarity < 0:
            rarity = 0
        if rarity == '':
            rarityList.append('')
            rarityList1inx.append('')
        elif rarity in [0, 1]:
            rarityList.append('')
            rarityList1inx.append('Improbable')
        elif tails[i] > 0:
            rarityList.append(1-rarity)
            rarityList1inx.append(int(1/(1-rarity)))
        else:
            rarityList.append(rarity)
            rarityList1inx.append(int(1/rarity))

    unicorns, unicornThreshold = isUnicorn(rarityList, reCalcWindow)

    for i in range(0,len(rarityList1inx)):
        rarityList1inx[i] = formatRarity(rarityList1inx[i])
        if compStats[i] != '' and compStats[i] in unicorns:
            rarityList1inx[i] = '⋆' + rarityList1inx[i] + '⋆'

    cutoffRaritiesHigh = []
    cutoffRaritiesLow = []
    for i in range(0,len(cutoffsHigh)):
        cutoffRarityHigh = getRarity(cutoffsHigh[i],means[i],stdevs[i],mixtureWeights)
        cutoffRarityLow = getRarity(cutoffsLow[i],means[i],stdevs[i],mixtureWeights)
        if tails[i] > 0:
            cutoffRaritiesHigh.append(1-cutoffRarityHigh)
            cutoffRaritiesLow.append(1-cutoffRarityLow)
        else:
            cutoffRaritiesHigh.append(cutoffRarityHigh)
            cutoffRaritiesLow.append(cutoffRarityLow)

    blankStats = 0
    rewardStats = 0

    for i in range(0,len(rarityList)):
        if rarityList[i] == '':
            blankStats += 1
        elif rewards[i]:
            rewardStats += 1

    for i in range(0,len(rarityList1inx)):
        if rewards[i]:
            rarityList1inx[i] = 'Reward'
        elif rarityList1inx[i] != '':
            formatRarity(rarityList1inx[i])

    #If all inputs are reward stats, or if attempting to match to a reward stat, return
    if blankStats + rewardStats == len(compStats):
        return [''] * 9, rarityList1inx, '', [''] * 9, [''] * 9, [''] * 9, [''] * 9, [''] * 9
    elif target not in ['Average Rarity', 'Best Stat', 'Worst Stat']:
        if rewards[compStats.index(target)]:
            return [''] * 9, rarityList1inx, '', [''] * 9, [''] * 9, [''] * 9, [''] * 9, [''] * 9

    nextBests = []
    nextBestStats = []

    for i in range(0,len(compStats)):
        if compStats[i] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
            nextBestRarity = getNextBestVsRefire(rawStats[i],compStats[i],means[i],stdevs[i],mixtureWeights,reMult)
            nextBests.append(nextBestRarity)
            nextBestStats.append(compStats[i])

    #NOW we get to modes.
    rarity = 0
    #First Mode: Single Stat Target. Default to average if invalid selection
    if target in compStats:
        rarity = rarityList[compStats.index(target)]
        if rarity == '':
            target = "Average Rarity"

    #Second Mode: Max/Min Targets.
    if target == 'Best Stat':
        rarityListTemp = [x for x in rarityList if rewards[rarityList.index(x)] == False and x != '']
        if rarityListTemp == []:
            target = "Average Rarity"
        else:
            rarity = min(rarityListTemp)


    if target == 'Worst Stat':
        rarityListTemp = [x for x in rarityList if rewards[rarityList.index(x)] == False and x != '']
        if rarityListTemp == []:
            target = "Average Rarity"
        else:
            rarity = max(rarityListTemp)

    if target == 'Average Rarity':
        exclude0 = []
        remainingStats = []
        rewardCutoff = []
        #0. Remove blank stats
        for i in range(0,len(rarityList)):
            if rarityList[i] != '':
                exclude0.append(rarityList[i])
                remainingStats.append(compStats[i])
                rewardCutoff.append(cutoffRaritiesHigh[i])

        #1. Remove AHP if it isn't armor, unless it's the only stat // need to rewrite this for blank stat exclusion
        # if AHP is in remaining stats, and there's an entry for AHP, and at least one entry elsewhere, exclude AHP
        if compType != 'Armor':
            if 'A/HP' in remainingStats:
                if len(remainingStats) > 1:
                    exclude1 = exclude0[1:]
                    remainingStats = remainingStats[1:]
                    rewardCutoff = rewardCutoff[1:]
                    rewardsCheck = rewards[1:]
                else:
                    exclude1 = exclude0
                    rewardsCheck = rewards
            else:
                exclude1 = exclude0
                rewardsCheck = rewards
        else:
            exclude1 = exclude0
            rewardsCheck = rewards

        #2. Remove suspected rewards based on whether or not the stat rarity surpasses the cutoff rarity
        exclude2 = []
        for i in range(0,len(exclude1)):
            if not rewardsCheck[i]:
                exclude2.append(exclude1[i])

        #3. Take first average
        average1 = logMean(exclude2)

        #4. If average is below reward cutoff rarity, exclude rewards
        exclude3 = []
        statsTemp = remainingStats
        remainingStats = []
        
        for i in range(0,len(rewardCutoff)):
            if rewards[compStats.index(statsTemp[i])]:
                if average1 < rewardCutoff[i]:
                    exclude3.append(rewardCutoff[i])
                    remainingStats.append(statsTemp[i])
            else:
                exclude3.append(exclude1[i])
                remainingStats.append(statsTemp[i])

        #Next, we exclude vs and refire if it's a weapon
        #Then take the average rarity without those stats
        #Then get the rarity of 0.01 better vs and refire to establish a range between worst case and best case for your input post
        #If the average without vs/refire falls inside the rarity band of the vs or refire, exclude it.
        ### UNLESS VS AND/OR REFIRE ARE THE ONLY INPUTS

        #For this step what we should be doing is FIRST excluding vs/refire if they are not the only stats involved, and getting the average of the rest of the stats. If they *are* the only stats involved, then we don't mess with the input.

        exclude4 = []

        for i in range(0,len(remainingStats)):
            if remainingStats[i] not in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
                exclude4.append(exclude3[i])
            if statsTemp == []:
                exclude4 = exclude3

        #Exclude4 is only used to get average2. Nothing else.
        statsTemp = remainingStats
        remainingStats = []

        average2 = logMean(exclude4)

        if compType == 'Weapon':
            exclude5 = []
            for i in range(0,len(statsTemp)):
                index = compStats.index(statsTemp[i])
                if statsTemp[i] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
                    inputStat = rawStats[index]
                    nextBestRarity = getNextBestVsRefire(inputStat,statsTemp[i],means[index],stdevs[index],mixtureWeights,reMult)
                    if average2 <= nextBestRarity:
                        exclude5.append(nextBestRarity)
                    elif average2 >= exclude3[i]:
                        exclude5.append(exclude3[i])
                    remainingStats.append(statsTemp[i])
                else:
                    exclude5.append(exclude3[i])
                    remainingStats.append(statsTemp[i])
        else:
            exclude5 = exclude3
            remainingStats = statsTemp

        average3 = logMean(exclude5)

        #and then we have to handle how selected matching target is used down below. Need to check input tail based on input matching target, which is easy enough with indexing for named stats. For average, it's -1.
        #that said, every stat in the rarity list is pre-rectified. getRarity isn't set up to rectify though. Basically, we need to see if it's a stat with +1 tail, if so, rectify it. If not, do nothing.

        ### vvvv Average Rarity Target vvvv ###
        rarity = average3

    if rarity == 0:
        return emptyOutput

    #All this shit down here is naive to how we do the inputs vvv. What matters is the target rarity we feed in. It will do the rest just fine. ^^^ Up here we have to get the target rarity

    #Account for weird shit on vs/refire matching by rounding up/down to .xxx for those stats respectively

    if target in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
        rarity = round(rarity - 0.0000000000005,12)

    matches = []
    matchesRaw = []
    postRE = []

    for i in range(0,len(compStats)):

        if tails[i] < 0:
            targetRarity = rarity
        else:
            targetRarity = 1-rarity

        delta = 1
        value = statMeans[i]
        testMin = -6 * statMeans[i]
        testMax = 6 * statMeans[i]

        loopCount = 0

        while delta > 0.000000000001:
            if loopCount > 10000:
                break
            if tails[i] < 0: #removes negative values from distribution for left-tailed stats
                zeroMass = getRarity(0,means[i],stdevs[i],mixtureWeights)
                testRarity = getRarity(value,means[i],stdevs[i],mixtureWeights) - zeroMass
                if rarity < 0:
                    testRarity = 0
            else:
                testRarity = getRarity(value,means[i],stdevs[i],mixtureWeights)

            if testRarity < targetRarity:
                testMin = value
                value = (testMin + testMax) / 2
            else:
                testMax = value
                value = (testMin + testMax) / 2
            
            delta = abs(testRarity - targetRarity)
            loopCount += 1
        
        if compStats[i] in ['Vs. Shields','Vs. Armor','Refire Rate']:
            multiplier = 1 + reMult * tryFloat(tails[i])
            postNotRounded = float(round(value * multiplier,2))
            postPreRounded = float(round(round(value,2) * multiplier,2))
            if compStats[i] == 'Refire Rate':
                sign = '<'
                optimal = min(postPreRounded,postNotRounded)
                optimalWorstCase = optimal + 0.005
                optWorstCaseRaw = optimalWorstCase / multiplier
                if round(optWorstCaseRaw,2) > optWorstCaseRaw:
                    worstCaseRaw = round(optWorstCaseRaw,3) - 0.001
                else:
                    worstCaseRaw = round(optWorstCaseRaw,2) + 0.004
            else:
                sign = '>'
                optimal = max(postPreRounded,postNotRounded)
                optimalWorstCase = optimal - 0.00499999
                optWorstCaseRaw = optimalWorstCase / multiplier
                if round(optWorstCaseRaw,2) < optWorstCaseRaw:
                    worstCaseRaw = round(optWorstCaseRaw,3) + 0.001
                else:
                    worstCaseRaw = round(optWorstCaseRaw,2) - 0.004
            matches.append(sign + "{:.3f}".format(worstCaseRaw))
            matchesRaw.append(worstCaseRaw)
            postRE.append("{:.3f}".format(optimal))
        elif compStats[i] == 'Recharge' and compType == "Shield":
            matches.append("{:.2f}".format(float(round(value,2))))
            matchesRaw.append(value)
            postRE.append("{:.2f}".format(float(round((1 + reMult * tryFloat(tails[i])) * value,2))))
        else:
            matches.append("{:.1f}".format(float(round(value,1))))
            matchesRaw.append(value)
            postRE.append("{:.1f}".format(float(round((1 + reMult * tryFloat(tails[i])) * value,1))))

    #Next step is clamping rarities to the part-level's native rarity ceiling. This is given as 10^(1/6) * the unicorn threshold.
    #I would like to scale the ceiling inversely with respect to the number of stats the component possesses. 1/3 is good for 8-9 stats but doesn't really fly for 2.
    #Correction: this wasn't really the issue. The issue I was aiming to address was the floor for unicorn matching, not the ceiling. At present, it caps out at the unicorn rarity but it needs to go higher for parts with fewer stats.
    #I think this still needs to apply though. We'll play with it.

    statScaling = len(compStats)/9

    averageClamp = unicornThreshold / pow(10,1/(3*statScaling))
    statClamp = unicornThreshold / pow(10,1/(2*statScaling))
    
    matchingRarities = []

    for i in range(0,len(rarityList)):
        if rarityList[i] not in [0, ''] and rarityList1inx[i] != 'Reward':
            if rarityList[i] < statClamp:
                matchingRarities.append(statClamp)
            else:
                matchingRarities.append(rarityList[i])

    logDelta = []
    matchingDelta = []

    if rarity < averageClamp and target == 'Average Rarity':
        matchRarity = averageClamp
    elif rarity < statClamp and target != 'Average Rarity':
        matchRarity = statClamp
    else:
        matchRarity = rarity

    for i in range(0,len(rarityList)):
        if rarityList[i] not in [0, ''] and rarityList1inx[i] != 'Reward':
            if compStats[i] in nextBestStats:
                rangeLow = rarityList[i]
                rangeHigh = nextBests[nextBestStats.index(compStats[i])]
                if rangeLow > rarity and rangeHigh < rarity:
                    logDelta.append(0)
                elif rangeLow < rarity:
                    logDelta.append(round(math.log10(rarity) - math.log10(rangeLow),2))
                elif rangeHigh > rarity:
                    logDelta.append(round(math.log10(rarity) - math.log10(rangeHigh),2))
                else:
                    logDelta.append(0)
            else:
                logDelta.append(round(math.log10(rarity) - math.log10(rarityList[i]),2))
        elif rarityList1inx[i] == 'Reward':
            if rarity < cutoffRaritiesHigh[i]:
                logDelta.append(round(math.log10(rarity) - math.log10(cutoffRaritiesHigh[i]),2))
            else:
                logDelta.append(0)
        else:
            logDelta.append('')

        if rarityList[i] not in [0, ''] and rarityList1inx[i] != 'Reward':
            if compStats[i] in nextBestStats:
                rangeLow = rarityList[i]
                rangeHigh = nextBests[nextBestStats.index(compStats[i])]
                if rangeLow < statClamp:
                    rangeLow = statClamp
                if rangeHigh < statClamp:
                    rangeHigh = statClamp
                if rangeLow > matchRarity and rangeHigh < matchRarity:
                    matchingDelta.append(0)
                elif rangeLow < matchRarity:
                    matchingDelta.append(round(math.log10(matchRarity) - math.log10(rangeLow),2))
                elif rangeHigh > matchRarity:
                    matchingDelta.append(round(math.log10(matchRarity) - math.log10(rangeHigh),2))
                else:
                    matchingDelta.append(0)
            else:
                if rarityList[i] < statClamp:
                    matchingDelta.append(round(math.log10(matchRarity) - math.log10(statClamp),2))
                else:
                    matchingDelta.append(round(math.log10(matchRarity) - math.log10(rarityList[i]),2))
        elif rarityList1inx[i] == 'Reward':
            #This might not play nice with the unicorn clamp, keep an eye on it.
            if rarity < cutoffRaritiesHigh[i]:
                matchingDelta.append(round(math.log10(matchRarity) - math.log10(cutoffRaritiesHigh[i]),2))
            else:
                matchingDelta.append(0)
        else:
            matchingDelta.append('')

    return rarityList, rarityList1inx, rarity, matches, matchesRaw, postRE, logDelta, matchingDelta

def formatStat(stat,statType,component):

    if stat == '':
        return stat
    
    stat = tryFloat(stat)

    if statType in ['Vs. Shields:', 'Vs. Armor:', 'Refire Rate:']:
        outputStat = "{:.3f}".format(stat)
    elif statType == 'Recharge:' and component == 'Shield':
        outputStat = "{:.2f}".format(stat)
    else:
        outputStat = "{:.1f}".format(stat)

    return outputStat

def formatLogDelta(logDelta):
    for i in range(0,len(logDelta)):
        try:
            logDelta[i] = "{:.2f}".format(round(logDelta[i],2))
            if float(logDelta[i]) >= 0:
                logDelta[i] = '+' + logDelta[i].replace('-','')
        except:
            pass
    return logDelta

def updateREOutputs(reCalcWindow):

    event, values = reCalcWindow.read(timeout=0)

    if values['relevelselect'] != '':
        if reCalcWindow['statsheader'].get() == "Input Raw Component Stats":
            direction = 1
        else:
            direction = -1
        reMults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
        reMult = reMults[values['relevelselect']-1]
        compStats = []
        for i in range(0,9):
            compStats.append(reCalcWindow['stattext' + str(i)].get())
        tails = list(cur.execute("SELECT stat1re,stat2re,stat3re,stat4re,stat5re,stat6re,stat7re,stat8re FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
        if values['componentselect'] != 'Armor':
            tails = ['1'] + tails
        for i in range(0,9):
            inputStat = tryFloat(values['statinput' + str(i)])
            if inputStat not in ['', 0] and tails[i] not in ['', 0]:
                multiplier = float(tails[i]) * reMult + 1
                if compStats[i] in ['Vs. Shields:','Vs. Armor:']:
                    if direction != 1:
                        inputStat = round(inputStat,2)-0.005
                        outputStat = "{:.3f}".format(min([round(inputStat / multiplier,3) + 0.001,round(inputStat / multiplier + 0.005,2)-0.004]))
                    else:
                        outputStat = "{:.3f}".format(max([round(round(inputStat,2) * multiplier,2),round(inputStat * multiplier,2)]))
                elif compStats[i] == 'Refire Rate:':
                    if direction != 1:
                        inputStat = round(inputStat,2)+0.00499999
                        outputStat = "{:.3f}".format(max([round(inputStat / multiplier,3) - 0.001,round(inputStat / multiplier - 0.00499999,2)+0.004]))
                    else:
                        outputStat = "{:.3f}".format(min([round(round(inputStat,2) * multiplier,2),round(inputStat * multiplier,2)]))
                elif compStats[i] == 'Recharge:' and values['componentselect'] == "Shield":
                    if direction != 1:
                        outputStat = "{:.2f}".format(round(inputStat / multiplier,2))
                    else:
                        outputStat = "{:.2f}".format(round(inputStat * multiplier,2))
                elif compStats[i] in ['Front HP:', 'Back HP:']:

                        if direction != 1:
                            outputStat = "{:.1f}".format(round(inputStat / multiplier,1)) 
                        else:
                            if tryFloat(values['statinput3']) > 0 and tryFloat(values['statinput4']) > 0:
                                outputStat = "{:.1f}".format(round((tryFloat(values['statinput3']) + tryFloat(values['statinput4']))/2 * multiplier,1))
                            else:
                                outputStat = "{:.1f}".format(round(inputStat * multiplier,1))                            
                else:
                    if direction != 1:
                        outputStat = "{:.1f}".format(round(inputStat / multiplier,1)) 
                    else:
                        outputStat = "{:.1f}".format(round(inputStat * multiplier,1))
                reCalcWindow['statoutput' + str(i)].update(outputStat)
            else:
                reCalcWindow['statoutput' + str(i)].update('')
    reCalcWindow.refresh()

def isUnicorn(rarityList,reCalcWindow):

    event, values = reCalcWindow.read(timeout=0)

    #Gathers a selection of unicorn thresholds for you based on the counts collected in the brandslist.csv. These will need significant tweaking.
    #Old method was using W0 max 5700 as the baseline. This allows me to incorporate a number of other archetypal unicorn stats to set a better baseline.
    thresholds = [generateThreshold('A0',1,2499.9), generateThreshold('C0',4,69), generateThreshold('E0',6,127), generateThreshold('R6',2,30000), generateThreshold('S0',3,4400), generateThreshold('W8',4,4200), generateThreshold('W0',4,5700)]
    threshold = math.pow(10,sum([math.log10(x) for x in thresholds])/len(thresholds))

    compType = values['componentselect']
    level = values['relevelselect']
    reLevel = compType[0] + str(level%10)

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    if 'A/HP:' not in compStats:
        compStats.insert(0,'A/HP:')
    
    compStats = [x for x in compStats if x != '']

    inputStats = []

    for i in range(0,len(compStats)):
        if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
            inputStats.append(values['statinput' + str(i)])
        else:
            inputStats.append(reCalcWindow['statoutput' + str(i)].get())

    #note: relevel is part-level, not just level (e.g. A0 rather than 10)
    counts = cur.execute("SELECT weight FROM brands WHERE relevel = ?",[reLevel]).fetchall()
    count = 0
    for i in counts:
        count += int(i[0])

    unicorns = []

    for i in range(0,len(rarityList)):
        if rarityList[i] != '':
            scaledRarity = rarityList[i] * count / math.sqrt(len(compStats)/9)
            reward, lohi = isReward(inputStats[i],compType,level,compStats[i])
            if scaledRarity <= threshold and not reward:
                unicorns.append(compStats[i][:-1])
            else:
                unicorns.append('')
        else:
            unicorns.append('')

    thresholdRarity = threshold / count * math.sqrt(len(compStats)/9)

    return unicorns, thresholdRarity

def updateMatchQuality(rarityList,logDeltas,reCalcWindow):

    event, values = reCalcWindow.read(timeout=0)
    compType = values['componentselect']

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    compStats = [x[:-1] for x in compStats if x != '']
    compStatsDropdown = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][1:9])
    if 'A/HP' not in compStats:
        compStats.insert(0,'A/HP')
        compStatsDropdown.insert(0,'Armor/Hitpoints')
    
    target = values['matchingtarget']

    if target == 'Shield Recharge Rate':
        target = 'Recharge'
    elif target in compStatsDropdown:
        target = compStats[compStatsDropdown.index(target)]
    elif 'Shield Hitpoints' in target:
        target = target.replace('Shield Hitpoints', 'HP')

    postsList, percentsList, rounding = reAnalysis(reCalcWindow)

    threshold = 1/6

    hexColors = delta2Hex(logDeltas, threshold)

    blanks = [x for x in logDeltas if x == '']
    for i in range(0,len(logDeltas)):
        reCalcWindow['matchquality' + str(i)].update(text_color=textColor)
        reCalcWindow['stattext' + str(i)].update(text_color=textColor)
        reCalcWindow['statinput' + str(i)].update(text_color=textColor)
        reCalcWindow['statrarity' + str(i)].update(text_color=textColor)
        reCalcWindow['logdelta' + str(i)].update(text_color=textColor)
        reCalcWindow['stattext2' + str(i)].update(text_color=textColor)
        reCalcWindow['statoutput' + str(i)].update(text_color=textColor)
        try:
            round = rounding[i][:5]
        except:
            round = ''
        if round == 'ROUND':
            reCalcWindow['matchquality' + str(i)].update('Round this!', text_color='#ff0000')
            reCalcWindow['stattext' + str(i)].update(text_color='#ff0000')
            reCalcWindow['statinput' + str(i)].update(text_color='#ff0000')
            reCalcWindow['statrarity' + str(i)].update(text_color='#ff0000')
            reCalcWindow['logdelta' + str(i)].update(text_color='#ff0000')
            reCalcWindow['stattext2' + str(i)].update(text_color='#ff0000')
            reCalcWindow['statoutput' + str(i)].update(text_color='#ff0000')
        elif logDeltas[i] != '':
            if compStats[i] == target:
                reCalcWindow['matchquality' + str(i)].update('Match Target', text_color='#ff42ff')
            elif len(blanks) != len(logDeltas) - 1:
                if abs(logDeltas[i]) < threshold:
                    reCalcWindow['matchquality' + str(i)].update('Great Match', text_color=hexColors[i])
                elif abs(logDeltas[i]) < 2 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Good Match', text_color=hexColors[i])
                elif abs(logDeltas[i]) < 3 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Borderline Match', text_color=hexColors[i])
                elif abs(logDeltas[i]) < 4 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Slight Mismatch', text_color=hexColors[i])
                elif abs(logDeltas[i]) < 5 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Moderate Mismatch', text_color=hexColors[i])
                elif abs(logDeltas[i]) < 6 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Significant Mismatch', text_color=hexColors[i])
                elif abs(logDeltas[i]) >= 6 * threshold:
                    reCalcWindow['matchquality' + str(i)].update('Critical Mismatch!', text_color=hexColors[i])
                else:
                    reCalcWindow['matchquality' + str(i)].update('', text_color=textColor)
            else:
                    reCalcWindow['matchquality' + str(i)].update('', text_color=textColor)
        else:
            reCalcWindow['matchquality' + str(i)].update('', text_color=textColor)

    if compType != 'Armor' and compStats[0] != target and values['statinput0'] != '' and rarityList != 9 * ['']:
        reCalcWindow['matchquality0'].update('Not Considered', text_color=textColor)
    
    reCalcWindow.refresh()

def brandTable(reCalcWindow, newWindow, *brandWindow):

    event, values = reCalcWindow.read(timeout=0)
    compType = values['componentselect']
    level = values['relevelselect']

    reLevel = compType[0] + str(level%10)

    tails = list(cur.execute("SELECT stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re FROM component WHERE type = ?",[compType]).fetchall()[0])
    stats = list(cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?",[compType]).fetchall()[0])
    stats = [x[:-1] for x in stats if x != '']
    if stats[0] != 'A/HP':
        stats.insert(0,'A/HP')
        tails.insert(0,1)
    
    brandsList = list(cur.execute("SELECT * FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    brandNames = list(cur.execute("SELECT name FROM brands WHERE relevel = ?", [reLevel]).fetchall())

    brandsList = [x[4:22] for x in brandsList]

    means = []
    stdevs = []

    for i in brandsList:
        newMeans = []
        newStdevs = []
        for j in range(0,len(i)):
            if i[j] != '':
                if j%2 == 0:
                    newMeans.append(float(i[j]))
                else:
                    newStdevs.append(float(i[j]) * float(i[j-1]) / 2)
        means.append(newMeans)
        stdevs.append(newStdevs)

    tempMeans = means
    tempStdevs = stdevs
    means = []
    stdevs = []

    for i in range(0,len(tempMeans[0])):
        newMeans = []
        newStdevs = []
        for j in range(0,len(tempMeans)):
            newMeans.append(tempMeans[j][i])
            newStdevs.append(tempStdevs[j][i])
        means.append(newMeans)
        stdevs.append(newStdevs)

    rarityList, rarityList1inx, rarityout, matches, matchesRaw, postRE, logDelta, matchDelta = getMatches(reCalcWindow)

    tableStats = []

    for i in range(0,len(stats)):
        if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
            if values['statinput' + str(i)] != '':
                tableStats.append(float(values['statinput' + str(i)]))
            elif matchesRaw[i] != '':
                tableStats.append(matchesRaw[i])
            else:
                tableStats.append(0)
        else:
            if reCalcWindow['statoutput' + str(i)].get() != '':
                tableStats.append(float(reCalcWindow['statoutput' + str(i)].get()))
            elif postRE[i] != '':
                tableStats.append(float(matchesRaw[i]))
            else:
                tableStats.append(0)
    
    rawTableStats = tableStats
    tableStats = []

    reMults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]

    for i in range(0,len(stats)):
        if stats[i] in ['Vs. Shields','Vs. Armor','Refire Rate']:
            tableStats.append(worstCaseVsRefire(rawTableStats[i],stats[i],reMults[level-1]))
        else:
            tableStats.append(rawTableStats[i])

    tableStats = [x for x in tableStats if x != '']

    rawRarities = []
    rarityTable = []
    rarityColors = []

    for i in range(0,len(stats)):
        brandRow = []
        rawRow = []
        x = tableStats[i]
        reward, lohi = isReward(x,compType,level,stats[i] + ':')
        for j in range(0,len(means[i])):
            mean = means[i][j]
            stdev = stdevs[i][j]
            if stats[i] in ['Vs. Shields','Vs. Armor','Refire Rate']:
                compare = round(mean,3)
            elif stats[i] == 'Recharge' and compType == 'Shield':
                compare = round(mean,2)
            else:
                compare = round(mean,1)
            if lohi != []:
                if reward and x >= min(lohi) and x <= max(lohi) and compare >= min(lohi) and compare <= max(lohi):
                    if float(tails[i]) > 0:
                        x = mean - 6 * stdev
                    else:
                        x = mean + 6 * stdev
            zScore = (x - mean) / stdev
            rawRarity = normalCDF(zScore)
            zeroRarity = normalCDF(-mean/stdev)
            if float(tails[i]) > 0:
                if rawRarity == 1:
                    rarity = '-'
                else:
                    rarity = formatRarity(1/(1-rawRarity))
                rawRarity = 1 - rawRarity
            else:
                if rawRarity <= zeroRarity:
                    rarity = '-'
                else:
                    rarity = formatRarity(1/(rawRarity-zeroRarity))
                rawRarity = min(rawRarity, rawRarity - zeroRarity)
            if rarity == 'Improbable':
                rarity = '-'
            brandRow.append(rarity)
            rawRow.append(rawRarity)
        rarityTable.append(brandRow)
        rawRarities.append(rawRow)

    basis = []

    for i in range(0,len(stats)):
        if rarityList[i] != '':
            basis.append(rarityList[i])
        else:
            basis.append(rarityout)

    for i in range(0,len(rawRarities)):
        newRow = []
        try:
            basisMax = max([x for x in rawRarities[i] if x != 0])
        except:
            basisMax = 0
        if rarityout in [0, '']:
            threshold = ''
        else:
            threshold = abs(getLogDelta(basis[i],basisMax))
        for j in range(0,len(rawRarities[i])):
            if rawRarities[i][j] == 0 or rawRarities[i][j] < math.pow(10,-11) or threshold == '':
                newRow.append('#ffffff')
            else:
                delta = getLogDelta(basis[i],rawRarities[i][j])
                if delta <= -threshold/2:
                    newRow.append('#00ffff')
                elif delta < 0:
                    newRow.append('#00ee00')
                elif delta < threshold/2:
                    newRow.append('#ffee00')
                elif delta < threshold:
                    newRow.append('#ff8800')
                else:
                    newRow.append('#ff3939')
        rarityColors.append(newRow)

    descCol = [
        [sg.Text("",font=summaryFont,p=0)],
        [sg.Push(),sg.Text("Input Stats:",font=baseFont,p=0)],
        [sg.Push(),sg.Text("Post-RE Stats:",font=baseFont,p=0)],
        [sg.Push(),sg.Text("Rarity:",font=baseFont,p=0)],
        [sg.Push(),sg.Text("Log Δ:",font=baseFont,p=0)],
        [sg.Text('',font=summaryFont,p=0)],
        [sg.Push(),sg.Text("",font=summaryFont,p=0)]
    ]

    for i in range(0,len(brandNames)):
        descCol.append([sg.Push(),sg.Text(brandNames[i][0],font=baseFont,p=0)])

    Layout = [
        [sg.Frame('',descCol,border_width=0,p=elementPadding)]
    ]

    logDelta = formatLogDelta(logDelta)

    try:
        targetRarity = formatRarity(1/rarityout)
    except:
        targetRarity = ''

    for i in range(0,len(rawTableStats)):
        if stats[i] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
            rawTableStats[i] = "{:.3f}".format(rawTableStats[i])
        elif stats[i] == 'Recharge' and compType == 'Shield':
            rawTableStats[i] = "{:.2f}".format(rawTableStats[i])
        else:
            rawTableStats[i] = "{:.1f}".format(rawTableStats[i])

    for i in range(0,len(stats)):
        newCol = [[sg.Push(),sg.Text(stats[i],font=summaryFont,p=0),sg.Push()]]
        if values['statinput' + str(i)] != '':
            newCol.append([sg.Push(),sg.Text(rawTableStats[i],font=baseFont,p=0,key='raw' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text(reCalcWindow['statoutput' + str(i)].get(),font=baseFont,p=0,key='output' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text(rarityList1inx[i],font=baseFont,p=0,key='1inx' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text(logDelta[i],font=baseFont,p=0,key='logdelta' + str(i)),sg.Push()])
        else:
            newCol.append([sg.Push(),sg.Text(reCalcWindow['matchoutput' + str(i)].get(),font=('Roboto',10,'italic'),p=0,key='raw' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text(reCalcWindow['matchpost' + str(i)].get(),font=('Roboto',10,'italic'),p=0,key='output' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text(targetRarity,font=('Roboto',10,'italic'),p=0,key='1inx' + str(i)),sg.Push()])
            newCol.append([sg.Push(),sg.Text('-',font=('Roboto',10,'italic'),p=0,key='logdelta' + str(i)),sg.Push()])
        newCol.append([sg.Text('',font=summaryFont,p=0)])
        newCol.append([sg.Push(),sg.Text(stats[i],font=summaryFont,p=0),sg.Push()])
        for j in range(0,len(brandNames)):
            newCol.append([sg.Push(),sg.Text(rarityTable[i][j],font=baseFont,p=0,text_color=rarityColors[i][j], key='table' + str(i) + '/' + str(j)),sg.Push()])
        Layout[0].append(sg.Frame('',newCol,border_width=0,p=elementPadding))

    if newWindow:
        brandWindow = sg.Window("Brand Rarity Breakdown",Layout,modal=False,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True)
        brandWindow.bind('<Control-c>','Capture Screenshot')
        return brandWindow
    else:
        try:
            brandWindow = brandWindow[0]
            for i in range(0,len(stats)):
                if values['statinput' + str(i)] != '':
                    brandWindow['raw' + str(i)].update(rawTableStats[i],font=baseFont)
                    brandWindow['output' + str(i)].update(reCalcWindow['statoutput' + str(i)].get(),font=baseFont)
                    brandWindow['1inx' + str(i)].update(rarityList1inx[i],font=baseFont)
                    brandWindow['logdelta' + str(i)].update(logDelta[i],font=baseFont)
                else:
                    brandWindow['raw' + str(i)].update(reCalcWindow['matchoutput' + str(i)].get(),font=('Roboto',10,'italic'))
                    brandWindow['output' + str(i)].update(reCalcWindow['matchpost' + str(i)].get(),font=('Roboto',10,'italic'))
                    brandWindow['1inx' + str(i)].update(targetRarity,font=('Roboto',10,'italic'))
                    brandWindow['logdelta' + str(i)].update('-',font=('Roboto',10,'italic'))
                for j in range(0,len(brandNames)):
                    brandWindow['table' + str(i) + '/' + str(j)].update(rarityTable[i][j],text_color=rarityColors[i][j])
            return brandWindow
        except:
            return []

def reAnalysis(reCalcWindow):

    event, values = reCalcWindow.read(timeout=0)

    compType = values['componentselect']
    level = values['relevelselect']

    if reCalcWindow['statsheader'].get() == "Input Raw Component Stats":
        direction = 1
    else:
        direction = -1
    reMults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
    reMult = reMults[int(level)-1]
    tails = list(cur.execute("SELECT stat1re,stat2re,stat3re,stat4re,stat5re,stat6re,stat7re,stat8re FROM component WHERE type = ?",[compType]).fetchall()[0])

    compStats = list(cur.execute("SELECT stat1disp,stat2disp,stat3disp,stat4disp,stat5disp,stat6disp,stat7disp,stat8disp FROM component WHERE type = ?",[compType]).fetchall()[0])
    stats = []

    for i in range(0,9):
        if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
            stats.append(values['statinput' + str(i)])
        else:
            stats.append(reCalcWindow['statoutput' + str(i)].get())

    if 'A/HP:' not in compStats:
        compStats.insert(0,'A/HP:')
        tails.insert(0,'1')
    else:
        tails.append('0')

    bestCase = []
    worstCase = []
    bestCasePreRounded = []
    worstCasePreRounded = []
    postsList = []
    percentsList = []

    reLevel = compType[0] + str(level%10)

    means, mods, stdevs, mixtureWeights = pullStatsData(reLevel)

    for i in range(0,9):
        reMultiplier = 1 + tryFloat(tails[i]) * reMult
        if stats[i] == '':
            best = ''
            worst = ''
            bestPreRounded = ''
            worstPreRounded = ''
            posts = []
            percents = []
        elif compStats[i] in ['Vs. Shields:', 'Vs. Armor:', 'Refire Rate:']:
            best, worst, posts, percents = bestCaseWorstCase(float(stats[i]),3,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            bestPreRounded, worstPreRounded, postsPreRounded, percentsPreRounded = bestCaseWorstCaseVsRefire(float(stats[i]),tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            posts = posts + postsPreRounded
            percents = percents + percentsPreRounded
        elif compStats[i] == 'Recharge:' and compType == 'Shield':
            best, worst, posts, percents = bestCaseWorstCase(float(stats[i]),2,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            bestPreRounded = ''
            worstPreRounded = ''
        elif compStats[i] == 'Front HP:':
            if stats[i] != '' and stats[i+1] != '':
                best, worst, posts, percents = bestCaseWorstCase((float(stats[i]) + float(stats[i+1]))/2,1,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            else:
                best, worst, posts, percents = bestCaseWorstCase(float(stats[i]),1,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            bestPreRounded = ''
            worstPreRounded = ''
        elif compStats[i] == 'Back HP:':
            if stats[i] != '' and stats[i-1] != '':
                best, worst, posts, percents = bestCaseWorstCase((float(stats[i]) + float(stats[i-1]))/2,1,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            else:
                best, worst, posts, percents = bestCaseWorstCase(float(stats[i]),1,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            bestPreRounded = ''
            worstPreRounded = ''
        else:
            best, worst, posts, percents = bestCaseWorstCase(float(stats[i]),1,tails[i],reMultiplier,means[i],stdevs[i],mixtureWeights)
            bestPreRounded = ''
            worstPreRounded = ''

        bestCase.append(best)
        worstCase.append(worst)
        bestCasePreRounded.append(bestPreRounded)
        worstCasePreRounded.append(worstPreRounded)
        postsList.append(posts)
        percentsList.append(percents)

    roundingAnalysis = [
        'Rounding will not affect the outcome',
        'ROUND before REing, this is guaranteed to improve the post-RE outcome',
        'ROUND before REing, there is a chance to improve the post-RE outcome',
        'DO NOT ROUND before REing, this is guaranteed to worsen the post-RE outcome',
        'DO NOT ROUND before REing, there is a chance to worsen the post-RE outcome',
        'Results of rounding uncertain - See analysis'
    ]

    rounding = []

    for i in range(0,len(compStats)):
        if compStats[i] in ['Vs. Shields:','Vs. Armor:','Refire Rate:'] and stats[i] != '':
            tail = float(tails[i])
            best = bestCase[i]
            worst = worstCase[i]
            bestPre = bestCasePreRounded[i]
            worstPre = worstCasePreRounded[i]

            if tail > 0:
                truth = [best > bestPre, bestPre > best, worst > worstPre, worstPre > worst, best > worst, bestPre > worstPre]
            else:
                truth = [best < bestPre, bestPre < best, worst < worstPre, worstPre < worst, best < worst, bestPre < worstPre]

            #I hate truth tables.

            if not truth[0] and not truth[1] and not truth[2] and not truth[3] and not truth[4] and not truth[5]:
                rounding.append(roundingAnalysis[0])
            elif truth[1] and truth[3] and not (truth[0] or truth[2] or truth[4] or truth[5]):
                rounding.append(roundingAnalysis[1])
            elif (truth[1] ^ truth[3]) and (truth[4] ^ truth[5]) and not (truth[0] or truth[2]):
                rounding.append(roundingAnalysis[2])
            elif truth[0] and truth[2] and not (truth[1] or truth[3] or truth[4] or truth[5]):
                rounding.append(roundingAnalysis[3])
            elif (truth[0] ^ truth[2]) and (truth[4] ^ truth[5]) and not (truth[1] or truth[3]):
                rounding.append(roundingAnalysis[4])
            else:
                rounding.append(roundingAnalysis[5])
        else:
            rounding.append('')

    return postsList, percentsList, rounding

def reAnalysisUI(reCalcWindow, newWindow, *analysisWindow):

    event, values = reCalcWindow.read(timeout=0)
    postsList, percentsList, rounding = reAnalysis(reCalcWindow)
    print(postsList)
    
    compName = values['projectname']
    compType = values['componentselect']
    level = values['relevelselect']

    mults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
    reBonus = str(round(mults[level-1] * 100,0)) + '%'

    compStats = []
    for i in range(0,9):
        compStats.append(reCalcWindow['stattext' + str(i)].get())

    compStats = [x for x in compStats if x != '']

    statsColumn = [[sg.Text('',font=baseFont,p=0)],[sg.Text('',font=baseFont,p=0)]]
    rawStatsColumn = [[sg.Text('',font=baseFont,p=0)],[sg.Push(),sg.Text('Raw Values',font=baseFont,p=0),sg.Push()]]
    worstCaseColumn = [[sg.Text('',font=baseFont,p=0)],[sg.Push(),sg.Text('Worst Case Post',font=baseFont,p=0),sg.Push()]]
    worstCaseStatColumn = []
    worstCasePercentColumn = []
    bestCaseColumn = [[sg.Text('',font=baseFont,p=0)],[sg.Push(),sg.Text('Best Case Post',font=baseFont,p=0),sg.Push()]]
    bestCaseStatColumn = []
    bestCasePercentColumn = []
    worstCasePreColumn = [[sg.Push(),sg.Text('Worst Case Post',font=baseFont,p=0),sg.Push()],[sg.Push(),sg.Text('Pre-Rounded',font=baseFont,p=0),sg.Push()]]
    worstCasePreStatColumn = []
    worstCasePrePercentColumn = []
    bestCasePreColumn = [[sg.Push(),sg.Text('Best Case Post',font=baseFont,p=0),sg.Push()],[sg.Push(),sg.Text('Pre-Rounded',font=baseFont,p=0),sg.Push()]]
    bestCasePreStatColumn = []
    bestCasePrePercentColumn = []
    roundingColumn = [[sg.Text('',font=baseFont,p=0)],[sg.Push(),sg.Text('Rounding Recommendations',font=baseFont,p=0),sg.Push()]]

    visibility = False
    worstCase = []
    worstCasePercent = []
    bestCase = []
    bestCasePercent = []
    worstCasePre = []
    worstCasePrePercent = []
    bestCasePre = []
    bestCasePrePercent = []
    visibility = False

    for i in range(0,len(compStats)):
        statsColumn.append([sg.Push(),sg.Text(compStats[i],font=baseFont,p=0,key='statscolumn' + str(i))])
        if values['statinput' + str(i)] != '':
            if compStats[i] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
                worstCase.append("{:.3f}".format(postsList[i][0]))
                worstCasePercent.append(' (' + str(round(percentsList[i][0],1)) + '%)')
                bestCase.append("{:.3f}".format(postsList[i][1]))
                bestCasePercent.append(' (' + str(round(percentsList[i][1],1)) + '%)')
                worstCasePre.append("{:.3f}".format(postsList[i][2]))
                worstCasePrePercent.append(' (' + str(round(percentsList[i][2],1)) + '%)')
                bestCasePre.append("{:.3f}".format(postsList[i][3]))
                bestCasePrePercent.append(' (' + str(round(percentsList[i][3],1)) + '%)')
                visibility = True
            elif compStats[i] == 'Recharge:' and compType == 'Shield':
                worstCase.append("{:.2f}".format(postsList[i][0]))
                worstCasePercent.append(' (' + str(round(percentsList[i][0],1)) + '%)')
                bestCase.append("{:.2f}".format(postsList[i][1]))
                bestCasePercent.append(' (' + str(round(percentsList[i][1],1)) + '%)')
                worstCasePre.append('')
                worstCasePrePercent.append('')
                bestCasePre.append('')
                bestCasePrePercent.append('')
            else:
                worstCase.append("{:.1f}".format(postsList[i][0]))
                worstCasePercent.append(' (' + str(round(percentsList[i][0],1)) + '%)')
                bestCase.append("{:.1f}".format(postsList[i][1]))
                bestCasePercent.append(' (' + str(round(percentsList[i][1],1)) + '%)')
                worstCasePre.append('')
                worstCasePrePercent.append('')
                bestCasePre.append('')
                bestCasePrePercent.append('')
        else:
            worstCase.append('')
            worstCasePercent.append('')
            bestCase.append('')
            bestCasePercent.append('')
            worstCasePre.append('')
            worstCasePrePercent.append('')
            bestCasePre.append('')
            bestCasePrePercent.append('')

        worstCaseStatColumn.append([sg.Push(),sg.Text(worstCase[-1],font=baseFont,p=0,key='worstcase' + str(i))])
        worstCasePercentColumn.append([sg.Text(worstCasePercent[-1],font=baseFont,p=0,key='worstcasepercent' + str(i)),sg.Push()])
        bestCaseStatColumn.append([sg.Push(),sg.Text(bestCase[-1],font=baseFont,p=0,key='bestcase' + str(i))])
        bestCasePercentColumn.append([sg.Text(bestCasePercent[-1],font=baseFont,p=0,key='bestcasepercent' + str(i)),sg.Push()])
        worstCasePreStatColumn.append([sg.Push(),sg.Text(worstCasePre[-1],font=baseFont,p=0,key='worstcasepre' + str(i))])
        worstCasePrePercentColumn.append([sg.Text(worstCasePrePercent[-1],font=baseFont,p=0,key='worstcaseprepercent' + str(i)),sg.Push()])
        bestCasePreStatColumn.append([sg.Push(),sg.Text(bestCasePre[-1],font=baseFont,key='bestcasepre' + str(i),p=0)])
        bestCasePrePercentColumn.append([sg.Text(bestCasePrePercent[-1],font=baseFont,p=0,key='bestcaseprepercent' + str(i)),sg.Push()])
        roundingColumn.append([sg.Push(),sg.Text(rounding[i],font=baseFont,p=0,key='rounding' + str(i)),sg.Push()])
        if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
            rawStatsColumn.append([sg.Push(),sg.Text(values['statinput' + str(i)],font=baseFont,key='rawstatscolumn' + str(i),p=0),sg.Push()])
        else:
            rawStatsColumn.append([sg.Push(),sg.Text(reCalcWindow['statoutput' + str(i)].get(),font=baseFont,p=0,key='rawstatscolumn' + str(i)),sg.Push()])

    worstCaseColumn.append([sg.Push(),sg.Frame('',worstCaseStatColumn,border_width=0,p=0),sg.Frame('',worstCasePercentColumn,border_width=0,p=0),sg.Push()])
    bestCaseColumn.append([sg.Push(),sg.Frame('',bestCaseStatColumn,border_width=0,p=0),sg.Frame('',bestCasePercentColumn,border_width=0,p=0),sg.Push()])
    worstCasePreColumn.append([sg.Push(),sg.Frame('',worstCasePreStatColumn,border_width=0,p=0),sg.Frame('',worstCasePrePercentColumn,border_width=0,p=0),sg.Push()])
    bestCasePreColumn.append([sg.Push(),sg.Frame('',bestCasePreStatColumn,border_width=0,p=0),sg.Frame('',bestCasePrePercentColumn,border_width=0,p=0),sg.Push()])

    Layout = [
        [sg.Push(),sg.Text('Reverse Engineering Analysis: ' + compName + ' ' + compType[0] + str(level%10),font=headerFont,p=0),sg.Push()],
        [sg.Push(),sg.Text('RE Bonus: ' + reBonus,font=baseFont,p=0),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',statsColumn,border_width=0,p=elementPadding),sg.Frame('',rawStatsColumn,border_width=0,p=elementPadding),sg.Frame('',worstCaseColumn,border_width=0,p=elementPadding),sg.Frame('',bestCaseColumn,border_width=0,p=elementPadding),sg.Frame('',worstCasePreColumn,border_width=0,p=elementPadding,visible=visibility),sg.Frame('',bestCasePreColumn,border_width=0,p=elementPadding,visible=visibility),sg.Frame('',roundingColumn,border_width=0,p=elementPadding,visible=visibility)]
    ]

    if newWindow:

        analysisWindow = sg.Window("Reverse Engineering Analysis",Layout,modal=False,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True)
        analysisWindow.bind('<Control-c>', 'Capture Screenshot')
        return analysisWindow

    else:
        analysisWindow = analysisWindow[0]

        for i in range(0,len(compStats)):
            analysisWindow['worstcase' + str(i)].update(worstCase[i])
            analysisWindow['worstcasepercent' + str(i)].update(worstCasePercent[i])
            analysisWindow['bestcase' + str(i)].update(bestCase[i])
            analysisWindow['bestcasepercent' + str(i)].update(bestCasePercent[i])
            analysisWindow['worstcasepre' + str(i)].update(worstCasePre[i])
            analysisWindow['worstcaseprepercent' + str(i)].update(worstCasePrePercent[i])
            analysisWindow['bestcasepre' + str(i)].update(bestCasePre[i])
            analysisWindow['bestcaseprepercent' + str(i)].update(bestCasePrePercent[i])
            analysisWindow['rounding' + str(i)].update(rounding[i])
            if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
                analysisWindow['rawstatscolumn' + str(i)].update(values['statinput' + str(i)])
            else:
                analysisWindow['rawstatscolumn' + str(i)].update(reCalcWindow['statoutput' + str(i)].get())
        return analysisWindow

def saveProject(reCalcWindow):
    event, values = reCalcWindow.read(timeout=0)

    name = values['projectname']
    compType = values['componentselect']
    level = values['relevelselect']

    stats = []

    if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
        for i in range(0,9):
            stats.append(values['statinput' + str(i)])
    else:
        for i in range(0,9):
            stats.append(reCalcWindow['statoutput' + str(i)].get())

    emptyStats = 0
    for i in range(0,9):
        if stats[i] in [0, '']:
            emptyStats += 1

    if name == '':
        alert('Error',['Error: Please enter a project name.'],[],1.5)
        return
    elif compType == '':
        alert('Error',['Error: Please select a component type.'],[],1.5)
        return
    elif level == '':
        alert('Error',['Error: Please select a reverse engineering level.'],[],1.5)
        return
    elif emptyStats == 9:
        alert('Error',['Error: You must enter at least one non-zero stat before you can save this project.'],[],1.5)
        return
    
    cur2.execute("CREATE TABLE IF NOT EXISTS reproject (name UNIQUE, compType, reLevel, stat0, stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8)")

    try:
        oldSave = list(cur2.execute("SELECT * FROM reproject WHERE name = ?", [name]).fetchall()[0])
        if oldSave == [name, compType, level] + stats:
            doOverwrite = False
        else:
            doOverwrite = True
    except:
        doOverwrite = False

    saved = False

    try:
        cur2.execute("INSERT INTO reproject VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",[name, compType, level] + stats)
        alert('',['Save Successful!'],[],1.5)
        saved = True
    except:
        if doOverwrite:
            result = alert("Overwrite?",['An RE project with this name already exists. Do you wish to overwrite it?'],['Proceed','Cancel'],0)
            if result == 'Proceed':
                cur2.execute("INSERT OR REPLACE INTO reproject VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",[name, compType, level] + stats)
                alert('',['Save Successful!'],[],1.5)
                saved = True

    compdb.commit()
    return saved

def loadREProject(reCalcWindow):

    try:
        projectList = listify(cur2.execute("SELECT name FROM reproject ORDER BY name ASC").fetchall())
    except:
        projectList = []

    leftFrame = [
        [sg.Push(),sg.Text('Select RE Project',font=headerFont,p=0),sg.Push()],
        [sg.Push(),sg.Listbox(values=projectList, size=(30, 24), enable_events=True, key='projectname', font=baseFont, select_mode="single", justification='center'),sg.Push()]
    ]

    text = [
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('',key='comptypetext', p=0, font=baseFont)],
        [sg.Push(),sg.Text('',key='releveltext', p=0, font=baseFont)],
        [sg.Text('',font=baseFont,p=0)]
    ]
    stats = [
        [sg.Text('',font=baseFont,p=0)],
        [sg.Text('',key='comptype', font=baseFont,p=0),sg.Push()],
        [sg.Text('',key='relevel', font=baseFont,p=0),sg.Push()],
        [sg.Text('',font=baseFont,p=0)]
    ]

    for i in range(0,9):
        text.append([sg.Push(),sg.Text('',key='text' + str(i), p=0, font=baseFont)])
        stats.append([sg.Text('',key='stats' + str(i), p=0, font=baseFont),sg.Push()])

    rightFrame = [
        [sg.Push(),sg.Text('Project Preview',font=headerFont,p=0),sg.Push()],
        [sg.Push(),sg.Frame('',text,border_width=0,p=elementPadding,s=(125,300)),sg.Frame('',stats,border_width=0,p=elementPadding,s=(125,300)),sg.Push()]
    ]

    loadWindowLayout = [
        [sg.Push(),sg.Frame('',leftFrame,border_width=0,p=elementPadding,s=(250,300)),sg.Frame('',rightFrame,border_width=0,p=elementPadding,s=(250,300)),sg.Push()],
        [sg.Push(),sg.Button("Load",font=buttonFont),sg.Push(),sg.Button("Delete",font=buttonFont),sg.Push(),sg.Button("Cancel",font=buttonFont),sg.Push()]
    ]

    loadWindow = sg.Window("Load RE Project",loadWindowLayout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),size=(600,350),finalize=True)

    loaded = False

    while True:
        event, values = loadWindow.read()

        if event == 'projectname':
            try:
                project = list(cur2.execute("SELECT * FROM reproject WHERE name = ?",[values['projectname'][0]]).fetchall()[0])
                name = project[0]
                compType = project[1]
                reLevel = project[2]
                stats = project[3:]

                compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
                statsDropdown = list(cur.execute("SELECT stat1,stat2,stat3,stat4,stat5,stat6,stat7,stat8 FROM component WHERE type = ?",[compType]).fetchall()[0])
                if 'A/HP:' not in compStats:
                    compStats.insert(0,'A/HP:')
                    statsDropdown.insert(0,'Armor/Hitpoints')
                else:
                    compStats.append('')
                if 'Shield Hitpoints' in statsDropdown:
                    statsDropdown.remove('Shield Hitpoints')
                    statsDropdown.insert(3, 'Back Shield Hitpoints')
                    statsDropdown.insert(3, 'Front Shield Hitpoints')

                loadWindow['comptypetext'].update('Component Type:')
                loadWindow['comptype'].update(compType)
                loadWindow['releveltext'].update('RE Level:')
                loadWindow['relevel'].update(reLevel)
                
                for i in range(0,9):
                    loadWindow['text' + str(i)].update(compStats[i])
                    loadWindow['stats' + str(i)].update(stats[i])
            except:
                pass
        
        if event == 'Load':
            projectName = values['projectname'][0]
            if projectName == '':
                alert('Error',['Error: Please select a project.'],[],1.5)
                loadWindow.TKroot.grab_set()
            else:
                project = list(cur2.execute("SELECT * FROM reproject WHERE name = ?",[projectName]).fetchall()[0])
                name = project[0]
                compType = project[1]
                reLevel = project[2]
                stats = project[3:]

                compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
                if 'A/HP:' not in compStats:
                    compStats.insert(0,'A/HP:')
                else:
                    compStats.append('')

                reCalcWindow['projectname'].update(name)
                reCalcWindow['componentselect'].update(compType)
                reCalcWindow['relevelselect'].update(reLevel,disabled=False)

                for i in range(0,9):
                    reCalcWindow['statinput' + str(i)].update('')
                    reCalcWindow['statoutput' + str(i)].update('')
                    reCalcWindow['matchoutput' + str(i)].update('')
                    reCalcWindow['matchpost' + str(i)].update('')
                    reCalcWindow['statrarity' + str(i)].update('')
                    reCalcWindow['targetrarity'].update('')

                    reCalcWindow['statsheader'].update('Input Raw Component Stats')
                    reCalcWindow['statsoutputheader'].update('Reverse Engineering Results')
                    reCalcWindow['matchingtarget'].update(value='Average Rarity', values=['Average Rarity','Best Stat','Worst Stat'] + statsDropdown)
                    reCalcWindow['statsheader'].update(visible=True)
                    reCalcWindow['statsoutputheader'].update(visible=True)
                    reCalcWindow['logdeltaheader'].update(visible=True)
                    reCalcWindow['matchanalysisheader'].update(visible=True)
                    reCalcWindow['matchheader'].update(visible=True)
                    reCalcWindow['⮂'].update(visible=True)
                    for i in range(0,9):
                        reCalcWindow['logdelta' + str(i)].update('')
                        reCalcWindow['matchquality' + str(i)].update('')
                        if compStats[i] != '':
                            reCalcWindow['stattext' + str(i)].update(compStats[i])
                            reCalcWindow['stattext2' + str(i)].update(compStats[i])
                            reCalcWindow['matchtext' + str(i)].update(compStats[i])
                            reCalcWindow['statinput' + str(i)].update(stats[i],visible=True,disabled=False)
                        else:
                            reCalcWindow['stattext' + str(i)].update('')
                            reCalcWindow['stattext2' + str(i)].update('')
                            reCalcWindow['matchtext' + str(i)].update('')
                            reCalcWindow['statinput' + str(i)].update('', visible=False)
                reCalcWindow.refresh()
                loaded = True
                break
        
        if event == 'Delete':
            projectName = values['projectname'][0]
            if projectName == '':
                alert('Error',['Error: Please select a project.'],[],1.5)
                loadWindow.TKroot.grab_set()
            else:
                result = alert('Alert',["You are attempting to delete the RE Project named '" + projectName + ".'",'This action cannot be undone. Are you sure you wish to proceed?',''],['Proceed','Cancel'],0)
                loadWindow.TKroot.grab_set()
                if result == 'Proceed':
                    cur2.execute("DELETE FROM reproject WHERE name = ?", [projectName])
                    loadWindow['comptypetext'].update('')
                    loadWindow['comptype'].update('')
                    loadWindow['releveltext'].update('')
                    loadWindow['relevel'].update('')
                    
                    for i in range(0,9):
                        loadWindow['text' + str(i)].update('')
                        loadWindow['stats' + str(i)].update('')

                    try:
                        projectList = listify(cur2.execute("SELECT name FROM reproject ORDER BY name ASC").fetchall())
                    except:
                        projectList = []
                    
                    loadWindow['projectname'].update(values=projectList)

        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
    
    loadWindow.close()
    compdb.commit()

    return loaded

def exportProject(reCalcWindow):

    export = False

    event, values = reCalcWindow.read(timeout=0)

    compType = values['componentselect']
    compTypeFormatted = compType.lower().replace(" ", "").replace("/", "").replace(".", "")
    compStatNames = list(cur.execute("SELECT stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8 FROM component WHERE type = ?",[compType]).fetchall()[0])

    compStats = []
    outputStats = []
    for i in range(0,9):
        compStats.append(reCalcWindow['stattext' + str(i)].get())
        if reCalcWindow['statsheader'].get() == 'Input Raw Component Stats':
            outputStats.append(reCalcWindow['statoutput' + str(i)].get())
        else:
            outputStats.append(values['statinput' + str(i)])
    
    compStats = [x for x in compStats if x != '']
    outputStats = [y for y in outputStats if y not in ['', 0]]

    if len(compStats) > len(outputStats):
        alert('Error',['Error: You must enter a non-zero numerical value for every stat', 'before you can export this project to your saved component lists.'],[],3)
        return
    elif len(compStats) < len(outputStats):
        alert('Error',['Error: Oopsie woopsie, something got a little fucky wucky!'],[],1.5)
    else:
        result = alert('Export Project',["You are attempting to export the project '" + values['projectname'] + "' to your saved " + compType + " list with the post-RE stats displayed in the window.","This will make it accessible from the main loadout tool and usable in your loadouts.","Do you wish to proceed?"],['Proceed','Cancel'],0)
        if result != 'Proceed':
            return
        else:
            if values['componentselect'] != 'Armor':
                outputStats = outputStats[1:]
                compStats = compStats[1:]
            if values['componentselect'] == 'Shield':
                if outputStats[2] != outputStats[3]:
                    result2 = alert('Alert',['Your output front and back shield HP do not appear to be equal.','Do you wish to use the average of the two for your exported shield HP?'],['Proceed','Cancel'],0)
                    if result2 == 'Cancel':
                        return
                    else:
                        outputStats[2] = str(round((float(outputStats[2]) + float(outputStats[3])) / 2,1))
                outputStats[3] = outputStats[4]
                outputStats = outputStats[:4]
            old = cur2.execute("SELECT * FROM " + compTypeFormatted + " WHERE name = ?",[values['projectname']]).fetchall()
            if len(old) > 0:
                result3 = alert('Overwrite',['A component with this name already exists. Do you wish to overwrite it?'],['Proceed','Cancel'],0)
                if result3 == 'Proceed':
                    bindings = '?, ' * (len([x for x in compStatNames if x != '']) + 1)
                    bindings = bindings[:-2] #just cuts the last comma/space off
                    cur2.execute("INSERT OR REPLACE INTO " + compTypeFormatted + " VALUES (" + bindings + ")",[values['projectname']] + outputStats)
                    alert('Success',['Export Successful!'],[],1.5)
                    export = True
                else:
                    return
            else:
                bindings = '?, ' * (len([x for x in compStatNames if x != '']) + 1)
                bindings = bindings[:-2]
                cur2.execute("INSERT OR REPLACE INTO " + compTypeFormatted + " VALUES (" + bindings + ")",[values['projectname']] + outputStats)
                alert('Success',['Export Successful!'],[],1.5)
                export = True
                remodalize(reCalcWindow)
            
    compdb.commit()
    return export

def isReward(statValue,compType,level,stat):

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    tails = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][9:17])
    if 'A/HP:' not in compStats:
        compStats.insert(0,'A/HP:')
        tails.insert(0,1)
    else:
        compStats.append('')
        tails.append(1)

    index = str(compStats.index(stat)+1)
    tail = int(tails[compStats.index(stat)])

    if tail > 0:
        best = [0, 0]
    else:
        best = [1000000,1000000]

    if statValue in [0, '']:
        reward = False
        lowHigh = best
        return reward, lowHigh

    reLevel = compType[0] + str(level%10)

    means = cur.execute("SELECT stat" + index + "mean FROM brands WHERE relevel = ?",[reLevel]).fetchall()
    mods = cur.execute("SELECT stat" + index + "mod FROM brands WHERE relevel = ?",[reLevel]).fetchall()

    isRewards = []
    lowHigh = []

    for i in range(0,len(means)):
        mean = float(means[i][0])
        mod = float(mods[i][0])
        if mod < 0.001:
            low = mean * (1 - 3 * mod) #6 stdevs each way
            high = mean * (1 + 3 * mod)
            if stat in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
                low = round(low,3)
                high = round(high,3)
                if low == high:
                    low -= 0.001
                    high += 0.001
            elif stat == 'Recharge:' and compType == 'Shield':
                low = round(low,2)
                high = round(high,2)
                if low == high:
                    low -= 0.01
                    high += 0.01
            else:
                low = round(low,1)
                high = round(high,1)
                if low == high:
                    low -= 0.1
                    high += 0.1
            lowHigh.append([low, high])
            statValue = tryFloat(statValue)
            if statValue >= low and statValue <= high:
                isRewards.append(True)
            else:
                isRewards.append(False)
        else:
            lowHigh.append([])
            isRewards.append(False)

    for i in range(0,len(means)):
        if isRewards[i]:
            if (tail > 0 and lowHigh[i][1] > best[1]) or (tail <0 and lowHigh[i][0] < best[1]):
                best = lowHigh[i]

    try:
        reward = isRewards[lowHigh.index(best)]
    except:
        reward = False

    if stat in ['Vs. Shields:', 'Vs. Armor:', 'Refire Rate:']:
        best = [best[0] - 0.005, best[1] + 0.00499999]

    if tail < 0:
        best.reverse()

    lowHigh = best
    
    return reward, lowHigh

def updateConfigPane(rarity, threshold, reCalcWindow):
    if rarity not in [0, ''] and formatRarity(1/(tryFloat(rarity))) != 'Improbable':
        if rarity < threshold:
            reCalcWindow['targetrarity'].update('⋆Unicorn⋆')
            thresholdLow = max(tryFloat(rarity)*pow(10,0.5),threshold)
            thresholdLowTight = max(tryFloat(rarity)*pow(10,1/3),threshold) #the 1/3 threshold for a good match is set in updateMatchQuality and I didn't bother importing it here. Just a note for later if I ever tweak that value.
            thresholdHighTight = 'inf'
            reCalcWindow['matchthreshold'].update(formatRarity(1/thresholdLow) + ' or better')
        else:
            reCalcWindow['targetrarity'].update('1 in ' + str(int(1/tryFloat(rarity))))
            thresholdLow = tryFloat(rarity)*pow(10,0.5)
            thresholdLowTight = tryFloat(rarity)*pow(10,1/3)
            thresholdHigh = tryFloat(rarity)/pow(10,0.5)
            thresholdHighTight = tryFloat(rarity)/pow(10,1/3)
            reCalcWindow['matchthreshold'].update(formatRarity(1/(tryFloat(rarity)*pow(10,0.5))) + " to " + formatRarity(1/(tryFloat(rarity)/pow(10,0.5))))
    else:
        thresholdLowTight = 0
        thresholdHighTight = 0
        reCalcWindow['targetrarity'].update('')
        reCalcWindow['matchthreshold'].update('')
    
    if reCalcWindow['componentselect'] != '' and reCalcWindow['relevelselect'] != '':
        reCalcWindow['unicornthreshold'].update('⋆' + formatRarity(1/tryFloat(threshold)) + '⋆')
    else:
        reCalcWindow['unicornthreshold'].update('')

    return thresholdLowTight, thresholdHighTight

def generateMatchBands(thresholdLow, thresholdHigh, matches, postRE, reCalcWindow):
    event, values = reCalcWindow.read(timeout=0)
    compType = values['componentselect']
    level = values['relevelselect']
    reLevel = compType[0] + str(level)[-1]

    means, mods, stdevs, mixtureWeights = pullStatsData(reLevel)
    
    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    tails = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][9:17])

    if 'A/HP:' not in compStats:
        compStats.insert(0,'A/HP:')
        tails.insert(0,1)
    else:
        compStats.append('')
        tails.append(1)

    tails = [int(x) for x in tails if x != '']
    compStats = [x for x in compStats if x != '']

    statMeans = []

    for i in range(0,len(compStats)):
        statMean = 0
        for j in range(0,len(mixtureWeights)):
            statMean += means[i][j]*mixtureWeights[j]
        statMeans.append(statMean)

    statsLow = []
    statsHigh = []

    if thresholdHigh == 'inf':
        thresholdHigh = 10**-9

    for i in range(0,len(compStats)):

        initial = statMeans[i]

        reLevel = compType[0] + str(level%10)

        if tails[i] > 0:
            testThresholdLow = 1 - thresholdLow
            testThresholdHigh = 1 - thresholdHigh
        else:
            testThresholdLow = thresholdLow
            testThresholdHigh = thresholdHigh

        statsLow.append(matchStat(means[i],stdevs[i],mixtureWeights,initial,testThresholdLow))
        if thresholdHigh <= 10**-9:
            statsHigh.append('∞')
        else:
            statsHigh.append(matchStat(means[i],stdevs[i],mixtureWeights,initial,testThresholdHigh))

    reMult = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
    reMult = reMult[level-1]
    statsLowPost = [0] * len(compStats)
    if thresholdHigh == 10**-9:
        statsHighPost = statsHigh
    else:
        statsHighPost = [0] * len(compStats)

    matchStringRaw = [0] * len(compStats)
    matchStringPost = [0] * len(compStats)

    for i in range(0,len(compStats)):
        if compStats[i] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
            if compStats[i] == 'Refire Rate:':
                try:
                    statsLowPost[i] = "{:.3f}".format(min(round(round(statsLow[i],2)*(1 + tails[i]*reMult),2),round(statsLow[i]*(1 + tails[i]*reMult),2)))
                    statsLow[i] = "{:.3f}".format(worstCaseVsRefireMin(statsLow[i],compStats[i],reMult))
                    if statsHigh[i] not in ['∞', '0']:
                        statsHighPost[i] = "{:.3f}".format(min(round(round(statsHigh[i],2)*(1 + tails[i]*reMult),2),round(statsHigh[i]*(1 + tails[i]*reMult),2)))
                        statsHigh[i] = "{:.3f}".format(bestCaseVsRefireMax(statsHigh[i],compStats[i],reMult))
                        matchStringRaw[i] = statsLow[i] + ' - ' + statsHigh[i] + ' (' + str(matches[i]) + ')'
                        matchStringPost[i] = statsLowPost[i] + ' - ' + statsHighPost[i] + ' (' + str(postRE[i]) + ')'
                    else:
                        matchStringRaw[i] = statsLow[i] + ' or better' + ' (' + str(matches[i]) + ')'
                        matchStringPost[i] = statsLowPost[i] + ' or better' + ' (' + str(postRE[i]) + ')'
                    
                except:
                    pass
            else:
                try:
                    statsLowPost[i] = "{:.3f}".format(max(round(round(statsLow[i],2)*(1 + tails[i]*reMult),2),round(statsLow[i]*(1 + tails[i]*reMult),2)))
                    statsLow[i] = "{:.3f}".format(worstCaseVsRefireMin(statsLow[i],compStats[i],reMult))
                    if statsHigh[i] not in ['∞', '0']:
                        statsHighPost[i] = "{:.3f}".format(max(round(round(statsHigh[i],2)*(1 + tails[i]*reMult),2),round(statsHigh[i]*(1 + tails[i]*reMult),2)))
                        statsHigh[i] = "{:.3f}".format(bestCaseVsRefireMax(statsHigh[i],compStats[i],reMult))
                        matchStringRaw[i] = statsLow[i] + ' - ' + statsHigh[i] + ' (' + str(matches[i]) + ')'
                        matchStringPost[i] = statsLowPost[i] + ' - ' + statsHighPost[i] + ' (' + str(postRE[i]) + ')'
                    else:
                        matchStringRaw[i] = statsLow[i]  + ' or better' + ' (' + str(matches[i]) + ')'
                        matchStringPost[i] = statsLowPost[i]  + ' or better' + ' (' + str(postRE[i]) + ')'
                except:
                    pass

        else:
            if compType == 'Shield' and 'Recharge' in compStats[i]:
                statsLowPost[i] = "{:.2f}".format(round(statsLow[i]*(1 + tails[i]*reMult),2))
                statsLow[i] = "{:.2f}".format(round(statsLow[i],2))
                if statsHigh[i] not in ['∞', '0']:
                    statsHighPost[i] = "{:.2f}".format(round(statsHigh[i]*(1 + tails[i]*reMult),2))
                    statsHigh[i] = "{:.2f}".format(round(statsHigh[i],2))
                    matchStringRaw[i] = statsLow[i] + ' - ' + statsHigh[i] + ' (' + str(matches[i]) + ')'
                    matchStringPost[i] = statsLowPost[i] + ' - ' + statsHighPost[i] + ' (' + str(postRE[i]) + ')'
                else:
                    matchStringRaw[i] = statsLow[i]  + ' or better' + ' (' + str(matches[i]) + ')'
                    matchStringPost[i] = statsLowPost[i]  + ' or better' + ' (' + str(postRE[i]) + ')'
            else:
                statsLowPost[i] = "{:.1f}".format(round(statsLow[i]*(1 + tails[i]*reMult),1))
                statsLow[i] = "{:.1f}".format(round(statsLow[i],1))
                if statsHigh[i] not in ['∞', '0']:
                    statsHighPost[i] = "{:.1f}".format(round(statsHigh[i]*(1 + tails[i]*reMult),1))
                    statsHigh[i] = "{:.1f}".format(round(statsHigh[i],1))
                    matchStringRaw[i] = statsLow[i] + ' - ' + statsHigh[i] + ' (' + str(matches[i]) + ')'
                    matchStringPost[i] = statsLowPost[i] + ' - ' + statsHighPost[i] + ' (' + str(postRE[i]) + ')'
                else:
                    matchStringRaw[i] = statsLow[i]  + ' or better' + ' (' + str(matches[i]) + ')'
                    matchStringPost[i] = statsLowPost[i]  + ' or better' + ' (' + str(postRE[i]) + ')'

    for i in range(0,len(statsLow)):
        if isReward(statsLow[i],compType,level,compStats[i])[0]:
            statsLow[i] = str(statsLow[i]) + ' (Reward)'
        if isReward(statsHigh[i],compType,level,compStats[i])[0]:
            statsHigh[i] = str(statsHigh[i]) + ' (Reward)'
            
    return matchStringRaw, matchStringPost

def reCalc():

    menu_def = [
        ['&RE Project', ['&New Project', '&!Open Project', '!&Save Project', 'E&xit']],
        ['&Tools', ['!&Brand Rarity Table', '!&RE Analysis', '!&Export Project']],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    menu_def_load_unlocked = [
        ['&RE Project', ['&New Project', '&Open Project', '!&Save Project', 'E&xit']],
        ['&Tools', ['!&Brand Rarity Table', '!&RE Analysis', '!&Export Project']],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    menu_def_save_unlocked = [
        ['&RE Project', ['&New Project', '&!Open Project', '&Save Project', 'E&xit']],
        ['&Tools', ['&Brand Rarity Table', '&RE Analysis', '&Export Project']],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    menu_def_save_load_unlocked = [
        ['&RE Project', ['&New Project', '&Open Project', '&Save Project', 'E&xit']],
        ['&Tools', ['&Brand Rarity Table', '&RE Analysis', '&Export Project']],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    selectLeft = [
        [sg.Push(),sg.Text("Project Name:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Component Type:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("RE Level:",font=baseFont,p=1)],
    ]

    selectRight = [
        [sg.Input('',font=baseFont,key='projectname',s=25,p=1),sg.Push()],
        [sg.Combo(values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'],key='componentselect',font=baseFont,s=(13,8),enable_events=True,readonly=True,p=1),sg.Push()],
        [sg.Combo(values=[1,2,3,4,5,6,7,8,9,10],key='relevelselect',font=baseFont,s=(5,10),readonly=True,enable_events=True,p=1,disabled=True),sg.Push()],
    ]

    selectFrame = [
        [sg.Push(),sg.Frame('',selectLeft,border_width=0,p=elementPadding,s=(135,85)),sg.Frame('',selectRight,border_width=0,p=elementPadding,s=(165,85)),sg.Push()]
    ]

    statsText = []
    statsInputs = []
    statRarities = []
    logDeltas = []
    matchQualities = []
    statsText2 = []
    statsOutputs = []
    matchesText = []
    matchesOutputs = []
    matchesPost = []

    for i in range(0,9):
        statsText.append([sg.Push(),sg.Text("",key='stattext' + str(i),font=baseFont,s=15,justification='right',p=(0,2))])
        statsInputs.append([sg.Input("",s=8,key='statinput' + str(i),visible=False,p=(0,2),font=baseFont,enable_events=True,disabled=True,disabled_readonly_background_color=boxColor)])
        statRarities.append([sg.Push(),sg.Text("",key='statrarity' + str(i),font=baseFont,s=9,p=(0,2),justification='center'),sg.Push()])
        logDeltas.append([sg.Push(),sg.Text("",key='logdelta' + str(i),font=baseFont,s=4,p=(0,2),justification='center'),sg.Push()])
        matchQualities.append([sg.Push(),sg.Text("",key='matchquality' + str(i),font=baseFont,s=17,p=(0,2),justification='center'),sg.Push()])
        statsText2.append([sg.Push(),sg.Text("",key='stattext2' + str(i),font=baseFont,s=15,justification='right',p=(0,2))])
        statsOutputs.append([sg.Text("",s=8,key='statoutput' + str(i),p=(0,2),font=baseFont)])
        matchesText.append([sg.Push(),sg.Text("",key='matchtext' + str(i),font=baseFont,s=15,justification='right',p=(0,2))])
        matchesOutputs.append([sg.Push(),sg.Text("",s=24,key='matchoutput' + str(i),p=(0,2),font=baseFont),sg.Push()])
        matchesPost.append([sg.Push(),sg.Text("",s=24,key='matchpost' + str(i),p=(0,2),font=baseFont),sg.Push()])

    inputFrame = [
        [sg.Text("Input Raw Component Stats",key='statsheader', font=baseFont,p=(0,2))],
        [sg.Push(),sg.vtop(sg.Frame('',statsText,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',statsInputs,border_width=0,p=elementPadding,element_justification='center',s=(70,210))),sg.vtop(sg.Frame('',statRarities,border_width=0,p=elementPadding,element_justification='center')),sg.Push()]
    ]

    outputFrame = [
        [sg.Text("Reverse Engineering Results",key='statsoutputheader', font=baseFont,p=(0,2))],
        [sg.Push(),sg.vtop(sg.Frame('',statsText2,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',statsOutputs,border_width=0,p=elementPadding,element_justification='center',s=(65,210))),sg.Push()]
    ]

    logDeltas = [
        [sg.Text("Log Δ",key='logdeltaheader', font=baseFont,p=(0,2),expand_x=True,justification='center')],
        [sg.Push(),sg.vtop(sg.Frame('',logDeltas,border_width=0,p=elementPadding)),sg.Push()]
    ]
    
    matchQualities = [
        [sg.Text("Matching Analysis",key='matchanalysisheader', font=baseFont,p=(0,2),expand_x=True,justification='center')],
        [sg.Push(),sg.vtop(sg.Frame('',matchQualities,border_width=0,p=elementPadding)),sg.Push()]
    ]

    matchAnalysisFrame = [
        [sg.Push(),sg.vtop(sg.Frame('',logDeltas,border_width=0,p=0)),sg.vtop(sg.Frame('',matchQualities,border_width=0,p=0,element_justification='center')),sg.Push()]
    ]

    matchingConfigFrameLeft = [
        [sg.Push(),sg.Text("Matching Target:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Target Rarity:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Matching Range:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Unicorn Threshold:",font=baseFont,p=1)],
    ]
    matchingConfigFrameRight = [
        [sg.Combo(values=['Average Rarity','Best Stat','Worst Stat'],default_value="Average Rarity",key='matchingtarget',enable_events=True,readonly=True,size=(20,3),font=baseFont,p=1,disabled=True),sg.Push()],
        [sg.Text("",font=baseFont,p=1,key='targetrarity'),sg.Push()],
        [sg.Text("",font=baseFont,p=1,s=20, key='matchthreshold'),sg.Push()],
        [sg.Text("",font=baseFont,p=1,key='unicornthreshold'),sg.Push()]
    ]

    matchingConfigFrame = [
        [sg.Push(),sg.vtop(sg.Frame('',matchingConfigFrameLeft,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',matchingConfigFrameRight,border_width=0,p=elementPadding)),sg.Push()]
    ]

    matchesFrame = [
        [sg.Text("Matching Stats",font=baseFont,key='matchheader',p=(0,2))],
        [sg.Push(),sg.vtop(sg.Frame('',matchesText,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',matchesOutputs,border_width=0,p=elementPadding,s=(170,210))),sg.vtop(sg.Frame('',matchesPost,border_width=0,p=elementPadding,s=(170,210))),sg.Push()]
    ]

    IOFrame = [
        [sg.Push(),sg.Frame('',selectFrame,border_width=0,p=elementPadding,s=(325,100),element_justification='center'),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',inputFrame,border_width=0,p=0,s=(285,250),element_justification='center'),sg.Frame('',[[sg.Button("⮂",font=("Roboto",18,"bold"),visible=False,s=(20,20))]],border_width=0,p=0,s=(50,50)),sg.Frame('',outputFrame,border_width=0,p=0,s=(200,250),element_justification='center'),sg.Frame('',matchAnalysisFrame,border_width=0,p=0,s=(250,250),element_justification='center'),sg.Push()]
    ]

    matchingFrame = [
        [sg.Push(),sg.Frame('',matchingConfigFrame,border_width=0,p=elementPadding,s=(280,100)),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',matchesFrame,border_width=0,p=0,s=(515,250),element_justification='center'),sg.Push()]
    ]  

    try:
        projects = cur2.execute("SELECT name FROM reproject").fetchall()
    except:
        projects = []

    if projects != []:
        menu = menu_def_load_unlocked
    else:
        menu = menu_def

    Layout = [
        [sg.Menu(menu, key='menu', text_color='#000000', disabled_text_color="#999999", background_color='#ffffff')],
        [sg.Button('focusout',visible=False,bind_return_key=True)],
        [sg.Push(),sg.Frame('',IOFrame,border_width=0,p=0,expand_y=True),sg.Frame('',matchingFrame,border_width=0,p=0,expand_y=True)]
    ]

    reCalcWindow = sg.Window("Reverse Engineering Calculator",Layout,modal=False,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),size=(1300,365),finalize=True)

    reCalcWindow.bind('<Control-s>','Save Project')
    reCalcWindow.bind('<Control-o>','Open Project')
    reCalcWindow.bind('<Control-n>','New Project')
    reCalcWindow.bind('<Control-b>','Brand Rarity Table')
    reCalcWindow.bind('<Control-r>','RE Analysis')
    reCalcWindow.bind('<Control-c>','Capture Screenshot')
    reCalcWindow.bind('<Control-e>','Export Project')

    inputKeys = []
    for i in range(0,9):
        inputKeys.append('statinput' + str(i))
    elements = [reCalcWindow[key] for key in inputKeys]
    for element in elements:
        element.bind('<FocusOut>','+FOCUS OUT')

    export = False

    analysisWindow = None
    brandWindow = None

    while True:
        window, event, values = sg.read_all_windows()

        if window == analysisWindow:

            if event == 'Capture Screenshot':
                appWindow = FindWindow(None, "Reverse Engineering Analysis")
                rect = GetWindowRect(appWindow)
                rect = (rect[0]+8, rect[1]+31, rect[2]-8, rect[3]-8)
                grab = ImageGrab.grab(bbox=rect, all_screens=True)
                screencapOutput = BytesIO()
                grab.convert("RGB").save(screencapOutput,"BMP")
                data = screencapOutput.getvalue()[14:]
                screencapOutput.close()
                toClipboard(win32clipboard.CF_DIB, data)

            if event == sg.WIN_CLOSED:
                analysisWindow.close()
                analysisWindow = None

        elif window == brandWindow:

            if event == 'Capture Screenshot':
                appWindow = FindWindow(None, "Brand Rarity Breakdown")
                rect = GetWindowRect(appWindow)
                rect = (rect[0]+8, rect[1]+31, rect[2]-8, rect[3]-8)
                grab = ImageGrab.grab(bbox=rect, all_screens=True)
                screencapOutput = BytesIO()
                grab.convert("RGB").save(screencapOutput,"BMP")
                data = screencapOutput.getvalue()[14:]
                screencapOutput.close()
                toClipboard(win32clipboard.CF_DIB, data)

            if event == sg.WIN_CLOSED:
                brandWindow.close()
                brandWindow = None

        elif window == reCalcWindow:

            if event == sg.WIN_CLOSED or event == 'Exit':
                break

            if event == 'Capture Screenshot':
                appWindow = FindWindow(None, "Reverse Engineering Calculator")
                rect = GetWindowRect(appWindow)
                rect = (rect[0]+8, rect[1]+51, rect[2]-8, rect[3]-8)
                grab = ImageGrab.grab(bbox=rect, all_screens=True)
                screencapOutput = BytesIO()
                grab.convert("RGB").save(screencapOutput,"BMP")
                data = screencapOutput.getvalue()[14:]
                screencapOutput.close()
                toClipboard(win32clipboard.CF_DIB, data)

            if event == 'Keyboard Shortcuts':
                alert('Keyboard Shortcuts',['• Ctrl+N - New Project','• Ctrl+S - Save Project','• Ctrl+O - Open Project','• Ctrl+B - Show Brand Rarity Table','• Ctrl+R - Show RE Analysis','• Ctrl+E - Export Project'],['Got it!'],0)
                
            if event == 'Brand Rarity Table':
                if brandWindow != None:
                    brandWindow.close()
                brandWindow = brandTable(reCalcWindow, True)
                brandWindow.TKroot.focus_set()
            
            if event == 'RE Analysis':
                if analysisWindow != None:
                    analysisWindow.close()
                analysisWindow = reAnalysisUI(reCalcWindow, True)
                analysisWindow.TKroot.focus_set()

            if event == 'Export Project':
                export = exportProject(reCalcWindow)

            if event == 'New Project':
                if analysisWindow != None:
                    analysisWindow.close()
                    analysisWindow = None
                if brandWindow != None:
                    brandWindow.close()
                    brandWindow = None
                result = alert('Alert',['Any unsaved project data will be lost. Do you wish to proceed?'],['Proceed','Cancel'],0)
                if result == 'Proceed':
                    reCalcWindow['projectname'].update('')
                    reCalcWindow['componentselect'].update('')
                    reCalcWindow['relevelselect'].update('',disabled=True)

                    fields = ['stattext','statinput','statrarity','logdelta','matchquality','stattext2','statoutput','matchtext','matchoutput','matchpost']

                    for i in fields:
                        for j in range(0,9):
                            if i == 'statinput':
                                reCalcWindow[i + str(j)].update('',disabled=True,visible=False,text_color='#ffffff')
                            else:
                                reCalcWindow[i + str(j)].update('',text_color='#ffffff')
                    
                    reCalcWindow['matchingtarget'].update('Average Rarity', disabled=True)
                    reCalcWindow['targetrarity'].update('')
                    reCalcWindow['matchthreshold'].update('')
                    reCalcWindow['unicornthreshold'].update('')
                    reCalcWindow['⮂'].update(visible=False)
                    reCalcWindow['statsheader'].update('Input Raw Component Stats')
                    reCalcWindow['statsoutputheader'].update('Reverse Engineering Results')
                    event, values = reCalcWindow.read(timeout=0)

                if menu == menu_def_save_load_unlocked:
                    reCalcWindow['menu'].update(menu_def_load_unlocked)
                    menu = menu_def_load_unlocked
                elif menu == menu_def_save_unlocked:
                    reCalcWindow['menu'].update(menu_def)
                    menu = menu_def

            if event == 'Save Project':
                saved = saveProject(reCalcWindow)
                if saved:
                    if menu not in [menu_def_load_unlocked, menu_def_save_load_unlocked]:
                        reCalcWindow['menu'].update(menu_def_save_load_unlocked)
                        menu = menu_def_save_load_unlocked

            if event == 'Open Project':
                loaded = loadREProject(reCalcWindow)
                if loaded:
                    if analysisWindow != None:
                        analysisWindow.close()
                        analysisWindow = None
                    if brandWindow != None:
                        brandWindow.close()
                        brandWindow = None
                    updateREOutputs(reCalcWindow)
                    rarityList, rarityList1inx, rarity, matches, matchesRaw, postRE, logDelta, matchDelta = getMatches(reCalcWindow)
                    updateMatchQuality(rarityList,matchDelta,reCalcWindow)
                    logDelta = formatLogDelta(logDelta)
                    unicorns, unicornThreshold = isUnicorn(rarityList, reCalcWindow)
                    thresholdLow, thresholdHigh = updateConfigPane(rarity,unicornThreshold,reCalcWindow)
                    matchRaw, matchPost = generateMatchBands(thresholdLow,thresholdHigh,matches,postRE,reCalcWindow)
                    for i in range(0,9):
                        try:
                            reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                            reCalcWindow['logdelta' + str(i)].update(logDelta[i])
                            reCalcWindow['matchoutput' + str(i)].update(matchRaw[i])
                            reCalcWindow['matchpost' + str(i)].update(matchPost[i])
                        except:
                            reCalcWindow['statrarity' + str(i)].update('')
                            reCalcWindow['logdelta' + str(i)].update('')
                            reCalcWindow['matchoutput' + str(i)].update('')
                            reCalcWindow['matchpost' + str(i)].update('')
                    nonEmptyStats = 0
                    matchCount = 0
                    event, values = reCalcWindow.read(timeout=0)
                    reCalcWindow['menu'].update(menu_def_save_load_unlocked)
                    menu = menu_def_save_load_unlocked
                    stats = list(cur.execute("SELECT stat1disp,stat2disp,stat3disp,stat4disp,stat5disp,stat6disp,stat7disp,stat8disp FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
                    statsDropdown = list(cur.execute("SELECT stat1,stat2,stat3,stat4,stat5,stat6,stat7,stat8 FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
                    if 'A/HP:' not in stats:
                        stats.insert(0,'A/HP:')
                        statsDropdown.insert(0,'Armor/Hitpoints')
                    else:
                        stats.append('')
                    if 'Shield Hitpoints' in statsDropdown:
                        statsDropdown.remove('Shield Hitpoints')
                        statsDropdown.insert(3, 'Back Shield Hitpoints')
                        statsDropdown.insert(3, 'Front Shield Hitpoints')
                    statsDropdown = [x for x in statsDropdown if x != '']
                    reCalcWindow['matchingtarget'].update(value='Average Rarity', values=['Average Rarity','Best Stat','Worst Stat'] + statsDropdown, size=(20,3+len(statsDropdown)))

            if event == 'focusout':
                reCalcWindow.TKroot.focus_set()

            try:
                if 'statinput' in event:
                    if values[event][-1] not in '1234567890.':
                        reCalcWindow[event].update(values[event][:-1])
            except:
                pass

            if event == 'componentselect':
                if analysisWindow != None:
                    analysisWindow.close()
                    analysisWindow = None
                if brandWindow != None:
                    brandWindow.close()
                    brandWindow = None
                reCalcWindow['relevelselect'].update(disabled=False)
                #Clear inputs and outputs
                for i in range(0,9):
                    reCalcWindow['statinput' + str(i)].update('')
                    reCalcWindow['statoutput' + str(i)].update('')
                    reCalcWindow['matchoutput' + str(i)].update('')
                    reCalcWindow['matchpost' + str(i)].update('')
                    reCalcWindow['statrarity' + str(i)].update('')
                reCalcWindow['targetrarity'].update('')
                reCalcWindow['matchthreshold'].update('')
                if values['componentselect'] != '' and values['relevelselect'] != '':
                    unicorns, unicornThreshold = isUnicorn([], reCalcWindow)
                    reCalcWindow['unicornthreshold'].update('⋆' + formatRarity(1/tryFloat(unicornThreshold)) + '⋆')
                else:
                    reCalcWindow['unicornthreshold'].update('')
                stats = list(cur.execute("SELECT stat1disp,stat2disp,stat3disp,stat4disp,stat5disp,stat6disp,stat7disp,stat8disp FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
                statsDropdown = list(cur.execute("SELECT stat1,stat2,stat3,stat4,stat5,stat6,stat7,stat8 FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
                if 'A/HP:' not in stats:
                    stats.insert(0,'A/HP:')
                    statsDropdown.insert(0,'Armor/Hitpoints')
                else:
                    stats.append('')
                if 'Shield Hitpoints' in statsDropdown:
                    statsDropdown.remove('Shield Hitpoints')
                    statsDropdown.insert(3, 'Back Shield Hitpoints')
                    statsDropdown.insert(3, 'Front Shield Hitpoints')
                statsDropdown = [x for x in statsDropdown if x != '']
                reCalcWindow['matchingtarget'].update(value='Average Rarity', values=['Average Rarity','Best Stat','Worst Stat'] + statsDropdown, size=(20,3+len(statsDropdown)))
                reCalcWindow['statsheader'].update(visible=True)
                reCalcWindow['statsoutputheader'].update(visible=True)
                reCalcWindow['logdeltaheader'].update(visible=True)
                reCalcWindow['matchanalysisheader'].update(visible=True)
                reCalcWindow['matchheader'].update(visible=True)
                reCalcWindow['⮂'].update(visible=True)
                for i in range(0,9):
                    reCalcWindow['logdelta' + str(i)].update('',text_color=textColor)
                    reCalcWindow['matchquality' + str(i)].update('',text_color=textColor)
                    if stats[i] != '':
                        reCalcWindow['stattext' + str(i)].update(stats[i],text_color=textColor)
                        reCalcWindow['stattext2' + str(i)].update(stats[i],text_color=textColor)
                        reCalcWindow['matchtext' + str(i)].update(stats[i],text_color=textColor)
                        reCalcWindow['statinput' + str(i)].update(visible=True,text_color=textColor)
                    else:
                        reCalcWindow['stattext' + str(i)].update('',text_color=textColor)
                        reCalcWindow['stattext2' + str(i)].update('',text_color=textColor)
                        reCalcWindow['matchtext' + str(i)].update('',text_color=textColor)
                        reCalcWindow['statinput' + str(i)].update('', visible=False,text_color=textColor)

            if event == 'relevelselect':
                if analysisWindow != None:
                    analysisWindow.close()
                    analysisWindow = None
                if brandWindow != None:
                    brandWindow.close()
                    brandWindow = None
                #Clear inputs and outputs
                reCalcWindow['targetrarity'].update('')
                reCalcWindow['matchthreshold'].update('')
                if values['componentselect'] != '' and values['relevelselect'] != '':
                    unicorns, unicornThreshold = isUnicorn([], reCalcWindow)
                    reCalcWindow['unicornthreshold'].update('⋆' + formatRarity(1/tryFloat(unicornThreshold)) + '⋆')
                else:
                    reCalcWindow['unicornthreshold'].update('')
                
                for i in range(0,9):
                    reCalcWindow['stattext' + str(i)].update(text_color=textColor)
                    reCalcWindow['stattext2' + str(i)].update(text_color=textColor)
                    reCalcWindow['matchtext' + str(i)].update(text_color=textColor)
                    reCalcWindow['statinput' + str(i)].update('', disabled=False,text_color=textColor)
                    reCalcWindow['statoutput' + str(i)].update('',text_color=textColor)
                    reCalcWindow['matchoutput' + str(i)].update('',text_color=textColor)
                    reCalcWindow['matchpost' + str(i)].update('',text_color=textColor)
                    reCalcWindow['statrarity' + str(i)].update('',text_color=textColor)
                    reCalcWindow['logdelta' + str(i)].update('',text_color=textColor)
                    reCalcWindow['matchquality' + str(i)].update('',text_color=textColor)

            if event.endswith("+FOCUS OUT"):
                reAnalysis(reCalcWindow)
                inputID = event.split("+FOCUS OUT")[0].split('statinput')[1]
                formattedStat = formatStat(values['statinput' + inputID],reCalcWindow['stattext' + inputID].get(),values['componentselect'])
                reCalcWindow['statinput' + inputID].update(formattedStat)
                updateREOutputs(reCalcWindow)
                rarityList, rarityList1inx, rarity, matches, matchesRaw, postRE, logDelta, matchDelta = getMatches(reCalcWindow)
                updateMatchQuality(rarityList,matchDelta,reCalcWindow)
                logDelta = formatLogDelta(logDelta)
                unicorns, unicornThreshold = isUnicorn(rarityList, reCalcWindow)
                thresholdLow, thresholdHigh = updateConfigPane(rarity,unicornThreshold,reCalcWindow)
                if '' in matches:
                    matchRaw = [''] * 9
                    matchPost = [''] * 9
                else:
                    matchRaw, matchPost = generateMatchBands(thresholdLow,thresholdHigh,matches,postRE,reCalcWindow)
                for i in range(0,9):
                    try:
                        reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                        reCalcWindow['logdelta' + str(i)].update(logDelta[i])
                        reCalcWindow['matchoutput' + str(i)].update(matchRaw[i])
                        reCalcWindow['matchpost' + str(i)].update(matchPost[i])
                    except:
                        reCalcWindow['statrarity' + str(i)].update('')
                        reCalcWindow['logdelta' + str(i)].update('')
                        reCalcWindow['matchoutput' + str(i)].update('')
                        reCalcWindow['matchpost' + str(i)].update('')
                nonEmptyStats = 0
                matchCount = 0
                for i in range(0,9):
                    if values['statinput' + str(i)] not in ['', 0]:
                        nonEmptyStats += 1
                    if reCalcWindow['matchoutput' + str(i)].get() not in ['', 0]:
                        matchCount += 1
                if nonEmptyStats > 0 and matchCount >= nonEmptyStats:
                    if projects != []:
                        reCalcWindow['menu'].update(menu_def_save_load_unlocked)
                        menu = menu_def_save_load_unlocked
                    else:
                        reCalcWindow['menu'].update(menu_def_save_unlocked)
                        menu = menu_def_save_unlocked
                else:
                    reCalcWindow['menu'].update(menu_def)
                    menu = menu_def
                if analysisWindow != None:
                    analysisWindow = reAnalysisUI(reCalcWindow, False, analysisWindow)
                if brandWindow != None:
                    brandWindow = brandTable(reCalcWindow, False, brandWindow)
                
            if event == 'matchingtarget':
                rarityList, rarityList1inx, rarity, matches, matchesRaw, postRE, logDelta, matchDelta = getMatches(reCalcWindow)
                unicorns, unicornThreshold = isUnicorn(rarityList, reCalcWindow)
                updateMatchQuality(rarityList,matchDelta,reCalcWindow)
                logDelta = formatLogDelta(logDelta)
                unicorns, unicornThreshold = isUnicorn(rarityList, reCalcWindow)
                thresholdLow, thresholdHigh = updateConfigPane(rarity,unicornThreshold,reCalcWindow)
                matchRaw, matchPost = generateMatchBands(thresholdLow,thresholdHigh,matches,postRE,reCalcWindow)
                for i in range(0,9):
                    try:
                        reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                        reCalcWindow['logdelta' + str(i)].update(logDelta[i])
                        reCalcWindow['matchoutput' + str(i)].update(matchRaw[i])
                        reCalcWindow['matchpost' + str(i)].update(matchPost[i])
                    except:
                        reCalcWindow['statrarity' + str(i)].update('')
                        reCalcWindow['logdelta' + str(i)].update('')
                        reCalcWindow['matchoutput' + str(i)].update('')
                        reCalcWindow['matchpost' + str(i)].update('')
                if brandWindow != None:
                    brandWindow = brandTable(reCalcWindow, False, brandWindow)

            if event == '⮂':
                if reCalcWindow['statsheader'].get() == "Input Raw Component Stats":
                    reCalcWindow['statsheader'].update("Input Reverse Engineered Stats")
                    reCalcWindow['statsoutputheader'].update("Raw Component Results")
                else:
                    reCalcWindow['statsheader'].update("Input Raw Component Stats")
                    reCalcWindow['statsoutputheader'].update("Reverse Engineering Results")
                for i in range(0,9):
                    leftStat = formatStat(values['statinput' + str(i)],reCalcWindow['stattext' + str(i)].get(),values['componentselect'])
                    rightStat = formatStat(reCalcWindow['statoutput' + str(i)].get(),reCalcWindow['stattext' + str(i)].get(),values['componentselect'])
                    reCalcWindow['statinput' + str(i)].update(rightStat)
                    reCalcWindow['statoutput' + str(i)].update(leftStat)

            try:
                if values['componentselect'] != '' and values['relevelselect'] != '':
                    reCalcWindow['matchingtarget'].update(disabled=False)
                else:
                    reCalcWindow['matchingtarget'].update(disabled=True)
            except:
                pass

    reCalcWindow.close()
    compdb.close()
    tables.close()

#reCalc() #uncomment to run from here.