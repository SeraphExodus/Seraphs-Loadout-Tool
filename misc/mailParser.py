import matplotlib.pyplot as plt
import os
import shutil

from datetime import datetime, timedelta

###Character List: Add your character names to this list if you want their saved mail included
charList = ["Artaros Blackthorne","Aile'atha Brightsun","Xanthira Silverwind"]

###Edit this with your own SWG path and account name
mailDirMain = "E:\\Program Files (x86)\\StarWarsGalaxies\\profiles\\seraphexodus\\Omega"

mailDir = mailDirMain + "\\mailcombined"

if not os.path.exists(mailDir):
    os.makedirs(mailDir)

for char in charList:
    thisDir = mailDirMain + "\\mail_" + char
    dirFiles = os.listdir(thisDir)
    for file in dirFiles:
        if not os.path.exists(mailDir + '\\' + file):
            shutil.copy(thisDir + '\\' + file, mailDir + '\\' + file)

mailFiles = os.listdir(mailDir)

saleCredits = []
saleTimestamps = []
purchaseCredits = []
purchaseTimestamps = []
dutyCredits = []
dutyTokens = []
dutyCPU = []
dutyTimestamps = []
timestamps = []

###Config###
interval = "Day" ###Day, Week, or Month
startDate = datetime(2025,9,1) #Y/M/D
endDate = datetime(2026,12,31) #Y/M/D

fig, ax = plt.subplots(5,1,figsize=(10,12),tight_layout=True)

for file in mailFiles:
    dir = mailDir + '\\' + file
    message = open(dir,'r').read()

    if "Sale Complete" in message:
        lines = message.split('\n')
        timestamp = datetime.fromtimestamp(int(lines[3].split(': ')[1]))
        saleTimestamps.append(timestamp)
        try:
            creds = int(lines[4].split(' credits.')[0].split(' for ')[-1])
        except:
            try:
                creds = int(lines[5].split(' credits.')[0].split(' for ')[-1])
            except:
                creds = 0
        saleCredits.append(creds)
    if "Duty Mission Token" in message and "Item Purchased" in message:
        lines = message.split('\n')
        timestamp = datetime.fromtimestamp(int(lines[3].split(': ')[1]))
        dutyTimestamps.append(timestamp)
        try:
            creds = int(lines[4].split(' credits.')[0].split(' for ')[-1])
            tokens = lines[4].split('Token')[1].split('" from')[0].replace(' ','')
            try:
                tokens = int(tokens)
                cpu = creds/tokens
                if cpu < 1000:
                    cpu = 1000
            except:
                tokens = int(creds/1000)
                cpu = 1000
        except:
            try:
                creds = int(lines[5].split(' credits.')[0].split(' for ')[-1])
                tokens = lines[5].split('Token')[1].split('" from')[0].replace(' ','')
                try:
                    tokens = int(tokens)
                    cpu = creds/tokens
                    if cpu < 1000:
                        cpu = 1000
                except:
                    tokens = int(creds/1000)
                    cpu = 1000
            except:
                creds = 0
                tokens = 0
                cpu = 0
        dutyCredits.append(creds)
        dutyTokens.append(tokens)
        dutyCPU.append(cpu)
    if "Item Purchased" in message and not "Duty Mission Token" in message:
        lines = message.split('\n')
        timestamp = datetime.fromtimestamp(int(lines[3].split(': ')[1]))
        purchaseTimestamps.append(timestamp)
        try:
            creds = int(lines[4].split(' credits.')[0].split(' for ')[-1])
        except:
            try:
                creds = int(lines[5].split(' credits.')[0].split(' for ')[-1])
            except:
                creds = 0
        purchaseCredits.append(creds)

allTimestamps = saleTimestamps + dutyTimestamps + purchaseTimestamps

