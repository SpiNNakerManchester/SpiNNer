"""Standard argument parsing routines for SpiNNer scripts."""

from spinner.utils import \
	ideal_system_size, \
	folded_torus, folded_torus_with_minimal_wire_length, \
	min_num_cabinets

from spinner.cabinet import Cabinet

from spinner import board
from spinner import topology
from spinner import coordinates
from spinner import transforms


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
	folding_group.add_argument("--folds", "-F", type=int, nargs=2,
	                           default=None, metavar=("X", "Y"),
	                           help="the number of pieces to fold into in each "
	                                "dimension (default: (2, 2)) ignored if "
	                                "--transformation is not given")


def get_topology_from_args(parser, args):
	"""To be used with add_topology_args.
	
	Check that the supplied arguments are valid and build a system of boards
	according to the specification given.
	
	Returns
	-------
	((w, h), hex_boards, folded_boards)
		(w, h) is the dimensions of the system in triads
		
		hex_boards is a list of tuples (board, Hexagonal(x, y)) giving the logical
		coordinates for each board on a 2D hexagonal grid.
		
		folded_boards is a list of tuples (board, Cartesian2D(x, y)) giving the
		coordinates of the boards laid out such that wirelength is minimised.
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
	if args.transformation is None:
		if args.folds is not None:
			parser.error("--folds cannot be used without --transformation")
		hex_boards, folded_boards = folded_torus_with_minimal_wire_length(w, h)
	else:
		if args.folds is None:
			args.folds = (2, 2)
		
		if args.folds[0] <= 0 or args.folds[1] <= 0:
			parser.error("number of pieces to fold into must be at least 1")
		
		hex_boards, folded_boards = folded_torus(
			w, h, args.transformation, args.folds)
	
	return ((w, h), hex_boards, folded_boards)


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


if __name__=="__main__":  # pragma: no cover
	# This file when run as a script acts as a quick proof-of-concept of all
	# argument parsing capabilities
	import argparse
	parser = argparse.ArgumentParser()
	add_topology_args(parser)
	add_cabinet_args(parser)
	
	args = parser.parse_args()
	print(get_topology_from_args(parser, args))
	print(get_cabinets_from_args(parser, args))
