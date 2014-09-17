#!/usr/bin/env python

"""
A tool for verifying the correctness of a SpiNNaker wiring scheme.

When used on the commandline communicates with the FPGAs on each board via the
FPGAs to discover the connectivity of the system. The discovered links are then
compared with an intended wiring scheme and corrective instructions are issued
using the same interface as the interactive_wiring_guide.
"""

import time
import random
import struct

from collections import defaultdict

from spinnman.transceiver import create_transceiver_from_hostname

from model.topology import EAST, NORTH_EAST, NORTH, WEST, SOUTH_WEST, SOUTH

from model.metrics import physical_wire_length


class WiringProbe(object):
	"""
	An object which probes a set of SpiNNaker boards to discover the connectivity
	between them. This tool uses the debugging facility of the board-to-board
	links to transmit/receive small values in their idle packets. As a result, the
	system should not be booted while performing link probing to ensure the links
	remain idle.
	
	Users should be sure to call the close() method to close connections and kill
	threads started by SpiNNMan.
	"""
	
	# Number of bits in an ID which can be applied to a board
	NUM_ID_BITS = 16
	
	
	# A dictionary {direction: (fpga_num, reg_addr_prefix), ...} which gives for
	# each link direction the index of the responsible FPGA and the prefix for
	# register bank addresses for the particular link hardware within that FPGA.
	# The reg_addr_prefix will come in the form of a value to bitwise-OR with the
	# desired register address. Note: register addresses are 30-bits long (due to
	# two bottom bits being used for direction).
	BOARD_FPGAS = {
		SOUTH:      (0, 0x00010000),
		EAST:       (0, 0x00000000),
		WEST:       (1, 0x00010000),
		SOUTH_WEST: (1, 0x00000000),
		NORTH_EAST: (2, 0x00010000),
		NORTH:      (2, 0x00000000),
	}
	
	# Register bank addresses for the "IDle Sentinel Input/Output" registers. The
	# IDSO register specifies a value to be transmitted as part of link idle
	# packets. IDSI indicates the value transmitted in the most recently received
	# idle packet.
	IDSO_REG = 19
	IDSI_REG = 20
	
	def __init__(self, cabinet_system, bmp_ips):
		"""
		Takes a cabinet system describing the system to probe along with a
		dictionary {board_position: ip} where board_position is either a tuple
		(cabinet, rack, slot) or (cabinet, rack) where the former should be used if
		both are available.
		"""
		self.cabinet_system = cabinet_system
		self.bmp_ips        = bmp_ips
		
		# A mapping from board_position (as in bmp_ips) to connected SpiNNMan
		# Transceiver objects.
		self.transceivers = {}
		self._connect_transceivers()
		
		# A dictionary {link_id: ((c,r,s),d), ...} and visa versa.
		self.id_to_link = {}
		self.link_to_id = {}
		self._assign_link_ids()
		
		# Write all link IDs into the system
		self._write_link_ids()
	
	
	def _connect_transceivers(self):
		"""
		Set up a Transceiver for every board.
		"""
		for board_position, ip in self.bmp_ips.items():
				if board_position not in self.transceivers:
					self.transceivers[board_position] = \
						create_transceiver_from_hostname(ip, discover = False)
	
	
	def _get_transceiver(self, board):
		"""
		Get the transceiver connected to the BMP of the requested board. If no
		transceiver exists (i.e. the IP is not known), returns None
		"""
		cabinet, rack, slot = board
		return self.transceivers.get( (cabinet,rack,slot)
		                            , self.transceivers.get((cabinet,rack), None)
		                            )
	
	
	def _write_register(self, board, direction, reg_addr, value):
		"""
		Write a register in the specified link endpoint.
		"""
		try:
			fpga_id, reg_addr_prefix = WiringProbe.BOARD_FPGAS[direction]
			addr = (reg_addr<<2) | reg_addr_prefix
			
			self._get_transceiver(board).write_neighbour_memory( 0 # X not relevant
			                                                   , 0 # Y not relevant
			                                                   , board[2]
			                                                   , fpga_id
			                                                   , addr
			                                                   , value
			                                                   )
		except Exception:
			print board
			raise
	
	
	def _read_register(self, board, direction, reg_addr):
		"""
		Read a register in the specified link endpoint.
		"""
		fpga_id, reg_addr_prefix = WiringProbe.BOARD_FPGAS[direction]
		addr = (reg_addr<<2) | reg_addr_prefix
		
		value = list(self._get_transceiver(board).read_neighbour_memory( 0
		                                                               , 0
		                                                               , board[2]
		                                                               , fpga_id
		                                                               , addr
		                                                               , 4
		                                                               ))[0]
		# Conversion to bytes is required on older versions of Python's struct
		# module which don't accept bytearrays.
		value = struct.unpack("<L", bytes(value))[0]
		return value
	
	def close(self):
		"""
		Close all open connections.
		"""
		for transceiver in self.transceivers.values():
			transceiver.close()
		self.transceivers = {}
	
	
	def _assign_link_ids(self):
		"""
		Assign a unique ID to each HSS endpoint.
		"""
		# Links are allocated sequential IDs and so values left by previous runs of
		# the tool could be the same or similar. To make this less likely, a fixed
		# random mask is XOR'd into every ID.
		mask = random.getrandbits(WiringProbe.NUM_ID_BITS)
		
		link_index = 0
		for c in range(self.cabinet_system.num_cabinets):
			for r in range(self.cabinet_system.cabinet.num_racks):
				for s in range(self.cabinet_system.cabinet.rack.num_slots):
					for d in [EAST, NORTH_EAST, NORTH, WEST, SOUTH_WEST, SOUTH]:
						id = link_index ^ mask
						self.id_to_link[id] = ((c,r,s),d)
						self.link_to_id[((c,r,s),d)] = id
						
						link_index += 1
	
	
	def _write_link_ids(self):
		"""
		Write the unique IDs into each link in the system.
		"""
		for id, (board,direction) in self.id_to_link.items():
			fpga_num, reg_addr_prefix = WiringProbe.BOARD_FPGAS[direction]
			self._write_register(board, direction, WiringProbe.IDSO_REG, id)
	
	
	def get_link_target(self, board, direction):
		"""
		Test a link leaving the board (cabinet,rack,slot) leaving the link going in
		the specified direction.
		
		Returns (board, direction) of the socket on the remote
		board. Returns None if the read fails or the remote ID is not recognised.
		"""
		id = self._read_register(board, direction, WiringProbe.IDSI_REG)
		return self.id_to_link.get(id, None)
	
	
	def discover_wires(self):
		"""
		Returns a list [(src, dst), ...] where src and dst are tuples (cabinet, rack,
		slot, direction) specifying which links were found to be working (in both
		directions). Directions NORTH, EAST and SOUTH_WEST are always "sources" and
		SOUTH, WEST, and NORTH_EAST are always "destinations", where possible.
		"""
		
		from_wires = set([])
		to_wires   = set([])
		
		for c in range(self.cabinet_system.num_cabinets):
			for r in range(self.cabinet_system.cabinet.num_racks):
				for s in range(self.cabinet_system.cabinet.rack.num_slots):
					for d in [EAST, NORTH_EAST, NORTH, WEST, SOUTH_WEST, SOUTH]:
						from_board, from_direction = (c,r,s), d
						target = self.get_link_target(from_board, from_direction)
						if target is None:
							# Not connected...
							continue
						to_board, to_direction = target
						
						# Flip the from/to so that the from is going from NORTH, EAST,
						# SOUTH_WEST (if neither end of the wire is from these then things are
						# very weird (connectors are electrically polarised so this isn't
						# possible) so just put up with the wrong order here).
						wires = from_wires
						if from_direction in [SOUTH, WEST, NORTH_EAST]:
							to_board,     from_board     = from_board,     to_board
							to_direction, from_direction = from_direction, to_direction
							wires = to_wires
						
						wires.add(( ( from_board[0]
						            , from_board[1]
						            , from_board[2]
						            , from_direction
						            )
						          , ( to_board[0]
						            , to_board[1]
						            , to_board[2]
						            , to_direction
						            )
						         ))
		
		# Return only those wires which were discovered travelling in both
		# directions
		return list(from_wires & to_wires)


