import pytest

from six import iteritems

from example_cabinet_params import real

from spinner import plan
from spinner import board
from spinner import topology
from spinner import transforms
from spinner import utils
from spinner import coordinates
from spinner import cabinet
from spinner import metrics

from spinner.topology import Direction


def test_enumerate_wires():
	# Special case: empty
	assert plan.enumerate_wires([]) == []
	
	# Test exhaustively with a triad
	boards = board.create_torus()
	c2b = {topology.to_xy(c): b for b,c in boards}
	wires = plan.enumerate_wires(boards)
	assert len(wires) == 3 * 3
	assert set(wires) == set([
		# From (0, 0)
		((c2b[(0,0)], Direction.north), (c2b[(0,1)], Direction.south)),
		((c2b[(0,0)], Direction.east), (c2b[(0,1)], Direction.west)),
		((c2b[(0,0)], Direction.south_west), (c2b[(0,1)], Direction.north_east)),
		# From (0, 1)
		((c2b[(0,1)], Direction.north), (c2b[(1,1)], Direction.south)),
		((c2b[(0,1)], Direction.east), (c2b[(1,1)], Direction.west)),
		((c2b[(0,1)], Direction.south_west), (c2b[(1,1)], Direction.north_east)),
		# From (1, 1)
		((c2b[(1,1)], Direction.north), (c2b[(0,0)], Direction.south)),
		((c2b[(1,1)], Direction.east), (c2b[(0,0)], Direction.west)),
		((c2b[(1,1)], Direction.south_west), (c2b[(0,0)], Direction.north_east)),
	])


def test_partition_wires():
	# Verify the correctness with a two-cabinet system.
	hex_boards, folded_boards = utils.folded_torus(10, 8, "shear", "rows", (2,2))
	cabinetised_boards = transforms.cabinetise(folded_boards, 2, 5, 24)
	all_wires = plan.enumerate_wires(cabinetised_boards)
	
	between_boards, between_frames, between_cabinets =\
		plan.partition_wires(all_wires, cabinetised_boards)
	
	# Should have the correct set of categories
	assert len(between_boards) == 5 * 2
	assert len(between_frames) == 2
	
	seen_wires = set()
	b2c = dict(cabinetised_boards)
	
	for (cabinet, frame), wires in iteritems(between_boards):
		assert 0 <= cabinet < 2
		assert 0 <= frame < 5
		for ((src_board, src_direction), (dst_board, dst_direction)) in wires:
			# Check it really does stay in the same frame
			sc, sf, sb = b2c[src_board]
			dc, df, db = b2c[dst_board]
			assert sc == cabinet
			assert dc == cabinet
			assert sf == frame
			assert df == frame
			assert (sc, sf) == (dc, df)
			assert src_direction.opposite == dst_direction
			
			# Check we've not seen it before
			wire = ((src_board, src_direction), (dst_board, dst_direction))
			assert wire not in seen_wires
			seen_wires.add(wire)
	
	for cabinet, wires in iteritems(between_frames):
		assert 0 <= cabinet < 2
		for ((src_board, src_direction), (dst_board, dst_direction)) in wires:
			# Check it really does stay in the same cabinet
			sc, sf, sb = b2c[src_board]
			dc, df, db = b2c[dst_board]
			assert sc == cabinet
			assert dc == cabinet
			assert sc == dc
			assert sf != df
			assert src_direction.opposite == dst_direction
			
			# Check we've not seen it before
			wire = ((src_board, src_direction), (dst_board, dst_direction))
			assert wire not in seen_wires
			seen_wires.add(wire)
	
	from pprint import pprint
	for ((src_board, src_direction), (dst_board, dst_direction)) in between_cabinets:
		# Check it really doesn't stay within a cabinet
		sc, sf, sb = b2c[src_board]
		dc, df, db = b2c[dst_board]
		assert sc != dc
		assert src_direction.opposite == dst_direction
		
		# Check we've not seen it before
		wire = ((src_board, src_direction), (dst_board, dst_direction))
		assert wire not in seen_wires
		seen_wires.add(wire)
	
	# Should have seen all wires too!
	assert seen_wires == set(all_wires)


def test_assign_wires():
	# Simply check the appropriateness of each point provided in an example system.
	hex_boards, folded_boards = utils.folded_torus(4, 2, "shear", "rows", (2,2))
	cabinetised_boards = transforms.cabinetise(folded_boards, 1, 1, 24)
	wires = plan.enumerate_wires(cabinetised_boards)
	
	# Map each board to a point along a line.
	physical_boards = [(board, coordinates.Cartesian3D(float(b), 0.0, 0.0))
	                   for board, (c, f, b) in cabinetised_boards]
	b2c = dict(physical_boards)
	
	# Given in no particular order
	available_wire_lengths = [8.0, 3.0, 24.0]
	
	board_wire_offset = {
		Direction.north: coordinates.Cartesian3D(0.0, 0.0, 0.0),
		Direction.south: coordinates.Cartesian3D(1.0, 0.0, 0.0),
		Direction.east: coordinates.Cartesian3D(0.0, 1.0, 0.0),
		Direction.west: coordinates.Cartesian3D(0.0, 0.0, 1.0),
		Direction.north_east: coordinates.Cartesian3D(1.0, 1.0, 1.0),
		Direction.south_west: coordinates.Cartesian3D(-1.0, -1.0, -1.0),
	}
	
	last_wire = None
	last_arc_height = None
	for src, dst, wire in plan.assign_wires(wires, physical_boards,
	                                        board_wire_offset,
	                                        available_wire_lengths, 0.0):
		# Check the wire was chosen correctly
		distance = ((b2c[src[0]] + board_wire_offset[src[1]]) -
		            (b2c[dst[0]] + board_wire_offset[dst[1]])).magnitude()
		shortest_possible_wire, arc_height = metrics.physical_wire_length(
			distance, available_wire_lengths, 0.0)
		assert wire == shortest_possible_wire
		
		# Make sure wires are given in ascending order of arc height unless the
		# wire length changes
		if last_wire == wire and last_arc_height is not None:
			assert arc_height >= last_arc_height
		last_arc_height = arc_height
		
		last_wire = wire


