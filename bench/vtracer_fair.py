"""vtracer given a fair shot at a size budget.

vtracer has no budget setting, and squeezing its output down afterwards wrecks it. So try its own detail settings
(input width, speck size, how much it merges similar colours, stacked or cutout), keep every result that fits by
itself, and return the one that scores best against the picture. Picking by score gives vtracer the best chance.
"""

from __future__ import annotations

import os
import tempfile

import cv2
import vtracer
from score import score

# Scoring every candidate is slow, so score only the most detailed (largest) ones that fit.
SCORED = 12


def trace(picture: str, budget: int) -> str | None:
    src = cv2.imread(picture)
    fits: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        png, svg = os.path.join(tmp, "in.png"), os.path.join(tmp, "out.svg")
        for width in (1920, 1280, 960, 640):
            height = round(src.shape[0] * width / src.shape[1])
            cv2.imwrite(png, cv2.resize(src, (width, height), interpolation=cv2.INTER_AREA))
            for speckle in (4, 8, 16, 32, 64, 128):
                for layers in (16, 32, 64):
                    for mode in ("stacked", "cutout"):
                        vtracer.convert_image_to_svg_py(
                            png, svg, colormode="color", hierarchical=mode, mode="spline", filter_speckle=speckle,
                            color_precision=6, layer_difference=layers, corner_threshold=60, length_threshold=4.0,
                            max_iterations=10, splice_threshold=45, path_precision=1,
                        )  # fmt: skip
                        with open(svg) as f:
                            text = f.read()
                        if len(text) <= budget:
                            fits.append(text)
        best: tuple[float, str] | None = None
        for text in sorted(fits, key=len, reverse=True)[:SCORED]:
            with open(svg, "w") as f:
                f.write(text)
            error = score(picture, svg).color_error
            if best is None or error < best[0]:
                best = (error, text)
    return None if best is None else best[1]
