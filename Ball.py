from __future__ import print_function

import math
import copy
import time
from common import *
from pprint import *

# todo: make all of the y calculation with physics format

class Ball:

	def __init__(self, parent, colour, radius):
		self.parent = parent

		self.colour = colour
		self.radius = radius

		self.shadow_colour = blend([0,0,0], self.parent.bg_colour, 0.80)
		self.shadow_height = self.radius #25 # height of the shadow in pixels
		self.shadow_pix_from_bottom = 40 #20 # pixels away from bottom of screen

		

		self.g = 9.8/10 # fraction of earth gravity
		self.mass = 1. # in kg
		self.velocity = (0., 0)#9.8/4)

		#self.goalCenter = (0.5, 0.5)
		self.center = (0.5, 0.75)
		self.maxYFrac = 1. # the defines how far down the floor is -- calculated in resize()

		# keep track of the path of the ball (only use fixed length history)
		self.hist_len = 600
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

		#self.maxYFrac = 1.-1.*(self.shadow_pix_from_bottom+self.shadow_height*0.5)/window_height

		self.maxYFrac = 1. - 1.*(self.shadow_pix_from_bottom+1.2*self.radius)/window_height

		self.draw()

	def getShadowPoints(self):

		leftX = self.center[0]*self.parent.window_width-self.radius
		rightX = self.center[0]*self.parent.window_width+self.radius

		return (leftX, self.parent.window_height-self.shadow_pix_from_bottom-self.shadow_height,
				rightX, self.parent.window_height-self.shadow_pix_from_bottom)

	def cursor_enter(self, event=[]):

		self.applyForce((random.random()-0.5, 0.5), 1.)
		self.parent.playing_game = not self.parent.playing_game

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
				self.velocity = (self.velocity[0]*0.75, -self.velocity[1]*0.75)#self.velocity[1])

			hitFloor = self.center[1] >= self.maxYFrac
			#print("hit floor")

			hitWall = self.center[0] <= 0 or self.center[0] >= 1

			if hitWall:
				self.velocity = (-self.velocity[0]*0.75, self.velocity[1]*0.75)

			if hitFloor:
				self.velocity = (self.velocity[0]*0.75, -self.velocity[1]*0.75)
				if abs(self.velocity[1]) <= 0.1:
					self.velocity = (self.velocity[0], 0.)
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

		

		# force: force vector (newtons in each direction) (kg*m/s^2)
		# duration: duration force is applied (seconds)
		# F = m*a
		# a = F/m

		#print(force, duration, time.time() - self.last_hit_time)

		self.last_hit_time = time.time()

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
		self.velocity = (0.0, 0)

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
			points = [[points[0][0]-0.01, points[0][1]-0.01], [points[0][0]+0.01, points[0][1]+0.01]]
		

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

		#pprint(newPoints)


		# now get average pointwise difference
		assert(len(valid_hist_pts) == len(newPoints))

		# want to normalize arc length of each sequence
		'''
		hist_dist_sum = 0.
		for i in range(len(valid_hist_pts)-1):
			p1 = valid_hist_pts[i]
			p2 = valid_hist_pts[i+1]
			hist_dist_sum += dist(p1, p2)
		valid_hist_pts = [[1.*v[0]/hist_dist_sum, 1.*v[1]/hist_dist_sum] for v in valid_hist_pts]

		newPoints_dist_sum = 0.
		for i in range(len(newPoints)-1):
			p1 = newPoints[i]
			p2 = newPoints[i+1]
			newPoints_dist_sum += dist(p1, p2)
		#if newPoints_dist_sum == 0.:
		#	return float('inf')
		newPoints = [[1.*v[0]/newPoints_dist_sum, 1.*v[1]/newPoints_dist_sum] for v in newPoints]
		'''
		# calculate arc length of each sequence
		hist_dist = 0.
		for i in range(len(valid_hist_pts)-1):
			p1 = valid_hist_pts[i]
			p2 = valid_hist_pts[i+1]
			hist_dist += dist(p1, p2)

		newpts_dist = 0.
		for i in range(len(newPoints)-1):
			p1 = newPoints[i]
			p2 = newPoints[i+1]
			newpts_dist += dist(p1, p2)


		# now want to points on path that are spaced equally along arc length
		NPTS = 30
		distSum = 0.
		valid_hist_pts_eql = [valid_hist_pts[0]]
		for i in range(1, len(valid_hist_pts)):
			p1 = valid_hist_pts[i-1]
			p2 = valid_hist_pts[i]
			distSum += dist(p1, p2) 
			if distSum >= hist_dist/NPTS:
				distSum = 0.
				valid_hist_pts_eql.append(p2)
				#print(len(new_points))

		distSum = 0.
		newPoints_eql = [newPoints[0]]
		for i in range(1, len(newPoints)):
			p1 = newPoints[i-1]
			p2 = newPoints[i]
			distSum += dist(p1, p2) 
			if distSum >= newpts_dist/NPTS:
				distSum = 0.
				newPoints_eql.append(p2)

		minDist = min(len(valid_hist_pts_eql), len(newPoints_eql))
		valid_hist_pts_eql = valid_hist_pts_eql[:minDist]
		newPoints_eql = newPoints_eql[:minDist]

		#pprint(valid_hist_pts_eql)
		#pprint(newPoints_eql)


		'''

		# instead of using the raw locations, use the derivatives
		valid_hist_pts_d = []
		for i in range(len(valid_hist_pts)-1):
			p1 = valid_hist_pts[i]
			p2 = valid_hist_pts[i+1]
			dx = p2[0]-p1[0]
			dy = p2[1]-p1[1]
			valid_hist_pts_d.append([dx, dy])

		newPoints_d = []
		for i in range(len(newPoints)-1):
			p1 = newPoints[i]
			p2 = newPoints[i+1]
			dx = p2[0]-p1[0]
			dy = p2[1]-p1[1]
			newPoints_d.append([dx, dy])

		#pprint(valid_hist_pts_d)
		#pprint(newPoints_d)

		'''

		diffSum = 0.
		for a, b in zip(valid_hist_pts_eql, newPoints_eql):
			diff = abs(a[0]-b[0])**2 + abs(a[1] - b[1])**2
			diffSum += diff

		return 1.*diffSum#/n
