#!/usr/bin/env python

"""
Utilities for working with coordinates of various types, notably ones in
hexagonal space.

Contains:

  * Constants/Functions for directions in the space that the chips/boards sit.
  * Constants for identifying edges of a hexagon of chips (uses same functions
    as directions)
  * Functions for addressing in a hexagonal world.
  * Functions for generating arrangements of hexagons.
  * Functions for Generation arrangements of spinnaker boards
  * Functions for transforming Cartesian coordinates
  * Functions for working with cabinets

This uses the hexagonal addressing scheme suggested in

	Addressing and Routing in Hexagonal Networks with Applications for Tracking
	Mobile Users and Connection Rerouting in Cellular Networks by Nocetti et. al.
"""

import coordinates

################################################################################
# Directions
################################################################################

EAST       = 0
NORTH_EAST = 1
NORTH      = 2
WEST       = 3
SOUTH_WEST = 4
SOUTH      = 5


def next_ccw(direction):
	"""
	Returns the next direction counter-clockwise from the given direction.
	"""
	return (direction+1)%6


def next_cw(direction):
	"""
	Returns the next direction counter-clockwise from the given direction.
	"""
	return (direction-1)%6


def opposite(direction):
	"""
	Returns the opposite direction
	"""
	return (direction+3)%6


################################################################################
# Coordinates in hexagon world :)
################################################################################

def add_direction(vector, direction):
	"""
	Returns the vector moved one unit in the given direction.
	"""
	add = {
		EAST:       ( 1, 0, 0),
		WEST:       (-1, 0, 0),
		NORTH:      ( 0, 1, 0),
		SOUTH:      ( 0,-1, 0),
		NORTH_EAST: ( 0, 0,-1),
		SOUTH_WEST: ( 0, 0, 1),
	}
	
	return coordinates.Hexagonal(*(v + a for (v,a) in zip(vector, add[direction])))


def manhattan(vector):
	"""
	Calculate the Manhattan distance required to traverse the given vector.
	"""
	return sum(map(abs, vector))


def median_element(values):
	"""
	Returns the value of the median element of the set.
	"""
	return sorted(values)[len(values)/2]


def to_shortest_path(vector):
	"""
	Converts a vector into the shortest-path variation.
	
	A shortest path has at least one dimension equal to zero and the remaining two
	dimensions have opposite signs (or are zero).
	"""
	assert(len(vector) == 3)
	
	# The vector (1,1,1) has distance zero so this can be added or subtracted
	# freely without effect on the destination reached. As a result, simply
	# subtract the median value from all dimensions to yield the shortest path.
	median = median_element(vector)
	return coordinates.Hexagonal(*(v - median for v in vector))


def to_xy(vector):
	"""
	Takes a 3D vector and returns the equivalent 2D version.
	"""
	return coordinates.Hexagonal2D(vector[0] - vector[2], vector[1] - vector[2])


def hex_to_cartesian(coords):
	"""
	Convert a set of hexagonal coordinates into equivalent (for presentation
	purposes) Cartesian values.
	"""
	
	old_x, old_y = to_xy(coords)
	
	new_x = old_x
	new_y = (old_y * 2) - old_x
	
	return coordinates.Cartesian2D(new_x, new_y)


def board_to_chip(coords, layers = 4):
	"""
	Convert a hexagonal board coordinate into a hexagonal chip coordinate for the
	chip at the bottom-left of a board that size.
	"""
	x,y = hex_to_skewed_cartesian(coords)
	x *= layers
	y *= layers
	return coordinates.Hexagonal(x,y,0)


def hex_to_skewed_cartesian(coords):
	"""
	Convert a set of hexagonal coordinates into equivalent Cartesian values
	skewed to make x and y in the coordinate space match x and y in Cartesian
	space.
	"""
	
	old_x, old_y = to_xy(coords)
	
	new_x = old_x + old_y
	new_y = (old_y * 2) - old_x
	
	return coordinates.Cartesian2D(new_x, new_y)