def test_generate_wiring_plan():
	# Since generate_wiring_plan is largely a wrapper around the functions tested
	# above, this simply tests that the output is not insane...
	hex_boards, folded_boards = utils.folded_torus(10, 8, "shear", "rows", (2,2))
	cabinetised_boards = transforms.cabinetise(folded_boards, 2, 5, 24)
	cab = cabinet.Cabinet(**real)
	physical_boards = transforms.cabinet_to_physical(cabinetised_boards, cab)
	all_wires = plan.enumerate_wires(cabinetised_boards)
	available_wire_lengths = [0.3, 0.5, 1.0]
	
	b2c = dict(cabinetised_boards)
	
	between_boards, between_frames, between_cabinets =\
		plan.generate_wiring_plan(cabinetised_boards, physical_boards,
		                          cab.board_wire_offset,
		                          available_wire_lengths,
		                          0.0)
	
	seen_wires = set()
	
	assert set(between_boards) == set((c, f, d)
	                                  for c in range(cab.num_cabinets)
	                                  for f in range(cab.frames_per_cabinet)
	                                  for d in [Direction.north,
	                                            Direction.south_west,
	                                            Direction.east])
	for (cabinet_num, frame_num, direction), wires in iteritems(between_boards):
		for ((src_board, src_direction), (dst_board, dst_direction),
		     wire_length) in wires:
			# The board does stay in the frame_num and goes in the specified direction
			c, f, b = b2c[src_board]
			assert c == cabinet_num
			assert f == frame_num
			assert src_direction == direction
			
			c, f, b = b2c[dst_board]
			assert c == cabinet_num
			assert f == frame_num
			assert dst_direction == direction.opposite
			
			# The wire length chosen should exist
			assert wire_length in available_wire_lengths
			
			# Check we've not seen it before
			wire = ((src_board, src_direction), (dst_board, dst_direction))
			assert wire not in seen_wires
			seen_wires.add(wire)
	
	assert set(between_frames) == set((c, d)
	                                  for c in range(cab.num_cabinets)
	                                  for d in [Direction.north,
	                                            Direction.south_west,
	                                            Direction.east])
	for (cabinet_num, direction), wires in iteritems(between_frames):
		for ((src_board, src_direction), (dst_board, dst_direction),
		     wire_length) in wires:
			# The board does stay in the cabinet and goes in the specified direction
			c, f, b = b2c[src_board]
			assert c == cabinet_num
			assert src_direction == direction
			
			c, f, b = b2c[dst_board]
			assert c == cabinet_num
			assert dst_direction == direction.opposite
			
			assert wire_length in available_wire_lengths
			
			# Check we've not seen it before
			wire = ((src_board, src_direction), (dst_board, dst_direction))
			assert wire not in seen_wires
			seen_wires.add(wire)
	
	assert set(between_cabinets) == set([Direction.north,
	                                     Direction.south_west,
	                                     Direction.east])
	for direction, wires in iteritems(between_cabinets):
		for ((src_board, src_direction), (dst_board, dst_direction),
		     wire_length) in wires:
			# The board does stay in the cabinet and goes in the specified direction
			assert src_direction == direction
			assert dst_direction == direction.opposite
			
			assert wire_length in available_wire_lengths
			
			# Check we've not seen it before
			wire = ((src_board, src_direction), (dst_board, dst_direction))
			assert wire not in seen_wires
			seen_wires.add(wire)
	
	# All wires should have been seen
	assert seen_wires == set(all_wires)


def test_flatten_wiring_plan():
	# Provide an artificial input to this function with a known correct sorting.
	# In the input, the board object is replaced with an integer indicating its
	# correct position in the ordering.
	
	cab = cabinet.Cabinet(**real)
	direction_order = sorted([Direction.north, Direction.east, Direction.south_west],
	                         key=(lambda d: cab.board_wire_offset[d].y))
	
	num = [0]
	def gen_wire(d_num):
		num[0] += 1
		return ((num[0], direction_order[d_num]),
		        (-num[0], direction_order[d_num].opposite),
		        1.0)
	
	wires_between_boards = {
		(c, f, direction_order[d_num]) : [gen_wire(d_num) for _ in range(5)]
		for c in range(2)
		for f in range(5)
		for d_num in range(3)
	}
	
	wires_between_frames = {
		(c, direction_order[d_num]) : [gen_wire(d_num) for _ in range(5)]
		for c in range(2)
		for d_num in range(3)
	}
	
	wires_between_cabinets = {
		direction_order[d_num] : [gen_wire(d_num) for _ in range(5)]
		for d_num in range(3)
	}
	
	flat_plan = plan.flatten_wiring_plan(wires_between_boards,
	                                     wires_between_frames,
	                                     wires_between_cabinets,
	                                     cab.board_wire_offset)
	
	# Should have a plan with one instruction per wire
	assert len(flat_plan) == num[0]
	
	# Plan should be in the predicted order
	assert [sb for ((sb, sd), (db, dd), wl) in flat_plan] ==\
		list(range(1, num[0]+1))
