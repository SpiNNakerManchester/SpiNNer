import pytest

from mock import Mock

from argparse import ArgumentParser

from spinner.scripts import arguments
from spinner import utils


@pytest.mark.parametrize("argstring",
                         ["",  # Requires -n or -t
                          "-n 12 -t 8 8",  # ...but not both
                          "-t -1 -1",  # Invalid dimensions
                          "-t 0 1",  # "
                          "-t 1 0",  # "
                          "-t -1 1",  # "
                          "-t 1 -1",  # "
                          "-n 8",  # Num boards must be a multiple of 3
                          "-n 3 --folds 2 2",  # Require transformation with folds
                          # Require transformation with uncrinkle-direction
                          "-n 3 --uncrinkle-direction rows",
                          "-n 3 --transformation foo",  # Only slice or shear
                          "-n 3 --transformation slice --folds 0 0",  # Invalid folds
                          "-n 3 --transformation slice --folds -1 1",  # "
                          "-n 3 --transformation slice --folds 1 -1",  # "
                          # Invalid uncrinkle_direction
                          "-n 3 --transformation slice --uncrinkle-direction foo",
                         ])
def test_get_topology_from_args_bad(argstring):
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_topology_from_args(parser, args)


@pytest.mark.parametrize("argstring,dimensions,auto,transformation,"
                         "uncrinkle_direction,folds",
                         [("-n 3", (1, 1), True, None, None, None),
                          ("-n 6", (1, 2), True, None, None, None),
                          ("-n 12", (2, 2), True, None, None, None),
                          ("-t 3 3", (3, 3), True, None, None, None),
                          ("-t 2 3", (2, 3), True, None, None, None),
                          ("-t 2 3 --transformation slice", (2, 3),
                           False, "slice", None, (2, 2)),
                          ("-t 2 3 --transformation shear", (2, 3),
                           False, "shear", None, (2, 2)),
                          ("-t 2 3 --transformation slice --folds 4 4", (2, 3),
                           False, "slice", None, (4, 4)),
                          ("-t 2 3 --transformation slice --uncrinkle-direction rows",
                           (2, 3), False, "slice", "rows", None),
                          ("-t 2 3 --transformation slice --uncrinkle-direction columns",
                           (2, 3), False, "slice", "columns", None),
                         ])
def test_get_topology_from_args_dimensions(argstring, dimensions, auto,
                                           transformation, uncrinkle_direction,
                                           folds, monkeypatch):
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	
	# Mock-wrap relevant construction functions to ensure they're called when
	# appropriate
	mock_folded_torus_with_minimal_wire_length = Mock()
	mock_folded_torus_with_minimal_wire_length.side_effect = \
		utils.folded_torus_with_minimal_wire_length
	monkeypatch.setattr(utils, "folded_torus_with_minimal_wire_length",
		mock_folded_torus_with_minimal_wire_length)
	
	mock_folded_torus = Mock()
	mock_folded_torus.side_effect = utils.folded_torus
	monkeypatch.setattr(utils, "folded_torus", mock_folded_torus)
	
	args = parser.parse_args(argstring.split())
	actual_dimensions, hex_boards, folded_boards = \
		arguments.get_topology_from_args(parser, args)
	
	# Check dimensions are correct
	assert actual_dimensions == dimensions
	assert len(hex_boards) == 3 * dimensions[0] * dimensions[1]
	assert len(folded_boards) == 3 * dimensions[0] * dimensions[1]
	
	# Check correct construction function is used
	if auto:
		assert mock_folded_torus_with_minimal_wire_length.called_once_with(
			*dimensions)
	else:
		assert mock_folded_torus.called_once_with(dimensions[0], dimensions[1],
		                                          transformation,
		                                          uncrinkle_direction,
		                                          folds)


