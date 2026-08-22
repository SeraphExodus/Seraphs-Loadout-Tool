import json
import os
import sqlite3
import sys

def buildComponentList(dataDir):

    dataPath = dataDir + '\\savedata.db'

    emptyCheck = True

    if not os.path.exists(dataDir):
        os.makedirs(dataDir)
    if not os.path.exists(dataPath):
        open(dataPath, 'w')
        print('savedata.db not found. A new one was created.')
    else:
        print('savedata.db already exists. Cancelling operation.')
        return

    dataDir = os.getenv('APPDATA') + "\\Seraph's Loadout Tool"

    try:
        with open(os.getenv('APPDATA') + "\\Seraph's Loadout Tool\\data.json", 'r') as f:
            tables = json.load(f)
    except:
        print('An error occurred. Table data could not be located.')
        sys.exit()

    compdb = sqlite3.connect('file:' + dataDir + "\\savedata.db?mode=rw", uri=True)  
    cur2 = compdb.cursor()

    raw = tables['componentstats']
    statsList = []
    newRow = ""
    headers = ""
    headerList = []

    for i in raw:
        newRow = ""
        for j in i['stat']:
            newRow += j.lower().replace(" ", "").replace("/", "").replace(".", "") + ", "
        headerList.append(i['comptype'].lower().replace(" ", "").replace("/", "").replace(".", ""))
        statsList.append("name UNIQUE, " + newRow[:-2])

    headers = headers[:-2]

    loadoutHeaders = "name UNIQUE, chassis, mass, armor1, armor2, booster, capacitor, cargohold, droidinterface, engine, reactor, shield, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, pack1, pack2, pack3, pack4, pack5, pack6, pack7, pack8, rolevel, eolevel, colevel, wolevel, adjust"

    cur2.execute("CREATE TABLE loadout(" + loadoutHeaders + ")")

    for i in range(0, len(statsList)):
        cur2.execute("CREATE TABLE " + headerList[i] + "(" + statsList[i] + ")")
        
    compdb.commit()
    compdb.close()