#!/usr/bin/env python

"""
An object which can provide visual and auditory instructions for wiring
SpiNNaker machines. If called as a program, acts as an interactive wiring guide.
"""

import sys
import colorsys
import subprocess

import pygame
import cairo
import numpy
from PIL import Image

from wiring_plan_generator import generate_wiring_plan, flatten_wiring_plan
from machine_diagram import MachineDiagram

try:
	from spinnman.transceiver import create_transceiver_from_hostname
except ImportError:
	sys.stderr.write("Warning: SpiNNMan not found, LEDs will not be illuminated.")
	create_transceiver_from_hostname = None


class InteractiveWiringGuide(object):
	"""
	An interactive, graphical tool which can guide a user through a predefined
	list of wiring instructions.
	
	After initialisation, calling "main()" will block while the GUI runs.
	
	Features:
	* Cycle through a list of wiring instructions
	* Display a full view of the system being wired up
	* Display close-up views of pairs of boards being connected
	* Illuminate an LED on boards to be connected
	* Read instructions using text-to-speech
	* Colour code diagrams by wire-length
	"""
	
	# TODO: Make this less constrained
	WIDTH  = 1024
	HEIGHT =  706
	
	# Colour of highlights for top-left and bottom-right ends of the current
	# cable.
	TOP_LEFT_COLOUR     = (1.0, 0.0, 0.0, 1.0)
	BOTTOM_RIGHT_COLOUR = (0.0, 0.0, 1.0, 1.0)
	
	# Width of the zoomed-in areas as a fraction of the display width
	ZOOMED_VIEW_WIDTH = 0.25
	
	# Height of each row of text under the drawings.
	TEXT_ROW_HEIGHT = 0.07
	
	# Zoom-out from zoomed in areas by this ratio
	ZOOMED_MARGINS = 0.8
	
	def __init__( self
	            , cabinet_system
	            , socket_names
	            , wire_lengths
	            , wires
	            , starting_wire = 0
	            , bmp_ips = {}
	            , bmp_led = 7
	            , use_tts = True
	            , tts_describe_relative_position = False
	            , show_installed_wires = True
	            , show_future_wires    = False
	            ):
		"""
		cabinet_system defines the size of cabinets in the system.
		
		socket_names is a dictionary {direction: human-name}.
		
		wire_lengths is a dictionary {length: name} listing all valid wire lengths.
		
		wires is a list [(src, dst, length), ...] where src and dst are tuples
		(cabinet, rack, slot, socket) and length is a length included in
		wire_lengths.
		
		starting_wire is the index of the first wire to be inserted. This could be
		used, e.g. to resume installation at a specified point.
		
		bmp_ips is a dictionary {board_position: ip} where board_position is either
		a tuple (cabinet, rack, slot) or (cabinet, rack) where the former will be
		used if both are available. The IP should be given as a string.
		
		bmp_led specifies which LED will be illuminated for boards where an IP is
		known.
		
		use_tts specifies whether text-to-spech will be used to announce
		instructions.
		
		tts_describe_relative_position specifies if the TTS should describe the
		relative position of the connection. Otherwise, only the start and end
		sockets are stated along with the length of cable (if it changes).
		
		show_installed_wires selects whether already-installed wires should be shown
		(feintly) at all times.
		
		show_future_wires selects whether to-be-installed wires should be shown
		(feintly) at all times.
		"""
		
		self.cabinet_system = cabinet_system
		self.socket_names   = socket_names
		self.wire_lengths   = wire_lengths
		self.wires          = wires
		
		self.cur_wire  = starting_wire
		
		self.bmp_ips = bmp_ips
		self.bmp_led = bmp_led
		
		self.use_tts = use_tts
		
		self.tts_describe_relative_position = tts_describe_relative_position
		
		self.show_installed_wires = show_installed_wires
		self.show_future_wires    = show_future_wires
		
		# A reference to any running TTS job
		self.tts_process = None
	
	
	def go_to_wire(self, wire):
		"""
		Advance to a specific wire.
		"""
		last_wire = self.cur_wire
		self.cur_wire = wire
		
		# Update LEDs
		self.set_leds(last_wire, False)
		self.set_leds(self.cur_wire, True)
		
		# Announce via TTS the distance relative to the last position
		if self.use_tts:
			self.tts_delta(last_wire, self.cur_wire)
	
	
	def set_leds(self, wire, state):
		"""
		Set the LEDs for the given wire index to the given state.
		"""
		for c,r,s,p in self.wires[wire][:2]:
			transceiver = create_transceiver_from_hostname(self._get_bmp_ip(c,r,s), discover = False)
			transceiver.set_leds(0,0, s, {self.bmp_led: state})
			transceiver.close()
			del transceiver
	
	
	def _describe_cabinet_change(self, src_cabinet, dst_cabinet):
		"""
		Describe the position of another cabinet with respect to the current
		cabinet. Returns an empty string if the soruce and destination are the same.
		"""
		if src_cabinet == dst_cabinet:
			return ""
		elif 1 <= abs(src_cabinet - dst_cabinet) <= 3:
			# Near-by cabinet
			return "%d cabinet%s to the %s. "%(
				abs(src_cabinet - dst_cabinet),
				"s" if abs(src_cabinet - dst_cabinet) != 1 else "",
				"right" if src_cabinet < dst_cabinet else "left",
			)
		else:
			# Distant cabinet
			return "Cabinet %d. "%(dst_cabinet)
	
	
	def _describe_rack_change(self, src_rack, dst_rack):
		"""
		Describe the position of another rack with respect to the current
		rack. Returns an empty string if the soruce and destination are the same.
		"""
		if src_rack == dst_rack:
			return ""
		elif abs(src_rack - dst_rack) <= 3:
			# Near-by rack
			return "%d rack%s %s. "%(
				abs(src_rack - dst_rack),
				"s" if abs(src_rack - dst_rack) != 1 else "",
				"up" if dst_rack < src_rack else "down",
			)
		else:
			# Distant rack
			return "Rack %d. "%(dst_rack)
	
	
	def _describe_slot_change(self, src_slot, dst_slot):
		"""
		Describe the position of another slot with respect to the current slot.
		Returns an empty string if the soruce and destination are the same.
		"""
		if src_slot == dst_slot:
			return ""
		else:
			# Near-by slot
			return "%d slot%s %s %s. "%(
				abs(src_slot - dst_slot),
				"s" if abs(src_slot - dst_slot) != 1 else "",
				"right" if dst_slot < src_slot else "left",
				"(slot %d)"%dst_slot if abs(src_slot - dst_slot) > 10 else "",
			)
	
	
	def tts_delta(self, last_wire, this_wire):
		"""
		Announce via TTS a brief instruction indicating what the next wire should be
		in terms of the difference to the previous wire.
		
		Changes are announced relative to the destination of the last wire.
		"""
		
		last_length = self.wires[last_wire][2]
		last_tl = self._top_left_socket(last_wire)
		last_br = self._bottom_right_socket(last_wire)
		
		this_length = self.wires[this_wire][2]
		this_tl = self._top_left_socket(this_wire)
		this_br = self._bottom_right_socket(this_wire)
		
		message = ""
		
		# Announce wire-length changes
		if last_length != this_length:
			message += "%s cable. "%(self.wire_lengths[this_length])
		
		# Announce connection
		message += self.socket_names[this_tl[3]]
		if self.tts_describe_relative_position:
			message += self._describe_cabinet_change(last_br[0], this_tl[0])
			message += self._describe_rack_change(last_br[1], this_tl[1])
			message += self._describe_slot_change(last_br[2], this_tl[2])
		
		message += "going "
		
		message += self.socket_names[this_br[3]]
		if self.tts_describe_relative_position:
			message += self._describe_cabinet_change(this_tl[0], this_br[0])
			message += self._describe_rack_change(this_tl[1], this_br[1])
			message += self._describe_slot_change(this_tl[2], this_br[2])
		
		self._tts_speak(message)
	
	
	def tts_describe(self, wire):
		"""
		Announce via TTS a full instruction indicating what the next wire should be
		in terms of the difference to the previous wire.
		"""
		
		# TODO
		pass
	
	
	def _tts_speak(self, text, wpm = 250):
		"""
		Speak the supplied string, interrupting whatever was already being said.
		Non-blocking.
		"""
		# Kill previous instances
		if self.tts_process is not None and self.tts_process.poll() is None:
			self.tts_process.terminate()
		
		# Speak the required text.
		self.tts_process = subprocess.Popen( ["espeak", "-s", str(wpm), text]
		                                   , stdout = subprocess.PIPE
		                                   , stderr = subprocess.PIPE
		                                   )
	
	
	def _get_bmp_ip(self, cabinet, rack, slot = None):
		"""
		Get the IP of the requested board (if known). Returns either the IP as a
		string or None.
		"""
		
		return self.bmp_ips.get( (cabinet,rack,slot)
		                       , self.bmp_ips.get((cabinet,rack), None)
		                       )
	
	
	def _get_wire_colour(self, length):
		"""
		Get the RGB colour (as a tuple) for wires of the specified length.
		
		Colours are allocated evenly across the spectrum.
		"""
		index = sorted(self.wire_lengths.keys()).index(length)
		
		hue = index / float(len(self.wire_lengths))
		
		return colorsys.hsv_to_rgb(hue, 1.0, 0.5)
	
	
	def _top_left_socket(self, wire):
		"""
		Return the (c,r,s,d) for the top-left socket for the current wire.
		"""
		
		src, dst, length = self.wires[wire]
		
		if src[0] == dst[0] and src[1] == dst[1]:
			return dst if src[2] < dst[2] else src
		elif src[0] == dst[0]:
			return src if src[1] < dst[1] else dst
		else:
			return dst if src[0] < dst[0] else src
	
	
	def _bottom_right_socket(self, wire):
		"""
		Return the (c,r,s,d) for the bottom-right socket for the current wire.
		"""
		
		src, dst, length = self.wires[wire]
		
		if src[0] == dst[0] and src[1] == dst[1]:
			return src if src[2] < dst[2] else dst
		elif src[0] == dst[0]:
			return dst if src[1] < dst[1] else src
		else:
			return src if src[0] < dst[0] else dst
	
	
	def _get_machine_diagram(self):
		"""
		Get the MachineDiagram ready to draw the system's current state.
		"""
		md = MachineDiagram(self.cabinet_system)
		
		# Wires already installed
		if self.show_installed_wires:
			for src, dst, length in self.wires[:self.cur_wire]:
				r,g,b = self._get_wire_colour(length)
				md.add_wire(src, dst, rgba = (r,g,b,0.5), width = 0.005)
		
		# Wires still to be installed
		if self.show_future_wires:
			for src, dst, length in self.wires[self.cur_wire+1:]:
				r,g,b = self._get_wire_colour(length)
				md.add_wire(src, dst, rgba = (r,g,b,0.5), width = 0.005)
		
		# Current wire (with a white outline)
		src, dst, length = self.wires[self.cur_wire]
		r,g,b = self._get_wire_colour(length)
		md.add_wire(src, dst, rgba = (1.0,1.0,1.0,1.0), width = 0.020)
		md.add_wire(src, dst, rgba = (r,g,b,1.0),       width = 0.010)
		
		# Highlight source and destination
		c,r,s,d = self._top_left_socket(self.cur_wire)
		md.highlight_socket(c,r,s,d, rgba = self.TOP_LEFT_COLOUR)
		md.highlight_slot(  c,r,s,   rgba = self.TOP_LEFT_COLOUR)
		c,r,s,d = self._bottom_right_socket(self.cur_wire)
		md.highlight_socket(c,r,s,d, rgba = self.BOTTOM_RIGHT_COLOUR)
		md.highlight_slot(  c,r,s,   rgba = self.BOTTOM_RIGHT_COLOUR)
		
		return md
	
	
	def _draw_text(self, ctx, text, size, rgba = (0.0,0.0,0.0, 1.0)):
		"""
		Draw the desired text centered below (0,0).
		"""
		ctx.save()
		
		ctx.select_font_face("Sans")
		ctx.set_source_rgba(*rgba)
		ctx.set_font_size(size*0.8)
		x,y, w,h, _w,_h = ctx.text_extents(text)
		ctx.move_to(-x - w/2, -y + size*0.1)
		ctx.show_text(text)
		
		ctx.restore()
		
	
	
	def _draw_gui(self, screen, gui_buffer, width, height):
		"""
		Re-draw the whole GUI and flip the display buffer
		"""
		
		# Create the Cairo surface on which the GUI will be drawn
		cairo_surface = cairo.ImageSurface.create_for_data(
			gui_buffer, cairo.FORMAT_ARGB32,
			width, height,
			width * 4,
		)
		
		# Draw with Cairo on the surface
		ctx = cairo.Context(cairo_surface)
		
		# Clear the buffer background
		ctx.set_source_rgba(1.0,1.0,1.0,1.0);
		ctx.rectangle(0,0, width, height)
		ctx.fill()
		
		md = self._get_machine_diagram()
		
		# Draw the main overview image
		ctx.save()
		ctx.translate(width*self.ZOOMED_VIEW_WIDTH, 0.0)
		md.draw( ctx
		       , width * (1.0 - (2*self.ZOOMED_VIEW_WIDTH))
		       , height * (1 - (2*self.TEXT_ROW_HEIGHT))
		       )
		ctx.restore()
		
		
		# Draw the left zoomed-in image
		ctx.save()
		ctx.rectangle(0,0, width*self.ZOOMED_VIEW_WIDTH, height*(1-(2*self.TEXT_ROW_HEIGHT)))
		ctx.clip()
		ctx.translate( width*self.ZOOMED_VIEW_WIDTH*(1-self.ZOOMED_MARGINS)/2
		             , height*(1-(2*self.TEXT_ROW_HEIGHT))*(1-self.ZOOMED_MARGINS)/2
		             )
		ctx.scale(self.ZOOMED_MARGINS, self.ZOOMED_MARGINS)
		md.draw( ctx
		       , width*self.ZOOMED_VIEW_WIDTH
		       , height*(1 - (2*self.TEXT_ROW_HEIGHT))
		       , *self._top_left_socket(self.cur_wire)[:3]
		       )
		ctx.restore()
		
		# Draw the right zoomed-in image
		ctx.save()
		ctx.translate(width*(1-self.ZOOMED_VIEW_WIDTH), 0.0)
		ctx.rectangle(0,0, width*self.ZOOMED_VIEW_WIDTH, height*(1-(2*self.TEXT_ROW_HEIGHT)))
		ctx.clip()
		ctx.translate( width*self.ZOOMED_VIEW_WIDTH*(1-self.ZOOMED_MARGINS)/2
		             , height*(1-(2*self.TEXT_ROW_HEIGHT))*(1-self.ZOOMED_MARGINS)/2
		             )
		ctx.scale(self.ZOOMED_MARGINS, self.ZOOMED_MARGINS)
		md.draw( ctx
		       , width*self.ZOOMED_VIEW_WIDTH
		       , height*(1 - (2*self.TEXT_ROW_HEIGHT))
		       , *self._bottom_right_socket(self.cur_wire)[:3]
		       )
		ctx.restore()
		
		# Draw the wire length
		ctx.save()
		ctx.translate(width/2, height*(1 - (2*self.TEXT_ROW_HEIGHT)))
		length = self.wires[self.cur_wire][2]
		self._draw_text( ctx
		               , "%s (%0.2fm)"%(self.wire_lengths[length], length)
		               , height*self.TEXT_ROW_HEIGHT
		               , rgba = self._get_wire_colour(length)
		               )
		
		# Draw the progress
		ctx.translate(0, height*self.TEXT_ROW_HEIGHT)
		self._draw_text( ctx
		               , "%d of %d (%0.1f%%)"%( self.cur_wire + 1
		                                      , len(self.wires)
		                                      , 100.0*((self.cur_wire+1)/float(len(self.wires)))
		                                      )
		               , height*self.TEXT_ROW_HEIGHT
		               )
		ctx.restore()
		
		# Draw the endpoint specifications
		for x_offset, (c,r,s,d) in [ (width * (self.ZOOMED_VIEW_WIDTH/2),     self._top_left_socket(self.cur_wire))
		                           , (width * (1-(self.ZOOMED_VIEW_WIDTH/2)), self._bottom_right_socket(self.cur_wire))
		                           ]:
			ctx.save()
			ctx.translate(x_offset, 0.0)
			
			# Socket number
			ctx.translate(0, height*(1 - (2*self.TEXT_ROW_HEIGHT)))
			self._draw_text( ctx
			               , self.socket_names[d]
			               , height*self.TEXT_ROW_HEIGHT
			               )
			
			# Draw the progress
			ctx.translate(0, height*self.TEXT_ROW_HEIGHT)
			self._draw_text( ctx
			               , "C%d R%d S%02d"%(c,r,s)
			               , height*self.TEXT_ROW_HEIGHT
			               )
			ctx.restore()
		
		# Convert the Cairo surface into a PyGame compatible data block
		img = Image.frombuffer('RGBA'
		                      , ( cairo_surface.get_width()
		                        , cairo_surface.get_height()
		                        )
		                      , cairo_surface.get_data()
		                      , 'raw', 'BGRA', 0, 1
		                      )
		data_string = img.tostring('raw', 'RGBA', 0, 1)
		
		# Create PyGame surface from the converted Cairo surface
		pygame_surface = pygame.image.frombuffer(data_string, (width, height), 'RGBA')
		 
		# Show the image on the PyGame display surface
		screen.fill((255,255,255))
		screen.blit(pygame_surface, (0,0))
		pygame.display.flip()
		
		del cairo_surface, ctx, img, data_string
	
	
	def _on_key_press(self, event):
		"""
		Event-handler for key-presses. Returns a boolean stating whether a redraw is
		required.
		"""
		
		# Advance to the next wire
		if event.key in (  32 # Space
		                , 274 # Down
		                , 275 # Right
		                ,  13 # Return
		                ,   9 # Tab
		                ):
			self.go_to_wire((self.cur_wire + 1) % len(self.wires))
			return True
		
		# Go back to the previous wire
		elif event.key in ( 273 # Down
		                  , 276 # Left
		                  ):
			self.go_to_wire((self.cur_wire - 1) % len(self.wires))
			return True
		
		# Go back to the first wire
		elif event.key == 278: # Home
			self.go_to_wire(0)
			return True
		
		# Go to the last wire
		elif event.key == 279: # End
			self.go_to_wire(len(self.wires)-1)
			return True
		
		# Advance rapidly through the wires
		elif event.key == 281: # Page-down
			self.go_to_wire((self.cur_wire + 25) % len(self.wires))
			return True
		
		# Go back rapidly through the wires
		elif event.key == 280: # Page-up
			self.go_to_wire((self.cur_wire - 25) % len(self.wires))
			return True
		
		# Toggle text-to-speech
		elif event.key == 115: # s
			self.use_tts = not self.use_tts
			if self.use_tts:
				self._tts_speak("Text to speech enabled.")
			else:
				self._tts_speak("Text to speech disabled.")
			return True
		
		# Do nothing by default
		return False
	
	
	def _on_mouse_click(self, event):
		"""
		Event-handler for mouse clicks. Returns a boolean stating whether a redraw
		is required.
		"""
		# Advance
		if event.button in ( 1 # Left
		                   , 5 # Scroll-down
		                   ):
			self.go_to_wire((self.cur_wire + 1) % len(self.wires))
			return True
		
		# Retreat
		elif event.button in ( 3 # Right
		                     , 4 # Scroll-up
		                     ):
			self.go_to_wire((self.cur_wire - 1) % len(self.wires))
			return True
		
		# Read-out
		elif event.button == 2: # Middle
			self.tts_describe(self.cur_wire)
			return False
		
		# Do nothing by default
		return False
	
	
	def main(self):
		"""
		Main loop.
		"""
		width, height = self.WIDTH, self.HEIGHT
		
		pygame_depth = 32
		pygame_flags = pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE
		
		pygame.display.init()
		pygame.display.set_caption("SpiNNer Interactive Wiring Guide")
		
		screen = pygame.display.set_mode((width, height), pygame_flags, pygame_depth)
		
		pygame.key.set_repeat(250, 50)
		
		# Create raw buffer for surface data.
		gui_buffer = numpy.empty(width * height * 4, dtype=numpy.int8)
		
		# Flag indicating that a redraw is required
		redraw = True
		
		# Illuminate the current wire
		self.set_leds(self.cur_wire, True)
		
		# Run until the window is closed
		while True:
			# Handle PyGame callbacks
			pygame.event.pump()
			
			# Handle events
			event = pygame.event.wait()
			if event.type == pygame.QUIT:
				pygame.display.quit()
				break
			elif event.type == pygame.VIDEORESIZE:
				# Re-initialise when window changes size
				width, height = event.dict['size']
				if width > 10 and height > 10:
					screen = pygame.display.set_mode((width, height), pygame_flags, pygame_depth)
					del gui_buffer
					gui_buffer = numpy.empty(width * height * 4, dtype=numpy.int8)
					redraw = True
			elif event.type == pygame.KEYDOWN:
				redraw |= self._on_key_press(event)
			elif event.type == pygame.MOUSEBUTTONDOWN:
				redraw |= self._on_mouse_click(event)
			
			if redraw:
				self._draw_gui(screen, gui_buffer, width, height)
				redraw = False
		
		# Turn off the LEDs before exit
		self.set_leds(self.cur_wire, False)


