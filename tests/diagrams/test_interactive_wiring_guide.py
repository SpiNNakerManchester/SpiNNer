"""Testing interactive graphical applications propperly, especially when they
interact with "real" hardware. These tests are fairly basic and are largely
based on the UI toolkit and any hardware involvement being mocked out.
"""

import pytest

from mock import Mock

from spinner.diagrams import interactive_wiring_guide

@pytest.fixture
def led_states(cabinet):
	"""The dictionary which backs the virtual LEDs of the BMPController mock."""
	# {(cabinet, frame, board): led_state}
	return {(c,f,b): False
	        for c in range(cabinet.num_cabinets)
	        for f in range(cabinet.frames_per_cabinet)
	        for b in range(cabinet.boards_per_frame)}

@pytest.fixture
def bmp_controller(led_states):
	from rig import machine_control
	
	bc = Mock(spec_set=machine_control.BMPController)
	
	def set_led(led, action, cabinet, frame, board):
		led_states[(cabinet, frame, board)] = action
	bc.set_led.side_effect = set_led
	
	return bc


@pytest.fixture
def installed_wires(wires):
	"""A dictionary mapping {(sc,sf,sb,sd): (dc,df,db,dd), ...} for all live
	connections.
	
	Initially states that the first two wires are installed.
	"""
	installed_wires = {}
	
	# Make it look as if the first wire is installed
	installed_wires[wires[0][0]] = wires[0][1]
	installed_wires[wires[0][1]] = wires[0][0]
	
	return installed_wires

@pytest.fixture
def wiring_probe(installed_wires):
	from spinner.probe import WiringProbe
	
	probe = Mock(spec_set=WiringProbe)
	
	def get_link_target(c,f,s,d):
		return installed_wires.get((c,f,s,d), None)
	probe.get_link_target.side_effect = get_link_target
	
	return probe


@pytest.fixture
def cairo(monkeypatch):
	import cairocffi
	
	ImageSurface = Mock(spec_set=cairocffi.ImageSurface)
	
	Context = Mock(spec_set=cairocffi.Context)
	Context.text_extents.return_value = [1.0]*6
	
	monkeypatch.setattr(cairocffi, "ImageSurface", Mock(return_value=ImageSurface))
	monkeypatch.setattr(cairocffi, "Context", Mock(return_value=Context))
	return cairocffi


@pytest.fixture
def popen(monkeypatch):
	import subprocess
	
	Popen = Mock(spec_set=subprocess.Popen)
	monkeypatch.setattr(subprocess, "Popen", Mock(return_value=Popen))
	return Popen


@pytest.fixture
def tkinter(monkeypatch):
	Tk = Mock()
	Label = Mock()
	monkeypatch.setattr(interactive_wiring_guide, "Tk", Mock(return_value=Tk))
	monkeypatch.setattr(interactive_wiring_guide, "Label", Mock(return_value=Label))
	
	return (Tk, Label)


@pytest.fixture
def PIL(monkeypatch):
	Image = Mock(spec_set=interactive_wiring_guide.Image)
	ImageTk = Mock(spec_set=interactive_wiring_guide.ImageTk)
	monkeypatch.setattr(interactive_wiring_guide, "Image", Mock(return_value=Image))
	monkeypatch.setattr(interactive_wiring_guide, "ImageTk", Mock(return_value=ImageTk))
	return (Image, ImageTk)


@pytest.fixture
def md(monkeypatch):
	md = Mock(spec_set=interactive_wiring_guide.MachineDiagram)
	monkeypatch.setattr(interactive_wiring_guide, "MachineDiagram", Mock(return_value=md))
	return md


@pytest.fixture
def wire_lengths():
	return [0.2, 0.5, 1.0]


@pytest.fixture
def cabinet():
	from example_cabinet_params import real
	from spinner.cabinet import Cabinet
	return Cabinet(**real)


