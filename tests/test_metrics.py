import pytest

from spinner import metrics
from spinner import transforms
from spinner import board
from spinner import coordinates

from spinner.topology import Direction


def test_wire_length():
	# Define *some* port locations
	wire_offsets = {
		Direction.north_east : (0, 0, 0),
		Direction.south_west : (0, 0, 0),
		Direction.east : (0, 0, 0),
		Direction.west : (0, 0, 0),
		Direction.north : (1, 1, 0),
		Direction.south : (-1, -1, 0),
	}
	
	# Get a single three-board like this
	#
	#  (0,2)
	#        (1,1)
	#  (0,0)
	boards = transforms.hex_to_cartesian(board.create_torus(1))
	
	c2b = dict((c,b) for (b,c) in boards)
	
	# Pick the board at (0,0)
	b = c2b[(0,0)]
	
	# North wire (which reaches the chip above)
	assert metrics.wire_length(boards, b, Direction.north) == 2.0
	# South wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, Direction.south) == 2.0**0.5
	
	# Now while giving a non-applicable wire_offsets
	# North-East wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, Direction.north_east, wire_offsets) == \
		2.0**0.5
	# South-West wire (which reaches the chip above)
	assert metrics.wire_length(boards, b, Direction.south_west, wire_offsets) == \
		2.0
	
	# Now while giving a applicable wire_offsets
	# North wire (which reaches the chip above)
	assert metrics.wire_length(boards, b, Direction.north, wire_offsets) == \
		2.0
	# South wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, Direction.south, wire_offsets) == \
		18**0.5
	
	# Test with 3D coordinates (just sets z to x+y)
	boards_3D = [(b, coordinates.Cartesian3D(c[0], c[1], c[0]+c[1]))
	             for (b, c) in boards]
	c2b_3D = dict((c,b) for (b,c) in boards_3D)
	metrics.wire_length(boards_3D, c2b_3D[(0,0,0)], Direction.north) == \
		8**0.5
	metrics.wire_length(boards_3D, c2b_3D[(0,0,0)], Direction.north, wire_offsets) == \
		8**0.5


def test_wire_lengths():
	# Get a single three-board like this
	#
	#  (0,2)
	#        (1,1)
	#  (0,0)
	boards = transforms.hex_to_cartesian(board.create_torus(1))
	
	assert sorted(metrics.wire_lengths(boards, Direction.north)) == sorted([
		# 0.0 
		2.0,     # North
		# 1,1
		2**0.5,  # North
		# 0,2
		2**0.5,  # North
	])


def test_dimensions():
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	
	c = coordinates.Cartesian2D
	
	# Fail with no arguments
	with pytest.raises(ValueError):
		metrics.dimensions([])
	
	# Singleton case
	assert metrics.dimensions([(o0, c(0, 0))]) == c(1, 1)
	assert metrics.dimensions([(o0, c(1, 0))]) == c(2, 1)
	assert metrics.dimensions([(o0, c(0, 1))]) == c(1, 2)
	assert metrics.dimensions([(o0, c(1, 1))]) == c(2, 2)
	
	# Multiple objects
	assert metrics.dimensions([(o0, c(0, 0)),
	                           (o1, c(1, 0)),
	                           (o2, c(0, 1))]) == c(2, 2)

@pytest.mark.parametrize("coord_a,coord_b,counts",
                         [((0,0,0), (0,0,1), (0,0,2)),
                          ((0,0,1), (0,1,1), (0,2,0)),
                          ((0,0,0), (0,1,1), (0,2,0)),
                          ((0,1,1), (1,1,1), (2,0,0)),
                          ((0,1,0), (1,1,1), (2,0,0)),
                          ((0,0,1), (1,1,1), (2,0,0)),
                          ((0,0,0), (1,1,1), (2,0,0)),
                         ])
def test_count_wires(coord_a, coord_b, counts):
	# Set up a system with two boards connected via North links only.
	boards = [(board.Board(), coordinates.Cabinet(*coord_a)),
	          (board.Board(), coordinates.Cabinet(*coord_b))]
	boards[0][0].connect_wire(boards[1][0], Direction.north)
	boards[1][0].connect_wire(boards[0][0], Direction.north)
	
	assert metrics.count_wires(boards, Direction.north) == counts
