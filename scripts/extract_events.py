"""Turn a song's stems + note CSVs into events.json (beat grid, bars, drum hits, notes, phrases) and a
bar-by-bar summary for working out the song's structure.

usage: extract_events.py <song> [--bpm=104] [--end=282.4] [--melody=vocals] [--loose] [--meter=3] [--phase=2]
  <song>     folder name under seqs/ (run separate.sh <song> first)
  --bpm      tempo hint when the tracker picks half/double time
  --meter    beats per bar, when the detected one is wrong (it tells 3 from 4; 2/4 and 4/4 both come out as 4)
  --phase    which beat (0-based) the first bar starts on, when you've found the real downbeat by ear
  --end      last musical moment in seconds (default: where the mix falls below -40 dB for good)
  --melody   stem whose notes drive the melody/voice motif (vocals, guitar, piano, other)
  --loose    the band plays without a click: beats follow the drummer (beat tracker) and drum hits keep their
             real times instead of snapping to a fixed 16th grid

Writes tooling/songs/<song>/events.json and summary.txt.
"""
import hashlib, json, sys
import numpy as np, librosa
from seqlib import song_dir, load_notes, cli_args, TOOLING
import os

opts = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
LOOSE = '--loose' in sys.argv
SONG = cli_args()[0]
HERE = song_dir(SONG)
CACHE = os.environ.get('XLIGHTS_TOOLING_CACHE', os.path.expanduser('~/.cache/xlights-tooling'))
D = f'{CACHE}/stems/{SONG}'
MELODY = opts.get('melody', 'vocals')
sr, hop = 22050, 128

# the stems must come from the mp3 that is there now (separate.sh records which one)
stamp = os.path.join(D, 'source.txt')
if os.path.exists(stamp):
    digest, _, name = open(stamp).read().strip().partition('  ')
    mp3 = TOOLING.parent / 'seqs' / SONG / name
    if not mp3.exists() or hashlib.sha256(mp3.read_bytes()).hexdigest() != digest:
        sys.exit(f'the stems in {D} were made from a different {name or "mp3"} than the one in seqs/{SONG}/ now: '
                 f'run separate.sh {SONG} again')

