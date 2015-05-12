SpiNNer
=======

A collection of tools for generating physical wiring info/diagrams for systems
of SpiNNaker boards.

Installation
------------

SpiNNer has the following external dependencies (aside from Python 2.7+ or 3.4+):

| Dependency                                                  | Ubuntu Package | Fedora Package | Arch Package |
| ----------------------------------------------------------- | -------------- | -------------- | ------------ |
| [Cairo](http://cairographics.org/)                          | libcairo2-dev  | cairo-devel    | cairo        |
| [libffi](https://sourceware.org/libffi/)                    | libffi-dev     | libffi-devel   | libffi       |
| [Tkinter](https://docs.python.org/3.4/library/tkinter.html) | python-tk      | tkinter        | tk           |
| [Espeak](http://espeak.sourceforge.net/)                    | espeak         | espeak         | espeak       |

The easiest way to install the latest release of SpiNNer (along with other
Python packages it uses) to use use
[pip](https://pip.pypa.io/en/latest/installing.html):

	# pip install spinnaker_spinner


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
