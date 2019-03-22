import os
import inspect
from PIL import Image, ImageTk
from mutagen.id3 import ID3, TRCK, TCON, TPOS, TALB, TIT2, TPE1, TPE2, TDRC, APIC, COMM, USLT, TBPM, ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from tkinter.messagebox import *
import musicbrainzngs as mb
from collections import defaultdict
from unidecode import unidecode
import re
import tkinter as tk
import sqlite3 as sq
import blowfish

import windows.customWindows as windows
import helpers.defaults as defaults

IMAGE_PATH = "C:\\Users\\Alex\\Pictures\\Downloaded Album Art\\"
count = 0

def addArt_Single(info):
    s = info[0]
    
    if isAlbumArtInFile(s.song_path.get()):
        try:
            image_path = "{0}{1} ({2}).jpg".format(IMAGE_PATH, s.song['TALB'][0], s.song['TPE2'][0])
            image_album = image_path.split("\\")[-1].rsplit(" (", maxsplit=1)[0]
            image_artist = image_path.split("\\")[-1].rsplit(" (", maxsplit=1)[-1].replace(").jpg", "")
            
            with open(image_path, "rb") as image:
                f = image.read()
                imageBytes = bytes(bytearray(f))
            
            for song in s.all_music:
                thisSong = MP3(s.dname + "\\" + song[0])
                TALB_found = [key.find("TALB") for key in thisSong.keys()]
                TPE2_found = [key.find("TPE2") for key in thisSong.keys()]
                APIC_found = [key.find("APIC") for key in thisSong.keys()]
                
                # do nothing if the APIC already exists in the MP3 and the JPEGs match
                if 0 in APIC_found:
                    for tag in thisSong.keys():
                        if "APIC" in tag:
                            key = tag
                            currentAPIC = thisSong[key].data
                            if currentAPIC == imageBytes:
                                break
                # add the JPEG to APIC if there is no APIC tag in the MP3 and the album and artist names match
                else:
                    if 0 in TALB_found and 0 in TPE2_found:
                        if thisSong['TALB'][0] == image_album and thisSong['TPE2'][0] == image_artist:
                            thisSong['APIC'] = APIC(encoding=3, mime=u'image/jpeg', type=3, desc=thisSong['TALB'][0],
                                                    data=imageBytes)
                            thisSong.save()
        
        except Exception as e:
            showinfo("Error", f"{inspect.currentframe().f_code.co_name} - {e}")
        finally:
            # write album art to database
            conn = sq.connect("C:\\Users\\Alex\\Dropbox\\Software\\Music Metadata Software\\albumart.db")
            conn.execute(f"REPLACE INTO albumart (album_title, album_artist, album_data) VALUES ({image_album}, "
                         f"{image_artist}, {imageBytes})")
            conn.commit()
            conn.close()
            
            s.songCntStr.set(f"Album art added to \'{s.song['TIT2'][0]}\'!")
            s.getMusic()

def addArt(info):
    '''
    Sets the album art for the selected song and any other MP3 that may have the same album and artist.
    If the song album and title match that of the JPEG name and there is no APIC tag, write it to the MP3 else skip it.
    '''
    s = info[0] # self
    master = info[1]

    if count > 1:
        # TODO: need to design a window to dynamically place the album arts that
        #  were downloaded for user to select one and save (only do if more
        #  than one image is downloaded)
        s.albumartWin = tk.Toplevel()
        # change the heading depending on the genre type
        s.albumartWin.title("Downloaded Album Art")
        pos = windows.centerWindow(s.saveLDWin, defaults.albumartWinWidth, defaults.albumartWinHeight)
        s.albumartWin.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))
    else:
        # rename image / remove "_[count]" from file name and move to main folder
        os.chdir(f'{IMAGE_PATH}\\temp')
        f = os.listdir()[0]
        f_rename = re.sub('_\d+', '', f)
        
        os.rename(f, f"{IMAGE_PATH}\\{f_rename}")

    # clear all other images from "temp" folder
    os.chdir(f"{IMAGE_PATH}\\temp")
    for file in os.listdir():
        os.remove(file)

    master.config(cursor="watch")
    master.update()

    s.songCntStr.set(f"Adding album art to '{s.song['TIT2'][0]}'...")
    addArt_Single(info)
    
