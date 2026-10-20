"""Builds the font from the glyph sheet PNG.

Reads every cell of src/8-bit-fortress.png (see tools/layout.py and src/layout.txt):
- any cyan pixel: the character isn't in the font
- otherwise black pixels are the glyph and the magenta pixel in the marker row is its advance width
Each glyph's pixels are traced into outlines along the pixel edges.
Font-wide settings (names, metrics) are below, mostly copied from the original font.

Usage: python tools/build.py
"""

import sys
from pathlib import Path

from fontTools.agl import UV2AGL
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image

import layout

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "src" / "8-bit-fortress.png"
OUTPUT = ROOT / "build" / "8-bit-fortress-modded.ttf"

FAMILY_NAME = "8-bit Fortress Modded"
POSTSCRIPT_NAME = "8-bitFortressModded"
VERSION = 1.1

NAMES = {
    "copyright": "Copyright (c) 2024, Fortress Tech. Modifications copyright (c) 2026, RudyTheDev.",
    "familyName": FAMILY_NAME,
    "styleName": "Regular",
    "uniqueFontIdentifier": f"{FAMILY_NAME} Regular {VERSION:.3f}",
    "fullName": f"{FAMILY_NAME} Regular",
    "version": f"Version {VERSION:.3f}",
    "psName": POSTSCRIPT_NAME,
    "designer": "Fortress Tech",
    "description": "Based on 8-bit Fortress by Fortress Tech, built with FontStruct, with glyphs added and edited",
    "designerURL": "https://www.dafont.com/8-bit-fortress.font",
    "licenseDescription": "This Font Software is licensed under the SIL Open Font License, Version 1.1.",
    "licenseInfoURL": "https://openfontlicense.org",
    "sampleText": "Five big quacking zephyrs jolt my wax bed",
}

