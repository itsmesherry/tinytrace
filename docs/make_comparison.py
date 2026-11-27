"""Make docs/images/comparison.jpg: one picture, then vtracer and tinytrace SVGs of it at the same budget.

Usage: python docs/make_comparison.py   (needs pip install -e ".[bench]" and resvg on PATH)

vtracer gets the same fair search over its own settings as the benchmark (bench/vtracer_fair.py). The top row shows
the whole frame, the bottom row a zoom where the difference is easiest to see.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

import tinytrace

DOCS = Path(__file__).parent
sys.path.insert(0, str(DOCS.parent / "bench"))
import vtracer_fair  # noqa: E402

SAMPLE = DOCS / "samples" / "bunny.jpg"
BUDGET = 125_000
PANEL = 640
# The zoom, as shares of the frame: left, top, width (the height follows the frame's shape).
ZOOM = (0.21, 0.24, 0.3)


def render(svg: str, width: int, height: int) -> NDArray[np.uint8]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "in.svg"
        path.write_text(svg)
        subprocess.run(["resvg", "-w", str(width * 3), str(path), str(Path(tmp) / "out.png")], check=True)
        big = cv2.imread(str(Path(tmp) / "out.png"))
    return cv2.resize(big, (width * 3, height * 3), interpolation=cv2.INTER_AREA)


def label(img: NDArray[np.uint8], text: str) -> NDArray[np.uint8]:
    img = img.copy()
    cv2.putText(img, text, (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(img, text, (14, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
    return img


def main() -> None:
    src = cv2.imread(str(SAMPLE))
    h, w = src.shape[:2]
    ph = round(PANEL * h / w)
    ours = tinytrace.trace(src, budget=BUDGET)
    theirs = vtracer_fair.trace(str(SAMPLE), BUDGET)
    if theirs is None:
        sys.exit("vtracer could not fit the budget")
    # Each version at 3x the panel size, so the zoom stays sharp.
    big = [
        cv2.resize(src, (PANEL * 3, ph * 3), interpolation=cv2.INTER_AREA),
        render(theirs, PANEL, ph),
        render(ours, PANEL, ph),
    ]
    names = ["picture", f"vtracer, {len(theirs):,} characters", f"tinytrace, {len(ours):,} characters"]
    zw = round(ZOOM[2] * PANEL * 3)
    x0, y0 = round(ZOOM[0] * PANEL * 3), round(ZOOM[1] * ph * 3)
    zh = round(zw * ph / PANEL)
    gap = np.full((ph, 8, 3), 255, np.uint8)
    top = [label(cv2.resize(b, (PANEL, ph), interpolation=cv2.INTER_AREA), n) for b, n in zip(big, names)]
    zoom = [
        label(cv2.resize(b[y0 : y0 + zh, x0 : x0 + zw], (PANEL, ph), interpolation=cv2.INTER_CUBIC), "zoomed in")
        for b in big
    ]
    rows = [np.hstack([top[0], gap, top[1], gap, top[2]]), np.hstack([zoom[0], gap, zoom[1], gap, zoom[2]])]
    sheet = np.vstack([rows[0], np.full((8, rows[0].shape[1], 3), 255, np.uint8), rows[1]])
    out = DOCS / "images" / "comparison.jpg"
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f"{out.name}: vtracer {len(theirs):,}, tinytrace {len(ours):,} characters")


if __name__ == "__main__":
    main()
