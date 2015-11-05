from setuptools import setup, find_packages


# Defines __version__
with open("spinner/version.py", "r") as f:
	exec(f.read())


setup(
	name="spinnaker_spinner",
	version=__version__,
	packages=find_packages(),
	
	# Metadata for PyPi
	author="Jonathan Heathcote",
	description="A tool for generating wiring instructions for large SpiNNaker machines.",
	long_description = (
		"See `GitHub <https://github.com/SpiNNakerManchester/SpiNNer>`_ or "
		"the documentation on `ReadTheDocs <http://spinner.readthedocs.org/>`_ for "
		"more information."
	),
	license="GPLv2",
	
	# Requirements
	install_requires=[
		# For Python 2/3 cross-compatibility
		"six", "enum-compat",
		# For generating diagrams
		"cairocffi",
		# For displaying diagrams interactively (used to connect Cairo images to
		# tkinter)
		"Pillow",
		# For interacting with a SpiNNaker machine
		"rig",
	],
	
	# Scripts
	entry_points={
		"console_scripts": [
			"spinner-topology-stats = spinner.scripts.topology_stats:main",
			"spinner-wiring-stats = spinner.scripts.wiring_stats:main",
			"spinner-wiring-diagram = spinner.scripts.wiring_diagram:main",
			"spinner-wiring-guide = spinner.scripts.wiring_guide:main",
			"spinner-wiring-validator = spinner.scripts.wiring_validator:main",
			"spinner-machine-map = spinner.scripts.machine_map:main",
			"spinner-ethernet-chips = spinner.scripts.ethernet_chips:main",
		],
	}
)