st = {s: librosa.load(f'{D}/{s}.wav', sr=sr)[0] for s in ('drums', 'bass', 'guitar', 'piano', 'other', 'vocals')}
mix = sum(st.values()); dur = len(mix) / sr
rms_mix = librosa.feature.rms(y=mix, hop_length=sr // 4)[0]
loud = np.where(20 * np.log10(rms_mix + 1e-9) > -40)[0]
END = float(opts.get('end', (loud[-1] + 1) * 0.25 if len(loud) else dur))

# ---------------------------------------------------------------- fixed beat grid (songs recorded to a click)
dr = st['drums']
drums_present = np.sqrt((dr ** 2).mean()) > 1e-3
ref = sum(st[s] for s in ('drums', 'bass', 'guitar', 'piano', 'other'))
o = librosa.onset.onset_strength(y=ref, sr=sr, hop_length=hop)
t = librosa.times_like(o, sr=sr, hop_length=hop)
kw = dict(start_bpm=float(opts['bpm'])) if 'bpm' in opts else {}
tempo, _ = librosa.beat.beat_track(onset_envelope=o, sr=sr, hop_length=hop, **kw)
p0 = 60 / float(np.atleast_1d(tempo)[0])
best = None
for per in np.arange(p0 * 0.985, p0 * 1.015, 0.0002):
    for t0 in np.arange(0, per, 0.005):
        g = np.arange(t0, END, per); sc = np.interp(g, t, o).mean()
        if best is None or sc > best[0]: best = (sc, per, t0)
_, PER, T0 = best

Sd = librosa.feature.melspectrogram(y=dr, sr=sr, hop_length=hop, n_mels=64, fmax=11025)
mf = librosa.mel_frequencies(n_mels=64, fmax=11025)
def band(lo, hi):
    m = (mf >= lo) & (mf < hi)
    e = librosa.onset.onset_strength(S=librosa.power_to_db(Sd[m]), sr=sr, hop_length=hop)
    return e / (np.percentile(e, 99.5) + 1e-9)
K, Sn, Cy = band(30, 120), band(150, 1200), band(6000, 11025)
td = librosa.times_like(K, sr=sr, hop_length=hop)
def at(env, tt, w=0.03):
    m = (td >= tt - w) & (td <= tt + w); return float(env[m].max()) if m.any() else 0.0

# on-beat vs off-beat: the grid may have locked onto the "&"s; drums decide
if drums_present:
    on_ = np.mean([at(K, g) + at(Sn, g) for g in np.arange(T0, END, PER)])
    off_ = np.mean([at(K, g) + at(Sn, g) for g in np.arange(T0 + PER / 2, END, PER)])
    if off_ > on_: T0 += PER / 2
T0 = T0 % PER
# local drift check
drift = []
for w0 in range(0, int(END), 20):
    g = np.arange(T0, END, PER); g = g[(g >= w0) & (g < w0 + 20)]
    if len(g) < 16: continue                  # too few beats to judge (e.g. the tail of the song)
    offs = np.arange(-0.15, 0.151, 0.01)
    drift.append((w0, int(offs[int(np.argmax([np.interp(g + d, t, o).mean() for d in offs]))] * 1000)))
beats = T0 + PER * np.arange(int((END - T0) / PER) + 1)
if LOOSE:
    # follow the drummer: a tight beat tracker seeded with the fitted tempo, filled out to the whole song
    _, bt = librosa.beat.beat_track(onset_envelope=o, sr=sr, hop_length=hop, start_bpm=60 / PER, tightness=300,
                                    trim=False, units='time')
    bt = bt[bt < END]
    head = np.arange(bt[0] - PER, -1e-9, -PER)[::-1]
    tail = np.arange(bt[-1] + PER, END, PER)
    beats = np.r_[head, bt, tail]
    T0 = float(beats[0]); PER = float(np.median(np.diff(beats)))
    lt = 60 / np.diff(beats)
    print(f'loose beats: {len(beats)}, local tempo {np.percentile(lt, 5):.1f}-{np.percentile(lt, 95):.1f} BPM')
print(f'{SONG}: {dur:.1f}s, end {END:.1f}s, {60 / PER:.2f} BPM, first beat {T0:.3f}s')
print('grid drift (ms) per 20 s window:', ' '.join(f'{d:+d}' for _, d in drift))
if max(abs(d) for _, d in drift) > 60 and not LOOSE:
    print('WARNING: drift over 60 ms - the song may not be on a click; check the beat track by ear.')

# ---------------------------------------------------------------- meter and bar phase: harmonic change + kick
harm = st['bass'] + st['guitar'] + st['piano'] + st['other'] + st['vocals']
C = librosa.feature.chroma_cqt(y=harm, sr=sr, hop_length=512)
Cs = librosa.util.sync(C, librosa.time_to_frames(beats, sr=sr, hop_length=512), aggregate=np.median)
nov = np.r_[0, np.linalg.norm(np.diff(librosa.util.normalize(Cs, axis=0), axis=1), axis=0)][:len(beats)]
kb = np.array([at(K, b) for b in beats])
accent = nov + 0.5 * kb                         # chords change and the kick lands on the downbeat

def periodic_fit(x, m):
    """How much of the beat-to-beat accent pattern repeats every m beats (0..1)."""
    n = len(x) // m * m
    if n < 4 * m: return 0.0
    x = x[:n] - x[:n].mean(); bars = x.reshape(-1, m)
    return max(0.0, 1 - float(((bars - bars.mean(0)) ** 2).mean()) / max(float((x ** 2).mean()), 1e-12))
FIT = {m: round(periodic_fit(accent, m), 3) for m in (3, 4)}
# Songs with a steady beat measure 0.09-0.40 for their own meter and ~0 for the other. A drumless, rubato waltz
# can lean the right way at far lower values, or flip with the beat grid, so only a clear case decides.
hi, lo = (3, 4) if FIT[3] > FIT[4] else (4, 3)
CLEAR = FIT[hi] >= 0.05 and FIT[hi] >= 3 * FIT[lo]
if 'meter' in opts:
    METER = int(opts['meter'])
else:
    METER = hi if CLEAR else 4
print(f'meter: accents repeat every 3 beats {FIT[3]:.3f}, every 4 beats {FIT[4]:.3f} -> {METER} beats per bar'
      + (' (--meter)' if 'meter' in opts else ''))
if 'meter' not in opts and not CLEAR:
    print(f'WARNING: no clear meter (it leans {hi}, too weakly to trust; often the beat grid itself is off); '
          f'assuming 4. Count a bar by ear and pass --meter=3 for a waltz.')
if METER == 3 and 60 / PER > 150:
    print(f'note: 3 beats at {60 / PER:.0f} BPM may be 6/8 counted in eighths; then a bar here is half a real bar.')

score = [float(accent[p::METER].mean()) for p in range(METER)]
order = sorted(range(METER), key=lambda p: -score[p])
PHASE = int(opts['phase']) % METER if 'phase' in opts else order[0]
margin = (score[order[0]] - score[order[1]]) / max(score[order[0]], 1e-9)
print('downbeat phase scores', np.round(score, 3), '-> first downbeat at beat', PHASE,
      '(--phase)' if 'phase' in opts else f'(runner-up beat {order[1]}, {margin:.0%} behind)')
if 'phase' not in opts and margin < 0.15:
    print(f'WARNING: the downbeat is a guess: beat {order[1]} scores almost as well as beat {order[0]}. Listen for '
          f'where bar 1 really starts (the big hits and chord changes land there) and pass --phase if it is not '
          f'beat {PHASE}.')

# ---------------------------------------------------------------- hits on the 16th grid
grid = [(b + j * PER / 4, i, j) for i, b in enumerate(beats) for j in range(4)]
kick = [g for g, i, j in grid if at(K, g) >= 0.35] if drums_present else []
snare = [g for g, i, j in grid if at(Sn, g) >= 0.35] if drums_present else []
cym = [g for g, i, j in grid if at(Cy, g) >= 0.35] if drums_present else []
off = [g for g, i, j in grid if drums_present and j != 0 and max(at(K, g), at(Sn, g)) >= 0.55
       and max(at(K, g), at(Sn, g)) > max(at(K, beats[i]), at(Sn, beats[i]))]
if LOOSE and drums_present:
    # real hit times: peaks of each drum band, at least a 16th apart
    def peaks(env, th=0.35):
        w = max(1, int(PER / 4 * sr / hop * 0.8))
        pk = librosa.util.peak_pick(env, pre_max=w, post_max=w, pre_avg=w, post_avg=w, delta=0.05, wait=w)
        return [round(float(td[i]), 3) for i in pk if env[i] >= th and td[i] < END]
    kick, snare, cym = peaks(K), peaks(Sn), peaks(Cy)
    nearest = lambda x: float(np.min(np.abs(beats - x)))
    off = [x for x in sorted(set(kick) | set(snare)) if nearest(x) > PER / 6 and max(at(K, x), at(Sn, x)) >= 0.55]

# ---------------------------------------------------------------- notes and phrases
NN = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
nm = lambda p: f'{NN[p % 12]}{p // 12 - 1}'
def line(notes, pick, minv=40, gap=0.05, lo=0, hi=200):
    """monophonic line: cluster near-simultaneous onsets, keep the highest (melody) or lowest (bass)"""
    out, cl = [], []
    for n in notes:
        if n[3] < minv or not (lo <= n[2] <= hi): continue
        if cl and n[0] - cl[0][0] > gap: out.append(cl); cl = []
        cl.append(n)
    if cl: out.append(cl)
    return [(c[0][0], max(x[1] for x in c), nm(pick(c, key=lambda x: x[2])[2])) for c in out]
mel = line(load_notes(HERE / 'midi' / f'{MELODY}_basic_pitch.csv'), max, minv=35, lo=48, hi=84)
bass = line(load_notes(HERE / 'midi' / 'bass_basic_pitch.csv'), min, lo=24, hi=60)
phrases, cur = [], None
for s, e, n in mel:
    if cur and s - cur[1] < 0.6: cur[1] = max(cur[1], e); cur[2] += 1
    else:
        if cur: phrases.append(cur)
        cur = [s, e, 1]
if cur: phrases.append(cur)
phrases = [p for p in phrases if p[2] >= 2]

# how hard each hit was (0..1), for effects that scale with the drums
kick_v = [round(min(at(K, g), 1.0), 3) for g in kick]
snare_v = [round(min(at(Sn, g), 1.0), 3) for g in snare]
json.dump(dict(song=SONG, dur=dur, end=END, t0=T0, per=PER, phase=PHASE, meter=METER, phase_scores=score,
               meter_fit=FIT, loose=LOOSE, beats=beats.tolist(), kick=kick,
               snare=snare, cym=cym, off=off, kick_v=kick_v, snare_v=snare_v, vox=mel, melody_stem=MELODY, bass=bass, phrases=phrases),
          open(HERE / 'events.json', 'w'))

# ---------------------------------------------------------------- bar-by-bar summary
BAR = METER * PER; B1 = T0 + PHASE * PER
STARTS = list(beats[PHASE::METER]) if LOOSE else [B1 + n * BAR for n in range(int((END - B1) / BAR) + 1)]
def db(y, a, b):
    seg = y[int(max(a, 0) * sr):int(b * sr)]
    return 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-6) if len(seg) else -99
