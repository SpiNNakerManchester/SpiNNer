import pytest

from spinner.model import coordinates


def test___repr__():
	# Make sure the generic repr implementation uses the correct name and lists
	# all dimensions in the correct order.
	assert repr(coordinates.Hexagonal(1, 2, 3)) == "Hexagonal(1, 2, 3)"
	assert repr(coordinates.Cartesian2D(1, 2)) == "Cartesian2D(1, 2)"


def test_hexagonal():
	a = coordinates.Hexagonal(1,2,3)
	b = coordinates.Hexagonal(-1,-1,-1)
	
	# Should always equal their equivilent tuples
	assert a == (1,2,3)
	assert b == (-1,-1,-1)
	
	# Basic operators
	assert a+b == (0,1,2)
	assert a-b == (2,3,4)
	assert abs(b) == (1,1,1)
	
	# Magnitude
	assert a.magnitude() == 2
	assert b.magnitude() == 0


def test_hexagonal2d():
	a = coordinates.Hexagonal2D(1,2)
	b = coordinates.Hexagonal2D(-1,-1)
	
	# Should always equal their equivilent tuples
	assert a == (1,2)
	assert b == (-1,-1)
	
	# Basic operators
	assert a+b == (0,1)
	assert a-b == (2,3)
	assert abs(b) == (1,1)
	
	# Magnitude
	assert a.magnitude() == 2
	assert b.magnitude() == 1


def test_cartesian3d():
	a = coordinates.Cartesian3D(1,2,3)
	b = coordinates.Cartesian3D(-1,-1,-1)
	
	# Should always equal their equivilent tuples
	assert a == (1,2,3)
	assert b == (-1,-1,-1)
	
	# Basic operators
	assert a+b == (0,1,2)
	assert a-b == (2,3,4)
	assert abs(b) == (1,1,1)
	
	# Magnitude
	assert a.magnitude() == (1**2 + 2**2 + 3**2)**0.5
	assert b.magnitude() == (3)**0.5


def test_cartesian2d():
	a = coordinates.Cartesian2D(1,2)
	b = coordinates.Cartesian2D(-1,-1)
	
	# Should always equal their equivilent tuples
	assert a == (1,2)
	assert b == (-1,-1)
	
	# Basic operators
	assert a+b == (0,1)
	assert a-b == (2,3)
	assert abs(b) == (1,1)
	
	# Magnitude
	assert a.magnitude() == (1**2 + 2**2)**0.5
	assert b.magnitude() == (2)**0.5


def test_cabinet():
	a = coordinates.Cabinet(1,2,3)
	b = coordinates.Cabinet(-1,-1,-1)
	
	# Should always equal their equivilent tuples
	assert a == (1,2,3)
	assert b == (-1,-1,-1)
	
	# Basic operators
	assert a+b == (0,1,2)
	assert a-b == (2,3,4)
	assert abs(b) == (1,1,1)

