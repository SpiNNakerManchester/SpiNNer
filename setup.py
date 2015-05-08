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
    install_requires=["six", "enum34", "cairocffi"],

    # Scripts
    entry_points={
        "console_scripts": [
            "spinner-topology-stats = spinner.scripts.topology_stats:main",
            "spinner-wiring-stats = spinner.scripts.wiring_stats:main",
            "spinner-wiring-diagram = spinner.scripts.wiring_diagram:main",
            "spinner-machine-map = spinner.scripts.machine_map:main",
        ],
    }
)
