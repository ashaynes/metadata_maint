# usr/bin/env python3

from mutagen.id3 import ID3, TRCK, TCON, TPOS, TALB, TIT2, TPE1, TPE2, TDRC
from mutagen.mp3 import MP3, EasyMP3, HeaderNotFoundError
from mutagen.id3 import APIC, USLT, TBPM, ID3NoHeaderError
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium import webdriver
from tkinter.messagebox import *
from tkinter.filedialog import *
from pydub import AudioSegment
from pydub.exceptions import *
from selenium import webdriver
from bs4 import BeautifulSoup
import tkinter.font as tkFont
from tkinter.ttk import *
from tkinter import *
from mutagen import *
import pygame as pg
import numpy as np
from PIL import Image, ImageTk
import subprocess
import threading
import functools
import urllib
from urllib.request import *
import requests
import requests_cache
import mutagen
import wget
import time
import math
import sys
import re
import io

import extractAPIC
import defaults

paused = False

'''
TODO:
1 -> Save descriptions of podcasts to USLT tag and display in Lyrics window on onselect() (WIP)
2 -> Create 'displayInfo' function for Search options to display metadata on double-click, differentiate between artist, album and song (WIP)
3 -> Make album art download pull songs from the same album and update those as well [possibly music.dawnfoxes.com]
4 -> Create function that allows an online search of MP3s to download and downloads the selected song to the default directory ??
5 -> Create function that downloads the Billboard Top 50, based on genre selected
'''

class mdict(dict):
	def __setitem__(self, key, value):
		"""add the given value to the list of values for this key"""
		self.setdefault(key, []).append(value)

