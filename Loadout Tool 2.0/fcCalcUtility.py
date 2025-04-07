import FreeSimpleGUI as sg
import os
import sqlite3
import win32clipboard

from datetime import datetime, timedelta

from buildCompList import buildComponentList
from buildTables import buildTables

headerFont = ("Roboto", 12, "bold")
summaryFont = ("Roboto", 11, "bold")
summaryFontStats = ("Roboto", 11)
baseFont = ("Roboto", 10, "bold")
baseFontStats = ("Roboto", 10, "bold")
buttonFont = ("Roboto", 13, "bold")
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

def remodalize(window):
    try:
        window.TKroot.grab_set()
    except:
        pass

def listify(x):
    xnew = []
    for i in x:
        xnew.append(i[0])
    return xnew

def listifyPrograms(input):
    
    output = []

    for i in range(0,16):
        newLine = []
        for j in range(0,len(input)):
            newLine.append(input[j][i])
        output.append(newLine)
    return output

def tryFloat(x):
    try:
        return float(x)
    except:
        return 0
    
def floor(x):
    try:
        y = round(x-0.5)
        return y
    except:
        SyntaxError
    
def toClipboard(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()

def alert(headerText, textLines, buttons, timeout, *settings):
    Layout = []

    try:
        textSettings = settings[0]
        dimensions = settings[1]
    except:
        textSettings = []
        dimensions = []

    if len(textLines) > 0:
        for i in range(0,len(textLines)):
            try:
                textFont = textSettings[0][i]
            except:
                textFont = summaryFont
            try:
                textJust = textSettings[0][i]
            except:
                textJust = 'center'
            
            Line = sg.Text(textLines[i],font=textFont, p=fontPadding)
            if textJust == 'left':
                Layout.append([Line,sg.Push()])
            elif textJust == 'right':
                Layout.append([sg.Push(),Line])
            else:
                Layout.append([sg.Push(),Line,sg.Push()])

    if len(dimensions) == 2 and 0 not in dimensions:
        Layout = [
            [sg.Frame('',[[sg.VPush()],Layout[0],[sg.VPush()]],size=(dimensions[0],dimensions[1]),border_width=0)]
        ]

    buttonList = [sg.Push(),sg.Push()]
    if len(buttons) > 0:
        for i in buttons:
            buttonList.append(sg.Button(i,font=buttonFont, button_color=bgColor))
            buttonList.append(sg.Push())
        buttonList.append(sg.Push())
        Layout.append(buttonList)

    alertWindow = sg.Window(headerText,Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), )

    if timeout > 0:
        startTime = datetime.now()
        currTime = startTime
        while currTime < startTime + timedelta(seconds=timeout):
            event, values = alertWindow.read(timeout=10)
            if event in buttons or event == sg.WIN_CLOSED:
                alertWindow.close()
                return event
            currTime = datetime.now()
        alertWindow.close()
        return
    
    while True:
        event, values = alertWindow.read()
        if event in buttons or event == sg.WIN_CLOSED:
            alertWindow.close()
            return event
    
def updateOrder(window,programNames,slashCommand):
    event, values = window.read(timeout=0)
    macroList = []
    for i in range(0,15):
        checkCount = 1
        for j in range(0,i):
            if values['checkbox' + str(j)] == True:
                checkCount += 1
        if values['checkbox' + str(i)] == True:
            window['order' + str(i)].update(checkCount)
            macroList += ['/droid ' + slashCommand[programNames.index(values['list'+str(i)])] + ';'] + ['/pause ' + window['cooldown' + str(i)].get().split(' ')[0] + ';']
        else:
            window['order' + str(i)].update('')
    window.refresh()
    return macroList

