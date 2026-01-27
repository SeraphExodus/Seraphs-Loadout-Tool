import os
import sqlite3

def buildComponentList(dataDir):

    dataPath = dataDir + '\\savedata.db'

    if not os.path.exists(dataDir):
        os.makedirs(dataDir)
    if not os.path.exists(dataPath):
        open(dataPath, 'w')
        print('savedata.db not found. A new one was created.')
    else:
        print('savedata.db already exists. Cancelling operation.')
        return

    tables = sqlite3.connect('file:tables.db?mode=ro', uri=True)
    cur1 = tables.cursor()

    compdb = sqlite3.connect('file:' + dataDir + "\\savedata.db?mode=rw", uri=True)  
    cur2 = compdb.cursor()

    raw = cur1.execute("SELECT * FROM component").fetchall()
    statsList = []
    newRow = ""
    headers = ""
    headerList = []

    for i in range(0, len(raw)):
        newRow = ""
        for j in range(0, len(raw[i])):
            if raw[i][j] == "" or len(raw[i][j].lower().replace(" ", "").replace("/", "").replace(".", "")) <= 2 or raw[i][j][-1] == ":":
                pass
            elif j > 0:
                newRow += raw[i][j].lower().replace(" ", "").replace("/", "").replace(".", "") + ", "
            if j == 0:
                headers += raw[i][j].lower().replace(" ", "").replace("/", "").replace(".", "") + ", "
                headerList.append(raw[i][j].lower().replace(" ", "").replace("/", "").replace(".", ""))
        statsList.append("name UNIQUE, " + newRow[:-2])

    headers = headers[:-2]

    loadoutHeaders = "name UNIQUE, chassis, mass, armor1, armor2, booster, capacitor, cargohold, droidinterface, engine, reactor, shield, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, pack1, pack2, pack3, pack4, pack5, pack6, pack7, pack8, rolevel, eolevel, colevel, wolevel, adjust"

    cur2.execute("CREATE TABLE loadout(" + loadoutHeaders + ")")

    for i in range(0, len(statsList)):
        cur2.execute("CREATE TABLE " + headerList[i] + "(" + statsList[i] + ")")
    compdb.commit()
    compdb.close()