"""
Tools for producing diagrams which show the network topology overlaid with board
boundaries and physical locations.
"""

import cairocffi as cairo

from math import pi, sin, cos, tan

from spinner.topology import to_xy, board_to_chip, hexagon_zero
from spinner.topology import Direction

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
	
	edge_num = {
		Direction.south:      0,
		Direction.east:       1,
		Direction.north_east: 2,
		Direction.north:      3,
		Direction.west:       4,
		Direction.south_west: 5,
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
	ctx.transform(cairo.Matrix( 1.0,           0.0
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


def _draw_board(ctx, x,y, width_chips, height_chips, btm_left_chip, board_label):
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
		_draw_edge(ctx, x_, y_, Direction.north)
		
		if northempty and northeastempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		elif northeastempty and eastempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, Direction.north_east)
		
		if eastempty and southempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		elif northeastempty and eastempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, Direction.east)
		
		if eastempty and southempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		elif southempty and southwestempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, Direction.south)
		
		if westempty and southwestempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		elif southempty and southwestempty:
			ctx.set_line_width(N_S_EDGE_WIDTH)
			ctx.set_source_rgba(*N_S_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, Direction.south_west)
		
		if westempty and southwestempty:
			ctx.set_line_width(NE_SW_EDGE_WIDTH)
			ctx.set_source_rgba(*NE_SW_EDGE_COLOUR)
		elif northempty and westempty:
			ctx.set_line_width(W_E_EDGE_WIDTH)
			ctx.set_source_rgba(*W_E_EDGE_COLOUR)
		else:
			ctx.set_line_width(INTERNAL_EDGE_WIDTH)
			ctx.set_source_rgba(*INTERNAL_EDGE_COLOUR)
		_draw_edge(ctx, x_, y_, Direction.west)
	
	
	# Draw the board's (0,0) chip label and dot
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
	elif y+max_y > height_chips:  # pragma: no branch
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

def draw_machine_map(ctx, image_width, image_height,
                     width, height,
                     hex_boards, cabinetised_boards):
	"""
	Given a Cairo context (and the size of the rectangle to draw in), draws a map of
	the machine. Takes the width and height of the system in triads, hex_boards
	(mapping 3D hexagonal board coordinates to boards) and a cabinetised version
	of the same.
	"""
	ctx.save()
	
	# Number of chips in the system
	width_chips  = width  * 12
	height_chips = height * 12
	
	# Get the extent of the cabinets used
	max_cabinet = max(c for (b,(c,f,b)) in cabinetised_boards)
	max_frame   = max(f for (b,(c,f,b)) in cabinetised_boards)
	max_board   = max(b for (b,(c,f,b)) in cabinetised_boards)
	
	# Lookup from board to cabinet position
	b2c = dict(cabinetised_boards)
	
	# Rescale the drawing such that the diagram is rescaled to nicely fit in the
	# space given
	diagram_width  = width_chips  + (2.0*MARGIN)
	diagram_height = height_chips + (2.0*MARGIN)
	scale = min(image_width/diagram_width, image_height/diagram_height)
	ctx.translate( (image_width  - (diagram_width*scale)) / 2
	             , (image_height - (diagram_height*scale)) / 2
	             )
	ctx.scale(scale, scale)
	
	ctx.set_line_cap(cairo.LINE_CAP_ROUND)
	
	# Move to bottom-left chip
	ctx.translate(MARGIN, height_chips+MARGIN)
	
	# Draw coordinates around edge
	_draw_coords(ctx, width_chips, height_chips)
	
	# Draw each board
	for board, board_pos in hex_boards:
		x,y = to_xy(board_to_chip(board_pos))
		c,f,b = b2c[board]
		_draw_board( ctx
		           , x,y, width_chips, height_chips
		           , "(%d,%d)"%(x,y)
		           , ("C%d "%c if max_cabinet else "")
		             + ("F%d "%f if max_frame else "")
		             + ("B%d"%b)
		           )
	
	ctx.restore()


def get_machine_map_aspect_ratio(width, height):
	"""Given a system size (in triads), returns the aspect ratio of the diagram
	generated by draw_machine_map.
	"""
	diagram_width  = (width * 12)  + (2.0*MARGIN)
	diagram_height = (height * 12) + (2.0*MARGIN)
	
	return diagram_width / float(diagram_height)
