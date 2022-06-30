"""An interactive, graphical tool which can guide a user through a predefined
list of wiring instructions."""

import colorsys

import subprocess

import traceback

from itertools import cycle

from six import iteritems, itervalues, next

import cairocffi as cairo

from math import pi

try:  # pragma: no cover
    # Python 3
    from tkinter import Tk, Label
except ImportError:  # pragma: no cover
    # Python 2
    from Tkinter import Tk, Label

from PIL import Image, ImageTk

from spinner.topology import Direction

from spinner.diagrams.machine import MachineDiagram


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

    # Poll interval in ms between checking the if the current wire has been
    # inserted or not.
    POLL_INTERVAL_MS = 500

    def __init__( self
                , cabinet
                , wire_lengths
                , wires
                , starting_wire=0
                , focus=[]
                , bmp_controller=None
                , bmp_led=7
                , wiring_probe=None
                , auto_advance=True
                , use_tts=True
                , show_installed_wires=True
                , show_future_wires=False
                , timing_logger=None
                ):
        """
        cabinet defines the size of cabinets in the system.

        wire_lengths is a list of all valid wire lengths.

        wires is a list [(src, dst, length), ...] where src and dst are tuples
        (cabinet, rack, slot, socket) and length is a length included in
        wire_lengths or is None indicating that the wire should be disconnected.

        starting_wire is the index of the first wire to be inserted. This could be
        used, e.g. to resume installation at a specified point.

        focus is a set of arguments (cabinet, frame, board) to use to select the
        area of interest for the central system diagram.

        bmp_ips is a dictionary {board_position: ip} where board_position is either
        a tuple (cabinet, rack, slot) or (cabinet, rack) where the former will be
        used if both are available. The IP should be given as a string.

        bmp_led specifies which LED will be illuminated for boards where an IP is
        known.

        wiring_probe is an optional WiringProbe object which will be used to
        auto-advance through the wiring when wires are inserted correctly.

        auto_advance specifies whether auto-advance will be enabled initially.

        use_tts specifies whether text-to-spech will be used to announce
        instructions.

        show_installed_wires selects whether already-installed wires should be shown
        (feintly) at all times.

        show_future_wires selects whether to-be-installed wires should be shown
        (feintly) at all times.

        timing_logger is a TimingLogger into which the cabling connections made
        will be logged. If None, no timings are logged.
        """

        self.cabinet      = cabinet
        self.wire_lengths = wire_lengths
        self.wires        = wires

        self.cur_wire  = starting_wire
        assert 0 <= self.cur_wire < len(self.wires), "Starting wire out of range."

        self.focus = focus

        self.bmp_controller = bmp_controller

        self.bmp_led = bmp_led

        self.wiring_probe = wiring_probe

        self.auto_advance = auto_advance

        self.use_tts = use_tts

        self.show_installed_wires = show_installed_wires
        self.show_future_wires    = show_future_wires

        self.timing_logger = timing_logger

        # Human readable names for each socket
        self.socket_names = {d: d.name.replace("_", " ") for d in Direction}

        # An infinately cycling iterator over all the boards in the machine.
        self.board_iter = iter(cycle(set((c, f, b)
                                         for ((c, f, b, _1), _2, _3)
                                         in self.wires)))

        # A reference to any running TTS job
        self.tts_process = None

        # A dict {fn: ([key, ...], description), ...} giving the keybindings and
        # homan-readable help string for all bound keyboard shortcuts.
        self.bindings = {}

        # Set up the Tk UI
        self.tk = Tk()
        self._init_ui()

        # Get started
        if self.timing_logger is not None:
            self.timing_logger.logging_started()
        self.go_to_wire(starting_wire)


    def _init_ui(self):
        """Initialise the Tk interface."""
        self.tk.wm_title("SpiNNer Interactive Wiring Guide")
        self.tk.geometry("1024x768")

        # Add a label widget into which the rendered UI is drawn
        self.widget = Label()
        self.widget.pack(expand=True, fill="both")

        # Used to avoid unecessary redraws on window resizes where nothing actually
        # changes.
        self._old_size = (None, None)

        # A flag which indicates whether, on the last poll of cable insertion, the
        # cable was found to be inserted but inserted into the wrong socket.
        self.connected_incorrectly = False

        # Set up a timer to poll for cable insertion
        self.tk.after(InteractiveWiringGuide.POLL_INTERVAL_MS, self._poll_wiring_probe)

        # Handle window events
        self.tk.bind("<Configure>", self._on_resize)  # Resize
        self.tk.protocol("WM_DELETE_WINDOW", self._on_close)  # Window closed

        # Setup key bindings
        self.bindings = {
            self._on_next:
                (["<Button-1>", "<Key-space>", "<Key-Down>", "<Key-Right>",
                  "<Key-Return>", "<Key-Tab>"],
                 "Next wire"),
            self._on_prev:
                (["<Button-3>", "<Key-Up>", "<Key-Left>", "<Key-BackSpace>"],
                 "Previous wire"),
            self._on_skip_next: (["<Key-Next>"], "Skip forward"),
            self._on_skip_prev: (["<Key-Prior>"], "Skip backward"),
            self._on_first: (["<Key-Home>"], "First wire"),
            self._on_last: (["<Key-End>"], "Last wire"),
            self._on_tts_toggle: (["<Key-t>"], "Toggle speech"),
        }

        if self.wiring_probe is not None:  # pragma: no branch
            self.bindings[self._on_auto_advance_toggle] = (
                ["<Key-a>"], "Toggle auto-advance")

        if self.timing_logger is not None: # pragma: no branch
            self.bindings[self._on_pause] = (["<Key-p>"], "Pause")

        for fn, (keys, help) in iteritems(self.bindings):
            for key in keys:
                self.tk.bind(key, fn)


    def go_to_wire(self, wire):
        """
        Advance to a specific wire.
        """
        last_wire = self.cur_wire
        self.cur_wire = wire

        # Reset the incorrect connection flag
        self.connected_incorrectly = False

        # Update LEDs
        self.set_leds(last_wire, False)
        self.set_leds(self.cur_wire, True)

        # Log the start of *insertion* of a new wire
        src, dst, length = self.wires[wire]
        if self.timing_logger is not None:
            self.timing_logger.unpause()
            if length is not None:
                sc, sf, sb, sd = self.wires[wire][0]
                dc, df, db, dd = self.wires[wire][1]
                self.timing_logger.connection_started(sc, sf, sb, sd,
                                                      dc, df, db, dd)

        # Announce via TTS the distance relative to the last position
        if self.use_tts:
            self.tts_delta(last_wire, self.cur_wire)


    def set_leds(self, wire, state):
        """
        Set the LEDs for the given wire index to the given state (assuming the
        board's IP is known).
        """
        try:
            if self.bmp_controller is not None:
                for c,f,b,p in self.wires[wire][:2]:
                    self.bmp_controller.set_led(self.bmp_led, state, c, f, b)
        except:
            # Quit if this goes wrong
            self.tk.destroy()
            raise


    def tts_delta(self, last_wire, this_wire):
        """
        Announce via TTS a brief instruction indicating what the next wire should be
        in terms of the difference to the previous wire.

        Changes are announced relative to the last wire.
        """
        message = ""

        # Announce wire-length changes
        last_length = self.wires[last_wire][2]
        this_length = self.wires[this_wire][2]

        if last_length != this_length:
            if this_length is None:
                message += "Disconnect cable. "
            else:
                message += "%s meter cable. "%(("%0.2f"%this_length).rstrip(".0"))

        # Announce which ports are being connected
        this_tl = self._top_left_socket(this_wire)
        this_br = self._bottom_right_socket(this_wire)

        message += self.socket_names[this_tl[3]]
        message += " going "
        message += self.socket_names[this_br[3]]
        message += "."

        self._tts_speak(message)


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


    def _get_wire_colour(self, length):
        """
        Get the RGB colour (as a tuple) for wires of the specified length.

        Colours are allocated evenly across the spectrum. Wires to be removed are
        shown in black.
        """
        if length is None:
            return (0.0, 0.0, 0.0)

        index = sorted(self.wire_lengths).index(length)

        hue = index / float(len(self.wire_lengths))

        return colorsys.hsv_to_rgb(hue, 1.0, 0.5)


    def _top_left_socket(self, wire):
        """
        Return the (c,r,s,d) for the top-left socket for the current wire.
        """

        src, dst, length = self.wires[wire]

        return min([src, dst], key=(lambda v: (-v[0],  # Right-to-left
                                               +v[1],  # Top-to-bottom
                                               -v[2])))  # Right-to-left


    def _bottom_right_socket(self, wire):
        """
        Return the (c,r,s,d) for the bottom-right socket for the current wire.
        """

        src, dst, length = self.wires[wire]

        return max([src, dst], key=(lambda v: (-v[0],  # Right-to-left
                                               +v[1],  # Top-to-bottom
                                               -v[2])))  # Right-to-left


    def _get_machine_diagram(self):
        """
        Get the MachineDiagram ready to draw the system's current state.
        """
        md = MachineDiagram(self.cabinet)

        bg_wire = self.cabinet.board_dimensions.x / 5.0
        fg_wire = self.cabinet.board_dimensions.x / 3.0

        board_hl = self.cabinet.board_dimensions.x / 3.0
        wire_hl = self.cabinet.board_dimensions.x / 2.0

        # Wires already installed
        if self.show_installed_wires:
            for src, dst, length in self.wires[:self.cur_wire]:
                r,g,b = self._get_wire_colour(length)
                md.add_wire(src, dst, rgba = (r,g,b,0.5), width = bg_wire)

        # Wires still to be installed
        if self.show_future_wires:
            for src, dst, length in self.wires[self.cur_wire+1:]:
                r,g,b = self._get_wire_colour(length)
                md.add_wire(src, dst, rgba = (r,g,b,0.5), width = bg_wire)

        # Current wire (with a white outline)
        src, dst, length = self.wires[self.cur_wire]
        r,g,b = self._get_wire_colour(length)
        md.add_wire(src, dst, rgba = (1.0,1.0,1.0,1.0), width = fg_wire * 2)
        md.add_wire(src, dst, rgba = (r,g,b,1.0),       width = fg_wire)

        # Highlight source and destination
        c,r,s,d = self._top_left_socket(self.cur_wire)
        md.add_highlight(c,r,s,d, rgba = self.TOP_LEFT_COLOUR, width=wire_hl)
        md.add_highlight(c,r,s,   rgba = self.TOP_LEFT_COLOUR, width=board_hl)
        c,r,s,d = self._bottom_right_socket(self.cur_wire)
        md.add_highlight(c,r,s,d, rgba = self.BOTTOM_RIGHT_COLOUR, width=wire_hl)
        md.add_highlight(c,r,s,   rgba = self.BOTTOM_RIGHT_COLOUR, width=board_hl)

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


    def _draw_help_text(self, ctx, width, height, rgba = (0.5,0.5,0.5, 1.0)):
        """
        Draw the help text along the bottom of the screen, return the height of the
        text in pixels.
        """
        # Generate help string
        help_text = "  |  ".join("{} {}".format(keys[0], help)
                                 for keys, help in
                                 sorted(itervalues(self.bindings),
                                        key=(lambda kh: kh[0])))

        ctx.save()

        # Determine font size which will fill the width of the screen
        ctx.select_font_face("Sans")
        ctx.set_source_rgba(*rgba)
        ctx.set_font_size(1.0)
        x,y, w,h, _w,_h = ctx.text_extents(help_text)
        scale_factor = (width * 0.95) / w

        # Draw the text along the bottom of the screen
        ctx.set_font_size(scale_factor)
        x,y, w,h, _w,_h = ctx.text_extents(help_text)
        ctx.move_to(x + ((width - w) / 2), height + y)
        ctx.show_text(help_text)

        ctx.restore()

        return h


    def _render_gui(self, ctx, width, height):
        """
        Re-draw the whole GUI into the supplied Cairo context.
        """
        # Clear the buffer background
        ctx.set_source_rgba(1.0,1.0,1.0,1.0);
        ctx.rectangle(0,0, width, height)
        ctx.fill()

        # Draw help text along bottom of screen.
        height -= self._draw_help_text(ctx, width, height)

        md = self._get_machine_diagram()

        # Draw the main overview image
        ctx.save()
        ctx.translate(width*self.ZOOMED_VIEW_WIDTH, 0.0)
        ctx.rectangle(0,0, width * (1.0 - (2*self.ZOOMED_VIEW_WIDTH)), height * (1 - (2*self.TEXT_ROW_HEIGHT)))
        ctx.clip()
        md.draw( ctx
               , width * (1.0 - (2*self.ZOOMED_VIEW_WIDTH))
               , height * (1 - (2*self.TEXT_ROW_HEIGHT))
               , *((list(self.focus) + [None]*3)[:3] * 2)
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
               , *(list(self._top_left_socket(self.cur_wire)[:3]) +
                   list(self.focus))
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
               , *(list(self._bottom_right_socket(self.cur_wire)[:3]) +
                   list(self.focus))
               )
        ctx.restore()

        # Draw the wire length
        ctx.save()
        ctx.translate(width/2, height*(1 - (2*self.TEXT_ROW_HEIGHT)))
        length = self.wires[self.cur_wire][2]
        self._draw_text( ctx
                       , "%0.2f m"%(length)
                         if length is not None
                         else "Disconnect Wire"
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
                           , "C%d F%d B%02d"%(c,r,s)
                           , height*self.TEXT_ROW_HEIGHT
                           )
            ctx.restore()

        # Draw a full-screen "paused" indicator, if paused
        if self.timing_logger is not None and self.timing_logger.paused:
            ctx.save()

            ctx.translate(width / 2.0, height / 2.0)
            scale = min(width, height) * 0.4
            ctx.scale(scale, scale)

            ctx.move_to(0, 0)
            ctx.new_sub_path()
            ctx.arc(0, 0, 1.0, 0.0, 2.0 * pi)
            ctx.set_source_rgba(0.0,0.0,0.0,0.8);
            ctx.fill_preserve()
            ctx.set_source_rgba(0.0,0.0,0.0,1.0);
            ctx.set_line_width(0.1)
            ctx.stroke()

            ctx.move_to(-0.25, -0.5);
            ctx.rel_line_to(0.0, 1.0);
            ctx.move_to(0.25, -0.5);
            ctx.rel_line_to(0.0, 1.0);
            ctx.set_source_rgba(0.7,0.7,0.7,1.0);
            ctx.set_line_width(0.2)
            ctx.stroke()

            ctx.restore()


    def _redraw(self):
        """Redraw the GUI and display it on the screen."""

        # Get a new context to draw the GUI into
        height = self.tk.winfo_height()
        width = self.tk.winfo_width()

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        # Render it
        self._render_gui(ctx, width, height)

        # Draw onto the window (note: a reference to the image is kept to keep it
        # safe from garbage collection)
        self.widget.image = ImageTk.PhotoImage(Image.frombuffer(
            "RGBA", (width, height), surface.get_data(), "raw", "BGRA", 0, 1))
        self.widget.configure(image=self.widget.image)
        self.widget.pack(expand=True, fill="both")


    def _poll_wiring_probe(self):
        """Poll the machine's hardware to determine if the wiring is complete.
        """
        try:
            # Check wiring conncectivity
            if self.wiring_probe is not None and self.auto_advance:
                src, dst, length = self.wires[self.cur_wire]

                # Check both ends of the cable
                actual_dst = self.wiring_probe.get_link_target(*src)
                actual_src = self.wiring_probe.get_link_target(*dst)

                advance = False

                if length is None:
                    # We're waiting for the wire to be disconnected
                    if actual_src is None and actual_dst is None:
                        # Disconnected! Advance to the next wire!
                        advance = True
                else:
                    # We're waiting for a wire to be connected
                    if actual_src == src and actual_dst == dst:
                        # Connected correctly! Advance to the next wire!
                        advance = True
                        if self.timing_logger is not None:
                            self.timing_logger.unpause()
                            self.timing_logger.connection_complete()
                    elif actual_dst is not None or actual_src is not None:
                        # The wire was connected, but was connected incorrectly!
                        if not self.connected_incorrectly:
                            self._tts_speak("Wire inserted incorrectly.")
                            if self.timing_logger is not None:
                                self.timing_logger.unpause()
                                self.timing_logger.connection_error()
                        self.connected_incorrectly = True
                    else:
                        # No wire is connected
                        self.connected_incorrectly = False

                # Actually advance, as required
                if advance and self.cur_wire != len(self.wires) - 1:
                    self.go_to_wire(self.cur_wire + 1)
                    self._redraw()
        except:
            # Fail gracefully...
            print(traceback.format_exc())

        # Schedule next poll
        self.tk.after(InteractiveWiringGuide.POLL_INTERVAL_MS, self._poll_wiring_probe)


    def _on_next(self, event):
        """Advance to the next wire."""
        self.go_to_wire((self.cur_wire + 1) % len(self.wires))
        self._redraw()


    def _on_prev(self, event):
        """Retreat to the previous wire."""
        self.go_to_wire((self.cur_wire - 1) % len(self.wires))
        self._redraw()


    def _on_first(self, event):
        """Go back to the first wire."""
        self.go_to_wire(0)
        self._redraw()


    def _on_last(self, event):
        """Go to the last first wire."""
        self.go_to_wire(len(self.wires)-1)
        self._redraw()


    def _on_skip_next(self, event):
        """Advance rapidly forward through the wires."""
        self.go_to_wire((self.cur_wire + 25) % len(self.wires))
        self._redraw()


    def _on_skip_prev(self, event):
        """Retreat rapidly backward through the wires."""
        self.go_to_wire((self.cur_wire - 25) % len(self.wires))
        self._redraw()


    def _on_tts_toggle(self, event):
        """Toggle whether Text-to-Speech is enabled."""
        self.use_tts = not self.use_tts
        if self.use_tts:
            self._tts_speak("Text to speech enabled.")
        else:
            self._tts_speak("Text to speech disabled.")


    def _on_auto_advance_toggle(self, event):
        """Toggle whether auto-advance is enabled."""
        if self.wiring_probe is not None:
            self.auto_advance = not self.auto_advance
            if self.auto_advance:
                self._tts_speak("Auto advance enabled.")
            else:
                self._tts_speak("Auto advance disabled.")
        else:
            self._tts_speak("Auto advance not supported.")


    def _on_pause(self, event):
        """Toggle whether timings are being recorded."""
        if self.timing_logger is not None:
            if self.timing_logger.paused:
                self.timing_logger.unpause()
            else:
                self.timing_logger.pause()
        self._redraw()


    def _on_resize(self, event):
        """Window has been resized, trigger a redraw."""
        new_size = (event.width, event.height)

        if self._old_size != new_size:
            self._old_size = new_size
            self._redraw()


    def _on_close(self, event=None):
        """The window has been closed."""
        if self.timing_logger is not None:
            self.timing_logger.logging_stopped()

        # Turn off LEDs before leaving
        self.set_leds(self.cur_wire, False)
        self.tk.destroy()


    def mainloop(self):  # pragma: no cover
        """Start the interactive wiring guide GUI. Returns when the window is
        closed."""
        return self.tk.mainloop()