def downloadArt(s, song):
    s.songCntStr.set(f"Scraping web for album art for \'{song['TALB'][0]}\' by \'{song['TPE2']}\'...")
    # search for releases (albums)
    api_releases = mb.search_release_groups(song['TALB'][0])

    # check if 'artistid' is present in COMM tag
    if 'COMM::XXX' in song.keys():
        artistid = song['COMM::XXX']
    else:
        artists = defaultdict(list)
        albums = defaultdict(list)
        comments = ""
        for r in api_releases['release-group-list']:
            for a in r['artist-credit']:
                if type(a) is dict and 'name' in a['artist'].keys() and 'id' in a['artist'].keys():
                    if a['artist']['name'] == song['TPE2'][0]:
                        artists['artistname'] = a['artist']['name']
                        artists['artistids'].append(a['artist']['id'])
                        print(f"\n{a['artist']['id']} -> {a['artist']['name']}")

                        if 'release-list' in r.keys():
                            for release in r['release-list']:
                                if 'title' in release.keys() and 'id' in release.keys():
                                    # replace all special unicode characters in title
                                    release_title = unidecode(release['title'])
                                    
                                    if release_title == song['TALB'][0]:
                                        albums['releaseids'].append(release['id'])
                                        albums['title'] = release_title
                                        artists['albums'] = albums
                                        print(f"--> {release['id']} :: {release_title}")

        # try to get album image for each releaseid [byte-array]. store temporarily until user selects which one to save
        count = 0
        for releaseid in albums['releaseids']:
            s.songCntStr.set(f"Attempting to download album cover(s) for \'{albums['title']}\'...")
            try:
                i = mb.get_image_front(releaseid, 250)
            except mb.ResponseError as e:
                s.songCntStr.set(f"Error downloading cover art: {e}")
                count += 1
            else:
                with open(f"temp\\{song['TALB'][0]} ({song['TPE2'][0]})_{count}.jpg", "wb") as image:
                    image.write(i)
    
                s.songCntStr.set(f"Downloaded album cover \'{song['TALB'][0]} ({song['TPE2'][0]})_{count}.jpg\'...")
                count += 1

        # create a new window that would display each album cover that was downloaded for the user to choose which
        # one that want to save to the MP3 and write to the database

def extractArt(slf):
    '''
    Extract the APIC data from the MP3 file and save to local directory as a JPEG
    '''
    file = slf.song_path.get()

    os.chdir("\\".join(file.split("\\")[:-1]))

    song = MP3(file)
    for key in song.keys():
        if "APIC" in key:
            apic_data = song[key].data
            with open(f"{IMAGE_PATH}{song['TALB'][0].replace(': ',' - ')} ({song['TPE2']}).jpg", "wb") as image:
                image.write(apic_data)
                slf.songCntStr.set(f"{IMAGE_PATH}{song['TALB'][0].replace(': ',' - ')} ({song['TPE2']}).jpg was created and saved to file!")
                print(f"{IMAGE_PATH}{song['TALB'][0].replace(': ',' - ')} ({song['TPE2']}).jpg was created and saved to file!")

            resizeArt(f"{IMAGE_PATH}{song['TALB'][0].replace(': ',' - ')} ({song['TPE2']}).jpg")
            break

# Images are loaded all over the place! Consolidate into a method call, passing the object and the file name (if applicable)
#  --> Lines: 285, 525, 748
# def load(obj):
#     s = obj
#     s.albumart = ImageTk.PhotoImage(Image.open(s.default).resize((194,194), Image.ANTIALIAS))

#     print("Image can \'open\'")

def removeArt(info):
    '''
    Removes the album art (APIC tag) from MP3 file
    '''
    s = info[0] # self
    master = info[1]
    tag = info[2]

    s.songCntStr.set(f"Removing album art from \'{s.song['TIT2']}\'...")
    master.update()
    
    s.song.pop(tag)
    s.song.save()
    s.getMusic()

def resizeArt(file):
    '''
    Converting image to true JPEG file and resizing, defaults to 250x250
    '''
    im = Image.open(file)
    im = im.resize((250, 250), Image.ANTIALIAS)
    if im.mode != "RGB":
        im = im.convert("RGB")
    os.remove(file)
    im.save(file[:-3]+"jpg","JPEG")

def isAlbumArtInFile(file):
    '''
    Determine if album art is in local directory. If it is, check that it is not a JPEG, convert it to a JPEG file
    '''
    os.chdir(IMAGE_PATH)

    if file is "":
        return False
    else:
        try:
            song = MP3(file)
            albumArtTitle = "{} ({})".format(song['TALB'][0], song['TPE2'][0])
            albumArtPresent = [albumArtTitle in file for file in os.listdir()]
            
            if True in albumArtPresent:
                albumArtFound = os.listdir()[albumArtPresent.index(True)]
                if not(albumArtFound.endswith("jpg")):
                    resizeArt(albumArtFound)
                return True
            else:
                return False
        except KeyError as e:
            print ("Error in key: {}".format(e))
            return False