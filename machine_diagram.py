#!/usr/bin/env python

"""
A module which generates diagrams (using Cairo) of cabinetised systems.

If called on its own this file produces an image of a specified system as a
PNG, e.g.::

  python2 machine_diagram.py my_machine.param output.png 800 600
"""

import cairo

from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST


class MachineDiagram(object):
	"""
	An object which can be configured to (quickly) generate wiring diagrams of
	large SpiNNaker machines using Cairo.
	"""
	
	# Colours of various components
	#                 R    G    B    A
	CABINET_COLOUR = (0.3, 0.3, 0.3, 1.0)
	RACK_COLOUR    = (0.7, 0.7, 0.7, 1.0)
	SLOT_COLOUR    = (0.7, 1.0, 0.7, 1.0)
	SOCKET_COLOUR  = (0.5, 0.5, 0.5, 1.0)
	
	def __init__(self, cabinet_system, cabinet_torus):
		"""
		cabinet_system is a model.cabinet.System describing the physical parameters
		of the machine in question.
		
		cabinet_torus is a list [(board, (cabinet, rack, slot)), ...] enumerating
		all boards (and their positions) within a set of cabinets.
		"""
		self.cabinet_system = cabinet_system
		self.cabinet_torus  = cabinet_torus
		
		# Set of wires to draw as a list [ ((c,r,s,d) , (c,r,s,d) , rgba, width),
		# ...] specifying source and destination cabinets, racks, slots and
		# directions.
		self.wires = []
	
	
	def add_wire( self
	            , src , dst
	            , rgba = (0.0, 0.0, 0.0, 1.0)
	            , width = 0.002
	            ):
		"""
		Cause the listed wire to be drawn from src and to dst where these arguments
		are (cabinet, rack, slot, direction) tuples.
		
		rgba is a tuple (red, green, blue, alpha) specifiying how the wire will
		appear in the image.
		
		width is a tuple specifiying how thick the wire should be drawn (in meters).
		"""
		self.wires.append((src, dst, rgba, width))
	
	
	def get_cabinet_position(self, c):
		"""
		Get the (x,y) of the top-left corner of a cabinet in meters.
		"""
		# Get coordinates of cabinet
		num_cabinets    = self.cabinet_system.num_cabinets
		cabinet_width   = self.cabinet_system.cabinet.dimensions[0]
		cabinet_spacing = self.cabinet_system.cabinet_spacing
		x = (cabinet_width+cabinet_spacing) * (num_cabinets - c - 1)
		y = 0.0
		
		return (x,y)
	
	
	def get_rack_offset(self, r):
		"""
		Get the offset in meters from the top-left of a cabinet to the top-left of
		the given rack.
		"""
		num_racks    = self.cabinet_system.cabinet.num_racks
		rack_height  = self.cabinet_system.cabinet.rack.dimensions[1]
		rack_spacing = self.cabinet_system.cabinet.rack_spacing
		rack_offset  = self.cabinet_system.cabinet.offset
		
		x = rack_offset[0]
		y = self.cabinet_system.cabinet.dimensions[1] - rack_offset[1] - rack_height
		
		y += -(rack_height+rack_spacing) * (num_racks - r - 1)
		
		return (x,y)
	
	
	def get_rack_position(self, c, r):
		"""
		Get the coordinates of the top-left corner of a given rack in meters.
		"""
		xc,yc = self.get_cabinet_position(c)
		xr,yr = self.get_rack_offset(r)
		return (xc+xr, yc+yr)
	
	
	def get_slot_offset(self, s):
		"""
		Get the offset in meters from the top-left of a rack to the top-left of the
		given slot.
		"""
		num_slots    = self.cabinet_system.cabinet.rack.num_slots
		slot_height  = self.cabinet_system.cabinet.rack.slot.dimensions[1]
		slot_width   = self.cabinet_system.cabinet.rack.slot.dimensions[0]
		slot_spacing = self.cabinet_system.cabinet.rack.slot_spacing
		slot_offset  = self.cabinet_system.cabinet.rack.offset
		
		x = slot_offset[0]
		y = self.cabinet_system.cabinet.rack.dimensions[1] - slot_offset[1] - slot_height
		
		# TODO
		x += (slot_width+slot_spacing) * (num_slots - s - 1)
		
		return (x, y)
	
	
	def get_slot_position(self, c, r, s):
		"""
		Get the coordinates of the top-left corner of a given slot in meters.
		"""
		xr,yr = self.get_rack_position(c, r)
		xs,ys = self.get_slot_offset(s)
		return (xr+xs, yr+ys)
	
	
	def _get_socket_dimensions(self):
		wire_positions = self.cabinet_system.cabinet.rack.slot.wire_position
		sw, sh, _ = self.cabinet_system.cabinet.rack.slot.dimensions
		
		w = (sw-wire_positions[NORTH][0])/2
		h = (wire_positions[NORTH][1] - wire_positions[SOUTH][1])*0.9
		
		return (w, h)
	
	
	def get_socket_offset(self, direction):
		"""
		Get the offset from the top-left of a slot the top-left of a socket in
		meters.
		"""
		wire_positions = self.cabinet_system.cabinet.rack.slot.wire_position
		
		w,h,_ = self.cabinet_system.cabinet.rack.slot.dimensions
		x,y,z = wire_positions[direction]
		return (x, h-y)
	
	
	def get_socket_position(self, c,r,s, direction):
		"""
		Get the coordinates of the top-left of a socket in meters.
		"""
		xs,ys = self.get_slot_position(c, r, s)
		xp,yp = self.get_socket_offset(direction)
		return (xs+xp, ys+yp)
	
	
	def get_socket_center_offset(self):
		"""
		Get the offset from the top-left of a socket to the center in meters.
		"""
		x,y = self._get_socket_dimensions()
		return (x/2.0, y/2.0)
	
	
	def get_socket_center_position(self, c,r,s, direction):
		"""
		Get the coordinates of the center of a socket in meters.
		"""
		xs,ys = self.get_socket_position(c,r,s, direction)
		xc,yc = self.get_socket_center_offset()
		return (xs+xc, ys+yc)
	
	
	def _draw_slot(self, ctx):
		"""
		Draw a single board. Assumes the top-left corner of the rack to
		draw is at (0,0).
		"""
		# Draw the slot
		w, h, _ = self.cabinet_system.cabinet.rack.slot.dimensions
		ctx.rectangle(0,0,w,h)
		ctx.set_source_rgba(*self.SLOT_COLOUR)
		ctx.fill()
		
		# Draw the sockets
		wire_positions = self.cabinet_system.cabinet.rack.slot.wire_position
		ww,wh = self._get_socket_dimensions()
		
		ctx.set_source_rgba(*self.SOCKET_COLOUR)
		for wire, (x,y,z) in wire_positions.items():
			ctx.rectangle(x, h-y, ww, wh)
			ctx.fill()
	
	
	def _draw_slots(self, ctx):
		"""
		Draw every board in a rack (with rack top-left at (0,0).
		"""
		for slot_num in range(self.cabinet_system.cabinet.rack.num_slots):
			ctx.save()
			ctx.translate(*self.get_slot_offset(slot_num))
			self._draw_slot(ctx)
			ctx.restore()
		
	
	def _draw_rack(self, ctx):
		"""
		Draw a single rack. Assumes the top-left corner of the rack to
		draw is at (0,0).
		"""
		w, h, _ = self.cabinet_system.cabinet.rack.dimensions
		ctx.rectangle(0,0,w,h)
		ctx.set_source_rgba(*self.RACK_COLOUR)
		ctx.fill()
		
		self._draw_slots(ctx)
	
	def _draw_racks(self, ctx):
		"""
		Draw every rack in a cabinet (with cabinet top-left at (0,0).
		"""
		for rack_num in range(self.cabinet_system.cabinet.num_racks):
			ctx.save()
			ctx.translate(*self.get_rack_offset(rack_num))
			self._draw_rack(ctx)
			ctx.restore()
	
	
	def _draw_cabinet(self, ctx):
		"""
		Draw a single cabinet in the given context with top-left corner at (0,0)
		and scaled in meters.
		"""
		w, h, _ = self.cabinet_system.cabinet.dimensions
		ctx.rectangle(0,0,w,h)
		ctx.set_source_rgba(*self.CABINET_COLOUR)
		ctx.fill()
		
		self._draw_racks(ctx)
	
	
	def _draw_cabinets(self, ctx):
		"""
		Draw every cabinet in the system
		"""
		for cabinet_num in range(self.cabinet_system.num_cabinets):
			ctx.save()
			ctx.translate(*self.get_cabinet_position(cabinet_num))
			self._draw_cabinet(ctx)
			ctx.restore()
	
	
	def _draw_wires(self, ctx):
		"""
		Draw all wires in the system specified by add_wire.
		"""
		for src, dst, rgba, width in self.wires:
			ctx.move_to(*self.get_socket_center_position(*src))
			ctx.line_to(*self.get_socket_center_position(*dst))
			ctx.set_source_rgba(*rgba)
			ctx.set_line_width(width)
			ctx.stroke()
	
	
	def draw(self, ctx, max_width, max_height, cabinet = None, rack = None, slot = None):
		"""
		Draw the diagram onto the supplied context at the sizes defined. Optionally
		zoom the diagram to a specific cabinet, rack or slot.
		
		ctx is a Cairo drawing context onto which the diagram will be drawn
		
		max_width and max_height are the maximum dimensions of the context which
		should be used.
		
		cabinet, rack and slot define a desired part of the system to focus on.
		"""
		cabinet_width   = self.cabinet_system.cabinet.dimensions[0]
		cabinet_height  = self.cabinet_system.cabinet.dimensions[1]
		cabinet_spacing = self.cabinet_system.cabinet_spacing
		
		system_width = (cabinet_width+cabinet_spacing) * self.cabinet_system.num_cabinets \
		               - cabinet_spacing
		system_height = cabinet_height
		
		ctx.save()
		
		if cabinet is None:
			focus_x = 0.0
			focus_y = 0.0
			focus_width  = system_width
			focus_height = system_height
		elif rack is None:
			assert cabinet is not None
			focus_x, focus_y = self.get_cabinet_position(cabinet)
			focus_width, focus_height, _  = self.cabinet_system.cabinet.dimensions
		elif slot is None:
			assert cabinet is not None and rack is not None
			focus_x, focus_y = self.get_rack_position(cabinet, rack)
			focus_width, focus_height, _  = self.cabinet_system.cabinet.rack.dimensions
		else:
			assert cabinet is not None and rack is not None and slot is not None
			focus_x, focus_y = self.get_slot_position(cabinet, rack, slot)
			focus_width, focus_height, _  = self.cabinet_system.cabinet.rack.slot.dimensions
		
		# Rescale the drawing such that the system fits the space as well as
		# possible
		fit_to_width_scale  = max_width/focus_width
		fit_to_height_scale = max_height/focus_height
		scale = min(fit_to_width_scale, fit_to_height_scale)
		ctx.translate( (max_width  - (focus_width*scale)) / 2
		             , (max_height - (focus_height*scale)) / 2
		             )
		ctx.scale(scale, scale)
		ctx.translate(-focus_x, -focus_y)
		
		# Draw the cabinets and such
		self._draw_cabinets(ctx)
		
		# Draw the wires
		self._draw_wires(ctx)
		
		ctx.restore()



