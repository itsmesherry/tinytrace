"""How close a traced SVG looks to its picture.

Renders the SVG with resvg at 1280 wide and compares it with the picture resized the same:

- colour error: mean CIE Lab difference (ΔE76) after a light blur. Lower is better; about 2 is barely visible.
- shape match: SSIM of the lightness. Higher is better; 1 is identical.
- outlines kept: share of the picture's strong edges that the SVG also has. Higher is better.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray
from skimage.metrics import structural_similarity

WIDTH = 1280


@dataclass
class Score:
    color_error: float
    shape_match: float
    outlines_kept: float


def _lab(img: NDArray[np.uint8]) -> NDArray[np.float32]:
    return cv2.cvtColor(cv2.GaussianBlur(img, (0, 0), 1.0).astype(np.float32) / 255, cv2.COLOR_BGR2LAB)


def _edges(img: NDArray[np.uint8]) -> NDArray[np.bool_]:
    return cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 60, 160) > 0


def score(picture: str, svg: str) -> Score:
    original = cv2.imread(picture)
    height = round(original.shape[0] * WIDTH / original.shape[1])
    original = cv2.resize(original, (WIDTH, height), interpolation=cv2.INTER_AREA)
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "render.png")
        subprocess.run(["resvg", "-w", str(WIDTH), svg, png], check=True)
        rendered = cv2.resize(cv2.imread(png), (WIDTH, height), interpolation=cv2.INTER_AREA)
    a, b = _lab(original), _lab(rendered)
    color = float(np.sqrt(((a - b) ** 2).sum(2)).mean())
    shape = float(structural_similarity(a[..., 0], b[..., 0], data_range=100))
    wanted = _edges(original)
    near = cv2.dilate(_edges(rendered).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return Score(color, shape, float((near & wanted).sum() / max(wanted.sum(), 1)))
