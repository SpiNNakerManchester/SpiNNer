SpiNNer
=======

A tool for generating physical wiring info/diagrams for systems of SpiNNaker
boards.

A model of the SpiNNaker system and a series of manipulation utilities are
provided in the "model" module. At the top level of the repository are a number
of scripts which attempt to provide useful metrics. `wiring_guide.py` is likely
the one of most interest which generates LaTeX documents describing large
machines.

Basic Usage
-----------

To generate a wiring guide:

	python wiring_guide.py params/[some .param file] > wiring_guide.tex
	pdflatex wiring_guide.tex
	pdflatex wiring_guide.tex

Further details are available at http://jhnet.co.uk/projects/spinner.


Author
------

The SpiNNer code base is the work of Jonathan Heathcote although the wiring
techniques used are based nearly in their entirety on extensive discussions with
Steve Furber, Jim Garside, Simon Davidson, Steve Temple and Luis Plana.

The physical measurements assumed by SpiNNer were contributed by Steve Temple.
