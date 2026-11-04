# The .xsq format (what `seqlib.Seq.write()` produces)

xLights sequences are XML. Everything here was checked against real 2026.19 files; when in doubt, open a recent
sequence from the user's show (the newest one made on the current layout) and copy its structure.

## Skeleton
```xml
<xsequence BaseChannel="0" ChanCtrlBasic="0" ChanCtrlColor="0" FixedPointTiming="1" ModelBlending="true">
  <head>  version 2026.19, song/artist/album, <sequenceTiming>25 ms</sequenceTiming>, <sequenceType>Media</sequenceType>,
          <mediaFile>ABSOLUTE path as seen by the machine running xLights</mediaFile>, <sequenceDuration>seconds</sequenceDuration>
  <ColorPalettes>  one <ColorPalette> string per distinct palette (effects reference by index)
  <EffectDB>       one <Effect> settings string per distinct settings set (effects reference by index)
  <DisplayElements>  timing tracks first, then model/group rows, in sequencer order
  <ElementEffects>   per element: <EffectLayer>s, each a list of <Effect ref name startTime endTime palette/>
```
- Times are integer **milliseconds on the 25 ms frame grid** (`q()` rounds seconds to it). Within one layer effects
  must not overlap (`Seq.resolve()` clips earlier ones). Nothing may run past the audio (`write()` trims).
- **Layer 0 is the top.** Layers blend downward with `T_CHOICE_LayerMethod` - `seqlib` sets `Max` on every layer
  but the last so stacked effects add up instead of covering each other.
- `ModelBlending="true"`: effects on a group and effects on its member models blend. This is what lets a character
  run on single models on top of group backgrounds (confirmed on a real render - the sprite in Wizards in Winter).
- Timing tracks: `<Element type="timing">` with `<Effect label startTime endTime/>` marks. Add generously -
  Sections, Story (what the lights are saying), Lyrics, Bars, Beats, Kick, Snare, note tracks. They're how the user
  finds things in xLights.

## Settings strings (EffectDB)
Comma-separated `KEY=value`, sorted. Prefixes: `E_` effect settings, `B_` buffer, `T_` timing/layer, `C_` palette.
**Wrong keys are silently ignored**, so copy keys from real files (`scripts/effect_examples.py <Effect>`).
- `B_CHOICE_BufferStyle`: `Default`; `Per Model Default` (each member model renders alone);
  `Per Model Per Preview` (each model alone, in its real orientation - needed for Fill/bounce on vertical sticks);
  `Per Preview` (the whole group as laid out).
- `B_CUSTOM_SubBuffer=x1xy1xx2xy2x0.00x0.00` - the effect renders only inside that rectangle (% of the buffer,
  **y=0 is the bottom**). Values may go outside 0-100 (overscan: `-20x-20x120x120` hides shader edges).
  For pixel art on a matrix, put edges just below pixel boundaries: column c of W spans
  `c*100/W - 0.01 .. (c+1)*100/W - 0.01` (see `cols()/rows()` in examples/bdw_inchrist).
- `T_TEXTCTRL_Fadein` / `T_TEXTCTRL_Fadeout` (seconds, `0.75`), `T_CHOICE_In_Transition_Type=Wipe`, ...
- Value curves (animate a slider): `E_VALUECURVE_<Key>=Active=TRUE|Id=ID_VALUECURVE_<Key>|Type=Ramp|Min=0.00|Max=100.00|P1=0.00|P2=100.00|RV=TRUE|`
  (Type also `Sine` with P2/P3, `TO` offset...). `Seq.fill` animates the Fill position this way.

## Palettes
`C_BUTTON_Palette1=#RRGGBB,C_CHECKBOX_Palette1=1,...` up to 8 slots, plus `C_SLIDER_Brightness`, sparkles
(`C_SLIDER_SparkleFrequency`, `C_COLOURPICKERCTRL_SparklesColour`).
**Colour curves** (gradients) replace a slot's colour:
`C_BUTTON_Palette1=Active=TRUE|Id=ID_BUTTON_Palette1|Timecurve=4|Values=x=0.000^c=#ff0000;x=1.000^c=#ffffff|`
Timecurve modes: 0/absent = over the effect's time, 1 right, 2 down, 3 left, 4 up, 5 radial-in, 6 radial-out,
7 cw, 8 ccw. `Grad(...)` builds these. A radial-out gradient that ends in black draws a soft disk (glows, the sun).

## Files referenced by effects
Shaders (`E_0FILEPICKERCTRL_IFS`) and the media file need absolute paths **on the machine running xLights**
(`MEDIA_ROOT` in show_config.py). Shader float inputs are stored x100 (`E_SLIDER_SHADERXYZZY_<name>`), bools as
`E_CHECKBOX_SHADERXYZZY_<name>`.

## Layout file (xlights_rgbeffects.xml)
`<models>`: each `<model name DisplayAs ...>`; matrices: `NumStrings x StrandsPerString` strands of
`NodesPerString / strands` pixels, `Vertical="true"` = strands are columns; arches `NodesPerArch`; single lines
`NodesPerString`; positions `WorldPosX/Y/Z`. `<modelGroups>`: `<modelGroup name models="a,b,c" layout="minimalGrid"
GridSize="400">`. Groups can contain groups. `scripts/layout_report.py` summarises it.

## What an xLights Save does to the file
xLights rewrites the whole file on every Save, edited or not:
- times snap to the 25 ms frame grid (an off-grid 5680 becomes 5675);
- settings and palette strings are normalised (keys re-ordered, values reformatted);
- `EffectDB` and `ColorPalettes` are rebuilt and re-indexed, so every `ref` and `palette` number can change.

So the bytes differ after any Save, and a hash (`.build_hashes.json`) cannot tell a hand edit from a plain Save. To
tell them apart, compare by content: per element and layer, the list of (effect name, start, end) with one frame
(25 ms) of tolerance on the times, then the settings of the effects that are still paired.

Other things the files on disk tell you:
- **Autosave writes `<seq>.xbkp`** beside the sequence, never the `.xsq` or the `.fseq`. A `.xbkp` newer than the
  `.xsq` means xLights holds unsaved edits; closing the sequence discards them. Look there when work seems lost.
- **A render does not write the `.fseq`; a Save does.** The `.fseq` is **sparse**: it holds only the channels of the
  models used in that sequence (a model not in the sequence reads as dark), and models with no controller are
  numbered by name after the last controller. A sequence whose length changed keeps the old `.fseq`'s frame count
  through open, render and save: move the old `.fseq` aside first.
- **A Single Line, or an Arches model with one arch, has a one-pixel-tall default buffer**, so any directional
  effect (Bars, Fill, a wipe) renders on it as a solid fill. Give it a buffer with more than one row
  (`Per Model Per Preview` on its group, or a render buffer the effect can move across) when you want motion on it.
