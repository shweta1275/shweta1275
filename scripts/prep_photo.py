#!/usr/bin/env python3
"""Prep a photo for ASCII conversion (run locally, once per photo).

1. Remove the background (rembg) so only the subject remains.
2. Boost local contrast with CLAHE so a flatly-lit face gets real
   highlights and shadows instead of converting to a dark blob.
3. Composite onto pure white — the background then maps to the blank
   end of the ASCII ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.jpg
    # writes source-prepped.png next to the repo root
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/prep_photo.py <photo.jpg>")
    src = Path(sys.argv[1])

    # 1. Background removal -> RGBA with transparent background
    img = Image.open(src).convert("RGBA")
    cut = remove(img)

    # 2. Crop to the subject so a small/off-centre figure fills the frame
    rgba = np.array(cut)
    ys, xs = np.where(rgba[:, :, 3] > 20)
    if len(xs):
        pad = int(0.04 * max(xs.max() - xs.min(), ys.max() - ys.min()))
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, rgba.shape[1])
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, rgba.shape[0])
        rgba = rgba[y0:y1, x0:x1]

    # 3. If the figure is much taller than wide (a full-body shot), tighten
    #    to head-and-shoulders — a distant face has too few pixels to survive
    #    the ~100-character downsample. The head is the topmost region of the
    #    alpha mask, so locate it from the mask's upper rows.
    h, w = rgba.shape[:2]
    if h > 1.4 * w:
        head_rows = rgba[: int(0.14 * h), :, 3] > 20
        head_cols = np.where(head_rows.any(axis=0))[0]
        if len(head_cols):
            cx = int(head_cols.mean())
            head_w = head_cols.max() - head_cols.min()
            half = max(int(1.4 * head_w), int(0.14 * h))
            x0, x1 = max(cx - half, 0), min(cx + half, w)
            rgba = rgba[: int(0.42 * h), x0:x1]

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 4. Composite onto white using the alpha mask
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    out = (gray.astype(np.float32) * alpha + 255.0 * (1.0 - alpha)).astype(np.uint8)

    Image.fromarray(out, mode="L").save(OUT)
    print(f"Wrote {OUT.name} ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
