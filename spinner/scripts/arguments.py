"""Standard argument parsing routines for SpiNNer scripts."""

import argparse

import re

from six import itervalues

import spinner

from spinner.topology import Direction

from spinner.utils import ideal_system_size, folded_torus, min_num_cabinets

from spinner.cabinet import Cabinet


def CabinetAction(num_levels=4, append=False):
	""""An argparse Action which accepts cabinet/frame/board/link references."""
	assert 1 <= num_levels <= 4
	
	class _CabinetAction(argparse.Action):
		
		"""Names of directions for command line arguments."""
		DIRECTION_NAMES = {d.name.replace("_", "-"): d for d in Direction}
		
		def __init__(self, *args, **kwargs):
			kwargs.setdefault("type", str)
			kwargs.setdefault("nargs", "+")
			
			metavar = ""
			if num_levels >= 4:
				metavar = " [{{{}}}{}]".format(",".join(self.DIRECTION_NAMES), metavar)
			if num_levels >= 3:
				metavar = " [BOARD{}]".format(metavar)
			if num_levels >= 2:
				metavar = " [FRAME{}]".format(metavar)
			metavar = "CABINET{}".format(metavar)
			kwargs.setdefault("metavar", (metavar, ""))
			
			argparse.Action.__init__(self, *args, **kwargs)
		
		def __call__(self, parser, namespace, values, option_string=None):
			# Fail with too many/few arguments
			if not 1 <= len(values) <= num_levels:
				parser.error("{} expects between 1 and {} values".format(
					option_string, num_levels))
			
			# Check cabinet/frame/board are integer types (and cast to int as
			# appropriate)
			for int_val, name in enumerate("CABINET FRAME BOARD".split()):
				if len(values) > int_val:
					if not values[int_val].isdigit():
						parser.error("{} value for {} must be a non-negative integer, not '{}'".format(
							option_string, name, values[int_val]))
					else:
						values[int_val] = int(values[int_val])
			
			# Convert direction into a Direction
			if len(values) >= 4:
				# Typecheck
				if not values[3] in self.DIRECTION_NAMES:
					parser.error("{} value for link must be one of {{{}}}, not {}".format(
						option_string, ",".join(self.DIRECTION_NAMES), values[3]))
				
				values[3] = self.DIRECTION_NAMES[values[3]]
			
			values = tuple(values)
			
			if append:
				if getattr(namespace, self.dest) is None:
					setattr(namespace, self.dest, [])
				getattr(namespace, self.dest).append(values)
			else:
				setattr(namespace, self.dest, values)
	
	return _CabinetAction


def add_version_args(parser):
	"""Adds a standard --version/-V incantation which prints the version number
	from spinner.__version__."""
	parser.add_argument("--version", "-V", action="version",
	                    version="%(prog)s {}".format(spinner.__version__))


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
	                         default=(0.014, 0.233, 0.240),
	                         help="physical board dimensions in meters (default: "
	                              "%(default)s)")
	for direction, default in [("south-west", (0.008, 0.013, 0.0)),
	                           ("north-east", (0.008, 0.031, 0.0)),
	                           ("east",       (0.008, 0.049, 0.0)),
	                           ("west",       (0.008, 0.067, 0.0)),
	                           ("north",      (0.008, 0.085, 0.0)),
	                           ("south",      (0.008, 0.103, 0.0))]:
		board_group.add_argument("--board-wire-offset-{}".format(direction),
		                         type=float, nargs=3, default=default,
		                         metavar=("X", "Y", "Z"),
		                         help="physical offset of the {} connector from "
		                              "board left-top-front corner in meters "
		                              "(default: %(default)s)".format(direction))
	board_group.add_argument("--inter-board-spacing", type=float,
	                         default=0.00124, metavar=("S"),
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
	                         default=(0.06, 0.017, 0.0),
	                         metavar=("X", "Y", "Z"),
	                         help="physical offset of the left-top-front corner of "
	                              "the left-most board from the left-top-front "
	                              "corner of a frame in meters (default: "
	                              "%(default)s)")
	frame_group.add_argument("--inter-frame-spacing", type=float,
	                         default=0.133, metavar=("S"),
	                         help="physical spacing between frames in a "
	                              "cabinet in meters (default: %(default)s)")
	
	cabinet_group = parser.add_argument_group("cabinet physical dimensions")
	cabinet_group.add_argument("--frames-per-cabinet", type=int, default=5,
	                           help="number of frames per cabinet (default: "
	                                "%(default)s)")
	cabinet_group.add_argument("--cabinet-dimensions", type=float, nargs=3,
	                           metavar=("W", "H", "D"),
	                           default=(0.600, 2.000, 0.250),
	                           help="cabinet physical dimensions in meters (default: "
	                                "%(default)s)")
	cabinet_group.add_argument("--cabinet-frame-offset", type=float, nargs=3,
	                           default=(0.085, 0.047, 0.0),
	                           metavar=("X", "Y", "Z"),
	                           help="physical offset of the left-top-front corner "
	                                "of the top frame from the left-top-front "
	                                "corner of a cabinet in meters (default: "
	                                "%(default)s)")
	cabinet_group.add_argument("--inter-cabinet-spacing", type=float,
	                           default=0.0, metavar=("S"),
	                           help="physical spacing between each cabinet in "
	                                "meters (default: %(default)s)")
	cabinet_group.add_argument("--num-cabinets", "-c", type=int, metavar="N",
	                           help="specify how many cabinets to spread the "
	                                "system over (default: the minimum possible)")
	cabinet_group.add_argument("--num-frames", "-f", type=int, metavar="N",
                             help="when only one cabinet is required, "
                                  "specifies how many frames within that "
                                  "cabinet the system should be spread "
                                  "across (default: the minimum possible)")


