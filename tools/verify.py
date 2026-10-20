"""Checks the built font against the glyph sheet, and lists how it differs from the original font.

1. Every glyph of the built font must have exactly the sheet's pixels and advance width, so the build loses nothing.
2. Every character whose pixels or advance width differ from the original font (snapped to whole pixels) is listed.

Usage: python tools/verify.py (after tools/build.py)
"""

import sys

from fontTools.ttLib import TTFont

import build
import extract
import raster


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sheet_glyphs, errors = build.read_cells(build.read_sheet())
    if errors:
        sys.exit("The glyph sheet has errors, run tools/build.py to see them")

    built = TTFont(build.OUTPUT)
    mismatches = compare_built_font(built, sheet_glyphs)
    if mismatches:
        print("The built font doesn't match the glyph sheet:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        sys.exit(1)
    print(f"The built font matches the glyph sheet ({len(sheet_glyphs)} glyphs)")

    print("Differences from the original font:")
    for difference in compare_original_font(TTFont(extract.FONT), built):
        print(f"  {difference}")


def compare_built_font(built, sheet_glyphs):
    glyph_set = built.getGlyphSet()
    character_map = built.getBestCmap()
    mismatches = []
    for sheet_glyph in sheet_glyphs:
        name = build.glyph_name(sheet_glyph.code)
        if sheet_glyph.code != build.layout.NOTDEF_CODE and character_map.get(sheet_glyph.code) != name:
            mismatches.append(f"{build.cell_name(sheet_glyph.code)}: not mapped")
            continue
        if raster.glyph_pixels(glyph_set[name]) != sheet_glyph.pixels:
            mismatches.append(f"{build.cell_name(sheet_glyph.code)}: pixels differ")
        if built["hmtx"][name][0] != build.layout.pixel_to_units(sheet_glyph.advance):
            mismatches.append(f"{build.cell_name(sheet_glyph.code)}: advance width differs")
    return mismatches


def compare_original_font(original, built):
    original_map = original.getBestCmap()
    built_map = built.getBestCmap()
    original_glyphs = original.getGlyphSet()
    built_glyphs = built.getGlyphSet()
    differences = []
    for code in sorted(set(original_map) | set(built_map)):
        label = build.cell_name(code)
        if code not in built_map:
            differences.append(f"{label}: removed")
            continue
        if code not in original_map:
            differences.append(f"{label}: added")
            continue

        original_name = original_map[code]
        built_name = built_map[code]
        if raster.glyph_pixels(original_glyphs[original_name]) != raster.glyph_pixels(built_glyphs[built_name]):
            differences.append(f"{label}: pixels changed")
        original_advance = original["hmtx"][original_name][0]
        built_advance = built["hmtx"][built_name][0]
        if original_advance != built_advance:
            differences.append(f"{label}: advance width {original_advance} -> {built_advance} units")
    return differences


if __name__ == "__main__":
    main()
