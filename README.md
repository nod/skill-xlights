![Skill Header](resources/xlights.png)


# xlights-skill

A [Claude Code](https://claude.com/claude-code) skill that writes xLights light-show sequences (`.xsq`) from a song.

You give it an mp3. The agent listens to the song with audio tools: it splits the song into instruments and finds
the beats, notes, lyrics, key and structure. It designs a show around what the song is about, then writes a Python
generator that produces the sequence. You open the sequence in xLights, watch the render, and tell the agent what
to change.

The skill is opinionated. It aims for lights that tell the song's story, timed to the words, with each signature
sound always getting the same look. It isn't for a beat-flash mapper. `SKILL.md` and `reference/case-studies.md`
explain the approach, which was learned from one show's sequences and its owner's feedback.

I've been using Opus 5.5 on xhigh effort and getting suprisingly good results.

## Quickstart

How I'm using this: install this to `.claude/skills/skills-xlight`. Then start a claude code session in your xlights 
project directory.  I like to create a folder in my xlights project dir called `./newseqs` and put mp3s there that I want 
to sequence.

Then, just tell claude 

> use the xlights skill to create a sequence for `./newseqs/coolsong.mp3`

On the first start, it will install some dependencies.

## What's in here

| Path | What |
|---|---|
| `SKILL.md` | The instructions the agent loads: workflow, design rules, how to work with you |
| `scripts/` | The toolkit the agent copies into your show folder as `tooling/` |
| `templates/build_template.py` | Starting point for a song's generator |
| `examples/<song>/` | Eight real generators, each with handoff notes and the analysis summary they were built from |
| `reference/` | The pipeline, the `.xsq` file format, effect settings, design techniques, case studies |

Audio files and lyrics are not included. Bring your own mp3s.

## Install the skill

Clone it into Claude Code's skills folder. Use either location:

```sh
# available in every project
git clone <this repo> ~/.claude/skills/xlights-skill

# or only in one show folder
git clone <this repo> <show>/.claude/skills/xlights-skill
```

Start Claude Code in your xLights show folder (the one with `xlights_rgbeffects.xml`). The skill appears as
`xlights-skill`.

## Requirements

### You install
- **xLights**, to render and play the sequences. It can run on a different machine from the agent; see
  `MEDIA_ROOT` below. With xLights 2026.17 or newer and its API port on, the agent can also render and save through
  it and read the render back (`xl.py`, `snap.py`; `reference/pipeline.md`, "Render, save, read back"). It does
  that only when you ask. The API has no password, so read the warning there before you open the port.
- **bash** and **Python 3** (any recent version; it's only used to bootstrap).
- **ffmpeg**, which Demucs uses to read mp3s. On Debian/Ubuntu: `apt install ffmpeg`. On macOS: `brew install ffmpeg`.

### `scripts/setup.sh` installs
Everything lives in `~/.cache/xlights-tooling`, outside the show folder (override with `XLIGHTS_TOOLING_CACHE`).
Show folders are often synced, and these files are big.

- **uv**. If uv isn't on your PATH, setup installs it into a private bootstrap venv. uv then downloads Python 3.11
  for the environments.
- **`audio` environment** (~1.7 GB):
  - PyTorch, CPU-only build. The default wheel pulls ~5 GB of CUDA, so setup uses the CPU index.
  - Demucs, librosa, soundfile, numpy, matplotlib, faster-whisper
- **`basicpitch` environment** (~200 MB): Spotify Basic Pitch with its ONNX model. Setup removes the TensorFlow it
  pulls in, because TensorFlow crashes against numpy 2.

### Downloaded on first use
- The Demucs `htdemucs_6s` model weights (six stems: drums, bass, guitar, piano, vocals, other).
- The Whisper model for lyrics. `medium.en` is ~1.5 GB and is recommended; the default `small.en` is smaller but
  misses more words.

### Disk and time
- Plan on about 4 GB for the environments and models. Separated stems add about 60 MB per minute of song, also in
  the cache.
- No GPU is needed. On a CPU, separating a song takes a few minutes and lyrics take a few more.

### What needs what
Only the listening step needs the heavy packages. The scripts that write and check sequences use only Python.

| Script | Needs |
|---|---|
| `separate.sh` | Demucs, PyTorch, Basic Pitch, soundfile, ffmpeg |
| `extract_events.py`, `analyze_key.py`, `find_motif.py` | librosa, numpy |
| `lyrics.py` | faster-whisper |
| `timeline.py` | matplotlib |
| `seqlib.py`, `validate_xsq.py`, song `build.py` files | Python only, plus your `show_config.py` |
| `layout_report.py`, `effect_examples.py`, `color_check.py` | Python only |
| `xl.py` | Python only, plus `show_config.py` (`MEDIA_ROOT`); xLights 2026.17+ with its API port on |
| `fseq.py`, `layout.py`, `snap.py` | zstandard (setup.sh installs it); `snap.py` also Pillow, which matplotlib brings |
| `xsq_compare.py` | Python only |

`seqlib.py` imports `show_config.py` when it loads. Every script that uses `seqlib` fails until that file
exists, so create it first.

## Platforms

Developed and tested on Linux. macOS should work, since the CPU PyTorch index has macOS wheels, but it's untested.
On Windows, use WSL, because the scripts are bash. xLights itself can stay on any OS.

## Setting up a show

The agent does these steps when you first ask for a sequence. Here they are by hand:

```sh
mkdir -p <show>/tooling && cp -r ~/.claude/skills/xlights-skill/scripts/* <show>/tooling/
cd <show>/tooling
./setup.sh
./run layout_report.py                            # lists your models and groups
./run layout_report.py --draft-config > show_config.py
```

Then edit `show_config.py`. It tells the generator about your yard:
- Which group is the whole yard.
- Which models form a matrix wall, which are arches, which are pixel sticks, and so on.
- Where each prop sits left to right.
- **What each prop physically is.** A matrix wrapped around a tree trunk should be sequenced differently from a
  free-standing panel, so write it in the comments.

`show_config.example.py` is a filled-in example from the show the skill was built on.

If the agent runs on one machine and xLights runs on another (for example, a Linux box writing into a synced
folder that a Mac renders), set `MEDIA_ROOT` to the show folder's path **on the xLights machine**. The mp3 and
shader paths inside the sequence use it.

## Using it

Put the song in its own folder under `seqs/`, for example `seqs/mysong/mysong.mp3`. Then ask Claude Code something
like:

> Make a light show for seqs/mysong. Look at the lyrics, the key and the mood, and come up with something original.

The agent then:
1. Runs the analysis: `separate.sh`, `extract_events.py`, `lyrics.py` and `analyze_key.py`.
2. Designs a story and an instrument-to-prop map.
3. Writes `tooling/songs/mysong/build.py` and runs it to produce `seqs/mysong/<name>.xsq`.
4. Validates the result.
5. Writes `seqs/mysong/notes.md` and tells you what to look for when you render.

Open the sequence in xLights, render it, and describe what you see. "The colours look subdued" or "the words go
by too fast" is the kind of feedback it works from. The build is a script, so changes are cheap.

Things that help:
- Point it at a sequence you already love and say why. It reads the XML and takes settings and ideas from it.
- Tell it what your props physically are, and which colours you like or dislike.
- If you edit a generated sequence in xLights, the builder refuses to overwrite it without asking.

## Running the tools yourself

```sh
cd <show>/tooling
./separate.sh mysong                              # stems + notes
./run extract_events.py mysong                    # beats, bars, drum hits -> songs/mysong/summary.txt
./run extract_events.py mysong --loose            # if the band didn't play to a click (grid drift > ~60 ms)
./run lyrics.py mysong --model=medium.en          # word timestamps -> songs/mysong/lyrics.txt
./run lyrics.py mysong --model=medium.en --no-vad --prompt="a few, sung, phrases"   # if lines are missing
./run analyze_key.py mysong
./run find_motif.py mysong RIFF=6.6:7.6 --notes=6     # every repeat of a riff you heard at 0:06.6
./run songs/mysong/build.py                       # write the sequence
./run validate_xsq.py ../seqs/mysong/mysong.xsq   # must report 0 problems
./run timeline.py ../seqs/mysong/mysong.xsq /tmp/t.png 0 60   # picture of the first minute
./run color_check.py ../seqs/a.xsq ../seqs/b.xsq  # compare colour vividness with a sequence you like
./run xl.py open ../seqs/mysong/mysong.xsq && ./run xl.py render && ./run xl.py save   # through xLights' API
./run snap.py --fseq ../seqs/mysong/mysong.fseq --model Arch1 --at 0:42.5              # what that prop showed
```

`reference/pipeline.md` covers the gotchas.

## About the examples

The examples were written for one specific yard: six free-standing vertical matrices, three tree-trunk wraps,
arches, 29 pixel sticks, spiral trees, a fence line and a manger spotlight. They use that show's model names, so
they won't run against your layout as they are. Read them for the ideas and the effect settings, then let the
agent write builds for your own `show_config.py`.

## License

MIT. See [LICENSE](LICENSE).
