import re, datetime, os, io, time
try:
    from PIL import Image
except:
    import Image

import pytesseract
from pyperclip import copy as cp

from variousRegexChecks import *
import creds

def detectTextUsingAWSRekognition(path, imageURL): # go to Billing page and there it shows the images out of5000 procesed/ month.
    """
    Input: path to image file (str)
    Output: text found in image (str)

    Detects text in the file using AWS Rekognition. LIMITATION: Rekog is able to detect ONLY 50 WORDS PER IMAGE :(
    """
    import base64, boto3 #boto3 is AWS Python API iThink
        
    # to finally get it working, i followed the instrucs in AWS Rekog docs. Created an IAM user acc as per its instructions but realized was no need & could've done in my AWS root anyway, but as per their best practice it is better to create sepearte IAM accounts for specific tasks and limit the authority of the IAM accs to specific tasks like Rekog or EC2.
    # currently i gave this Administrator IAM account full administrative rights so kinda doesn't make sense, better i give it access only to Rekognition API for it to be safer. Anyway, creating this IAM is optional, not really need to do it just best prac.
    # then i copied the code from here: https://docs.aws.amazon.com/rekognition/latest/dg/text-detecting-text-procedure.html and tried to bruteforce my way through it. Even this Getting Started code helped: https://docs.aws.amazon.com/rekognition/latest/dg/images-bytes.html
    # then i brute forced those codees and got errors for "region" and "creds not found". which were solved by the SO Gods, God blessem.

    os.chdir("/home/ubuntu") # this is because script is running inside venv (on AWS), so creds.json & numberofTime.txt files don't get found if i don't do this.

    with open("nuOfTimesOCRused.txt") as f: 
        nuOfTimesOCRusedAndURLsBrowsed = f.read() # record my free usage of AWS Rekog, 5000 images a month is free then chargeable :OO Also recroding URLs that have already been processed so that if some error in code & it keeps looping on a specific URL, at least GCV usage isn't wasted.
    countAndURLSeparated = nuOfTimesOCRusedAndURLsBrowsed.split("\n")
    nuOfTimesOCRused = int(countAndURLSeparated[1]) # AWS Rekog usage is on the 2nd line, 1st line is GCV usage
    if nuOfTimesOCRused > 1000: 
        print("AAAAAAAAAAAAIIIIIIIIIIIIIIIILLLLLLLLLLLLLLAAAAAAAAAAAAAAAAAAAAAA AWS Rekog usage reached > 1000 images, limit is 5000 pm free :OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
    if nuOfTimesOCRused > 4000: 
        print("AWS Rekog usage count reached 4000, suspending further processes until manual humanity override.")
        return ""

    # startTime = datetime.datetime.now()
    if f"{imageURL} aws" in nuOfTimesOCRusedAndURLsBrowsed: # recording & checking AWS/GCV operation separately as in current model i'm using GCV ONLY if >49 words detected in image.
        print("AWS Rekog being re-used for same image, check ID above & sort it out.")
        return ""
    # endTime = datetime.datetime.now(); print(f"Time it took to check OCR'd URLs: {(str(endTime - startTime))[-9:]} secs")

    client=boto3.client('rekognition', region_name=creds.region_name, \
                        aws_access_key_id=creds.aws_access_key_id, aws_secret_access_key=creds.aws_secret_access_key)
    
    # do the recording of URL & usage count BEFORE you make the call because sometimes call to AWS results in error which halts the script & so usage doesn't get recorded and worse it keeps doing the same URL again and again.
    nuOfTimesOCRused += 1
    countAndURLSeparated[1] = str(nuOfTimesOCRused)
    countAndURLSeparated.append(imageURL + " aws") # recording & checking AWS/GCV operation separately as in current model i'm using GCV ONLY if >49 words detected in image.
    countAndURLSeparatedStringified = "\n".join(countAndURLSeparated)
    with open("nuOfTimesOCRused.txt", "w") as f: 
        f.write(countAndURLSeparatedStringified)

    # print(f"Performing AWS Rekog request - {imageURL} - {time.ctime()}")
    with open(f"{path}.jpg", 'rb') as image:
        response = client.detect_text(Image={'Bytes': image.read()})
    # print(f"Performed AWS Rekog request - {imageURL} - {time.ctime()}")

    extractedText = ""
    wordCount = 0
    for text in response['TextDetections']: # as per my understanding, it gives results by "LINE" & "WORD" 2 types only. So this code will just take by "LINE". Because "WORD" listings are already captured in "LINE" & it just repeats the stuff if i don't filter it out.
            if text['Type'] == "LINE":
                extractedText += text['DetectedText'] + "\n" # new line is correct delimiter since i'm grabbing the "LINES" from image
            if  text["Type"] == "WORD":
                wordCount+=1

    if wordCount >= 49: # AWS Rekog has a limit of doing 50 words per image only.
        print(">= 49 words detected. Letting GCV handle this one.")
        return """~(^Let GCV handle this.$^#"""

    if extractedText == "": 
        print(f'No text detected in {imageURL}')
    else: 
        print("AWS Rekog Output:\n", extractedText)
    return extractedText

def detectTextUsingGoogleCloudVision(path, imageURL):
    """
    Input: path to image file (str)
    Output: text found in image (str)

    Detects text in the file using Google Cloud Vision. If GCV throws an error, just prints the error on screen & skips the specific image. 
    """
    import io, os
    from google.cloud import vision
    
    os.chdir("/home/ubuntu") # this is because script is running inside venv (on AWS), so creds.json & numberofTime.txt files don't get found if i don't do this.

    with open("nuOfTimesOCRused.txt") as f: 
        nuOfTimesOCRusedAndURLsBrowsed = f.read() # record my free usage of GCV, 1000 images a month is free then chargeable $1.5 per imagee :OO Also recroding URLs that have already been processed so that if some error in code & it keeps looping on a specific URL, at least GCV usage isn't wasted.
    countAndURLSeparated = nuOfTimesOCRusedAndURLsBrowsed.split("\n")
    nuOfTimesOCRused = int(countAndURLSeparated[0])
    if nuOfTimesOCRused > 900: 
        print("AAAAAAAAAAAAIIIIIIIIIIIIIIIILLLLLLLLLLLLLLAAAAAAAAAAAAAAAAAAAAAA GCV usage reached > 900 images, limit is 1000 pm free :OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
    if nuOfTimesOCRused > 980: 
        print("GCV count reached 980, suspending further GCV processes until manual humanity override.")
        return ""

    # startTime = datetime.datetime.now()
    if f"{imageURL} gcv" in nuOfTimesOCRusedAndURLsBrowsed: # recording & checking AWS/GCV operation separately as in current model i'm using GCV ONLY if >49 words detected in image.
        print("GCV being re-used for same image, check ID above & sort it out.")
        return ""
    # endTime = datetime.datetime.now(); print(f"Time it took to check OCR'd URLs: {(str(endTime - startTime))[-9:]} secs")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=r"/home/ubuntu/credsgcv.json"
    client = vision.ImageAnnotatorClient()

    with io.open(f"{path}.jpg", 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    # do the recording of URL & usage count BEFORE you make the call because sometimes call to GCV results in error which halts the script & so usage doesn't get recorded and worse it keeps doing the same URL again and again.    
    nuOfTimesOCRused += 1
    countAndURLSeparated[0] = str(nuOfTimesOCRused)
    countAndURLSeparated.append(imageURL + " gcv") # recording & checking AWS/GCV operation separately as in current model i'm using GCV ONLY if >49 words detected in image.
    countAndURLSeparatedStringified = "\n".join(countAndURLSeparated)
    with open("nuOfTimesOCRused.txt", "w") as f: 
        f.write(countAndURLSeparatedStringified)

    # print(f"Performing GCV request - {imageURL} - {time.ctime()}")
    response = client.text_detection(image=image)
    # print(f"Performed GCV request - {imageURL} - {time.ctime()}")

    texts = response.text_annotations
    if response.error.message:
        print(f"""GCV threw this error "{response.error.message}" \nBad image URL is this: {imageURL} \nSkipping this image.""")
        return ""

    if texts != []: # return underneath thing ONLY if texts is not empty. Texts will be empty when there is no text in the image
        print("GCV output: ")
        print(texts[0].description)
        return texts[0].description # returns a string
    print(f'No text detected in {imageURL}')   
    return ""

def ocrTheImage(path, imageURL):
    """
    Input: Image name/path without extension (str)
    Output: Comment for a Single image that has been processed (str) or empty str if nothing found
    """
    #pytesseract.pytesseract.tesseract_cmd = r"D:\Program Files\Tesseract-OCR\tesseract.exe"
    # extractedText = pytesseract.image_to_string(Image.open(f'{path}.jpg'))
    # if checkStravaOrGarminSplitsPaceList(extractedText): #check firstly for this type of "Strava splits pace list" image as it false positively gets detected in the next line of regex
    #     paceRegexedFromExtractedTextTypeList = re.findall(r"(splits).*?(mi|km).*?(pace)", extractedText, flags=re.IGNORECASE | re.DOTALL)
    #     splitsPreFmtgStringified = ' '.join(paceRegexedFromExtractedTextTypeList[0]) # this is used later on to check if existing pace is km or miles
    #     convertedPace = converPaceForStravaPaceList(extractedText, splitsPreFmtgStringified)
    #     return convertedPace
    # commentForThisImage = ("" + checkStrava1stVariation(extractedText)
    #                     + checkGarmin1stVariation(extractedText) 
    #                     + checkNike1stVariation(extractedText) 
    #                     + checkForMPHorKPH(extractedText)
    # )

    # if commentForThisImage == "": # checks if this list is empty, which means either the pace on image is unextractable by Tesseract, or image doesn't contain any pace at all. So just double checking with GCV as last resort.
    #     print("Trying Google Cloud Vision...")

    #if os.path.getsize(f"{path}.jpg") <= 5_000_000: # if file size greater than 5 MB, return "" so that it continues to next image in post / next post
        #extractedText = detectTextUsingAWSRekognition(path, imageURL)
    #else:
        #print("File size greater than 5 MB, AWS Rekog cannot accept it as it has a limit of 5 MB only. Continuing to next image/post.")
    extractedText = """~(^Let GCV handle this.$^#"""

    if extractedText == """~(^Let GCV handle this.$^#""":
        # print("GCVVVVVVVVVVVVVVVV is handling this.")
        extractedText = detectTextUsingGoogleCloudVision(path, imageURL)

    commentForThisImage = checkStravaOrGarminSplitsPaceList(extractedText) # checks for this kind of image first as it causes false positives in further code if not checked beforehand
    if commentForThisImage != "":
        return commentForThisImage

    commentForThisImage = ("" + checkStrava1stVariation(extractedText)
                + checkGarmin1stVariation(extractedText) 
                + checkNike1stVariation(extractedText) 
                + checkForMPHorKPH(extractedText)
                + checkNike4thVariation(extractedText)
                + checkGarmin4thVariation(extractedText)
    )
    return commentForThisImage
