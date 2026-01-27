import pydirectinput as pdi

from pynput.mouse import Listener, Button

pCount = 0
toggleMode = 1

print("--------")

def setPlayerCount(pCount):
    pCount = str(pCount)
    pdi.keyDown('ctrl')
    pdi.keyDown('shift')
    pdi.keyDown('f' + pCount)
    pdi.keyUp('ctrl')
    pdi.keyUp('shift')
    pdi.keyUp('f' + pCount)
    pdi.keyUp('shift')
    print(f"Player count set to {pCount}")

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
            print("1-8 Mode")
            toggleMode = 1
        else:
            print("1-3-5-8 Mode")
            toggleMode = 0

print("Running")
if toggleMode == 1:
    print("1-8 Mode")
else:
    print("1-3-5-8 Mode")

# Initialize the Listener to monitor mouse clicks
with Listener(on_click=on_click) as listener:
    listener.join()