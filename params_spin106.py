#!/usr/bin/env python

"""
Parameter file for wiring_guide.py
"""


################################################################################
# Basic Parameters
################################################################################

# The number of boards in the system (in threeboards)
width  = 20
height = 20

# When compressing a hexagonal grid into a regular rectangular gird, should
# every-other column of hexagons be shifted down by one? If not, every other row
# will be shifted left by one.
compress_rows = True

# The number of folds (actually the number of faces of a folded sheet)
num_folds_x = 4
num_folds_y = 2

# How is the machine split up into physical units
num_cabinets          = 10
num_racks_per_cabinet = 5
num_slots_per_rack    = 24


################################################################################
# Report Parameters
################################################################################

title = "SpiNNaker $10^6$ Machine Wiring"

# Scale all diagrams by this factor
diagram_scaling = 0.5

# The scaling factor applied to drawing of the racks/cabinets
cabinet_diagram_scaling_factor = 3.5

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