class EditMetadata(Frame):
	def sortby(self, tree, col, descending):
		"""sort tree contents when a column is clicked on"""
		data = [(tree.set(k, col), k) for k in tree.get_children('')]
		data.sort(reverse=descending)
		[tree.move(k, '', index) for index, (val, k) in enumerate(data)]
		tree.heading(col, command=lambda col=col: self.sortby(tree, col, int(not descending)))

	def __init__(self, master):
		def mainQuit(master):
			master.quit() if askyesno("Exit?", "Do you really want to exit?") == True else False

		def switchModes():
			'''switch between Edit Mode and View Mode'''
			self.save.config(state=NORMAL) if self.state.get() == True else self.save.config(state=DISABLED)
			self.mode.set("Edit Mode") if self.state.get() == True else self.mode.set("View Mode")
			self.editFile() if self.state.get() == True else self.saveFile()

		def playSong():
			# setting events
			END_MUSIC_EVENT = pg.USEREVENT + 0
			pg.mixer.music.set_endevent(END_MUSIC_EVENT)

			'''play current song selected in Listbox and update elapsed time'''
			self.current_song_playing.set(self.song['TIT2'][0])
			# set Pause and Stop buttons to normal state
			self.play.config(state=DISABLED)
			self.pause.config(state=NORMAL)
			self.stop.config(state=NORMAL)
			
			# for i in range(0, len(self.all_music)):
			# 	if self.song['TIT2'][0] in self.all_music[i][1]:
			# 		time = self.all_music[i][-1]
			
			self.lyricsText.config(state=NORMAL, cursor="arrow")
			
			# display lyrics from USLT tag else web scrape
			uslt_found = False
			for tags in self.song.keys():
				if "USLT" in tags:
					uslt_found = True
					lyrics = self.song[tags]

			if uslt_found is False:
			# web scraping: search for lyrics with "best match" URL -- www.metrolyrics.com
				if self.song['TCON'][0] != 'Orchestral' and self.song['TCON'] != 'Podcast':
					if re.search(r'[a-zA-Z0-9\'\&]',self.song['TIT2'][0].lower()):
						artist, song = [re.sub(r'[^a-zA-Z0-9\'\+\.\(\)\&]',"-",self.song['TPE2'][0].lower()), re.sub(r'[^a-zA-Z0-9\'\+\.\(\)\&]',"-",self.song['TIT2'][0].lower())]
					else:
						artist, song = [re.sub(r'\s',"-",self.song['TPE2'][0].lower()), re.sub(r'\s',"-",self.song['TIT2'][0].lower())]
					
					if artist == "various-artists":
						artist = re.sub(r'[^a-zA-Z0-9\'\+\.\(\)\&]',"-",self.song['TPE1'][0].lower())
					song=song.replace(".","")
					artist=artist.replace(".","")
					
					# search lyrics
					try:
						requests_cache.install_cache('lyrics_cache')
						url = "http://www.metrolyrics.com/{0}-lyrics-{1}.html".format(song, artist)
						soup = BeautifulSoup(requests.get(url).content, "lxml")
						lyrics = str()
						verses = soup.find_all("p", {"class": "verse"})
						for verse in verses:
							lyrics += verse.text+"\n\n"
						self.song['USLT'] = USLT(encoding=3, lang=u'eng', text=lyrics)
						self.song.save()

					except requests.exceptions.ConnectionError as e:
						showerror("Connection Error", "%s" % e)

			self.lyricsText.delete("0.0", END)
			self.lyricsText.insert("0.0", lyrics)
			self.lyricsText.config(state=DISABLED, cursor="arrow")
			
			# load music file, else return error
			song_header = self.song.pprint().split("\n")[0].split(", ")
			freq = "44100 Hz"
			for x in range(len(song_header)):
				if "Hz" in song_header[x]:
					freq = song_header[x]
					print (song_header, freq)
					break
			
			pg.mixer.pre_init(int(freq[:-3]), -16, 2, 2048)
			pg.mixer.init()
			pg.mixer.music.set_volume(0.8)

			try:
				pg.mixer.music.load(self.song_path.get())
				pg.mixer.music.play(1)
				print (pg.mixer.music.get_busy())
				if bool(pg.mixer.music.get_busy()) is True:
					print ("{} is playing right now".format(self.song_path.get()))
			except pg.error:
				showerror("Playback Error","{}".format(pg.get_error()))
			
			# reset pause status in player
			if paused is True:
				pauseSong()
			
			if pg.mixer.music.get_busy() is False:
				pg.mixer.music.stop()
				pg.mixer.music.load("")
				print ("{} has stopped playing".format(self.song_path.get()))
				self.lyricsText.config(state=NORMAL, cursor="arrow")	
			
		def pauseSong():
			'''pauses playback of song'''
			global paused
			if pg.mixer.music.get_busy() and paused is False:
				pg.mixer.music.pause()
				pause_unpause.set("Unpause")
				paused = True
			else:
				pg.mixer.music.unpause()
				pause_unpause.set("Pause")
				paused = False

		def stopSong():
			'''stops the song that is playing'''
			if pg.mixer.music.get_busy():
				pg.mixer.music.stop()
				self.play.config(state=NORMAL)
				self.stop.config(state=DISABLED)

		'''set initial values to certain parameters used within the program'''
		os.chdir('/home/alex/Music/') if os.name == "posix" else os.chdir("C:\\Users\\Alex\\Music\\")
		if os.name == "nt":
			self.default = os.getcwd()+"\\No Image Available.jpg"
		if os.name == "posix":
			self.default = os.getcwd()+"/No Image Available.jpg"
		
		self.entries = []
		self.l = ['Song Title','Artist(s)','Album','Album Artist','Genre','Year','Track Number','BPM','Disc Number']
		self.all_music = []
		
		self.song_path = StringVar()
		self.title = StringVar()
		self.artist = StringVar()
		self.album = StringVar()
		self.performer = StringVar()
		self.genre = StringVar()
		self.date = StringVar()
		self.tracknumber = StringVar()
		self.bpm = StringVar()
		self.discnumber = StringVar()
		self.albumart = StringVar()
		self.directoryStr = ""
		self.searchStr = StringVar()
		self.searchStr.trace("w", lambda var, index, mode: self.update_lb())
		self.songCntStr = StringVar()
		self.path = StringVar()
		self.current_song_selected = StringVar()
		self.current_song_playing = StringVar()
		
		self.musicLb_columns = ['Title', 'Artist(s)', 'Album', 'Genre', 'Time', 'Bitrate']
		self.tags = ['TIT2', 'TPE1', 'TALB', 'TPE2', 'TCON', 'TDRC', 'TRCK', 'TBPM', 'TPOS', 'APIC', 'USLT']
		self.cats = [self.title, self.artist, self.album, self.performer, self.genre, \
			self.date, self.tracknumber, self.bpm, self.discnumber, self.albumart]
		
		# creating popup Menu for Listbox
		self.menu = Menu(master, tearoff=0)
		self.menu.add_command(label="Extract Album Art", command=self.extractAlbumArt)
		self.menu.add_command(label="Move File", command=self.moveFile)
		self.menu.add_command(label="Remove File", command=self.removeFile)
		self.menu.add_command(label="Rename File", command=self.renameFile)
		self.menu.add_command(label="Convert Type of File", command=functools.partial(self.convertToMP3, 1))
		self.menu.add_command(label="Convert Bitrate of File", command=functools.partial(self.convertBitrate, 1))
		self.menu.add_command(label="View/Edit Description", command=self.lyricsDescription)

		# creating top Menu bar
		self.mastermenu = Menu(master)
		# menu options for files and directories
		self.fileMenu = Menu(self.mastermenu, tearoff = 0)
		self.mastermenu.add_cascade(label = "File", menu = self.fileMenu, underline=0)
		self.fileMenu.add_command(label = "New Folder", command = self.newFolder)
		self.fileMenu.add_command(label = "Print Tracklist", command = self.printTracklist)
		self.fileMenu.add_separator()
		self.fileMenu.add_command(label = "Exit", command=functools.partial(mainQuit, master))
		# edit menu options
		self.editMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label="Directory", menu=self.editMenu, underline=0)
		self.editMenu.add_command(label="Convert to MP3", command=self.convertToMP3)
		self.editMenu.add_command(label="Convert Bitrate", command=self.convertBitrate)
		# metadata menu option
		self.metaMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label="Metadata", menu=self.metaMenu, underline=0)
		self.metaMenu.add_command(label="Search Missing Metadata", command=self.searchMetadata)
		self.metaMenu.add_command(label="Show Songs with Missing Metadata", command=self.showMissingMetadata)
		# search menu options
		self.searchMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label = "Advanced...", menu=self.searchMenu, underline=0)
		self.searchMenu.add_command(label = "Artist Search", command=functools.partial(self.search, ('artist', ('Song', 'Track Artist(s)', 'BPM'))))
		self.searchMenu.add_command(label = "Album Search", command=functools.partial(self.search, ('album', ('Song', 'Genre', 'BPM'))))
		self.searchMenu.add_command(label = "Genre Search", command=functools.partial(self.search, ('genre', ('Song', 'Album', 'BPM'))))
		self.searchMenu.add_command(label = "Year Search", command=functools.partial(self.search, ('year', ('Song', 'Album', 'Genre', 'BPM'))))
		self.searchMenu.add_command(label = "BPM Search", command=functools.partial(self.search, ('bpm', ('Song', 'Album', 'Genre', 'Year'))))
		master.config(menu=self.mastermenu)

		# configuring certain menu option to be disabled at initial program launch
		self.mastermenu.entryconfig("Directory", state=DISABLED)
		self.mastermenu.entryconfig("Metadata", state=DISABLED)
		self.mastermenu.entryconfig("Advanced...", state=DISABLED)

		Label(master).grid(columnspan=12)
		# creating Label and Entry items
		metadata = LabelFrame(master, text='Metadata')
		metadata.grid(columnspan=3, padx=10, ipadx=5, ipady=5, sticky=W)
		for item in self.l:
			i = self.l.index(item)
			Label(metadata, text=item+":").grid(row=i+1, sticky='W', padx=15)
			self.entries.append(Entry(metadata, textvariable=self.cats[i], width=defaults.metadataEntryWidth, state=DISABLED))
			self.entries[i].grid(row=i+1, column=1, columnspan=4, sticky='W')
		
		# adding Buttons
		self.mode = StringVar()
		self.state = BooleanVar()
		self.mode.set("View Mode")
		self.edit = Checkbutton(metadata, indicatoron=0, textvariable=self.mode, variable=self.state, onvalue=True, offvalue=False, width=12, \
			height=defaults.editHeight, command=switchModes, state=DISABLED)
		self.edit.grid(row=len(self.l)+1, column=1, sticky=E+W)
		self.save = Button(metadata, text="Save Metadata", width=12, state=DISABLED, command=self.saveFile)
		self.save.grid(row=len(self.l)+1, column=2, sticky=E+W)
		self.getAlbumArt = Button(metadata, text="Add Album Art", state=DISABLED, width=12, command=self.addAlbumArt)
		self.getAlbumArt.grid(row=len(self.l)+1, column=4, sticky=E+W)
		
		# creating empty Canvas for media player (album art place holder)
		self.player = LabelFrame(master, text='Media Player')
		self.player.grid(row=1, column=3, columnspan=4, sticky=W+E)
		self.original = Image.open(self.default)
		self.resized = self.original.resize((194,194), Image.ANTIALIAS)
		self.albumart = ImageTk.PhotoImage(self.resized)
		self.canvas = Canvas(self.player, width=194, height=194)
		self.canvas_image = self.canvas.create_image(97, 97, image=self.albumart)
		self.canvas.grid(row=1, rowspan=3, padx=49, columnspan=3, sticky=N+S+E+W)
		
		# create media buttons for media player
		pause_unpause = StringVar()
		pause_unpause.set("Pause")
		self.play = Button(self.player, text="Play", command=playSong, state=DISABLED, width=5)
		self.play.grid(row=5, column=0, sticky=E+W, pady=7)
		self.pause = Button(self.player, textvariable=pause_unpause, command=pauseSong, state=DISABLED, width=5)
		self.pause.grid(row=5, column=1, sticky=E+W, pady=7)
		self.stop = Button(self.player, text="Stop", command=stopSong, state=DISABLED, width=5)
		self.stop.grid(row=5, column=2, sticky=E+W, pady=7)
		
		# creating lyrics LabelFrame - scrape internet for lyrics and display in Text widget
		self.lyrics = LabelFrame(master, text="Lyrics")
		self.lyricsText = Text(self.lyrics, height=defaults.lyricsTextHeight, width=defaults.lyricsTextWidth, \
			font="Tahoma 8 italic", wrap=WORD, background="dark blue", foreground="white")
		self.lyricsText.grid()
		self.lyrics.grid(row=1, column=defaults.lyricsColumn, padx=10)
		
		# add total music files and Button to browse to different path
		files = LabelFrame(master, text='Files & Directory', width=defaults.filesWidth, height=defaults.filesHeight)
		files.grid(row=len(self.l)+2, columnspan=8, padx=10)
		self.lbl = Label(files, text="\nCurrent Directory:")
		self.lbl.grid(row=len(self.l)+3, columnspan=8, padx=15, sticky='W')
		browseBtn = Button(files, text="Browse...", width=25, command=self.getNewDirectory)
		browseBtn.grid(row=len(self.l)+3, column=8)
		
		# creating the quick search bar
		Label(files, text="Quick Search: ").grid(row=len(self.l)+4, column=1, padx=15, sticky=W)
		self.searchBar = Entry(files, textvariable=self.searchStr, font="Arial 10 italic", width=113, state=DISABLED)
		self.searchBar.grid(row=len(self.l)+4, column=2, columnspan=6)
		Label(files, text="Only searches Song Title".center(57), font="Arial 10 italic").grid(row=len(self.l)+4, column=8, sticky=E+W)
		
		# creating the Multi-column Listbox (Treeview) for the music files
		frame = Frame(files)
		frame.grid(columnspan=10, sticky="nsew")
		self.musicLb = Treeview(columns=self.musicLb_columns, height=15, show="headings")
		self.musicLb.bind('<<TreeviewSelect>>', self.onselect)
		self.musicLb.bind('<Button-3>', self.popup)
		self.vsb = Scrollbar(orient="vertical", command=self.musicLb.yview)
		self.musicLb.configure(yscrollcommand=self.vsb.set)
		self.musicLb.grid(row=len(self.l)+5, rowspan=3, columnspan=15, sticky=N+E+S+W, padx=15, in_=frame)
		self.vsb.grid(column=1, row=len(self.l)+5, rowspan=3, sticky='ns', in_=frame)
		frame.grid_columnconfigure(0, weight=1)

		# building the tree (headers and items)
		[self.musicLb.heading(col, text=col.capitalize(), command=lambda c=col: self.sortby(self.musicLb, c, 0)) for col in self.musicLb_columns]
		self.musicLb.column('Genre', minwidth=15, width=15)
		self.musicLb.column('Time', minwidth=15, width=15, anchor="center")
		self.musicLb.column('Bitrate', minwidth=15, width=15, anchor="center")

		# total music files in directory/listbox
		self.songCount = Label(master, textvariable=self.songCntStr)
		self.songCount.grid(row=len(self.l)+6, column=0, padx=10, sticky='W')
		self.songCntStr.set("Total Files: n/a; Total Size: n/a; Total Time: n/a")

		# label that updates the count of songs added to table against total songs found in folder
		self.songsAddedStr = StringVar()
		self.songsAdded = Label(master, textvariable=self.songsAddedStr)
		self.songsAdded.grid(row=len(self.l)+6, column=6, sticky='EW')
		self.songsAddedStr.set("")

		# progress bar to show loading of file(s)
		self.song_count = IntVar()
		self.progressBar = ttk.Progressbar(master, value=0, variable=self.song_count, orient="horizontal", length=200, mode="determinate")
		self.progressBar.grid(row=len(self.l)+6, column=7, padx=10, sticky='E')
	
	def displayInfo(self, event):
		'''displays general information for the song selected'''
		self.displayWindow = Toplevel()
		selected_song = self.tree.item(self.tree.selection())
		self.displayWindow.title('\'%s\' General Info' % selected_song['values'][0])

	def printTracklist(self, event):
		'''Function that takes the album and track list information, prints to default printer'''
		return
	
	def popup(self, event):
		if len(self.musicLb.get_children('')) > 0:
			self.menu.tk_popup(event.x_root, event.y_root)

	def conversion(self, filesize=0, totaltime=0):
		'''converts the filesize and/or total time of files in the Listbox'''
		time = [0,0,0,0] #days, hours, minutes, seconds
		
		# converting the filesize to appropriate units
		if filesize <= pow(2,10):
			convFS = str(filesize)+" bytes"
		elif filesize > pow(2,10) and filesize <= pow(2,20):
			convFS = str(round(filesize/pow(2,10),2))+" KB"
		elif filesize > pow(2,20) and filesize <= pow(2,30):
			convFS = str(round(filesize/pow(2,20),2))+" MB"
		else:
			convFS = str(round(filesize/pow(2,30),2))+" GB"

		# converting the total time to the appropriate format
		if totaltime < 60: # store seconds if time is less than a minute
			time[3] = int(round(totaltime, 0))
		elif totaltime < 3600 and totaltime >= 60: # store minutes and seconds if time is less than an hour
			time[2], time[3] = int(totaltime//60), int(round(totaltime%60, 0))
		elif totaltime < 86400 and totaltime <= 3600: # store hours, minutes, seconds if time is less than a day (24 hours)
			time[1], time[2], time[3] = int(totaltime//3600), int((totaltime%3600)//60), int(round(totaltime%60, 0))
		else: # else, return days, hours, minutes, seconds
			time[0], time[1], time[2], time[3] = int(totaltime//86400), int((totaltime%86400)//3600), int((totaltime%3600)//60), int(round(totaltime%60, 0))

		convTT = '{0:01d} {1}, {2:02d}:{3:02d}:{4:02d}'.format(time[0], 'day' if time[0]==1 else 'days', time[1], time[2], time[3])
		return [convFS, convTT]

	def update_lb(self):
		search_term = self.searchStr.get()
		files = []
		size = time = 0
		
		# delete all contents of Listbox and re-populate with resulting search items; update new total time and total file size
		for item in self.musicLb.get_children():
			self.musicLb.delete(item)
		for item in self.all_music:
			if search_term.lower() in item[1].lower() and item not in files:
				files.append(item)
				size += os.stat(files[-1][0]).st_size
				time += MP3(files[-1][0]).info.length
		for item in files:
			self.musicLb.insert("", END, text=item[0], values=(item[1], item[2], item[3], item[4], ('{0:02}:{1:02}:{2:02}').format(\
				int(MP3(files[files.index(item)][0]).info.length % 86400) // 3600, int(MP3(files[files.index(item)][0]).info.length % 3600) // 60,\
				int(MP3(files[files.index(item)][0]).info.length % 60)), int(MP3(files[files.index(item)][0]).info.bitrate/1000)))
			
		# convert and get size of directory and total time of files in directory
		convertedSize, convertedTime = self.conversion(size, time)

		# updating total music files in directory/listbox
		self.songCntStr.set("Total Files: " + str(len(files)) + "; Total Size: " + convertedSize + "; Total Time: " + convertedTime)

	def extractAlbumArt(self):
		file = self.song_path.get()
		extractAPIC.extract(file)

	def addAlbumArt(self):
		try:
			image_path = u"C:\\Users\\Alex\\Documents\\Downloaded Album Art\\{} ({}).jpg".format(self.song['TALB'][0], self.song['TPE2'][0])
			# resizing the album art
			self.resizeAlbumArt(image_path)
			
			with open(image_path, "rb") as image:
				f = image.read()
				imageBytes = bytes(bytearray(f))
			
			if self.dname.split("/")[-1] == self.song['TALB'][0]:
				for song in self.all_music:
					thisSong = MP3(self.dname + "\\" + song[0])
					APIC_found = [key.find("APIC") for key in thisSong.keys()]
					if 0 not in APIC_found:
						thisSong['APIC'] = APIC(encoding=3, mime=u'image/jpeg', type=3, desc=self.song['TALB'][0], data=imageBytes)
						thisSong.save()
			else:
				self.song['APIC'] = APIC(encoding=3, mime=u'image/jpeg', type=3, desc=self.song['TALB'][0], data=imageBytes)
				self.song.save()
		except Exception as e:
			showinfo("Error", str(e))
		finally:
			self.getMusic()

	def removeAlbumArt(self, info):
		song = info[0]; tag = info[1]
		song.pop(tag)
		song.save()
		self.getMusic()

	def resizeAlbumArt(self, art):
		'''converting image to true JPEG file and resizing'''
		im = Image.open(art)
		im = im.resize((250, 250), Image.ANTIALIAS)
		if im.mode != "RGB":im.convert("RGB")
		im.save(art,"JPEG")
		
	def recreateMP3File(self, song_path):
		"""create new header for .mp3 file and necessary metadata"""
		self.song = ID3(song_path)
		self.newFile = MP3()
		
		# copy necessary contents of old .mp3 file to new .mp3 file
		for t in self.song.keys():
			if t in self.tags:
				self.newFile[t] = self.song[t]
		return self.newFile

	def onselect(self, e):
		"""when a file is selected, show the existing metadata if there are not any errors.
		else, correct the errors and then display the metadata"""
		# collect information from the event
		self.value = self.musicLb.item(self.musicLb.selection())
		self.play.config(state=NORMAL)
		self.stop.config(state=DISABLED)
		
		if os.getcwd() != self.dname:
			os.chdir(self.dname)
		
		if os.name == "posix":
			self.song_path.set(os.getcwd()+"/"+self.value['text'])
		if os.name == "nt":
			self.song_path.set(os.getcwd()+"\\"+self.value['text'])

		self.menu.entryconfig(0, state=DISABLED) if extractAPIC.albumArtInFile(self.song_path.get()) == True else self.menu.entryconfig(0, state=NORMAL)

		# read .mp3 file
		try:
			self.song = MP3(self.song_path.get()) # dictionary
			
			# "removing" unnecessary tags if header is present
			self.remove = []
			for t in self.song.keys():
				if "APIC" in t or "USLT" in t: continue
				if t not in self.tags: self.remove.append(t)

			for tag in self.remove:
				self.song.pop(tag)
				self.song.save()
			
			self.state.set(False)
			self.mode.set("View Mode")
			self.save.config(state=DISABLED)

			# print whatever contents are in the tags in the .mp3 file
			for k in self.song.keys():
				if "APIC" in k or "USLT" in k: continue
				self.cats[self.tags.index(k)].set(self.song[k][0]) if k not in self.remove else next
				
			# update self.getAlbumArt Label, depending on whether APIC tag is in MP3
			for k in self.song.keys():
				if "APIC" in k:
					self.getAlbumArt.config(text="Remove Album Art", state=NORMAL, command=functools.partial(self.removeAlbumArt, (self.song, k)))
					self.getAlbumArt.update()
					break
				else:
					self.getAlbumArt.config(text="Add Album Art", state=NORMAL, command=self.addAlbumArt)
					self.getAlbumArt.update()	
				
			if "TCON" in self.song.keys():
				self.menu.entryconfig(6, label="Edit Lyrics") if self.song['TCON'][0] != "Podcast" else self.menu.entryconfig(6, label="Edit Description")

				# change self.lyricsWindowTitle based on TCON tag; display lyrics from USLT tag in MP3
				self.lyrics.config(text="Description") if self.song['TCON'][0] == "Podcast" else self.lyrics.config(text="Lyrics")
				self.lyrics.update()
			else:
				self.state.set(True)
				self.mode.set("Edit Mode")
				self.save.config(state=NORMAL)

			lyricsText = "No lyrics available"
			self.lyricsText.delete("0.0", END)
			for tag in self.song.keys():
				if "USLT" in tag:
					lyricsText = self.song[tag]
			self.lyricsText.insert("0.0", lyricsText)

			# determine when "Search Missing Metadata" option is available for selection in Metadata menu
			# should only be available when there is at least one metadata field (self.cats) that is empty (legit)
			tempList=self.tags[:-2]
			self.metaMenu.entryconfig("Search Missing Metadata", state=NORMAL) if any(len(self.cats[self.tags.index(t)].get())==0 for t in tempList) \
				else self.metaMenu.entryconfig("Search Missing Metadata", state=DISABLED)
			
			for k in self.entries:
				k.config(state=DISABLED)
			self.edit.config(state=NORMAL)

			# display album art on file else display default art
			self.albumArt = Image.open(self.default)			# display default album art (No Image Available)
			try:
				for tag in self.song.keys():
					if "APIC" in tag:
						imageData = self.song[tag].data
						# imageData = resizeAlbumArt(imageData)
						self.albumArt = Image.open(io.BytesIO(imageData))		# display album art found if art is embedded to mp3
						break

			except Exception as e:
				if type(e) is OSError:
					self.song.pop(tag)
					self.song.save()
		
			resized = self.albumArt.resize((194, 194), Image.ANTIALIAS)
			# resized.show()
			self.albumImage = ImageTk.PhotoImage(resized)
			self.canvas.itemconfigure(self.canvas_image, image=self.albumImage)
		# do this if header is missing
		except HeaderNotFoundError:
			self.recreateMP3File(self.song_path.get())

	def editFile(self):
		i = 0
		for k in self.entries:
			i += 1
			next if i == 8 else k.config(state=NORMAL)
			k.focus() if i == 1 else next
		self.save.config(state=NORMAL)

	def saveFile(self):
		"""take information from Entry boxes and save to .mp3 file"""
		self.song['TALB'] = TALB(encoding=3, text=self.cats[self.tags.index('TALB')].get())
		self.song['TIT2'] = TIT2(endoding=3, text=self.cats[self.tags.index('TIT2')].get())
		self.song['TPE1'] = TPE1(encoding=3, text=self.cats[self.tags.index('TPE1')].get())
		self.song['TPE2'] = TPE2(encoding=3, text=self.cats[self.tags.index('TPE2')].get())
		self.song['TDRC'] = TDRC(encoding=3, text=self.cats[self.tags.index('TDRC')].get())
		self.song['TRCK'] = TRCK(encoding=3, text=self.cats[self.tags.index('TRCK')].get())
		self.song['TCON'] = TCON(encoding=3, text=self.cats[self.tags.index('TCON')].get())
		self.song['TPOS'] = TPOS(encoding=3, text=self.cats[self.tags.index('TPOS')].get())
		self.song['TBPM'] = TBPM(encoding=3, text=self.cats[self.tags.index('TBPM')].get())
				
		for k in self.entries: k.config(state=DISABLED)
		self.save.config(state=DISABLED)
		self.state.set(False)
		self.mode.set("View Mode")
		try:
			self.song.save(self.song_path.get(), v2_version=3)
		except mutagen.MutagenError as e:
			showerror("Error","%s" % e)
		self.getMusic()
	
	'''	change this function to save lyrics/description displayed in the lyrics/description window to MP3 USLT file'''
	def lyricsDescription(self):
		'''function that allows user to view and edit description of music file (not lyrics)'''
		def switchModes():
			modes.set("Edit Mode") if state.get() == True else modes.set("View Mode")
			textbox.config(state=NORMAL, cursor="xterm") if state.get() == True else textbox.config(state=DISABLED, cursor="arrow")
			save.config(state=NORMAL) if state.get() == True else save.config(state=DISABLED)
		
		def saveFile():
			# remove old USLT tag(s) from MP3 file and add new USLT tag to file
			listOfKeys = list(self.song.keys())
			for key in listOfKeys:
				if 'USLT' in key:
					self.song.pop(key)
			
			self.song['USLT'] = USLT(encoding=3, lang=u'eng', text=textbox.get(1.0, END))
			self.song.save(self.song_path.get(), v2_version=3)
			showinfo("Song Description","Description has been saved!") if self.song['TCON'] == "Podcast" else next
			closeWindow()

		def closeWindow():
			self.saveLDWin.destroy()

		uslt_found = False
		for tags in self.song.keys():
			if "USLT" in tags:
				uslt_found = True
				lyrics = self.song[tags]

		if uslt_found is False:
			artist = self.song['TPE2'][0].replace(" ","-").lower()
			song = self.song['TIT2'][0].replace(" ","-").lower()
			url = "http://www.metrolyrics.com/{0}-lyrics-{1}.html".format(song, artist)
			
			try:
				requests_cache.install_cache('lyrics_cache')
				soup = BeautifulSoup(requests.get(url).content, "lxml")
				lyrics = str()
				verses = soup.find_all("p", {"class": "verse"})
				for verse in verses:
					lyrics += verse.text+"\n\n"
				
			except requests.exceptions.ConnectionError as e:
				showerror("Connection Error", "%s" % e)

		self.saveLDWin = Toplevel()
		# change the heading depending on the genre type
		self.saveLDWin.title("{0}'s '{1}' {2}".format(self.song['TPE2'][0], self.song['TIT2'][0], "Description")) if self.song['TCON'][0] == 'Podcast' \
			else self.saveLDWin.title("{0}'s '{1}' {2}".format(self.song['TPE2'][0], self.song['TIT2'][0], "Lyrics"))
		pos = centerWindow(self.saveLDWin, defaults.lyricDescWinWidth, defaults.lyricDescWinHeight)
		self.saveLDWin.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))
		
		Label(self.saveLDWin, text="Title: "+self.song['TIT2'][0], font="Arial 10 italic", justify=CENTER).grid(row=1, columnspan=3, sticky=E+W)
		Label(self.saveLDWin, text="Album: "+self.song['TALB'][0], font="Arial 10 italic", justify=CENTER).grid(row=2, columnspan=3, sticky=E+W)
		Label(self.saveLDWin, text="Track: "+self.song['TRCK'][0], font="Arial 10 italic", justify=CENTER).grid(row=3, columnspan=3, sticky=E+W)
		Label(self.saveLDWin, text="Disc: "+self.song['TPOS'][0], font="Arial 10 italic", justify=CENTER).grid(row=4, columnspan=3, sticky=E+W)
		textbox = Text(self.saveLDWin, font='Times 10', width=65, wrap=WORD)
		textbox.grid(row=6, columnspan=3, pady=10)
		textbox.insert(END, lyrics)
		textbox.config(state=DISABLED, cursor="arrow")
		textbox.focus()
		
		state = BooleanVar()
		modes = StringVar()
		mode = Checkbutton(self.saveLDWin, indicatoron=0, textvariable=modes, variable=state, onvalue=True, offvalue=False, width=15, height=2, \
			command=switchModes)
		mode.grid(row=7, column=0, padx=10)
		save = Button(self.saveLDWin, command=saveFile)
		
		if textbox.get(0.0, END) == '\n':
			modes.set("Edit Mode"); textbox.config(state=NORMAL, cursor="xterm"); state.set(True)
			save.config(state=NORMAL)
		else:
			modes.set("View Mode"); textbox.config(state=DISABLED, cursor="arrow"); state.set(False)
			save.config(state=DISABLED)
		save.config(text="Save Description", width=15) if self.song['TCON'][0] == "Podcast" else save.config(text="Save Lyrics", width=15)
		save.grid(row=7, column=1, padx=10)
		close = Button(self.saveLDWin, text="Close", width=15, command=closeWindow)
		close.grid(row=7, column=2, padx=10)
	
	def newFolder(self):
		'''creating a new folder in existing directory'''
		folder = askdirectory(title="Create New Folder")
		if folder is not str(): os.makedirs(folder)

	def moveFile(self):
		'''moving an .mp3 file to a different location'''
		def move():
			from_arg = self.path.get().replace('/',"\\") + "\\" + move_from.get()
			to_arg = move_to.get()

			if os.name == "nt":
				arg_list = ["cmd", "/c", "move", from_arg, to_arg]
			elif os.name == "posix":
				arg_list = ["mv", from_arg, to_arg]
			
			try:
				os.chdir(move_to.get())
				if not os.path.exists(move_from.get()) is True:
					subprocess.call(arg_list)
					showinfo("Moved File", "File \n\'{0}\'\nhas been moved from \n\'{1}\' to \n\'{2}\'".format(move_from.get(), self.path.get(), move_to.get()))
					self.moveFiles.destroy()
					self.getMusic()
				else:
					showinfo("File Already Exists", "File \'{0}\' already exists in \'{1}\'! The file will not be moved.".format(move_from.get(), move_to.get()))
			except Exception as e:
				showerror("Error Moving File", "There was an error moving {0}!\n{1}\n\nPlease try again.".format(move_from.get(), str(e)))
				
		move_from = StringVar()
		move_to = StringVar()
		
		self.moveFiles = Toplevel()
		self.moveFiles.title("Move File to New Directory")
		pos = centerWindow(self.moveFiles, 415, 120)
		self.moveFiles.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))

		Label(self.moveFiles, text="Name of file to move:").grid(sticky=W, padx=5)
		Entry(self.moveFiles, textvariable=move_from, state=DISABLED, width=50).grid(sticky=W, padx=5)
		move_from.set(self.value['text'])
		Label(self.moveFiles, text="Enter path of directory you want to move the file:").grid(sticky=W, padx=5)
		ent = Entry(self.moveFiles, textvariable=move_to, width=50)
		ent.grid(sticky=W, padx=5)
		ent.focus()
		ent.icursor(END)
		move_to.set(self.path.get())
		Button(self.moveFiles, text="Move File", command=move).grid(sticky=EW, padx=15, pady=7)

	def removeFile(self):
		removefile = askquestion("Remove File","Are you sure you want to remove {0}".format(self.value['text']))
		os.remove(removefile) if removefile == True else False
		self.getMusic()

	def changeName(self):
		'''renames selected music file'''
		os.chdir(self.dname)
		os.rename(self.value['text'], self.newName.get()+".mp3")
		self.nameFile.destroy()
		search = self.searchStr.get()
		self.getMusic()
		self.searchStr.set(search)

	def renameFile(self):
		'''renames the chosen music file'''
		def closeWindow():
			self.nameFile.destroy()

		title = StringVar()
		self.nameFile = Toplevel()
		self.nameFile.title("Rename Music File")
		pos = centerWindow(self.nameFile, defaults.renameWidth, defaults.renameHeight)
		self.nameFile.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))
		text = Label(self.nameFile, text="Edit the name of the music file (excluding ext, e.g. .mp3)")
		text.grid(sticky=W+E, columnspan=4, padx=25)
		self.newName = Entry(self.nameFile, textvariable=title, width=30, justify=CENTER)
		title.set(self.value['text'][:-4])
		self.newName.grid(row=1, sticky=W+E, columnspan=4, padx=25)
		self.newName.focus()
		changeBtn = Button(self.nameFile, text="Change", command=self.changeName)
		changeBtn.grid(row=2, column=1)
		cancelBtn = Button(self.nameFile, text="Cancel", command=closeWindow)
		cancelBtn.grid(row=2, column=2)
		
	def getMusic(self):
		'''get music files from directory and display in ListBox'''
		size = length = 0
		paused = False
		os.chdir(self.dname)
		# clearing the StringVars, if anything is there
		for c in range(len(self.cats)):
			self.cats[c].set("")

		self.songCntStr.set("Performing calculations...")
		master.config(cursor="watch")
		master.update()
		
		# populate files in list, get size of all files in directory
		file_types = ('.mp3','.mp4','.m4a','.wma')
		self.missingMetadata = []
		self.all_music.clear()
		for fn in os.listdir():
			if fn[-4:] in file_types:
				try:
					s = MP3(fn)
					self.all_music.append([fn, s['TIT2'][0], s['TPE1'][0], s['TALB'][0], s['TCON'][0], ('{0:02}:{1:02}:{2:02}').format(
						int(s.info.length%86400)//3600, int(s.info.length%3600)//60, int(s.info.length%60)), int(s.info.bitrate / 1000)])
					size += os.stat(fn).st_size
					length += s.info.length
				except KeyError as e:
					self.missingMetadata.append(fn)
					self.all_music.append([fn, fn, " ", " ", " ", ('{0:02}:{1:02}:{2:02}').format(
						int(s.info.length%86400)//3600, int(s.info.length%3600)//60, int(s.info.length%60)), int(s.info.bitrate / 1000)])
					size += os.stat(fn).st_size
					length += s.info.length
				except HeaderNotFoundError as e:
					if fn[-4:] == ".wma":
						showerror("WMA Conversion Attempt","Aborting conversion! Possible DRM protection.")
					else:
						self.recreateMP3File(fn)

		# get size of entire directory and convert total time of all songs
		convertedSize, convertedTime = self.conversion(size, length)

		# set the maximum value for the progress bar
		self.maximum = len(self.all_music)
		self.progressBar["maximum"] = self.maximum

		# delete all contents from Treeview and re-populate with new information; update progress bar before adding each
		for item in self.musicLb.get_children():
			self.musicLb.delete(item)
		for i in self.all_music:
			self.update_progressbar()
			self.musicLb.insert("", END, text=i[0], values=(i[1], i[2], i[3], i[4], i[5], i[6]))
		
		# clearing any album art (set to default)
		self.art = Image.open(self.default)
		resized = self.art.resize((194, 194), Image.ANTIALIAS)
		self.artImage = ImageTk.PhotoImage(resized)
		self.canvas.itemconfigure(self.canvas_image, image=self.artImage)
			
		# updating total music files in directory/listbox
		self.songCntStr.set("Total Files: "+str(len(self.all_music))+"; Total Size: "+convertedSize+"; Total Time: "+convertedTime)
		master.config(cursor="")
		
		# setting focus to listbox
		self.searchBar.delete(0, END)
		self.searchBar.config(state=NORMAL)
		self.searchBar.focus()
		self.play.config(state=NORMAL)
		self.mastermenu.entryconfig("Metadata", state=NORMAL)
		self.metaMenu.entryconfig("Search Missing Metadata", state=DISABLED)
		
	def update_progressbar(self):
		count = self.song_count.get()
		count += 1
		self.song_count.set(count)
		self.songsAddedStr.set("{0}%".format(int((count / self.maximum) * 100)))
		self.progressBar.update()

		if self.progressBar["value"] == self.maximum:
			self.song_count.set(0)
			self.songsAddedStr.set("")

	def getNewDirectory(self):
		directory = askdirectory()
		if directory == '' and os.name == "posix":
			self.mastermenu.entryconfig("Directory", state=DISABLED)
			self.mastermenu.entryconfig("Advanced...", state=DISABLED)
			self.dname = '/home/alex/Music'
		elif directory == '' and os.name == "nt":
			self.mastermenu.entryconfig("Directory", state=DISABLED)
			self.mastermenu.entryconfig("Advanced...", state=DISABLED)
			self.dname = u"C:\\Users\\Alex\\Music"
		else:
			self.dname = directory
			os.chdir(self.dname)
			self.path.set(self.dname)
			self.lbl.config(text="\nCurrent Directory: {0}".format(self.path.get()))
			self.getMusic()
			self.mastermenu.entryconfig("Directory", state=NORMAL)
			self.mastermenu.entryconfig("Advanced...", state=NORMAL)

	def searchMetadata(self):
		'''search for missing metadata via the Internet - using Bing'''
		metaWin = Toplevel()
		metaWin.title("Missing Metadata - \"%s\" by %s" % (self.song['TIT2'], self.song['TPE1']))
		pos = centerWindow(metaWin,750,300)
		metaWin.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))
	
	def showMissingMetadata(self):
		'''display all files that having missing metadata information'''
		missingMetaWin = Toplevel()
		missingMetaWin.title("Songs with Missing Metadata")
		pos = centerWindow(missingMetaWin,750,245)
		missingMetaWin.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))
		missingMetaWin.resizable(False, False)
		missingMetaWin.config(cursor="arrow")
		missingText=Text(missingMetaWin, width=defaults.missingMDWidth, height=defaults.missingMDHeight)
		[missingText.insert(END, f+"\n") if len(self.missingMetadata) > 0 else next for f in self.missingMetadata]
		missingText.insert(END, "No files with missing metadata") if len(self.missingMetadata) == 0 else next
		missingText.insert(END, "\nTotal: %s files" % len(self.missingMetadata))
		missingText.config(state=DISABLED, cursor="arrow")
		missingText.focus()
		missingText.grid()

	def search(self, args):
		'''searching for the criteria entered by user'''
		def tree(searchItems):
			# creating Multi-column Treeview widget to hold search results
			self.tree = Treeview(self.searchWin, columns=searchItems)
			vsb = Scrollbar(self.tree, orient=VERTICAL, command=self.tree.yview)
			self.tree.config(yscrollcommand=vsb.set)
			self.tree.heading("#0", text=title.upper())
			for s in searchItems:
				if s == "BPM" or s == "Genre":
					self.tree.column(s, width=75, anchor="center", stretch=False)
				else:
					self.tree.column(s, width=350, anchor="center", stretch=False)
				self.tree.heading(s, text=s)
			self.tree.bind('<Double-1>', self.displayInfo)
			self.tree.columnconfigure(0, weight=1, minsize=1000)
			self.tree.rowconfigure(0, minsize=200)
			self.tree.grid(row=3, columnspan=7, sticky="nsew", padx=20, pady=10)
			vsb.grid(column=1, sticky=N+S+E, in_=self.tree)
			
		def find(event):
			'''finding and building the tree based on search criteria'''
			# args[0] = title, args[1] = searchItems, args[2] = criteria
			# clear() if args[2] != '' else next
			self.searchWin.config(cursor="watch")
			self.searchWin.update()

			try:
				os.chdir(self.dname)
				f = str(criteria.get()).lower()
				results = mdict()
				
				if args[0] == "artist":		# album artist
					for m in self.all_music:
						try:
							s = MP3(self.dname+"/"+m[0])
							artist = s['TPE2'][0]
							# setting the album artist as key in dictionary
							if f in artist.lower():
								results[artist] = s
						except KeyError:
							pass
						except TclError:
							pass					
					for k in results.keys():
						self.tree.insert("", END, k, text=k)	# set album artist as parent of tree
						for v in results[k]:
							key = "{0} ({1})".format(v['TALB'][0], v['TDRC'][0])
							if not self.tree.exists(key):
								self.tree.insert(k, END, key, text=key)
								self.tree.insert(key, END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album', 'BPM')
							else:
								self.tree.insert(key, END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album', 'BPM')
				elif args[0] == "album":	# album
					for m in self.all_music:
						try:
							s = MP3(self.dname+"/"+m[0])
							album = str(s['TALB'][0])

							# setting the album as key in dictionary
							if f in album.lower():
								results[album] = s
						except KeyError:
							pass
						except TclError:
							pass					
					for k in results.keys():
						for v in results[k]:
							if not self.tree.exists(k):
								key = "{0} ({1} - {2})".format(k, v['TPE2'][0], v['TDRC'][0])
								self.tree.insert("", END, k, text=key)
								self.tree.insert(k, END, None, text=v['TRCK'][0], values=(v['TIT2'][0], v['TCON'][0], v['TBPM'][0])) #('Song', 'Genre', 'BPM')
							else:
								self.tree.insert(k, END, None, text=v['TRCK'][0], values=(v['TIT2'][0], v['TCON'][0], v['TBPM'][0])) #('Song', 'Genre', 'BPM')
				elif args[0] == "genre":	# genre
					for m in self.all_music:
						try:
							s = MP3(self.dname+"/"+m[0])
							genre = str(s['TCON'][0])
							if f in genre.lower():
								results[genre] = s
						except KeyError:
							pass
						except TclError:
							pass
					for k in results.keys():
						self.tree.insert("", END, k, text=k)
						for v in results[k]:
							if not self.tree.exists(v['TPE2'][0]):
								key = "{0} ({1})".format(v['TALB'][0], v['TDRC'][0])
								self.tree.insert(k, END, v['TPE2'][0], text=v['TPE2'][0])
								self.tree.insert(v['TPE2'][0], END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], key, v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album (Year)', 'Song Artists', 'BPM')
							else:
								self.tree.insert(v['TPE2'][0], END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], key, v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album (Year)', 'Song Artists', 'BPM')
				elif args[0] == "year":		# year
					for m in self.all_music:
						try:
							s = MP3(self.dname+"/"+m[0])
							year = str(s['TDRC'][0])
							if f in year:
								results[year] = s
						except KeyError:
							pass
						except TclError:
							pass
					try:
						for k in results.keys():
							self.tree.insert("", END, k, text=k)
							for v in results[k]:
								self.tree.insert(k, END, None, values=(v['TIT2'][0], v['TALB'][0], v['TCON'][0], v['TBPM'][0]))
					except KeyError:
						if 'TBPM':
							v['TBPM'][0] = 0
				elif args[0] == "bpm":		# bpm
					for m in self.all_music:
						try:
							s = MP3(self.dname+"/"+m[0])
							bpm = str(s['TBPM'][0])
							if f in bpm:
								results[bpm] = s
						except KeyError:
							pass
						except TclError:
							pass
					for k in results.keys():
						self.tree.insert("", END, k, text=k)
						for v in results[k]:
							self.tree.insert(k, END, None, text=v['TPE1'][0], values=(v['TIT2'][0], v['TALB'][0], v['TCON'][0], v['TDRC'][0]))
			except AttributeError:
				onError(criteria)
			except TypeError:
				onError(criteria)
			
			self.searchWin.config(cursor="")
			
			if self.tree.get_children() == ():
				nullSearch(title, criteria)

		def clear():
			searchItem.delete(0, END)
			searchItem.focus()
			tree(searchItems)

		def nullSearch(title, criteria):
			showinfo("No Results Found", "There were no %s results for \'%s\'" % (title, criteria.get()), parent=self.searchWin)
			clear()

		def onError(criteria):
			showerror("Directory Error", "Search failed: '%s'!\nNo directory chosen" % criteria.get(), parent=self.searchWin)
			clear()
    	
		title = args[0]
		searchItems = args[1]
		criteria = StringVar()
		self.searchWin = Toplevel()
		self.searchWin.attributes("-topmost", False)
		pos = centerWindow(self.searchWin,1050, 300)
		self.searchWin.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
		self.searchWin.resizable(False, False)
		
		Label(self.searchWin).grid(columnspan=5)
		if title == 'bpm':
			self.searchWin.title("%s Search" % title.upper())
			Label(self.searchWin, text="Enter the %s you want to search for:" % title.upper()).grid(row=1, column=2, padx=35)
		else:
			self.searchWin.title("%s Search" % title.title())
			Label(self.searchWin, text="Enter the %s you want to search for:" % title.lower()).grid(row=1, column=2, padx=35)

		searchItem = Entry(self.searchWin, textvariable=criteria, width=30)
		searchItem.bind('<Return>', find)
		searchItem.grid(row=1, column=3, sticky="w")
		searchItem.focus()
		clearBtn = Button(self.searchWin, text="Clear", width=10, command=clear)
		clearBtn.grid(row=2, column=2, padx=5)
		searchBtn = Button(self.searchWin, text="Search", width=10, command=functools.partial(find, (title, searchItems, criteria)))
		searchBtn.grid(row=2, column=3, padx=5)
		tree(searchItems)

	def convertToMP3(self, option=0):
		'''converting non-MP3 music files to MP3 with 128 kbps bitrate (default)'''
		def closeWin():
			self.convert.destroy()

		def convert(args):
			'''convert the file to the desired filetype'''
			for i in range(2):
				args[i].config(cursor="watch")
				args[i].update()

			try:
				if args[3] == 0:
					for f in args[1].get(1.0, END).split("\n"):
						AudioSegment.from_file(f).export(f[:-4]+'.mp3', bitrate="128k", format=args[2].get())
				else:
					AudioSegment.from_file(args[1]).export(args[1][:-4]+'.mp3', bitrate="128k", format=args[2].get())

				args[0].config(cursor="")
				showinfo("Filetype Conversion","Conversion is completed!")
			except CouldntDecodeError as e:
				showerror("Conversion Failure",e)
			closeWin()
		
		FILETYPES = [
		('.mp3', 'mp3'),
		('.mp4', 'mp4'),
		('.avi', 'avi'),
		('.wav', 'wav')]
		convert2type = StringVar()
		os.chdir(self.dname)
		self.convert = Toplevel()
		self.convert.title("Convert to MP3 Files")
		Label(self.convert, text="Non-MP3 Files to Convert - Default Bitrate = 128kbps").grid(row=1, columnspan=4)
		
		if option == 0:
			pos = centerWindow(self.convert, 650, 260)
			self.convert.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
			converting = Text(self.convert, font="Times 10", width=86, height=10, cursor="arrow")
			converting.grid(row=3, padx=20, columnspan=4)
			for f in os.listdir():
				converting.insert(END, f+"\n") if (not f.endswith('.mp3') and "." in f) else next
				converting.config(state=DISABLED)
			convertBtn = Button(self.convert, text="Convert", width=8, command=functools.partial(convert, (self.convert, converting, convert2type, option)))
			convertBtn.config(state=DISABLED) if converting.get(1.0, END) == "\n" else next
	
			# create radio buttons
			for text, convertTo in FILETYPES:
				radioBtn = Radiobutton(self.convert, text=text, indicatoron=0, width=10, padx=10, variable=convert2type, value=convertTo)
				radioBtn.grid(row=2, column=FILETYPES.index((text, convertTo)), padx=8)
		else:
			pos = centerWindow(self.convert, 480, 125)
			self.convert.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
			Label(self.convert, text=self.value).grid(row=2, columnspan=4, ipady=7, pady=5)
			convertBtn = Button(self.convert, text="Convert", width=8, command=functools.partial(convert, (self.convert, self.value, convert2type, option)))
			# create radio buttons
			for text, convertTo in FILETYPES:
				radioBtn = Radiobutton(self.convert, text=text, indicatoron=0, width=10, padx=10, variable=convert2type, value=convertTo)
				radioBtn.grid(row=3, column=FILETYPES.index((text, convertTo)), padx=8)	

		convertBtn.grid(row=4, pady=8, column=1)
		close = Button(self.convert, text="Close", width=8, command=closeWin)
		close.grid(row=4, pady=8, column=2)
		
	def convertBitrate(self, option=0):
		'''converting bitrate of MP3 files'''
		def closeWin():
			self.bitrate.destroy()
			os.chdir(self.path.get())
			self.getMusic()

		def changeDirPath():
			os.chdir(choose.get())
			bitrateLb.delete(0, END)
			for f in os.listdir():
				bitrateLb.insert("", END, values=(MP3(f)['TIT2'][0], round(MP3(f).info.bitrate/1000),2))
			
		def convert(args):
			'''self.bitrate, bitrate, choose, option'''
			args[0].config(cursor="watch")
			args[0].update()

			if args[3] == 1:
				if os.name == "nt": f = args[2].get().split("\\")[-1]
				else: f = args[2].get().split("/")[-1]
				song = MP3(f)
				temp = MP3()
				for t in song.keys():
					temp[t] = song[t]
				
				# converting to new bitrate
				AudioSegment.from_file(f).export(f, bitrate=str(args[1].get())+'k')

				# transfer tags from temp back to saved song
				newSong = MP3(f)
				for t in temp.keys():
					newSong[t] = temp[t]
				newSong.save(f, v2_version=3)
			else:
				# copying metadata to temp MP3 file
				songsToConvert = bitrateLb.selection()
				songsToConvert = [bitrateLb.item(s)['values'][0] for s in songsToConvert]
				for songName in songsToConvert:
					songFile = self.path.get()+"/"+songName
					status.set("Converting \"{}\"...".format(songName[:-4]))
					song = MP3(songFile)
					temp = MP3()
					for t in song.keys():
						temp[t] = song[t]
					
					# converting the song to new bitrate and saving back in .mp3 file
					AudioSegment.from_file(songFile).export(songFile, bitrate=str(args[1].get())+'k')
				
					# transfer tags from temp back to saved song
					newSong = MP3(songFile)
					for t in temp.keys():
						newSong[t] = temp[t]
					newSong.save(songFile, v2_version=3)
				status.set("Finished converting!!")
			time.sleep(1)
			args[0].config(cursor="")
			showinfo("Bitrate Conversion","Conversion is completed!", parent=self.bitrate)
			closeWin()

		# ---------------------------------------------------------
		# BITRATES & THEIR QUALITY
		# ---------------------------------------------------------
	    # 320 kbps – Virtually indistinguishable from original CDs
	    # 192 kbps - Great sound quality for music files
	    # 128 kbps – Typical for musical MP3s and quality podcasts
	    # 64 kbps – Common birtate for speech podcasts
	    # 48 kbps – Reasonably common for longer speech podcasts
	    # 32 kbps – Poor, usually used to reduce download times
	    # ---------------------------------------------------------

		bitrateLb_columns = ['Title','Bitrate']
		BITRATES = [
			("32 kbps", 32),
			("48 kbps", 48),
			("64 kbps", 64),
			("128 kbps", 128),
			("192 kbps", 192),
			("320 kbps", 320)]
		
		choose = StringVar()
		bitrate = IntVar()
		status = StringVar()
		status.set("Ready.")

		self.bitrate = Toplevel()
		self.bitrate.title("Convert Bitrate")
		os.chdir(self.path.get())

		if option == 1:
			song = MP3(self.value['text'])
			pos = centerWindow(self.bitrate, defaults.convertWidth1, 80)
			self.bitrate.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
			Label(self.bitrate, text="Song: "+self.value['text']+"; Bitrate: "+str('{0:00.0f}'.format(song.info.bitrate/1000)), font="Arial 10").grid(row=1, \
				columnspan=6, sticky=E+W)
			if os.name == "nt": choose.set(os.getcwd()+"\\"+self.value['text'])
			else: choose.set(os.getcwd()+"/"+self.value['text'])
		else:
			pos = centerWindow(self.bitrate, 530, defaults.convertHeightWin)
			self.bitrate.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
			Label(self.bitrate, text="Enter directory:", font="Times 11").grid(row=1, padx=10)
			bitrateDirectory = Entry(self.bitrate, textvariable=choose, font="Times 10", width=defaults.convertWidth2)
			choose.set(self.path.get())
			bitrateDirectory.grid(column=1, columnspan=4, row=1, sticky=E+W)
			changeDir = Button(self.bitrate, text="Change", command=changeDirPath)
			changeDir.grid(row=1, column=5)
				
			# show list of songs in Listbox with checkboxes
			bitrateFrame = Frame(self.bitrate)
			bitrateFrame.grid(row=3, columnspan=6)
			bitrateLb = Treeview(bitrateFrame, columns=bitrateLb_columns, height=8, show="headings", selectmode=EXTENDED)
			vsb = Scrollbar(bitrateFrame, orient="vertical", command=bitrateLb.yview)
			bitrateLb.configure(yscrollcommand=vsb.set)
			
			# building the tree (headers and items)
			[bitrateLb.heading(col, text=col.title(), command=lambda c=col: self.sortby(bitrateLb, c, 0)) for col in bitrateLb_columns]
			bitrateLb.column('Title', width=300)
			bitrateLb.column('Bitrate', anchor="center", width=defaults.bitrateColWidth)
			bitrateLb.grid(row=3, sticky=N+E+S+W, padx=25)
			vsb.grid(row=3, column=6, sticky=N+S+E)
		
			for f in os.listdir():
				if f.endswith(".mp3"):
					try:
						bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))
					except HeaderNotFoundError:
						self.recreateMP3File(f)
						bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))

		# create radio buttons
		for text, rate in BITRATES:
			radioBtn = Radiobutton(self.bitrate, text=text, variable=bitrate, value=rate)
			radioBtn.grid(row=2, column=BITRATES.index((text, rate)))


		conversionStatus = Label(self.bitrate, textvariable=status, font="Times 9").grid(row=5, columnspan=6, sticky=W)
		# convertBtn = Button(self.bitrate, text="Convert", command=functools.partial(convert, (self.bitrate, bitrate, choose, option)))
		convertThread = threading.Thread(target=convert, args=([self.bitrate, bitrate, choose, option],))
		convertBtn = Button(self.bitrate, text="Convert", command=convertThread.start)
		convertBtn.grid(column=1, columnspan=2, row=4, pady=5)
		cancelBtn = Button(self.bitrate, text="Cancel", command=closeWin)
		cancelBtn.grid(column=3, columnspan=2, row=4, pady=5)
		
def centerWindow(master, width, height):
	sW = master.winfo_screenwidth()
	sH = master.winfo_screenheight()
	x = (sW/2) - (width/2)
	y = (sH/2) - (height/2)
	return [width, height, x, y]

if __name__ == '__main__':
	master = Tk()
	EditMetadata(master)
	master.title("MP3 Metadata Editor")
	# add program icon
	progDir = sys.path[0]
	master.iconphoto(True, PhotoImage(file=os.path.join(progDir,'music-note-icon.png')))
	position = centerWindow(master, defaults.width, defaults.height)
	master.geometry('%dx%d+%d+%d' % (position[0], position[1], position[2],	0))
	master.mainloop()