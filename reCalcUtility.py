import FreeSimpleGUI as sg
import math
import os
import sqlite3
import win32clipboard

from datetime import datetime, timedelta

from buildTables import buildTables

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
                    'BUTTON': ('#e4f2ff', '#202225'),
                    'PROGRESS': ('#01826B', '#D0D0D0'),
                    'BORDER': 1,
                    'SLIDER_DEPTH': 0,
                    'PROGRESS_DEPTH' : 0}

sg.theme_add_new('Discord_Dark', theme_definition)

sg.theme('Discord_Dark')

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
    
def normalCDF(Z):
    try:
        y = 0.5 * (1 + math.erf(Z/math.sqrt(2)))
        return y
    except:
        SyntaxError
    
def logMean(values):
    total = 0
    for i in values:
        total += math.log10(i)/len(values)
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

def formatRarity(rarity):
    if type(rarity) == str or rarity == 0:
        return rarity
    if rarity > 10000000000:
        rarity = '1 in ' + str(int(rarity/1000000000)) + 'B'
    elif rarity > 1000000000:
        rarity = '1 in ' + str(round(rarity/1000000000,1)) + 'B'
    elif rarity > 10000000:
        rarity = '1 in ' + str(int(rarity/1000000)) + 'M'
    elif rarity > 1000000:
        rarity = '1 in ' + str(round(rarity/1000000,1)) + 'M'
    elif rarity > 10000:
        rarity = '1 in ' + str(int(rarity/1000)) + 'k'
    elif rarity > 1000:
        rarity = '1 in ' + str(round(rarity/1000,1)) + 'k'
    else:
        rarity = '1 in ' + str(rarity)
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

def getNextBestVsRefire(input,stat,mean,stdev,mixtureWeights,reMult):
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
    
