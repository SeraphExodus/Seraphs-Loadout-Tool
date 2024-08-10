import FreeSimpleGUI as sg
import os
import sqlite3

from buildCompList import buildComponentList
from buildTables import buildTables

headerFont = ("Roboto", 14, "bold")
baseFont = ("Roboto", 10, "bold")
baseFont_large = ("Roboto", 12, "bold")
buttonFont = ("Roboto", 12, "bold")
fontPadding = 0
elementPadding = 4
bgColor = "#202225"
boxColor = "#2f3136"
textColor = '#e4f2ff'

def doError(errorText):
    errorLayout = [
        [sg.Push(), sg.Text(errorText, font=baseFont_large), sg.Push()],
        [sg.Push(), sg.Button('Okay', font=baseFont_large), sg.Push()]
    ]

    errorWindow = sg.Window('Error', errorLayout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = errorWindow.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Okay':
            break

    errorWindow.close()

def doOverwrite(text):

    Layout = [
        [sg.Push(), sg.Text(text, font=baseFont_large), sg.Push()],
        [sg.Push(), sg.Button('Proceed', font=baseFont_large), sg.Button('Cancel', font=baseFont_large), sg.Push()]
    ]

    window = sg.Window('Overwrite?', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED or not event == "":
            window.close()
            return event
            
def ordnanceCheck(stats, compName):
    if compName == "Ordnance Launcher":
        if stats[2] == '':
            return False
        else:
            return True
    elif compName == "Ordnance Pack":
        if stats[3] == '':
            return False
        else:
            return True
    else:
        return True

def createComponent(componentName, *editArgs):
    sg.theme('Discord_Dark')

    if not os.path.exists("Data\\tables.db"):
        buildTables('null')

    if not os.path.exists("Data\\savedata.db"):
        buildComponentList()

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    lookup = cur.execute("SELECT * FROM component WHERE type = '" + componentName + "'").fetchall()[0]
    statColumn = []
    inputColumn = []

    try:   
        editArgs = editArgs[0]
        editingName = editArgs[0]
        editing = True  
    except:
        editing = False
        editingName = ''
        editArgs = [""] * 9

    for i in range(1, 9):
        if lookup[i] != '':
            statColumn.append([sg.Push(), sg.Text(lookup[i] + ":", font=baseFont)])
            if lookup[i] == "Type":
                ordnance = cur.execute("SELECT * FROM ordnance").fetchall()
                types = []
                for j in ordnance:
                    types.append(j[0])
                inputColumn.append([sg.Combo(values = types, s=(25,14), key="stat" + str(i), font=baseFont, readonly=True, default_value=editArgs[i])])
            else:
                inputColumn.append([sg.Input(s = 10, key="stat" + str(i), font=baseFont, default_text=editArgs[i])])

    statColumn.insert(0,[sg.Push(), sg.Text('Component Name:', font=baseFont)])

    inputColumn.insert(0,[sg.Input(key='name', font=baseFont, s=25, default_text=editArgs[0], disabled_readonly_background_color=boxColor)])

    if editing:
        statColumn.insert(0,[sg.Push(),sg.Text('Editing Component:',font=baseFont)])
        inputColumn.insert(0,[sg.Text(editingName,font=baseFont),sg.Push()])
        

    layout = [
        [sg.Push(),sg.Text('Input Component Stats', font=headerFont),sg.Push()],
        [sg.Push(),sg.Text(componentName,font=baseFont),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',statColumn,border_width=0,s=(200,275)), sg.Frame('',inputColumn,border_width=0,s=(200,275))],
        [sg.VPush()],
        [sg.Push(),sg.Button("Save", font=buttonFont, bind_return_key=True), sg.Button("Cancel", font=buttonFont),sg.Push()]
    ]

    window = sg.Window('Create Component',layout, modal=True, finalize=True, size=(450,450), icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    window['name'].set_focus()
    window.bind('<Escape>', 'Cancel')

    compUpdate = False

    while True:
        event, values = window.read()

        if event == "Save":
            stats = []
            for i in range(1, 9):
                try:
                    stats.append(float(values['stat' + str(i)]))
                except:
                    try:
                        stats.append(values['stat' + str(i)])
                    except:
                        pass

            statsReduced = [x for x in stats if x != '' and x != 0]

            try:
                weaponList = cur2.execute("SELECT name FROM weapon").fetchall()[0]
            except:
                weaponList = []
            try:
                ordList = cur2.execute("SELECT name FROM ordnancelauncher").fetchall()[0]
            except:
                ordList = []
            try:
                cmList = cur2.execute("SELECT name FROM countermeasurelauncher").fetchall()[0]
            except:
                cmList = []


            if values['name'] == "":
                doError("Error: You must enter a name for this component.")
            elif componentName == "Weapon" and (values['name'] in ordList or values['name'] in cmList):
                doError("Error: This name is already in use for an ordnance launcher or countermeasure launcher. Please use a different name.")
            elif componentName == "Ordnance Launcher" and (values['name'] in weaponList or values['name'] in cmList):
                doError("Error: This name is already in use for a weapon or countermeasure launcher. Please use a different name.")
            elif componentName == "Countermeasure Launcher" and (values['name'] in weaponList or values['name'] in ordList):
                doError("Error: This name is already in use for a weapon or ordnance launcher. Please use a different name.")
            elif ordnanceCheck(stats, componentName) == False:
                doError("Error: You must select an ordnance type.")
            elif len(statsReduced) < len(inputColumn)-2:
                doError("Error: You must enter a non-zero numerical value for every stat.")
            else:
                bindings = ""
                stats.insert(0, values['name'])
                statString = ""
                for i in range(0, len(stats)):
                    bindings += "?, "
                    if i > 0:
                        statString += lookup[i].lower().replace(" ","").replace("/","").replace(".","") + ", "
                bindings = bindings[:-2]
                statString = "name, " + statString[:-2]
                compName = componentName.lower().replace(" ","").replace("/","").replace(".","")

                if editing:
                    decision = doOverwrite("You are about to overwrite your part with the new stats entered below. Do you wish to continue?")
                    window.TKroot.grab_set()
                    if decision == "Proceed":
                        decision2 = "Proceed"
                        sameName = cur2.execute('SELECT * FROM ' + compName + ' WHERE name = ?', [stats[0]]).fetchall()
                        if sameName != [] and stats[0] != editArgs[0]:
                            decision2 = doOverwrite("A part with this name already exists. Do you wish to overwrite it?")
                            window.TKroot.grab_set()
                        if decision == "Proceed" and decision2 == "Proceed":
                            cur2.execute("DELETE FROM " + compName + " WHERE name = ?", [editArgs[0]])
                            cur2.execute("INSERT OR REPLACE INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                            compUpdate = True
                            break
                else:
                    try:
                        cur2.execute("INSERT INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                        compUpdate = True
                        break
                    except:
                        decision = doOverwrite("A part with this name already exists. Do you wish to overwrite it?")
                        window.TKroot.grab_set()
                        if decision == "Proceed":
                            cur2.execute("INSERT OR REPLACE INTO " + compName + "(" + statString + ") VALUES(" + bindings + ")", stats)
                            compUpdate = True
                            break

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            window.close()
            try:
                editArgs[0]
            except:
                pass
            break

    compdb.commit()
    compdb.close()
    db.close()
    window.close()
    return compUpdate
