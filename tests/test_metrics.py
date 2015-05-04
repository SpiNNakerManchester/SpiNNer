import pytest

from spinner import metrics
from spinner import topology
from spinner import transforms
from spinner import board


def test_wire_length():
	# Define *some* port locations
	wire_offsets = {
		topology.NORTH : (1,1),
		topology.SOUTH : (-1,-1),
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
	assert metrics.wire_length(boards, b, topology.NORTH) == 2.0
	# South wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, topology.SOUTH) == 2.0**0.5
	
	# Now while giving a non-applicable wire_offsets
	# North-East wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, topology.NORTH_EAST, wire_offsets) == \
		2.0**0.5
	# South-West wire (which reaches the chip above)
	assert metrics.wire_length(boards, b, topology.SOUTH_WEST, wire_offsets) == \
		2.0
	
	# Now while giving a applicable wire_offsets
	# North wire (which reaches the chip above)
	assert metrics.wire_length(boards, b, topology.NORTH, wire_offsets) == \
		2.0
	# South wire (which reaches the chip above-right)
	assert metrics.wire_length(boards, b, topology.SOUTH, wire_offsets) == \
		18**0.5


