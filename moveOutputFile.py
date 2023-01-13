#!/usr/bin/python3.8

# i have no clue why i made this when i made this lmao

import datetime, os, shutil, string

today = datetime.datetime.now()
month = today.strftime("%B")[:3]
date = today.strftime("%d")[:3]
newFileName = month.lower() + date

# os.chdir("C:/users/firoz/Desktop")
destinationFolder = "oldoutputfiles"
existingFiles = [f for f in os.listdir(destinationFolder) if os.path.isfile(os.path.join(destinationFolder, f))]

if any(newFileName in oldFilenames for oldFilenames in existingFiles):
    alphabets = list(string.ascii_lowercase)
    oldFileNames = []
    for fileName in existingFiles:
        if newFileName in fileName:
            fileSuffix = fileName[-5]
    newFileSuffix = alphabets[(alphabets.index(fileSuffix) + 1)]
    finalFileName = f"{newFileName}{newFileSuffix}.txt"
else:
    finalFileName = f"{newFileName}a.txt"

print(f"{finalFileName} created.")
shutil.move('output.txt', f'oldoutputfiles/{finalFileName}')
# shutil.copyfile('output.txt', f'oldoutputfiles/{finalFileName}')
# os.remove("output.txt")
