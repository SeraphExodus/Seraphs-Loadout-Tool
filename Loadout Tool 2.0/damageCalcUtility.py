import json
import matplotlib.pyplot as plt
import os

dataDir = os.getenv('APPDATA') + "\\Seraph's Loadout Tool"

with open('data.json','r') as importData:
    tableData = json.load(importData)

print(tableData['ordnance'])