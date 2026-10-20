"""Shared layout of the glyph sheet PNG and the font's pixel grid.

The sheet is a grid of cells, 16 per row. A cell's position decides its character:
the rows in SHEET_ROWS each start at a code point and hold the next 16 code points.

Each cell is CELL_WIDTH pixels wide and CELL_HEIGHT tall:
- GLYPH_ROWS rows of glyph pixels, ASCENT_PIXELS above the baseline and DESCENT_PIXELS below
- one marker row underneath, holding the magenta advance-width marker

Cells are separated (and the sheet framed) by 1 pixel grid lines.
"""

UNITS_PER_EM = 2048
ASCENT_PIXELS = 7
DESCENT_PIXELS = 1
GLYPH_ROWS = ASCENT_PIXELS + DESCENT_PIXELS

COLUMNS = 16
CELL_WIDTH = 12
CELL_HEIGHT = GLYPH_ROWS + 1
MARKER_ROW = GLYPH_ROWS

# Each sheet row's first code point
SHEET_ROWS = [0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0, 0xF0]

# DEL is never printed, so its cell holds .notdef, the glyph shown for missing characters
NOTDEF_CODE = 0x7F

SHEET_WIDTH = COLUMNS * (CELL_WIDTH + 1) + 1
SHEET_HEIGHT = len(SHEET_ROWS) * (CELL_HEIGHT + 1) + 1

INK = (0, 0, 0)
ADVANCE_MARKER = (255, 0, 255)
MISSING_MARKER = (0, 255, 255)

# Guide colors, ignored when reading the sheet
GRID_LINE = (128, 128, 128)
BACKGROUND = (255, 255, 255)
DESCENT_BACKGROUND = (220, 230, 255)
MARKER_BACKGROUND = (235, 235, 235)
GUIDE_COLORS = {GRID_LINE, BACKGROUND, DESCENT_BACKGROUND, MARKER_BACKGROUND}


def pixel_to_units(pixels):
    """Font units of a pixel coordinate, truncated like the original FontStruct export (1 pixel = 292, 3 = 877)"""
    return int(pixels * UNITS_PER_EM / ASCENT_PIXELS)


def units_to_pixel(units):
    return units * ASCENT_PIXELS / UNITS_PER_EM


def cells():
    """(code point, cell left x, cell top y) for every cell in the sheet"""
    for row, first_code in enumerate(SHEET_ROWS):
        for column in range(COLUMNS):
            yield first_code + column, 1 + column * (CELL_WIDTH + 1), 1 + row * (CELL_HEIGHT + 1)


def glyph_row_to_pixel_y(glyph_row):
    """Pixel y above the baseline of a cell's glyph row; row 0 is the top, the bottom row is below the baseline (-1)"""
    return ASCENT_PIXELS - 1 - glyph_row


def guide_color(glyph_row):
    if glyph_row == MARKER_ROW:
        return MARKER_BACKGROUND
    if glyph_row >= ASCENT_PIXELS:
        return DESCENT_BACKGROUND
    return BACKGROUND
