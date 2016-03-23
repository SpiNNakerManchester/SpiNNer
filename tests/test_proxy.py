import pytest

from mock import Mock, call

from spinner import __version__

import spinner.proxy

from spinner.proxy import ProxyServer, ProxyClient, ProxyError

from spinner.topology import Direction


class TestServer(object):
	
	@pytest.fixture
	def server_sock(self, monkeypatch):
		server_sock = Mock()
		monkeypatch.setattr(spinner.proxy.socket, "socket", Mock(return_value=server_sock))
		return server_sock
	
	@pytest.fixture
	def select(self, monkeypatch):
		select = Mock()
		monkeypatch.setattr(spinner.proxy.select, "select", select)
		return select
	
	def test_main_loop(self, server_sock, select):
		# Make sure nothing breaks if no clients ever connect
		
		select.side_effect = KeyboardInterrupt()
		
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe, hostname="foo", port=1234)
		ps.main()
		
		server_sock.bind.assert_called_once_with(("foo", 1234))
		assert len(server_sock.listen.mock_calls) == 1
		
		# BMP and wiring probe should be unused
		assert len(bmp_controller.set_led.mock_calls) == 0
		assert len(wiring_probe.get_link_target.mock_calls) == 0
	
	@pytest.mark.parametrize("last_client_action", [b"", IOError()])
	def test_client_comms(self, server_sock, select, last_client_action):
		# Make sure a client can connect, send a command and disconnect
		
		client = Mock()
		
		# First accept client then client disconnects
		select.side_effect = [([server_sock],[],[]),  # New client!
		                      ([client],[],[]),       # Send something
		                      ([client],[],[]),       # Client disconnecting
		                      KeyboardInterrupt()]    # Done!
		
		server_sock.accept.return_value = (client, "foo")
		client.recv.side_effect = [b"VERSION,v0.0.0\n",  # Something to send
		                           last_client_action]   # Disconnected!
		
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		ps.process_data = Mock()
		ps.main()
		
		assert select.mock_calls == [
			# Initially only server should be selected
			call([server_sock], [], []),
			# Client should be selected on once connected
			call([server_sock, client], [], []),  # Data received
			call([server_sock, client], [], []),  # Disconnected
			# Client should nolonger be selected after disconnection
			call([server_sock], [], []),
		]
		
		ps.process_data.assert_called_once_with(client, b"VERSION,v0.0.0\n")
		
		# Client's connection should have been removed
		client.close.assert_called_once_with()
		
		# BMP and wiring probe should be unused
		assert len(bmp_controller.set_led.mock_calls) == 0
		assert len(wiring_probe.get_link_target.mock_calls) == 0
	
	def test_process_data(self, server_sock):
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		
		c = Mock()
		ps.add_client(c, None)
		
		# Command should be buffered up if sent in multiple pieces.
		ps.process_data(c, b"VERSION")
		assert len(c.send.mock_calls) == 0
		ps.process_data(c, b"," + __version__.encode("ascii") + b"\n")
		c.send.assert_called_once_with(b"OK\n")
		c.send.reset_mock()
		
		# If multiple commands arrive at once, should split them up
		vers_command = b"VERSION," + __version__.encode("ascii") + b"\n"
		ps.process_data(c, vers_command + vers_command)
		assert c.send.mock_calls == [
			call(b"OK\n"),
			call(b"OK\n"),
		]
		c.send.reset_mock()
		
		# If a failure occurs, disconnect the client
		ps.process_data(c, b"VERSION,failfailfail\n")
		c.close.assert_called_once_with()
	
	def test_handle_version(self, server_sock):
		bmp_controller = Mock()
		wiring_probe = Mock()
		c = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		
		# Bad version
		with pytest.raises(Exception):
			ps.handle_version(c, b"fail")
		
		# Good version
		ps.handle_version(c, __version__.encode("ascii"))
		c.send.assert_called_once_with(b"OK\n")
	
	def test_handle_led(self, server_sock):
		bmp_controller = Mock()
		wiring_probe = Mock()
		c = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		ps.add_client(c, None)
		
		# Turn on
		ps.handle_led(c, b"0,1,2,3,1")
		c.send.assert_called_once_with(b"OK\n")
		c.send.reset_mock()
		bmp_controller.set_led.assert_called_once_with(3, True, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		
		# Turn off
		ps.handle_led(c, b"0,1,2,3,0")
		c.send.assert_called_once_with(b"OK\n")
		c.send.reset_mock()
		bmp_controller.set_led.assert_called_once_with(3, False, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		
		# Removing a client should turn off its LEDs
		ps.handle_led(c, b"0,1,2,3,1")
		bmp_controller.set_led.assert_called_once_with(3, True, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		ps.remove_client(c)
		bmp_controller.set_led.assert_called_once_with(3, False, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		
		# Unless it has none
		ps.add_client(c, None)
		ps.remove_client(c)
		assert len(bmp_controller.set_led.mock_calls) == 0
	
	def test_set_led(self, server_sock):
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		
		c1 = Mock()
		c2 = Mock()
		c3 = Mock()
		
		ps.set_led(c1, 0, 1, 2, 3, 1)
		bmp_controller.set_led.assert_called_once_with(3, True, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		
		# More turning it on should do nothing
		ps.set_led(c1, 0, 1, 2, 3, 1)
		ps.set_led(c2, 0, 1, 2, 3, 1)
		assert len(bmp_controller.set_led.mock_calls) == 0
		
		# Turning something else on should work
		ps.set_led(c3, 0, 1, 2, 4, 1)
		bmp_controller.set_led.assert_called_once_with(4, True, 0, 1, 2)
		bmp_controller.set_led.reset_mock()
		
		# Some turning off the first LED should do nothing
		ps.set_led(c1, 0, 1, 2, 3, 0)
		ps.set_led(c1, 0, 1, 2, 3, 0)  # even if done multiple times!
		assert len(bmp_controller.set_led.mock_calls) == 0
		
		# Last person to turn off should manage
		ps.set_led(c2, 0, 1, 2, 3, 0)
		ps.set_led(c2, 0, 1, 2, 3, 0)  # multiple times shouldn't hurt
		bmp_controller.set_led.assert_called_once_with(3, False, 0, 1, 2)
	
	
	def test_handle_target(self, server_sock):
		bmp_controller = Mock()
		wiring_probe = Mock()
		c = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		
		wiring_probe.get_link_target.return_value = None
		ps.handle_target(c, b"0,1,2,3")
		c.send.assert_called_once_with(b"None\n")
		c.send.reset_mock()
		wiring_probe.get_link_target.assert_called_once_with(0, 1, 2, 3)
		
		wiring_probe.get_link_target.return_value = (4, 5, 6, 7)
		ps.handle_target(c, b"0,1,2,3")
		c.send.assert_called_once_with(b"4,5,6,7\n")
	
	
	def test_terminate(self, server_sock, select):
		# Make sure the client is disconnected when the server terminates.
		
		client = Mock()
		
		# First accept client then disconnect everyone
		select.side_effect = [([server_sock],[],[]), KeyboardInterrupt()]
		
		server_sock.accept.return_value = (client, "foo")
		
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		ps.main()
		
		# Client's connection should have been closed when the server closed
		client.close.assert_called_once_with()

class TestProxyClient(object):
	
	@pytest.fixture
	def client_sock(self, monkeypatch):
		client_sock = Mock()
		monkeypatch.setattr(spinner.proxy.socket, "socket", Mock(return_value=client_sock))
		client_sock.recv.return_value = b"OK\n"
		return client_sock
	
	def test_initial_version_check(self, client_sock):
		pc = ProxyClient("foo", 1234)
		client_sock.connect.assert_called_once_with(("foo", 1234))
		client_sock.send.assert_called_once_with(
			b"VERSION," + __version__.encode("ascii") + b"\n")
		assert len(client_sock.recv.mock_calls) == 1
	
	def test_recvline(self, client_sock):
		pc = ProxyClient("foo", 1234)
		client_sock.send.reset_mock()
		client_sock.recv.reset_mock()
		
		# Should get line all at once
		client_sock.recv.return_value = b"foo\n"
		assert pc.recvline() == b"foo"
		
		# Should get line in pieces
		client_sock.recv.side_effect = [b"bar", b"baz\n"]
		assert pc.recvline() == b"barbaz"
		
		# Should get multiple lines at once
		client_sock.recv.side_effect = [b"qux\n", b"quux\n"]
		assert pc.recvline() == b"qux"
		assert pc.recvline() == b"quux"
		
		# Should crash on disconnect
		client_sock.recv.side_effect = [b""]
		with pytest.raises(ProxyError):
			pc.recvline()
	
	def test_check_version(self, client_sock):
		pc = ProxyClient("foo", 1234)
		client_sock.recv.return_value = b"Fail\n"
		with pytest.raises(ProxyError):
			pc.check_version()
	
	def test_set_led(self, client_sock):
		pc = ProxyClient("foo", 1234)
		client_sock.reset_mock()
		client_sock.recv.return_value = b"OK\n"
		
		pc.set_led(3, True, 0, 1, 2)
		client_sock.send.assert_called_once_with(b"LED,0,1,2,3,1\n")
		client_sock.reset_mock()
		
		pc.set_led(7, False, 4, 5, 6)
		client_sock.send.assert_called_once_with(b"LED,4,5,6,7,0\n")
		client_sock.reset_mock()
		
		client_sock.recv.return_value = b"Fail\n"
		with pytest.raises(ProxyError):
			pc.set_led(7, False, 4, 5, 6)
	
	def test_get_link_target(self, client_sock):
		pc = ProxyClient("foo", 1234)
		client_sock.reset_mock()
		client_sock.recv.return_value = b"1,2,3,4\n"
		
		assert pc.get_link_target(0, 1, 2, Direction.east) == (1, 2, 3, Direction.south_west)
		client_sock.send.assert_called_once_with(b"TARGET,0,1,2,0\n")
		client_sock.reset_mock()
		
		client_sock.recv.return_value = b"None\n"
		pc.get_link_target(4, 5, 6, Direction.west) == None
		client_sock.send.assert_called_once_with(b"TARGET,4,5,6,3\n")
		client_sock.reset_mock()
		
		client_sock.recv.return_value = b"Fail\n"
		with pytest.raises(ProxyError):
			pc.get_link_target(4, 5, 6, Direction.north)
