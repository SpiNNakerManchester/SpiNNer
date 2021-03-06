import pytest

from spinner import transforms
from spinner import coordinates
from spinner import cabinet

from example_cabinet_params import exact


def test_hex_to_cartesian():
	h = coordinates.Hexagonal
	c = coordinates.Cartesian2D
	
	# Test single element cases
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	assert transforms.hex_to_cartesian(
		[(o0, h(0,0,0)), (o1, h(0,1,0)), (o2, h(1,1,0))]) == \
		[(o0, c(0,0)), (o1, c(0,2)), (o2, c(1,1))]


def test_hex_to_skew_cartesian():
	h = coordinates.Hexagonal
	c = coordinates.Cartesian2D
	
	# Test single element cases
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	assert transforms.hex_to_skewed_cartesian(
		[(o0, h(0,0,0)), (o1, h(0,1,0)), (o2, h(1,1,0))]) == \
		[(o0, c(0,0)), (o1, c(1,2)), (o2, c(2,1))]


def test_rhombus_to_rect():
	c2 = coordinates.Cartesian2D
	c3 = coordinates.Cartesian3D
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	
	assert transforms.rhombus_to_rect([]) == []
	
	assert transforms.rhombus_to_rect(
		[(o0, c2(-1,0)), (o1, c2(0,0)), (o2, c2(1,1))]) == \
		[(o0, c2(1,0)), (o1, c2(0,0)), (o2, c2(1,1))]
	
	assert transforms.rhombus_to_rect(
		[(o0, c3(-1,-1,-1)), (o1, c3(0,1,1)), (o2, c3(1,1,0))]) == \
		[(o0, c3(1,1,1)), (o1, c3(0,1,1)), (o2, c3(1,1,0))]


def test_compress():
	c = coordinates.Cartesian2D
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	o3 = "o3"
	o4 = "o4"
	o5 = "o5"
	
	assert transforms.compress([(o0, c(0,0)), (o1, c(1,1)), (o2, c(2,0)),
	                            (o3, c(0,2)), (o4, c(1,3)), (o5, c(2,2))]) == \
		[(o0, c(0,0)), (o1, c(1,0)), (o2, c(2,0)),
		 (o3, c(0,1)), (o4, c(1,1)), (o5, c(2,1))]


def test_flip_axes():
	c = coordinates.Cartesian2D
	
	o0 = "o0"
	o1 = "o1"
	
	assert transforms.flip_axes([(o0, c(1,2)), (o1, c(3,4))]) == \
		[(o0, c(2,1)), (o1, c(4,3))]


def test_folds():
	c = coordinates.Cartesian2D
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	o3 = "o3"
	
	assert transforms.fold([], (1,1)) == []
	
	# No folding
	assert transforms.fold(
		[(o0, c(0,0)), (o1, c(1,0)), (o2, c(2,0)), (o3, c(3,0))], (1,1)) == \
		[(o0, c(0,0)), (o1, c(1,0)), (o2, c(2,0)), (o3, c(3,0))]
	
	# Fold on X
	assert transforms.fold(
		[(o0, c(0,0)), (o1, c(1,0)), (o2, c(2,0)), (o3, c(3,0))], (2,1)) == \
		[(o0, c(0,0)), (o1, c(2,0)), (o2, c(3,0)), (o3, c(1,0))]
	
	# Fold on Y
	assert transforms.fold(
		[(o0, c(0,0)), (o1, c(0,1)), (o2, c(0,2)), (o3, c(0,3))], (1,2)) == \
		[(o0, c(0,0)), (o1, c(0,2)), (o2, c(0,3)), (o3, c(0,1))]


def test_cabinetise():
	c = coordinates.Cartesian2D
	s = coordinates.Cabinet
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	o3 = "o3"
	
	assert transforms.cabinetise([], num_cabinets=0, frames_per_cabinet=0) == []
	
	assert transforms.cabinetise(
		[(o0, c(0,0)), (o1, c(1,0)), (o2, c(0,1)), (o3, c(1,1))],
		num_cabinets=2, frames_per_cabinet=2, boards_per_frame=1) == \
		[(o0, s(0,0,0)), (o1, s(1,0,0)), (o2, s(0,1,0)), (o3, s(1,1,0))]


def test_remove_gaps():
	c = coordinates.Cabinet
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	
	# Empty case
	assert transforms.remove_gaps([]) == []
	
	# Singletons (with and without need to move)
	assert transforms.remove_gaps([(o0, c(0,0,0))]) == [(o0, c(0,0,0))]
	assert transforms.remove_gaps([(o0, c(1,2,0))]) == [(o0, c(1,2,0))]
	assert transforms.remove_gaps([(o0, c(1,2,3))]) == [(o0, c(1,2,0))]
	
	# With and without gaps
	assert set(transforms.remove_gaps(
		[(o0, c(0,0,0)), (o1, c(0,0,1))])) ==\
		set([(o0, c(0,0,0)), (o1, c(0,0,1))])
	assert set(transforms.remove_gaps(
		[(o0, c(0,0,0)), (o1, c(0,0,2))])) ==\
		set([(o0, c(0,0,0)), (o1, c(0,0,1))])
	assert set(transforms.remove_gaps(
		[(o0, c(0,0,5)), (o1, c(0,0,2))])) ==\
		set([(o0, c(0,0,1)), (o1, c(0,0,0))])
	
	# Independent frames with restructuring needs
	assert set(transforms.remove_gaps(
		[(o0, c(1,0,5)), (o1, c(0,1,2))])) ==\
		set([(o0, c(1,0,0)), (o1, c(0,1,0))])
	assert set(transforms.remove_gaps(
		[(o0, c(0,0,0)), (o1, c(0,0,3)), (o2, c(1,0,3))])) ==\
		set([(o0, c(0,0,0)), (o1, c(0,0,1)), (o2, c(1,0,0))])


def test_cabinet_to_physical():
	c = cabinet.Cabinet(**exact)
	
	o0 = "o0"
	o1 = "o1"
	o2 = "o2"
	o3 = "o3"
	
	boards = transforms.cabinet_to_physical([(o0, coordinates.Cabinet(0, 0, 0)),
	                                         (o1, coordinates.Cabinet(0, 0, 1)),
	                                         (o2, coordinates.Cabinet(0, 1, 1)),
	                                         (o3, coordinates.Cabinet(1, 1, 1)),
	                                        ], c)
	
	b2c = dict(boards)
	
	# Make sure all boards make it through
	assert len(boards) == len(b2c)
	assert set([o0, o1, o2, o3]) == set(b2c)
	
	# Check all board positions
	assert b2c[o0] == (42.0, 2.0, 2.0)
	assert b2c[o1] == (40.5, 2.0, 2.0)
	assert b2c[o2] == (40.5, 5.0, 2.0)
	assert b2c[o3] == (14.0, 5.0, 2.0)
