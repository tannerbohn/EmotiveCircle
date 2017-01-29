from __future__ import print_function

import math
import copy
import time
from common import *

class Circle:

	def __init__(self, parent, colour, radius, width, has_shadow):

		self.parent = parent

		self.colour = colour
		self.radius = radius
		self.width = width
		self.has_shadow = has_shadow

		self.shadow_colour = blend([0,0,0], self.parent.bg_colour, 0.80)
		self.shadow_height = 25 # height of the shadow in pixels
		self.shadow_pix_from_bottom = 15 # pixels away from bottom of screen

		self.minPixFromBottom = 50

		self.width_mult = 1.0
		self.radius_mult = 1.0

		self.nb_circle_points = 64

		self.goalNoise = [1. for _ in range(self.nb_circle_points)]
		self.circle_offsets = [1. for _ in range(self.nb_circle_points)]

		self.topLoc = 0.
		self.botLoc = 0.
		self.leftLoc = 0.
		self.rightLoc = 0.

		self.center_pix = (0,0)

		self.prevPoints = None

		self.shadow_index = None
		self.index = None

	def draw(self, init=False):

		if init:

			# perform this call so that the shadow has necessary info to draw
			self.getPoints()

			if self.has_shadow:
				self.shadow_index = self.parent.canvas.create_oval(*self.getShadowPoints(), fill=toHex(self.shadow_colour), width=0)


			self.index = self.parent.canvas.create_polygon(*self.getPoints(), fill="", outline=toHex(self.colour), width=self.getWidth(), smooth=1)


		self.parent.canvas.coords(self.index, *self.getPoints(smooth=True))
		self.parent.canvas.itemconfig(self.index, width = self.getWidth())

		if self.has_shadow:
			self.parent.canvas.coords(self.shadow_index, *self.getShadowPoints())


		return

	def resize(self, event=[]):

		self.parent.canvas.coords(self.index, *self.getPoints())

		if self.has_shadow:
			self.parent.canvas.coords(self.shadow_index, *self.getShadowPoints())

	def getShadowPoints(self):

		return (self.leftLoc[0], self.parent.window_height-self.shadow_pix_from_bottom-self.shadow_height,
				self.rightLoc[0], self.parent.window_height-self.shadow_pix_from_bottom)


	def getWidth(self):

		return self.width*self.width_mult

	def getRadius(self):

		return self.radius*self.radius_mult

	def getPoints(self, smooth=False):

		center = self.parent.getCenter()

		cx = center[0]*self.parent.window_width
		cy = center[1]*self.parent.window_height

		self.center_pix = (cx, cy)
		
		# how many parts to split the circle into
		n = self.nb_circle_points

		pts = []

		theta = 0.

		minX = float('inf')
		maxX = -float('inf')
		minY = float('inf')
		maxY = -float('inf')
		for i in range(n):
			x = math.cos(theta) * self.getRadius()*self.circle_offsets[i] + cx
			y = math.sin(theta) * self.getRadius()*self.circle_offsets[i] + cy

			pts.extend([x, y])

			theta += 2*math.pi/n

			if y >= maxY: maxY = y
			if y <= minY: minY = y
			if x >= maxX: maxX = x
			if x <= minX: minX = x


		# get the lowest point, and then move entire thing up if necessary


		if maxY > self.parent.window_height - self.minPixFromBottom:
			diff = maxY - (self.parent.window_height - self.minPixFromBottom)
			for i in range(1, len(pts), 2):
				pts[i] = pts[i] - diff



		if self.prevPoints == None:
			self.prevPoints = copy.deepcopy(pts)

		if smooth:
			
		
			pts = blend(self.prevPoints, pts, 0.25)#self.parent.dt)

			self.prevPoints = copy.deepcopy(pts)


		self.topLoc = (minX*0.5+maxX*0.5, minY)
		self.botLoc = (minX*0.5+maxX*0.5, maxY)
		self.leftLoc = (minX, minY*0.5+maxY*0.5)
		self.rightLoc = (maxX, minY*0.5+maxY*0.5)

		return pts

	def getClosestSide(self, loc):

		topDist = dist(loc, self.topLoc)
		rightDist = dist(loc, self.rightLoc)
		leftDist = dist(loc, self.leftLoc)
		botDist = dist(loc, self.botLoc)
		midDist = dist(loc, self.center_pix)

		dists = [topDist, rightDist, leftDist, botDist, midDist]

		return ["top", "right", "left", "bottom", "middle"][dists.index(min(dists))]

	def isInside(self, loc):

		withinRad = dist(loc, self.center_pix) < self.getRadius()

		return withinRad