def wiring_diff(a, b):
	"""
	Determine differences between two wire listings a, and b which are lists
	[(src, dst), ...] where src and dst are tuples ((cabinet, rack, slot), socket).
	
	Returns two lists as a tuple (remove, add) with the same format as the input
	where the remove list gives wires which were present in a but not in b and the
	add list gives wires present in b but not a.
	"""
	
	a = set(a)
	b = set(b)
	
	return (list(a - b), list(b - a))


def generate_correction_plan( remove, add
                            , cabinet_system
                            , available_wires
                            , minimum_arc_height
                            ):
	"""
	Takes a pair of lists lists [(src,dst),...] where src and dst are
	(cabinet,rack,slot,direction) tuples, the lists decribing wires to be removed
	and added respectively.
	
	Returns a single, list [(src,dst,len),...] where lengths may be None to
	indicate a removed wire.
	"""
	correction_plan = []
	
	# Remove all wrong wires first
	for src, dst in remove:
		correction_plan.append((src,dst,None))
	
	# Add new wires ordered fairly arbitrarily
	for src, dst in sorted(add, key = (lambda (src,dst): src)):
		# Get wire length
		src_position = cabinet_system.get_position(src[:3], src[3])
		dst_position = cabinet_system.get_position(dst[:3], dst[3])
		distance = (src_position - dst_position).magnitude()
		wire_length, arc_height = physical_wire_length( distance
		                                              , available_wires
		                                              , minimum_arc_height
		                                              )
		correction_plan.append((
			src,
			dst,
			wire_length
		))
	
	return correction_plan


