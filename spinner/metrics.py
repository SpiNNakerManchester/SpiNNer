#!/usr/bin/env python

"""
A library of functions which calculate various metrics about systems of boards
and their wiring.
"""

import math

from spinner.topology import Direction

from spinner import coordinates


def wire_length(boards, board, direction, board_wire_offset=None):
	"""
	Returns the length of a wire leaving the specified board in a given direction.
	
	boards is a list [(board, coord),...)] where all coords support subtraction
	and magnitude() (such as those from the coordinates module).
	
	board is a board in that list
	
	direction is a wire direction to measure
	
	board_wire_offset is an (optional) dict {direction:offset,...} where the
	offset of each wire from the right-top-front corner of a board is supplied.
	This structure can be attained from a spinner.cabinet.Cabinet object.
	"""
	b2c = dict(boards)
	
	source = b2c[board]
	target = b2c[board.connection[direction]]
	
	# Up-cast the coordinates to 3D
	if len(source) == 2:
		source = coordinates.Cartesian3D(source[0], source[1], 0)
	if len(target) == 2:
		target = coordinates.Cartesian3D(target[0], target[1], 0)
	
	if board_wire_offset is not None:
		source += board_wire_offset[direction]
		target += board_wire_offset[direction.opposite]
	
	return (source - target).magnitude()


def wire_lengths(boards, direction=None, board_wire_offset=None):
	"""
	Generate a list of wire lengths for the supplied system.
	
	If direction is not given, lists wire lengths in all directions, otherwise
	lists only wires travelling in the specified direction.
	
	board_wire_offset is as defined for wire_length().
	"""
	if direction is not None:
		directions = [direction]
	else:
		directions = [Direction.north, Direction.north_east, Direction.east]
	
	for direction in directions:
		for board, coord in boards:
			yield wire_length(boards, board, direction, board_wire_offset)


def dimensions(boards):
	"""
	Return the width and height of the space occupied by the supplied set of
	boards.
	"""
	if len(boards) == 0:
		raise ValueError("Expected at least one board")
	
	return type(boards[0][1])(max(x for b, (x, y) in boards) + 1,
	                          max(y for b, (x, y) in boards) + 1)
