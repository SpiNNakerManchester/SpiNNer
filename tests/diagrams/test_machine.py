"""
Tests of machine drawing functions.

Since it is very hard to test visual output, these tests are *very* rough and
simply check low-hanging fruit: Does it not crash? Does it draw the right number
of rectangles?
"""

import pytest

from mock import Mock

from collections import defaultdict

from six import itervalues

from spinner.diagrams.machine import normalise_slice, MachineDiagram

from spinner.cabinet import Cabinet

from spinner.topology import Direction

from example_cabinet_params import real, unique


# Cabinet used in all examples (instantiated like this rather than using a
# fixture since it is used in test parameters)
c = Cabinet(**real)



@pytest.mark.parametrize("orig,new", [# Constants
                                      (0, slice(0, 1)),
                                      (1, slice(1, 2)),
                                      # None
                                      (None, slice(0, 10)),
                                      # Complete slices
                                      (slice(0, 2), slice(0, 2)),
                                      (slice(4, 8), slice(4, 8)),
                                      # Open-ended slices
                                      (slice(0, None), slice(0, 10)),
                                      (slice(2, None), slice(2, 10)),
                                      (slice(None, 2), slice(0, 2)),
                                      (slice(None, 5), slice(0, 5)),
                                     ])
def test_normalise_slice(orig, new):
	assert normalise_slice(orig, 10) == new


def test_unsupported_3D_connectors():
	# Ensure that if our cabinet has connectors outside the x-y plane it fails
	# noisily rather than silently flattening everything.
	with pytest.raises(NotImplementedError):
		c = Cabinet(**unique)
		MachineDiagram(c)


@pytest.mark.parametrize("add_wires,add_labels,add_highlights",
                         [(False, False, False),
                          (True, False, False),
                          (False, True, False),
                          (False, False, True)])
def test_draw(add_wires, add_labels, add_highlights):
	"""
	A very incomplete test of the drawing functions but enough to see that nothing
	outright crashes.
	"""
	md = MachineDiagram(c)
	
	if add_highlights:
		md.add_highlight(1)
		md.add_highlight(1, 2)
		md.add_highlight(1, 2, 3)
		md.add_highlight(1, 2, 3, Direction.north)
	
	if add_labels:
		md.add_label("one", 0)
		md.add_label("two", 0, 1)
		md.add_label("three", 0, 1, 2)
		md.add_label("four", 0, 1, 2, Direction.north)
	
	if add_wires:
		md.add_wire((0,0,0,Direction.north), (1,2,3,Direction.north))
		md.add_wire((1,2,3,Direction.west), (1,2,3,Direction.east))
	
	ctx = Mock()
	ctx.text_extents.return_value = [1.0]*6
	
	md.draw(ctx, 1.0, 1.0)
	
	# Brief check that the right number of rectangles of the right sizes for all
	# the cabinets, frames, boards and that they're drawn in the right
	# places.
	expected_coordinates = {
		c.board_dimensions[:2]: list(c.get_position(cab,frm,brd)[:2]
		                             for cab in range(c.num_cabinets)
		                             for frm in range(c.frames_per_cabinet)
		                             for brd in range(c.boards_per_frame)),
		c.frame_dimensions[:2]: list(c.get_position(cab,frm)[:2]
		                             for cab in range(c.num_cabinets)
		                             for frm in range(c.frames_per_cabinet)),
		c.cabinet_dimensions[:2]: list(c.get_position(cab)[:2]
		                               for cab in range(c.num_cabinets)),
	}
	
	# If we've added highlights, we should expect a extra rectangles in the
	# highlighted locations
	if add_highlights:
		expected_coordinates[c.cabinet_dimensions[:2]].append(c.get_position(1)[:2])
		expected_coordinates[c.frame_dimensions[:2]].append(c.get_position(1, 2)[:2])
		expected_coordinates[c.board_dimensions[:2]].append(c.get_position(1, 2, 3)[:2])
	
	other_size_counts = defaultdict(lambda: 0)
	
	for rectangle_call in ctx.rectangle.mock_calls:
		x,y, w,h = rectangle_call[1]
		if (w, h) in expected_coordinates:
			assert (x, y) in expected_coordinates[(w, h)]
			expected_coordinates[(w, h)].remove((x, y))
		else:
			other_size_counts[(w, h)] += 1
	
	# All expected coordinates should have been seen
	assert all(len(cnt) == 0 for cnt in itervalues(expected_coordinates))
	
	# Should have one extra set of rectangles, the connectors, of which there
	# should be the correct number (possibly including an extra for the highlight)
	assert len(other_size_counts) == 1
	assert other_size_counts.popitem()[1] == (
		len(c.board_wire_offset) *
		c.num_cabinets *
		c.frames_per_cabinet *
		c.boards_per_frame) + int(add_highlights)
	
	# Check that the correct labels were drawn
	labels_drawn = set()
	for show_text_mock in ctx.show_text.mock_calls:
		labels_drawn.add(show_text_mock[1][0])
	if add_labels:
		assert labels_drawn == set("one two three four".split())
	else:
		assert len(labels_drawn) == 0
	
	# Check that the correct wires were drawn
	lines_drawn = set()
	for mv, ln in zip(ctx.move_to.mock_calls, ctx.line_to.mock_calls):
		lines_drawn.add((mv[1], ln[1]))
	
	if add_wires:
		assert len(lines_drawn) == 2
		assert ((c.get_position(0,0,0,Direction.north)[:2],
		         c.get_position(1,2,3,Direction.north)[:2]) in lines_drawn
		        or
		        (c.get_position(1,2,3,Direction.north)[:2],
		         c.get_position(0,0,0,Direction.north)[:2]) in lines_drawn)
		assert ((c.get_position(1,2,3,Direction.west)[:2],
		         c.get_position(1,2,3,Direction.east)[:2]) in lines_drawn
		        or
		        (c.get_position(1,2,3,Direction.west)[:2],
		         c.get_position(1,2,3,Direction.east)[:2]) in lines_drawn)
	else:
		assert len(lines_drawn) == 0

