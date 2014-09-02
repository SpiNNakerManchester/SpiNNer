#!/usr/bin/env python

"""
Provides a utility function for reading model specifications from files.
"""

from ConfigParser import ConfigParser

from model import coordinates
from model.topology import NORTH, NORTH_EAST, EAST, SOUTH, SOUTH_WEST, WEST

def parse_params(filenames):
	"""
	Takes a set of filenames to read as config files and returns a dictionary
	containing the following keys:
		
		slot_width,    slot_height,    slot_depth,
		rack_width,    rack_height,    rack_depth,
		cabinet_width, cabinet_height, cabinet_depth,
		wire_positions, socket_names,
		slot_spacing, slot_offset, num_slots_per_rack,
		rack_spacing, rack_offset, num_racks_per_cabinet,
		cabinet_spacing, num_cabinets,
		width, height,
		num_folds_x, num_folds_y,
		compress_rows,
		title,
		diagram_scaling, cabinet_diagram_scaling_factor,
		show_wiring_metrics, show_topology_metrics, show_development,
		show_board_position_list, show_wiring_instructions,
		wire_length_histogram_bins
	"""
	cp = ConfigParser()
	assert set(cp.read(filenames)) == set(filenames) \
	     , "%s could not be read."%(", ".join(set(filenames) - set(cp.read(filenames))))
	
	def to_3D_tuple(option):
		return map(float, map(str.strip, option.strip("()").split(",")))
	
	output = {}
	
	# Board properties
	output["wire_positions"] = {
		SOUTH_WEST: to_3D_tuple(cp.get("board", "wire_south_west")),
		NORTH_EAST: to_3D_tuple(cp.get("board", "wire_north_east")),
		EAST:       to_3D_tuple(cp.get("board", "wire_east")),
		WEST:       to_3D_tuple(cp.get("board", "wire_west")),
		NORTH:      to_3D_tuple(cp.get("board", "wire_north")),
		SOUTH:      to_3D_tuple(cp.get("board", "wire_south")),
	}
	output["socket_names"] = {
		SOUTH_WEST: cp.get("board", "socket_name_south_west").strip(),
		NORTH_EAST: cp.get("board", "socket_name_north_east").strip(),
		EAST:       cp.get("board", "socket_name_east").strip(),
		WEST:       cp.get("board", "socket_name_west").strip(),
		NORTH:      cp.get("board", "socket_name_north").strip(),
		SOUTH:      cp.get("board", "socket_name_south").strip(),
	}
	
	# Slot properties
	output["slot_width"]   = cp.getfloat("slot", "width")
	output["slot_height"]  = cp.getfloat("slot", "height")
	output["slot_depth"]   = cp.getfloat("slot", "depth")
	output["slot_spacing"] = cp.getfloat("slot", "spacing")
	
	# Rack properties
	output["rack_width"]   = cp.getfloat("rack", "width")
	output["rack_height"]  = cp.getfloat("rack", "height")
	output["rack_depth"]   = cp.getfloat("rack", "depth")
	output["rack_spacing"] = cp.getfloat("rack", "spacing")
	output["slot_offset"]  = coordinates.Cartesian3D(*
	                           to_3D_tuple(cp.get("rack", "slot_offset"))
	                         ) if cp.has_option("rack","slot_offset") else None
	
	# Cabinet properties
	output["cabinet_width"]   = cp.getfloat("cabinet", "width")
	output["cabinet_height"]  = cp.getfloat("cabinet", "height")
	output["cabinet_depth"]   = cp.getfloat("cabinet", "depth")
	output["cabinet_spacing"] = cp.getfloat("cabinet", "spacing")
	output["rack_offset"]     = coordinates.Cartesian3D(*
	                              to_3D_tuple(cp.get("cabinet", "rack_offset"))
	                            ) if cp.has_option("cabinet","rack_offset") else None
	
	# System properties
	output["num_slots_per_rack"]    = cp.getint("system", "num_slots_per_rack")
	output["num_racks_per_cabinet"] = cp.getint("system", "num_racks_per_cabinet")
	output["num_cabinets"]          = cp.getint("system", "num_cabinets")
	
	# Wiring properties
	output["minimum_arc_height"] = cp.getfloat("wiring", "minimum_arc_height")
	
	# Available wire lengths {wire_length: wire_name,...}
	output["available_wires"] = dict( (cp.getfloat("available wires", o), o)
	                                  for o in cp.options("available wires")
	                                )
	
	# Network properties
	output["width"]         = cp.getint("network", "width")
	output["height"]        = cp.getint("network", "height")
	output["num_folds_x"]   = cp.getint("network", "num_folds_x")
	output["num_folds_y"]   = cp.getint("network", "num_folds_y")
	output["compress_rows"] = cp.getboolean("network", "compress_rows")
	
	# Metadata
	output["title"] = cp.get("metadata", "title").strip()
	
	# Report parameters
	output["diagram_scaling"] = cp.getfloat("report", "diagram_scaling")
	output["cabinet_diagram_scaling_factor"] = cp.getfloat("report", "cabinet_diagram_scaling_factor")
	
	output["show_wiring_metrics"]      = cp.getboolean("report", "show_wiring_metrics")
	output["show_topology_metrics"]    = cp.getboolean("report", "show_topology_metrics")
	output["show_development"]         = cp.getboolean("report", "show_development")
	output["show_board_position_list"] = cp.getboolean("report", "show_board_position_list")
	output["show_wiring_instructions"] = cp.getboolean("report", "show_wiring_instructions")
	
	output["wire_length_histogram_bins"] = cp.getint("report", "wire_length_histogram_bins")
	
	return output


def parse_bmp_ips(filenames):
	"""
	Takes a set of filenames to read as config files listing BMP IP addresses.
	
	Returns a dictionary {board_position: ip} where board_position is either
	a tuple (cabinet, rack, slot) or (cabinet, rack) where the former should be
	used if both are available. The IP/hostname is given as a string.
	"""
	cp = ConfigParser()
	assert set(cp.read(filenames)) == set(filenames) \
	     , "%s could not be read."%(", ".join(set(filenames) - set(cp.read(filenames))))
	
	out = {}
	
	for board_position, ip in cp.items("bmpip"):
		board_position = tuple(map(int, map(str.strip, board_position.split(","))))
		
		assert board_position not in out \
		     , "%s is defined multiple times"%(board_position)
		
		out[board_position] = ip
	
	return out