def wrap_around(coord, bounds):
	"""
	Wrap the coordinate given around the edges of a torus made of hexagonal
	pieces. Assumes that the world is a NxM arrangement of threeboards (see
	threeboards function) with bounds = (N, M).
	
	XXX: Implementation could be nicer (and non iterative)...
	"""
	
	w,h = bounds
	x,y = to_xy(coord)
	
	assert(w > 0)
	assert(h > 0)
	
	while True:
		# Where is the coordinate relative to the world
		left  = x + y     < 0
		right = x + y     >= w*3
		below = (2*y) - x <  0
		above = (2*y) - x >= h*3
		
		if below and left:
			x += 1 + (w-1)*2 - (h-1)
			y += 2 + (w-1)   + (h-1)
			continue
		
		if above and right:
			x -= 1 + (w-1)*2 - (h-1)
			y -= 2 + (w-1)   + (h-1)
			continue
		
		if left:
			x += w*2
			y += w
			continue
		
		if right:
			x -= w*2
			y -= w
			continue
		
		if below:
			x -= h
			y += h
			continue
		
		if above:
			x += h
			y -= h
			continue
		
		break
	
	return coordinates.Hexagonal(x,y,0)




################################################################################
# Cartesian Coordinate Manipulations
################################################################################


def euclidean(v):
	"""
	The Euclidean distance represented by the given vector.
	"""
	return sum(x**2 for x in v) ** 0.5


def fold_dimension(x, w, f):
	r"""
	Takes a coordinate, x, on a single dimension of length w. Returns a tuple
	(new_x, fold) where new_x is the coordinate after the dimension has been
	folded into f pieces and fold is the fold number it is on.
	
	Input::
		
		 ______ w _____
		|              |
		-----+----------
		     |
		     x
		
		      | |
		     \| |/
		      \./
		
		new_x ___\__.\    f = 3
		          \/| \
		            |
		          fold
	"""
	# Width of the folded sections (round up so sections are bigger than
	# neccessary if not evenly divisible)
	fold_width = (w+(f-1)) / f
	
	new_x = x % fold_width
	fold  = x / fold_width
	
	# If on a reverse-facing fold, flip the coordinate
	if fold%2:
		# If this is the last fold, it may be smaller if not evenly divisible
		if fold == f - 1:
			new_x = (fold_width - ((fold_width*f) - w)) - new_x - 1
		else:
			new_x = fold_width - new_x - 1
	
	return (new_x, fold)


def fold_interleave_dimension(x, w, f):
	r"""
	As fold_dimension but returns a new x such that if the following points were
	folded, they would be mapped like so::
		
		 _______   ---\  (0,0) \  / (0,1)  ---\   _______
		 0 1 2 3   ---/   (1,0) \/ (1,1)   ---/   0 3 1 2
	
	That is, it interleaves points which would be mapped to the same position by
	fold_dimension.
	"""
	new_x, fold = fold_dimension(x,w,f)
	
	new_x *= f
	new_x += fold
	
	return new_x


################################################################################
# Cabinets
################################################################################


def cabinetise(coord, bounds, num_cabinets, racks_per_cabinet, slots_per_rack = None):
	r"""
	Takes a set of Cartesian coordinates and maps them into a series of cabinets.
	Splits the system into columns, one per cabinet. Splits each column into rows,
	one per rack. These rows likely consist of several columns and rows in
	Cartesian space and so values are interleaved to yield a slot allocation.
	
	coord is an (x,y) tuple containing the coordinate to map
	
	bounds is a (w,h) tuple containing the width and height of the Cartesian space
	
	If slots_per_rack is given then an assertion checks that the number of slots
	is adequate.
	
	Returns a tuple (cabinet, rack, slot).
	"""
	
	x, y = coord
	w, h = bounds
	
	# Must be divisible into cabinets
	assert(w % num_cabinets == 0)
	
	# Must be divisible into racks
	assert(h % racks_per_cabinet == 0)
	
	# Must be able to fit in the given number of slots.
	assert(slots_per_rack is None or
	       ((w * h)) / num_cabinets / racks_per_cabinet <= slots_per_rack)
	
	cols_per_cabinet = w / num_cabinets
	rows_per_rack    = h / racks_per_cabinet
	
	cabinet = x / cols_per_cabinet
	rack    = y / rows_per_rack
	
	# Sub coordinate within the rack
	x %= cols_per_cabinet
	y %= rows_per_rack
	
	# Interleave into slot number
	slot = y + (rows_per_rack * x)
	
	return coordinates.Cabinet(cabinet, rack, slot)



