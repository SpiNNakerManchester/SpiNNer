#!/usr/bin/env python

"""Print basic statistics about a specified machine's topology."""

import argparse

from spinner.scripts import arguments

from spinner.scripts.markdown_gen import heading, table


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Print basic topological statistics for a specified "
		            " configuration of boards.")
	arguments.add_version_args(parser)
	arguments.add_topology_args(parser)
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	out = ""
	out += heading("Topology Statistics", 1)
	out += "\n"
	out += table([["Measurement", "Value", "Unit"],
	              ["Network dimensions", "{}x{}".format(w*12, h*12), "chips"],
	              ["Board array", "{}x{}".format(w, h), "triad"],
	              ["Number of boards", 3 * w * h, ""],
	              ["Number of cables", 3 * w * h * 3, ""],
	              ["Number of chips", 3 * w * h * 48, ""],
	              ["Number of cores", 3 * w * h * 48 * 18, ""],
	             ])
	
	print(out)
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())
