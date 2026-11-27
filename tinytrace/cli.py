"""Command line: tinytrace picture.jpg [-o picture.svg] [--budget N] [--colors N] [--cover]."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .core import BudgetTooSmall, trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tinytrace",
        description="Turn a picture into the best-looking SVG that fits a size budget.",
    )
    parser.add_argument("image", type=Path, help="the picture to trace (jpg, png, webp, tiff, ...)")
    parser.add_argument("-o", "--output", type=Path, help="where to write the SVG (default: next to the picture)")
    parser.add_argument(
        "-b", "--budget", type=int, default=125_000, help="most characters the SVG may have (default: 125000)"
    )
    parser.add_argument("-c", "--colors", type=int, default=40, help="fill palette size (default: 40)")
    parser.add_argument(
        "--cover", action="store_true", help="fill any box it is drawn in, cropping the edges (for backgrounds)"
    )
    parser.add_argument("-V", "--version", action="version", version=f"tinytrace {__version__}")
    args = parser.parse_args(argv)

    output = args.output or args.image.with_suffix(".svg")
    if output.resolve() == args.image.resolve():
        parser.error("the output would overwrite the picture; pass -o")
    started = time.monotonic()
    try:
        svg = trace(args.image, budget=args.budget, colors=args.colors, cover=args.cover)
    except (BudgetTooSmall, ValueError) as error:
        print(f"tinytrace: {error}", file=sys.stderr)
        return 1
    output.write_text(svg, encoding="utf-8")
    print(f"{output}: {len(svg):,} characters (budget {args.budget:,}), {time.monotonic() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
