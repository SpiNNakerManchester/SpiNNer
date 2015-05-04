import pytest

from spinner.model import cabinet
from spinner.model import topology


@pytest.fixture
def b():
	"""A Board with just two wire positions defined."""
	return cabinet.Board((1,10,10), {topology.NORTH : (0.0,0.0,1.0)})


@pytest.fixture
def f(b):
	"""A frame with 10 boards.
	
	The bay should be centered with offset (2.75, 2.5, 0)
	"""
	return cabinet.Frame(b, (20,15,15), 10, 0.5)


@pytest.fixture
def c(f):
	"""A cabinet with 10 frames.
	
	The bay should have offset (1,1,1)
	"""
	return cabinet.Cabinet(f, (25, 120, 20), 5, 5.0, (1,1,1))


@pytest.fixture
def sys(c):
	"""A system of 10 cabinets."""
	return cabinet.System(c, 10, 100)


def test_board():
	"""Test the board model"""
	b = cabinet.Board((10,20,30), {
		topology.NORTH : (1,2,3),
		topology.SOUTH : (-1,-2,-3),
	})
	# Check the various dimensions
	assert b.width ==  10
	assert b.height == 20
	assert b.depth ==  30
	
	# Check accessing defined wire offsets
	assert b.get_position(topology.NORTH) == (1,2,3)
	assert b.get_position(topology.SOUTH) == (-1,-2,-3)
	
	# Check accessing undefined wire offsets
	assert b.get_position(topology.EAST) == (0,0,0)


def test_frame(f):
	"""Test the frame model"""
	
	# Check the various dimensions
	assert f.width ==  20
	assert f.height == 15
	assert f.depth ==  15
	
	# Check accessing wires
	assert f.get_position(0) == (2.75,2.5,0.0)
	assert f.get_position(1) == (4.25,2.5,0.0)
	
	# Check accessing a particular link
	assert f.get_position(2, topology.NORTH) == (5.75,2.5,1.0)


def test_cabinet(c):
	"""Test the cabinet model"""
	
	# Check the various dimensions
	assert c.width ==  25
	assert c.height == 120
	assert c.depth ==  20
	
	# Check accessing frame via the cabinet...
	assert c.get_position(0, 0) == (3.75,3.5,1.0)
	assert c.get_position(0, 1) == (5.25,3.5,1.0)
	
	# Access a subsequent frame
	assert c.get_position(1, 0) == (3.75,23.5,1.0)
	
	
	# Check accessing a particular link
	assert c.get_position(0, 2, topology.NORTH) == (6.75,3.5,2.0)


def test_system(sys):
	"""Test the system of cabinets model"""
	
	# Check accessing frames via the cabinet via the system...
	assert sys.get_position((0,0,0)) == (3.75,3.5,1.0)
	assert sys.get_position((0,0,1)) == (5.25,3.5,1.0)
	
	# Access a subsequent frame
	assert sys.get_position((0,1,0)) == (3.75,23.5,1.0)
	
	# Access a subsequent cabinet
	assert sys.get_position((1,1,0)) == (128.75,23.5,1.0)
	
	# Check accessing a particular link
	assert sys.get_position((0,0,2), topology.NORTH) == (6.75,3.5,2.0)
