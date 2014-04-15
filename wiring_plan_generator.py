#!/usr/bin/env python

"""
Utility functions for producing practical wiring plans.

If executed as a script, currently reports what wire lengths are used for what
connections.
"""

import sys

from collections import defaultdict

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

from model import topology
from model import board
from model import metrics


def enumerate_wires(boards):
	"""
	Takes a set of boards and enumerates the wires in the network. Returns a
	list [((src_board, src_direction), (dst_board, dst_direction)),...] in no
	particular order.
	"""
	
	wires = []
	for src_board, src_pos in boards:
		for src_direction in [NORTH, EAST, SOUTH_WEST]:
			dst_board = src_board.follow_wire(src_direction)
			dst_direction = topology.opposite(src_direction)
			
			wires.append(((src_board, src_direction), (dst_board, dst_direction)))
	
	return wires


def partition_wires(wires, cabinet_torus):
	"""
	Partition a list of wires up by whether they stay in the same rack, cabinet or
	not. Returns a tuple of two dictionaries and a list::
		
		( {(cabinet,rack): wires_between_slots,...}
		, {(cabinet): wires_between_racks,...}
		, wires_between_cabinets
		)
	"""
	# Get the mapping from boards to their cabinet positions
	b2c = dict(cabinet_torus)
	
	# {(cabinet,rack): [wire,...]}
	wires_between_slots = defaultdict(list)
	# {(cabinet): [wire,...]}
	wires_between_racks = defaultdict(list)
	# [wire,...]
	wires_between_cabinets = []
	
	for wire in wires:
		src_pos = b2c[wire[0][0]]
		dst_pos = b2c[wire[1][0]]
		
		if src_pos[0:2] == dst_pos[0:2]:
			# Same cabinet and rack
			wires_between_slots[(src_pos[0:2])].append(wire)
		elif src_pos[0] == dst_pos[0]:
			# Same cabinet
			wires_between_racks[src_pos[0]].append(wire)
		else:
			# Different cabinet
			wires_between_cabinets.append(wire)
	
	return (wires_between_slots, wires_between_racks, wires_between_cabinets)


def assign_wires(wires, phys_torus, wire_positions, available_wire_lengths, minimum_arc_height):
	"""
	Given a list `[((src_board,src_direction),(dst_board,dst_direction)),...]`,
	sort into an order where the tightest wires are connected first. Returns::
		
		[((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
	
	Where wire_length is the length of the wire assigned to that connection.
	"""
	b2p = dict(phys_torus)
	
	# Augment each wire with the length and arc
	wires = [ (wire[0], wire[1], metrics.physical_wire_length(
	              phys_torus, wire[0][0], wire[0][1],
	              wire_positions, available_wire_lengths, minimum_arc_height
	            )
	          )
	          for wire in wires
	        ]
	
	# Sort the wires such that the shortest, furthest-stretched wires are
	# connected first but beyond that we move left-to-right.
	def sort_wires(w1, w2):
		if   w1[2][1] < w2[2][1]: return -1 # Tightly stretched wires go first...
		elif w1[2][1] > w2[2][1]: return +1
		elif b2p[w1[0][0]].x < b2p[w2[0][0]].x: return -1 # Left-to-right
		elif b2p[w1[0][0]].x > b2p[w2[0][0]].x: return +1
		elif b2p[w1[0][0]].y < b2p[w2[0][0]].y: return -1 # Left-to-right
		elif b2p[w1[0][0]].y > b2p[w2[0][0]].y: return +1
	wires.sort(cmp = sort_wires)
	
	# Strip out the arc height and return
	return [ (wire[0],wire[1],wire[2][0]) for wire in wires ]


