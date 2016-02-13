"""A proxy enabling multiple wiring guide instances to interact with the same
SpiNNaker boards.
"""

import traceback

import socket

import select

from collections import defaultdict

import logging

from six import iteritems

from spinner.version import __version__

from spinner.topology import Direction

DEFAULT_PORT = 6512


class ProxyError(Exception):
	"""Exception raised when the proxy cannot connect."""
	pass


class ProxyServer(object):
	"""A proxy server enabling multiple wiring guide instances to interact with
	the same SpiNNaker boards.
	"""
	
	def __init__(self, bmp_controller, wiring_probe,
	             hostname="", port=DEFAULT_PORT):
		self.bmp_controller = bmp_controller
		self.wiring_probe = wiring_probe
		
		# Open a TCP socket
		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_sock.setsockopt(socket.SOL_SOCKET,
                                socket.SO_REUSEADDR, 1)
		self.server_sock.bind((hostname, port))
		self.server_sock.listen(5)
		
		self.client_socks = []
		
		# A buffer for unprocessed data received from each client
		self.client_buffer = {}
		
		# For each LED, maintains a set of clients which have turned it on
		self.led_setters = defaultdict(set)
	
	
	def add_client(self, sock, addr):
		"""Register a new client."""
		logging.info("New connection {} from {}".format(sock, addr))
		self.client_socks.append(sock)
		
		# Create buffer for received data (and schedule its deletion upon
		# disconnection)
		self.client_buffer[sock] = b""
	
	
	def set_led(self, sock, c, f, b, led, state):
		"""Set the state of a diagnostic LED.
		
		An LED is turned on if at least one client has turned it on. An LED is only
		turned off if all clients which have turned the LED on have also turned it
		off again.
		"""
		
		setters = self.led_setters[(c, f, b, led)]
		
		cur_led_state = bool(setters)
		
		if state:
			setters.add(sock)
		else:
			setters.discard(sock)
		
		new_led_state = bool(setters)
		
		if cur_led_state != new_led_state:
			self.bmp_controller.set_led(led, new_led_state, c, f, b)
	
	
	def remove_client(self, sock):
		"""Disconnect and cleanup after a particular child."""
		logging.info("Closing socket {}".format(sock))
		
		# Remove buffer
		self.client_buffer.pop(sock)
		
		# Turn off any LEDs left on by the client
		for (c, f, b, led), socks in iteritems(self.led_setters):
			if sock in socks:
				self.set_led(sock, c, f, b, led, False)
		
		# Close socket
		self.client_socks.remove(sock)
		sock.close()
	
	
	def handle_version(self, sock, args):
		"""Handle "VERSION" commands.
		
		This command contains, as the argument, the SpiNNer version number of the
		remote client. If the version of the client does not match the server, the
		client is disconnected.
		
		Arguments: vX.Y.Z
		
		Returns: OK
		"""
		# Check for identical version
		assert args.decode("ascii") == __version__
		sock.send(b"OK\n")
	
	
	def handle_led(self, sock, args):
		"""Handle "LED" commands.
		
		Set the state of a diagnostic LED on a board.
		
		Arguments: c,f,b,led,state
		
		Returns: OK
		"""
		c, f, b, led, state = map(int, args.split(b","))
		
		self.set_led(sock, c, f, b, led, state)
		
		sock.send(b"OK\n")
	
	
	def handle_target(self, sock, args):
		"""Handle "TARGET" commands.
		
		Determine what is at the other end of a given link.
		
		Arguments: c,f,b,d
		
		Returns: c,f,b,d or None
		"""
		c, f, b, d = map(int, args.split(b","))
		
		target = self.wiring_probe.get_link_target(c, f, b, d)
		
		if target is None:
			sock.send(b"None\n")
		else:
			sock.send("{},{},{},{}\n".format(*map(int, target)).encode("ascii"))
	
	
	def process_data(self, sock, data):
		"""Process data received from a socket."""
		# Prepend any previously unprocessed data
		data = self.client_buffer[sock] + data
		
		# Handle any received commands. If a command fails (or is invalid) the
		# connection is dropped.
		try:
			while b"\n" in data:
				line, _, data = data.partition(b"\n")
				logging.debug("Handling command {} from {}".format(line, sock))
				
				cmd, _, args = line.partition(b",")
				
				# If an unrecognised command arrives, this lookup will fail and get
				# caught by the exception handler, printing an error and disconnecting
				# the client.
				{
					b"VERSION": self.handle_version,
					b"LED": self.handle_led,
					b"TARGET": self.handle_target,
				}[cmd](sock, args)
		
		except Exception as e:
			logging.error(traceback.format_exc())
			logging.error(
				"Disconnected client {} due to bad command (above)".format(sock))
			self.remove_client(sock)
			return
		
		# Retain any remaining unprocessed data
		self.client_buffer[sock] = data
		
		# Drop the connection if the buffer gets too big
		if len(data) > 1024:
			logging.error(
				"Disconnected {} due to excessively long command: {}.".format(
					sock, data))
			self.remove_client(sock)
			return
	
	
	def main(self):
		logging.info("Starting proxy server...")
		
		try:
			while True:
				ready, _1, _2 = select.select([self.server_sock] + self.client_socks, [], [])
				
				for sock in ready:
					if sock is self.server_sock:
						# New client connected!
						self.add_client(*self.server_sock.accept())
					else:
						# Data arrived from a client
						try:
							data = sock.recv(1024)
						except IOError as exc:
							logging.error(
								"Socket {} failed to receive: {}".format(sock, exc))
							# Cause socket to get closed
							data = b""
							
						if len(data) == 0:
							# Connection closed
							self.remove_client(sock)
						else:
							self.process_data(sock, data)
		except KeyboardInterrupt:
			# Disconnect all clients (also cleans up LED states, etc.)
			for sock in self.client_socks:
				self.remove_client(sock)
		
		logging.info("Proxy server terminated cleanly.")