@pytest.mark.parametrize("w,h", [(1.0, 1.0), (1, 1), (100, 100),
                                 (10, 100), (100, 10)])
@pytest.mark.parametrize(
	"args,offset,dimensions",
	[
		# Should default to showing all cabinets
		([], c.get_position(1), c.get_dimensions()),
		# Should be able to select everything via a slice
		([slice(0, 2)], c.get_position(1), c.get_dimensions()),
		([slice(None, 2)], c.get_position(1), c.get_dimensions()),
		([slice(0, None)], c.get_position(1), c.get_dimensions()),
		([slice(None, None)], c.get_position(1), c.get_dimensions()),
		# Should be able to select individual cabinets
		([0], c.get_position(0), c.get_dimensions(cabinets=1)),
		# Should be able to select groups of frames to view
		([0, 0], c.get_position(0, 0), c.get_dimensions(frames=1)),
		([0, 1], c.get_position(0, 1), c.get_dimensions(frames=1)),
		([1, 0], c.get_position(1, 0), c.get_dimensions(frames=1)),
		([1, 1], c.get_position(1, 1), c.get_dimensions(frames=1)),
		([1, slice(2, 4)], c.get_position(1, 2), c.get_dimensions(frames=2)),
		([1, slice(None, 4)], c.get_position(1, 0), c.get_dimensions(frames=4)),
		([1, slice(2, None)], c.get_position(1, 2), c.get_dimensions(frames=3)),
		([1, slice(None, None)], c.get_position(1, 0), c.get_dimensions(frames=5)),
		# Should be able to select groups of boards to view
		([0, 0, 0], c.get_position(0, 0, 0), c.get_dimensions(boards=1)),
		([0, 0, 1], c.get_position(0, 0, 1), c.get_dimensions(boards=1)),
		([1, 2, 0], c.get_position(1, 2, 0), c.get_dimensions(boards=1)),
		([1, 2, 1], c.get_position(1, 2, 1), c.get_dimensions(boards=1)),
		([1, 2, slice(2, 4)], c.get_position(1, 2, 3), c.get_dimensions(boards=2)),
		([1, 2, slice(None, 4)], c.get_position(1, 2, 3), c.get_dimensions(boards=4)),
		([1, 2, slice(2, None)], c.get_position(1, 2, 23), c.get_dimensions(boards=22)),
		([1, 2, slice(None, None)], c.get_position(1, 2, 23), c.get_dimensions(boards=24)),
	])
