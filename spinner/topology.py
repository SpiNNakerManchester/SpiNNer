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

from enum import IntEnum

from spinner import coordinates

################################################################################
# Directions
################################################################################

class Direction(IntEnum):
	east       = 0
	north_east = 1
	north      = 2
	west       = 3
	south_west = 4
	south      = 5
	
	@property
	def next_ccw(self):
		"""
		Returns the next direction counter-clockwise from the given direction.
		"""
		return Direction((self + 1) % 6)
	
	@property
	def next_cw(self):
		"""
		Returns the next direction clockwise from the given direction.
		"""
		return Direction((self - 1) % 6)
	
	@property
	def opposite(self):
		"""
		Returns the opposite direction.
		"""
		return Direction((self + 3) % 6)
	
	@property
	def vector(self):
		"""
		Returns the vector which moves one unit in the given direction.
		"""
		return _DIRECTION_VECTORS[self]

_DIRECTION_VECTORS = {
	Direction.east:       ( 1, 0, 0),
	Direction.west:       (-1, 0, 0),
	Direction.north:      ( 0, 1, 0),
	Direction.south:      ( 0,-1, 0),
	Direction.north_east: ( 0, 0,-1),
	Direction.south_west: ( 0, 0, 1),
}


################################################################################
# Coordinates in hexagon world :)
################################################################################

def add_direction(vector, direction):
	"""
	Returns the vector moved one unit in the given direction.
	"""
	return coordinates.Hexagonal(*(v + a for (v,a) in zip(vector, direction.vector)))


def manhattan(vector):
	"""
	Calculate the Manhattan distance required to traverse the given vector.
	"""
	return sum(map(abs, vector))


def median_element(values):
	"""
	Returns the value of the median element of the set.
	"""
	return sorted(values)[len(values)//2]


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
	fold_width = (w+(f-1)) // f
	
	new_x = x % fold_width
	fold  = x // fold_width
	
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


def cabinetise(coord, bounds, num_cabinets, frames_per_cabinet, boards_per_frame = None):
	r"""
	Takes a set of Cartesian coordinates and maps them into a series of cabinets.
	Splits the system into columns, one per cabinet. Splits each column into rows,
	one per frame. These rows likely consist of several columns and rows in
	Cartesian space and so values are interleaved to yield a board allocation.
	
	If the width of the set of boards doesn't divide into the num_cabinets
	or the height doesn't divide into the number of frames_per_cabinet, the axes
	are flipped and tried again. If this doesn't solve the problem, a ValueError
	is raised.
	
	coord is an (x,y) tuple containing the coordinate to map
	
	bounds is a (w,h) tuple containing the width and height of the Cartesian space
	
	If boards_per_frame is given then an assertion checks that the number of boards
	is adequate.
	
	Returns a tuple (cabinet, frame, board).
	"""
	
	x, y = coord
	w, h = bounds
	
	# If not divisible, try flipping the axes
	if w % num_cabinets != 0 or h % frames_per_cabinet != 0:
		y, x = x, y
		h, w = w, h
	
	# If still not divisible into cabinets and frames, fail.
	if w % num_cabinets != 0 or h % frames_per_cabinet != 0:
		raise ValueError("Cannot directly map boards into cabinets.")
	
	cols_per_cabinet = w // num_cabinets
	rows_per_frame   = h // frames_per_cabinet
	
	cabinet = x // cols_per_cabinet
	frame   = y // rows_per_frame
	
	# Sub coordinate within the frame
	x %= cols_per_cabinet
	y %= rows_per_frame
	
	# Interleave into board number
	board = y + (rows_per_frame * x)
	
	# Sanity check the position is actually within the system.
	assert(board < boards_per_frame)
	assert(frame < frames_per_cabinet)
	assert(cabinet < num_cabinets)
	
	return coordinates.Cabinet(cabinet, frame, board)



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
