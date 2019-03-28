from mutagen.id3 import ID3, TRCK, TCON, TPOS, TALB, TIT2, TPE1, TPE2, TDRC, APIC, USLT, TBPM, ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from bs4 import BeautifulSoup
import tkinter as tk
import tkinter.ttk
import requests
import requests_cache
from tkinter.messagebox import *
import functools

import windows.customWindowSize as windowSize
import utils.defaults as defaults

def lyrics(self):
	'''
	Allows user to view and edit description and/or lyrics of music file
	'''
	URLS = ["http://www.metrolyrics.com/{0}-lyrics-{1}.html"]
	USLT_FOUND = False

	for tags in self.song.keys():
		if "USLT" in tags:
			USLT_FOUND = True
			lyrics = str(self.song[tags])

	if self.song['TCON'][0] != "Podcast":
		search_artist = self.song['TPE2'][0].replace(" ","-").lower()
		search_song_title = self.song['TIT2'][0].replace(" ","-").lower()

	artist = self.song['TPE2'][0] if 'TPE2' in self.song.keys() else "No Artist"
	
	if USLT_FOUND is False and self.song['TCON'][0] is not "Podcast":
		for url in URLS:
			completeUrl = url.format(search_song_title, search_artist)

			try:
				requests_cache.install_cache('lyrics_cache')
				soup = BeautifulSoup(requests.get(completeUrl).content, "lxml")
				lyrics = str()
				verses = soup.find_all("p", {"class": "verse"})
				for verse in verses:
					lyrics += verse.text+"\n\n"
				if lyrics is not "": break
			except requests.exceptions.ConnectionError as e:
				showerror("Connection Error", "%s" % e)
			else:
				lyrics = ""
	
	self.saveLDWin = tk.Toplevel()
	# change the heading depending on the genre type
	song_title = self.song['TIT2'][0] if 'TIT2' in self.song.keys() else "No Song Title"

	self.saveLDWin.title("'{0}' {1}".format(song_title, "Description")) if self.song['TCON'][0] is 'Podcast' \
		else self.saveLDWin.title("'{0}' {1}".format(song_title, "Lyrics"))
	pos = windowSize.centerWindow(self.saveLDWin, defaults.lyricsWinWidth, defaults.lyricsWinHeight)
	self.saveLDWin.geometry('%dx%d+%d+%d' % (pos[0], pos[1], pos[2], pos[3]))

	album_name = self.song['TALB'][0] if 'TALB' in self.song.keys() else "No Album"
	track = self.song['TRCK'][0] if 'TRCK' in self.song.keys() else "No Track"
	disc_number = self.song['TPOS'][0] if 'TPOS' in self.song.keys() else "No Disc Number"

	tk.Label(self.saveLDWin, text=f"Title: {song_title}", font="Arial 10 italic", justify=tk.CENTER).grid(row=1, columnspan=3, sticky=tk.E+tk.W)
	tk.Label(self.saveLDWin, text=f"Album: {album_name}", font="Arial 10 italic", justify=tk.CENTER).grid(row=2, columnspan=3, sticky=tk.E+tk.W)
	tk.Label(self.saveLDWin, text=f"Track: {track}", font="Arial 10 italic", justify=tk.CENTER).grid(row=3, columnspan=3, sticky=tk.E+tk.W)
	tk.Label(self.saveLDWin, text=f"Disc: {disc_number}", font="Arial 10 italic", justify=tk.CENTER).grid(row=4, columnspan=3, sticky=tk.E+tk.W)

	textbox = tk.Text(self.saveLDWin, font='Times 10', width=65, wrap=tk.WORD)
	textbox.grid(row=6, columnspan=3, pady=10)
	textbox.insert("end", lyrics.rstrip())
	textbox.config(state=tk.DISABLED, cursor="arrow")
	textbox.focus()

	save = tk.Button(self.saveLDWin, command=functools.partial(saveFile, (self, textbox)))
	state = tk.BooleanVar()
	modes = tk.StringVar()
	mode = tk.Checkbutton(self.saveLDWin, indicatoron=False, textvariable=modes, variable=state, onvalue=True, offvalue=False, width=15, height=2, \
		command=functools.partial(switchModes, (modes, state, textbox, save)))
	mode.grid(row=7, column=0, padx=10)
	
	if textbox.get(0.0, tk.END) is '\n':
		modes.set("Edit Mode")
		textbox.config(state=tk.NORMAL, cursor="xterm")
		state.set(True)
		save.config(state=tk.NORMAL)
	else:
		modes.set("View Mode")
		textbox.config(state=tk.DISABLED, cursor="arrow")
		state.set(False)
		save.config(state=tk.DISABLED)
	save.config(text="Save Description", width=15) if self.song['TCON'][0] == "Podcast" else save.config(text="Save Lyrics", width=15)
	save.grid(row=7, column=1, padx=10)
	close = tk.Button(self.saveLDWin, text="Close", width=15, command=functools.partial(closeWindow, self))
	close.grid(row=7, column=2, padx=10)

def switchModes(args):
	modes, state, textbox, save = args

	modes.set("Edit Mode") if state.get() == True else modes.set("View Mode")
	textbox.config(state='normal', cursor="xterm") if state.get() == True else textbox.config(state='disabled', cursor="arrow")
	save.config(state='normal') if state.get() == True else save.config(state="disabled")

def saveFile(args):
	self = args[0]
	textbox = args[1]

	# remove old USLT tag(self) from MP3 file and add new USLT tag to file
	listOfKeys = list(self.song.keys())
	for key in listOfKeys:
		if 'USLT' in key:
			self.song.pop(key)
	
	self.song['USLT'] = USLT(encoding=3, lang=u'eng', text=textbox.get(1.0, 'end'))
	self.song.save(self.song_path.get(), v2_version=3)
	showinfo("Song Description","Description has been saved!") if self.song['TCON'] == "Podcast" else next
	closeWindow(self)

def closeWindow(self):
	self.saveLDWin.destroy()