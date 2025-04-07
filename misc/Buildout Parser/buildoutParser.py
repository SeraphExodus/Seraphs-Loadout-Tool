import FreeSimpleGUI as sg
import itertools
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import operator
import os
import pandas as pd
import pyglet
import win32clipboard

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

def draw_figure(canvas, figure, loc=(0, 0)):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

def delete_figure_agg(figure_agg):
    figure_agg.get_tk_widget().forget()
    plt.close('all')

def toClipboard(text):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()

def generateRandomHexColor(minBright,minContrast):
    while True:
        color = np.random.rand(3)
        red = color[0]
        green = color[1]
        blue = color[2]
        
        chroma = max([red,green,blue]) - min([red,green,blue])
        value = np.mean([red,green,blue])
        if value > minBright and chroma > minContrast:
            redHex = hex(int(red * 255 + 0.5))[2:]
            greenHex = hex(int(green * 255 + 0.5))[2:]
            blueHex = hex(int(blue * 255 + 0.5))[2:]
            while len(redHex) < 2:
                redHex = '0' + redHex
            while len(greenHex) < 2:
                greenHex = '0' + greenHex
            while len(blueHex) < 2:
                blueHex = '0' + blueHex
            output = '#' + redHex + greenHex + blueHex
            break
    return output

def plotZoneBounds(ax):
    face = [[],[],[],[],[],[]]
    face[0] = [[-8160,-8160,-8160,-8160,-8160],[-8160,-8160,8160,8160,-8160],[-8160,8160,8160,-8160,-8160]]
    face[1] = [[-8160,-8160,8160,8160,-8160],[-8160,-8160,-8160,-8160,-8160],[-8160,8160,8160,-8160,-8160]]
    face[2] = [[-8160,-8160,8160,8160,-8160],[-8160,8160,8160,-8160,-8160],[-8160,-8160,-8160,-8160,-8160]]
    face[3] = [[8160,8160,8160,8160,8160],[-8160,-8160,8160,8160,-8160],[-8160,8160,8160,-8160,-8160]]
    face[4] = [[-8160,-8160,8160,8160,-8160],[8160,8160,8160,8160,8160],[-8160,8160,8160,-8160,-8160]]
    face[5] = [[-8160,-8160,8160,8160,-8160],[-8160,8160,8160,-8160,-8160],[8160,8160,8160,8160,8160]]
    for i in face:
        ax.plot(i[0],i[1],i[2],color='#ff0000',linewidth=1,linestyle=':')
    return ax

