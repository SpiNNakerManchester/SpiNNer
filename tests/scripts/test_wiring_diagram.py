import pytest

from mock import Mock

from tempfile import mkstemp

import os

from PIL import Image

from argparse import ArgumentParser

from spinner.topology import Direction

from spinner.scripts import arguments

from spinner.scripts.wiring_diagram import \
	main, add_diagram_arguments, get_diagram_arguments

from spinner.diagrams.machine import MachineDiagram

from spinner.cabinet import Cabinet

from example_cabinet_params import real


# Cabinet used in all examples (instantiated like this rather than using a
# fixture since it is used in test parameters)
c = Cabinet(**real)


@pytest.mark.parametrize("argstring,to_check",
                         [# Wire thickness
                          ("-n 3", {"wire_thickness": "normal"}),
                          ("-n 3 --wire-thickness normal",
                           {"wire_thickness": "normal"}),
                          ("-n 3 --wire-thickness thin",
                           {"wire_thickness": "thin"}),
                          ("-n 3 --wire-thickness thick",
                           {"wire_thickness": "thick"}),
                          # Focus on individual boards for small systems
                          ("-n 3", {"focus": (0, 0, slice(0, 3))}),
                          ("-n 9", {"focus": (0, 0, slice(0, 9))}),
                          ("-n 24", {"focus": (0, 0, slice(0, 24))}),
                          # Focus on frames for larger systems
                          ("-n 48", {"focus": (0, slice(0, 2))}),
                          # Focus on cabinets for the largest systems
                          ("-n 1200", {"focus": (slice(0, 10), )}),
                          # Highlights
                          ("-n 3", {"highlight": []}),
                          ("-n 3 --highlight 0 0 0 north",
                           {"highlight": [(0, 0, 0, Direction.north)]}),
                          ("-n 3 --highlight 0 0 0 north --highlight 0",
                           {"highlight": [(0, 0, 0, Direction.north), (0, )]}),
                          # Show/hide labels
                          ("-n 3", {"hide_labels": False}),
                          ("-n 3 -L", {"hide_labels": True}),
                         ])
def test_get_diagram_arguments(argstring, to_check):
	parser = ArgumentParser()
	arguments.add_topology_args(parser)
	arguments.add_cabinet_args(parser)
	add_diagram_arguments(parser)
	
	args = parser.parse_args(argstring.split())
	
	(w, h), transformation, uncrinkle_direction, folds =\
		arguments.get_topology_from_args(parser, args)
	
	cabinet, num_frames =\
		arguments.get_cabinets_from_args(parser, args)
	
	aspect_ratio, focus, wire_thickness, highlights, hide_labels =\
		get_diagram_arguments(parser, args, w, h, cabinet, num_frames)
	
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
			expected_labels.append(tuple([cabinet]))
			for frame in range(5):
				expected_labels.append((cabinet, frame))
				for board in range(24):
					expected_labels.append((cabinet, frame, board))
		expected_labels.sort()
		
		# XXX: Note we're just checking the labels are added to the right places,
		# not their actual content
		assert sorted(c[1][1:] for c in add_label_mock.mock_calls) == expected_labels
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
