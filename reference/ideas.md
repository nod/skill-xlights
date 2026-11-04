# Ideas not yet tried

These are techniques seen in other people's xLights sequences. None of them has been built or rendered with this
toolkit yet, so treat each as a proposal: offer it to the user, build a short test, and get their verdict before
using it in a whole song. The settings keys come from real EffectDB strings. Still confirm each one in the user's own
sequences with `./run effect_examples.py <Effect>`, since a wrong key is silently ignored.

## Singing characters (Faces + picture eyes)
A matrix becomes a character that sings the lyrics. It's built from three layers on the same model:
- **Mouth: the Faces effect.**
  - Settings: `E_CHOICE_Faces_FaceDefinition=<face set>`, `E_CHOICE_Faces_TimingTrack=<lyric track>`,
    `E_CHOICE_Faces_Eyes=Open`, `E_CHECKBOX_Faces_Outline=0`.
  - The lyric track has three layers: phrases, words, and mouth shapes (`AI E FV L MBP O U WQ etc rest`).
  - `lyrics.py` already gives phrases and words. xLights fills the mouth-shape layer itself with *Breakdown words* on
    the timing track.
  - A face set is defined on the model (`<faceInfo>` in the layout). It's either the built-in matrix face or one image
    per mouth shape, with eyes open and closed. Ask the user whether they have one; never ship someone else's
    artwork.
- **Eyes: a Pictures layer above the mouth.**
  - Mostly open, with a 0.2-0.3 s closed-eyes blink every 2-4 s.
  - Glance up or down on a meaningful word.
  - This small hand animation is what makes the character feel alive.
- **Duets.**
  - Give each voice its own matrix, face set, colour and 3-layer track.
  - Split the lines by singer, or by the vocal stem's loudness per section.
  - Bring the second character in when that voice enters.

## Instrument pictures
- An animated GIF or PNG of the instrument appears on a matrix exactly when that instrument plays:
  - a trumpet on the horn stabs
  - a violin under the violin line
  - a disco ball through a dance break
- The stems give the timing.
- `E_CHOICE_Pictures_Direction=none` holds the picture still and lets the GIF animate itself.
- `right` / `left` / `up once` / `wiggle` / `peekaboo` move it. A picture travelling across a row of matrices is a
  sprite made from an image.

## Words with entrances
- Show one key word at a time with the Text effect: `E_TEXTCTRL_Text`, `E_FONTPICKER_Text_Font`, and
  `E_CHOICE_Text_Dir=none` to hold or `left` to scroll.
- Let the **In/Out transition** carry it: `T_CHOICE_In_Transition_Type` / `T_CHOICE_Out_Transition_Type` =
  `Doorway`, `Zoom`, `Wipe`, `Circle Explode`, `Blobs`, `Circular Swirl`.
- It's an alternative to hand-drawn pixel letters when a word is too long to stack, or the matrix is wide.

## Masks and blends
`Max` (brightest wins) is the safe default. The other layer methods make new looks from the same effects:
- **`1 is Unmask`, `2 is Mask`, `2 reveals 1`**: one effect's shape cuts or reveals another, e.g. moving Bars
  revealing a rainbow Pinwheel underneath. Whole sections can be built this way.
- **`Effect 1` + `T_CHECKBOX_LayerMorph=1`**: cross-fades from one layer's effect to the other's over its length.
- **`Average`** mixes the colours instead of the brighter one winning. **`Shadow 1 on 2`**, **`Subtractive`** and
  **`Additive`** are also available.

## Transitions as the motion
- A plain On or Spirals effect with `T_CHOICE_In_Transition_Type` / `Out` set to `Wipe`, `Clock`,
  `Circle Explode`, `Square Explode` or `Slide Bars`.
- The entrance and exit become the event, so a held colour sweeps in like a clock hand on the downbeat.
- Very cheap: no new effect types.

## How an effect spreads over a group
`B_CHOICE_BufferStyle` on a group effect changes its meaning:
- `Per Model Per Preview`: each member gets its own copy, e.g. a Shockwave on every spinner at once.
- `Single Line` (often with `B_CHOICE_BufferTransform=Rotate CC 90`): one chase runs through all the members as one
  line.
- Also: `Per Model Single Line`, `Line Segments`, `Vertical Per Model/Strand`, `Horizontal Per Model`.
- `B_CHOICE_BufferTransform=Rotate 180` / `Flip Horizontal` reverses it.

## Value curves on the shape
Animate the effect's geometry across a phrase, not just its brightness:
- Pinwheel `ArmSize` and `Twist`
- Bars or Pictures rotation (`B_VALUECURVE_Rotation`)
- Fill `Position` (a level rising)
- Shape `StartSize`
- Warp `X`/`Y`
- Wave `Number_Waves`
- Spirals `Movement`
- Fire `Height`

## Effects driven by a timing track
- VU Meter *Timing Event* types (`Timing Event Bar`, `Spike`, `Bars`, `Alternate Timed Sweep 2`) fire on each mark
  of `E_CHOICE_VUMeter_TimingTrack`. Feed it an onset track from `extract_events.py`.
- VU Meter *Note Level Pulse* and *Level Bar* follow the audio directly.
- Shape's `E_CHOICE_Shape_FireTimingTrack` launches a shape on each mark.
- Either lets xLights place hundreds of hits that would otherwise be written one by one.

## Effects still to explore
Galaxy (on arches), Kaleidoscope, Life, Candle, Spirograph, Snowstorm, Garlands, and more shader (`.fs`) files
beyond the ones in `effects.md`.
