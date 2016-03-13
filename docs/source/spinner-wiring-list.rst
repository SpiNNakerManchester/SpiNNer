``spinner-wiring-list``
========================

Textually enumerates every connection required in a machine.

::

	$ spinner-wiring-list -h
	usage: spinner-wiring-list [-h]
	                           [--sort-by {installation-order,board,wire-length}]
	                           [--version] (--num-boards N | --triads W H)
	                           [--transformation {shear,slice}]
	                           [--uncrinkle-direction {columns,rows}]
	                           [--folds X Y] [--board-dimensions W H D]
	                           [--board-wire-offset-south-west X Y Z]
	                           [--board-wire-offset-north-east X Y Z]
	                           [--board-wire-offset-east X Y Z]
	                           [--board-wire-offset-west X Y Z]
	                           [--board-wire-offset-north X Y Z]
	                           [--board-wire-offset-south X Y Z]
	                           [--inter-board-spacing S]
	                           [--boards-per-frame BOARDS_PER_FRAME]
	                           [--frame-dimensions W H D]
	                           [--frame-board-offset X Y Z]
	                           [--inter-frame-spacing S]
	                           [--frames-per-cabinet FRAMES_PER_CABINET]
	                           [--cabinet-dimensions W H D]
	                           [--cabinet-frame-offset X Y Z]
	                           [--inter-cabinet-spacing S] [--num-cabinets N]
	                           [--num-frames N] [--wire-length L [L ...]]
	                           [--minimum-slack H]
	
	Textually enumerate every connection required in a machine.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --sort-by {installation-order,board,wire-length}, -s {installation-order,board,wire-length}
	                        Specifies the order the connections should be listed
	                        in the file: installation-order sorts in the most
	                        sensible order for installation, board lists wires on
	                        a board-by-board basis, wire-length lists in order of
	                        wire length.
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
	
	board physical dimensions:
	  --board-dimensions W H D
	                        physical board dimensions in meters (default: (0.014,
	                        0.233, 0.24))
	  --board-wire-offset-south-west X Y Z
	                        physical offset of the south-west connector from board
	                        left-top-front corner in meters (default: (0.008,
	                        0.013, 0.0))
	  --board-wire-offset-north-east X Y Z
	                        physical offset of the north-east connector from board
	                        left-top-front corner in meters (default: (0.008,
	                        0.031, 0.0))
	  --board-wire-offset-east X Y Z
	                        physical offset of the east connector from board left-
	                        top-front corner in meters (default: (0.008, 0.049,
	                        0.0))
	  --board-wire-offset-west X Y Z
	                        physical offset of the west connector from board left-
	                        top-front corner in meters (default: (0.008, 0.067,
	                        0.0))
	  --board-wire-offset-north X Y Z
	                        physical offset of the north connector from board
	                        left-top-front corner in meters (default: (0.008,
	                        0.085, 0.0))
	  --board-wire-offset-south X Y Z
	                        physical offset of the south connector from board
	                        left-top-front corner in meters (default: (0.008,
	                        0.103, 0.0))
	  --inter-board-spacing S
	                        physical spacing between each board in a frame in
	                        meters (default: 0.00124)
	
	frame physical dimensions:
	  --boards-per-frame BOARDS_PER_FRAME
	                        number of boards per frame (default: 24)
	  --frame-dimensions W H D
	                        frame physical dimensions in meters (default: (0.43,
	                        0.266, 0.25))
	  --frame-board-offset X Y Z
	                        physical offset of the left-top-front corner of the
	                        left-most board from the left-top-front corner of a
	                        frame in meters (default: (0.06, 0.017, 0.0))
	  --inter-frame-spacing S
	                        physical spacing between frames in a cabinet in meters
	                        (default: 0.133)
	
	cabinet physical dimensions:
	  --frames-per-cabinet FRAMES_PER_CABINET
	                        number of frames per cabinet (default: 5)
	  --cabinet-dimensions W H D
	                        cabinet physical dimensions in meters (default: (0.6,
	                        2.0, 0.25))
	  --cabinet-frame-offset X Y Z
	                        physical offset of the left-top-front corner of the
	                        top frame from the left-top-front corner of a cabinet
	                        in meters (default: (0.085, 0.047, 0.0))
	  --inter-cabinet-spacing S
	                        physical spacing between each cabinet in meters
	                        (default: 0.0)
	  --num-cabinets N, -c N
	                        specify how many cabinets to spread the system over
	                        (default: the minimum possible)
	  --num-frames N, -f N  when only one cabinet is required, specifies how many
	                        frames within that cabinet the system should be spread
	                        across (default: the minimum possible)
	
	available wire lengths:
	  --wire-length L [L ...], -l L [L ...]
	                        specify one or more available wire lengths in meters
	  --minimum-slack H     the minimum slack to allow in a wire connecting two
	                        boards in meters


Enumerating required wires
--------------------------

To get a list of all connections required when assembling a given machine
simply run ``spinner-wiring-list`` specifying a number of boards and available
wire lengths::

	$ spinner-wiring-list -n 24 -l 0.15 0.3 0.5
	C  F  B  Socket      C  F  B  Socket      Length
	-- -- -- ----------  -- -- -- ----------  ------
	 0  0  0 east         0  0  5 west        0.15
	 0  0  0 north        0  0  4 south       0.15
	 0  0  0 south west   0  0  7 north east  0.30
	 0  0  1 east         0  0  4 west        0.15
	 0  0  1 north        0  0  5 south       0.15
	 0  0  1 south west   0  0  6 north east  0.15
	 0  0  2 east         0  0  0 west        0.15
	 0  0  2 north        0  0  1 south       0.15
	[...snip...]

Each connection is listed with its Cabinet, Frame and Board (C, F and B) number
and the socket to use. The suggested wire length to use is also given.

By default the list is ordered by board position (top-right to bottom-left) but
this can be changed to either installation-order or ordered by wire length
using the ``--sort-by`` arguments.
