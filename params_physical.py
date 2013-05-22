#!/usr/bin/env python

"""
Generic parameters describing physical dimensions of the cabinets/racks/boards.
"""

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST


# The unit in which cabinet measurements are given
cabinet_unit = "m"

# The scaling factor applied to drawing of the racks/cabinets
cabinet_diagram_scaling_factor = 7.0

# How big is each slot in a rack (not including spacing between slots) cm
slot_width  = 1.5/100.0
slot_height = 24.0/100.0
slot_depth = 24.0/100.0

# Horizontal space between slots. cm
slot_spacing = 0.1/100.0

# Human-readable names the sockets on a spinnaker board
socket_names = {
	SOUTH_WEST : "J1 (SW)",
	NORTH_EAST : "J2 (NE)",
	EAST       : "J3 (E)",
	WEST       : "J4 (W)",
	NORTH      : "J5 (N)",
	SOUTH      : "J6 (S)",
}

# The position of the sockets on the spinnaker boards relative to the
# bottom-left corner of a slot or None to spread evenly over the slot. cm
#wire_positions = None
wire_positions = {
	SOUTH_WEST : (slot_width/2, slot_height - (0.02 * 0.5), 0.0), # J1
	NORTH_EAST : (slot_width/2, slot_height - (0.02 * 1.5), 0.0), # J2
	EAST       : (slot_width/2, slot_height - (0.02 * 2.5), 0.0), # J3
	WEST       : (slot_width/2, slot_height - (0.02 * 3.5), 0.0), # J4
	NORTH      : (slot_width/2, slot_height - (0.02 * 4.5), 0.0), # J5
	SOUTH      : (slot_width/2, slot_height - (0.02 * 5.5), 0.0), # J6
}

# Size of a rack. cm
rack_width  = 48.0/100.0
rack_height = (4.445*6)/100.0 # 6u
rack_depth  = 25.0/100.0

# Space between each rack. cm
rack_spacing = (4.445*2)/100.0 # 2u

# Position of bottom-left corner of the first slot in the rack relative to the
# bottom-left corner of the rack or None to center all the slots in the rack. cm
slot_offset = None
#slot_offset = (1.0, 1.0, 0.0)

# Size of a cabinet. cm
cabinet_width  = (48 + 10)/100.0
cabinet_height = (4.445*42)/100.0 # 42u
cabinet_depth  = 25./100.0

# Space in-between cabinets. cm
cabinet_spacing = 10.0/100.0

# Position of bottom-left corner of the first rack in the cabinet relative to
# the bottom-left corner of the cabinet or None to center all the racks in the
# cabinet. cm
rack_offset = None
#rack_offset = (1.0, 1.0, 0.0)

