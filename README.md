SpiNNer
=======

A collection of tools for generating physical wiring info/diagrams for systems
of SpiNNaker boards.

Paper Wiring Guides
-------------------

To generate a PDF wiring guide:

	python wiring_guide.py params/[some .param file] > wiring_guide.tex
	pdflatex wiring_guide.tex
	pdflatex wiring_guide.tex

Further details are available at http://jhnet.co.uk/projects/spinner.

Interactive Wiring Guide
------------------------

An interactive, graphical tool which can guide a user through a list of wiring
instructions or corrections.

Features:
* Cycle through a list of wiring instructions
* Display a full view of the system being wired up
* Display close-up views of pairs of boards being connected
* Illuminate an LED on boards to be connected
* Read instructions using text-to-speech
* Colour code diagrams by wire-length
* Check the wiring of a running system

Requires:
* pygame
* pycairo
* numpy
* PIL (Python Imaging Library)
* espeak (optional: for text-to-speech)
* SpiNNMan (optional: for board LED control and wiring checking)

See help for full usage:

	python interactive_wiring_guide.py -h

Example usage:

	# Generates (and then interactively guide through) a wiring plan to wire up a
	# complete machine.
	python interactive_wiring_guide.py params/[some .param file] \
	  -b params/[some .bmpip file]
	
	# Examine the wiring of a machine and produce (and interactively guide
	# through) a correction plan. Note that the tool must be re-run to update the
	# list of errors (at the time of writing it is also advisable to reset the
	# system before doing so to ensure all newly connected links handshake
	# correctly).
	python interactive_wiring_guide.py params/[some .param file] \
	  -b params/[some .bmpip file] -c

Annotated screenshot:

![Interactive Wiring Guide](http://jhnet.co.uk/misc/interactive_wiring_guide_screenshot.png)


Wiring Plan Generator
---------------------

Intended to be a module of functions for creating sensible wiring instructions
for assembling large machine. If called on the command line, produces a textual
wiring plan. Example incantation:

	python wiring_plan_generator.py params/[some .param file]


Wiring Validator
----------------

Intended to be a module of functions for discovering the connectivity of a large
system (and producing plans for any required corrections). If called on the
command line, produces a textual list of corrections to be made. Example
incantation:

	python wiring_validator.py params/[some .param file] \
	  -b params/[some .bmpip file]

If the wiring is correct, the program exits with exit code 0. If there are
errors present, the program terminates with a non-zero exit code.

Requires:
* SpiNNMan


Machine Map Generator
---------------------

This tool generates a map defining the relation between cabinet/rack/slot and
chip x/y coordinates in a system booted up via the board in cabinet=rack=slot=0.

A graphical map can be produced (in PDF) for a given page size (given in mm)
using the command below. Note that the PDF is written to standard out.

	python machine_map_generator.py params/[some .param file] -g [width] [height] > map.pdf

Sample output can be seen below:

![Machine Map](http://jhnet.co.uk/misc/spin_105_map.png)


A plain-text enumeration can be generated using the commandline below. This can
be extended with the `-a` option which enumerates every chip, not just one per
board.

	python wiring_map_generator.py params/[some .param file]


Machine Diagram
---------------

A module which (quickly) generates images of SpiNNaker machines and their wiring
using Cairo. Though intended for use as a library, if called on the command line
it will produce an image sequence showing the wiring plan for a given system:

	python machine_diagram.py params/[some .param file] \
	  output_file_name_xxxx.png width height

An example output for a SpiNN-105 Machine:

![Animated Wiring Plan](http://jhnet.co.uk/misc/spin_105_wiring.gif)


Model
-----

A model of the SpiNNaker system and a series of manipulation utilities are
provided in the "model" module. At the top level of the repository are a number
of scripts which attempt to produce useful information or implement wrappers
around the model to handle common manipulations.

Author
------

The SpiNNer code base is the work of Jonathan Heathcote although the wiring
techniques used are based nearly in their entirety on extensive discussions with
Steve Furber, Jim Garside, Simon Davidson, Steve Temple and Luis Plana.

The physical measurements assumed by SpiNNer were contributed by Steve Temple.
