# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Tracing is about twice as fast (bunny 9.9 s to 5.3 s, poster 14.2 s to 7.7 s on
  an Apple M1). The SVGs are byte for byte the same as before.

## [0.1.0] - 2026-11-27

### Added

- Published on PyPI as `tinytrace-svg` (PyPI doesn't allow the name `tinytrace`);
  the module and command are `tinytrace`.
- `tinytrace.trace(image, budget, colors, cover)`: trace a picture into the
  best-looking SVG that fits a character budget.
- `tinytrace` command line tool.
- Benchmark against vtracer at the same budget (`bench/`).
- Example: a picture slideshow backdrop for the Claude desktop app
  (`examples/claude-backdrop/`).
