import math
import sqlite3

def tryFloat(x):
    try:
        return float(x)
    except:
        return 0
    
def normalCDF(Z):
    try:
        y = 0.5 * (1 + math.erf(Z/math.sqrt(2)))
        return y
    except:
        SyntaxError

def getRarity(value, statIndex, tail, reLevel):
    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()
    
    compList = cur.execute("SELECT * FROM brands WHERE relevel = ?", [reLevel]).fetchall()
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
    
    weights = [float(x[3]) for x in compList]
    total = sum(weights)
    weights = [x/total for x in weights]
    totalRarity = 0
    for i in range(0,len(rarity)):
        totalRarity += rarity[i] * weights[i]
    data.close()
    return totalRarity

def showRewardParts():
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

    compStats = [list(x[0:]) for x in cur.execute("SELECT type, stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8 from component").fetchall()]
    tails = [list(x[0:]) for x in cur.execute("SELECT type, stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re from component").fetchall()]
    for i in range(0,len(compStats)):
        if compStats[i][1] != 'Armor/Hitpoints':
            compStats[i].insert(1,'Armor/Hitpoints')
            tails[i].insert(1,'1')
        else:
            compStats[i].append('')
            tails[i].append('')

        if compStats[i][0] == 'Shield':
            compStats[i][4] = 'Front Shield Hitpoints'
            compStats[i].insert(5,'Back Shield Hitpoints')
            tails[i].insert(5,1)
            tails[i].remove('')
            compStats[i].remove('')

    rewardBrands = []

    for i in brands:
        if any([0.0001 in i[3:], '0.0001' in i[3:]]):
            newLine = [i[1],i[2]]
            for j in range(0,9):
                mean = tryFloat(i[4 + 2*j])
                if mean != 0:
                    mod = tryFloat(i[5 + 2*j])
                    if mod < 0.001:
                        stdev = mean*mod/2
                        level = i[2]
                        for k in compStats:
                            if level[0] == k[0][0]:
                                componentType = k[0]
                                statList = [x for x in k[1:] if x != '']
                                break
                        for k in tails:
                            if k[0] == componentType:
                                typeTails = k
                        tail = int(typeTails[j+1])
                        statExtreme = mean + stdev * tail * 6
                        rarity = getRarity(statExtreme,j,tail,level)
                        if tail == 1:
                            low = round(mean - 6 * stdev,3)
                            high = round(mean + 6 * stdev,3)
                        else:
                            low = round(mean + 6 * stdev,3)
                            high = round(mean - 6 * stdev,3)
                        if rarity < 0.01:
                            newLine.append(statList[j] + ': ' + str(mean) + ' (' + str(low) + ' - ' + str(high) + ')')
            if newLine[2:] != []:
                rewardBrands.append(newLine)

    for x in rewardBrands:
        lineOut = '{:<4}'.format(str(x[1])) + '{:<60}'.format(str(x[0]))
        for y in x[2:]:
            lineOut += '{:<80}'.format(str(y))
        print(lineOut)
    data.close()
showRewardParts()