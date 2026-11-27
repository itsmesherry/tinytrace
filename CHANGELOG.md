# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

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
