import pytest

from mock import Mock

from tempfile import mkstemp

import os

from PIL import Image

from argparse import ArgumentParser

from spinner.topology import Direction

from spinner.scripts.wiring_diagram import \
	main, CabinetAction, add_arguments, get_arguments

from spinner.diagrams.machine import MachineDiagram

from spinner.cabinet import Cabinet

from example_cabinet_params import real


# Cabinet used in all examples (instantiated like this rather than using a
# fixture since it is used in test parameters)
c = Cabinet(**real)


class TestCabinetAction(object):
	
	@pytest.fixture
	def parser(self):
		parser = ArgumentParser()
		
		parser.add_argument("--cabinet-only", action=CabinetAction(1))
		parser.add_argument("--frame-only", action=CabinetAction(2))
		parser.add_argument("--board-only", action=CabinetAction(3))
		parser.add_argument("--full-spec", action=CabinetAction(4))
		parser.add_argument("--multiple", action=CabinetAction(4, append=True))
		
		return parser
	
	
	@pytest.mark.parametrize("argstring", [# No arguments
	                                       "--cabinet-only",
	                                       "--frame-only",
	                                       "--board-only",
	                                       "--full-spec",
	                                       "--multiple",
	                                       "--multiple --multiple",
	                                       # Too many arguments
	                                       "--cabinet-only 1 2",
	                                       "--frame-only 1 2 3",
	                                       "--board-only 1 2 3 north",
	                                       "--full-spec 1 2 3 north bad",
	                                       "--multiple 1 2 3 north bad",
	                                       "--multiple 1 2 3 north bad --multiple 1 2 3 north bad",
	                                       # Negative
	                                       "--cabinet-only -1",
	                                       "--frame-only 1 -2",
	                                       "--board-only 1 2 -3 north",
	                                       "--full-spec 1 2 -3 north",
	                                       "--multiple 1 2 -3 north",
	                                       "--multiple 1 2 -3 north --multiple 1 2 -3 north",
	                                       # Non-number
	                                       "--cabinet-only bad",
	                                       "--frame-only 1 bad",
	                                       "--board-only 1 2 bad north",
	                                       "--full-spec 1 2 bad north",
	                                       "--multiple 1 2 bad north",
	                                       "--multiple 1 2 bad north --multiple 1 2 bad north",
	                                       # Non-direction
	                                       "--full-spec 1 2 3 bad",
	                                       "--multiple 1 2 3 bad",
	                                       "--multiple 1 2 3 bad --multiple 1 2 3 bad",
	                                      ])
	def test_bad(self, parser, argstring):
		with pytest.raises(SystemExit):
			parser.parse_args(argstring.split())
	
	
	@pytest.mark.parametrize("argstring,full_spec",
	                         [# Just cabinet
	                          ("--full-spec 0", (0, )),
	                          ("--full-spec 1", (1, )),
	                          # Cabinet and frame
	                          ("--full-spec 0 0", (0, 0)),
	                          ("--full-spec 1 2", (1, 2)),
	                          # Cabinet, frame and board
	                          ("--full-spec 0 0 0", (0, 0, 0)),
	                          ("--full-spec 1 2 3", (1, 2, 3)),
	                          # Cabinet, frame, board and socket
	                          ("--full-spec 0 0 0 north",
	                           (0, 0, 0, Direction.north)),
	                          ("--full-spec 1 2 3 north-east",
	                           (1, 2, 3, Direction.north_east)),
	                         ])
	def test_full_spec(self, parser, argstring, full_spec):
		args = parser.parse_args(argstring.split())
		assert args.full_spec == full_spec
	
	
	@pytest.mark.parametrize("argstring,multiple",
	                         [# None
	                          ("", None),
	                          # One
	                          ("--multiple 1", [(1, )]),
	                          # Several
	                          ("--multiple 1 --multiple 2 3", [(1, ), (2, 3)]),
	                         ])
	def test_multiple(self, parser, argstring, multiple):
		args = parser.parse_args(argstring.split())
		assert args.multiple == multiple


