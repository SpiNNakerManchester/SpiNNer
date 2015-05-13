``spinner-wiring-validator``
============================

Validate the wiring of a SpiNNaker system.

::

	$ spinner-wiring-validator -h
	usage: spinner-wiring-validator [-h] [--version] [--verbose]
	                                (--num-boards N | --triads W H)
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
	                                [--num-frames N]
	                                [--bmp CABINET FRAME HOSTNAME]
	
	Validate the wiring of a SpiNNaker system.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --version, -V         show program's version number and exit
	  --verbose, -v         list all incorrect and missing wires
	
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
	
	SpiNNaker BMP connection details:
	  --bmp CABINET FRAME HOSTNAME
	                        specify the hostname of a BMP to use to communicate
	                        with SpiNNaker boards in the given frame


Validating machine wiring
-------------------------

To check that all board-to-board links are operational and the wiring of a
machine matches the wiring plans produced by SpiNNer,
``spinner-wiring-validator`` can be used::

	$ spinner-wiring-validator -n 24 --bmp 0 0 BMP_HOSTNAME
	All 72 wires correctly connected.

Note a ``--bmp`` argument for every frame in the system must be supplied giving
the cabinet number, frame number and BMP hostname.

This test requires that all boards are powered on (e.g. using ``rig-power
BMP_HOSTNAME on -b 0-23`` for each frame).

.. note::
	
	``spinner-wiring-validator`` only checks that the high-speed-serial
	board-to-board links are active and connected to the correct boards. They do
	not test the integrity of the actual SpiNNaker chip-to-chip network.

If any wiring errors are detected, the missing connections can be listed by
enabling the ``--verbose`` option.

To aid in making any required corrections, you can also use
:ref:`spinner-wiring-guide --fix option <spinner-wiring-guide-fix>`.
