"""Turn a folder of pictures into slides for the picture-backdrop mod.

Usage: python make_slides.py PICTURES_FOLDER

Each picture is traced by tinytrace into an SVG of at most 125,000 characters (the app's limit for a backdrop
scene is 131,072) and saved as hooks/slides/slide-N.ts, one per file, because the app won't read a module file
over 1 MiB. hooks/slides.ts lists them in order. Rerunning replaces the slides.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tinytrace

PICTURES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
HOOKS = Path(__file__).parent / "hooks"


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    files = sorted(p for p in Path(sys.argv[1]).iterdir() if p.suffix.lower() in PICTURES)
    if not files:
        sys.exit(f"no pictures in {sys.argv[1]}")
    slides = HOOKS / "slides"
    slides.mkdir(exist_ok=True)
    for old in slides.glob("slide-*.ts"):
        old.unlink()
    for n, picture in enumerate(files, 1):
        svg = tinytrace.trace(picture, budget=125_000, cover=True)
        (slides / f"slide-{n}.ts").write_text(f"export const SLIDE = {json.dumps(svg)}\n")
        print(f"slide {n}: {picture.name} ({len(svg):,} characters)")
    imports = "\n".join(f"import {{ SLIDE as S{n} }} from './slides/slide-{n}'" for n in range(1, len(files) + 1))
    names = ", ".join(f"S{n}" for n in range(1, len(files) + 1))
    (HOOKS / "slides.ts").write_text(
        "// Written by make_slides.py: one import per slide, each in its own file "
        "(the app reads no module file over 1 MiB).\n"
        f"{imports}\n\nexport const SLIDES: readonly string[] = [{names}]\n"
    )
    print(f"{len(files)} slides written. Reinstall the mod and restart Claude to see them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
