from __future__ import print_function

import math
import copy
import time
from common import *

class ClickBall:

	def __init__(self, parent):#, colour, radius):
		self.parent = parent

		self.opacity = 0.5
		self.default_colour = [1, 1, 1]
		self.current_colour = self.default_colour
		#self.colour = blend(self.default_colour, self.parent.bg_colour, self.opacity)
		self.max_radius = 20
		self.radius = 0
		self.lifetime = 0.5 # how long to appear for

		self.index = None
		self.loc = (0, 0)

		return

	def draw(self, init=False):

		if init:

			self.index = self.parent.canvas.create_oval(*self.getPoints(), fill=toHex(blend(self.current_colour, self.parent.bg_colour, self.opacity)), width=0)

			self.parent.root.update()

			self.resize()

		self.parent.canvas.coords(self.index, *self.getPoints())
		self.parent.canvas.itemconfig(self.index, fill=toHex(blend(self.current_colour, self.parent.bg_colour, self.opacity)))

		# lifetime = self.max_radius*c
		# c = 

		if self.radius <= 0:
			self.loc = (-10, -10)
			self.current_colour = self.default_colour
			return

		self.radius -= self.parent.dt * (1.*self.max_radius/self.lifetime)

		#print(self.radius, self.loc)


	def resize(self, event=[]):

		self.draw()

	def clickAt(self, loc, colour = None):

		if colour != None:
			self.current_colour = colour
			#print("colour:", self.current_colour)

		self.radius = self.max_radius

		self.loc = loc # in pixels

	def rightClickAt(self, loc):

		self.radius = self.max_radius/2

		self.loc = loc # in pixels

	def getPoints(self):

		r = self.radius

		x, y = self.loc

		pts = [x-r, y-r, x+r, y+r]

		return pts
