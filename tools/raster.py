"""Turns font glyph outlines into pixels on the font's pixel grid."""

import math

from fontTools.pens.pointInsidePen import PointInsidePen

import layout


def glyph_pixels(glyph):
    """(x, y) of every pixel whose center is inside the glyph outline; y is above the baseline, so -1 is below it"""
    pixels = set()
    for glyph_row in range(layout.GLYPH_ROWS):
        y = layout.glyph_row_to_pixel_y(glyph_row)
        for x in range(layout.CELL_WIDTH):
            center = (layout.pixel_to_units(x + 0.5), layout.pixel_to_units(y + 0.5))
            pen = PointInsidePen(None, center)
            glyph.draw(pen)
            if pen.getResult():
                pixels.add((x, y))
    return pixels


def advance_pixels(advance_units):
    """Advance width rounded to whole pixels, half up"""
    return math.floor(layout.units_to_pixel(advance_units) + 0.5)
