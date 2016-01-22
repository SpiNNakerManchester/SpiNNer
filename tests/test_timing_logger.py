import pytest

import re

from six import StringIO

from spinner.topology import Direction
from spinner import timing_logger
from spinner.timing_logger import TimingLogger


class TestOutputFormatting(object):
	"""Tests of basic CSV generation."""
	
	expected_columns = ("event_type,realtime,time,"
	                    "sc,sf,sb,sd,"
	                    "dc,df,db,dd,"
	                    "duration,attempt_duration,"
	                    "num_attempts").split(",")
	
	def test_header(self):
		"""Headers should be generated when required."""
		s = StringIO()
		t = TimingLogger(s)
		assert s.getvalue() == "{}\n".format(",".join(self.expected_columns))
	
	def test_no_header(self):
		"""Headers should be suppressed when required."""
		s = StringIO()
		t = TimingLogger(s, add_header=False)
		assert s.getvalue() == ""
	
	def test_write_row_defaults(self):
		"""All columns should be filled with NAs by default."""
		s = StringIO()
		t = TimingLogger(s, add_header=False)
		
		t._write_row()
		assert s.getvalue() == "{}\n".format(  # pragma: no branch
			",".join("NA" for _ in self.expected_columns))
	
	def test_write_row_partial_defaults(self):
		"""Provided columns should be filled out and others left with NAs."""
		s = StringIO()
		t = TimingLogger(s, add_header=False)
		
		t._write_row(event_type="foo", num_attempts=123)
		assert s.getvalue() == "foo,{},123\n".format(  # pragma: no branch
			",".join("NA" for _ in range(len(self.expected_columns) - 2)))
	
	def test_write_row_all(self):
		"""If all values are provided, the order should be correct."""
		s = StringIO()
		t = TimingLogger(s, add_header=False)
		
		t._write_row(**{c: i for i, c in enumerate(self.expected_columns)})
		assert s.getvalue() == "{}\n".format(  # pragma: no branch
			",".join(str(i) for i in range(len(self.expected_columns))))
	
	def test_write_row_sanity_check(self):
		"""A sanity check should be provided which disallows unknown columns."""
		s = StringIO()
		t = TimingLogger(s, add_header=False)
		
		with pytest.raises(Exception):
			t._write_row(foo="bar")


