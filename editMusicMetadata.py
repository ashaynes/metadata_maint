# usr/bin/env python3

import functools
import inspect
import io
import math
import os
import re
import subprocess
import sys
import threading
import time
import tkinter.font as tkFont
import urllib
from tkinter import (
    CENTER, DISABLED, END, EW, EXTENDED, NORMAL, VERTICAL, WORD, BooleanVar,
    Button, Canvas, E, Entry, Frame, IntVar, Label, LabelFrame, Menu, N,
    OptionMenu, PhotoImage, Radiobutton, S, Scrollbar, StringVar, TclError,
    Text, Tk, Toplevel, W)
from tkinter.filedialog import askdirectory
from tkinter.messagebox import *
from urllib.request import *

import ffmpy
import musicbrainzngs as mb
import mutagen
import numpy as np
import PIL.Image
import PIL.ImageTk
import pygame as pg
from bs4 import BeautifulSoup
from mutagen.id3 import (APIC, ID3, TALB, TBPM, TCON, TDRC, TIT2, TPE1, TPE2,
                         TPOS, TRCK, USLT, ID3NoHeaderError)
from mutagen.mp3 import MP3, HeaderNotFoundError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import albumArt.albumArt as albumArt
import audio.playbackMusicFile as playBack
import lyrics.lyrics as lyrics
import shared.genres as genres
import utils
import utils.defaults as default
import windows.customWindowSize as windows


'''
TODO:
1 -> Create 'displayInfo' function for Search options to display metadata on double-click, differentiate between artist, album and song (WIP)
2 -> Create function that allows an online search of MP3s to download and downloads the selected song to the default directory ??
3 -> Create function that downloads a top 40 list, based on genre selected (BillboardAPI)
''' 

class mdict(dict):
	def __setitem__(self, key, value):
		"""add the given value to the list of values for this key"""
		self.setdefault(key, []).append(value)

