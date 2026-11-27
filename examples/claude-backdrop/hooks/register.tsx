// A slideshow behind the Claude desktop app's chat. The slides are still SVG pictures made by tinytrace
// (make_slides.py), so the app draws them as plain images: no animation code, about 0% CPU at idle.
// /backdrop on | off | next
import type { Register, Timer } from 'claude-code'

import { SLIDES } from './slides'

const PLUGIN = 'picture-backdrop'
const SCENE = 'slideshow'
const EVERY_MS = 120_000
const GLASS = { blur: 14, tint: '#14161c', opacity: 0.55 }
// On or off, kept across sessions.
const STORE_KEY = 'on'

let shown = 0
let timer: Timer | undefined

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'backdrop', description: 'Picture backdrop: on, off or next' })
    if (SLIDES.length > 0 && (await $.store.get(STORE_KEY)) !== 'off') {
      await $.theme.set({ backdrop: { scene: SCENE, glass: GLASS }, overrideColorScheme: 'dark' })
      timer = $.clock.every(EVERY_MS, () => {
        shown = (shown + 1) % SLIDES.length
        $.ui.invalidate('ui.render')
      })
    }

    return next(e)
  })

  on('command.run', { command: 'backdrop' }, async ($, e) => {
    const word = e.args.trim().toLowerCase()

    if (SLIDES.length === 0) {
      return { text: 'No slides yet: run make_slides.py on a folder of pictures first.' }
    }
    if (word === 'off') {
      timer?.cancel()
      timer = undefined
      await $.store.set(STORE_KEY, 'off')
      await $.theme.clear()

      return { text: 'Backdrop off.' }
    }
    if (word === 'next') {
      shown = (shown + 1) % SLIDES.length
      $.ui.invalidate('ui.render')

      return { text: `Slide ${shown + 1} of ${SLIDES.length}.` }
    }
    await $.store.set(STORE_KEY, 'on')
    await $.theme.set({ backdrop: { scene: SCENE, glass: GLASS }, overrideColorScheme: 'dark' })
    if (timer === undefined) {
      timer = $.clock.every(EVERY_MS, () => {
        shown = (shown + 1) % SLIDES.length
        $.ui.invalidate('ui.render')
      })
    }

    return { text: `Backdrop on: ${SLIDES.length} slides, a new one every ${EVERY_MS / 60_000} minutes.` }
  })

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }
    if (e.props.plugin !== PLUGIN || e.props.scene !== SCENE || SLIDES.length === 0) {
      return next(e)
    }
    const { Svg } = $.ui.resolve(e)

    return <Svg alt={`Slide ${shown + 1} of ${SLIDES.length}`} source={SLIDES[shown] ?? SLIDES[0]!} />
  })
}
