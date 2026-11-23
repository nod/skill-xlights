# Techniques (recipes that worked, with where to find the code)

Every recipe below is in a real build under `examples/`. Copy the helper, then adapt names to show_config.

## Anchoring to the music
- **Bars**: `B(n)` from `events.json` beats (`beats[phase + 4*(n-1)]`) - works for click tracks and `--loose`
  (uneven) beats alike. Write `SECTIONS` as bar numbers read off `summary.txt`.
- **Words**: `word('prefix', after)` returns a word's start time from `lyrics.json`; anchor every lyric moment with
  it, never with hand-typed seconds. `sung(t)` snaps to the vocal note onset just before (Whisper is ~0.1-0.4 s late).
  Lines: find the key word, walk back to the line's first word (examples/bdw_inchrist `line()`).
- **Notes**: `mono(stem, lo, hi)` = the top line of a stem. Which stem holds what varies by song (the "melody" of an
  instrumental may be in `other`; a lead guitar may sit in `vocals`); check `summary.txt` and the note CSVs.
- **Hits**: `events.json` kick/snare with `kick_v/snare_v` strengths; when the bands overlap (live recordings), give
  each hit to the band it's stronger in (examples/pixies). Skip snare ghost notes closer than ~0.6 beat.
- **Riffs**: `find_motif.py` finds every repeat of a figure from one example (examples/bdw_joy `PAIRS`: the
  six-note keyboard run, always in pairs: six notes, six panels - a pixel ball bounces across the wall landing on each
  note, and the second run bounces it back lower. Frame-by-frame On effects with `minlen=25`). Put a moving sprite on layers 0-1 of its model: under
  a full-panel effect (a Twinkle) it vanishes completely.
- **Stops / band drop-outs**: bars with kick count 0 in `summary.txt`. These are the song's punctuation.

## Characters (the biggest win)
A light with a personality that travels the yard and does what the words say.
- **Sprite** (examples/tso_wizards): `vert_path` (streak panel to panel at a height, or glide within a panel, with
  a fading glow where it lands), `hop_sticks` (bounce stick to stick), `run_arch`, `climb_spiral`, `climb_trunk`,
  `sprint_fence`. Single-model rows sorted by `layout_x()`; they blend on top of group backgrounds.
- **The mind** (examples/pixies): same toolkit, softer (no sparkles, long tails) - drifts, is lost, pinged, swims.
- **The spark** (examples/owl_shine): firefly that leaps (`AllModels` Morph segments along a sine arc), walks then
  runs the fence, becomes the sun.
- **A crowd** (examples/bdw_inchrist): each pixel stick is a person (dim body + one bright "heart" pixel). A light
  spreads person to person on lyric cues (`SPREAD` schedule: (t0, t1, how many lit), centre outward), and only lit
  people dance with the drums.
Give it a timing track (`Sprite`/`Story`) so the user can follow it in xLights.

## Canvas (matrix wall) motion - never flash panels
Repertoire (choose per song): melody scrolling right-to-left like sheet music (`melody_scroll`, needs ~8-12 spare
layers); ripples from a wandering point on the snare; bands sliding (`bars Left/Right`); diagonal sweeps (`DIAG`);
H-expand / H-compress bursts; smooth fill climbs; swinging 3D spirals; a character gliding panel to panel; ghosts
(a band rising with long tails, one per sustained "ooh"); a sky gradient that changes every bar (examples/owl_shine
`SKY_KEYS`); the VU waveform; Butterfly water/aurora; starfields (Twinkle in the top part).

## Pixel art on matrices
**Prefer pictures** (examples/aggie_war_hymn, examples/tso_wizards_winter): draw the art as a bitmap (rows of
characters, top first), write a PNG exactly the matrix's size with `write_png()` (6x44 for a Vert; transparent
where nothing is lit), and show it with `pictures(model, ..., scaling='No Scaling')` on the single model. One effect
per picture, any number of colours, pixel-exact (checked on renders), and it composites over the group background.
Fade with `fadein`/`fadeout`; animate by switching pictures (a spinning snowflake = two shapes alternating every
0.1 s, drifting a row down every 0.14 s; 80 tiny PNGs are fine). Push the PNGs with the sequence.

The older way still works under Normal blending: On effects in pixel-exact subbuffers on the single models
(examples/bdw_inchrist `art()`, `heart()`, `crown()`), edges just below pixel boundaries, one layer per rectangle.
Under the old `Max` default only the first rectangle rendered (xsq-format.md "Layer blending").

**Logos and images on a row of narrow matrices:** a logo stretched across the group shows as nine thin vertical
slices and doesn't read, still or scrolled (tested with the Texas A&M logo). Redraw it as pixel art made for the
panels: the A&M logo became an A on one Vert, the big T's bar across the top of five Verts with the stem down the
middle one, the M on the fifth, keeping the file's two colours and its white bevel lines. Big letters one per
panel (6x14: a 6x7 font stretched x2) read very well: "TEXAS A&M" is nine characters on nine Verts.

