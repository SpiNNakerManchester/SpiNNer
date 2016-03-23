import pytest

from mock import Mock

import logging

from spinner.scripts.proxy_server import main
import spinner.scripts.proxy_server


@pytest.fixture
def mock_hardware(monkeypatch):
	bmp_controller = Mock()
	bmp_controller.return_value = bmp_controller
	wiring_probe = Mock()
	wiring_probe.return_value = wiring_probe
	monkeypatch.setattr(
		spinner.scripts.proxy_server, "BMPController", bmp_controller)
	monkeypatch.setattr(
		spinner.scripts.proxy_server, "WiringProbe", wiring_probe)
	return (bmp_controller, wiring_probe)


@pytest.fixture
def mock_proxy_server(monkeypatch):
	proxy_server = Mock()
	proxy_server.return_value = proxy_server
	monkeypatch.setattr(
		spinner.scripts.proxy_server, "ProxyServer", proxy_server)
	return proxy_server


@pytest.mark.parametrize("args", ["", "-n 3"])
def test_bad_args(args):
	with pytest.raises(SystemExit):
		main(args.split())

def test_num_boards(mock_hardware, mock_proxy_server):
	main("-n 3 --bmp 0 0 localhost".split())
	assert mock_hardware[1].mock_calls[-1][1][3] == 3
	
	main("-n 24 --bmp 0 0 localhost".split())
	assert mock_hardware[1].mock_calls[-1][1][3] == 24
	
	main("-n 48 --bmp 0 0 localhost --bmp 0 1 127.0.0.1".split())
	assert mock_hardware[1].mock_calls[-1][1][3] == 24


def test_verbose(monkeypatch, mock_hardware, mock_proxy_server):
	basicConfig = Mock()
	monkeypatch.setattr(spinner.scripts.proxy_server.logging, "basicConfig", basicConfig)
	
	main("-n 3 --bmp 0 0 localhost".split())
	assert len(basicConfig.mock_calls) == 0
	
	main("-n 3 --bmp 0 0 localhost -v".split())
	basicConfig.assert_called_once_with(level=logging.INFO)
	basicConfig.reset_mock()
	
	main("-n 3 --bmp 0 0 localhost -vv".split())
	basicConfig.assert_called_once_with(level=logging.DEBUG)
	basicConfig.reset_mock()
	
	main("-n 3 --bmp 0 0 localhost -vvv".split())
	basicConfig.assert_called_once_with(level=logging.DEBUG)
	basicConfig.reset_mock()


def test_server_args(mock_hardware, mock_proxy_server):
	main("-n 3 --bmp 0 0 localhost -H foobar -p 1234".split())
	
	mock_proxy_server.assert_called_once_with(
		mock_hardware[0], mock_hardware[1],
		"foobar", 1234)
