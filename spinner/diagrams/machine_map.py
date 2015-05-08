#!/usr/bin/env python

"""
If executed as a script, the program produces either a graphical or textual
representatation of the position of each core in the system with respect to
cabinets/racks/slots.
"""

from math import pi,sin,cos,tan

from model.coordinates import Hexagonal2D
from model.topology import to_xy, board_to_chip, hexagon_zero
from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

POINTS_PER_MM = 2.83464567

# Margin (in chip widths) around the diagram (must be enough for labels)
MARGIN = 2

# Colours/thicknesses for drawing edges of chips
INTERNAL_EDGE_COLOUR = (0.82, 0.84, 0.81, 1.0)
N_S_EDGE_COLOUR      = (0.80, 0.00, 0.00, 1.0)
W_E_EDGE_COLOUR      = (0.30, 0.60, 0.02, 1.0)
NE_SW_EDGE_COLOUR    = (0.20, 0.40, 0.64, 1.0)

INTERNAL_EDGE_WIDTH = 0.03
N_S_EDGE_WIDTH      = 0.1
W_E_EDGE_WIDTH      = 0.1
NE_SW_EDGE_WIDTH    = 0.1

# Text label sizes/colours
BTM_LEFT_CHIP_LABEL_COLOUR = (0.33, 0.34, 0.32, 1.0)
BOARD_LABEL_COLOUR         = (0.33, 0.34, 0.32, 0.5)
COORD_LABEL_COLOUR         = (0.53, 0.54, 0.52, 1.0)

BTM_LEFT_CHIP_LABEL_SIZE = 0.6
BOARD_LABEL_SIZE = 1.1
COORD_LABEL_SIZE = 0.6

COORD_LABEL_OFFSET = 0.4

# Dot to place on the bottom left chip
BTM_LEFT_CHIP_DOT_COLOUR = BTM_LEFT_CHIP_LABEL_COLOUR
BTM_LEFT_CHIP_DOT_SIZE = 0.20


def D2R(d):
	"""
	Convert degrees to radians.
	"""
	return (float(d)/180.0)*pi


def _draw_edge(ctx, x,y, edge):
	"""
	Draw the specified single edge of a hexagon whose bottom-left corner is at
	(x,y) using whatever style is currently set.
	"""
	from cairo import Matrix
	
	edge_num = {
		SOUTH:      0,
		EAST:       1,
		NORTH_EAST: 2,
		NORTH:      3,
		WEST:       4,
		SOUTH_WEST: 5,
	}[edge]
	
	# The transformation to use when drawing hexagons such that they sit on an x,y
	# grid.
	ctx.save()
	x_scale = 1.0/(2.0*sin(D2R(60)))
	y_scale = 1.0/(1.0+cos(D2R(60)))
	ctx.translate( (0.25*tan(D2R(60))) * x_scale
	             , 0.5*sin(D2R(30)) * y_scale
	             )
	ctx.move_to(x,y)
	ctx.transform(Matrix( 1.0,           0.0
	                    , -cos(D2R(60)), 1.0
	                    ))
	ctx.scale( x_scale
	         , y_scale
	         )
	
	# Draw the specified edge 
	ctx.rotate(D2R(30))
	for _ in range(edge_num):
		ctx.rotate(D2R(-60))
		ctx.rel_move_to(1.0,0.0)
	ctx.rotate(D2R(-60))
	ctx.rel_line_to(1.0,0.0)
	ctx.restore()
	
	ctx.stroke()


def _draw_text(ctx, text, align_point=0.0, size = 1.0, rgba = (0.0,0.0,0.0, 1.0)):
	"""
	Draw the desired text centered vertically around (0,0) horizontally
	"align_point" along the text's width.
	"""
	ctx.save()
	
	ctx.select_font_face("Sans")
	ctx.set_source_rgba(*rgba)
	ctx.set_font_size(size)
	x,y, w,h, _w,_h = ctx.text_extents(text)
	ctx.move_to(-x + ((1.0-w)*align_point), -y - size/2)
	ctx.show_text(text)
	
	ctx.restore()