def updateMemory(window,programNames,memory):
    event, values = window.read(timeout=0)
    totalMemoryUsage = 0
    for i in range(0,15):
        try:
            progMemory = int(memory[programNames.index(values['list'+str(i)])])
            window['memory'+str(i)].update(progMemory)
            totalMemoryUsage+= progMemory
        except:
            window['memory'+str(i)].update('')
    fcLevelList = ['None','1','2','3','4','5','6']
    fcMemoryList = [0,20,40,70,110,125,150]
    fcLevel = window['fclevel'].get()
    fcMemory = fcMemoryList[fcLevelList.index(fcLevel)]
    if totalMemoryUsage > fcMemory:
        newColor = '#dd0000'
    else:
        newColor = textColor
    window['memoryutilization'].update(str(totalMemoryUsage) + ' / ' + str(fcMemory), text_color = newColor)
    window.refresh()

def updateCooldown(window,programNames,cooldown): 
    event, values = window.read(timeout=0)

    for i in range(0,15):
        try:
            if values['dcs'] == 0 or values['dcs'] == '':
                dcs = 0
            else:
                dcs = tryFloat(values['dcs'])

            baseDelay = tryFloat(cooldown[programNames.index(values['list'+str(i)])])

            if baseDelay == 0:
                cd = int(0)
            else:
                cd = int(floor(dcs * baseDelay + 1))
            window['cooldown'+str(i)].update(str(cd) + ' s')
        except:
            window['cooldown'+str(i)].update('')
    window.refresh()

def updateEnables(window):
    event, values = window.read(timeout=0)
    progCount = 0
    for i in range(0,15):
        if values['list' + str(i)] != '':
            progCount += 1
    for i in range(0,15):
        if i <= progCount - 1:
            window['checkbox' + str(i)].update(disabled=False)
            window['moveup' + str(i)].update(disabled=False)
            window['movedown' + str(i)].update(disabled=False)
            window['minus' + str(i)].update(disabled=False)
            window['effects' + str(i)].update(disabled=False)
        else:
            window['checkbox' + str(i)].update(False, disabled=True)
            window['moveup' + str(i)].update(disabled=True)
            window['movedown' + str(i)].update(disabled=True)
            window['minus' + str(i)].update(disabled=True)
            window['effects' + str(i)].update(disabled=True)
        if i <= progCount:
            window['list' + str(i)].update(disabled=False)
        else:
            window['list' + str(i)].update(disabled=True)
    window.refresh()

