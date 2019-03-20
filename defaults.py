##########################################
# defaults.py
#
# Stores all of the default GUI settings
# depending on the environment it is
# being launched
##########################################

import os

if os.name == "nt":
    width = 1243
    height = 705
    lyricsColumn = 7
    lyricsTextWidth = 57
    lyricsTextHeight = 18
    lyricDescWinWidth = 405
    lyricDescWinHeight = 520
    filesWidth = 5000
    filesHeight = 500
    renameWidth = 355
    renameHeight = 75
    metadataEntryWidth = 70
    convertWidth1 = 470
    convertWidth2 = 55
    convertHeightWin = 285
    bitrateColWidth = 40
    editHeight = 2
    missingMDHeight = 15
    missingMDWidth = 125
    displayWinHeight = 350
    displayWinWidth = 500
    moveFileWidth = 315
    moveFileHeight = 120
    dispInfoWidth = 800
    dispInfoHeight = 600

if os.name == "posix":
    width = 1255
    height = 705
    lyricsColumn = 7
    lyricsTextWidth = 40
    lyricsTextHeight = 18
    filesWidth = 5000
    filesHeight = 500
    renameWidth = 400
    renameHeight = 75
    metadataEntryWidth = 60
    convertWidth1 = 490
    convertWidth2 = 45
    convertHeightWin = 285
    bitrateColWidth = 50
    editHeight = 3
    missingMDHeight = 17
    missingMDWidth = 106
    lyricDescWinWidth = 480
    lyricDescWinHeight = 560
    