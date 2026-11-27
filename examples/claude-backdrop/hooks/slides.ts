// Written by make_slides.py: one import per slide, each in its own file (the app reads no module file over 1 MiB).
import { SLIDE as S1 } from './slides/slide-1'
import { SLIDE as S2 } from './slides/slide-2'
import { SLIDE as S3 } from './slides/slide-3'

export const SLIDES: readonly string[] = [S1, S2, S3]
