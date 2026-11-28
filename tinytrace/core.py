"""Turn a picture into the best-looking SVG that fits a fixed number of characters.

How, in order:

1. Work at 1920 pixels wide (tall pictures at the same pixel count as a 4:3 one).
   Small pictures are enlarged smoothly first, so edges follow curves instead of
   the source's pixel steps.
2. Fills: mean-shift flattens texture noise, k-means picks the palette in Lab
   colour space, and a 5x5 majority vote straightens ragged borders.
3. Ink: lines darker than their surroundings (cartoon outlines) are found on the
   unfiltered picture, joined, and given a few ink colours of their own, painted
   last on top.
4. Stacked layers, largest fill first. A layer may also cover anything painted
   after it, so its outline skips the holes and jaggies later layers hide (each
   border is stored about once, not twice), and it reaches one pixel under later
   layers so no hairline cracks show.
5. Outlines are Douglas-Peucker polygons written as short relative integer steps.
   Specks below a size are dropped. The tolerance and speck size are searched so
   the result fills the budget as closely as it can.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar, Union

import cv2
import numpy as np
from numpy.typing import NDArray

Image = Union[str, "os.PathLike[str]", NDArray[np.uint8]]
T = TypeVar("T")

WIDTH = 1920
# Tall pictures are worked on at the same pixel count as a 4:3 one, not 1920 wide, or they couldn't fit a budget.
MAX_PIXELS = 1920 * 1440
INKS = 4


class BudgetTooSmall(ValueError):
    """Even the coarsest tracing of the picture is over the budget."""


def _kmeans(px: NDArray[np.float32], k: int) -> tuple[NDArray[np.int32], NDArray[np.float32]]:
    cv2.setRNGSeed(1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, lbl, centers = cv2.kmeans(px, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
    return np.asarray(lbl, np.int32).ravel(), np.asarray(centers, np.float32)


def _majority(lbl: NDArray[np.int32], k: int) -> NDArray[np.int32]:
    # Majority vote in a k x k window: straightens ragged colour borders (fewer corners to store).
    best = np.zeros(lbl.shape, np.uint16)
    out = lbl.copy()
    for c in range(int(lbl.max()) + 1):
        votes = cv2.boxFilter((lbl == c).astype(np.uint16), cv2.CV_16U, (k, k), normalize=False)
        win = votes > best
        best[win] = votes[win]
        out[win] = c
    return out


def _despeckle(lbl: NDArray[np.int32], min_area: int) -> NDArray[np.int32]:
    # Specks smaller than min_area take the colour of the nearest larger region.
    keep = np.ones(lbl.shape, np.uint8)
    flat = keep.reshape(-1)  # a view: writing to it marks keep
    # Each colour's pixel indices, so each colour's specks are looked up on its own pixels, not the whole picture.
    by_color = np.argsort(lbl.ravel().astype(np.min_scalar_type(lbl.max())), kind="stable")
    counts = np.bincount(lbl.ravel())
    ends = np.cumsum(counts)
    for c in range(int(lbl.max()) + 1):
        _, comp, stats, _ = cv2.connectedComponentsWithStats((lbl == c).astype(np.uint8), connectivity=8)
        small = stats[:, cv2.CC_STAT_AREA] < min_area
        small[0] = False
        if small.any():
            px = by_color[ends[c] - counts[c] : ends[c]]
            flat[px[small[comp.ravel()[px]]]] = 0
    if keep.all():
        return lbl
    _, idx = cv2.distanceTransformWithLabels(1 - keep, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(keep)
    near = np.zeros(int(idx.max()) + 1, np.int32)
    near[idx[ys, xs]] = lbl[ys, xs]
    out: NDArray[np.int32] = near[idx]
    return out


def _map(f: Callable[[int], T], items: Iterable[int]) -> list[T]:
    # In order, on threads: OpenCV and most NumPy calls release the GIL. Pyodide can't start threads.
    if sys.platform == "emscripten":
        return list(map(f, items))
    with ThreadPoolExecutor() as pool:
        return list(pool.map(f, items))


def _mask(r: NDArray[np.integer], i: int) -> NDArray[np.uint8]:
    # r: each pixel's layer. Layer i may cover pixels of later layers (they paint over it), never an earlier layer's
    # pixels: its mask is everything except the parts of "not this colour" connected to earlier pixels, grown 1px
    # under later layers.
    if i == 0:
        return np.ones(r.shape, np.uint8)
    n, comp, stats, _ = cv2.connectedComponentsWithStats((r != i).astype(np.uint8), connectivity=4)
    # Every 4-connected piece of the earlier pixels has an edge pixel and one label throughout, so reading the
    # labels on the edge alone finds every component they touch.
    earlier = (r < i).astype(np.uint8)
    edge = earlier > cv2.erode(earlier, cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3)))
    blocked = np.zeros(n, bool)
    blocked[comp[edge]] = True
    blocked[0] = False
    # Label 0 is this layer's own pixels. Most layers keep no other component, or a few: fill those in from their
    # boxes rather than looking up every pixel's label.
    kept = np.flatnonzero(~blocked)[1:]
    if len(kept) > 64:  # ponytail: box-by-box stops paying off somewhere past this; not tuned
        m = ~blocked[comp]
    else:
        m = r == i
        for c in kept:
            x, y, w, h = stats[c, :4]
            box = (slice(y, y + h), slice(x, x + w))
            m[box] |= comp[box] == c
    grown = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    out: NDArray[np.uint8] = (m | (grown & (r > i))).astype(np.uint8)
    return out


def _outline(mask: NDArray[np.uint8], eps: float) -> str:
    # findContours on a 2x mask (so the outline sits on pixel edges, not half a pixel inside), Douglas-Peucker to
    # eps pixels, then relative integer steps.
    big = cv2.resize(mask, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    contours, _ = cv2.findContours(big, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    d: list[str] = []
    px = py = 0
    for contour in contours:
        approx = cv2.approxPolyDP(contour, eps * 2, True)
        # Small specks keep a few corners instead of collapsing to nothing.
        if len(approx) < 4 and len(contour) >= 4:
            approx = cv2.approxPolyDP(contour, eps / 2, True)
        # (x + 0.5) / 2 is never a tie, so np.round rounds as Python's round does. Repeated points are dropped.
        pts = np.round((approx.reshape(-1, 2) + 0.5) / 2).astype(np.int64)
        pts = pts[np.r_[True, (np.diff(pts, axis=0) != 0).any(1)]]
        if len(pts) < 3:
            continue
        x0, y0 = int(pts[0, 0]), int(pts[0, 1])
        steps = " ".join(map(str, np.diff(pts, axis=0).ravel().tolist()))
        d.append((f"m{x0 - px} {y0 - py}" if d else f"M{x0} {y0}") + "l" + steps + "z")
        px, py = x0, y0
    return "".join(d).replace(" -", "-")


def _load(image: Image) -> NDArray[np.uint8]:
    if isinstance(image, np.ndarray):
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("expected a BGR image array of shape (height, width, 3)")
        return image
    src = cv2.imread(os.fspath(image))
    if src is None:
        raise ValueError(f"can't read {os.fspath(image)}")
    return np.asarray(src, np.uint8)


def _prepare(src: NDArray[np.uint8], colors: int) -> tuple[NDArray[np.int32], NDArray[np.float32], int]:
    w = min(WIDTH, round((MAX_PIXELS * src.shape[1] / src.shape[0]) ** 0.5))
    h = round(src.shape[0] * w / src.shape[1])
    resample = cv2.INTER_AREA if src.shape[1] >= w else cv2.INTER_CUBIC
    raw = cv2.resize(src, (w, h), interpolation=resample)

    # Fills.
    flat = cv2.pyrMeanShiftFiltering(raw, 6, 20)
    small = cv2.resize(flat, (640, round(h * 640 / w)), interpolation=cv2.INTER_AREA)
    _, centers = _kmeans(cv2.cvtColor(small, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32), colors)
    flat_lab = cv2.cvtColor(flat, cv2.COLOR_BGR2LAB).astype(np.float32)
    # Nearest centre per pixel, one centre at a time on separate channel planes: the same float32 sums, in the same
    # order, as broadcasting all centres at once, without the pixels x centres temporary. Strict < keeps the first
    # of equal distances, as argmin does.
    planes = cv2.split(flat_lab)
    lbl = np.zeros(flat_lab.shape[:2], np.int32)
    best = np.full(flat_lab.shape[:2], np.inf, np.float32)
    for c, center in enumerate(centers):
        d = (planes[0] - center[0]) ** 2
        d += (planes[1] - center[1]) ** 2
        d += (planes[2] - center[2]) ** 2
        closer = d < best
        best[closer] = d[closer]
        lbl[closer] = c
    lbl = _majority(lbl, 5)

    # Ink.
    lab = cv2.cvtColor(raw, cv2.COLOR_BGR2LAB)
    light = lab[:, :, 0]
    r = round(WIDTH / 1280 * 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    dark = cv2.morphologyEx(light, cv2.MORPH_BLACKHAT, kernel)
    lines = ((dark > 25) & (light < 180)).astype(np.uint8)
    ink = cv2.morphologyEx(lines, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)) > 0
    px = lab[ink].astype(np.float32)
    if len(px) < 50 * INKS:
        return lbl, centers, 0
    il, ic = _kmeans(px, INKS)
    # Each ink colour from the darker half of its group, so lines don't wash out.
    groups = [px[il == j] for j in range(INKS)]
    ic = np.array([np.median(g[g[:, 0] <= np.median(g[:, 0])], 0) if len(g) else ic[j] for j, g in enumerate(groups)])
    # Edge pixels that only looked dark next to something brighter keep their fill colour.
    il[np.sqrt(((px - ic[il]) ** 2).sum(1)) > 45] = -1
    inkl = np.zeros(lbl.shape, np.uint8)
    inkl[ink] = il + 1
    # Thin lines from a big picture get a pixel thicker, so they stay solid strokes rather than dotted ones.
    if src.shape[1] >= 1.5 * w:
        inkl = np.where(inkl > 0, inkl, cv2.dilate(inkl, np.ones((2, 2), np.uint8)))
    lbl[inkl > 0] = len(centers) + inkl[inkl > 0].astype(np.int32) - 1
    return lbl, np.vstack([centers, ic]).astype(np.float32), INKS


def _build(lbl: NDArray[np.int32], centers: NDArray[np.float32], inks: int, s: float, cover: bool) -> str:
    # s: outline tolerance in pixels; specks under ~18*s^2 pixels are dropped.
    lbl = _despeckle(lbl, max(3, round(18 * s * s)))
    h, w = lbl.shape
    n = len(centers)
    area = np.bincount(lbl.ravel(), minlength=n)
    # Fills first, largest first; ink colours last.
    order = sorted((c for c in range(n - inks) if area[c]), key=lambda c: -area[c])
    order += sorted((c for c in range(n - inks, n) if area[c]), key=lambda c: -area[c])
    rgb = cv2.cvtColor(np.clip(centers, 0, 255).reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_LAB2RGB)[0]
    rank = np.empty(n, np.min_scalar_type(len(order)))
    rank[order] = np.arange(len(order))
    r = rank[lbl]
    outlines = _map(lambda i: _outline(_mask(r, i), s), range(len(order)))
    fit = ' preserveAspectRatio="xMidYMid slice"' if cover else ""
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"{fit}>']
    for c, d in zip(order, outlines):
        if d:
            color = "#%02x%02x%02x" % tuple(int(v) for v in rgb[c])
            parts.append(f'<path fill-rule="evenodd" fill="{color}" d="{d}"/>')
    return "".join(parts) + "</svg>"


def trace(image: Image, budget: int = 125_000, colors: int = 40, cover: bool = False) -> str:
    """Trace ``image`` into an SVG string of at most ``budget`` characters.

    Args:
        image: a file path, or a BGR ``uint8`` array as OpenCV loads it.
        budget: the most characters the SVG may have.
        colors: fill palette size. More gives truer shading but leaves fewer
            characters for detail.
        cover: add ``preserveAspectRatio="xMidYMid slice"`` so the picture
            fills any box it is drawn in, cropping the edges (for backgrounds).

    Raises:
        BudgetTooSmall: even the coarsest tracing is over ``budget``.
        ValueError: the image can't be read.
    """
    if budget < 1:
        raise ValueError("budget must be positive")
    if colors < 2:
        raise ValueError("colors must be at least 2")
    lbl, centers, inks = _prepare(_load(image), colors)
    # Coarser = fewer characters: search for the finest that fits.
    lo, hi, best = 0.4, 4.0, None
    for _ in range(7):
        mid = (lo + hi) / 2
        svg = _build(lbl, centers, inks, mid, cover)
        if len(svg) <= budget:
            hi, best = mid, svg
        else:
            lo = mid
    if best is None:
        raise BudgetTooSmall(f"even the coarsest tracing is over {budget} characters")
    return best
