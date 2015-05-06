#!/usr/bin/env python

"""
A representation of Boards linked by wires in a SpiNNaker system along with
utilities for creating systems of them and iterating over them.
"""

from six import iteritems

from spinner.topology import Direction, \
	threeboards, wrap_around, add_direction

from spinner import coordinates


class Board(object):
	"""
	Represents a SpiNNaker board in a complete system.
	
	A board is an entity with links to its six neighbouring boards.
	"""
	
	# Counter used to label boards
	NEXT_BOARD_ID = 0
	
	def __init__(self):
		
		# References to other boards in the system which lie at the end of a wire
		# connected to a particular port.
		self.connection = {
			Direction.north      : None,
			Direction.north_east : None,
			Direction.east       : None,
			Direction.south      : None,
			Direction.south_west : None,
			Direction.west       : None,
		}
		
		# Set the board's ID
		self.id = Board.NEXT_BOARD_ID
		Board.NEXT_BOARD_ID += 1
	
	
	def connect_wire(self, other, direction):
		"""
		Connect a wire between this board and another for the given direction.
		"""
		# Ensure it isn't already connected
		assert(self.follow_wire(direction) is None)
		assert(other.follow_wire(direction.opposite) is None)
		
		self.connection[direction] = other
		other.connection[direction.opposite] = self
	
	
	def follow_wire(self, direction):
		"""
		Follow the wire going in the given direction from this board.
		"""
		return self.connection[direction]
	
	
	def follow_packet(self, in_wire_side, packet_direction):
		"""
		Follow the path of a packet which entered in to the board via the wire
		in_wire_side following packet_direction through the chips in the board.
		Returns a tuple (next_in_wire_side, next_board).
		
		We only need to know the side on which the incoming link is on (not the
		exact chip) because for any incoming side there is a fixed outgoing side
		when travelling in a fixed direction.
		"""
		
		# Mapping of {(in_wire_side, packet_direction) : out_wire_side,...}
		out_sides = {
			(Direction.south_west, Direction.east)       : Direction.east,
			(Direction.west,       Direction.east)       : Direction.north_east,
			
			(Direction.south_west, Direction.north_east) : Direction.north,
			(Direction.south,      Direction.north_east) : Direction.north_east,
			
			(Direction.south,      Direction.north)      : Direction.west,
			(Direction.east,       Direction.north)      : Direction.north,
		}
		# Opposite cases are simply inverted versions of the above...
		for (iws, pd), ows in iteritems(out_sides.copy()):
			out_sides[( iws.opposite
			          , pd.opposite
			          )] = ows.opposite
		
		out_wire_side = out_sides[(in_wire_side, packet_direction)]
		
		return (out_wire_side.opposite, self.follow_wire(out_wire_side))
		
	
	def __repr__(self):
		return "<Board id={}>".format(self.id)



def create_torus(width = 1, height = None):
	"""
	Returns a mapping of boards containing width * height threeboards connected in
	a torus with corresponding hexagonal coordinates. If height is not specified,
	height = width.
	"""
	
	height = width if height is None else height
	
	boards = {}
	
	# Create the boards
	for coord in threeboards(width, height):
		boards[coordinates.Hexagonal(*coord)] = Board()
	
	# Link the boards together
	for coord in boards:
		for direction in [ Direction.east
		                 , Direction.north_east
		                 , Direction.north
		                 ]:
			# Get the coordinate of the neighbour in each direction
			n_coord = wrap_around(
			            add_direction(list(coord)+[0], direction), (width, height))
			
			# Connect the boards together
			boards[coord].connect_wire(boards[n_coord], direction)
	
	return [(b, c) for (c, b) in iteritems(boards)]
