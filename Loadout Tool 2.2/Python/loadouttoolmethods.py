import FreeSimpleGUI as sg
import json
import os
import sqlite3

from csv import reader as csvreader
from win32gui import FindWindow, GetWindowRect

textScale = 8

headerFont = ("Calibri", textScale+2, 'bold')
summaryFont = ("Calibri", textScale+1, 'bold')
summaryFontStats = ("Calibri", textScale+1)
baseFont = ("Calibri", textScale, 'bold')
baseFontStats = ("Calibri", textScale, 'bold')
buttonFont = ("Calibri", textScale+3, 'bold')

fontPadding = 0
elementPadding = 4
bgColor = '#202225'
boxColor = '#313338'
textColor = '#f3f4f5'

fullPowerColor = '#00cc00'
lowPowerColor = '#ffcc00'
noPowerColor = '#dd0000'

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

unids = [
    'reactor',
    'engine',
    'booster',
    'capacitor',
    'shield',
    'frontarmor',
    'reararmor',
    'droidinterface',
    'cargohold',
    'slot0',
    'slot1',
    'slot2',
    'slot3',
    'slot4',
    'slot5',
    'slot6',
    'slot7'
    ]

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
        if 'armor' in category[0]:
            return savedata['armor']
        else:
            return savedata[category[0]]
    except:
        return savedata

