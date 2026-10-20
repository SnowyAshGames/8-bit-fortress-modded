"""Draws the original font's glyphs into a glyph sheet PNG, kept as a reference of the original next to the edited sheet.

Each pixel is filled if its center is inside the glyph outline, so outlines off the pixel grid get snapped to it.
Advance widths are rounded to whole pixels, half up.
The original .notdef is a box with hairline borders thinner than a pixel, so it's drawn as a plain hollow box instead.

Usage: python tools/extract.py
"""

from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

import layout
import raster

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "original" / "8-bit-fortress.ttf"
OUTPUT = ROOT / "reference" / "8-bit-fortress-original.png"


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

        pixels = notdef_box_pixels() if code == layout.NOTDEF_CODE else raster.glyph_pixels(glyph_set[glyph_name])
        for x, y in pixels:
            sheet.putpixel((cell_x + x, cell_y + layout.pixel_y_to_glyph_row(y)), layout.INK)
        advance = raster.advance_pixels(font["hmtx"][glyph_name][0])
        sheet.putpixel((cell_x + advance, cell_y + layout.MARKER_ROW), layout.ADVANCE_MARKER)

    sheet_codes = {code for code, _, _ in layout.cells()}
    dropped = [f"U+{code:04X}" for code in character_map if code not in sheet_codes]
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


def notdef_box_pixels():
    """Hollow box covering the original's outline, 4 pixels wide and 6 tall on the baseline"""
    width = 4
    height = 6
    return {(x, y) for x in range(width) for y in range(height) if x in (0, width - 1) or y in (0, height - 1)}


if __name__ == "__main__":
    main()