@pytest.fixture
def cabinetised_boards(cabinet):
	from spinner import transforms
	from spinner import utils
	
	# Generate folded system
	hex_boards, folded_boards = utils.folded_torus(10, 8, "shear", "rows", (2, 2))
	
	# Divide into cabinets
	cabinetised_boards = transforms.cabinetise(folded_boards,
	                                           cabinet.num_cabinets,
	                                           cabinet.frames_per_cabinet,
	                                           cabinet.boards_per_frame)
	cabinetised_boards = transforms.remove_gaps(cabinetised_boards)
	
	return cabinetised_boards


@pytest.fixture
def wires(cabinetised_boards, cabinet, wire_lengths):
	"""Return a flat wiring list for the suggested cabinet system. The first wire
	will be set to be disconnected and the rest will have their assigned
	lengths."""
	from spinner import transforms
	from spinner import plan
	
	physical_boards = transforms.cabinet_to_physical(cabinetised_boards, cabinet)
	
	wires_between_boards, wires_between_frames, wires_between_cabinets =\
		plan.generate_wiring_plan(cabinetised_boards, physical_boards,
		                          cabinet.board_wire_offset, wire_lengths)
	flat_wiring_plan = plan.flatten_wiring_plan(wires_between_boards,
	                                            wires_between_frames,
	                                            wires_between_cabinets,
	                                            cabinet.board_wire_offset)
	b2c = dict(cabinetised_boards)
	
	wires = []
	for i, ((src_board, src_direction),
	        (dst_board, dst_direction),
	        wire_length) in enumerate(flat_wiring_plan):
		sc,sf,sb = b2c[src_board]
		dc,df,db = b2c[dst_board]
		# Label the first wire for disconnection
		wires.append(((sc,sf,sb,src_direction),
		              (dc,df,db,dst_direction),
		              wire_length if i != 0 else None))
	
	return wires


@pytest.fixture
def iwg(bmp_controller, cairo, tkinter, PIL, md, popen, wiring_probe,
        cabinet, wire_lengths, wires, monkeypatch):
	# Prevent Tk actually schedluing callbacks in the test
	monkeypatch.setattr(interactive_wiring_guide.InteractiveWiringGuide,
	                    "after", Mock())
	
	# Create an interactive wiring guide with (basically) all external libraries
	# mocked out.
	iwg = interactive_wiring_guide.InteractiveWiringGuide(
		cabinet, wire_lengths, wires, bmp_controller=bmp_controller,
		wiring_probe=wiring_probe)
	
	# Wrap various internal methods in Mocks to log calls
	for name in ["_redraw", "_tts_speak"]:
		setattr(iwg, name, Mock(side_effect=getattr(iwg, name)))
	
	return iwg


@pytest.fixture
def count_wires(iwg, md):
	# A function which returns the number of wires drawn by _redraw().
	
	def count_wires():
		md.add_wire.reset_mock()
		iwg._redraw()
		
		count = 0
		for add_wire_call in md.add_wire.mock_calls:
			# Skip the outline drawn around the current wire
			if add_wire_call[2]["rgba"] != (1.0, 1.0, 1.0, 1.0):
				count += 1
		return count
	return count_wires


def test_next_prev(iwg, count_wires, wires):
	"""Test that the next and previous functions work (and that they wrap
	around)"""
	
	# Should initially be on the first wire
	assert count_wires() == 1
	
	# Shouldn't advance on its own...
	assert count_wires() == 1
	
	# Should advance one wire at a time
	iwg._on_next(None)
	assert count_wires() == 2
	iwg._on_next(None)
	assert count_wires() == 3
	
	# Should be able to go backward
	iwg._on_prev(None)
	assert count_wires() == 2
	iwg._on_prev(None)
	assert count_wires() == 1
	
	# Should wrap-around negatively
	iwg._on_prev(None)
	assert count_wires() == len(wires)
	
	# Should wrap-around positively again
	iwg._on_next(None)
	assert count_wires() == 1


