# The listening pipeline: setup, commands, gotchas

Scripts live in `<show>/tooling/` (copied from this skill's `scripts/`). Big things (Python envs ~1.6 GB, stems
~60 MB per song-minute) live in `~/.cache/xlights-tooling` (`XLIGHTS_TOOLING_CACHE`), outside the show folder -
show folders are often synced (Syncthing/Dropbox) and must not fill up.

## One-time setup
```sh
cd <show>/tooling && ./setup.sh        # uv venvs: 'audio' (librosa, Demucs CPU torch, faster-whisper), 'basicpitch'
cp show_config.example.py show_config.py && ./run layout_report.py   # then edit show_config.py for this show
```
Gotchas found the hard way (setup.sh handles them):
- the default torch wheel pulls ~5 GB of CUDA; install from the CPU index.
- basic-pitch's TensorFlow crashes with numpy 2: uninstall TF so Basic Pitch uses its ONNX model; pin `setuptools<81`.
- if `uv` has a global `exclude-newer`, very new packages may not resolve; pin older versions.

## Per song
The mp3 goes in `seqs/<song>/` (song keys may contain a slash: `new/owl`).
```sh
./separate.sh <song>                     # Demucs htdemucs_6s stems + Basic Pitch notes; prints each stem's loudness
./run extract_events.py <song>           # beats, bars, drum hits, notes -> songs/<song>/events.json + summary.txt
./run lyrics.py <song> --model=medium.en # Whisper word timestamps -> lyrics.json / lyrics.txt
./run analyze_key.py <song>              # key per 16 s window; spot modulations and minor stretches
./run find_motif.py <song> HI=6.6:7.6 LO=9.0:10.05 --notes=6   # every repeat of a riff the user pointed at
```
- **If the user has a video of their real show**, use it: it's the only view of how effects, colours and brightness
  actually look on their props. `footage.py <xsq> <video> --sync` finds the offset, `--map` shows where each element
  is in the frame and whether the video matches that version of the sequence (peak r ~0.9 yes, ~0.3 no), and
  `footage.py <xsq> <video> out.png 30-36/6` labels frames with the effects running. Read the frames yourself.
  Phone cameras auto-expose and clip saturated pixels to white, so trust shapes and relative brightness over hue.
- `extract_events.py` fits a fixed click grid and reports drift per 20 s window. **Drift over ~60 ms = the band
  played without a click: rerun with `--loose`** (beat tracker follows the drummer; hits keep real times). Use
  `--bpm=` when tempo comes out half/double, `--melody=<stem>` for instrumentals.
- Whisper drops lines (it lost most of a song after a silence; it found 7 lines of the Pixies song). Fix:
  `--prompt="a few phrases you know are sung, comma separated" --no-vad`. Always read `lyrics.txt`; Whisper also
  hallucinates text in silence after the song ends (ignore anything past `events.json` `end`).
- When the user names a sound ("the da-da-da run at 0:06"), find the example in the notes CSV, then
  `find_motif.py` with it (one NAME=t0:t1 per variant). Clean solo figures score 0.9-1.0 on repeats; under a full band
  0.5-0.8, and chordal figures match loosely everywhere - pick those by their spot in the bar, then ask the user.
- Don't download audio from YouTube or other sites for the user; ask them to put the file in the folder.
- Never write full song lyrics into files you hand around; `lyrics.json` stays in `tooling/songs/<song>/`.

## Reading summary.txt
One row per bar: loudness per stem (drums, bass, gtr, piano, other, vox in dB; -80 = silent), hit counts, the
melody notes. Sections show up as column changes: drums entering (-80 → -20), vocals dropping out (instrumental
hook), kick count 0 (a band stop), guitar dropping 20 dB (a quiet chorus). Pair it with lyrics.txt timestamps and
analyze_key.py to write the `SECTIONS` table.

## Build, check, look
```sh
./run songs/<song>/build.py                      # writes seqs/<song>/<name>.xsq (refuses if edited in xLights)
./run validate_xsq.py ../seqs/<song>/<name>.xsq  # unknown models, overlaps, off-grid times, bad refs -> must be 0
./run timeline.py ../seqs/<song>/<name>.xsq /tmp/a.png 0 60   # picture of every row/layer; look at it
```
Also print the Story timing track (labels + times) and read it against the lyrics - it catches mistimed moments
faster than anything. Things xLights would show but these checks can't: whether a motif *reads*. List those for the
user as "things to check when you render".

The builder keeps a hash of each file it wrote in `.build_hashes.json` and refuses to overwrite a sequence that
changed since (the user edited it in xLights). Back it up or ask before `--force`. To test without touching the real
file, pass an output path. If you test-build to a scratch path, remember the hash bookkeeping writes there too.