def test_get_cabinets_from_args():
	parser = ArgumentParser()
	arguments.add_cabinet_args(parser)
	
	# Tuples of value name to value pairs (chosen such that all values are unique
	# but are not impossible
	value_names = [("board_dimensions", (0.1, 0.2, 0.3)),
	               ("board_wire_offset_south_west", (0.01,0.001,0.0001)),
	               ("board_wire_offset_north_east", (0.02,0.002,0.0002)),
	               ("board_wire_offset_east", (0.03,0.003,0.0003)),
	               ("board_wire_offset_west", (0.04,0.004,0.0004)),
	               ("board_wire_offset_north", (0.05,0.005,0.0005)),
	               ("board_wire_offset_south", (0.06,0.006,0.0006)),
	               ("inter_board_spacing", (0.123,)),
	               ("boards_per_frame", (2,)),
	               ("frame_dimensions", (1.0, 2.0, 3.0)),
	               ("frame_board_offset", (0.11, 0.22, 0.33)),
	               ("inter_frame_spacing", (0.321,)),
	               ("frames_per_cabinet", (3,)),
	               ("cabinet_dimensions", (10.0, 20.0, 30.0)),
	               ("cabinet_frame_offset", (0.111, 0.222, 0.333)),
	               ("inter_cabinet_spacing", (3.21,))]
	
	# Construct an argument string to set all possible arguments
	argstring = " ".join("--{} {}".format(name.replace("_", "-"),
	                                      " ".join(map(str, vals)))
	                     for (name, vals) in value_names)
	
	args = parser.parse_args(argstring.split())
	cabinet = arguments.get_cabinets_from_args(parser, args)
	
	# Check all arguments propagated through to the cabinet
	for name, value in value_names:
		print(name, value)
		assert hasattr(cabinet, name)
		if len(value) == 1:
			assert getattr(cabinet, name) == value[0]
		else:
			assert getattr(cabinet, name) == value


def test_get_cabinets_from_args_bad():
	# Make sure it fails if an impossible parameter combination is given
	
	# Invalid since dimensions must be positive
	argstring = "--board-dimensions -1 -1 -1 "
	
	parser = ArgumentParser()
	arguments.add_cabinet_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		cabinet = arguments.get_cabinets_from_args(parser, args)


@pytest.mark.parametrize("argstring,cabinets_frames",
                         [# Automatic sizing should work as usual
                          ("-n 3", (1, 1)),
                          ("-n 24", (1, 1)),
                          ("-n 48", (1, 2)),
                          ("-n 120", (1, 5)),
                          ("-n 1200", (10, 5)),
                          ("-t 1 1", (1, 1)),
                          ("-t 4 2", (1, 1)),
                          ("-t 4 4", (1, 2)),
                          ("-t 5 8", (1, 5)),
                          ("-t 20 20", (10, 5)),
                          # Manual sizing should work
                          ("-n 120 -c 1", (1, 5)),
                          ("-n 120 -c 2", (2, 5)),
                          ("-n 12 -c 1", (1, 5)),
                          ("-n 12 -c 2", (2, 5)),
                          ("-n 12 -f 1", (1, 1)),
                          ("-n 12 -f 2", (1, 2)),
                         ])
def test_get_space_from_args(argstring, cabinets_frames):
	# Make sure the expected number of cabinets and frames are allocated
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_space_args(parser)
	
	args = parser.parse_args(argstring.split())
	assert arguments.get_space_from_args(parser, args) == cabinets_frames


@pytest.mark.parametrize("argstring",
                         [# Specifying both cabinets and frames should fail,
                          # even if the numbers are vaild.
                          "-n 9 -c 10 -f 1",
                          "-n 9 -c 10 -f 5",
                          # Suggesting less cabinets or frames than needed
                          # should fail.
                          "-n 3 -f 0",
                          "-n 3 -c 0",
                          "-n 48 -f 1",
                          "-n 240 -f 5",
                          "-n 240 -c 1",
                          # Suggesting more frames than fit in a rack should
                          # fail.
                          "-n 240 -f 10",
                         ])
def test_get_space_from_args_bad(argstring):
	# Make sure bad arguments fail to validate
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_space_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_space_from_args(parser, args)