def get_cabinets_from_args(parser, args):
	"""For use with add_cabinet_args (and optionally add_topology_args).
	
	Get information about the dimensions of the cabinets in the system from the
	supplied arguments.
	
	Returns
	-------
	(:py:class:`spinner.cabinet.Cabinet`, num_frames)
		num_frames is the number of frames (per cabinet) to actually fill with
		boards.
	"""
	kwargs = {
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
	}
	
	# Work out number of boards to allow checking of num_cabinets and num_frames
	# (only possible if topology args are present)
	if hasattr(args, "num_boards") and args.num_boards is not None:
		num_boards = args.num_boards
	elif hasattr(args, "triads") and args.triads is not None:
		num_boards = 3 * args.triads[0] * args.triads[1]
	else:
		num_boards = None  # unknown!
	
	if args.num_cabinets is None and args.num_frames is None:
		# Try to pick an sensible default value if number of boards is known,
		# otherwise default to a single cabinet system.
		if num_boards is not None:
			num_cabinets, num_frames = min_num_cabinets(num_boards,
			                                            args.frames_per_cabinet,
			                                            args.boards_per_frame)
		else:
			num_cabinets = 1
			num_frames = args.frames_per_cabinet
	else:
		# Default to 1 cabinet
		if args.num_cabinets is None:
			num_cabinets = 1
		else:
			num_cabinets = args.num_cabinets
		
		# Default to the full number of frames
		if args.num_frames is None:
			num_frames = args.frames_per_cabinet
		else:
			num_frames = args.num_frames
			if num_frames > args.frames_per_cabinet:
				parser.error("more frames specified than fit in a cabinet")
			if num_cabinets > 1 and num_frames != args.frames_per_cabinet:
				parser.error("--num-frames must equal --frames-per-cabinet "
				             "when there is more than one cabinet")
	
	# Check that the number of cabinets/frames is sufficient for the number of
	# boards present (if known)
	if (num_boards is not None and
	    num_cabinets * num_frames * args.boards_per_frame < num_boards):
		parser.error("not enough cabinets/frames available for {} "
		             "boards".format(num_boards))
	
	kwargs["num_cabinets"] = num_cabinets
	
	try:
		return (Cabinet(**kwargs), num_frames)
	except ValueError as e:
		parser.error(e.args[0])


def add_histogram_args(parser):
	"""Add arguments for specifying the histogram of wire lengths (i.e.
	cabinets/frames) available for a given system."""
	histogram_group = parser.add_argument_group("wire length histogram options")
	histogram_mut_group = histogram_group.add_mutually_exclusive_group()
	histogram_mut_group.add_argument("--histogram-bins", "-H", type=int, metavar="N",
	                                 default=5,
	                                 help="number of bins to pack wire lengths into "
	                                      "in the histogram of wire lengths (default: "
	                                      "%(default)s)")


def get_histogram_from_args(parser, args):
	"""To be used with add_histogram_args.
	
	Check that the supplied arguments are valid and returns the number of bins
	requested.
	
	Returns
	-------
	int
		The number of bins to use in the wire-length histogram.
	"""
	if args.histogram_bins < 1:
		parser.error("--histogram-bins must be at least 1")
	return args.histogram_bins


def add_wire_length_args(parser):
	"""Add arguments for specifying sets of wire lengths available for a given
	system."""
	wire_length_group = parser.add_argument_group("available wire lengths")
	wire_length_group.add_argument("--wire-length", "-l", type=float, metavar="L",
	                               action="append", nargs="+",
	                               help="specify one or more available wire "
	                                    "lengths in meters")
	wire_length_group.add_argument("--minimum-wire-arc-height", type=float, metavar="H",
	                               default=0.05,
	                               help="the minimum height of the arc formed by a "
	                                    "wire connecting two boards in meters "
	                                    "(a heuristic for determining the slack "
	                                    "to allow when selecting wires)")


