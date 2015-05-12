SpiNNer
=======

A collection of tools for generating physical wiring info/diagrams for systems
of SpiNNaker boards.

Installation
------------

First make sure you have Python 2.7+ or 3.4+ installed along with:

* [Python pip](https://pip.pypa.io/en/stable/)
* [Cairo](http://cairographics.org/)
* [Espeak](http://espeak.sourceforge.net/)

Then type:

	$ pip install spinnaker-spinner

To install SpiNNer


Available commands
------------------

The following standalone command line tools are installed by SpiNNer:

* `spinner-topology-stats`: Print basic topological statistics (including
  network dimensions) for a specified configuration of boards.
* `spinner-wiring-stats`: Print basic wiring statistics for a specified
  configuration of boards.
* `spinner-wiring-diagram`: Generate illustrations of SpiNNaker machine wiring.
* `spinner-wiring-guide`: Interactively guide the user through the process of
  wiring up a SpiNNaker machine.
* `spinner-wiring-validator`: Validate the wiring of a SpiNNaker system.
* `spinner-machine-map`: Generate visual maps from the SpiNNaker network
  topology to board locations.
* `spinner-ethernet-chips`: Produce CSV listings of Ethernet connected chip
  physical and network positions.


Author
------

The SpiNNer code base is the work of Jonathan Heathcote although the wiring
techniques used are based nearly in their entirety on extensive discussions with
Steve Furber, Jim Garside, Simon Davidson, Steve Temple and Luis Plana.

The default physical machine measurements used by SpiNNer were contributed by
Steve Temple.
