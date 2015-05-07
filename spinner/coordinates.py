#!/usr/bin/env python

"""
Coordinate systems which may be used. Coordinates can be added, subtracted, and
their magnitudes taken using .magnitude().
"""

from collections import namedtuple

################################################################################
# Base Classes (Internal Use Only)
################################################################################

class _ElementwiseCoordsMixin(object):
	"""
	Support for common operations on coordinates for which simple element-wise
	operators are adequate.
	"""
	
	def __add__(self, other):
		"""
		Performs element-wise subtraction.
		"""
		assert(len(self) == len(other))
		return type(self)(*(a+b for (a,b) in zip(self,other)))
	
	
	def __sub__(self, other):
		"""
		Performs element-wise subtraction.
		"""
		assert(len(self) == len(other))
		return type(self)(*(a-b for (a,b) in zip(self,other)))
	
	
	def __abs__(self):
		"""
		Element-wise absolute.
		"""
		return type(self)(*(abs(v) for v in self))
	
	
	def __repr__(self):
		return "%s(%s)"%(
			type(self).__name__,
			", ".join(map(repr, self))
		)



class _HexCoordsMixin(_ElementwiseCoordsMixin):
	"""
	Support for common operations on hexagonal coordinates.
	"""
	
	def __init__(self):
		_ElementwiseCoordsMixin.__init__(self)
	
	
	def magnitude(self):
		"""
		Magnitude
		"""
		# Pad to a 3-field value if 2D version.
		v = (list(self) + [0])[:3]
		from spinner import topology
		return topology.manhattan(topology.to_shortest_path(v))



class _CartesianCoordsMixin(_ElementwiseCoordsMixin):
	"""
	Support for common operations on Cartesian coordinates.
	"""
	
	def __init__(self, *args, **kwargs):
		_ElementwiseCoordsMixin.__init__(self)
	
	
	def to_positive(self):
		"""
		Return a positive-only version of the coordinate.
		"""
		return type(self)(*(abs(v) for v in self))
	
	
	def magnitude(self):
		"""
		Magnitude (Euclidean distance)
		"""
		from spinner import topology
		return topology.euclidean(self)



_HexagonalTuple = namedtuple("_HexagonalTuple", ["x","y","z"])
_Hexagonal2DTuple = namedtuple("_Hexagonal2DTuple", ["x","y"])

_Cartesian2DTuple = namedtuple("_Cartesian2DTuple", ["x","y"])
_Cartesian3DTuple = namedtuple("_Cartesian3DTuple", ["x","y","z"])

_CabinetTuple = namedtuple("_CabinetTuple", ["cabinet","frame","board"])




################################################################################
# Front-end Classes
################################################################################

"""
Hexagonal coordinate system conventionally used when working with a hexagonal
mesh such a SpiNNaker nodes or boards.

Note: The three axes are non-orthogonal and so various strange things can happen
when working with such schemes. See the topology module for various useful
functions.
"""
class Hexagonal(_HexCoordsMixin, _HexagonalTuple):
	def __init__(self, *args, **kwargs):
		_HexCoordsMixin.__init__(self)


"""
Special case of Hexagonal. Represents the Hexagonal() value with z fixed as 0.
"""
class Hexagonal2D(_HexCoordsMixin , _Hexagonal2DTuple):
	def __init__(self, *args, **kwargs):
		_HexCoordsMixin.__init__(self)


"""
Cartesian coordinates in either 2D or 3D space.
"""
class Cartesian2D(_CartesianCoordsMixin, _Cartesian2DTuple):
	def __init__(self, *args, **kwargs):
		_CartesianCoordsMixin.__init__(self)

class Cartesian3D(_CartesianCoordsMixin, _Cartesian3DTuple):
	def __init__(self, *args, **kwargs):
		_CartesianCoordsMixin.__init__(self)

"""
Logical coordinates for locations in a series of cabinets containing frames
containing boards, like so::
	
	          2             1                0
	Cabinet --+-------------+----------------+
	          |             |                |
	+-------------+  +-------------+  +-------------+    Frame
	|             |  |             |  |             |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 0
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : :#| |  | | : : : : | |  | | : : : : |--------+ 1
	| | : : : :#| |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 2
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 3
	| | : : : : | |  | | : : : : | |  | | : : : : | |
	| +---------+ |  | +|-|-|-|-|+ |  | +---------+ |
	|             |  |  | | | | |  |  |             |
	+-------------+  +--|-|-|-|-|--+  +-------------+
	                    | | | | |
	         Board -----+-+-+-+-+
	                    4 3 2 1 0

In this example there are 3 cabinets each containing 4 frames which in turn
contain 5 boards.

Cabinets are numbered from 0 right-to-left. Frames are numbered from 0
top-to-bottom. Boards are numbered from 0 right-to-left. Therefore, the board
marked with "#" is at the coordinate (2,1,0).
"""
class Cabinet(_ElementwiseCoordsMixin, _CabinetTuple):
	def __init__(self, *args, **kwargs):
		_ElementwiseCoordsMixin.__init__(self)


