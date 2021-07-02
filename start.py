#!/usr/bin/python3

import re, requests, threading, time, os, shutil, traceback
from datetime import datetime
import praw, inflect #inflect is to convert numbers into ordinals like 1st 2nd 3rd etc
from pyperclip import copy as cp

from ocrNconvert import ocrTheImage
import creds


# The below two are special ways to represent new lines on Reddit. The 'halfANewLine' is the one you reprodduce in the UI by pressing Shift+Enter, and in markdown it is technically called a new line within same para. The 'newLine' is the normal new line you get on pressing single Enter and it is called a new para techincally in md. Latter is useful when you need to insert multiple new lines.
halfANewLine = "  \n" # don't use this as Reddit official app itself doesn't show it properly. but leaving it still just for future ref.
newLine = "\n\n&#x200B;\n\n" # You can do this f"5 enters after this{newLine*5}5 enters before this" easily using this.
horizontalLine = "\n\n---\n\n" # basically --- on a line by themselves in MD is a horizontal line/rule.

def send_message(message):
    url = f'https://api.telegram.org/bot{creds.bot_token}/sendMessage'
    payload = {'chat_id':creds.telegram_chat_id, 'text': f"""{message}"""}
    requests.post(url,json=payload)

def checkPostsForAnImageWithPaceNComment(sub):
    # print(f"Performing request - {sub} - {time.ctime()}")
    r = requests.get(url=f"https://www.reddit.com/r/{sub}/new/.json", params={'limit':20}, headers={'User-agent': 'PaceConverterBot'})
    # print(f"Performed request - {sub} - {time.ctime()}")
    if r.ok:
        response = r.json()
    else: # i think this error happens when reddit server fails to send a proper response. VSCode Linter is wrong, code works fine, dw.
        print(f"\nReddit unresponsive while trying r/{sub}. This is the error: \"{r.status_code}\". Quitting.")
        quit()
    with open("commentedSubmissionsIDDB.txt") as f: commentedSubmissionsIDDB = f.read()
    with open("nonPaceSubmissionsIDDB.txt") as f: nonPaceSubmissionsIDDB = f.read()
    for item in response['data']['children']:
        if item['data']['id'] not in commentedSubmissionsIDDB and item['data']['id'] not in nonPaceSubmissionsIDDB:
            print("\n\n****************************************")
            print(f"""{time.ctime()}: Checking reddit.com/{item['data']['id']}\n""") 
            # endTime = datetime.now(); print(f"Time it took to check both DBs: {(str(endTime - startTime))[-9:]} secs")
            post_hint = item['data'].get("post_hint", None) # reddit puts "image" if it is one.
            singleImagePost = True # By default all posts tb treated thus. 
            if post_hint == "image": # if reddit classifies it as image, the url field is perfect to go
                imageURL = item['data']['url']
            else:
                if "imgur.com/" in item['data']['url']: # handling imgur URLs with jpg ext missing in the end
                    print("Entered imgur checker")
                    if "imgur.com/a/" in item['data']['url']: # handle Imgur album. Just grabbing the URLs and giving it ahead to the code so that i don't have to refactor the further up code, albeit i do admit this is a kind of a rigamrole.
                        print("Imgur Album detected")
                        # print(f"Performing Imgur ZipAlbum request - {item['data']['url']} - {time.ctime()}")
                        r = requests.get(item['data']['url'] + "/zip") # sometimes user will post imgur album without fw slash in end & sometimes ending with fw slash, but it's ok if if it gets doubled because i tested it irl.
                        # print(f"Performed Imgur ZipAlbum request - {item['data']['url']} - {time.ctime()}")
                        if r.status_code != 200:
                            print(f"Error code {r.status_code} obtained while trying to download Imgur Album zip'ed. Skipping this post.")
                            with open("nonPaceSubmissionsIDDB.txt", "a") as f:
                                f.write(f"{item['data']['id']} ")
                            continue
                        # now if the Imgur Album contains a single image, suffixing zip & downloading lands you the actual jpg/png image. So need to handle those seaparetely.
                        if "zip" in r.headers['Content-Type']: 
                            singleImagePost = False
                            with open(f"{sub}.zip", 'wb') as f:
                                f.write(r.content)
                            shutil.unpack_archive(f"{sub}.zip", sub)
                            fileNames = []
                            for filename in os.listdir(sub):
                                fileNames.append(filename)
                            imageURLs = []
                            if len(fileNames) >= 10: # if greater than 10 photos in Imgur album, skip this post not worth the effort & resources.
                                print("Greater than 10 photos in Imgur Album, not worth the effort or resources, skipping post.")
                                continue
                            for fileName in fileNames:
                                imageURLs.append(f"https://i.imgur.com/{fileName[4:]}") # the index 4 contraction handles max 9 no of images & extensions gets auto detected.
                            shutil.rmtree(sub) # clean up the folder & zip file created to capture the imageURLs.
                            os.remove(f'{sub}.zip')
                        elif "jpg" in r.headers['Content-Type'] or "jpeg" in r.headers['Content-Type']: #i've checked jpg/jpeg irl in browser either works nvm the type
                            contentDisposition = r.headers['Content-Disposition']
                            regexedImageURL = re.findall(r"""filename=["']\w+""", contentDisposition)
                            imageID = regexedImageURL[0][10:]
                            imageURL = "https://i.imgur.com/" + imageID + ".jpg"
                        elif "png" in r.headers['Content-Type']:
                            contentDisposition = r.headers['Content-Disposition']
                            regexedImageURL = re.findall(r"""filename=["']\w+""", contentDisposition)
                            imageID = regexedImageURL[0][10:]
                            imageURL = "https://i.imgur.com/" + imageID + ".png"
                    elif "imgur.com/gallery/" in item['data']['url']: # although it says gallery, these are in my experience only single images, which can be downloaded easily by replacing "gallery" with "a" and appending "/zip" at end.
                        print("TeeeeeeeOOOOOOOOOONNNNNnnnnnnnnnnnnnnnEEEEEEEEEEEEOooooooooooooooooo Imgur Gallery detected, see if it gets handled like a well of water.")
                        imgurID = item['data']['url'][26:] # 26 coz trimming "https://imgur.com/gallery/" portion
                        imageURL = "https://imgur.com/a/" + imgurID + "/zip"
                    else:
                        print("Single imgur image")
                        imageURL = f"{item['data']['url']}.jpg"
                elif "https://preview.redd.it" in item['data']['selftext']: # user either posted image in the self post or has linked to a 3rd party website from where Reddit has generated a preview url
                    print("Selftext images detected.")
                    selftext = item['data']['selftext']
                    urlsFromSelfTextTypeList = re.findall(r"https://preview.redd.it/[\w]+\.\w{3,4}", selftext) # 3 for jpg/png and 4 if jpeg
                    imageURLs = [f"https://i.redd.it/{url[24:]}" for url in urlsFromSelfTextTypeList] # sending it out as a list jic user posted multiple images
                    singleImagePost = False
                elif item['data'].get("is_gallery", False) == True: # some posts are in gallery form idk. So as last resort trying to grab images from gallery.
                    postJSONhasNotYetBeenGeneratedProperly = False
                    currentEpochTime = int(time.time())
                    postCreatedEpochTime = item['data']['created_utc']
                    if currentEpochTime - postCreatedEpochTime <= 300: # jumps to next post if Reddit Gallery post is less than 5 mins old. This is to avoid incorrect image order extraction. The image order JSON takes some time to correctly order the images, if i do it too quickly then image order is wrong.
                        print(">>>><<<< Reddit Gallery detected but still less than 5 mins old, so will process on next cron run.")
                        continue
                    imageOrder = []
                    try:
                        for image in item['data']['gallery_data']['items']: # picking from this specific location because this is the correct order of images as shown to user. Helpful to me to parse these images in order because thereafter i give out paces with each image numbered. Earlier i used to extract URLs from media_metadata json, but it is randomly ordered
                            media_id = image['media_id']
                            try: # if a post has JUST been created, it throws key error, which gets resolved in the next running of the script autoly.
                                if item['data']['media_metadata'][media_id]['status'] != "failed": # usually it will be "valid" but sometimes this is "failed" which causes a wrongful detection of KeyError. So if failed, move on to next image in the same gallery. Eg post: reddit.com/lspwqs
                                    imageExtension = item['data']['media_metadata'][media_id]['m']
                                else:
                                    continue
                            except KeyError:
                                postJSONhasNotYetBeenGeneratedProperly = True
                                print("Post JSON not yet properly built, will process on next cron run.")
                                break
                            imageDetails = media_id + " " + imageExtension
                            imageOrder.append(imageDetails)
                    except TypeError as e: # catching this error whenever it happens next time
                        send_message("Reddit gallery error recurring. Simply comment this print line to stop getting notifications")
                        print(f"Reddit gallery error happnd. Skipping this post prmntnly. Exact error: {e}")
                        with open("nonPaceSubmissionsIDDB.txt", "a") as f:
                            f.write(f"{item['data']['id']} ")
                        continue
                    if postJSONhasNotYetBeenGeneratedProperly == True: continue # continues to next post. Will process this post on the next script running by which time JSON should be properly built up.
                    imageURLs = [f"https://i.redd.it/{img[:-11]}.jpeg" if "image/jpeg" in img else \
                                f"https://i.redd.it/{img[:-10]}.png" if "image/png" in img else \
                                f"https://i.redd.it/{img[:-10]}.jpg" for img in imageOrder] # append the media id to that Italian URL & append a extension as appropriate thereafter to form image URL. 
                    singleImagePost = False
                else:
                    print(f"""r/{sub} Not an image: "{item['data']['title'][:35]}".""") #truncating to 35 as i don't want to see full
                    with open("nonPaceSubmissionsIDDB.txt", "a") as f:
                        f.write(f"{item['data']['id']} ")
                    continue

            if singleImagePost: # handles single image posts.
                # print(f"Performing SingleImageReq request - {imageURL} - {time.ctime()}")
                r = requests.get(imageURL) 
                # print(f"Performed SingleImageReq request - {imageURL} - {time.ctime()}")
                if r.status_code == 404: # 404 gets thrown when user has deleted post. Important to catch it as otherwise bad image data gets fed to GCV causing in program crash
                    print(f"{imageURL} has been deleted by OP/admin. Continuing to next post.")
                    with open("nonPaceSubmissionsIDDB.txt", "a") as f:
                        f.write(f"{item['data']['id']} ")
                    continue # continues onto the next post in the for loop.
                with open(f"{sub}.jpg", 'wb') as f:
                    f.write(r.content)
                commentToBeMade = ocrTheImage(sub, imageURL)
            else: # handling multi-image posts
                commentToBeMade = "" 
                noOfImagesContainingUniquePace = 0 # unused currently
                p = inflect.engine() # initiazlining the ordinal functionality i geuss
                for idx, imageURL in enumerate(imageURLs):
                    # print(f"Performing MultiImg request - {imageURL} - {time.ctime()}")
                    r = requests.get(imageURL)
                    # print(f"Performed MultiImg request - {imageURL} - {time.ctime()}")
                    if r.status_code == 404: # 404 gets thrown when user has deleted post. Important to catch it as otherwise bad image data gets fed to GCV causing in program crash
                        print(f"{imageURL} has been deleted by OP/admin. Continuing to next post.")
                        break # breaks out of for loop looping over images in this post.
                    with open(f"{sub}.jpg", 'wb') as f:
                        f.write(r.content)
                    resultRecvdFromOCRnConvertFile = ocrTheImage(sub, imageURL) # sending URL of the image as well because many times if my code fails it keeps unnecessarily using GCV, so to avoid that passing this in & writing down the URL to file after each GCV run
                    if resultRecvdFromOCRnConvertFile != None and resultRecvdFromOCRnConvertFile != "" : # do following only if some pace is returned from the function
                        if resultRecvdFromOCRnConvertFile not in commentToBeMade: # eg) user posts 2 images, both have same pace but photos are different. So pace will be repeated twice in comment. To avoid that repititon i'm doing this. Eg post: lgekj4 (Mario)
                            commentToBeMade += f"{p.ordinal(idx+1)} Image:" + resultRecvdFromOCRnConvertFile
                            if idx < (len(imageURLs)-1): commentToBeMade += horizontalLine
                            noOfImagesContainingUniquePace += 1
                            # print(f"No of images contng unique paces is {noOfImagesContainingUniquePace}")
                    time.sleep(2) # sleep 2 secs to avoid overloading GCV
                if noOfImagesContainingUniquePace == 1:
                    # print(f"entered clipper block, {noOfImagesContainingUniquePace}")
                    # print(f"comment at start", commentToBeMade)
                    if commentToBeMade[:10] == "1st Image:": # will remove "1st Image" if only 1st image's pace is being converted. However, if only pace being converted is that of 2nd/3rd/4th/etc, the ordinal prefix will be retained for that image. More user-friendly that way.
                        commentToBeMade = commentToBeMade[10:] # removes "1st Image:" 
                    commentToBeMade = commentToBeMade.replace(horizontalLine,'') # remove the horizontal line if it is only a single image's pace being shown
                    # print(f"comment at end", commentToBeMade)

            if commentToBeMade == None or commentToBeMade == "": # in case no pace found in the image. Also other scenarios (such as no text at all in image). Sometimes i'll get None & sometimes "" so checking both.
                with open("nonPaceSubmissionsIDDB.txt", "a") as f:
                    f.write(f"{item['data']['id']} ")
                print(f"""r/{sub} No pace detected in: "{item['data']['title'][:35]}".""")
                continue
            
            reddit = praw.Reddit(client_id=creds.client_id,client_secret=creds.client_secret,user_agent="PaceConverterBot", username=creds.username,password=creds.password)
            submissionToBeCommentedOn = reddit.submission(id=item['data']['id'])
            submissionToBeCommentedOn.reply(commentToBeMade)
            #send_message(f"""Yo, i've commented on https://www.reddit.com{item['data']['permalink']}""")
            print(f"""YESSSSSSSSSSSSSSSSSSS r/{sub} - "{commentToBeMade}" commented on "{item['data']['title']}".""")
            with open("commentedSubmissionsIDDB.txt", "a") as f:
                    f.write(f"{item['data']['id']} ")
            # quit() # quit if ever a comment is made so that i don't spam the 10 min comment rule of reddit & get the bot dieded.
            time.sleep(20) # sleep long to avoid too many comments within short time

os.chdir("/home/ubuntu/") # this is because script is running inside venv (on AWS), so creds.json & numberofTime.txt files don't get found if i don't do this.

subs = ['ultrarunning', 'nikerunclub', 'strava', 'stravaactivities', 'stravaart', 'garmin']
#subs = ['garmin']
for sub in subs:
    checkPostsForAnImageWithPaceNComment(sub)
    # threading.Thread(target=checkPostsForAnImageWithPaceNComment, args=(sub,)).start() #need to pass in args as tuple, & if only 1 then comma at end is compulsory
    time.sleep(1) # sleep 1 sec to avoid overloading reddit limits
