import pytest

from mock import Mock

from six import iteritems

from argparse import ArgumentParser

from spinner.topology import Direction

from spinner.scripts import arguments

from spinner import utils

from example_cabinet_params import board_wire_offset_fields, unique


class TestCabinetAction(object):
	
	@pytest.fixture
	def parser(self):
		parser = ArgumentParser()
		
		parser.add_argument("--cabinet-only", action=arguments.CabinetAction(1))
		parser.add_argument("--frame-only", action=arguments.CabinetAction(2))
		parser.add_argument("--board-only", action=arguments.CabinetAction(3))
		parser.add_argument("--full-spec", action=arguments.CabinetAction(4))
		parser.add_argument("--multiple", action=arguments.CabinetAction(4, append=True))
		
		return parser
	
	
	@pytest.mark.parametrize("argstring", [# No arguments
	                                       "--cabinet-only",
	                                       "--frame-only",
	                                       "--board-only",
	                                       "--full-spec",
	                                       "--multiple",
	                                       "--multiple --multiple",
	                                       # Too many arguments
	                                       "--cabinet-only 1 2",
	                                       "--frame-only 1 2 3",
	                                       "--board-only 1 2 3 north",
	                                       "--full-spec 1 2 3 north bad",
	                                       "--multiple 1 2 3 north bad",
	                                       "--multiple 1 2 3 north bad --multiple 1 2 3 north bad",
	                                       # Negative
	                                       "--cabinet-only -1",
	                                       "--frame-only 1 -2",
	                                       "--board-only 1 2 -3 north",
	                                       "--full-spec 1 2 -3 north",
	                                       "--multiple 1 2 -3 north",
	                                       "--multiple 1 2 -3 north --multiple 1 2 -3 north",
	                                       # Non-number
	                                       "--cabinet-only bad",
	                                       "--frame-only 1 bad",
	                                       "--board-only 1 2 bad north",
	                                       "--full-spec 1 2 bad north",
	                                       "--multiple 1 2 bad north",
	                                       "--multiple 1 2 bad north --multiple 1 2 bad north",
	                                       # Non-direction
	                                       "--full-spec 1 2 3 bad",
	                                       "--multiple 1 2 3 bad",
	                                       "--multiple 1 2 3 bad --multiple 1 2 3 bad",
	                                      ])
	def test_bad(self, parser, argstring):
		with pytest.raises(SystemExit):
			parser.parse_args(argstring.split())
	
	
	@pytest.mark.parametrize("argstring,full_spec",
	                         [# Just cabinet
	                          ("--full-spec 0", (0, )),
	                          ("--full-spec 1", (1, )),
	                          # Cabinet and frame
	                          ("--full-spec 0 0", (0, 0)),
	                          ("--full-spec 1 2", (1, 2)),
	                          # Cabinet, frame and board
	                          ("--full-spec 0 0 0", (0, 0, 0)),
	                          ("--full-spec 1 2 3", (1, 2, 3)),
	                          # Cabinet, frame, board and socket
	                          ("--full-spec 0 0 0 north",
	                           (0, 0, 0, Direction.north)),
	                          ("--full-spec 1 2 3 north-east",
	                           (1, 2, 3, Direction.north_east)),
	                         ])
	def test_full_spec(self, parser, argstring, full_spec):
		args = parser.parse_args(argstring.split())
		assert args.full_spec == full_spec
	
	
	@pytest.mark.parametrize("argstring,multiple",
	                         [# None
	                          ("", None),
	                          # One
	                          ("--multiple 1", [(1, )]),
	                          # Several
	                          ("--multiple 1 --multiple 2 3", [(1, ), (2, 3)]),
	                         ])
	def test_multiple(self, parser, argstring, multiple):
		args = parser.parse_args(argstring.split())
		assert args.multiple == multiple


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
                          ("-n 6", (2, 1), "shear", "rows", (2, 2)),
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
                          ("-l 1.5", [1.5]),
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


@pytest.mark.parametrize("argstring,expectation",
                         [("-l 1", [1.0]),
                          ("-l 1.5", [1.5]),
                          ("-l 1 2 3", [1.0, 2.0, 3.0]),
                          ("-l 3 2 1", [1.0, 2.0, 3.0]),
                          ("-l 1 -l 2 -l 3", [1.0, 2.0, 3.0]),
                          ("-l 3 -l 2 -l 1", [1.0, 2.0, 3.0]),
                          ("-l 3 -l 2 1", [1.0, 2.0, 3.0]),
                         ])
def test_get_wire_lengths_from_args(argstring, expectation):
	parser = ArgumentParser()
	arguments.add_wire_length_args(parser)
	
	args = parser.parse_args(argstring.split())
	assert arguments.get_wire_lengths_from_args(parser, args) == expectation



