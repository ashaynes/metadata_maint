import os
from PIL import Image
from mutagen.mp3 import *
from tkinter.messagebox import *

if os.name == "nt":
    imageFilePath = "C:\\Users\\Alex\\Documents\\Downloaded Album Art\\"
else:
    imageFilePath = "/home/alex/Documents/Downloaded Album Art/"


def extract(file):
    if os.name == "nt":
        os.chdir("\\".join(file.split("\\")[:-1]))
    else:
        os.chdir("/".join(file.split("/")[:-1]))

    song = MP3(file)
    for key in song.keys():
        if "APIC" in key:
            apic_data = song[key].data
            with open("{0} ({1}).jpg".format(imageFilePath + song['TALB'][0], song['TPE2']), "wb") as image:
                image.write(apic_data)
                
            im = Image.open("{0} ({1}).jpg".format(imageFilePath + song['TALB'][0], song['TPE2']))
            im = im.resize((250, 250), Image.ANTIALIAS)
            if im.mode != "RGB":
                im.convert("RGB")
            im.save("{0} ({1}).jpg".format(imageFilePath + song['TALB'][0], song['TPE2']), "JPEG")
            break


def albumArtInFile(file):
    os.chdir(imageFilePath)

    if file is "":
        return False
    else:
        try:
            song = MP3(file)
            albumArtTitle = "{} ({})".format(song['TALB'][0], song['TPE2'][0])
            albumArtPresent = [albumArtTitle in file for file in os.listdir()]

            if True in albumArtPresent:
                return True
            else:
                return False
        except KeyError as e:
            return False
