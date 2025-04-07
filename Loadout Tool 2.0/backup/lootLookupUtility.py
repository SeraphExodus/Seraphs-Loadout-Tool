import FreeSimpleGUI as sg
import math
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import operator
import os
import pyglet
import sqlite3
import win32clipboard

from io import BytesIO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import ImageGrab
from win32gui import FindWindow, GetWindowRect

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
baseFontLite = ("Roboto", 10)
baseFontStats = ("Roboto", 10, "bold")
buttonFont = ("Roboto", 13, "bold")
fontPadding = 0
elementPadding = 4
bgColor = '#202225'
boxColor = '#313338'
textColor = '#f3f4f5'

fontPath = str(os.path.abspath(os.path.join(os.path.dirname(__file__)))) + '/Fonts/Roboto-Bold.ttf'
fm.fontManager.addfont(fontPath)
prop = fm.FontProperties(fname=fontPath)

mpl.rcParams['figure.facecolor'] = boxColor
mpl.rcParams['axes.facecolor'] = bgColor
mpl.rcParams['axes.labelcolor'] = '#ffffff'
mpl.rcParams['axes.titlecolor'] = '#ffffff'
mpl.rcParams['axes.edgecolor'] = '#ffffff'
mpl.rcParams['axes.xmargin'] = 0
mpl.rcParams['xtick.labelcolor'] = '#ffffff'
mpl.rcParams['ytick.labelcolor'] = '#ffffff'
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = prop.get_name()

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

specialSources = ['Convoy Crate', 'Kash Nunes', 'Space Battle Reward', 'Lord Cyssc', "Nym's Starmap", 'High-Tier', 'Beacon', 'GCW2 Reward']

def toClipboard(type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(type, data)
    win32clipboard.CloseClipboard()

def tryFloat(x):
    try:
        return float(x)
    except:
        return 0
    
def sigfig(x, p):
    x = np.asarray(x)
    xpositive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10**(p-1))
    mag = 10 ** (p -1 - np.floor(np.log10(xpositive)))
    return np.round(x * mag) / mag

def listToHex(input, mode, reverse):

    colors = ['#ff0000','#ff6600','#ffff00','#99ff00','#00ff00','#00ffff']

    for i in range(0,len(input)):
        if input[i] != '' and input[i] > 100000000000:
            input[i] = ''
        elif input[i] == 0 and mode == 'linear':
            input[i] = ''

    intervalCount = len(colors)-1

    if mode == 'log':
        input = [math.log10(x) if x not in ['', 0] else x for x in input]
    
    maximum = max([x for x in input if x != ''])
    minimum = min([x for x in input if x != ''])

    if mode == 'log':
        inputColors = [int(round((x-minimum),0)) if x != '' else '' for x in input]
        for i in range(0,len(inputColors)):
            if inputColors[i] != '':
                if inputColors[i] > len(colors)-1:
                    inputColors[i] = len(colors)-1
    else:
        intervalSpacing = (maximum-minimum)/intervalCount
        if intervalSpacing == 0:
            intervalSpacing = 1
            reverse = True
        inputColors = [int(round((x-minimum)/intervalSpacing,0)) if x != '' else '' for x in input]

    if reverse:
        colors.reverse()
    hexes = [colors[x] if x != '' else '#ffffff' for x in inputColors]
    return hexes

def formatRarity(rarity):
    if type(rarity) == str or rarity == 0:
        return ''
    if rarity > 0 and rarity <= 1:
        rarity = 1
    else:
        rarity = int(rarity)
    if rarity >= 100000000000:
        rarity = '-'
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

def tableSortByDroprate(table, direction):

    for i in range(0,len(table)):
        table[i][2] = tryFloat(table[i][2][:-1])
    table = sorted(table,key=operator.itemgetter(2),reverse=direction)
    for i in range(0,len(table)):
        table[i][2] = str(table[i][2]) + '%'

    return table

def tableSortByOdds(table, direction):

    for i in range(0,len(table)):
        numOdds = table[i][1].split(' ')[2]
        if numOdds[-1] == 'k':
            numOdds = float(numOdds[:-1]) * 1000
        elif numOdds[-1] == 'M':
            numOdds = float(numOdds[:-1]) * 1000000
        elif numOdds[-1] == 'B':
            numOdds = float(numOdds[:-1]) * 1000000000
        table[i].append(float(numOdds))

    table = [x[:-1] for x in sorted(table,key=operator.itemgetter(2),reverse=direction)]

    return table

def constructConvoyStandardTable():

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    kashParts = []
    kashRates = []
    for i in ['a','b','c','d','e','r','s','w']:
        for j in ['5','6','7','8','9','0']:
            tableid = 'equipment_kash_nunes_' + i + j
            parts = [x for x in list(cur.execute("SELECT * FROM loottables WHERE loottable = ?", [tableid]).fetchall()[0])[1:] if x != '']
            kashParts.extend(parts)
            #selecting from 48 tables
            kashRates.extend([np.float64(1/(len(parts) * 48))] * len(parts))

    data.close()
    return kashParts, kashRates

def buildTable(entry):

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    brands = cur.execute("SELECT * FROM brands").fetchall()
    componentids = []
    componentStrings = []
    componentLevels = []
    componentData = []
    for i in brands:
        componentids.append(i[0])
        componentStrings.append(i[1])
        componentLevels.append(i[2])
        componentData.append(i[3:])

    npcShips = cur.execute("SELECT * FROM npcships").fetchall()
    ships = []
    rates = []
    groups = []
    for i in npcShips:
        ships.append(i[0])
        rates.append(tryFloat(i[2]) * tryFloat(i[3]))
        groups.append(i[4])
    
    lootGroups = cur.execute("SELECT * FROM lootgroups").fetchall()
    groupids = []
    groupTables = []
    for i in lootGroups:
        groupids.append(i[0])
        groupTables.append(i[1:])

    lootTables = cur.execute("SELECT * FROM loottables").fetchall()
    tableids = []
    loot = []
    for i in lootTables:
        tableids.append(i[0])
        loot.append(i[1:])

    dropRate = rates[ships.index(entry)]
    if dropRate == 0:
        return [], []

    lootGroup = groups[ships.index(entry)]
    lootTables = [x for x in groupTables[groupids.index(lootGroup)] if x != '']
    fullTable = []
    for i in lootTables:
        fullTable.append([x for x in loot[tableids.index(i)] if x != ''])

    if 'convoy_crate'.casefold() in entry:
        tier = int(entry[-1])
        standardRate = (60 - 5*tier)/100
        rareRate = (12 + 5*tier)/100
        rewardRate = 0.15
        decoRate = 0
        flightPlanRate = 0.05
        schemRate = 0.08
        tableRates = [rareRate, rewardRate, standardRate, decoRate, flightPlanRate, schemRate]
    elif 'gcw2_crate' in entry:
        standardRate = 0.35
        rareRate = 0.65
        tableRates = [standardRate, rareRate]
    elif 'beacon' in entry:
        standardRate = 0.34
        rewardRate = 0.1
        rareRate = 0.51
        tableRates = [standardRate, rewardRate, rareRate]
    else:
        tableRates = [1/len(lootTables)] * len(lootTables)

    tableids = []
    loot = []
    for i in lootTables:
        row = list(cur.execute("SELECT * FROM loottables WHERE loottable = ?", [i]).fetchall()[0])
        tableids.append(row[0])
        lootList = [x for x in row[1:] if x != '']
        loot.append(lootList)

    uniqueStrings = []
    rates = []
    fullList = []
    fullListRates = []

    for i in range(0,len(loot)):
        uniqueParts, counts = np.unique(loot[i], return_counts=True)
        rates.append([x/len(loot[i]) * tableRates[i] * dropRate for x in counts])
        uniqueStrings.append([componentStrings[componentids.index(x)] for x in uniqueParts])
        fullList.extend(uniqueStrings[-1])
        fullListRates.extend(rates[-1])

    if 'equipment_convoy_standard' in lootTables:
        index = lootTables.index('equipment_convoy_standard')
        kashParts, kashRates = constructConvoyStandardTable()
        kashRates = [x * tableRates[index] * dropRate for x in kashRates]
        kashParts = [componentStrings[componentids.index(x)] for x in kashParts]
        rates[index] = kashRates
        uniqueStrings[index] = kashParts
        fullList.extend(kashParts)
        fullListRates.extend(kashRates)

    fullListUniques = list(np.unique(fullList))
    fullListUniqueRates = []
    for i in fullListUniques:
        combinedRate = 0
        for j in range(0,len(loot)):
            if i in uniqueStrings[j]:
                combinedRate += rates[j][uniqueStrings[j].index(i)]
        fullListUniqueRates.append(combinedRate)
    
    data.close()

    return fullListUniques, fullListUniqueRates