if __name__=="__main__":
	import sys
	
	from wiring_plan_generator import generate_wiring_plan, flatten_wiring_plan
	from model_builder import build_model
	from param_parser import parse_params, parse_bmp_ips
	
	################################################################################
	# Parse command-line arguments
	################################################################################
	
	import argparse
	
	parser = argparse.ArgumentParser(description = "discover and list wiring errors")
	
	parser.add_argument( "param_files", type=str, nargs="+"
	                   , help="parameter files describing machine parameters"
	                   )
	
	parser.add_argument( "-b", "--bmp-ips", type=str, nargs="?"
	                   , help="Config file defining BMP IP addresses"
	                   )
	
	args = parser.parse_args()
	
	################################################################################
	# Load Parameters
	################################################################################
	params = parse_params(["machine_params/universal.param"] + args.param_files)
	
	title                          = params["title"]
	
	diagram_scaling                = params["diagram_scaling"]
	cabinet_diagram_scaling_factor = params["cabinet_diagram_scaling_factor"]
	show_wiring_metrics            = params["show_wiring_metrics"]
	show_topology_metrics          = params["show_topology_metrics"]
	show_development               = params["show_development"]
	show_board_position_list       = params["show_board_position_list"]
	show_wiring_instructions       = params["show_wiring_instructions"]
	wire_length_histogram_bins     = params["wire_length_histogram_bins"]
	
	slot_width                     = params["slot_width"]
	slot_height                    = params["slot_height"]
	slot_depth                     = params["slot_depth"]
	
	rack_width                     = params["rack_width"]
	rack_height                    = params["rack_height"]
	rack_depth                     = params["rack_depth"]
	
	cabinet_width                  = params["cabinet_width"]
	cabinet_height                 = params["cabinet_height"]
	cabinet_depth                  = params["cabinet_depth"]
	
	wire_positions                 = params["wire_positions"]
	socket_names                   = params["socket_names"]
	
	slot_spacing                   = params["slot_spacing"]
	slot_offset                    = params["slot_offset"]
	num_slots_per_rack             = params["num_slots_per_rack"]
	rack_spacing                   = params["rack_spacing"]
	rack_offset                    = params["rack_offset"]
	
	num_racks_per_cabinet          = params["num_racks_per_cabinet"]
	cabinet_spacing                = params["cabinet_spacing"]
	num_cabinets                   = params["num_cabinets"]
	
	width                          = params["width"]
	height                         = params["height"]
	num_folds_x                    = params["num_folds_x"]
	num_folds_y                    = params["num_folds_y"]
	compress_rows                  = params["compress_rows"]
	
	minimum_arc_height             = params["minimum_arc_height"]
	available_wires                = params["available_wires"]
	
	
	################################################################################
	# Generate models
	################################################################################
	
	# Fold the system
	( torus
	, cart_torus
	, rect_torus
	, comp_torus
	, fold_spaced_torus
	, folded_cabinet_spaced_torus
	, cabinet_torus
	, phys_torus
	, cabinet_system
	) = build_model( slot_width,    slot_height,    slot_depth
	               , rack_width,    rack_height,    rack_depth
	               , cabinet_width, cabinet_height, cabinet_depth
	               , wire_positions
	               , slot_spacing, slot_offset, num_slots_per_rack
	               , rack_spacing, rack_offset, num_racks_per_cabinet
	               , cabinet_spacing, num_cabinets
	               , width, height
	               , num_folds_x, num_folds_y
	               , compress_rows
	               )
	
	# Plan the wiring
	( wires_between_slots
	, wires_between_racks
	, wires_between_cabinets
	) = generate_wiring_plan( cabinet_torus
	                        , phys_torus
	                        , wire_positions
	                        , available_wires
	                        , minimum_arc_height
	                        )
	
	# Flatten the instructions
	wires_ = flatten_wiring_plan( wires_between_slots
	                            , wires_between_racks
	                            , wires_between_cabinets
	                            , wire_positions
	                            )
	
	# Assemble a list of wires in terms of slot positions (rather than Board
	# objects) and without wire lengths.
	b2p = dict(cabinet_torus)
	plan_wires = []
	for (src_board, src_direction), (dst_board, dst_direction), wire_length in wires_:
		src = tuple(list(b2p[src_board]) + [src_direction])
		dst = tuple(list(b2p[dst_board]) + [dst_direction])
		plan_wires.append((src, dst))
	
	################################################################################
	# Probe the existing system
	################################################################################
	
	p = WiringProbe(cabinet_system, parse_bmp_ips([args.bmp_ips]))
	actual_wires = p.discover_wires()
	p.close()
	
	remove, add = wiring_diff(actual_wires, plan_wires)
	correction_plan = generate_correction_plan( remove, add
                                            , cabinet_system
                                            , available_wires
                                            , minimum_arc_height
                                            )
	
	
	################################################################################
	# Guide user through corrections
	################################################################################
	
	if not correction_plan:
		print("All %d expected wires present and operational."%(len(plan_wires)))
	else:
		if remove:
			print("Unexpected wires to remove: %4d"%(len(remove)))
			print("================================")
			print("")
			print("   C  R  S  Socket      <->  C  R  S  Socket    ")
			print("  -- -- --  ----------      -- -- --  ----------")
			for src, dst in ((s,d) for (s,d,l) in correction_plan if l is None):
				print("  %2d %2d %2d  %-10s      %2d %2d %2d  %-10s"%(
					src[0],
					src[1],
					src[2],
					socket_names[src[3]],
					dst[0],
					dst[1],
					dst[2],
					socket_names[dst[3]],
				))
		
		if remove and add:
			print("")
		
		if add:
			print("Missing wires to add: %4d"%(len(add)))
			print("==========================")
			print("")
			print("   C  R  S  Socket      <->  C  R  S  Socket       Length")
			print("  -- -- --  ----------      -- -- --  ----------   ------")
			for src, dst, length in ((s,d,l) for (s,d,l) in correction_plan if l is not None):
				print("  %2d %2d %2d  %-10s      %2d %2d %2d  %-10s   %0.2fm (%s)"%(
					src[0],
					src[1],
					src[2],
					socket_names[src[3]],
					dst[0],
					dst[1],
					dst[2],
					socket_names[dst[3]],
					length,
					available_wires[length],
				))
			
			# Exit with an error code
			sys.exit(1)
