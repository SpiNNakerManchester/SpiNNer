#!/usr/bin/env python

"""
Parameter file for wiring_guide.py

A single rack of machines.
"""

################################################################################
# Basic Parameters
################################################################################

# The number of boards in the system (in threeboards)
width  = 2
height = 2

# The number of folds (actually the number of faces of a folded sheet)
num_folds_x = 2
num_folds_y = 1

# How is the machine split up into physical units
num_cabinets          = 1
num_racks_per_cabinet = 1
num_slots_per_rack    = 12


################################################################################
# Report Parameters
################################################################################

title = "SpiNNaker $10^4$ Machine Wiring"

# Scale all diagrams by this factor
diagram_scaling = 1.0

# Scale the cabinet diagram by this factor
cabinet_diagram_scaling_factor = 40

# Show metrics relating to the 
show_wiring_metrics = True

# Show information relating to the topology
show_topology_metrics = True

# Include the development section in the report
show_development = True

# Show metrics relating to the 
show_board_position_list = True

# Show instructions for wiring the machine
show_wiring_instructions = True

# Number of bins on wire-length histograms
wire_length_histogram_bins = 5

