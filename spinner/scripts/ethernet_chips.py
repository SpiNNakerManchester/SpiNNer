#!/usr/bin/env python

"""Produce CSV listings of Ethernet connected chip positions."""

import argparse

from spinner.diagrams.machine_map import draw_machine_map, \
	get_machine_map_aspect_ratio

from spinner.utils import folded_torus

from spinner import transforms
from spinner import topology

from spinner.scripts import arguments
from spinner.scripts.contexts import PDFContextManager, PNGContextManager


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Produce CSV listings of Ethernet connected chip physical and "
		            "network positions.")
	arguments.add_version_args(parser)
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
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
	
	# Generate the output
	print("cabinet,frame,board,x,y")
	b2c = dict(cabinetised_boards)
	for board, hex_coord in sorted(hex_boards, key=(lambda v: topology.to_xy(v[1]))):
		x, y = topology.to_xy(topology.board_to_chip(hex_coord))
		c, f, b = b2c[board]
		print(",".join(map(str, [c,f,b, x,y])))
	
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())


