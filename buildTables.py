import os
import sqlite3
import csv
import sys

def isFloat(n):
    try:
        float(n)
        return True
    except:
        return False

def buildList(path):
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)

        output = []
        newRow = tuple()

        for row in reader:
            newRow = tuple(row)
            output.append(newRow)
        return output
    
def buildTables():

    if not os.path.exists("Data"):
        os.makedirs("Data")
    if not os.path.exists("Data\\tables.db"):
        open("Data\\tables.db", 'w')
    else:
        os.remove("Data\\tables.db")
        open("Data\\tables.db", 'w')

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    #Build component stats table
    cur.execute("CREATE TABLE component(type, stat1, stat2, stat3, stat4, stat5, stat6, stat7, stat8, stat1re, stat2re, stat3re, stat4re, stat5re, stat6re, stat7re, stat8re, stat1disp, stat2disp, stat3disp, stat4disp, stat5disp, stat6disp, stat7disp, stat8disp)")
    componentStats = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'componentStats.csv')))
    cur.executemany("INSERT INTO component VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", componentStats)

    cur.execute("CREATE TABLE fcprogram(command, name, size, target, delay, energyefficiency, genefficiency, compdamage, fronttobackreinf, backtofrontreinf, capreinfpercent, frontshieldratio)")
    fcPrograms = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'fcprograms.csv')))
    cur.executemany("INSERT INTO fcprogram VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", fcPrograms)

    cur.execute("CREATE TABLE chassis(name, mass, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, accel, decel, pitchaccel, yawaccel, rollaccel, speedmod, speedfoils, minthrottle, optthrottle, maxthrottle, slide)")
    chassisList = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'chassis.csv')))
    cur.executemany("INSERT INTO chassis VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", chassisList)

    cur.execute("CREATE TABLE brands(path, name, relevel, stat1mean, stat1mod, stat2mean, stat2mod, stat3mean, stat3mod, stat4mean, stat4mod, stat5mean, stat5mod, stat6mean, stat6mod, stat7mean, stat7mod, stat8mean, stat8mod, stat9mean, stat9mod)")
    brands = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'brandslist.csv')))
    cur.executemany("INSERT INTO brands VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", brands)

    cur.execute("CREATE TABLE ordnance(type, multiplier, shieldeff, armoreff)")
    launchers = buildList(os.path.abspath(os.path.join(os.path.dirname(__file__), 'ordnance.csv')))
    cur.executemany("INSERT INTO ordnance VALUES(?, ?, ?, ?)", launchers)

    data.commit()
    data.close()

buildTables()