class TestLogging(object):
	"""Tests of the logging capabilities of the TimingLogger object."""
	
	@pytest.fixture
	def entries(self):
		"""A list to which all written log entries (as a dict of column values for
		non-NA columns).
		"""
		return []
	
	@pytest.fixture
	def time(self, monkeypatch):
		"""A fake time module where the current time can be set by hand, monkey
		patched into the test_logging module.
		
		This time module starts time at 100.0 seconds and increments the time
		returned by 0.25 seconds every time it is called. The next time to return
		can be overridden by assigning to the cur_time property.
		"""
		
		class Time(object):
			def __init__(self, initial_time=100.0):
				self.cur_time = initial_time
			
			def time(self):
				now = self.cur_time
				self.cur_time += 0.25
				return now
		
		time = Time()
		monkeypatch.setattr(timing_logger, "time", time)
		return time
	
	@pytest.fixture
	def t(self, entries, time, monkeypatch):
		"""Return a monkey-patched TimingLogger which uses the fake time module
		whose output is logged as a list of dictionaries in the 'entries'
		dictionary.
		"""
		
		class MockFile(object):
			"""Decode and record the CSV data written."""
			
			def __init__(self, entries):
				self.columns = None
				self.entries = entries
			
			def write(self, data):
				# Sanity check: make sure the line is well-formed
				assert data.endswith("\n")
				data = data.strip("\n")
				
				# Read out data
				values = data.split(",")
				
				if self.columns is None:
					# The first line read gives the column headings
					self.columns = values
				else:
					# Subsequent lines should be unpacked
					assert len(values) == len(self.columns)
					self.entries.append({c: v for v, c in zip(values, self.columns)
					                     if v != "NA"})
				
				# Maintain the appearence of actually being a file...
				return len(data)
		
		# Make the _realtime just return NA to ease testing
		monkeypatch.setattr(TimingLogger, "_realtime", (lambda _: "<NOW>"))
		
		t = TimingLogger(MockFile(entries))
		
		# Start logging 
		t.logging_started()
		assert len(entries) == 1
		assert entries.pop() == {
			"event_type": "logging_started",
			"time": "0.0",
			"realtime": "<NOW>",
		}
		
		return t
	
	def test_realtime(self):
		"""Test that the _realtime function which is monkeypatched out in other
		tests would actually work if left.
		"""
		t = TimingLogger(StringIO())
		rt = t._realtime()
		
		# Should contain a time
		assert re.search(r"[0-9]{2}:[0-9]{2}:[0-9]{2}", rt)
		
		# Should contain a date
		assert re.search(r"[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}", rt)
	
	def test_now(self, t, time):
		"""Make sure the internal 'now' function works."""
		assert t._now() == 0.25
		time.cur_time = 500.0
		assert t._now() == 400.0
	
	def test_pause(self, t, time, entries):
		"""The pause function should cause the internal 'now' function to be
		compensated for the pause duration.
		"""
		assert t._now() == 0.25
		
		# Pause at time = 0.5 for 399.5 seconds
		assert not t.paused
		t.pause()
		assert t.paused
		time.cur_time = 500.0
		t.unpause()
		assert not t.paused
		time.cur_time = 500.0  # Compensate for reading time taking some time
		
		# The pause should be reported
		assert entries == [{
			"event_type": "pause",
			"duration": "399.5",
			"time": "0.5",
		}]
		
		# Time should resume counting as before
		assert t._now() == 0.5
		assert t._now() == 0.75
	
	def test_logging_stopped(self, t, entries):
		"""Stopping logging should work."""
		t.logging_stopped()
		
		assert entries == [{
			"event_type": "logging_stopped",
			"time": "0.25",
		}]
	
	CONNECTION_ARGUMENTS = { "sc": 0, "sf": 1, "sb": 2, "sd": Direction.north
		                     , "dc": 3, "df": 4, "db": 5, "dd": Direction.south
		                     }
	CONNECTION_ENTRIES = { "sc": "0", "sf": "1", "sb": "2", "sd": "north"
		                   , "dc": "3", "df": "4", "db": "5", "dd": "south"
		                   }
	
	def test_connection_nominal(self, t, entries, time):
		"""Make sure the state of a connection is logged correctly in the common
		case.
		"""
		# Connection should be logged
		t.connection_started(**self.CONNECTION_ARGUMENTS)
		
		model_entries = {
			"event_type": "connection_started",
			"time": "0.25", "realtime": "<NOW>",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
		
		# Completion should be logged
		t.connection_complete()
		
		model_entries = {
			"event_type": "connection_complete",
			"time": "0.5", "realtime": "<NOW>",
			"duration": "0.25",
			"attempt_duration": "0.25",
			"num_attempts": "1",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
	
	def test_connection_with_errors(self, t, entries, time):
		"""Make sure the state of a connection is logged correctly when mistakes
		are made.
		"""
		# Connection should be logged
		t.connection_started(**self.CONNECTION_ARGUMENTS)
		
		model_entries = {
			"event_type": "connection_started",
			"time": "0.25", "realtime": "<NOW>",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
		
		# First failiure should be logged
		t.connection_error()
		model_entries = {
			"event_type": "connection_error",
			"time": "0.5", "realtime": "<NOW>",
			"attempt_duration": "0.25",
			"num_attempts": "1",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
		
		# Second failiure should be logged
		t.connection_error()
		model_entries = {
			"event_type": "connection_error",
			"time": "0.75", "realtime": "<NOW>",
			"attempt_duration": "0.25",
			"num_attempts": "2",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
		
		# Completion should be logged
		t.connection_complete()
		
		model_entries = {
			"event_type": "connection_complete",
			"time": "1.0", "realtime": "<NOW>",
			"duration": "0.75",
			"attempt_duration": "0.25",
			"num_attempts": "3",
		}
		model_entries.update(self.CONNECTION_ENTRIES)
		assert entries == [model_entries]
		entries.pop()
	
	def test_no_connection(self, t, entries, time):
		"""Make sure when no connection has been started, the other events don't
		result in any logging data.
		"""
		t.connection_error()
		assert entries == []
		
		t.connection_complete()
		assert entries == []
	
	def test_no_pause(self, t, entries, time):
		"""Make sure unpausing when not paused doesn't log anything.
		"""
		t.unpause()
		assert entries == []
