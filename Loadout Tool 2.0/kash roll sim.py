import sqlite3
import math
import random

#Simulate me up some kash rolls

data = sqlite3.connect("file:Data\\tables.db?mode=rw", uri=True)
cur = data.cursor()

stats = cur.execute("SELECT name, stat1mean, stat1mod, stat2mean, stat2mod FROM brands WHERE relevel = ?", ['A0']).fetchall()
name = [x[0] for x in stats]
ahpMeans = [float(x[1]) for x in stats]
ahpStdevs = [float(x[1]) * float(x[2]) / 2 for x in stats]
massMeans = [float(x[3]) for x in stats]
massStdevs = [float(x[3]) * float(x[4]) / 2 for x in stats]


simulationCycles = 1
j = 0
while j < simulationCycles:

    simCount = 1000000

    print('Spending ' + str(simCount * 100) + ' tokens on A0s at Kash:')
    print('Showing all unicorn AHP > 4250 post and Mass < 1000 post')
    i = 0

    keepers = []

    while i < simCount:
        index = name.index(random.choice(name))
        brand = name[index]
        ahp = round(random.normalvariate(ahpMeans[index],ahpStdevs[index]),1)
        mass = round(random.normalvariate(massMeans[index],massStdevs[index]),1)
        component = [brand, 'A/HP: ' + str(ahp), 'Mass: ' + str(mass)]
        if ahp > 3972.1 or (mass < 1075.1 and mass > 0):
            print(['Unicorn!'] + component + ['Pull number ' + str(i)])
            keepers.append(component)
        elif ahp > 3300 or mass < 10000:
            keepers.append(component)
            #print(component)
        i += 1

    print('Keep Count: ' + str(len(keepers)))

    j += 1


data.close()