def filterList(loot, compType, reLevel):

    if compType == '':
        compType = 'Any'
    if reLevel == '':
        reLevel = 'Any'

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    brands = cur.execute("SELECT * FROM brands").fetchall()
    componentids = []
    componentStrings = []
    componentLevels = []
    componentData = []
    for i in brands:
        componentids.append(i[0])
        componentStrings.append(i[1])
        componentLevels.append(i[2])
        componentData.append(i[3:])
    
    reLevel = str(reLevel)

    filterLevel = compType[0] + reLevel[-1]

    if compType != 'Any' and reLevel != 'Any':
        filteredLoot = [x for x in loot if componentLevels[componentStrings.index(x)] == filterLevel]
    elif compType == 'Any' and reLevel != 'Any':
        filteredLoot = [x for x in loot if componentLevels[componentStrings.index(x)][1] == reLevel[-1]]
    elif compType != 'Any' and reLevel == 'Any':
        filteredLoot = [x for x in loot if componentLevels[componentStrings.index(x)][0] == compType[0]]
    else:
        filteredLoot = loot

    data.close()
    return filteredLoot

def normalCDF(Z):
    try:
        y = 0.5 * (1 + math.erf(Z/math.sqrt(2)))
        return y
    except:
        SyntaxError

def calculateBestSources(lootLookupWindow, *selection):
    event, values = lootLookupWindow.read(timeout=0)

    component = values['componentselect']
    level = values['relevelselect']
    stat = values['inputstat']
    value = tryFloat(values['inputvalue'])

    #So what do we need to do here...
    #Step 1: Pull brands list and compute odds for each component brand in that RE level
    #Step 2: Get the odds of looting each brand from every. single. entry. in the list
    #step 3: Multiply stat rarity by drop rarity to get the chance from each ship type
    #step 4: sort high to low

    try:
        reLevel = component[0] + str(level)[-1]
    except:
        return []

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    #need to map stat names to numbers here.

    componentStats = [x for x in cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?", [component]).fetchall()[0] if x!= '']
    tails = [int(x) for x in cur.execute("SELECT stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re FROM component WHERE type = ?", [component]).fetchall()[0] if x!= '']

    if component != 'Armor':
        componentStats = ['A/HP:'] + componentStats
        tails = [1] + tails

    stat = stat + ':'

    statIndex = componentStats.index(stat)

    tail = tails[statIndex]

    compList = cur.execute("SELECT * FROM brands WHERE relevel = ?", [reLevel]).fetchall()
    brands = [x[0] for x in compList]
    means = [float(x[4 + 2 * statIndex]) for x in compList]
    mods = [float(x[5 + 2 * statIndex]) for x in compList]
    rarity = []
    for i in range(0,len(means)):
        stdev = means[i] * mods[i] / 2
        zScore = (value - means[i])/stdev
        zZero = (0 - means[i])/stdev #Removes negative values from the distribution (this is only significant for armor mass)
        rarity.append(normalCDF(zScore) - normalCDF(zZero))
    if tail == 1:
        rarity = [1-x for x in rarity]

    brandNames = [x[1] for x in compList]
    brandOdds = [[x, rarity[brandNames.index(x)]] for x in brandNames]

    #Step 1 done, onto step 2
    #So to accomplish this, we work from the bottom up. First, we go through all the loottables (need the convoy tables for this so I might wanna set up a standalone function that constructs it)
    #Iterate over the list of brands and check each loot table to see if the brand is present. Construct a list of tables for each brand, along with densities
    #Next, go through loot groups and find which ones contain the tables from the last step. Construct a list of loot groups for each brand, along with densities.
    #Finally, go through the ship list to see which ships own the loot groups, and apply droprates to get final density
    #With the final density in hand for each brand, multiply by the stat rarity for that brand and sum to get the drop chance for that ship
    #order ship list by drop chance

    tables = cur.execute("SELECT * FROM loottables").fetchall()
    density = []
    for i in tables:
        brandDensity = []
        for j in brands:
            table = [x for x in i if x != '']
            if table[0] == 'equipment_convoy_standard':
                kashParts, kashRates = constructConvoyStandardTable()
                try:
                    tableDensity = float(kashRates[kashParts.index(j)])
                except:
                    tableDensity = 0
            else:
                if len(table) == 1:
                    tableDensity = 0
                else:
                    tableDensity = table[1:].count(j)/len(table[1:])
            brandDensity.append(tableDensity)
        density.append(brandDensity)

    tableNames = [x[0] for x in tables]

    groups = cur.execute("SELECT * FROM lootgroups").fetchall()

    groupNames = [x[0] for x in groups]

    groupedDensity = []
    for i in groups:
        subTables = [x for x in i[1:] if x != '']
        if 'convoy' in i[0]:
            tier = int(i[0][-1])
            standardRate = (60 - 5*tier)/100
            rareRate = (12 + 5*tier)/100
            rewardRate = 0.15
            decoRate = 0
            flightPlanRate = 0.05
            schemRate = 0.08
            tableRates = [rareRate, rewardRate, standardRate, decoRate, flightPlanRate, schemRate]
        elif 'gcw2_crate' in i[0]:
            standardRate = 0.35
            rareRate = 0.65
            tableRates = [standardRate, rareRate]
        elif 'beacon' in i[0]:
            standardRate = 0.31
            rewardRate = 0.1
            rareRate = 0.51
            tableRates = [standardRate, rewardRate, rareRate]
        else:
            tableRates = [1/len(subTables)] * len(subTables)

        groupDensity = [0] * len(brands)
        for j in subTables:
            for k in tableNames:
                if j == k:
                    addedDensity = density[tableNames.index(k)]
                    for l in range(0,len(brands)):
                        groupDensity[l] += addedDensity[l] * tableRates[subTables.index(j)]
                
        groupedDensity.append(groupDensity)

    ships = cur.execute("SELECT * FROM npcships").fetchall()

    shipsTable = []
    densityList = []
    for i in ships:
        dropRate = float(i[2]) * float(i[3])
        shipDensity = [x * dropRate for x in groupedDensity[groupNames.index(i[4])]]
        shipRarity = sum([shipDensity[x] * rarity[x] for x in range(0,len(brands))])
        # if any(x in i[1] for x in specialSources):
        #     newLine = [i[1], shipRarity]
        # else:
        newLine = [i[1] + ' [' + i[0] + ']', shipRarity]
        if shipRarity >= 10 ** -8:
            shipsTable.append(newLine)
            densityList.append([i[1], shipDensity])

    shipsTable = sorted(shipsTable,key=operator.itemgetter(1), reverse=True)
    for i in shipsTable:
        if 'Convoy Reward' in i[0]:
            tier = int(i[0].split('Tier ')[1][0])
            lineString = ' Crates (' + formatRarity((3 + 2 * tier) * int(1/i[1]))[5:] + ' Items)'
        elif 'Beacon' in i[0] or 'Space Battle' in i[0]:
            lineString = ' Crates (' + formatRarity(30 * int(1/i[1]))[5:] + ' Items)'
        elif 'Kash Nunes' in i[0]:
            tokenRatio = level * 5 + 50
            lineString = ' (' + formatRarity((int(1/i[1]) * tokenRatio))[5:] + ' Tokens)'
        elif 'Reward' in i[0]:
            lineString = ' Runs'
        else:
            lineString = ' Kills'
        i[1] = formatRarity(1/i[1]) + lineString
    
    if len(selection) != 0:
        selection = selection[0].split(' [')[0]
        selectionDensity = [x[1] for x in densityList if x[0] == selection][0]
        selectionTable = []
        statRarity = []
        dropChance = []
        brandChance = []
        for i in brandOdds:
            if i[1] == 0 and selectionDensity[brandOdds.index(i)] == 0:
                statRarity.append('')
                dropChance.append('')
                brandChance.append('')
                selectionTable.append([i[0], '-', '-', '-'])
            elif i[1] == 0:
                statRarity.append('')
                dropChance.append(selectionDensity[brandOdds.index(i)])
                brandChance.append('')
                selectionTable.append([i[0], '-', str(round(selectionDensity[brandOdds.index(i)]*100,2)) + '%', '-'])
            elif selectionDensity[brandOdds.index(i)] == 0:
                statRarity.append(1/i[1])
                dropChance.append(selectionDensity[brandOdds.index(i)])
                brandChance.append('')
                selectionTable.append([i[0], formatRarity(int(1/i[1])), '-', '-'])
            else:
                statRarity.append(1/i[1])
                dropChance.append(selectionDensity[brandOdds.index(i)])
                brandChance.append(1/(i[1] * selectionDensity[brandOdds.index(i)]))
                selectionTable.append([i[0], formatRarity(int(1/i[1])), str(round(selectionDensity[brandOdds.index(i)]*100,2)) + '%', formatRarity(int(1/(i[1] * selectionDensity[brandOdds.index(i)])))])

        statRarityColors = listToHex(statRarity,'log',True)
        dropChanceColors = listToHex(dropChance,'linear',False)
        brandChanceColors = listToHex(brandChance,'log',True)
        for i in range(0,len(statRarity)):
            selectionTable[i].append(statRarityColors[i])
            selectionTable[i].append(dropChanceColors[i])
            selectionTable[i].append(brandChanceColors[i])
        return shipsTable, selectionTable
    else:
        return shipsTable

def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def delete_figure_agg(figure_agg):
    figure_agg.get_tk_widget().forget()
    plt.close('all')

def generateDropRateChart(lootLookupWindow):

    event, values = lootLookupWindow.read(timeout=0)

    selection = values['shipsdropdown']
    component = values['componentselect']
    level = values['relevelselect']
    stat = values['inputstat']
    value = tryFloat(values['inputvalue'])
    count = values['tokenskills']

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    brands = cur.execute("SELECT * FROM brands").fetchall()
    componentids = []
    componentStrings = []
    componentLevels = []
    componentData = []
    for i in brands:
        componentids.append(i[0])
        componentStrings.append(i[1])
        componentLevels.append(i[2])
        componentData.append(i[3:])

    npcShips = cur.execute("SELECT * FROM npcships").fetchall()
    ships = []
    shipids = []
    shipStrings = []
    rates = []
    groups = []
    for i in npcShips:
        shipids.append(i[0])
        ships.append(i[1])
        # if any(x in i[1] for x in specialSources):
        #     shipStrings.append(i[1])
        # else:
        shipStrings.append(i[1] + ' [' + i[0] + ']')
        rates.append(tryFloat(i[2]) * tryFloat(i[3]))
        groups.append(i[4])

    x = []
    y = []
    x2 = []
    y2 = []

    overflow = False

    if selection in shipStrings:
        entryid = shipids[shipStrings.index(selection)]               
        uniques, lootRates = buildTable(entryid)

        tableLoot = uniques

        tableLoot = filterList(tableLoot,component,level)

        tableValues = [[x, lootRates[uniques.index(x)]] for x in tableLoot]

        compStats = [x[:-1] for x in list(cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0])]
        if values['componentselect'] != 'Armor':
            compStats = ['A/HP'] + compStats

        index = compStats.index(stat)
        level = values['componentselect'][0] + str(values['relevelselect'])[-1]
        means = []
        mods = []
        for i in tableValues:
            entry = i[0]
            compData = componentData[componentStrings.index(entry)]
            means.append(tryFloat(compData[1 + 2 * index]))
            mods.append(tryFloat(compData[2 + 2 * index]))

        tails = list(cur.execute('SELECT stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re FROM component WHERE type = ?',[values['componentselect']]).fetchall()[0])
        if values['componentselect'] != 'Armor':
            tails = [1] + tails
        tail = int(tails[index])
        
        rarity = []
        for i in range(0,len(means)):
            stdev = means[i] * mods[i] / 2
            zScore = (value - means[i])/stdev
            zZero = (0 - means[i])/stdev #Removes negative values from the distribution (this is only significant for armor mass)
            rarity.append(normalCDF(zScore) - normalCDF(zZero))
        if tail == 1:
            rarity = [1-x for x in rarity]

        lootChance = [x[1] * rarity[tableValues.index(x)] for x in tableValues]

        p = sum(lootChance)
        q = 1-p
        k = 0 #chance of 0 successes, then append the complement of that
        samples = 1000
        
        try:
            y = []
            dx = int(3/p) #determines how far the x-axis extends
            x = np.arange(0,dx+1,int(dx/samples))
            for n in x:
                try:
                    y.append(1-math.comb(n,k)*math.pow(p,k)*math.pow(q,n-k))
                except:
                    y.append(0)
            if count not in ['','0']:
                reset = True
                while reset == True:
                    y2 = []
                    errorCount = 0
                    count = int(count)
                    if "kash nunes".casefold() in selection.casefold():
                        tokenMult = int(values['relevelselect']) * 5 + 50
                        count = int(count/tokenMult)
                        expected = int(count*p)
                    else:
                        count = int(count)
                        expected = int(count*p)
                    if expected > 200:
                        errorCount += 1
                    else:
                        try:
                            apex = math.comb(count,expected)*math.pow(p,expected)*math.pow(q,count-expected)
                        except:
                            errorCount += 1
                        low = int(max(0,expected-25))
                        high = int(expected+25)
                        x2 = range(low,high+1)
                        for k in x2:
                            try:
                                y2.append(math.comb(count,k)*math.pow(p,k)*math.pow(q,count-k))
                            except:
                                errorCount += 1
                    if errorCount == 0:
                        reset = False
                        if "kash nunes".casefold() in selection.casefold():
                            lootLookupWindow['tokenskills'].update(int(count*tokenMult))
                        else:
                            lootLookupWindow['tokenskills'].update(int(count))
                    else:
                        overflow = True
                        if "kash nunes".casefold() in selection.casefold():
                            count = int(0.99 * count * tokenMult)
                        else:
                            count = int(0.99 * count)

                if expected > 0:
                    y2reduced = [y for y in y2 if y >= apex/10]
                    x2reduced = [x2[y2.index(x)] for x in y2reduced]
                    # if len(y2reduced) > 10:
                    #     sampleWidth = math.ceil(len(y2reduced)/10)
                    #     sampleIndices = np.arange(0,len(y2reduced)+1,sampleWidth)
                    #     x2reduced = [x2reduced[x] for x in sampleIndices]
                    #     y2reduced = [y2reduced[x] for x in sampleIndices]
                    x2 = x2reduced
                    y2 = y2reduced
                else:
                    x2 = x2[0:6]
                    y2 = y2[0:6]
        except:
            pass

    data.close()

    return x, y, x2, y2, overflow

