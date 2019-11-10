import os
import re
import ffmpy
from mutagen.id3 import TIT2, TPE1, TPE2, TRCK, TPOS, TALB, TCON, TDRC

def _rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def _convert(podcasts):
    for podcast in podcasts:
        songFile = f"{os.getcwd()}\\{podcast}"
        convertedFile = f"{os.getcwd()}\\{podcast[:-3]}mp3"
        print (f"Converting {songFile} to {convertedFile}...")

        ff = ffmpy.FFmpeg(inputs={songFile: None}, outputs={convertedFile: '-y -ac 2 -ar 41000 -ab 54k'})
        ff.run()

        print (f"Converted to {convertedFile}!!", "\n")

def addArtist(podcasts):
    i = 0
    for podcast in podcasts:
        i += 1
        print (podcast)
        p = MP3(podcast)

        podcast = _rreplace(podcast, '.', ';', 1)
        date, title, ext = podcast.replace(' - ',';').split(';')

        try:
            title, artist = re.split(' with | on ', title)
        except ValueError:
            title, artist = title, "Sven Johann"
            
        p['TIT2'] = TIT2(encoding=3, text=title)
        p['TPE1'] = TPE1(encoding=3, text=artist)
        p['TALB'] = TALB(encoding=3, text="CaSE Podcast Team")
        p['TPE2'] = TPE2(encoding=3, text="Sven Johann")
        p['TPOS'] = TPOS(encoding=3, text="1/1")
        p['TCON'] = TCON(encoding=3, text="Podcast")
        p['TDRC'] = TDRC(encoding=3, text=date)
        p['TRCK'] = TRCK(encoding=3, text=f"{i}/{len(os.listdir())}")
        p.save()

directory = "C:\\Users\\Alex\\Music\\CaSE_ Conversations about Software Engineering"
os.chdir(directory)

podcasts = os.listdir()

_convert(podcasts)
addArtist(podcasts)
