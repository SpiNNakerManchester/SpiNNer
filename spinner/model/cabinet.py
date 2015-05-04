#!/usr/bin/env python

"""
Utilities for working with the geometry of cabinets of frames of boards.
"""

from spinner.model import topology
from spinner.model import coordinates


class Board(object):
	"""
	A board in a frame.
	"""
	
	def __init__( self
	            , dimensions = coordinates.Cartesian3D(1.0,10.0,10.0)
	            , wire_position = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		wire_position is a mapping {direction:position, ...} which gives the physical
		offset from the bottom, left front corner of the board of the given wire.
		Defaults to zero offsets for all dimensions.
		"""
		
		self.dimensions = dimensions
		
		self.wire_position = wire_position or {
			topology.NORTH      : (self.width/2.0, (self.height/6.0)*0, 0.0),
			topology.NORTH_EAST : (self.width/2.0, (self.height/6.0)*1, 0.0),
			topology.EAST       : (self.width/2.0, (self.height/6.0)*2, 0.0),
			topology.SOUTH      : (self.width/2.0, (self.height/6.0)*3, 0.0),
			topology.SOUTH_WEST : (self.width/2.0, (self.height/6.0)*4, 0.0),
			topology.WEST       : (self.width/2.0, (self.height/6.0)*5, 0.0),
		}
	
	
	@property
	def width(self):  return self.dimensions[0]
	@property
	def height(self): return self.dimensions[1]
	@property
	def depth(self):  return self.dimensions[2]
	
	
	def get_position(self, direction):
		"""
		Get the position of the given wire relative to (0,0,0) in this board. If the
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
		
		# Make sure the boards fit inside the cabinet...
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


class Frame(_Container):
	"""
	A frame which contains boards horizontally along the x-axis.
	"""
	
	def __init__( self
	            , board = None
	            , dimensions = coordinates.Cartesian3D(30.0,15.0,20.0)
	            , num_boards = 24
	            , board_spacing = 0.1
	            , board_offset = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		num_boards is the number of boards the frame fits
		
		board_spacing is the additional (horizontal) space between each board
		
		board_offset is the offset of the 0th board from (0,0,0) of the frame. If
		not specified, the boards are centered within the frame's vertical and
		horizontal axes and placed at depth 0.
		
		board is a Board definition.
		"""
		board = board or Board()
		self.volume = board
		self.board  = board
		
		self.num_boards    = num_boards
		self.board_spacing = board_spacing
		
		_Container.__init__( self
		                   , dimensions
		                   , (num_boards, 1)
		                   , coordinates.Cartesian2D(board_spacing, 0.0)
		                   , board_offset
		                   )
	
	
	def get_position(self, board, direction = None):
		"""
		Get the position of the given board (and optionally wire) relative to (0,0,0)
		in this frame.
		"""
		
		board_position = self.get_volume_position((board, 0))
		
		wire_position = self.board.get_position(direction)
		
		return coordinates.Cartesian3D( board_position.x + wire_position.x
		                              , board_position.y + wire_position.y
		                              , board_position.z + wire_position.z
		                              )



class Cabinet(_Container):
	"""
	A cabinet which contains frames vertically along the y-axis.
	"""
	
	def __init__( self
	            , frame = None
	            , dimensions = coordinates.Cartesian3D(40.0,180.0,25.0)
	            , num_frames = 10
	            , frame_spacing = 2
	            , frame_offset = None
	            ):
		"""
		dimensions is a Cartesian3D(width, height, depth).
		
		num_frames is the number of frames the cabinet fits
		
		frame_spacing is the additional (vertical) space between each frame
		
		frame_offset is the offset of the 0th frame from (0,0,0) of the frame. If
		not specified, the frames are centered within the frame's vertical and
		horizontal axes and placed at depth 0.
		
		frame is a Frame definition.
		"""
		frame = frame or Frame()
		self.volume = frame
		self.frame  = frame
		
		self.num_frames    = num_frames
		self.frame_spacing = frame_spacing
		
		_Container.__init__( self
		                   , dimensions
		                   , (1, num_frames)
		                   , coordinates.Cartesian2D(0.0, frame_spacing)
		                   , frame_offset
		                   )
	
	
	def get_position(self, frame, board, direction = None):
		"""
		Get the position of the given board within a frame (and optionally wire)
		relative to (0,0,0) in this cabinet.
		"""
		
		frame_position = self.get_volume_position((0, frame))
		
		wire_position = self.frame.get_position(board, direction)
		
		return coordinates.Cartesian3D( frame_position.x + wire_position.x
		                              , frame_position.y + wire_position.y
		                              , frame_position.z + wire_position.z
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
		Get the position of the given board in a frame in a cabinet (and optionally
		wire) in the system.
		"""
		
		wire_position = self.cabinet.get_position(coord[1], coord[2], direction)
		
		return coordinates.Cartesian3D(
			wire_position.x + (self.cabinet.width + self.cabinet_spacing) * coord[0],
			wire_position.y,
			wire_position.z,
		)
