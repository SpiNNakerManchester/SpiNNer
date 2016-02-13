import pytest

from mock import Mock, call

import spinner.proxy

from spinner.proxy import ProxyServer, ProxyClient


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
	
	def test_no_clients(self, server_sock, select):
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
	
	def test_trivial_client(self, server_sock, select):
		# Make sure a client can connect and disconnect
		
		client = Mock()
		
		# First accept client then client disconnects
		select.side_effect = [([server_sock],[],[]), ([client],[],[]), KeyboardInterrupt()]
		
		server_sock.accept.return_value = (client, "foo")
		client.recv.return_value = b""
		
		bmp_controller = Mock()
		wiring_probe = Mock()
		ps = ProxyServer(bmp_controller, wiring_probe)
		ps.main()
		
		assert select.mock_calls == [
			# Initially only server should be selected
			call([server_sock], [], []),
			# Client should be selected on once connected
			call([server_sock, client], [], []),
			# Client should nolonger be selected after disconnection
			call([server_sock], [], []),
		]
		
		# Client's connection should have been removed
		client.close.assert_called_once_with()
		
		# BMP and wiring probe should be unused
		assert len(bmp_controller.set_led.mock_calls) == 0
		assert len(wiring_probe.get_link_target.mock_calls) == 0
	
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