def test_skip_next_prev(iwg, count_wires, wires):
	"""Test that the multi-skip next and previous functions work (and that they
	wrap around)"""
	
	# Should initially be on the first wire
	assert count_wires() == 1
	
	# Should advance more-than one wire at a time
	iwg._on_skip_next(None)
	first_count = count_wires()
	assert first_count > 2
	
	# Should advance that many again
	iwg._on_skip_next(None)
	assert count_wires() == first_count*2 - 1
	
	# Should reverse back the same amount
	iwg._on_skip_prev(None)
	assert count_wires() == first_count
	iwg._on_skip_prev(None)
	assert count_wires() == 1
	
	# Should wrap-around negatively
	iwg._on_skip_prev(None)
	assert count_wires() == len(wires) - first_count + 2
	
	# And back again
	iwg._on_skip_next(None)
	assert count_wires() == 1


def test_first_last(iwg, count_wires, wires):
	"""Test that the first and last functions work."""
	iwg.go_to_wire(10)
	assert count_wires() == 11
	
	iwg._on_first(None)
	assert count_wires() == 1
	iwg._on_first(None)
	assert count_wires() == 1
	
	iwg._on_last(None)
	assert count_wires() == len(wires)
	iwg._on_last(None)
	assert count_wires() == len(wires)


def test_tts_toggle(iwg):
	"""Check that TTS can be turned on and off"""
	
	# Should initially be turned on
	assert iwg.use_tts == True
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(0)
	assert iwg._tts_speak.called
	
	iwg._tts_speak.reset_mock()
	iwg._on_tts_toggle(None)
	assert iwg.use_tts == False
	assert iwg._tts_speak.called_once_with("Text to speech disabled.")
	
	# Should now be turned off
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(0)
	assert not iwg._tts_speak.called
	
	iwg._tts_speak.reset_mock()
	iwg._on_tts_toggle(None)
	assert iwg.use_tts == True
	assert iwg._tts_speak.called_once_with("Text to speech enabled.")
	
	# Should now be turned on again
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(0)
	assert iwg._tts_speak.called


def test_tts_terminate(iwg, popen):
	"""Make sure that when speaking, any in-process announcements are cancelled."""
	# Should not terminate if previous process has already finished
	iwg._tts_speak("hello")
	popen.poll.return_value = 0
	iwg._tts_speak("world")
	assert not popen.terminate.called
	
	# Should terminate if previous process is long-running
	iwg._tts_speak("blocking")
	popen.poll.return_value = None
	iwg._tts_speak("killing")
	assert popen.terminate.called


def test_leds(iwg, led_states, wires):
	"""Check that LEDs are lit up correctly and turned off on closure."""
	# Should initially have the LEDs enabled for the first wire endpoint's LEDs
	sc,sf,sb,_ = wires[0][0]
	dc,df,db,_ = wires[0][1]
	assert led_states == {(c,f,b): (c,f,b) in ((sc,sf,sb), (dc,df,db))
	                      for (c,f,b) in led_states}
	
	# Upon advancing, the LEDs should follow
	iwg.go_to_wire(1)
	sc,sf,sb,_ = wires[1][0]
	dc,df,db,_ = wires[1][1]
	assert led_states == {(c,f,b): (c,f,b) in ((sc,sf,sb), (dc,df,db))
	                      for (c,f,b) in led_states}
	
	# Upon closing, the LEDs should all be turned off
	iwg._on_close()
	assert led_states == {(c,f,b): False for (c,f,b) in led_states}


def test_no_bmp(iwg):
	"""Shouldn't crash if BMP not provided"""
	iwg.bmp_controller = None
	iwg.go_to_wire(1)


def test_show_installed_and_future_wires(iwg, count_wires, wires, md):
	"""Should be able to disable display of installed/future wires"""
	iwg.show_installed_wires = False
	
	iwg.go_to_wire(0)
	assert count_wires() == 1
	
	iwg.go_to_wire(10)
	assert count_wires() == 1

	iwg.show_future_wires = True
	
	iwg.go_to_wire(0)
	assert count_wires() == len(wires)
	
	iwg.go_to_wire(10)
	assert count_wires() == len(wires) - 10
	
	iwg.show_installed_wires = True
	
	iwg.go_to_wire(10)
	assert count_wires() == len(wires)


