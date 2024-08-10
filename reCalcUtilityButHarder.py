import FreeSimpleGUI as sg
import numpy as np
import os
import sqlite3
import win32clipboard

from datetime import datetime, timedelta
from scipy.stats import norm

from buildTables import buildTables

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
        
def getMatches(stats,values,type,level,match):

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

    reLevel = type[0] + str(level%10)

    compStats = list(cur.execute("SELECT * from component WHERE type = ?", [type]).fetchall()[0][17:25])
    tails = list(cur.execute("SELECT * from component WHERE type = ?", [type]).fetchall()[0][9:17])
    if compStats[0] != 'A/HP':
        compStats.insert(0,'A/HP:')
        tails.insert(0,'1')
    
    compStats = [x for x in compStats if x != '']
    tails = [y for y in tails if y != '']

    brandNames = listify(cur.execute("SELECT name FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    brandWeights = listify(cur.execute("SELECT weight FROM brands WHERE relevel = ?", [reLevel]).fetchall())
    rawMeans = cur.execute("SELECT stat1mean, stat2mean, stat3mean, stat4mean, stat5mean, stat6mean, stat7mean, stat8mean, stat9mean FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    mods = cur.execute("SELECT stat1mod, stat2mod, stat3mod, stat4mod, stat5mod, stat6mod, stat7mod, stat8mod, stat9mod FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    means = []
    stdevs = []
    
    for i in range(0,len(compStats)):
        newRowStdevs = []
        newRowMeans = []
        for j in range(0,len(rawMeans)):
            newRowStdevs.append(tryFloat(rawMeans[j][i]) * tryFloat(mods[j][i]) / 2)
            newRowMeans.append(tryFloat(rawMeans[j][i]))
        means.append(newRowMeans)
        stdevs.append(newRowStdevs)

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
    
    rarityList = []

    for k in range(0,len(compStats)):

        value = values[k]    
        rarity = 0
        
        try:
            for i in range(0,len(brandNames)):
                mean = means[k][i]
                stdev = stdevs[k][i]
                zScore = (value - mean) / stdev
                cdf = norm.cdf(zScore)
                rarity += cdf * mixtureWeights[i]
        except:
            rarity = 0
        rarityList.append(float(rarity))

    #first, let's find average rarity, because why not. Gotta start somewhere.
    averageBasis1 = []

    for i in range(0,len(compStats)):
        if rarityList[i] == 0:
            averageBasis1.append('')
        elif tails[i] == '1':
            averageBasis1.append(1-rarityList[i])
        else:
            averageBasis1.append(rarityList[i])
    
    averageBasis2 = []

    for i in range(0,len(compStats)):
        sumTotalList = [x for x in averageBasis1 if x != '']
        sumTotal = np.sum(sumTotalList) - tryFloat(averageBasis1[i])
        averageBasis2.append(sumTotal/len(compStats))

    print(averageBasis2)

    matches = []

    reMults = [0.02, 0.03, 0.03, 0.04, 0.04, 0.05, 0.05, 0.06, 0.07, 0.07]
    reMult = reMults[level-1]
    postRE = []

    for i in range(0,len(compStats)):

        if tails[i] == tails[index]:
            targetRarity = np.double(rarity)
        else:
            targetRarity = np.double(1-rarity)

        delta = 1
        value = statMeans[i]
        testMin = 0
        testMax = 6 * statMeans[i]

        while delta > 0.000000000001:
            testRarity = 0
            for j in range(0,len(brandNames)):
                mean = means[i][j]
                stdev = stdevs[i][j]
                zScore = (value - mean) / stdev
                cdf = norm.cdf(zScore)
                testRarity += cdf * mixtureWeights[j]

            if testRarity < targetRarity:
                testMin = value
                value = (testMin + testMax) / 2
            else:
                testMax = value
                value = (testMin + testMax) / 2
            
            delta = abs(testRarity - targetRarity)
        
        if compStats[i] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
            multiplier = 1 + reMult * tryFloat(tails[i])
            postNotRounded = float(np.round(value * multiplier,2))
            postPreRounded = float(np.round(np.round(value,2) * multiplier,2))
            if compStats[i] == 'Refire Rate:':
                sign = '<'
                optimal = min(postPreRounded,postNotRounded)
                optimalWorstCase = optimal + 0.005
                optWorstCaseRaw = optimalWorstCase / multiplier
                if np.round(optWorstCaseRaw,2) > optWorstCaseRaw:
                    worstCaseRaw = np.round(optWorstCaseRaw,3) - 0.001
                else:
                    worstCaseRaw = np.round(optWorstCaseRaw,2) + 0.004
            else:
                sign = '>'
                optimal = max(postPreRounded,postNotRounded)
                optimalWorstCase = optimal - 0.00499999
                optWorstCaseRaw = optimalWorstCase / multiplier
                if np.round(optWorstCaseRaw,2) < optWorstCaseRaw:
                    worstCaseRaw = np.round(optWorstCaseRaw,3) + 0.001
                else:
                    worstCaseRaw = np.round(optWorstCaseRaw,2) - 0.004
            matches.append(sign + "{:.3f}".format(worstCaseRaw))
            postRE.append(sign + "{:.3f}".format(optimal))
        elif compStats[i] == 'Recharge:' and type == "Shield":
            matches.append("{:.2f}".format(float(np.round(value,2))))
            postRE.append("{:.2f}".format(float(np.round((1 + reMult * tryFloat(tails[i])) * value,2))))
        else:
            matches.append("{:.1f}".format(float(np.round(value,1))))
            postRE.append("{:.1f}".format(float(np.round((1 + reMult * tryFloat(tails[i])) * value,1))))

    print(matches)
    print(postRE)
    return rarity, matches

rarity, matches = getMatches(['A/HP:','Drain:','Mass:','Front HP:','Back HP:','Recharge:'],['', '', 37066.1, '', '', ''], "Shield", 10, 'average')
#need to restructure this to accept myriad inputs and switchable matching target (average, best, worst, per-stat, etc)