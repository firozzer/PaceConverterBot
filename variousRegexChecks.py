import re, datetime
from pyperclip import copy as cp
import inflect

# regexOfAll = r"""\d+[:|.|,]\d+ *[a-zA-Z]*/[a-zA-Z]+|\d+:\d+.{1,3}\s+.{1,8}\s.{2,15}\(\w+/\w{2}\)|[mikl]{2}\s[o0]? ?[\d']{3,5}\"""" # just for easy copying/testing purposes at pythex.org
global paceUnitOfThisRedditPost
paceUnitOfThisRedditPost = ""

def checkStravaOrGarminSplitsPaceList(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Strava & Garmin Pace Splits images
    """
    paceRegexedFromExtractedTextTypeList = re.findall(r"(splits).*?(mi|km).*?(pace)", extractedText, flags=re.IGNORECASE | re.DOTALL) # returns a list. # this is STrava AND garmin both together
    try: #will throw Index Error in case it is not able to find the desired pattern
        splitsPreFmtgStringified = ' '.join(paceRegexedFromExtractedTextTypeList[0])
    except IndexError: 
        return ""
    if bool(re.search(r'(splits).*?(mi|km).*?(pace)', splitsPreFmtgStringified, flags=re.IGNORECASE|re.DOTALL)): 
        print("Splits image detected (list of paces).")
        splitsPreFormatting = re.findall(r"(splits).*?(mi|km).*?(pace)", extractedText, flags=re.IGNORECASE | re.DOTALL)
        splitsPreFmtgStringified = ' '.join(splitsPreFormatting[0]) # this is used later on to check if existing pace is km or miles
        intactStringPatternInside = re.findall(r"((splits).*?(mi|km).*?(pace))", extractedText, flags=re.IGNORECASE | re.DOTALL) # returns a list. # this is STrava AND garmin both together
        startingIndexOfIntactStringPtrn = extractedText.find(intactStringPatternInside[0][0])
        realDataBeginsFromThisIndex = startingIndexOfIntactStringPtrn + len(intactStringPatternInside[0][0])
        realDataExtracted = extractedText[realDataBeginsFromThisIndex:]
        pacesExtractedFromRealData = re.findall(r"\s\d{1,2}[:']{1}\d{2}", realDataExtracted) # \s at the beginning seems to cover both Nike3 & Strava2 variations. \s needed as otherwise pace incrememnt/decrement gets captured in Nike3. Don't worry about time being captured by regex as i'm cutting the string before regexing.
        strToBeReturned = ""
        p = inflect.engine() # initiazlining the ordinal functionality 
        for index, pace in enumerate(pacesExtractedFromRealData):
            digitsInPace = re.findall(r"\d+", pace) # this returns in 2 groups/list items, so easier to call further on by just index.
            if len(digitsInPace) > 2: continue # a pace with hours detected, doesn't make computing it. This will return None & hence post will get ignored.
            minutesOfPace = int(digitsInPace[0])
            secondsOfPace = int(digitsInPace[1])
            totSecsOfPace = (minutesOfPace*60) + secondsOfPace
            if bool(re.search(r'km', splitsPreFmtgStringified, flags=re.IGNORECASE)): # this will hadnle km to mi conversion of pace
                totSecsOfPaceInMile = round(totSecsOfPace * 1.60934) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInMile)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                originalPace = digitsInPace[0] + ":" + digitsInPace[1]
                strToBeReturned += (f"\n\n{p.ordinal(index+1)} - {originalPace}/km is {convertedPace}/mi.")
            else: # handles mins per mile to mins per km
                totSecsOfPaceInKm = round(totSecsOfPace * 0.621371) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInKm)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                originalPace = digitsInPace[0] + ":" + digitsInPace[1]
                strToBeReturned += (f"\n\n{p.ordinal(index+1)} - {originalPace}/mi is {convertedPace}/km.")
    if strToBeReturned != "": 
        print("Returning generated comment from Strava/Garmin Splits checker.")
        return f"\n\nSplits:{strToBeReturned}"
    return ""        

def checkStrava1stVariation(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Strava Variation 1 images.
    """
    paceRegexedFromExtractedTextTypeList = re.findall(r"\d+[:|.|,]\d+\s?[kmin]{0,3}/[kmiuh]{1,2}", extractedText, flags=re.IGNORECASE) # using \s as a divider instead of a space because sometimes kph/mph is on the next line + space gets covered by \s too. Added n in the first character set in this regex to catch "min/km" in rare images.
    if not paceRegexedFromExtractedTextTypeList: return ""  # checks if the list is empty, meaning no pace detected, in which case return emtpyt string
    strToBeReturned = "" #in case of multiple paces detected i need to append them so doing this
    for paceListItem in paceRegexedFromExtractedTextTypeList:
        if "km/" in paceListItem.lower() or "mi/" in paceListItem.lower(): # handling cycling pace
            #print("this is a cycling speed")
            digitsInPaceTypeList = re.findall(r"\d+[.|,]\d+", paceListItem) # returns a list..
            if "mi" in paceListItem.lower(): # handling mph to kph
                if "," in digitsInPaceTypeList[0]: # handling comma in pace if any
                    digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                    convertedPace = round(float(digitsInPaceTypeListCommaToDot)*1.60934,2)
                    convertedPaceDotToComma = str(convertedPace).replace(".",",")
                    if paceListItem not in strToBeReturned: # duplicate check within same image
                        strToBeReturned += (f"\n\n{paceListItem} is {convertedPaceDotToComma} km/h.")
                else: # if no comma then directly mathematically convert & show result
                    if paceListItem not in strToBeReturned: # duplicate check within same image
                        strToBeReturned += (f"\n\n{paceListItem} is {round((float(digitsInPaceTypeList[0]))*1.60934,2)} km/h.")
            elif "km" in paceListItem.lower(): # handling kph to mph
                if "," in digitsInPaceTypeList[0]: # if comma present in pace
                    digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                    convertedPace = round(float(digitsInPaceTypeListCommaToDot)*0.621371,2)
                    convertedPaceDotToComma = str(convertedPace).replace(".",",")
                    if paceListItem not in strToBeReturned: # duplicate check within same image
                        strToBeReturned += (f"\n\n{paceListItem} is {convertedPaceDotToComma} mi/h.")
                else:
                    if paceListItem not in strToBeReturned: # duplicate check within same image
                        strToBeReturned += (f"\n\n{paceListItem} is {round(float(digitsInPaceTypeList[0])*0.621371,2)} mi/h.")
        else: # handles running pace
            digitsInPaceTypeList = re.findall(r"\d+", paceListItem) # this returns in 2 groups/list items, so easier to call further on by just index.
            if len(digitsInPaceTypeList) > 2: return # a pace with hours detected, doesn't make computing it. This will return None & hence post will get ignored.
            minutesOfPace = int(digitsInPaceTypeList[0])
            secondsOfPace = int(digitsInPaceTypeList[1])
            totSecsOfPace = (minutesOfPace*60) + secondsOfPace
            if totSecsOfPace <= 90 or totSecsOfPace > 2220: continue # +/- times from prev lap's pace get falsely detected, and these are usually less than 90 mins, so this check to skip them. Also 2220 is proper upper limit for /km to /mi secs conversion, if number is above that then further on it goes into hours and fudges up the result. And no sense in coding hour handling as obviously it is a wrong pace in the first place.
            if "k" in paceListItem.lower(): # handling mins per km to mins per mlie. just using k as once m got musrcgzd as n and then it did the else part wtongfully.
                totSecsOfPaceInMile = round(totSecsOfPace * 1.60934) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInMile)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                if paceListItem not in strToBeReturned: #duplicate pace check within same image
                    strToBeReturned += (f"\n\n{paceListItem} is {convertedPace} /mi.")
            else: # handles mins per mile to mins per km
                totSecsOfPaceInKm = round(totSecsOfPace * 0.621371) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInKm)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                if paceListItem not in strToBeReturned: #duplicate pace check within same image
                    strToBeReturned += (f"\n\n{paceListItem} is {convertedPace} /km.")
    #     print(strToBeReturned)
    if strToBeReturned != "": print("Returning generated comment from Strava 1st variation checker.")
    return strToBeReturned

