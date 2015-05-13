``spinner-topology-stats``
==========================

Prints basic statistics about the network topology which will result from a
given system.

::

	$ spinner-topology-stats -h
	usage: spinner-topology-stats [-h] [--version] (--num-boards N | --triads W H)
	                              [--transformation {shear,slice}]
	                              [--uncrinkle-direction {columns,rows}]
	                              [--folds X Y]
	
	Print basic topological statistics for a specified configuration of boards.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --version, -V         show program's version number and exit
	
	machine topology dimensions:
	  --num-boards N, -n N  build the 'squarest' system with this many boards
	  --triads W H, -t W H  build a system with the specified number of triads of
	                        boards in each dimension (yielding 3*W*H boards)
	
	topology folding options:
	  --transformation {shear,slice}, -T {shear,slice}
	                        the transformation function to use from hexagonal
	                        torus to rectangular Cartesian grid (selected
	                        automatically if omitted)
	  --uncrinkle-direction {columns,rows}
	                        direction in which to uncrinkle the hexagonal mesh to
	                        form a regular grid (default: rows)
	  --folds X Y, -F X Y   the number of pieces to fold into in each dimension
	                        (default: (2, 2)) ignored if --transformation is not
	                        given
	


Finding sytstem dimensions
--------------------------

The most common use-case for ``spinner-topology-stats`` is determining the
network dimensions of a given system of N boards.

For example, want to know about a 120-board system? ::

	$ spinner-topology-stats -n 120
	Topology Statistics
	===================
	
	| Measurement        | Value  | Unit  |
	| ------------------ | ------ | ----- |
	| Network dimensions | 96x60  | chips |
	| Board array        | 8x5    | triad |
	| Number of boards   | 120    |       |
	| Number of cables   | 360    |       |
	| Number of chips    | 5760   |       |
	| Number of cores    | 103680 |       |

In this example, the network of SpiNNaker chips in this system will be 96x60 and
the system is made up of 8x5 triads.
