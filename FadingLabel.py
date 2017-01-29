from __future__ import print_function

import math
import copy
import time
from common import *

class FadingLabel:

	def __init__(self, parent):#, colour, radius):
		self.parent = parent

		self.text = ""

		self.colour = blend([1, 1, 1], self.parent.bg_colour, 0.25)
		self.lifetime = 0.5 # how long to appear for

		self.index = None

		self.last_type_time = 0
		#self.loc = (0, 0)

		return

	def draw(self, init=False):

		if init:

			self.index = self.parent.canvas.create_text(0, 0, text=self.text, fill=toHex(self.colour), font=("Courier", 25))
			self.parent.canvas.itemconfig(self.index, width=200)

			self.parent.root.update()

			self.resize()



		if time.time() - self.last_type_time >= 3 and len(self.text)>= 1:
			self.text = self.text[1:]


		self.parent.canvas.itemconfig(self.index, text=self.text, width = 2.*self.parent.window_width/3)

		#if self.radius <= 0:
		#	self.loc = (-10, -10)
		#	return

		#self.radius -= self.parent.dt * (1.*self.max_radius/self.lifetime)

		#print(self.radius, self.loc)

	def resize(self, event=[]):

		self.parent.canvas.coords(self.index, self.parent.window_width/2, 25)

	def type(self, keysym):

		valid = False

		if keysym == 'space':
			self.text += ' '
			valid = True
		elif keysym == 'comma':
			self.text += ','
			valid = True
		elif keysym == 'period':
			self.text += '.'
			valid = True
		elif keysym == 'question':
			self.text += '?'
			valid = True
		elif keysym == 'apostrophe':
			self.text += '\''
			valid = True
		elif keysym == 'quotedbl':
			self.text += '"'
			valid = True
		elif keysym == 'minus':
			self.text += '-'
			valid = True
		elif keysym == 'exclam':
			self.text += '!'
			valid = True

		elif keysym in "1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPLKJHGFDSAZXCVBNM":
			self.text += keysym
			valid = True
		elif keysym == 'BackSpace':
			self.text = self.text[:-1]
			valid = True

		if valid:
			self.last_type_time = time.time()
	#def resize(self, event=[]):

	#	self.draw()