class EditMetadata(Frame):
	def sortby(self, tree, col, descending):
		"""sort tree contents when a column header is clicked"""
		data = [(tree.set(k, col), k) for k in tree.get_children('')]
		data.sort(reverse=descending)
		[tree.move(k, '', index) for index, (val, k) in enumerate(data)]
		tree.heading(col, command=lambda col=col: self.sortby(tree, col, int(not descending)))

	def __init__(self, master):
		def mainQuit(master):
			master.quit() if askyesno("Exit?", "Do you really want to quit this program?") == True else False

		def switchModes():
			'''switch between Edit Mode and View Mode'''
			self.save.config(state="normal") if self.state.get() == True else self.save.config(state="disabled")
			self.mode.set("Edit Mode") if self.state.get() == True else self.mode.set("View Mode")
			self.editFile() if self.state.get() == True else self.viewFile()

		# set initial values to certain parameters used within the program
		if os.name == "nt":
			os.chdir("C:\\Code\\Music Metadata Editor\\")
			self.default = f"{os.getcwd()}\\media\\images\\No Image Available.jpg"
		if os.name == "posix":
			os.chdir('/home/alex/Music/')
			self.default = f"{os.getcwd()}/No Image Available.jpg"
		
		# register client to musicBrainz
		mb.set_useragent("MP3 Editor", "1.0", "alexbballa@hotmail.com")
		self.paused = False
		self.entries = []
		self.l = ['Song Title','Artist(s)','Album','Album Artist','Genre','Year','Track Number','BPM','Disc Number']
		self.all_music = []
		
		self.song_path = StringVar(master)
		self.title = StringVar(master)
		self.artist = StringVar(master)
		self.album = StringVar(master)
		self.performer = StringVar(master)
		self.genre = StringVar(master)
		self.date = StringVar(master)
		self.tracknumber = StringVar(master)
		self.bpm = StringVar(master)
		self.discnumber = StringVar(master)
		self.albumart = StringVar(master)
		self.directoryStr = ""
		self.searchStr = StringVar(master)
		# self.searchStr.trace("w", lambda var, index, mode: self.update_lb())
		self.songCntStr = StringVar(master)
		self.path = StringVar()
		self.current_song_selected = StringVar(master)
		self.current_song_playing = StringVar(master)
		
		self.musicLb_columns = ['Title', 'Artist(s)', 'Album', 'Genre', 'Time', 'Bitrate']
		self.tags = ['TIT2', 'TPE1', 'TALB', 'TPE2', 'TCON', 'TDRC', 'TRCK', 'TBPM', 'TPOS', 'APIC', 'USLT', 'SYLT']
		self.cats = [self.title, self.artist, self.album, self.performer, self.genre, self.date, self.tracknumber, self.bpm, self.discnumber, self.albumart]
		
		# creating popup Menu for Listbox
		self.menu = Menu(master, tearoff=0)
		self.menu.add_command(label="Extract Album Art", command=functools.partial(albumArt.extractArt, self))
		self.menu.add_command(label="Download Album Art", command=self.downloadAlbumArt)
		self.menu.add_command(label="Move File", command=self.moveFile)
		self.menu.add_command(label="Copy File", command=self.copyFile)
		self.menu.add_command(label="Delete File", command=self.deleteFile)
		self.menu.add_command(label="Rename File", command=self.renameFile)
		self.menu.add_command(label="Change File Type", command=functools.partial(self.convertToMP3, 1))
		self.menu.add_command(label="Change Bitrate", command=functools.partial(self.convertBitrate, 1))
		self.menu.add_command(label="Update Lyrics/Description", command=functools.partial(lyrics.lyrics, self))

		# creating top Menu bar
		self.mastermenu = Menu(master)
		# menu options for files and directories
		self.fileMenu = Menu(self.mastermenu, tearoff = 0)
		self.mastermenu.add_cascade(label = "File", menu = self.fileMenu, underline=0)
		# self.fileMenu.add_command(label = "Download Album Art", command = albumArt.downloadArt)
		self.fileMenu.add_command(label = "Print Tracklist", command = self.printTracklist)
		self.fileMenu.add_separator()
		self.fileMenu.add_command(label = "Exit", command=functools.partial(mainQuit, master))
		# edit menu options
		self.editMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label="Directory", menu=self.editMenu, underline=0)
		self.editMenu.add_command(label="Convert to MP3", command=self.convertToMP3)
		self.editMenu.add_command(label="Convert Bitrate", command=self.convertBitrate)
		# analyze MP3 options
		self.editMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label="Analyze", menu=self.editMenu, underline=0)
		self.editMenu.add_command(label="Calculate BPM", command=self.launchBpmAnalyzer)
		self.editMenu.add_command(label="Analyze Gain", command=self.analyzeGain)
		# metadata menu option
		self.metaMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label="Metadata", menu=self.metaMenu, underline=0)
		self.metaMenu.add_command(label="Search Missing Metadata", command=self.searchMetadata)
		self.metaMenu.add_command(label="Show Songs with Missing Metadata", command=self.showMissingMetadata)
		self.metaMenu.add_command(label="Show Songs with Corrupted Headers", command=self.showCorruptFiles)
		# search menu options
		self.searchMenu = Menu(self.mastermenu, tearoff=0)
		self.mastermenu.add_cascade(label = "Search", menu=self.searchMenu, underline=0)
		self.searchMenu.add_command(label = "Artist", command=functools.partial(self.search, ('artist', ('Song', 'Track Artist(s)', 'BPM'))))
		self.searchMenu.add_command(label = "Album", command=functools.partial(self.search, ('album', ('Song', 'Genre', 'BPM'))))
		self.searchMenu.add_command(label = "Genre", command=functools.partial(self.search, ('genre', ('Song', 'Album', 'BPM'))))
		self.searchMenu.add_command(label = "Year", command=functools.partial(self.search, ('year', ('Song', 'Album', 'Genre', 'BPM'))))
		self.searchMenu.add_command(label = "BPM", command=functools.partial(self.search, ('bpm', ('Song', 'Album', 'Genre', 'Year'))))
		master.config(menu=self.mastermenu)

		# configuring certain menu option to be disabled at initial program launch
		self.mastermenu.entryconfig("Directory", state=DISABLED)
		self.mastermenu.entryconfig("Metadata", state=DISABLED)
		self.mastermenu.entryconfig("Search", state=DISABLED)

		Label(master).grid(columnspan=6)
		# creating Label and Entry items
		metadata = LabelFrame(master, text='Metadata')
		metadata.grid(columnspan=3, sticky=W, padx=10, ipadx=2)
		# change TCON from Entry to OptionMenu
		for item in self.l:
			i = self.l.index(item)
			Label(metadata, text=f"{item}:").grid(row=i+1, sticky='W', padx=15)
			if item != "Genre":
				self.entries.append(Entry(metadata, textvariable=self.cats[i], width=default.metadataEntryWidth, state=DISABLED))
			else:
				optionmenu = OptionMenu(metadata, self.cats[i], *genres.sortedGenres)
				optionmenu.config(width=default.metadataOptionMenuWidth, state=DISABLED)
				self.entries.append(optionmenu)
				self.cats[i].set('')
			self.entries[i].grid(row=i+1, column=1, columnspan=4, sticky='W')
		
		# adding Buttons
		self.mode = StringVar()
		self.state = BooleanVar()
		self.mode.set("View Mode")
		self.edit = ttk.Checkbutton(metadata, textvariable=self.mode, variable=self.state, onvalue=True, offvalue=False, command=switchModes, state=DISABLED)
		# width=12, height=default.editHeight, indicatoron=0, 
		self.edit.grid(row=len(self.l)+1, column=1, sticky=E+W)
		self.save = Button(metadata, text="Save Metadata", width=12, state=DISABLED, command=self.saveFile)
		self.save.grid(row=len(self.l)+1, column=2, sticky=E+W, pady=11)
		self.getAlbumArt = Button(metadata, text="Add Album Art", state=DISABLED, width=12, command=functools.partial(albumArt.addArt, self))
		self.getAlbumArt.grid(row=len(self.l)+1, column=4, sticky='EW', pady=11)
		
		# creating empty Canvas for media player (album art place holder)
		self.player = LabelFrame(master, text='Media Player')
		self.player.grid(row=1, column=3, sticky='WE')
		self.original = PIL.Image.open(self.default)
		self.resized = self.original.resize((194,194), PIL.Image.ANTIALIAS)
		self.albumart = PIL.ImageTk.PhotoImage(self.resized)
		self.canvas = Canvas(self.player, width=194, height=194)
		self.canvas_image = self.canvas.create_image(97, 97, image=self.albumart)
		self.canvas.grid(row=1, rowspan=3, padx=49, columnspan=3, sticky='NSEW')
		
		# create media buttons for media player
		self.pause_unpause = StringVar()
		self.pause_unpause.set("Pause")
		self.play = Button(self.player, text="Play", command=functools.partial(playBack.playSong, self), state=DISABLED, width=5)
		self.play.grid(row=5, column=0, sticky=E+W, pady=7)
		self.pause = Button(self.player, textvariable=self.pause_unpause, command=functools.partial(playBack.pauseSong, self), state=DISABLED, width=5)
		self.pause.grid(row=5, column=1, sticky=E+W, pady=7)
		self.stop = Button(self.player, text="Stop", command=functools.partial(playBack.stopSong, self), state=DISABLED, width=5)
		self.stop.grid(row=5, column=2, sticky=E+W, pady=7)
		
		# display lyrics/description (if any)
		self.lyrics = LabelFrame(master, text="Lyrics")
		self.lyricsText = Text(self.lyrics, height=default.lyricsTextHeight, width=default.lyricsTextWidth, font="Tahoma 8 italic bold", wrap=WORD, background="dark blue", foreground="white")
		self.lyricsText.grid()
		self.lyrics.grid(row=1, rowspan=3, column=4, columnspan=2, padx=10, sticky="NSE")
		
		# add total music files and Button to browse to different path
		files = LabelFrame(master, text='Files & Folders', width=default.filesWidth, height=default.filesHeight)
		files.grid(row=2, columnspan=4, padx=(10,0), ipadx=8, ipady=8, sticky='SEW')
		self.lbl = Label(files, text="\nCurrent Folder Path:")
		self.lbl.grid(row=2, columnspan=3, padx=15, sticky='W')
		browseBtn = Button(files, text="Change Folder", width=25, command=self.getNewDirectory)
		browseBtn.grid(row=2, column=3, sticky='E')
		
		# creating the Multi-column Listbox (Treeview) for the music files
		frame = Frame(files, width=default.musicLbFrame)
		frame.grid(columnspan=4, sticky='NSEW')
		self.musicLb = ttk.Treeview(columns=self.musicLb_columns, height=default.musicLbHeight, show="headings")
		self.musicLb.bind('<<TreeviewSelect>>', self.onselect)
		self.musicLb.bind('<Button-3>', self.popup)
		self.vsb = Scrollbar(orient="vertical", command=self.musicLb.yview)
		self.musicLb.configure(yscrollcommand=self.vsb.set, height=16)
		self.musicLb.grid(row=len(self.l)+5, rowspan=3, columnspan=4, sticky='NESW', padx=15, in_=frame)
		self.vsb.grid(column=1, row=len(self.l)+5, rowspan=3, sticky='NS', in_=frame)
		frame.grid_columnconfigure(0, weight=1)

		# building the tree (headers and items)
		[self.musicLb.heading(col, text=col.capitalize(), command=lambda c=col: self.sortby(self.musicLb, c, 0)) for col in self.musicLb_columns]
		self.musicLb.column('Title', width=240)
		self.musicLb.column('Artist(s)', width=240)
		self.musicLb.column('Genre', width=85)
		self.musicLb.column('Time', width=55, anchor="center")
		self.musicLb.column('Bitrate', width=50, anchor="center")

		# total music files in directory/listbox
		self.songCount = Label(master, textvariable=self.songCntStr)
		self.songCount.grid(row=len(self.l)+4, padx=10, sticky='NW')
		self.songCntStr.set("Total Files: n/a; Total Size: n/a; Total Time: n/a")

		# progress bar to show loading of file(s)
		self.song_count = IntVar()
		self.progressBar = ttk.Progressbar(master, value=0, variable=self.song_count, orient="horizontal", length=200, mode="determinate")
		self.progressBar.grid(row=len(self.l)+4, column=5, padx=10, pady=5, sticky='SE')
	
	def displayInfo(self, event):
		'''
		Displays general information for the song selected
		'''
		self.displayWindow = Toplevel(master)
		selected_song = self.tree.item(self.tree.selection())
		self.displayWindow.title(f"\'{selected_song['values'][0]}\' General Info")

	def downloadAlbumArt(self):
		'''
		Downloads album art for specific album and artist
		'''
		albumArt.downloadArt(self)
		albumArt.addArt(self)
		self.getMusic()

	def printTracklist(self, event):
		'''
		Function that takes the album and track list information, prints to selected or default printer
		'''
		return
	
	def popup(self, event):
		'''
		Make popup (context) menu enabled on grid
		'''
		if len(self.musicLb.get_children('')) > 0:
			self.menu.tk_popup(event.x_root, event.y_root)

	def conversion(self, filesize=0, totaltime=0):
		'''
		Converts the filesize and/or total time of files in the Listbox
		'''
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

	def recreateMP3File(self, song_path):
		'''
		Creates a new header for the MP3 file and necessary metadata
		'''
		try:
			self.song = ID3(song_path)
			self.newFile = MP3()
			
			# copy necessary contents of old .mp3 file to new .mp3 file
			for t in self.song.keys():
				if t in self.tags:
					self.newFile[t] = self.song[t]
			return self.newFile
		except:
			self.corruptMP3.append(song_path)

	def onselect(self, e):
		'''
		Displays the existing metadata if there are not any errors.
		else, correct the errors and then display the metadata
		'''

		# collect information from the event
		self.value = self.musicLb.item(self.musicLb.selection())
		self.play.config(state=NORMAL)
		self.stop.config(state=DISABLED)
		
		if os.getcwd() is not self.dname:
			os.chdir(self.dname)
		
		if os.name == "posix":
			self.song_path.set(f"{os.getcwd()}/{+self.value['text']}")
		if os.name == "nt":
			self.song_path.set(f"{os.getcwd()}\\{self.value['text']}")

		# read .mp3 file
		try:
			self.song = MP3(self.song_path.get()) # dictionary
			
			# "removing" unnecessary tags if header is present
			self.remove = []
			apicFound = [key for key in self.song.keys() if "APIC" in key]
			usltFound = [key for key in self.song.keys() if "USLT" in key]
			
			for t in self.song.keys():
				if t in apicFound or t in usltFound:
					continue
				if t not in self.tags:
					self.remove.append(t)

			for tag in self.remove:
				self.song.pop(tag)
				self.song.save()
			
			self.state.set(False)
			self.mode.set("View Mode")
			self.save.config(state=DISABLED)

			# determine if album art can be extracted from the MP3
			if albumArt.isAlbumArtInFile(self.song_path.get()) == False and 0 in [key.find("APIC") for key in self.song.keys()]:
				self.menu.entryconfig("Extract Album Art", state=NORMAL)
			else:
				self.menu.entryconfig("Extract Album Art", state=DISABLED)
		
			# print whatever contents are in the tags in the .mp3 file
			for k in self.song.keys():
				if "APIC" in k or "USLT" in k: continue
				self.cats[self.tags.index(k)].set(self.song[k][0]) if k not in self.remove else next
				
			# update self.getAlbumArt Label, depending on whether APIC tag is in MP3
			for k in self.song.keys():
				if "APIC" in k:
					self.getAlbumArt.config(text="Remove Album Art", state=NORMAL, command=functools.partial(
						albumArt.removeArt, (self, master, k)))
					self.getAlbumArt.update()
					break
				else:
					self.getAlbumArt.config(text="Add Album Art", state=NORMAL, command=functools.partial(
						albumArt.addArt, self))
					self.getAlbumArt.update()	
			
			# get and display song lyrics/podcast description from metadata, if any
			self.lyricsText.delete("0.0", END)
			self.lyricsText.update()
			if 'TCON' in self.song.keys():
				usltInKeys = [tag for tag in self.song.keys() if "USLT" in tag]
				if len(usltInKeys) == 1:
					lyricsText = self.song[usltInKeys[0]]
				else:
					lyricsText = " -- No lyrics available -- " if self.song['TCON'][0] != "Podcast" else " -- No podcast description available -- "
			else:
				lyricsText = "-- Cannot get lyrics or podcast information --"
			self.lyricsText.insert("0.0", lyricsText)
			self.lyricsText.update()
					
			# determine when "Search Missing Metadata" option is available for selection in Metadata menu
			# should only be available when there is at least one metadata field (self.cats) that is empty (legit)
			tempList=self.tags[:-3]
			self.metaMenu.entryconfig("Search Missing Metadata", state=NORMAL) if any(len(self.cats[self.tags.index(t)].get())==0 for t in tempList) \
				else self.metaMenu.entryconfig("Search Missing Metadata", state=DISABLED)
			
			for k in self.entries:
				k.config(state=DISABLED)
			self.edit.config(state=NORMAL)

			# display album art on file else display default art
			self.albumArt = PIL.Image.open(self.default)			# display default album art (No Image Available)
			try:
				for tag in self.song.keys():
					if "APIC" in tag:
						imageData = self.song[tag].data
						self.albumArt = PIL.Image.open(io.BytesIO(imageData))		# display album art found if art is embedded to mp3
						break

			except Exception as e:
				if type(e) is OSError:
					self.song.pop(tag)
					self.song.save()
		
			resized = self.albumArt.resize((194, 194), PIL.Image.ANTIALIAS)
			# resized.show()
			self.albumImage = PIL.ImageTk.PhotoImage(resized)
			self.canvas.itemconfigure(self.canvas_image, image=self.albumImage)
		# do this if header is missing
		except HeaderNotFoundError:
			self.recreateMP3File(self.song_path.get())

	def editFile(self):
		'''
		Sets the textbox objects in a NORMAL state so the data can be editable
		'''
		i = 0
		for k in self.entries:
			i += 1
			next if i == 8 else k.config(state=NORMAL)
			k.focus() if i == 1 else next
		self.save.config(state=NORMAL)

	def viewFile(self):
		'''
		Sets the textbox objects in a DISABLED state so the data cannot be editable
		'''
		i = 0
		for k in self.entries:
			i += 1
			next if i == 8 else k.config(state=DISABLED)
		self.save.config(state=DISABLED)
	
	def saveFile(self):
		'''
		Saves the information from the Entry boxes to the MP3 file
		'''
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
			showerror("Error", f"{e}")
		self.getMusic()
	
	def moveFile(self):
		'''
		Moves the selected MP3 file to a different location
		'''
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
					try:
						results = subprocess.check_output(arg_list, shell=False)
						if ("1 file(s) moved." in str(results)):
							self.songCntStr.set(f"\'{move_from.get()}\' was moved from \'{self.path.get()}\' to \'{move_to.get()}\'")
						else:
							self.songCntStr.set(f"Error Moving File: {results}")
					except (subprocess.CalledProcessError, OSError, IOError) as cpe:
						showerror("Error Moving File", f"{cpe}\n{cpe.output}")
				else:
					self.songCntStr.set(f"\'{move_from.get()}\' already exists in \'{move_to.get()}\'! The file was not moved.")
			except Exception as e:
				self.songCntStr.set(f"There was an error moving {move_from.get()}! Please try again.")
				showerror("Error Moving File", f"{str(e)}")

			master.config(cursor="watch")
			master.update()
			
			self.moveFiles.destroy()
			self.getMusic()
				
		move_from = StringVar()
		move_to = StringVar()
		
		self.moveFiles = Toplevel()
		self.moveFiles.title("Move File to New Directory")
		pos = windows.centerWindow(self.moveFiles, 415, 120)
		self.moveFiles.geometry(f'{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}')

		Label(self.moveFiles, text="Name of file to move:").grid(sticky=W, padx=5)
		Entry(self.moveFiles, textvariable=move_from, state=DISABLED, width=67).grid(sticky=W, padx=5)
		move_from.set(self.value['text'])
		Label(self.moveFiles, text="Enter path of directory you want to move the file:").grid(sticky=W, padx=5)
		ent = Entry(self.moveFiles, textvariable=move_to, width=67)
		ent.grid(sticky=W, padx=5)
		ent.focus()
		ent.icursor(END)
		move_to.set(self.path.get())
		Button(self.moveFiles, text="Move File", command=move).grid(sticky=EW, padx=15, pady=7)

	def deleteFile(self):
		'''
		Deletes the MP3 file from storage
		'''
		os.chdir(self.dname)
		deleteFileResult = askokcancel("Delete File", f"Are you sure you want to delete \'{self.value['text']}\' from \'{self.dname}\'")
		
		try:
			if deleteFileResult == True:
				result = subprocess.check_output(['cmd','/c','del', self.value['text']])
				print (result)
				if True not in [self.value['text'] in song for song in os.listdir()]:
					showinfo("Deleted File", f"Successfully deleted \'{self.value['text']}\'!")
					self.getMusic()
		except Exception as e:
			showerror("Error", f"There was an error deleting \'{self.value['text']}\'.\n\n{e}")

	def copyFile(self):
		'''
		Copies selected file to a different location, defaults to overwrite
		'''
		def copy():
			from_arg = self.path.get().replace('/',"\\") + "\\" + copy_from.get()
			to_arg = copy_to.get()

			if os.name == "nt":
				arg_list = ["cmd", "/c", "copy", from_arg, to_arg, '/Y']
			elif os.name == "posix":
				arg_list = ["cp", from_arg, to_arg]
			
			try:
				os.chdir(copy_to.get())
				try:
					results = subprocess.check_output(arg_list, shell=False)
					print (results)
					if ("1 file(s) copied." in str(results)):
						self.songCntStr.set(f"\'{copy_from.get()}\' was copied to \'{copy_to.get()}\'")
					else:
						self.songCntStr.set(f"Error Copying File: {results}")
				except (subprocess.CalledProcessError, OSError, IOError) as cpe:
					showerror("Error Copying File", f"{cpe}\n{cpe.output1}")
			except Exception as e:
				self.songCntStr.set(f"There was an error copying {copy_from.get()}! Please try again.")
				showerror("Error Copying File", f"{str(e)}")

			master.config(cursor="watch")
			master.update()
			
			self.copyFiles.destroy()
			self.getMusic()
				
		copy_from = StringVar()
		copy_to = StringVar()
		
		self.copyFiles = Toplevel()
		self.copyFiles.title("Copy File to Another Directory")
		pos = windows.centerWindow(self.copyFiles, 415, 120)
		self.copyFiles.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")

		Label(self.copyFiles, text="Name of file to copy:").grid(sticky=W, padx=5)
		Entry(self.copyFiles, textvariable=copy_from, state=DISABLED, width=67).grid(sticky=W, padx=5)
		copy_from.set(self.value['text'])
		Label(self.copyFiles, text="Enter path of directory you want to copy the file to:").grid(sticky=W, padx=5)
		ent = Entry(self.copyFiles, textvariable=copy_to, width=67)
		ent.grid(sticky=W, padx=5)
		ent.focus()
		ent.icursor(END)
		copy_to.set(self.path.get())
		Button(self.copyFiles, text="Copy File", command=copy).grid(sticky=EW, padx=15, pady=7)

	def changeName(self):
		'''
		Changes the filename of the selected MP3 file
		'''
		try:
			os.chdir(self.dname)
			os.rename(self.value['text'], self.newName.get()+".mp3")
		except Exception as e:
			showerror("Error", f"There was an error renaming \'{self.value['text']}\'.\n\n{e}")
		else:
			self.nameFile.destroy()
		finally:
			self.getMusic()
	
	def renameFile(self):
		'''
		Renames the selected MP3 file
		'''
		def closeWindow():
			self.nameFile.destroy()

		title = StringVar()
		self.nameFile = Toplevel()
		self.nameFile.title("Rename Music File")
		pos = windows.centerWindow(self.nameFile, default.renameWidth, default.renameHeight)
		self.nameFile.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
		text = Label(self.nameFile, text="Rename the music file (excluding the extension, e.g. '.mp3')")
		text.grid(sticky='EW', columnspan=2)
		self.newName = Entry(self.nameFile, width=55, textvariable=title, justify=CENTER)
		title.set(self.value['text'][:-4])
		self.newName.grid(row=1, sticky=E+W, columnspan=2, padx=10, pady=(0,5))
		self.newName.focus()
		changeBtn = Button(self.nameFile, text="Change", command=self.changeName)
		changeBtn.grid(row=2, sticky=E+W, padx=5)
		cancelBtn = Button(self.nameFile, text="Cancel", command=closeWindow)
		cancelBtn.grid(row=2, column=1, sticky=E+W, padx=5)
		
	def getMusic(self):
		'''
		Get music files from directory and display in the ListBoxes
		'''
		
		# clearing any album art (set to default)
		self.art = PIL.Image.open(self.default)
		resized = self.art.resize((194, 194), PIL.Image.ANTIALIAS)
		self.artImage = PIL.ImageTk.PhotoImage(resized)
		self.canvas.itemconfigure(self.canvas_image, image=self.artImage)
			
		size = length = 0
		self.paused = False
		os.chdir(self.dname)

		# clearing the StringVars, if anything is there
		for c in range(len(self.cats)):
			self.cats[c].set("")

		# run the podcast scripts to do initial edits on the filenames and the metadata
		# if "Sex With Emily" in os.getcwd():
		# 	self.songCntStr.set("Editing recently downloaded \'Sex With Emily\' podcasts...")
		# 	master.config(cursor="watch")
		# 	master.update()
		# 	utils.fix_SexWithEmilyPodcasts.fixPodcasts()
		
		# if "Sword and Scale" in os.getcwd():
		# 	self.songCntStr.set("Editing recently downloaded \'Sword and Scale\' podcasts...")
		# 	master.config(cursor="watch")
		# 	master.update()
		# 	utils.fix_SwordAndScalePodcasts.fixPodcasts()
		
		self.songCntStr.set("Performing calculations...")
		master.config(cursor="watch")
		master.update()
		
		# resetting the correct directory path
		os.chdir(self.dname)

		# populate files in list, get size of all files in directory
		self.missingMetadata = []
		self.corruptMP3 = []
		self.not128kBitrate = []
		self.not64kBitrate = []
		self.all_music.clear()
		
		music_formats = ['mp3','m4a','wav']
		music = [fn for fn in os.listdir() if fn[-3:] in music_formats]
		
		print (f"Songs: {len(music)}")
		for fn in music:
			if "mp3" not in fn:
				self.songCntStr.set(f"Converting {fn} to MP3...")
				master.update()
				new_fn = f"{fn[:-4]}.mp3"
				ff = ffmpy.FFmpeg(inputs={fn: None}, outputs={f"new_{new_fn}": '-y -ac 2 -ar 44100 -ab 128k'})
				ff.run()
				
				self.songCntStr.set("Performing calculations...")
				master.update()
				os.replace(f"new_{new_fn}", fn)

			try:
				s = MP3(fn)
				self.all_music.append([fn, s['TIT2'][0], s['TPE1'][0], s['TALB'][0], s['TCON'][0], ('{0:02}:{1:02}:{2:02}').format(
					int(s.info.length % 86400) // 3600, int(s.info.length % 3600) // 60, int(s.info.length % 60)), int(s.info.bitrate / 1000)])

				size += os.stat(fn).st_size
				length += s.info.length

				if s['TCON'][0] != "Podcast" and int(s.info.bitrate / 1000) != 128:
					self.not128kBitrate.append(fn)
				if s['TCON'][0] == "Podcast" and int(s.info.bitrate / 1000) != 64:
					self.not64kBitrate.append(fn)

			except KeyError as e:
				self.missingMetadata.append(fn)
				self.all_music.append([fn, fn, " ", " ", " ", ('{0:02}:{1:02}:{2:02}').format(
					int(s.info.length % 86400) // 3600, int(s.info.length % 3600) // 60, int(s.info.length % 60)), int(s.info.bitrate / 1000)])
				size += os.stat(fn).st_size
				length += s.info.length
				self.songCntStr.set(f"ERROR!! {e}")
			except HeaderNotFoundError as e:
				if fn[-4:] == ".wma":
					showerror("WMA Conversion Attempt","Aborting conversion! Possible DRM protection.")
				else:
					self.recreateMP3File(fn)
				self.songCntStr.set(f"ERROR!! {e}")

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
		
		# updating total music files in directory/listbox
		self.songCntStr.set(f"Total Files: {len(self.all_music)}; Total Size: {convertedSize}; Total Time: {convertedTime}")
		master.config(cursor="")
		
	def update_progressbar(self):
		count = self.song_count.get()
		count += 1
		self.song_count.set(count)
		self.songCntStr.set(f"Performing calculations... {int((count / self.maximum) * 100)}%")
		self.progressBar.update()

		if self.progressBar["value"] == self.maximum:
			self.song_count.set(0)
			
	def getNewDirectory(self):
		directory = askdirectory()
		if directory == '' and os.name == "posix":
			self.mastermenu.entryconfig("Directory", state=DISABLED)
			self.mastermenu.entryconfig("Search", state=DISABLED)
			self.dname = '/home/alex/Music'
		elif directory == '' and os.name == "nt":
			self.mastermenu.entryconfig("Directory", state=DISABLED)
			self.mastermenu.entryconfig("Search", state=DISABLED)
			self.dname = u"C:\\Users\\Alex\\Music"
		else:
			self.dname = directory
			os.chdir(self.dname)
			self.path.set(self.dname)
			self.lbl.config(text=f"\nCurrent Directory: {self.path.get()}")
			self.getMusic()
			self.mastermenu.entryconfig("Directory", state=NORMAL)
			self.mastermenu.entryconfig("Search", state=NORMAL)
			if len(self.missingMetadata) > 0 or len(self.corruptMP3) > 0:
				self.mastermenu.entryconfig("Metadata", state=NORMAL)
				if len(self.missingMetadata) > 0:
					self.metaMenu.entryconfig(1, state=NORMAL)
				if len(self.corruptMP3) > 0:
					self.metaMenu.entryconfig(2, state=NORMAL)

	def searchMetadata(self):
		'''
		Search for missing metadata via the Internet - using MusicBrainz API
		'''
		metaWin = Toplevel()
		metaWin.title(f"Missing Metadata - \"{self.song['TIT2']}\" by {self.song['TPE1']}")
		pos = windows.centerWindow(metaWin,750,300)
		metaWin.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
	
	def showMissingMetadata(self):
		'''
		Display all files that have missing metadata information
		'''
		missingMetaWin = Toplevel(master=master)
		missingMetaWin.title("Songs with Missing Metadata")
		pos = windows.centerWindow(missingMetaWin,750,245)
		missingMetaWin.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
		missingMetaWin.resizable(False, False)
		missingMetaWin.config(cursor="arrow")
		missingText=Text(missingMetaWin, width=default.missingMDWidth, height=default.missingMDHeight)
		[missingText.insert(END, f"{f}\n") if len(self.missingMetadata) > 0 else next for f in self.missingMetadata]
		missingText.insert(END, "No files with missing metadata") if len(self.missingMetadata) == 0 else next
		missingText.insert(END, f"\nTotal: {len(self.missingMetadata)} files")
		missingText.config(state=DISABLED, cursor="arrow")
		missingText.focus()
		missingText.grid()

	def showCorruptFiles(self):
		'''
		Display all files that have corrupted headers
		'''
		corruptFilesWin = Toplevel(master=master)
		corruptFilesWin.title("Songs with Corrupted Headers")
		pos = windows.centerWindow(corruptFilesWin,750,245)
		corruptFilesWin.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
		corruptFilesWin.resizable(False, False)
		corruptFilesWin.config(cursor="arrow")
		corruptMP3=Text(corruptFilesWin, width=default.corruptMP3Width, height=default.corruptMP3Height)
		[corruptMP3.insert(END, f"{f}\n") if len(self.corruptMP3) > 0 else next for f in self.corruptMP3]
		corruptMP3.insert(END, "No files with corrupted headers") if len(self.corruptMP3) == 0 else next
		corruptMP3.insert(END, f"\nTotal: {len(self.corruptMP3)} files")
		corruptMP3.config(state=DISABLED, cursor="arrow")
		corruptMP3.focus()
		corruptMP3.grid()

	def search(self, args):
		'''searching for the criteria entered by user'''
		def tree(searchItems):
			# creating Multi-column Treeview widget to hold search results
			self.tree = ttk.Treeview(self.searchWin, columns=searchItems)
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
			vsb.grid(column=1, sticky=N+S+W, in_=self.tree)
			
		def find(event):
			'''finding and building the tree based on search criteria'''
			# args[0] = title, args[1] = searchItems, args[2] = criteria
			# clear() if args[2] != '' else next
			if len(self.tree.get_children()) > 0:
				for child in self.tree.get_children():
					self.tree.delete(child)

			self.searchWin.config(cursor="watch")
			self.searchWin.update()

			try:
				os.chdir(self.dname)
				f = str(criteria.get()).lower()
				results = mdict()
				
				if args[0] == "artist":		# album artist
					for m in self.all_music:
						try:
							s = MP3(f"{m[0]}")
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
							key = f"{v['TALB'][0]} ({v['TDRC'][0]})"
							if not self.tree.exists(key):
								self.tree.insert(k, END, key, text=key)
								self.tree.insert(key, END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album', 'BPM')
							else:
								self.tree.insert(key, END, None, text=(v['TRCK'][0]), values=(v['TIT2'][0], v['TPE1'][0], v['TBPM'][0])) #('Song', 'Album', 'BPM')
				elif args[0] == "album":	# album
					for m in self.all_music:
						try:
							s = MP3(f"{m[0]}")
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
								key = f"{k} ({v['TPE2'][0]} - {v['TDRC'][0]})"
								self.tree.insert("", END, k, text=key)
								self.tree.insert(k, END, None, text=v['TRCK'][0], values=(v['TIT2'][0], v['TCON'][0], v['TBPM'][0])) #('Song', 'Genre', 'BPM')
							else:
								self.tree.insert(k, END, None, text=v['TRCK'][0], values=(v['TIT2'][0], v['TCON'][0], v['TBPM'][0])) #('Song', 'Genre', 'BPM')
				elif args[0] == "genre":	# genre
					for m in self.all_music:
						try:
							s = MP3(f"{m[0]}")
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
							s = MP3(f"{m[0]}")
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
							s = MP3(f"{m[0]}")
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
			showinfo("No Results Found", f"There were no {title} results for \'{criteria.get()}\'")
			clear()

		def onError(criteria):
			showerror("Directory Error", f"Search failed: '{criteria.get()}'!\nNo directory chosen")
			clear()
		
		title = args[0]
		searchItems = args[1]
		criteria = StringVar()
		self.searchWin = Toplevel()
		self.searchWin.attributes("-topmost", False)
		pos = windows.centerWindow(self.searchWin,1050, 300)
		self.searchWin.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))
		self.searchWin.resizable(False, False)
		
		Label(self.searchWin).grid(columnspan=5)
		self.searchWin.title(f"{title.upper()} Search")
		Label(self.searchWin, text=f"Enter the {title.upper()} you want to search for:").grid(row=1, column=2, padx=35)
		
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
		'''
		Converting non-MP3 music files to MP3 with 128 kbps bitrate (default)
		'''
		def closeWin():
			self.convert.destroy()

		def convert(args):
			'''
			Convert the file to the desired filetype
			'''
			# self.convert, convertingTv, convert2type, option
			print (inspect.currentframe().f_code.co_name, args)
			args[0].config(cursor="watch")
			args[0].update()

			songsToConvert = args[1].selection()
			songsToConvert = [args[1].item(s)['values'][0] for s in songsToConvert]
			
			for songTitle in songsToConvert:
				try:
					# saving the song tags to a temp MP3 object
					songFile = f"{self.path.get()}/{songTitle}"
					song = MP3(songFile)
					temp = MP3()
			
					for t in song.keys():
						temp[t] = song[t]
				
					ff = ffmpy.FFmpeg(inputs={songFile: None}, outputs={f"new_{songTitle}": '-ab 128k'})
					ff.run()
					
					os.remove(f"{self.dname}\\{songTitle}")
					os.rename(f"{self.dname}\\new_{songTitle}", f"{self.dname}\\{songTitle}")

					args[0].config(cursor="")
					showinfo("File Type Conversion", "Conversion is completed!")
				except CouldntDecodeError as e:
					showerror("Conversion Failure",e)
			closeWin()
		
		convertMP3_Columns = ['Title', 'File Type']
		FILETYPES = [
		('.mp3', 'mp3'),
		('.m4a', 'm4a'),
		('.avi', 'avi'),
		('.wav', 'wav')]

		convert2type = StringVar()
		os.chdir(self.dname)
		self.convert = Toplevel()
		self.convert.title("Convert to MP3 Files")
		Label(self.convert, text="Non-MP3 Files to Convert - Default Bitrate = 128kbps").grid(row=1, columnspan=4)
		
		pos = windows.centerWindow(self.convert, default.convertMP3Width, 260)
		self.convert.geometry("%dx%d+%d+%d" % (pos[0], pos[1], pos[2], pos[3]))

		if option == 0:	
			convertFrame = Frame(self.convert)
			convertFrame.grid(row=3, padx=10, columnspan=6)
			convertingTv = ttk.Treeview(convertFrame, columns=convertMP3_Columns, height=10, selectmode=EXTENDED)
			convert_vsb = Scrollbar(convertFrame, orient="vertical", command=convertingTv.yview)
			convertingTv.configure(yscrollcommand=convert_vsb.set)

			[convertingTv.heading(col, text=col.title(), command=lambda c=col: self.sortby(convertMP3_Columns, c, 0)) for col in convertMP3_Columns]
			convertingTv.column('Title', width=300)
			convertingTv.column('File Type', anchor="center", width=50)
			convertingTv.grid(row=3, columnspan=4, sticky=E+W)
			convert_vsb.grid(row=3, column=6, sticky=N+S+W)
			
			for f in os.listdir():
				if f.endswith('mp3'):
					try:
						convertingTv.insert("", END, values=(f, f[-4]))
					except HeaderNotFoundError:
						# self.recreateMP3File(f)
						convertingTv.insert("", END, values=(f, f[-4]))
			convertBtn = Button(self.convert, text="Convert", width=8, command=functools.partial(convert, (self.convert, convertingTv, convert2type, option)))
			convertBtn.grid(row=4, column=2)
			
			# create radio buttons
			for text, convertTo in FILETYPES:
				radioBtn = Radiobutton(self.convert, text=text, indicatoron=0, width=10, padx=10, variable=convert2type, value=convertTo)
				radioBtn.grid(row=2, column=FILETYPES.index((text, convertTo)), padx=8)
		else:
			pos = windows.centerWindow(self.convert, 480, 125)
			self.convert.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
			Label(self.convert, text=self.value).grid(row=2, columnspan=4)
			# create radio buttons
			for text, convertTo in FILETYPES:
				radioBtn = Radiobutton(self.convert, text=text, indicatoron=0, width=10, variable=convert2type, value=convertTo)
				radioBtn.grid(row=3, column=FILETYPES.index((text, convertTo)))	
			# convertBtn = Button(self.convert, text="Convert", width=8, command=functools.partial(convert, (self.convert, convertingTv, convert2type, option)))
			# convertBtn.grid(row=4, column=4)
		convertMP3Thread = threading.Thread(target=convert, args=([self.convert, self.value, convert2type, option],))
		convertBtn = Button(self.convert, text="Convert", command=convertMP3Thread.start)
		
		convertBtn.grid(row=4, pady=8, column=1)
		close = Button(self.convert, text="Close", width=8, command=closeWin)
		close.grid(row=4, pady=8, column=2)
		
	def convertBitrate(self, option=0):
		'''
		Converting bitrate of MP3 files
		'''
		def closeWin():
			self.bitrate.destroy()
			os.chdir(self.path.get())
			self.getMusic()

		def convert(args):
			# self.bitrate, bitrate, choose (filename), option
			args[0].config(cursor="watch")
			args[0].update()

			if args[3] == 1:
				if os.name == "nt": songFile = args[2].get().split("\\")[-1]
				else: songFile = args[2].get().split("/")[-1]
				song = MP3(songFile)
				temp = MP3()
				for t in song.keys():
					temp[t] = song[t]
				
				# converting to new bitrate
				ff = ffmpy.FFmpeg(inputs={songFile: None}, outputs={f"new_{songFile}": f'-ab {args[1].get()}k'})
				ff.run()
				os.replace(f"{self.dname}\\new_{songFile}", f"{self.dname}\\{songFile}")

			else:
				# copying metadata to temp MP3 file
				songsToConvert = bitrateLb.selection()
				songsToConvert = [bitrateLb.item(s)['values'][0] for s in songsToConvert]
				for songName in songsToConvert:
					songFile = self.path.get()+"/"+songName
					status.set(f"Converting \"{songName[:-4]}\"...")
					song = MP3(songFile)
					temp = MP3()
					for t in song.keys():
						temp[t] = song[t]
					
					# converting the song to new bitrate and saving back in .mp3 file
					ff = ffmpy.FFmpeg(inputs={songName: None}, outputs={f"new_{songName}": f'-ab {args[1].get()}k'})
					ff.run()
					os.replace(f"{self.dname}\\new_{songName}", f"{self.dname}\\{songName}")
		
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
			pos = windows.centerWindow(self.bitrate, default.convertBitrateWidth, default.convertBitrateHeight)
			genre = "Song" if song['TCON'][0] != "Podcast" else "Podcast"
			self.bitrate.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
			Label(self.bitrate, text=f"{genre}: {song['TIT2'][0]}; Bitrate: {str('{0:00.0f}'.format(song.info.bitrate/1000))}", font="Times 10", justify=CENTER).grid(row=1, columnspan=6, sticky=E+W)
			if os.name == "nt": choose.set(os.getcwd()+"\\"+self.value['text'])
			else: choose.set(f"{os.getcwd()}/{self.value['text']}")
		else:
			pos = windows.centerWindow(self.bitrate, default.convertWidthWin, default.convertHeightWin)
			self.bitrate.geometry(f"{pos[0]}x{pos[1]}+{pos[2]}+{pos[3]}")
			bitrateLbl = Label(self.bitrate, text="Select a bitrate to convert files to:")
			bitrateLbl.grid(column=1, columnspan=4, row=1, sticky=E+W)
				
			# show list of songs in Listbox
			bitrateFrame = Frame(self.bitrate)
			bitrateFrame.grid(row=3, padx=10, columnspan=6)
			bitrateLb = ttk.Treeview(bitrateFrame, columns=bitrateLb_columns, height=8, show="headings", selectmode=EXTENDED)
			vsb = ttk.Scrollbar(bitrateFrame, orient="vertical", command=bitrateLb.yview)
			bitrateLb.configure(yscrollcommand=vsb.set)
			
			# building the tree (headers and items)
			[bitrateLb.heading(col, text=col.title(), command=lambda c=col: self.sortby(bitrateLb, c, 0)) for col in bitrateLb_columns]
			bitrateLb.column('Title', width=default.bitrateTitleColWidth)
			bitrateLb.column('Bitrate', anchor="center", width=default.bitrateBitrateColWidth)
			bitrateLb.grid(row=3, sticky=N+S)
			vsb.grid(row=3, column=6, sticky=N+S+W)
		
			genre128k = []
			genre64k = []
			for f in self.not128kBitrate:
				genre128k.append(MP3(f)['TCON'].text[0])
			for f in self.not64kBitrate:
				genre64k.append(MP3(f)['TCON'].text[0])

			# if set(self.not128kBitrate) <= set(os.listdir()) and all(genre != "Podcast" for genre in genre128k):
			# 	for f in self.not128kBitrate:
			# 		try:
			# 			bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))
			# 		except HeaderNotFoundError:
			# 			# self.recreateMP3File(f)
			# 			# bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))
			# 			continue
			if set(self.not64kBitrate) <= set(os.listdir()) and all(genre == "Podcast" for genre in genre64k):
				for f in self.not64kBitrate:
					try:
						bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))
					except HeaderNotFoundError:
						# self.recreateMP3File(f)
						# bitrateLb.insert("", END, values=(f, round(MP3(f).info.bitrate/1000),2))
						continue
		# create radio buttons
		for text, rate in BITRATES:
			radioBtn = Radiobutton(self.bitrate, text=text, variable=bitrate, value=rate)
			radioBtn.grid(row=2, column=BITRATES.index((text, rate)))

		conversionStatus = Label(self.bitrate, textvariable=status, font="Times 9").grid(row=5, columnspan=6, sticky=W)
		# convertBtn = Button(self.bitrate, text="Convert", command=functools.partial(convert, (self.bitrate, bitrate, choose, option)))
		convertThread = threading.Thread(target=convert, args=([self.bitrate, bitrate, choose, option],))
		convertBtn = Button(self.bitrate, text="Convert", command=convertThread.start)
		convertBtn.grid(column=0, columnspan=3, row=4, pady=5, padx=5, sticky=E+W)
		cancelBtn = Button(self.bitrate, text="Cancel", command=closeWin)
		cancelBtn.grid(column=3, columnspan=3, row=4, pady=5, padx=5, sticky=E+W)

	def launchBpmAnalyzer(self):
		'''
		Launch MixMeister BPM Analyzer
		'''
		launchBpm = ["C:\\Program Files (x86)\\MixMeister BPM Analyzer\\BpmAnalyzer.exe"]
		subprocess.run(launchBpm)
		self.getMusic()

	def analyzeGain(self):
		'''
		Lanuch MP3Gain
		'''
		launchMp3Gain = ["C:\\Program Files (x86)\\MP3Gain\\MP3GainGUI.exe"]
		subprocess.run(launchMp3Gain)
		self.getMusic()

if __name__ == '__main__':
	import tkinter
	import tkinter.ttk as ttk

	master = Tk()
	EditMetadata(master)
	master.title("MP3 Music Maintenance")

	# add program icon
	progDir = sys.path[0]
	master.iconphoto(True, PhotoImage(file=os.path.join(progDir, 'media\\icons\\music-note-icon.png')))
	master.mainloop()
