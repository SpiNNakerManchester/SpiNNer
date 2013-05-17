#!/usr/bin/env python

"""
The representation of a board in a system.
"""

import topology


class Board(object):
	"""
	Represents a SpiNNaker board in a complete system.
	
	A board is an entity with links to its six neighbouring boards.
	"""
	
	def __init__(self):
		
		# References to other boards in the system which lie at the end of a wire
		# connected to a particular port.
		self.connection = {
			topology.NORTH      : None,
			topology.NORTH_EAST : None,
			topology.EAST       : None,
			topology.SOUTH      : None,
			topology.SOUTH_WEST : None,
			topology.WEST       : None,
		}
	
	
	def connect_wire(self, other, direction):
		"""
		Connect a wire between this board and another for the given direction.
		"""
		# Ensure it isn't already connected
		assert(self.follow_wire(direction) is None)
		assert(other.follow_wire(topology.opposite(direction)) is None)
		
		self.connection[direction] = other
		other.connection[topology.opposite(direction)] = self
	
	
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
			(topology.SOUTH_WEST, topology.EAST)       : topology.EAST,
			(topology.WEST,       topology.EAST)       : topology.NORTH_EAST,
			
			(topology.SOUTH_WEST, topology.NORTH_EAST) : topology.NORTH,
			(topology.SOUTH,      topology.NORTH_EAST) : topology.NORTH_EAST,
			
			(topology.SOUTH,      topology.NORTH)      : topology.WEST,
			(topology.EAST,       topology.NORTH)      : topology.NORTH,
		}
		# Opposite cases are simply inverted versions of the above...
		for (iws, pd), ows in out_sides.items():
			out_sides[( topology.opposite(iws)
			          , topology.opposite(pd)
			          )] = topology.opposite(ows)
		
		out_wire_side = out_sides[(in_wire_side, packet_direction)]
		
		return (topology.opposite(out_wire_side), self.follow_wire(out_wire_side))
		
	
	
	def __repr__(self):
		return "Board()"

