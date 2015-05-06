#!/usr/bin/env python

"""
Transformations on the coordinates to be applied to [(board, coord),...] lists.
"""

from operator import mul

from collections import defaultdict

from six import iteritems

from spinner import topology
from spinner import coordinates


def _assert_coord(boards, coordinate_types):
	"""
	Used Internally.
	
	Assert that the coordinates are for a Cartesian space (or that the set of
	boards is empty).
	"""
	assert(len(boards) == 0 or isinstance(boards[0][1], coordinate_types))


def hex_to_cartesian(boards):
	"""
	Convert hexagonal coordinates into 2D Cartesian coordinates maintaining the
	shape of the input. That is, feed in a mesh from board.create_torus() which
	looks like a rhombus and the resulting set of Cartesian coordinates will also
	look like a torus.
	"""
	_assert_coord(boards, coordinates.Hexagonal)
	
	return [ (board, topology.hex_to_cartesian(coord))
	         for (board, coord) in boards
	       ]


def hex_to_skewed_cartesian(boards):
	"""
	Convert hexagonal coordinates into 2D Cartesian coordinates skewing the input
	-30deg on the x-axis. That is, feed in a mesh from board.create_torus() which
	looks like a rhombus and the resulting set of Cartesian coordinates will look
	like a ragged rectangle.
	"""
	_assert_coord(boards, coordinates.Hexagonal)
	
	return [ (board, topology.hex_to_skewed_cartesian(coord))
	         for (board, coord) in boards
	       ]


def rhombus_to_rect(boards):
	r"""
	Performs a modulo max+1 for all coordinates. When given, for e.g., the rhombus
	arrangement of a toroid of 3-boards (e.g. from create_torus()) which has been
	mapped onto Cartesian coordinates turns it into a rectangle like so::
		
		_________         ___   ______             _________
		\        \        \  | |      \           |         |
		 \        \   -->  \ | |       \      --> |         |
		  \._______\        \| |._______\ .       |.________|
		   |                             /;\       |
		 (0,0)               \___________/       (0,0)
	"""
	_assert_coord(boards, (coordinates.Cartesian2D, coordinates.Cartesian3D))
	
	# Can't do anything with an empty input
	if len(boards) == 0:
		return []
	
	maxes = tuple(map(max, *(c for (b,c) in boards)))
	return [ (board, type(boards[0][1])(*(v%(m+1) for (v,m) in zip(c, maxes))))
	         for (board, c) in boards
	       ]


