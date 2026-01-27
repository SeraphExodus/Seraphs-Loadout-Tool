import FreeSimpleGUI as sg
import numpy as np
import os
import pyglet
import sqlite3

from pandas import read_excel

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
baseFont = ("Roboto", 10, "bold")
baseFontStats = ("Roboto", 10, "bold")
buttonFont = ("Roboto", 12, "bold")
fontPadding = 0
elementPadding = 4
bgColor = '#202225'
boxColor = '#313338'
textColor = '#f3f4f5'

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

global tables
global cur
global compdb
global cur2

tables = sqlite3.connect("file:tables.db?mode=ro", uri=True)
cur = tables.cursor()

compdb = sqlite3.connect("file:"+os.getenv("APPDATA")+"\\Seraph's Loadout Tool\\savedata.db?mode=rw", uri=True)
cur2 = compdb.cursor()

def listify(query):
    output = []
    for i in query:
        output.append(i[0])
    return output

def doAlert(alertText):
    alertLayout = [
        [sg.Push(), sg.Text(alertText, font=baseFont, justification='center'), sg.Push()],
        [sg.Push(), sg.Button('Okay', font=buttonFont, bind_return_key=True), sg.Push()]
    ]

    alertWindow = sg.Window('Alert', alertLayout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = alertWindow.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Okay':
            break

    alertWindow.close()

def doAlertYN(alertText):
    alertLayout = [
        [sg.Push(), sg.Text(alertText, font=baseFont, justification='center'), sg.Push()],
        [sg.Push(), sg.Button('Yes', font=baseFont), sg.Button('No', font=baseFont), sg.Push()]
    ]

    alertWindow = sg.Window('Alert', alertLayout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = alertWindow.read()
        if event == "Yes":
            output = "Yes"
            break

        if event == "Exit" or event == sg.WIN_CLOSED or event == 'No':
            output = "No"
            break

    alertWindow.close()
    return output

def tryStr(x):
    if (type(x) == np.float64 or type(x) == float) and np.isnan(x):
        return ''
    else:
        try:
            return str(x)
        except:
            return ''
    

def importBackup(filepath):

    data = read_excel(filepath, sheet_name=None, header=None)

    reactors = data['Reactors'].values.tolist()
    for i in reactors:
        entry = [tryStr(i[0]), i[15], i[19]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO reactor(name, mass, reactorgenerationrate) VALUES(?, ?, ?)",entry)
            
    engines = data['Engines'].values.tolist()
    for i in engines:
        entry = [tryStr(i[0]), i[15], i[19], i[23], i[27], i[31], i[35]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO engine(name, reactorenergydrain, mass, pitchratemaximum, yawratemaximum, rollratemaximum, enginetopspeed) VALUES(?, ?, ?, ?, ?, ?, ?)",entry)

    boosters = data['Boosters'].values.tolist()
    for i in boosters:
        entry = [tryStr(i[0]), i[15], i[19], i[23], i[27], i[31], i[35], i[39]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO booster(name, reactorenergydrain, mass, boosterenergy, boosterrechargerate, boosterenergyconsumptionrate, acceleration, topboosterspeed) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",entry)

    shields = data['Shields'].values.tolist()
    for i in shields:
        entry = [tryStr(i[0]), i[15], i[19], i[23], i[27]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO shield(name, reactorenergydrain, mass, shieldhitpoints, shieldrechargerate) VALUES(?, ?, ?, ?, ?)",entry)

    armor = data['Armor'].values.tolist()
    for i in armor:
        entry = [tryStr(i[0]), i[15], i[19]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO armor(name, armorhitpoints, mass) VALUES(?, ?, ?)",entry)

    dis = data['DIs'].values.tolist()
    for i in dis:
        entry = [tryStr(i[0]), i[15], i[19], i[23]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO droidinterface(name, reactorenergydrain, mass, droidcommandspeed) VALUES(?, ?, ?, ?)",entry)

    chs = data['Cargo Holds'].values.tolist()
    for i in chs:
        entry = [tryStr(i[0]), i[19]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO cargohold(name, mass) VALUES(?, ?)",entry)

    caps = data['Capacitors'].values.tolist()
    for i in caps:
        entry = [tryStr(i[0]), i[15], i[19], i[23], i[27]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO capacitor(name, reactorenergydrain, mass, capacitorenergy, rechargerate) VALUES(?, ?, ?, ?, ?)",entry)

    weapons = data['Weapons'].values.tolist()
    for i in weapons:
        entry = [tryStr(i[0]), i[15], i[19], i[23], i[27], i[31], i[35], i[39], i[43]]
        entry = [entry[0]] + [1 if x == 0 or x == '' else x for x in entry[1:]]
        if entry[0] != '':
            cur2.execute("INSERT OR REPLACE INTO weapon(name, reactorenergydrain, mass, minimumdamage, maximumdamage, vsshields, vsarmor, energyshot, refirerate) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",entry)

    loadouts = data['Loadouts'].values.tolist()
    for i in loadouts:
        entry = [tryStr(i[0]), i[1], i[2], i[7], i[8], i[5], i[11], i[10], i[9], i[4], i[3], i[6], i[12], i[13], i[14], i[15], i[16], i[17], i[18], i[19], 'None', 'None', 'None', 'None', 'None', 'None', 'None', 'None', i[21], i[22], i[23], i[24], i[29]]
        armorList = listify(cur2.execute("SELECT name FROM armor").fetchall())
        boosterList = listify(cur2.execute("SELECT name FROM booster").fetchall())
        capList = listify(cur2.execute("SELECT name FROM capacitor").fetchall())
        chList = listify(cur2.execute("SELECT name FROM cargohold").fetchall())
        diList = listify(cur2.execute("SELECT name FROM droidinterface").fetchall())
        engineList = listify(cur2.execute("SELECT name FROM engine").fetchall())
        reactorList = listify(cur2.execute("SELECT name FROM reactor").fetchall())
        shieldList = listify(cur2.execute("SELECT name FROM shield").fetchall())
        weaponList = listify(cur2.execute("SELECT name FROM weapon").fetchall())

        lists = [armorList, armorList, boosterList, capList, chList, diList, engineList, reactorList, shieldList, weaponList, weaponList, weaponList, weaponList, weaponList, weaponList, weaponList, weaponList]

        for j in range(3,20):
            if tryStr(entry[j]) == '' or tryStr(entry[j]) not in lists[j-3]:
                entry[j] = "None"
            else:
                entry[j] = tryStr(entry[j])

        if i[29] == "No Adjust":
            entry[32] = "None"
        else:
            side = i[29].split(" | ")[0]
            degree = i[29].split(" | ")[1]
            if side == "F":
                adjust = "Front - " + degree
            else:
                adjust = "Rear - " + degree
            entry[32] = adjust

        cur2.execute("INSERT OR REPLACE INTO loadout(name, chassis, mass, armor1, armor2, booster, capacitor, cargohold, droidinterface, engine, reactor, shield, slot1, slot2, slot3, slot4, slot5, slot6, slot7, slot8, pack1, pack2, pack3, pack4, pack5, pack6, pack7, pack8, rolevel, eolevel, colevel, wolevel, adjust) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",entry)

    if not len(loadouts) == 0:
        callback = True
    else:
        callback = False

    compdb.commit()
    return callback

def importBackupData():

    Layout = [
    [sg.Text()],
    [sg.Push(), sg.Text("Select Backup Datafile:", font=headerFont), sg.Input(s=50, key='input'), sg.FileBrowse(font=buttonFont), sg.Push()],
    [sg.Push(),sg.Text("Backup data should be downloaded from Google Sheets as a .xlsx file. Other file types will not work.", font=baseFont),sg.Push()],
    [sg.Text()],
    [sg.Push(), sg.Push(), sg.Button('Import', font=buttonFont), sg.Push(),sg.Button('Cancel', font=buttonFont), sg.Push(), sg.Push()]
    ]

    callback = False

    window = sg.Window("Import Backup Data from Seraph's Loadout Tool", Layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = window.read()

        if event == "Import":
            filepath = values['input']
            if filepath == '':
                doAlert("Please select a file to import.")
                window.TKroot.grab_set()
            elif os.path.splitext(filepath)[1] != '.xlsx':
                doAlert("The file you have selected does not appear to be a valid backup data file.\n\nPlease ensure that you have selected the correct file, and that it is in .xlsx format.")
                window.TKroot.grab_set()
            else:
                result = doAlertYN("This process will overwrite any currently-saved parts and loadouts which share a name with their imported counterparts.\nThis action cannot be undone. Do you wish to proceed?")
                window.TKroot.grab_set()
                if result == "Yes":
                    #try:
                    callback = importBackup(values['input'])
                    break
                    #except:
                        #doAlert("The file you have selected does not appear to be a valid backup data file.\n\nPlease ensure that you have selected the correct file, and that it is in .xlsx format.")
                        #window.TKroot.grab_set()

        if event == "Exit" or event == sg.WIN_CLOSED or event == "Cancel":
            break

    window.close()
    compdb.close()
    tables.close()
    return callback