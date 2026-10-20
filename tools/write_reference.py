"""Writes src/layout.txt, a text map of which character each glyph sheet cell holds.

Usage: python tools/write_reference.py
"""

from pathlib import Path

import layout

OUTPUT = Path(__file__).resolve().parent.parent / "src" / "layout.txt"

# Cells whose character is invisible or not a character
SPECIAL_LABELS = {
    0x20: "SP",
    layout.NOTDEF_CODE: "ND",
    0xA0: "NBSP",
    0xAD: "SHY",
}

COLUMN_TEXT_WIDTH = 5


def main():
    lines = [
        "Glyph sheet layout of src/8-bit-fortress.png",
        "",
        "Each cell shows the character it holds if drawn. A cell's code point is its row's code point plus its column.",
        "x and y are the pixel coordinates of the cell's top left corner in the PNG.",
        "",
        "SP   = space",
        "ND   = .notdef, the box shown for characters the font doesn't have (the cell of DEL, 0x7F)",
        "NBSP = no-break space",
        "SHY  = soft hyphen",
        "",
        header_line("", lambda column: f"{column:X}"),
        header_line("x", lambda column: str(1 + column * (layout.CELL_WIDTH + 1))),
        "",
    ]
    for row, first_code in enumerate(layout.SHEET_ROWS):
        y = 1 + row * (layout.CELL_HEIGHT + 1)
        label = f"0x{first_code:02X} y{y}"
        lines.append(header_line(label, lambda column: cell_label(first_code + column)))

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8", newline="\r\n") as file:
        file.write("\n".join(lines) + "\n")
    print(f"Wrote {OUTPUT}")


def header_line(label, column_text):
    return f"{label:<10}" + "".join(f"{column_text(column):<{COLUMN_TEXT_WIDTH}}" for column in range(layout.COLUMNS)).rstrip()


def cell_label(code):
    return SPECIAL_LABELS.get(code, chr(code))


if __name__ == "__main__":
    main()
