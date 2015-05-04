#!/usr/bin/env python

"""
A library of functions which calculate various metrics about systems of boards
and their wiring.
"""

import math

from spinner.model import topology
from spinner.model import coordinates


def wire_length(boards, board, direction, wire_offsets={}):
	"""
	Returns the length of a wire leaving the specified board in a given direction.
	
	boards is a list [(board, coord),...)] where all coords support subtraction
	and magnitude() (such as those from the coordinates module).
	
	board is a board in that list
	
	direction is a wire direction to measure
	
	wire_offsets is an (optional) dict {direction:offset,...} where the offset
	supplied for each direction.
	"""
	b2c = dict(boards)
	source = b2c[board]
	target = b2c[board.connection[direction]]
	
	if direction in wire_offsets:
		source += wire_offsets[direction]
	if topology.opposite(direction) in wire_offsets:
		target += wire_offsets[topology.opposite(direction)]
	
	return (source - target).magnitude()



def physical_wire_length(distance, available_wire_lengths, minimum_arc_height):
	"""
	Returns (wire_length, arc_height) for a wire required to span a given
	distance. The wire length is the length of wire chosen from
	available_wire_lengths. The arc-height is the height of the arc of cable
	between the sockets.
		
		          wire_length           -+-
		         , - ~ ~ ~ - ,           |
		     , '               ' ,       | arc_height = r * (1 - cos(alpha/2))
		---:--------distance-------:--- -+-
		  ,  .                   .  ,    |
		 ,      .  ,-'''''-,  .      ,   | r * cos(alpha/2)
		 ,        '. alpha .'   r    ,   |
		 ,             o             ,  -+-
		  ,                         ,
		   ,                       ,
		     ,                  , '
		       ' - , _ _ _ ,  '
		
		distance**2 / (2*wire_length**2) == (1 - cos(alpha)) / alpha**2
	
	
	distance is a crow-flies distance between the sockets to be connected.
	
	available_wire_lengths is a list of available wire lengths
	
	minimum_arc_height is the minimum height of the arc to be allowed.
	"""
	# Select the shortest wire possible for the job
	for wire_length in sorted(available_wire_lengths):
		# Skip wire lengths which are obviously too short
		if wire_length < distance:
			continue
		
		if wire_length >= (distance*math.pi)/2.0:
			# If the wire is too long to make an arc with angle<pi, make a semicircle
			# offset by some fixed distance
			semicircle_length = (distance*math.pi)/2.0
			offset = (wire_length - semicircle_length)/2.0
			arc_height = offset + (distance/2.0)
		else:
			lhs = (distance**2.0 / (2.0*wire_length**2))
			rhs = lambda alpha: (1.0 - math.cos(alpha))/(alpha**2)
			
			# Perform a binary search to find the value of alpha which gets
			# close-enough. Note that rhs is monotonically decreasing as alpha
			# increases.
			max_error = 0.0001
			low = 0.0
			high = math.pi
			while True:
				alpha = (high+low)/2.0
				error = rhs(alpha) - lhs
				if abs(error) < max_error:
					break
				elif error < 0.0:
					high = alpha
				else:
					low = alpha
			
			r = wire_length/alpha
			
			arc_height = r*(1.0 - math.cos(alpha/2.0))
		
		# Try again if this wire results in too-tight an connection
		if arc_height < minimum_arc_height:
			continue
		
		return (wire_length, arc_height)
	
	raise Exception("No wire is long enough to span a %fm gap."%distance)

