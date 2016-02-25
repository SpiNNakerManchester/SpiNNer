#!/usr/bin/env python

"""
A tool which enumerates all connections to be made in a machine.
"""

import sys

import argparse

from spinner.utils import folded_torus

from spinner import transforms

from spinner.scripts import arguments

from spinner.plan import generate_wiring_plan, flatten_wiring_plan


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Textually enumerate every connection required in a machine.")
	
	parser.add_argument("--sort-by", "-s",
	                    choices=["installation-order", "board", "wire-length"],
	                    default="board",
	                    help="Specifies the order the connections should be "
	                         "listed in the file: installation-order sorts in "
	                         "the most sensible order for installation, "
	                         "board lists wires on a board-by-board basis, "
	                         "wire-length lists in order of wire length.")
	
	arguments.add_version_args(parser)
	
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_wire_length_args(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	wire_lengths, min_slack = arguments.get_wire_lengths_from_args(
		parser, args, mandatory=True)
	
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
	physical_boards = transforms.cabinet_to_physical(cabinetised_boards, cabinet)
	
	# Generate wiring plan
	wires_between_boards, wires_between_frames, wires_between_cabinets =\
		generate_wiring_plan(cabinetised_boards, physical_boards,
		                     cabinet.board_wire_offset, wire_lengths, min_slack)
	flat_wiring_plan = flatten_wiring_plan(wires_between_boards,
	                                       wires_between_frames,
	                                       wires_between_cabinets,
	                                       cabinet.board_wire_offset)
	
	# Convert wiring plan into cabinet coordinates
	b2c = dict(cabinetised_boards)
	wires = []
	for ((src_board, src_direction), (dst_board, dst_direction), wire_length) \
	    in flat_wiring_plan:
		
		sc, sf, sb = b2c[src_board]
		dc, df, db = b2c[dst_board]
		wires.append(((sc, sf, sb, src_direction),
		              (dc, df, db, dst_direction),
		              wire_length, src_board, dst_board))
	
	b2p = dict(physical_boards)
	
	# Order as requested on the command-line
	if args.sort_by == "board":
		wires = sorted(wires)
	elif args.sort_by == "wire-length":
		wires = sorted(wires, key=(lambda w: (w[2], w[:2])))
	elif args.sort_by == "installation-order":  # pragma: no branch
		pass  # List is initially in assembly order
	
	print("C  F  B  Socket      C  F  B  Socket      Length")
	print("-- -- -- ----------  -- -- -- ----------  ------")
	for ((sc, sf, sb, src_direction), (dc, df, db, dst_direction), wire_length, src_board, dst_board) in wires:
		print("{:2d} {:2d} {:2d} {:10s}  {:2d} {:2d} {:2d} {:10s}  {:0.2f}".format(
			sc, sf, sb, src_direction.name.replace("_", " "),
			dc, df, db, dst_direction.name.replace("_", " "),
			wire_length))
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