## The orb (examples/tso_wizards_winter)
"Some sphere or orb that dances across the scene occasionally would feel lively." A radial gradient
(white core -> cyan -> blue -> black) in a subbuffer on AllModels, moved every 50 ms (`seqlib.orb`), Additive,
AllModels as the last row. On the whole-yard buffer the props it passes light up round it: low y = the arches and
the bottom of the wall, y 50 = the middle of the wall and the spirals. Dances that worked: hopping arch to arch on
the beat (arcs between landing points), spiralling up during a build then a ring burst, circling the yard during a
whirl, drifting on a slow sine through falling snow, bouncing off every snare, rocketing up into a big moment,
twin orbs (cyan, magenta) hopping mirror-image, and alone in a silence, swelling, until the last hit bursts it.
"Occasionally" = about a dozen appearances in three minutes, each a few bars.

## Instrumental and band-only recordings
No vocals (Whisper finds 0 words, the vocal stem sits at -50 dB): the crowd still knows the words. Find the form
from the tune: a beat-synchronous chroma self-similarity of the melody stem shows the repeats (a verse repeating at
a 68-beat lag, two 28-beat halves, a final strain in a new key), the loudness envelope shows the band's stops
(1.5 s of silence after a stab = where the crowd shouts "SHORT!"), and phrase boundaries come every 8 beats. Map
the known lines onto the phrases, then ask the user to confirm the map in one question (times + which line) before
building on it. Put the words in a `Words` timing track so they can check it in xLights.

## Call and response as weather (examples/tso_wizards_winter)
Wizards in Winter's 22 stop bars: the band's stab FREEZES the yard (an icy ring, icicles growing down from the top
of every panel), then each note of the piano's answer is a snowflake picture on the wall, hopping panel to panel
with the run, high notes high. Scale the height to each run's own pitch range, not the song's: with a global range
the flakes all landed near the bottom.

## Words on a matrix (examples/bdw_joy)
A bold 6x7 pixel font (`FONT`), letters stacked top to bottom on a tall 6x44 panel - a vertical marquee sign. Each
glyph is decomposed into rectangles (`rects()`: row runs merged downward), one On effect each in a pixel-exact
subbuffer (`cell()`), so a 5-letter word needs ~25 layers on that single model. Phrases are detected in
`lyrics.json` with templates (first word + following words within 4 s) and spelled one word per panel as sung;
each panel keeps its word until the next line's word for that panel replaces it (otherwise fast lines blink).
Words of 5 letters or fewer fit 44 rows (7 per letter + 2 gap). An alternative is xLights' Text effect with an OS
font across the whole canvas (what the user's older sequences do).

## Story devices
- **Upside-down world** (pixies): the canvas is a scene (sky, stars in a subbuffer, ground band); a Morph band
  carries the ground to the top; sticks bounce with `direction='Down'`; trunk rings run down; roof and fence swap roles.
- **Collapse / nothing** (pixies): inward shockwaves, then cut everything but one small light.
- **Search / found** (pixies): a dim 2-arm searchlight pinwheel on the whole yard; a small "sonar" ring from a
  different prop each time the question is sung; the last one is big.
- **Progressive reveal** (owl_shine): the fence is "the way" - each "your way" lights another stretch until the
  line that completes it. Anything counted in the lyrics can be a progress bar on some prop.
- **Source of light** (bdw_inchrist): one prop (the manger spot) is where light comes from; every refrain sends a
  ring out from its position across the whole yard and along the fence both ways.
- **Tears dry in the sun** (owl_shine): blue Meteors down, then a warm fill rises and gold Meteors float up.
- **Rising sun** (owl_shine): a radial-out gradient (white→gold→pink→black) On in a subbuffer stepped upward across
  the whole-yard group, plus slow thin-armed pinwheel rays.
- **Call and response** (tso_wizards, from the user's joy_daddyweave): the band phrase lights the yard, the reply
  happens alone in the dark (`cut` the stop bar, then one character answers).
- **Lift** at a key change (bdw_inchrist, owl_shine): a whole-yard wave up + ring, and the palette steps up.

## Moments and contrast
- A handful of whole-yard moments per song at the structural peaks; everything else stays on groups.
- Quiet passages get *less* light: darkness, one character, the song's voice. The contrast is what makes the
  chorus land.
- End with one light left (the user's show: the Nativity spot is always the last light out).
- A team's or a rival's colour is a story device: in the Aggie War Hymn burnt orange appears only for t.u. and is
  always swept off, burned or sawed away; the school's maroon and white carry everything else. Gold only for the
  Aggie Ring. A crowd's shout into the band's silence ("SHORT!") is the word alone on a black yard.
