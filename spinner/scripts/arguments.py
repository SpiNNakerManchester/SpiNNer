"""Standard argument parsing routines for SpiNNer scripts."""

from spinner.utils import ideal_system_size, folded_torus, min_num_cabinets

from spinner.cabinet import Cabinet


def add_topology_args(parser):
	"""Add arguments for specifying SpiNNaker machine topologies and their
	folding."""
	# Require the specification of the size of the system
	topology_group = parser.add_argument_group("machine topology dimensions")
	system_size_group = topology_group.add_mutually_exclusive_group(required=True)
	system_size_group.add_argument("--num-boards", "-n", type=int, metavar="N",
	                               help="build the 'squarest' system with this "
	                                    "many boards")
	system_size_group.add_argument("--triads", "-t", type=int, nargs=2,
	                               metavar=("W", "H"),
	                               help="build a system with the specified "
	                                    "number of triads of boards in each "
	                                    "dimension (yielding 3*W*H boards)")
	
	# Arguments for specification of how the system should be folded. If left out,
	# this is done automatically
	folding_group = parser.add_argument_group("topology folding options")
	folding_group.add_argument("--transformation", "-T", choices=["shear","slice"],
	                           help="the transformation function to use from "
	                                "hexagonal torus to rectangular Cartesian "
	                                "grid (selected automatically if omitted)")
	folding_group.add_argument("--uncrinkle-direction", choices=["columns", "rows"],
	                           help="direction in which to uncrinkle the hexagonal "
	                                "mesh to form a regular grid (default: rows)")
	folding_group.add_argument("--folds", "-F", type=int, nargs=2,
	                           default=None, metavar=("X", "Y"),
	                           help="the number of pieces to fold into in each "
	                                "dimension (default: (2, 2)) ignored if "
	                                "--transformation is not given")


def get_topology_from_args(parser, args):
	"""To be used with add_topology_args.
	
	Check that the supplied arguments are valid and return corresponding
	parameters for spinner.utils.folded_torus.
	
	Returns
	-------
	((w, h), transformation, uncrinkle_direction, (x, y))
		(w, h) is the dimensions of the system in triads
		
		transformation is "slice" or "shear"
		
		uncrinkle_direction is "rows" or "columns"
		
		(x, y) gives the number of pieces to fold each dimension into
	"""
	# Extract the system dimensions
	if args.num_boards is not None:
		try:
			w, h = ideal_system_size(args.num_boards)
		except TypeError:
			parser.error("number of boards must be a multiple of three")
	else:
		w, h = args.triads
		if w <= 0 or h <= 0:
			parser.error("system dimensions must be positive and non-zero")
	
	# Fold accordingly
	transformation = "shear"
	uncrinkle_direction = "rows"
	folds = (2, 2)
	
	if args.transformation is None:
		# Work out the folding process to use by following the guidelines set out in
		# "Bringing the Hexagonal Torus Topology into the Real-World" by Heathcote
		# et. al. (unpublished at the time of writing...).
		if h == 2 * w:
			transformation = "slice"
		else:
			transformation = "shear"
		uncrinkle_direction = "rows"
		folds = (2, 2)
	else:
		transformation = args.transformation
	
	if args.folds is not None:
		folds = tuple(args.folds)
	
	if folds[0] <= 0 or folds[1] <= 0:
		parser.error("number of pieces to fold into must be at least 1")
	
	if args.uncrinkle_direction is not None:
		uncrinkle_direction = args.uncrinkle_direction
	
	return ((w, h), transformation, uncrinkle_direction, folds)


