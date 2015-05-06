import pytest

from spinner.scripts import markdown_gen


def test_heading():
	assert markdown_gen.heading("Hi") ==\
		"Hi\n"\
		"==\n"
	assert markdown_gen.heading("Hello, World!", level=1) ==\
		"Hello, World!\n"\
		"=============\n"
	
	assert markdown_gen.heading("Hello, World!", level=2) ==\
		"Hello, World!\n"\
		"-------------\n"
	
	assert markdown_gen.heading("Hello, World!", level=3) ==\
		"### Hello, World!\n"\
	
	assert markdown_gen.heading("Hello, World!", level=4) ==\
		"#### Hello, World!\n"\


def test_table():
	# Special case
	assert markdown_gen.table([]) == "\n"
	
	# Ensure width is detected correctly
	assert markdown_gen.table([["Hi"]]) == (
		"| Hi |\n"
		"| -- |\n"
	)
	assert markdown_gen.table([["Hi", "There"]]) == (
		"| Hi | There |\n"\
		"| -- | ----- |\n"
	)
	assert markdown_gen.table([["Hi", "There"],
	                           [123, 1]]) == (
		"| Hi  | There |\n"
		"| --- | ----- |\n"
		"| 123 | 1     |\n"
	)
	assert markdown_gen.table([["Hi", "There"],
	                           [123, 1],
	                           ["", "Welcome"]]) == (
		"| Hi  | There   |\n"
		"| --- | ------- |\n"
		"| 123 | 1       |\n"
		"|     | Welcome |\n"
	)
