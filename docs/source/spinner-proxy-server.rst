``spinner-proxy-server``
========================

A proxy server which sits between very large SpiNNaker machines and multiple
instances of ``spinner-wiring-guide`` to enable multiple people to work on a
large machine at once. See below for a tutorial.

::

	usage: spinner-proxy-server [-h] [--version] [--host HOST] [--port PORT]
	                            [--verbose] (--num-boards N | --triads W H)
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
	                            [--num-frames N] [--bmp CABINET FRAME HOSTNAME]
	
	Start a proxy server to enable multiple interactive wiring sessions to
	interact with the same SpiNNaker machine.
	
	optional arguments:
	  -h, --help            show this help message and exit
	  --version, -V         show program's version number and exit
	  --host HOST, -H HOST  Host interface to listen on (default: any)
	  --port PORT, -p PORT  Port listen on (default: 6512)
	  --verbose, -v         Increase verbosity.
	
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
	
	SpiNNaker BMP connection details:
	  --bmp CABINET FRAME HOSTNAME
	                        specify the hostname of a BMP to use to communicate
	                        with SpiNNaker boards in the given frame

.. _multi-person-wiring:

Parallel, multi-person cable installation
-----------------------------------------

To enable multiple people to install the cables in a very large machine
simultaneously, a ``spinner-proxy-server`` may be set up which allows multiple
instances of the ``spinner-wiring-guide`` tool to be started, one instance per
person (ideally running on seperate computers and headphones).

The server should be started (on a single machine) like so::

	$ spinner-proxy-server -n 600 --bmp 0 0 192.168.1.0 ...
	Proxy server starting...

Note that the arguments specifying the size of the machine, along with BMP IP
addresses for all frames, must be given.

Next, each installer must start the interactive wiring guide, substituting the
ususal ``--bmp`` arguments for the hostname of the machine running the proxy
server. In addition the ``--subset`` argument (see :ref:`the documentation
<subset-argument>`) should be used to assign each installer a non-overlapping
portion of the machine.

For example, if the first installer will install all cables within cabinet 0
and between cabinets 1 and 0, the following command would be used to start the
wiring guide on their machine::

	$ spinner-wiring-guide -n 600 -l 0.15 0.3 0.5 0.7 1.0 --proxy hostname --subset 0.*.* 0-1.*.*

If the second installer will install cables in cabinet 1 and going between
cabinets 1 and 2, the following command would be used on their machine::

	$ spinner-wiring-guide -n 600 -l 0.15 0.3 0.5 0.7 1.0 --proxy hostname --subset 1.*.* 1-2.*.*

...and so on!

Since SpiNNer will install cables staying within cabinets before moving to
inter-cabinet cabling, the scheme described above should result in minimal
overlap between installers' activity. An alternative scheme would be for each
installer to first complete the wiring within their assigned cabinet and, once
complete, restart the tool to guide installation of the cables between
cabinets.
