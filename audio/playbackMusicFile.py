import pygame as pg
import mutagen.id3
import tkinter.ttk as ttk
import tkinter

global paused

def playSong(self):
	# setting events
	# END_MUSIC_EVENT = pg.USEREVENT + 0
	# pg.mixer.music.set_endevent(END_MUSIC_EVENT)
	paused = False

	'''play current song selected in Listbox'''
	self.current_song_playing.set(self.song['TIT2'][0])
	# set Pause and Stop buttons to normal state
	self.play.config(state=tkinter.DISABLED)
	self.pause.config(state=tkinter.NORMAL)
	self.stop.config(state=tkinter.NORMAL)
	
	self.lyricsText.config(state=tkinter.NORMAL, cursor="arrow")
	
	# display lyrics from USLT tag else display default message
	lyrics = " -- No lyrics/description to display -- "
	for tags in self.song.keys():
		if "USLT" in tags:
			lyrics = self.song[tags]

	self.lyricsText.delete("0.0", tkinter.END)
	self.lyricsText.insert("0.0", lyrics)
	self.lyricsText.config(state=tkinter.DISABLED, cursor="arrow")
	self.lyricsText.update()
	
	# load music file, else return error
	song_header = self.song.pprint().split("\n")[0].split(", ")
	freq = "44100 Hz"
	for x in range(len(song_header)):
		if "Hz" in song_header[x]:
			freq = song_header[x]
			break
	
	pg.mixer.pre_init(int(freq[:-3]), -16, 2, 1024)
	pg.mixer.init()
	pg.mixer.music.set_volume(0.8)
	try:
		pg.mixer.music.load(self.song_path.get())
		pg.mixer.music.play(1)
		if pg.mixer.music.get_busy() is True:
			print (f'{self.song_path.get()} is playing right now')
	except:
		pass

	# reset pause status in player
	if paused is True:
		pauseSong(self)
	
	if pg.mixer.music.get_busy() is False:
		pg.mixer.music.stop()
		pg.mixer.music.load("")
		print (f"{self.song_path.get()} has stopped playing")
		self.lyricsText.config(state=tkinter.NORMAL, cursor="arrow")	
	
def pauseSong(self):
	'''pauses playback of song'''
	if pg.mixer.music.get_busy() and self.paused is False:
		pg.mixer.music.pause()
		self.pause_unpause.set("Unpause")
		self.paused = True
	else:
		pg.mixer.music.unpause()
		self.pause_unpause.set("Pause")
		self.paused = False

def stopSong(self):
	'''stops the song that is playing'''
	if pg.mixer.music.get_busy():
		pg.mixer.music.stop()
		self.play.config(state=tkinter.NORMAL)
		self.stop.config(state=tkinter.DISABLED)
