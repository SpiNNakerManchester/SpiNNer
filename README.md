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

An interactive, graphical tool which can guide a user through a predefined
list of wiring instructions.

Features:
* Cycle through a list of wiring instructions
* Display a full view of the system being wired up
* Display close-up views of pairs of boards being connected
* Illuminate an LED on boards to be connected
* Read instructions using text-to-speech
* Colour code diagrams by wire-length

Requires:
* pygame
* pycairo
* numpy
* PIL (Python Imaging Library)
* espeak (optional: for text-to-speech)
* SpiNNMan (optional: for board LED control)

See help for full usage:

	python interactive_wiring_guide.py -h

Example usage:

	python interactive_wiring_guide.py params/[some .param file] \
	  -b params/[some .bmpip file]

Annotated screenshot:

![Interactive Wiring Guide](http://jhnet.co.uk/misc/interactive_wiring_guide_screenshot.png)


Machine Diagram
---------------

A module which (quickly) generates images of SpiNNaker machines and their wiring
using Cairo. Though intended for use as a library, if called on the command line
it will produce an image sequence showing the wiring plan for a given system:

	python machine_diagram.py params/[some .param file] \
	  output_file_name_xxxx.png width height

An example output for a SpiNN-105 Machine:

![Animated Wiring Plan](http://jhnet.co.uk/misc/spin_105_wiring.gif)

Wiring Plan Generator
---------------------

Intended to be a module of functions for creating sensible wiring instructions
for assembling large machine. If called on the command line, produces a textual
wiring plan. Example incantation:

	python wiring_plan_generator.py params/[some .param file]

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
