import FreeSimpleGUI as sg
import sqlite3
import os
from buildTables import buildTables
from buildCompList import buildComponentList

headerFont = ("Roboto", 13, "bold")
baseFont = ("Roboto", 11, "bold")
buttonFont = ("Roboto", 13, "bold")
fontPadding = 0
elementPadding = 5
bgColor = "#202225"
boxColor = "#2f3136"
textColor = '#e4f2ff'

def isFloat(x):
    try:
        float(x)
        return True
    except:
        return False

def doError(errorText):
    sg.theme('Discord_Dark')
    errorLayout = [
        [sg.Push(), sg.Text(errorText, font=headerFont), sg.Push()],
        [sg.Push(), sg.Button('Okay', font=buttonFont), sg.Push()]
    ]

    errorWindow = sg.Window('Error', errorLayout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = errorWindow.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Okay':
            break

    errorWindow.close()

def doOverwrite():
    sg.theme('Discord_Dark')
    Layout = [
        [sg.Push(), sg.Text("A loadout with this name already exists. Do you wish to overwrite it?", font=baseFont), sg.Push()],
        [sg.Push(), sg.Button('Proceed', font=buttonFont), sg.Button('Cancel', font=buttonFont), sg.Push()]
    ]

    window = sg.Window('Overwrite?', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = window.read()
        if event == "Exit" or event == sg.WIN_CLOSED or not event == "":
            window.close()
            return event

def createLoadout():
    sg.theme('Discord_Dark')
    if not os.path.exists("Data\\tables.db"):
        buildTables()

    if not os.path.exists("Data\\savedata.db"):
        buildComponentList()

    tables = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = tables.cursor()
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    chassisRaw= cur.execute("SELECT name FROM chassis").fetchall()
    massRaw = cur.execute("SELECT mass FROM chassis").fetchall()
    chassisList = []
    massList = []

    for i in range(0, len(chassisRaw)):
        chassisList.append(chassisRaw[i][0])
        massList.append(massRaw[i][0])

    textColumn = [
        [sg.Push(), sg.Text("Loadout Name:", font=baseFont)],
        [sg.Push(), sg.Text("Select Chassis:", font=baseFont)],
        [sg.Push(), sg.Text("Chassis Mass:", font=baseFont)],
    ]

    inputColumn = [
        [sg.Input("", font=baseFont, key='name', s=26)],
        [sg.Combo(chassisList, default_value="Select Chassis", font=baseFont, key='chassis', s=24, enable_events=True, readonly=True)],
        [sg.Input("", font=baseFont, key='mass', s=11), sg.Text("", key='maxmass', font=baseFont), sg.Push()],
    ]

    layout = [
        [sg.Push(), sg.Text("Create New Loadout", font=headerFont), sg.Push()],
        [sg.Text("",font=baseFont,p=fontPadding)],
        [sg.Column(textColumn), sg.Column(inputColumn)],
        [sg.Text("",font=baseFont,p=fontPadding)],
        [sg.Push(),sg.Push(),sg.Button("Save", font=buttonFont, bind_return_key=True), sg.Push(), sg.Button("Cancel", font=buttonFont),sg.Push(),sg.Push()]
    ]

    window = sg.Window('Create Loadout',layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    window['name'].set_focus()
    window.bind('<Escape>', 'Cancel')

    valueList = ['', '', '']

    while True:
        event, values = window.read()
        if event == 'chassis':
            if not values['chassis'] == "":
                maxMass = massList[chassisList.index(values['chassis'])]
                window['maxmass'].update("Max: " + "{:,.0f}".format(float(maxMass)))
        if event == 'Save':
            valueList = [values['name'], values['chassis'], values['mass']]
            if valueList[0] == "":
                doError("Error: You must enter a name for this loadout.")
            elif valueList[1] == "Select Chassis" or valueList[1] == "":
                doError("Error: You must select a chassis.")
            elif not isFloat(valueList[2]):
                doError("Error: You must enter a numerical value for chassis mass.")
            else:
                valueList += ['None'] * 30
                try:
                    cur2.execute("INSERT INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",valueList)
                    break
                except:
                    decision = doOverwrite()
                    if decision == "Proceed":
                        cur2.execute("INSERT OR REPLACE INTO loadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",valueList)
                        break
                    else:
                        pass

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Cancel':
            break

    window.close()
    compdb.commit()
    compdb.close()
    tables.close()

    return valueList[0:3]


