import os
from mutagen.mp3 import *
from mutagen.id3 import TALB, TPE2, TCON, TRCK

def fixPodcasts():
    basePath = "C:\\Users\\Alex\\Music\\Sex With Emily"
    oldArtist = ""
    oldAlbumName = ""
    talbInKey = False
    tpe2InKey = False
    talbNameSWE = True
    tpe2NameEmily = True

    os.chdir(basePath)
    directories = os.listdir()

    for directory in directories:
        while os.path.isdir(directory):
            os.chdir(basePath + "\\" + directory)
            podcasts = os.listdir()
            count = 0

            for podcast in podcasts:
                if podcast.endswith("mp3"):
                    count += 1

                    print(" | ", podcast)

                    # replace non-Unicode characters
                    if u'\u2019' in podcast or u'\u201c' in podcast or u'\u201d' in podcast or u'\u2013' in podcast:
                        newPodcastName = podcast.replace(u'\u2019', "'").replace(u'\u201c', "'").replace(u'\u201d', "'").replace(u'\u2013', '-')
                        os.rename(podcast, newPodcastName)
                        podcast = newPodcastName

                    #  restructure the name of the podcast
                    year, month, day = podcast.split(" - ")[0].split("-")
                    if len(year) == 4:
                        newPodcastName = "{0}-{1}-{2} - {3}".format(month, day, year, podcast.split(" - ")[-1])
                        os.rename(podcast, newPodcastName)
                        print(" |---> Renamed {0} to {1}".format(podcast, newPodcastName))
                        podcast = newPodcastName
                    else:
                        print(" |---> {} was not renamed".format(podcast))

                    #  make MP3 object of currect podcast
                    p = MP3(basePath + "\\" + directory + "\\" + podcast)

                    # re-number the tracks within the directory
                    for tag in p.keys():
                        if 'TRCK' in tag:
                            p.pop(tag)
                            p['TRCK'] = TRCK(encoding=3, text="{0}".format(count))
                            p.save()
                            print(" |---> \'{0}\' is track {1} of {2}".format(podcast, count, len(os.listdir())))
                        else:
                            p['TRCK'] = TRCK(encoding=3, text="{0}".format(count))
                            p.save()
                            print(" |---> \'{0}\' is track {1} of {2}".format(podcast, count, len(os.listdir())))
                        break

                    # rename the album
                    if 'TALB' in p.keys() and p['TALB'][0] != "Sex With Emily":
                        talbInKey = True
                        talbNameSWE = False
                        oldAlbumName = p['TALB'][0]
                        p['TALB'] = TALB(encoding=3, text="Sex With Emily")

                    # rename the artist
                    if 'TPE2' in p.keys() and p['TPE2'][0] != "Emily Morse":
                        tpe2InKey = True
                        tpe2NameEmily = False
                        oldArtist = p['TPE2'][0]
                        p['TPE2'] = TPE2(encoding=3, text="Emily Morse")

                    # set album name if none is present
                    if talbInKey == False:
                        talbNameSWE = False
                        oldAlbumName = ""
                        p['TALB'] = TALB(encoding=3, text="Sex With Emily")

                    # set album artist name if none is present
                    if tpe2InKey == False:
                        tpe2NameEmily = False
                        oldArtist = ""
                        p['TPE2'] = TPE2(encoding=3, text="Emily Morse")

                    # set genre if none is present
                    if 'TCON' not in p.keys():
                        p['TCON'] = TCON(encoding=3, text='Podcast')
                        print(" |---> Added genre 'Podcast' to podcast \'{}\'".format(podcast))
                    # rename genre
                    elif p['TCON'][0] != "Podcast":
                        genre = p['TCON'][0]
                        p.pop('TCON')
                        p['TCON'] = TCON(encoding=3, text='Podcast')
                        print(" |---> Updated genre from \'{0}\' to \'{1}\'".format(genre, p['TCON']))
                    else:
                        print(" |---> No update to genre: {}".format(p['TCON']))

                    # identify if album name changed
                    if talbNameSWE == False:
                        print(" |---> Album name changed from '{0}' to '{1}'".format(oldAlbumName, p['TALB']))
                    else:
                        print(" |---> No change to album name: '{}'".format(p['TALB']))

                    # identify if album artist changed
                    if tpe2NameEmily == False:
                        print(" |---> Album artist changed from '{0}' to '{1}'".format(oldArtist, p['TPE2']))
                    else:
                        print(" |---> No change to album artist: '{}'".format(p['TPE2']))
        else:
            if os.path.isfile(directory) and directory.endswith("mp3"):
                podcast = directory
                count += 1
                # move file to appropriate folder
                # execute modifications on file as normally would if it were located in a folder originally

                print(" | ", podcast)

                # replace non-Unicode characters
                if u'\u2019' in podcast or u'\u201c' in podcast or u'\u201d' in podcast or u'\u2013' in podcast:
                    newPodcastName = podcast.replace(u'\u2019', "'").replace(u'\u201c', "'").replace(u'\u201d', "'").replace(u'\u2013', '-')
                    os.rename(podcast, newPodcastName)
                    podcast = newPodcastName

                #  restructure the name of the podcast
                year, month, day = podcast.split(" - ")[0].split("-")
                if len(year) == 4:
                    newPodcastName = "{0}-{1}-{2} - {3}".format(month, day, year, podcast.split(" - ")[-1])
                    os.rename(podcast, newPodcastName)
                    print(" |---> Renamed {0} to {1}".format(podcast, newPodcastName))
                    podcast = newPodcastName
                else:
                    print(" |---> {} was not renamed".format(podcast))

                directory = year
                os.rename(podast, directory + "\\" + podcast)

                #  make MP3 object of currect podcast
                p = MP3(basePath + "\\" + directory + "\\" + podcast)

                # re-number the tracks within the directory
                for tag in p.keys():
                    if 'TRCK' in tag:
                        p.pop(tag)
                        p['TRCK'] = TRCK(encoding=3, text="{0}".format(count))
                        p.save()
                        print(" |---> \'{0}\' is track {1} of {2}".format(podcast, count, len(os.listdir())))
                    else:
                        p['TRCK'] = TRCK(encoding=3, text="{0}".format(count))
                        p.save()
                        print(" |---> \'{0}\' is track {1} of {2}".format(podcast, count, len(os.listdir())))
                    break

                # rename the album
                if 'TALB' in p.keys() and p['TALB'][0] != "Sex With Emily":
                    talbInKey = True
                    talbNameSWE = False
                    oldAlbumName = p['TALB'][0]
                    p['TALB'] = TALB(encoding=3, text="Sex With Emily")

                # rename the artist
                if 'TPE2' in p.keys() and p['TPE2'][0] != "Emily Morse":
                    tpe2InKey = True
                    tpe2NameEmily = False
                    oldArtist = p['TPE2'][0]
                    p['TPE2'] = TPE2(encoding=3, text="Emily Morse")

                # set album name if none is present
                if talbInKey == False:
                    talbNameSWE = False
                    oldAlbumName = ""
                    p['TALB'] = TALB(encoding=3, text="Sex With Emily")

                # set album artist name if none is present
                if tpe2InKey == False:
                    tpe2NameEmily = False
                    oldArtist = ""
                    p['TPE2'] = TPE2(encoding=3, text="Emily Morse")

                # set genre if none is present
                if 'TCON' not in p.keys():
                    p['TCON'] = TCON(encoding=3, text='Podcast')
                    print(" |---> Added genre 'Podcast' to podcast \'{}\'".format(podcast))
                # rename genre
                elif p['TCON'][0] != "Podcast":
                    genre = p['TCON'][0]
                    p.pop('TCON')
                    p['TCON'] = TCON(encoding=3, text='Podcast')
                    print(" |---> Updated genre from \'{0}\' to \'{1}\'".format(genre, p['TCON']))
                else:
                    print(" |---> No update to genre: {}".format(p['TCON']))

                # identify if album name changed
                if talbNameSWE == False:
                    print(" |---> Album name changed from '{0}' to '{1}'".format(oldAlbumName, p['TALB']))
                else:
                    print(" |---> No change to album name: '{}'".format(p['TALB']))

                # identify if album artist changed
                if tpe2NameEmily == False:
                    print(" |---> Album artist changed from '{0}' to '{1}'".format(oldArtist, p['TPE2']))
                else:
                    print(" |---> No change to album artist: '{}'".format(p['TPE2']))

    p.save()
