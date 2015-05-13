#!/usr/bin/env python

"""Print basic statistics about a specified machine's wiring."""

import argparse

from six import iteritems, itervalues

from spinner.topology import Direction

from spinner.utils import folded_torus

from spinner import metrics
from spinner import transforms

from spinner.scripts import arguments

from spinner.scripts.markdown_gen import heading, table


def avg_wire_length_table(boards, units, wire_offsets=None):
	"""Render a table of average wire lengths for the given system."""
	wire_lengths = {d: list(metrics.wire_lengths(boards, d, wire_offsets))
	                for d in [Direction.north_east,
	                          Direction.north,
	                          Direction.west]}
	mean_wire_lengths = {d: sum(wl)/len(wl) for d, wl in iteritems(wire_lengths)}
	mean_wire_length = sum(itervalues(mean_wire_lengths))/len(mean_wire_lengths)
	max_wire_lengths = {d: max(wl) for d, wl in iteritems(wire_lengths)}
	max_wire_length = max(itervalues(max_wire_lengths))
	
	return table([["Parameter", "Value", "Unit"],
	              ["System dimensions",
	               " x ".join("%0.2f"%v for v in metrics.dimensions(boards)),
	               units],
	              ["Mean wire length", "%0.2f"%mean_wire_length, units],
	              ["  NE/SW", "  %0.2f"%mean_wire_lengths[Direction.north_east], units],
	              ["  N/S", "  %0.2f"%mean_wire_lengths[Direction.north], units],
	              ["  W/E", "  %0.2f"%mean_wire_lengths[Direction.west], units],
	              ["Maximum wire length", "%0.2f"%max_wire_length, units],
	              ["  NE/SW", "  %0.2f"%max_wire_lengths[Direction.north_east], units],
	              ["  N/S", "  %0.2f"%max_wire_lengths[Direction.north], units],
	              ["  W/E", "  %0.2f"%max_wire_lengths[Direction.west], units],
	             ])


def wire_counts_table(boards):
	"""Render a table which displays counts of wires."""
	table_data = [["Axis", "Total", "Between Cabinets", "Between Frames", "Within Frames"]]
	
	totals = [0, 0, 0, 0]
	
	for name, axis in [("NE/SW", Direction.north_east),
	                   ("N/S", Direction.north),
	                   ("W/E", Direction.west)]:
		counts = metrics.count_wires(boards, axis)
		table_data.append([name, sum(counts)] + list(counts))
		
		for col_num in range(4):
			totals[col_num] += table_data[-1][col_num + 1]
	
	table_data.append(["All"] + totals)
	
	return table(table_data)


def wire_length_table(boards, bins, min_arc_height,
                      wire_offsets=None, bar_length=15):
	"""Render a histogram of wire lengths in the system."""
	wire_lengths = sum((list(metrics.wire_lengths(boards, d, wire_offsets))
	                    for d in [Direction.north_east,
	                              Direction.north,
	                              Direction.west]),
	                   [])
	
	bin_counts, bin_max_arc_heights = metrics.wire_length_histogram(wire_lengths, min_arc_height, bins)
	
	data = [["Range (meters)", "Count", "Histogram", "Max Arc Height (meters)"]]
	
	max_count = max(itervalues(bin_counts))
	last_bin = 0.0
	for bin in sorted(bin_counts):
		count = bin_counts[bin]
		max_arc_height = bin_max_arc_heights[bin]
		data.append(("%0.2f < x <= %0.2f"%(last_bin, bin),
		             count,
		             "#"*((count * bar_length + max_count - 1) // max_count),
		             "%0.2f"%max_arc_height))
		last_bin = bin
	
	return table(data)


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Print basic wiring statistics for a specified "
		            " configuration of boards.")
	arguments.add_version_args(parser)
	arguments.add_topology_args(parser)
	arguments.add_histogram_args(parser)
	arguments.add_wire_length_args(parser)
	arguments.add_cabinet_args(parser)
	
	# Process and display command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	histogram_bins = arguments.get_histogram_from_args(parser, args)
	wire_lengths, min_arc_height =\
		arguments.get_wire_lengths_from_args(parser, args)
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	print(heading("Wiring Statistics", 1))
	print(heading("Folding Parameters", 2))
	print(table([["Parameter", "Value", "Unit"],
	             ["Number of boards", 3 * w * h, ""],
	             ["System dimensions", "{}x{}".format(w, h), "triads"],
	             ["Transformation", transformation, ""],
	             ["Uncrinkle Direction", uncrinkle_direction, ""],
	             ["Folds", "{}x{}".format(*folds), "pieces"],
	             ["Number of cabinets", cabinet.num_cabinets, ""],
	             ["Number of frames-per-cabinet", num_frames, ""],
	             ["Number of boards-per-frame", cabinet.boards_per_frame, ""],
	            ]))
	
	# Generate folded system and report wire-lengths after folding
	hex_boards, folded_boards = folded_torus(w, h,
	                                         transformation,
	                                         uncrinkle_direction,
	                                         folds)
	print(heading("Non-cabinetised measurements", 2))
	print(avg_wire_length_table(folded_boards, "boards"))
	
	# Divide into cabinets and report crossings
	cabinetised_boards = transforms.cabinetise(folded_boards,
	                                           cabinet.num_cabinets,
	                                           num_frames,
	                                           cabinet.boards_per_frame)
	cabinetised_boards = transforms.remove_gaps(cabinetised_boards)
	
	print(heading("Inter-cabinet/Inter-frame wiring", 2))
	print(wire_counts_table(cabinetised_boards))
	
	# Map to real, physical cabinets and measure wire lengths
	physical_boards = transforms.cabinet_to_physical(cabinetised_boards, cabinet)
	
	print(heading("Cabinetised measurements", 2))
	print("All wire lengths described in this section do not include any slack.\n")
	print(avg_wire_length_table(physical_boards, "meters",
	                            cabinet.board_wire_offset))
	
	# Generate a histogram of wire lengths
	print(heading("Wire length histogram", 2))
	print("Wire lengths are chosen to include enough slack such that each wire "
	      "forms an arc protruding no less than {} meters from the "
	      "system.\n".format(min_arc_height))
	print(wire_length_table(physical_boards,
	                        wire_lengths if wire_lengths else histogram_bins,
	                        min_arc_height,
	                        cabinet.board_wire_offset))
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

