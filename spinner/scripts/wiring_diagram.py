#!/usr/bin/env python

"""Generate illustrations of SpiNNaker machine wiring."""

import argparse

from spinner.diagrams.machine import MachineDiagram

from spinner.topology import Direction

from spinner.utils import folded_torus

from spinner import transforms
from spinner import topology

from spinner.scripts import arguments

from spinner.scripts.contexts import PDFContextManager, PNGContextManager


def add_diagram_arguments(parser):
	"""
	Add arguments which specify the output format and what is to be drawn.
	"""
	parser.add_argument("--wire-thickness", choices="thick normal thin".split(),
	                    default="normal",
	                    help="set the thickness of wires drawn (default: "
	                         "%(default)s)")
	
	parser.add_argument("--highlight", action=arguments.CabinetAction(4, append=True),
	                    help="highlight a particular cabinet/frame/board/socket "
	                         "with a red border")
	
	parser.add_argument("--hide-labels", "-L", action="store_true", default=False,
	                    help="hide socket/board/frame/cabinet number labels")


def get_diagram_arguments(parser, args, w, h, cabinet, num_frames):
	"""
	Validate and unpack the arguments added by add_diagram_arguments.
	"""
	# Determine the set of cabinets/frames/boards to focus on and the aspect ratio
	# of the resulting part of the system (to enable automatic image width/height
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
	
	wire_thickness = args.wire_thickness
	highlights = args.highlight or []
	hide_labels = args.hide_labels
	
	return (aspect_ratio, focus, wire_thickness, highlights, hide_labels)


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Generate illustrations of SpiNNaker machine wiring.")
	arguments.add_version_args(parser)
	arguments.add_image_args(parser)
	add_diagram_arguments(parser)
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_subset_args(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames =\
		arguments.get_cabinets_from_args(parser, args)
	
	aspect_ratio, focus, wire_thickness, highlights, hide_labels =\
		get_diagram_arguments(parser, args, w, h, cabinet, num_frames)
	
	output_filename, file_type, image_width, image_height =\
		arguments.get_image_from_args(parser, args, aspect_ratio)
	
	wire_filter = arguments.get_subset_from_args(parser, args)
	
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
	
	# Create lookup from cabinet coord to chip x/y to enable labelling of boards
	b2cab = dict(cabinetised_boards)
	b2chip = dict((b, topology.to_xy(topology.board_to_chip(c)))
	              for b, c in hex_boards)
	cab2chip = dict((b2cab[b], b2chip[b]) for b, c in cabinetised_boards)
	
	# Add labels
	if not hide_labels:
		for cabinet_num in range(cabinet.num_cabinets):
			md.add_label(cabinet_num, cabinet_num)
			for frame_num in range(cabinet.frames_per_cabinet):
				md.add_label(frame_num, cabinet_num, frame_num)
				for board_num in range(cabinet.boards_per_frame):
					# Only label boards which are actually part of the system
					xy = cab2chip.get((cabinet_num, frame_num, board_num), None)
					if xy is not None:
						md.add_label("{} ({},{})".format(board_num, xy.x, xy.y),
						             cabinet_num, frame_num, board_num)
						for socket in Direction:
							name = "".join(w[0] for w in socket.name.split("_")).upper()
							md.add_label(name, cabinet_num, frame_num, board_num, socket,
							             rgba=(1.0, 1.0, 1.0, 0.7))
	
	# Add highlights
	for highlight in highlights:
		md.add_highlight(*highlight, width=cabinet.board_dimensions.x/3.0)
	
	# Add wires
	wire_thickness_m = {
		"thick" : cabinet.board_dimensions.x / 5.0,
		"normal" : cabinet.board_dimensions.x / 10.0,
		"thin" : cabinet.board_dimensions.x / 20.0,
	}[wire_thickness]
	b2c = dict(cabinetised_boards)
	for direction in [Direction.north, Direction.west, Direction.north_east]:
		for b, c in cabinetised_boards:
			ob = b.follow_wire(direction)
			oc = b2c[ob]
			
			src = (c.cabinet, c.frame, c.board, direction)
			dst = (oc.cabinet, oc.frame, oc.board, direction.opposite)
			if wire_filter((src, dst)):
				md.add_wire(src, dst, width=wire_thickness_m)
	
	# Render the image
	Context = {"png": PNGContextManager,
	           "pdf": PDFContextManager}[file_type]
	with Context(output_filename, image_width, image_height) as ctx:
		md.draw(ctx, image_width, image_height, *(((list(focus) + [None]*3)[:3])*2))
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