def generate_wiring_plan(cabinet_torus, phys_torus, wire_positions, available_wire_lengths, minimum_arc_height):
	"""
	Get a wiring plan broken down into various stages.
	
	Takes a cabinetised torus (cabinet_torus), the physical positions of the
	boards in space (phys_torus) and a list of available wire lengths
	(available_wire_lengths).
	
	Produces a tuple of three dictionaries::
		
		# Connections between slots
		{ (cabinet, rack, direction)
		  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
	  }
		
		# Connections between racks
		{ (cabinet, direction)
		  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
	  }
		
		# Connections between cabinets
		{ direction
		  : [((src_board,src_direction),(dst_board,dst_direction), wire_length),...]
	  }
	
	Which gives an ordered list of wiring connections to make for each cabinet,
	rack and axis of the system.
	"""
	b2c = dict(cabinet_torus)
	b2p = dict(phys_torus)
	
	plan_between_slots    = {}
	plan_between_racks    = {}
	plan_between_cabinets = {}
	
	# List all the wires which exist
	wires = enumerate_wires(cabinet_torus)
	
	# Split up wires by directon
	for direction in [NORTH, EAST, SOUTH_WEST]:
		direction_wires = [ wire for wire in wires if wire[0][1] == direction or wire[1][1] == direction ]
		
		# Split wires up depending on whether they're within a single rack/cabinet
		# or not.
		wires_between_slots, wires_between_racks, wires_between_cabinets = \
			partition_wires(direction_wires, cabinet_torus)
		
		for (cabinet, rack), w in wires_between_slots.iteritems():
			plan_between_slots[(cabinet, rack, direction)] = \
				assign_wires( w
				            , phys_torus
				            , wire_positions
				            , available_wire_lengths
				            , minimum_arc_height
				            )
		
		for cabinet, w in wires_between_racks.iteritems():
			plan_between_racks[(cabinet, direction)] = \
				assign_wires( w
				            , phys_torus
				            , wire_positions
				            , available_wire_lengths
				            , minimum_arc_height
				            )
		
		plan_between_cabinets[direction] = \
			assign_wires( wires_between_cabinets
			            , phys_torus
			            , wire_positions
			            , available_wire_lengths
			            , minimum_arc_height
			            )
	
	return (plan_between_slots, plan_between_racks, plan_between_cabinets)


if __name__=="__main__":
	import sys
	
	from model_builder import build_model
	from param_parser import parse_params
	
	################################################################################
	# Load Parameters
	################################################################################
	
	params = parse_params(["machine_params/universal.param", sys.argv[1]])
	
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
	
	
	################################################################################
	# List wires
	################################################################################
	
	b2p = dict(cabinet_torus)
	
	# Work out what wires should be used
	wires = enumerate_wires(phys_torus)
	wires_with_lenghts = assign_wires( wires
	                                 , phys_torus
	                                 , wire_positions
	                                 , available_wires.keys()
	                                 , minimum_arc_height
	                                 )
	
	# Mapping from wire-length to a list of ((src_board, src_direction),
	# (dst_board, dst_direction), absolute_distance) tuples.
	wire_used_for = defaultdict(list)
	for ((src_board, src_direction), (dst_board, dst_direction), wire_length) in wires_with_lenghts:
		wire_used_for[wire_length].append( ( (src_board, src_direction)
		                                   , (dst_board, dst_direction)
		                                   , metrics.wire_length( phys_torus
		                                                        , src_board
		                                                        , src_direction
		                                                        , wire_positions
		                                                        )
		                                   )
		                                 )
	
	# For each wire-length, report the connections made with such a wire (and
	# their length) in ascending order of length.
	for wire_length in sorted(available_wires.keys()):
		connections = sorted(wire_used_for[wire_length], key=(lambda (_1, _2, l): l), reverse=True)
		
		print "="*80
		print "Connections Using '%s' (%f unit) Wires (%d Wires)"%( available_wires[wire_length]
		                                                        , wire_length
		                                                        , len(connections)
		                                                        )
		print "="*80
		
		def print_connection(connection):
			((src_board, src_direction), (dst_board, dst_direction), absolute_distance) = connection
			print "Distance = %f units: %s (%s) --> %s (%s)"%( absolute_distance
			                                                 , b2p[src_board], socket_names[src_direction]
			                                                 , b2p[dst_board], socket_names[dst_direction]
			                                                 )
		
		for connection in connections[:10]:
			print_connection(connection)
		print "..."
		for connection in connections[-10:]:
			print_connection(connection)
		
		print

