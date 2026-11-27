# TODO

Planned work, roughly in priority order. Open an issue or pull request if you
want to pick one up.

## Tracing

- [ ] Close the colour gap on very flat cartoons: vtracer has the lower colour
      error on four of them, in far fewer characters. Already tried without a
      gain: tracing without the smoothing step, merging near-identical colours,
      true-average colours per shape, and picking between variants by an
      internal error measure (it picked the worse one)
- [ ] Keep small dark features their own colour: Big Buck Bunny's eyes come out
      with a greenish tint from the ink colours
- [ ] Reduce visible banding in smooth gradients such as skies, for example by
      spending more palette colours where the picture changes slowly
- [ ] Trace faster: about 10 s per picture today, whatever its size, mostly in
      the 7-step search for the budget
- [ ] See whether Bézier curves beat polygons at larger budgets (polygons won
      at 125,000 characters)

## Benchmark

- [ ] Add more pictures that can be shared, especially line art, logos and
      photos, and publish the set so anyone can reproduce the numbers

## Project

- [ ] Show a download count badge in the README once pepy lists
      `tinytrace-svg`
