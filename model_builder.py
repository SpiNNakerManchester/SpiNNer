#!/usr/bin/env python

"""
Utility function which builds SpiNNaker-like models based on a given
specification.
"""

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

from model import cabinet
from model import board
from model import transforms
from model import coordinates

def build_model( slot_width,    slot_height,    slot_depth
               , rack_width,    rack_height,    rack_depth
               , cabinet_width, cabinet_height, cabinet_depth
               , wire_positions
               , slot_spacing, slot_offset, num_slots_per_rack
               , rack_spacing, rack_offset, num_racks_per_cabinet
               , cabinet_spacing, num_cabinets
               , width, height
               , num_folds_x, num_folds_y
               , compress_rows
               ):
	"""
	Build a model of a spinnaker system. Returns a tuple::
		
		( torus
		, cart_torus
		, rect_torus
		, comp_torus
		, fold_spaced_torus
		, folded_cabinet_spaced_torus
		, cabinet_torus
		, phys_torus
		, cabinet_system
		)
	"""
	# Set up the cabinet data structure
	cabinet_system = cabinet.System(
		cabinet = cabinet.Cabinet(
			rack = cabinet.Rack(
				slot = cabinet.Slot(
					dimensions    = (slot_width, slot_height, slot_depth),
					wire_position = wire_positions,
				),
				dimensions   = (rack_width, rack_height, rack_depth),
				num_slots    = num_slots_per_rack,
				slot_spacing = slot_spacing,
				slot_offset  = slot_offset,
			),
			dimensions   = (cabinet_width, cabinet_height, cabinet_depth),
			num_racks    = num_racks_per_cabinet,
			rack_spacing = rack_spacing,
			rack_offset  = rack_offset,
		),
		num_cabinets    = num_cabinets,
		cabinet_spacing = cabinet_spacing,
	)
	
	# Create an inter-linked torus
	torus = board.create_torus(width, height)
	
	# Convert to Cartesian coordinates as the coming manipulations use/abuse this
	cart_torus = transforms.hex_to_cartesian(torus)
	
	# Cut the left-hand side of the torus off and move it to the right to form a
	# rectangle
	rect_torus = transforms.rhombus_to_rect(cart_torus)
	
	# Compress the coordinates to eliminate the "wavy" pattern on the y-axis turning
	# the board coordinates into a continuous mesh.
	comp_torus = transforms.compress(rect_torus, 1 if compress_rows else 2
	                                           , 2 if compress_rows else 1
	                                           )
	
	# Show where the folds will occur
	fold_spaced_torus = transforms.space_folds(comp_torus, (num_folds_x, num_folds_y))
	
	# Actually do the folds
	folded_torus = transforms.fold(comp_torus, (num_folds_x, num_folds_y))
	
	# Place spaces in the folded version to see how it folded
	folded_spaced_torus = transforms.space_folds(folded_torus, (num_folds_x, num_folds_y))
	
	# Place spaces where the design is split into racks & cabinets
	folded_cabinet_spaced_torus = transforms.space_folds(folded_torus, (num_cabinets, num_racks_per_cabinet))
	
	# Map to cabinets
	cabinet_torus = transforms.cabinetise( folded_torus
	                                     , num_cabinets
	                                     , num_racks_per_cabinet
	                                     , num_slots_per_rack
	                                     )
	
	# Map to physical space for the cabinets described
	phys_torus = transforms.cabinet_to_physical(cabinet_torus, cabinet_system)
	
	return ( torus
	       , cart_torus
	       , rect_torus
	       , comp_torus
	       , fold_spaced_torus
	       , folded_cabinet_spaced_torus
	       , cabinet_torus
	       , phys_torus
	       , cabinet_system
	       )


