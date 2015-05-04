#!/usr/bin/env python

"""
A library of functions which calculate various metrics about systems of boards
and their wiring.
"""

import math

from spinner import topology
from spinner import coordinates


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
