SpiNNer Command-Line Utilities
==============================

SpiNNer's functions are broken down into a number of individual command-line
tools, all starting with ``spinner-*``. Each tool accepts arguments which
describe the SpiNNaker system of interest and a complete listing of these can be
found using the ``-h`` option.


Standard Arguments
------------------

All the SpiNNer commands accept a common set of arguments to specify the size of
the system to be built.

All commands require that you specify the size of the system you're working
with:

``--num-boards N`` or ``-n N``
	The number of boards to use. The 'squarest' possible system with this many
	boards will be created.

``--triads W H`` or ``-t W H``
	The dimensions of system in terms of triads of boards.

You can also optionally specify how these boards should be 'folded' to reduce
the maximum wire-length required when assembling such systems. These options are
largely for backward compatibility: the tool will automatically select a
sensible folding scheme.

When working with commands which deal with real-world physical dimensions, the
exact dimensions and positions of sockets, boards, frames and cabinets can be
defined using additional options (see ``spinner-wiring-guide -h``, for example,
for a list of these). The default values represent the dimensions of standard
cabinets and frames and can generally be left unchanged.


Command Documentation
---------------------

Example of common uses for each command can be found below:

.. toctree::
	:maxdepth: 2
	
	spinner-topology-stats
	spinner-wiring-stats
	spinner-wiring-diagram
	spinner-wiring-guide
	spinner-wiring-list
	spinner-wiring-validator
	spinner-machine-map
	spinner-ethernet-chips
	spinner-proxy-server

Backwards compatibility
-----------------------

Options which recreate wiring plans from old versions of SpiNNer can be found
here:

.. toctree::
	:maxdepth: 2
	
	backward_compatibility_options
