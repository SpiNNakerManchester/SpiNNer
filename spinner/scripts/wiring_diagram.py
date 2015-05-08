#!/usr/bin/env python

"""Generate illustrations of SpiNNaker machine wiring."""

import argparse

import cairocffi as cairo

from spinner.diagrams.machine import MachineDiagram

from spinner.topology import Direction

from spinner.utils import folded_torus

from spinner import transforms

from spinner.scripts import arguments


"""
Number of points in a millimetre.
"""
MM_TO_PT = 2.83464567


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


def add_arguments(parser):
	"""
	Add arguments which specify the output format and what is to be drawn.
	"""
	
	parser.add_argument("filename", type=str,
	                    help="filename to write the diagram to (.pdf and .png "
	                          "supported)")
	parser.add_argument("width", type=float, nargs="?",
	                    help="width of the image in mm for PDF and pixels for "
	                         "PNG (defaults to 280 mm if PDF and 1000 px for PNG)")
	parser.add_argument("height", type=float, nargs="?",
	                    help="height of the image in mm for PDF and pixels for "
	                         "PNG (if only WIDTH is given, output will be at "
	                         "most WIDTH wide and WIDTH tall)")
	
	parser.add_argument("--wire-thickness", choices="thick normal thin".split(),
	                    default="normal",
	                    help="set the thickness of wires drawn (default: "
	                         "%(default)s)")
	
	parser.add_argument("--highlight", action=CabinetAction(4, append=True),
	                    help="highlight a particular cabinet/frame/board/socket "
	                         "with a red border")
	
	parser.add_argument("--hide-labels", "-L", action="store_true", default=False,
	                    help="hide board/frame/cabinet number labels")
	
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)


def get_arguments(parser, args):
	"""
	Validate and unpack the arguments added by add_arguments.
	"""
	# Handle "standard" arguments
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	output_filename = args.filename
	
	# Detect file-type from file-name
	if args.filename.lower().endswith(".png"):
		file_type = "png"
	elif args.filename.lower().endswith(".pdf"):
		file_type = "pdf"
	else:
		parser.error("filename must end in .png or .pdf")
	
	# Determine the set of cabinets/frames/boards to focus on and the aspect ratio
	# of the resulting part of the system (to enable automatic width/height
	# determination later)
	if cabinet.num_cabinets == 1 and num_frames == 1:
		focus = (0, 0, slice(0, 3 * w * h))
		dimensions = cabinet.get_dimensions(boards=3 * w * h)
	elif cabinet.num_cabinets == 1:
		focus = (0, slice(0, num_frames))
		dimensions = cabinet.get_dimensions(frames=num_frames)
	else:
		focus = (slice(0, cabinet.num_cabinets), )
		dimensions = cabinet.get_dimensions()
	aspect_ratio = float(dimensions.x) / float(dimensions.y)
	
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
	
	wire_thickness = args.wire_thickness
	highlights = args.highlight or []
	hide_labels = args.hide_labels
	
	return ((w, h), transformation, uncrinkle_direction, folds,
	        cabinet, num_frames,
	        output_filename, file_type, image_width, image_height,
	        focus, wire_thickness, highlights, hide_labels)


class PDFContext(object):
	"""A context manager which creates a Cairo PDF context."""
	
	def __init__(self, filename, width, height):
		"""Context manager for a PDF context with the specified filename and with
		all units given in mm.
		"""
		self.filename = filename
		self.width = width
		self.height = height
	
	def __enter__(self):
		surface = cairo.PDFSurface(self.filename,
		                           self.width * MM_TO_PT,
		                           self.height * MM_TO_PT)
		self.ctx = cairo.Context(surface)
		# Make the base unit mm.
		self.ctx.scale(MM_TO_PT, MM_TO_PT)
		return self.ctx
	
	def __exit__(self, type, value, traceback):
		self.ctx.show_page()


class PNGContext(object):
	"""A context manager which creates a Cairo PNG context."""
	
	def __init__(self, filename, width, height):
		"""Context manager for a PDF context with the specified filename and with
		all units given in pixels.
		"""
		self.filename = filename
		self.width = width
		self.height = height
	
	def __enter__(self):
		self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
		                                  self.width,
		                                  self.height)
		ctx = cairo.Context(self.surface)
		return ctx
	
	def __exit__(self, type, value, traceback):
		self.surface.write_to_png(self.filename)


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Generate illustrations of SpiNNaker machine wiring.")
	add_arguments(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds, \
		cabinet, num_frames, \
		output_filename, file_type, image_width, image_height, \
		focus, wire_thickness, highlights, hide_labels =\
			get_arguments(parser, args)
	
	# Generate folded system
	hex_boards, folded_boards = folded_torus(w, h,
	                                         transformation,
	                                         uncrinkle_direction,
	                                         folds)
	
	# Divide into cabinets
	cabinetised_boards = transforms.cabinetise(folded_boards,
	                                           cabinet.num_cabinets,
	                                           num_frames,
	                                           cabinet.boards_per_frame)
	cabinetised_boards = transforms.remove_gaps(cabinetised_boards)
	
	# Set up diagram
	md = MachineDiagram(cabinet)
	
	# Add labels
	if not hide_labels:
		for cabinet_num in range(cabinet.num_cabinets):
			md.add_label(cabinet_num, cabinet_num)
			for frame_num in range(cabinet.frames_per_cabinet):
				md.add_label(frame_num, cabinet_num, frame_num)
				for board_num in range(cabinet.boards_per_frame):
					md.add_label(board_num, cabinet_num, frame_num, board_num)
	
	# Add highlights
	for highlight in highlights:
		md.add_highlight(*highlight, width=cabinet.board_dimensions.x/3.0)
	
	# Add wires
	wire_thickness_m = {
		"thick" : cabinet.board_dimensions.x / 5,
		"normal" : cabinet.board_dimensions.x / 10,
		"thin" : cabinet.board_dimensions.x / 20,
	}[wire_thickness]
	b2c = dict(cabinetised_boards)
	for direction in [Direction.north, Direction.west, Direction.north_east]:
		for b, c in cabinetised_boards:
			ob = b.follow_wire(direction)
			oc = b2c[ob]
			md.add_wire((c.cabinet, c.frame, c.board, direction),
			            (oc.cabinet, oc.frame, oc.board, direction.opposite),
			            width=wire_thickness_m)
	
	# Render the image
	Context = {"png": PNGContext, "pdf": PDFContext}[file_type]
	with Context(output_filename, image_width, image_height) as ctx:
		md.draw(ctx, image_width, image_height, *focus, hide_unfocused=True)
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

