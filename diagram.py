#!/usr/bin/env python

"""
A module which generates TikZ diagrams of systems of boards.
"""

from model import coordinates
from model import board
from model import transforms
from model import topology
from model import cabinet


class Diagram(object):
	"""
	A drawing tool for generating TikZ diagrams.
	"""
	
	PREAMBLE = r"""
% Hexagon radius
\pgfmathsetmacro{\hexRadiusScale}{1/cos(30)}

% Colours for cabinets
\tikzset{ cabinet/.style={fill,color=gray} }
\tikzset{ rack/.style={fill,color=gray!50!white} }
\tikzset{ slot/.style={} }
\tikzset{ occupied slot/.style={fill,color=green!20!white} }

% Mapping for hexagonal coordinates in TikZ
\tikzset{
	hexagon coords/.style={ x=( -30:1cm)
	                        , y=(  90:1cm)
	                        , z=(-150:1cm)
	                        }
}

% Mapping for Cartesian coordinates when showing hexagons.
\tikzset{
	cartesian hexagon coords/.style={ x=( 0:1cm/\hexRadiusScale)
	                                , y=(90:0.5cm)
	                                }
}

% Mapping for Cartesian coordinates when showing hexagons.
\tikzset{
	cartesian skewed hexagon coords/.style={ x=( 0:0.5cm)
	                                       , y=(90:0.5cm)
	                                       }
}

% Draws a hexagon.
%  #1 Identifier
%  #2 Position
%  #3 Style
%
% Also defines #1 north, #1 north east etc.
\newcommand{\hexagon}[3]{
	\begin{scope}[#3]
		\coordinate (#1) at (#2);
	\end{scope}
	\draw (#1)                        +( 120:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 north)       +(  60:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 north east)  +(   0:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 east)        +( -60:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 south)       +(-120:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 south west)  +(-180:\hexRadiusScale * 0.5cm)
	   -- coordinate (#1 west)        +( 120:\hexRadiusScale * 0.5cm)
	   -- cycle
	   [#3]
	   ;
}

% Draws a skewed hexagon.
%  #1 Identifier
%  #2 Position
%  #3 Style
%
% Also defines #1 north, #1 north east etc.
\newcommand{\skewedhexagon}[3]{
	\begin{scope}[#3]
		\coordinate (#1) at (#2);
	\end{scope}
	\draw (#1)                       ++(-0.5,-0.5)
	   -- coordinate (#1 south west) ++( 0.0, 0.5)
	   -- coordinate (#1 west)       ++( 0.5, 0.5)
	   -- coordinate (#1 north)      ++( 0.5, 0.0)
	   -- coordinate (#1 north east) ++( 0.0,-0.5)
	   -- coordinate (#1 east)       ++(-0.5,-0.5)
	   -- coordinate (#1 south)      ++(-0.5, 0.0)
	   -- cycle
	   [#3]
	      ;
}

% Draws a square.
%  #1 Identifier
%  #2 Position
%  #3 Style
%
% Also defines #1 north, #1 north east etc.
\newcommand{\square}[3]{
	\begin{scope}[#3]
		\coordinate (#1) at (#2);
	\end{scope}
	\draw (#1)
	   ++(-0.5,-0.5) coordinate (#1 south west)
	              -- coordinate (#1 west)       ++( 0.0, 1.0)
	              -- coordinate (#1 north)
	   ++( 1.0, 0.0) coordinate (#1 north east)
	              -- coordinate (#1 east)       ++( 0.0,-1.0)
	              -- coordinate (#1 south)      ++(-1.0, 0.0)
	   -- cycle
	   [#3]
	      ;
}

% Draws a board in a cabinet.
%  #1 Identifier
%  #2 Position
%  #3 Style
%
% Also defines #1 north, #1 north east etc.
\newcommand{\cabinet}[3]{
	\begin{scope}[scale=\cabscale,#3]
		% Redefine as center
		\coordinate (#1) at ([shift={(0.5*\slotwidth,0.5*\slotheight)}]#2);
		
		\path [occupied slot] (#2) rectangle ++(\slotwidth, \slotheight);
		
		\coordinate (#1 north) at ([shift=(\cabnorth)]#2);
		\coordinate (#1 north east) at ([shift=(\cabnortheast)]#2);
		\coordinate (#1 east) at ([shift=(\cabeast)]#2);
		\coordinate (#1 south) at ([shift=(\cabsouth)]#2);
		\coordinate (#1 south west) at ([shift=(\cabsouthwest)]#2);
		\coordinate (#1 west) at ([shift=(\cabwest)]#2);
	\end{scope}
}
	""".strip()
	
	
	# Mapping of directions to names for which tikz references exist.
	DIRECTION_POSTFIX = {
		topology.NORTH      : "north",
		topology.NORTH_EAST : "north east",
		topology.EAST       : "east",
		topology.SOUTH      : "south",
		topology.SOUTH_WEST : "south west",
		topology.WEST       : "west",
	}
	
	
	def __init__(self):
		self.preamble = Diagram.PREAMBLE
		
		# Cabinet definitions. Drawing of each of the cabinets.
		self.cabinet_definitions = ""
		
		# Boards definitions. All boards have a coordinates of the form:
		# board [unique id] {,north,north east,east,south,south west,west}
		self.board_definitions = ""
		
		# Definitions of paths to be drawn
		self.path_definitions = ""
		
		# Definitions of labels added to boards
		self.label_definitions = ""
		
		# The cabinet system the boards are placed in or None if no cabinets used
		self.cabinet_system = None
		self.cabinet_scale = 0.01
	
	
	def get_tikz(self):
		return "\n\n".join((
			self.preamble,
			self.cabinet_definitions,
			self.board_definitions,
			self.path_definitions,
			self.label_definitions,
		))
	
	
	def set_cabinet_system(self, system, scale = 0.01):
		self.cabinet_system = system
		self.cabinet_definitions = ""
		self.cabinet_scale = scale
		
		if self.cabinet_system is None:
			return
		
		cabinet = system.cabinet
		rack    = cabinet.rack
		slot    = rack.slot
		
		self.cabinet_definitions += r"\newcommand{\cabscale}{%f}"%scale
		
		for direction, name in Diagram.DIRECTION_POSTFIX.iteritems():
			position = slot.get_position(direction)
			self.cabinet_definitions += r"\newcommand{\cab%s}{%f,%f}"%(
				"".join(name.split(" ")),
				position[0],
				position[1],
			) + "\n"
		
		
		self.cabinet_definitions += r"\newcommand{\slotwidth}{%f}"%slot.width
		self.cabinet_definitions += r"\newcommand{\slotheight}{%f}"%slot.height
		
		self.cabinet_definitions += r"\begin{scope}[scale=\cabscale]"
		
		for cabinet_num in range(system.num_cabinets):
			cabinet_x = cabinet_num * (cabinet.width + system.cabinet_spacing)
			cabinet_y = 0.0
			# Only bother drawing the cabinet if we have more than one rack
			if cabinet.num_racks > 1:
				self.cabinet_definitions += r"\path [cabinet] (%f,%f) rectangle ++(%f,%f);"%(
					cabinet_x, cabinet_y,
					cabinet.width, cabinet.height
				) + "\n"
			for rack_num in range(cabinet.num_racks):
				rack_x = cabinet_x + cabinet.offset.x
				rack_y = cabinet_y + cabinet.offset.y \
				         + (rack.height + cabinet.rack_spacing) * rack_num
				
				self.cabinet_definitions += r"\path [rack] (%f,%f) rectangle ++(%f,%f);"%(
					rack_x, rack_y,
					rack.width, rack.height
				) + "\n"
				for slot_num in range(rack.num_slots):
					slot_x = rack_x + rack.offset.x \
					         + (slot.width + rack.slot_spacing) * slot_num
					slot_y = rack_y + rack.offset.y
					
					self.cabinet_definitions += r"\path [slot] (%f,%f) rectangle ++(%f,%f);"%(
						slot_x, slot_y,
						slot.width, slot.height
					) + "\n"
		
		self.cabinet_definitions += r"\end{scope}[scale=%f]"%scale
	
	
	def _add_board(self, board, position_str, macro, styles):
		"""
		Used internally. The general form of adding a board.
		"""
		self.board_definitions += r"\%s{board %d}{%s}{%s};"%(
			macro,
			id(board),
			position_str,
			",".join(styles),
		) + "\n"
	
	
	def add_board_hexagon(self, board, position, styles = None):
		"""
		Add a hexagonal board to the design.
		
		board is the board object this represents
		
		position is the hexagonal coordinate or the Cartesian coordinate generated
		by transforms.hex_to_cartesian()
		
		styles is an array of tikz styles to apply to the node
		"""
		styles = styles or []
		
		if isinstance(position, coordinates.Hexagonal):
			position_str  = "%f,%f,%f"%position
			styles       += ["hexagon coords"]
		elif isinstance(position, coordinates.Hexagonal2D):
			position_str  = "%f,%f"%position
			styles       += ["hexagon coords"]
		elif isinstance(position, coordinates.Cartesian2D):
			position_str  = "%f,%f"%position
			styles       += ["cartesian hexagon coords"]
		else:
			raise Exception("Hexagonal{,2D} or Cartesian2D coordinates required.")
		
		
		self._add_board(board, position_str, "hexagon", styles)
	
	
	def add_board_skewed_hexagon(self, board, position, styles = None):
		"""
		Add a skewed hexagonal board to the design.
		
		board is the board object this represents
		
		position is the hexagonal coordinate or the Cartesian coordinate generated
		by transforms.hex_to_cartesian()
		
		styles is an array of tikz styles to apply to the node
		"""
		
		styles = styles or []
		
		if isinstance(position, coordinates.Hexagonal):
			position = topology.hex_to_skewed_cartesian(position)
		elif isinstance(position, coordinates.Hexagonal2D):
			position = topology.hex_to_skewed_cartesian(list(position)+[0])
		elif isinstance(position, coordinates.Cartesian2D):
			pass
		else:
			raise Exception("Hexagonal{,2D} or Cartesian2D coordinates required.")
		
		styles += ["cartesian skewed hexagon coords"]
		
		self._add_board(board, "%f,%f"%position, "skewedhexagon", styles)
	
	
	def add_board_square(self, board, position, styles = None):
		"""
		Add a board drawn as a simple square to the design.
		
		board is the board object this represents
		
		position is the Cartesian coordinate of the rectangle
		
		styles is an array of tikz styles to apply to the node
		"""
		assert(isinstance(position, coordinates.Cartesian2D))
		
		styles = styles or []
		
		self._add_board(board, "%f,%f"%position,
			"square", styles)
	
	
	def add_board_cabinet(self, board, position, styles = None):
		"""
		Add a board to be drawn in the cabinet specified by set_cabinet_system().
		
		board is the board object this represents
		
		position is the Cabinet coordinate of the board
		
		styles is an array of tikz styles to apply to the node
		"""
		assert(self.cabinet_system is not None)
		assert(isinstance(position, coordinates.Cabinet))
		
		styles = styles or []
		
		self._add_board(board, "%f,%f"%(self.cabinet_system.get_position(position)[:2]),
			"cabinet", styles)
	
	
	def add_label(self, board, latex, styles = None):
		"""
		Add a label to the center of the requested board.
		
		styles is an array of tikz styles to apply to the node containing the label
		"""
		styles = styles or []
		
		self.label_definitions += r"\node [%s] at (board %d) {%s};"%(
			",".join(styles),
			id(board),
			latex
		) + "\n"
	
	
	def get_tikz_ref(self, board, direction = None):
		"""
		Get a TikZ reference to a particular board. If no direction is given, a
		reference to the center of the board is given.
		"""
		return (r"board %d %s"%(
			id(board),
			Diagram.DIRECTION_POSTFIX[direction] if direction is not None else ""
		)).strip()
	
	
	def _add_path(self, locations, styles = None):
		"""
		For internal use.
		
		Add a path going between all locations.
		
		arrows enables drawing of arrows on the path segments
		
		styles is an array of tikz styles to apply to the path
		"""
		
		styles = styles or []
		
		self.path_definitions += r"\draw [%s] %s;"%(
			",".join(styles),
			" -- ".join("(%s)"%l for l in locations),
		) + "\n"
	
	
	def add_wire(self, board, direction, styles = None):
		self._add_path(
			[ "board %d %s"%(id(board), Diagram.DIRECTION_POSTFIX[direction])
			, "board %d %s"%( id(board.follow_wire(direction))
			                , Diagram.DIRECTION_POSTFIX[topology.opposite(direction)]
			                )
			],
			styles
		)
	
	
	def add_packet_path(self, board, in_direction, out_direction, styles = None):
		self._add_path(
			[ "board %d %s"%(id(board), Diagram.DIRECTION_POSTFIX[in_direction])
			, "board %d %s"%(id(board), Diagram.DIRECTION_POSTFIX[out_direction])
			],
			styles
		)


if __name__=="__main__":
	d = Diagram()
	boards = board.create_torus(20)
	boards = transforms.hex_to_cartesian(boards)
	b2c = dict(boards)
	boards = transforms.compress(boards)
	boards = transforms.rhombus_to_rect(boards)
	boards = transforms.fold(boards, (4,2))
	
	boards = transforms.cabinetise(boards, 5, 10, 24)
	
	d.set_cabinet_system(cabinet.System(), 0.1)
	
	for board, coords in boards:
		d.add_board_cabinet(board, coords)
		d.add_label(board, r"\tiny %s"%(str(tuple(b2c[board]))), ["rotate=90"])
		d.add_wire(board, topology.NORTH, ["red"])
		d.add_wire(board, topology.EAST, ["green"])
		d.add_wire(board, topology.SOUTH_WEST, ["blue"])
	
	print d.get_tikz()
