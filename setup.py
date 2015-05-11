from setuptools import setup, find_packages

setup(
	name="spinnaker_spinner",
	version="0.1.2",
	packages=find_packages(),
	
	# Metadata for PyPi
	author="Jonathan Heathcote",
	description="A tool for generating wiring instructions for large SpiNNaker machines.",
	license="GPLv2",
	
	# Requirements
	install_requires=[
		# For Python 2/3 cross-compatibility
		"six", "enum34",
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
		],
	}
)
