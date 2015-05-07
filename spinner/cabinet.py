"""Data structure which defines the physical dimensions of a set of cabinets."""

from spinner.topology import Direction

from spinner.coordinates import Cartesian3D

class Cabinet(object):
	"""Data structure which defines the physical dimensions of a set of
	cabinets.
	
	All coordinates and vectors are relative to the left-top-front corner of the
	machine.
	"""
	
	def __init__(self,
	             board_dimensions,
	             board_wire_offset_south_west, board_wire_offset_north_east,
	             board_wire_offset_east, board_wire_offset_west,
	             board_wire_offset_north, board_wire_offset_south,
	             inter_board_spacing,
	             boards_per_frame, frame_dimensions, frame_board_offset,
	             inter_frame_spacing,
	             frames_per_cabinet, cabinet_dimensions, cabinet_frame_offset,
	             inter_cabinet_spacing):
		"""Create a new Cabinet structure with the specified measurements (all in
		meters).
		
		Parameters
		----------
		board_dimensions : (w, h, d)
			Physical board dimensions in meters.
		board_wire_offset_south_west : (x, y, z)
			Physical offset of the South West connector from board left-top-front
			corner in meters. Others are similar.
		inter_board_spacing : float
			Physical spacing between each board in a frame in meters.
		boards_per_frame : int
			Number of boards in each frame.
		frame_dimensions : (w, h, d)
			Frame physical dimensions in meters.
		frame_board_offset : (x, y, z)
			Physical offset of the left-most board from the left-top-front corner of
			a frame in meters.
		inter_frame_spacing : float
			Physical spacing between frames in a cabinet in meters.
		frames_per_cabinet : int
			Number of frames per cabinet.
		cabinet_dimensions : (w, h, d)
			Cabinet physical dimensions in meters.
		cabinet_frame_offset : (x, y, z)
			Physical offset of the top frame from the left-top-front corner of a
			cabinet in meters.
		inter_cabinet_spacing : float
			Physical spacing between each cabinet in meters.
		"""
		c = Cartesian3D
		
		self.board_dimensions = c(*board_dimensions)
		
		# Combine wire offsets into a dictionary
		self.board_wire_offset = {}
		self.board_wire_offset[Direction.south_west] = c(*board_wire_offset_south_west)
		self.board_wire_offset[Direction.north_east] = c(*board_wire_offset_north_east)
		self.board_wire_offset[Direction.east]       = c(*board_wire_offset_east)
		self.board_wire_offset[Direction.west]       = c(*board_wire_offset_west)
		self.board_wire_offset[Direction.north]      = c(*board_wire_offset_north)
		self.board_wire_offset[Direction.south]      = c(*board_wire_offset_south)
		
		self.inter_board_spacing = inter_board_spacing
		
		self.boards_per_frame    = boards_per_frame
		self.frame_dimensions    = c(*frame_dimensions)
		self.frame_board_offset  = c(*frame_board_offset)
		self.inter_frame_spacing = inter_frame_spacing
		
		self.frames_per_cabinet    = frames_per_cabinet
		self.cabinet_dimensions    = c(*cabinet_dimensions)
		self.cabinet_frame_offset  = c(*cabinet_frame_offset)
		self.inter_cabinet_spacing = inter_cabinet_spacing
		
		# Check that all values are positive that are meant to be...
		for field in ["board_dimensions",
		              "inter_board_spacing",
		              "boards_per_frame",
		              "frame_dimensions",
		              "frame_board_offset",
		              "inter_frame_spacing",
		              "frames_per_cabinet",
		              "cabinet_dimensions",
		              "cabinet_frame_offset",
		              "inter_cabinet_spacing"]:
			value = getattr(self, field)
			if isinstance(value, tuple):
				if any(v < 0.0 for v in value):
					raise ValueError("{} must be positive".format(field))
			elif value < 0.0:
				raise ValueError("{} must be positive".format(field))
		
		# Check all board wires are within the bounds of the board
		for direction in [Direction.south_west,
		                  Direction.north_east,
		                  Direction.east,
		                  Direction.west,
		                  Direction.north,
		                  Direction.south]:
			if any(v < 0.0 or v > m for (v, m)
			       in zip(self.board_wire_offset[direction], self.board_dimensions)):
				raise ValueError("{} wire must be within bounds of board".format(
					direction.name))
		
		# Check boards fit in the frame
		if any(v > m for (v, m)
		       in zip((self.frame_board_offset +
		               self.get_dimensions(boards=self.boards_per_frame)),
		              self.frame_dimensions)):
			raise ValueError("boards must be within bounds of a frame")
		
		# Check frames fit in the cabinet
		if any(v > m for (v, m)
		       in zip((self.cabinet_frame_offset +
		               self.get_dimensions(frames=self.frames_per_cabinet)),
		              self.cabinet_dimensions)):
			raise ValueError("frames must be within bounds of a cabinet")
	
	
	def get_position(self, cabinet, frame=None, board=None, wire=None):
		"""
		Get the physical position of a given cabinet, frame, board or wire (i.e. the
		left-top-front corner).
		"""
		
		assert cabinet >= 0
		
		pos = Cartesian3D(0, 0, 0)
		pos += Cartesian3D((self.cabinet_dimensions.x + self.inter_cabinet_spacing) * cabinet, 0, 0)
		
		if frame is None:
			assert board is None and wire is None
			return pos
		
		assert 0 <= frame < self.frames_per_cabinet
		
		pos += self.cabinet_frame_offset
		pos += Cartesian3D(0, (self.frame_dimensions.y + self.inter_frame_spacing) * frame, 0)
		
		if board is None:
			assert wire is None
			return pos
		
		assert 0 <= board < self.boards_per_frame
		
		# Note: boards go right-to-left(!)
		pos += self.frame_board_offset
		pos += Cartesian3D(((self.board_dimensions.x + self.inter_board_spacing) *
		                    (self.boards_per_frame - board - 1)),
		                   0,
		                   0)
		
		if wire is None:
			return pos
		
		pos += self.board_wire_offset[wire]
		
		return pos
	
	
	def get_position_opposite(self, cabinet, frame=None, board=None, wire=None):
		"""
		Get the physical position of the opposite-corner of a given cabinet, frame,
		board or wire (i.e. the right-bottom-back corner).
		"""
		
		pos = self.get_position(cabinet, frame, board, wire)
		
		if frame is None:
			assert board is None and wire is None
			return pos + self.cabinet_dimensions
		
		if board is None:
			assert wire is None
			return pos + self.frame_dimensions
		
		if wire is None:
			# Note: boards grow right-to-left, hence inverted X
			return pos + self.board_dimensions
		
		# Wires have zero size so no adjustment is necessary
		return pos
	
	
	def get_dimensions(self, cabinets=None, frames=None, boards=None):
		"""
		Get the dimensions of the specified number of cabinets, frames or boards.
		"""
		if cabinets is not None:
			assert frames is None and boards is None
			assert cabinets >= 1
			return self.get_position_opposite(cabinets-1) - self.get_position(0)
		
		if frames is not None:
			assert cabinets is None and boards is None
			assert 0 < frames <= self.frames_per_cabinet
			return self.get_position_opposite(0, frames-1) - self.get_position(0, 0)
		
		if boards is not None:  # pragma: no branch
			assert cabinets is None and frames is None
			assert 0 < boards <= self.boards_per_frame
			# Note: boards go in opposite directions
			return self.get_position_opposite(0, 0, 0) - self.get_position(0, 0, boards-1)
		
		assert False, "at least one argument must be given"  # pragma: no cover
