# Wizards in Winter (TSO) — rebuilt from scratch, 2026-11-21

Brief: "a great fun song where the notes literally dance like winter. What can you do to rework that one from
scratch?" + "some sphere or orb that dances across the scene occasionally would feel lively" + "make your best
guess" (the user was asleep; built, rendered and checked end to end).

## Status
Built (5,488 effects, 0 validation problems), rendered and saved through xLights on the Mac, frames read back and
checked (wall.py / yard.py / litstats.py). **Not yet watched by the user.**

**File: `seq2026/tso_wizards/tso_wizards_winter.xsq`** — a NEW file beside the old one. The user's own
`tso_wizards.xsq` was not replaced: the MCP push guard reported it "draws 365 things differently" from the last
push (edited in xLights?), so it was left alone and a copy was also saved as `tso_wizards.original.xsq`. Later it
turned out an xLights save alone rewrites `B_CHOICE_BufferStyle` "Per Model Per Preview" -> "Per Preview" on single
models (the same message came back for a file only the API had saved), so the 365 differences may be save
normalisation, not hand edits. Ask the user before replacing it.

## The song
`wis.mp3`, 186 s (music ends 182.2 s), on a click, 148.42 BPM, bar 1 at 0.315 s, bar = 1.617 s. E minor. Same
structure as the 2026-10 build (bars checked by ear then): 22 stop bars (STOPS), piano breakdown 58-61, drum drive
62-65, launch 92, rainbow 93-96, finale 97-110, hammer hits 174.0-178.2, last hit 181.42. Theme in `other`
(60-90), lead in `vocals`, the stop-bar runs in `piano` (3-7 notes each).

## Design (the docstring of build.py has it all)
- The band's stab freezes the yard (icy ring, ice flash on house/trunks, icicles dropping on every Vert); every
  piano note of the answer is a spinning snowflake (two 6x5 shapes alternating, drifting down) hopping Vert to Vert,
  high notes high (each run's own range), direction alternating per stop.
- Theme = a frozen xylophone on the 29 pixel sticks (pitch -> stick, aurora colour by pitch, white tip); spiral trees
  glow to the note's height. Lead = northern lights: the notes scroll across the wall over an aurora sky.
- Kick = arch pulses (Additive), snare = rings up the trunks (and wall ripples in the drive), bass = fence dot.
- The orb (AllModels radial gradient, Additive, AllModels is the LAST row): 13 appearances — bounces in over the
  arches and back (intro), spirals up each build, circles the whirl, drifts through the breakdown, bounces on the
  snare (drive), rockets up (launch), twin cyan/magenta orbs mirror-dancing (finale x3), alone and swelling in the
  silence before the last hit.
- Breakdown: dark, snow on the whole yard (Snowflakes, accumulating on the Verts), a big snowflake (5 centre Verts)
  crystallises one part per bar. Ending: ice cracks on the hammer hits, the orb swells, the last hit bursts it into
  snow and the big snowflake; manger spot (ice) last.
- Colour: ice, cyan, blue, night + aurora green, teal, violet, magenta. No amber/orange/gold. Spirals get bright
  colours only (their -70 % dimming curve).

## Files
| What | Where |
|---|---|
| Sequence | `seq2026/tso_wizards/tso_wizards_winter.xsq` (+ `.fseq`) |
| The user's sequence, untouched | `seq2026/tso_wizards/tso_wizards.xsq` (copy: `tso_wizards.original.xsq`) |
| Pictures (snowflakes, big snowflake) | `seq2026/tso_wizards/Images/wiz_*.png` (78, written by build.py) |
| Generator | `tooling/songs/tso_wizards/build.py` |
| Test (can be deleted) | `seq2026/tso_wizards/orb_test.xsq` (+ fseq) |

Rebuild: `cd tooling && ./run songs/tso_wizards/build.py`; close it in xLights; `./run xl.py push
../seq2026/tso_wizards/Images/wiz_*.png ../seq2026/tso_wizards/tso_wizards_winter.xsq` (needs `--force` after an
xLights save, which only normalises it); MCP open/render/save; `./run xl.py pull ../seq2026/tso_wizards/tso_wizards_winter.fseq`.

## Lessons
- Meteors as "snow" on 6-wide Verts reads as static/rain: use the Snowflakes effect (Type 1, count 3-6 per model,
  `Per Model Default`), "Falling & Accumulating" piles it up at the bottom.
- A moving orb: On + `Grad(..., mode='radial-out')` ending in black, in a subbuffer stepped every 50 ms on AllModels,
  **Additive** (with Normal the black corners blank the props under it: 4 black arch pixels vs 0), AllModels the
  last row so nothing covers it.

## Couldn't verify (the user's eye)
1. Do the dancing snowflakes (6x5 px, spinning) read as snowflakes from the street?
2. Is the orb big enough / round enough on the real yard (rx 6 %, ry 22 % of the yard buffer)?
3. The theme xylophone: does the forest feel like it's playing the tune?
4. The aurora sky + lead scroll in the lead sections — too busy or just right?