def fetchStats(compType, component, output):
    savedComponents = fetchSavedata(compType)
    keys = [toKey(y) for y in [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['stat']]
    if component not in ['', 'None']:
        compDict = [x for x in savedComponents if x['name'] == component][0]
        if output == 'list':
            return [compDict[x] for x in keys]
        elif output == 'dict':
            return compDict
        else:
            raise ValueError
    else:
        if output == 'list':
            return []
        elif output == 'dict':
            return {}

def fetchOrdnanceStats(compType):
    rawStats = [x for x in tables['ordnance'] if x['name'] == compType][0]
    return [rawStats['name'],rawStats['vsx'],rawStats['pvemod']]

def fetchLoadoutStats(window):
    global unids
    statDicts = []
    for unid in unids:
        component = window[unid+'dropdown1'].get()
        if component in ['None','']:
            statDicts.append({'unid':unid,'component':'None','stats':{}})
        elif 'slot' in unid:
            compType = checkSlotSelection(component)
            if compType == 'weapon':
                statDicts.append({'unid':unid,'stats':fetchStats(compType,component,'dict')})
            else:
                pack = window[unid+'dropdown2'].get()
                packType = compType.replace('launcher','pack')
                statDicts.append({'unid':unid,'stats':fetchStats(compType,component,'dict')})
                statDicts.append({'unid':unid+'pack','stats':fetchStats(packType,pack,'dict')})
        else:
            if 'armor' in unid:
                compType = 'armor'
            else:
                compType = unid
            statDicts.append({'unid':unid,'stats':fetchStats(compType,component,'dict')})
    return statDicts

def fetchOverloadEffects(window):
    event, values = window.read(timeout=0)

    overloadSettings = [window['reactoroverloadlevel'].get(),window['engineoverloadlevel'].get(),window['capacitoroverloadlevel'].get(),window['weaponoverloadlevel'].get()]
    typeMap = ['Reactor Overload', 'Engine Overload', 'Capacitor Overcharge', 'Weapon Overload']
    levelMap = ['None', 'One', 'Two', 'Three', 'Four']
    overloadSettings = [levelMap[tryInt(x)] if x != 'None' else 'None' for x in overloadSettings]
    fcProgs = tables['fcprograms']
    modifiers = []
    for i in range(4):
        if overloadSettings[i] != 'None':
            modifiers.append([x['modifiers'][1:3] for x in fcProgs if typeMap[i] in x['name'] and overloadSettings[i] in x['name']][0])
        else:
            modifiers.append([1, 1])
    return modifiers

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

    with open(dir + 'data.json', 'w') as f:
        json.dump(compiledData, f)

def constructLoadoutSummary(size, textScale):
    headerFont = ("Calibri", textScale+2, 'bold')
    baseFont = ("Calibri", textScale, 'bold')

    textColumn = []
    dataColumn = []

    for i in range(5):
        textColumn.append([sg.Push(),sg.Text('',key='loadouttext'+str(i),font=summaryFont,p=0)])
        dataColumn.append([sg.Text('',key='loadoutdata'+str(i),font=summaryFont,p=0),sg.Push()])

    layout = [
        [sg.Push(),sg.Text('Loadout Summary',font=headerFont,p=0),sg.Push()],
        [sg.Push(),sg.Text('',key='loadoutname',font=summaryFont,p=0),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',textColumn,border_width=0,p=0),sg.Frame('',dataColumn,border_width=0,p=0),sg.Push()],
        [sg.VPush()]
    ]

    box = sg.Frame('',layout,border_width=0,p=elementPadding,size=size)

    return box

def constructFCProgramSelector(size, textScale):

    headerFont = ("Calibri", textScale+2, 'bold')
    baseFont = ("Calibri", textScale, 'bold')

    programLevels = ['None',1,2,3,4]
    if textScale == 10:
        adjustLevels = ['Front - Extreme','Front - Heavy','Front - Moderate','Front - Light','None','Rear - Light','Rear - Moderate','Rear - Heavy','Rear - Extreme']
        adjustComboWidth = 16
    else:
        adjustLevels = ['Front - Extr.','Front - Heavy','Front - Mod.','Front - Light','None','Rear - Light','Rear - Mod.','Rear - Heavy','Rear - Extr.']
        adjustComboWidth = 9

    textColumn = [
        [sg.Push(),sg.Text('Reactor Overload:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Engine Overload:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Capacitor Overcharge:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Weapon Overload:',font=baseFont,p=1)],
        [sg.Text('',font=baseFont,p=0)],
    ]

    selectColumn = [
        [sg.Combo(values=programLevels,default_value=4,size=(4,5),key='reactoroverloadlevel',font=baseFont,p=1,readonly=True,enable_events=True),sg.Push()],
        [sg.Combo(values=programLevels,default_value=4,size=(4,5),key='engineoverloadlevel',font=baseFont,p=1,readonly=True,enable_events=True),sg.Push()],
        [sg.Combo(values=programLevels,default_value=4,size=(4,5),key='capacitoroverloadlevel',font=baseFont,p=1,readonly=True,enable_events=True),sg.Push()],
        [sg.Combo(values=programLevels,default_value=4,size=(4,5),key='weaponoverloadlevel',font=baseFont,p=1,readonly=True,enable_events=True),sg.Push()],
        [sg.Text('',font=baseFont,p=0)],
    ]

    leftWidth = size[0]/2+25
    rightWidth = size[0]/2-25

    layout = [
        [sg.Push(),sg.Text('FC Program Settings',font=headerFont,p=0),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',textColumn,border_width=0,p=0,size=(leftWidth,size[1]/2)),sg.Frame('',selectColumn,border_width=0,p=0,size=(rightWidth,size[1]/2))],
        [sg.Frame('',[[sg.Push(),sg.Text('Shield Adjust:',font=baseFont,p=1),sg.Combo(values=adjustLevels,default_value='None',size=(adjustComboWidth,9),key='shieldadjustlevel',font=baseFont,p=1,readonly=True,enable_events=True),sg.Push()]],border_width=0,p=0)],
        [sg.VPush()]
    ]

    box = sg.Frame('',layout,border_width=0,p=elementPadding,size=size)

    return box

def constructComponentBox(unid,size,powered,dropdowns,textScale):

    headerFont = ("Calibri", textScale+2, 'bold')
    baseFont = ("Calibri", textScale, 'bold')

    width = size[0]
    halfWidth = size[0]/2-4
    topHeight = 25
    bottomHeight = (textScale+10) * dropdowns
    midHeight = size[1] - (topHeight + bottomHeight + 10)
    
    if powered:
        titleRow = [sg.Frame('',[[sg.Text('',font=headerFont,p=0)]],border_width=0,p=0,size=(20,20)), sg.Push(), sg.Frame('',[[sg.Text('',font=headerFont,key=unid+'title',p=0)]],border_width=0,p=0), sg.Push(), sg.Frame('',[[sg.Text("⚡",key=unid+'powerbox',font=headerFont,text_color=boxColor,p=0,justification='center')]],border_width=0,p=0,size=(20,20))]
    else:
        titleRow = [sg.Push(), sg.Frame('',[[sg.Text('',font=headerFont,key=unid + 'title',p=0)]],border_width=0,p=0), sg.Push()]

    textLines = 8 #Just gonna have it default to the maximum for now. Unused lines will remain blank and may be cut off depending on the box dimensions. Saves me some headaches when updating stats.

    textCol = [[sg.Push(),sg.Text('',font=baseFont,p=0,key=unid+'textline'+str(x))] for x in range(textLines)] + [[sg.VPush()]]
    statCol = [[sg.Text('',font=baseFont,p=0,key=unid+'statline'+str(x)),sg.Push()] for x in range(textLines)] + [[sg.VPush()]]

    if dropdowns == 2:
        dropdownFrame = [
            [sg.Combo(values=[],default_value='',p=1,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown2',s=(40,10))], #tactical decision to put the ammo dropdown as dropdown 2 because it makes more sense programmatically even though it means they're in the wrong order
            [sg.Combo(values=[],default_value='',p=1,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown1',s=(40,10))]
        ]
    else:
        dropdownFrame = [
            [sg.Combo(values=[],default_value='',p=1,enable_events=True,readonly=True,font=baseFont,key=unid+'dropdown1',s=(40,10))]
        ]
 
    box = sg.Frame('',[
        [sg.Frame('',[titleRow],border_width=0,p=0,size=(width,topHeight))],
        [sg.Push(),sg.Frame('',textCol,border_width=0,p=0,size=(halfWidth,midHeight)),sg.Frame('',statCol,border_width=0,p=0,size=(halfWidth,midHeight)),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',dropdownFrame,border_width=0,p=0,size=(width,bottomHeight))],
    ],border_width=0,p=elementPadding,size=size)

    return box

def unidToHeader(unid, chassis):
    try:
        return [x['weaponslots'][int(unid[-1])] for x in tables['chassis'] if x['name'] == chassis][0]
    except:
        try:
            nonSlotUnids = ['reactor','engine','booster','capacitor','shield','frontarmor','reararmor','droidinterface','cargohold']
            mappedNames = ['Reactor','Engine','Booster','Capacitor','Shield','Front Armor','Rear Armor','Droid Interface','Cargo Hold']
            return mappedNames[nonSlotUnids.index(unid)]
        except:
            return ''

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

def populateDropdowns(window):
    event, values = window.read(timeout=0) #Async read to see updates
    global unids
    chassis = window['loadoutdata0'].get()
    if chassis != '':
        for unid in unids:
            try:
                disableFlag = False
                previousSelection = window[unid+'dropdown1'].get()
                if 'slot' in unid:
                    header = unidToHeader(unid,chassis)
                    validComps = getValidComponentTypes(header)
                    if validComps != []:
                        disableFlag = False
                        dropdownCompNames = ['None']
                        dropdownPackNames = ['None']
                        for compType in validComps:
                            savedComponents = fetchSavedata(compType)
                            dropdownCompNames += [x['name'] for x in savedComponents]
                        dropdownPackNames += getValidPacks(previousSelection)
                        if dropdownPackNames != ['None']:
                            previousPack = window[unid+'dropdown2'].get()
                            if previousPack not in dropdownPackNames:
                                previousPack = 'None'
                            window[unid+'dropdown2'].update(value=previousPack,values=dropdownPackNames,size=(40,10), disabled=False)
                    else:
                        dropdownCompNames = ['None']
                        disableFlag = True
                        window[unid+'dropdown2'].update(value='None',values=['None'],size=(40,10),disabled=True, visible=False)
                else:
                    savedComponents = fetchSavedata(unid)
                    dropdownCompNames = ['None'] + [x['name'] for x in savedComponents]
                window[unid+'dropdown1'].update(value=previousSelection,values=dropdownCompNames,size=(40,10), disabled=disableFlag)
            except:
                window[unid+'dropdown1'].update(value='None',values=['None'],size=(40,10),disabled=True)
                if 'slot' in unid:
                    window[unid+'dropdown2'].update(value='None',values=['None'],size=(40,10),disabled=True, visible=False)
    else:
        for unid in unids:
            window[unid+'dropdown1'].update(value='None',values=['None'],size=(40,10),disabled=True)
            if 'slot' in unid:
                window[unid+'dropdown2'].update(value='None',values=['None'],size=(40,10),disabled=True, visible=False)

def updateMassTotals(window):
    currentLoadoutName = window['loadoutname'].get()
    loadoutData = fetchSavedata('loadout')

    if currentLoadoutName != '':
        try:
            loadoutMaxMass = tryFloat([x['mass'] for x in loadoutData if x['name'] == currentLoadoutName][0])
        except:
            loadoutMaxMass = 0

        currentLoadoutData = fetchLoadoutStats(window)
        massTotal = sum([x['stats'].get('mass') or 0 for x in currentLoadoutData])

        try:
            percentage = ' (' + '{:.1f}'.format(round(massTotal/loadoutMaxMass * 100, 1)) + '%)'
        except:
            percentage = ''

        remainder = round(loadoutMaxMass - massTotal,1)

        if remainder < 0:
            color = '#ff0000'
        else:
            color = textColor

        window['loadoutdata1'].update('{:.1f}'.format(massTotal) + ' of ' + '{:.1f}'.format(loadoutMaxMass) + percentage,text_color=color)
        window['loadoutdata2'].update(str(remainder))
    else:
        window['loadoutdata1'].update('',text_color=textColor)
        window['loadoutdata2'].update('')

def updateDrainTotals(window):
    currentLoadoutName = window['loadoutname'].get()
    chassisType = window['loadoutdata0'].get()
    loadoutData = fetchLoadoutStats(window)

    if currentLoadoutName != '':
        overloadEffects = fetchOverloadEffects(window)
        try:
            reactorOverloadedGen = overloadEffects[0][1] * tryFloat([x['stats']['reactorgenerationrate'] for x in loadoutData if x['unid'] == 'reactor'][0])
        except:
            reactorOverloadedGen = 0
        componentDrain = []
        reactorGenRemaining = reactorOverloadedGen
        powerHierarchy = ['engine','shield','capacitor','booster','droidinterface','slot0','slot1','slot2','slot3','slot4','slot5','slot6','slot7']
        for unid in powerHierarchy:
            component = [x for x in loadoutData if x['unid'] == unid][0]
            drain = tryFloat(component['stats'].get('reactorenergydrain')) or 0
            cmFlag = False
            if drain == 0:
                window[unid + 'powerbox'].Widget.config(background=boxColor)
                window[unid + 'powerbox'].update(text_color=boxColor)
            else:
                if unid == 'engine':
                    drain /= overloadEffects[1][0]
                    reactorGenRemaining -= drain
                elif unid == 'capacitor':
                    drain /= overloadEffects[2][0]
                    reactorGenRemaining -= drain
                elif 'slot' in unid: ### FIX THIS, IT'S NOT CORRECT - drain from cm is only 1/10th if it's last in sequence, otherwise it pulls full power before passing leftover gen to later slots (gunship issue)
                    drain /= overloadEffects[3][0]
                    header = unidToHeader(unid,chassisType)
                    if 'Countermeasure' in header:
                        cmFlag = True
                        reactorGenRemaining -= drain/10
                    else:
                        reactorGenRemaining -= drain
                if reactorGenRemaining >= 0:
                    window[unid + 'powerbox'].Widget.config(background=fullPowerColor)
                    window[unid + 'powerbox'].update(text_color='#000000')
                elif reactorGenRemaining < 0 and reactorGenRemaining + drain >= 0:
                    window[unid + 'powerbox'].Widget.config(background=lowPowerColor)
                    window[unid + 'powerbox'].update(text_color='#000000')
                else:
                    window[unid + 'powerbox'].Widget.config(background=noPowerColor)
                    window[unid + 'powerbox'].update(text_color='#000000')

            componentDrain.append({'unid':unid, 'drain':drain, 'cmflag':cmFlag})

        if reactorGenRemaining < 0:
            color = '#ff0000'
        else:
            color = textColor

        reactorConsumedEnergy = reactorOverloadedGen - reactorGenRemaining
        percentage = ' (' + '{:.1f}'.format(round(reactorConsumedEnergy/reactorOverloadedGen*100,1)) + '%)'
        window['loadoutdata3'].update('{:.1f}'.format(round(reactorConsumedEnergy,1)) + ' of ' + '{:.1f}'.format(round(reactorOverloadedGen,1)) + percentage,text_color=color)

        minimumReactorEnergy = round(reactorConsumedEnergy / overloadEffects[0][1],1)
        window['loadoutdata4'].update('{:.1f}'.format(minimumReactorEnergy))

    else:
        window['loadoutdata3'].update('',text_color=textColor)
        window['loadoutdata4'].update('')

def updateLoadoutSummary(window, loadout):

    loadoutData = fetchSavedata('loadout')

    try:
        currentLoadout = [x for x in loadoutData if x['name'] == loadout][0]
        window['loadoutname'].update(loadout)

        window['loadouttext0'].update('Chassis Type:')
        window['loadouttext1'].update('Mass Utilization:')
        window['loadouttext2'].update('Remaining Mass:')
        window['loadouttext3'].update('Reactor Utilization:')
        window['loadouttext4'].update('Minimum Required Gen:')

        window['loadoutdata0'].update(currentLoadout['chassis'])
        window['loadoutdata1'].update(currentLoadout['mass'])
    except:
       window['loadoutname'].update('')
       for i in range(5):
           window['loadouttext' + str(i)].update('')
           window['loadoutdata' + str(i)].update('')

def updateOverloads(window, loadout):

    loadoutData = fetchSavedata('loadout')
    thisLoadout = [x for x in loadoutData if x['name'] == loadout][0]
    
    window['reactoroverloadlevel'].update(thisLoadout['rolevel'])
    window['engineoverloadlevel'].update(thisLoadout['eolevel'])
    window['capacitoroverloadlevel'].update(thisLoadout['colevel'])
    window['weaponoverloadlevel'].update(thisLoadout['wolevel'])

    scale = window.metadata
    adjustMapLarge = ['Front - Extreme','Front - Heavy','Front - Moderate','Front - Light','None','Rear - Light','Rear - Moderate','Rear - Heavy','Rear - Extreme']
    adjustMapSmall = ['Front - Extr.','Front - Heavy','Front - Mod.','Front - Light','None','Rear - Light','Rear - Mod.','Rear - Heavy','Rear - Extr.']
    if scale == 'small':
        mappedValue = adjustMapSmall[adjustMapLarge.index(thisLoadout['adjust'])]
        window['shieldadjustlevel'].update(mappedValue)
    else:
        window['shieldadjustlevel'].update(thisLoadout['adjust'])

    
def updateComponentBox(window,unid,dropdown,component,*launcher):
    """
    Update component box (unid) with selected component.
    Calls subroutines to update loadout mass/power levels and update box power levels
    """

    event, values = window.read(timeout=0) #async window read to get updates
    chassis = window['loadoutdata0'].get()

    updateType = 1

    header = unidToHeader(unid,chassis)
    window[unid+'title'].update(header)

    if 'slot' in unid:
        if dropdown == 1:
            compType = checkSlotSelection(component)
            if compType == 'None' and component not in ['None', '']:
                print('Error: could not identify the type of the selected component')
                return
            elif compType not in ['ordnancelauncher','countermeasurelauncher']:
                window[unid+'dropdown2'].update(values=[],visible=False)
            else:
                window[unid+'dropdown2'].update(visible=True,size=(40,10))
        else:
            compType = checkSlotSelection(launcher[0])
            packType = compType.split('launcher')[0]+'pack'
            if compType == 'None' and component not in ['None', '']:
                print('Error: could not identify the type of the selected component')
                return
            updateType = 2
    elif 'armor' in unid:
        compType = 'armor'
    else:
        compType = unid

    if updateType == 1:
        if component in ['None', '']:
            dispStats = [''] * 8
            compStats = [''] * 8
        else:
            dispStats = [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['statdisp']
            if unid == 'shield' and 'Front HP:' in dispStats: #had to add second condition because there's some weird persistence that causes front HP to still be removed on second and subsequent calls? idk why.
                dispStats.remove('Front HP:') #prob a smarter way to do this, will have to think about it and come back to it.
                dispStats[2] = 'Shield HP:'
            if component != 'None':
                compStats = fetchStats(compType, component,'list')
            else:
                compStats = [''] * 8
    else: #only run this if a pack was selected or removed via the second dropdown
        if component in ['None', '']:
            dispStats = [x for x in tables['componentstats'] if toKey(x['comptype']) == compType][0]['statdisp']
            compStats = fetchStats(compType,launcher[0],'list')
        elif packType == 'ordnancepack':
            dispStats = ['Drain:','Mass:','Min Damage:','Max Damage:','Vs. Shields:','Vs. Armor:','Ammo:','PvE Mult:'] #clunky, but less ugly than other things that would be easy to implement. Maybe revisit later.
            launcherStats = fetchStats(compType,launcher[0],'list')
            packStats = fetchStats(packType,component,'list')
            packTypeStats = fetchOrdnanceStats(packStats[3])
            compStats = launcherStats[0:2] + packStats[0:2] + packTypeStats[1][0:2] + [packStats[2]] + [packTypeStats[2]] #again, clunky, but sanest way I could think of
        else:
            dispStats = ['Drain:','Mass:','Ammo:']
            launcherStats = fetchStats(compType,launcher[0],'list')
            packStats = fetchStats(packType,component,'list')
            compStats = launcherStats[0:2] + [packStats[0]]

    while len(compStats) < 8:
        compStats += ['']

    while len(dispStats) < 8:
        dispStats += ['']

    if unid == 'shield' and component != 'None': #apply shield adjust
        adjust = window['shieldadjustlevel'].get()
        adjustMapLarge = ['Front - Extreme','Front - Heavy','Front - Moderate','Front - Light','None','Rear - Light','Rear - Moderate','Rear - Heavy','Rear - Extreme']
        adjustMapSmall = ['Front - Extr.','Front - Heavy','Front - Mod.','Front - Light','None','Rear - Light','Rear - Mod.','Rear - Heavy','Rear - Extr.']
        if adjust != 'None':
            side = adjust.split(' ')[0]
            level = adjust.split(' ')[2]
            if window.metadata == 'small':
                level = level.split('.')[0]
            programData = [x for x in tables['fcprograms'] if all(['Adjust' in x['name'], side in x['name'], level in x['name']])][0]
            dispAdjust = programData['name'].split(' ')[1] + ' - ' + programData['name'].split(' ')[4]
            if window.metadata == 'small':
                dispAdjust = adjustMapSmall[adjustMapLarge.index(dispAdjust)] #annoying to have to change it to full-length and then back but it is what it is.
            dispStats[5:8] = ['Adjust:', 'Front HP:', 'Back HP:']
            compStats[5:8] = [dispAdjust, compStats[2] * programData['modifiers'][7], compStats[2] * (2 - programData['modifiers'][7])]
        else:
            dispStats[4:9] = [''] * 4
            compStats[4:9] = [''] * 4 

    for i in range(len(dispStats)):
        if compStats[i] != '':
            if dispStats[i] in ['Vs. Shields:','Vs. Armor:','Refire Rate:']:
                compStats[i] = "{:.3f}".format(tryFloat(compStats[i])) #tryfloat needed in case the stats are saved as strings (just a failsafe, definitely not because I'm lazy in how I store data)
            elif dispStats[i] == 'Recharge Rate:' and compType == 'shield':
                compStats[i] = "{:.2f}".format(tryFloat(compStats[i]))
            elif dispStats[i] == 'Ammo:':
                compStats[i] = "{:.0f}".format(tryFloat(compStats[i]))
            elif type(compStats[i]) != str:
                compStats[i] = "{:.1f}".format(tryFloat(compStats[i]))

        window[unid+'textline'+str(i)].update(dispStats[i])
        window[unid+'statline'+str(i)].update(compStats[i])

def loadLoadout(window, loadout):
    global unids

    updateLoadoutSummary(window, loadout['name'])
    updateOverloads(window,loadout['name'])
    event, values = window.read(timeout=0)

    for unid in unids:
        dropdowns = [1]
        newValue2 = []
        if 'slot' not in unid:
            if unid == 'frontarmor':
                source = 'armor1'
                savedItems = fetchSavedata('armor')
            elif unid == 'reararmor':
                source = 'armor2'
                savedItems = fetchSavedata('armor')
            else:
                source = unid
                savedItems = fetchSavedata(unid)
            if loadout[source] in [x['name'] for x in savedItems]:
                newValue = loadout[source]
            else:
                newValue = 'None'
        else:
            source = unid[:-1] + str(int(unid[-1]) + 1) #paying the price for my own shit design choices
            compType = checkSlotSelection(loadout[source])
            if compType == 'None':
                newValue = 'None'
            elif compType == 'weapon':
                savedItems = fetchSavedata(compType)
                if loadout[source] in [x['name'] for x in savedItems]:
                    newValue = loadout[source]
                else:
                    newValue = 'None'
            else:
                dropdowns.append(2)
                savedItems = fetchSavedata(compType)
                savedPacks = fetchSavedata(compType.replace('launcher','pack'))
                if loadout[source] in [x['name'] for x in savedItems]:
                    newValue = loadout[source]
                else:
                    newValue = 'None'
                if loadout[source.replace('slot','pack')] in [x['name'] for x in savedPacks]:
                    newValue2 = loadout[source.replace('slot','pack')]
                else:
                    newValue2 = 'None'
        
        window[unid+'dropdown1'].update(value=newValue)
        updateComponentBox(window,unid,1,newValue)
        if newValue2 != []:
            window[unid+'dropdown2'].update(value=newValue2)
            updateComponentBox(window,unid,2,newValue2,newValue)
    

def move_center(window):
    screen_width, screen_height = window.get_screen_dimensions()
    win_width, win_height = window.size
    screen_height -= 100
    x, y = (screen_width - win_width)//2, (screen_height - win_height)//2
    window.move(x, y)

def setMenus(menuEnables):

    [openLoadoutEnable,saveAsEnable,saveEnable] = menuEnables

    if openLoadoutEnable:
        openLoadoutString = '&Open Loadout'
    else:
        openLoadoutString = '!&Open Loadout'
    
    if saveAsEnable:
        saveAsString = '&Save Loadout As'
        clearCompString = '&Clear All Components'
    else:
        saveAsString = '!&Save Loadout As'
        clearCompString = '!&Clear All Components'

    if saveEnable:
        saveString = '&Save Loadout'
    else:
        saveString = '!&Save Loadout'

    menu_def = [
            ['&Loadout', ['&New Loadout', openLoadoutString, saveString, saveAsString, '&Quit']],
            ['&Components', ['Add and &Manage Components', clearCompString]],
            ['&Tools', ['&Reverse Engineering Calculator','&Flight Computer Calculator','&Loot Lookup Tool','&Import v1.x Data', '&Check for Updates']],
            ['&Options', ['&Change Window Scale']],
            ['&Help', ['&About','&Keyboard Shortcuts']]
        ]
        
    return menu_def

def buildWindow(currentVersion, scale, menu_def):

    if scale == 'small':

        textScale = 8
        boxWidth = 161
        boxHeight = 213
        boxHeightShort = 163

        summaryBoxSize = (2*boxWidth + 2*elementPadding, boxHeightShort)
        largeBoxSize = (boxWidth, boxHeight)
        smallBoxSizeA = (boxWidth, boxHeightShort)
        smallBoxSizeB = (boxWidth, boxHeight/2-4)
        smallBoxSizeC = (boxWidth, boxHeightShort/2+5)
        smallBoxSizeD = (boxWidth, boxHeight-boxHeightShort/2-4)
        smallBoxSizeE = (boxWidth, boxHeightShort/2-13)

        leftFrame = [
            [constructLoadoutSummary(summaryBoxSize,textScale),sg.Frame('',[[constructComponentBox('reactor',smallBoxSizeC,False,1,textScale)],[constructComponentBox('cargohold',smallBoxSizeE,False,1,textScale)]],border_width=0,p=0,background_color=bgColor)],
            [constructComponentBox('engine',largeBoxSize,True,1,textScale),constructComponentBox('booster',largeBoxSize,True,1,textScale),constructComponentBox('slot0',largeBoxSize,True,2,textScale)],
            [sg.Frame('',[[constructComponentBox('shield',largeBoxSize,True,1,textScale)],],border_width=0,p=0,background_color=bgColor),
             sg.Frame('',[[constructComponentBox('frontarmor',smallBoxSizeB,False,1,textScale)],[constructComponentBox('reararmor',smallBoxSizeB,False,1,textScale)]],border_width=0,p=0,background_color=bgColor),constructComponentBox('slot1',largeBoxSize,True,2,textScale)]
        ]
    
        rightFrame = [
            [constructComponentBox('capacitor',smallBoxSizeA,True,1,textScale),constructComponentBox('droidinterface',smallBoxSizeA,True,1,textScale),constructFCProgramSelector(smallBoxSizeA,textScale)],
            [constructComponentBox('slot2',largeBoxSize,True,2,textScale),constructComponentBox('slot4',largeBoxSize,True,2,textScale),constructComponentBox('slot6',largeBoxSize,True,2,textScale)],
            [constructComponentBox('slot3',largeBoxSize,True,2,textScale),constructComponentBox('slot5',largeBoxSize,True,2,textScale),constructComponentBox('slot7',largeBoxSize,True,2,textScale)]
        ]

        Layout = [
            [sg.Menu(menu_def)],
            [sg.Frame('',leftFrame,border_width=0,p=0,background_color=bgColor),sg.Frame('',rightFrame,border_width=0,p=0,background_color=bgColor)],
        ]

    elif scale == 'large':

        textScale = 10
        boxWidth = 215
        boxHeight = 240

        summaryBoxSize = (3*boxWidth + 4*elementPadding, boxHeight)
        largeBoxSize = (boxWidth, boxHeight)
        smallBoxSizeA = (boxWidth, boxHeight/2+13)
        smallBoxSizeB = (boxWidth, boxHeight/2-4)
        smallBoxSizeD = (boxWidth, boxHeight/2-19)

        leftFrame = [
            [constructLoadoutSummary(summaryBoxSize,textScale)],
            [constructComponentBox('engine',largeBoxSize,True,1,textScale),constructComponentBox('booster',largeBoxSize,True,1,textScale),constructComponentBox('slot0',largeBoxSize,True,2,textScale)],
            [constructComponentBox('shield',largeBoxSize,True,1,textScale),sg.Frame('',[[constructComponentBox('frontarmor',smallBoxSizeB,False,1,textScale)],[constructComponentBox('reararmor',smallBoxSizeB,False,1,textScale)]],border_width=0,p=0,background_color=bgColor),constructComponentBox('slot1',largeBoxSize,True,2,textScale)]
        ]
    
        rightFrame = [
            [constructFCProgramSelector(largeBoxSize,textScale),
            sg.Frame('',[[constructComponentBox('reactor',smallBoxSizeD,False,1,textScale)],[constructComponentBox('droidinterface',smallBoxSizeA,True,1,textScale)]],border_width=0,p=0,background_color=bgColor),
            sg.Frame('',[[constructComponentBox('cargohold',smallBoxSizeD,False,1,textScale)],[constructComponentBox('capacitor',smallBoxSizeA,True,1,textScale)]],border_width=0,p=0,background_color=bgColor)],
            [constructComponentBox('slot2',largeBoxSize,True,2,textScale),constructComponentBox('slot4',largeBoxSize,True,2,textScale),constructComponentBox('slot6',largeBoxSize,True,2,textScale)],
            [constructComponentBox('slot3',largeBoxSize,True,2,textScale),constructComponentBox('slot5',largeBoxSize,True,2,textScale),constructComponentBox('slot7',largeBoxSize,True,2,textScale)]
        ]

        Layout = [
            [sg.Menu(menu_def,background_color=bgColor,text_color=textColor)],
            [sg.Frame('',leftFrame,border_width=0,p=0,background_color=bgColor),sg.Frame('',rightFrame,border_width=0,p=0,background_color=bgColor)],
        ]

    else:
        pass
    
    loadoutTool = sg.Window("Seraph's Loadout Tool V" + currentVersion,Layout, finalize=True, background_color=bgColor, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), margins=(elementPadding, elementPadding), enable_close_attempted_event=True, resizable=False, metadata=scale)

    return loadoutTool

def applyBindings(window):

    window.bind('<Escape>','test')