#!/usr/bin/env python

"""
A library of functions which calculate various metrics about systems of boards
and their wiring.
"""

import math

from six import integer_types

from spinner import coordinates


def wire_length(boards, board, direction, board_wire_offset=None):
	"""
	Returns the length of a wire leaving the specified board in a given direction.
	
	boards is a list [(board, coord),...)] where all coords support subtraction
	and magnitude() (such as those from the coordinates module).
	
	board is a board in that list
	
	direction is a wire direction to measure
	
	"""


def wire_lengths(boards, direction, board_wire_offset=None):
	"""
	Generate a list of as-the-crow-files wire lengths for the supplied system.
	
	board_wire_offset is an (optional) dict {direction:offset,...} where the
	offset of each wire from the left-top-front corner of a board is supplied.
	This structure can be attained from a spinner.cabinet.Cabinet object.
	"""
	b2c = dict(boards)
	
	for board, coord in boards:
		source = b2c[board]
		target = b2c[board.connection[direction]]
		
		# Up-cast the coordinates to 3D
		if len(source) == 2:
			source = coordinates.Cartesian3D(source[0], source[1], 0)
		if len(target) == 2:
			target = coordinates.Cartesian3D(target[0], target[1], 0)
		
		if board_wire_offset is not None:
			source += board_wire_offset[direction]
			target += board_wire_offset[direction.opposite]
		
		yield (source - target).magnitude()


def physical_wire_length(distance, available_wire_lengths, minimum_arc_height):
	"""
	Returns (wire_length, arc_height) for a wire required to span a given
	distance. The wire length is the length of wire chosen from
	available_wire_lengths. The arc-height is the height of the arc of cable
	between the sockets.
		
		          wire_length           -+-
		         , - ~ ~ ~ - ,           |
		     , '               ' ,       | arc_height = r * (1 - cos(alpha/2))
		---:--------distance-------:--- -+-
		  ,  .                   .  ,    |
		 ,      .  ,-'''''-,  .      ,   | r * cos(alpha/2)
		 ,        '. alpha .'   r    ,   |
		 ,             o             ,  -+-
		  ,                         ,
		   ,                       ,
		     ,                  , '
		       ' - , _ _ _ ,  '
		
		distance**2 / (2*wire_length**2) == (1 - cos(alpha)) / alpha**2
	
	
	distance is a crow-flies distance between the sockets to be connected.
	
	available_wire_lengths is a list of available wire lengths
	
	minimum_arc_height is the minimum height of the arc to be allowed.
	"""
	# Select the shortest wire possible for the job
	for wire_length in sorted(available_wire_lengths):
		# Skip wire lengths which are obviously too short
		if wire_length < distance:
			continue
		
		if wire_length >= (distance*math.pi)/2.0:
			# If the wire is too long to make an arc with angle<pi, make a semicircle
			# offset by some fixed distance
			semicircle_length = (distance*math.pi)/2.0
			offset = (wire_length - semicircle_length)/2.0
			arc_height = offset + (distance/2.0)
		else:
			lhs = (distance**2.0 / (2.0*wire_length**2))
			rhs = lambda alpha: (1.0 - math.cos(alpha))/(alpha**2)
			
			# Perform a binary search to find the value of alpha which gets
			# close-enough. Note that rhs is monotonically decreasing as alpha
			# increases.
			max_error = 0.0001
			low = 0.0
			high = math.pi
			while True:
				alpha = (high+low)/2.0
				error = rhs(alpha) - lhs
				if abs(error) < max_error:
					break
				elif error < 0.0:
					high = alpha
				else:
					low = alpha
			
			r = wire_length/alpha
			
			arc_height = r*(1.0 - math.cos(alpha/2.0))
		
		# Try again if this wire results in too-tight an connection
		if arc_height < minimum_arc_height:
			continue
		
		return (wire_length, arc_height)
	
	raise Exception("No wire is long enough to span a %fm gap."%distance) 


def wire_length_histogram(wire_lengths, bins=10):
	"""
	Generate a histogram of wire lengths.
	
	wire_lengths is an iterable of wire length values (e.g. from wire_lengths).
	
	bins is either an int (giving the total number of bins) or a list of bin upper
	bounds. If the last bin supplied is smaller than the longest wire length, a
	ValueError will be raised.
	
	Returns a list [(min, max, count), ...] where each entry indicates the count
	of wire lengths min < x <= max.
	"""
	wire_lengths = sorted(wire_lengths)
	max_wire_length = wire_lengths[-1]
	
	# Auto-generate bins if required
	if isinstance(bins, integer_types):
		bins = [((n+1)/float(bins)) * float(max_wire_length)
		        for n in range(bins)]
	else:
		bins = sorted(map(float, bins))
	
	# Check bins are sufficient
	if bins[-1] < max_wire_length:
		raise ValueError(
			"largest wire length, {}, is larger than largest bin, {}".format(
				max_wire_length, bins[-1]))
	
	# Bin the wire lengths
	last_bin = 0.0
	out = []
	for bin in bins:
		count = 0
		while wire_lengths:
			if wire_lengths[0] <= bin:
				# Add to bin
				wire_lengths.pop(0)
				count += 1
			else:
				# Wire length is too large for this bin
				break
		out.append((last_bin, bin, count))
		last_bin = bin
	
	return out

def dimensions(boards):
	"""
	Return the width and height of the space occupied by the supplied set of
	boards.
	"""
	if len(boards) == 0:
		raise ValueError("Expected at least one board")
	
	return type(boards[0][1])(*(max(c[i] for b, c in boards) + 1
	                            for i in range(len(boards[0][1]))))


def count_wires(boards, direction):
	"""
	Given a cabinetised system, count the number of wires connecting between
	cabinets, between frames or within frames.
	
	direction if given restricts the count to just those directions
	
	Returns a tuple (between_cabinets, between_frames, between_boards) giving the
	counts of wires in each of the categories described above respectively.
	"""
	b2c = dict(boards)
	
	between_cabinets = 0
	between_frames = 0
	between_boards = 0
	
	for board, coord in boards:
		other = board.follow_wire(direction)
		other_coord = b2c[other]
		
		if coord.cabinet != other_coord.cabinet:
			between_cabinets += 1
		elif coord.frame != other_coord.frame:
			between_frames += 1
		else:  # if coord.board != other_coord.board:
			between_boards += 1
	
	return (between_cabinets, between_frames, between_boards)