# Original's creation time, used for both timestamps so builds are reproducible
TIMESTAMP = 3806288933


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sheet = read_sheet()
    glyphs, errors = read_cells(sheet)
    if errors:
        print("The glyph sheet has errors, nothing was built:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)

    font = build_font(glyphs)
    OUTPUT.parent.mkdir(exist_ok=True)
    font.save(OUTPUT)
    print(f"Wrote {OUTPUT} with {len(glyphs)} glyphs")


class SheetGlyph:
    def __init__(self, code, pixels, advance):
        self.code = code
        # (x, y) with y above the baseline, -1 is below it
        self.pixels = pixels
        self.advance = advance


def read_sheet():
    sheet = Image.open(SHEET).convert("RGBA")
    if sheet.size != (layout.SHEET_WIDTH, layout.SHEET_HEIGHT):
        sys.exit(f"{SHEET} is {sheet.size[0]}x{sheet.size[1]}, expected {layout.SHEET_WIDTH}x{layout.SHEET_HEIGHT}")
    return sheet


def read_cells(sheet):
    """SheetGlyph of every cell that holds a character, and a list of error messages"""
    glyphs = []
    errors = []
    for code, cell_x, cell_y in layout.cells():
        glyph = read_cell(sheet, code, cell_x, cell_y, errors)
        if glyph is not None:
            glyphs.append(glyph)
    return glyphs, errors


def read_cell(sheet, code, cell_x, cell_y, errors):
    pixels = set()
    advances = []
    is_missing = False
    cell_errors = []
    for glyph_row in range(layout.CELL_HEIGHT):
        for x in range(layout.CELL_WIDTH):
            sheet_x = cell_x + x
            sheet_y = cell_y + glyph_row
            color = pixel_color(sheet, sheet_x, sheet_y)
            if color in layout.GUIDE_COLORS:
                continue

            in_marker_row = glyph_row == layout.MARKER_ROW
            if color == layout.MISSING_MARKER:
                is_missing = True
            elif color == layout.INK and not in_marker_row:
                pixels.add((x, layout.glyph_row_to_pixel_y(glyph_row)))
            elif color == layout.ADVANCE_MARKER and in_marker_row:
                advances.append(x)
            else:
                cell_errors.append(f"unexpected color {color} at x {sheet_x}, y {sheet_y}")

    if is_missing:
        return None

    label = f"{cell_name(code)} (cell at x {cell_x}, y {cell_y}):"
    if len(advances) != 1:
        cell_errors.append(f"needs exactly one magenta advance marker in its bottom row, found {len(advances)}")
    errors.extend(f"{label} {error}" for error in cell_errors)
    if cell_errors:
        return None
    return SheetGlyph(code, pixels, advances[0])


def pixel_color(sheet, x, y):
    red, green, blue, alpha = sheet.getpixel((x, y))
    # Transparent pixels count as background, whatever color they hold
    if alpha == 0:
        return layout.BACKGROUND
    return red, green, blue


def cell_name(code):
    if code == layout.NOTDEF_CODE:
        return ".notdef"
    if code > 0xFF:
        return f"U+{code:04X}"
    return f"U+{code:04X} '{chr(code)}'"


def glyph_name(code):
    if code == layout.NOTDEF_CODE:
        return ".notdef"
    return UV2AGL.get(code, f"uni{code:04X}")


def build_font(glyphs):
    glyphs = sorted(glyphs, key=lambda glyph: (glyph.code != layout.NOTDEF_CODE, glyph.code))
    if glyphs[0].code != layout.NOTDEF_CODE:
        sys.exit(".notdef (the cell of 0x7F) must hold a glyph")

    builder = FontBuilder(layout.UNITS_PER_EM, isTTF=True)
    builder.font.recalcTimestamp = False
    builder.updateHead(fontRevision=VERSION, created=TIMESTAMP, modified=TIMESTAMP, lowestRecPPEM=8)
    builder.setupGlyphOrder([glyph_name(glyph.code) for glyph in glyphs])
    builder.setupCharacterMap({glyph.code: glyph_name(glyph.code) for glyph in glyphs if glyph.code != layout.NOTDEF_CODE})
    builder.setupGlyf({glyph_name(glyph.code): outline(glyph.pixels) for glyph in glyphs})

    glyf = builder.font["glyf"]
    builder.setupHorizontalMetrics({
        glyph_name(glyph.code): (layout.pixel_to_units(glyph.advance), getattr(glyf[glyph_name(glyph.code)], "xMin", 0))
        for glyph in glyphs
    })
    builder.setupHorizontalHeader(ascent=layout.pixel_to_units(layout.ASCENT_PIXELS), descent=layout.pixel_to_units(-layout.DESCENT_PIXELS))
    builder.setupNameTable(NAMES)
    builder.setupOS2(
        version=2,
        usWeightClass=400,
        usWidthClass=5,
        # Preview & print embedding, as in the original
        fsType=4,
        ySubscriptXSize=1024,
        ySubscriptYSize=1024,
        ySubscriptYOffset=-146,
        ySuperscriptXSize=1024,
        ySuperscriptYSize=1024,
        ySuperscriptYOffset=1024,
        yStrikeoutSize=102,
        yStrikeoutPosition=409,
        sTypoAscender=layout.pixel_to_units(6),
        sTypoDescender=layout.pixel_to_units(-layout.DESCENT_PIXELS),
        sTypoLineGap=0,
        usWinAscent=layout.pixel_to_units(layout.ASCENT_PIXELS),
        usWinDescent=layout.pixel_to_units(layout.DESCENT_PIXELS),
        sxHeight=layout.pixel_to_units(5),
        sCapHeight=layout.pixel_to_units(6),
        usDefaultChar=0,
        usBreakChar=0x20,
        fsSelection=0x40,
    )
    builder.font["OS/2"].recalcUnicodeRanges(builder.font)
    builder.font["OS/2"].recalcCodePageRanges(builder.font)
    builder.setupPost(underlinePosition=204, underlineThickness=102)
    return builder.font


def outline(pixels):
    """TrueType glyph tracing the edges of the filled pixels into contours, clockwise around ink"""
    pen = TTGlyphPen(None)
    for contour in trace_contours(pixels):
        pen.moveTo(to_units(contour[0]))
        for point in contour[1:]:
            pen.lineTo(to_units(point))
        pen.closePath()
    return pen.glyph()


def to_units(point):
    return layout.pixel_to_units(point[0]), layout.pixel_to_units(point[1])


def trace_contours(pixels):
    """Contours as lists of corner points, following pixel edges that have ink on their right"""
    # Each edge between a filled and an empty pixel, directed so ink is on its right
    edges = {}
    for x, y in pixels:
        if (x - 1, y) not in pixels:
            edges.setdefault((x, y), []).append((x, y + 1))
        if (x, y + 1) not in pixels:
            edges.setdefault((x, y + 1), []).append((x + 1, y + 1))
        if (x + 1, y) not in pixels:
            edges.setdefault((x + 1, y + 1), []).append((x + 1, y))
        if (x, y - 1) not in pixels:
            edges.setdefault((x + 1, y), []).append((x, y))

    contours = []
    while edges:
        start = min(edges)
        contour = [start]
        previous = start
        current = take_edge(edges, start, None)
        while current != start:
            contour.append(current)
            direction = (current[0] - previous[0], current[1] - previous[1])
            previous, current = current, take_edge(edges, current, direction)
        contours.append(remove_straight_points(contour))
    return contours


def take_edge(edges, start, direction):
    """Removes and returns the end of an edge leaving start; where two pixels touch diagonally, turns right to keep them apart"""
    ends = edges[start]
    if direction is not None and len(ends) > 1:
        right_turn = (start[0] + direction[1], start[1] - direction[0])
        end = right_turn if right_turn in ends else ends[0]
    else:
        end = ends[0]
    ends.remove(end)
    if not ends:
        del edges[start]
    return end


def remove_straight_points(contour):
    corners = []
    for index, point in enumerate(contour):
        before = contour[index - 1]
        after = contour[(index + 1) % len(contour)]
        is_straight = (point[0] - before[0]) * (after[1] - point[1]) == (point[1] - before[1]) * (after[0] - point[0])
        if not is_straight:
            corners.append(point)
    return corners


if __name__ == "__main__":
    main()