@pytest.mark.parametrize("argstring,to_check",
                         [# File type detection
                          ("out.png -n 3", {"file_type": "png"}),
                          ("out.pNg -n 3", {"file_type": "png"}),
                          ("out.PNG -n 3", {"file_type": "png"}),
                          ("out.pdf.png -n 3", {"file_type": "png"}),
                          ("out.pdf -n 3", {"file_type": "pdf"}),
                          ("out.pDf -n 3", {"file_type": "pdf"}),
                          ("out.PDF -n 3", {"file_type": "pdf"}),
                          ("out.png.pdf -n 3", {"file_type": "pdf"}),
                          # Manual image sizes (PNGs should be integers, PDFs
                          # should be floats)
                          ("out.png 10.5 100.5 -n 3", {"image_width":10,
                                                       "image_height":100}),
                          ("out.png 100.5 10.5 -n 3", {"image_width":100,
                                                       "image_height":10}),
                          ("out.pdf 10.5 100.5 -n 3", {"image_width":10.5,
                                                       "image_height":100.5}),
                          ("out.pdf 100.5 10.5 -n 3", {"image_width":100.5,
                                                       "image_height":10.5}),
                          # Semi-automatic image sizes (three-board systems
                          # should be tall)
                          ("out.pdf 1000.5 -n 3", {"image_height":1000.5,
                                                   "same_ratio_as":c.get_dimensions(boards=3)[:2]}),
                          ("out.png 1000.5 -n 3", {"image_height":1000,
                                                   "same_ratio_as":c.get_dimensions(boards=3)[:2]}),
                          # Semi-automatic but for wider system
                          ("out.pdf 1000.5 -n 24", {"image_width":1000.5,
                                                    "same_ratio_as":c.get_dimensions(boards=24)[:2]}),
                          ("out.png 1000.5 -n 24", {"image_width":1000,
                                                    "same_ratio_as":c.get_dimensions(boards=24)[:2]}),
                          # Fully-automatic for tall systems
                          ("out.png -n 3", {"image_height":1000,
                                            "same_ratio_as":c.get_dimensions(boards=3)[:2]}),
                          ("out.pdf -n 3", {"image_height":280.0,
                                            "same_ratio_as":c.get_dimensions(boards=3)[:2]}),
                          # Fully-automatic for wide systems
                          ("out.png -n 24", {"image_width":1000,
                                             "same_ratio_as":c.get_dimensions(boards=24)[:2]}),
                          ("out.pdf -n 24", {"image_width":280.0,
                                             "same_ratio_as":c.get_dimensions(boards=24)[:2]}),
                          # Wire thickness
                          ("out.png -n 3", {"wire_thickness": "normal"}),
                          ("out.png -n 3 --wire-thickness normal",
                           {"wire_thickness": "normal"}),
                          ("out.png -n 3 --wire-thickness thin",
                           {"wire_thickness": "thin"}),
                          ("out.png -n 3 --wire-thickness thick",
                           {"wire_thickness": "thick"}),
                          # Focus on individual boards for small systems
                          ("out.png -n 3", {"focus": (0, 0, slice(0, 3))}),
                          ("out.png -n 9", {"focus": (0, 0, slice(0, 9))}),
                          ("out.png -n 24", {"focus": (0, 0, slice(0, 24))}),
                          # Focus on frames for larger systems
                          ("out.png -n 48", {"focus": (0, slice(0, 2))}),
                          # Focus on cabinets for the largest systems
                          ("out.png -n 1200", {"focus": (slice(0, 10), )}),
                          # Highlights
                          ("out.png -n 3", {"highlight": []}),
                          ("out.png -n 3 --highlight 0 0 0 north",
                           {"highlight": [(0, 0, 0, Direction.north)]}),
                          ("out.png -n 3 --highlight 0 0 0 north --highlight 0",
                           {"highlight": [(0, 0, 0, Direction.north), (0, )]}),
                          # Show/hide labels
                          ("out.png -n 3", {"hide_labels": False}),
                          ("out.png -n 3 -L", {"hide_labels": True}),
                         ])
def test_get_arguments(argstring, to_check):
	parser = ArgumentParser()
	add_arguments(parser)
	
	args = parser.parse_args(argstring.split())
	(w, h), transformation, uncrinkle_direction, folds, \
	       cabinet, num_frames, \
	       output_filename, file_type, image_width, image_height, \
	       focus, wire_thickness, highlights, hide_labels =\
		get_arguments(parser, args)
	
	if "file_type" in to_check:
		assert file_type == to_check.pop("file_type")
	
	if "image_height" in to_check:
		assert image_height == to_check.pop("image_height")
	if "image_width" in to_check:
		assert image_width == to_check.pop("image_width")
	
	if "same_ratio_as" in to_check:
		ref_w, ref_h = to_check.pop("same_ratio_as")
		ref_ratio = ref_w / float(ref_h)
		ratio = image_width / float(image_height)
		
		# Should be pretty close (slack allowed for rounding to pixels in PNG)
		assert abs(ratio - ref_ratio) < 0.001
	
	if "wire_thickness" in to_check:
		assert wire_thickness == to_check.pop("wire_thickness")
	
	if "focus" in to_check:
		assert focus == to_check.pop("focus")
	
	if "highlight" in to_check:
		assert highlights == to_check.pop("highlight")
	
	if "hide_labels" in to_check:
		assert hide_labels == to_check.pop("hide_labels")
	
	# Make sure none of the test-cases define something to test which isn't
	# tested...
	assert len(to_check) == 0