def checkGarmin1stVariation(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Garmin Variation 1 images.
    """
    paceRegexedFromExtractedTextTypeList = re.findall(r"\d+:\d+.{1,3}\s+.{1,8}\s.{2,15}\(\w+/\w{2}\)",extractedText, flags=re.IGNORECASE)
    if not paceRegexedFromExtractedTextTypeList: return ""  # checks if the list is empty, meaning no pace detected, in which case return emtpyt string. Important to return empty string as if None gets returned adding it to a str in ocrNconvert.py will throw an error
    if paceRegexedFromExtractedTextTypeList != None:
        print("Garmin first variation conversion will be done")
        strToBeReturned = ""
        for pace in paceRegexedFromExtractedTextTypeList:
            timeRegxdFromPace = re.findall(r"\d+:\d+", pace)
            unitsRegxedFromPace = re.findall(r"\w+\/\w+", pace)
            unitsRegxedFromPace = unitsRegxedFromPace[0]
            print("Garmin first variation",timeRegxdFromPace, unitsRegxedFromPace)
            minsNSecsRegxdFromTime = re.findall(r"\d+", timeRegxdFromPace[0])
            minsOfPace = int(minsNSecsRegxdFromTime[0])
            secsOfPace = int(minsNSecsRegxdFromTime[1])
            totSecsOfPace = (minsOfPace*60) + secsOfPace
            if totSecsOfPace <= 90 or totSecsOfPace > 2220: continue # +/- times from prev lap's pace get falsely detected, and these are usually less than 90 mins, so this check to skip them. Also 2220 is proper upper limit for /km to /mi secs conversion, if number is above that then further on it goes into hours and fudges up the result. And no sense in coding hour handling as obviously it is a wrong pace in the first place.
            if "k" in unitsRegxedFromPace.lower(): # handles min/km to min/mi
                totSecsOfPaceInMile = round(totSecsOfPace * 1.60934) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInMile)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                originalPace = minsNSecsRegxdFromTime[0] + ":" + minsNSecsRegxdFromTime[1] + "/km" # 0 index is min & 1 index is secs
                if originalPace not in strToBeReturned: # duplicate pace check within same image
                    strToBeReturned += (f"\n\n{originalPace} is {convertedPace}/mi.")
            else: # handles min/mi to min/km
                totSecsOfPaceInKm = round(totSecsOfPace * 0.621371) # 1.6 km = 1 mile & rounding it up.
                paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInKm)) # 90% OTTATT it comes in 0:00:00 format even if 0.
                convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
                originalPace = minsNSecsRegxdFromTime[0] + ":" + minsNSecsRegxdFromTime[1] + "/mi" # 0 index is min & 1 index is secs
                if originalPace not in strToBeReturned: # duplicate pace check within same image
                    strToBeReturned += (f"\n\n{originalPace} is {convertedPace}/km.")
        if strToBeReturned != "": print("Returning generated comment from Garmin 1st Variation checker.")
        return strToBeReturned

def checkNike1stVariation(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Nike Variation 1&2 images.
    """
    global paceUnitOfThisRedditPost
    extractedText += "kl324 jlk23 k m32\n342\n" + paceUnitOfThisRedditPost # doing this just so that i can get the latter variable incorporated into the string when detected.
    paceRegexedFromExtractedTextTypeList = re.findall(r"""\d{1,2}[' ]?\d{2}['"]\B""", extractedText, flags=re.IGNORECASE) 
    if not paceRegexedFromExtractedTextTypeList: return ""  # checks if the list is empty, meaning no pace detected, in which case return emtpyt string
    strToBeReturned = ""
    for pace in paceRegexedFromExtractedTextTypeList:
        digitsInpace = re.findall(r"\d", pace)
        # print(pace,"\n")
        secsOfPace = int(digitsInpace[-2] + digitsInpace[-1])
        if len(digitsInpace) == 3:
            minsOfPace = int(digitsInpace[-3])
        elif len(digitsInpace) > 3: # this also covers 5, which MIGHT occur if it detects that pace icon from the image as a Zero.
            minsOfPace = int(digitsInpace[-4] + digitsInpace[-3]) 
        totSecsOfPace = (minsOfPace*60) + secsOfPace
        if totSecsOfPace <= 90 or totSecsOfPace > 2220: continue # +/- times from prev lap's pace get falsely detected, and these are usually less than 90 mins, so this check to skip them. Also 2220 is proper upper limit for /km to /mi secs conversion, if number is above that then further on it goes into hours and fudges up the result. And no sense in coding hour handling as obviously it is a wrong pace in the first place.
        if "kilo " in extractedText.lower() or "km" in extractedText.lower() or "kм" in extractedText.lower(): # handling mins per km to mins per mile. that final M is a different m char lowercased, not the regular M.
            paceUnitOfThisRedditPost = "kilo"
            totSecsOfPaceInMile = round(totSecsOfPace * 1.60934) # 1.6 km = 1 mile & rounding it up.
            paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInMile)) # 90% OTTATT it comes in 0:00:00 format even if 0.
            convertedPace = f"{paceInHMMSS[-5:-3]}'{paceInHMMSS[-2:]}\""
            originalPace = pace
            if originalPace not in strToBeReturned: # ensures no duplicate pace is re-entered. A single image might have duplicate pace.
                strToBeReturned += (f"\n\n{originalPace} /km is {convertedPace} /mi.")
        elif 'mi' in extractedText.lower() or "мi" in extractedText.lower(): # handles mins per mile to mins per km. That second lowercase m is some weird m char that gets outputted in GCV.
            paceUnitOfThisRedditPost = "mile"
            totSecsOfPaceInKm = round(totSecsOfPace * 0.621371) # 1.6 km = 1 mile & rounding it up.
            paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInKm)) # 90% OTTATT it comes in 0:00:00 format even if 0.
            convertedPace = f"{paceInHMMSS[-5:-3]}'{paceInHMMSS[-2:]}\""
            originalPace = pace
            if originalPace not in strToBeReturned: # ensures no duplicate pace is re-entered. A single image might have duplicate pace.
                strToBeReturned += (f"\n\n{originalPace} /mi is {convertedPace} /km.")
    if strToBeReturned != "": print("Returning generated comment from Nike 1st Variation checker.")
    return strToBeReturned

