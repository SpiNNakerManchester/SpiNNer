"""Test the explicit wiring listings.
"""

import pytest

from spinner.scripts.wiring_list import main

@pytest.mark.parametrize("extra_args",
                         ["",
                          " --sort-by board",
                          " --sort-by wire-length",
                          " --sort-by installation-order"])
def test_sanity(capsys, extra_args):
	"""
	Sanity check that the tool will happily run with basic arguments.
	"""
	# Shouldn't crash
	assert main("-n 24 -l 100.0 {}".format(extra_args).split()) == 0
	
	# Should have one line per expected wire and two lines for the heading
	out, err = capsys.readouterr()
	assert len(out.strip().split("\n")) == (24 * 3) + 2


@pytest.mark.parametrize("extra_args",
                         ["",
                          " --sort-by board"])
def test_board_sorting(capsys, extra_args):
	"""
	Check that sorting by board works
	"""
	# Shouldn't crash
	assert main("-n 24 -l 100.0 {}".format(extra_args).split()) == 0
	
	# Should be in order of boards
	out, err = capsys.readouterr()
	lines = out.strip().split("\n")
	order = [tuple(filter(None, line.split(" ")))[:4] for line in lines[2:]]
	order = [(int(c), int(f), int(b), d) for (c, f, b, d) in order]
	assert order == sorted(order)


def test_wire_length_sorting(capsys):
	"""
	Check that sorting by wire-length works
	"""
	# Shouldn't crash
	assert main("-n 24 -l 0.15 0.30 0.50 --sort-by wire-length".split()) == 0
	
	# Should be in order of wire-lengths then boards
	out, err = capsys.readouterr()
	lines = out.strip().split("\n")
	order = [tuple(filter(None, line.split(" "))) for line in lines[2:]]
	order = [(float(v[-1]), int(v[0]), int(v[1]), int(v[2]), v[3]) for v in order]
	assert order == sorted(order)
