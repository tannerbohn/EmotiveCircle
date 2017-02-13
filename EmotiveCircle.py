from __future__ import print_function


from PIL import ImageTk
import PIL.Image

from pygame import mixer

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

from Tkinter import *
import random
import math
import time
import copy
import json
import sys
import numpy as np


from Learner import *
from Vitals import *
from Circle import *
from Ball import *
from ClickBall import *
from FadingLabel import *
from common import *

# todo: make all of the y calculation with physics format

class EmotiveCircle(Frame):

	def __init__(self, directory):


		self.root = Tk()
		self.root.config(cursor="dot")

		Frame.__init__(self, None, [])

		self.dir = directory
		self.window_width = 800
		self.window_height = 600

		#self.bg_colour = [255./255, 76./255, 30./255.]
		#self.fg_colour = [1, 1, 1]
		
		#self.bg_colour = [v/255. for v in (246,239,201)]
		#self.c1_colour = [v/255. for v in (68,59,65)]
		#self.c2_colour = [v/255. for v in (137,90,108)]
		#self.c2_transparency = 0.8
		#self.ball_colour = [v/255. for v in (137,90,108)]

		self.bg_colour = [v/255. for v in (255, 76, 30)]
		self.c1_colour = [v/255. for v in (255, 255, 255)]
		self.c2_colour = [v/255. for v in (255, 255, 255)]
		self.c2_transparency = 0.8
		self.ball_colour = [v/255. for v in (255, 255, 255)]

		self.label_colour = blend(self.ball_colour, [1, 1, 1], 0.0)#0.75)

		self.dt = 1./60 # frame rate

		self.speed_of_time = 1. # only use for testing!
		self.last_update_time = time.time()

		self.frame = 0.

		# need these two so that heartbeat and respiration animations are smooth
		self.hrx = 0.
		self.rrx = 0.

		self.vitals = Vitals(parent=self)
		self.last_thump_time = time.time()
		self.last_breath_in_time = time.time()
		self.last_breath_out_time = time.time()
		self.last_breath_operation = "in"

		self.C1 = Circle(parent=self, colour = self.c1_colour, radius = 100, width = 10, has_shadow=True)
		self.C2 = Circle(parent=self, colour = blend(self.c2_colour, self.bg_colour, self.c2_transparency), radius = 100, width = 24, has_shadow=False)

		self.ball = Ball(parent=self, colour=self.ball_colour, radius = 10.)

		self.clickBall = ClickBall(parent=self)

		self.fadingLabel = FadingLabel(parent=self)

		mixer.init()
		self.loadSounds()
		


		self.learner = Learner(parent=self)
		self.action_stack = []
		self.wait_to_act = 1.
		self.game_goal_points = [(0.5, 0.5)]
		self.playing_game = False
		self.action_start_time = None

		self.loadState()

		self.showLabel = True

		self.draw(init=True)

		self.isStopped = True

		return

	def loadSounds(self):

		# see: https://notificationsounds.com/notification-sounds?page=21

		self._intro_sound = mixer.Sound(self.dir+"sounds/intro_sound.wav")
		self._save_sound = mixer.Sound(self.dir+"sounds/save_sound.wav")
		self._heartbeat_sound = mixer.Sound(self.dir+"sounds/heartbeat_sound.wav")
		self._breath_in_sound = mixer.Sound(self.dir+"sounds/breath_in_sound_3.wav")
		self._breath_out_sound = mixer.Sound(self.dir+"sounds/breath_out_sound_3.wav")
		self._chime_sound = mixer.Sound(self.dir+"sounds/chime_sound.wav")

	def loadState(self):

		print("loading...")

		try:
			with open(self.dir+'state.json') as state_file:    
				state = json.load(state_file)

				self.frame = state['frame']
				self.action_stack = state['action_stack']
				self.wait_to_act = state['wait_to_act']
				self.game_goal_points = state['game_goal_points']
				self.playing_game = state['playing_game']

				self.vitals.loadState(state['vitality'])
				self.learner.loadState(state['learner'])
		except IOError:
			print("no state file")

	def saveState(self):

		state = dict()

		state['frame'] = self.frame
		state['action_stack'] = self.action_stack
		state['wait_to_act'] = self.wait_to_act
		state['game_goal_points'] = self.game_goal_points
		state['playing_game'] = self.playing_game
		state['vitality'] = self.vitals.saveStateToDict()
		state['learner'] = self.learner.saveStateToDict()

		print("saving...")

		with open(self.dir+'state.json', 'w') as outfile:
			json.dump(state, outfile)


	def draw(self, init=False):

		if init:

			self.root.wm_title("EmotiveCircle")
			self.root.geometry("%dx%d" % (self.window_width, self.window_height))

			self.root.protocol("WM_DELETE_WINDOW", self.leave)


			self.canvas = Canvas(self.root, bg=toHex(self.bg_colour))

			self.canvas.bind('<Button-1>', self.left_click)

			self.canvas.bind('<Button-3>', self.right_click)
			

			# add shadow first so it is below everything
			#self.shadow = self.canvas.create_oval(*self.getShadowPoints(), fill=toHex(self.shadow_colour), width=0)

			self.C2.draw(init=True)
			self.C1.draw(init=True)

			self.canvas.tag_bind(self.C1.index, '<Enter>', self.cursor_enter)

			# need to wait until there is the main canvas before drawing ball
			self.ball.draw(init=True)

			self.clickBall.draw(init=True)

			self.fadingLabel.draw(init=True)

			self.label = self.canvas.create_text(10, 10, text="", anchor='nw', fill=toHex(self.label_colour), font=("Courier", 10, "bold"))

			self.root.bind("<Configure>", self.resize)

			self.root.bind("<Key>", self.handleKey)

			self.root.update()

			self.resize()

		self.C1.draw()
		self.C2.draw()

		self.clickBall.draw()

		self.fadingLabel.draw()

		self.ball.draw()

	def resize(self, event=[]):
		

		self.window_width=self.root.winfo_width()
		self.window_height=self.root.winfo_height()

		self.canvas.place(x=0, y=0, width=self.window_width, height=self.window_height)

		self.C1.resize()
		self.C2.resize()

		self.ball.resize()

		self.fadingLabel.resize()

	def left_click(self, event=[]):
		# left click for feeding
		# * need to click inside to feed
		feeding = False
		if self.C1.isInside((event.x, event.y)):
			feeding = True
			self.vitals.feed()

		# if clicking at left edge of screen, pop up/hide label
		if event.x <= 25:
			self.showLabel = not self.showLabel

		# make clicking animation?
		colour = [0,0,0] if feeding else [1, 1, 1]
		self.clickBall.clickAt((event.x, event.y), colour=colour)

		return

	def right_click(self, event=[]):
		# right click for setting game goals

		newpt = (1.*event.x/self.window_width, 1.-1.*event.y/self.window_height)
		self.game_goal_points.append(newpt)
		
		#print("goal:", self.game_goal_points, event.x, event.y)
		self.learner.reset()

		self.clickBall.rightClickAt((event.x, event.y))

	def handleKey(self, event=[]):

		#print(str(event.keysym))
		#if event.keysym == 'q':
		#	print("Bye.")
		#	self.leave()

		#if event.keysym == 's':
		#	self.showLabel = not self.showLabel

		if event.keysym == 'Tab':
			print("reset goals")
			self.game_goal_points = []

		self.fadingLabel.type(event.keysym)

		#print(event.keysym)


		return

	def cursor_enter(self, event=[]):

		# entering from top/bottom: comforting
		# entering from left/right: annoying

		#print("hovering")

		#print("loc:", event.x, event.y)

		closestSide = self.C1.getClosestSide((event.x, event.y))

		#print(closestSide)

		if closestSide == "top" or closestSide == "bottom":
			# print("comfort")
			self.vitals.comfort()

		elif closestSide == "left" or closestSide == "right":
			# print("annoy")
			self.vitals.poke()
		#else:
			# print("center enter!")

		return

	def getNoise(self):

		# hungry, bored, ignored

		amplitude = interpolate(0., 1., self.vitals.getJaggedness())

		if self.frame%(2*int(1./self.dt)) == 0:

			n = self.C1.nb_circle_points

			# slowly rotate
			#self.C1.goalNoise = self.C1.goalNoise[1:]+self.C1.goalNoise[:1]

			#for _ in range(2):
			self.C1.goalNoise[random.randint(0, n-1)] = 1. + random.choice([1, -0.5])*amplitude


			
			new_pts = [v for v in self.C1.goalNoise]
			for _ in range(2):
				for i in range(n):
					new_pts[i] = (self.C1.goalNoise[(i-1)%n]+2*self.C1.goalNoise[i%n]+self.C1.goalNoise[(i+1)%n])/4.0
				self.C1.goalNoise = new_pts

			self.C1.goalNoise = [min(max(g, 0.75), 1.5) for g in self.C1.goalNoise]

			avg = 1.*sum(self.C1.goalNoise)/n
			self.C1.goalNoise = [1.*v/avg for v in self.C1.goalNoise]

			self.C1.circle_offsets = self.C1.goalNoise
			self.C2.circle_offsets = self.C1.goalNoise

	def pulsations(self):

		pi = math.pi

		
		blood_pressure = self.vitals.getBloodPressure() # increases amplitude of heart beat and breathing, but not rate

		HR = self.vitals.getHeartRate()
		Hf = math.cos(self.hrx + self.dt*pi*HR/60.)**2**2**2 - (math.cos(self.hrx + self.dt*pi*HR/60.)**4)/1.5
		# now need to scale from 0 to 1
		Hf = (Hf+0.3)*1.6
		#heart_mult = interpolate(0.9-E*0.15, 1.1+E*0.15, Hf)
		heart_mult = interpolate(1.-blood_pressure*0.2, 1.+blood_pressure*0.2, Hf)
		if Hf >= 0.8:
			self.thump()


		resp_depth = self.vitals.getRespiratoryDepth()

		RR = self.vitals.getRespiratoryRate()
		Rf = math.cos(self.rrx + 2.*self.dt*pi*RR/60.)
		# now need to scale from 0 to 1
		Rf = (Rf+1.0)*0.5
		#respiratory_mult = interpolate(0.95-E*0.05, 1.05+E*0.05, Rf)
		respiratory_mult = interpolate(1.-resp_depth*0.1, 1.+resp_depth*0.1, Rf)
		if Rf <= 0.2:
			self.breathe("in")
		if Rf >= 0.8:
			self.breathe("out")

		self.hrx += self.dt*pi*HR/60.
		self.rrx += 2.*self.dt*pi*RR/60.

		self.C2.width_mult = heart_mult

		# more full -> larger, more angry -> larger
		#m = min(interpolate(0.5, 1.5, self.vitals.emotion_levels['fullness']) * interpolateN([1., 1.5], [0.5, 1.], self.vitals.getAnger()), 1.5)
		m = interpolate(0.5, 1.5, self.vitals.getSize())

		self.C2.radius_mult = respiratory_mult* m
		self.C1.radius_mult = respiratory_mult* m

		return

	def thump(self):

		# 120 bpm = 2 beats/s

		if time.time() - self.last_thump_time <= 60./300.:
			return

		self.last_thump_time = time.time()

		#print("THUMP")
		self._heartbeat_sound.set_volume(self.vitals.getBloodPressure())
		mixer.Sound.play(self._heartbeat_sound)
		mixer.music.stop()

		return

	def breathe(self, direction):

		
		# 60 bpm = 1 beats/s
		if direction == "in":
			#if time.time() - self.last_breath_in_time <= 60./60. or self.last_breath_operation == "out":
			#	return
			if self.last_breath_operation == "in": return

			self.last_breath_operation = "in"
			self.last_breath_in_time = time.time()

			#print("BREATH IN")
			self._breath_in_sound.set_volume(0.5*self.vitals.getRespiratoryDepth())
			mixer.Sound.play(self._breath_in_sound)
			mixer.music.stop()
		else:
			#if time.time() - self.last_breath_out_time <= 60./60.:
			#	return

			if self.last_breath_operation == "out": return

			self.last_breath_operation = "out"

			self.last_breath_out_time = time.time()

			#print("BREATH OUT")
			self._breath_out_sound.set_volume(0.5*self.vitals.getRespiratoryDepth())
			mixer.Sound.play(self._breath_out_sound)
			mixer.music.stop()
		


		return

	def chime(self):
		self._chime_sound.set_volume(0.25)
		mixer.Sound.play(self._chime_sound)
		mixer.music.stop()

	def controlBall(self):

		def getScore():

			#loc = [loc[0], 1.-loc[1]] # convert to the physics form
			goalpts = [(0.5, 0.5)] if self.game_goal_points == [] else self.game_goal_points
			avgDist = self.ball.getPathAverageMinDist(self.action_start_time, goalpts)
			#print("avg:", avgDist)
			#return loc[1]
			#return -abs(loc[0]-0.5)
			return -avgDist #-dist(avgDist, self.game_goal)

		action_time = 0.5

		if self.vitals.wantsToStartPlaying() or self.learner.need_reward or (self.playing_game and self.vitals.wantsToKeepPlaying()):
			#print(self.vitals.wantsToStartPlaying(), self.learner.need_reward, (self.playing_game and self.vitals.wantsToKeepPlaying()))
			self.playing_game = True
			self.vitals.setExertionLevel(0.25)

			curTime = time.time()
			if curTime - self.ball.last_hit_time >= action_time + self.wait_to_act: # hit at max rate
				self.wait_to_act = 0.

				if self.learner.need_reward and self.action_stack == []:

					r = getScore()

					isBest = self.learner.applyReward(r)

					if isBest:
						self.vitals.practiceReward()
						self.chime()

					self.wait_to_act = 1.

				elif not self.learner.need_reward and self.action_stack == []:

					#print("RESTARTING")
					self.ball.reset_position()

					self.action_stack = self.learner.getNextGuess()

					#self.vitals.exercise(intensity=0.25)

					self.action_start_time = time.time()

				else:

					force, duration = self.action_stack.pop()
					#print(force, duration)
					self.ball.applyForce(force, duration)


		else:
			self.playing_game = False
			self.vitals.setExertionLevel(0.0)

	def getCenter(self):

		# ['fullness', 'affection', 'excitement', 'arousal']


		# affection : increase
		# excitement : increase
		# arousal : increase
		# anger : --
		# boredom : ** (try use just this)

		height = interpolate(0.25, 0.6, self.vitals.getElevation()) # 

		return (0.5, height) # in physics form

	def updateLabel(self):

		text = ""
		if self.showLabel:
			text = str(self.vitals.summary())
			text += '\n'
			text += "{}:\n\t{}".format("goal points", '\n\t'.join([str((round(v[0], 2), round(v[1], 2))) for v in self.game_goal_points]))

		self.canvas.itemconfig(self.label, text=text)

		return

	def step(self):

		if self.isStopped: return

		self.vitals.step()

		self.pulsations()

		self.getNoise()

		self.controlBall()

		self.updateLabel()

		self.draw()


		self.frame += 1.

		self.after(int(self.dt*1000/self.speed_of_time), self.step)

	def run(self):

		self.isStopped = False

		
		#mixer.Sound.play(self._intro_sound)
		#mixer.music.stop()

		#time.sleep(3.)

		self.step()

		self.root.mainloop()

	def leave(self, event=[]):

		self.saveState()

		#mixer.Sound.play(self._save_sound)
		#mixer.music.stop()
		#time.sleep(0.75)

		self.isStopped = True

		#print("here")
		self.root.quit()
		#print("here")
		self.root.destroy()

