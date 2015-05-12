import pytest

from mock import Mock

from tempfile import mkstemp

import os

from spinner.scripts.ethernet_chips import main

def test_valid_csv(capsys):
	"""Simply test a valid CSV is produced with one title row and the rest
	numbers."""
	
	assert main("-n 240".split()) == 0
	
	out, err = capsys.readouterr()
	
	# Should have one line per board with one heading layer
	lines = out.strip().split("\n")
	assert len(lines) == 240 + 1
	
	# Should have the same number of columns in every row
	assert all(len(line.split(",")) == 5 for line in lines)
	
	# All non-title cells should be integers
	assert all(all(col.isdigit()
	               for col in line.split(","))
	           for line in lines[1:])
	
	# Build up a list of boards and network coordinates to check
	boards = []
	coords = []
	for line in lines[1:]:
		c,f,b, x,y = map(int, line.split(","))
		boards.append((c,f,b))
		coords.append((x,y))
	
	# No duplicates
	assert len(boards) == len(set(boards))
	assert len(coords) == len(set(coords))
	
	# Within expected range (combined with the previous assertions, this
	# effectively guarantees that every board has a mention)
	assert all(0 <= c < 2 and 0 <= f < 5 and 0 <= b < 24
	           for c,f,b in boards)
	
	# Check network coordinates in expected range
	assert all(0 <= x < 120 and 0 <= y < 96 for x,y in coords)


def test_exhaustive(capsys):
	"""Test the output for a 3 board system exhaustively."""
	
	assert main("-n 3".split()) == 0
	stdout, stderr = capsys.readouterr()
	
	assert stdout == (
		"cabinet,frame,board,x,y\n"
		"0,0,0,0,0\n"
		"0,0,2,4,8\n"
		"0,0,1,8,4\n"
	)
