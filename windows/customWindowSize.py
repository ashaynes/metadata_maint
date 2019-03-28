import math

def centerWindow(window, w, h):
	sW = math.floor(window.winfo_screenwidth())
	sH = math.floor(window.winfo_screenheight())
	x = math.floor((sW / 2) - (w / 2))
	y = math.floor((sH / 2) - (h / 2))
	return [w, h, x, y]