def generateSpawnList(buildout):
    data = pd.DataFrame.to_numpy(pd.read_table(buildout))[2:]
    squads = pd.DataFrame.to_numpy(pd.read_table("squads.tab"))[2:]

    squadNames = [x[0] for x in squads]
    squadShips = [x[3:13] for x in squads]

    spawners = [x for x in data if 'spawner' in x[0]]
    patrolPoints = [x for x in data if 'patrol_point' in x[0]]
    staticShips = [x for x in data if '/ship/' in x[0] and 'spacestation' not in x[0]]
    minorStations = [x for x in data if 'spacestation' in x[0] and '/ship/' not in x[0]]
    majorStations = [x for x in data if 'spacestation' in x[0] and '/ship/' in x[0]]
    beacons = [x for x in data if '/beacon/' in x[0]]

    statics = []
    staticStations = []
    staticMajorStations = []
    staticBeacons = []
    for i in staticShips:
        statics.append([float(i[7]),float(i[8]),float(i[9])])
    for i in minorStations:
        staticStations.append([float(i[7]),float(i[8]),float(i[9])])
    for i in majorStations:
        staticMajorStations.append([float(i[7]),float(i[8]),float(i[9])])
    for i in beacons:
        staticBeacons.append([float(i[7]),float(i[8]),float(i[9])])
    spawns = []
    asteroids = []

    for i in spawners:
        contentList = i[10].split('|')
        coords = [float(i[7]),float(i[8]),float(i[9])]
        facingj = [float(i[1]),float(i[2]),float(i[3])]
        facingk = [float(i[4]),float(i[5]),float(i[6])]
        facingi = np.cross(facingj,facingk)

        try:
            name = contentList[contentList.index('strSpawnerName') + 2]
        except:
            name = ''

        try:
            behavior = contentList[contentList.index('strDefaultBehavior') + 2]
        except:
            behavior = ''

        try:
            minSpawnDist = float(contentList[contentList.index('fltMinSpawnDistance') + 2])
            maxSpawnDist = float(contentList[contentList.index('fltMaxSpawnDistance') + 2])
            spawnShell = [minSpawnDist, maxSpawnDist]
        except:
            spawnShell = [0, 0]
            
        try:
            minCircleDist = float(contentList[contentList.index('fltMinCircleDistance') + 2])
            maxCircleDist = float(contentList[contentList.index('fltMaxCircleDistance') + 2])
            circleShell = [minCircleDist, maxCircleDist]
        except:
            circleShell = [0, 0]

        try:
            spawnCount = str(int(contentList[contentList.index('intSpawnCount')+2]))
        except:
            spawnCount = 0

        try:
            respawn = str(int(contentList[contentList.index('fltMinSpawnTime')+2])) + 's to ' + str(int(contentList[contentList.index('fltMaxSpawnTime')+2])) + 's'
        except:
            respawn = 'N/A'
        
        try:
            patrolList = contentList[contentList.index('strPatrolPoints_mangled.segment.0')+2].split(':')[:-1]
            patrolCoords = []
            for a in patrolPoints:
                if any(x in a[10] for x in patrolList):
                    patrolCoords.append([float(a[7]),float(a[8]),float(a[9])])
            if 'patrolNoRecycle' not in contentList:
                patrolCoords.append(patrolCoords[0])
                spawnerType = 'Patrol'
            else:
                spawnerType = 'Patrol (No Recycle)'
            patrolCoords = patrolCoords
        except:
            patrolCoords = []
            spawnerType = 'Static'

        try:
            ships = contentList[contentList.index('strSpawns_mangled.segment.0')+2].split(':')[:-1]
            shipList = []
            for a in ships:
            #     if a in squadNames:
            #         shipList += [x for x in squadShips[squadNames.index(a)] if type(x) == str]
            #     else:
                shipList += [a]
        except:
            try:
                ships = contentList[contentList.index('strAsteroidType')+2] + ' asteroid'
                shipList = [ships]
            except:
                shipList = []
        
        if 'asteroid' in ships:
            asteroids.append(coords)
        else:
            spawns.append([name, spawnerType, spawnCount, respawn, coords, shipList, patrolCoords, behavior, spawnShell, circleShell])

    spawns.sort(key=operator.itemgetter(0))

    return spawns, statics, staticStations, staticMajorStations, staticBeacons, asteroids

