#!/usr/bin/env python

"""
An interactive graphical program for guiding a user through the process of
wiring a SpiNNaker machine.
"""

import sys

import argparse

import os.path

from spinner.utils import folded_torus

from spinner import transforms

from spinner.scripts import arguments

from spinner.plan import generate_wiring_plan, flatten_wiring_plan

from spinner.diagrams.interactive_wiring_guide import InteractiveWiringGuide

from spinner.probe import WiringProbe

from spinner.timing_logger import TimingLogger

from rig.machine_control import BMPController


def main(args=None):
	parser = argparse.ArgumentParser(
		description="Interactively guide the user through the process of wiring up a "
		            "SpiNNaker machine.")
	arguments.add_version_args(parser)
	
	parser.add_argument("--no-tts", action="store_true", default=False,
	                    help="disable text-to-speech announcements of wiring "
	                         "steps")
	
	parser.add_argument("--no-auto-advance", action="store_true", default=False,
	                    help="disable auto-advancing through wiring steps")
	
	parser.add_argument("--fix", action="store_true", default=False,
	                    help="detect errors in existing wiring and just show "
	                         "corrective steps")
	
	parser.add_argument("--log", type=str, metavar="LOGFILE",
	                    help="record the times at which each cable is installed")
	
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	arguments.add_wire_length_args(parser)
	arguments.add_bmp_args(parser)
	
	# Process command-line arguments
	args = parser.parse_args(args)
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)
	
	wire_lengths, min_arc_height = arguments.get_wire_lengths_from_args(
		parser, args, mandatory=True)
	
	bmp_ips = arguments.get_bmps_from_args(parser, args,
	                                       cabinet.num_cabinets,
	                                       num_frames)
	
	if cabinet.num_cabinets == num_frames == 1:
		num_boards = 3 * w * h
	else:
		num_boards = cabinet.boards_per_frame
	
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
	
	# Focus on only the boards which are part of the system
	if cabinet.num_cabinets > 1:
		focus = [slice(0, cabinet.num_cabinets)]
	elif num_frames > 1:
		focus = [0, slice(0, num_frames)]
	else:
		focus = [0, 0, slice(0, w*h*3)]
	
	
	# Generate wiring plan
	wires_between_boards, wires_between_frames, wires_between_cabinets =\
		generate_wiring_plan(cabinetised_boards, physical_boards,
		                     cabinet.board_wire_offset, wire_lengths, min_arc_height)
	flat_wiring_plan = flatten_wiring_plan(wires_between_boards,
	                                       wires_between_frames,
	                                       wires_between_cabinets,
	                                       cabinet.board_wire_offset)
	
	# Create a BMP connection
	if len(bmp_ips) == 0:
		if args.fix:
			parser.error("--fix requires that all BMPs be listed")
		bmp_controller = None
		wiring_probe = None
	else:
		bmp_controller = BMPController(bmp_ips)
	
	# Create a wiring probe
	if bmp_controller is not None and (not args.no_auto_advance or args.fix):
		wiring_probe = WiringProbe(bmp_controller,
		                           cabinet.num_cabinets,
		                           num_frames,
		                           num_boards)
	
	# Create a TimingLogger if required
	if args.log:
		if os.path.isfile(args.log):
			logfile = open(args.log, "a")
			add_header = False
		else:
			logfile = open(args.log, "w")
			add_header = True
		timing_logger = TimingLogger(logfile, add_header)
	else:
		logfile = None
		timing_logger = None
	
	# Convert wiring plan into cabinet coordinates
	b2c = dict(cabinetised_boards)
	wires = []
	for ((src_board, src_direction), (dst_board, dst_direction), wire_length) \
	    in flat_wiring_plan:
		
		sc, sf, sb = b2c[src_board]
		dc, df, db = b2c[dst_board]
		wires.append(((sc, sf, sb, src_direction),
		              (dc, df, db, dst_direction),
		              wire_length))
	
	if not args.fix:
		# If running normally, just run through the full set of wires
		wiring_plan = wires
	else:
		# If running in fix mode, generate a list of fixes to make
		correct_wires = set((src, dst) for src, dst, length in wires)
		actual_wires = set(wiring_probe.discover_wires())
		
		to_remove = actual_wires - correct_wires
		to_add = correct_wires - actual_wires
		
		# Remove all bad wires first, then re-add good ones (note ordering now is
		# just reset to cabinets right-to-left, frames top-to-bottom and boards
		# left-to-right).
		wiring_plan = [(src, dst, None) for src, dst in sorted(to_remove)]
		for src, dst, length in sorted(wires):
			if (src, dst) in to_add:
				wiring_plan.append((src, dst, length))

	
	# Intialise the GUI and launch the mainloop
	ui = InteractiveWiringGuide(cabinet=cabinet,
	                            wire_lengths=wire_lengths,
	                            wires=wiring_plan,
	                            bmp_controller=bmp_controller,
	                            use_tts=not args.no_tts,
	                            focus=focus,
	                            wiring_probe=wiring_probe,
	                            auto_advance=not args.no_auto_advance,
	                            timing_logger=timing_logger)
	ui.mainloop()
	
	if logfile is not None:
		logfile.close()
	
	return 0


if __name__=="__main__":  # pragma: no cover
	import sys
	sys.exit(main())