def lootLookup():

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    brands = cur.execute("SELECT * FROM brands").fetchall()
    componentids = []
    componentStrings = []
    componentLevels = []
    componentData = []
    for i in brands:
        componentids.append(i[0])
        componentStrings.append(i[1])
        componentLevels.append(i[2])
        componentData.append(i[3:])

    npcShips = cur.execute("SELECT * FROM npcships").fetchall()
    ships = []
    shipids = []
    shipStrings = []
    rates = []
    dropCounts = []
    dropRates = []
    groups = []
    for i in npcShips:
        shipids.append(i[0])
        ships.append(i[1])
        # if any(x in i[1] for x in specialSources):
        #     shipStrings.append(i[1])
        # else:
        shipStrings.append(i[1] + ' [' + i[0] + ']') 
        rates.append(tryFloat(i[2]) * tryFloat(i[3]))
        dropCounts.append(tryFloat(i[2]))
        dropRates.append(tryFloat(i[3]))
        groups.append(i[4])
    
    lootGroups = cur.execute("SELECT * FROM lootgroups").fetchall()
    groupids = []
    groupTables = []
    for i in lootGroups:
        groupids.append(i[0])
        groupTables.append(i[1:])

    lootTables = cur.execute("SELECT * FROM loottables").fetchall()
    tableids = []
    loot = []
    for i in lootTables:
        tableids.append(i[0])
        loot.append(i[1:])

    selectLeft1 = [
        [sg.Push(),sg.Text("Component Type:",font=baseFont,p=1,key='filtercomptext')],
        [sg.Push(),sg.Text("RE Level:",font=baseFont,p=1,key='filterleveltext')],
    ]

    selectLeft2 = [
        [sg.Push(),sg.Text('',key='inputstattext',font=baseFont,p=1,visible=False)],
        [sg.Push(),sg.Text('',key='inputvaluetext',font=baseFont,p=1,visible=False)],
        [sg.Push(),sg.Text('',key='posttext',font=baseFont,p=1,visible=False)],
    ]

    selectLeft3 = [
        [sg.Push(),sg.Text('',key='tokenskillstext',font=baseFont,p=1,visible=False)],
        [sg.Push(),sg.Text('Chance to Loot:',key='chancetext',font=baseFont,p=1,visible=False)],
    ]

    selectRight1 = [
        [sg.Combo(values=['Any', 'Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'], default_value='Any', key='componentselect',font=baseFont,s=(13,9),enable_events=True,readonly=True,p=1),sg.Push()],
        [sg.Combo(values=['Any', 1,2,3,4,5,6,7,8,9,10],key='relevelselect', default_value='Any', font=baseFont,s=(5,11),readonly=True,enable_events=True,p=1),sg.Push()],
    ]

    selectRight2 = [
        [sg.Combo(values=[],key='inputstat',visible=False,enable_events=True,readonly=True,p=1,font=baseFont)],
        [sg.Input('',key='inputvalue',visible=False,p=1,font=baseFont,s=8,enable_events=True)],
        [sg.Text('',key='postvalue',font=baseFont,p=1,visible=False)],
    ]

    selectRight3 = [
        [sg.Input('',key='tokenskills',font=baseFont,p=1,visible=False,enable_events=True,size=10)],
        [sg.Text('',key='chance',font=baseFont,p=1,visible=False)],
    ]

    lootGroupsFrame = [
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='lootgrouptext',visible=True),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='lootgroup',visible=True),sg.Push()],
        [sg.VPush()]
    ]

    for i in range(1,7):
        lootGroupsFrame.append([sg.Push(),sg.Text('',font=baseFont,p=1,key='loottable' + str(i),visible=True),sg.Push()])

    lootGroupsFrame.append([sg.VPush()])

    dropCountLeft = [
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='dropcounttext1')],
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='dropcounttext2')],
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='dropcounttext3')],
    ]

    dropCountRight = [
        [sg.Text('',font=baseFont,p=1,key='dropcountvalue1'),sg.Push()],
        [sg.Text('',font=baseFont,p=1,key='dropcountvalue2'),sg.Push()],
        [sg.Text('',font=baseFont,p=1,key='dropcountvalue3'),sg.Push()],
    ]

    dropCountLine = [sg.Push(),sg.Frame('',dropCountLeft,border_width=0,p=elementPadding,s=(180,60)),sg.Frame('',dropCountRight,border_width=0,p=elementPadding,s=(120,60)),sg.Push()]

    lootGroupsFrame.append(dropCountLine)

    for i in range(0,3):
        lootGroupsFrame.append([sg.VPush()])

    selectFrame = [
        [sg.VPush()],
        [sg.Push(),sg.Text("Select Mode:",font=baseFont,p=1),sg.Combo(values=['View Loot Tables','Find Best Sources','View Drop Rate Charts'],default_value='View Loot Tables',readonly=True,key='modeselect',font=baseFont,p=1,size=(20,3),enable_events=True),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Text("Loot Source:",font=baseFont,p=1,key='shipsdropdowntext'), sg.Combo(values=shipStrings, key='shipsdropdown',font=baseFont, p=1, enable_per_char_events=True, size=(40,20), auto_size_text=False, enable_events=True),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Text('Filter by',font=baseFont,p=1,key='filtertext'),sg.Push()],
        [sg.Push(),sg.Frame('',selectLeft1,border_width=0,p=elementPadding,s=(135,40)),sg.Frame('',selectRight1,border_width=0,p=elementPadding,s=(165,40)),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',selectLeft2,border_width=0,p=elementPadding,s=(135,60)),sg.Frame('',selectRight2,border_width=0,p=elementPadding,s=(165,60)),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',selectLeft3,border_width=0,p=elementPadding,s=(135,40)),sg.Frame('',selectRight3,border_width=0,p=elementPadding,s=(165,40)),sg.Push()],
        [sg.VPush()],
    ]

    brandListCol1 = [
        [sg.Push(),sg.Text('Selected Source [UID]',font=baseFont,p=0,key='brandlistcol1header1'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFontLite,p=0,key='brandlistcol1header2'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol1header3'),sg.Push()],
    ]

    brandListCol1a = [
        [sg.Push(),sg.Text('Brand Name',font=baseFont,p=0,key='brandlistcol1aheader4'),sg.Push()],
    ]

    brandListCol1b = [
        [sg.Push(),sg.Text('Stat Odds',font=baseFont,p=0,key='brandlistcol1bheader4'),sg.Push()],
    ]


    brandListCol2 = [
        [sg.Push(),sg.Text('Avg. Drops',font=baseFont,p=0,key='brandlistcol2header1'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFontLite,p=0,key='brandlistcol2header2'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol2header3'),sg.Push()],
        [sg.Push(),sg.Text('Drop Chance',font=baseFont,p=0,key='brandlistcol2header4'),sg.Push()],
    ]

    brandListCol3 = [
        [sg.Push(),sg.Text('Total Odds',font=baseFont,p=0,key='brandlistcol3header1'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFontLite,p=0,key='brandlistcol3header2'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol3header3'),sg.Push()],
        [sg.Push(),sg.Text('Brand Odds',font=baseFont,p=0,key='brandlistcol3header4'),sg.Push()],
    ]

    for i in range(0,17):
        brandListCol1a.append([sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol1aline' + str(i)),sg.Push()])
        brandListCol1b.append([sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol1bline' + str(i)),sg.Push()])
        brandListCol2.append([sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol2line' + str(i)),sg.Push()])
        brandListCol3.append([sg.Push(),sg.Text('',font=baseFont,p=0,key='brandlistcol3line' + str(i)),sg.Push()])

    brandListCol1 = [
        [sg.Push(),sg.Frame('',brandListCol1,border_width=0,p=0),sg.Push()],
        [sg.Frame('',brandListCol1a,border_width=0,p=0),sg.Frame('',brandListCol1b,border_width=0,p=0)]
    ]

    brandListFrame = [
        [sg.Frame('',brandListCol1,border_width=0,p=0),sg.Frame('',brandListCol2,border_width=0,p=0),sg.Frame('',brandListCol3,border_width=0,p=0)]
    ]

    Layout = [
        [
            sg.Frame('',selectFrame,border_width=0,expand_x=True,size=(420,420)),
            sg.Table(values=[],headings=['Level', 'Component', 'Drop Rate'],col_widths=[5, 40, 10], key='loottable',num_rows=25, auto_size_columns=False,enable_click_events=True, cols_justification=['center','left','center'], header_font=baseFont, font=('Roboto',10),),
            sg.Frame('',lootGroupsFrame,border_width=0,p=elementPadding,key='lootgroupframe', size=(300,400)),
            sg.Table(values=[],headings=['Loot Source','Odds'],col_widths=[50, 25], key='sourcestable',num_rows=25, auto_size_columns=False,enable_click_events=True, enable_events=True, cols_justification=['center','center'], header_font=baseFont, font=('Roboto',10),visible=False),
            #sg.Table(values=[],headings=['Brand Name','Stat Odds','Drop Chance','Overall Chance'],col_widths=[40,10,10,25],key='brandtable',num_rows=25,auto_size_columns=False,cols_justification=['center','center','center','center'],header_font=baseFont, font=('Roboto',10),visible=False,hide_vertical_scroll=True),
            sg.Frame('',brandListFrame,border_width=0,key='brandtable',visible=False),
            sg.Canvas(size=(1500,500),key='dropratechart',visible=False,background_color=bgColor)
        ]
    ]

    lootLookupWindow = sg.Window("Loot Lookup Utility",Layout,modal=False,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True,)

    lootLookupWindow.bind('<Control-c>','Capture Screenshot')
    lootLookupWindow.bind('<Return>','Clear Focus')

    inputKeys = ['shipsdropdown','inputvalue','tokenskills']
    elements = [lootLookupWindow[key] for key in inputKeys]
    for element in elements:
        element.bind('<FocusOut>','+FOCUS OUT')

    fig = plt.Figure(figsize=(12,4))
    ax = fig.add_subplot(121)
    ax.set_title('Chance to Loot One or More')
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid()
    ax2 = fig.add_subplot(122)
    ax2.set_title('Number of Parts at Least This Good')
    ax2.set_xlabel("")
    ax2.set_ylabel("")
    ax2.grid()
    fig_canvas_agg = draw_figure(lootLookupWindow['dropratechart'].TKCanvas,fig)

    tableValues = []
    shipsTable = []
    selection = ''
    buildGraphTriggerFlag = False
    sortFlag = 2
    oldMode = 'View Loot Tables' #since it's the default

    while True:
        event, values = lootLookupWindow.read()

        if values == None:
            break

        if event == 'Clear Focus':
            lootLookupWindow.TKroot.focus_set()

        if event == 'Capture Screenshot':
            appWindow = FindWindow(None, "Loot Lookup Utility")
            rect = GetWindowRect(appWindow)
            rect = (rect[0]+8, rect[1]+31, rect[2]-8, rect[3]-8)
            grab = ImageGrab.grab(bbox=rect, all_screens=True)
            screencapOutput = BytesIO()
            grab.convert("RGB").save(screencapOutput,"BMP")
            capdata = screencapOutput.getvalue()[14:]
            screencapOutput.close()
            toClipboard(win32clipboard.CF_DIB, capdata)

        if event in ['shipsdropdown','componentselect','relevelselect','inputstat']: #does some housekeeping when fields are modified
            if event in ['componentselect','relevelselect','inputstat'] and values['modeselect'] != 'View Loot Tables':
                lootLookupWindow['shipsdropdown'].update(value='')  
            lootLookupWindow['tokenskillstext'].update(visible=False)
            lootLookupWindow['tokenskills'].update('',visible=False)
            lootLookupWindow['chancetext'].update(visible=False)
            lootLookupWindow['chance'].update('',visible=False)
            ax.cla()
            ax.set_title('Chance to Loot One or More')
            ax.set_xlabel("")
            ax.set_ylabel("")
            ax.set_ylim([0,1])
            ax.grid()
            fig_canvas_agg.draw()
            ax2.cla()
            ax2.set_title('Number of Parts at Least This Good')
            ax2.set_xlabel("")
            ax2.set_ylabel("")
            ax2.set_ylim([0,1])
            ax2.grid()
            fig_canvas_agg.draw()

        if event == 'modeselect':
            newMode = values['modeselect']
            if newMode == 'View Loot Tables' and oldMode != newMode:
                sortFlag = 2
                lootLookupWindow['shipsdropdowntext'].update('Loot Source:', visible=True)
                lootLookupWindow['shipsdropdown'].update(value='', values=shipStrings,visible=True)
                lootLookupWindow['loottable'].update(values=[], visible=True)
                lootLookupWindow['filtertext'].update('Filter by',visible=True)
                lootLookupWindow['filtercomptext'].update(visible=True)
                lootLookupWindow['filterleveltext'].update(visible=True)
                lootLookupWindow['sourcestable'].update(visible=False)
                lootLookupWindow['brandtable'].update(visible=False)
                lootLookupWindow['dropratechart'].update(visible=False)
                lootLookupWindow['inputstattext'].update('',visible=False)
                lootLookupWindow['inputstat'].update('',visible=False)
                lootLookupWindow['inputvaluetext'].update('',visible=False)
                lootLookupWindow['inputvalue'].update('',visible=False)
                lootLookupWindow['posttext'].update('',visible=False)
                lootLookupWindow['postvalue'].update('',visible=False)
                lootLookupWindow['componentselect'].update(value='',values=['Any', 'Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'])
                lootLookupWindow['relevelselect'].update(value='',values=['Any', 1,2,3,4,5,6,7,8,9,10])
                lootLookupWindow['tokenskillstext'].update(visible=False)
                lootLookupWindow['tokenskills'].update('',visible=False)
                lootLookupWindow['chancetext'].update(visible=False)
                lootLookupWindow['chance'].update('',visible=False)
                lootLookupWindow['lootgroupframe'].update(visible=True)
                lootLookupWindow['lootgroupframe'].Widget.config(width=300)
            elif newMode == 'Find Best Sources' and oldMode != newMode:
                try:
                    shipsTable = calculateBestSources(lootLookupWindow)
                    filteredValues = [x[0] for x in shipsTable]
                    filteredValues.sort()
                    lootLookupWindow['shipsdropdown'].update(value='',values=filteredValues,visible=True)
                except:
                    lootLookupWindow['shipsdropdown'].update(value='',values=shipStrings,visible=True)
                sortFlag = 1
                lootLookupWindow['shipsdropdowntext'].update('Filter Source:', visible=True)
                lootLookupWindow['loottable'].update(visible=False)
                lootLookupWindow['filtertext'].update('Input Component Stats',visible=True)
                lootLookupWindow['filtercomptext'].update(visible=True)
                lootLookupWindow['filterleveltext'].update(visible=True)
                lootLookupWindow['sourcestable'].update(values=[], visible=True)
                lootLookupWindow['brandtable'].update(visible=False)
                lootLookupWindow['dropratechart'].update(visible=False)
                lootLookupWindow['tokenskillstext'].update(visible=False)
                lootLookupWindow['tokenskills'].update('',visible=False)
                lootLookupWindow['chancetext'].update(visible=False)
                lootLookupWindow['chance'].update('',visible=False)
                lootLookupWindow['lootgroupframe'].update(visible=False)
                lootLookupWindow['lootgrouptext'].update('',visible=False)
                lootLookupWindow['lootgroup'].update('',visible=False)
                for i in range(1,7):
                    lootLookupWindow['loottable' + str(i)].update('',visible=False)
                if values['componentselect'] == 'Any':
                    lootLookupWindow['componentselect'].update(value='',values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'])
                else:
                    lootLookupWindow['componentselect'].update(value=values['componentselect'],values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'])
                if values['relevelselect'] == 'Any':
                    lootLookupWindow['relevelselect'].update(value='',values=[1,2,3,4,5,6,7,8,9,10])
                else:
                    lootLookupWindow['relevelselect'].update(value=values['relevelselect'],values=[1,2,3,4,5,6,7,8,9,10])

                if values['componentselect'] not in ['Any',''] and values['relevelselect'] not in ['Any','']:
                    compStats = [x[:-1] for x in list(cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0])]
                    if values['componentselect'] != 'Armor':
                        compStats = ['A/HP'] + compStats
                    lootLookupWindow['inputstattext'].update('Stat:',visible=True)
                    lootLookupWindow['inputstat'].update(value=values['inputstat'],values=compStats,visible=True,size=(15,len(compStats)))
                    lootLookupWindow['inputvaluetext'].update('Value:',visible=True)
                    lootLookupWindow['inputvalue'].update(visible=True)
                    lootLookupWindow['posttext'].update('Post:',visible=True)
                    lootLookupWindow['postvalue'].update(visible=True)
                else:
                    lootLookupWindow['inputstattext'].update('',visible=False)
                    lootLookupWindow['inputstat'].update('',visible=False)
                    lootLookupWindow['inputvaluetext'].update('',visible=False)
                    lootLookupWindow['inputvalue'].update('',visible=False)
                    lootLookupWindow['posttext'].update('',visible=False)
                    lootLookupWindow['postvalue'].update('',visible=False)
            elif newMode == 'View Drop Rate Charts' and oldMode != newMode:
                lootLookupWindow['shipsdropdowntext'].update('Loot Source:', visible=True)
                if selection in shipStrings:
                    lootLookupWindow['shipsdropdown'].update(value=selection,visible=True)
                    selection = ''
                    buildGraphTriggerFlag = True
                else:
                    lootLookupWindow['shipsdropdown'].update(value='',visible=True)
                    buildGraphTriggerFlag = False
                lootLookupWindow['loottable'].update(visible=False)
                lootLookupWindow['filtertext'].update(visible=True)
                lootLookupWindow['filtercomptext'].update(visible=True)
                lootLookupWindow['filterleveltext'].update(visible=True)
                lootLookupWindow['sourcestable'].update(values=[], visible=False)
                lootLookupWindow['brandtable'].update(visible=False)
                lootLookupWindow['dropratechart'].update(visible=True)
                lootLookupWindow['lootgroupframe'].update(visible=False)
                lootLookupWindow['lootgrouptext'].update('',visible=False)
                lootLookupWindow['lootgroup'].update('',visible=False)
                for i in range(1,7):
                    lootLookupWindow['loottable' + str(i)].update('',visible=False)
                if values['componentselect'] == 'Any':
                    lootLookupWindow['componentselect'].update(value='',values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'])
                else:
                    lootLookupWindow['componentselect'].update(value=values['componentselect'],values=['Armor','Booster','Capacitor','Droid Interface','Engine','Reactor','Shield','Weapon'])
                if values['relevelselect'] == 'Any':
                    lootLookupWindow['relevelselect'].update(value='',values=[1,2,3,4,5,6,7,8,9,10])
                else:
                    lootLookupWindow['relevelselect'].update(value=values['relevelselect'],values=[1,2,3,4,5,6,7,8,9,10])

                if values['componentselect'] not in ['Any',''] and values['relevelselect'] not in ['Any','']:
                    compStats = [x[:-1] for x in list(cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0])]
                    if values['componentselect'] != 'Armor':
                        compStats = ['A/HP'] + compStats
                    lootLookupWindow['inputstattext'].update('Stat:',visible=True)
                    lootLookupWindow['inputstat'].update(value=values['inputstat'],values=compStats,visible=True,size=(15,len(compStats)))
                    lootLookupWindow['inputvaluetext'].update('Value:',visible=True)
                    lootLookupWindow['inputvalue'].update(visible=True)
                    lootLookupWindow['posttext'].update('Post:',visible=True)
                    lootLookupWindow['postvalue'].update(visible=True)
                else:
                    lootLookupWindow['inputstattext'].update('',visible=False)
                    lootLookupWindow['inputstat'].update('',visible=False)
                    lootLookupWindow['inputvaluetext'].update('',visible=False)
                    lootLookupWindow['inputvalue'].update('',visible=False)
                    lootLookupWindow['posttext'].update('',visible=False)
                    lootLookupWindow['postvalue'].update('',visible=False)

        if event in ['componentselect', 'relevelselect']:
            lootLookupWindow['brandtable'].update(visible=False)
            if values['modeselect'] == 'View Loot Tables':
                entry = values['shipsdropdown']
                if entry in shipStrings:

                    entryid = shipids[shipStrings.index(entry)]               
                    uniques, lootRates = buildTable(entryid)

                    tableLoot = uniques
                
                    tableLoot = filterList(tableLoot,values['componentselect'],values['relevelselect'])

                    lootRates = [str(sigfig((x * 100),4)) + '%' for x in lootRates]
                    tableValues = [[componentLevels[componentStrings.index(x)], x, lootRates[uniques.index(x)]] for x in tableLoot]
                    tableValues = sorted(tableValues, key=operator.itemgetter(0,1))  
                    tableValues = sorted(tableValues, key=operator.itemgetter(2),reverse=True)
                sortFlag = 2
                lootLookupWindow['loottable'].update(values = tableValues)
            else:
                if values['componentselect'] not in ['Any',''] and values['relevelselect'] not in ['Any','']:
                    compStats = [x[:-1] for x in list(cur.execute("SELECT stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0])]
                    if values['componentselect'] != 'Armor':
                        compStats = ['A/HP'] + compStats
                    lootLookupWindow['inputstattext'].update('Stat:',visible=True)
                    lootLookupWindow['inputstat'].update(value=values['inputstat'],values=compStats,visible=True,size=(15,len(compStats)))
                    lootLookupWindow['inputvaluetext'].update('Value:',visible=True)
                    lootLookupWindow['inputvalue'].update('',visible=True)
                    lootLookupWindow['posttext'].update('Post:',visible=True)
                    lootLookupWindow['postvalue'].update('',visible=True)
                else:
                    lootLookupWindow['inputstattext'].update('',visible=False)
                    lootLookupWindow['inputstat'].update('',visible=False)
                    lootLookupWindow['inputvaluetext'].update('',visible=False)
                    lootLookupWindow['inputvalue'].update('',visible=False)
                    lootLookupWindow['posttext'].update('',visible=False)
                    lootLookupWindow['postvalue'].update('',visible=False)

        if event == 'shipsdropdown':
            entry = values['shipsdropdown']
            filtered = []
            if entry == '':
                filtered = shipStrings
            else:
                for i in shipStrings:
                    if values['shipsdropdown'].casefold() in i.casefold():
                        filtered.append(i)
            lootLookupWindow['shipsdropdown'].update(value=entry, values=filtered)

            if entry in shipStrings and values['modeselect'] == 'View Loot Tables':
                lootGroup = groups[shipStrings.index(entry)]

                lootLookupWindow['lootgrouptext'].update('Loot Group',visible=True)
                lootLookupWindow['lootgroup'].update(lootGroup,visible=True)
                lootLookupWindow['dropcounttext1'].update('Item Drop Rolls: ',visible=True)
                lootLookupWindow['dropcounttext2'].update('Chance per Roll: ',visible=True)
                lootLookupWindow['dropcounttext3'].update('Avg. Items Dropped: ',visible=True)
                rate = dropRates[shipStrings.index(entry)]
                if 'convoy' in entry and 'crate' in entry:
                    totalDrops = str(int(dropCounts[shipStrings.index(entry)])-1) + ' - ' + str(int(dropCounts[shipStrings.index(entry)])+1)
                    lootLookupWindow['dropcountvalue1'].update(totalDrops,visible=True)
                    lootLookupWindow['dropcountvalue2'].update(str((tryFloat(rate*100))) + '%',visible=True)
                    lootLookupWindow['dropcountvalue3'].update(dropCounts[shipStrings.index(entry)],visible=True)
                else:
                    totalDrops = dropCounts[shipStrings.index(entry)]
                    lootLookupWindow['dropcountvalue1'].update(str(int(totalDrops)),visible=True)
                    lootLookupWindow['dropcountvalue2'].update(str((tryFloat(rate*100))) + '%',visible=True)
                    lootLookupWindow['dropcountvalue3'].update(round(totalDrops*rate,3),visible=True)
                
                tables = groupTables[groupids.index(lootGroup)]
                while len(tables) < 6:
                    tables += ['']

                if len(tables) > 6:
                    tables = tables[0:6]
                for i in range(1,7):
                    lootLookupWindow['loottable' + str(i)].update(tables[i-1],visible=True)

            if values['modeselect'] == 'View Loot Tables':
                if entry in shipStrings:
                    lootLookupWindow['shipsdropdown'].update(value=entry, values=shipStrings)

                    entryid = shipids[shipStrings.index(entry)]
                    lootLookupWindow['loottable'].update(values = [])
                    uniques, lootRates = buildTable(entryid)

                    tableLoot = uniques

                    tableLoot = filterList(tableLoot,values['componentselect'],values['relevelselect'])
                    lootRates = [str(sigfig((x * 100),4)) + '%' for x in lootRates]
                    tableValues = [[componentLevels[componentStrings.index(x)], x, lootRates[uniques.index(x)]] for x in tableLoot]
                    tableValues = sorted(tableValues, key=operator.itemgetter(0,1))  
                    tableValues = tableSortByDroprate(tableValues,True)
                    sortFlag = 2

                    lootLookupWindow['loottable'].update(values = tableValues)

        if event == 'inputvalue':
            try:
                float(values['inputvalue'])
            except:
                if values['inputvalue'] == '.':
                    lootLookupWindow['inputvalue'].update('0.')
                else:
                    lootLookupWindow['inputvalue'].update(values['inputvalue'][:-1])

        if event == 'tokenskills':
            try:
                float(values['tokenskills'])
                if values['tokenskills'][-1] == '.':
                    lootLookupWindow['tokenskills'].update(values['tokenskills'][:-1])
            except:
                lootLookupWindow['tokenskills'].update(values['tokenskills'][:-1])

        if event == 'inputstat':
            lootLookupWindow['inputvalue'].update('')
            lootLookupWindow['postvalue'].update('')

        try:
            if (event.endswith("+FOCUS OUT") and '' not in [values['componentselect'],values['relevelselect']] and tryFloat(values['inputvalue']) != 0 and values['inputvalue'] != '' and values['modeselect'] == 'View Drop Rate Charts') or buildGraphTriggerFlag:
                if buildGraphTriggerFlag: #This var triggers when a selection is made in Find Best Sources and then mode is switched to View Drop Rate Charts in order to get the graph to plot automatically
                    event, values = lootLookupWindow.read(timeout=0)
                    buildGraphTriggerFlag = False
                shipsTable = calculateBestSources(lootLookupWindow)
                entry = values['shipsdropdown']
                if entry != '' and any([entry.casefold() in x[0].casefold() for x in shipsTable]):
                    displayedRows = [x for x in shipsTable if entry.casefold() in x[0].casefold()]
                    filteredValues = [x[0] for x in displayedRows]
                    filteredValues.sort()
                    lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
                else:
                    displayedRows = shipsTable
                    filteredValues = [x[0] for x in shipsTable]
                    filteredValues.sort()
                    lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
                x, y, xalt, yalt, overflow = generateDropRateChart(lootLookupWindow)
                ax.cla()
                ax2.cla()
                if y != []:
                    if values['tokenskills'] not in ['', 0]:
                        count = int(values['tokenskills'])
                        x2 = np.array([count, count])
                        if 'kash nunes'.casefold() in values['shipsdropdown'].casefold():
                            tokenMult = int(values['relevelselect']) * 5 + 50
                            count = int(count/tokenMult)
                            if count > x[-1]:
                                x2 = np.array([x[-1]*tokenMult, x[-1]*tokenMult])
                        else:
                            if count > x[-1]:
                                x2 = np.array([x[-1], x[-1]])
                        chance = '≥' + str(int(tryFloat(y[-1])*100)) + '%'
                        y2 = np.array([0, y[-1]])
                        for i in range(0,len(x)):
                            if x[i] >= count and count in x:
                                chance = str(round(tryFloat(y[i])*100,2)) + '%'
                                y2 = np.array([0, y[i]])
                                break
                            elif x[i] >= count and count not in x:
                                chance = str(round(tryFloat((y[i] + y[i-1])/2)*100,2)) + '%'
                                y2 = np.array([0, (y[i] + y[i-1])/2])
                                break
                        lootLookupWindow['chancetext'].update(visible=True)
                        lootLookupWindow['chance'].update(chance, visible=True)
                    else:
                        x2 = []
                        y2 = []
                        lootLookupWindow['chancetext'].update(visible=False)
                        lootLookupWindow['chance'].update('', visible=False)
                    lootLookupWindow['tokenskills'].update(visible=True)
                    ax.set_title('Chance to Loot One or More')
                    if 'crate:'.casefold() in values['shipsdropdown'].casefold():
                        ax.set_xlabel("Crates")
                        lootLookupWindow['tokenskillstext'].update('Crates Opened:',visible=True)
                    elif 'reward:'.casefold() in values['shipsdropdown'].casefold():
                        ax.set_xlabel("Runs")
                        lootLookupWindow['tokenskillstext'].update('Run Count:',visible=True)
                    elif 'kash nunes'.casefold() in values['shipsdropdown'].casefold():
                        tokenMult = int(values['relevelselect']) * 5 + 50
                        x = [k * tokenMult for k in x]
                        ax.set_xlabel("Tokens")
                        lootLookupWindow['tokenskillstext'].update('Tokens Spent:',visible=True)
                    else:
                        ax.set_xlabel("Kills")
                        lootLookupWindow['tokenskillstext'].update('Kill Count:',visible=True)
                    ax.set_ylabel("Probability of Success")
                    ax.grid()
                    ax2.set_title('Number of Parts at Least This Good')
                    ax2.set_xlabel('Count')
                    ax2.set_ylabel('Likelihood')
                    ax2.grid()
                    space = int(max(x)/10)
                    xticks = [0]
                    i = space
                    while i < max(x)+space:
                        if formatRarity(i) == '-':
                            xticks.append('∞')
                        else:
                            xticks.append(formatRarity(i)[5:])
                        i += space
                    if xticks[1] == '∞':
                        ax.cla()
                        ax.set_title('Chance to Loot One or More')
                        ax.set_xlabel("")
                        ax.set_ylabel("")
                        ax.set_ylim([0,1])
                        ax.grid()
                        fig_canvas_agg.draw()
                    else:
                        ax.set_xticks(np.arange(0,max(x)+space,space),xticks)
                        ax.set_yticks(np.arange(0,1.1,0.1),[str(round(x,1)) + '%' for x in np.arange(0,110,10)])
                        ax.set_ylim([0,1])
                        ax.plot(x,y,color='#00ffff')
                        ax.plot(x2,y2,color='#ffcc00',linestyle='dashed')
                        fig_canvas_agg.draw()
                    
                    if xalt == []:
                        ax2.cla()
                        ax2.set_title('Number of Parts at Least This Good')
                        ax2.set_xlabel("")
                        ax2.set_ylabel("")
                        ax2.set_ylim([0,1])
                        ax2.grid()
                        fig_canvas_agg.draw()
                    else:
                        if len(xalt) > 10:
                            sampleWidth = math.ceil(len(xalt)/10)
                            apexPoint = yalt.index(max(yalt))
                            print(np.arange(apexPoint-sampleWidth, 0, -sampleWidth)[::-1])
                            print(apexPoint)
                            print(np.arange(apexPoint + sampleWidth,len(xalt),sampleWidth))
                            sampleIndices = list(np.arange(apexPoint-sampleWidth, 0, -sampleWidth)[::-1]) + [apexPoint] + list(np.arange(apexPoint + sampleWidth,len(xalt),sampleWidth))
                            xticks2 = [xalt[x] for x in sampleIndices]
                        else:
                            xticks2 = xalt
                        ax2.set_xticks(xticks2,xticks2)
                        tickOrder = math.floor(math.log10(max(yalt))) #log10 and round down to get the order for the ticks
                        maxTick = round(math.pow(2,math.ceil(math.log2(max(yalt)))),-tickOrder) #log2 and ceil to get the highest tick, then round to the order
                        tickSize = math.pow(10,tickOrder)
                        ax2.set_yticks(np.arange(0,maxTick+tickSize,tickSize),[str(round(round(x,-tickOrder)*100,1)) + '%' for x in np.arange(0,maxTick+tickSize,tickSize)])
                        ax2.set_xlim([min(xalt),max(xalt)])
                        ax2.set_ylim([0,min(1,max(yalt)*1.25)])
                        ax2.plot(xalt,yalt,color='#00ffff')
                        ax2.scatter(xalt,yalt,color='#00ffff')
                        fig_canvas_agg.draw()
                else:
                    ax.cla()
                    ax.set_title('Chance to Loot One or More')
                    ax.set_xlabel("")
                    ax.set_ylabel("")
                    ax.set_ylim([0,1])
                    ax.grid()
                    fig_canvas_agg.draw()
                    ax2.cla()
                    ax2.set_title('Number of Parts at Least This Good')
                    ax2.set_xlabel("")
                    ax2.set_ylabel("")
                    ax2.set_ylim([0,1])
                    ax2.grid()
                    fig_canvas_agg.draw()
                    
                    lootLookupWindow['tokenskillstext'].update(visible=False)
                    lootLookupWindow['tokenskills'].update('',visible=False)
        except:
            pass

        if values['modeselect'] == 'Find Best Sources':
            if event in ['componentselect','relevelselect','inputstat']:
                lootLookupWindow['sourcestable'].update(values=[])
            elif values['componentselect'] not in ['Any',''] and values['relevelselect'] not in ['Any','']:
                try:
                    if event.endswith("+FOCUS OUT") or event == 'modeselect':
                        if values['inputstat'] != '' and values['inputvalue'] != '':
                            reMults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
                            reMult = reMults[int(values['relevelselect'])-1]
                            tails = [int(x) for x in cur.execute("SELECT stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0] if x!= '']
                            if values['componentselect'] != 'Armor':
                                tails = [1] + tails
                            tail = tails[compStats.index(values['inputstat'])]
                            reMult = 1 + tail * reMult
                            lootLookupWindow['posttext'].update('Post:',visible=True)
                            if values['inputstat'] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
                                post = str("{:.3f}".format(round(reMult*tryFloat(values['inputvalue']),2)))
                            elif values['inputstat'] == 'Recharge Rate' and values['componentselect'] == 'Shield':
                                post = str("{:.2f}".format(round(reMult*tryFloat(values['inputvalue']),2)))
                            else:
                                post = str("{:.1f}".format(round(reMult*tryFloat(values['inputvalue']),1)))
                            lootLookupWindow['postvalue'].update(post,visible=True)

                            event, values = lootLookupWindow.read(timeout=0)

                            shipsTable = calculateBestSources(lootLookupWindow)
                            entry = values['shipsdropdown']
                            if entry != '' and any([entry.casefold() in x[0].casefold() for x in shipsTable]):
                                displayedRows = [x for x in shipsTable if entry.casefold() in x[0].casefold()]
                                filteredValues = [x[0] for x in displayedRows]
                                filteredValues.sort()
                                lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
                            else:
                                displayedRows = shipsTable
                                filteredValues = [x[0] for x in shipsTable]
                                filteredValues.sort()
                                lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
                            lootLookupWindow['brandtable'].update(visible=False)
                            lootLookupWindow['sourcestable'].update(values=displayedRows, visible=True)
                except:
                    pass

        if values['modeselect'] == 'View Drop Rate Charts':
            try:
                if event.endswith("+FOCUS OUT"):
                    if values['inputstat'] != '' and values['inputvalue'] != '':
                        reMults = [0.02,0.03,0.03,0.04,0.04,0.05,0.05,0.06,0.07,0.07]
                        reMult = reMults[int(values['relevelselect'])-1]
                        tails = [int(x) for x in cur.execute("SELECT stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re FROM component WHERE type = ?", [values['componentselect']]).fetchall()[0] if x!= '']
                        if values['componentselect'] != 'Armor':
                            tails = [1] + tails
                        tail = tails[compStats.index(values['inputstat'])]
                        reMult = 1 + tail * reMult
                        lootLookupWindow['posttext'].update('Post:',visible=True)
                        if values['inputstat'] in ['Vs. Shields', 'Vs. Armor', 'Refire Rate']:
                            post = str("{:.3f}".format(round(reMult*tryFloat(values['inputvalue']),2)))
                        elif values['inputstat'] == 'Recharge Rate' and values['componentselect'] == 'Shield':
                            post = str("{:.2f}".format(round(reMult*tryFloat(values['inputvalue']),2)))
                        else:
                            post = str("{:.1f}".format(round(reMult*tryFloat(values['inputvalue']),1)))
                        lootLookupWindow['postvalue'].update(post,visible=True)

                if event == 'shipsdropdown':
                        if not any([values['componentselect'] in ['', 'Any'],values['relevelselect'] in ['', 'Any'],values['inputstat'] in ['', 'Any'],values['inputvalue'] in ['', 'Any']]):
                            shipsTable = calculateBestSources(lootLookupWindow)
                            event, values = lootLookupWindow.read(timeout=0)
                            entry = values['shipsdropdown']
                            if entry != '' and any([entry.casefold() in x[0].casefold() for x in shipsTable]):
                                displayedRows = [x for x in shipsTable if entry.casefold() in x[0].casefold()]
                                filteredValues = [x[0] for x in displayedRows]
                                filteredValues.sort()
                                lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
                            else:
                                displayedRows = shipsTable
                                filteredValues = [x[0] for x in shipsTable]
                                filteredValues.sort()
                                lootLookupWindow['shipsdropdown'].update(value=entry,values=filteredValues)
            except:
                pass
                
        if event == 'sourcestable':
            try:
                if values['inputstat'] != '' and values['inputvalue'] != 0:
                    selectedRow = displayedRows[values['sourcestable'][0]]
                    selection = displayedRows[values['sourcestable'][0]][0]
                    shipsTable, selectionTable = calculateBestSources(lootLookupWindow, selection)
                    dropCount = rates[shipids.index(selectedRow[0].split(' [')[1].split(']')[0])]
                    if dropCount%1 == 0:
                        dropCount = str(int(dropCount))
                    else:
                        dropCount = str(dropCount)
                    lootLookupWindow['brandlistcol1header2'].update(selection)
                    lootLookupWindow['brandlistcol2header2'].update(dropCount)
                    lootLookupWindow['brandlistcol3header2'].update(selectedRow[1])
                    while len(selectionTable) < 17:
                        print('pop')
                        selectionTable.append(['','','','','#ffffff','#ffffff','#ffffff'])
                    print(len(selectionTable))
                    for i in range(0,len(selectionTable)):
                        lootLookupWindow['brandlistcol1aline' + str(i)].update(selectionTable[i][0])
                        lootLookupWindow['brandlistcol1bline' + str(i)].update(selectionTable[i][1],text_color=selectionTable[i][4])
                        lootLookupWindow['brandlistcol2line' + str(i)].update(selectionTable[i][2],text_color=selectionTable[i][5])
                        lootLookupWindow['brandlistcol3line' + str(i)].update(selectionTable[i][3],text_color=selectionTable[i][6])
                    lootLookupWindow['brandtable'].update(visible=True)
            except:
                pass

        if isinstance(event, tuple):
            if event[0] == 'loottable':
                if event[2][0] == -1 and event[2][1] != -1:
                    sortColumn = event[2][1]
                    if sortColumn == 0:
                        if sortFlag == -1 or sortFlag != sortColumn:
                            tableValues = sorted(tableValues, key=operator.itemgetter(1))
                            tableValues = sorted(tableValues, key=operator.itemgetter(2),reverse=True)
                            tableValues = sorted(tableValues, key=operator.itemgetter(0))
                            sortFlag = sortColumn
                        else:
                            tableValues = sorted(tableValues, key=operator.itemgetter(1))
                            tableValues = tableSortByDroprate(tableValues,True)
                            tableValues = sorted(tableValues, key=operator.itemgetter(0),reverse=True)
                            sortFlag = -1
                    elif sortColumn == 1:
                        if sortFlag == -1 or sortFlag != sortColumn:
                            tableValues = sorted(tableValues, key=operator.itemgetter(0))
                            tableValues = tableSortByDroprate(tableValues,True)
                            tableValues = sorted(tableValues, key=operator.itemgetter(1))
                            sortFlag = sortColumn
                        else:
                            tableValues = sorted(tableValues, key=operator.itemgetter(0))
                            tableValues = tableSortByDroprate(tableValues,True)
                            sortFlag = -1
                    elif sortColumn == 2:
                        if sortFlag == -1 or sortFlag != sortColumn:
                            tableValues = sorted(tableValues, key=operator.itemgetter(0,1))
                            tableValues = tableSortByDroprate(tableValues,True)
                            sortFlag = sortColumn
                        else:
                            tableValues = sorted(tableValues, key=operator.itemgetter(0,1))
                            tableValues = tableSortByDroprate(tableValues,False)
                            sortFlag = -1

                    lootLookupWindow['loottable'].update(values = tableValues)
            elif event[0] == 'sourcestable':
                if event[2][0] == -1 and event[2][1] != -1:
                    sortColumn = event[2][1]
                    if sortColumn == 0:
                        if sortFlag == -1 or sortFlag != sortColumn:
                            shipsTable = tableSortByOdds(shipsTable,False)
                            shipsTable = sorted(shipsTable, key=operator.itemgetter(0))
                            sortFlag = sortColumn
                        else:
                            shipsTable = tableSortByOdds(shipsTable,True)
                            shipsTable = sorted(shipsTable, key=operator.itemgetter(0),reverse=True)
                            sortFlag = -1
                    if sortColumn == 1:
                        if sortFlag == -1 or sortFlag != sortColumn:
                            shipsTable = sorted(shipsTable, key=operator.itemgetter(0))
                            shipsTable = tableSortByOdds(shipsTable,False)
                            sortFlag = sortColumn
                        else:
                            shipsTable = sorted(shipsTable, key=operator.itemgetter(0))
                            shipsTable = tableSortByOdds(shipsTable,True)
                            sortFlag = -1
                    
                    lootLookupWindow['sourcestable'].update(values = shipsTable)

        if event == sg.WIN_CLOSED:
            break

        oldMode = values['modeselect'] #sets the current mode after each event loop for the purposes of only triggering mode change events when the mode actually changes

    lootLookupWindow.close()
    data.close()

#lootLookup()