@pytest.mark.parametrize("argstring",
                         [# Missing filename
                          "-n 3",
                          # Missing/Unknown file extension
                          "out -n 3",
                          "out.gif -n 3",
                          "out.png.gif -n 3",
                          # Invalid output sizes
                          "out.png 0.5 -n 3",
                          "out.png 0.5 0.5 -n 3",
                          "out.png 10 0.5 -n 3",
                          "out.png 0.5 10 -n 3",
                          "out.pdf 0 -n 3",
                          "out.pdf 0 0 -n 3",
                          "out.pdf 1 0 -n 3",
                          "out.pdf 0 1 -n 3",
                          # Invalid wire thickness
                          "out.png --wire-thickness bad -n 3",
                          # Invalid highlight
                          "out.png --highlight bad -n 3",
                         ])
def test_get_arguments_bad(argstring):
	parser = ArgumentParser()
	add_arguments(parser)
	
	with pytest.raises(SystemExit):
		args = parser.parse_args(argstring.split())
		get_arguments(parser, args)


@pytest.yield_fixture
def png_file():
	_, filename = mkstemp(suffix="diagram.png")
	
	yield filename
	
	os.remove(filename)


@pytest.yield_fixture
def pdf_file():
	_, filename = mkstemp(suffix="diagram.pdf")
	
	yield filename
	
	os.remove(filename)


def test_png_output(png_file):
	"""
	Run the utility and make sure it generates a PNG of the correct size (doesn't
	verify its contents; this is assumed to be correct).
	"""
	
	# Shouldn't crash
	assert main("{} 123 234 -n 3".format(png_file).split()) == 0
	
	# Should be able to read the file with PIL
	im = Image.open(png_file)
	assert im.format == "PNG"
	assert im.size == (123, 234)


def test_pdf_output(pdf_file):
	"""
	Run the utility and make sure it generates a PDF. Due to difficulties in
	easily working with PDF files, this simply checks that the file starts with a
	PDF magic byte.
	"""
	
	# Shouldn't crash
	assert main("{} 123 234 -n 3".format(pdf_file).split()) == 0
	
	# Should be a valid PDF file
	with open(pdf_file, "rb") as f:
		assert f.read(4) == b"%PDF"


@pytest.mark.parametrize("has_labels", [True, False])
def test_labels(pdf_file, has_labels, monkeypatch):
	"""
	Test that labels are added for every board but only when requested.
	"""
	add_label_mock = Mock()
	monkeypatch.setattr(MachineDiagram, "add_label", add_label_mock)
	
	# Shouldn't crash
	assert main("{} 123 234 -n 240 {}".format(
		pdf_file,
		"" if has_labels else "-L",
	).split()) == 0
	
	# Should have labels added to every board/cabinet/rack
	if has_labels:
		expected_labels = []
		for cabinet in range(2):
			expected_labels.append((cabinet, cabinet))
			for frame in range(5):
				expected_labels.append((frame, cabinet, frame))
				for board in range(24):
					expected_labels.append((board, cabinet, frame, board))
		expected_labels.sort()
		
		assert sorted(c[1] for c in add_label_mock.mock_calls) == expected_labels
	else:
		assert not add_label_mock.called


@pytest.mark.parametrize("add_highlight", [True, False])
def test_highlight(pdf_file, add_highlight, monkeypatch):
	"""
	Test that highlights are added when requested
	"""
	add_highlight_mock = Mock()
	monkeypatch.setattr(MachineDiagram, "add_highlight", add_highlight_mock)
	
	# Shouldn't crash
	assert main("{} 123 234 -n 3 {}".format(
		pdf_file,
		"--highlight 0 0 0 --highlight 0 0 0 north" if add_highlight else "",
	).split()) == 0
	
	# Should have the expected highlights
	if add_highlight:
		expected_highlights = sorted([(0, 0, 0), (0, 0, 0, Direction.north)])
		assert sorted(c[1] for c in add_highlight_mock.mock_calls) == expected_highlights
	else:
		assert not add_highlight_mock.called
