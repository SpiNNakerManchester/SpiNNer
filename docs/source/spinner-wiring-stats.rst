``spinner-wiring-stats``
========================

Prints basic statistics about the wiring of a specified configuration of boards.

::

	$ spinner-wiring-stats -h
	usage: spinner-wiring-stats [-h] [--version] (--num-boards N | --triads W H)
	                            [--transformation {shear,slice}]
	                            [--uncrinkle-direction {columns,rows}]
	                            [--folds X Y] [--histogram-bins N]
	                            [--wire-length L [L ...]]
	                            [--minimum-wire-arc-height H]
	                            [--board-dimensions W H D]
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
	                            [--num-frames N]
	
	Print basic wiring statistics for a specified configuration of boards.
	
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
	
	wire length histogram options:
	  --histogram-bins N, -H N
	                        number of bins to pack wire lengths into in the
	                        histogram of wire lengths (default: 5)
	
	available wire lengths:
	  --wire-length L [L ...], -l L [L ...]
	                        specify one or more available wire lengths in meters
	  --minimum-wire-arc-height H
	                        the minimum height of the arc formed by a wire
	                        connecting two boards in meters (a heuristic for
	                        determining the slack to allow when selecting wires)
	
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
	                        (default: 0.089)
	
	cabinet physical dimensions:
	  --frames-per-cabinet FRAMES_PER_CABINET
	                        number of frames per cabinet (default: 5)
	  --cabinet-dimensions W H D
	                        cabinet physical dimensions in meters (default: (0.6,
	                        1.822, 0.25))
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


Selecting wire lengths to buy
-----------------------------

By default ``spinner-wiring-stats`` shows a histogram of wire lengths required
to wire up the supplied system in the *Wire length histogram* section. This
histogram gives a basic overview of the lengths of wires required::

	$ spinner-wiring-stats -n 120
	...snip...
	| Range (meters)   | Count | Histogram       | Max Arc Height (meters) |
	| ---------------- | ----- | --------------- | ----------------------- |
	| 0.00 < x <= 0.16 | 200   | ############### | 0.07                    |
	| 0.16 < x <= 0.32 | 0     |                 | 0.00                    |
	| 0.32 < x <= 0.48 | 64    | #####           | 0.14                    |
	| 0.48 < x <= 0.64 | 0     |                 | 0.00                    |
	| 0.64 < x <= 0.80 | 96    | ########        | 0.17                    |


If the available wire lengths are known, these can be listed using the
``--wire-length`` option and the histogram will bin the wires in the system
accordingly::

	$ spinner-wiring-stats -n 120 --wire-length 0.15 0.30 0.50 1.00
	...snip...
	| Range (meters)   | Count | Histogram       | Max Arc Height (meters) |
	| ---------------- | ----- | --------------- | ----------------------- |
	| 0.00 < x <= 0.15 | 200   | ############### | 0.07                    |
	| 0.15 < x <= 0.30 | 0     |                 | 0.00                    |
	| 0.30 < x <= 0.50 | 64    | #####           | 0.15                    |
	| 0.50 < x <= 1.00 | 96    | ########        | 0.30                    |
	...snip...

When deciding the length of wire to use, spinner automatically includes a
certain amount of slack. To chose the amount of slack, SpiNNer assumes that
installed wires form a perfect arc between their sockets::

	                _ _ _ _ _ _ _ _ _ _
	         , - ~ ~ ~ - ,           ^
	     , '               ' ,       | arc height
	   ,                       ,     V
	--| |---------------------| |-------

In order to introduce a sensible amount of slack, wires are required to form an
arc of a minimimum height away from the boards. This value is controlled by the
``--minimum-wire-arc-height`` option and defaults to 0.05 m.

The histogram table also indicates the maximum arc height for each wire length.
This number gives an indication of how much excess slackness there will be when
the supplied wire lengths are used. This may be important when building systems
whose wires are installed in an enclosed space.

Determining the folding process
-------------------------------

Generally, SpiNNer automatically makes all the decisions required to 'fold' the
system to remove long wires. If you wish to see what decisions have been made,
refer to the *Folding Parameters* section of ``spinner-wiring-stats``'s output::

	$ spinner-wiring-stats -n 120
	...snip...
	Folding Parameters
	------------------
	
	| Parameter                    | Value | Unit   |
	| ---------------------------- | ----- | ------ |
	| Number of boards             | 120   |        |
	| System dimensions            | 8x5   | triads |
	| Transformation               | shear |        |
	| Uncrinkle Direction          | rows  |        |
	| Folds                        | 2x2   | pieces |
	| Number of cabinets           | 1     |        |
	| Number of frames-per-cabinet | 5     |        |
	| Number of boards-per-frame   | 24    |        |
	...snip...


Perfect-world wire-length measurements
--------------------------------------

The *Non-cabinetised measurements* section of ``spinner-wiring-stats`` gives the
wire-lengths of the folded system before the boards are mapped into real-world
cabinets. This section is useful when comparing alternative folding schemes
since the results are not distorted by the cabinet mapping process.

The numbers in this section assume all boards are laid out in large
rectangular grid and distance measures are given in units of the size of a
board.

::

	$ spinner-wiring-stats -n 1200
	...snip...
	Non-cabinetised measurements
	----------------------------
	
	| Parameter           | Value         | Unit   |
	| ------------------- | ------------- | ------ |
	| System dimensions   | 60.00 x 20.00 | boards |
	| Mean wire length    | 2.91          | boards |
	|   NE/SW             |   4.02        | boards |
	|   N/S               |   2.49        | boards |
	|   W/E               |   2.22        | boards |
	| Maximum wire length | 4.47          | boards |
	|   NE/SW             |   4.47        | boards |
	|   N/S               |   2.83        | boards |
	|   W/E               |   2.83        | boards |
	...snip...