################################################################################
# Demonstration program
################################################################################

if __name__=="__main__":
	import sys
	import colorsys
	
	from wiring_plan_generator import generate_wiring_plan, flatten_wiring_plan
	
	param_file    = sys.argv[1]
	output_file   = sys.argv[2]
	output_width  = int(sys.argv[3])
	output_height = int(sys.argv[4])
	
	from model_builder import build_model
	from param_parser import parse_params
	
	################################################################################
	# Load Parameters
	################################################################################
	
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
	
	wires = flatten_wiring_plan( wires_between_slots
	                           , wires_between_racks
	                           , wires_between_cabinets
	                           , wire_positions
	                           )
	
	b2p = dict(cabinet_torus)
	
	surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, output_width, output_height)
	ctx = cairo.Context (surface)
	
	md = MachineDiagram(cabinet_system, cabinet_torus)
	
	for num, ((src_board, src_direction), (dst_board, dst_direction), wire_length) in enumerate(wires):
		src = list(b2p[src_board]) + [src_direction]
		dst = list(b2p[dst_board]) + [dst_direction]
		
		r,g,b = colorsys.hsv_to_rgb(num/float(len(wires)), 1.0, 1.0)
		
		md.add_wire(src, dst, (r,g,b, 1.0))
	
	md.draw(ctx, output_width, output_height)
	surface.write_to_png(output_file)
