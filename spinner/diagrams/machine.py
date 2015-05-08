#!/usr/bin/env python

"""
A module which generates diagrams (using Cairo) of cabinetised systems.
"""

import cairocffi as cairo

from six import itervalues, integer_types

from spinner.topology import Direction


def normalise_slice(val, max_val):
	"""
	Utility function.
	
	Take a value which may/may-not be a slice and cast into a slice with a
	start and stop value. If an int, produce a singleton slice, if None, produce a
	0-max slice.
	"""
	if val is None:
		return slice(0, max_val)
	elif isinstance(val, integer_types):
		return slice(val, val+1)
	else:
		assert val.step is None
		
		stop = val.stop
		if stop is None:
			stop = max_val
		
		start = val.start
		if start is None:
			start = 0
		
		return slice(start, stop)


class MachineDiagram(object):
	"""
	An object which can be configured to (quickly) generate wiring diagrams of
	large SpiNNaker machines using Cairo.
	"""
	
	# Colours of various components
	#                 R    G    B    A
	CABINET_COLOUR = (0.3, 0.3, 0.3, 1.0)
	FRAME_COLOUR   = (0.7, 0.7, 0.7, 1.0)
	BOARD_COLOUR   = (0.7, 1.0, 0.7, 1.0)
	SOCKET_COLOUR  = (0.5, 0.5, 0.5, 1.0)
	
	def __init__(self, cabinet):
		"""
		cabinet_system is a spinner.cabinet.Cabinet describing the physical parameters
		of the machine in question.
		"""
		self.cabinet = cabinet
		
		# Give up if any connectors are on the back
		if any(c.z != 0.0 for c in itervalues(self.cabinet.board_wire_offset)):
			raise NotImplementedError(
				"Connectors on multiple z-planes not currently supported.")
		
		# Set of wires to draw as a list [ ((c,f,b,d) , (c,f,b,d) , rgba, width),
		# ...] specifying source and destination cabinets, frame, board and
		# directions.
		self.wires = []
		
		# Set of highlight rectangles to draw into the image before wires are added.
		# A list [(x,y, w,h, rgba, width), ...].
		self.highlights = []
	
	
	def add_wire( self
	            , src , dst
	            , rgba = (0.0, 0.0, 0.0, 1.0)
	            , width = 0.002
	            ):
		"""
		Cause the listed wire to be drawn from src and to dst where these arguments
		are (cabinet, frame, board, direction) tuples.
		
		rgba is a tuple (red, green, blue, alpha) specifiying how the wire will
		appear in the image.
		
		width is a tuple specifiying how thick the wire should be drawn (in meters).
		"""
		self.wires.append((src, dst, rgba, width))
	
	
	def add_highlight(self, cabinet, frame=None, board=None, direction=None,
	                  rgba=(1.0,0.0,0.0,1.0), width = 0.01):
		"""
		Highlight a specific cabinet/frame/board/socket.
		"""
		if direction is not None:
			assert frame is not None and board is not None
			x, y, _ = self.cabinet.get_position(cabinet, frame, board, direction)
			w, h = self._socket_dimensions
			x -= w/2.0
			y -= h/2.0
		elif board is not None:
			assert frame is not None
			x, y, _ = self.cabinet.get_position(cabinet, frame, board)
			w, h, _ = self.cabinet.board_dimensions
		elif frame is not None:
			x, y, _ = self.cabinet.get_position(cabinet, frame)
			w, h, _ = self.cabinet.frame_dimensions
		else:
			x, y, _ = self.cabinet.get_position(cabinet)
			w, h, _ = self.cabinet.cabinet_dimensions
	
		self.highlights.append((x,y, w,h, rgba, width))
	
	
	@property
	def _socket_dimensions(self):
		"""
		As a heuristic, draw sockets as rectangles half the width of the board.
		"""
		sw = self.cabinet.board_dimensions.x / 2.0
		sh = sw * 2.0
		
		return (sw, sh)
	
	
	def _draw_board(self, ctx, cabinet_num, frame_num, board_num):
		"""
		Draw a single board. Assumes the top-left corner of the frame to
		draw is at (0,0).
		"""
		# Draw the board
		x, y, _ = self.cabinet.get_position(cabinet_num, frame_num, board_num)
		w, h, _ = self.cabinet.board_dimensions
		
		ctx.save()
		ctx.rectangle(x,y,w,h)
		ctx.set_source_rgba(*self.BOARD_COLOUR)
		ctx.fill()
		ctx.restore()
		
		# Draw the sockets
		ctx.save()
		ctx.set_source_rgba(*self.SOCKET_COLOUR)
		for direction in Direction:
			# Centre position of each socket
			sx, sy, _ = self.cabinet.get_position(cabinet_num, frame_num, board_num,
			                                      direction)
			
			# As a heuristic, draw sockets as rectangles half the width of the board.
			sw, sh = self._socket_dimensions
			sx -= sw/2.0
			sy -= sh/2.0
			
			ctx.rectangle(sx, sy, sw, sh)
			ctx.fill()
		ctx.restore()
		
	
	def _draw_frame(self, ctx, cabinet_num, frame_num, boards=None):
		"""
		Draw the specified frame.
		"""
		x, y, _ = self.cabinet.get_position(cabinet_num, frame_num)
		w, h, _ = self.cabinet.frame_dimensions
		
		ctx.save()
		ctx.rectangle(x,y,w,h)
		ctx.set_source_rgba(*self.FRAME_COLOUR)
		ctx.fill()
		ctx.restore()
		
		boards = normalise_slice(boards, self.cabinet.boards_per_frame)
		for board_num in range(boards.start, boards.stop):
			self._draw_board(ctx, cabinet_num, frame_num, board_num)
	
	
	def _draw_cabinet(self, ctx, cabinet_num, frames=None, boards=None):
		"""
		Draw the specified cabinet.
		"""
		x, y, _ = self.cabinet.get_position(cabinet_num)
		w, h, _ = self.cabinet.cabinet_dimensions
		
		ctx.save()
		ctx.rectangle(x,y,w,h)
		ctx.set_source_rgba(*self.CABINET_COLOUR)
		ctx.fill()
		ctx.restore()
		
		frames = normalise_slice(frames, self.cabinet.frames_per_cabinet)
		for frame_num in range(frames.start, frames.stop):
			self._draw_frame(ctx, cabinet_num, frame_num, boards)
	
	
	def _draw_system(self, ctx, cabinets=None, frames=None, boards=None):
		"""
		Draw every cabinet in the system.
		"""
		cabinets = normalise_slice(cabinets, self.cabinet.num_cabinets)
		for cabinet_num in range(cabinets.start, cabinets.stop):
			self._draw_cabinet(ctx, cabinet_num, frames, boards)
	
	
	def _draw_highlights(self, ctx):
		"""
		Draw any highlight rectangles specified using the highlight_* methods.
		"""
		for x,y, w,h, rgba, width in self.highlights:
			ctx.rectangle(x,y, w,h)
			ctx.set_source_rgba(*rgba)
			ctx.set_line_width(width)
			ctx.stroke()
	
	
	def _draw_wires(self, ctx):
		"""
		Draw all wires in the system specified by add_wire.
		"""
		for src, dst, rgba, width in self.wires:
			ctx.set_line_cap(cairo.LINE_CAP_ROUND)
			ctx.move_to(*self.cabinet.get_position(*src)[:2])
			ctx.line_to(*self.cabinet.get_position(*dst)[:2])
			ctx.set_source_rgba(*rgba)
			ctx.set_line_width(width)
			ctx.stroke()
	
	
	def draw(self, ctx, max_width, max_height,
	         cabinet = None, frame = None, board = None,
	         hide_unfocused=False):
		"""
		Draw the diagram onto the supplied context at the sizes defined. Optionally
		zoom the diagram to a specific cabinet, frame or board.
		
		ctx is a Cairo drawing context onto which the diagram will be drawn
		
		max_width and max_height are the maximum dimensions of the context which
		should be used.
		
		cabinet, frame and board define a desired part of the system to focus on.
		The last to be specified may be an integer or a slice.
		
		hide_unfocused determines whether unfocused boards/frames/cabinets should be
		drawn or not.
		"""
		ctx.save()
		
		# Produce a slice equivalent of each argument which is either the specified
		# slice or a slice which selects everything.
		cabinets = normalise_slice(cabinet, self.cabinet.num_cabinets)
		frames = normalise_slice(frame, self.cabinet.frames_per_cabinet)
		boards = normalise_slice(board, self.cabinet.boards_per_frame)
		
		# Work out the bounding box for the selection specified
		if board is not None:
			assert cabinet is not None and frame is not None
			assert isinstance(cabinet, integer_types)
			assert isinstance(frame, integer_types)
			
			focus_x, focus_y, _ =\
				self.cabinet.get_position(cabinet, frame, boards.stop - 1)
			focus_width, focus_height, _  =\
  			self.cabinet.get_dimensions(boards=boards.stop-boards.start)
		elif frame is not None:
			assert cabinet is not None
			assert isinstance(cabinet, integer_types)
			
			focus_x, focus_y, _ =\
				self.cabinet.get_position(cabinet, frames.start)
			focus_width, focus_height, _  =\
				self.cabinet.get_dimensions(frames=frames.stop-frames.start)
		elif cabinet is not None:
			focus_x, focus_y, _ =\
				self.cabinet.get_position(cabinets.stop-1)
			focus_width, focus_height, _  =\
				self.cabinet.get_dimensions(cabinets=cabinets.stop-cabinets.start)
		else:
			# If nothing specified, show everything
			focus_x, focus_y = 0, 0
			focus_width, focus_height, _ = self.cabinet.get_dimensions()
		
		# Rescale the drawing such that the system fits the space as well as
		# possible
		fit_to_width_scale  = max_width/focus_width
		fit_to_height_scale = max_height/focus_height
		scale = min(fit_to_width_scale, fit_to_height_scale)
		ctx.translate( (max_width  - (focus_width*scale)) / 2
		             , (max_height - (focus_height*scale)) / 2
		             )
		ctx.scale(scale, scale)
		ctx.translate(-focus_x, -focus_y)
		
		# Draw the specified subset of the system
		if hide_unfocused:
			self._draw_system(ctx, cabinets, frames, boards)
		else:
			self._draw_system(ctx)
		
		# Draw the wires
		self._draw_wires(ctx)
		
		# Draw borders around highlighted areas
		self._draw_highlights(ctx)
		
		ctx.restore()
