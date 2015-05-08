"""Test machine map generator.

Unfortunately, due to the highly visual nature of this utility, these unit tests
are limited to simply checking for crashes and that outputs are of the correct
format and dimensions.
"""

import pytest

from mock import Mock

from tempfile import mkstemp

import os

from PIL import Image

from spinner.scripts.machine_map import main

@pytest.yield_fixture
def png_file():
	_, filename = mkstemp(suffix="map.png")
	
	yield filename
	
	os.remove(filename)

@pytest.yield_fixture
def pdf_file():
	_, filename = mkstemp(suffix="map.pdf")
	
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
