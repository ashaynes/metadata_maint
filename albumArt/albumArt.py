import inspect
import os
import re
import sqlite3 as sq
import tkinter as tk
from collections import defaultdict
from tkinter.messagebox import showinfo

import musicbrainzngs as mb
import numpy as np
from mutagen.id3 import (APIC, COMM, ID3, TALB, TBPM, TCON, TDRC, TIT2, TPE1,
                         TPE2, TPOS, TRCK, USLT, ID3NoHeaderError)
from mutagen.mp3 import MP3, HeaderNotFoundError
from PIL import Image, ImageTk
from skimage.util.shape import view_as_blocks
from unidecode import unidecode

import utils.defaults as defaults
import windows.customWindowSize as windowSize

IMAGE_PATH = "C:\\Users\\Alex\\Pictures\\Downloaded Album Art\\"
count = 0

def addArt(self):
    '''
    Sets the album art for the selected song and any other MP3 that may have the same album and artist.
    If the song album and title match that of the JPEG name and there is no APIC tag, write it to the MP3 else skip it.
    '''
    if os.path.exists(f'{IMAGE_PATH}\\temp'):
        os.chdir(f'{IMAGE_PATH}\\temp')
        if len(os.listdir()) > 0:
            # TODO: create a new window that displays multiple album covers and allows the user to select which one (ONLY!)
            # they want to keep. The selected album cover is formated and moved to the main album cover directory and
            # the others are removed from the temp directory
            showinfo("More Than One Image Downloaded", "More than one image was downloaded for the selected album. Please select your preferred album cover to be saved.")

            # self.downloadAlbumArtWindow = tk.Toplevel()
            # self.downloadAlbumArtWindow.title = "Downloaded Album Art"
            # pos = windowSize.centerWindow(self.downloadAlbumArtWindow, defaults.downloadAlbumArtWidth, defaults.downloadAlbumArtHeight)
            # self.downloadAlbumArtWindow.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))

            # A = np.arrange(4*4).reshape(4,4)
        elif len(os.listdir()) == 1:
            # rename image / remove "_[count]" from file name and move to main folder, create APIC and add to MP3
            f = os.listdir()[0]
            f_rename = re.sub(r'_\d+', '', f)
            os.replace(f, f"{IMAGE_PATH}\\{f_rename}")
            
            self.songCntStr.set(f"Adding album art to '{self.song['TIT2'][0]}'...")
            
            try:
                image_path = "{0}{1} ({2}).jpg".format(IMAGE_PATH, self.song['TALB'][0], self.song['TPE2'][0])
                image_album = self.song['TALB'][0]
                image_artist = self.song['TPE2'][0]
                
                # resize the album art if not 250x250 px
                with Image.open(image_path) as i:
                    height, width = i.size
                if height is not 250 and width is not 250:
                    resizeArt(image_path)

                with open(image_path, "rb") as image:
                    file_image = image.read()
                    imageBytes = bytes(bytearray(file_image))
                
                for song in self.all_music:
                    thisSong = MP3(self.dname + "\\" + song[0])
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
    else:
        os.chdir(f'{IMAGE_PATH}')
        if len(os.listdir()) > 0:
            try:
                image_album = self.song['TALB'][0]
                image_artist = self.song['TPE2'][0]
                image_path = "{0}{1} ({2}).jpg".format(
                    IMAGE_PATH, 
                    image_album, 
                    image_artist)
                
                with Image.open(image_path) as i:
                    width, height = i.size
                if height is not 250 and width is not 250:
                    resizeArt(image_path)

                with open(image_path, "rb") as image:
                    f = image.read()
                    imageBytes = bytes(bytearray(f))
                
                for song in self.all_music:
                    thisSong = MP3(self.dname + "\\" + song[0])
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
        else:
            os.chdir(f'{IMAGE_PATH}')
            if len(os.listdir()) > 0:
                try:
                    image_path = "{0}{1} ({2}).jpg".format(IMAGE_PATH, re.sub(r'\/', '-', self.song['TALB'][0]), re.sub(r'\/', '-', self.song['TPE2'][0]))
                    image_album = image_path.split("\\")[-1].rsplit(" (", maxsplit=1)[0]
                    image_artist = image_path.split("\\")[-1].rsplit(" (", maxsplit=1)[-1].replace(").jpg", "")
                    
                    with open(image_path, "rb") as image:
                        f = image.read()
                        imageBytes = bytes(bytearray(f))
                    
                    for song in self.all_music:
                        thisSong = MP3(self.dname + "\\" + song[0])
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
                    showinfo("Error", f"{e.traceback.print_exc(limit=None, file=None, chain=True)}")
            else:
                showinfo("No Album Art Downloaded", "Sorry! No album art was downloaded for the selected album :(")
    self.getMusic()
        
