import pytest

from mock import Mock

from six import iteritems

from argparse import ArgumentParser

from spinner.topology import Direction

from spinner.scripts import arguments

from spinner import utils

from example_cabinet_params import board_wire_offset_fields, unique


@pytest.mark.parametrize("argstring",
                         ["",  # Requires -n or -t
                          "-n 12 -t 8 8",  # ...but not both
                          "-t -1 -1",  # Invalid dimensions
                          "-t 0 1",  # "
                          "-t 1 0",  # "
                          "-t -1 1",  # "
                          "-t 1 -1",  # "
                          "-n 8",  # Num boards must be a multiple of 3
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


@pytest.mark.parametrize("argstring,dimensions,transformation,"
                         "uncrinkle_direction,folds",
                         [# Check automatic choices made are correct
                          ("-n 3", (1, 1), "shear", "rows", (2, 2)),
                          ("-n 6", (1, 2), "slice", "rows", (2, 2)),
                          ("-n 12", (2, 2), "shear", "rows", (2, 2)),
                          ("-t 1 1", (1, 1), "shear", "rows", (2, 2)),
                          ("-t 1 2", (1, 2), "slice", "rows", (2, 2)),
                          ("-t 2 1", (2, 1), "shear", "rows", (2, 2)),
                          ("-t 3 6", (3, 6), "slice", "rows", (2, 2)),
                          # Check custom options
                          ("-t 2 3 --transformation slice",
                           (2, 3), "slice", "rows", (2, 2)),
                          ("-t 2 3 --transformation shear",
                           (2, 3), "shear", "rows", (2, 2)),
                          ("-t 2 3 --transformation slice --folds 4 4",
                           (2, 3), "slice", "rows", (4, 4)),
                          ("-t 2 3 --folds 4 4",
                           (2, 3), "shear", "rows", (4, 4)),
                          ("-t 2 3 --transformation slice --uncrinkle-direction rows",
                           (2, 3), "slice", "rows", (2, 2)),
                          ("-t 2 3 --uncrinkle-direction columns",
                           (2, 3), "shear", "columns", (2, 2)),
                         ])
def test_get_topology_from_args_dimensions(argstring, dimensions,
                                           transformation, uncrinkle_direction,
                                           folds):
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	
	args = parser.parse_args(argstring.split())
	(actual_dimensions,
	 actual_transformation,
	 actual_uncrinkle_direction,
	 actual_folds) = arguments.get_topology_from_args(parser, args)
	
	assert actual_dimensions == dimensions
	assert actual_transformation == transformation
	assert actual_uncrinkle_direction == uncrinkle_direction
	assert actual_folds == folds


def test_get_cabinets_from_args():
	parser = ArgumentParser()
	arguments.add_cabinet_args(parser)
	
	# Construct an argument string to set all possible arguments
	argstring = " ".join("--{} {}".format(name.replace("_", "-"),
	                                      " ".join(map(str, vals))
	                                      if isinstance(vals, tuple)
	                                      else str(vals))
	                     for (name, vals) in iteritems(unique))
	
	args = parser.parse_args(argstring.split())
	cabinet = arguments.get_cabinets_from_args(parser, args)
	
	# Check all arguments propagated through to the cabinet
	for name, value in iteritems(unique):
		if name in board_wire_offset_fields:
			cabinet.board_wire_offset[board_wire_offset_fields[name]] == value
		else:
			assert hasattr(cabinet, name)
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

