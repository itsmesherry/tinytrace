# Picture backdrop for the Claude desktop app

A slideshow of your own pictures behind the Claude desktop app's chat, under its
frosted glass panels. Each picture is traced by tinytrace into a still SVG, so the
app draws it as a plain image and it idles at about the same CPU and GPU as having
no backdrop at all.

> Claude desktop mods are an early-access feature, and their API can change
> between app releases.

## Make your slides

```bash
pip install tinytrace
python make_slides.py ~/Pictures/backdrops
```

Each picture becomes `hooks/slides/slide-N.ts`, at most 125,000 characters (the app
allows 131,072 for a backdrop scene). Slides live in separate files because the app
won't read a module file over 1 MiB, and a mod with one silently doesn't load.

## Install

The repository is a Claude Code plugin marketplace. After making your slides, add your
local copy and install the mod, then restart the Claude app:

```bash
claude plugin marketplace add /path/to/tinytrace
claude plugin install picture-backdrop@tinytrace
```

After changing the slides, run `claude plugin marketplace update tinytrace` and
`claude plugin update picture-backdrop@tinytrace`, bump `version` in
`.claude-plugin/plugin.json` first, and restart.

Once installed, `/backdrop on`, `/backdrop off` and `/backdrop next` control it.
Pictures change every 2 minutes (`EVERY_MS` in `hooks/register.tsx`).

## What we measured

On an M1 MacBook, with the app idle:

| Backdrop | GPU busy | Renderer CPU |
| --- | ---: | ---: |
| None | 2.7% | 0.7% |
| This slideshow | 2.2% | 0.3% |
| A scene with CSS animation | ~30–40% CPU | |
| A GPU shader crossfade between slides | 49% | 6.6% |

That's why slides switch without a fade: a smooth crossfade means a shader running
all the time.
