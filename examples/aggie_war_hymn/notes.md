# Aggie War Hymn — sequence notes

Last updated 2026-11-21. Brief: "completely redo it, it's boring… THE BEST UNIVERSITY ON THE PLANET. It deserves
something amazing." Use the school's maroon and white; use the logo file. Full rivalry approved (orange only for t.u.).

## Status
Built (2,766 effects, 0 validation problems), rendered and saved through xLights on the Mac (xl_mcp), frames read
back and checked with snap/wall/litstats. **User's verdict after the first build: "that's pretty great"** (2026-11-21).

## The song
- `trimmed-hymn.wav`, 177.5 s. Band only (no vocals: Whisper found 0 words; vocal stem -52 dB). B-flat major,
  111 BPM, live (`extract_events.py --loose --melody=other`). Last strain lifts to E-flat at bar 67.
- Structure confirmed by the user: fanfare (bars 1-4) · Hullabaloo x2 (5-6) · verse 1 "All hail" (7-23) · verse 2
  "Good-bye" (24-40) · "Saw Varsity's horns off" x3 + SHORT (41-47) · "Varsity's horns are sawed off" x3 + SHORT
  (48-54) · interlude (55-66) · final strain twice in E-flat (67-82). The verse repeats at a 68-beat lag; each line is
  one 8-beat phrase (2 bars), then a 3-bar tag: "We're goin' to beat you all to" / "Chig-gar-roo-gar-rem x2" /
  "Rough! Tough! Real stuff! Texas A&M!".
- The two SHORT! stops: band stab at 100.19 s and 115.19 s, then 1.5 s of silence (100.6-102.2, 115.6-117.2).
- Word placement is by tune, not by voice: the `Words` timing track shows which line each phrase is.

## Design
See the docstring of `build.py` (the whole story, section by section). In short: Kyle Field lights up, the ATM logo,
rally, the gold Aggie Ring, the Spirit, yells, TEXAS A&M one letter per Vert after every Rough/Tough/Real stuff;
verse 2 sweeps the orange off, the eyes of Texas get burned ("sounds like hell!"); the orange longhorn gets sawed off
while the yard sways, SHORT in the silence; 12TH MAN + the crowd stands + Block T; key-change lift, logo with
fireworks, TEXAS A&M, the logo and manger spot last.

## Files
| What | Where |
|---|---|
| Sequence | `seq2026/aggie_war_hymn/aggie_war_hymn.xsq` (+ `.fseq`) |
| The user's original (boring) sequence | `seq2026/aggie_war_hymn/aggie_war_hymn.original.xsq` |
| Pixel-art pictures (6x44 PNGs, one per Vert) | `seq2026/aggie_war_hymn/Images/awh_*.png` (written by build.py) |
| Generator | `tooling/songs/aggie_war_hymn/build.py`, art in `art.py` |
| Analysis | `tooling/songs/aggie_war_hymn/events.json`, `summary.txt`, `midi/` |
| Test sequences (can be deleted) | `logo_test.xsq`, `layer_test.xsq`, `layer_test2.xsq` (+ fseq), `Images/test_6x44.png`, `Images/atm_led*.png` |

Rebuild: `cd tooling && ./run songs/aggie_war_hymn/build.py`, validate, then
`./run xl.py push ../seq2026/aggie_war_hymn/aggie_war_hymn.xsq ../seq2026/aggie_war_hymn/Images/awh_*.png`
(close the sequence in xLights first: a push refuses the open sequence), open/render/save via the MCP, and
`./run xl.py pull ../seq2026/aggie_war_hymn/aggie_war_hymn.fseq`. Look with `./run wall.py --fseq … --at t1,t2`
(nine Verts side by side) and `./run litstats.py <fseq> <times> <models>`.

## Things learned on this show (2026-11-21)
- **Layer blend `Max` shows only the top layer on this xLights (2026.19).** Two diagnostic renders
  (`layer_test.py`, `layer_test2.py`): with Max, a Morph over a Butterfly showed only the Morph; four stacked
  subbuffer layers showed only layer 0; and the saved `bdw_joy.fseq` shows the same (its letters render as one bar).
  `Normal` (no key) composites correctly (lit covers, unlit shows through), so does `Additive`. build.py uses an
  `NSeq` subclass that turns every Max into Normal; flashes over a background use Additive. A fading `On` is
  opaque: it covers the layers under it while it fades.
- **The logo file can't be shown as a picture on the Verts**: across the group it becomes nine thin slices, and
  scrolled it reads as moving blobs. The logo is redrawn as pixel art (`art.py` LOGO) on Verts 7, 1, 8, 2, 9.
- **Pictures with a 6x44 PNG land pixel-exact on a single Vert** (No Scaling), PNG alpha is transparent. One
  effect per Vert per picture instead of one per rectangle.
- **The spiral trees carry a -70 % gamma-2.2 dimming curve** in the layout: maroon vanishes on them (renders ~12/255);
  use pure red `#FF0028` and white there. Controller brightness: Verts 15-18 %, arches 20 %, fence 25 %,
  Nativity 60 % (applied by the controller, not in the fseq).
- **The Verts are staggered**: Vert-3, 4, 1, 2, 5, 6 in front; Vert-7, 8, 9 set back in the gaps. Left to right:
  3, 4, 7, 1, 8, 2, 9, 5, 6 — nine panels, exactly "TEXAS A&M".

## Couldn't verify (the user's eye)
1. Does the pixel-art ATM read as the logo from the street (it spans five Verts, two rows deep)?
2. Is maroon `#A0001C` on the LEDs the right maroon, or too red / too dark?
3. Do the word placements (phrase per line) match how they hear the band version?
4. The sway: does the yard feel like the student section sawing?
5. The orange-eye pairs (2x2 px) — big enough?
