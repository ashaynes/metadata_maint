import os
from mutagen.mp3 import *
from mutagen.id3 import TALB, TPE2, TPE1, TCON, TRCK, TIT2, TPOS, TDRC
import subprocess

def fixPodcasts():
    basePath = "C:\\Users\\Alex\\Music\\Sword and Scale"
    
    os.chdir(basePath)
    directories = os.listdir()

    # check for recently downloaded podcasts, moves file to correct folder or creates folder and then move the file
    for directory in directories:
        if directory.endswith("mp3"):
            podcast = MP3(directory)

            if "Season" in podcast['TALB'][0]:
                folder = podcast['TALB'][0]
                podcast.save()
                if os.name == "nt":
                    if not(os.path.exists(folder)):
                        os.mkdir(folder)
                    arg_list = ["cmd", "/c", "move", directory, folder]
                elif os.name == "posix":
                    arg_list = ["mv", directory, folder]

                results = subprocess.check_output(arg_list, shell=False)
                print (results)
    
    # get new directory list after moving files
    directories = os.listdir()

    for directory in directories:
        os.chdir(basePath + "\\" + directory)
        podcasts = os.listdir()

        for podcast in podcasts:
            #  make MP3 object of currect podcast
            p = MP3(podcast)

            # set the episode number as the track number
            for tag in p.keys():
                if 'TRCK' in tag and p['TRCK'][0] != p['TIT2'][0].split(' ')[-1]:
                    p.pop(tag)
                    p['TRCK'] = TRCK(encoding=3, text="{0}".format(p['TIT2'][0].split(' ')[-1]))
                elif 'TRCK' not in tag:
                    p['TRCK'] = TRCK(encoding=3, text="{0}".format(p['TIT2'][0].split(' ')[-1]))
                else:
                    pass
                break

            # add year
            if 'TDRC' not in p.keys():
                p['TDRC'] = TDRC(encoding=3, text=podcast[:4])

            # add disc number
            if 'TPOS' not in p.keys():
                p['TPOS'] = TPOS(encoding=3, text="1")

            # rename the album
            if 'TALB' in p.keys() and p['TALB'][0] != "Sword and Scale":
                p.pop('TALB')
                p['TALB'] = TALB(encoding=3, text="Sword and Scale")

            # rename the album artist
            if 'TPE2' in p.keys() and p['TPE2'][0] != "Mike Boudet":
                p.pop('TPE2')
                p['TPE2'] = TPE2(encoding=3, text="Mike Boudet")
            else:
                p['TPE2'] = TPE2(encoding=3, text="Mike Boudet")
            
            # rename the track artist
            if 'TPE1' in p.keys() and p['TPE1'][0] != "Mike Boudet":
                p.pop('TPE1')
                p['TPE1'] = TPE1(encoding=3, text="Mike Boudet")
            else:
                p['TPE1'] = TPE1(encoding=3, text="Mike Boudet")

            # rename title
            if 'TIT2' in p.keys():
                if "Season" not in p['TIT2'][0]:
                    oldTitle = p['TIT2'][0]
                    p.pop('TIT2')
                    p['TIT2'] = TIT2(encoding=3, text="{0}, {1}".format(directory, oldTitle))
                else:
                    title = p['TIT2'][0]
                    title_space_correct = title.split(", ")
                    title_space_correct = [w.strip() for w in title_space_correct]
                    title = ", ".join(title_space_correct)

                    while title.count("Season") > 1:
                        title_split = title.split(", ")
                        title_split.reverse()
                        disregard = title_split.pop()
                        title_split.reverse()
                        title = ", ".join(title_split)
                    p.pop('TIT2')
                    p['TIT2'] = TIT2(encoding=3, text=title)

            # set genre if none is present
            if 'TCON' not in p.keys():
                p['TCON'] = TCON(encoding=3, text='Podcast')
            # rename genre
            elif p['TCON'][0] != "Podcast":
                genre = p['TCON'][0]
                p.pop('TCON')
                p['TCON'] = TCON(encoding=3, text='Podcast')
        
            p.save()