for dataSet in range(5):
    if dataSet == 0:
        timestamps = saleTimestamps
        credits = saleCredits
        plotTitle = "Sales per " + interval + " (credits)"
    elif dataSet == 1:
        timestamps = purchaseTimestamps
        credits = purchaseCredits
        plotTitle = "Purchases per " + interval + " (credits)"
    elif dataSet == 2:
        timestamps = dutyTimestamps
        credits = dutyCredits
        plotTitle = "Duty Token Purchases per " + interval + " (credits)"
    elif dataSet == 3:
        timestamps = dutyTimestamps
        credits = dutyTokens
        plotTitle = "Duty Token Purchases per " + interval + " (tokens)"
    else:
        timestamps = dutyTimestamps
        credits = dutyCPU
        plotTitle = "Duty Token price per " + interval + " (cpu)"


    startYear = min([x.year for x in allTimestamps])
    startMonth = min([x.month for x in allTimestamps if x.year == startYear])
    startDay = min([x.day for x in allTimestamps if x.year == startYear and x.month == startMonth])

    if datetime(startYear,startMonth,startDay) < startDate:
        startYear = startDate.year
        startMonth = startDate.month
        startDay = startDate.day

    endYear = max([x.year for x in allTimestamps])
    endMonth = max([x.month for x in allTimestamps if x.year == endYear])
    endDay = max([x.day for x in allTimestamps if x.year == endYear and x.month == endMonth])

    if datetime(endYear,endMonth,endDay) > endDate:
        endYear = endDate.year
        endMonth = endDate.month
        endDay = endDate.day

    currentDay = startDay
    currentMonth = startMonth
    currentYear = startYear

    daysPerMonthStandard = [31,28,31,30,31,30,31,31,30,31,30,31]
    daysPerMonthLeap = [31,29,31,30,31,30,31,31,30,31,30,31]

    chartData = []

    while True:
        if currentYear % 4 == 0:
            daysPerMonth = daysPerMonthLeap
        else:
            daysPerMonth = daysPerMonthStandard
        while True:
            while True:
                dailyTotal = 0
                count = 0
                for i in range(0,len(credits)):
                    if timestamps[i].year == currentYear and timestamps[i].month == currentMonth and timestamps[i].day == currentDay:
                        dailyTotal += credits[i]
                        count += 1
                if dataSet == 4 and count != 0:
                    chartData.append([datetime(currentYear,currentMonth,currentDay),dailyTotal/count])
                else:
                    chartData.append([datetime(currentYear,currentMonth,currentDay),dailyTotal])
                currentDay += 1
                if currentDay > daysPerMonth[currentMonth-1] or (currentDay > endDay and currentMonth == endMonth and currentYear == endYear):
                    break
            currentDay = 1
            currentMonth += 1
            if currentMonth > 12 or (currentMonth > endMonth and currentYear == endYear):
                break
        currentMonth = 1
        currentYear += 1
        if currentYear > endYear:
            break

    ### For monthly

    if interval == "Month":

        monthlyData = []

        for i in range(0,len(chartData)):
            absMonth = chartData[i][0].month + chartData[i][0].year * 12
            monthlyData.append([absMonth,chartData[i][1]])

        allMonths = set([x[0] for x in monthlyData])
        chartData = []

        for month in range(min(allMonths),max(allMonths)+1):
            if dataSet == 4:
                count = len([x[1] for x in monthlyData if (x[0] == month and x[1] != 0)])
                if count != 0:
                    monthlyTotal = sum([x[1] for x in monthlyData if x[0] == month])/count
                else:
                    if len(chartData) == 0:
                        monthlyTotal = 1000
                    else:
                        monthlyTotal = chartData[-1][1]
            else:
                monthlyTotal = sum([x[1] for x in monthlyData if x[0] == month])
            modMonth = month%12
            if modMonth == 0:
                modMonth = 12
                modYear = int(month/12) - 1
            else:
                modYear = int(month/12)
            chartData.append([datetime(modYear,modMonth,1), monthlyTotal])

    ### For weekly
    elif interval == "Week":

        weeklyData = []

        for i in range(0,len(chartData)):
            #Date 0 for abs week is Jan 1 2017, second most recent year that started on a sunday so we don't get any weirdness from that.
            absWeek = int((chartData[i][0] - datetime(2017,1,1)).days/7)
            weeklyData.append([absWeek,chartData[i][1]])
        
        allWeeks = set([x[0] for x in weeklyData])
        chartData = []

        for week in range(min(allWeeks),max(allWeeks)+1):
            if dataSet == 4:
                count = len([x[1] for x in weeklyData if (x[0] == week and x[1] != 0)])
                if count != 0:
                    weeklyTotal = sum([x[1] for x in weeklyData if x[0] == week])/count
                else:
                    if len(chartData) == 0:
                        weeklyTotal = 1000
                    else:
                        weeklyTotal = chartData[-1][1]
            else:
                weeklyTotal = sum([x[1] for x in weeklyData if x[0] == week])
            weekStartDate = datetime(2017,1,1) + timedelta(days=week*7)
            chartData.append([weekStartDate,weeklyTotal])


    totalSales = sum([x[1] for x in chartData])
    highestDay = max([x[1] for x in chartData])

    cumulative = []
    cumTotal = 0

    for data in chartData:
        cumTotal += data[1]
        cumulative.append([data[0],cumTotal])

    ax = plt.subplot(5,1,dataSet+1)
    
    if dataSet != 4:
        ax.plot([x[0] for x in chartData],[x[1] for x in chartData],color='blue')
        ax2 = ax.twinx()
        ax2.plot([x[0] for x in cumulative],[x[1] for x in cumulative],color='red')
    else:
        ax.plot([x[0] for x in chartData if x[1] != 0],[x[1] for x in chartData if x[1] != 0],color='blue')
    plt.title(plotTitle)
plt.show()