cnt = lambda lst, a, b: sum(1 for x in lst if a <= x < b)
lines = [f'{SONG}: {60 / PER:.2f} BPM, {METER} beats per bar, ' + (f'bars follow the beat tracker (events.json beats[{PHASE}::{METER}])' if LOOSE else
         f'bar n starts at {B1:.3f} + (n-1) * {BAR:.4f} s'),
         'bar   time | drums  bass   gtr piano other   vox | kick snare cym off | melody notes']
for n, a in enumerate(STARTS):
    b = STARTS[n + 1] if n + 1 < len(STARTS) else a + BAR
    e = [db(st[s], a, b) for s in ('drums', 'bass', 'guitar', 'piano', 'other', 'vocals')]
    notes = ' '.join(x[2] for x in mel if a <= x[0] < b)
    lines.append(f'{n + 1:3d} {a:6.1f} |' + ''.join(f'{x:6.0f}' for x in e) +
                 f' | {cnt(kick, a, b):4d} {cnt(snare, a, b):5d} {cnt(cym, a, b):3d} {cnt(off, a, b):3d} | {notes[:60]}')
(HERE / 'summary.txt').write_text('\n'.join(lines) + '\n')
print(f'kick {len(kick)}  snare {len(snare)}  cymbal {len(cym)}  off-beat {len(off)}  '
      f'{MELODY} notes {len(mel)}  bass notes {len(bass)}  phrases {len(phrases)}')
print(f'wrote {HERE / "events.json"} and summary.txt')
