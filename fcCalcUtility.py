import FreeSimpleGUI as sg
import numpy as np
import os
import sqlite3

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
compBoxWidth = 215
rightPaneWidth = 250
topRowHeight = 160
row1Height = 210
row2Height = 240
row3Height = 240

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

def listify(input):
    
    output = []

    for i in range(0,12):
        newLine = []
        for j in range(0,len(input)):
            newLine.append(input[j][i])
        output.append(newLine)
    return output

def fcCalc():
    if not os.path.exists("Data\\tables.db"):
        buildTables()

    db = sqlite3.connect("file:Data\\tables.db?mode=ro", uri=True)
    cur = db.cursor()

    programs = listify(cur.execute("SELECT * FROM fcprogram").fetchall())
    programNames = programs[1]

    visibleCount = 5

    frames = []

    for i in range(0,15):
        if i > visibleCount-1:
            isVisible=False
        else:
            isVisible=True

        newFrame = [
            [sg.Text("",font=baseFont,p=3,key='order'+str(i),visible=isVisible),sg.Checkbox('',key='checkbox'+str(i),p=1,disabled=True,visible=isVisible),sg.Combo(programNames,key='list'+str(i),font=baseFont,readonly=True,s=(50,20),visible=isVisible,enable_events=True),sg.Button('-',key='minus'+str(i),font=("Roboto",8),visible=isVisible,s=2)]
        ]
        frames.append([sg.Frame('',newFrame,border_width=0)])
    Layout = [
        [sg.Push(),sg.Button('+',font=buttonFont,s=2),sg.Button('-',font=buttonFont,s=2),sg.Push()],
        [frames]
        ]

    window = sg.Window('Flight Computer Calculator', Layout, modal=True, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')))
    while True:
        event, values = window.read()
        if event == '+' and visibleCount <= 14:
            window['order' + str(visibleCount)].update(visible=True)
            window['checkbox' + str(visibleCount)].update(visible=True)
            window['list' + str(visibleCount)].update(visible=True)
            window['minus' + str(visibleCount)].update(visible=True)
            visibleCount += 1

        if event == '-' and visibleCount >= 2:
            window['order' + str(visibleCount-1)].update(visible=False)
            window['list' + str(visibleCount-1)].update(visible=False)
            window['checkbox' + str(visibleCount-1)].update(visible=False)
            window['minus' + str(visibleCount-1)].update(visible=False)
            visibleCount -= 1
        
        try:
            if 'list' in event:
                window['checkbox'+event[-1]].update(disabled=False)
        except:
            pass

        if event == "Exit" or event == sg.WIN_CLOSED:
            break

    window.close()

fcCalc()