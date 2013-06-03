#!/usr/bin/env python

"""
Parameter file for wiring_guide.py

A single threeboard.
"""

################################################################################
# Basic Parameters
################################################################################

# The number of boards in the system (in threeboards)
width  = 1
height = 1

# The number of folds (actually the number of faces of a folded sheet)
num_folds_x = 1
num_folds_y = 1

# When compressing a hexagonal grid into a regular rectangular gird, should
# every-other column of hexagons be shifted down by one? If not, every other row
# will be shifted left by one.
compress_rows = True

# How is the machine split up into physical units
num_cabinets          = 1
num_racks_per_cabinet = 1
num_slots_per_rack    = 4


################################################################################
# Report Parameters
################################################################################

title = "SpiNNaker $10^3$ Machine Wiring"

# Scale all diagrams by this factor
diagram_scaling = 1.0

# Scale the cabinet diagram by this factor
cabinet_diagram_scaling_factor = 40

# Show metrics relating to the 
show_wiring_metrics = False

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
