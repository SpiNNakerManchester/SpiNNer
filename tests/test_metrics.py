import pytest

from spinner import metrics
from spinner import transforms
from spinner import board
from spinner import coordinates

from spinner.topology import Direction

from math import pi, sin, cos


def test_wire_lengths():
	"""Test with a few singleton examples to check the arithmetic."""
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
	
	# Place board (0, 0) at the start of the list as this is the board we're
	# interested in below.
	for b, c in boards:
		if c == (0, 0):
			boards.remove((b, c))
	boards.insert(0, (b, c))
	
	# North wire (which reaches the chip above)
	assert list(metrics.wire_lengths(boards, Direction.north))[0] == 2.0
	# South wire (which reaches the chip above-right)
	assert list(metrics.wire_lengths(boards, Direction.south))[0] == 2.0**0.5
	
	# Now while giving a non-applicable wire_offsets
	# North-East wire (which reaches the chip above-right)
	assert list(metrics.wire_lengths(boards, Direction.north_east, wire_offsets))[0] == \
		2.0**0.5
	# South-West wire (which reaches the chip above)
	assert list(metrics.wire_lengths(boards, Direction.south_west, wire_offsets))[0] == \
		2.0
	
	# Now while giving a applicable wire_offsets
	# North wire (which reaches the chip above)
	assert list(metrics.wire_lengths(boards, Direction.north, wire_offsets))[0] == \
		2.0
	# South wire (which reaches the chip above-right)
	assert list(metrics.wire_lengths(boards, Direction.south, wire_offsets))[0] == \
		18**0.5
	
	# Test with 3D coordinates (just sets z to x+y)
	boards_3D = [(b, coordinates.Cartesian3D(c[0], c[1], c[0]+c[1]))
	             for (b, c) in boards]
	assert list(metrics.wire_lengths(boards_3D, Direction.north))[0] == \
		8**0.5
	assert list(metrics.wire_lengths(boards_3D, Direction.north, wire_offsets))[0] == \
		8**0.5


def test_wire_lengths_multiple():
	"""Test multiple boards can be fed into the wire_lengths function."""
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


@pytest.mark.parametrize("distance,min_slack,"
                         "exp_wire_length,exp_slack",
                         [# Zero-length
                          (0.0, 0.0, 0.15, 0.15),
                          # Zero-slack
                          (0.15, 0.0, 0.15, 0.0),
                          (0.30, 0.0, 0.30, 0.0),
                          (0.50, 0.0, 0.50, 0.0),
                          (1.00, 0.0, 1.00, 0.0),
                          # General case.
                          (0.10, 0.04, 0.15, 0.05),
                          (0.01, 0.05, 0.15, 0.14),
                          (0.20, 0.05, 0.30, 0.10),
                         ])
def test_physical_wire_length_cases(distance, min_slack,
                                    exp_wire_length, exp_slack):
	"""Test a few specific cases of wire length to check basic behaviour."""
	wire_length, slack = metrics.physical_wire_length(
		distance, [0.15, 0.3, 0.5, 1.0], min_slack)
	
	assert abs(wire_length - exp_wire_length) < 0.0001
	assert abs(slack - exp_slack) < 0.0001

def test_physical_wire_length_fail():
	with pytest.raises(ValueError):
		metrics.physical_wire_length(2.0, [1.0], 0.0)

@pytest.mark.parametrize("distance,wire_lengths,min_slack",
                         [# No wire lengths provided
                          (0.0, [], 0.0),
                          # Longest wire is too short
                          (0.5, [0.4], 0.0),
                          # Longest wire is too tight
                          (0.5, [0.5], 0.1),
                         ])
def test_physical_wire_length_impossible(distance, wire_lengths,
                                         min_slack):
	"""Check that impossible situations yield an error."""
	with pytest.raises(ValueError):
		metrics.physical_wire_length(distance, wire_lengths, min_slack)


@pytest.mark.parametrize("bins,exp_bin_counts",
                         [# Automatically bin
                          (10, {float(n+1): n+1 for n in range(10)}),
                          # Single bin
                          (1, {10.0: sum(n+1 for n in range(10))}),
                          # Manual binning
                          ([5.0, 10.0], {5.0: 1+2+3+4+5,
                                         10.0: 6+7+8+9+10}),
                         ])
def test_wire_length_histogram(bins, exp_bin_counts):
	test_case = sum([[n+1]*(n+1) for n in range(10)], [])
	
	bin_counts, bin_min_slack, bin_max_slack =\
		metrics.wire_length_histogram(test_case, 0.0, bins)
	
	# Make sure expected result appears
	assert bin_counts == exp_bin_counts
	
	# Slacks should be populated for each bin
	assert set(bin_counts) == set(bin_min_slack)
	assert set(bin_counts) == set(bin_max_slack)


def test_wire_length_histogram_bad():
	# Fail if bin sizes not sufficient
	with pytest.raises(ValueError):
		metrics.wire_length_histogram([1.0], 0.0, [0.5])
	
	# Fail if slack is not met
	with pytest.raises(ValueError):
		metrics.wire_length_histogram([1.0], 0.5, [1.0])


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
