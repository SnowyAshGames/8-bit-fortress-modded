"""Draws the original font's glyphs into a new glyph sheet PNG. Run once to create the starting sheet.

Each pixel is filled if its center is inside the glyph outline, so outlines off the pixel grid get snapped to it.
Advance widths are rounded to whole pixels, half up.
The original .notdef is a box with hairline borders thinner than a pixel, so it's drawn as a plain hollow box instead.

Usage: python tools/extract.py
"""

import math
from pathlib import Path

from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.ttLib import TTFont
from PIL import Image

import layout

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "original" / "8-bit-fortress.ttf"
OUTPUT = ROOT / "src" / "8-bit-fortress.png"


def main():
    font = TTFont(FONT)
    glyph_set = font.getGlyphSet()
    character_map = font.getBestCmap()

    sheet = new_sheet()
    for code, cell_x, cell_y in layout.cells():
        glyph_name = ".notdef" if code == layout.NOTDEF_CODE else character_map.get(code)
        if glyph_name is None:
            sheet.putpixel((cell_x, cell_y), layout.MISSING_MARKER)
            continue

        if code == layout.NOTDEF_CODE:
            draw_notdef_box(sheet, cell_x, cell_y)
        else:
            draw_glyph(sheet, cell_x, cell_y, glyph_set[glyph_name])
        advance = math.floor(layout.units_to_pixel(font["hmtx"][glyph_name][0]) + 0.5)
        sheet.putpixel((cell_x + advance, cell_y + layout.MARKER_ROW), layout.ADVANCE_MARKER)

    dropped = [f"U+{code:04X}" for code in character_map if code not in {code for code, _, _ in layout.cells()}]
    if dropped:
        print(f"Not in the sheet layout, dropped: {' '.join(dropped)}")

    OUTPUT.parent.mkdir(exist_ok=True)
    sheet.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


def new_sheet():
    sheet = Image.new("RGB", (layout.SHEET_WIDTH, layout.SHEET_HEIGHT), layout.GRID_LINE)
    for _, cell_x, cell_y in layout.cells():
        for glyph_row in range(layout.CELL_HEIGHT):
            for x in range(layout.CELL_WIDTH):
                sheet.putpixel((cell_x + x, cell_y + glyph_row), layout.guide_color(glyph_row))
    return sheet


def draw_glyph(sheet, cell_x, cell_y, glyph):
    for glyph_row in range(layout.GLYPH_ROWS):
        pixel_y = layout.glyph_row_to_pixel_y(glyph_row)
        for x in range(layout.CELL_WIDTH):
            center = (layout.pixel_to_units(x + 0.5), layout.pixel_to_units(pixel_y + 0.5))
            pen = PointInsidePen(None, center)
            glyph.draw(pen)
            if pen.getResult():
                sheet.putpixel((cell_x + x, cell_y + glyph_row), layout.INK)


def draw_notdef_box(sheet, cell_x, cell_y):
    """Hollow box covering the original's outline, 4 pixels wide and 6 tall on the baseline"""
    width = 4
    height = 6
    top_row = layout.ASCENT_PIXELS - height
    for glyph_row in range(top_row, top_row + height):
        for x in range(width):
            if glyph_row in (top_row, top_row + height - 1) or x in (0, width - 1):
                sheet.putpixel((cell_x + x, cell_y + glyph_row), layout.INK)


if __name__ == "__main__":
    main()
