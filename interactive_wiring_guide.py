#!/usr/bin/env python

"""
A tool which interactively guides a user through the steps involved in wiring up
a SpiNNaker machine using the LEDs on the boards and the spinn_blink library.
"""

import sys

from collections import defaultdict

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

from model import topology
from model import board
from model import metrics

from param_parser          import parse_params
from model_builder         import build_model
from wiring_plan_generator import generate_wiring_plan

import diagram


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

minimum_arc_height             = params["minimum_arc_height"]
available_wires                = params["available_wires"]

num_racks_per_cabinet          = params["num_racks_per_cabinet"]
cabinet_spacing                = params["cabinet_spacing"]
num_cabinets                   = params["num_cabinets"]

width                          = params["width"]
height                         = params["height"]
num_folds_x                    = params["num_folds_x"]
num_folds_y                    = params["num_folds_y"]
compress_rows                  = params["compress_rows"]



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
# Print out wiring instructions
################################################################################

if __name__=="__main__":
	DIRECTION_NAMES = {
		NORTH      : "North",
		NORTH_EAST : "North East",
		EAST       : "East",
		SOUTH      : "South",
		SOUTH_WEST : "South West",
		WEST       : "West",
	}
	
	plan_between_slots, plan_between_racks, plan_between_cabinets = \
		generate_wiring_plan( cabinet_torus
		                    , phys_torus
		                    , wire_positions
		                    , available_wires.keys()
		                    , minimum_arc_height
		                    )
	
	b2c = dict(cabinet_torus)
	
	# TODO: Currently a proof-of-concept, make interactive
	
	print "Wires between slots"
	for key, wires in plan_between_slots.iteritems():
		print "  Cabinet %d, Rack %d, %s"%(key[0], key[1], DIRECTION_NAMES[key[2]])
		for ((src_board,src_direction),(dst_board,dst_direction),wire_length) in wires:
			print "    Slot %2d, %-7s -> Slot %2d, %-7s (%.1fm wire)"%(
				b2c[src_board].slot, socket_names[src_direction],
				b2c[dst_board].slot, socket_names[dst_direction],
				wire_length
			)
	
	print
	print "Wires between racks"
	for key, wires in plan_between_racks.iteritems():
		print "  Cabinet %d, %s"%(key[0], DIRECTION_NAMES[key[1]])
		for ((src_board,src_direction),(dst_board,dst_direction),wire_length) in wires:
			print "    Rack %2d, Slot %2d, %-7s -> Rack %2d, Slot %2d, %-7s (%.1fm wire)"%(
				b2c[src_board].rack, b2c[src_board].slot, socket_names[src_direction],
				b2c[dst_board].rack, b2c[dst_board].slot, socket_names[dst_direction],
				wire_length
			)
	
	print
	print "Wires between cabinets"
	for key, wires in plan_between_cabinets.iteritems():
		print "  %s"%DIRECTION_NAMES[key]
		for ((src_board,src_direction),(dst_board,dst_direction),wire_length) in wires:
			print "    Cabinet %2d, Rack %2d, Slot %2d, %-7s -> Cabinet %2d, Rack %2d, Slot %2d, %-7s (%.1fm wire)"%(
				b2c[src_board].cabinet, b2c[src_board].rack, b2c[src_board].slot, socket_names[src_direction],
				b2c[dst_board].cabinet, b2c[dst_board].rack, b2c[dst_board].slot, socket_names[dst_direction],
				wire_length
			)
