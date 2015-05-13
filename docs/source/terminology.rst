Terminology & Conventions
=========================

The following terminology and conventions are used throughout SpiNNer's scripts
and code.

Cabinets, Frames and Boards
---------------------------

When discussing SpiNNaker systems, it is assumed that the system is comprised of
SpiNN-5 boards arranged in standard 19" cabinets and frames like so::

	          2             1                0
	Cabinet --+-------------+----------------+
	          |             |                |
	+-------------+  +-------------+  +-------------+    Frame
	|             |  |             |  |             |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 0
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
	| +---------+ |  | +---------+ |  | +---------+ |      |
	| | : : : : | |  | | : : : : | |  | | : : : : |--------+ 1
	| | : : : : | |  | | : : : : | |  | | : : : : | |      |
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

A convention used throughout SpiNNer is to refer to individual boards by their
position expressed in the form of (cabinet, frame, board) triples.

Triads and Boards
-----------------

When describing large systems, their size is referred to either as a number of
SpiNN-5 boards or in terms of their width/height in triads. A triad is a group
of three SpiNN-5 boards connected like so::

	 ___
	/   \___
	\___/   \
	/   \___/
	\___/

This pattern is repeated horizontally::

	 ___     ___     ___     ___
	/   \___/   \___/   \___/   \___
	\___/   \___/   \___/   \___/   \
	/   \___/   \___/   \___/   \___/
	\___/   \___/   \___/   \___/


And then vertically::

	 ___     ___     ___     ___
	/   \___/   \___/   \___/   \___
	\___/   \___/   \___/   \___/   \
	/   \___/   \___/   \___/   \___/
	\___/   \___/   \___/   \___/   \___
	    \___/   \___/   \___/   \___/   \
	    /   \___/   \___/   \___/   \___/
	    \___/   \___/   \___/   \___/

Thus, in this example, we have a 4x2 triad, or 24 board system.

When specifying systems just in terms of numbers of boards, the squarest-possible
arrangement of triads with that number of boards is assumed (preferring
landscape arrangements when a square arrangement is not possible).

Physical Dimensions
-------------------

All real-world physical dimensions are given in meters.

Physical coordinates are supplied in 3D space with the axes going from
left-to-right, top-to-bottom and front-to-back for X, Y and Z respectively. ::

	   _  Z
	   /|
	  /
	 /
	o-------> X
	|
	|
	|
	V
	Y


Folding
-------

For definitions of the terms used to describe the folding process (e.g. shear,
slice and uncrinkling), please refer to "Bringing the Hexagonal Torus Topology
into the Real-World" by `Jonathan Heathcote <mailto:mail@jhnet.co.uk>`_ et. al.
which is available on request and is expected to be published at some future
point.
