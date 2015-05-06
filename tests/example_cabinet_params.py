"""Cabinet parameter sets used in multiple tests."""

from spinner.topology import Direction

# Map from board wire offset parameter names to their corresponding direction
# enum value to enable easy lookup
board_wire_offset_fields = {
	"board_wire_offset_south_west": Direction.south_west,
	"board_wire_offset_north_east": Direction.north_east,
	"board_wire_offset_east": Direction.east,
	"board_wire_offset_west": Direction.west,
	"board_wire_offset_north": Direction.north,
	"board_wire_offset_south": Direction.south,
}


# A set of values of which all are unique
unique = {"board_dimensions": (0.1, 0.2, 0.3),
          "board_wire_offset_south_west": (0.01,0.001,0.0001),
          "board_wire_offset_north_east": (0.02,0.002,0.0002),
          "board_wire_offset_east": (0.03,0.003,0.0003),
          "board_wire_offset_west": (0.04,0.004,0.0004),
          "board_wire_offset_north": (0.05,0.005,0.0005),
          "board_wire_offset_south": (0.06,0.006,0.0006),
          "inter_board_spacing": 0.123,
          "boards_per_frame": 2,
          "frame_dimensions": (1.0, 2.0, 3.0),
          "frame_board_offset": (0.11, 0.22, 0.33),
          "inter_frame_spacing": 0.321,
          "frames_per_cabinet": 3,
          "cabinet_dimensions": (10.0, 20.0, 30.0),
          "cabinet_frame_offset": (0.111, 0.222, 0.333),
          "inter_cabinet_spacing": 3.21}

# A set of values where everything *exactly* fits
exact = {"board_dimensions": (1, 1, 1),
         "board_wire_offset_south_west": (0.0, 0.0, 0.0),
         "board_wire_offset_north_east": (1.0, 0.0, 0.0),
         "board_wire_offset_east": (0.0, 1.0, 0.0),
         "board_wire_offset_west": (0.0, 0.0, 1.0),
         "board_wire_offset_north": (0.5, 0.5, 0.5),
         "board_wire_offset_south": (1.0, 1.0, 1.0),
         "inter_board_spacing": 0.5,
         "boards_per_frame": 10,
         "frame_dimensions": (15.5, 2.0, 2.0),
         "frame_board_offset": (1.0, 1.0, 1.0),
         "inter_frame_spacing": 1.0,
         "frames_per_cabinet": 2,
         "cabinet_dimensions": (16.5, 6.0, 3.0),
         "cabinet_frame_offset": (1.0, 1.0, 1.0),
         "inter_cabinet_spacing": 10.0}

# A set of values which are well within the required bounds
within = {"board_dimensions": (1.0, 1.0, 1.0),
          "board_wire_offset_south_west": (0.5, 0.1, 0.0),
          "board_wire_offset_north_east": (0.5, 0.2, 0.0),
          "board_wire_offset_east": (0.5, 0.3, 0.0),
          "board_wire_offset_west": (0.5, 0.4, 0.0),
          "board_wire_offset_north": (0.5, 0.5, 0.0),
          "board_wire_offset_south": (0.5, 0.6, 0.0),
          "inter_board_spacing": 0.5,
          "boards_per_frame": 10,
          "frame_dimensions": (16.5, 3.0, 3.0),
          "frame_board_offset": (1.0, 1.0, 1.0),
          "inter_frame_spacing": 1.0,
          "frames_per_cabinet": 2,
          "cabinet_dimensions": (18.5, 9.0, 5.0),
          "cabinet_frame_offset": (1.0, 1.0, 1.0),
          "inter_cabinet_spacing": 10.0}
