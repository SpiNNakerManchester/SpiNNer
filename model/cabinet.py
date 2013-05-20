#!/usr/bin/env python

"""
Utilities for working with the geometry of cabinets of racks of boards.
"""

import topology
import coordinates


class Slot(object):
	"""
	A slot in a rack.
	"""
	
	def __init__( self
	            , dimensions = coordinates.Cartesian3D(1.0,10.0,10.0)
	            , wire_position = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		wire_position is a mapping {direction:position, ...} which gives the physical
		offset from the bottom, left front corner of the slot of the given wire.
		Defaults to zero offsets for all dimensions.
		"""
		
		self.dimensions = dimensions
		
		self.wire_position = wire_position or {
			topology.NORTH      : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*0, 0.0),
			topology.NORTH_EAST : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*1, 0.0),
			topology.EAST       : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*2, 0.0),
			topology.SOUTH      : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*3, 0.0),
			topology.SOUTH_WEST : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*4, 0.0),
			topology.WEST       : coordinates.Cartesian3D(self.width/2.0, (self.height/6.0)*5, 0.0),
		}
	
	
	@property
	def width(self):  return self.dimensions[0]
	@property
	def height(self): return self.dimensions[1]
	@property
	def depth(self):  return self.dimensions[2]
	
	
	def get_position(self, direction):
		"""
		Get the position of the given wire relative to (0,0,0) in this slot. If the
		direction given is None or was not defined, returns (0,0,0).
		"""
		
		return coordinates.Cartesian3D(
			*self.wire_position.get(direction, coordinates.Cartesian3D(0.0,0.0,0.0)))


class _Container(object):
	"""
	Used Internally
	
	A container which contains a grid of regularly spaced volumes along the x and
	y axes.
	"""
	
	def __init__( self
	            , dimensions
	            , grid_size
	            , spacing
	            , offset = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		grid_size is a tuple (cols, rows) specifying the number of elements in the
		grid of contained volumes.
		
		spacing is a tuple (horzontal, vertical) specifying the additional space
		between each contained volume
		
		offset is the offset of the (0,0)th volume from (0,0,0) of the container. If
		not specified, the volume grid is centered within the container's vertical
		and horizontal axes and placed at depth 0.
		
		Before this is called an object with a width and height and depth property
		should be defined as "volume" defining the size of the contained volume.
		"""
		
		self.dimensions = dimensions
		self.grid_size  = grid_size
		self.spacing    = spacing
		
		self.offset = offset if offset is not None \
		              else coordinates.Cartesian3D(
		                     (self.width/2.0) - (self.bay_width/2.0),
		                     (self.height/2.0) - (self.bay_height/2.0),
		                     0,
		                   )
		
		# Make sure the slots fit inside the cabinet...
		assert(self.bay_width  + self.offset[0] <= self.width)
		assert(self.bay_height + self.offset[1] <= self.height)
		assert(self.bay_depth                   <= self.depth)
	
	
	@property
	def width(self):  return self.dimensions[0]
	@property
	def height(self): return self.dimensions[1]
	@property
	def depth(self):  return self.dimensions[2]
	
	
	@property
	def bay_width(self):
		"""
		Width of the area holding volumes
		"""
		return ((self.volume.width + self.spacing[0]) * self.grid_size[0]) - self.spacing[0]
	@property
	def bay_height(self):
		"""
		Height of the area holding volumes
		"""
		return ((self.volume.height + self.spacing[1]) * self.grid_size[1]) - self.spacing[1]
	@property
	def bay_depth(self): return self.volume.depth
	
	
	def get_volume_position(self, volume):
		"""
		Get the position of the given volume relative to (0,0,0) in this container.
		"""
		
		col, row = volume
		
		return coordinates.Cartesian3D(
			x = self.offset[0]
			    + ((self.volume.width + self.spacing.x) * col),
			y = self.offset[1]
			    + ((self.volume.height + self.spacing.y) * row),
			z = self.offset[2],
		)


class Rack(_Container):
	"""
	A rack which contains slots horizontally along the x-axis.
	"""
	
	def __init__( self
	            , slot = None
	            , dimensions = coordinates.Cartesian3D(30.0,15.0,20.0)
	            , num_slots = 24
	            , slot_spacing = 0.1
	            , slot_offset = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		num_slots is the number of slots the rack fits
		
		slot_spacing is the additional (horizontal) space between each slot
		
		slot_offset is the offset of the 0th slot from (0,0,0) of the rack. If
		not specified, the slots are centered within the rack's vertical and
		horizontal axes and placed at depth 0.
		
		slot is a Slot definition.
		"""
		slot = slot or Slot()
		self.volume = slot
		self.slot   = slot
		
		self.num_slots    = num_slots
		self.slot_spacing = slot_spacing
		
		_Container.__init__( self
		                   , dimensions
		                   , (num_slots, 1)
		                   , coordinates.Cartesian2D(slot_spacing, 0.0)
		                   , slot_offset
		                   )
	
	
	def get_position(self, slot, direction = None):
		"""
		Get the position of the given slot (and optionally wire) relative to (0,0,0)
		in this rack.
		"""
		
		slot_position = self.get_volume_position((slot, 0))
		
		wire_position = self.slot.get_position(direction)
		
		return coordinates.Cartesian3D( slot_position.x + wire_position.x
		                              , slot_position.y + wire_position.y
		                              , slot_position.z + wire_position.z
		                              )



class Cabinet(_Container):
	"""
	A cabinet which contains racks vertically along the y-axis.
	"""
	
	def __init__( self
	            , rack = None
	            , dimensions = coordinates.Cartesian3D(40.0,180.0,25.0)
	            , num_racks = 10
	            , rack_spacing = 2
	            , rack_offset = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		num_racks is the number of racks the cabinet fits
		
		rack_spacing is the additional (vertical) space between each rack
		
		rack_offset is the offset of the 0th rack from (0,0,0) of the rack. If
		not specified, the racks are centered within the rack's vertical and
		horizontal axes and placed at depth 0.
		
		rack is a Rack definition.
		"""
		rack = rack or Rack()
		self.volume = rack
		self.rack   = rack
		
		self.num_racks    = num_racks
		self.rack_spacing = rack_spacing
		
		_Container.__init__( self
		                   , dimensions
		                   , (1, num_racks)
		                   , coordinates.Cartesian2D(0.0, rack_spacing)
		                   , rack_offset
		                   )
	
	
	def get_position(self, rack, slot, direction = None):
		"""
		Get the position of the given slot within a rack (and optionally wire)
		relative to (0,0,0) in this cabinet.
		"""
		
		rack_position = self.get_volume_position((0, rack))
		
		wire_position = self.rack.get_position(slot, direction)
		
		return coordinates.Cartesian3D( rack_position.x + wire_position.x
		                              , rack_position.y + wire_position.y
		                              , rack_position.z + wire_position.z
		                              )



class System(object):
	"""
	A system which contains a row of Cabinets horizontally along the x-axis.
	"""
	
	def __init__( self
	            , cabinet = None
	            , num_cabinets = 5
	            , cabinet_spacing = 1
	            ):
		"""
		num_cabinets is the number of cabinets in the system
		
		cabinet_spacing is the additional (horizontal) space between each cabinet
		
		cabinet is a Cabinet definition.
		"""
		self.num_cabinets    = num_cabinets
		self.cabinet_spacing = cabinet_spacing
		self.cabinet         = cabinet or Cabinet()
	
	
	def get_position(self, coord, direction = None):
		"""
		Get the position of the given slot in a rack in a cabinet (and optionally
		wire) in the system.
		"""
		
		wire_position = self.cabinet.get_position(coord[1], coord[2], direction)
		
		return coordinates.Cartesian3D(
			wire_position.x + (self.cabinet.width + self.cabinet_spacing) * coord[0],
			wire_position.y,
			wire_position.z,
		)
