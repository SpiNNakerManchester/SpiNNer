#!/usr/bin/env python

"""Generate maps from topological positions to physical locations."""

import argparse

from spinner.diagrams.machine_map import draw_machine_map, \
    get_machine_map_aspect_ratio

from spinner.utils import folded_torus

from spinner import transforms

from spinner.scripts import arguments
from spinner.scripts.contexts import PDFContextManager, PNGContextManager


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Generate visual maps from the SpiNNaker network topology to "
                    "board locations.")
    arguments.add_version_args(parser)
    arguments.add_image_args(parser)
    arguments.add_topology_args(parser)
    arguments.add_cabinet_args(parser)

    # Process command-line arguments
    args = parser.parse_args(args)
    (w, h), transformation, uncrinkle_direction, folds =\
        arguments.get_topology_from_args(parser, args)

    cabinet, num_frames = arguments.get_cabinets_from_args(parser, args)

    aspect_ratio = get_machine_map_aspect_ratio(w, h)

    output_filename, file_type, image_width, image_height =\
        arguments.get_image_from_args(parser, args, aspect_ratio)

    # Generate folded system
    hex_boards, folded_boards = folded_torus(w, h,
                                             transformation,
                                             uncrinkle_direction,
                                             folds)

    # Divide into cabinets
    cabinetised_boards = transforms.cabinetise(folded_boards,
                                               cabinet.num_cabinets,
                                               num_frames,
                                               cabinet.boards_per_frame)
    cabinetised_boards = transforms.remove_gaps(cabinetised_boards)

    # Render the image
    Context = {"png": PNGContextManager, "pdf": PDFContextManager}[file_type]
    with Context(output_filename, image_width, image_height) as ctx:
        draw_machine_map(ctx, image_width, image_height,
                         w, h, hex_boards, cabinetised_boards)

    return 0


if __name__=="__main__":  # pragma: no cover
    import sys
    sys.exit(main())