def logDelta(a,b):
    delta = math.log10(a) - math.log10(b)

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

    #if all input stats are blanks, return
    inputStats = 0
    for i in rawStats:
        if i != '':
            inputStats += 1
    if inputStats == 0:
        return [''] * 9, '', [''] * 9, [''] * 9

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

    reLevel = compType[0] + str(level%10)

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][17:25])
    compStats = [x[:-1] for x in compStats if x != '']
    compStatsDropdown = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][1:9])
    tails = list(cur.execute("SELECT * from component WHERE type = ?", [compType]).fetchall()[0][9:17])
    if 'A/HP' not in compStats:
        compStats.insert(0,'A/HP')
        compStatsDropdown.insert(0,'Armor/Hitpoints')
        tails.insert(0,'1')
    
    if target in compStatsDropdown:
        target = compStats[compStatsDropdown.index(target)]

    tails = [tryFloat(y) for y in tails if y != '']

    brandNames = listify(cur.execute("SELECT name FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    brandWeights = listify(cur.execute("SELECT weight FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    rawMeans = cur.execute("SELECT stat1mean, stat2mean, stat3mean, stat4mean, stat5mean, stat6mean, stat7mean, stat8mean, stat9mean FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    rawMods = cur.execute("SELECT stat1mod, stat2mod, stat3mod, stat4mod, stat5mod, stat6mod, stat7mod, stat8mod, stat9mod FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    means = []
    mods = []
    stdevs = []
    
    for i in range(0,len(compStats)):
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

    stats = []

    for i in range(0,len(rawStats)):
        if rawStats[i] != '':
            worstCase = worstCaseVsRefire(rawStats[i],compStats[i],reMult)
            stats.append(worstCase)
        else:
            stats.append('')

    rarityList = []
    rarityList1inx = []

    for i in range(0,len(compStats)):

        rarity = getRarity(stats[i],means[i],stdevs[i],mixtureWeights)
        if rarity == '':
            rarityList.append('')
            rarityList1inx.append('')
        elif tails[i] > 0:
            rarityList.append(1-rarity)
            rarityList1inx.append(int(1/(1-rarity)))
        else:
            rarityList.append(rarity)
            rarityList1inx.append(int(1/rarity))

    for i in range(0,len(rarityList1inx)):
        rarityList1inx[i] = formatRarity(rarityList1inx[i])

    #Reward Cutoffs - There need to be exceptions in some cases, like w8 eps. Round the cutoff to the nearest 0.1. If vs/refire/srr, 0.01
    cutoffs = []
    
    for i in range(0,len(compStats)):
        cutoffsNewLine = []
        for j in range(0,len(brandNames)):
            if float(mods[i][j]) < 0.001:
                cutoffsNewLine.append(means[i][j] * (1 + mods[i][j] * 3 * tails[i]))
        if cutoffsNewLine != []:
            if tails[i] > 0:
                cutoffsNew = max(cutoffsNewLine)
                if compStats[i] in ['Vs. Shields', 'Vs. Armor'] or (compStats[i] == 'Recharge' and compType == 'Shield'):
                    cutoffsNew = float(round(cutoffsNew,2))
                else:
                    cutoffsNew = float(round(cutoffsNew,1))
            else:
                cutoffsNew = min(cutoffsNewLine)
                if compStats[i] == 'Refire Rate':
                    cutoffsNew = float(round(cutoffsNew,2))
                else:
                    cutoffsNew = float(round(cutoffsNew,1))
        else:
            if tails[i] > 0:
                cutoffsNew = 0
            else:
                cutoffsNew = 1000000

        cutoffs.append(float(cutoffsNew))

    cutoffRarities = []

    for i in range(0,len(cutoffs)):
        cutoffRarity = getRarity(cutoffs[i],means[i],stdevs[i],mixtureWeights)
        if tails[i] > 0:
            cutoffRarities.append(1-cutoffRarity)
        else:
            cutoffRarities.append(cutoffRarity)

    isReward = []
    blankStats = 0
    rewardStats = 0

    for i in range(0,len(rarityList)):
        if rarityList[i] == '':
            isReward.append(False)
            blankStats += 1
        elif rarityList[i] < cutoffRarities[i]:
            isReward.append(False)
        else:
            isReward.append(True)
            rewardStats += 1

    for i in range(0,len(rarityList1inx)):
        if isReward[i]:
            rarityList1inx[i] = 'Reward'
        elif rarityList1inx[i] != '':
            formatRarity(rarityList1inx[i])

    #If all inputs are reward stats, return
    if blankStats + rewardStats == len(compStats):
        return rarityList1inx, '', [''] * 9, [''] * 9
    
    nextBests = []
    nextBestStats = []

    for i in range(0,len(compStats)):
        if compStats[i] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
            nextBestRarity = getNextBestVsRefire(inputStat,compStats[i],means[i],stdevs[i],mixtureWeights,reMult)
            nextBests.append(nextBestRarity)
            nextBestStats.append(statsTemp[i])

    #NOW we get to modes.
    rarity = 0

    #First Mode: Single Stat Target. Default to average if invalid selection
    if target in compStats:
        rarity = rarityList[compStats.index(target)]
        if rarity == '':
            target = "Average Rarity"

    #Second Mode: Max/Min Targets.
    if target == 'Best Stat':
        rarityListTemp = [x for x in rarityList if isReward[rarityList.index(x)] == False and x != '']
        if rarityListTemp == []:
            target = "Average Rarity"
        else:
            rarity = min(rarityListTemp)


    if target == 'Worst Stat':
        rarityListTemp = [x for x in rarityList if isReward[rarityList.index(x)] == False and x != '']
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
                rewardCutoff.append(cutoffRarities[i])

        #1. Remove AHP if it isn't armor, unless it's the only stat // need to rewrite this for blank stat exclusion
        # if AHP is in remaining stats, and there's an entry for AHP, and at least one entry elsewhere, exclude AHP
        if compType != 'Armor':
            if 'A/HP' in remainingStats:
                if len(remainingStats) > 1:
                    exclude1 = exclude0[1:]
                    remainingStats = remainingStats[1:]
                    rewardCutoff = rewardCutoff[1:]
                else:
                    exclude1 = exclude0
            else:
                exclude1 = exclude0

        #2. Remove suspected rewards based on whether or not the stat rarity surpasses the cutoff rarity
        exclude2 = []
        for i in range(0,len(exclude1)):
            if exclude1[i] < rewardCutoff[i]:
                exclude2.append(exclude1[i])

        #3. Take first average
        average1 = logMean(exclude2)
        #4. If average is below reward cutoff rarity, exclude rewards
        exclude3 = []
        statsTemp = remainingStats
        remainingStats = []
        for i in range(0,len(rewardCutoff)):
            if average1 < rewardCutoff[i]:
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
                    if average2 <= nextBestRarity or average2 >= exclude3[i]:
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

        rarity = average3

    if rarity == 0:
        return [], []

    #All this shit down here is naive to how we do the inputs vvv. What matters is the target rarity we feed in. It will do the rest just fine. ^^^ Up here we have to get the target rarity

    #Account for weird shit on vs/refire matching by rounding up/down to .xxx for those stats respectively

    if target in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
        rarity = round(rarity - 0.0000000000005,12)

    matches = []
    postRE = []

    for i in range(0,len(compStats)):

        if tails[i] < 0:
            targetRarity = rarity
        else:
            targetRarity = 1-rarity

        delta = 1
        value = statMeans[i]
        testMin = 0
        testMax = 6 * statMeans[i]

        while delta > 0.000000000001:

            testRarity = getRarity(value,means[i],stdevs[i],mixtureWeights)

            if testRarity < targetRarity:
                testMin = value
                value = (testMin + testMax) / 2
            else:
                testMax = value
                value = (testMin + testMax) / 2
            
            delta = abs(testRarity - targetRarity)
        
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
            postRE.append("{:.3f}".format(optimal))
        elif compStats[i] == 'Recharge' and compType == "Shield":
            matches.append("{:.2f}".format(float(round(value,2))))
            postRE.append("{:.2f}".format(float(round((1 + reMult * tryFloat(tails[i])) * value,2))))
        else:
            matches.append("{:.1f}".format(float(round(value,1))))
            postRE.append("{:.1f}".format(float(round((1 + reMult * tryFloat(tails[i])) * value,1))))

    logDelta = []

    for i in range(0,9):
        if rarityList[i] not in [0, ''] and rarityList1inx[i] != 'Reward':
            if compStats[i] in nextBestStats:
                rangeLow = rarityList[i]
                rangeHigh = nextBests[nextBestStats.index(compStats[i])]
                if rangeLow > rarity and rangeHigh < rarity:
                    logDelta.append(0)
                elif rangeLow < rarity:
                    logDelta.append(math.log10(rarity) - math.log10(rangeLow))
                elif rangeHigh > rarity:
                    logDelta.append(math.log10(rarity) - math.log10(rangeHigh))
            else:
                logDelta.append(math.log10(rarity) - math.log10(rarityList[i]))
        else:
            logDelta.append('')
    print(logDelta)          

    db.close()

    return rarityList1inx, rarity, matches, postRE

#rarityList1inx, matches = getMatches("Weapon",8,[714.9, 1391.8, 19639.7, 2587.0, 4124.4, .7, .685, 14.1, .372],"Average Rarity")

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


def updateREOutputs(reCalcWindow):

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

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
        tails = ['1'] + list(cur.execute("SELECT stat1re,stat2re,stat3re,stat4re,stat5re,stat6re,stat7re,stat8re FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
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
                else:
                    if direction != 1:
                        outputStat = "{:.1f}".format(round(inputStat / multiplier,1)) 
                    else:
                        outputStat = "{:.1f}".format(round(inputStat * multiplier,1))
                reCalcWindow['statoutput' + str(i)].update(outputStat)
            else:
                reCalcWindow['statoutput' + str(i)].update('')
    reCalcWindow.refresh()
    db.close()

def reCalc():

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

    selectLeft = [
        [sg.Push(),sg.Text("Component Type:",font=summaryFont)],
        [sg.Push(),sg.Text("RE Level:",font=summaryFont)],
    ]

    selectRight = [
        [sg.Combo(values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'],key='componentselect',font=summaryFont,s=(15,8),enable_events=True,readonly=True),sg.Push()],
        [sg.Combo(values=[1,2,3,4,5,6,7,8,9,10],key='relevelselect',font=summaryFont,s=(5,10),readonly=True,enable_events=True),sg.Push()],
    ]

    statsText = []
    statsInputs = []
    statRarities = []
    statsText2 = []
    statsOutputs = []
    matchesText = []
    matchesOutputs = []
    matchesPost = []

    for i in range(0,9):
        statsText.append([sg.Push(),sg.Text("",key='stattext' + str(i),font=baseFont,s=12,justification='right',p=(0,2))])
        statsInputs.append([sg.Input("",s=8,key='statinput' + str(i),visible=False,p=(0,2),font=baseFont,enable_events=True),sg.Push()])
        statRarities.append([sg.Push(),sg.Text("",key='statrarity' + str(i),font=baseFont,s=12,p=(0,2),justification='center'),sg.Push()])
        statsText2.append([sg.Push(),sg.Text("",key='stattext2' + str(i),font=baseFont,s=12,justification='right',p=(0,2))])
        statsOutputs.append([sg.Text("",s=8,key='statoutput' + str(i),visible=False,p=(0,2),font=baseFont),sg.Push()])
        matchesText.append([sg.Push(),sg.Text("",key='matchtext' + str(i),font=baseFont,s=12,justification='right',p=(0,2))])
        matchesOutputs.append([sg.Text("",s=8,key='matchoutput' + str(i),visible=False,p=(0,2),font=baseFont),sg.Push()])
        matchesPost.append([sg.Text("",s=8,key='matchpost' + str(i),visible=False,p=(0,2),font=baseFont),sg.Push()])

    inputFrame = [
        [sg.Text("Input Raw Component Stats",key='statsheader', font=baseFont,p=(0,2),visible=False)],
        [sg.Push(),sg.vtop(sg.Frame('',statsText,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',statsInputs,border_width=0,p=elementPadding,element_justification='center')),sg.vtop(sg.Frame('',statRarities,border_width=0,p=elementPadding,element_justification='center')),sg.Push()]
    ]

    outputFrame = [
        [sg.Text("Reverse Engineering Results",key='statsoutputheader', font=baseFont,p=(0,2),visible=False)],
        [sg.Push(),sg.vtop(sg.Frame('',statsText2,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',statsOutputs,border_width=0,p=elementPadding,element_justification='center')),sg.Push()]
    ]

    matchingConfigFrameLeft = [
        [sg.Push(),sg.Text("Matching Target:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Target Rarity:",font=baseFont,p=1)],
        [sg.Push(),sg.Text("Match Threshold:",font=baseFont,p=1)],
    ]
    matchingConfigFrameRight = [
        [sg.Combo(values=['Average Rarity','Best Stat','Worst Stat'],default_value="Average Rarity",key='matchingtarget',enable_events=True,readonly=True,size=(20,12),font=baseFont,p=1),sg.Push()],
        [sg.Text("",font=baseFont,p=1,key='targetrarity'),sg.Push()],
        [sg.Input("0.167",font=baseFont,p=1,key='matchthreshold',s=5,enable_events=True),sg.Push()]
    ]

    matchingConfigFrame = [
        [sg.Push(),sg.vtop(sg.Frame('',matchingConfigFrameLeft,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',matchingConfigFrameRight,border_width=0,p=elementPadding)),sg.Push()]
    ]

    matchesFrame = [
        [sg.Text("Matching Stats",font=baseFont,key='matchheader',p=0,visible=False)],
        [sg.Push(),sg.vtop(sg.Frame('',matchesText,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',matchesOutputs,border_width=0,p=elementPadding)),sg.vtop(sg.Frame('',matchesPost,border_width=0,p=elementPadding)),sg.Push()]
    ]

    IOFrame = [
        [sg.Push(),sg.Frame('',selectLeft,border_width=0,p=elementPadding),sg.Frame('',selectRight,border_width=0,p=elementPadding),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',inputFrame,border_width=0,p=0,s=(300,250),element_justification='center'),sg.Frame('',[[sg.Button("⮂",font=("Roboto",18,"bold"),visible=False,s=(20,20))]],border_width=0,p=0,s=(50,50)),sg.Frame('',outputFrame,border_width=0,p=0,s=(250,250),element_justification='center'),sg.Push()]
    ]

    matchingFrame = [
        [sg.Push(),sg.Frame('',matchingConfigFrame,border_width=0,p=elementPadding),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',matchesFrame,border_width=0,p=elementPadding,s=(3250,250),element_justification='center')]
    ]

    Layout = [
        [sg.Button('focusout',visible=False,bind_return_key=True)],
        [sg.Push(),sg.Frame('',IOFrame,border_width=0,p=0,expand_y=True),sg.Frame('',matchingFrame,border_width=1,p=0,expand_y=True)]
    ]

    reCalcWindow = sg.Window("Reverse Engineering Calculator",Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),size=(950,350),finalize=True)

    inputKeys = []
    for i in range(0,9):
        inputKeys.append('statinput' + str(i))
    elements = [reCalcWindow[key] for key in inputKeys]
    for element in elements:
        element.bind('<FocusOut>','+FOCUS OUT')

    while True:
        event, values = reCalcWindow.read()

        if event == 'focusout':
            reCalcWindow.TKroot.focus_set()

        try:
            if 'statinput' in event or 'matchthreshold' in event:
                if values[event][-1] not in '1234567890.':
                    reCalcWindow[event].update(values[event][:-1])
        except:
            pass


        if event == 'componentselect':
            stats = list(cur.execute("SELECT stat1disp,stat2disp,stat3disp,stat4disp,stat5disp,stat6disp,stat7disp,stat8disp FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
            statsDropdown = list(cur.execute("SELECT stat1,stat2,stat3,stat4,stat5,stat6,stat7,stat8 FROM component WHERE type = ?",[values['componentselect']]).fetchall()[0])
            if 'A/HP:' not in stats:
                stats.insert(0,'A/HP:')
                statsDropdown.insert(0,'Armor/Hitpoints')
            reCalcWindow['matchingtarget'].update(value='Average Rarity', values=['Average Rarity','Best Stat','Worst Stat'] + statsDropdown)
            reCalcWindow['statsheader'].update(visible=True)
            reCalcWindow['statsoutputheader'].update(visible=True)
            reCalcWindow['matchheader'].update(visible=True)
            reCalcWindow['⮂'].update(visible=True)
            for i in range(0,9):
                if stats[i] != '':
                    reCalcWindow['stattext' + str(i)].update(stats[i])
                    reCalcWindow['stattext2' + str(i)].update(stats[i])
                    reCalcWindow['matchtext' + str(i)].update(stats[i])
                    reCalcWindow['statinput' + str(i)].update(visible=True)
                    reCalcWindow['statoutput' + str(i)].update(visible=True)
                    reCalcWindow['matchoutput' + str(i)].update(visible=True)
                    reCalcWindow['matchpost' + str(i)].update(visible=True)
                else:
                    reCalcWindow['stattext' + str(i)].update('')
                    reCalcWindow['stattext2' + str(i)].update('')
                    reCalcWindow['matchtext' + str(i)].update('')
                    reCalcWindow['statinput' + str(i)].update('', visible=False)
                    reCalcWindow['statoutput' + str(i)].update(visible=False)
                    reCalcWindow['matchoutput' + str(i)].update(visible=False)
                    reCalcWindow['matchpost' + str(i)].update(visible=False)
        #try:
        if event.endswith("+FOCUS OUT"):
            inputID = event.split("+FOCUS OUT")[0].split('statinput')[1]
            formattedStat = formatStat(values['statinput' + inputID],reCalcWindow['stattext' + inputID].get(),values['componentselect'])
            reCalcWindow['statinput' + inputID].update(formattedStat)
            updateREOutputs(reCalcWindow)
            rarityList1inx, rarity, matches, postRE = getMatches(reCalcWindow)
            if rarity not in [0, '']:
                reCalcWindow['targetrarity'].update('1 in ' + str(int(1/tryFloat(rarity))))
            else:
                reCalcWindow['targetrarity'].update('')
            for i in range(0,9):
                reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                reCalcWindow['matchoutput' + str(i)].update(matches[i])
                reCalcWindow['matchpost' + str(i)].update(postRE[i])
        #except:
            #pass

        if event == 'relevelselect':
            rarityList1inx, rarity, matches, postRE = getMatches(reCalcWindow)
            if rarity not in [0, '']:
                reCalcWindow['targetrarity'].update('1 in ' + str(int(1/tryFloat(rarity))))
            else:
                reCalcWindow['targetrarity'].update('')
            updateREOutputs(reCalcWindow)
            for i in range(0,9):
                reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                reCalcWindow['matchoutput' + str(i)].update(matches[i])
                reCalcWindow['matchpost' + str(i)].update(postRE[i])
        
        if event == 'matchingtarget':
            rarityList1inx, rarity, matches, postRE = getMatches(reCalcWindow)
            if rarity not in [0, '']:
                reCalcWindow['targetrarity'].update('1 in ' + str(int(1/tryFloat(rarity))))
            else:
                reCalcWindow['targetrarity'].update('')
            for i in range(0,9):
                reCalcWindow['statrarity' + str(i)].update(rarityList1inx[i])
                reCalcWindow['matchoutput' + str(i)].update(matches[i])
                reCalcWindow['matchpost' + str(i)].update(postRE[i])

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


        if event == sg.WIN_CLOSED:
            break

    reCalcWindow.close()
    db.close()

reCalc()
