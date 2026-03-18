import FreeSimpleGUI as sg
import json
import os
import sqlite3

from csv import reader as csvreader

headerFont = ("Calibri", int(12), 'bold')
summaryFont = ("Calibri", int(11), 'bold')
summaryFontStats = ("Calibri", int(11))
baseFont = ("Calibri", int(10), 'bold')
baseFontStats = ("Calibri", int(10), 'bold')
buttonFont = ("Calibri", int(13), 'bold')
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
                    'BUTTON': ('#f3f4f5', '#202225'),
                    'PROGRESS': ('#01826B', '#D0D0D0'),
                    'BORDER': 1,
                    'SLIDER_DEPTH': 0,
                    'PROGRESS_DEPTH' : 0}

sg.theme_add_new('Discord_Dark', theme_definition)

sg.theme('Discord_Dark')

dir = os.path.join(os.path.dirname(os.path.dirname(__file__))) + '\\Data\\'

with open(os.path.abspath(dir + 'data.json')) as jsonData:
    tables = json.load(jsonData)

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
    
def toKey(x):
    return x.lower().replace(" ", "").replace("/", "").replace(".", "")
    
def fetchSavedata(*category):

    saveDir = os.getenv("APPDATA") + "\\Seraph's Loadout Tool\\"

    with open(os.path.abspath(saveDir + 'savedata.json')) as jsonSavedata:
        savedata = json.load(jsonSavedata)

    try:
        return savedata[category[0]]
    except:
        return savedata

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

    data = {}

    for table in tables:
        columnNames = [x[0] for x in cur.execute("SELECT * FROM "+table).description]
        tableData = [x for x in cur.execute("SELECT * FROM "+table).fetchall()]
        tableList = []
        for entry in tableData:
            entryDict = {x:y for (x,y) in zip(columnNames,entry)}
            tableList.append(entryDict)
        data.update({table:tableList})

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

    dir = os.path.join(os.path.dirname(os.path.dirname(__file__))) + '\\Data\\'

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

