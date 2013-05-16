#!/usr/bin/env python

import topology
import model

import sys

w,h = map(int, sys.argv[1:])
direction = topology.EAST
start_coord = (0,0)



boards = model.rhombus_to_rect(model.create_threeboards(w,h), (w,h))
#boards = model.create_threeboards(w,h)

print r"\section*{$%d \times %d$}"%(w,h)
print r"\begin{tikzpicture}[hexagonBoardXYZ]"

for b, (x,y) in boards:
	print r"""
		\node [draw,hexagonBoard,minimum size=1cm,inner sep=0]
			(node %d)
			at (%d,%d)
			{\tiny %s}
			;
	"""%(id(b), x,y, "%d,%d"%(topology.hex_to_cartesian((x,y,0))))

for start_board, coord in boards:
	if coord == start_coord:
		break


steps = {}

DIR_NAMES = {
	topology.EAST       : "east",
	topology.NORTH_EAST : "north east",
	topology.NORTH      : "north",
	topology.WEST       : "west",
	topology.SOUTH_WEST : "south west",
	topology.SOUTH      : "south",
}

for direction, colour in [ (topology.NORTH,      "red")
                         , (topology.SOUTH_WEST, "green")
                         , (topology.EAST,       "blue")
                         ]:
	points = map( (lambda b: "node %d.center"%id(b))
	            , model.follow_wiring_loop( start_board
	                                      , direction
	                                      )
	            )
	#points = map( (lambda (iws,b): "node %d.side %s"%(id(b), DIR_NAMES[iws]))
	#            , model.follow_packet_loop( start_board
	#                                      , topology.opposite(direction)
	#                                      , direction
	#                                      )
	#            )
	steps[direction] = (colour, len(points))
	
	# Draw a line
	print r"\draw [thick,%s] %s;"%(
		colour,
		"--".join("(%s)"%p for p in points)
	)
	
	# Draw blobs on each
	for p in points:
		print r"\node [fill,%s,circle,minimum size=0.2cm,inner sep=0] at (%s) {};"%(colour, p)

print r"\end{tikzpicture}"

print r"\begin{description}"
for direction, (colour, steps) in steps.iteritems():
	english = DIR_NAMES[direction]
	#print r"\item [\color{%s}%s] %d steps"%(colour, english, (steps/2)*3*4)
	print r"\item [\color{%s}%s] %d steps"%(colour, english, steps)
print r"\end{description}"
