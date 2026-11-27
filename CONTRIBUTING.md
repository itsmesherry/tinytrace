# Contributing

Thanks for helping improve `tinytrace`. Bug reports, pictures it handles badly
and fixes are all welcome.

## Setup

```bash
git clone https://github.com/itsmesherry/tinytrace.git
cd tinytrace
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before opening a pull request

```bash
ruff format && ruff check . && mypy tinytrace && pytest
```

CI runs the same checks on Python 3.10 to 3.13. One test renders the SVG and
needs [resvg](https://github.com/linebender/resvg) on your PATH; without it the
test is skipped.

A pull request should:

- include a test for any behaviour it adds or fixes
- add a line under `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md)
- keep `trace()` and the command line options working as they are

## Changes to the tracing

A change to how pictures are traced should come with benchmark numbers from
before and after, on the same pictures and budget:

```bash
pip install -e ".[bench]"
python bench/run.py path/to/pictures
```

Say which kinds of pictures you ran (cartoons, art, photos). A change that
helps one kind and hurts another is worth discussing first.

## Releasing (maintainers)

1. Update `version` in `pyproject.toml` and `__version__` in
   `tinytrace/__init__.py`.
2. Move the `[Unreleased]` notes in the changelog under the new version.
3. Publish a GitHub Release tagged `v<version>`. The publish workflow builds
   the package and uploads it to PyPI.
