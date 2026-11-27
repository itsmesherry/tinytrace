"""vtracer given a fair shot at a size budget.

vtracer has no budget setting, and squeezing its output down afterwards wrecks it. So try its own detail
settings (input width, speck size, stacked or cutout) and keep the most detailed result that fits by itself.
"""

from __future__ import annotations

import os
import tempfile

import cv2
import vtracer


def trace(picture: str, budget: int) -> str | None:
    src = cv2.imread(picture)
    best: str | None = None
    with tempfile.TemporaryDirectory() as tmp:
        png, svg = os.path.join(tmp, "in.png"), os.path.join(tmp, "out.svg")
        for width in (1920, 1280, 960, 640):
            height = round(src.shape[0] * width / src.shape[1])
            cv2.imwrite(png, cv2.resize(src, (width, height), interpolation=cv2.INTER_AREA))
            for speckle in (8, 16, 32, 64, 128):
                for mode in ("stacked", "cutout"):
                    vtracer.convert_image_to_svg_py(
                        png, svg, colormode="color", hierarchical=mode, mode="spline", filter_speckle=speckle,
                        color_precision=6, layer_difference=16, corner_threshold=60, length_threshold=4.0,
                        max_iterations=10, splice_threshold=45, path_precision=1,
                    )  # fmt: skip
                    with open(svg) as f:
                        text = f.read()
                    if len(text) <= budget and (best is None or len(text) > len(best)):
                        best = text
    return best