def get_wire_lengths_from_args(parser, args, mandatory=False):
	"""To be used with add_wire_length_args.
	
	Also used internally by get_histogram_from_args.
	
	Check that the supplied arguments are valid and then return the list of wire
	lengths supplied..
	
	Returns
	-------
	([float, ...], min_arc_height)
		Gives the wire lengths available (which may be empty) and the minimum arc
		length requested.
	"""
	if args.wire_length is None:
		wire_lengths = []
	else:
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
		
		wire_lengths = sorted(args.wire_length)
	
	if args.minimum_wire_arc_height < 0.0:
		parser.error("--minimum-wire-arc-height must be positive")
	
	if mandatory and not wire_lengths:
		parser.error("At least one --wire-length argument must be provided.")
	
	return (wire_lengths, args.minimum_wire_arc_height)


def add_image_args(parser):
	"""Add arguments for specifying output image filenames and dimensions."""
	image_group = parser.add_argument_group("image file parameters")
	image_group.add_argument("filename", type=str,
	                         help="filename to write the output to (.pdf or .png)")
	image_group.add_argument("width", type=float, nargs="?",
	                         help="width of the image in mm for PDF and pixels for "
	                              "PNG (defaults to 280 mm if PDF and 1000 px for PNG)")
	image_group.add_argument("height", type=float, nargs="?",
	                         help="height of the image in mm for PDF and pixels for "
	                              "PNG (if only width is given, output will be at "
	                              "most width wide and width tall)")
	


def get_image_from_args(parser, args, aspect_ratio=1.0):
	"""To be used with add_image_args.
	
	Check that the supplied arguments are valid and then return the filename, type
	and dimensions of the image to be created.
	
	Parameters
	----------
	aspect_ratio : float
		If the user does not fully specify the image size, what aspect ratio
		(width/height) should the image defined be?
	
	Returns
	-------
	output_filename, file_type, image_width, image_height
	"""
	output_filename = args.filename
	
	# Detect file-type from file-name
	if args.filename.lower().endswith(".png"):
		file_type = "png"
	elif args.filename.lower().endswith(".pdf"):
		file_type = "pdf"
	else:
		parser.error("filename must end in .png or .pdf")
	
	# Determine the size of the output image
	if args.width is None and args.height is None:
		# Width and height not specified, use default sizes
		if file_type == "png":
			args.width = 1000
		else:  # if file_type == "png":
			args.width = 280.0
	
	if args.width is not None and args.height is None:
		# Height is not specified, make the longest side as long as width and make
		# the whole image the same aspect ratio as the part of the system we're
		# focusing on
		if aspect_ratio < 1.0:
			# Tall image
			args.height = args.width
			args.width = args.height * aspect_ratio
		else:
			# Wide image
			args.height = args.width / aspect_ratio
	
	# Clamp to integers if PNG
	if file_type == "png":
		args.width = int(args.width)
		args.height = int(args.height)
	
	image_width = args.width
	image_height = args.height
	
	# Image dimensions must be non-zero and positive
	if image_width <= 0 or image_height <= 0:
		parser.error("image dimensions must be greater than 0")
	
	return (output_filename, file_type, image_width, image_height)


def add_bmp_args(parser):
	"""Add arguments for specifying a set of BMPs to connect to."""
	bmp_group = parser.add_argument_group("SpiNNaker BMP connection details")
	bmp_group.add_argument("--bmp", type=str, nargs=3, action="append",
	                       metavar=("CABINET", "FRAME", "HOSTNAME"),
	                       help="specify the hostname of a BMP to use to "
	                            "communicate with SpiNNaker boards in the given "
	                            "frame")


