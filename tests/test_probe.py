import pytest

from six import itervalues

from mock import Mock

from spinner import probe

from spinner.topology import Direction

from rig.machine_control import BMPController

IDSO = 0x4C
IDSI = 0x50
HAND = 0x54

SCRM = 0x00040010

# Lookup from FPGA number and the top bits of read/write address to the link
ADDR_TO_DIRECTION_MASK = 0xFFFF0000
ADDR_TO_DIRECTION = {
	(0, 0x00000000): Direction.east,
	(0, 0x00010000): Direction.south,
	(1, 0x00000000): Direction.south_west,
	(1, 0x00010000): Direction.west,
	(2, 0x00000000): Direction.north,
	(2, 0x00010000): Direction.north_east,
}


@pytest.fixture
def dead_endpoints():
	"""An (initially empty) set which defines which (c,f,b,d) HAND registers
	should report not having a handshake."""
	return set()


@pytest.fixture
def mock_bmp_controller(dead_endpoints):
	"""A mock BMPController instance.
	
	This pretends to be attached to a fully powered on system in which north is
	connected to south etc. on each board. Any (c,f,b,d) added to the
	dead_endpoints fixture will report not having a handshake.
	"""
	# The last value written to each IDSO register
	idso = {}
	
	m = Mock(spec_set=BMPController)
	
	def write_fpga_reg(fpga_num, addr, value, c, f, b):
		d = ADDR_TO_DIRECTION.get((fpga_num, addr&ADDR_TO_DIRECTION_MASK), None)
		reg = addr & ~ADDR_TO_DIRECTION_MASK
		
		# Should only ever write to IDSO and SCRM
		assert (d is not None and reg == IDSO) or addr == SCRM
		
		idso[(c,f,b,d)] = value
		
	m.write_fpga_reg.side_effect = write_fpga_reg
	
	def read_fpga_reg(fpga_num, addr, c, f, b):
		d = ADDR_TO_DIRECTION.get((fpga_num, addr&ADDR_TO_DIRECTION_MASK), None)
		reg = addr & ~ADDR_TO_DIRECTION_MASK
		
		if d is not None and reg == IDSO:
			return idso.get((c,f,b,d), 0xFFFFFFFF)
		elif d is not None and reg == IDSI:
			return idso.get((c,f,b,d.opposite), 0xFFFFFFFF)
		elif d is not None and reg == HAND:  # pragma: no branch
			return 0x01 if (c,f,b,d) not in dead_endpoints else 0x00
		else:  # pragma: no cover
			return 0xFFFFFFFF
	m.read_fpga_reg.side_effect = read_fpga_reg
	
	return m


@pytest.fixture
def mock_bmp_controller_powered_down():
	"""A mock BMPController which behaves like an FPGA which has been powered
	down, just reading 0xFFFFFFFF to every read."""
	m = Mock(spec_set=BMPController)
	m.read_fpga_reg.return_value = 0xFFFFFFFF
	return m


def test_init(mock_bmp_controller, dead_endpoints):
	# Shouldn't fail when some links don't have a handshake
	dead_endpoints.add((0,0,0,Direction.north))
	
	# Test that every node gets a unique ID
	p = probe.WiringProbe(mock_bmp_controller, 2, 5, 24)
	
	def get_assigned_ids(mock_bmp_controller):
		# Populate a lookup from (c,f,b,d) to ID and also check that every write is
		# appropriate
		ids = {}
		for write_fpga_reg_call in mock_bmp_controller.write_fpga_reg.mock_calls:
			fpga_num, addr, value, c, f, b = write_fpga_reg_call[1]
			
			# Skip scrambler setup
			if addr == SCRM:
				continue
			
			# Determine the link written to
			d = ADDR_TO_DIRECTION.get((fpga_num, addr&ADDR_TO_DIRECTION_MASK), None)
			assert d is not None
			
			# Make sure the correct register was written to
			assert addr & ~ADDR_TO_DIRECTION_MASK == 0x4C  # The IDSO register
			
			assert (c,f,b,d) not in ids
			ids[(c,f,b,d)] = value
		return ids
	
	ids = get_assigned_ids(mock_bmp_controller)
	
	# Check every link was covered
	assert set((c,f,b,d)
	           for c in range(2)
	           for f in range(5)
	           for b in range(24)
	           for d in Direction) == set(ids)
	
	# Check each link ID is unique
	assert len(set(itervalues(ids))) == len(ids)
	
	# Check that a second run assigns different IDs
	mock_bmp_controller.write_fpga_reg.reset_mock()
	p2 = probe.WiringProbe(mock_bmp_controller, 2, 5, 24)
	ids2 = get_assigned_ids(mock_bmp_controller)
	assert ids != ids2


def test_powered_down(mock_bmp_controller_powered_down):
	# Should fail to initialise if any FPGAs are powered down
	with pytest.raises(probe.WiringProbeError):
		probe.WiringProbe(mock_bmp_controller_powered_down, 2, 5, 24)


def test_get_link_target(mock_bmp_controller, dead_endpoints):
	# Should report everything correctly when all links have a handshake
	p = probe.WiringProbe(mock_bmp_controller, 2, 5, 24)
	
	for c in range(2):
		for f in range(5):
			for b in range(24):
				for d in Direction:
					assert p.get_link_target(c, f, b, d) == (c, f, b, d.opposite)
	
	# Should report bad links when the endpoint is not handshaking
	dead_endpoints.add((0, 0, 0, Direction.north))
	assert p.get_link_target(0, 0, 0, Direction.north) is None
	
	# Other links should not be effected
	assert p.get_link_target(0, 0, 0, Direction.west) == (0, 0, 0, Direction.east)


def test_discover_wires(mock_bmp_controller, dead_endpoints):
	# Check everything is listed (excluding links which are dead in one or both
	# directions)
	p = probe.WiringProbe(mock_bmp_controller, 2, 5, 24)
	
	# Dead at one end
	dead_endpoints.add((0, 0, 0, Direction.north))
	
	# Dead at both ends
	dead_endpoints.add((0, 0, 0, Direction.north_east))
	dead_endpoints.add((0, 0, 0, Direction.south_west))
	
	assert set(p.discover_wires()) == set(  # pragma: no branch
		((c,f,b,d), (c,f,b,d.opposite))
		for c in range(2)
		for f in range(5)
		for b in range(24)
		for d in [Direction.north, Direction.east, Direction.south_west]
		if (c, f, b, d) not in [(0,0,0,Direction.north),
		                        (0,0,0,Direction.south_west)])
