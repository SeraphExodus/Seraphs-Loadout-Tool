import FreeSimpleGUI as sg
import json
import os
import sqlite3

from csv import reader as csvreader

def tryInt(x):
    try:
        if x%0 > 0:
            return x
        else:
            return int(x)
    except:
        return x
        
def tryFloat(x):
    try:
        return float(x)
    except:
        return x

### Need to create a function to locate existing savedata.dbs to feed into the json converter.

def savedataToJSON():
    """Convert old sqlite3 savedata.db file to JSON format.
    A new JSON file will be created in the appdata directory,
    but the old .db will not be deleted.""" 

    dir = os.getenv("APPDATA") + "\\Seraph's Loadout Tool"

    file = "file:" + dir + "\\savedata.db?mode=rw"

    compdb = sqlite3.connect(file,uri=True)
    cur = compdb.cursor()

    tables = [x[0] for x in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    data = []

    for table in tables:
        columnNames = [x[0] for x in cur.execute("SELECT * FROM "+table).description]
        tableData = [x for x in cur.execute("SELECT * FROM "+table).fetchall()]
        tableList = []
        for entry in tableData:
            entryDict = {x:y for (x,y) in zip(columnNames,entry)}
            tableList.append(entryDict)
        data.append({table:tableList})

    with open(dir + '\\savedata.json','w') as f:
        json.dump(data, f)

def dataToJSON(path, headers, entryLengths, dataTypes):

    with open(path, newline='') as csvfile:
        reader = csvreader(csvfile)

        rawData = [x for x in reader]

        data = []

        for x in rawData:
            entry = {}
            indexCounter = 0
            for y in range(len(headers)):
                e = entryLengths[y]
                t = dataTypes[y]
                if e == 1:
                    if t == 'i':
                        entry.update({headers[y]: tryInt(x[indexCounter:indexCounter+e][0])})
                    elif t == 'f':
                        entry.update({headers[y]: tryFloat(x[indexCounter:indexCounter+e][0])})
                    else:
                        entry.update({headers[y]: x[indexCounter:indexCounter+e][0]})
                else:  
                    if t == 'i':
                        entry.update({headers[y]: [tryInt(a) for a in x[indexCounter:indexCounter+e] if a != '']})
                    elif t == 'f':
                        entry.update({headers[y]: [tryFloat(a) for a in x[indexCounter:indexCounter+e] if a != '']})
                    else:
                        entry.update({headers[y]: [a for a in x[indexCounter:indexCounter+e] if a != '']})
                indexCounter += e
            data.append(entry)

    return data

def buildTablesJSON():

    dir = os.path.join(os.path.dirname(__file__)) + '\\'

    compiledData = {}

    with open(os.path.abspath(dir + 'jsonConfig.csv')) as config:
        headers = []
        entryLengths = []
        config = [x for x in csvreader(config)]

        for c in config:
            filepath = c[0]
            headerCount = int(c[1])
            headers = c[2:headerCount+2]
            entryLengths = [int(x) for x in c[headerCount+2:2*headerCount+2] if x != '']
            dataTypes = c[2*headerCount+2:]
            compiledData.update({filepath[:-4]: dataToJSON(os.path.abspath(dir + filepath),headers,entryLengths,dataTypes)})

    with open('data.json', 'w') as f:
        json.dump(compiledData, f)