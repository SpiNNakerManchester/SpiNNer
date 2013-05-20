#!/usr/bin/env python

"""
Transformations on the coordinates to be applied to [(board, coord),...] lists.
"""

import topology
import coordinates


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
	
	return [ (board, topology.hex_to_skew_cartesian(coord))
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
	if len(boards):
		return []
	
	maxes = map(max, *(c for (b,c) in boards))
	
	return [ (board, type(boards[0][1])(v%(m+1) for (v,m) in zip(c, maxes)))
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
	
	return [ (board, coordinates.Cartesian2D(int(x)/int(x_div), int(y)/int(y_div)))
	         for (board, (x,y)) in boards
	       ]


def space_folds(boards, folds, gaps):
	r"""
	Takes a set of Cartesian coordinates and adds a gap where a fold would take
	place. Below, space_folds(b, (2,1), (2,0)) is shown::
		
		+---+---+---+---+          +---+---+        +---+---+
		| 8 | 9 |10 |11 |          | 8 | 9 |        |10 |11 |
		+---+---+---+---+  -----\  +---+---+        +---+---+
		| 4 | 5 | 6 | 7 |  -----/  | 4 | 5 |        | 6 | 7 |
		+---+---+---+---+          +---+---+        +---+---+
		| 0 | 1 | 2 | 3 |          | 0 | 1 |        | 2 | 3 |
		+---+---+---+---+          +---+---+        +---+---+
	"""
	_assert_coord(boards, (coordinates.Cartesian2D, coordinates.Cartesian3D))
	
	# Can't do anything with an empty input
	if len(boards):
		return []
	
	# Must have a number of folds and gaps for each dimension
	assert(len(boards[0][1]) == len(folds) == len(gaps))
	
	maxes = map(max, *(c for (b,c) in boards))
	
	# Use topology.fold_dimension() to get the fold number and multiply this by
	# the gap size to get an offset for each value.
	return [ ( board, type(board[0][1])( v + (g*topology.fold_dimension(v,m+1,f)[1])
	                                     for (v,m,f,g)
	                                     in zip(c, maxes, folds, gaps)
	                                   )
	         )
	         for (board, c) in boards
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
	if len(boards):
		return []
	
	# Must have a number of folds and gaps for each dimension
	assert(len(boards[0][1]) == len(folds) == len(gaps))
	
	maxes = map(max, *(c for (b,c) in boards))
	
	# Use topology.fold_dimension() to get the fold number and multiply this by
	# the gap size to get an offset for each value.
	return [ (board, type(board[0][1])( topology.fold_interleave_dimension(v,m+1,f)[1]
	                                    for (v,m,f)
	                                    in zip(c, maxes, folds)
	                                  ))
	         for (board, c) in boards
	       ]


def cabinetise(boards, num_cabinets, racks_per_cabinet, slots_per_rack = None):
	r"""
	Takes a set of Cartesian coordinates and maps them into a series of cabinets.
	Splits the system into columns, one per cabinet. Splits each column into rows,
	one per rack. These rows likely consist of several columns and rows in
	Cartesian space and so values are interleaved to yield a slot allocation.
	
	If slots_per_rack is given then an assertion checks that the number of slots
	is adequate.
	"""
	_assert_coord(boards, coordinates.Cartesian2D)
	
	# Can't do anything with an empty input
	if len(boards):
		return []
	
	max_x, max_y = map(max, *(c for (b,c) in boards))
	
	return [ (board, topology.cabinetise( (x,y)
	                                    , (max_x+1, max_y+1)
	                                    , num_cabinets
	                                    , racks_per_cabinet
	                                    , slots_per_rack
	                                    ))
	         for (board, (x,y)) in boards
	       ]


def cabinet_to_physical(boards, system):
	"""
	Takes Cabinet coordinates and converts them into Cartesian3D coordinates
	representing the physical positions of cabinets based on a cabinet.System()
	specification.
	"""
	_assert_coord(boards, coordinates.Cabinet)
	
	return [(board, system.get_position(coord)) for (board,coord) in boards]

