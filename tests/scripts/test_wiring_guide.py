import pytest

from mock import Mock

import os.path

from tempfile import mkdtemp

from shutil import rmtree

from spinner.scripts import wiring_guide

from spinner.topology import Direction


@pytest.fixture
def bc(monkeypatch):
	# Mock out all parts which talk to the outside world...
	bc = Mock()
	monkeypatch.setattr(wiring_guide, "BMPController", Mock(return_value=bc))
	return bc


@pytest.fixture
def wp(monkeypatch):
	wp = Mock()
	monkeypatch.setattr(wiring_guide, "WiringProbe", Mock(return_value=wp))
	
	# Make the discovered wire set look like just report one wire which needs to
	# be removed
	wp.discover_wires.return_value = [
		# To be removed...
		((0,0,0,Direction.north), (0,0,0,Direction.west)),
		# To be kept...
		((0,0,0,Direction.south_west), (0,0,2,Direction.north_east)),
		]
	
	return wp


@pytest.fixture
def iwg(monkeypatch):
	# Mock out all parts which talk to the outside world...
	iwg = Mock()
	monkeypatch.setattr(wiring_guide, "InteractiveWiringGuide", iwg)
	return iwg


@pytest.yield_fixture
def logdir():
	logdir = mkdtemp()
	yield logdir
	rmtree(logdir)


@pytest.mark.parametrize("argstring",
                         [# Not enough BMPs
                          "-l 1 -n 48 --bmp 0 0 localhost",
                          # --fix without any BMPs
                          "-l 1 -n 3 --fix",
                          # --log without a filename
                          "--log",
                         ])
def test_bad_args(argstring):
	with pytest.raises(SystemExit):
		wiring_guide.main(argstring.split())


@pytest.mark.parametrize("argstring,to_check",
                         [# Run the tool without the BMP and check the defaults
                          ("-n 3 -l 1.0", {"bmp": False,
                                           "use_tts":True,
                                           "wires_to_add": 9,
                                           "wires_to_remove": 0}),
                          # No TTS
                          ("-n 3 -l 1.0 --no-tts", {"bmp": False,
                                                    "use_tts":False,
                                                    "wires_to_add": 9,
                                                    "wires_to_remove": 0}),
                          # Run the tool with the BMP and check the defaults
                          ("-n 3 -l 1.0 --bmp 0 0 localhost",
                           {"bmp": True,
                            "use_tts":True,
                            "wires_to_add": 9,
                            "wires_to_remove": 0}),
                          # Fix mode
                          ("-n 3 -l 1.0 --bmp 0 0 localhost --fix",
                           {"wires_to_add": 8,
                            "wires_to_remove": 1}),
                          # Fix mode with no auto advance (just shouldn't
                          # break...)
                          ("-n 3 -l 1.0 --no-auto-advance --bmp 0 0 localhost --fix",
                           {"bmp": True,
                            "wires_to_add": 8,
                            "wires_to_remove": 1}),
                         ])
def test_argument_parsing(argstring, to_check, bc, wp, iwg):
	# Command should exit happily
	assert wiring_guide.main(argstring.split()) == 0
	
	# The timing logger should not be provided
	assert iwg.mock_calls[0][2]["timing_logger"] is None
	
	# Check if the BMP is used
	if "bmp" in to_check:  # pragma: no branch
		has_bmp = iwg.mock_calls[0][2]["bmp_controller"] is not None
		assert has_bmp == to_check.pop("bmp")
	
	# Check if TTS is enabled
	if "use_tts" in to_check:  # pragma: no branch
		assert iwg.mock_calls[0][2]["use_tts"] == to_check.pop("use_tts")
	
	num_added = 0
	num_removed = 0
	for s,d,l in iwg.mock_calls[0][2]["wires"]:
		if l is None:
			num_removed += 1
		else:
			num_added += 1
	
	# Check if the right number of wires are added/removed
	if "wires_to_add" in to_check:  # pragma: no branch
		assert num_added == to_check.pop("wires_to_add")
	if "wires_to_remove" in to_check:  # pragma: no branch
		assert num_removed == to_check.pop("wires_to_remove")
	
	# All to-checks should be handled...
	assert len(to_check) == 0


@pytest.mark.parametrize("argstring,focus",
                         [# Some-of a frame
                          ("-n 3 -l 1.0", [0,0,slice(0,3)]),
                          # Full frame
                          ("-n 24 -l 1.0", [0,0,slice(0,24)]),
                          # Two frames
                          ("-n 48 -l 1.0", [0,slice(0,2)]),
                          # Full cabinet
                          ("-n 120 -l 1.0", [0,slice(0,5)]),
                          # Multiple frames
                          ("-n 240 -l 1.0", [slice(0,2)]),
                         ])
def test_focus(argstring, focus, bc, wp, iwg):
	# Command should exit happily
	assert wiring_guide.main(argstring.split()) == 0
	
	assert iwg.mock_calls[0][2]["focus"] == focus


def test_logging(logdir, bc, wp, iwg):
	filename = os.path.join(logdir, "test.log")
	
	def iwg_constructor(*args, **kwargs):
		# Pretend to drive the timing logger
		tl = kwargs["timing_logger"]
		tl.logging_started()
		tl.logging_stopped()
		return Mock()
	iwg.side_effect = iwg_constructor
	
	# First time the file is written, the header should be included
	assert wiring_guide.main(["-n3", "-l1", "--log", filename]) == 0
	assert iwg.mock_calls[0][2]["timing_logger"] is not None
	with open(filename, "r") as f:
		assert len(f.read().split("\n")) == 4
	
	# Second time the file is written, we should have opened for append and no
	# additional header should be included
	assert wiring_guide.main(["-n3", "-l1", "--log", filename]) == 0
	assert iwg.mock_calls[0][2]["timing_logger"] is not None
	with open(filename, "r") as f:
		data = f.read()
		assert len(data.split("\n")) == 6