def tl(wire):
	"""Get the top-left most src/dst tuple of a ((sc,sf,sb,sd), (dc,df,db,dd), l)
	tuple."""
	src, dst, l = wire
	return min([src, dst], key=(lambda v: (-v[0],  # Right-to-left
	                                       +v[1],  # Top-to-bottom
	                                       -v[2])))  # Right-to-left


def br(wire):
	"""Get the bottom-right most src/dst tuple of a (src, dst), l) tuple."""
	src, dst, l = wire
	return max([src, dst], key=(lambda v: (-v[0],  # Right-to-left
	                                       +v[1],  # Top-to-bottom
	                                       -v[2])))  # Right-to-left


def test_tts_delta(iwg, wires, wire_lengths):
	"""Check announcements are appropriate."""
	iwg.go_to_wire(1)
	
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(0)
	message = iwg._tts_speak.mock_calls[0][1][0]
	assert "Disconnect cable. {} going {}.".format(
		tl(wires[0])[3].name.replace("_", " "),
		br(wires[0])[3].name.replace("_", " "))== message
	
	# Going to a wire with a different length should trigger that length to be
	# spoken
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(1)
	message = iwg._tts_speak.mock_calls[0][1][0]
	assert message == "{} meter cable. {} going {}.".format(
		("%0.2f"%wires[1][2]).rstrip(".0"),
		tl(wires[1])[3].name.replace("_", " "),
		br(wires[1])[3].name.replace("_", " "))
	
	# Going to a wire with the same length should result in no length being
	# spoken.
	for wire_num, (src, dst, length) in enumerate(wires):  # pragma: no branch
		if length == wires[1][2]:  # pragma: no branch
			break
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(wire_num)
	message = iwg._tts_speak.mock_calls[0][1][0]
	assert message == "{} going {}.".format(
		tl(wires[wire_num])[3].name.replace("_", " "),
		br(wires[wire_num])[3].name.replace("_", " "))
	
	# Going to a wire with a different length should result in the length being
	# spoken
	last_length = length
	for wire_num, (src, dst, length) in enumerate(wires):  # pragma: no branch
		if length is not None and length != last_length:  # pragma: no branch
			break
	iwg._tts_speak.reset_mock()
	iwg.go_to_wire(wire_num)
	message = iwg._tts_speak.mock_calls[0][1][0]
	assert message == "{} meter cable. {} going {}.".format(
		("%0.2f"%wires[wire_num][2]).rstrip(".0"),
		tl(wires[wire_num])[3].name.replace("_", " "),
		br(wires[wire_num])[3].name.replace("_", " "))


def test_resize(iwg):
	"""Make sure that duplicate resize events don't cause multiple redraws."""
	iwg._redraw.reset_mock()
	
	# Initial resize should cause a single redraw
	iwg._on_resize(Mock(width=100, height=50))
	assert len(iwg._redraw.mock_calls) == 1
	
	# Duplicates should not result in further redraws
	iwg._on_resize(Mock(width=100, height=50))
	iwg._on_resize(Mock(width=100, height=50))
	iwg._on_resize(Mock(width=100, height=50))
	assert len(iwg._redraw.mock_calls) == 1
	
	# Size change should result in a new redraw
	iwg._on_resize(Mock(width=50, height=100))
	iwg._on_resize(Mock(width=50, height=100))
	iwg._on_resize(Mock(width=50, height=100))
	assert len(iwg._redraw.mock_calls) == 2


def test_no_wiring_probe(iwg):
	"""Shouldn't crash without wiring probe."""
	iwg.wiring_probe = None
	iwg._poll_wiring_probe()