def add_cabinet_args(parser):
	"""Add arguments for specifying SpiNNaker cabinet sizes."""
	# Physical dimensions (defaults to standard rack sizes)
	board_group = parser.add_argument_group("board physical dimensions")
	board_group.add_argument("--board-dimensions", type=float, nargs=3,
	                         metavar=("W", "H", "D"),
	                         default=(0.01524, 0.233, 0.240),
	                         help="physical board dimensions in meters (default: "
	                              "%(default)s)")
	for direction, default in [("south-west", (0.005, 0.013, 0.0)),
	                           ("north-east", (0.005, 0.031, 0.0)),
	                           ("east",       (0.005, 0.049, 0.0)),
	                           ("west",       (0.005, 0.067, 0.0)),
	                           ("north",      (0.005, 0.085, 0.0)),
	                           ("south",      (0.005, 0.103, 0.0))]:
		board_group.add_argument("--board-wire-offset-{}".format(direction),
		                         type=float, nargs=3, default=default,
		                         metavar=("X", "Y", "Z"),
		                         help="physical offset of the {} connector from "
		                              "board right-top-front corner in meters "
		                              "(default: %(default)s)".format(direction))
	board_group.add_argument("--inter-board-spacing", type=float,
	                         default=0.0, metavar=("S"),
	                         help="physical spacing between each board in a "
	                              "frame in meters (default: %(default)s)")
	
	frame_group = parser.add_argument_group("frame physical dimensions")
	frame_group.add_argument("--boards-per-frame", type=int, default=24,
	                         help="number of boards per frame (default: "
	                              "%(default)s)")
	frame_group.add_argument("--frame-dimensions", type=float, nargs=3,
	                         metavar=("W", "H", "D"),
	                         default=(0.430, 0.266, 0.250),
	                         help="frame physical dimensions in meters (default: "
	                              "%(default)s)")
	frame_group.add_argument("--frame-board-offset", type=float, nargs=3,
	                         default=(0.00424, 0.017, 0.0),
	                         metavar=("X", "Y", "Z"),
	                         help="physical offset of the right-most board "
	                              "from the right-top-front corner of a frame in "
	                              "meters (default: %(default)s)")
	frame_group.add_argument("--inter-frame-spacing", type=float,
	                         default=0.089, metavar=("S"),
	                         help="physical spacing between frames in a "
	                              "cabinet in meters (default: %(default)s)")
	
	cabinet_group = parser.add_argument_group("cabinet physical dimensions")
	cabinet_group.add_argument("--frames-per-cabinet", type=int, default=5,
	                           help="number of frames per cabinet (default: "
	                                "%(default)s)")
	cabinet_group.add_argument("--cabinet-dimensions", type=float, nargs=3,
	                           metavar=("W", "H", "D"),
	                           default=(0.600, 1.822, 0.250),
	                           help="cabinet physical dimensions in meters (default: "
	                                "%(default)s)")
	cabinet_group.add_argument("--cabinet-frame-offset", type=float, nargs=3,
	                           default=(0.085, 0.047, 0.0),
	                           metavar=("X", "Y", "Z"),
	                           help="physical offset of the top frame from the "
	                                "right-top-front corner of a cabinet in "
	                                "meters (default: %(default)s)")
	cabinet_group.add_argument("--inter-cabinet-spacing", type=float,
	                           default=0.0, metavar=("S"),
	                           help="physical spacing between each cabinet in "
	                                "meters (default: %(default)s)")


def get_cabinets_from_args(parser, args):
	"""For use with add_cabinet_args.
	
	Get information about the dimensions of the cabinets in the system from the
	supplied arguments.
	
	Returns
	-------
	:py:class:`spinner.cabinet.Cabinet`
	"""
	try:
		return Cabinet(**{
			kw: tuple(getattr(args, kw))
			    if type(getattr(args, kw)) is list
			    else getattr(args, kw)
			for kw in [
				"board_dimensions",
				"board_wire_offset_south_west",
				"board_wire_offset_north_east",
				"board_wire_offset_east",
				"board_wire_offset_west",
				"board_wire_offset_north",
				"board_wire_offset_south",
				"inter_board_spacing",
				"boards_per_frame",
				"frame_dimensions",
				"frame_board_offset",
				"inter_frame_spacing",
				"frames_per_cabinet",
				"cabinet_dimensions",
				"cabinet_frame_offset",
				"inter_cabinet_spacing",
			]
		})
	except ValueError as e:
		parser.error(e.args[0])


def add_space_args(parser):
	"""Add arguments for specifying the physical space (i.e. cabinets/frames)
	available for a given system. Should always be used along-side
	add_topology_args and add_cabinet_args."""
	space_group = parser.add_argument_group("physical space availability")
	space_mut_group = space_group.add_mutually_exclusive_group()
	space_mut_group.add_argument("--num-cabinets", "-c", type=int, metavar="N",
	                             help="spread across N cabinets (default: "
	                                  "automatically work out minimum needed)")
	space_mut_group.add_argument("--num-frames", "-f", type=int, metavar="N",
                               help="spread across N frames in one cabinet "
                                    "(default: automatically work out "
                                    "minimum needed)")