def checkForMPHorKPH(extractedText):
    """
    Input: Extracted OCR Text (str)
    Output: Reddit Comment containing converted speed (str)

    This handles mph kph kmph miph with numbers in the beginning with either dot or comma
    """
    mphOrKphTypeList = re.findall(r"\d{1,3}[.,]{1}\d{0,3}\s{0,3}[mik]{1,2}ph", extractedText, flags=re.IGNORECASE) # captures 232.32 kph mph kmph miph
    if not mphOrKphTypeList: return "" # checks if the list is empty, meaning no mph kph detected, in which case return emtpyt string
    strToBeReturned = "" #in case of multiple paces detected i need to append them so doing this
    for speedListItem in mphOrKphTypeList:
        digitsInPaceTypeList = re.findall(r"\d+[.|,]\d+", speedListItem) # returns a list..
        if "m" in speedListItem.lower(): # handling mph to kph
            if "," in digitsInPaceTypeList[0]: # handling comma in pace if any
                digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                convertedPace = round(float(digitsInPaceTypeListCommaToDot)*1.60934,2)
                convertedPaceDotToComma = str(convertedPace).replace(".",",")
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{speedListItem} is {convertedPaceDotToComma} kph.")
            else: # if no comma then directly mathematically convert & show result
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{speedListItem} is {round((float(digitsInPaceTypeList[0]))*1.60934,2)} kph.")
        elif "k" in speedListItem.lower(): # handling kph to mph
            if "," in digitsInPaceTypeList[0]: # if comma present in pace
                digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                convertedPace = round(float(digitsInPaceTypeListCommaToDot)*0.621371,2)
                convertedPaceDotToComma = str(convertedPace).replace(".",",")
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{speedListItem} is {convertedPaceDotToComma} mph.")
            else:
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{speedListItem} is {round(float(digitsInPaceTypeList[0])*0.621371,2)} mph.")
    if strToBeReturned != "": print("Returning generated comment from MPH/KPH checker.")
    return strToBeReturned