def test_wiring_probe(iwg, wires, wiring_probe, installed_wires):
	"""Check that advancing based on the wiring probe works."""
	iwg._redraw.reset_mock()
	
	# The first wire is due to be removed so we shouldn't advance
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 0
	assert not iwg._redraw.called
	
	# If we half-remove the wire, we still shouldn't advance (admidtedly this
	# can't really happen in practice...)
	installed_wires.pop(wires[0][0])
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 0
	assert not iwg._redraw.called
	
	# If we fully remove the wire, we should advance one step
	installed_wires.pop(wires[0][1])
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 1
	assert iwg._redraw.called
	iwg._redraw.reset_mock()
	
	# We should now be stuck on the next wire
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 1
	assert not iwg._redraw.called
	
	# If we add half of the next wire, we should not advance
	installed_wires[wires[1][0]] = wires[1][1]
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 1
	assert not iwg._redraw.called
	
	# If we add the other half, we should advance
	installed_wires[wires[1][1]] = wires[1][0]
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 2
	assert iwg._redraw.called
	iwg._redraw.reset_mock()
	
	# If we add the next wire incorrectly, we should get a warning and not advance
	installed_wires[wires[2][0]] = wires[3][0]
	installed_wires[wires[3][0]] = wires[2][0]
	iwg._tts_speak.reset_mock()
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 2
	assert not iwg._redraw.called
	assert iwg._tts_speak.called_once_with("Wire inserted incorrectly.")
	iwg._tts_speak.reset_mock()
	
	# If nothing is changed, we shouldn't get another warning
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 2
	assert not iwg._redraw.called
	assert not iwg._tts_speak.called
	
	# If we disconnect again, nothing should change
	installed_wires.pop(wires[2][0])
	installed_wires.pop(wires[3][0])
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 2
	assert not iwg._redraw.called
	assert not iwg._tts_speak.called
	
	# Re-adding the bad wire should raise the warning again
	installed_wires[wires[2][0]] = wires[3][0]
	installed_wires[wires[3][0]] = wires[2][0]
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 2
	assert not iwg._redraw.called
	assert iwg._tts_speak.called_once_with("Wire inserted incorrectly.")
	iwg._tts_speak.reset_mock()
	
	# Finally add the correct wire
	installed_wires.pop(wires[2][0])
	installed_wires.pop(wires[3][0])
	installed_wires[wires[2][0]] = wires[2][1]
	installed_wires[wires[2][1]] = wires[2][0]
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 3
	assert iwg._redraw.called
	iwg._redraw.reset_mock()
	
	# Installing the next wire wrong should result in an error
	installed_wires[wires[3][0]] = wires[4][0]
	installed_wires[wires[4][0]] = wires[3][0]
	iwg._tts_speak.reset_mock()
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 3
	assert not iwg._redraw.called
	assert iwg._tts_speak.called_once_with("Wire inserted incorrectly.")
	
	# Should never advance past the last wire, even if it is installed
	# appropriately
	iwg.go_to_wire(len(wires) - 1)
	installed_wires[wires[-1][0]] = wires[-1][1]
	installed_wires[wires[-1][1]] = wires[-1][0]
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == len(wires) - 1
	assert not iwg._redraw.called


def test_auto_advance_toggle(iwg, wires, installed_wires):
	"""Check that auto-advance can be turned on and off"""
	iwg._tts_speak.reset_mock()
	
	# Should initially be turned on
	assert iwg.auto_advance == True
	
	# If turned off, it should be announced and auto-advance should be disabled
	iwg._on_auto_advance_toggle(None)
	assert iwg._tts_speak.called_once_with("Auto advance disabled.")
	iwg._tts_speak.reset_mock()
	
	# Unplug the initial wire and test that auto-advance doesn't go past it
	installed_wires.pop(wires[0][0])
	installed_wires.pop(wires[0][1])
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 0
	
	# Turn on auto-advance again
	iwg._on_auto_advance_toggle(None)
	assert iwg._tts_speak.called_once_with("Auto advance enabled.")
	iwg._tts_speak.reset_mock()
	
	# Should now work as usual
	iwg._poll_wiring_probe()
	assert iwg.cur_wire == 1
	iwg._tts_speak.reset_mock()
	
	# If the wiring probe is removed, auto advance should not toggle and an error
	# should be announced
	iwg.wiring_probe = None
	iwg._on_auto_advance_toggle(None)
	assert iwg._tts_speak.called_once_with("Auto advance not supported.")
