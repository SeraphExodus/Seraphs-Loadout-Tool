import ctypes
import FreeSimpleGUI as sg
import jellyfish
import loadouttoolmethods as slt
import multiprocessing
import multiprocessing.popen_spawn_win32 as forking
import json
import numpy as np
import os
import pytesseract
import shutil
import sqlite3
import sys
import win32clipboard

from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageGrab, ImageStat
from requests import get
from webbrowser import open as browserOpen
from win32gui import FindWindow, GetWindowRect

currentVersion = '2.20.0'

versionURL = "https://gist.github.com/SeraphExodus/8ae0b6980e3780e8782847dbe76b0bf5/raw"

user32 = ctypes.windll.user32
screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
displayScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)/100 #may just be able to ignore this since screensize yields effective monitor resolution

dir = os.path.join(os.path.dirname(__file__)) + '\\'

with open(os.path.abspath(dir + 'data.json')) as jsonData:
    data = json.load(jsonData)

window_concise = [1024,768]
window_verbose = [1440,1080]

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