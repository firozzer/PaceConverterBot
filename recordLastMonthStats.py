#!/usr/bin/python3

import os
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("nuOfTimesOCRused.txt") as f:
    dataFromFile = f.read()
dataFromFile = dataFromFile.split('\n')
gcvUsage = dataFromFile[0]
awsRekUsage = dataFromFile[1]

# saving past month's info to stats file
lastMonth = datetime.now().month - 1 
if lastMonth == 0: # if now() is 1/1/yr then spl attn reqd
    lastMonth = 12
    yearOfMonth = datetime.now().year - 1
else:
    yearOfMonth = datetime.now().year
with open("usageStatsOfAPIs.txt", "a") as f:
    f.write(f'{lastMonth} {yearOfMonth} - {gcvUsage} {awsRekUsage}\n')

# resetting nuOfTimes.txt file
dataFromFile[0], dataFromFile[1] = '0', '0'
with open("nuOfTimesOCRused.txt", "w") as f:
    f.write('\n'.join(dataFromFile))
