#!/usr/bin/env python

"""
Transformations on the coordinates to be applied to [(board, coord),...] lists.
"""

import topology
import coordinates


def hex_to_cartesian(boards):
	"""
	Convert hexagonal coordinates into 2D Cartesian coordinates maintaining the
	shape of the input. That is, feed in a mesh from board.create_torus() which
	looks like a rhombus and the resulting set of Cartesian coordinates will also
	look like a torus.
	"""
	# Assert that the coordinates are for a hexagonal space.
	assert(len(boards) == 0 or isinstance(boards[0][1], coordinates.Hexagonal))
	
	return [ (board, coordinates.Cartesian2D(topology.hex_to_cartesian(coord)))
	         for (board, coord) in boards
	       ]


def hex_to_skewed_cartesian(boards):
	"""
	Convert hexagonal coordinates into 2D Cartesian coordinates skewing the input
	-30deg on the x-axis. That is, feed in a mesh from board.create_torus() which
	looks like a rhombus and the resulting set of Cartesian coordinates will look
	like a ragged rectangle.
	"""
	# Assert that the coordinates are for a hexagonal space.
	assert(len(boards) == 0 or isinstance(boards[0][1], coordinates.Hexagonal))
	
	return [ (board, coordinates.Cartesian2D(topology.hex_to_skewed_cartesian(coord)))
	         for (board, coord) in boards
	       ]