def test_focus(w, h, args, offset, dimensions):
	"""
	Check that zooming is being done correctly.
	
	Tests building a diagram of various sizes and ensures that the focused area's
	four corners always touch the sides of the bounds and are not distorted.
	
	w, h is the image boundary
	
	args is the set of extra arguments to give the draw function (i.e. the
	specification of the area to focus)
	
	offset, dimensions give the expected area to be zoomed to fill the image.
	"""
	md = MachineDiagram(c)
	
	# Mock out the draw function to speed up testing...
	md._draw_system = Mock()
	
	ctx = Mock()
	md.draw(ctx, w, h, *args)
	
	# Grab the transformations performed before drawing (assumption: the
	# transforms go translate, scale translate).
	tx1, ty1 = ctx.translate.mock_calls[0][1]
	sx1, sy1 = ctx.scale.mock_calls[0][1]
	tx2, ty2 = ctx.translate.mock_calls[1][1]
	
	def transform(x, y):
		x, y = x+tx2, y+ty2
		x, y = x*sx1, y*sy1
		x, y = x+tx1, y+ty1
		return (x, y)
	
	# Make sure the expected bounds maximally fit the area specified
	x1, y1, _ = offset
	x2, y2, _ = offset + dimensions
	x1, y1 = transform(x1,y1)
	x2, y2 = transform(x2,y2)
	
	def approx_equal(a, b):
		print("approx_equal({}, {})".format(a, b))
		return abs(a - b) < 0.00001
	
	# The expected bounding area should be in proportion to its original
	# size/shape (give-or-take floating-point precision)
	assert approx_equal(float(x2-x1) / float(y2-y1),
	                    float(dimensions.x) / float(dimensions.y))
	
	# The bounding area's corners should touch the image boundary
	assert approx_equal(x1, 0) or approx_equal(y1, 0)
	assert approx_equal(x2, w) or approx_equal(y2, h)


@pytest.mark.parametrize(
	"args",
	[[],
	 [0],
	 [1],
	 [slice(0, 2)],
	 [1, 0],
	 [1, 1],
	 [1, slice(2, 4)],
	 [1, 2, 0],
	 [1, 2, 1],
	 [1, 2, slice(2, 4)],
	])
def test_masks(args):
	# Build the expected set of boards/frames/cabinets to render
	expected_cabinets = set()
	expected_frames = set()
	expected_boards = set()
	
	args_padded = args + [None, None, None]
	cabinets = normalise_slice(args_padded[0], c.num_cabinets)
	frames = normalise_slice(args_padded[1], c.frames_per_cabinet)
	boards = normalise_slice(args_padded[2], c.boards_per_frame)
	
	for cabinet in range(cabinets.start, cabinets.stop):
		expected_cabinets.add(cabinet)
		for frame in range(frames.start, frames.stop):
			expected_frames.add((cabinet, frame))
			for board in range(boards.start, boards.stop):
				expected_boards.add((cabinet, frame, board))
	
	# From this expected set, build the expected set of rectangles to draw
	expected_rectangles = set()
	for cabinet in expected_cabinets:
		x, y, _ = c.get_position(cabinet)
		w, h, _ = c.cabinet_dimensions
		expected_rectangles.add((x, y, w, h))
	for cabinet, frame in expected_frames:
		x, y, _ = c.get_position(cabinet, frame)
		w, h, _ = c.frame_dimensions
		expected_rectangles.add((x, y, w, h))
	for cabinet, frame, board in expected_boards:
		x, y, _ = c.get_position(cabinet, frame, board)
		w, h, _ = c.board_dimensions
		expected_rectangles.add((x, y, w, h))
	
	md = MachineDiagram(c)
	
	ctx = Mock()
	md.draw(ctx, 1, 1, None, None, None, *args)
	
	expected_sizes = set([c.cabinet_dimensions[:2],
	                      c.frame_dimensions[:2],
	                      c.board_dimensions[:2]])
	
	# Make sure exactly the right set of rectangles was drawn
	for rectangle_call in ctx.rectangle.mock_calls:
		# Skip connectors
		x, y, w, h = rectangle_call[1]
		if (w, h) in expected_sizes:
			assert rectangle_call[1] in expected_rectangles
			expected_rectangles.remove(rectangle_call[1])
	assert len(expected_rectangles) == 0
