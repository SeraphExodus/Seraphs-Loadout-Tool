import ctypes
import FreeSimpleGUI as sg
import json
import loadouttoolmethods as slt
import os

from win32gui import FindWindow, GetWindowRect

currentVersion = '2.18.0'

versionURL = "https://gist.github.com/SeraphExodus/8ae0b6980e3780e8782847dbe76b0bf5/raw"

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
displayScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)/100 #may just be able to ignore this since screensize yields effective monitor resolution

dir = os.path.join(os.path.dirname(__file__)) + '\\'

with open(os.path.abspath(dir + 'data.json')) as jsonData:
    data = json.load(jsonData)

defaultSize = [1024,768]


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

slt.savedataToJSON()

def move_center(window):
    screen_width, screen_height = window.get_screen_dimensions()
    win_width, win_height = window.size
    screen_height -= 100
    x, y = (screen_width - win_width)//2, (screen_height - win_height)//2
    window.move(x, y)

def getCurrentArea(windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin):
    appWindow = FindWindow(None, "Seraph's Loadout Tool V" + currentVersion)
    rect = GetWindowRect(appWindow)
    xDim = rect[2]-rect[0] - windowFrameSideMargin * 2
    yDim = rect[3]-rect[1] - windowFrameTopMargin - windowFrameBottomMargin
    windowArea = xDim * yDim

    return xDim, yDim, rect, windowArea

def move_resize(window, rect, newRect, windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin): 

    xDim = newRect[2]-newRect[0] - 2*windowFrameSideMargin
    yDim = newRect[3]-newRect[1] - windowFrameBottomMargin - windowFrameTopMargin

    if xDim < defaultSize[0]:
        xDim = defaultSize[0]
    if yDim < defaultSize[1]:
        yDim = defaultSize[1]

    sameCoords = [False] * 4
    for i in range(4):
        if newRect[i] == rect[i]:
            sameCoords[i] = True
    #knowing which two (or three) edges haven't moved allows us to determine which corner to keep static when resizing, according to a hierarchy. Top-left > Bottom-left > Top-right > Bottom-right
    if all(sameCoords[0:2]): #top-left hasn't moved
        window.move(rect[0],rect[1])
    elif all([sameCoords[0],sameCoords[3]]): #bottom-left hasn't moved
        window.move(rect[0],rect[3] - defaultSize[1] - windowFrameBottomMargin - windowFrameTopMargin)
    elif all(sameCoords[1:3]): #top-right hasn't moved
        window.move(rect[2] - defaultSize[0] - 2*windowFrameSideMargin, rect[1])
    elif all(sameCoords[2:4]): #bottom-right hasn't moved
        window.move(rect[2] - defaultSize[0] - 2*windowFrameSideMargin, rect[3] - defaultSize[1] - windowFrameBottomMargin - windowFrameTopMargin)
    window.set_size([xDim, yDim]) #FYI this method doesn't like floats. Make sure inputs are ints.

Layout = [[]]

window = sg.Window("Seraph's Loadout Tool V" + currentVersion,Layout, finalize=True, background_color=bgColor, icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')), margins=(elementPadding, elementPadding), enable_close_attempted_event=True, size=(defaultSize[0],defaultSize[1]), resizable=True)
move_center(window)

window.bind('<Configure>','Resize')

#Element Size and Scaling Configuration

appWindow = FindWindow(None, "Seraph's Loadout Tool V" + currentVersion)
rect = GetWindowRect(appWindow)

windowFrameSideMargin = int((rect[2]-rect[0]-defaultSize[0]) / 2)
windowFrameBottomMargin = windowFrameSideMargin
windowFrameTopMargin = rect[3]-rect[1]-defaultSize[1]-windowFrameBottomMargin

xDim, yDim, rect, windowArea = getCurrentArea(windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSE_ATTEMPTED_EVENT:
        break

    if event == 'Resize':
        newXDim, newYDim, newRect, newArea = getCurrentArea(windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin) #check new area
        if newXDim < defaultSize[0] or newYDim < defaultSize[1]:
            move_resize(window,rect,newRect, windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin)
        else:
            xDim, yDim, rect, windowArea = getCurrentArea(windowFrameSideMargin, windowFrameTopMargin, windowFrameBottomMargin)

window.close()