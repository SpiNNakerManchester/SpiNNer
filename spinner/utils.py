"""Utility functions for generating wiring plans."""

from spinner import board
from spinner import topology
from spinner import coordinates
from spinner import transforms


def torus_without_long_wires(w, h):
	"""Generate a 2D arrangement of boards in a (w, h) triad torus with short
	wires.
	
	This process follows the guidelines set out in "Bringing the Hexagonal Torus
	Topology into the Real-World" by Heathcote et. al. (unpublished at the time of
	writing...).
	
	Parameters
	----------
	w : int
		Width of the system in triads
	h : int
		Width of the system in triads
	
	
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
	
	# It is best to slice the system when the topology is twice as tall as it is
	# wide, otherwise it is best to shear the topology.
	should_slice = h == 2 * w
	
	if should_slice:
		cart_boards = transforms.rhombus_to_rect(
			transforms.compress(
				transforms.hex_to_cartesian(
					hex_boards),
				x_div=1, y_div=2))
	else:
		# Should shear
		cart_boards = transforms.compress(
				transforms.hex_to_skewed_cartesian(
					hex_boards),
				x_div=1, y_div=3)
	
	# Fold and interleave 2x2
	folded_boards = transforms.fold(cart_boards, (2, 2))
	
	return (hex_boards, folded_boards)
