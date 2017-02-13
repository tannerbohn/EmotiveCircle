from __future__ import print_function

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.kernel_ridge import KernelRidge

import itertools
import random
import math
import time
import copy
import numpy as np
from pprint import *

from scipy.stats import pearsonr, spearmanr

from common import *

class Learner:

	def __init__(self, parent):

		self.parent = parent

		self.restarting = True

		## SETTINGS ##
		self.seqLen = 6

		self.minForceX = -2.0
		self.maxForceX = 2.0
		self.minForceY = -2.0
		self.maxForceY = 2.0

		self.minDuration = 0.5
		self.maxDuration = 0.5
		##############

		self.best_guess = self.getCenterSolution()
		self.best_score = None

		self.new_guess = None
		self.new_score = None

		self.need_reward = False

		# params for multi-stage space search
		self.stage_num = 0
		self.samples_per_stage = 5
		self.stage_samples = []



		self.guesses = []

	def loadState(self, state):

		try:
			self.best_guess = state['best_guess']
		except:
			print("Could not load best_guess")
			pass

		try:
			self.best_score = state['best_score']
		except:
			print("Could not load best_score")
			pass

		try:
			self.new_guess = state['new_guess']
		except:
			print("Could not load new_guess")
			pass

		try:
			self.new_score = state['new_score']
		except:
			print("Could not load new_score")
			pass

		try:
			self.need_reward = state['need_reward']
		except:
			print("Could not load need_reward")
			pass

		try:
			self.guesses = state['guesses']
		except:
			print("Could not load guesses")
			pass

		try:
			self.stage_num = state['stage_num']
		except:
			print("Could not load stage_num")
			pass

		try:
			self.stage_samples = state['stage_samples']
		except:
			print("Could not load stage_samples")
			pass



		return

	def saveStateToDict(self):

		state = dict()
		state['best_guess'] = self.best_guess
		state['best_score'] = self.best_score
		state['new_guess'] = self.new_guess
		state['new_score'] = self.new_score
		state['need_reward'] = self.need_reward
		state['guesses'] = self.guesses
		state['stage_num'] = self.stage_num
		state['stage_samples'] = self.stage_samples

		return state


	def applyReward(self, r):
		#print("IN APPLY REWARD")

		if len(self.stage_samples) == 0:
			self.need_reward = False
			return False


		isBest = False

		self.new_score = r

		self.stage_samples[-1]['y'] = r

		print("{}\t{}\t{}\t{}".format(len(self.guesses),self.stage_num,len(self.stage_samples),r))

		if self.new_score > self.best_score:
			self.best_guess = copy.deepcopy(self.new_guess)
			self.best_score = self.new_score

			isBest = True

			#print("\tnew best:", self.best_guess, self.best_score)


		self.guesses.append({'x':copy.deepcopy(self.new_guess), 'y':r})
		#self.guesses = self.guesses[-50:]

		self.need_reward = False

		return isBest


	def getNextGuess(self):
		#print("IN GET NEXT")
	
		assert(len(self.best_guess) >= 1)

		self.new_guess = self.getNextSpaceSample()

		self.new_score = None
		self.need_reward = True

		assert(len(self.new_guess) >= 1)

		#print("\tnew guess:", self.new_guess)

		return copy.deepcopy(self.new_guess)

		#return [[[1.0, 1.0], 0.4] for _ in range(6)]

	
	def getNextSpaceSample(self):

		# self.stage_num = 0
		# self.samples_per_stage = 5
		# self.stage_center = None
		# self.stage_samples = []

		def getSolutionDists(solution):
			# return min dist from other stage samples, dist from center
			sol_list = self.solutionToList(solution)
			minDist = float('inf')
			for s in self.stage_samples:
				d = dist(self.solutionToList(s['x']), sol_list)
				if d < minDist: minDist = d

			center_dist = dist(self.solutionToList(self.stage_samples[0]['x']), sol_list)
			return minDist, center_dist


		# check if this is the very first call
		if len(self.stage_samples) == 0: 
			assert(self.stage_num == 0 and self.stage_samples==[])
			#self.stage_center = getCenterSolution()
			self.stage_samples = [{'x':self.getCenterSolution()}] # 'y' will store score
			return self.stage_samples[-1]['x']


		# check if we just finished a stage
		if len(self.stage_samples) >= self.samples_per_stage:
			# increment stage num and get new center
			self.stage_num += 1
			self.stage_samples = [{'x':copy.deepcopy(self.best_guess), 'y':self.best_score}]

		# now find a sample within radius of stage_center as far from possible from other samples in same stage
		rScaling = max(self.maxForceX-self.minForceX, self.maxForceY-self.minForceY)
		radius = ((self.seqLen*2.*rScaling)**0.5)/(1.15**self.stage_num)
		#radius = ((self.seqLen*2.*rScaling)**0.5)/(self.stage_num+1)

		best_solution = copy.deepcopy(self.stage_samples[-1]['x'])
		best_dist = 0.# want to maximize distance from other stage samples

		for _ in range(2000):
			new_solution = self.modifySolution(best_solution, variation=min(1., radius), modTypes = [1, 3, 6, 7, 8])
			new_dist, new_center_dist = getSolutionDists(new_solution)
			if new_dist > best_dist and new_center_dist <= radius:
				best_solution = new_solution
				best_dist = new_dist

		# boy poke hand 

		#print("dist\t",best_dist)
		self.stage_samples.append({'x':best_solution})

		#print("dist/rad: ", 1.*best_dist/radius)
		#if best_dist < radius*0.85:
		#	self.samples_per_stage = len(self.stage_samples)
		#else:
		#	self.samples_per_stage += 1


		return self.stage_samples[-1]['x']




	def modifySolution(self, solution, variation = 1.0, modTypes=[0, 1, 2, 3, 6]):
		#print("IN MOD")

		#assert(len(solution) >= 1)

		
		#if random.random() < 0.2:
		#	return self.getRandomSolution()

		#return solution

		solution_cp = copy.deepcopy(solution)

		new_solution = []

		mType = random.choice(modTypes)#, 3, 4, 5]) #random.choice([1, 3])

		if mType == 0:

			for s in solution:
				#if random.random() < 0.6:
				#	new_solution.append(s)
				#else:

				force, duration = s
				#print("MOD:", force, duration)

				new_force = [bound(self.minForceX, self.maxForceX, force[0]+random.choice([0,0,0,-1,1])*random.random()**2),
							 bound(self.minForceY, self.maxForceY, force[1]+random.choice([0,0,0,-1,1])*random.random()**2)]
				#new_force = [0.1, 1.5]#random.choice([-0.5, 0., 0.5]), random.choice([-0.5, 0., 0.5])]

				new_duration = bound(self.minDuration, self.maxDuration, duration+random.randint(-1, 1)*random.random()**4)

				new_solution.append([new_force, new_duration])
		elif mType == 1:
			# push in some direction

			

			for i in range(len(solution)):

				biasVec = [rand(self.minForceX, self.maxForceX), rand(self.minForceY, self.maxForceY), rand(self.minDuration, self.maxDuration)]

				weight = random.choice([0., 1.])*min(variation, 1.) #max(0, random.random()*2. - 1.) #*0.5

				force, duration = solution[i]

				new_force_x = force[0]*(1.-weight) + biasVec[0]*weight
				new_force_y = force[1]*(1.-weight) + biasVec[1]*weight
				new_duration = duration*(1.-weight) + biasVec[2]*weight
				
				new_solution.append([[new_force_x, new_force_y], new_duration])

		elif mType == 2:

			# copy one action to multiple locations

			to_copy = random.choice(solution_cp)

			indices = range(len(solution_cp))
			random.shuffle(indices)

			new_solution = solution_cp
			for i in indices[:1]:
				new_solution[i] = to_copy


		elif mType == 3:

			# make one of the actions random

			biasVec = [rand(self.minForceX, self.maxForceX), rand(self.minForceY, self.maxForceY), rand(self.minDuration, self.maxDuration)]

			weight = variation #1.0 #random.random()*0.5

			new_solution = solution_cp

			index = random.randint(0, len(new_solution)-1)

			force, duration = solution[index]

			new_force_x = bound(self.minForceX, self.maxForceX, force[0]*(1.-weight) + biasVec[0]*weight)
			new_force_y = bound(self.minForceY, self.maxForceY, force[1]*(1.-weight) + biasVec[1]*weight)
			new_duration = bound(self.minDuration, self.maxDuration, duration*(1.-weight) + biasVec[2]*weight)
			
			new_solution[index] = [[new_force_x, new_force_y], new_duration]


		elif mType == 4:

			# invert x or y forces

			x_m = rand(-1., 1.)
			y_m = rand(-1., 1.)

			for s in solution_cp:

				force, duration = s

				new_force_x = force[0]*x_m
				new_force_y = force[1]*y_m
				
				new_duration = duration


				new_solution.append([[new_force_x, new_force_y], new_duration])


		elif mType == 5:
			#print("rotate")
			if random.random() < 0.5:
				new_solution = solution_cp[1:]+solution_cp[:1]
			else:
				new_solution = solution_cp[-1:]+solution_cp[:-1]

			#print("force, duration: ", new_force, new_duration)

		elif mType == 6:
			# add a symmetric change 

			biasVec = [rand(self.minForceX, self.maxForceX), rand(self.minForceY, self.maxForceY), rand(self.minDuration, self.maxDuration)]

			weight = variation #1.0 #random.random()*0.5

			new_solution = solution_cp

			index_1 = random.randint(0, len(new_solution)-1)
			index_2 = random.randint(0, len(new_solution)-1)

			force, duration = solution[index_1]

			new_force_x = force[0]*(1.-weight) + biasVec[0]*weight
			new_force_y = force[1]*(1.-weight) + biasVec[1]*weight
			new_duration = duration*(1.-weight) + biasVec[2]*weight
			
			new_solution[index_1] = [[new_force_x, new_force_y], new_duration]


			force, duration = solution[index_2]

			new_force_x = force[0]*(1.-weight) - biasVec[0]*weight
			new_force_y = force[1]*(1.-weight) - biasVec[1]*weight
			new_duration = duration*(1.-weight) + biasVec[2]*weight
			
			new_solution[index_2] = [[new_force_x, new_force_y], new_duration]
		
		elif mType == 7:
			# insert a move between two, replace one at either end

			newMove = self.getRandomAction() #random.choice(solution_cp) #

			index = random.randint(0, self.seqLen)

			solution_cp = solution_cp[:index]+[newMove]+solution_cp[index:]

			if index == 0:
				solution_cp = solution_cp[:-1]
			elif index == self.seqLen:
				solution_cp = solution_cp[1:]
			else:
				if random.random() < 0.5:
					solution_cp = solution_cp[:-1]
				else:
					solution_cp = solution_cp[1:]

			new_solution = solution_cp

		elif mType == 8:

			# decrease agnitude of random action

			biasVec = [0., 0., rand(self.minDuration, self.maxDuration)]

			weight = 0.5 #1.0 #random.random()*0.5

			new_solution = solution_cp

			index = random.randint(0, len(new_solution)-1)

			force, duration = solution[index]

			new_force_x = bound(self.minForceX, self.maxForceX, force[0]*(1.-weight) + biasVec[0]*weight)
			new_force_y = bound(self.minForceY, self.maxForceY, force[1]*(1.-weight) + biasVec[1]*weight)
			new_duration = bound(self.minDuration, self.maxDuration, duration*(1.-weight) + biasVec[2]*weight)
			
			new_solution[index] = [[new_force_x, new_force_y], new_duration]

		#print("\tMOD:", new_solution)

		assert(len(new_solution) >= 1)

		
		if random.random() < 0.2:
			return self.modifySolution(new_solution, variation = variation, modTypes=modTypes)
		else:
			return new_solution #




	def getRandomSolution(self, init_guess=False):
		s = []

		#if not init_guess:
		for _ in range(self.seqLen):
			s.append(self.getRandomAction(init_guess=init_guess))

		#else:

		#	r = self.getRandomAction(init_guess=init_guess)
		#	for _ in range(self.seqLen):
		#		s.append(r)

		return s

	def getRandomAction(self, init_guess=False):

		# random force and duration
		
		if init_guess:

			force = (rand(self.minForceX, self.maxForceX),
					 rand(0., self.maxForceY))
			
			#force = (random.choice([self.minForceX,self.minForceX*0.5, 0., self.maxForceX*0.5, self.maxForceX]),
			#		 random.choice([self.minForceY,self.minForceY*0.5, 0., self.maxForceY*0.5, self.maxForceY]))
			duration = rand(self.minDuration, self.maxDuration)

			return [force, duration]

		else:

			force = (rand(self.minForceX, self.maxForceX),
					 rand(self.minForceY, self.maxForceY))
			
			#force = (random.choice([self.minForceX,self.minForceX*0.5, 0., self.maxForceX*0.5, self.maxForceX]),
			#		 random.choice([self.minForceY,self.minForceY*0.5, 0., self.maxForceY*0.5, self.maxForceY]))
			duration = rand(self.minDuration, self.maxDuration)

			return [force, duration]


	def getCenterSolution(self):
		solution = []
		for _ in range(self.seqLen):
			midX = self.maxForceX*0.5+self.minForceX*0.5
			midY = self.maxForceY*0.5+self.minForceY*0.5
			midDur = self.maxDuration*0.5+self.minDuration*0.5
			solution.append([[midX, midY], midDur])
		return solution

	def solutionToList(self, solution):

		x = []
		for s in solution:
			x.extend(list(s[0]))
			x.append(s[1])

		return x

	def listToSolution(self, solution_list):

		solution = []

		for i in range(0, len(solution_list), 3):
			f_x = solution_list[i]
			f_y = solution_list[i+1]
			dur = solution_list[i+2]
			solution.append([[f_x, f_y], dur])

		return solution


	def reset(self):
		
		self.restarting = True

		self.guesses = []



		self.stage_num = 0
		self.stage_samples = []


		self.best_score = -float('inf')
		self.best_guess = self.getRandomSolution()
		
