from __future__ import print_function

import math
import time
from common import *

class Vitals():

	def __init__(self, parent):

		self.parent = parent

		self.base_heart_rate = 60.
		self.base_respiratory_rate = 16. #60. #16.
		self.base_metabolic_rate = 1500. # kcal/day

		self.calories_available = 0.#self.base_metabolic_rate*1.5#16. # measured in kcal
		self.calories_in_stomach = 0.
		self.stomach_calorie_capacity = 2.*self.base_metabolic_rate

		self.hours_to_digest_bmr = 6. #how long it would take to digest a days worth of calories

		self.emotion_levels = dict()
		self.emotion_levels['fullness'] = 0.0 # hungry/full
		self.emotion_levels['excitement'] = 0.0 # excited/bored
		self.emotion_levels['arousal'] = 0.0 # aroused/sleepy
		self.emotion_levels['affection'] = 0.0 # loved/ignored

		# importance order
		self.emotion_order = ['fullness', 'affection', 'excitement', 'arousal']

		self.last_update_time = 0

		


		return


	def loadState(self, state):

		self.calories_available = state['calories_available']
		self.calories_in_stomach = state['calories_in_stomach']
		self.emotion_levels = state['emotion_levels']
		self.last_update_time = state['last_update_time']

		return

	def saveStateToDict(self):

		state = dict()
		state['calories_available'] = self.calories_available
		state['calories_in_stomach'] = self.calories_in_stomach
		state['emotion_levels'] = self.emotion_levels
		state['last_update_time'] = self.last_update_time

		return state

	def step(self):

		if self.last_update_time == None:
			self.last_update_time = time.time()

		curTime = time.time()
		timeDiff = curTime - self.last_update_time

		## AFFECTION DECAY
		affection_halflives = timeDiff/(3600.) # half life of one hour
		if self.emotion_levels['affection'] >= 0.75:
			self.emotion_levels['affection'] -= timeDiff/120.
		else:
			self.emotion_levels['affection'] = self.emotion_levels['affection'] * (0.5 ** (affection_halflives))
		self.emotion_levels['affection'] = bound(0, 1, self.emotion_levels['affection'])

		## EXCITEMENT DECAY
		excitement_halflives = timeDiff/(3600.*0.125) # half life of 1/8 hour
		if self.emotion_levels['excitement'] >= 0.75:
			self.emotion_levels['excitement'] -= timeDiff/30.
		else:
			self.emotion_levels['excitement'] = self.emotion_levels['excitement'] * (0.5 ** (excitement_halflives))
		self.emotion_levels['excitement'] = bound(0, 1, self.emotion_levels['excitement'])

		## AROUSAL DECAY
		arousal_halflives = timeDiff/(3600.*0.5) # half life of 1/5 hour
		self.emotion_levels['arousal'] = self.emotion_levels['arousal'] * (0.5 ** (excitement_halflives))
		self.emotion_levels['arousal'] = bound(0, 1, self.emotion_levels['arousal'])



		self.energyStep(timeDiff)

		self.last_update_time = curTime



		return


	def energyStep(self, elapsed):
		# calculate calories spent
		# MR
		calSpent = self.getMetabolicRate() * elapsed/(60.*60.*24.)

		# lets just say you are able to digest bmr cal/day
		# calories digested per second
		cdps = self.base_metabolic_rate/(60*60*self.hours_to_digest_bmr)
		calDigested = min(max(self.calories_in_stomach-cdps, 0), cdps*elapsed)
		self.calories_in_stomach -= cdps*elapsed
		self.calories_in_stomach = max(self.calories_in_stomach, 0)

		self.calories_available += calDigested - calSpent
		self.calories_available = max(self.calories_available, 0.)

		self.updateFullness()

		return



	def updateFullness(self):

		if self.calories_in_stomach > 0:
			self.emotion_levels['fullness'] = interpolateN([0.5, 1.], [0., 1.], self.calories_in_stomach/self.stomach_calorie_capacity)
		else:
			self.emotion_levels['fullness'] = interpolateN([0., 0.2, 0.5], [0., 1., 2.], self.calories_available/self.base_metabolic_rate)

	def getEmotionImmediacy(self):

		IVec = [0 for _ in self.emotion_order]


		# individual weights
		R = [0.5*(1.0-self.emotion_levels[k]) for k in self.emotion_order]

		for i in range(0, len(self.emotion_order)):
			IVec[i] = math.pow(R[i], 1.5)*(1.0 - sum(IVec))

		return IVec

	def getEmotion(self):

		# get immediacy vector
		IV = self.getEmotionImmediacy()
		
		return dict(zip(self.emotion_order, IV))

	def getEnergyLevel(self):

		# base level is 1. (it acts as a multiplier)

		# ranges from 0 to 1
		# excitation depends on the following moods:
		E = 0.75*self.emotion_levels['excitement'] + 0.25*self.emotion_levels['arousal']
		#E = self.emotion_levels['excitement']
		return E

	def getHeartRate(self):

		return self.base_heart_rate*interpolateN([0.75, 1., 3.], [0., 0.5, 1.], self.getEnergyLevel())

	def getRespiratoryRate(self):

		return self.base_respiratory_rate*interpolateN([0.75, 1., 4.], [0., 0.5, 1.], self.getEnergyLevel())

	def getMetabolicRate(self):

		return self.base_metabolic_rate*interpolateN([1., 2.], [0., 1.], self.getEnergyLevel())

	def feed(self):

		self.calories_in_stomach = bound(0, self.stomach_calorie_capacity, self.calories_in_stomach+5)
		self.emotion_levels['arousal'] = 0.9*self.emotion_levels['arousal'] + 0.1*1.

		return

	def comfort(self):

		#self.emotion_levels['affection'] = bound(0, 1, self.emotion_levels['affection'] + 1./50)

		self.emotion_levels['affection'] = 0.9*self.emotion_levels['affection'] + 0.1*1.
		self.emotion_levels['excitement'] = 0.9*self.emotion_levels['excitement'] + 0.1*0.25

		return

	def annoy(self):

		self.emotion_levels['excitement'] = 0.8*self.emotion_levels['excitement'] + 0.2*1.
		self.emotion_levels['affection'] = 0.8*self.emotion_levels['affection'] + 0.2*0.
		self.emotion_levels['arousal'] = 0.95*self.emotion_levels['arousal'] + 0.05*1.0

		return

	def practiceReward(self):

		self.emotion_levels['excitement'] = bound(0, 1, self.emotion_levels['excitement']+0.15)
		self.emotion_levels['arousal'] = 0.95*self.emotion_levels['arousal'] + 0.05*1.0
		#print("exciting!")

	def playingGame(self):

		self.emotion_levels['excitement'] = bound(0, 1, self.emotion_levels['excitement']+0.01)

		# increase or decrease arousal?
		# perhaps playng increases excitement, but makes you exhausted?
		self.emotion_levels['arousal'] = 0.995*self.emotion_levels['arousal'] + 0.005*0.0 #1.0



	def getAnger(self):

		anger = self.emotion_levels['excitement'] * (1. - self.emotion_levels['affection'])

		return anger

	def getBoredom(self):

		#boredom when excitement is low, affection is also low, and arousal is high

		boredom = self.emotion_levels['arousal'] * (1.-self.emotion_levels['excitement']) * (1. - self.emotion_levels['affection'])#**2)

		return boredom

	def getDiscomfort(self):

		# jagged when hungry
		hunger_factor = interpolate(1., 0, self.emotion_levels['fullness']) **2**2
		# jagged when feeling unliked
		unliked_factor = interpolate(1., 0, self.emotion_levels['affection']) **2**2
		# jagged when bored
		boredom_factor = interpolate(0., 1., self.getBoredom())

		return max(hunger_factor, unliked_factor, boredom_factor)

	def summary(self):

		text = ""
		for e in self.emotion_order:
			text += "{}: {}\n".format(e, round(self.emotion_levels[e], 3))

		text += "\n{}: {}".format("energy", round(self.getEnergyLevel(), 3))
		text += "\n{}: {}".format("discomfort", round(self.getDiscomfort(), 3))
		text += "\n{}: {}".format("anger", round(self.getAnger(), 3))
		text += "\n{}: {}\n".format("boredom", round(self.getBoredom(), 3))

		text += "\n{}: {}".format("heart rate", round(self.getHeartRate(), 1))
		text += "\n{}: {}\n".format("resp rate", round(self.getRespiratoryRate(), 1))

		text += "\n{}: {}".format("kCal total", round(self.calories_available, 0))
		text += "\n{}: {}".format("kCal in stomach", round(self.calories_in_stomach, 0))
		text += "\n{}: {}\n".format("metabolic rate (kCal/day)", round(self.getMetabolicRate(), 0))
		
		return text
