"""Renders a preview image of the built font for the README.

The font size is a whole multiple of the font's pixel grid and anti-aliasing is off, so every font pixel is a crisp square.

Usage: python tools/preview.py (after tools/build.py)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import layout

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "build" / "8-bit-fortress-modded.ttf"
OUTPUT = ROOT / "build" / "preview.png"

SCALE = 4
MARGIN = 3 * SCALE
LINE_HEIGHT = (layout.GLYPH_ROWS + 3) * SCALE

LINES = [
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789",
    "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    "",
    "Five big quacking zephyrs jolt my wax bed.",
    "The quick brown fox jumps over the lazy dog!",
    "x = (a + b) / 2;  y <= 10 - z  {[100%]}",
]

TEXT_COLOR = (0, 0, 0)
BACKGROUND_COLOR = (255, 255, 255)


def main():
    font = ImageFont.truetype(FONT, layout.ASCENT_PIXELS * SCALE)
    width = max(int(font.getlength(line)) for line in LINES) + 2 * MARGIN
    height = len(LINES) * LINE_HEIGHT + 2 * MARGIN - 3 * SCALE

    image = Image.new("RGB", (width, height), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    for index, line in enumerate(LINES):
        draw.text((MARGIN, MARGIN + index * LINE_HEIGHT), line, font=font, fill=TEXT_COLOR)

    image.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
