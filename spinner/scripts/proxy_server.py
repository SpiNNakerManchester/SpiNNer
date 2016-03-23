#!/usr/bin/env python

"""
A proxy server which enables multiple interactive wiring sessions to interact
with the same SpiNNaker machine.
"""

import argparse

import logging

from spinner.scripts import arguments

from spinner.probe import WiringProbe

from spinner.proxy import ProxyServer, DEFAULT_PORT

from rig.machine_control import BMPController


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Start a proxy server to enable multiple interactive wiring "
		            "sessions to interact with the same SpiNNaker machine.")
	arguments.add_version_args(parser)
	
	parser.add_argument("--host", "-H", type=str, default="",
	                    help="Host interface to listen on (default: any)")
	
	parser.add_argument("--port", "-p", type=int, default=DEFAULT_PORT,
	                    help="Port listen on (default: %(default)d)")
	
	parser.add_argument("--verbose", "-v", action="count", default=0,
	                    help="Increase verbosity.")
	
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_bmp_args(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	bmp_ips = arguments.get_bmps_from_args(parser, args,
	                                       cabinet.num_cabinets,
	                                       num_frames)
	
	if cabinet.num_cabinets == num_frames == 1:
		num_boards = 3 * w * h
	else:
		num_boards = cabinet.boards_per_frame
	
	# Set verbosity level
	if args.verbose == 1:
		logging.basicConfig(level=logging.INFO)
	elif args.verbose >= 2:
		logging.basicConfig(level=logging.DEBUG)
	
	# Create a BMP connection
	if len(bmp_ips) == 0:
		parser.error("All BMPs must be supplied using --bmp")
	bmp_controller = BMPController(bmp_ips)
	
	# Create a wiring probe
	wiring_probe = WiringProbe(bmp_controller,
	                           cabinet.num_cabinets,
	                           num_frames,
	                           num_boards)
	
	proxy_server = ProxyServer(bmp_controller, wiring_probe,
	                           args.host, args.port)
	
	print("Proxy server starting...")
	proxy_server.main()
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

