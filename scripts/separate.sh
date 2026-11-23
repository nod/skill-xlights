#!/usr/bin/env bash
# Split a song into instrument stems (Demucs) and transcribe the pitched stems to notes (Basic Pitch).
#   usage: separate.sh <song>      where seqs/<song>/ holds the song's .mp3 (or .wav)
# Stems (large) go to the cache; note CSVs (small) go to tooling/songs/<song>/midi/.
set -euo pipefail
SONG="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"
SHOW="$(dirname "$HERE")"
CACHE="${XLIGHTS_TOOLING_CACHE:-$HOME/.cache/xlights-tooling}"
V="$CACHE/venvs"
# the song's audio: an .mp3 (or a .wav) in seqs/<song>/. `|| true`: under pipefail, ls failing on a missing
# *.mp3 would end the script silently with nothing separated.
MP3="$( (ls "$SHOW/seqs/$SONG"/*.mp3 "$SHOW/seqs/$SONG"/*.wav 2>/dev/null || true) | head -1)"
[ -n "$MP3" ] || { echo "no .mp3 or .wav in $SHOW/seqs/$SONG" >&2; exit 1; }
STEMS="$CACHE/stems/$SONG"
MIDI="$HERE/songs/$SONG/midi"
mkdir -p "$STEMS" "$MIDI"

# The stems and notes are only good for the mp3 they came from. source.txt records its sha256 and name, so a
# replaced mp3 (another edit of the song under the same name) is separated again instead of reusing old stems.
SRC="$("$V/audio/bin/python" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$MP3")  $(basename "$MP3")"
for d in "$STEMS" "$MIDI"; do
    if [ -f "$d/source.txt" ] && [ "$(cat "$d/source.txt")" != "$SRC" ]; then
        echo "$(basename "$MP3") is not the mp3 these were made from: redoing $d"
        rm -f "$d"/*.wav "$d"/*_basic_pitch.csv "$d/source.txt"
    elif [ ! -f "$d/source.txt" ] && [ -n "$(ls -A "$d")" ]; then
        echo "note: $d was made before source tracking; assuming it came from $(basename "$MP3") (delete it to redo)"
        echo "$SRC" > "$d/source.txt"
    fi
done

if [ ! -f "$STEMS/drums.wav" ]; then
    echo "separating $MP3 (a few minutes on CPU) ..."
    "$V/audio/bin/python" -m demucs -n htdemucs_6s -o "$CACHE/demucs-tmp" --filename "{stem}.{ext}" "$MP3"
    mv "$CACHE/demucs-tmp/htdemucs_6s/"*.wav "$STEMS/"
    rm -rf "$CACHE/demucs-tmp"
    rm -f "$MIDI"/*_basic_pitch.csv                 # notes from older stems
    echo "$SRC" > "$STEMS/source.txt"
fi

for s in vocals bass guitar piano other; do
    [ -f "$MIDI/${s}_basic_pitch.csv" ] && continue
    echo "transcribing $s ..."
    "$V/basicpitch/bin/basic-pitch" --save-note-events "$MIDI" "$STEMS/$s.wav" >/dev/null 2>&1
    rm -f "$MIDI/${s}_basic_pitch.mid"
done
echo "$SRC" > "$MIDI/source.txt"

# report which stems actually carry sound
"$V/audio/bin/python" - "$STEMS" <<'EOF'
import sys, numpy as np, soundfile as sf
for s in ('drums', 'bass', 'guitar', 'piano', 'other', 'vocals'):
    y, _ = sf.read(f'{sys.argv[1]}/{s}.wav')
    print(f'  {s:7} {20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9):6.1f} dB')
EOF
echo "stems: $STEMS"
echo "notes: $MIDI"
