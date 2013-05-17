#!/usr/bin/env python

import topology
import model

from operator import sub
from math import sin, cos, pi, sqrt

import sys

w,h, x_folds, y_folds, x_cabinates, y_racks = map(int, sys.argv[1:])
skew = False
direction = topology.EAST
start_coord = (0,0)



# Load the boards
boards = model.create_threeboards(w,h)


if not skew:
	# Convert to cartesian coords
	boards = [
		(board, topology.hex_to_cartesian(list(coord)+[0]))
		for (board, coord) in
		boards
	]
	
	b2hc = dict(boards)
	
	# Wrap around
	boards = [(b, (x%(w*2), y%(h*3))) for (b,(x,y)) in boards]
	
	# Squash into rows and columns
	boards = [(b, (x, y/2)) for (b,(x,y)) in boards]
else:
	boards = [
		(board, topology.hex_to_skew_cartesian(list(coord)+[0]))
		for (board, coord) in
		boards
	]
	
	b2hc = dict(boards)

#if not skew:
#	max_x = w*2 
#	max_y = (h*3)/2
#else:
#	max_x = w*3
#	max_y = h*3

# Show With Folds
max_x,max_y = map(max, *((x,y) for (b,(x,y)) in boards))
boards = [(b, ( topology.fold_interleave_dimension(x,max_x+1,x_folds)
              , topology.fold_interleave_dimension(y,max_y+1,y_folds)
              ))
          for (b,(x,y)) in boards]

#boards = model.compress_layout(boards)
#max_x = w*2
#max_y = (h*3)/2

b2c = dict(boards)

## Show Fold Gaps
#max_x,max_y = map(max, *((x,y) for (b,(x,y)) in boards))
#boards = [(b, ( x + 2*topology.fold_dimension(x,max_x+1,x_folds)[1]
#              , y + 2*topology.fold_dimension(y,max_y+1,y_folds)[1]
#              ))
#          for (b,(x,y)) in boards]

# Show Cabinate Gaps
max_x,max_y = map(max, *((x,y) for (b,(x,y)) in boards))
boards = [(b, ( x + 2*topology.fold_dimension(x,max_x+1,x_cabinates)[1]
              , y + 2*topology.fold_dimension(y,max_y+1,y_racks)[1]
              ))
          for (b,(x,y)) in boards]

#if not skew:
#	# Scale x-axis
#	boards = [(b, (x*cos(pi/6), y/2.0)) for (b,(x,y)) in boards]


print r"\section*{$%d \times %d$}"%(w,h)

#print r"\begin{tikzpicture}[yscale=0.5,xscale=1/\hexRadiusScale]"
print r"\begin{tikzpicture}[]"

if not skew:
	print r"""
	\newcommand{\hex}[3]{
		\node [draw,hexagonBoard, minimum size=1cm, inner sep=0]
			at (#1) (#2) {#3};
		
		\coordinate (#2 side south west) at (#2.side south west);
		\coordinate (#2 side west)       at (#2.side west);
		\coordinate (#2 side north)      at (#2.side north);
		\coordinate (#2 side north east) at (#2.side north east);
		\coordinate (#2 side east)       at (#2.side east);
		\coordinate (#2 side south)      at (#2.side south);
	}
	"""
else:
	print r"""
	\newcommand{\hex}[3]{
		\begin{scope}[scale=0.5]
			\node at ([shift={(1,1)}]#1) (#2) {#3};
			
			\draw                                   (#1)
			   -- coordinate (#2 side south west) ++(0,1)
			   -- coordinate (#2 side west)       ++(1,1)
			   -- coordinate (#2 side north)      ++(1,0)
			   -- coordinate (#2 side north east) ++(0,-1)
			   -- coordinate (#2 side east)       ++(-1,-1)
			   -- coordinate (#2 side south)      ++(-1,0)
			   -- cycle
			      ;
		\end{scope}
	}
	"""


for b, (x,y) in boards:
	print r"""
		\hex{%f,%f}{node %d}{\tiny %s}
	"""%(x,y, id(b), "%d,%d"%b2hc[b])

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


def distance(b1, b2):
	return sqrt(sum(x**2 for x in map(sub, b2c[b1],b2c[b2])))

dir_lengths = {}

# Draw a path from start_board in each primary direction
for direction, colour in [ (topology.NORTH,      "red")
                         , (topology.SOUTH_WEST, "green")
                         , (topology.EAST,       "blue")
                         ]:
	# Draw the wires between boards
	lengths = []
	for board,coords in boards:
		lengths.append(distance(board, board.follow_wire(direction)))
	for board,coords in boards:
			#if distance(board, board.follow_wire(direction)) >= max(lengths)-1:
			print r"\draw [thick,%s] (node %d side %s) -- (node %d side %s);"%(
				colour,
				id(board), DIR_NAMES[direction],
				id(board.follow_wire(direction)), DIR_NAMES[topology.opposite(direction)]
			)
	
	dir_lengths[direction] = lengths
	
	
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
	
	## Draw a line
	#print r"\draw [thick,%s] %s;"%(
	#	colour,
	#	"--".join("(%s)"%p for p in points)
	#)
	#
	## Draw blobs on each
	#for p in points:
	#	print r"\node [fill,%s,circle,minimum size=0.2cm,inner sep=0] at (%s) {};"%(colour, p)

print r"\end{tikzpicture}"

print r"\begin{description}"
for direction, (colour, steps) in steps.iteritems():
	english = DIR_NAMES[direction]
	#print r"\item [\color{%s}%s] %d steps"%(colour, english, (steps/2)*3*4)
	print r"\item [\color{%s}%s] %d steps, %f $\le$ len $\le$ %f"%(
		colour, english, steps,
		min(dir_lengths[direction]),
		max(dir_lengths[direction]),
	)
print r"\end{description}"

print r"\begin{itemize}"
for direction, lengths in dir_lengths.iteritems():
	print r"	\item %s Lengths"%DIR_NAMES[direction]
	hist = {}
	for length in lengths:
		hist[length] = hist.get(length,0) + 1
	print r"	\begin{itemize}"
	for length in sorted(hist):
		print r"		\item %f: %d"%(length, hist[length])
	print r"	\end{itemize}"
print r"\end{itemize}"
