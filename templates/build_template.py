"""<Song title> (<artist>) -> seqs/<song>/<song>.xsq

<The concept in a paragraph: the story the lights tell, the character, what each signature sound becomes, the
big moments. Write this FIRST - it is the design. Then make the code below do exactly what it says.>

Copy to tooling/songs/<song>/build.py. Run: ./run songs/<song>/build.py [out.xsq] [timeline.json] [--force]
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))    # tooling/ (parents[3] if the song key has a slash)
from seqlib import *

SONG = '<song>'                     # folder under seqs/ (may contain a slash: 'new/owl')
MP3 = '<file>.mp3'
HERE = song_dir(SONG)
ARGS = cli_args()
OUT = ARGS[0] if ARGS else str(SHOW / 'seqs' / SONG / f'{Path(SONG).name}.xsq')
ev = json.load(open(HERE / 'events.json'))
BEATS, PH, PER = ev['beats'], ev['phase'], ev['per']
M = ev.get('meter', 4)                  # beats per bar (3 for a waltz)
DUR, END = round(ev['dur'], 3), ev['end']
BAR = M * PER

def B(n):
    """start of 1-based bar n (the bars of summary.txt). Works for click (even) and --loose (uneven) beats."""
    i = PH + M * (n - 1)
    return BEATS[i] if i < len(BEATS) else BEATS[-1] + (i - len(BEATS) + 1) * PER

# ---------------------------------------------------------------- single props, left to right (for characters)
LX = layout_x()
# e.g. STICKS = sorted((m for m in LX if m.startswith('pixstk')), key=LX.get)
sq = Seq(ELEMENTS, nlayers=10)      # add single-model rows here if a character travels prop to prop

# ---------------------------------------------------------------- colour (decide per song; no amber unless asked)
A, B_, C = '#FF00C8', '#00E5FF', '#FFC832'

# ---------------------------------------------------------------- words and notes
WORDS = [(w['word'].strip(' ,.?!').lower(), w['start'], w['end'])
         for w in json.load(open(HERE / 'lyrics.json')) if w['start'] < END] if (HERE / 'lyrics.json').exists() else []
def word(prefix, after, before=1e9):
    """time of the first word starting with `prefix` at/after `after` - anchor every lyric moment with this"""
    return next(s for w, s, e in WORDS if w.startswith(prefix) and after <= s < before)
VOX = [n for n in load_notes(HERE / 'midi' / 'vocals_basic_pitch.csv') if n[3] >= 40 and n[0] < END]
def sung(t, back=0.5):
    """snap a Whisper word time to the sung note onset just before it (Whisper runs late)"""
    c = [n[0] for n in VOX if t - back <= n[0] <= t + 0.1]
    return min(c) if c else t
def mono(stem, lo, hi, minv=40, gap=0.06):
    """the top line of a stem: [(start, pitch, length)]"""
    ns = [n for n in load_notes(HERE / 'midi' / f'{stem}_basic_pitch.csv') if n[3] >= minv and lo <= n[2] <= hi
          and n[0] < END]
    out, cl = [], []
    for n in ns:
        if cl and n[0] - cl[0][0] > gap: out.append(max(cl, key=lambda x: x[2])); cl = []
        cl.append(n)
    if cl: out.append(max(cl, key=lambda x: x[2]))
    return [(s, p, e - s) for s, e, p, v in out]
MELODY = mono('vocals', 50, 84)
KICKS, SNARES = ev['kick'], ev['snare']
BASS = [(t, midi(nm)) for t, e, nm in ev['bass']]

# ---------------------------------------------------------------- structure: read summary.txt + lyrics.txt + analyze_key.py
SECTIONS = [('intro', 1, 9), ('verse1', 9, 17), ('chorus1', 17, 25), ('end', 25, None)]   # name, first bar, end bar
SPAN = {n: (B(a) if a > 1 else 0.0, B(b) if b else DUR) for n, a, b in SECTIONS}
section = lambda t: next((n for n, (a, b) in SPAN.items() if a <= t < b), SECTIONS[-1][0])
kind = lambda t: section(t).rstrip('0123456789')
STORY = []                          # (label, start, end): what the lights are saying - becomes a timing track

# ================================================================ the instrument map (constant through the song)
for i, t in enumerate(KICKS):
    if kind(t) in ('intro', 'end'): continue
    sq.flash(ARCHES, 0, t, min(max(nxt(KICKS, i, 0.3), 0.1), 0.3), Grad(A, WHITE, mode='right'))
for i, t in enumerate(SNARES):
    if kind(t) in ('intro', 'end'): continue
    sq.ripple(CANVAS, 3, t, PER * 1.5, [WHITE, B_], VERT_X[pingpong(i, len(VERT_X))], 30 if i % 2 else 70)
    if TRUNKS: sq.trunk_ring(t, 0.45, B_, tree=i % len(TREE_X))
bt = [t for t, _ in BASS]
for i, (t, p) in enumerate(BASS):
    pos = 5 + (min(max(p, 30), 54) - 30) / 24 * 90
    sq.flash(FENCE, 0, t, max(nxt(bt, i, 2 * PER), 0.075), Grad(WHITE, A), bright=70,
             subbuf=sub(max(pos - 5, 0), 0, min(pos + 5, 100), 100), end_level=30)
for i, (t, p, d) in enumerate(MELODY):
    g = min(MELODY[i + 1][0] - t, 2 * PER) if i + 1 < len(MELODY) else min(d, 2 * PER)
    h = 15 + (min(max(p, 55), 79) - 55) / 24 * 85
    sq.on(SPIRAL, 1, t, t + max(g, 0.075), Grad(B_, WHITE, mode='up'), 100, 50, subbuf=sub(0, 0, 100, h), perModel=True)

# ================================================================ backgrounds per section
for name, (s0, s1) in SPAN.items():
    if kind(s0) == 'chorus':
        sq.spirals(CANVAS, 4, s0, s1, [A, B_], count=2, thickness=50, movement=1.0, bright=30, three_d=True, swing=True)

# ================================================================ lyric moments (the part that makes it sing)
# t = word('shine', SPAN['chorus1'][0]); sq.shockwave(ALL, 1, t, t + 1.2, [WHITE, C], cx=50, cy=20, r_end=200)
# STORY.append(('shine: a ring across the yard', t, t + 1.2))

# ================================================================ whole-yard moments (a handful; they clear what's underneath)
# sq.moment(a, b, lambda a, b: sq.shockwave(ALL, 0, a, b, [WHITE, C], cx=50, cy=30, r_end=300, w_end=80), C)

# ================================================================ timing tracks + write
st = sorted(STORY, key=lambda x: x[1])
nbars = next(n for n in range(1, 2000) if B(n) > END)
sq.tracks = [
    ('Sections', marks([SPAN[n][0] for n, _, _ in SECTIONS], [n for n, _, _ in SECTIONS], end=DUR)),
    ('Story', [(lab, q(s), q(min(e, st[i + 1][1]) if i + 1 < len(st) else e)) for i, (lab, s, e) in enumerate(st)
               if q(min(e, st[i + 1][1]) if i + 1 < len(st) else e) > q(s)]),
    ('Lyrics', marks([s for w, s, e in WORDS], [w for w, s, e in WORDS], maxlen=1.2)),
    ('Bars', marks([B(n) for n in range(1, nbars)], [str(n) for n in range(1, nbars)], end=END)),
    ('Beats', marks(BEATS, [str((i - PH) % M + 1) for i in range(len(BEATS))], end=END)),
    ('Kick', marks(KICKS, maxlen=PER / 2)), ('Snare', marks(SNARES, maxlen=PER / 2)),
]
sq.write(OUT, dict(song='<title>', artist='<artist>', album='', media=media_path(SONG, MP3),
                   comment='Generated from stem-separated audio analysis.'),
         DUR, timeline=ARGS[1] if len(ARGS) > 1 else None)
