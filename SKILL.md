---
name: xlights-skill
description: Design and generate xLights Christmas/holiday light-show sequences (.xsq) from a song's audio - split the song into instruments, find beats, notes, lyrics, key and structure, then write a sequence whose lights tell the song's story. Use when someone has an xLights show folder and wants a new sequence for an mp3, wants an existing generated sequence changed, or asks how to make their lights "dance" to a song.
---

# xLights sequencing from audio

You are building a light show for a person who will watch it on their own house. You cannot see the result:
xLights renders it on their machine. So you listen to the song with tools, design deliberately, write the design
down, generate the sequence with code, check it every way you can without eyes, and ask them what it looks like. If
the user has turned on xLights' API port and said you may drive their xLights, `xl.py` and `snap.py` let you render,
save and look at the actual frames first (`reference/pipeline.md`, "Render, save, read back"); the user's eye still
has the last word.

What made the user's favourites great was never the effect count. It was **a story the lights tell, timed to the
words, with every signature sound given one consistent look.** Read `reference/case-studies.md` before designing
anything - it is the user's own verdicts on their songs.

## Files in this skill
| Path | What |
|---|---|
| `scripts/` | the toolkit, copied into `<show>/tooling/`: `setup.sh`, `separate.sh` (Demucs + Basic Pitch), `extract_events.py` (beats, hits, bars, summary), `lyrics.py` (Whisper words), `analyze_key.py`, `find_motif.py` (every repeat of a riff from one example), `seqlib.py` (effect helpers + .xsq writer), `validate_xsq.py`, `timeline.py`, `layout_report.py`, `effect_examples.py`, `xl.py` (drive xLights: open, render, save, close), `fseq.py` + `layout.py` (decode a saved render at a model's channels), `snap.py` (a still of one prop from the render), `xsq_compare.py` (do two .xsq draw the same effects), `show_config.example.py`, `run` |
| `templates/build_template.py` | starting point for a song's generator |
| `examples/<song>/` | eight real generators with their handoff notes (`build.py`, `notes.md`, `summary.txt`). They use the names in `show_config.example.py` (the show they were made for) |
| `reference/pipeline.md` | setup, commands, analysis gotchas |
| `reference/xsq-format.md` | the file format: layers, blending, subbuffers, palettes, colour curves, value curves |
| `reference/effects.md` | each effect: what it looks like, the helper, verified or not |
| `reference/techniques.md` | recipes: characters, canvas motion, pixel art, crowds, story devices, moments |
| `reference/case-studies.md` | what was built for each song and what the user said; the feedback that became rules |

## First time in a show folder
1. Look around: `xlights_rgbeffects.xml` (layout), `xlights_networks.xml`, the sequences folders. Find the newest
   sequence made for the **current** layout (layouts change between years; old sequences reference models that
   no longer exist) and use it as the format reference.
2. Find out where xLights runs. If it's another machine, media and shader paths must use *that* machine's path
   (`MEDIA_ROOT` in show_config.py).
3. Install: copy `scripts/*` to `<show>/tooling/`, run `./setup.sh`, copy `show_config.example.py` to
   `show_config.py`, run `./run layout_report.py` (and `--draft-config`), and fill in the config.
   **Ask the user what the props physically are** - a matrix wrapped around a tree trunk, a wall of free-standing
   matrices, a spot on the manger - and write it in the config comments. Physical meaning drives good design.
4. Ask which of their existing sequences they love and why; read them with `effect_examples.py` and the XML. That's where their taste and the verified settings keys are.

## Making a sequence
1. **Listen.** `separate.sh`, `extract_events.py` (`--loose` if it drifts), `lyrics.py --model=medium.en`
   (`--prompt` + `--no-vad` if lines are missing), `analyze_key.py`. Read `summary.txt` + `lyrics.txt` together and
   write the section table in bars: intro, verses, pre-choruses, choruses, stops (kick count 0), breakdowns, key
   changes, the ending. Note which stem carries what (melody, lead, synth hook, backing "oohs").
2. **Understand.** What is the song about, in one sentence? What's the mood? What are its 2-4 signature sounds
   (a falsetto ooh, a guitar riff, a synth sparkle, a band that stops dead)? Where are its big moments (the key
   change, the drop, the last chorus, the silence)? Minor-key stretches are usually its darkest words.
3. **Design** (write it as the build's docstring before coding):
   - **A story and a character.** A light that does what the words say - a sprite, "the mind", a spark, a heart
     passed through a crowd. Map the lyric's images literally and playfully: "feet in the air" turns the world
     upside down, "spin it" spins the yard, "where is my mind?" sends out sonar pings, "your way" lights a road.
   - **One look per signature sound**, held all song (the oohs are always the lavender ghosts).
   - **The instrument map**, constant across the show for cohesion: kick → arches, snare → motion on the canvas /
     rings up trunks, bass → a dot on a long line positioned by pitch, melody → how high the spiral trees glow,
     drums → pixel sticks bounce.
   - **A colour plan** by section that follows the mood and the key (warm → rainbow at a lift; cold and dark in the
     minor pre-chorus). Ask the user's colour likes; this user found #FFAA00 too amber - gold is #FFC832.
   - **A handful of whole-yard moments** at the peaks; **darkness** for stops and quiet lines.
4. **Build** `tooling/songs/<song>/build.py` from the template or the nearest example. Anchor everything to bars,
   beats, hits, notes and words from the analysis - never hand-typed seconds.
5. **Check.** `validate_xsq.py` must say 0 problems. Draw `timeline.py` images and look at them. Print the Story
   track against the lyrics. Only if the user has set up rendering through xLights and said you may use it
   (`reference/pipeline.md`), and isn't working in xLights right now: open, render and save through `xl.py`, then
   `snap.py` the props that carry the story at the moments that matter, and fix what you see before handing off.
   Rebuild every other song afterwards if you touched `seqlib.py` (they should come out byte-identical) - other
   sequences depend on it.
6. **Hand off.** Write `seqs/<song>/notes.md` (the song, sections, concept, files, rebuild command, and the list of
   things you couldn't verify), then tell the user in plain words what they'll see, moment by moment, and what to
   check first. Ask for their render feedback, and fold it into the build and the notes.

## Rules from this user's feedback (keep unless your user says otherwise)
- **Groups over single models.** Single models only for a character that must land on one exact prop, or pixel art.
- **Whole-yard moments every so often** (`Seq.moment`), not constantly.
- **A matrix wall is ONE canvas: never flash panels on and off.** Light moves across it (sweeps, ripples, scrolls,
  climbs, characters). Solid colour that moves is fine.
- **Props wrapped on real objects get their own vocabulary** (trunks: rings racing up, barber poles, rising from the
  roots, drips) - not mini-walls.
- **Gradients, not flat colour - but keep them saturated.** Blend a colour toward a neighbour of its own family,
  not toward white (pastel) and never red straight into green (the midpoint is olive brown). The user called a
  build "more subdued than they should" when most motifs faded to white and the canvas sat at 18-25 %. Keep
  backgrounds around 35-45 %, foreground 85-100 %, and run `scripts/color_check.py` against a sequence they liked.
- **Contrast.** Quiet words get less light; the stop before a chorus is darkness and one small thing.
- **No amber unless asked**; gold sparingly, for meaningful moments.
- **Don't overwrite their edits**: the builder refuses if a sequence changed since it was generated - ask first.

## Working with the user
- They see the render; you don't. Lead with what they will see, in their words, and end with 2-5 concrete things to
  check. Keep it short; offer depth on request.
- When they point at a sequence they like, study it and name what you're taking from it.
- When they say "just try to one-shot it", do the whole job end to end, then report.
- Save what you learn about their taste where future sessions will see it (the song's notes.md, and memory if you
  have it).
