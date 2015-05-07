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


@pytest.mark.parametrize("with_topology", [True, False])
@pytest.mark.parametrize("set_num_cabinets", [True, False])
@pytest.mark.parametrize("set_num_frames", [True, False])
def test_get_cabinets_from_args(with_topology,
                                set_num_cabinets,
                                set_num_frames):
	parser = ArgumentParser()
	if with_topology:
		arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	
	unique_copy = unique.copy()
	del unique_copy["num_cabinets"]
	
	# Construct an argument string to set all possible arguments
	argstring = " ".join("--{} {}".format(name.replace("_", "-"),
	                                      " ".join(map(str, vals))
	                                      if isinstance(vals, tuple)
	                                      else str(vals))
	                     for (name, vals) in iteritems(unique_copy))
	
	if with_topology:
		argstring += " -n 3"
	if set_num_cabinets:
		argstring += " --num-cabinets 1"
	if set_num_frames:
		argstring += " --num-frames 1"
	
	args = parser.parse_args(argstring.split())
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	# Check all arguments propagated through to the cabinet
	for name, value in iteritems(unique_copy):
		if name in board_wire_offset_fields:
			cabinet.board_wire_offset[board_wire_offset_fields[name]] == value
		else:
			assert hasattr(cabinet, name)
			assert getattr(cabinet, name) == value
	
	# Check that the cabinet/frame count is correct
	if ((not with_topology and not set_num_frames) or
	    (set_num_cabinets and not set_num_frames)):
		assert cabinet.num_cabinets == 1
		assert num_frames == 2
	else:
		assert cabinet.num_cabinets == 1
		assert num_frames == 1


@pytest.mark.parametrize("argstring,num_cabinets,num_frames",
                         [# Test automatic selection
                          ("-n 3", 1, 1),
                          ("-n 24", 1, 1),
                          ("-t 1 1", 1, 1),
                          ("-t 2 4", 1, 1),
                          ("-t 3 4", 1, 2),
                          ("-n 27", 1, 2),
                          ("-n 120", 1, 5),
                          ("-n 123", 2, 5),
                          ("-n 1200", 10, 5),
                          # Test manual selection
                          ("-n 3 --num-frames 1", 1, 1),
                          ("-n 3 --num-frames 2", 1, 2),
                          ("-n 3 --num-frames 5", 1, 5),
                          ("-n 3 --num-cabinets 1", 1, 5),
                          ("-n 3 --num-cabinets 2", 2, 5),
                          ("-n 3 --num-cabinets 2 --num-frames 5", 2, 5),
                         ])
def test_get_cabinets_from_args_num_cabinets_num_frames(argstring,
                                                        num_cabinets,
                                                        num_frames):
	# Ensure that the number of frames/cabinets required is worked out correctly.
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	
	args = parser.parse_args(argstring.split())
	cabinet, actual_num_frames =\
		arguments.get_cabinets_from_args(parser, args)
	actual_num_cabinets = cabinet.num_cabinets
	
	assert actual_num_cabinets == num_cabinets
	assert actual_num_frames == num_frames


@pytest.mark.parametrize("argstring",
                         [# Make sure cabinet value validation failure causes a
                          # parser error rather than letting its exception
                          # trickle out.
                          "-n 3 --board-dimensions -1 -1 -1 ",
                          # Can't set num-frames to anything but the number of
                          # frames per cabinet when more than one cabinet
                          # present.
                          "-n 3 --num-cabinets 2 --num-frames 3",
                          # Can't set num-frames to anything larger than the
                          # number of frames per cabinet.
                          "-n 3 --num-frames 7",
                          "-n 3 --num-cabinets 1 --num-frames 7",
                          # Can't suggest too few frames/cabinets
                          "-n 25 --num-frames 1",
                          "-n 121 --num-cabinets 1",
                         ])
def test_get_cabinets_from_args_bad(argstring):
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		cabinet = arguments.get_cabinets_from_args(parser, args)


@pytest.mark.parametrize("argstring,expectation",
                         [# Numbers of bins
                          ("-H 1", 1),
                          ("-H 99", 99),
                          # Sets of wire lengths
                          ("-l 1", [1.0]),
                          ("-l 1 2 3", [1.0, 2.0, 3.0]),
                          ("-l 3 2 1", [1.0, 2.0, 3.0]),
                          ("-l 1 -l 2 -l 3", [1.0, 2.0, 3.0]),
                          ("-l 3 -l 2 -l 1", [1.0, 2.0, 3.0]),
                          ("-l 3 -l 2 1", [1.0, 2.0, 3.0]),
                         ])
def test_get_histogram_from_args(argstring, expectation):
	parser = ArgumentParser()
	arguments.add_histogram_args(parser)
	
	args = parser.parse_args(argstring.split())
	assert arguments.get_histogram_from_args(parser, args) == expectation



@pytest.mark.parametrize("argstring",
                         [# Specifying lengths at the same time as number of
                          # bins
                          "-H 100 -l 1",
                          "-H 100 -l 1 -l 2",
                          # Supplying a zero/negative/fractional number of bins
                          "-H 0",
                          "-H -1",
                          "-H -2",
                          "-H 0.5",
                          # Supplying an empty set of wire lengths
                          "-l",
                          # Supplying some zero/negative wire lengths
                          "-l 0",  # Alone
                          "-l 0.0",
                          "-l -1",
                          "-l -1.0",
                          "-l 1 0 2",  # With other values
                          "-l 1 0.0 2",
                          "-l 1 -1 2",
                          "-l 1 -1.0 2",
                          "-l 3 -l 1 0 2",  # With multiple -l options
                          "-l 3 -l 1 0.0 2",
                          "-l 3 -l 1 -1 2",
                          "-l 3 -l 1 -1.0 2",
                          # Supplying duplicate lengths
                          "-l 1 1",
                          "-l 1 2 1",
                          "-l 1 -l 1",
                          "-l 1 2 -l 1 3",
                         ])
def test_get_histogram_from_args_bad(argstring):
	# Make sure bad arguments fail to validate
	parser = ArgumentParser()
	arguments.add_histogram_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_histogram_from_args(parser, args)