@pytest.mark.parametrize("argstring",
                         [# Supplying no wire lengths
                          "",
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
def test_get_wire_lengths_from_args_bad(argstring):
	# Make sure bad arguments fail to validate
	parser = ArgumentParser()
	arguments.add_wire_length_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_wire_lengths_from_args(parser, args)


@pytest.mark.parametrize("argstring,aspect_ratio,to_check",
                         [# Passes through the filename...
                          ("/super/happy/smiley.png", 0.5,
                           {"output_filename": "/super/happy/smiley.png"}),
                          # File type detection
                          ("out.png", 0.5, {"file_type": "png"}),
                          ("out.pNg", 0.5, {"file_type": "png"}),
                          ("out.PNG", 0.5, {"file_type": "png"}),
                          ("out.pdf.png", 0.5, {"file_type": "png"}),
                          ("out.pdf", 0.5, {"file_type": "pdf"}),
                          ("out.pDf", 0.5, {"file_type": "pdf"}),
                          ("out.PDF", 0.5, {"file_type": "pdf"}),
                          ("out.png.pdf", 0.5, {"file_type": "pdf"}),
                          # Manual image sizes (PNGs should be integers, PDFs
                          # should be floats)
                          ("out.png 10.5 100.5", 0.5, {"image_width":10,
                                                       "image_height":100}),
                          ("out.png 100.5 10.5", 0.5, {"image_width":100,
                                                       "image_height":10}),
                          ("out.pdf 10.5 100.5", 0.5, {"image_width":10.5,
                                                       "image_height":100.5}),
                          ("out.pdf 100.5 10.5", 0.5, {"image_width":100.5,
                                                       "image_height":10.5}),
                          # Semi-automatic for tall images
                          ("out.pdf 1000.5", 0.5, {"image_height":1000.5,
                                                   "aspect_ratio":0.5}),
                          ("out.png 1000.5", 0.5, {"image_height":1000,
                                                   "aspect_ratio":0.5}),
                          # Semi-automatic but for wider images
                          ("out.pdf 1000.5", 1.5, {"image_width":1000.5,
                                                    "aspect_ratio":1.5}),
                          ("out.png 1000.5", 1.5, {"image_width":1000,
                                                    "aspect_ratio":1.5}),
                          # Fully-automatic for tall images
                          ("out.png", 0.5, {"image_height":1000,
                                            "aspect_ratio":0.5}),
                          ("out.pdf", 0.5, {"image_height":280.0,
                                            "aspect_ratio":0.5}),
                          # Fully-automatic for wide images
                          ("out.png", 1.5, {"image_width":1000,
                                             "aspect_ratio":1.5}),
                          ("out.pdf", 1.5, {"image_width":280.0,
                                             "aspect_ratio":1.5}),
                         ])
def test_get_image_args(argstring, aspect_ratio, to_check):
	parser = ArgumentParser()
	arguments.add_image_args(parser)
	
	args = parser.parse_args(argstring.split())
	output_filename, file_type, image_width, image_height =\
		arguments.get_image_from_args(parser, args, aspect_ratio)
	
	if "output_filename" in to_check:
		assert output_filename == to_check.pop("output_filename")
	
	if "file_type" in to_check:
		assert file_type == to_check.pop("file_type")
	
	if "image_height" in to_check:
		assert image_height == to_check.pop("image_height")
	if "image_width" in to_check:
		assert image_width == to_check.pop("image_width")
	
	if "aspect_ratio" in to_check:
		ref_ratio = to_check.pop("aspect_ratio")
		ratio = image_width / float(image_height)
		
		# Should be pretty close (slack allowed for rounding to pixels in PNG)
		assert abs(ratio - ref_ratio) < 0.01
	
	# Make sure none of the test-cases define something to test which isn't
	# tested...
	assert len(to_check) == 0


@pytest.mark.parametrize("argstring",
                         [# Missing filename
                          "",
                          # Missing/Unknown file extension
                          "out",
                          "out.gif",
                          "out.png.gif",
                          # Invalid output sizes
                          "out.png 0.5",
                          "out.png 0.5 0.5",
                          "out.png 10 0.5",
                          "out.png 0.5 10",
                          "out.pdf 0",
                          "out.pdf 0 0",
                          "out.pdf 1 0",
                          "out.pdf 0 1",
                         ])
def test_get_image_args_bad(argstring):
	parser = ArgumentParser()
	arguments.add_image_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_image_from_args(parser, args)


@pytest.mark.parametrize("argstring,expectation",
                         [("", {}),
                          ("--bmp 0 0 one --bmp 0 1 two "
                           "--bmp 1 0 three --bmp 1 1 four",
                           {(0, 0): "one", (0, 1): "two",
                            (1, 0): "three", (1, 1): "four"}),
                         ])
def test_get_bmps_from_args(argstring, expectation):
	parser = ArgumentParser()
	arguments.add_bmp_args(parser)
	
	args = parser.parse_args(argstring.split())
	assert arguments.get_bmps_from_args(parser, args, 2, 2) == expectation



@pytest.mark.parametrize("argstring",
                         [# Supplying wrong number of arguments
                          "--bmp",
                          "--bmp 0",
                          "--bmp 0 0",
                          # Supplying arguments of the wrong type
                          "--bmp bad 0 localhost",
                          "--bmp 0 bad localhost",
                          # Supplying arguments of the wrong sign
                          "--bmp -1 0 localhost",
                          "--bmp 0 -1 localhost",
                          # Supplying duplicate hostnames
                          "--bmp 0 0 bad --bmp 0 1 bad",
                          # Supplying duplicate frames
                          "--bmp 0 1 foo --bmp 0 1 bar",
                          # Supplying not enough BMPs
                          "--bmp 0 0 foo",
                          # Supplying too many/the wrong BMPs
                          "--bmp 0 0 foo --bmp 0 1 bar --bmp 0 2 baz",
                          "--bmp 1 0 foo --bmp 1 1 bar",
                         ])
def test_get_bmps_from_args_bad(argstring):
	# Make sure bad arguments fail to validate
	parser = ArgumentParser()
	arguments.add_bmp_args(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		arguments.get_bmps_from_args(parser, args, 1, 2)