################################################################################
# Hexagon Generation
################################################################################

def hexagon(layers = 4):
	"""
	Generator which produces a list of (x,y) tuples which produce a hexagon of the
	given number of layers.
	
	Try me::
	
		points = set(hexagon(4))
		for y in range(min(y for (x,y) in points), max(y for (x,y) in points) + 1)[::-1]:
			for x in range(min(x for (x,y) in points), max(x for (x,y) in points) + 1):
				if (x,y) in points:
					print "#",
				else:
					print " ",
			print
	"""
	
	X,Y,Z = 0,1,2
	
	next_position = [0,0,0]
	
	for n in range(layers):
		for _ in range(n):
			yield to_xy(next_position)
			next_position[Y] -= 1
		
		for _ in range(n):
			yield to_xy(next_position)
			next_position[Z] += 1
		
		for _ in range(n+1):
			yield to_xy(next_position)
			next_position[X] -= 1
		
		for _ in range(n):
			yield to_xy(next_position)
			next_position[Y] += 1
		
		for _ in range(n+1):
			yield to_xy(next_position)
			next_position[Z] -= 1
		
		for _ in range(n+1):
			yield to_xy(next_position)
			next_position[X] += 1


def hexagon_zero(layers = 4):
	"""
	As with hexagon except coordinates are given relative to the bottom-left
	coordinate of the hexagon.
	"""
	
	return ( coordinates.Hexagonal2D(x+layers, y+layers-1)
	         for (x,y) in hexagon(layers)
	       )




################################################################################
# Threeboard Generation
################################################################################


def threeboards(width = 1, height = None):
	r"""
	Generates a list of width x height threeboards. If height is not specified,
	height = width. Width defaults to 1. Coordinates are given as (x,y,0) tuples
	on a hexagonal coordinate system like so::
		
		
		    | y
		    |
		   / \
		z /   \ x
	
	A threeboard looks like so::
		
		   ___
		  / 1 \___
		  \___/ 2 \
		  / 0 \___/
		  \___/
	
	With the bottom-left hexagon being at (0,0).
	
	And is tiled in to long rows like so::
		
		   ___     ___     ___     ___
		  / 0 \___/ 1 \___/ 2 \___/ 3 \___
		  \___/ 0 \___/ 1 \___/ 2 \___/ 3 \
		  / 0 \___/ 1 \___/ 2 \___/ 3 \___/
		  \___/   \___/   \___/   \___/
	
	And into a mesh like so::
		
		   ___     ___     ___     ___
		  / 4 \___/ 5 \___/ 6 \___/ 7 \___
		  \___/ 4 \___/ 5 \___/ 6 \___/ 7 \
		  / 4 \___/ 5 \___/ 6 \___/ 7 \___/
		  \___/ 0 \___/ 1 \___/ 2 \___/ 3 \___
		      \___/ 0 \___/ 1 \___/ 2 \___/ 3 \
		      / 0 \___/ 1 \___/ 2 \___/ 3 \___/
		      \___/   \___/   \___/   \___/
	
	"""
	
	height = width if height is None else height
	
	# Create the boards
	for y in range(height):
		for x in range(width):
			# z is the index of the board within the set. 0 is the bottom left, 1 is
			# the top, 2 is the right
			for z in range(3):
				# Offset within threeboard --+
				# Y offset ---------+        |
				# X offset -+       |        |
				#           |       |        |
				x_coord = (x*2) + (-y) + (z >= 2)
				y_coord = (x  ) + ( y) + (z >= 1)
				yield coordinates.Hexagonal(x_coord,y_coord,0)


################################################################################
# Board to chip coordinate mapping
################################################################################

def board_xy_to_chip_xy(x,y, board_layers=4):
	"""
	Given the logical (x,y) coordinate of a board, return the (x,y) coordinate of
	the chip at the bottom-left corner of that board. Optionally takes the number
	of layers in the hexagonal arrangement of chips on a board.
	"""
	
