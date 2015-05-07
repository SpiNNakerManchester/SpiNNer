import pytest

from spinner.scripts.topology_stats import main

def test_topology_stats(capsys):
	# Just sanity check that the right numbers appear in the output
	assert main("-n 120".split()) == 0
	
	stdout, stderr = capsys.readouterr()
	
	assert "96x60" in stdout  # Network dimensions
	assert "8x5" in stdout  # Board array
	assert "120" in stdout  # Num boards
	assert "360" in stdout  # Num cables
	assert "5760" in stdout  # Num chips
	assert "103680" in stdout  # Num cores
