from __future__ import print_function

import math
import random

def rand(m, M):
	r = random.random()*(M-m) + m
	return r

def minDistToPoints(point, points):

	minDist = float('inf')

	for p in points:

		d = dist(p, point)
		if d <= minDist:
			minDist = d


	return minDist

def chunk(input, size):
	return map(None, *([iter(input)] * size))


def interpolateN(values, centers, v):

	if len(values) == 1:
		return values[0]
	elif len(values) == 0:
		return 0

	# centers must be sorted

	if v < min(centers): v = min(centers)

	if v > max(centers): v = max(centers)

	# figure out which range v is in
	r = (0,1)
	rIndex=0
	for i in range(len(centers)-1):
		m = centers[i]
		M = centers[i+1]

		if v >= m and v <= M:
			r = (m, M)
			rIndex=i
			break

	# now just return the shade in that range
	vp = (1.0*v - 1.0*r[0])/(1.0*r[1]-1.0*r[0])
	return interpolate(values[rIndex], values[rIndex+1], vp)

def interpolateNVec(values, centers, v):

	if len(values) == 1:
		return values[0]
	elif len(values) == 0:
		return 0

	# centers must be sorted

	if v < min(centers): v = min(centers)

	if v > max(centers): v = max(centers)

	# figure out which range v is in
	r = (0,1)
	rIndex=0
	for i in range(len(centers)-1):
		m = centers[i]
		M = centers[i+1]

		if v >= m and v <= M:
			r = (m, M)
			rIndex=i
			break

	# now just return the shade in that range
	vp = (1.0*v - 1.0*r[0])/(1.0*r[1]-1.0*r[0])
	return blend(values[rIndex], values[rIndex+1], vp)

def interpolate(v1, v2, frac):
	newC = v1*(1.-frac) + v2*frac
	return newC

def blend(C1, C2, frac):
	newC = [interpolate(v1, v2, frac) for v1, v2 in zip(C1, C2)]
	return newC

def bound(m, M, v):
	return max(min(v, M), m)

def dist(p1, p2):
	return sum([(a-b)**2 for a, b in zip(p1, p2)])**0.5

def toHex(cvec):

	rgb = tuple([int(255*v) for v in cvec])

	return '#%02x%02x%02x' % rgb