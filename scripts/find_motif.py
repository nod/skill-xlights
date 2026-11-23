"""Find every repeat of a short musical figure (a riff, a run, a stab) from an example or two you've located by ear.

usage: find_motif.py <song> NAME=t0:t1 [NAME=t0:t1 ...] [--stem=other] [--min=0.5] [--notes=6]
  NAME=t0:t1   an example of the figure in seconds (several names = several variants, e.g. HI=6.62:7.62 LO=9.0:10.05)
  --stem       the stem it plays in (drums bass guitar piano other vocals) or 'mix' for the whole song
  --min        keep matches scoring at least this (1.0 = the example itself; real repeats under a full band ~0.5-0.8)
  --notes      how many notes the figure has; if the example's detected onsets don't come to that, N are spread
               evenly over its first..last onset (default: as many as are detected)

Matches the chroma (which notes) plus the onset envelope (the rhythm) by normalised correlation, keeps the best
variant per spot, and for each match lists its note onsets: the example's onset pattern shifted onto the match,
each snapped to a detected onset within 60 ms. Writes songs/<song>/motifs.json:
  [{"name", "t", "score", "notes": [onset times]}] sorted by time.
"""
import json, os, sys
import numpy as np, librosa
from seqlib import song_dir, cli_args, SHOW

args = cli_args()
opts = {a[2:].split('=')[0]: a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
song, specs = args[0], [a for a in args[1:] if '=' in a]
stem, lo, nnotes = opts.get('stem', 'other'), float(opts.get('min', 0.5)), opts.get('notes')
CACHE = os.environ.get("XLIGHTS_TOOLING_CACHE", os.path.expanduser("~/.cache/xlights-tooling"))
path = (next(p for ext in ('*.mp3', '*.wav') for p in sorted((SHOW / 'seqs' / song).glob(ext))) if stem == 'mix'
        else f'{CACHE}/stems/{song}/{stem}.wav')

sr, hop = 22050, 256
y, _ = librosa.load(str(path), sr=sr, mono=True)
C = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop, bins_per_octave=36)
O = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
O = O[:C.shape[1]] / (O.max() + 1e-9)
F = np.vstack([C, 2 * O[None, :]])                 # rhythm weighted like two chroma bins
ONSETS = librosa.onset.onset_detect(onset_envelope=O, sr=sr, hop_length=hop, units='time')
fr = lambda t: int(round(t * sr / hop))
tm = lambda i: i * hop / sr


def scores(t0, t1):
    a = F[:, fr(t0):fr(t1)]
    a = (a - a.mean()) / np.linalg.norm(a - a.mean())
    w = a.shape[1]
    win = np.lib.stride_tricks.sliding_window_view(F, w, axis=1)          # (bins, frames, w)
    b = win - win.mean(axis=(0, 2), keepdims=True)
    n = np.linalg.norm(b, axis=(0, 2))
    return np.einsum('ij,ikj->k', a, b) / np.maximum(n, 1e-9)


variants = {}
for s in specs:
    name, rng = s.split('=')
    t0, t1 = map(float, rng.split(':'))
    pattern = []
    for t in ONSETS:                               # the example's onsets, doubled detections merged
        if t0 - 0.02 <= t < t1 and (not pattern or t - t0 - pattern[-1] > 0.07): pattern.append(t - t0)
    if nnotes and len(pattern) != int(nnotes):     # too few found (a dense mix): spread N over the first..last
        a, b = (pattern[0], pattern[-1]) if len(pattern) > 1 else (0.0, t1 - t0)
        pattern = list(np.linspace(a, b, int(nnotes)))
    variants[name] = (t0, t1, scores(t0, t1), pattern)

found = []
for name, (t0, t1, sc, pattern) in variants.items():
    gap = fr(0.6 * (t1 - t0))
    for i in np.argsort(-sc):
        if sc[i] < lo: break
        found.append((sc[i], tm(i), name))
found.sort(reverse=True)
keep = []
for s, t, name in found:                           # best variant per spot, no overlapping matches
    if all(abs(t - k[1]) > 0.6 * (variants[k[2]][1] - variants[k[2]][0]) for k in keep):
        keep.append((s, t, name))
out = []
for s, t, name in sorted(keep, key=lambda k: k[1]):
    notes = []
    for off in variants[name][3]:
        near = [o for o in ONSETS if abs(o - (t + off)) <= 0.06 and o not in notes]
        notes.append(min(near, key=lambda o: abs(o - t - off)) if near else t + off)
    notes = sorted(round(float(n), 3) for n in notes)
    out.append({'name': name, 't': round(t, 3), 'score': round(float(s), 3), 'notes': notes})
    print(f'{t:7.2f}s  {name:6} {s:.2f}  notes ' + ' '.join(f'{n:.2f}' for n in notes))
json.dump(out, open(song_dir(song) / 'motifs.json', 'w'), indent=1)
print(f'{len(out)} matches -> songs/{song}/motifs.json')