def compress(boards, x_div = 1, y_div = 2):
	r"""
	Compress coordinates, more precisely, does integer division on coordinates.
	This is useful for taking the hexagonal pattern in Cartesian coordinates and
	making it a more regular pattern like so::
		
		     ___     ___
		 ___/ 9 \___/11 \               +---+---+---+---+
		/ 8 \___/10 \___/               | 8 | 9 |10 |11 |
		\___/ 5 \___/ 7 \    ------\    +---+---+---+---+
		/ 4 \___/ 6 \___/    ------/    | 4 | 5 | 6 | 7 |
		\___/ 1 \___/ 3 \               +---+---+---+---+
		/ 0 \___/ 2 \___/               | 0 | 1 | 2 | 3 |
		\___/   \___/                   +---+---+---+---+
	
	Here, compress(x=1, y=2) takes all coordinates and maps them to (x/1, y/2)
	using integer division.
	"""
	_assert_coord(boards, coordinates.Cartesian2D)
	
	return [ (board, coordinates.Cartesian2D(int(x)//int(x_div), int(y)//int(y_div)))
	         for (board, (x,y)) in boards
	       ]


def flip_axes(boards):
	"""
	Invert the axes of the array of boards.
	
	Useful when attempting to cabinetise a grid which doesn't divide unless the
	axes are flipped.
	"""
	_assert_coord(boards, coordinates.Cartesian2D)
	
	return [ (board, coordinates.Cartesian2D(y, x))
	         for (board, (x, y)) in boards
	       ]


def fold(boards, folds):
	r"""
	Takes a set of Cartesian coordinates and folds into the number of segments
	specified for each dimension in folds. The folded segments are then
	interleaved. Below, fold(b, (2,1)) is shown::
		
		+---+---+---+---+          +---+---+---+---+
		| 8 | 9 |10 |11 |          | 8 |11 | 9 |10 |
		+---+---+---+---+  -----\  +---+---+---+---+
		| 4 | 5 | 6 | 7 |  -----/  | 4 | 7 | 5 | 6 |
		+---+---+---+---+          +---+---+---+---+
		| 0 | 1 | 2 | 3 |          | 0 | 3 | 1 | 2 |
		+---+---+---+---+          +---+---+---+---+
	"""
	_assert_coord(boards, (coordinates.Cartesian2D, coordinates.Cartesian3D))
	
	# Can't do anything with an empty input
	if len(boards) == 0:
		return []
	
	# Must have a number of folds and gaps for each dimension
	assert(len(boards[0][1]) == len(folds))
	
	maxes = tuple(map(max, *(c for (b,c) in boards)))
	
	# Use topology.fold_dimension() to get the fold number and multiply this by
	# the gap size to get an offset for each value.
	return [ (board, type(boards[0][1])(*[topology.fold_interleave_dimension(v,m+1,f)
	                                      for (v,m,f)
	                                      in zip(c, maxes, folds)]
	                                   ))
	         for (board, c) in boards
	       ]


def cabinetise(boards, num_cabinets, frames_per_cabinet, boards_per_frame = None):
	r"""
	Takes a set of Cartesian coordinates and maps them into a series of cabinets.
	Splits the system into columns, one per cabinet. Splits each column into rows,
	one per frame. These rows likely consist of several columns and rows in
	Cartesian space and so values are interleaved to yield a board allocation.
	
	If the width of the set of boards doesn't divide into the num_cabinets
	or the height doesn't divide into the number of frames_per_cabinet, the axes
	are flipped and tried again. If this doesn't solve the problem, a ValueError
	is raised.
	
	If boards_per_frame is given then an assertion checks that the number of boards
	is adequate.
	"""
	_assert_coord(boards, coordinates.Cartesian2D)
	
	# Can't do anything with an empty input
	if len(boards) == 0:
		return []
	
	max_x, max_y = map(max, *(c for (b,c) in boards))
	
	return [ (board, topology.cabinetise( (x,y)
	                                    , (max_x+1, max_y+1)
	                                    , num_cabinets
	                                    , frames_per_cabinet
	                                    , boards_per_frame
	                                    ))
	         for (board, (x,y)) in boards
	       ]


def remove_gaps(boards):
	"""
	Take a cabinetised system and shift boards right in their frames to remove any
	empty gaps between boards in frames.
	"""
	_assert_coord(boards, coordinates.Cabinet)
	
	# Initially collect together boards which share a frame
	# {(c, f): {b: Board, ...}, ...}
	frames = defaultdict(dict)
	for board, (c, f, b) in boards:
		frames[(c, f)][b] = board
	
	# Reconstruct the mapping one frame at a time, placing all baords into
	# contiguous blocks.
	boards = []
	for (c, f), rack_boards in iteritems(frames):
		# Renumber the boards in the frame
		b = 0
		for old_b, board in sorted(iteritems(rack_boards),
			                         key=(lambda tup: tup[0])):
			boards.append((board, coordinates.Cabinet(c, f, b)))
			b += 1
	return boards


def cabinet_to_physical(boards, cabinet):
	"""
	Takes Cabinet coordinates and converts them into Cartesian3D coordinates
	representing the physical positions of cabinets based on a
	spinner.cabinet.Cabinet specification.
	"""
	_assert_coord(boards, coordinates.Cabinet)
	
	return [(board, cabinet.get_position(*coord)) for (board,coord) in boards]
