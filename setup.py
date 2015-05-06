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
    install_requires=["six", "enum34"],

    # Scripts
    entry_points={
        "console_scripts": [
            "spinner-topology-stats = spinner.scripts.topology_stats:main",
        ],
    }
)
