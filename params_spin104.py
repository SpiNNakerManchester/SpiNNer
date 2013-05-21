#!/usr/bin/env python

"""
Parameter file for wiring_guide.py

A single threeboard.
"""


from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

################################################################################
# Basic Parameters
################################################################################

# The number of boards in the system (in threeboards)
width  = 2
height = 2

# The number of folds (actually the number of faces of a folded sheet)
num_folds_x = 2
num_folds_y = 1

# How is the machine split up into physical units
num_cabinets          = 1
num_racks_per_cabinet = 1
num_slots_per_rack    = 12


################################################################################
# Report Parameters
################################################################################

title = "SpiNNaker Three-Board Machine Wiring"

# Scale all diagrams by this factor
diagram_scaling = 1.0

# Include the development section in the report
show_development = True

# Show metrics relating to the 
show_wiring_metrics = True

# Show information relating to the topology
show_topology_metrics = True

# Show metrics relating to the 
show_board_position_list = True

# Show instructions for wiring the machine
show_wiring_instructions = True

# Number of bins on wire-length histograms
wire_length_histogram_bins = 5

################################################################################
# Cabinet/Rack/Slot Dimensions
################################################################################

# The unit in which cabinet measurements are given
cabinet_unit = "cm"

# The scaling factor applied to drawing of the racks/cabinets
cabinet_diagram_scaling_factor = 0.5

# How big is each slot in a rack (not including spacing between slots) cm
slot_width  = 1.0
slot_height = 10.0
slot_depth  = 10.0

# Horizontal space between slots. cm
slot_spacing = 0.1

# Human-readable names the sockets on a spinnaker board
socket_names = {
	NORTH      : "North",
	NORTH_EAST : "North East",
	EAST       : "East",
	SOUTH      : "South",
	SOUTH_WEST : "South West",
	WEST       : "West",
}

# The position of the sockets on the spinnaker boards relative to the
# bottom-left corner of a slot or None to spread evenly over the slot. cm
wire_positions = None
#wire_positions = {
#	NORTH      : (0.0, 0.0, 0.0),
#	NORTH_EAST : (0.0, 1.0, 0.0),
#	EAST       : (0.0, 2.0, 0.0),
#	SOUTH      : (0.0, 3.0, 0.0),
#	SOUTH_WEST : (0.0, 4.0, 0.0),
#	WEST       : (0.0, 5.0, 0.0),
#}

# Size of a rack. cm
rack_width  =  15.0
rack_height = 15.0
rack_depth  = 20.0

# Space between each rack. cm
rack_spacing = 2.0

# Position of bottom-left corner of the first slot in the rack relative to the
# bottom-left corner of the rack or None to center all the slots in the rack. cm
slot_offset = None
#slot_offset = (1.0, 1.0, 0.0)

# Size of a cabinet. cm
cabinet_width  = 20
cabinet_height = 20.0
cabinet_depth  = 25.0

# Space in-between cabinets. cm
cabinet_spacing = 3.0

# Position of bottom-left corner of the first rack in the cabinet relative to
# the bottom-left corner of the cabinet or None to center all the racks in the
# cabinet. cm
rack_offset = None
#rack_offset = (1.0, 1.0, 0.0)

