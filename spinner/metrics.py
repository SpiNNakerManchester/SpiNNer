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


def physical_wire_length(distance, available_wire_lengths, min_slack):
	"""
	Selects a wire length for a wire required to span a given distance with a
	certain amount of slack. Returns a tuple (selected_wire_length, slack).
	
	distance is a crow-flies distance between the sockets to be connected.
	
	available_wire_lengths is a list of available wire lengths
	
	min_slack is the minimum slack to allow.
	"""
	try:
		wire_length = min(l for l in available_wire_lengths
		                  if l >= (distance + min_slack))
		slack = wire_length - distance
		return (wire_length, slack)
	except ValueError:
		raise ValueError(
			"No wire is long enough to span a %0.3f m gap with %0.3f m of slack."%(
				distance, min_slack)) 


def wire_length_histogram(wire_lengths, min_slack, bins=10):
	"""
	Generate a histogram of physical wire lengths.
	
	wire_lengths is an iterable of crow-flies wire length values (e.g. from
	wire_lengths). Wires will be chosen for each length based on the
	physical_wire_length function.
	
	min_slack is the minimum amount of slack to provide in a wire.
	
	bins is either an int (giving the total number of bins) or a list of wire
	lengths. If the last bin supplied is too short to accomodate the largest
	input wire with sufficient slack, a ValueError will be raised.
	
	Returns a (bin_counts, bin_min_slack, bin_max_slack). bin_counts is a dictionary
	{bin: count, ...} with one entry per histogram bin. Each bin ranges from
	zero or the next-lowest bin to the specified bin. bin_min_slack and
	bin_max_slack record the range of slack for wires in each bin.
	"""
	wire_lengths = sorted(wire_lengths)
	
	# Auto-generate bins if required
	if isinstance(bins, integer_types):
		max_physical_wire_length = max(wire_lengths) + min_slack
		bins = [((n+1)/float(bins)) * float(max_physical_wire_length)
		        for n in range(bins)]
	else:
		bins = sorted(map(float, bins))
	
	# Construct the histogram
	bin_counts = {bin: 0 for bin in bins}
	bin_min_slack = {bin: bin for bin in bins}
	bin_max_slack = {bin: 0.0 for bin in bins}
	for distance in wire_lengths:
		bin, slack = physical_wire_length(distance, bins, min_slack)
		bin_counts[bin] += 1
		bin_min_slack[bin] = min(bin_min_slack[bin], slack)
		bin_max_slack[bin] = max(bin_max_slack[bin], slack)
	
	return bin_counts, bin_min_slack, bin_max_slack

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

