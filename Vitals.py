from __future__ import print_function

import math
import time
from common import *


# anger: https://www.sciencedaily.com/releases/2010/05/100531082603.htm
# exercise, cortisol: https://www.ncbi.nlm.nih.gov/pubmed/18787373

# todo: updateMuscleFatigue -- proportional to current exertion level

'''
The main reason we become more irritable when hungry is because our blood glucose level drops.
This can make it difficult for us to concentrate, and more likely to snap at those around us.

Low blood sugar also triggers the release of stress-related hormones like cortisol and adrenaline,
as well as a chemical called neuropeptide Y, which has been found to make people behave more aggressively towards those around them.
'''

class Vitals():

	def __init__(self, parent):

		self.parent = parent

		self.base_heart_rate = 60.
		self.base_respiratory_rate = 16. #60. #16.
		self.base_metabolic_rate = 1500. # kcal/day

		self.calories_stored = 0.#self.base_metabolic_rate*1.5#16. # measured in kcal
		self.calories_in_stomach = 0.
		self.stomach_calorie_capacity = 2.*self.base_metabolic_rate

		self.hours_to_digest_bmr = 6. #how long it would take to digest a days worth of calories

		self._ghrelin = 0.5 # updates
		self._leptin = 0.5 # updates
		self._oxytocin = 0.5
		self._cortisol = 0.5
		self._adrenaline = 0.5
		self._insulin = 0.5 # updates
		self._endorphins = 0.5
		self._muscle_fatigue = 0.0 # https://en.wikipedia.org/wiki/Muscle_fatigue

		self._blood_glucose = 0.5

		self._exertion = 0.0


		self.gameBoredomStartThreshold = 0.15
		self.gameBoredomStopThreshold = 0.05

		self.last_update_time = 0


		return


	def loadState(self, state):

		self.calories_stored = state['calories_stored']
		self.calories_in_stomach = state['calories_in_stomach']
		#self.emotion_levels = state['emotion_levels']
		self._ghrelin = state['_ghrelin']
		self._leptin = state['_leptin']
		self._oxytocin = state['_oxytocin']
		self._cortisol = state['_cortisol']
		self._adrenaline = state['_adrenaline']
		self._insulin = state['_insulin']
		self._endorphins = state['_endorphins']
		self._blood_glucose = state['_blood_glucose']

		try:
			self._muscle_fatigue = state['_muscle_fatigue']
		except:
			print("cannot load _muscle_fatigue")

		self.last_update_time = state['last_update_time']

		return

	def saveStateToDict(self):

		state = dict()
		state['calories_stored'] = self.calories_stored
		state['calories_in_stomach'] = self.calories_in_stomach
		#state['emotion_levels'] = self.emotion_levels
		state['_ghrelin'] = self._ghrelin
		state['_leptin'] = self._leptin
		state['_oxytocin'] = self._oxytocin
		state['_cortisol'] = self._cortisol
		state['_adrenaline'] = self._adrenaline
		state['_insulin'] = self._insulin 
		state['_endorphins'] = self._endorphins
		state['_blood_glucose'] = self._blood_glucose
		state['_muscle_fatigue'] = self._muscle_fatigue

		state['last_update_time'] = self.last_update_time

		return state

	def step(self):

		if self.last_update_time == None:
			self.last_update_time = time.time()

		curTime = time.time()
		timeDiff = curTime - self.last_update_time

		self.digestion(timeDiff)

		# needs decay:
		#	- oxytocin
		#	- cortisol
		# 	- adrenaline
		#	- endorphins
		# 	- muscle fatigue

		oxytocin_halflife = timeDiff/(3600.*(3./60.)) # half life of 1-6 minutes
		self._oxytocin = self._oxytocin * (0.5 ** (oxytocin_halflife))

		

		adrenaline_halflife = timeDiff/(3600.*(3./60.)) # half life of 2-3 minutes
		self._adrenaline = self._adrenaline * (0.5 ** (adrenaline_halflife))

		endorphins_halflife = timeDiff/(3600.*(30./60.)) # half life of 1/2 hour
		self._endorphins = self._endorphins * (0.5 ** (endorphins_halflife))

		muscle_fatigue_halflife = timeDiff/(3600.*(4.*60./60.)) # half life of 4 hours? (guessing)
		self._muscle_fatigue = self._muscle_fatigue * (0.5 ** (muscle_fatigue_halflife))


		self.updateCortisol(timeDiff)
		self.updateInsulin()
		self.updateLeptin()
		self.updateGhrelin()
		self.updateBloodGlucose()

		self.last_update_time = curTime



		return

	def digestion(self, elapsed):
		# calculate calories spent
		# MR
		calSpent = self.getMetabolicRate() * elapsed/(60.*60.*24.)

		# lets just say you are able to digest bmr cal/day
		# calories digested per second
		cdps = self.base_metabolic_rate/(60*60*self.hours_to_digest_bmr)
		calDigested = min(max(self.calories_in_stomach-cdps, 0), cdps*elapsed)
		self.calories_in_stomach -= cdps*elapsed
		self.calories_in_stomach = max(self.calories_in_stomach, 0)

		self.calories_stored += calDigested - calSpent
		self.calories_stored = max(self.calories_stored, 0.)

		return

	def getMetabolicRate(self):

		# increased by adrenaline

		return self.base_metabolic_rate * interpolate(1, 2, self._adrenaline) * interpolate(0.8, 1.2, self._blood_glucose)

	def getHunger(self):

		# between 0 and 1

		# ghrelin, leptin, adrenaline, cortisol

		#hunger = bound(0, 1., 0.5 + 0.5*self._ghrelin - 0.5*self._leptin - 0.5*self._adrenaline - 0.25*self._cortisol)

		#return hunger

		base_weight = 0.25

		m = (self._ghrelin*self._ghrelin 
			+ self._leptin*0.0 
			+ self._adrenaline*0.0 
			+ 0.5*self._cortisol*0.0 
			+ base_weight*0.0)/(self._ghrelin + self._leptin + 0.5*self._cortisol + self._adrenaline + base_weight)

		return m

	def getHeartRate(self):
		# http://www.healthline.com/health/low-blood-sugar-effects-on-body

		bgw = 1.-self._blood_glucose

		# adrenaline, endorphins, blood sugar
		base_weight = 0.25

		# todo: low blood sugar can cause rapid heartbeat

		m = (self._endorphins*1. 
			+ self._adrenaline*3. 
			+ base_weight*1.)/(self._endorphins + self._adrenaline + base_weight)

		return self.base_heart_rate*m

	def getBloodPressure(self):
		# between 0 and 1 -> 0.5 is average

		# cortisol, adrenaline, endorphins

		base_weight = 0.25

		m = (self._cortisol*1.0 
			+ self._adrenaline*1.0 
			+ self._endorphins*0.5 
			+ base_weight*0.5)/(self._cortisol + self._adrenaline + self._endorphins + base_weight)

		return m

	def getRespiratoryRate(self):

		# adrenaline
		base_weight = 0.25

		m = (self._adrenaline*3. + base_weight*1.)/(self._adrenaline + base_weight)

		return self.base_respiratory_rate*m

	def getRespiratoryDepth(self):
		# between 0 and 1, 0.5 avg

		# just guessing here...

		base_weight = 0.25

		m = (self._cortisol*0.25 + self._adrenaline*1.0 + base_weight*0.5)/(self._cortisol + self._adrenaline + base_weight)

		return m

	

	def getHappiness(self):
		# between 0 and 1

		# oxytocin, endorphins

		base_weight = 0.25

		m = (self._oxytocin*1.0 
			+ self._endorphins*1.0 
			+ self._cortisol*0.0
			+ self._adrenaline*0.25
			+ base_weight*0.5)/(self._oxytocin + self._endorphins + self._cortisol + self._adrenaline + base_weight)

		return m

	def updateBloodGlucose(self):
		# increased by cortisol
		# increased by adrenaline
		# decreased by insulin
		# increased by ghrelin

		#self._blood_glucose = bound(0, 1., 0.5 + 0.2*self._cortisol + 0.2*self._adrenaline - 0.5*self._insulin + 0.2*self._ghrelin)

		base_weight = 0.25

		m = (self._cortisol*1.0 
			+ self._adrenaline*1.0 
			+ self._insulin*(1.-self._insulin)
			+ self._ghrelin*0.75 
			+ base_weight*0.5)/(self._cortisol + self._adrenaline + self._insulin + self._ghrelin + base_weight)

		#m = 1.-self._insulin

		self._blood_glucose = 0.5*self._blood_glucose + 0.5*m
		#return m


	def updateInsulin(self):

		# between 0 and 1, avg 0.5

		#self._insulin = bound(0, 1, 0.5 -  0.2*self._cortisol + 0.5*(self._blood_glucose-0.5) - 0.2*self._ghrelin)

		base_weight = 0.#25

		m = (0.25*self._cortisol*0.0
			+ 1.*self._blood_glucose 
			+ 0.25*self._ghrelin*0.0
			+ base_weight*0.5)/(0.25*self._cortisol + 1. + 0.25*self._ghrelin + base_weight)

		#m = self._blood_glucose

		self._insulin = 0.5*self._insulin + 0.5*m
		#return m


	def updateLeptin(self):

		# leptin levels determined by body fat level

		# between 0, 1
		self._leptin = bound(0, 1, self.calories_stored/(30.*self.base_metabolic_rate))

	def updateGhrelin(self):

		# released when stomach is empty

		self._ghrelin = (1. - 1.*self.calories_in_stomach/self.stomach_calorie_capacity)**2

	def updateCortisol(self, timeDiff):
		# timeDiff: time since last update
		
		# apply exponential decay
		cortisol_halflives = timeDiff/(3600.*(66./60.)) # half life of 66 minutes # but is released at small constant rate
		self._cortisol = self._cortisol * (0.5 ** (cortisol_halflives))


		#if self._exertion >= 0.5:
		#	self._cortisol = bound(0, 1, self._cortisol + 0.01*(1.-self._oxytocin))
		#else:
		#	self._cortisol = bound(0, 1, self._cortisol - 0.01)


		# increase cortisol levels at some rate:
		# 1 per hour per exertion unit * (1-oxytocin)

		hours = timeDiff/3600.

		added_cortisol = 0.

		if self._exertion >= 0.5:
			# strenuous exercise increases cortisol
			added_cortisol = hours * (2.*(self._exertion-0.5)) * (1.-self._oxytocin)
		elif self._exertion > 0.:
			# low level exercise decreases cortisol
			added_cortisol = hours * (2.*(self._exertion-0.5))*0.5 # decrease at a rate of 0.5 per hour

		self._cortisol = bound(0, 1, self._cortisol + added_cortisol)


	def comfort(self):
		# decrease cortisol
		# increase oxytocin
		# increase endorphins

		self._cortisol = bound(0, 1, self._cortisol - 0.01)
		self._oxytocin = bound(0, 1, self._oxytocin + 0.01)
		self._endorphins = bound(0, 1, self._endorphins + 0.01)

	def poke(self):
		# increase cortisol

		self._cortisol = bound(0, 1, self._cortisol + 0.1*(1.-self._oxytocin))

	def feed(self):

		self.calories_in_stomach = bound(0., self.stomach_calorie_capacity, self.calories_in_stomach +5.)

	def exercise(self, intensity = 1.0):
		# increase cortisol (if mid-to-high intensity, otherwise decrease)
		# increase adrenaline
		# increase endorphins

		if intensity >= 0.5:
			self._cortisol = bound(0, 1, self._cortisol + 0.01*(1.-self._oxytocin))
		else:
			self._cortisol = bound(0, 1, self._cortisol - 0.01)

		self._muscle_fatigue = bound(0, 1, self._muscle_fatigue + intensity/200.)

		self._adrenaline = bound(0, 1, self._adrenaline + 0.01*intensity)

		self._endorphins = bound(0, 1, self._endorphins + 0.01*intensity)



	def practiceReward(self):

		self._adrenaline = bound(0, 1, self._adrenaline + 0.1)



	def getElevation(self):
		# between 0 and 1, 0.5 avg

		return self.getHappiness()

	def getSize(self):
		# between 0 and 1, 0.5 avg

		return bound(0, 1.0, 0.5 - self.getHunger()*0.5 + self._adrenaline*0.5)

	def getThickness(self):

		return self._leptin

	def getJaggedness(self):

		return max(self.getHunger(), self._cortisol)**2

	def wantsToStartPlaying(self):
		#return False
		# not too hungry or stressed

		return self.getHunger() <= 0.5 and self._muscle_fatigue <= 0.25 # self._cortisol <= 0.5


	def wantsToKeepPlaying(self):
		#return False
		return self.getHunger() <= 0.5 and self._muscle_fatigue <= 0.8 # and self._cortisol <= 0.75

	def setExertionLevel(self, exertion):
		self._exertion = exertion

	def summary(self):

		text = ""

		text += "{}: {:.2f}\n".format("  exertion", self._exertion)
		text += "{}: {:.2f}\n".format(" happiness", self.getHappiness())

		text += "\n=== Heart ===\n"
		text += "{}: {:.2f}\n".format("    rate", self.getHeartRate())
		text += "{}: {:.2f}\n".format("pressure", self.getBloodPressure())

		text += "\n=== Respiration ===\n"
		text += "{}: {:.2f}\n".format(" rate", self.getRespiratoryRate())
		text += "{}: {:.2f}\n".format("depth", self.getRespiratoryDepth())

		text += "\n=== Food & Energy ===\n"
		text += "{}: {:.2f}\n".format("    kCal stored", self.calories_stored)
		text += "{}: {:.2f}\n".format("kCal in stomach", self.calories_in_stomach)
		text += "{}: {:.2f}\n".format(" metabolic rate", self.getMetabolicRate())
		text += "{}: {:.2f}\n".format("         hunger", self.getHunger())

		text += "\n==== Chemical Levels ===\n"
		text += "{}: {:.2f}\n".format(" blood glucose", self._blood_glucose)
		text += "{}: {:.2f}\n".format("       ghrelin", self._ghrelin)
		text += "{}: {:.2f}\n".format("        leptin", self._leptin)
		text += "{}: {:.2f}\n".format("      oxytocin", self._oxytocin)
		text += "{}: {:.2f}\n".format("      cortisol", self._cortisol)
		text += "{}: {:.2f}\n".format("    adrenaline", self._adrenaline)
		text += "{}: {:.2f}\n".format("       insulin", self._insulin)
		text += "{}: {:.2f}\n".format("    endorphins", self._endorphins)
		text += "{}: {:.2f}\n".format("muscle fatigue", self._muscle_fatigue) # todo: is this classified as chemical level?

		text += "\n=== Visual Properties ===\n"
		text += "{}: {:.2f}\n".format(" elevation", self.getElevation())
		text += "{}: {:.2f}\n".format("      size", self.getSize())
		text += "{}: {:.2f}\n".format("jaggedness", self.getJaggedness())

		return text


if __name__ == "__main__":

	V = Vitals(parent=None)
	print(V.summary())