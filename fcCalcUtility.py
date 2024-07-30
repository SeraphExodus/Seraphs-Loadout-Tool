import FreeSimpleGUI as sg
import numpy as np
import os
import sqlite3

from buildTables import buildTables

def fcCalc():
    if not os.path.exists("Data\\tables.db"):
        buildTables()

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