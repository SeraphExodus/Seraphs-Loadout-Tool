import matplotlib.pyplot as plt
import numpy as np
import os

from datetime import datetime

mailDir = "E:\\Program Files (x86)\\StarWarsGalaxies\\profiles\\seraphexodus\\Omega\\mail_Artaros Blackthorne"

mailFiles = os.listdir(mailDir)

credits = []
timestamps = []

for file in mailFiles:
    dir = mailDir + '\\' + file
    message = open(dir,'r').read()
    if "Sale Complete" in message:
        lines = message.split('\n')
        timestamp = datetime.fromtimestamp(int(lines[3].split(': ')[1]))
        timestamps.append(timestamp)
        try:
            creds = lines[4].split(' for ')[1].split(' credits')[0]
        except:
            try:
                creds = lines[5].split(' for ')[1].split(' credits')[0]
            except:
                creds = 0
        try:
            credits.append(int(creds))
        except:
            credits.append(0)
#'Vendor: Flight Computers and Droid Command Chips has sold "\\#3399ff[BHI] \\#ffffffv6 Flight Computer Command Kit'
start = min([x.year for x in timestamps])
end = max([x.year for x in timestamps])
months = range(1,13)
years = range(start, end+1)
chartData = []
for year in years:
    for month in months:
        monthlyExpenditure = 0
        for i in range(0,len(credits)):
            if [timestamps[i].year, timestamps[i].month] == [year, month]:
                monthlyExpenditure += credits[i]
        chartData.append([datetime(year,month,1), monthlyExpenditure])

totalSales = sum([x[1] for x in chartData])
print(totalSales)

fig, ax = plt.subplots(figsize=(10,5))
#time = np.arange(str(start)+'-01-01', str(end)+'-12-31', dtype='datetime64[D]')
ax.plot([x[0] for x in chartData],[x[1] for x in chartData])

plt.show()