#!/usr/bin/env python

"""Print basic statistics about a specified machine's wiring."""

import argparse

from spinner.scripts import arguments

from spinner.scripts.markdown_gen import heading, table


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Print basic topological statistics for a specified "
		            " configuration of boards.")
	arguments.add_topology_args(parser)
	args = parser.parse_args(args)
	(w, h), hex_boards, folded_boards =\
		arguments.get_topology_from_args(parser, args)
	
	max_x = max(x for b, (x, y) in folded_boards)
	max_y = max(y for b, (x, y) in folded_boards)
	
	out = ""
	out += heading("Topology Statistics", 1)
	out += "\n"
	out += table([["Parameter", "Value", "Unit"],
	              ["Network dimensions", "{}x{}".format(w*12, h*12), "chips"],
	              ["Board array", "{}x{}".format(w, h), "traids"],
	              ["Folded array", "{}x{}".format(max_x+1, max_y+1), "boards"],
	              ["Number of cables", 3 * w * h, ""],
	              ["Number of boards", 3 * w * h * 3, ""],
	              ["Number of chips", 3 * w * h * 48, ""],
	              ["Number of cores", 3 * w * h * 48 * 18, ""],
	             ])
	
	print(out)
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())
