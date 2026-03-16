import json
import os
import sqlite3

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