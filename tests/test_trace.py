import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
import pytest

from tinytrace import BudgetTooSmall, trace
from tinytrace.cli import main

SVG = "{http://www.w3.org/2000/svg}"


@pytest.fixture(scope="module")
def picture() -> np.ndarray:
    """A small cartoon: sky gradient, ground, a red sun and a black-outlined house."""
    img = np.zeros((450, 800, 3), np.uint8)
    for y in range(300):
        img[y] = (235 - y // 3, 190 - y // 6, 120)  # BGR: blue sky, lighter lower down
    img[300:] = (60, 150, 80)
    cv2.circle(img, (650, 90), 50, (40, 40, 220), -1)
    cv2.rectangle(img, (200, 180), (380, 320), (90, 200, 240), -1)
    cv2.rectangle(img, (200, 180), (380, 320), (20, 20, 20), 4)
    cv2.line(img, (190, 185), (290, 110), (20, 20, 20), 4)
    cv2.line(img, (290, 110), (390, 185), (20, 20, 20), 4)
    return img


@pytest.fixture(scope="module")
def svg(picture: np.ndarray) -> str:
    return trace(picture, budget=40_000)


def colors(svg: str) -> list[tuple[int, int, int]]:
    root = ET.fromstring(svg)
    return [tuple(int(p.get("fill")[i : i + 2], 16) for i in (1, 3, 5)) for p in root.iter(f"{SVG}path")]


def test_fits_the_budget_and_is_valid_svg(svg: str) -> None:
    assert len(svg) <= 40_000
    root = ET.fromstring(svg)
    assert root.tag == f"{SVG}svg"
    assert root.get("viewBox") == "0 0 1920 1080"
    assert len(list(root.iter(f"{SVG}path"))) > 3


def test_keeps_the_picture_colours(svg: str) -> None:
    found = colors(svg)

    def near(rgb: tuple[int, int, int]) -> bool:
        return any(sum(abs(a - b) for a, b in zip(rgb, c)) < 40 for c in found)

    assert near((220, 40, 40)), "red sun"
    assert near((80, 150, 60)), "green ground"
    assert near((20, 20, 20)), "black outline"


def test_a_smaller_budget_gives_a_smaller_svg(picture: np.ndarray, svg: str) -> None:
    small = trace(picture, budget=8_000)
    assert len(small) <= 8_000 < len(svg)


def test_too_small_a_budget_says_so(picture: np.ndarray) -> None:
    with pytest.raises(BudgetTooSmall):
        trace(picture, budget=300)


def test_tall_pictures_fit_too(picture: np.ndarray) -> None:
    # A portrait picture has more pixels at 1920 wide; it must still fit, at a sensible size.
    tall = np.ascontiguousarray(np.rot90(picture))  # 450 wide, 800 tall
    svg = trace(tall, budget=40_000)
    assert len(svg) <= 40_000
    width, height = map(int, ET.fromstring(svg).get("viewBox").split()[2:])
    assert height > width and width * height <= 1920 * 1440


def test_cover_fills_the_box(picture: np.ndarray) -> None:
    assert 'preserveAspectRatio="xMidYMid slice"' in trace(picture, budget=10_000, cover=True)


def test_rejects_what_it_cannot_read(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        trace(tmp_path / "missing.png")
    with pytest.raises(ValueError):
        trace(np.zeros((10, 10), np.uint8))


def test_cli_writes_the_svg(picture: np.ndarray, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    src = tmp_path / "house.png"
    cv2.imwrite(str(src), picture)
    assert main([str(src), "--budget", "20000"]) == 0
    out = tmp_path / "house.svg"
    assert out.exists() and len(out.read_text()) <= 20_000
    assert "characters" in capsys.readouterr().out
    assert main([str(src), "--budget", "100"]) == 1


@pytest.mark.skipif(shutil.which("resvg") is None, reason="needs resvg to render the SVG")
def test_rendered_svg_looks_like_the_picture(picture: np.ndarray, svg: str, tmp_path: Path) -> None:
    (tmp_path / "t.svg").write_text(svg)
    subprocess.run(["resvg", "-w", "800", str(tmp_path / "t.svg"), str(tmp_path / "t.png")], check=True)
    rendered = cv2.imread(str(tmp_path / "t.png"))
    rendered = cv2.resize(rendered, (800, 450), interpolation=cv2.INTER_AREA)

    def lab(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(cv2.GaussianBlur(img, (0, 0), 1.5).astype(np.float32) / 255, cv2.COLOR_BGR2LAB)

    error = np.sqrt(((lab(picture) - lab(rendered)) ** 2).sum(2)).mean()
    assert error < 4, f"mean colour error {error:.2f}"


def test_search_finds_the_finest_tolerance_that_fits() -> None:
    from tinytrace.core import _search

    def build(s: float) -> str:
        return "x" * int(100_000 / s**1.3)  # size falls as a power of the tolerance, like a real tracing

    svg = _search(build, 50_000)
    assert svg is not None and 0.98 * 50_000 <= len(svg) <= 50_000
    assert _search(build, 10) is None  # even the coarsest is over
    assert _search(lambda s: "x", 50_000) == "x"  # everything fits: the finest is kept