def buildoutParser():

    dataFrameCol1 = []
    dataFrameCol2 = []

    spawns = []

    for i in range(0,40):
        dataFrameCol1.append([sg.Push(),sg.Text('',key='col1text' + str(i),font=baseFont,p=0)])
        dataFrameCol2.append([sg.Push(),sg.Text('',key='col2text' + str(i),font=baseFont,p=0),sg.Push()])

    dataFrame = [
        [sg.Column(dataFrameCol1),sg.Column(dataFrameCol2)]
    ]

    tableFrame = [
        [sg.Push(),sg.Input('',font=baseFont,p=0,key='buildoutdir',enable_events=True),sg.FileBrowse(),sg.Push()],
        [sg.Push(),sg.Table([x[0] for x in spawns],['Spawner Name'], size=(50,50), def_col_width=40,cols_justification='center',auto_size_columns=False,enable_click_events=True,font=baseFont,key='table'),sg.Push()]
    ]

    radioFrame = [
        [sg.Checkbox('Show space stations',default=True,font=baseFont,p=0,enable_events=True,key='majorstations')],
        [sg.Checkbox('Show asteroids',default=True,font=baseFont,p=0,enable_events=True,key='asteroids')],
        [sg.Checkbox('Show static objects',default=True,font=baseFont,p=0,enable_events=True,key='statics')],
        [sg.Text('',font=baseFont,p=0)],
        [sg.Radio('Copy all waypoints',default=True,font=baseFont,p=0,enable_events=True,key='wp1',group_id='radio')],
        [sg.Radio('Copy shortest path between static waypoints',default=False,font=baseFont,p=0,enable_events=True,key='wp2',group_id='radio')],
    ]

    Layout = [
        [sg.Frame('',tableFrame,border_width=0,p=elementPadding),sg.Frame('',dataFrame,border_width=0,p=elementPadding,size=(450,750)),sg.Push(),sg.Canvas(size=(500,400),key='plot',background_color=bgColor),sg.Frame('',radioFrame,border_width=0,p=0),sg.Push()]
    ]

    buildoutWindow = sg.Window('Buildout Parser',Layout,finalize=True)

    fig = plt.Figure(figsize=(8,8))
    ax = fig.add_subplot(projection='3d')
    ax.set_title('')
    ax.set_xlabel("X-coordinate")
    ax.set_ylabel("Y-coordinate")
    ax.set_zlabel("Z-coordinate")
    ax.set_aspect('equal')
    ax.grid()
    fig_canvas_agg = draw_figure(buildoutWindow['plot'].TKCanvas,fig)

    colorList = []
    for i in range(0,20):
        colorList.append(generateRandomHexColor(0.5,0.5))

    while True:
        window, event, values = sg.read_all_windows()

        if window == buildoutWindow:

            if event == 'buildoutdir':
                zone = values['buildoutdir'].split('/')[-1].split('.')[0]
                if zone == 'space_light1':
                    zone = 'space_kessel'
                
                spawns, statics, minorStations, majorStations, beacons, asteroids = generateSpawnList(values['buildoutdir'])
                names = [x[0] for x in spawns]
                buildoutWindow['table'].update(names)
                ax.cla()
                ax.set_aspect('equal')
                ax.set_xlim(-8160,8160)
                ax.set_ylim(-8160,8160)
                ax.set_zlim(-8160,8160)
                ax.set_xlabel("X-coordinate")
                ax.set_ylabel("Y-coordinate")
                ax.set_zlabel("Z-coordinate")
                if values['statics']:
                    ax.scatter([x[0] for x in statics],[y[1] for y in statics],[z[2] for z in statics],color='#ff9900',marker='>', s=30)
                    ax.scatter([x[0] for x in minorStations],[y[1] for y in minorStations],[z[2] for z in minorStations],color='#ff9900',marker='p',s=30)
                    ax.scatter([x[0] for x in beacons],[y[1] for y in beacons],[z[2] for z in beacons],color='#ff9900',marker='d', s=30)
                if values['majorstations']:
                    ax.scatter([x[0] for x in majorStations],[y[1] for y in majorStations],[z[2] for z in majorStations],color='#ffff00',marker='p',s=200)
                    ax.scatter([x[0] for x in majorStations],[y[1] for y in majorStations],[z[2] for z in majorStations],color='#00ff00',marker='p',s=50)   
                if values['asteroids']:
                    ax.scatter([x[0] for x in asteroids],[y[1] for y in asteroids],[z[2] for z in asteroids],color='#444444',marker='D', s=75)
                    ax.scatter([x[0] for x in asteroids],[y[1] for y in asteroids],[z[2] for z in asteroids],color='#666666',marker='D', s=15)
                fig_canvas_agg.draw()
                
            if (type(event) == tuple or event in ['majorstations','statics','asteroids','beacons']) and values['buildoutdir'] != '':
                squads = pd.DataFrame.to_numpy(pd.read_table("squads.tab"))[2:]
                squadNames = [x[0] for x in squads]
                squadShips = [x[3:13] for x in squads]
                rows = values['table']
                spawns, statics, minorStations, majorStations, beacons, asteroids = generateSpawnList(values['buildoutdir'])
                ax.cla()
                ax.set_aspect('equal')
                ax.set_xlim(-8160,8160)
                ax.set_ylim(-8160,8160)
                ax.set_zlim(-8160,8160)
                ax.set_xlabel("X-coordinate")
                ax.set_ylabel("Y-coordinate")
                ax.set_zlabel("Z-coordinate")
                if values['statics']:
                    ax.scatter([x[0] for x in statics],[y[1] for y in statics],[z[2] for z in statics],color='#ff9900',marker='>', s=30)
                    ax.scatter([x[0] for x in minorStations],[y[1] for y in minorStations],[z[2] for z in minorStations],color='#ff9900',marker='p',s=30)
                    ax.scatter([x[0] for x in beacons],[y[1] for y in beacons],[z[2] for z in beacons],color='#ff9900',marker='d', s=30)
                if values['majorstations']:
                    ax.scatter([x[0] for x in majorStations],[y[1] for y in majorStations],[z[2] for z in majorStations],color='#ffff00',marker='p',s=200)
                    ax.scatter([x[0] for x in majorStations],[y[1] for y in majorStations],[z[2] for z in majorStations],color='#00ff00',marker='p',s=50)   
                if values['asteroids']:
                    ax.scatter([x[0] for x in asteroids],[y[1] for y in asteroids],[z[2] for z in asteroids],color='#444444',marker='D', s=75)
                    ax.scatter([x[0] for x in asteroids],[y[1] for y in asteroids],[z[2] for z in asteroids],color='#666666',marker='D', s=15)
                fig_canvas_agg.draw()
                wpString = ''
                wpList = []
                staticSpheres = []
                if len(rows) != 0:
                    for i in range(0,40):
                        buildoutWindow['col1text' + str(i)].update('')
                        buildoutWindow['col2text' + str(i)].update('')
                    for r in rows:
                        data = spawns[r]
                        tableData = [
                            ['Spawner Name',data[0]],
                            ['Spawner Type',data[1]],
                            ['Spawn Count'],                                
                            ['Respawn Timer',data[3]],
                            ['Spawn Coordinates',str(data[4][0])+', '+str(data[4][1])+', '+str(data[4][2])],
                            ['','']
                        ]
                        for i in range(0,len(data[5])):
                            if data[5][i] in squadNames:
                                squadListEnum = list(squadShips[squadNames.index(data[5][i])])
                                for j in range(0,len(squadListEnum)):
                                    if str(squadListEnum[j]) != '' and str(squadListEnum[j]) != 'nan':
                                        if j == 0:
                                            tableData.append(['Spawn Group ' + str(i+1),squadListEnum[j]])
                                        else:
                                            tableData.append(['',squadListEnum[j]])
                            else:
                                tableData.append(['Spawn Option ' + str(i+1),data[5][i]])
                        if len(data[5]) > 1:
                            tableData[2].append(data[2] + ' at random from below')
                        else:
                            tableData[2].append(data[2])
                        tableData.append(['',''])
                        if data[6] != []:
                            for i in range(0,len(data[6])):
                                tableData.append(['Patrol Point ' + str(i+1),str(data[6][i][0])+', '+str(data[6][i][1])+', '+str(data[6][i][2])])
                            xcoords = [x[0] for x in data[6]]
                            ycoords = [x[1] for x in data[6]]
                            zcoords = [x[2] for x in data[6]]
                            vectors = [[], [], []]
                            for i in range(0,len(xcoords)-1):
                                vectors[0].append(xcoords[i+1]-xcoords[i])
                                vectors[1].append(ycoords[i+1]-ycoords[i])
                                vectors[2].append(zcoords[i+1]-zcoords[i])
                            #ax.quiver(xcoords[0:-1],ycoords[0:-1],zcoords[0:-1],vectors[0],vectors[1],vectors[2],color='#ffff00')
                            ax.set_aspect('equal')
                            ax.plot3D(xcoords,ycoords,zcoords,color=colorList[rows.index(r)%20])
                            ax.scatter(xcoords[-1],ycoords[-1],zcoords[-1],color='#ff0000')
                            ax.scatter(xcoords[0],ycoords[0],zcoords[0],color='#00ff00')
                            ax = plotZoneBounds(ax)
                            fig_canvas_agg.draw()
                        elif data[7].casefold() == 'patrolRandomPath'.casefold():
                            ax.set_aspect('equal')
                            centerpoint = [data[4][0],data[4][1],data[4][2]]
                            maxRadius = data[9][1]
                            spherePoints = []

                            # shift = False
                            # for phi in np.linspace(0,np.pi,int(maxRadius/64)):
                            #     if shift:
                            #         for theta in np.linspace(0,2*np.pi,int(maxRadius/64)):
                            #             x = maxRadius * np.cos(theta+np.pi/int(maxRadius/64)) * np.sin(phi) + centerpoint[0]
                            #             y = maxRadius * np.sin(theta+np.pi/int(maxRadius/64)) * np.sin(phi) + centerpoint[1]
                            #             z = maxRadius * np.cos(phi) + centerpoint[2]
                            #             spherePoints.append([x, y, z])
                            #             shift = False
                            #     else:
                            #         for theta in np.linspace(0,2*np.pi,int(maxRadius/64)):
                            #             x = maxRadius * np.cos(theta) * np.sin(phi) + centerpoint[0]
                            #             y = maxRadius * np.sin(theta) * np.sin(phi) + centerpoint[1]
                            #             z = maxRadius * np.cos(phi) + centerpoint[2]
                            #             spherePoints.append([x, y, z])
                            #             shift = True

                            # /// Implements fibonacci spiral point patterns to make a sphere with uniform point distribution per https://arxiv.org/pdf/0912.4540 ///
                            n = int(maxRadius/8)
                            for p in range(-n,n):
                                phi = np.arcsin(2*p/(2*n+1)) + np.pi/2
                                theta = (2*np.pi*p*1/1.61803398875) #golden ratio
                                x = maxRadius * np.cos(theta) * np.sin(phi) + centerpoint[0]
                                y = maxRadius * np.sin(theta) * np.sin(phi) + centerpoint[1]
                                z = maxRadius * np.cos(phi) + centerpoint[2]
                                spherePoints.append([x, y, z])

                            ax.scatter([x[0] for x in spherePoints],[x[1] for x in spherePoints],[x[2] for x in spherePoints],color=colorList[rows.index(r)%20],s=2.5)
                            ax.scatter(centerpoint[0],centerpoint[1],centerpoint[2],color='#00ff00')
                            ax = plotZoneBounds(ax)
                            fig_canvas_agg.draw()
                        else:
                            ax.set_aspect('equal')
                            ax.scatter(data[4][0],data[4][1],data[4][2],color='#00ff00')
                            ax = plotZoneBounds(ax)
                            fig_canvas_agg.draw()
                        wpString += '/way ' + zone + ' ' + tableData[4][1].replace(',','') + ' ' + tableData[0][1] + ' (' + tableData[1][1].lower() + ')'
                        if tableData[1][1] == 'Patrol':
                            wpString += ' green;'
                        else:
                            wpString += ' orange;'
                            wpList.append([float(tableData[4][1].split(', ')[0]),float(tableData[4][1].split(', ')[1]),float(tableData[4][1].split(', ')[2])])
                            staticSpheres.append(data[9][1])
                        if values['wp1']:
                            toClipboard(wpString)
                
                #///Find best path for static spawns, copy wps to clipboard, and plot///
                if values['wp2']:
                    if len(wpList) > 1:
                        perms = list(itertools.permutations(wpList))
                        permCumDist = []
                        for i in perms:
                            cumDist = 0
                            for j in range(0,len(i)-1):
                                dx = i[j][0] - i[j+1][0]
                                dy = i[j][1] - i[j+1][1]
                                dz = i[j][2] - i[j+1][2]
                                cumDist += np.linalg.norm([dx, dy, dz])
                            permCumDist.append(cumDist)
                        bestPath = perms[permCumDist.index(min(permCumDist))]
                        ax.set_aspect('equal')
                        pointers = []
                        for i in range(1,len(bestPath)):
                            pointers.append([bestPath[i][0]-bestPath[i-1][0],bestPath[i][1]-bestPath[i-1][1],bestPath[i][2]-bestPath[i-1][2]])
                        bestPathStarts = bestPath[:-1]
                        spheres = []
                        for i in bestPath:
                            spheres.append(staticSpheres[wpList.index(i)])
                        ax.quiver([x[0] for x in bestPathStarts],[x[1] for x in bestPathStarts],[x[2] for x in bestPathStarts],[x[0] for x in pointers],[x[1] for x in pointers],[x[2] for x in pointers],color='#00ffff')
                        fig_canvas_agg.draw()
                        bestPathString = ''
                        for i in range(0,len(bestPath)):
                            bestPathString += '/way ' + zone + ' ' + str(bestPath[i][0]) + ' ' + str(bestPath[i][1]) + ' ' + str(bestPath[i][2]) + ' Point ' + str(i) + ' (' + str(spheres[i]) + 'm) green;'
                        toClipboard(bestPathString)

                if len(rows) == 1:
                    for i in range(1,3):
                        for j in range(0,len(tableData)):
                            buildoutWindow['col' + str(i) + 'text' + str(j)].update(tableData[j][i-1])

        if event == sg.WIN_CLOSED:
            break

    buildoutWindow.close()

buildoutParser()