def newFCLoadout():
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    columnString = ''

    for i in range(0,15):
        columnString += 'prog' + str(i) + ', '

    for i in range(0,15):
        columnString += 'incl' + str(i) + ', '
    columnString = columnString[:-2]

    cur2.execute("CREATE TABLE IF NOT EXISTS fcloadout (name UNIQUE, fclevel, dcs, " + columnString + ")")

    textColumn = [
        [sg.Push(),sg.Text("Name:",font=baseFont,p=3)],
        [sg.Push(),sg.Text("FC Level:",font=baseFont,p=3)],
    ]

    inputColumn = [
        [sg.Input(p=2,font=summaryFont,s=30,key='fcname'),sg.Push()],
        [sg.Combo(values=[6,5,4,3,2,1],s=(6,7),p=2,font=summaryFont,readonly=True,key='fclevel'),sg.Push()]
    ]

    Layout = [
        [sg.Push(),sg.Text("New Flight Computer",font=headerFont,p=0),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',textColumn,border_width=0,p=elementPadding),sg.Frame('',inputColumn,border_width=0,p=elementPadding),sg.Push()],
        [sg.VPush()],
        [sg.Push(),sg.Button("Create",font=buttonFont,button_color=bgColor), sg.Push(), sg.Button("Cancel",font=buttonFont,button_color=bgColor),sg.Push()]
    ]

    newFCWindow = sg.Window("Create New Flight Computer",Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True, size=(400,200))

    fcName = ''
    fcLevel = ''

    while True:
        event, values = newFCWindow.read()

        if event == 'Create':
            try:
                nameList = list(cur2.execute("SELECT name FROM fcloadout").fetchall()[0])
            except:
                nameList = []
            name = values['fcname']
            if values['fcname'] == '' or values['fclevel'] == '':
                alert('Error',['Error: You must enter a name and select an FC Level.'],['Okay'],0)
                remodalize(newFCWindow)
            else:
                if name in nameList:
                    out = alert('Alert',['','A Flight Computer loadout with this name already exists. Do you wish to overwrite it?',''],['Proceed','Cancel'],0)
                    remodalize(newFCWindow)
                    if out == 'Proceed':
                        bindings = '?, ' * 33
                        bindings = bindings[:-2]
                        cur2.execute("INSERT OR REPLACE INTO fcloadout VALUES(" + bindings + ")",[values['fcname'],values['fclevel']] + [''] * 31)
                        fcName = values['fcname']
                        fcLevel = values['fclevel']
                        break
                else:
                    bindings = '?, ' * 33
                    bindings = bindings[:-2]
                    cur2.execute("INSERT OR REPLACE INTO fcloadout VALUES(" + bindings + ")",[values['fcname'],values['fclevel']] + [''] * 31)
                    fcName = values['fcname']
                    fcLevel = values['fclevel']
                    break
            
        if event == 'Cancel' or event == sg.WIN_CLOSED:
            break

    compdb.commit()
    compdb.close()
    newFCWindow.close()

    return fcName, fcLevel

def saveFCLoadout(window):
    event, values = window.read(timeout=0)

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    name = window['fcname'].get()
    level = window['fclevel'].get()
    dcs = values['dcs']

    saveData = [name, level, dcs]

    for i in range(0,15):
        saveData.append(values['list' + str(i)])
    for i in range(0,15):
        saveData.append(values['checkbox' + str(i)])
    
    cur2.execute("INSERT OR REPLACE INTO fcloadout VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",saveData)
    alert("",['Save Successful!'],[],3)
    remodalize(window)

    compdb.commit()
    compdb.close()

def loadFCLoadout(window):
    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()
    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    fcList = listify(cur2.execute("SELECT name FROM fcloadout ORDER BY name ASC").fetchall())

    leftCol = [
        [sg.Push(),sg.Text("Select a Flight Computer", font=headerFont,p=fontPadding),sg.Push()],
        [sg.Listbox(values=fcList, size=(30, 27), enable_events=True, key='fcname', font=baseFont, select_mode="single", justification='center')]
    ]

    rightColTopLeft = [
        [sg.Push(),sg.Text('',font=baseFont,p=fontPadding, key='nametext')],
        [sg.Push(),sg.Text('',font=baseFont,p=fontPadding, key='leveltext')],
        [sg.Push(),sg.Text('',font=baseFont,p=fontPadding, key='memorytext')],
    ]

    rightColTopRight = [
        [sg.Text("",key='fcnamepreview',font=baseFont,p=fontPadding),sg.Push()],
        [sg.Text("",key='fclevel',font=baseFont,p=fontPadding),sg.Push()],
        [sg.Text("",key='memoryutilization',font=baseFont,p=fontPadding),sg.Push()],
    ]

    rightColBottom = [
        [sg.Push(),sg.Text("", key='programsheadertext', font=baseFont, p=fontPadding),sg.Push()],
    ]

    for i in range(0,15):
        rightColBottom.append([sg.Text("", font=baseFont, key='text'+str(i), p=fontPadding),sg.Push()])

    rightCol = [
        [sg.Push(),sg.Text("FC Preview", font=headerFont, p=fontPadding),sg.Push()],
        [sg.Push(),sg.Frame('',rightColTopLeft,border_width=0,p=elementPadding,s=(132,75)),sg.Frame('',rightColTopRight,border_width=0,p=elementPadding,s=(132,75)),sg.Push()],
        [sg.Push(),sg.Frame('',rightColBottom,border_width=0,p=elementPadding,s=(292,392)),sg.Push()]
    ]

    Layout = [
        [sg.Frame('',leftCol,border_width=0,p=elementPadding,s=(250,475),element_justification='center'),sg.Frame('',rightCol,border_width=0,p=elementPadding,s=(300,475))],
        [sg.Push(),sg.Button("Load",font=buttonFont),sg.Push(),sg.Button("Delete",font=buttonFont),sg.Push(),sg.Button("Cancel",font=buttonFont),sg.Push()]
    ]

    loadFCWindow = sg.Window("Load and Manage FC Loadouts", Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))

    loaded = False

    while True:
        event, values = loadFCWindow.read()
        try:
            if event == 'fcname':
                progString = ''
                for i in range(0,15):
                    progString += 'prog' + str(i) + ','
                progString = progString[:-1]
                programs = list(cur2.execute("SELECT " + progString + " FROM fcloadout WHERE name = ?",values['fcname']).fetchall()[0])
                loadFCWindow['nametext'].update('Name:')
                loadFCWindow['leveltext'].update('Level:')
                loadFCWindow['memorytext'].update('Memory:')
                loadFCWindow['fcnamepreview'].update(values['fcname'][0])
                loadFCWindow['fclevel'].update(cur2.execute("SELECT fclevel FROM fcloadout WHERE name = ?",values['fcname']).fetchall()[0][0])
                memoryTotal = 0
                for i in range(0, 15):
                    loadFCWindow['text' + str(i)].update(programs[i])
                    try:
                        memoryTotal += int(cur.execute("SELECT size FROM fcprogram WHERE name = ?",[programs[i]]).fetchall()[0][0])
                    except:
                        pass
            
                if memoryTotal != 0:
                    loadFCWindow['programsheadertext'].update("Programs")
                else:
                    loadFCWindow['programsheadertext'].update("")

                fcMemoryList = ['0', '20', '40', '70', '110', '125', '150']
                fcLevelList = ['None', '1', '2', '3', '4', '5', '6']
                try:
                    fcMaxMemory = fcMemoryList[fcLevelList.index(cur2.execute("SELECT fclevel FROM fcloadout WHERE name = ?",values['fcname']).fetchall()[0][0])]
                except:
                    fcMaxMemory = '0'
                loadFCWindow['memoryutilization'].update(str(memoryTotal) + ' of ' + fcMaxMemory)
        except:
            pass

        if event == 'Load':
            try:
                fcLoadout = list(cur2.execute("SELECT * FROM fcloadout WHERE name = ?",values['fcname']).fetchall()[0])
                window['fcname'].update(fcLoadout[0])
                window['fclevel'].update(fcLoadout[1])
                window['dcs'].update(fcLoadout[2])
                for i in range(0,15):
                    window['list' + str(i)].update(fcLoadout[i+3])
                    window['checkbox' + str(i)].update(fcLoadout[i+18])
                window.refresh()
                loaded = True
                break
            except:
                alert('',['Select a flight computer to load.'],[],3)
                remodalize(loadFCWindow)

        if event == 'Delete':
            if values['fcname'] == '':
                alert('Error',['Error: Select a flight computer.'],[],3)
                remodalize(loadFCWindow)
            else:
                result = alert('Alert',["You are attempting to delete the flight computer loadout named '" + values['fcname'][0] + ".'", 'This action cannot be undone. Do you wish to continue?'],['Proceed','Cancel'],0)
                remodalize(loadFCWindow)
                if result == 'Proceed':
                    cur2.execute("DELETE FROM fcloadout WHERE name = ?",values['fcname'])
                    loadFCWindow['nametext'].update('')
                    loadFCWindow['leveltext'].update('')
                    loadFCWindow['memorytext'].update('')
                    loadFCWindow['fcnamepreview'].update('')
                    loadFCWindow['fclevel'].update('')
                    loadFCWindow['programsheadertext'].update('')
                    loadFCWindow['memoryutilization'].update('')
                    for i in range(0, 15):
                        loadFCWindow['text' + str(i)].update('')
                    fcList = listify(cur2.execute("SELECT name FROM fcloadout ORDER BY name ASC").fetchall())
                    loadFCWindow['fcname'].update(values=fcList)
                    loadFCWindow.refresh()


        if event == sg.WIN_CLOSED or event == 'Cancel':
            break

    loadFCWindow.close()
    compdb.commit()
    compdb.close()
    db.close()
    return loaded

