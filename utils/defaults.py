'''
defaults.py
-----------------------------------------------------------------------------
Stores all of the default GUI settings depending on the environment it is
being launched
'''
import os

if os.name == "nt":
    lyricsTextWidth = 57
    lyricsTextHeight = 50
    lyricsWinWidth = 405
    lyricsWinHeight = 520
    musicLbFrame = 2000
    musicLbHeight = 15
    filesWidth = 2500
    filesHeight = 800
    renameWidth = 355
    renameHeight = 75
    metadataEntryWidth = 81
    metadataOptionMenuWidth = 75
    convertBitrateWidth = 425
    convertBitrateHeight = 80
    convertWidth2 = 55
    convertHeightWin = 285
    convertWidthWin = 500
    bitrateTitleColWidth = 400
    bitrateBitrateColWidth = 60
    editHeight = 2
    missingMDHeight = 15
    missingMDWidth = 125
    corruptMP3Height = 15
    corruptMP3Width = 125
    displayWinHeight = 350
    displayWinWidth = 500
    moveFileWidth = 315
    moveFileHeight = 120
    dispInfoWidth = 800
    dispInfoHeight = 600
    convertMP3Width = 800
    albumartWinHeight = 600
    albumartWinWidth = 800
    downloadAlbumArtHeight = 800
    downloadAlbumArtWidth = 1600

if os.name == "posix":
    lyricsColumn = 7
    lyricsTextWidth = 45
    lyricsTextHeight = 46
    filesWidth = 5000
    filesHeight = 10
    renameWidth = 400
    renameHeight = 75
    metadataEntryWidth = 60
    metadataOptionMenuWidth = 55
    musicLbFrame = 2000
    musicLbHeight = 12
    convertWidth1 = 490
    convertWidth2 = 45
    convertHeightWin = 265
    bitrateColWidth = 50
    editHeight = 3
    missingMDHeight = 17
    missingMDWidth = 106
    another = 1000
