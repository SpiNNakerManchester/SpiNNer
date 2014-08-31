#!/usr/bin/env python

"""
Utility functions for displaying diagrams of machines using Cairo and PyGame.
Itended to be used as part of an interactive wiring assistant.
"""

#!/usr/bin/env python
# Copyleft 2010 Niels Serup, WTFPL 2.0. Free software.
 
### Imports ###
import math
import pygame
import cairo
import numpy

from PIL import Image
import sys

from wiring_plan_generator import generate_wiring_plan, flatten_wiring_plan
from machine_diagram import MachineDiagram

### Constants ###
width, height = 1000, 700
param_file = sys.argv[1]


### Functions ###
def draw(ctx, radius):
	pass

def bgra_surf_to_rgba_string(cairo_surface):
	# On little-endian machines (and perhaps big-endian, who knows?),
	# Cairo's ARGB format becomes a BGRA format. PyGame does not accept
	# BGRA, but it does accept RGBA, which is why we have to convert the
	# surface data. You can check what endian-type you have by printing
	# out sys.byteorder
	# We use PIL to do this
	img = Image.frombuffer(
		'RGBA', (cairo_surface.get_width(),
		         cairo_surface.get_height()),
		cairo_surface.get_data(), 'raw', 'BGRA', 0, 1)
	
	return img.tostring('raw', 'RGBA', 0, 1)


### Body ###
# Init PyGame
pygame.display.init()
screen = pygame.display.set_mode((width, height), 0, 32)

# Create raw surface data (could also be done with something else than
# NumPy)
data = numpy.empty(width * height * 4, dtype=numpy.int8)



from model_builder import build_model
from param_parser import parse_params

################################################################################
# Load Parameters
################################################################################

def load_wiring():
	params = parse_params(["machine_params/universal.param", param_file])
	
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
	
	( wires_between_slots
	, wires_between_racks
	, wires_between_cabinets
	) = generate_wiring_plan( cabinet_torus
	                        , phys_torus
	                        , wire_positions
	                        , available_wires
	                        , minimum_arc_height
	                        )
	
	wires_ = flatten_wiring_plan( wires_between_slots
	                            , wires_between_racks
	                            , wires_between_cabinets
	                            , wire_positions
	                            )
	
	b2p = dict(cabinet_torus)
	
	wires = []
	for (src_board, src_direction), (dst_board, dst_direction), wire_length in wires_:
		src = list(b2p[src_board]) + [src_direction]
		dst = list(b2p[dst_board]) + [dst_direction]
		wires.append((src, dst, wire_length))
	
	return cabinet_system, wires

cabinet_system, wires = load_wiring()

def reblit(step):
	# Create Cairo surface
	cairo_surface = cairo.ImageSurface.create_for_data(
	    data, cairo.FORMAT_ARGB32, width, height, width * 4)
	
	md = MachineDiagram(cabinet_system)
	
	# Draw with Cairo on the surface
	ctx = cairo.Context(cairo_surface)
	for wire_step, (src, dst, len) in enumerate(wires):
		if wire_step < step:
			md.add_wire(src, dst, (0.5, 0.5, 0.5, 0.5), 0.005)
		elif wire_step == step:
			md.add_wire(src, dst, (1.0, 0.0, 0.0, 1.0), 0.008)
		else:
			break
	md.draw(ctx, width, height)
	 
	data_string = bgra_surf_to_rgba_string(cairo_surface)
	del cairo_surface, ctx, md
	 
	# Create PyGame surface
	pygame_surface = pygame.image.frombuffer(
	    data_string, (width, height), 'RGBA')
	 
	# Show PyGame surface
	screen.fill( (1,1,1) )
	screen.blit(pygame_surface, (0,0)) 
	pygame.display.flip()
	
	del data_string

clock = pygame.time.Clock()
num_steps = len(wires)
step = 0
while not pygame.QUIT in [e.type for e in pygame.event.get()]:
    clock.tick(15)
    reblit(step)
    step += 1
    step %= num_steps
