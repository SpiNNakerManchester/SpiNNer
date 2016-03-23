"""Utilities for probing the wiring in a SpiNNaker machine."""

from six import iteritems

import random

from spinner.topology import Direction


class WiringProbeError(Exception):
	"""An error occurred when trying to probe the machine!"""
	pass


class WiringProbe(object):
	"""
	An object which probes a set of SpiNNaker boards to discover the connectivity
	between them. This tool uses the debugging facility of the board-to-board
	links to transmit/receive small values in their idle packets. As a result, the
	system should not be booted while performing link probing to ensure the links
	remain idle.
	"""
	
	# Number of bits in an ID which can be applied to a board
	NUM_ID_BITS = 16
	
	
	# A dictionary {direction: (fpga_num, reg_base_addr), ...} which gives for
	# each link direction the index of the responsible FPGA and the prefix for
	# register bank addresses for the particular link hardware within that FPGA.
	BOARD_FPGAS = {
		Direction.south:      (0, 0x00010000),
		Direction.east:       (0, 0x00000000),
		Direction.west:       (1, 0x00010000),
		Direction.south_west: (1, 0x00000000),
		Direction.north_east: (2, 0x00010000),
		Direction.north:      (2, 0x00000000),
	}
	
	# Register bank addresses for the "IDle Sentinel Input/Output" registers. The
	# IDSO register specifies a value to be transmitted as part of link idle
	# packets. IDSI indicates the value transmitted in the most recently received
	# idle packet.
	IDSO_REG = 19
	IDSI_REG = 20
	
	# Register address of the idle packet scrambling enable register
	SCRM_REG = 0x00040010
	
	# Register bank address of the handshake status bits. If bit 0 is set, the
	# link is alive, if 0, the link is dead.
	HAND_REG = 21
	
	def __init__(self, bmp_controller,
	             num_cabinets, frames_per_cabinet, boards_per_frame):
		"""Takes a connection to the system's BMPs along with the dimensions of the
		system."""
		self.bmp_controller = bmp_controller
		
		self.num_cabinets = num_cabinets
		self.frames_per_cabinet = frames_per_cabinet
		self.boards_per_frame = boards_per_frame
		
		# A dictionary {link_id: ((c,f,b),d), ...} and visa versa.
		self.id_to_link = {}
		self.link_to_id = {}
		
		# Assign every link an ID (also serves to check all FPGAs are powered on)
		self._assign_link_ids()
	
	def _assign_link_ids(self):
		"""Assign a unique ID to each HSS endpoint.
		
		Assigns IDs and loads them onto the machine. Raises a WiringProbeError if
		any FPGA is powered down.
		"""
		# Links are allocated sequential IDs and so values left by previous runs of
		# the tool could be the same or similar. To make this less likely, a fixed
		# random mask is XOR'd into every ID.
		mask = random.getrandbits(WiringProbe.NUM_ID_BITS)
		
		link_index = 0
		for c in range(self.num_cabinets):
			for f in range(self.frames_per_cabinet):
				for b in range(self.boards_per_frame):
					for d in Direction:
						# Generate the ID
						id = link_index ^ mask
						link_index += 1
						
						# Record it
						self.id_to_link[id] = (c,f,b,d)
						self.link_to_id[(c,f,b,d)] = id
						
						# Write it to the hardware
						self._write_register(c, f, b, d, WiringProbe.IDSO_REG, id)
						
						# Check the FPGA is powered on by reading back the register and
						# comparing it
						if self._read_register(c, f, b, d, WiringProbe.IDSO_REG) != id:
							raise WiringProbeError("FPGA not powered on "
							                       "(cabinet:{} frame:{} "
							                       "board:{} link:{})".format(c,f,b,d.name))
					
					# Also turn off scrabmling so this ID is actually sent out with idle
					# packets
					for fpga_num in range(3):
						self.bmp_controller.write_fpga_reg(fpga_num, WiringProbe.SCRM_REG, 0,
						                                   c, f, b)
	
	def _write_register(self, cabinet, frame, board, direction,
	                    reg_num, value):
		"""Write to a register in the specified link endpoint."""
		fpga_num, reg_base_addr = WiringProbe.BOARD_FPGAS[direction]
		addr = (reg_num<<2) | reg_base_addr
		
		self.bmp_controller.write_fpga_reg(fpga_num, addr, value,
		                                   cabinet, frame, board)
	
	
	def _read_register(self, cabinet, frame, board, direction, reg_num):
		"""Read a register in the specified link endpoint."""
		fpga_num, reg_base_addr = WiringProbe.BOARD_FPGAS[direction]
		addr = (reg_num<<2) | reg_base_addr
		
		return self.bmp_controller.read_fpga_reg(fpga_num, addr,
		                                         cabinet, frame, board)
	
	
	def get_link_target(self, cabinet, frame, board, direction):
		"""Determine which link is at the other end of the supplied link.
		
		Returns (cabinet, frame, board, direction) of the socket on the remote
		board. Returns None if the link is not connected to any known endpoint.
		"""
		# If the link is down, the link is definately not connected
		handshake = self._read_register(cabinet, frame, board, direction,
		                                WiringProbe.HAND_REG)
		if handshake & 1 == 0:
			return None
		else:
			id = self._read_register(cabinet, frame, board, direction,
			                         WiringProbe.IDSI_REG)
			return self.id_to_link.get(id, None)
	
	
	def discover_wires(self):
		"""
		Returns a list [(src, dst), ...] where src and dst are tuples (cabinet,
		frame, board, direction) specifying which links were found to be working (in both
		directions). Directions north, east and south_west are always "sources" and
		south, west, and north_east are always "destinations" except when an invalid
		connection (e.g. east to north) is made in which case the order is not
		defined.
		"""
		
		from_wires = set([])
		to_wires   = set([])
		
		for fc in range(self.num_cabinets):
			for ff in range(self.frames_per_cabinet):
				for fb in range(self.boards_per_frame):
					for fd in Direction:
						source = (fc, ff, fb, fd)
						target = self.get_link_target(fc, ff, fb, fd)
						if target is None:
							# Not connected...
							continue
						
						# Flip the from/to so that the from is going from north, east,
						# south_west (if neither end of the wire is from these then things are
						# very weird (connectors are electrically polarised so this isn't
						# possible) so just put up with the wrong order here).
						if fd in [Direction.south, Direction.west, Direction.north_east]:
							target, source = source, target
							wires = to_wires
						else:
							wires = from_wires
						
						wires.add((source, target))
		
		# Return only those wires which were discovered travelling in both
		# directions
		return list(from_wires & to_wires)
