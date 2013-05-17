#!/usr/bin/env python

"""
A model of a SpiNNaker system's boards and their positions.

Generally sets of boards are represented as a list [(board, position), ...]
where position is a coordinate in some coordinate system.
"""

import topology

from board import Board



def create_threeboards(width = 1, height = None):
	"""
	Returns a set boards containing width x height threeboards. If height is not
	specified, height = width. Links the boards together in a torus.
	"""
	
	height = width if height is None else height
	
	boards = {}
	
	# Create the boards
	for coord in topology.threeboards(width, height):
		boards[coord] = Board()
	
	# Link the boards together
	for coord in boards:
		for direction in [ topology.EAST
		                 , topology.NORTH_EAST
		                 , topology.NORTH
		                 ]:
			# Get the coordinate of the neighbour in each direction
			n_coord = topology.to_xy(
			            topology.wrap_around(
			              topology.add_direction(list(coord)+[0], direction), (width, height)))
			
			# Connect the boards together
			boards[coord].connect_wire(boards[n_coord], direction)
	
	return [(b, c) for (c, b) in boards.iteritems()]


def follow_wiring_loop(start_board, direction):
	"""
	Follows the 'direction' edge until it gets back to the starting board. Yields
	each board along the way.
	
	Generates a sequence of boards that were traversed.
	"""
	yield(start_board)
	cur_board = start_board.follow_wire(direction)
	while cur_board != start_board:
		yield(cur_board)
		cur_board = cur_board.follow_wire(direction)


def follow_packet_loop(start_board, in_wire_side, direction):
	"""
	Follows the path of a packet entering on in_wire_side of start_board
	travelling in the direction given.
	
	Generates a sequence of (in_wire_side, board) tuples that were traversed.
	"""
	yield(in_wire_side, start_board)
	in_wire_side, cur_board = start_board.follow_packet(in_wire_side, direction)
	while cur_board != start_board:
		yield(in_wire_side, cur_board)
		in_wire_side, cur_board = cur_board.follow_packet(in_wire_side, direction)


def compress_layout(boards):
	"""
	Takes a layout with entries spaced out on the x and y axes and compresses them
	to take up minimal width.
	"""
	out = []
	
	boards = [(b,(x,y/2)) for (b,(x,y)) in boards]
	
	cur_row = None
	cur_col = None
	for board, coords in sorted(boards, key=(lambda (b,c): (c[1], c[0]))):
		if cur_row != coords[1]:
			cur_row = coords[1]
			cur_col = 0
		out.append((board, (cur_col, cur_row)))
		cur_col += 1
	
	return out