if __name__=="__main__":
	import sys
	
	from model_builder import build_model
	from param_parser import parse_params
	
	################################################################################
	# Parse command-line arguments
	################################################################################
	
	param_file = sys.argv[1]
	
	################################################################################
	# Load Parameters
	################################################################################
	params = parse_params(["machine_params/universal.param", param_file])
	
	title                          = params["title"]
	
	diagram_scaling                = params["diagram_scaling"]
	cabinet_diagram_scaling_factor = params["cabinet_diagram_scaling_factor"]
	show_wiring_metrics            = params["show_wiring_metrics"]
	show_topology_metrics          = params["show_topology_metrics"]
	show_development               = params["show_development"]
	show_board_position_list       = params["show_board_position_list"]
	show_wiring_instructions       = params["show_wiring_instructions"]
	wire_length_histogram_bins     = params["wire_length_histogram_bins"]
	
	slot_width                     = params["slot_width"]
	slot_height                    = params["slot_height"]
	slot_depth                     = params["slot_depth"]
	
	rack_width                     = params["rack_width"]
	rack_height                    = params["rack_height"]
	rack_depth                     = params["rack_depth"]
	
	cabinet_width                  = params["cabinet_width"]
	cabinet_height                 = params["cabinet_height"]
	cabinet_depth                  = params["cabinet_depth"]
	
	wire_positions                 = params["wire_positions"]
	socket_names                   = params["socket_names"]
	
	slot_spacing                   = params["slot_spacing"]
	slot_offset                    = params["slot_offset"]
	num_slots_per_rack             = params["num_slots_per_rack"]
	rack_spacing                   = params["rack_spacing"]
	rack_offset                    = params["rack_offset"]
	
	num_racks_per_cabinet          = params["num_racks_per_cabinet"]
	cabinet_spacing                = params["cabinet_spacing"]
	num_cabinets                   = params["num_cabinets"]
	
	width                          = params["width"]
	height                         = params["height"]
	num_folds_x                    = params["num_folds_x"]
	num_folds_y                    = params["num_folds_y"]
	compress_rows                  = params["compress_rows"]
	
	minimum_arc_height             = params["minimum_arc_height"]
	available_wires                = params["available_wires"]
	
	
	################################################################################
	# Generate models
	################################################################################
	
	# Fold the system
	( torus
	, cart_torus
	, rect_torus
	, comp_torus
	, fold_spaced_torus
	, folded_cabinet_spaced_torus
	, cabinet_torus
	, phys_torus
	, cabinet_system
	) = build_model( slot_width,    slot_height,    slot_depth
	               , rack_width,    rack_height,    rack_depth
	               , cabinet_width, cabinet_height, cabinet_depth
	               , wire_positions
	               , slot_spacing, slot_offset, num_slots_per_rack
	               , rack_spacing, rack_offset, num_racks_per_cabinet
	               , cabinet_spacing, num_cabinets
	               , width, height
	               , num_folds_x, num_folds_y
	               , compress_rows
	               )
	
	# Plan the wiring
	( wires_between_slots
	, wires_between_racks
	, wires_between_cabinets
	) = generate_wiring_plan( cabinet_torus
	                        , phys_torus
	                        , wire_positions
	                        , available_wires
	                        , minimum_arc_height
	                        )
	
	# Flatten the instructions
	wires_ = flatten_wiring_plan( wires_between_slots
	                            , wires_between_racks
	                            , wires_between_cabinets
	                            , wire_positions
	                            )
	
	# Assemble a list of wires in terms of slot positions (rather than Board
	# objects).
	b2p = dict(cabinet_torus)
	wires = []
	for (src_board, src_direction), (dst_board, dst_direction), wire_length in wires_:
		src = list(b2p[src_board]) + [src_direction]
		dst = list(b2p[dst_board]) + [dst_direction]
		wires.append((src, dst, wire_length))
	
	################################################################################
	# Initialise and start UI
	################################################################################
	
	iwg = InteractiveWiringGuide( cabinet_system       = cabinet_system
	                            , socket_names         = socket_names
	                            , wire_lengths         = available_wires
	                            , wires                = wires
	                            , starting_wire        = 0
	                            , bmp_ips              = {(0,0):"192.168.3.0"}
	                            , bmp_led              = 7
	                            , use_tts              = True
	                            , tts_describe_relative_position = False
	                            , show_installed_wires = True
	                            , show_future_wires    = False
	                            )
	iwg.main()
