from __future__ import print_function

import math
import copy
import time
from common import *

# todo: make all of the y calculation with physics format

class Ball:

	def __init__(self, parent, colour, radius):
		self.parent = parent

		self.colour = colour
		self.radius = radius

		self.shadow_colour = blend([0,0,0], self.parent.bg_colour, 0.80)
		self.shadow_height = 15 #25 # height of the shadow in pixels
		self.shadow_pix_from_bottom = 20 # pixels away from bottom of screen

		self.center = (0.5, 0.75)

		self.g = 9.8/10 # fraction of earth gravity
		self.mass = 1. # in kg
		self.velocity = (0., 0)#9.8/4)

		#self.goalCenter = (0.5, 0.5)

		self.maxYFrac = 1. # the defines how far down the floor is

		# keep track of the path of the ball (only use fixed length history)
		self.hist_len = 60
		self.path = []

		self.index = None

		self.shadow_index = None

		self.last_hit_time = 0.

		#self.draw(init=True)

		return

	def draw(self, init=False):

		if init:

			self.shadow_index = self.parent.canvas.create_oval(*self.getShadowPoints(), fill=toHex(self.shadow_colour), width=0)

			self.index = self.parent.canvas.create_oval(*self.getPoints(), fill=toHex(self.colour), width=0)

			self.parent.canvas.tag_bind(self.index, '<Enter>', self.cursor_enter)

			self.parent.root.update()

			self.resize()

		self.parent.canvas.coords(self.index, *self.getPoints(smooth=True))

		self.parent.canvas.coords(self.shadow_index, *self.getShadowPoints())

		self.path.append(dict({'x':self.center[0], 'y':self.center[1], 'time':time.time()}))
		self.path = self.path[-self.hist_len:]


	def resize(self, event=[]):
		
		#window_width=self.parent.root.winfo_width()
		window_height=self.parent.root.winfo_height()

		self.maxYFrac = 1.-30./window_height

		self.draw()

	def getShadowPoints(self):

		leftX = self.center[0]*self.parent.window_width-self.radius
		rightX = self.center[0]*self.parent.window_width+self.radius

		return (leftX, self.parent.window_height-self.shadow_pix_from_bottom-self.shadow_height,
				rightX, self.parent.window_height-self.shadow_pix_from_bottom)

	def cursor_enter(self, event=[]):

		self.applyForce((random.random()-0.5, 0.5), 1.)

	def getPoints(self, smooth=False):

		window_width=self.parent.root.winfo_width()
		window_height=self.parent.root.winfo_height()

		r = self.radius


		if smooth:

			# apply physics
			# note: positive velocity is moving down
			self.center = (self.center[0] + self.velocity[0]*self.parent.dt, self.center[1] - self.velocity[1]*self.parent.dt)

			# see if it has not hit a floor yet:
			self.center = (bound(0, 1, self.center[0]),
							bound(0, self.maxYFrac, self.center[1]))


			hitCeiling = self.center[1] <= 0
			if hitCeiling:
				self.velocity = (self.velocity[0], 0)#self.velocity[1])

			hitFloor = self.center[1] >= self.maxYFrac
			#print("hit floor")

			hitWall = self.center[0] <= 0 or self.center[0] >= 1

			if hitWall:
				self.velocity = (-self.velocity[0], self.velocity[1])

			if hitFloor:
				self.velocity = (0, 0)
			else:
				self.velocity = (self.velocity[0], self.velocity[1] - self.g*self.parent.dt)
			

		#x, y = self.center_pix
		x, y = self.center[0]*window_width, self.center[1]*window_height

		#print(x, y)

		pts = [x-r, y-r, x+r, y+r]

		return pts

	def getLocation(self):

		# we want 0 to be the bottom of the screen, and 1 to be the top
		return (self.center[0], 1.-self.center[1])

	def movePix(self, pix):

		# move the ball by this many pixels

		window_width=self.parent.root.winfo_width()
		window_height=self.parent.root.winfo_height()


		self.goalCenter = (bound(0, 1, self.goalCenter[0]+1.*pix[0]/window_width),
							bound(0, self.maxYFrac, self.goalCenter[1]+1.*pix[1]/window_height))

		return

	def moveFrac(self, frac):

		self.goalCenter = (bound(0, 1, self.goalCenter[0]+frac[0]),
							bound(0, self.maxYFrac, self.goalCenter[1]+frac[1]))

		return

	def applyForce(self, force, duration):

		self.last_hit_time = time.time()

		# force: force vector (newtons in each direction) (kg*m/s^2)
		# duration: duration force is applied (seconds)
		# F = m*a
		# a = F/m

		a_x = force[0]/self.mass
		a_y = force[1]/self.mass

		#a_y -= 9.8 # for gravity

		self.velocity = (self.velocity[0] + a_x *duration, self.velocity[1] + a_y *duration)

	def pullToLocation(self, loc):

		self.last_hit_time = time.time()

		self.center = loc
		#self.velocity = (loc[0]-self.center[0], loc[1]-self.center[1])
		self.velocity = (0, 0)

		return

	def reset_position(self):

		self.center = (0.5, 1)

	def getPathAverage(self, startTime):

		ptSum = [0., 0.]
		n = 0
		for p in self.path:
			if p['time'] > startTime:
				ptSum = [ptSum[0]+p['x'], ptSum[1]+p['y']]
				n += 1

		ptAvg = [1.*ptSum[0]/n, 1.*ptSum[1]/n]

		return ptAvg

	def getPathAverageMinDist(self, startTime, points):

		# for each recent point in path, see how close it is to a reference point
		# note: using physics format in the calculations for y


		if len(points) == 1:
			points = [points[0], points[0]]
		

		valid_hist_pts = []

		n = 0
		for p in self.path:
			if p['time'] > startTime:
				n += 1
				point = [p['x'], 1.-p['y']]
				#minDistSum += minDistToPoints(point, points)
				valid_hist_pts.append(point)

		newPoints = []

		nrp = len(points) # number of ref points
		centers = [1.*i/(nrp-1.) for i in range(nrp)]

		for i in range(n):
			f = 1.*i/(n-1.)
			newPt = interpolateNVec(points, centers, f)
			newPoints.append(newPt)


		# now get average pointwise difference
		assert(len(valid_hist_pts) == len(newPoints))

		diffSum = 0.
		for a, b in zip(valid_hist_pts, newPoints):
			diff = abs(a[0]-b[0]) + abs(a[1] - b[1])
			diffSum += diff

		return 1.*diffSum/n
