#!/usr/bin/env python

"""
A library of functions which calculate various metrics about systems of boards
and their wiring.
"""

import math

from six import integer_types

from spinner import coordinates


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


def physical_wire_length(distance, available_wire_lengths, min_arc_height):
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
	
	min_arc_height is the minimum height of the arc to be allowed.
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
		if arc_height < min_arc_height:
			continue
		
		return (wire_length, arc_height)
	
	raise ValueError(
		"No wire is long enough to span a %0.3f m gap with an arc %0.3f m high."%(
			distance, min_arc_height)) 


def wire_length_histogram(wire_lengths, min_arc_height, bins=10):
	"""
	Generate a histogram of physical wire lengths.
	
	wire_lengths is an iterable of crow-flies wire length values (e.g. from
	wire_lengths). Wires will be chosen for each length based on the
	physical_wire_length function.
	
	min_arc_height is the height of the tightest arc allowed by a wire between two
	connected sockets.
	
	bins is either an int (giving the total number of bins) or a list of wire
	lengths. If the last bin supplied is to short to accomodate the largest input
	wire with a sufficently high arc, a ValueError will be raised.
	
	Returns a (bin_counts, bin_max_arc_heights). bin_counts is a dictionary
	{bin: count, ...} with one entry per histogram bin. Each bin ranges from
	zero or the next-lowest bin to the specified bin. bin_max_arc_heights records
	the maximum wire arc height for wires in each bin.
	"""
	wire_lengths = sorted(wire_lengths)
	
	# Auto-generate bins if required
	if isinstance(bins, integer_types):
		# XXX: Calculating the shortest wire-length possible for a known distance
		# and arc height has no closed-form solution. Though a numerical solution
		# could be used (as in physical_wire_length), since this feature is for
		# "informational purposes", we'll simply start with the maximum distance to
		# be covered and gradually increase this until a large enough arc is
		# achieved.
		max_wire_length = wire_lengths[-1]
		max_physical_wire_length = max_wire_length
		while True:
			try:
				physical_wire_length(max_wire_length, [max_physical_wire_length],
				                     min_arc_height)
				break
			except ValueError:
				# Try again with a longer wire length
				max_physical_wire_length *= 1.1
		
		bins = [((n+1)/float(bins)) * float(max_physical_wire_length)
		        for n in range(bins)]
	else:
		bins = sorted(map(float, bins))
	
	# Construct the histogram
	bin_counts = {bin: 0 for bin in bins}
	bin_max_arc_heights = {bin: 0.0 for bin in bins}
	for distance in wire_lengths:
		bin, arc_height = physical_wire_length(distance, bins, min_arc_height)
		bin_counts[bin] += 1
		bin_max_arc_heights[bin] = max(bin_max_arc_heights[bin], arc_height)
	
	return bin_counts, bin_max_arc_heights

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