def constructComponentBox(powered,dropdowns,unid,dims):
    
    if powered:
        titleRow = [[sg.Frame('',[[]],border_width=0,size=(20,20),p=0), sg.Push(), sg.Frame('',[[sg.Text('',font=headerFont,key=unid+'title',p=0)]],border_width=0,p=0), sg.Push(), sg.Frame('',[[sg.Text("⚡",key=unid+'powerboxtext',font=baseFont,text_color=boxColor,p=0,justification='center')]],border_width=0,key=unid+'powerbox',p=0,size=(20,20))]]
    else:
        titleRow = [[sg.Push(), sg.Frame('',[[sg.Text('',font=headerFont,key=unid + 'title',p=0)]],border_width=0,p=0), sg.Push()]]

    textLines = 8 #Just gonna have it default to the maximum for now. Unused lines will remain blank and may be cut off depending on the box dimensions. Saves me some headaches when updating stats.

    textCol = [[sg.Push(),sg.Text('',font=baseFont,p=0,key=unid+'textline'+str(x))] for x in range(textLines)] + [[sg.VPush()]]
    statCol = [[sg.Text('',font=baseFont,p=0,key=unid+'statline'+str(x)),sg.Push()] for x in range(textLines)] + [[sg.VPush()]]

    if dropdowns == 2:
        dropdownFrame = [
            [sg.Combo(values=[],default_value='',p=0,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown2',s=(40,10))], #tactical decision to put the ammo dropdown as dropdown 2 because it makes more sense programmatically even though it means they're in the wrong order
            [sg.Combo(values=[],default_value='',p=0,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown1',s=(40,10))]
        ]
    else:
        dropdownFrame = [
            [sg.Combo(values=[],default_value='',p=0,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown1',s=(40,10))]
        ]
 
    box = sg.Frame('',[
        [sg.Frame('',titleRow,border_width=0,p=0,size=(dims[0],25))],
        [sg.Push(),sg.Frame('',textCol,border_width=0,p=0,size=(dims[0]/2-4,dims[1]-70)),sg.Frame('',statCol,border_width=0,p=0,size=(dims[0]/2-4,dims[1]-70)),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',dropdownFrame,border_width=0,p=0,size=(dims[0],40))],
    ],border_width=0,p=0,size=dims)

    return box

def unidToSlotHeader(unid, chassis):
    return [x['weaponslots'][int(unid[-1])] for x in tables['chassis'] if x['name'] == chassis][0]

def checkSlotSelection(component):
    weapons = [x['name'] for x in fetchSavedata('weapon')]
    ordnance = [x['name'] for x in fetchSavedata('ordnancelauncher')]
    countermeasures = [x['name'] for x in fetchSavedata('countermeasurelauncher')]
    
    if component in weapons:
        return 'weapon'
    elif component in ordnance:
        return 'ordnancelauncher'
    elif component in countermeasures:
        return 'countermeasurelauncher'
    else:
        return 'None'
    
def getValidComponentTypes(slotHeader):
    try:
        validTypes = []
        if 'weapon' in slotHeader.casefold():
            validTypes.append('weapon')
        if 'ordnance' in slotHeader.casefold():
            validTypes.append('ordnancelauncher')
        if 'countermeasure' in slotHeader.casefold() or 'cm' in slotHeader.casefold():
            validTypes.append('countermeasurelauncher')
        return validTypes
    except:
        return []
    
def getValidPacks(component):
    compType = checkSlotSelection(component)
    if 'ordnance' in compType:
        launcherType = [x['type'] for x in fetchSavedata('ordnancelauncher') if x['name'] == component][0]
        return [x['name'] for x in fetchSavedata('ordnancepack') if x['type'] == launcherType]
    elif 'countermeasure' in compType:
        return [x['name'] for x in fetchSavedata('countermeasurepack')]
    else:
        return []

def populateDropdowns(window): #Also expand this later to run through all the dropdowns
    #unids = ['reactor','engine','booster','capacitor','shield','frontarmor','reararmor','droidinterface','cargohold','slot0','slot1','slot2','slot3','slot4','slot5','slot6','slot7']
    unids = ['slot0']
    #chassis = window['chassistype'].get()
    chassis = 'Advanced X-Wing' #test
    for unid in unids:
        try:
            previousSelection = window[unid+'dropdown1'].get()
            if 'slot' in unid:
                slotHeader = unidToSlotHeader(unid,chassis)
                validComps = getValidComponentTypes(slotHeader)
                dropdownCompNames = []
                dropdownPackNames = []
                for compType in validComps:
                    savedComponents = fetchSavedata(compType)
                    dropdownCompNames += [x['name'] for x in savedComponents]
                packs = getValidPacks(previousSelection)
                if packs != []:
                    window[unid+'dropdown2'].update(values=packs,size=(40,10))
            else:
                savedComponents = fetchSavedata(unid)
                dropdownCompNames = [x['name'] for x in savedComponents]
            window[unid+'dropdown1'].update(value=previousSelection,values=dropdownCompNames,size=(40,10)) #again, need to update when I add packs back in
            if dropdownPackNames != []:
                window[unid+'dropdown2'].update(value=previousSelection,values=dropdownCompNames,size=(40,10))
        except:
            pass

def updateComponentBox(window,unid,dropdown,component,*launcher):
    """
    Update component box (unid) with selected component.
    Calls subroutines to update loadout mass/power levels and update box power levels
    """
    #chassis = window['chassistype'].get()

    chassis = 'Advanced X-Wing' #test

    slotHeader = unidToSlotHeader(unid,chassis)
    window[unid+'title'].update(slotHeader)

    if component == 'None':
        dispStats = [''] * 8
        compStats = [''] * 8
    else:
        if 'slot' in unid:
            if dropdown == 1:
                compType = checkSlotSelection(component)
                keys = [toKey(y) for y in [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['stat']]
                if compType == 'None':
                    print('Error: could not identify the type of the selected component')
                    return
                elif compType not in ['ordnancelauncher','countermeasurelauncher']:
                    window[unid+'dropdown2'].update(values=[],visible=False)
                else:
                    window[unid+'dropdown2'].update(visible=True,size=(40,10))
            elif dropdown == 2:
                compType = checkSlotSelection(launcher)
                packType = compType.split('launcher')[0]+'pack'
                if compType == 'None':
                    print('Error: could not identify the type of the selected component')
                    return
            else:
                compType = unid
        else:
            compType = unid

        keys = [toKey(y) for y in [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['stat']]
        dispStats = [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['statdisp']
        if unid == 'shield' and 'Front HP:' in dispStats: #had to add second condition because there's some weird persistence that causes front HP to still be removed on second and subsequent calls? idk why.
            dispStats.remove('Front HP:') #prob a smarter way to do this, will have to think about it and come back to it.
            dispStats[2] = 'Shield HP:'
        if component != 'None':
            savedComponents = fetchSavedata(compType)
            compDict = [x for x in savedComponents if x['name'] == component][0]
            compStats = [compDict[x] for x in keys]
        else:
            compStats = [''] * 8
        if compType == 'ordnancepack':
            packType = [x['type'] for x in fetchSavedata(compType) if x['name'] == component][0]
            packStats = [x for x in tables['ordnance'] if x['name'] == packType][0]
            dispStats = ['Drain:','Mass:','Min Damage:','Max Damage:','Vs. Shields:','Vs. Armor:','Ammo:','PvE Mult:'] #clunky, but less ugly than other things that would be easy to implement. Maybe revisit later.
            compStats = compStats[0:2]

    for i in range(len(dispStats)): #note: will have to update later to add lines to shield for adjust in line with current implementation but obv can't do that until fc settings are re-implemented.
        window[unid+'textline'+str(i)].update(dispStats[i])
        window[unid+'statline'+str(i)].update(compStats[i])

    populateDropdowns(window)
    

def updateComponentBoxDepr(window, unid, keys, *powerLevel, enable=False, values=['',[],[]], dropdowns=[[]],): #Deprecated in favor of the version above with simpler inputs.
    """
    Update component box data. Returns nothing.
    Window: active window which contains the keys referenced by unid
    Unid: unique identifier for the box to be updated
    Keys: list of valid keys for the box
    Enable: enable or disable dropdowns for this box
    Values: list of a box title string followed by two lists representing the entries in the left and right columns
    Dropdowns: list of up to two lists representing the values to be listed in the dropdown boxes
    *PowerLevel: optional value from 0 to 1 which will determine the color of the power box
    """

    textLines = 0

    for key in keys:
        if 'textline' in key:
            textLines += 1

    if not(enable):
        values = [values[0],[],[]]
        dropdowns = [[]]
        powerLevel = None

    powerLevel = powerLevel[0]

    try:
        if powerLevel == 1:
            window[unid+'powerboxtext'].update(background_color='#00cc00',text_color="#000000")
            window[unid+'powerbox'].Widget.config(background='#00cc00')
        elif powerLevel >= 0.1:
            window[unid+'powerboxtext'].update(background_color='#ffcc00',text_color="#000000")
            window[unid+'powerbox'].Widget.config(background='#ffcc00')
        elif powerLevel == 0:
            window[unid+'powerboxtext'].update(background_color='#dd0000',text_color="#000000")
            window[unid+'powerbox'].Widget.config(background='#dd0000')
        else:
            window[unid+'powerboxtext'].update(background_color=boxColor,text_color=boxColor)
            window[unid+'powerbox'].Widget.config(background=boxColor)
    except:
        window[unid+'powerboxtext'].update(background_color=boxColor,text_color=boxColor)
        window[unid+'powerbox'].Widget.config(background=boxColor)
    else:
        pass

    window[unid+'title'].update(values[0])
    
    for i in range(textLines):
        try:
            window[unid+'textline'+str(i)].update(values[1][i])
            window[unid+'statline'+str(i)].update(values[2][i])
        except:
            window[unid+'textline'+str(i)].update('')
            window[unid+'statline'+str(i)].update('')

    window[unid+'dropdown1'].update(values=dropdowns[0],disabled=not(enable))

    if len(dropdowns) == 2:
        window[unid+'dropdown2'].update(values=dropdowns[1],disabled=not(enable))
