import pytest

from mock import Mock

from spinner.scripts import wiring_validator

from spinner.topology import Direction


@pytest.fixture
def bc(monkeypatch):
	# Mock out all parts which talk to the outside world...
	bc = Mock()
	monkeypatch.setattr(wiring_validator, "BMPController", Mock(return_value=bc))
	return bc


@pytest.fixture
def discover_wires():
	"""The list of values to be returned by wp.discover_wires().
	
	By default this is a fully connected 3-board system.
	"""
	return [((0, 0, 0, Direction.south_west), (0, 0, 2, Direction.north_east)),
	        ((0, 0, 2, Direction.south_west), (0, 0, 1, Direction.north_east)),
	        ((0, 0, 1, Direction.south_west), (0, 0, 0, Direction.north_east)),
	        ((0, 0, 0, Direction.east), (0, 0, 2, Direction.west)),
	        ((0, 0, 2, Direction.east), (0, 0, 1, Direction.west)),
	        ((0, 0, 1, Direction.east), (0, 0, 0, Direction.west)),
	        ((0, 0, 0, Direction.north), (0, 0, 2, Direction.south)),
	        ((0, 0, 2, Direction.north), (0, 0, 1, Direction.south)),
	        ((0, 0, 1, Direction.north), (0, 0, 0, Direction.south))]


@pytest.fixture
def wp(monkeypatch, discover_wires):
	wp = Mock()
	monkeypatch.setattr(wiring_validator.probe, "WiringProbe", Mock(return_value=wp))
	
	# Make the discovered wire set look like just report one wire which needs to
	# be removed
	wp.discover_wires.return_value = discover_wires
	
	def get_link_target(*src):
		src = tuple(src)
		
		d = dict(discover_wires)
		if src in d:
			return d[src]
		
		d = dict((d, s) for s, d in discover_wires)
		if src in d:
			return d[src]
		
		return None
	wp.get_link_target.side_effect = get_link_target
	
	return wp


@pytest.mark.parametrize("argstring",
                         [# No BMP
                          "-n 3",
                          # Not enough BMPs
                          "-n 48 --bmp 0 0 localhost",
                         ])
def test_bad_args(argstring):
	"""Make sure it fails with bad arguments."""
	with pytest.raises(SystemExit):
		wiring_validator.main(argstring.split())


def test_correct(bc, wp, discover_wires):
	"""Make sure when a correctly wired system is presented, it passes."""
	assert wiring_validator.main("-n 3 --bmp 0 0 localhost".split()) == 0


@pytest.mark.parametrize("verbose", [True, False])
def test_missing_wire(bc, wp, discover_wires, verbose):
	"""Remove a wire and it should fail."""
	discover_wires.pop(0)
	assert wiring_validator.main("-n 3 --bmp 0 0 localhost {}".format(
		"-v" if verbose else "").split()) != 0


@pytest.mark.parametrize("verbose", [True, False])
def test_bad_wire(bc, wp, discover_wires, verbose):
	"""Get some wires crossed it should fail."""
	src0, dst0 = discover_wires.pop(0)
	src1, dst1 = discover_wires.pop(0)
	discover_wires.append((src0, dst1))
	discover_wires.append((src1, dst0))
	assert wiring_validator.main("-n 3 --bmp 0 0 localhost {}".format(
		"-v" if verbose else "").split()) != 0


@pytest.mark.parametrize("num_boards,num_cabinets,num_frames",
                         [(24, 1, 1), (48, 1, 2), (240, 2, 5)])
def test_larger_systems(bc, wp, discover_wires,
                        num_boards, num_frames, num_cabinets):
	"""With larger systems, the test will fail because the wiring won't be in
	place but it shouldn't crash!"""
	bmp_args = " ".join("--bmp {} {} f{}c{}".format(c,f,c,f)
	                    for c in range(num_cabinets)
	                    for f in range(num_frames))
	
	assert wiring_validator.main("-n {} {}".format(num_boards, bmp_args).split()) != 0
