import pytest

import fractions

from spinner.model import board
from spinner.model import topology


def lcm(a, b):
	"""
	Least common multiple
	"""
	return abs(a * b) / fractions.gcd(a,b) if a and b else 0


def follow_packet_loop(start_board, in_wire_side, direction): 
	""" 
	Follows the path of a packet entering on in_wire_side of start_board 
	travelling in the direction given. 
	 
	Yields a sequence of (in_wire_side, board) tuples starting with those 
	supplied. 
	""" 
	yield(in_wire_side, start_board) 
	in_wire_side, cur_board = start_board.follow_packet(in_wire_side, direction) 
	while cur_board != start_board: 
		yield(in_wire_side, cur_board) 
		in_wire_side, cur_board = cur_board.follow_packet(in_wire_side, direction) 


@pytest.mark.parametrize("w,h", [ (1,1), (2,2), (3,3), (4,4), # Square: odd & even
                                  (3,5), (5,3), # Rectangular: odd/odd
                                  (2,4), (4,2), # Rectangular: even/even
                                  (3,4), (4,3), # Rectangular: odd/even
                                  (1,4), (4,1), # 1-dimension: even
                                  (1,3), (3,1), # 1-dimension: odd
                                ])
def test_threeboard_packets(w, h):
	# Exhaustively check that packets travelling in each direction take the
	# correct number of hops to wrap back according to Simon Davidson's model.
	boards = board.create_torus(w, h)
	
	# Try starting from every board
	for start_board, start_coord in boards:
		# Try going in every possible direction
		for direction in [ topology.EAST
		                 , topology.NORTH_EAST
		                 , topology.NORTH
		                 , topology.WEST
		                 , topology.SOUTH_WEST
		                 , topology.SOUTH
		                 ]:
			# Packets can enter when travelling in direction from the side with the
			# opposite label and one counter-clockwise from that.
			for entry_point in [topology.opposite(direction)
			                   , topology.next_ccw(topology.opposite(direction))
			                   ]:
				num_boards = len(list(follow_packet_loop(start_board, entry_point, direction)))
				# For every threeboard traversed, the number of chips traversed is 3*l
				# where l is the number of rings in the hexagon. Travelling in one
				# direction we pass through a threeboard every two boards traversed so
				# the number of nodes traversed is num_nodes*l where num_hops is given
				# as below.
				num_nodes = (num_boards/2) * 3
				
				# The principal axis is south to north, i.e. along the height in
				# threeboards. This should have 3*l*h nodes along its length.
				if direction in (topology.NORTH, topology.SOUTH):
					assert num_nodes == h*3
				
				# The major axis is east to west, i.e. along the width in
				# threeboards. This should have 3*l*w nodes along its length.
				if direction in (topology.EAST, topology.WEST):
					assert num_nodes == w*3
				
				# The minor axis is norht-east to south-west, i.e. diagonally across
				# the mesh of threeboards. This should have 3*l*lcm(w,h) nodes along
				# its length.
				if direction in (topology.NORTH_EAST, topology.SOUTH_WEST):
					assert num_nodes == lcm(w,h)*3


def test___repr__():
	b0 = board.Board()
	b1 = board.Board()
	
	# Should contain the type name
	assert "Board" in repr(b0)
	
	# Should contain the unique ID in repr
	assert repr(b0) != repr(b1)