def _draw_board(ctx, x,y, width_chips, height_chips, btm_left_chip=None, board_label=None):
	"""
	Draw a board at the given position onto the given context in a system of the
	given width/height in chips. If specified a label will be added to the
	bottom-left chip and the board as a whole. Edges of chips at the edge of the
	board will be drawn differently to indicate which HSS link they will use.
	"""
	# Draw the chips
	hexagon = set(hexagon_zero())
	max_x = max(x for (x,y) in hexagon)
	max_y = max(y for (x,y) in hexagon)
	for dx,dy in hexagon:
		northempty     = (dx+0, dy+1) not in hexagon
		southempty     = (dx+0, dy-1) not in hexagon
		southwestempty = (dx-1, dy-1) not in hexagon
		westempty      = (dx-1, dy+0) not in hexagon
		eastempty      = (dx+1, dy+0) not in hexagon
		northeastempty = (dx+1, dy+1) not in hexagon
		
		x_ =   (x+dx)%width_chips
		y_ = -((y+dy)%height_chips)
		
		if northempty and northeastempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		elif northempty and westempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, NORTH)
		
		if northempty and northeastempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		elif northeastempty and eastempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, NORTH_EAST)
		
		if eastempty and southempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		elif northeastempty and eastempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, EAST)
		
		if eastempty and southempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		elif southempty and southwestempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, SOUTH)
		
		if westempty and southwestempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		elif southempty and southwestempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, SOUTH_WEST)
		
		if westempty and southwestempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		elif northempty and westempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, WEST)
	
	
	# Draw the (0,0) label and dot
	if btm_left_chip is not None:
		ctx.save()
		ctx.translate(x+0.5, -y-0.5)
		
		# Dot
		ctx.set_source_rgba(*BTM_LEFT_CHIP_DOT_COLOUR)
		ctx.arc( 0.0,0.0
		       , BTM_LEFT_CHIP_DOT_SIZE/2.0
		       , 0.0, 2.0*pi
		       )
		ctx.fill()
		
		# Label
		ctx.translate(BTM_LEFT_CHIP_DOT_SIZE*1.5, 0.0)
		_draw_text( ctx
		          , btm_left_chip
		          , align_point = 0.0
		          , size = BTM_LEFT_CHIP_LABEL_SIZE
		          , rgba = BTM_LEFT_CHIP_LABEL_COLOUR
		          )
		ctx.restore()
	
	
	# Draw the board label
	if board_label is not None:
		positions = []
		
		# Position (or duplicate) appropriately depending on splitting of the board
		if x+max_x < width_chips and y+max_y < height_chips:
			# Not split
			positions.append((x+(0.5*max_x), -y-(0.5*max_y)))
		elif x+max_x > width_chips:
			# Split on the right edge
			positions.append((x+(0.5*(width_chips-x)), -y-(0.33*max_y)))
			# Split on the left edge
			positions.append(((0.5*(max_x-(width_chips-x))), -y-(0.66*max_y)))
			
			board_label = board_label.replace(" ","\n")
		elif y+max_y > height_chips:
			# Split on top edge
			positions.append((x+(0.33*max_x), -y-(0.5*(height_chips-y))))
			# Split on bottom edge
			positions.append((x+(0.66*max_x), 0.5-(0.5*(max_y-(height_chips-y)))))
		
		for x_,y_ in positions:
			ctx.save()
			ctx.translate(x_,y_)
			lines = board_label.split("\n")
			ctx.translate(0.0, -(BOARD_LABEL_SIZE*(len(lines)/2.0)))
			for num, line in enumerate(lines):
				_draw_text( ctx
				          , line
				          , align_point = 0.5
				          , size = BOARD_LABEL_SIZE
				          , rgba = BOARD_LABEL_COLOUR
				          )
				ctx.translate(0.0, BOARD_LABEL_SIZE)
			ctx.restore()


def _draw_coords(ctx, width, height):
	"""
	Given a context and a width and height in chips, draw numbered ticks along the
	edges of the diagram.
	"""
	for num, rotation, offset, alignment in ( (height, 0.0,    -1 - COORD_LABEL_OFFSET,          1.0) # Left
	                                        , (height, 0.0,    width + COORD_LABEL_OFFSET,       0.0) # Right
	                                        , (width,  0.5*pi, COORD_LABEL_OFFSET,               0.0) # Bottom
	                                        , (width,  0.5*pi, -height - 1 - COORD_LABEL_OFFSET, 1.0) # Top
	                                        ):
		ctx.save()
		ctx.rotate(rotation)
		ctx.translate(offset, -0.5)
		for i in range(num):
			_draw_text( ctx
			          , str(i)
			          , align_point = alignment
			          , size = COORD_LABEL_SIZE
			          , rgba = COORD_LABEL_COLOUR
			          )
			ctx.translate(0.0, -1.0)
		ctx.restore()

