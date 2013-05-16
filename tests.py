#!/usr/bin/env python

"""
Unit tests. Not comprehensive but just quick and dirty... Usage:

python tests.py
"""

import unittest

from itertools import product
import fractions

import model

import topology

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
	
	
	def test_get_path(self):
		gp = topology.get_path
		# Simple case (just a delta and to_shortest_path
		self.assertEqual(gp((0,0,0), (0,0,0)),   (0,0,0))
		self.assertEqual(gp((0,0,0), (1,1,0)),   (0,0,-1))
		self.assertEqual(gp((5,5,0), (10,10,0)), (0,0,-5))
		
		# In a repeating 12-12 mesh.
		# Simple cases: just go straight there
		self.assertEqual(gp((0,0,0), (0,0,0),   (12,12)), (0,0,0))
		self.assertEqual(gp((0,0,0), (1,1,0),   (12,12)), (0,0,-1))
		self.assertEqual(gp((5,5,0), (10,10,0), (12,12)), (0,0,-5))
		
		# Have to wrap around the edges for shortest path
		self.assertEqual(gp((0,0,0), (11,0,0),  (12,12)), (-1,0,0))
		self.assertEqual(gp((0,0,0), (0,11,0),  (12,12)), (0,-1,0))
		self.assertEqual(gp((0,0,0), (11,11,0), (12,12)), (0,0,1))
	
	
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
	
	def test_hexagon_edge_link(self):
		# Get the set of edge nodes for a 4-layer hexagon
		all_nodes   = set(topology.hexagon(4))
		inner_nodes = set(topology.hexagon(3))
		outer_nodes = all_nodes - inner_nodes
		
		directions = [
			topology.EAST,
			topology.NORTH_EAST,
			topology.NORTH,
			topology.WEST,
			topology.SOUTH_WEST,
			topology.SOUTH
		]
		
		edges = [
			topology.EDGE_TOP_LEFT,
			topology.EDGE_TOP,
			topology.EDGE_TOP_RIGHT,
			topology.EDGE_BOTTOM_RIGHT,
			topology.EDGE_BOTTOM,
		  topology.EDGE_BOTTOM_LEFT,
		]
		
		# Get the set of outward-facing links as (node_xy,direction) pairs
		outward_facing_links = []
		for node in all_nodes:
			for direction in directions:
				# Get the node that this link would connect to
				facing_node = topology.to_xy(
					topology.add_direction(topology.zero_pad(node), direction))
				# If that node isn't part of our set, it is an edge link
				if facing_node not in all_nodes:
					outward_facing_links.append((node, direction))
		
		# Get the set of outward facing links according to the function under test
		all_links = []
		for edge in edges:
			for num in range(8):
				all_links.append(topology.hexagon_edge_link(edge, num, 4))
		
		# No duplicates
		self.assertEqual(len(all_links), len(set(all_links)))
		
		# The algorithm gets every outward facing edge
		self.assertEqual(set(all_links), set(outward_facing_links))
	
	
	def test_threeboards(self):
		# Creating no threeboards makes no boards...
		self.assertEqual(list(topology.threeboards(0)), [])
		
		# Creating 2x2 threeboards (throw away the boards...)
		boards = list(topology.threeboards(2))
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
	
	
	def test_boardxyz_to_cartesian(self):
		# Test single element cases
		self.assertEqual(topology.hex_to_cartesian((0,0,0)), (0,0))
		self.assertEqual(topology.hex_to_cartesian((1,0,0)), (1,0))
		self.assertEqual(topology.hex_to_cartesian((10,0,0)), (10,-5))
		self.assertEqual(topology.hex_to_cartesian((0,10,0)), (0,10))


class ModelTests(unittest.TestCase):
	"""
	Tests the model functions
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
	
	
	def test_threeboard_packets(self):
		# Exhaustively check that packets travelling in each direction take the
		# correct number of hops to wrap back according to Simon Davidson's model.
		for testcase in ModelTests.TEST_CASES:
			w, h = testcase
			boards = model.create_threeboards(w, h)
			
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
						num_boards = len(list(model.follow_packet_loop(start_board, entry_point, direction)))
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
	


if __name__=="__main__":
	unittest.main()
