import os
import sqlite3

from csv import reader as csvreader

import datetime

def buildList(path):
    with open(path, newline='') as csvfile:
        reader = csvreader(csvfile)

        output = []
        newRow = tuple()

        for row in reader:
            newRow = tuple(row)
            output.append(newRow)
        return output
    
def buildTables(currentVersion):

    if not os.path.exists("Data"):
        os.makedirs("Data")

    if not os.path.exists("Data\\tables.db"):
        open("Data\\tables.db", 'w')
    else:
        data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
        cur = data.cursor()
        try:
            tableVersion = cur.execute("SELECT versionid FROM version").fetchall()[0][0]
            data.close()
            if tableVersion == currentVersion and currentVersion != 'null':
                return
            elif currentVersion == 'null':
                currentVersion = tableVersion
        except:
            data.close()
        os.remove("Data\\tables.db")
        open("Data\\tables.db", 'w')

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    cur.execute("CREATE TABLE version(versionid)")
    cur.execute("INSERT INTO version VALUES(?)",[currentVersion])

    cur.execute("CREATE TABLE component(type, stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8, stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re, stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp)")
    componentStats = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'componentStats.csv')))
    cur.executemany("INSERT INTO component VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", componentStats)

    cur.execute("CREATE TABLE fcprogram(command, name, size, target, delay, energyefficiency, genefficiency, compdamage, fronttobackreinf, backtofrontreinf, capreinfpercent, frontshieldratio, desc1, desc2, desc3, desc4)")
    fcPrograms = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'fcprograms.csv')))
    cur.executemany("INSERT INTO fcprogram VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcPrograms)

    cur.execute("CREATE TABLE chassis(name, mass, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, accel, decel, pitchaccel, yawaccel, rollaccel, speedmod, speedfoils, minthrottle, optthrottle, maxthrottle, slide)")
    chassisList = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chassis.csv')))
    cur.executemany("INSERT INTO chassis VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", chassisList)

    cur.execute("CREATE TABLE brands(path, name, relevel, weight, stat1mean, stat1mod, stat2mean, stat2mod, stat3mean, stat3mod, stat4mean, stat4mod, stat5mean, stat5mod, stat6mean, stat6mod, stat7mean, stat7mod, stat8mean, stat8mod, stat9mean, stat9mod)")
    brands = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'brandslist.csv')))
    cur.executemany("INSERT INTO brands VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", brands)

    cur.execute("CREATE TABLE ordnance(type, multiplier, shieldeff, armoreff, minmass, maxmass, minmax, maxmax)")
    launchers = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'ordnance.csv')))
    cur.executemany("INSERT INTO ordnance VALUES(?, ?, ?, ?, ?, ?, ?, ?)", launchers)

    cur.execute("CREATE TABLE npcships(type, string, lootrolls, droprate, lootgroup, shiptype)")
    npcShips = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'shipTable.csv')))
    cur.executemany("INSERT INTO npcships VALUES(?, ?, ?, ?, ?, ?)", npcShips)

    cur.execute("CREATE TABLE lootgroups(lootgroup, table1, table2, table3, table4, table5, table6)")
    lootGroups = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lootGroups.csv')))
    cur.executemany("INSERT INTO lootgroups VALUES(?, ?, ?, ?, ?, ?, ?)", lootGroups)

    bindString = 'name, chassishp, reactorhp, reactorarmor, enginehp, enginearmor, shield0fronthp, shield0backhp, shield1fronthp, shield1backhp, armorfronthp, armorbackhp, capacitorhp, capacitorarmor, boosterhp, boosterarmor, dihp, diarmor, bridgehp, bridgearmor, hangarhp, hangararmor, targetinghp, targetingarmor, '
    for i in range(0,8):
        bindString += 'weapon' + str(i) + 'type, '
        bindString += 'weapon' + str(i) + 'hp, '
        bindString += 'weapon' + str(i) + 'armor, '
        bindString += 'weapon' + str(i) + 'refire, '
        bindString += 'weapon' + str(i) + 'mindam, '
        bindString += 'weapon' + str(i) + 'maxdam, '
        bindString += 'weapon' + str(i) + 'vss, '
        bindString += 'weapon' + str(i) + 'vsa, '
        bindString += 'weapon' + str(i) + 'ammo, '

    bindings = bindString.count(',') * '?, '
    bindings = bindings[:-2]
    bindString = bindString[:-2]

    cur.execute("CREATE TABLE shiptypes(" + bindString + ")")
    shipTypes = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'shipTypes.csv')))
    cur.executemany("INSERT INTO shiptypes VALUES(" + bindings + ")",shipTypes)

    lootTables = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'lootTables.csv')))
    tempids = []
    tempLoot = []
    for i in lootTables:
        tempids.append(i[0])
        tempLoot.append(i[1:])
    length = len(lootTables[-1])
    temp = lootTables
    lootTables = []
    for k in temp:
        lootTables.append(tuple(list(k) + [''] * (length-len(k))))
    createString = 'CREATE TABLE loottables(loottable, '
    for i in range(1,len(lootTables[-1])):
        createString += 'item' + str(i) + ', '
    createString = createString[:-2] + ')'
    cur.execute(createString)
    bindingString = len(lootTables[-1]) * '?, '
    executeString = 'INSERT INTO loottables VALUES(' + bindingString[:-2] + ')'
    cur.executemany(executeString, lootTables)

    data.commit()
    data.close()
    print('Tables Built Successfully!')

#buildTables('null')