def draw_machine_map( ctx, width, height
                    , torus, cabinet_torus
                    , width_threeboards, height_threeboards
                    ):
	"""
	Given a cairo context (and the size of the area to draw in), draws a map of
	the machine. Takes a torus (mapping 3D hexagonal board coordinates to boards)
	and a cabinetised version of the same, and the width/height of the system in
	threeboards.
	"""
	ctx.save()
	
	# Number of chips in the system
	width_chips  = width_threeboards*12
	height_chips = height_threeboards*12
	
	# Get the extent of the cabinets used
	max_cabinet = max(c for (b,(c,r,s)) in cabinet_torus)
	max_rack    = max(r for (b,(c,r,s)) in cabinet_torus)
	max_slot    = max(s for (b,(c,r,s)) in cabinet_torus)
	
	# Lookup from board to cabinet position
	b2c = dict(cabinet_torus)
	
	# Rescale the drawing such that the diagram is rescaled to nicely fit in the
	# space given
	diagram_width  = width_chips  + (2.0*MARGIN)
	diagram_height = height_chips + (2.0*MARGIN)
	scale = min(width/diagram_width, height/diagram_height)
	ctx.translate( (width  - (diagram_width*scale)) / 2
	             , (height - (diagram_height*scale)) / 2
	             )
	ctx.scale(scale, scale)
	
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	
	# Move to bottom-left chip
	ctx.translate(MARGIN, height_chips+MARGIN)
	
	# Draw coordinates around edge
	_draw_coords(ctx, width_chips, height_chips)
	
	# Draw each board
	for board, board_pos in torus:
		x,y = to_xy(board_to_chip(board_pos))
		c,r,s = b2c[board]
		_draw_board( ctx
		           , x,y, width_chips, height_chips
		           , "(%d,%d)"%(x,y)
		           , ("C%d "%c if max_cabinet else "")
		             + ("R%d "%r if max_rack else "")
		             + ("S%d"%s)
		           )
	
	ctx.restore()
	
	


def get_machine_map(torus, cabinet_torus, width, height, all_chips = False):
	"""
	Given a torus (mapping 3D hexagonal board coordinates to boards) and a
	cabinetised version and the width/height of the system in threeboards, produce
	a list [(chip_x,chip_y, cabinet, rack, slot), ...]. If all_chips is False,
	this list will list only the bottom-left chip of each board, if all_chips is
	True all chips are listed.
	"""
	# Create a listing of boards with bottom-left-chip coordinate
	board_chips = [(b, to_xy(board_to_chip(c))) for (b,c) in torus]
	
	# Add other chips on each board
	if all_chips:
		for board, btm_left_chip_coord in board_chips[:]:
			x,y = btm_left_chip_coord
			for dx,dy in hexagon_zero():
				if (dx, dy) != (0,0):
					board_chips.append((board, Hexagonal2D(x+dx, y+dy)))
	
	# Ensure coordinates are all in their positive form
	chips_width  = width*12
	chips_height = height*12
	board_chips = [(b, Hexagonal2D(x%chips_width, y%chips_height)) for (b,(x,y)) in board_chips]
	
	# Order the list sensibly
	board_chips = sorted(board_chips, key=(lambda (b,c):(c.y,c.x)))
	
	# Mapping from board to cabinet/rack/slot
	board_to_location = dict(cabinet_torus)
	
	out = []
	for board, (x,y) in board_chips:
		c,r,s = board_to_location[board]
		out.append((x,y, c,r,s))
	return out


if __name__=="__main__":
	import sys
	import argparse
	
	from model_builder import build_model
	from param_parser import parse_params
	
	################################################################################
	# Parse command-line arguments
	################################################################################
	
	parser = argparse.ArgumentParser(description = "Machine map generator.")
	
	parser.add_argument( "param_files", type=str, nargs="+"
	                   , help="parameter files describing machine parameters"
	                   )
	
	parser.add_argument( "-a", "--all-chips", action="store_true", default=False
	                   , dest="list_all_chips"
	                   , help="list all chips, including those not at the corner of a board"
	                   )
	
	parser.add_argument( "-g", "--graphical", nargs=2, type=int
	                   , dest="graphical"
	                   , help="instead of a textual listing, produce graphical map as PDF of the given width/height in mm"
	                   )
	
	args = parser.parse_args()
	
	################################################################################
	# Load Parameters
	################################################################################
	params = parse_params(["machine_params/universal.param"] + args.param_files)
	
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
	
	# Fold the system
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
	# Print chip position table
	################################################################################
	
	if args.graphical:
		import cairo
		output_width, output_height = args.graphical
		output_width  *= POINTS_PER_MM
		output_height *= POINTS_PER_MM
		surface = cairo.PDFSurface(sys.stdout, output_width, output_height)
		ctx = cairo.Context (surface)
		draw_machine_map( ctx, output_width, output_height
		                , torus, cabinet_torus
		                , width, height
		                )
	else:
		print("Chip      Location")
		print("-------   --------")
		print("  X   Y    C  R  S")
		print("--- ---   -- -- --")
		for x,y, c,r,s in get_machine_map( torus, cabinet_torus
		                                 , width, height
		                                 , args.list_all_chips
		                                 ):
			print("%3d %3d   %2d %2d %2d"%(x,y,c,r,s))
