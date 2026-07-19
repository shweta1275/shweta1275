#!/usr/bin/env python3
"""Convert source-prepped.png into a self-typing monochrome ASCII SVG.

Each pixel's brightness picks a glyph from a density ramp (bright ->
sparse, dark -> dense). Each row is wrapped in a horizontal clip that
wipes left-to-right with a small block cursor riding the edge, staggered
top to bottom. Prints once and freezes — SMIL, so GitHub plays it.

Usage:
    python scripts/make_ascii_svg.py            # writes avi-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"

# bright (sparse) -> dark (dense); leading space clears the background
RAMP = " .`:-=+*cs#%@"

COLS = 100
CHAR_W = 7.2       # monospace cell width at font-size 12
CHAR_H = 13.2      # line height
FG = "#c9d1d9"     # one light-gray fill — monochrome on purpose
FONT = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

ROW_DUR = 0.08     # seconds each row takes to wipe in
ROW_STAGGER = ROW_DUR  # rows type sequentially so one cursor can ride the edge

STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    if not SRC.exists():
        raise SystemExit("source-prepped.png not found — run prep_photo.py first.")

    img = Image.open(SRC).convert("L")
    # Character cells are taller than wide, so squash rows to keep proportions
    rows = max(1, round(img.height / img.width * COLS * (CHAR_W / CHAR_H)))
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = np.asarray(img, dtype=np.float32) / 255.0

    # brightness 1.0 -> ramp[0] (space), 0.0 -> ramp[-1] (dense)
    idx = ((1.0 - px) * (len(RAMP) - 1)).round().astype(int)
    lines = ["".join(RAMP[i] for i in row).rstrip() for row in idx]

    width = round(COLS * CHAR_W)
    height = round(rows * CHAR_H) + 8

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="ASCII portrait">',
        "<defs>",
    ]

    # One clip rect per row, animated 0 -> full width
    for r in range(rows):
        if STATIC:
            svg.append(
                f'<clipPath id="c{r}"><rect x="0" y="0" width="{width}" '
                f'height="{CHAR_H}"/></clipPath>'
            )
        else:
            begin = f"{r * ROW_STAGGER:.3f}s"
            svg.append(
                f'<clipPath id="c{r}"><rect x="0" y="0" width="0" height="{CHAR_H}">'
                f'<animate attributeName="width" from="0" to="{width}" '
                f'begin="{begin}" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
    svg.append("</defs>")

    for r, line in enumerate(lines):
        if not line:
            continue
        y = round(r * CHAR_H)
        svg.append(
            f'<g clip-path="url(#c{r})" transform="translate(0,{y})">'
            f'<text x="0" y="{CHAR_H - 3:.1f}" xml:space="preserve" '
            f'font-family="{FONT}" font-size="12" fill="{FG}" '
            f'textLength="{len(line) * CHAR_W:.1f}" lengthAdjust="spacingAndGlyphs"'
            f">{esc(line)}</text></g>"
        )

    # Block cursor riding each row's wipe edge, top to bottom
    if not STATIC:
        total = rows * ROW_DUR
        y_steps = ";".join(f"{r * CHAR_H:.1f}" for r in range(rows))
        svg.append(
            f'<rect x="0" y="0" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" fill="{FG}">'
            f'<animate attributeName="x" from="0" to="{width}" dur="{ROW_DUR}s" '
            f'begin="0s" repeatCount="{rows}"/>'
            f'<animate attributeName="y" values="{y_steps}" calcMode="discrete" '
            f'dur="{total:.2f}s" begin="0s" fill="freeze"/>'
            f'<animate attributeName="opacity" to="0" begin="{total:.2f}s" '
            f'dur="0.01s" fill="freeze"/></rect>'
        )

    svg.append("</svg>")
    OUT.write_text("\n".join(svg))
    print(f"Wrote {OUT.name} ({width}x{height}, {rows} rows)")


if __name__ == "__main__":
    main()
