import pytest

from mock import Mock

from spinner import utils
from spinner import topology


def test_ideal_system_size():
	# Special case: 0
	assert utils.ideal_system_size(0) == (0, 0)
	
	# Should crash on non-multiples of 3
	with pytest.raises(TypeError):
		utils.ideal_system_size(1)
	with pytest.raises(TypeError):
		utils.ideal_system_size(5)
	
	# Square systems
	assert utils.ideal_system_size(3 * 1 * 1) == (1, 1)
	assert utils.ideal_system_size(3 * 2 * 2) == (2, 2)
	assert utils.ideal_system_size(3 * 20 * 20) == (20, 20)
	
	# Rectangular systems (should always be tall
	assert utils.ideal_system_size(3 * 1 * 2) == (1, 2)
	assert utils.ideal_system_size(3 * 1 * 3) == (1, 3)
	assert utils.ideal_system_size(3 * 2 * 4) == (2, 4)
	assert utils.ideal_system_size(3 * 1 * 17) == (1, 17)


@pytest.fixture
def mock_rhombus_to_rect(monkeypatch):
	from spinner import transforms
	
	m = Mock()
	m.side_effect = transforms.rhombus_to_rect
	
	monkeypatch.setattr(transforms, "rhombus_to_rect", m)
	return m


@pytest.fixture
def mock_fold(monkeypatch):
	from spinner import transforms
	
	m = Mock()
	m.side_effect = transforms.fold
	
	monkeypatch.setattr(transforms, "fold", m)
	return m


@pytest.mark.parametrize("w,h", [(1,1), (7,5), (5,7), (4,8), (8, 4)])
@pytest.mark.parametrize("transformation", ["slice", "shear"])
@pytest.mark.parametrize("uncrinkle_direction", ["rows", "columns"])
@pytest.mark.parametrize("folds", [(1,1), (2,3)])
def test_folded_torus(w, h, transformation, uncrinkle_direction, folds,
                      mock_rhombus_to_rect,
                      mock_fold):
	hex_boards, folded_boards = utils.folded_torus(w, h, transformation,
	                                               uncrinkle_direction, folds)
	
	# Right number of boards produced
	assert len(hex_boards) == len(folded_boards) == 3 * w * h
	
	# Same board should be present in hexagonal layout as in folded layout
	assert set(b for (b, c) in hex_boards) == set(b for (b, c) in folded_boards)
	
	# Positions allocated should be unique
	assert len(set(c for (b, c) in hex_boards)) == len(hex_boards)
	assert len(set(c for (b, c) in folded_boards)) == len(folded_boards)
	
	# Should only use rhombus-to-rect when slicing
	if transformation == "slice":
		assert mock_rhombus_to_rect.called
	else:
		assert not mock_rhombus_to_rect.called
	
	min_x = min(c[0] for (b, c) in folded_boards)
	min_y = min(c[1] for (b, c) in folded_boards)
	
	# Should be based from 0,0
	assert min_x == 0
	assert min_y == 0
	
	max_x = max(c[0] for (b, c) in folded_boards)
	max_y = max(c[1] for (b, c) in folded_boards)
	
	# Should be folded the required number of times
	assert mock_fold.call_args[0][1] == folds
	
	# Folded boards should fit within expected bounds (note that the 'or's here
	# are to allow for folding odd numbers of boards in each dimension).
	if transformation == "slice":
		if uncrinkle_direction == "rows":
			assert max_x == 2*w or max_x + 1 == 2*w
			assert max_y == int(1.5*h) or max_y + 1 == int(1.5 * h)
		else:  # if uncrinkle_direction == "columns":
			assert max_x == w or max_x + 1 == w
			assert max_y == 3 * h or max_y + 1 == 3 * h
	else:  # if transformation == "shear"
		if uncrinkle_direction == "rows":
			assert max_x == 3*w or max_x + 1 == 3*w
			assert max_y == h or max_y + 1 == h
		else:  # if uncrinkle_direction == "columns":
			assert max_x == w or max_x + 1 == w
			assert max_y == 3*h or max_y + 1 == 3*h


def test_folded_torus_bad_args():
	with pytest.raises(TypeError):
		utils.folded_torus(1, 1, "foo", "rows", (1, 1))
	with pytest.raises(TypeError):
		utils.folded_torus(1, 1, "slice", "foo", (1, 1))


def test_min_num_cabinets():
	# Special case: 0 boards
	assert utils.min_num_cabinets(0, 1, 1) == (0, 0)
	assert utils.min_num_cabinets(0, 5, 10) == (0, 0)
	
	# Special case: 1 board
	assert utils.min_num_cabinets(1, 1, 1) == (1, 1)
	assert utils.min_num_cabinets(1, 5, 10) == (1, 1)
	
	# Up-to a frame worth
	assert utils.min_num_cabinets(5, 5, 10) == (1, 1)
	assert utils.min_num_cabinets(9, 5, 10) == (1, 1)
	assert utils.min_num_cabinets(10, 5, 10) == (1, 1)
	
	# Up-to a cabinet worth
	assert utils.min_num_cabinets(11, 5, 10) == (1, 2)
	assert utils.min_num_cabinets(20, 5, 10) == (1, 2)
	assert utils.min_num_cabinets(21, 5, 10) == (1, 3)
	assert utils.min_num_cabinets(49, 5, 10) == (1, 5)
	assert utils.min_num_cabinets(50, 5, 10) == (1, 5)
	
	# Multiple cabinets worth
	assert utils.min_num_cabinets(51, 5, 10) == (2, 5)
	assert utils.min_num_cabinets(99, 5, 10) == (2, 5)
	assert utils.min_num_cabinets(100, 5, 10) == (2, 5)
	assert utils.min_num_cabinets(101, 5, 10) == (3, 5)
