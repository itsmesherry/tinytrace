"""Benchmark tinytrace against vtracer at the same size budget.

Usage: python bench/run.py PICTURES_FOLDER [--budget 125000] [--out bench/out]
Needs: pip install -e ".[bench]" and resvg on PATH (brew install resvg, or cargo install resvg).
Writes each SVG to --out and prints a Markdown table.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import vtracer_fair
from score import Score, score

import tinytrace

PICTURES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def row(name: str, ours: Score, theirs: Score | None) -> str:
    def cells(s: Score | None) -> str:
        return (
            " | ".join("–" for _ in range(3))
            if s is None
            else f"{s.color_error:.2f} | {s.shape_match:.3f} | {s.outlines_kept:.3f}"
        )

    return f"| {name} | {cells(ours)} | {cells(theirs)} |"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pictures", type=Path)
    parser.add_argument("--budget", type=int, default=125_000)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "out")
    args = parser.parse_args()

    files = sorted(p for p in args.pictures.iterdir() if p.suffix.lower() in PICTURES)
    if not files:
        sys.exit(f"no pictures in {args.pictures}")
    args.out.mkdir(parents=True, exist_ok=True)
    print(
        f"Budget: {args.budget:,} characters. "
        "Colour error: lower is better. Shape match, outlines kept: higher is better.\n"
    )
    print("| Picture | tinytrace colour | shape | outlines | vtracer colour | shape | outlines |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for picture in files:
        ours_svg = args.out / f"{picture.stem}.tinytrace.svg"
        ours_svg.write_text(tinytrace.trace(picture, budget=args.budget))
        theirs_text = vtracer_fair.trace(str(picture), args.budget)
        theirs = None
        if theirs_text is not None:
            theirs_svg = args.out / f"{picture.stem}.vtracer.svg"
            theirs_svg.write_text(theirs_text)
            theirs = score(str(picture), str(theirs_svg))
        print(row(picture.stem, score(str(picture), str(ours_svg)), theirs), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
