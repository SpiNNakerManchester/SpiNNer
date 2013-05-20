#!/usr/bin/env python

"""
Unit tests. Not comprehensive but just quick and dirty... Usage:

python tests.py
"""

import unittest

from itertools import product
import fractions

import board

import cabinet

import topology

import coordinates

class TopologyTests(unittest.TestCase):
	"""
	Tests the topology utility functions
	"""
	
	def test_next(self):
		cw  = topology.next_cw
		ccw = topology.next_ccw
		
		# Clockwise
		self.assertEqual(cw(topology.EAST),       topology.SOUTH)
		self.assertEqual(cw(topology.NORTH_EAST), topology.EAST)
		self.assertEqual(cw(topology.NORTH),      topology.NORTH_EAST)
		self.assertEqual(cw(topology.WEST),       topology.NORTH)
		self.assertEqual(cw(topology.SOUTH_WEST), topology.WEST)
		self.assertEqual(cw(topology.SOUTH),      topology.SOUTH_WEST)
		
		# Counter-Clockwise
		self.assertEqual(ccw(topology.EAST),       topology.NORTH_EAST)
		self.assertEqual(ccw(topology.NORTH_EAST), topology.NORTH)
		self.assertEqual(ccw(topology.NORTH),      topology.WEST)
		self.assertEqual(ccw(topology.WEST),       topology.SOUTH_WEST)
		self.assertEqual(ccw(topology.SOUTH_WEST), topology.SOUTH)
		self.assertEqual(ccw(topology.SOUTH),      topology.EAST)
	
	def test_opposite(self):
		opp = topology.opposite
		
		self.assertEqual(opp(topology.EAST),       topology.WEST)
		self.assertEqual(opp(topology.NORTH_EAST), topology.SOUTH_WEST)
		self.assertEqual(opp(topology.NORTH),      topology.SOUTH)
		self.assertEqual(opp(topology.WEST),       topology.EAST)
		self.assertEqual(opp(topology.SOUTH_WEST), topology.NORTH_EAST)
		self.assertEqual(opp(topology.SOUTH),      topology.NORTH)
	
	def test_direction(self):
		ad = topology.add_direction
		
		self.assertEqual(ad((11,11,11), topology.EAST),       (12,11,11))
		self.assertEqual(ad((11,11,11), topology.NORTH_EAST), (11,11,10))
		self.assertEqual(ad((11,11,11), topology.NORTH),      (11,12,11))
		self.assertEqual(ad((11,11,11), topology.WEST),       (10,11,11))
		self.assertEqual(ad((11,11,11), topology.SOUTH_WEST), (11,11,12))
		self.assertEqual(ad((11,11,11), topology.SOUTH),      (11,10,11))
	
	
	def test_manhattan(self):
		self.assertEqual(topology.manhattan([0]),      0)
		self.assertEqual(topology.manhattan([1]),      1)
		self.assertEqual(topology.manhattan([-1]),     1)
		self.assertEqual(topology.manhattan([-1, 0]),  1)
		self.assertEqual(topology.manhattan([-1, -1]), 2)
		self.assertEqual(topology.manhattan([-1,  1]), 2)
	
	
	def test_median_element(self):
		self.assertEqual(topology.median_element([0]), 0)
		self.assertEqual(topology.median_element([0,1,2]), 1)
		self.assertEqual(topology.median_element([2,1,0]), 1)
		self.assertEqual(topology.median_element([1,2,0]), 1)
		self.assertEqual(topology.median_element([2,0,1]), 1)
		self.assertEqual(topology.median_element([2,2,2]), 2)
	
	
	def test_to_shortest_path(self):
		self.assertEqual(topology.to_shortest_path((0,0,0)), (0,0,0))
		self.assertEqual(topology.to_shortest_path((1,1,1)), (0,0,0))
		self.assertEqual(topology.to_shortest_path((0,1,2)), (-1,0,1))
		self.assertEqual(topology.to_shortest_path((-2,0,2)), (-2,0,2))
	
	
	def test_to_xy(self):
		self.assertEqual(topology.to_xy((0,0,0)), (0,0))
		self.assertEqual(topology.to_xy((1,1,1)), (0,0))
		self.assertEqual(topology.to_xy((0,1,2)), (-2,-1))
		self.assertEqual(topology.to_xy((-2,0,2)), (-4,-2))
	
	
	def test_hexagon(self):
		it = topology.hexagon(2)
		
		# Inner layer
		self.assertEqual(it.next(), ( 0, 0))
		self.assertEqual(it.next(), (-1, 0))
		self.assertEqual(it.next(), ( 0, 1))
		
		# Outer layer
		self.assertEqual(it.next(), ( 1, 1))
		self.assertEqual(it.next(), ( 1, 0))
		self.assertEqual(it.next(), ( 0,-1))
		self.assertEqual(it.next(), (-1,-1))
		self.assertEqual(it.next(), (-2,-1))
		self.assertEqual(it.next(), (-2, 0))
		self.assertEqual(it.next(), (-1, 1))
		self.assertEqual(it.next(), ( 0, 2))
		self.assertEqual(it.next(), ( 1, 2))
		
		# Stop now
		self.assertRaises(StopIteration, it.next)
	
	
	def test_threeboards(self):
		# Creating no threeboards makes no boards...
		self.assertEqual(list(topology.threeboards(0)), [])
		
		# Creating 2x2 threeboards (throw away the boards...)
		boards = [topology.to_xy(c) for c in topology.threeboards(2)]
		self.assertEqual(len(boards), 3*2*2)
		# Threeboard (0,0)
		self.assertTrue((0,0) in boards)
		self.assertTrue((0,1) in boards)
		self.assertTrue((1,1) in boards)
		# Threeboard (1,0)
		self.assertTrue((2,1) in boards)
		self.assertTrue((2,2) in boards)
		self.assertTrue((3,2) in boards)
		# Threeboard (0,1)
		self.assertTrue((-1,1) in boards)
		self.assertTrue((-1,2) in boards)
		self.assertTrue((0,2) in boards)
		# Threeboard (1,1)
		self.assertTrue((1,2) in boards)
		self.assertTrue((1,3) in boards)
		self.assertTrue((2,3) in boards)
	
	
	def test_wrap_around(self):
		# Exhaustively test single threeboard case
		# Stays in board
		self.assertEqual(topology.wrap_around((0,0,0), (1,1)), (0,0,0))
		self.assertEqual(topology.wrap_around((0,1,0), (1,1)), (0,1,0))
		self.assertEqual(topology.wrap_around((1,1,0), (1,1)), (1,1,0))
		
		# Off the top-left of (0,0)
		self.assertEqual(topology.wrap_around((-1,0,0), (1,1)), (1,1,0))
		# Off the bottom-left of (0,0)
		self.assertEqual(topology.wrap_around((-1,-1,0), (1,1)), (0,1,0))
		# Off the bottom-right of (0,0)
		self.assertEqual(topology.wrap_around((1,0,0), (1,1)), (0,1,0))
		# Off the bottom of (0,0)
		self.assertEqual(topology.wrap_around((0,-1,0), (1,1)), (1,1,0))
		
		# Off the bottom-left of (0,1)
		self.assertEqual(topology.wrap_around((-1,0,0), (1,1)), (1,1,0))
		# Off the top-left of (0,1)
		self.assertEqual(topology.wrap_around((-1,1,0), (1,1)), (0,0,0))
		# Off the top of (0,1)
		self.assertEqual(topology.wrap_around((0,2,0), (1,1)), (1,1,0))
		# Off the top-right of (0,1)
		self.assertEqual(topology.wrap_around((0,-1,0), (1,1)), (1,1,0))
		
		# Off the top of (1,1)
		self.assertEqual(topology.wrap_around((1,2,0), (1,1)), (0,0,0))
		# Off the top-right of (1,1)
		self.assertEqual(topology.wrap_around((2,2,0), (1,1)), (0,1,0))
		# Off the bottom-right of (1,1)
		self.assertEqual(topology.wrap_around((2,1,0), (1,1)), (0,0,0))
		# Off the bottom of (1,1)
		self.assertEqual(topology.wrap_around((1,0,0), (1,1)), (0,1,0))
		
		# Try some random examples for a larger system
		self.assertEqual(topology.wrap_around((-3,5,0), (4,4)), (1,1,0))
		self.assertEqual(topology.wrap_around((8,4,0), (4,4)), (0,0,0))
		self.assertEqual(topology.wrap_around((0,-1,0), (4,4)), (4,7,0))
		self.assertEqual(topology.wrap_around((4,8,0), (4,4)), (0,0,0))
		
		# And now non-equally sized systems
		self.assertEqual(topology.wrap_around((0,-1,0), (4,3)), (5,6,0))
		self.assertEqual(topology.wrap_around((5,7,0), (4,3)), (0,0,0))
		
		# Multi-world-sized steps
		self.assertEqual(topology.wrap_around((4,5,0), (1,1)), (0,0,0))
		self.assertEqual(topology.wrap_around((-2,2,0), (1,1)), (0,0,0))
	
	
	def test_hex_to_cartesian(self):
		# Test single element cases
		self.assertEqual(topology.hex_to_cartesian((0,0,0)), (0,0))
		self.assertEqual(topology.hex_to_cartesian((0,1,0)), (0,2))
		self.assertEqual(topology.hex_to_cartesian((1,1,0)), (1,1))
	
	
	def test_hex_to_skew_cartesian(self):
		# Test single element cases
		self.assertEqual(topology.hex_to_skew_cartesian((0,0,0)), (0,0))
		self.assertEqual(topology.hex_to_skew_cartesian((0,1,0)), (1,2))
		self.assertEqual(topology.hex_to_skew_cartesian((1,1,0)), (2,1))
	
	
	def test_fold_dimension(self):
		# No folding
		self.assertEqual(topology.fold_dimension(0, 4, 1), (0,0))
		self.assertEqual(topology.fold_dimension(1, 4, 1), (1,0))
		self.assertEqual(topology.fold_dimension(2, 4, 1), (2,0))
		self.assertEqual(topology.fold_dimension(3, 4, 1), (3,0))
		
		# Single fold (into two sides)
		# Folds for things on the first side
		self.assertEqual(topology.fold_dimension(0, 4, 2), (0,0))
		self.assertEqual(topology.fold_dimension(1, 4, 2), (1,0))
		# Folds on the inside
		self.assertEqual(topology.fold_dimension(2, 4, 2), (1,1))
		self.assertEqual(topology.fold_dimension(3, 4, 2), (0,1))
		
		# Odd number of folds (into three pieces)
		self.assertEqual(topology.fold_dimension(0, 9, 3), (0,0))
		self.assertEqual(topology.fold_dimension(1, 9, 3), (1,0))
		self.assertEqual(topology.fold_dimension(2, 9, 3), (2,0))
		
		self.assertEqual(topology.fold_dimension(3, 9, 3), (2,1))
		self.assertEqual(topology.fold_dimension(4, 9, 3), (1,1))
		self.assertEqual(topology.fold_dimension(5, 9, 3), (0,1))
		
		self.assertEqual(topology.fold_dimension(6, 9, 3), (0,2))
		self.assertEqual(topology.fold_dimension(7, 9, 3), (1,2))
		self.assertEqual(topology.fold_dimension(8, 9, 3), (2,2))
		
		
		# Folded twice (into four sides)
		# Front
		self.assertEqual(topology.fold_dimension(0, 12, 4), (0,0))
		self.assertEqual(topology.fold_dimension(1, 12, 4), (1,0))
		self.assertEqual(topology.fold_dimension(2, 12, 4), (2,0))
		# Mid Front
		self.assertEqual(topology.fold_dimension(3, 12, 4), (2,1))
		self.assertEqual(topology.fold_dimension(4, 12, 4), (1,1))
		self.assertEqual(topology.fold_dimension(5, 12, 4), (0,1))
		# Mid Back
		self.assertEqual(topology.fold_dimension(6, 12, 4), (0,2))
		self.assertEqual(topology.fold_dimension(7, 12, 4), (1,2))
		self.assertEqual(topology.fold_dimension(8, 12, 4), (2,2))
		# Back
		self.assertEqual(topology.fold_dimension(9, 12, 4), (2,3))
		self.assertEqual(topology.fold_dimension(10, 12, 4), (1,3))
		self.assertEqual(topology.fold_dimension(11, 12, 4), (0,3))
	
	
	def test_fold_interleave_dimension(self):
		# No folds
		self.assertEqual(topology.fold_interleave_dimension(0, 4, 1), 0)
		self.assertEqual(topology.fold_interleave_dimension(1, 4, 1), 1)
		self.assertEqual(topology.fold_interleave_dimension(2, 4, 1), 2)
		self.assertEqual(topology.fold_interleave_dimension(3, 4, 1), 3)
		
		# Two sides (one fold)
		self.assertEqual(topology.fold_interleave_dimension(0, 4, 2), 0)
		self.assertEqual(topology.fold_interleave_dimension(3, 4, 2), 1)
		self.assertEqual(topology.fold_interleave_dimension(1, 4, 2), 2)
		self.assertEqual(topology.fold_interleave_dimension(2, 4, 2), 3)
		
		# Odd number of sides
		self.assertEqual(topology.fold_interleave_dimension(0, 9, 3), 0)
		self.assertEqual(topology.fold_interleave_dimension(5, 9, 3), 1)
		self.assertEqual(topology.fold_interleave_dimension(6, 9, 3), 2)
		self.assertEqual(topology.fold_interleave_dimension(1, 9, 3), 3)
		self.assertEqual(topology.fold_interleave_dimension(4, 9, 3), 4)
		self.assertEqual(topology.fold_interleave_dimension(7, 9, 3), 5)
		self.assertEqual(topology.fold_interleave_dimension(2, 9, 3), 6)
		self.assertEqual(topology.fold_interleave_dimension(3, 9, 3), 7)
		self.assertEqual(topology.fold_interleave_dimension(8, 9, 3), 8)
		
		# Four sides (2 folds)
		self.assertEqual(topology.fold_interleave_dimension(0, 12, 4), 0)
		self.assertEqual(topology.fold_interleave_dimension(5, 12, 4), 1)
		self.assertEqual(topology.fold_interleave_dimension(6, 12, 4), 2)
		self.assertEqual(topology.fold_interleave_dimension(11, 12, 4), 3)
		self.assertEqual(topology.fold_interleave_dimension(1, 12, 4), 4)
		self.assertEqual(topology.fold_interleave_dimension(4, 12, 4), 5)
		self.assertEqual(topology.fold_interleave_dimension(7, 12, 4), 6)
		self.assertEqual(topology.fold_interleave_dimension(10, 12, 4), 7)
		self.assertEqual(topology.fold_interleave_dimension(2, 12, 4), 8)
		self.assertEqual(topology.fold_interleave_dimension(3, 12, 4), 9)
		self.assertEqual(topology.fold_interleave_dimension(8, 12, 4), 10)
		self.assertEqual(topology.fold_interleave_dimension(9, 12, 4), 11)
	
	
	def test_cabinetise(self):
		# Test a 4x4 system exhaustively
		#                          +---+---+  +---+---+
		# +---+---+---+---+        |0,3|1,3|  |2,3|3,3|
		# |0,3|1,3|2,3|3,3|        +---+---+  +---+---+        +-------------+ +-------------+
		# +---+---+---+---+        |0,2|1,2|  |2,2|3,2|        |+-----------+| |+-----------+|
		# |0,2|1,2|2,2|3,2|  ---\  +---+---+  +---+---+  ---\  ||02:03:12:13|| ||22:23:32:33||
		# +---+---+---+---+  ---/                        ---/  |+-----------+| |+-----------+|
		# |0,1|1,1|2,1|3,1|        +---+---+  +---+---+        ||00:01:10:11:| ||20:21:30:31||
		# +---+---+---+---+        |0,1|1,1|  |2,1|3,1|        |+-----------+| |+-----------+|
		# |0,0|1,0|2,0|3,0|        +---+---+  +---+---+        +-------------+ +-------------+
		# +---+---+---+---+        |0,0|1,0|  |2,0|3,0|
		#                          +---+---+  +---+---+
		
		self.assertEqual(topology.cabinetise((0,0), (4,4), 2, 2, 4), (0,0,0))
		self.assertEqual(topology.cabinetise((0,1), (4,4), 2, 2, 4), (0,0,1))
		self.assertEqual(topology.cabinetise((1,0), (4,4), 2, 2, 4), (0,0,2))
		self.assertEqual(topology.cabinetise((1,1), (4,4), 2, 2, 4), (0,0,3))
		
		self.assertEqual(topology.cabinetise((0,2), (4,4), 2, 2, 4), (0,1,0))
		self.assertEqual(topology.cabinetise((0,3), (4,4), 2, 2, 4), (0,1,1))
		self.assertEqual(topology.cabinetise((1,2), (4,4), 2, 2, 4), (0,1,2))
		self.assertEqual(topology.cabinetise((1,3), (4,4), 2, 2, 4), (0,1,3))
		
		self.assertEqual(topology.cabinetise((2,0), (4,4), 2, 2, 4), (1,0,0))
		self.assertEqual(topology.cabinetise((2,1), (4,4), 2, 2, 4), (1,0,1))
		self.assertEqual(topology.cabinetise((3,0), (4,4), 2, 2, 4), (1,0,2))
		self.assertEqual(topology.cabinetise((3,1), (4,4), 2, 2, 4), (1,0,3))
		
		self.assertEqual(topology.cabinetise((2,2), (4,4), 2, 2, 4), (1,1,0))
		self.assertEqual(topology.cabinetise((2,3), (4,4), 2, 2, 4), (1,1,1))
		self.assertEqual(topology.cabinetise((3,2), (4,4), 2, 2, 4), (1,1,2))
		self.assertEqual(topology.cabinetise((3,3), (4,4), 2, 2, 4), (1,1,3))


