import FreeSimpleGUI as sg
import numpy as np
import matplotlib as mpl
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os
import pyglet
import sqlite3

from buildTables import buildTables

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

fontList = sg.Text.fonts_installed_list()

if "Roboto" not in fontList:
    pyglet.options['win32_gdi_font'] = True
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Black.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-BlackItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Bold.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-BoldItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Italic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Light.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-LightItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Medium.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-MediumItalic.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Regular.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-Thin.ttf'))))
    pyglet.font.add_file(str(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Fonts/Roboto-ThinItalic.ttf'))))

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

fontPath = str(os.path.abspath(os.path.join(os.path.dirname(__file__)))) + '/Fonts/Roboto-Bold.ttf'
fm.fontManager.addfont(fontPath)
prop = fm.FontProperties(fname=fontPath)

mpl.rcParams['figure.facecolor'] = boxColor
mpl.rcParams['axes.facecolor'] = bgColor
mpl.rcParams['axes.labelcolor'] = '#ffffff'
mpl.rcParams['axes.titlecolor'] = '#ffffff'
mpl.rcParams['axes.edgecolor'] = '#ffffff'
mpl.rcParams['axes.xmargin'] = 0
mpl.rcParams['xtick.labelcolor'] = '#ffffff'
mpl.rcParams['ytick.labelcolor'] = '#ffffff'
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.sans-serif'] = prop.get_name()

def tryFloat(x):
    try:
        y = float(x)
        return y
    except:
        return 0

def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def delete_figure_agg(figure_agg):
    figure_agg.get_tk_widget().forget()
    plt.close('all')

def getThrottleMod(currentSpeed,maxSpeed,minThrottle,optThrottle,maxThrottle):

    currentSpeed = tryFloat(currentSpeed)
    maxSpeed = tryFloat(maxSpeed)
    minThrottle = tryFloat(minThrottle)
    optThrottle = tryFloat(optThrottle)
    maxThrottle = tryFloat(maxThrottle)

    if maxSpeed > 0:
        speedPercent = currentSpeed / maxSpeed
    else:
        speedPercent = 0

    if speedPercent < optThrottle or optThrottle >= 1:
        percentToOptimal = speedPercent / optThrottle
        throttleMod = percentToOptimal * (1 - minThrottle) + minThrottle
    else:
        percentFromOptimal = (speedPercent - optThrottle)/(1 - optThrottle)
        throttleMod = ((maxThrottle - 1) * percentFromOptimal + 1)

    throttleMod = np.floor(10*throttleMod+0.5)/10
    
    return throttleMod

def updateAxis(current, controlPosition, maxRate, accel, decel, dt):
    target = controlPosition * maxRate
    if current < target:
        current += accel * dt
        if current > target:
            current = target
    elif current > target:
        current -= decel * dt
        if current < target:
            current = target
    else:
        current = target

    return current

def transformPitch(matrix,degrees):
    rads = degrees * np.pi/180

    sine = np.sin(rads)
    cosine = np.cos(rads)

    b = matrix[0][1]
    c = matrix[0][2]
    f = matrix[1][1]
    g = matrix[1][2]
    j = matrix[2][1]
    k = matrix[2][2]

    matrix[0][1] = b * cosine + c * sine
    matrix[0][2] = b * -sine + c * cosine
    matrix[1][1] = f * cosine + g * sine
    matrix[1][2] = f * -sine + g * cosine
    matrix[2][1] = j * cosine + k * sine
    matrix[2][2] = j * -sine + k * cosine

    return matrix

def transformYaw(matrix,degrees):
    rads = degrees * np.pi/180

    sine = np.sin(rads)
    cosine = np.cos(rads)

    a = matrix[0][0]
    c = matrix[0][2]
    e = matrix[1][0]
    g = matrix[1][2]
    i = matrix[2][0]
    k = matrix[2][2]

    matrix[0][0] = a * cosine + c * -sine
    matrix[0][2] = a * sine + c * cosine
    matrix[1][0] = e * cosine + g * -sine
    matrix[1][2] = e * sine + g * cosine
    matrix[2][0] = i * cosine + k * -sine
    matrix[2][2] = i * sine + k * cosine

    return matrix

def transformRoll(matrix,degrees):
    rads = degrees * np.pi/180

    sine = np.sin(rads)
    cosine = np.cos(rads)

    a = matrix[0][0]
    b = matrix[0][1]
    e = matrix[1][0]
    f = matrix[1][1]
    i = matrix[2][0]
    j = matrix[2][1]

    matrix[0][0] = a * cosine + b * sine
    matrix[0][1] = a * -sine + b * cosine
    matrix[1][0] = e * cosine + f * sine
    matrix[1][1] = e * -sine + f * cosine
    matrix[2][0] = i * cosine + j * sine
    matrix[2][1] = i * -sine + j * cosine

    return matrix

def modelFlightPath(flightSimWindow):
    event, values = flightSimWindow.read(timeout=0)

    inputs = [flightSimWindow['chassisstat' + str(x)].get() for x in range(1,12)] + [values['enginestat' + str(x)] for x in range(1,6)] + [values['throttlesetting' + str(x)] for x in range(1,5)] + [values['simsetting' + str(x)] for x in range(1,3)]
    inputs = [tryFloat(x) for x in inputs]

    if inputs[15] != 'None':
        overloadModifier = 1 + int(inputs[15])/10
    else:
        overloadModifier = 1

    accel = inputs[0] * overloadModifier
    decel = inputs[1] * overloadModifier
    pitchAccel = inputs[2] * overloadModifier
    yawAccel = inputs[3] * overloadModifier
    rollAccel = inputs[4] * overloadModifier

    if inputs[6] in [0, '', 'N/A']: #just in case. Should be 0 for 'N/A' though
        speedMod = inputs[5]
    else:
        speedMod = inputs[6]

    maxSpeed = inputs[11] * overloadModifier * speedMod
    maxPitch = inputs[12] * overloadModifier
    maxYaw = inputs[13] * overloadModifier
    maxRoll = inputs[14] * overloadModifier

    throttleSetting = inputs[16]
    pitchSetting = inputs[17]
    yawSetting = inputs[18]
    rollSetting = inputs[19]

    slideMod = inputs[10]

    x = [0]
    y = [0]
    z = [0]

    pitch = [0]
    yaw = [0]
    roll = [0]

    speed = maxSpeed * throttleSetting #initial speed = throttle set speed
    speed = 0
    speedOut = [speed]

    accelOut = [0]

    rotationMatrix = [
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
    ]

    kx = [rotationMatrix[0][2]]
    ky = [rotationMatrix[1][2]]
    kz = [rotationMatrix[2][2]]

    Vx = [speed * kx[0]]
    Vy = [speed * ky[0]]
    Vz = [speed * kz[0]]

    Ax = [0]
    Ay = [0]
    Az = [0]

    t = [0]
    theta = [0]

    dt = 1/inputs[20]
    steps = int(inputs[20]*inputs[21])+1


    for i in range(0,steps):
        t.append(i * dt)

        rotationModifier = getThrottleMod(speedOut[-1],maxSpeed,inputs[7],inputs[8],inputs[9])
        
        pitch.append(updateAxis(pitch[-1],pitchSetting,maxPitch*rotationModifier,pitchAccel,pitchAccel,dt))
        yaw.append(updateAxis(yaw[-1],yawSetting,maxYaw*rotationModifier,yawAccel,yawAccel,dt))
        roll.append(updateAxis(roll[-1],rollSetting,maxRoll,rollAccel,rollAccel,dt)) #roll isn't actually affected by throttle. See: src/engine/server/library/serverGame/src/shared/object/ShipObject_Components.cpp L2292
        speed = updateAxis(speed,throttleSetting,maxSpeed,accel,decel,dt) #speed is independent from velocity, it just coerces it towards a certain target value <- but does this really make sense?
        #the speed problem arises because we're essentially multiplying by dt twice when actually accelerating the ship. This makes the acceleration due to updateaxis basically negligible.

        rotationMatrix = transformYaw(rotationMatrix,yaw[-1]*dt)
        rotationMatrix = transformPitch(rotationMatrix,pitch[-1]*dt)
        rotationMatrix = transformRoll(rotationMatrix,roll[-1]*dt)

        kx.append(rotationMatrix[0][2])
        ky.append(rotationMatrix[1][2])
        kz.append(rotationMatrix[2][2])

        newVx = Vx[-1] + kx[-1] * speed * slideMod * dt
        newVy = Vy[-1] + ky[-1] * speed * slideMod * dt
        newVz = Vz[-1] + kz[-1] * speed * slideMod * dt

        magnitude = np.linalg.norm([newVx,newVy,newVz])

        if slideMod == 0:
            Vx.append(kx[-1]*speed)
            Vy.append(ky[-1]*speed)
            Vz.append(kz[-1]*speed)
        else:
            if magnitude > speed:
                Vx.append(newVx/magnitude * speed)
                Vy.append(newVy/magnitude * speed)
                Vz.append(newVz/magnitude * speed)
            else:
                Vx.append(newVx)
                Vy.append(newVy)
                Vz.append(newVz)

        Ax.append((Vx[-1]-Vx[-2])/dt)
        Ay.append((Vy[-1]-Vy[-2])/dt)
        Az.append((Vz[-1]-Vz[-2])/dt)

        x.append(x[-1] + Vx[-1] * dt)
        y.append(y[-1] + Vy[-1] * dt)
        z.append(z[-1] + Vz[-1] * dt)

        speedOut.append(np.linalg.norm([Vx[-1],Vy[-1],Vz[-1]]))
        accelOut.append(np.linalg.norm([Ax[-1],Ay[-1],Az[-1]]))
        try:
            theta.append(np.arccos(np.dot([kx[-1],ky[-1],kz[-1]],[Vx[-1],Vy[-1],Vz[-1]])/(np.linalg.norm([kx[-1],ky[-1],kz[-1]])*np.linalg.norm([Vx[-1],Vy[-1],Vz[-1]]))) * 180/np.pi)
        except:
            theta.append(0)

    return x, y, z, Vx, Vy, Vz, kx, ky, kz, Ax, Ay, Az, t, speedOut, accelOut, pitch, yaw, roll, theta

def flightSimulator():
    if not os.path.exists("Data\\tables.db"):
        buildTables("Null")

    data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
    cur = data.cursor()

    chassisTable = cur.execute("SELECT * FROM chassis").fetchall()
    chassisData = [[x[0]] + list(x[10:22]) for x in chassisTable]
    chassisNames = [x[0] for x in chassisTable]

    ### UI Layout Begins Here ###

    selectionPaneLeft = [
        [sg.Push(),sg.Text('Select Chassis:',font=baseFont,p=1)],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('Acceleration:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Deceleration:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Pitch Accel:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Yaw Accel:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Roll Accel:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Speed Mod (Foils Closed):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Speed Mod (Foils Open):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Min Throttle Turning:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Opt Turning Throttle:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Max Throttle Turning:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Slide Mod:',font=baseFont,p=1)],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('Engine Top Speed:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Engine Pitch Rate Max:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Engine Yaw Rate Max:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Engine Roll Rate Max:',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Engine Overload Level:',font=baseFont,p=1)],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('Throttle Setting (0 to 1):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Pitch Setting (-1 to 1):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Yaw Setting (-1 to 1):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Roll Setting (-1 to 1):',font=baseFont,p=1)],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Push(),sg.Text('Interval Frequency (Hz):',font=baseFont,p=1)],
        [sg.Push(),sg.Text('Simulation Time (s):',font=baseFont,p=1)],
    ]

    selectionPaneRight = [
        [sg.Combo([x[0] for x in chassisData],size=(20,20),font=baseFont,p=1,key='chassisselect',readonly=True,enable_events=True),sg.Push()],
        [sg.Text('',font=baseFont,p=0)],
    ]

    selectionPaneRight += [[sg.Text('',key='chassisstat' + str(x),font=baseFont,p=1)] for x in range(1,12)]
    selectionPaneRight += [[sg.Text('',font=baseFont,p=0)]]
    selectionPaneRight += [[sg.Input('',s=6,key='enginestat' + str(x),font=baseFont,p=1)] for x in range(1,5)]
    selectionPaneRight += [[sg.Combo(values=['None','1','2','3','4'],key='enginestat5',font=baseFont,p=0)]]
    selectionPaneRight += [[sg.Text('',font=baseFont,p=0)]]
    selectionPaneRight += [[sg.Input('',s=4,key='throttlesetting' + str(x),font=baseFont,p=1)] for x in range(1,5)]
    selectionPaneRight += [[sg.Text('',font=baseFont,p=0)]]
    selectionPaneRight += [[sg.Input('',s=4,key='simsetting' + str(x),font=baseFont,p=1)] for x in range(1,3)]

    selectionPane = [
        [sg.Frame('',selectionPaneLeft,border_width=0,p=0),sg.Frame('',selectionPaneRight,border_width=0,p=0)]
    ]

    leftFrame = [
        [sg.Frame('',selectionPane,border_width=0,p=0)],
        [sg.VPush()],
        [sg.Push(),sg.Button('Calculate',font=('Roboto',18,'bold')),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='dist'),sg.Push()],
        [sg.Push(),sg.Text('',font=baseFont,p=1,key='curve'),sg.Push()]
    ]

    rightFrame = [
        [sg.Canvas(size=(500,400),key='plot',background_color=bgColor),sg.Canvas(size=(800,600),key='plot2',background_color=bgColor)]
    ]

    Layout = [
        [sg.Frame('',leftFrame,border_width=0,p=0),sg.Frame('',rightFrame,border_width=0,p=0)]
    ]

    flightSimWindow = sg.Window("SWG Legends Flight Simulator",Layout,modal=True,icon=os.path.abspath(os.path.join(os.path.dirname(__file__), 'SLT_Icon.ico')),finalize=True)

    fig = plt.Figure(figsize=(8,8))
    ax = fig.add_subplot(projection='3d')
    ax.set_title('')
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.grid()
    fig_canvas_agg = draw_figure(flightSimWindow['plot'].TKCanvas,fig)

    fig2 = plt.Figure(figsize=(6,8))
    ax2 = fig2.add_subplot(2,1,1)
    ax2.set_title('Speed and PYR Rate vs. Time')
    ax2.set_xlabel('')
    ax2.set_ylabel('Speed (m/s) / PYR Rate (°/s)')
    ax2.grid()
    ax3 = fig2.add_subplot(2,1,2)
    ax3.set_title('Phase Angle vs. Time')
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Phase Angle (°)')
    ax3.grid()
    fig_canvas_agg2 = draw_figure(flightSimWindow['plot2'].TKCanvas,fig2)

    initialStats = ['Ixiyen Starfighter','125.4','90.3','90.2','90.3','4','0.5','0','1','0','75','20']

    if initialStats != []:
        flightSimWindow['chassisselect'].update(value=initialStats[0])
        for i in range(1,12):
            index = chassisNames.index(initialStats[0])
            flightSimWindow['chassisstat' + str(i)].update(value=chassisData[index][i])
        for i in range(1,6):
            flightSimWindow['enginestat' + str(i)].update(initialStats[i])
        for i in range(1,5):
            flightSimWindow['throttlesetting' + str(i)].update(initialStats[i+5])
        for i in range(1,3):
            flightSimWindow['simsetting' + str(i)].update(initialStats[i+9])

    while True:
        event, values = flightSimWindow.read()

        if event == 'chassisselect':
            chassisName = values['chassisselect']
            if chassisName in chassisNames:
                index = chassisNames.index(chassisName)
                for i in range(1,12):
                    flightSimWindow['chassisstat' + str(i)].update(value=chassisData[index][i])
        
        if event == 'Calculate':
            ax.cla()
            ax2.cla()
            ax3.cla()
            x, y, z, Vx, Vy, Vz, kx, ky, kz, Ax, Ay, Az, t, speed, accel, pitch, yaw, roll, theta = modelFlightPath(flightSimWindow)
            simdt = float(values['simsetting1'])
            simTime = float(values['simsetting2'])
            truncationFactor = max(int(simdt/5),int(simTime*simdt/100)) #5 arrows per second or 50 arrows total, whichever is smaller.
            xTrunc = []
            yTrunc = []
            zTrunc = []
            VxTrunc = []
            VyTrunc = []
            VzTrunc = []
            AxTrunc = []
            AyTrunc = []
            AzTrunc = []
            kxTrunc = []
            kyTrunc = []
            kzTrunc = []
            midpointx = (max(x) + min(x))/2
            midpointy = (max(y) + min(y))/2
            midpointz = (max(z) + min(z))/2
            xwidth = max(x) - min(x)
            ywidth = max(y) - min(y)
            zwidth = max(z) - min(z)
            largestdim = max(xwidth,ywidth,zwidth) * 1.1 #plot cube with sides 10% wider than the largest dimension
            ax.set_xlim(midpointx-largestdim/2,midpointx+largestdim/2)
            ax.set_ylim(midpointy-largestdim/2,midpointy+largestdim/2)
            ax.set_zlim(midpointz-largestdim/2,midpointz+largestdim/2)
            scale = largestdim/simTime
            for i in np.arange(0,len(x)+1,truncationFactor):
                xTrunc.append(x[i])
                yTrunc.append(y[i])
                zTrunc.append(z[i])
                if speed[i] == 0:
                    VxTrunc.append(0)
                    VyTrunc.append(0)
                    VzTrunc.append(0)
                else:
                    VxTrunc.append(Vx[i]/speed[i]*scale)
                    VyTrunc.append(Vy[i]/speed[i]*scale)
                    VzTrunc.append(Vz[i]/speed[i]*scale)
                if accel[i] == 0:
                    AxTrunc.append(0)
                    AyTrunc.append(0)
                    AzTrunc.append(0)
                else:
                    AxTrunc.append(Ax[i]/accel[i]*scale)
                    AyTrunc.append(Ay[i]/accel[i]*scale)
                    AzTrunc.append(Az[i]/accel[i]*scale)
                kxTrunc.append(kx[i]*truncationFactor)
                kyTrunc.append(ky[i]*truncationFactor)
                kzTrunc.append(kz[i]*truncationFactor)
            ax.set_xlabel("X-Axis")
            ax.set_ylabel("Y-Axis")
            ax.set_zlabel("Z-Axis")
            curveLength = 0
            for i in range(1,len(x)):
                dx = x[i] - x[i-1]
                dy = y[i] - y[i-1]
                dz = z[i] - z[i-1]
                mag = np.linalg.norm([dx, dy, dz])
                curveLength += mag
            ax.set_aspect('equal')
            ax.plot3D(x,y,z,color='#00ffff')
            ax.scatter3D(0,0,0,color='#ffff00',)
            ax.quiver(xTrunc,yTrunc,zTrunc,AxTrunc,AyTrunc,AzTrunc,color='#00ff00')
            ax.quiver(xTrunc,yTrunc,zTrunc,VxTrunc,VyTrunc,VzTrunc,color='#ff0000')
            fig_canvas_agg.draw()
            ax2.plot(t,speed,color='#00ffff')
            ax2.plot(t,pitch,color='#ff0000')
            ax2.plot(t,yaw,color='#00ff00')
            ax2.plot(t,roll,color='#0000ff')
            ax2.set_title('Speed and PYR Rate vs. Time')
            ax2.set_xlabel('')
            ax2.set_ylabel('Speed (m/s) / PYR Rate (°/s)')
            fig_canvas_agg2.draw()
            ax3.plot(t,theta,color='#00ffff')
            ax3.plot(t,[90]*len(t),color="#ffff00")
            ax3.set_title('Phase Angle vs. Time')
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Phase Angle (°)')
            fig_canvas_agg2.draw()
            flightSimWindow['dist'].update('Net Distance Traveled: ' + str(round(np.linalg.norm([x[-1],y[-1],z[-1]]),1)) + 'm')
            flightSimWindow['curve'].update('Path Length: ' + str(round(curveLength,1)) + 'm')

        if event == sg.WIN_CLOSED:
            break

    data.close()
    flightSimWindow.close()

flightSimulator()


#for i in np.arange(1,2.0,0.1):
#    print('Slide Mod: ' + str(round(i,1)), '        Critical Angle: ' + str(round(270 - 2 * np.arctan(2/i + np.sqrt((4-np.pow(i,2))/np.pow(i,2)))*180/np.pi,1)) + '°')