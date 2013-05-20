#!/usr/bin/env python

"""
Coordinate systems which may be used.
"""

from collections import namedtuple


"""
Hexagonal coordinate system conventionally used when working with a hexagonal
mesh such a SpiNNaker nodes or boards.

Note: The three axes are non-orthogonal and so various strange things can happen
when working with such schemes. See the topology module for various useful
functions.
"""
Hexagonal = namedtuple("Hexagonal", ["x","y","z"])


"""
Special case of Hexagonal. Represents the Hexagonal() value with z fixed as 0.
"""
Hexagonal2D = namedtuple("Hexagonal2D", ["x","y"])


"""
Cartesian coordinates in either 2D or 3D space.
"""
Cartesian2D = namedtuple("Cartesian2D", ["x","y"])
Cartesian3D = namedtuple("Cartesian3D", ["x","y","z"])

"""
Logical coordinates for locations in a series of cabinets containing racks
containing slots, like so::
	
	          0             1                2
	Cabinet --+-------------+----------------+
	          |             |                |
	+-------------+  +-------------+  +-------------+     Rack
	|             |  |             |  |             |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 3
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 2
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | |#: : : : |--------+ 1
	| | : : : : | |  | | : : : : | |  | |#: : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 0
	| | : : : : | |  | | : : : : | |  | | : : : : | |
	| +---------+ |  | +|-|-|-|-|+ |  | +---------+ |
	|             |  |  | | | | |  |  |             |
	+-------------+  +--|-|-|-|-|--+  +-------------+
	                    | | | | |
	          Slots ----+-+-+-+-+
	                    0 1 2 3 4

In this example there are 3 cabinets each containing 4 racks which in turn
contain 5 slots.

Cabinets are numbered from 0 left-to-right. Racks are numbered from 0
bottom-to-top. Slots are numbered from 0 left-to-right. Therefore, the slot
marked with "#" is at the coordinate (2,1,0).
"""
Cabinet = namedtuple("Cabinet", ["cabinet","rack","slot"])


