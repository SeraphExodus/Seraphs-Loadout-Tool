import FreeSimpleGUI as sg
import sqlite3
import os

from buildCompList import buildComponentList
from buildTables import buildTables
from createComponent import createComponent

headerFont = ("Roboto", 14, "bold")
baseFont = ("Roboto", 10, "bold")
baseFont_large = ("Roboto", 11, "bold")
buttonFont = ("Roboto", 16, "bold")
fontPadding = 0
elementPadding = 4
bgColor = "#202225"
boxColor = "#2f3136"
textColor = '#e4f2ff'

def tryFloat(x):
    try:
        y = float(x)
        return y
    except:
        return 0

def listify(x):
    xnew = []
    for i in x:
        xnew.append(i[0])
    return xnew

def doError(errorText):
    errorLayout = [
        [sg.Push(), sg.Text(errorText, font=baseFont), sg.Push()],
        [sg.Push(), sg.Button('Okay', font=baseFont), sg.Push()]
    ]

    errorWindow = sg.Window('Error', errorLayout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = errorWindow.read()
        if event == "Exit" or event == sg.WIN_CLOSED or event == 'Okay':
            break

    errorWindow.close()

def getComponentStats():

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    components = listify(cur.execute("SELECT type FROM component").fetchall())
    componentArray = []
    componentNames = []
    for i in components:
        i = i.lower().replace(" ", "").replace("/", "").replace(".", "")
        componentArray.append(cur2.execute("SELECT * FROM " + i + " ORDER BY name ASC").fetchall())
        componentNames.append(listify(componentArray[-1]))

    db.close()
    compdb.close()

    return components, componentNames, componentArray

def updateStatPreview(window, values):
            
    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    [components, componentNames, componentArray] = getComponentStats()

    partList = componentNames[components.index(values['comptypeselect'][0])]
    componentType = values['comptypeselect'][0]
    index1 = components.index(values['comptypeselect'][0])
    index2 = partList.index(values['complistbox'][0])
    window['parttype'].update(componentType)
    statList = list(cur.execute("SELECT * FROM component WHERE type = ?", [componentType]).fetchall()[0][17:35])
    statValues = componentArray[index1][index2][1:]
    for i in range(1, 9):
        try:
            window['stat' + str(i) + 'text'].update(statList[i-1])
            if statList[i-1] in ["Vs. Shields:", "Vs. Armor:", "Refire Rate:"]:
                window['stat' + str(i)].update("{:.3f}".format(tryFloat(statValues[i-1])))
            elif statList[i-1] == "Recharge:" and componentType == "Shield":
                window['stat' + str(i)].update("{:.2f}".format(tryFloat(statValues[i-1])))
            elif statList[i-1] == "Ammo:":
                window['stat' + str(i)].update(int(tryFloat(statValues[i-1])))
            else:
                window['stat' + str(i)].update(statValues[i-1])
        except:
            pass
    if componentType == "Shield":
        event, values = window.read(timeout = 0)
        window['stat5'].update(window['stat4'].get())
        window['stat4'].update(window['stat3'].get())

    componentName = values['complistbox'][0]
    entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
    loadoutList = ""
    for i in entries:
        loadouts = cur2.execute("SELECT name FROM loadout WHERE " + i + "= ?", [componentName]).fetchall()
        for j in loadouts:
            if j[0] not in loadoutList:
                loadoutList += j[0] + "\n"
    window['loadoutlist'].update(loadoutList)

    window.refresh()

    db.close()
    return componentType, statValues

def clearStatPreview(window):
    window['parttype'].update("")
    for i in range(1, 9):
        window['stat' + str(i) + 'text'].update("")
        window['stat' + str(i)].update("")
    window.refresh()

def deleteComponent(componentType, componentName):

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()
    Layout = [
        [sg.Push(), sg.Text("Are you certain you wish to delete this component? This action cannot be undone.", font=baseFont_large), sg.Push()],
        [sg.Push(), sg.Button('Proceed', font=baseFont_large, bind_return_key=True), sg.Button('Cancel', font=baseFont_large), sg.Push()]
    ]

    window = sg.Window('Delete Component?', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = window.read()
        if event == "Proceed":
            componentType = componentType.lower().replace(" ","").replace("/","").replace(".","")
            cur2.execute("DELETE FROM " + componentType + " WHERE name = ?", [componentName])
            if componentType == 'ordnancepack' or componentType == 'countermeasurepack':
                for i in range(1, 9):
                    cur2.execute("UPDATE loadout SET pack" + str(i) + " = '' WHERE pack" + str(i) + " = ?", [componentName])
            elif componentType == 'ordnancelauncher' or componentType == 'countermeasurelauncher' or componentType == 'weapon':
                for i in range(1, 9):
                    cur2.execute("UPDATE loadout SET slot" + str(i) + " = '' WHERE slot" + str(i) + " = ?", [componentName])
            else:
                entries = ['armor1', 'armor2', 'booster', 'capacitor', 'cargohold', 'droidinterface', 'engine', 'reactor', 'shield', 'slot1', 'slot2', 'slot3', 'slot4', 'slot5', 'slot6', 'slot7', 'slot8', 'pack1', 'pack2', 'pack3', 'pack4', 'pack5', 'pack6', 'pack7', 'pack8']
                for i in entries:    
                    cur2.execute("UPDATE loadout SET " + i + " = '' WHERE " + i + " = ?", [componentName])
            break

        if event == "Exit" or event == "Cancel" or event == sg.WIN_CLOSED or not event == "":
            break

    compdb.commit()
    compdb.close()
    window.close()

def manageComponents():
    sg.theme('Discord_Dark')

    if not os.path.exists("Data\\tables.db"):
        buildTables('null')

    if not os.path.exists("Data\\savedata.db"):
        buildComponentList()

    [components, componentNames, componentArray] = getComponentStats()

    leftColumn = [
        [sg.Push(),sg.Text("Select Component Type", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=components, size=(24, 13), enable_events=True, key='comptypeselect', justification='center', no_scrollbar=True, font=baseFont, select_mode="single")],
        [sg.VPush()],
    ]
    centerColumn = [
        [sg.Push(),sg.Text("Select Component", font=baseFont, p=fontPadding),sg.Push()],
        [sg.VPush()],
        [sg.Listbox(values=[], key='complistbox', size=(40,13), font=baseFont, enable_events=True, select_mode='single')],
        [sg.VPush()],
    ]

    statPreviewText = [
        [sg.Push(),sg.Text("",font=baseFont,key='stat1text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat2text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat3text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat4text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat5text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat6text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat7text', p=fontPadding, justification='right')],
        [sg.Push(),sg.Text("",font=baseFont,key='stat8text', p=fontPadding, justification='right')],
    ]

    statPreviewStats = [
        [sg.Text("",font=baseFont,key='stat1', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat2', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat3', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat4', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat5', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat6', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat7', p=fontPadding)],
        [sg.Text("",font=baseFont,key='stat8', p=fontPadding)],
    ]

    statFrame = [
        [sg.Push(),sg.Text("",font=baseFont,key='parttype'), sg.Push()],
        [sg.Frame('', statPreviewText, border_width=0, s=(100,250), p=elementPadding),sg.Frame('', statPreviewStats, border_width=0, s=(134,250), p=elementPadding)]
    ]

    rightCenterColumn = [
        [sg.Push(),sg.Text("Stat Preview", font=baseFont), sg.Push()],
        [sg.VPush()],
        [sg.Frame('', statFrame, border_width=0, s=(235,250))],
        [sg.VPush()]
    ]

    loadoutColumn = [
        [sg.Push(), sg.Text("Used in These Loadouts", font=baseFont), sg.Push()],
        [sg.VPush()],
        [sg.Frame('',[[sg.Push(),sg.Text("", font=baseFont, key='loadoutlist', justification='center'),sg.Push()]],border_width=0,p=elementPadding,size=(225,250))],
        [sg.VPush()]
    ]

    Layout = [
        [sg.Push(), sg.Text("Manage Components", font=headerFont), sg.Push()],
        [sg.vtop(sg.Frame('',leftColumn, border_width=0,p=elementPadding,s=(200,250),element_justification='center')), sg.vtop(sg.Frame('',centerColumn, border_width=0,p=elementPadding,s=(300,250),element_justification='center')), sg.vtop(sg.Frame('',rightCenterColumn, border_width=0,p=elementPadding,s=(250,250),element_justification='center')),sg.vtop(sg.Frame('',loadoutColumn, border_width=0,p=elementPadding,s=(225,250),element_justification='center'))],
        [sg.VPush()],
        [sg.Push(),sg.Push(),sg.Button("Add",font=buttonFont),sg.Push(),sg.Button("Edit",font=buttonFont),sg.Push(),sg.Button("Delete",font=buttonFont),sg.Push(),sg.Button("Exit",font=buttonFont),sg.Push(),sg.Push()],
        [sg.VPush()]
    ]

    window = sg.Window('Manage Components', Layout, modal=True, finalize=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    window.bind('<Escape>', 'Exit')

    modified = False

    while True:
        event, values = window.read()
        if event == 'comptypeselect':
            [components, componentNames, componentArray] = getComponentStats()
            partList = componentNames[components.index(values['comptypeselect'][0])]
            window['complistbox'].update(values=partList)

        if event == 'complistbox':
            for i in range(1, 9):
                try:
                    window['stat' + str(i) + 'text'].update("")
                    window['stat' + str(i)].update("")
                except:
                    pass
            
            if values['complistbox'] != []:
                updateStatPreview(window, values)

        if event == "Add":
            try:
                modified = createComponent(values['comptypeselect'][0])
                [components, componentNames, componentArray] = getComponentStats() 
                partList = componentNames[components.index(values['comptypeselect'][0])]
                window['complistbox'].update(values=partList)
            except:
                doError("Error: Select a component type.")
            window.TKroot.grab_set()
            
        if event == "Edit":
            try:
                [componentType, statValues] = updateStatPreview(window, values)
                try: 
                    event, values = window.read(timeout=0)
                    editArgs = values['complistbox'] + [window['stat1'].get(),window['stat2'].get(),window['stat3'].get(),window['stat4'].get(),window['stat5'].get(), window['stat6'].get(),window['stat7'].get(),window['stat8'].get()]
                    modified = createComponent(componentType, editArgs)
                    event, values = window.read(timeout=0)
                    [components, componentNames, componentArray] = getComponentStats() 
                    partList = componentNames[components.index(values['comptypeselect'][0])]
                    window['complistbox'].update(values=partList)
                    updateStatPreview(window, values)
                except:
                    pass
            except:
                doError("Error: Select a component to edit.")
            window.TKroot.grab_set()

        if event == "Delete":
            event, values = window.read(timeout=0)
            componentType = window['parttype'].get()
            try:
                componentName = values['complistbox'][0]
                deleteComponent(componentType, componentName)
                [components, componentNames, componentArray] = getComponentStats() 
                partList = componentNames[components.index(values['comptypeselect'][0])]
                window['complistbox'].update(values=partList)
                clearStatPreview(window)
                modified = True
            except:
                pass
            window.TKroot.grab_set()

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    window.close()
    return modified