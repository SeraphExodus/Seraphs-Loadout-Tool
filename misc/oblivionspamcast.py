import pydirectinput as pdi
import time

from win32gui import GetWindowText, GetForegroundWindow

while True:
    if "Oblivion" in GetWindowText(GetForegroundWindow()):
        pdi.keyDown('c')