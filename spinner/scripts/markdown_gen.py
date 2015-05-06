"""Markdown generation utilities for producing reports."""

def heading(text, level=1):
	"""Render the supplied text as a heading.
	
	Parameters
	----------
	text : str
		The text to render as a heading
	level : int
		The heading level from 1 upward.
	"""
	if level == 1:
		return "{}\n{}\n".format(text, "="*len(text))
	elif level == 2:
		return "{}\n{}\n".format(text, "-"*len(text))
	else:
		return "{} {}\n".format("#"*level, text)


def table(data):
	"""Render the supplied data as a table.
	
	Parameters
	----------
	data : [[object, ...], ...]
		Table data, a list of rows of values. Each row must be the same length.
		Values are formated with `str`. The first row of data is presented as a
		header.
	"""
	# Special case if no data provided
	if len(data) == 0:
		return "\n"
	
	# Convert all data into strings
	data = [[str(v) for v in row] for row in data]
	
	# Work out the maximum width of each column
	col_widths = [0]*len(data[0])
	for row in data:
		for n, col in enumerate(row):
			if len(col) > col_widths[n]:
				col_widths[n] = len(col)
	
	# Print the table
	out = ""
	for row_num, row in enumerate(data):
		out += "| {} |\n".format(
			" | ".join(
				col.ljust(col_widths[col_num])
				for col_num, col in enumerate(row)
			)
		)
		
		# Print underline for header row
		if row_num == 0:
			out += "| {} |\n".format(
				" | ".join("-"*w for w in col_widths)
			)
	
	return out
