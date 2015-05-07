import pytest

from six import iteritems

from spinner.topology import Direction

from spinner.cabinet import Cabinet

from example_cabinet_params import \
	board_wire_offset_fields, unique, exact, within


@pytest.mark.parametrize("values", [unique, exact, within])
def test_possible(values):
	# Test that all attributes given as arguments get set correctly and that all
	# supplied situations do not get rejected as impossible.
	c = Cabinet(**values)
	for name, value in iteritems(values):
		if name in board_wire_offset_fields:
			assert c.board_wire_offset[board_wire_offset_fields[name]] == value
		else:
			assert hasattr(c, name)
			assert getattr(c, name) == value


@pytest.mark.parametrize("changes",
                         [# Negative values are not acceptible
                          {"board_dimensions": (-1, -1, -1)},
                          {"board_wire_offset_south_west": (-0.5, -0.1, -1.0)},
                          {"board_wire_offset_north_east": (-0.5, -0.2, -1.0)},
                          {"board_wire_offset_east": (-0.5, -0.2, -1.0)},
                          {"board_wire_offset_west": (-0.5, -0.2, -1.0)},
                          {"board_wire_offset_north": (-0.5, -0.2, -1.0)},
                          {"board_wire_offset_south": (-0.5, -0.2, -1.0)},
                          {"inter_board_spacing": -0.5},
                          {"boards_per_frame": -10},
                          {"frame_dimensions": (-16.5, -3.0, -1.0)},
                          {"frame_board_offset": (-1.0, -1.0, -1.0)},
                          {"inter_frame_spacing": -1.0},
                          {"frames_per_cabinet": -2},
                          {"cabinet_dimensions": (-18.5, -9.0, -1.0)},
                          {"cabinet_frame_offset": (-1.0, -1.0, -0.0)},
                          {"inter_cabinet_spacing": -10.0},
                          # Wires should not be placed outside the bounds of a
                          # board
                          {"board_wire_offset_south_west": (1.5, 0.1, 0.0)},
                          {"board_wire_offset_north_east": (0.5, 1.1, 0.0)},
                          {"board_wire_offset_east": (0.5, 0.1, 2.0)},
                          {"board_wire_offset_west": (-0.5, 0.1, 0.0)},
                          {"board_wire_offset_north": (0.5, -0.1, 0.0)},
                          {"board_wire_offset_south": (0.5, 0.1, -0.1)},
                          # Boards should not take more room than available is
                          # in a frame
                          {"board_dimensions": (1.1, 1.0, 1.0)},
                          {"board_dimensions": (1.0, 1.1, 1.0)},
                          {"board_dimensions": (1.0, 1.0, 1.1)},
                          {"inter_board_spacing": 0.501},
                          {"boards_per_frame": 11},
                          {"frame_dimensions": (15.4, 2.0, 2.0)},
                          {"frame_dimensions": (15.5, 1.9, 2.0)},
                          {"frame_dimensions": (15.5, 2.0, 1.9)},
                          {"frame_board_offset": (1.1, 1.0, 1.0)},
                          {"frame_board_offset": (1.0, 1.1, 1.0)},
                          {"frame_board_offset": (1.0, 1.0, 1.1)},
                          # Frames should not take more room than available in a
                          # cabinet
                          {"frame_dimensions": (15.6, 2.0, 2.0)},
                          {"frame_dimensions": (15.5, 2.1, 2.0)},
                          {"frame_dimensions": (15.5, 2.0, 2.1)},
                          {"inter_frame_spacing": 1.1},
                          {"frames_per_cabinet": 3},
                          {"cabinet_dimensions": (16.4, 6.0, 3.0)},
                          {"cabinet_dimensions": (16.5, 5.9, 3.0)},
                          {"cabinet_dimensions": (16.5, 6.0, 2.9)},
                          {"cabinet_frame_offset": (1.1, 1.0, 1.0)},
                          {"cabinet_frame_offset": (1.0, 1.1, 1.0)},
                          {"cabinet_frame_offset": (1.0, 1.0, 1.1)},
                         ])
def test_impossible(changes):
	# All supplied changes are physically impossible and should trigger an
	# exception.
	values = exact.copy()
	values.update(changes)
	with pytest.raises(ValueError):
		Cabinet(**values)


def test_frame_board_offset_opposite():
	c = Cabinet(**exact)
	assert c.frame_board_offset_opposite == c.frame_dimensions


def test_cabinet_frame_offset_opposite():
	c = Cabinet(**exact)
	assert c.cabinet_frame_offset_opposite == c.cabinet_dimensions


@pytest.mark.parametrize("args,pos",
                         [([0], (0.0, 0.0, 0.0)),
                          ([1], (26.5, 0.0, 0.0)),
                          ([0, 0], (1.0, 1.0, 1.0)),
                          ([0, 1], (1.0, 4.0, 1.0)),
                          ([1, 1], (27.5, 4.0, 1.0)),
                          ([0, 0, 0], (2.0, 2.0, 2.0)),
                          ([0, 0, 1], (3.5, 2.0, 2.0)),
                          ([0, 1, 1], (3.5, 5.0, 2.0)),
                          ([0, 0, 0, Direction.north], (2.5, 2.5, 2.5)),
                          ([0, 0, 1, Direction.north], (4.0, 2.5, 2.5)),
                         ])
def test_cabinet_get_position(args, pos):
	c = Cabinet(**exact)
	assert c.get_position(*args) == pos


@pytest.mark.parametrize("args,pos",
                         [([0], (16.5, 6.0, 3.0)),
                          ([1], (43.0, 6.0, 3.0)),
                          ([0, 0], (16.5, 3.0, 3.0)),
                          ([0, 1], (16.5, 6.0, 3.0)),
                          ([1, 1], (43.0, 6.0, 3.0)),
                          ([0, 0, 0], (3.0, 3.0, 3.0)),
                          ([0, 0, 1], (4.5, 3.0, 3.0)),
                          ([0, 1, 1], (4.5, 6.0, 3.0)),
                          ([0, 0, 0, Direction.north], (2.5, 2.5, 2.5)),
                          ([0, 0, 1, Direction.north], (4.0, 2.5, 2.5)),
                         ])
def test_cabinet_get_position_opposite(args, pos):
	c = Cabinet(**exact)
	assert c.get_position_opposite(*args) == pos


@pytest.mark.parametrize(
	"kwargs,dimen",
	[({"cabinets": 1}, (16.5, 6.0, 3.0)),
	 ({"cabinets": 2}, (43.0, 6.0, 3.0)),
	 ({"frames": 1}, (15.5, 2.0, 2.0)),
	 ({"frames": 2}, (15.5, 5.0, 2.0)),
	 ({"boards": 1}, (1.0, 1.0, 1.0)),
	 ({"boards": 2}, (2.5, 1.0, 1.0)),
	])
def test_cabinet_get_dimensions(kwargs, dimen):
	c = Cabinet(**exact)
	assert c.get_dimensions(**kwargs) == dimen
