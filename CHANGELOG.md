# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Tracing is about 20% faster again (bunny 5.3 s to 3.9 s, sunset 5.5 s to 3.7 s
  on an Apple M1): layers are traced on threads, except under Pyodide. The SVGs
  are byte for byte the same as before.
- The search for the budget guesses each next coarseness from the sizes so far,
  instead of halving the range 7 times: about 3 tracings per picture instead of 7,
  and a trace takes about 3 s instead of 5 on the 23 benchmark pictures. The SVGs
  change slightly. Benchmark scores are the same to two decimals, except the
  photos' colour error, 3.86 to 3.87.

## [0.1.1] - 2026-11-28

### Changed

- Tracing is about twice as fast (bunny 9.9 s to 5.3 s, poster 14.2 s to 7.7 s on
  an Apple M1). The SVGs are byte for byte the same as before.
- README: the night city example is now a hot-air balloon at sunset, and a
  downloads badge shows the PyPI download count.

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
