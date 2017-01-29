from __future__ import print_function

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor

import random
import math
import time
import copy
import numpy as np

from common import *

class Learner:

	def __init__(self, parent):

		self.parent = parent

		## SETTINGS ##
		self.seqLen = 5

		self.minForceX = -1.5
		self.maxForceX = 1.5
		self.minForceY = 0.
		self.maxForceY = 1.5

		self.minDuration = 0.4
		self.maxDuration = 0.4
		##############



		self.best_guess = self.getRandomSolution()
		self.best_score = -float('inf')

		self.new_guess = None
		self.new_score = None

		self.need_reward = False

	def loadState(self, state):

		self.best_guess = state['best_guess']
		self.best_score = state['best_score']
		self.new_guess = state['new_guess']
		self.new_score = state['new_score']
		self.need_reward = state['need_reward']

		return

	def saveStateToDict(self):

		state = dict()
		state['best_guess'] = self.best_guess
		state['best_score'] = self.best_score
		state['new_guess'] = self.new_guess
		state['new_score'] = self.new_score
		state['need_reward'] = self.need_reward

		return state


	def applyReward(self, r):
		#print("IN APPLY REWARD")

		isBest = False

		assert(float(r))

		assert(len(self.new_guess) >= 1)
		assert(len(self.best_guess) >= 1)
		assert(float(self.best_score))
		#if self.new_guess == None or self.new_guess == []:
		#	print("ERROR: new_guess empty")

		self.new_score = r

		if self.new_score > self.best_score:
			self.best_guess = copy.deepcopy(self.new_guess)
			self.best_score = self.new_score

			isBest = True

			#print("\tnew best:", self.best_guess, self.best_score)


		assert(len(self.new_guess) >= 1)
		assert(len(self.best_guess) >= 1)
		assert(float(self.new_score))
		assert(float(self.best_score))


		self.need_reward = False

		return isBest


	def modifySolution(self, solution):
		#print("IN MOD")

		#assert(len(solution) >= 1)

		if random.random() < 0.25:
			return self.getRandomSolution()

		#return solution

		new_solution = []

		mType = random.randint(0, 1)

		if mType == 0:

			for s in solution:
				if random.random() < 0.6:
					new_solution.append(s)
				else:

					force, duration = s
					#print("MOD:", force, duration)

					new_force = [bound(self.minForceX, self.maxForceX, force[0]+random.randint(-1, 1)*random.random()**4),
								 bound(self.minForceY, self.maxForceY, force[1]+random.randint(-1, 1)*random.random()**4)]
					#new_force = [0.1, 1.5]#random.choice([-0.5, 0., 0.5]), random.choice([-0.5, 0., 0.5])]

					new_duration = bound(self.minDuration, self.maxDuration, duration+random.randint(-1, 1)*random.random()**4)

					new_solution.append([new_force, new_duration])
		elif mType == 1:
			#print("rotate")
			if random.random() < 0.5:
				new_solution = solution[1:]+solution[:1]
			else:
				new_solution = solution[-1:]+solution[:-1]
			#print("force, duration: ", new_force, new_duration)
		
		#print("\tMOD:", new_solution)

		assert(len(new_solution) >= 1)

		return new_solution #


	def getNextGuess(self):
		#print("IN GET NEXT")
	
		assert(len(self.best_guess) >= 1)

		#print("BEST_GUESS:", self.best_guess)
		self.new_guess = self.modifySolution(self.best_guess)
		self.new_score = None
		self.need_reward = True

		assert(len(self.new_guess) >= 1)

		#print("\tnew guess:", self.new_guess)

		return copy.deepcopy(self.new_guess)


	def getRandomSolution(self):
		s = []
		for _ in range(self.seqLen):
			s.append(self.getRandomAction())

		return s



	def getRandomAction(self):

		# random force and duration

		force = (rand(self.minForceX, self.maxForceX), rand(self.minForceY, self.maxForceY))
		duration = rand(self.minDuration, self.maxDuration)

		return [force, duration]

	def reset(self):
		self.getRandomSolution()
		self.best_score = -float('inf')

'''
class Learner:

	def __init__(self, parent):

		self.parent = parent

		self.X = []
		self.y = []

		self.preferred_solution = None

		self.model = None

	def addData(self, X, y):

		self.X.append(X)
		self.y.append(y)

		self.X = self.X[-100:]
		self.y = self.y[-100:]


	def getBestAction(self):
		# predict where to pull ball towards

		# make training data semi-sequential

		# get current ball state
		ball_loc = self.parent.ball.getLocation()
		ball_vel = self.parent.ball.velocity

		histLen = 1

		if len(self.X )< 10: #histLen:
			return [random.random(), random.random()]


		self.model = KNeighborsRegressor(n_neighbors=3) # DecisionTreeRegressor() #LinearRegression() # 
		self.model.fit(np.array(self.X), np.array(self.y))

		# to find a good actions, create a bunch of randoms and choose the best
		# or try hill climbing?

		# list(force+tuple([duration])+loc+acc)
		
		def randomSample(loc=None):
			#force = ((random.random()-0.5), 0.)#random.random())#-0.5)
			#duration = 0.5 #random.random()
			pullLoc = (random.random(), random.random())
			if loc != None:
				pullLoc = loc

			loc = ball_loc
			vel = ball_vel
			return list(pullLoc+loc+vel)

		
		X_test = [randomSample() for _ in range(10)]
		if self.preferred_solution != None:
			X_test.append(randomSample(tuple(self.preferred_solution)))

		y_pred = list(self.model.predict(X_test))

		y_best = max(y_pred)

		x_best = X_test[y_pred.index(y_best)]
		#x_best = chunk(x_best, len(x_best)/histLen)[0]
		#x_best = list(x_best[:3]) # need only the force and duration parts
		best_action = x_best[:2]
		#print("pred:", best_action, y_best)

		self.preferred_solution = best_action

		return best_action
		#return [0, 1, 1]
'''