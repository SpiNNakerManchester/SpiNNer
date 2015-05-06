"""Utility functions for generating wiring plans."""

from math import ceil, sqrt

from spinner import board
from spinner import topology
from spinner import coordinates
from spinner import transforms


def ideal_system_size(num_boards):
	"""Calculate the ideal system size for a system with the specified number of
	boards.
	
	Returns
	-------
	(w, h)
		Width and height in triads of the most square system possible with the given
		number of boards. When a square system cannot be made, the function prefers
		taller systems over wider systems. This enables advantageous folding in the
		case where the system is twice as tall as it is wide.
	
	Raises
	------
	TypeError
		If the number of boards is not a multiple of three. (Hexagonal toruses
		require multiples of three boards to construct).
	"""
	if num_boards % 3 != 0:
		raise TypeError("{} is not a multiple of 3".format(num_boards))
	
	# Special case to avoid division by 0
	if num_boards == 0:
		return (0, 0)
	
	# Find the largest pair of factors to discover the squarest system
	for w in reversed(range(1, int(sqrt(num_boards//3)) + 1)):  # pragma: no branch
		if (num_boards//3) % w == 0:
			break
	
	h = (num_boards//3) // w
	
	return (w, h)


def folded_torus(w, h, transformation, uncrinkle_direction, folds):
	"""Generate a 2D arrangement of boards in a (w, h) triad torus folded in the
	specified fashion.
	
	Parameters
	----------
	w : int
		Width of the system in triads
	h : int
		Width of the system in triads
	transformation : "slice" or "shear"
		The transformation to use to map from hexagonal coordinates to a rectangular
		2D grid.
	uncrinkle_direction : "rows" or "columns"
		When uncrinckling the hexagonal mesh into a 2D grid, should groups rows be
		flattened or groups of columns. Typically, rows will be chosen.
	folds : (x, y)
		Number of peieces to fold each dimension into.
	
	Returns
	-------
	(hex_boards, folded_boards)
		hex_boards is a list of tuples (board, Hexagonal(x, y)) giving the logical
		coordinates for each board on a 2D hexagonal grid.
		
		folded_boards is a list of tuples (board, Cartesian2D(x, y)) giving the coordinates of
		the boards laid out such that wirelength is minimised.
	"""
	# Boards in their Hexagonal coordinate system
	hex_boards = board.create_torus(w, h)
	
	if uncrinkle_direction not in ("rows", "columns"):
		raise TypeError("Uncrinkle direction must be 'rows' or 'columns'")
	rows = uncrinkle_direction == "rows"
	cols = uncrinkle_direction == "columns"
	
	if transformation == "slice":
		cart_boards = transforms.rhombus_to_rect(
			transforms.compress(
				transforms.hex_to_cartesian(
					hex_boards),
				x_div=2 if cols else 1, y_div=2 if rows else 1))
	elif transformation == "shear":
		cart_boards = transforms.compress(
				transforms.hex_to_skewed_cartesian(
					hex_boards),
				x_div=3 if cols else 1, y_div=3 if rows else 1)
	else:
		raise TypeError("Unsupported transformation {}".format(transformation))
	
	# Fold and interleave
	folded_boards = transforms.fold(cart_boards, folds)
	
	return (hex_boards, folded_boards)


def min_num_cabinets(num_boards, frames_per_cabinet, boards_per_frame):
	"""Calculate the minimum number of cabinets and frames required to house the
	given set of boards.
	
	Just simple arithmetic!
	
	Returns
	-------
	(num_cabinets, num_frames)
	"""
	
	num_cabinets = int(ceil(num_boards / float(frames_per_cabinet *
	                                           boards_per_frame)))
	# If more than one cabinet is required, we must be using all the frames in
	# each cabinet
	if num_cabinets > 1:
		return (num_cabinets, frames_per_cabinet)
	
	num_frames = int(ceil(num_boards / float(boards_per_frame)))
	
	return (num_cabinets, num_frames)

