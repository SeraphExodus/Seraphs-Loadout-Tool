import pydirectinput as pdi
import time

from pynput.mouse import Listener, Button

pCount = 0
toggleMode = 0

def setPlayerCount(pCount):
    pCount = str(pCount)
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.keyDown('f' + pCount)
    pdi.keyUp('ctrl')
    pdi.keyUp('shift')
    pdi.keyUp('f' + pCount)

# Function called on a mouse click
def on_click(x, y, button, pressed):
    global pCount
    global toggleMode
    if pressed and button == Button.x2:
        if toggleMode == 0:
            if pCount == 0:
                setPlayerCount(1)
                pCount = 1
            elif pCount == 1:
                setPlayerCount(3)
                pCount = 3
            elif pCount == 3:
                setPlayerCount(5)
                pCount = 5
            elif pCount == 5:
                setPlayerCount(8)
                pCount = 8
        else:
            setPlayerCount(8)
            pCount = 8
    if pressed and button == Button.x1:
        if toggleMode == 0:
            if pCount == 0:
                setPlayerCount(1)
                pCount = 1
            elif pCount == 8:
                setPlayerCount(5)
                pCount = 5
            elif pCount == 5:
                setPlayerCount(3)
                pCount = 3
            elif pCount == 3:
                setPlayerCount(1)
                pCount = 1
        else:
            setPlayerCount(1)
            pCount = 1
    if pressed and button == Button.middle:
        if toggleMode == 0:
            toggleMode = 1
        else:
            toggleMode = 0

# Initialize the Listener to monitor mouse clicks
with Listener(on_click=on_click) as listener:
    listener.join()