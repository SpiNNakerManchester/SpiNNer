"""Functions for producing practical wiring plans."""

from six import iteritems

from collections import defaultdict

from spinner.topology import Direction

from spinner import topology
from spinner import board
from spinner import metrics


def enumerate_wires(boards):
	"""
	Takes a set of boards and enumerates the wires in the network. Returns a
	list [((src_board, src_direction), (dst_board, dst_direction)),...] in no
	particular order. Directions north, east and south_west are always "sources"
	and south, west, and north_east are always "destinations".
	"""
	
	wires = []
	for src_board, src_pos in boards:
		for src_direction in [Direction.north, Direction.east, Direction.south_west]:
			dst_board = src_board.follow_wire(src_direction)
			dst_direction = src_direction.opposite
			
			wires.append(((src_board, src_direction), (dst_board, dst_direction)))
	
	return wires


def partition_wires(wires, cabinetised_boards):
	"""
	Partition a list of wires up by whether they stay in the same frame, cabinet or
	not. Returns a tuple of two dictionaries and a list::
		
		( {(cabinet,frame): wires_between_boards,...}
		, {cabinet: wires_between_frames,...}
		, wires_between_cabinets
		)
	"""
	# Get the mapping from boards to their cabinet positions
	b2c = dict(cabinetised_boards)
	
	# {(cabinet,frame): [wire,...]}
	wires_between_boards = defaultdict(list)
	# {(cabinet): [wire,...]}
	wires_between_frames = defaultdict(list)
	# [wire,...]
	wires_between_cabinets = []
	
	for wire in wires:
		src_pos = b2c[wire[0][0]]
		dst_pos = b2c[wire[1][0]]
		
		if src_pos[0:2] == dst_pos[0:2]:
			# Same cabinet and frame
			wires_between_boards[(src_pos[0:2])].append(wire)
		elif src_pos[0] == dst_pos[0]:
			# Same cabinet
			wires_between_frames[src_pos[0]].append(wire)
		else:
			# Different cabinet
			wires_between_cabinets.append(wire)
	
	return (wires_between_boards, wires_between_frames, wires_between_cabinets)


def assign_wires(wires, physical_boards, board_wire_offset, available_wire_lengths):
	"""
	Given a list `[((src_board,src_direction),(dst_board,dst_direction)),...]`,
	sort into an order where the tightest wires are connected first. Returns::
		
		[((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
	
	Where wire_length is the length of the wire assigned to that connection taken
	from the list available_wire_lengths.
	"""
	b2p = dict(physical_boards)
	d2o = board_wire_offset
	
	available_wire_lengths = sorted(available_wire_lengths)
	
	def assign_wire(distance):
		"""Return a tuple (wire_length, slack) shortest possible wire which coveres
		the distance and the amount of slack."""
		for length in available_wire_lengths:  # pragma: no branch
			if distance <= length:
				return (length, length - distance)
		assert False  # pragma: no cover
	
	# Augment each wire with a wire length and amount of slack
	wires = [(src, dst, assign_wire(((b2p[src[0]] + d2o[src[1]]) -
	                                 (b2p[dst[0]] + d2o[dst[1]])).magnitude()))
	          for (src, dst) in wires]
	
	# Sort the wires such that the shortest, furthest-stretched wires are
	# connected first but beyond that we move left-to-right.
	wires.sort(key=(lambda wire: (wire[2][1],  # Least-slack first first
	                              b2p[wire[0][0]].x,  # Left-most next
	                              b2p[wire[0][0]].y)))  # Top-most next
	
	# Strip out the slack and return
	return [(src, dst, length) for src, dst, (length, slack) in wires]


def generate_wiring_plan(cabinetised_boards, physical_boards,
                         board_wire_offset, available_wire_lengths):
	"""
	Get a wiring plan broken down into various stages.
	
	Takes a cabinetised torus (cabinetised_boards), the physical positions of the
	boards in space (physical_boards) and a list of available wire lengths
	(available_wire_lengths).
	
	Produces a tuple of three dictionaries::
		
		(
			# Connections between boards
			{ (cabinet, frame, direction)
			  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
			},
			
			# Connections between frames
			{ (cabinet, direction)
			  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
			},
			
			# Connections between cabinets
			{ direction
			  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
			}
		)
	
	Which gives an ordered list of wiring connections to make for each cabinet,
	frame and axis of the system.
	"""
	b2c = dict(cabinetised_boards)
	b2p = dict(physical_boards)
	
	plan_between_boards   = {}
	plan_between_frames   = {}
	plan_between_cabinets = {}
	
	# List all the wires which exist
	wires = enumerate_wires(cabinetised_boards)
	
	# Split up wires by directon
	for direction in [Direction.north, Direction.east, Direction.south_west]:
		direction_wires = [ wire for wire in wires if wire[0][1] == direction or wire[1][1] == direction ]
		
		# Split wires up depending on whether they're within a single frame/cabinet
		# or not.
		wires_between_boards, wires_between_frames, wires_between_cabinets = \
			partition_wires(direction_wires, cabinetised_boards)
		
		for (cabinet, frame), w in iteritems(wires_between_boards):
			plan_between_boards[(cabinet, frame, direction)] = \
				assign_wires( w
				            , physical_boards
				            , board_wire_offset
				            , available_wire_lengths
				            )
		
		for cabinet, w in iteritems(wires_between_frames):
			plan_between_frames[(cabinet, direction)] = \
				assign_wires( w
				            , physical_boards
				            , board_wire_offset
				            , available_wire_lengths
				            )
		
		plan_between_cabinets[direction] = \
			assign_wires( wires_between_cabinets
			            , physical_boards
			            , board_wire_offset
			            , available_wire_lengths
			            )
	
	return (plan_between_boards, plan_between_frames, plan_between_cabinets)


def flatten_wiring_plan( wires_between_boards
                       , wires_between_frames
                       , wires_between_cabinets
                       , board_wire_offset
                       ):
	"""
	Takes the output of generate_wiring_plan and produces a flat list
	[((src_board, src_direction), (dst_board, dst_direction), wire_length), ...]
	in a sensible order.
	"""
	out = []
	
	# Wires between boards in the same frame
	cabinets = set(c for (c,f,d) in wires_between_boards)
	for cabinet in sorted(cabinets):
		frames = set(f for (c,f,d) in wires_between_boards
		               if c == cabinet
		            )
		for frame in sorted(frames):
			directions = set(d for (c,f,d) in wires_between_boards
			                   if c == cabinet and f == frame
			                )
			for direction in sorted(directions, key=(lambda d: board_wire_offset[d].y)):
				out += wires_between_boards[(cabinet,frame,direction)]
	
	# Wires between frames in the same cabinet
	cabinets = set(c for (c,d) in wires_between_frames)
	for cabinet in sorted(cabinets):
		directions = set(d for (c,d) in wires_between_frames
		                   if c == cabinet
		                )
		for direction in sorted(directions, key=(lambda d: board_wire_offset[d].y)):
			out += wires_between_frames[(cabinet,direction)]
	
	# Wires between cabinets
	directions = set(wires_between_cabinets)
	for direction in sorted(directions, key=(lambda d: board_wire_offset[d].y)):
		out += wires_between_cabinets[direction]
	
	return out
