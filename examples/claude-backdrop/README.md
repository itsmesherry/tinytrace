# Picture backdrop for the Claude desktop app

A slideshow of your own pictures behind the Claude desktop app's chat, under its
frosted glass panels. Each picture is traced by tinytrace into a still SVG, so the
app draws it as a plain image and it idles at about the same CPU and GPU as having
no backdrop at all.

> Claude desktop mods are an early-access feature, and their API can change
> between app releases.

## Install

The repository is a Claude Code plugin marketplace, and the mod comes with three
sample slides, so it works straight away. Add the marketplace, install the mod, then
restart the Claude desktop app:

```bash
claude plugin marketplace add itsmesherry/tinytrace
claude plugin install picture-backdrop@tinytrace
```

`/backdrop on`, `/backdrop off` and `/backdrop next` control it. Pictures change every
2 minutes (`EVERY_MS` in `hooks/register.tsx`).

## Use your own pictures

Clone the repository, make slides from a folder of pictures, and install from your
local copy instead:

```bash
git clone https://github.com/itsmesherry/tinytrace.git
pip install tinytrace-svg
python tinytrace/examples/claude-backdrop/make_slides.py ~/Pictures/backdrops
claude plugin marketplace add ./tinytrace
claude plugin install picture-backdrop@tinytrace
```

Each picture becomes `hooks/slides/slide-N.ts`, at most 125,000 characters (the app
allows 131,072 for a backdrop scene). Slides live in separate files because the app
won't read a module file over 1 MiB, and a mod with one silently doesn't load. If you
already installed the samples, remove that marketplace first
(`claude plugin marketplace remove tinytrace`). After changing slides later, bump
`version` in `.claude-plugin/plugin.json`, run `claude plugin marketplace update tinytrace`
and `claude plugin update picture-backdrop@tinytrace`, and restart.

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

## Sample slide credits

- *Big Buck Bunny* frame © Blender Foundation, [peach.blender.org](https://peach.blender.org),
  licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). The slide is a traced
  version of the frame.
- *Under the Wave off Kanagawa*, Katsushika Hokusai: public domain, from
  [The Metropolitan Museum of Art](https://www.metmuseum.org/art/collection/search/36491).
- City at night: photo by Jeff Golenski,
  [WordPress Photo Directory](https://wordpress.org/photos/photo/3016a7fb59/), CC0.
