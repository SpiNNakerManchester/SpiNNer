"""A logger for cable installation times."""

from six import iteritems

import time
import datetime

class TimingLogger(object):
	"""A tool which logs cable installation events and their timings.
	
	This tool is designed to record detailed information chronicling the process
	of cable installation in large machines for research purposes. The tool
	outputs a CSV of events in a format suitable for processing using R or
	similar tools.
	
	The timing logger contains a state machine which is advanced by the reporting
	of various low-level events (e.g. "starting cable installation" and "cable
	installed correctly"). This state machine logs the incoming fine-grained
	event stream while also generating higher-level events.
	
	The CSV output contains many columns, some of which are only applicable to
	certain types of event. The first column, "type", defines the event type and
	is always populated. Other columns are populated dependent on the type of
	event.
	"""
	
	# An in-order list of all columns present in the CSV.
	_COLUMNS = [
		# The type of event
		"event_type",
		# The real time and date
		"realtime",
		# Time that the event occurred, in seconds since the start of logging and
		# excluding any time spent paused.
		"time",
		# Source and destination cabinet, frame, board and direction
		"sc", "sf", "sb", "sd",
		"dc", "df", "db", "dd",
		# Overall time to connect a cable correctly
		"duration",
		# Time since last attempt to connect the cable
		"attempt_duration",
		# Number of attempts made to install the current cable
		"num_attempts",
		# Temperature report values
		"c", "f", "b", "temp_top", "temp_btm", "temp_ext_0", "temp_ext_1",
		"fan_0", "fan_1",
	]
	
	def __init__(self, file, add_header=True):
		"""Start logging into the specified file.
		
		Parameters
		----------
		file : file-like
			The file into which the CSV data will be written.
		add_header : bool
			Determines whether a header line defining all columns will be added to
			the file. When appending to an existing file, this should generally be
			False.
		"""
		self.file = file
		
		if add_header:
			self.file.write("{}\n".format(",".join(self._COLUMNS)))
		
		# Set by logging_started()
		self._start_time = None
		
		# Set when recording is paused and used to compensate timers for time spent
		# paused.
		self._pause_start_time = None
		
		# The current connection being installed (if any). If set, this is a
		# dictionary mapping from strings "sc", "sf", "sb", "sl", and "dc", "df",
		# "db", "dl", to the source and destination frame, cabinet, board and link
		# the connection is between.
		self._cur_connection = None
		
		# The time the current connection started being installed
		self._cur_connection_start_time = None
		
		# The time the last connection error for the current connection occurred
		# (or the connection start time if no errors have occurred.
		self._cur_connection_last_error_time = None
		
		# The number of errors made during installation of the current cable
		self._cur_connection_errors = None
	
	@property
	def paused(self):
		return self._pause_start_time is not None
	
	def _write_row(self, **columns):
		"""Write a row to the CSV."""
		# Sanity check no extra fields have made it in
		assert set(columns) <= set(self._COLUMNS)
		
		# Write out the line
		self.file.write("{}\n".format(",".join(str(columns.get(c, "NA"))
		                                       for c in self._COLUMNS)))
	
	def _now(self):
		"""Get the currently elapsed time in seconds."""
		return time.time() - self._start_time
	
	def _realtime(self):
		"""Return the current real time as a sensibly formatted string."""
		return datetime.datetime.now().isoformat()
	
	def logging_started(self):
		"""Event when logging has started."""
		self._start_time = time.time()
		self._write_row( event_type="logging_started"
		               , time=0.0
		               , realtime=self._realtime()
		               )
	
	def logging_stopped(self):
		"""Event when logging has started."""
		self._write_row( event_type="logging_stopped"
		               , time=self._now()
		               )
		self._start_time = None
	
	def connection_started(self, sc, sf, sb, sd, dc, df, db, dd):
		"""Event when a new cable has been presented for installation."""
		
		now = self._now()
		self._cur_connection_start_time = now
		self._cur_connection_last_error_time = now
		self._cur_connection_errors = 0
		
		self._cur_connection = {
			"sc": sc, "sf": sf, "sb": sb, "sd": sd.name,
			"dc": dc, "df": df, "db": db, "dd": dd.name,
		}
		
		self._write_row( event_type="connection_started"
		               , time=now
		               , realtime=self._realtime()
		               , **self._cur_connection
		               )
	
	def connection_error(self):
		"""Event when the current cable was installed incorrectly."""
		if self._cur_connection is None:
			return
		
		now = self._now()
		
		# The time since the last error (or start of connection)
		attempt_duration = now - self._cur_connection_last_error_time
		self._cur_connection_last_error_time = now
		
		self._write_row( event_type="connection_error"
		               , time=now
		               , realtime=self._realtime()
		               , attempt_duration=attempt_duration
		               , num_attempts=self._cur_connection_errors + 1
		               , **self._cur_connection
		               )
		
		self._cur_connection_errors += 1
	
	def connection_complete(self):
		"""Event when the current cable was installed correctly."""
		if self._cur_connection is None:
			return
		
		now = self._now()
		
		# The time since the start of the connection
		duration = now - self._cur_connection_start_time
		
		# The time since the last error (or start of connection)
		attempt_duration = now - self._cur_connection_last_error_time
		
		self._write_row( event_type="connection_complete"
		               , time=now
		               , realtime=self._realtime()
		               , duration=duration
		               , attempt_duration=attempt_duration
		               , num_attempts=self._cur_connection_errors + 1
		               , **self._cur_connection
		               )
		
		self._cur_connection = None
		self._cur_connection_start_time = None
		self._cur_connection_last_error_time = None
		self._cur_connection_errors = None
	
	def pause(self):
		"""Pause all timers."""
		self._pause_start_time = self._now()
	
	def unpause(self):
		"""Resume all timers."""
		if self._pause_start_time is None:
			return
		
		now = self._now()
		pause_duration = now - self._pause_start_time
		
		# Compensate for time spent paused
		self._start_time += pause_duration
		
		# Report it in the logs
		self._write_row( event_type="pause"
		               , time=now - pause_duration
		               , duration=pause_duration
		               )
		
		self._pause_start_time = None
	
	def temperature(self, c, f, b, adc_info):
		"""Event when logging has started."""
		self._start_time = time.time()
		self._write_row( event_type="temperature"
		               , time=0.0
		               , realtime=self._realtime()
		               , c=c, f=f, b=b
		               , temp_top=adc_info.temp_top
		               , temp_btm=adc_info.temp_btm
		               , temp_ext_0=adc_info.temp_ext_0
		               , temp_ext_1=adc_info.temp_ext_1
		               , fan_0=adc_info.fan_0
		               , fan_1=adc_info.fan_1
		               )
