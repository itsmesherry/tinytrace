"""Make the README's example images from the pictures in docs/samples/.

Usage: python docs/make_examples.py

For each docs/samples/NAME.jpg writes docs/images/NAME.jpg (the picture, 1200 wide) and docs/images/NAME.svg (its
tinytrace SVG at 125,000 characters), plus docs/images/hero.jpg: the first sample split at HERO_SPLIT,
picture on the left and SVG on the right. The hero needs resvg on PATH.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

import tinytrace

DOCS = Path(__file__).parent
SAMPLES, IMAGES = DOCS / "samples", DOCS / "images"
ORDER = ["bunny", "wave", "poster", "sunset"]
# Where the hero splits picture from SVG, as a share of the width: through the middle of the bunny.
HERO_SPLIT = 0.36


def main() -> None:
    IMAGES.mkdir(exist_ok=True)
    names = [n for n in ORDER if (SAMPLES / f"{n}.jpg").exists()]
    for name in names:
        src = cv2.imread(str(SAMPLES / f"{name}.jpg"))
        h = round(src.shape[0] * 1200 / src.shape[1])
        cv2.imwrite(
            str(IMAGES / f"{name}.jpg"),
            cv2.resize(src, (1200, h), interpolation=cv2.INTER_AREA),
            [cv2.IMWRITE_JPEG_QUALITY, 88],
        )
        svg = tinytrace.trace(src, budget=125_000)
        (IMAGES / f"{name}.svg").write_text(svg)
        print(f"{name}: {len(svg):,} characters")
    if names:
        first = names[0]
        picture = cv2.imread(str(IMAGES / f"{first}.jpg"))
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "svg.png"
            subprocess.run(["resvg", "-w", "1200", str(IMAGES / f"{first}.svg"), str(png)], check=True)
            traced = cv2.resize(cv2.imread(str(png)), (picture.shape[1], picture.shape[0]))
        half = round(picture.shape[1] * HERO_SPLIT)
        hero = np.hstack([picture[:, :half], traced[:, half:]])
        hero[:, half - 1 : half + 1] = 255
        for text, x in (("picture", 16), ("tinytrace SVG, 125,000 characters", half + 16)):
            cv2.putText(hero, text, (x, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5, cv2.LINE_AA)
            cv2.putText(hero, text, (x, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.imwrite(str(IMAGES / "hero.jpg"), hero, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("hero.jpg written")


if __name__ == "__main__":
    main()
