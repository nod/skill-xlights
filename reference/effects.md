# Effects: what they look like and how to drive them

`seqlib.Seq` helpers wrap the effects below with settings copied from real sequences. "Rendered" = seen on the
real show by the user and liked; "file-verified" = keys copied from the user's own sequences but not yet judged
in a render of ours. For anything else, run `scripts/effect_examples.py <Name>` first.

| Effect | Helper | What it gives you | Status |
|---|---|---|---|
| On | `on(els, layer, a, b, color, a%, b%, subbuf=, perModel=)`, `flash(...)` | a solid colour ramping a%→b%. With a radial `Grad` ending in black: a soft glow/disk. In a tiny subbuffer: a dot, a pixel, pixel art | rendered |
| Bars | `bars(els, layer, a, b, direction, colors, count, cycles)` | bands rolling. Directions: `up`, `down`, `expand`, `compress` (lowercase), `Left`, `Right`, `H-expand`, `H-compress`. A single gradient bar `up` on the whole yard = "a wave of light rolls up everything" | rendered |
| Morph | `morph(els, layer, a, b, colors, line_a, line_b, tail_start, tail_end, extra=)` | a line moving from one position to another with a tail. The workhorse for anything that travels: sweeps (`DIAG[...]`), a dot gliding between panels, a band rising (`DIAG['up']` with long tails = a ghost), wings (a line pivoting about one end), arcs (chain segments) | rendered |
| Shockwave | `shockwave(els, layer, a, b, colors, cx, cy, r_end, w_end, r_start=, w_start=)`, `ripple(...)` | a ring growing from a point; `r_start > r_end` makes it collapse inward. On the whole-yard group from a prop's position = "light goes out from here" | rendered |
| Pinwheel | `pinwheel(...)`, `peppermint(...)`, `whirl(...)` | spinning arms. 2 thin arms slow = searchlight; 8-12 thin arms = star/sun rays; 6 colours 3D = celebration wheel; 4-part whirl (slow/fast/reverse) | rendered |
| Spirals | `spirals(..., three_d=, swing=, perModel=)` | barber-pole stripes (great on trunks/columns); `swing=True` rocks back and forth - calm canvas background | rendered |
| Wave | `wave(els, layer, a, b, color, kind='Sine', fill='None', direction=...)` | sine lines rolling across pixel sticks (alternate groups and direction per bar) | rendered |
| Fill | `fill(els, layer, a, b, colors, p_from, p_to, per_model=, direction='Up'/'Down')`, `bounce(...)`, `trunk_rise(...)` | a level rising/falling. `bounce` = drum hit on vertical sticks (height = hit strength). `direction='Down'` hangs it from the top (upside-down world) | rendered |
| Meteors | `meteors(..., direction='Down'/'Up', perModel=)` | rain, tears, drips, snow, rising sparks; `perModel` gives every stick its own (a crowd "searching") | rendered |
| Twinkle | `twinkle(..., subbuf=)` | stars (in the top part of a canvas), sparkle, gold treasure | rendered |
| VU Meter | `waveform(...)` | the song's own audio drawn live across a canvas - a voice "speaking" | rendered |
| Butterfly | `butterfly(..., style=1, speed=)` | slow churning plasma in the palette: water, caustics, aurora | rendered |
| Circles | `bubbles(...)` | Circles in bubble mode - rising rings, underwater | rendered |
| Shader | `shader(els, layer, a, b, 'Shaders/X.fs', params, bools, fadein, fadeout)` | ISF shaders: starfields, flares, hyperspace, galaxies, spirals. Big atmosphere, best with long fades | rendered |
| Fire | raw `sq.add(..., 'Fire', ...)` (see examples/owl_shine `fire_fx`, examples/aggie_war_hymn `fire`) | flames from the bottom; `E_SLIDER_Fire_HueShift` recolours: 97 = red-orange (hell's flames), 94 already reads hot pink. On the Verts group the flames fill every panel. Real fire is orange - fine in short literal doses | rendered (frames read back) |
| Pictures | `pictures(els, layer, a, b, path, fadein, fadeout)` + `write_png(path, rows, colors)` | an image. A PNG exactly the matrix's size (6x44) with `No Scaling` lands pixel for pixel on a single model; transparent pixels show what's below. Best way to do pixel art (letters, logos, sprites, snowflakes): one effect per picture. A wide image across a group of narrow matrices does NOT read (each panel shows a thin slice; scrolled it's moving blobs) | rendered (frames read back) |
| Snowflakes | `snowflakes(els, layer, a, b, colors, count, speed, falling, kind)` | real snow. Type 1 (single pixels), count 3-6, speed 4-5, `Per Model Default` on a group = each panel its own snowfall; `Falling & Accumulating` piles it up at the bottom. Meteors used as snow on 6-wide panels read as rain or static - don't | rendered (frames read back) |
| Fireworks | raw `sq.add(..., 'Fireworks', ...)` (examples/aggie_war_hymn `fireworks`) | bursts in the palette colours; per single Vert works | rendered (frames read back) |
| an orb | `orb(ALL, layer, a, b, path)` | a glowing sphere travelling through the whole yard: a radial gradient in a subbuffer stepped every 50 ms, Additive, AllModels as the last row. Paths: hops (arcs between landing points on the beat), circles, spirals, drifts | rendered (frames read back) |
| Galaxy, Liquid, Fan, Curtain, Ripple, Text, Spirograph | none yet | exist in the user's sequences; get keys from `effect_examples.py` | file-verified |

## Habits that paid off
- **Gradients everywhere** (`Grad`) instead of flat colours: across a group (`right`), bottom-to-top with a white tip
  (`up`), from the middle (`radial-out`), over time (hits that start white and settle).
- **Brightness as a design tool**: backgrounds 20-45 %, foreground motifs 80-100 %. Things on top only read if the
  background is dim.
- **Layers by role** per element (decide up front, write it in a comment): e.g. canvas layer 0 character,
  1 motifs, 2 washes, 3 ripples, 4 background, 5 sky, 7-14 melody scroll. With Normal blending (the default now,
  `xsq-format.md` "Layer blending") the order matters: the background must be the lowest used layer, sparse
  motifs above it; two effects on the same layer at the same start time keep only one (`resolve()`), so things
  that overlap in time (both eyes of a pair, rising ghosts every beat) need layers of their own.
- **Spiral trees / any model with a dimming curve** in the layout (`<dimmingCurve>` with brightness -70, gamma 2.2
  on the lol2026 spirals): it's applied in the render, so dark colours (maroon, navy) all but vanish there (160 of
  red came out as 12). Give those props bright colours and white. A controller `Brightness` is NOT in the render.
- **`Seq.moment(a, b, draw, color)`** for whole-yard moments: clears every row in [a, b), draws on the ALL group,
  and brings the non-member props along. A handful per song, at structural peaks.
- **`Seq.cut(a_ms, b_ms, els, layers)`** to carve silence: stops, "nothing in it", endings.