def get_space_from_args(parser, args):
	"""To be used with add_space_args (and add_topology_args and add_cabinet_args).
	
	Check that the supplied arguments are valid and get the number of cabinets and
	frames the user wishes to spread their system across.
	
	Returns
	-------
	(num_cabinets, num_frames)
		num_cabinets is the number of cabinets to use, num_frames is the number of
		frames to use which will be equal to frames_per_cabinet unless num_cabinets
		is 1 in which case it may be less.
	"""
	# Work out number of boards present
	if args.num_boards is not None:
		num_boards = args.num_boards
	else:  # if args.triads is not None:
		num_boards = 3 * args.triads[0] * args.triads[1]
	
	# Work out size based on arguments
	if args.num_cabinets is None and args.num_frames is None:
		num_cabinets, num_frames = min_num_cabinets(num_boards,
		                                            args.frames_per_cabinet,
		                                            args.boards_per_frame)
	elif args.num_cabinets is not None:
		num_cabinets = args.num_cabinets
		num_frames = args.frames_per_cabinet
	else:  # if args.num_frames is not None:
		num_cabinets = 1
		num_frames = args.num_frames
		
		if num_frames > args.frames_per_cabinet:
			parser.error("more frames specified than fit in a cabinet")
	
	# Check that the number of cabinets is definately sufficient
	if num_cabinets * num_frames * args.boards_per_frame < num_boards:
		parser.error("not enough cabinets/frames available for {} "
		             "boards".format(num_boards))
	
	return (num_cabinets, num_frames)


def add_histogram_args(parser):
	"""Add arguments for specifying the histogram of wire lengths (i.e.
	cabinets/frames) available for a given system."""
	histogram_group = parser.add_argument_group("available wire lengths")
	histogram_mut_group = histogram_group.add_mutually_exclusive_group()
	histogram_mut_group.add_argument("--wire-length", "-l", type=float, metavar="L",
	                                 action="append", nargs="+",
	                                 help="specify one or more available wire "
	                                      "lengths in meters (if supplied, these "
	                                      "lengths will be used to construct the "
	                                      "histogram of wire lengths)")
	histogram_mut_group.add_argument("--histogram-bins", "-H", type=int, metavar="N",
	                                 default=5,
	                                 help="number of bins to pack wire lengths into "
	                                      "in the histogram of wire lengths (default: "
	                                      "%(default)s)")


def get_histogram_from_args(parser, args):
	"""To be used with add_histogram_args.
	
	Check that the supplied arguments are valid and then return either the number
	of histogram bins or the set of bin boundaries.
	
	Returns
	-------
	int or [float, ...]
		If a single int, gives the number of bins to use in the wire-length
		histogram.
		
		If a list of floats, gives the upper-boundary of each bin to create (in
		ascending order).
	"""
	if args.wire_length is None:
		# Number of bins supplied
		if args.histogram_bins < 1:
			parser.error("--histogram-bins must be at least 1")
		return args.histogram_bins
	else:
		# List of wire-lengths supplied
		
		# Flatten list of lists
		args.wire_length = sum(args.wire_length, [])
		
		# Check signs and for duplicates
		seen = set()
		for wire_length in args.wire_length:
			if wire_length <= 0.0:
				parser.error("--wire-lengths must be positive and non-zero")
			if wire_length in seen:
				parser.error("wire length {} defined multiple times".format(wire_length))
			seen.add(wire_length)
		
		return sorted(args.wire_length)


if __name__=="__main__":  # pragma: no cover
	# This file when run as a script acts as a quick proof-of-concept of all
	# argument parsing capabilities
	import argparse
	parser = argparse.ArgumentParser()
	add_topology_args(parser)
	add_space_args(parser)
	add_cabinet_args(parser)
	add_histogram_args(parser)
	
	args = parser.parse_args()
	print(get_topology_from_args(parser, args))
	print(get_space_from_args(parser, args))
	print(get_cabinets_from_args(parser, args))
	print(get_histogram_from_args(parser, args))
