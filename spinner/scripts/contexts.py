"""Python context managers which deal with the boilerplate for working with
Cairo PNG and PDF surfaces.
"""

import cairocffi as cairo


class PDFContextManager(object):
	"""A context manager which creates a Cairo PDF context."""
	
	# Number of points in a millimetre.
	PT_PER_MM = 2.83464567
	
	def __init__(self, filename, width, height):
		"""Context manager for a PDF context with the specified filename and with
		all units given in mm.
		"""
		self.filename = filename
		self.width = width
		self.height = height
	
	def __enter__(self):
		surface = cairo.PDFSurface(self.filename,
		                           self.width * self.PT_PER_MM,
		                           self.height * self.PT_PER_MM)
		self.ctx = cairo.Context(surface)
		# Make the base unit mm.
		self.ctx.scale(self.PT_PER_MM, self.PT_PER_MM)
		return self.ctx
	
	def __exit__(self, type, value, traceback):
		self.ctx.show_page()


class PNGContextManager(object):
	"""A context manager which creates a Cairo PNG context."""
	
	def __init__(self, filename, width, height):
		"""Context manager for a PDF context with the specified filename and with
		all units given in pixels.
		"""
		self.filename = filename
		self.width = width
		self.height = height
	
	def __enter__(self):
		self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
		                                  self.width,
		                                  self.height)
		ctx = cairo.Context(self.surface)
		return ctx
	
	def __exit__(self, type, value, traceback):
		self.surface.write_to_png(self.filename)