def get_bmps_from_args(parser, args, num_cabinets, num_frames):
	"""To be used with add_bmp_args.
	
	Check that the supplied arguments are valid and then return a dictionary
	mapping (cabinet, frame) tuples to hostnames.
	
	Either no arguments must be supplied or exactly one per frame.
	"""
	# Special case when no arguments supplied.
	if args.bmp is None:
		return {}
	else:
		bmp_hostnames = {}
		
		for cabinet, frame, hostname in args.bmp:
			# Check types
			if not cabinet.isdigit():
				parser.error("--bmp cabinet number must be a number")
			cabinet = int(cabinet)
			
			if not frame.isdigit():
				parser.error("--bmp frame number must be a number")
			frame = int(frame)
			
			# Check for duplicates
			if (cabinet, frame) in bmp_hostnames:
				parser.error("bmp hostname for cabinet {}, frame {} "
				             "specified multiple times".format(cabinet, frame))
			if hostname in itervalues(bmp_hostnames):
				parser.error("bmp hostname '{}' given for more than one frame".format(
					hostname))
			
			bmp_hostnames[(cabinet, frame)] = hostname
		
		# Check every frame is included
		missing = set((c, f)
		              for c in range(num_cabinets)
		              for f in range(num_frames)) - set(bmp_hostnames)
		extra = set(bmp_hostnames) - set((c, f)
		                                 for c in range(num_cabinets)
		                                 for f in range(num_frames))
		
		if missing:
			parser.error("BMP hostname missing for {}".format(  # pragma: no branch
				", ".join("C:{} F:{}".format(c, f) for c, f in missing)))
		elif extra:
			parser.error(  # pragma: no branch
				"unexpected BMP for {} which are not part of the system".format(
					", ".join("C:{} F:{}".format(c, f) for c, f in extra)))
		
		return bmp_hostnames


def add_subset_args(parser):
	"""Add arguments for specifying a subset of wires to connect."""
	subset_group = parser.add_argument_group(
		"wire subset selection",
		description="""
			These arguments allow the specificiation of subsets of wires
			to install, for example, selecting only particular wires
			within a particular cabinet or frame. If no subsets are
			specified, all wires will be included, otherwise the union
			of all specified subsets are included. Use '1.2.*' to select all wires
			between boards in cabinet 1, frame 2. Use '1.*.*' to select all wires
			between boards in cabinet 1. Use '1-2.*.*' to select all
			wires which cross between cabinets 1 and 2.
		"""
	)
	subset_group.add_argument("--subset", nargs="+", type=str, metavar="SUBSET",
	                    help="specify the subset of wires to include")


def get_subset_from_args(parser, args):
	"""To be used with add_subset_args.
	
	Check that the supplied arguments are valid and then return a function with
	the prototype fn(wire) -> bool where wire is a tuple ((c, f, b, d), (c, f, b,
	d), length).
	"""
	if args.subset is None:
		# Special case when no arguments supplied: accept everything
		return (lambda wire: True)
	else:
		rules = []
		for subset in args.subset:
			# Split into cabinet, frame and board rules
			parts = re.split(r"\s*[,.]\s*", subset)
			if len(parts) != 3:
				parser.error(
					"--subset arguments must be of the form '???.???.???'"
					", not {}".format(subset))
			
			rule_fragments = []
			for i, part in enumerate(parts):
				# For each part, work out the rule
				match = re.match(r"^("
				                   r"(?P<single>[0-9]+)|"  # Specific c/f/b
				                   r"((?P<from>[0-9]+)-(?P<to>[0-9]+))|"  # Between two c/f/b
				                   r"(?P<wildcard>[*])"  # Wildcard
				                 r")$", part)
				if not match:
					parser.error(
						"--subset components must be either 'N', 'N-M' or '*', "
						"not {}".format(part))
				elif match.group("single"):
					value = int(match.group("single"))
					rule_fragments.append(
						lambda wire, i=i, value=value: (wire[0][i] == value and
					                                  wire[1][i] == value))
				elif match.group("from") and match.group("to"):
					frm = int(match.group("from"))
					to = int(match.group("to"))
					rule_fragments.append(
						lambda wire, i=i, frm=frm, to=to: (wire[0][i] == frm and
					                                     wire[1][i] == to)
					                                    or (wire[1][i] == frm and
					                                        wire[0][i] == to))
				elif match.group("wildcard"):
					# Don't append any rules: the wildcard always matches
					pass
				else:  # pragma: no cover
					assert False
			
			rules.append(lambda wire, rule_fragments=rule_fragments:
			             all(rf(wire) for rf in rule_fragments))
		
		return (lambda wire: any(r(wire) for r in rules))




if __name__=="__main__":  # pragma: no cover
	# This file when run as a script acts as a quick proof-of-concept of all
	# argument parsing capabilities
	import argparse
	parser = argparse.ArgumentParser()
	add_image_args(parser)
	add_topology_args(parser)
	add_cabinet_args(parser)
	add_histogram_args(parser)
	add_bmp_args(parser)
	add_subset_args(parser)
	
	args = parser.parse_args()
	print(get_image_from_args(parser, args, 0.5))
	print(get_topology_from_args(parser, args))
	print(get_cabinets_from_args(parser, args))
	print(get_histogram_from_args(parser, args))
	print(get_bmps_from_args(parser, args, 2, 2))
	print(get_subset_from_args(parser, args))