def downloadArt(self):
    self.songCntStr.set(f"Scraping web for album art for album \'{self.song['TALB'][0]}\' by \'{self.song['TPE2']}\'...")
    # search for releases (albums)
    api_releases = mb.search_release_groups(self.song['TALB'][0], artist=self.song['TPE2'][0])

    artists = defaultdict(list)
    albums = defaultdict(list)
    for r in api_releases['release-group-list']:
        for a in r['artist-credit']:
            if type(a) is dict and 'name' in a['artist'].keys() and 'id' in a['artist'].keys():
                if a['artist']['name'] == self.song['TPE2'][0]:
                    artists['artistname'] = a['artist']['name']
                    artists['artistids'].append(a['artist']['id'])
                    print(f"\n{a['artist']['id']} -> {a['artist']['name']}")

                    if 'release-list' in r.keys():
                        for release in r['release-list']:
                            if 'title' in release.keys() and 'id' in release.keys():
                                # replace all special unicode characters in title
                                release_title = unidecode(release['title'])
                                
                                if release_title == self.song['TALB'][0]:
                                    albums['releaseids'].append(release['id'])
                                    albums['title'] = release_title
                                    artists['albums'] = albums
                                    print(f"--> {release['id']} :: {release_title}")

    # try to get album image for each releaseid [byte-array]. store temporarily until user selects which one to save
    count = 0
    for releaseid in albums['releaseids']:
        self.songCntStr.set(f"Attempting to download album cover(s) for \'{albums['title']}\'...")
        try:
            i = mb.get_image_front(releaseid, 250)
        except mb.ResponseError as e:
            self.songCntStr.set(f"Error downloading cover art: {e}")
            count += 1
        else:
            with open(fr"temp\{self.song['TALB'][0]} ({self.song['TPE2'][0]})_{count}.jpg", "wb") as image:
                image.write(i)

            self.songCntStr.set(fr"Downloaded album cover '{self.song['TALB'][0]} ({self.song['TPE2'][0]})_{count}.jpg'...")
            count += 1

        # create a new window that would display each album cover that was downloaded for the user to choose which
        # one that want to save to the MP3 and write to the database

def extractArt(self):
    '''
    Extract the APIC data from the MP3 file and save to local directory as a JPEG
    '''
    file = self.song_path.get()

    os.chdir("\\".join(file.split("\\")[:-1]))

    song = MP3(file)
    apic_key = [key for key in song.keys() if "APIC" in key][0]
    apic_data = song[apic_key].data
    new_image_name = f"{song['TALB'][0].replace(': ',' - ')} ({song['TPE2'][0]}).jpg"
    
    with open(f"{IMAGE_PATH}{new_image_name}", "wb") as image:
        image.write(apic_data)
        self.songCntStr.set(f"{IMAGE_PATH}{new_image_name} was created and saved to file!")
    
    resizeArt(f"{IMAGE_PATH}{new_image_name}")
    showinfo("Album Art Extracted", f"{IMAGE_PATH}{new_image_name} was created and saved to file!")

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
    Converting image to true JPEG file and resizing to 250x250
    '''
    im = Image.open(file)
    im = im.resize((250, 250), Image.ANTIALIAS)
    if im.mode != "RGB":
        im = im.convert("RGB")
    os.remove(file)
    im.save(file[:-3]+"jpg","JPEG")

def isAlbumArtInFile(file):
    '''
    Determine if album art is in local directory and/or if APIC is present in MP3. If it is, check that it is not a JPEG and convert it to a JPEG file. Else, return False
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