class ProxyClient(object):
	"""A client for the ProxyServer object defined above.
	
	This object implements a BMPController-compatible ``set_led`` method and
	WiringProbe compatible ``get_link_target`` method and thus may be substituted
	for the above when these functions are all that are required, e.g. for the
	InteractiveWiringGuide.
	"""
	
	def __init__(self, hostname, port=DEFAULT_PORT):
		"""Connect to a running ProxyServer."""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((hostname, port))
		
		# A receive buffer
		self.buf = b""
		
		# Check for protocol version compatibility.
		self.check_version()
	
	def recvline(self):
		"""Wait for a full line to be received from the server."""
		while b"\n" not in self.buf:
			data = self.sock.recv(1024)
			self.buf += data
			if len(data) == 0:
				raise ProxyError("Remote server closed the connection.")
		
		line, _, self.buf = self.buf.partition(b"\n")
		return line
	
	def check_version(self):
		"""Check that the remote server has a compatible protocol version."""
		self.sock.send("VERSION,{}\n".format(__version__).encode("ascii"))
		
		if self.recvline() != b"OK":
			raise ProxyError("Remote server has incompatible protocol version")
	
	def set_led(self, led, state, c, f, b):
		"""Set the state of an LED on the remote machine."""
		self.sock.send("LED,{},{},{},{},{}\n".format(
			c, f, b, led, int(state)).encode("ascii"))
		
		if self.recvline() != b"OK":
			raise ProxyError("Got unexpected response to LED command.")
	
	def get_link_target(self, c, f, b, d):
		"""Discover the other end of a specified link on a remote machine."""
		self.sock.send("TARGET,{},{},{},{}\n".format(
			c, f, b, int(d)).encode("ascii"))
		
		response = self.recvline()
		if response == b"None":
			return None
		else:
			c, f, b, d = map(int, response.split(b","))
			return (c, f, b, Direction(d))