class BoardTests(unittest.TestCase):
	"""
	Tests the board model's wiring.
	"""
	
	TEST_CASES = [ (1,1), (2,2), (3,3), (4,4), # Square: odd & even
	               (3,5), (5,3), # Rectangular: odd/odd
	               (2,4), (4,2), # Rectangular: even/even
	               (3,4), (4,3), # Rectangular: odd/even
	               (1,4), (4,1), # 1-dimension: even
	               (1,3), (3,1), # 1-dimension: odd
	               (20,20) # Full size (106 machine)
	             ]
	
	def lcm(self, a,b):
		"""
		Least common multiple
		"""
		return abs(a * b) / fractions.gcd(a,b) if a and b else 0
	
	
	def follow_packet_loop(self, start_board, in_wire_side, direction):
		"""
		Follows the path of a packet entering on in_wire_side of start_board
		travelling in the direction given.
		
		Generates a sequence of (in_wire_side, board) tuples that were traversed.
		"""
		yield(in_wire_side, start_board)
		in_wire_side, cur_board = start_board.follow_packet(in_wire_side, direction)
		while cur_board != start_board:
			yield(in_wire_side, cur_board)
			in_wire_side, cur_board = cur_board.follow_packet(in_wire_side, direction)
	
	
	def test_threeboard_packets(self):
		# Exhaustively check that packets travelling in each direction take the
		# correct number of hops to wrap back according to Simon Davidson's model.
		for testcase in BoardTests.TEST_CASES:
			w, h = testcase
			boards = board.create_torus(w, h)
			
			# Try starting from every board
			for start_board, start_coord in boards:
				# Try going in every possible direction
				for direction in [ topology.EAST
				                 , topology.NORTH_EAST
				                 , topology.NORTH
				                 , topology.WEST
				                 , topology.SOUTH_WEST
				                 , topology.SOUTH
				                 ]:
					# Packets can enter when travelling in direction from the side with the
					# opposite label and one counter-clockwise from that.
					for entry_point in [topology.opposite(direction)
					                   , topology.next_ccw(topology.opposite(direction))
					                   ]:
						num_boards = len(list(self.follow_packet_loop(start_board, entry_point, direction)))
						# For every threeboard traversed, the number of chips traversed is 3*l
						# where l is the number of rings in the hexagon. Travelling in one
						# direction we pass through a threeboard every two boards traversed so
						# the number of nodes traversed is num_nodes*l where num_hops is given
						# as below.
						num_nodes = (num_boards/2) * 3
						
						# The principal axis is south to north, i.e. along the height in
						# threeboards. This should have 3*l*h nodes along its length.
						if direction in (topology.NORTH, topology.SOUTH):
							self.assertEqual(num_nodes, h*3)
						
						# The major axis is east to west, i.e. along the width in
						# threeboards. This should have 3*l*w nodes along its length.
						if direction in (topology.EAST, topology.WEST):
							self.assertEqual(num_nodes, w*3)
						
						# The minor axis is norht-east to south-west, i.e. diagonally across
						# the mesh of threeboards. This should have 3*l*lcm(w,h) nodes along
						# its length.
						if direction in (topology.NORTH_EAST, topology.SOUTH_WEST):
							self.assertEqual(num_nodes, self.lcm(w,h)*3)