def updateMacroButton(window):
    event, values = window.read(timeout=0)
    filledCount = 0
    for i in range(0,15):
        if values['checkbox' + str(i)] != False:
            filledCount += 1
    if filledCount > 0:
        return '&Copy Macro'
    else:
        return '!&Copy Macro'

def setMenu(saveLock, openLock, macroLock):
    menu_def = [
        ['&Flight Computer', ['&New FC Loadout', openLock, saveLock, 'E&xit']],
        ['&Macro', [macroLock]],
        ['&Help', ['&Keyboard Shortcuts']]
    ]
    return menu_def

def fcCalc(*dcs):
    if not os.path.exists("Data\\tables.db"):
        buildTables('null')
    if not os.path.exists("Data\\savedata.db"):
        buildComponentList()

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

    programs = listifyPrograms(cur.execute("SELECT * FROM fcprogram").fetchall())
    slashCommand = programs[0]
    programNames = programs[1]
    memory = programs[2]
    cooldown = programs[4]

    orderColumn = [[sg.Push(),sg.Text("Macro",font=summaryFont,p=0),sg.Push()]]
    listColumn = [[sg.Push(),sg.Push(),sg.Text("Select Programs",font=summaryFont,p=0),sg.Push(),sg.Push(),sg.Push()]]
    memoryColumn = [[sg.Push(),sg.Text("Memory",font=summaryFont,p=0),sg.Push()]]
    cooldownColumn = [[sg.Push(),sg.Text("Cooldown",font=summaryFont,p=0),sg.Push()]]

    for i in range(0,15):

        orderColumn.append([sg.Text("",font=baseFont,p=0,key='order'+str(i),s=2,justification='right'),sg.Checkbox('',key='checkbox'+str(i),p=(0,1),disabled=True,enable_events=True,font=baseFont)])
        listColumn.append([sg.Combo(programNames,key='list'+str(i),font=baseFont,readonly=True,s=(42,20),disabled=True,enable_events=True),sg.Button('▲',key='moveup'+str(i),font=("Roboto",8),disabled=True,s=2,p=(1,0),border_width=0),sg.Button('▼',key='movedown'+str(i),font=("Roboto",8),disabled=True,s=2,p=(1,0),border_width=0),sg.Button('-',key='minus'+str(i),font=("Roboto",8,"bold"),disabled=True,s=2,p=(5,0),border_width=0),sg.Button('?',key='effects'+str(i),font=("Roboto",8,"bold"),disabled=True,s=2,p=(5,0),border_width=0)])
        memoryColumn.append([sg.Push(),sg.Text("",key='memory'+str(i),font=baseFont),sg.Push()])
        cooldownColumn.append([sg.Push(),sg.Text("",key='cooldown'+str(i),font=baseFont),sg.Push()])

    topBoxFrameLeft = [
        [sg.Push(),sg.Text("Flight Computer Name:",font=summaryFont,p=2)],
        [sg.Push(),sg.Text("Flight Computer Level:",font=summaryFont,p=2)],
        [sg.Push(),sg.Text("Memory Utilization:",p=2,font=summaryFont)],
        [sg.Push(),sg.Text("Droid Command Speed:",font=summaryFont,p=2)]
    ]
    try:
        if tryFloat(dcs[0]) > 0:
            defaultDCS = tryFloat(dcs[0])
        else:
            defaultDCS = ''
    except:
        defaultDCS = ''

    topBoxFrameRight = [
        [sg.Text("",p=2,key='fcname',font=summaryFont,justification='center'),sg.Push()],
        [sg.Text("",p=2,key='fclevel',font=summaryFont,s=9,justification='center'),sg.Push()],
        [sg.Text("0 / 0",key='memoryutilization',p=2,font=summaryFont,s=9,justification='center'),sg.Push()],
        [sg.Input(default_text=defaultDCS,p=2,font=summaryFont,s=10,key='dcs',justification='center',disabled=True, disabled_readonly_background_color=boxColor,disabled_readonly_text_color=textColor),sg.Push()]
    ]

    compdb = sqlite3.connect("file:Data\\savedata.db?mode=rw", uri=True)
    cur2 = compdb.cursor()

    try:
        saved = cur2.execute("SELECT name FROM fcloadout").fetchall()
    except:
        saved = []

    if len(saved) > 0:
        openLock = '&Open FC Loadout'
    else:
        openLock = '!&Open FC Loadout'

    saveLock = '!&Save FC Loadout'
    macroLock = '!&Copy Macro'

    menu_def = [
        ['&Flight Computer', ['&New FC Loadout', openLock, saveLock, 'E&xit']],
        ['&Macro', [macroLock]],
        ['&Help', ['&Keyboard Shortcuts']]
    ]

    Layout = [
        [sg.Menu(menu_def, key='menu', text_color='#000000', disabled_text_color="#999999", background_color='#ffffff')],
        [sg.Button('Push DCS',visible=False,bind_return_key=True)],
        [sg.VPush()],
        [sg.Push(),sg.Frame('',topBoxFrameLeft,border_width=0,p=0, s=(240,110)),sg.Frame('',topBoxFrameRight,border_width=0,p=0, s=(240,110)),sg.Push()],
        [sg.VPush()],
        [sg.Frame('',orderColumn,border_width=0,p=0),sg.Frame('',listColumn,border_width=0,p=0,element_justification='center'),sg.Frame('',memoryColumn,border_width=0,p=0),sg.Frame('',cooldownColumn,border_width=0,p=0)],
        [sg.VPush()]
        ]

    window = sg.Window('Flight Computer Calculator', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), size=(640,550), finalize=True)

    window.bind('<Control-c>', 'Copy Macro')
    window.bind('<Control-s>', 'Save FC Loadout')
    window.bind('<Control-o>', 'Open FC Loadout')
    window.bind('<Control-n>', 'New FC Loadout')

    while True:
        event, values = window.read()

        if event == 'New FC Loadout':
            newFCName, newFCLevel = newFCLoadout()
            remodalize(window)
            if newFCName != '':
                window['fcname'].update(newFCName)
                window['fclevel'].update(newFCLevel)
                window['dcs'].update(disabled=False)
                for i in range(0,15):
                    window['list' + str(i)].update('')
                updateEnables(window)
                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
                updateOrder(window,programNames,slashCommand)
                saveLock = '&Save FC Loadout'
                macroLock = updateMacroButton(window)
                menu_def = setMenu(saveLock, openLock, macroLock)
                window['menu'].update(menu_def)

        if event == 'Open FC Loadout':
            loaded = loadFCLoadout(window)
            remodalize(window)
            if loaded:
                window['dcs'].update(disabled=False)
                updateEnables(window)
                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
                updateOrder(window,programNames,slashCommand)
                saveLock = '&Save FC Loadout'
                macroLock = updateMacroButton(window)
                menu_def = setMenu(saveLock, openLock, macroLock)
                window['menu'].update(menu_def)

        if event == 'Save FC Loadout':
            saveFCLoadout(window)

        if event == 'Push DCS' and window.find_element_with_focus().Key == 'dcs':
            try:
                updateCooldown(window,programNames,cooldown)
                window.TKroot.focus_set()
            except:
                pass
        
        if event == 'dcs' and tryFloat(values['dcs']) == 0:
            window['dcs'].update(values['dcs'][:-1])

        if event == 'fclevel':
            updateMemory(window,programNames,memory)

        try:
            if 'list' in event:
                updateEnables(window)
                newList = programNames
                for i in range(0,15):
                    input = window['list' + str(i)].get()
                    newList = [x for x in newList if x != input]
                for i in range(0,15):
                    window['list' + str(i)].update(value = window['list' + str(i)].get(), values=newList,size=(42,20))
                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
        except:
            pass
        
        try:
            if 'checkbox' in event:
                updateOrder(window,programNames,slashCommand)
                macroLock = updateMacroButton(window)
                menu_def = setMenu(saveLock, openLock, macroLock)
                window['menu'].update(menu_def)
        except:
            pass

        try:
            if 'minus' in event:
                window['list'+str(event.split('minus')[1])].update('')
                for i in range(int(event.split('minus')[1]),14):
                    window['list' + str(i)].update(values['list' + str(i + 1)])
                    window['checkbox' + str(i)].update(values['checkbox' + str(i + 1)])
                updateEnables(window)
 
                newList = programNames
                for i in range(0,15):
                    input = window['list' + str(i)].get()
                    newList = [x for x in newList if x != input]
                for i in range(0,15):
                    window['list' + str(i)].update(value = window['list' + str(i)].get(), values=newList,size=(42,20))

                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
                updateOrder(window,programNames,slashCommand)
                macroLock = updateMacroButton(window)
                menu_def = setMenu(saveLock, openLock, macroLock)
                window['menu'].update(menu_def)
        except:
            pass

        try:
            if 'moveup' in event and not int(event.split('moveup')[1]) == 0 and not values['list' + event.split('moveup')[1]] == '':
                listTemp = window['list' + str(int(event.split('moveup')[1])-1)].get()
                cbTemp = values['checkbox' + str(int(event.split('moveup')[1])-1)]
                orderTemp = window['order' + str(int(event.split('moveup')[1])-1)].get()

                window['list' + str(int(event.split('moveup')[1])-1)].update(window['list' + str(event.split('moveup')[1])].get())
                window['checkbox' + str(int(event.split('moveup')[1])-1)].update(window['checkbox' + str(event.split('moveup')[1])].get())
                window['order' + str(int(event.split('moveup')[1])-1)].update(window['order' + str(event.split('moveup')[1])].get())

                window['list' + str(event.split('moveup')[1])].update(listTemp)
                window['checkbox' + str(event.split('moveup')[1])].update(cbTemp)
                window['order' + str(event.split('moveup')[1])].update(orderTemp)
                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
                updateOrder(window,programNames,slashCommand)
        except:
            pass

        try:
            if 'movedown' in event and not int(event.split('movedown')[1]) == 14 and not values['list' + str(int(event.split('movedown')[1]) + 1)] == '':
                listTemp = window['list' + str(int(event.split('movedown')[1])+1)].get()
                cbTemp = values['checkbox' + str(int(event.split('movedown')[1])+1)]
                orderTemp = window['order' + str(int(event.split('movedown')[1])+1)].get()

                window['list' + str(int(event.split('movedown')[1])+1)].update(window['list' + str(event.split('movedown')[1])].get())
                window['checkbox' + str(int(event.split('movedown')[1])+1)].update(window['checkbox' + str(event.split('movedown')[1])].get())
                window['order' + str(int(event.split('movedown')[1])+1)].update(window['order' + str(event.split('movedown')[1])].get())

                window['list' + str(event.split('movedown')[1])].update(listTemp)
                window['checkbox' + str(event.split('movedown')[1])].update(cbTemp)
                window['order' + str(event.split('movedown')[1])].update(orderTemp)
                updateMemory(window,programNames,memory)
                updateCooldown(window,programNames,cooldown)
                updateOrder(window,programNames,slashCommand)
        except:
            pass

        try:
            if 'effects' in event:
                target = values['list' + str(int(event.split('effects')[1]))]
                descList = []
                for i in range(1,5):
                    descList.append(cur.execute("SELECT desc" + str(i) + " FROM fcprogram WHERE name = ?",[target]).fetchall()[0][0])
                descList = ["• " + x for x in descList if x != '']
                alert("Program Effects",["Program Effects"] + [target, ""] + descList + [""],['Okay'],0,[[headerFont,baseFont,baseFont,baseFont,baseFont,baseFont,baseFont,baseFont],['center','center','center','left','left','left','left','left']],[])
        except:
            pass

        if event == "Copy Macro":
            macroList = updateOrder(window,programNames,slashCommand)
            macroText = ''
            for i in range(0,len(macroList)-1):
                macroText += macroList[i] + '\n'
            if macroText != '':
                toClipboard(macroText)
                alert("",["Macro copied to clipboard!"],[],3,[[('Roboto',24,'bold')],['center']],[250, 75])
                remodalize(window)

        if event == "Keyboard Shortcuts":
            alert("Keyboard Shortcuts",['• Ctrl+N - New FC loadout', '• Ctrl+S - Save FC loadout', '• Ctrl+O - Open FC loadout', '• Ctrl+C - Copy macro to clipboard',''],['Got it!'],0)

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    window.close()
    db.close()