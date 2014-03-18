#!/usr/bin/env python

"""
Utility functions for producing practical wiring plans.
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