class CabinetTests(unittest.TestCase):
	"""
	Tests for the cabinet dimension definitions
	"""
	
	def test_slot(self):
		# Test the slot model
		s = cabinet.Slot((10,20,30), {
			topology.NORTH : (1,2,3),
			topology.SOUTH : (-1,-2,-3),
		})
		
		# Check the various dimensions
		self.assertEqual(s.width,  10)
		self.assertEqual(s.height, 20)
		self.assertEqual(s.depth,  30)
		
		# Check accessing defined wire offsets
		self.assertEqual(s.get_position(topology.NORTH), (1,2,3))
		self.assertEqual(s.get_position(topology.SOUTH), (-1,-2,-3))
		
		# Check accessing undefined wire offsets
		self.assertEqual(s.get_position(topology.EAST), (0,0,0))
	
	
	def test_rack(self):
		# Test the rack model
		# Slot with the north port slightly offset on the z axis
		s = cabinet.Slot((1,10,10), {topology.NORTH : (0.0,0.0,1.0)})
		# A rack with 10 slots. The bay should be centered with offset (2.75, 2.5, 0)
		r = cabinet.Rack(s, (20,15,15), 10, 0.5)
		
		# Check the various dimensions
		self.assertEqual(r.width,  20)
		self.assertEqual(r.height, 15)
		self.assertEqual(r.depth,  15)
		
		# Check accessing wires
		self.assertEqual(r.get_position(0), (2.75,2.5,0.0))
		self.assertEqual(r.get_position(1), (4.25,2.5,0.0))
		
		# Check accessing a particular link
		self.assertEqual(r.get_position(2, topology.NORTH), (5.75,2.5,1.0))
	
	
	def test_cabinet(self):
		# Test the cabinet model
		# Slot with the north port slightly offset on the z axis
		s = cabinet.Slot((1,10,10), {topology.NORTH : (0.0,0.0,1.0)})
		# A rack with 10 slots. The bay should be centered with offset (2.75, 2.5, 0)
		r = cabinet.Rack(s, (20,15,15), 10, 0.5)
		# A cabinet with 10 racks. The bay should have offset (1,1,1)
		c = cabinet.Cabinet(r, (25, 120, 20), 5, 5.0, (1,1,1))
		
		# Check the various dimensions
		self.assertEqual(c.width,  25)
		self.assertEqual(c.height, 120)
		self.assertEqual(c.depth,  20)
		
		# Check accessing racks via the cabinet...
		self.assertEqual(c.get_position(0, 0), (3.75,3.5,1.0))
		self.assertEqual(c.get_position(0, 1), (5.25,3.5,1.0))
		
		# Access a subsequent rack
		self.assertEqual(c.get_position(1, 0), (3.75,23.5,1.0))
		
		
		# Check accessing a particular link
		self.assertEqual(c.get_position(0, 2, topology.NORTH), (6.75,3.5,2.0))
	
	
	def test_system(self):
		# Test the system of cabinets model
		# Slot with the north port slightly offset on the z axis
		s = cabinet.Slot((1,10,10), {topology.NORTH : (0.0,0.0,1.0)})
		# A rack with 10 slots. The bay should be centered with offset (2.75, 2.5, 0)
		r = cabinet.Rack(s, (20,15,15), 10, 0.5)
		# A cabinet with 10 racks. The bay should have offset (1,1,1)
		c = cabinet.Cabinet(r, (25, 120, 20), 5, 5.0, (1,1,1))
		# A system of 10 cabinets.
		sys = cabinet.System(c, 10, 100)
		
		# Check accessing racks via the cabinet via the system...
		self.assertEqual(sys.get_position((0,0,0)), (3.75,3.5,1.0))
		self.assertEqual(sys.get_position((0,0,1)), (5.25,3.5,1.0))
		
		# Access a subsequent rack
		self.assertEqual(sys.get_position((0,1,0)), (3.75,23.5,1.0))
		
		# Access a subsequent cabinet
		self.assertEqual(sys.get_position((1,1,0)), (128.75,23.5,1.0))
		
		# Check accessing a particular link
		self.assertEqual(sys.get_position((0,0,2), topology.NORTH), (6.75,3.5,2.0))


if __name__=="__main__":
	unittest.main()
