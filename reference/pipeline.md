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
faster than anything. Things xLights would show but these checks can't: whether a motif *reads*. If the user has
set up the next section and said you may use it, look yourself; otherwise list those for the user as "things to
check when you render".

## Render, save, read back (optional, and only when the user asks for it)
Everything above checks the XML. This step checks the RENDER: `xl.py` drives the running xLights through its
automation API, saves (the save is what writes the `.fseq`), and `snap.py` decodes the saved frames at a model's
exact channels and draws the prop as it was lit. It takes over the user's xLights while it runs, so use it only
when they have set it up and said yes, and not while they are working in xLights. Needs xLights 2026.17 or newer.
```sh
./run xl.py status                                    # which show folder xLights has loaded, what is open
./run xl.py open ../seqs/<song>/<name>.xsq            # refuses on another show folder, unsaved changes, newer .xbkp
./run xl.py render                                    # ONE renderAll; nothing may touch the sequence meanwhile
./run xl.py save                                      # writes the .fseq and waits until it stops growing
./run snap.py --fseq ../seqs/<song>/<name>.fseq --model <Model> --at 1:02.5                    # a still of one prop
./run snap.py --fseq ../seqs/<song>/<name>.fseq --model <Model> --strip 1:02..1:04 --step 0.1  # a contact sheet
./run xl.py close                                     # refuses while xLights reports unsaved changes
```
Setup, once, by the user in xLights: Preferences -> Output -> API Port -> Port A (49913), and **GPU rendering OFF**
(Preferences; on by default). The Metal shader effects hung the machine under automation, and the API cannot report
the setting, so `xl.py` cannot check it: ask. From another machine set `XLIGHTS_HOST=<the xLights machine>`; `xl.py`
maps paths through `MEDIA_ROOT` the way the media paths already are, and reads the `.fseq` from this machine's copy
of the show folder once it has synced, so the sync has to carry the `.fseq` back as well as the `.xsq` out.

**The API has no password.** xLights binds the port on every interface and answers any request that reaches it:
open, save over, Save As anywhere, close without saving, and `runScript`, which runs a script file from any path
on that machine. Turn the port on only while you use it, and if the agent runs on another machine, let the
firewall in from that one address only, never the whole LAN. It also answers web pages (it sends
`Access-Control-Allow-Origin: *`), so a page open in a browser on a machine that can reach the port could send it
commands too: another reason to keep it off when it isn't in use.

Rules, each paid for with a crash or an evening on the show this came from; `xl.py` enforces them:
- One render at a time, and nothing touches the sequence while it runs (a lock file). Churn under a live render is
  what reset the GPU, not the render itself. If xLights doesn't answer the render, the lock stays (it expires after
  20 minutes): it may still be rendering.
- A render does not write the `.fseq`; a save does, and the API returns before the write is finished. Read the file
  only after `save` reports it settled.
- xLights holds the user's unsaved edits in memory, and an API open or close never shows the Save Changes dialog.
  `close` and `open` ask xLights to close without force, so xLights itself refuses while there are unsaved changes;
  then ask the user (`save` keeps them, `close --discard` throws them away). `open` also refuses while the target's
  `<name>.xbkp` (autosave, never the `.xsq`) is newer than its `.xsq`: the API skips xLights' offer to restore it.
- A save rewrites the `.xsq`, so the builder would refuse the next build. When the `.xsq` was the builder's own
  output before the save, `save` compares the two by content (`xsq_compare.py`) and records the saved file as the
  build if they draw the same effects; if they don't, xLights held edits, and the builder refuses as it should.
- The loaded show folder is part of a sequence's identity: `xl.py` refuses to open, render or save while xLights has
  another show loaded, because that can write every model the other layout lacks out of the file.
- `snap.py` refuses to read past the next model's start channel (a wrong geometry would quietly read the neighbour)
  and draws exactly the frame you ask for. Sample strictly inside an effect's span: a boundary frame still holds the
  neighbour's last frame. It reads each model's channel count and colour order from its string type (`GRB Nodes`,
  `RGBW Nodes`, single colour), and refuses the one-node-per-string types.

What it buys: whether a motif reads, whether the right prop lit, and what colour actually came out, settled from the
file instead of from the user's description. The user's eye still has the last word; it just starts later.

The builder keeps a hash of each file it wrote in `.build_hashes.json` and refuses to overwrite a sequence that
changed since (the user edited it in xLights). A changed hash can also mean the user only *saved*: xLights rewrites
the whole file on every Save (times snap to the grid, strings normalise, `EffectDB` re-indexes; see
`xsq-format.md`), so compare the effects by content before concluding they edited it: build to a scratch path
and `./run xsq_compare.py /tmp/built.xsq ../seqs/<song>/<name>.xsq` (`xl.py save` does this itself). Back it up or
ask before `--force`. To test without touching the real file, pass an output path. If you test-build to a scratch
path, remember the hash bookkeeping writes there too.