def checkNike4thVariation(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Nike Variation 4 images. Which are those badges of "Fastest 1k" or "Fastest Mile" etc.
    """
    # global paceUnitOfThisRedditPost
    # extractedText += "kl324 jlk23 k m32\n342\n" + paceUnitOfThisRedditPost # doing this just so that i can get the latter variable incorporated into the string when detected.
    paceRegexedFromExtractedTextTypeList = re.findall(r"""stest {0,2}1k.*\s*.*\s*\d{1,2}:\d{2}|stest\s*mile.*\s*.*\s*.*\s*\d{1,2}:\d{2}""", extractedText, flags=re.IGNORECASE) # the additional /s are for in case GCV output. OTherwise AWS Rekog output needs lesser \s.
    if not paceRegexedFromExtractedTextTypeList: return ""  # checks if the list is empty, meaning no pace detected, in which case return emtpyt string
    strToBeReturned = ""
    for pace in paceRegexedFromExtractedTextTypeList:
        if "1k" in pace.lower():
            paceLookalikes = re.findall(r"\d{1,2}:\d{1,2}", pace)
            digitsInPace = paceLookalikes[-1]
            paceUnit = "km"
        else:
            paceLookalikes = re.findall(r"\d{1,2}:\d{1,2}", pace)
            digitsInPace = paceLookalikes[0]
            paceUnit = "mile"
        # print(pace,"\n")
        secsOfPace = int(digitsInPace[-2] + digitsInPace[-1])
        minsOfPace = int(digitsInPace[:-3])
        totSecsOfPace = (minsOfPace*60) + secsOfPace
        if totSecsOfPace <= 90 or totSecsOfPace > 2220: continue # +/- times from prev lap's pace get falsely detected, and these are usually less than 90 mins, so this check to skip them. Also 2220 is proper upper limit for /km to /mi secs conversion, if number is above that then further on it goes into hours and fudges up the result. And no sense in coding hour handling as obviously it is a wrong pace in the first place.
        if paceUnit == "km": # handling mins per km to mins per mile. that final M is a different m char lowercased, not the regular M.
            # paceUnitOfThisRedditPost = "kilo"
            totSecsOfPaceInMile = round(totSecsOfPace * 1.60934) # 1.6 km = 1 mile & rounding it up.
            paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInMile)) # 90% OTTATT it comes in 0:00:00 format even if 0.
            convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
            originalPace = digitsInPace[-4] + digitsInPace[-3] + digitsInPace[-2] + digitsInPace[-1]
            if originalPace not in strToBeReturned: # ensures no duplicate pace is re-entered. A single image might have duplicate pace.
                strToBeReturned += (f"\n\nFastest 1k: {originalPace} /km is {convertedPace} /mi.")
        else: # handles mins per mile to mins per km. That second lowercase m is some weird m char that gets outputted in GCV.
            # paceUnitOfThisRedditPost = "mile"
            totSecsOfPaceInKm = round(totSecsOfPace * 0.621371) # 1.6 km = 1 mile & rounding it up.
            paceInHMMSS = str(datetime.timedelta(seconds=totSecsOfPaceInKm)) # 90% OTTATT it comes in 0:00:00 format even if 0.
            convertedPace = f"{paceInHMMSS[-5:-3]}:{paceInHMMSS[-2:]}"
            originalPace = digitsInPace[-4] + digitsInPace[-3] + digitsInPace[-2] + digitsInPace[-1]
            if originalPace not in strToBeReturned: # ensures no duplicate pace is re-entered. A single image might have duplicate pace.
                strToBeReturned += (f"\n\nFastest Mile: {originalPace} /mi is {convertedPace} /km.")
    if strToBeReturned != "": print("Returning generated comment from Nike 4th Variation checker.")
    return strToBeReturned

def checkGarmin4thVariation(extractedText):
    """
    Input: OCR Extracted text (str)
    Output: reddit comment (str) or empty str if check fails

    Handles Garmin Variation 4 images, which is cycling speeds.
    """
    speedRegexedFromExtractedTextTypeList = re.findall(r"\d{1,3}[.,]\d{1}.{0,4}\s.{1,20}\s.*mph\)|\d{1,3}[.,]\d{1}.{0,4}\s.{1,20}\s.*kph\)|\d{1,3}[.,]\d{1}.{0,4}\s.{1,20}\s.*мph\)",extractedText, flags=re.IGNORECASE)
    if not speedRegexedFromExtractedTextTypeList: return ""  # checks if the list is empty, meaning no pace detected, in which case return emtpyt string. Important to return empty string as if None gets returned adding it to a str in ocrNconvert.py will throw an error
    # print("Garmin 4th variation conversion will be done")
    strToBeReturned = ""
    for speedListItem in speedRegexedFromExtractedTextTypeList:
        digitsInPaceTypeList = re.findall(r"\d+[.|,]\d+", speedListItem) # returns a list..
        if "mph" in speedListItem.lower() or "мph" in speedListItem.lower(): # handling mph to kph
            if "," in digitsInPaceTypeList[0]: # handling comma in pace if any
                digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                convertedPace = round(float(digitsInPaceTypeListCommaToDot)*1.60934,2)
                convertedPaceDotToComma = str(convertedPace).replace(".",",")
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{digitsInPaceTypeList[0]} mph is {convertedPaceDotToComma} kph.")
            else: # if no comma then directly mathematically convert & show result
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{digitsInPaceTypeList[0]} mph is {round((float(digitsInPaceTypeList[0]))*1.60934,2)} kph.")
        elif "kph" in speedListItem.lower(): # handling kph to mph
            if "," in digitsInPaceTypeList[0]: # if comma present in pace
                digitsInPaceTypeListCommaToDot = digitsInPaceTypeList[0].replace(",",".")
                convertedPace = round(float(digitsInPaceTypeListCommaToDot)*0.621371,2)
                convertedPaceDotToComma = str(convertedPace).replace(".",",")
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{digitsInPaceTypeList[0]} kph is {convertedPaceDotToComma} mph.")
            else:
                if speedListItem not in strToBeReturned: # duplicate speed check within same image
                    strToBeReturned += (f"\n\n{digitsInPaceTypeList[0]} kph is {round(float(digitsInPaceTypeList[0])*0.621371,2)} mph.")
    if strToBeReturned != "": print("Returning generated comment from Garmin 4th Variation checker.")
    return strToBeReturned
