"""Wizards in Winter (Trans-Siberian Orchestra) -> seq2026/tso_wizards/tso_wizards_winter.xsq
(rebuilt from scratch; the user's own tso_wizards.xsq has hand edits in xLights and is left alone)

Winter, conjured: the notes literally dance as snow. The song is a call and response (the band plays, stops dead
on a stab, a piano run answers); here the band's stab FREEZES the yard and the piano answers in SNOW.

THE SOUNDS, one look each, all song
- The 22 stop bars (the piano's answers): the stab freezes the yard - an icy ring across everything, the house and
  trunks flash ice, icicles drop from the top of every Vert. Then every piano note is a SNOWFLAKE that appears on
  the wall at the height of its pitch, spinning (two shapes alternating) and drifting down, hopping Vert to Vert
  across the wall with the run (left to right, then right to left the next time). The notes dance as snow.
- The theme melody (strings/synth): the 29 pixel sticks are a frozen xylophone - each note bounces the stick at
  its pitch (low notes left, high notes right) in an aurora colour, with a white tip. The spiral trees glow up to
  the height of the note.
- The lead melody (the middle sections): northern lights - the notes glide across the wall right to left like
  sheet music, each one coloured by its pitch, over an aurora sky.
- Kick: the arches pulse in the section's colours. Snare: white rings race up the trunks, one tree at a time (in
  the drum drive: ripples across the wall too). Bass: a white dot on the fence, positioned by pitch.

THE ORB (the wizard's orb: a white-hot sphere with a cyan-blue glow that moves through the whole yard)
It appears now and then and dances: it bounces in over the arches on the beat at the start and back again; spirals
up the wall in each build and bursts; circles the yard during the whirl; drifts slowly through the falling snow in
the piano breakdown; bounces off the snare in the drum drive; rockets up into the rainbow; splits into twin orbs
(cyan and magenta) that dance mirror-image in the finale; and in the silence before the last hit it hovers alone in
the middle, swelling, until the last hit blows it apart into snow.

THE SECTIONS
- Intro (bars 1-8): a winter night - stars over the wall, the orb bounces in over the arches.
- Themes 1-4: snow falling down the wall under stars; the frozen xylophone; frost barber poles on the trunks.
- Builds: the wall and trunks fill with colour from the ground while the orb spirals up.
- The band hits (bar 29): ice rings across the yard from alternating sides.
- The whirl (heavy riff, bars 32-35): a 3D aurora wheel over the whole yard with the orb circling it.
- Leads 1-2: the aurora - northern-lights sky on the wall, the lead melody gliding across it.
- Piano breakdown (bars 58-61): everything goes dark and it snows on the whole yard; a big snowflake crystallises
  on the middle of the wall, one arm per bar; the piano's notes are small flakes on the outer Verts; the orb drifts.
- Drum drive (62-65): bands of violet and cyan swap direction every bar; the orb bounces on the snare.
- Launch + rainbow (92-96): the orb rockets up and the whole yard becomes a spinning aurora wheel.
- Finale (97-110): aurora sky with snow, the xylophone, twin orbs.
- Ending: ice-crack rings on the hammer hits, then silence and the orb alone, then the last hit: the big snowflake
  flashes on the wall, snow sparkles over the yard and fades; the manger spot (ice blue) is the last light.

Colour: winter and aurora - ice blue, cyan, deep blue, white, with violet, magenta and aurora green; per-section
pairs. No amber, orange or gold. The spiral trees carry a -70 % dimming curve, so they only get bright colours.
Blending: every layer Normal (Max hides lower layers on this xLights); orb and pulses Additive. AllModels is the
LAST row so the orb draws over everything.

usage: ./run songs/tso_wizards/build.py [out.xsq] [timeline.json] [--force] [--no-images]
"""
import bisect, json, math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from seqlib import *

SONG, MP3 = 'tso_wizards', 'wis.mp3'
HERE = song_dir(SONG)
ARGS = cli_args()
OUT = ARGS[0] if ARGS else str(SHOW / 'seqs' / SONG / f'{SONG}_winter.xsq')   # beside the user's edited tso_wizards.xsq
IMG_DIR = SHOW / 'seqs' / SONG / 'Images'
IMG_REMOTE = f'{MEDIA_ROOT}/seq2026/{SONG}/Images'
ev = json.load(open(HERE / 'events.json'))
BEATS, PH, PER = ev['beats'], ev['phase'], ev['per']
M = 4
DUR, END = round(ev['dur'], 3), ev['end']
BAR = M * PER
random.seed(1225)


def bt(n, k=0.0):
    """time of beat k (fractional ok) of 1-based bar n"""
    i = PH + M * (n - 1) + k
    i0 = int(math.floor(i)); f = i - i0
    b = lambda j: BEATS[j] if j < len(BEATS) else BEATS[-1] + (j - len(BEATS) + 1) * PER
    return b(i0) + f * (b(i0 + 1) - b(i0))
B = lambda n: bt(n, 0)

# ---------------------------------------------------------------- the props
LX = layout_x()
STICKS = sorted((m for m in LX if m.startswith('pixstk')), key=LX.get)
ARCHS = sorted((m for m in LX if m.startswith('arch-big')), key=LX.get)
SPIRALS = sorted(['Spiral Tree 2', 'Spiral Tree 3', 'little spiral - left', 'little spiral - right'], key=LX.get)
TREES = sorted(TREES_LR, key=LX.get)
VERTS = VERTS_LR
CENTRE5 = ['Vert-7', 'Vert-1', 'Vert-8', 'Vert-2', 'Vert-9']
OUTER4 = ['Vert-3', 'Vert-4', 'Vert-5', 'Vert-6']
HOUSE_ALL = ['roofline-1', 'window-master', 'window-char', 'grinch-1']
ROWS = (['Verts'] + VERTS + ['trees'] + TREES + ['arches_big'] + ARCHS + ['pix-evens', 'pix-odds'] + STICKS
        + ['Spiral Trees'] + SPIRALS + ['fenceline', 'roofline-1', 'window-master', 'window-char', 'grinch-1',
                                         'Nativity Spot', 'AllModels'])            # AllModels last: the orb on top
# where each prop sits across the AllModels buffer (% of its width, from the layout centres)
_mx = [LX[m] for m in STICKS + ARCHS + SPIRALS + VERTS]
X_LO, X_HI = min(_mx) - 55, max(_mx) + 55
ALLX = lambda m: (LX[m] - X_LO) / (X_HI - X_LO) * 100
Y_ARCH, Y_MID, Y_TOP = 12, 50, 85


class NSeq(Seq):
    """every layer blends Normal (xLights' default); Max blanks the lower layers on this xLights."""
    def add(self, els, layer, name, start, end, settings, colors, *a, **k):
        settings = dict(settings)
        if settings.get('_blend', 'Max') == 'Max': settings['_blend'] = None
        return super().add(els, layer, name, start, end, settings, colors, *a, **k)

sq = NSeq(ROWS, nlayers=16)
# Verts group: 0 ripples / fills   1 snow / stars   2 bands, aurora   3-14 the lead's aurora scroll   15 sky
# single Verts: 0-1 snowflakes (alternating)   2 icicles   3 big snowflake parts
# AllModels: 0 moments   1 orb A   2 orb B   3 snow over the yard
# trees group: 0 fills / rises   1 frost poles     single trees: 0 snare rings
# arches group: 0 kick pulse (Additive)   1 runs     sticks: groups 0 waves; singles 0 the xylophone
# spirals group: 0 melody   1 background            fence: 0 bass dot   1 runs   2 base   house: 0 flash 1 breathe

# ---------------------------------------------------------------- colour: winter + aurora
ICE, CYAN, BLUE, NIGHT = '#40C8FF', '#00E5FF', '#1E50FF', '#0A1450'
VIOLET, MAGENTA, AURORA, TEAL = '#8A2BFF', '#FF00C8', '#00FF80', '#00FFC8'
AUR = ['#00FF80', '#00FFB4', '#00FFE0', '#00E5FF', '#00B4FF', '#0080FF', '#1E50FF', '#4B3CFF', '#8A2BFF', '#C800FF',
       '#FF00C8', '#FF3CF0']                    # 12 aurora colours, no red/orange/yellow
pc = lambda p: AUR[(p * 7) % 12]                # circle of fifths: neighbouring notes get different colours
PARTNER = {ICE: CYAN, CYAN: TEAL, BLUE: VIOLET, VIOLET: '#C800FF', MAGENTA: '#FF3CF0', AURORA: TEAL, TEAL: CYAN,
           NIGHT: BLUE, WHITE: ICE}
rich = lambda c, mode='up': Grad(c, PARTNER.get(c, c), mode=mode)
tip = lambda c: Grad((0, c), (0.72, c), (0.82, WHITE), (1, WHITE), mode='up')
ORB = Grad((0, WHITE), (0.28, WHITE), (0.45, CYAN), (0.75, BLUE), (1, BLACK), mode='radial-out')
ORB_M = Grad((0, WHITE), (0.28, WHITE), (0.45, MAGENTA), (0.75, VIOLET), (1, BLACK), mode='radial-out')

# ---------------------------------------------------------------- notes
def mono(stem, lo, hi, minv=40, gap=0.05):
    ns = [n for n in load_notes(HERE / 'midi' / f'{stem}_basic_pitch.csv') if n[3] >= minv and lo <= n[2] <= hi
          and n[0] < END]
    out, cl = [], []
    for n in ns:
        if cl and n[0] - cl[0][0] > gap: out.append(max(cl, key=lambda x: x[2])); cl = []
        cl.append(n)
    if cl: out.append(max(cl, key=lambda x: x[2]))
    return [(s, p, e - s) for s, e, p, v in out]
THEME = mono('other', 60, 90)
LEAD = mono('vocals', 55, 90)
PIANO = mono('piano', 36, 96)
KICKS, SNARES = ev['kick'], ev['snare']
BASS = [(t, midi(nm)) for t, e, nm in ev['bass']]

# ---------------------------------------------------------------- structure (bars of 1.617 s; checked by ear for the 2026-10 build)
STOPS = [4, 8, 12, 16, 17, 23, 27, 28, 30, 31, 44, 45, 51, 55, 56, 57, 78, 79, 85, 89, 90, 91]
SECTIONS = [  # name, first bar, end bar, kind, colours
    ('intro', 1, 9, 'night', (BLUE, CYAN)),
    ('theme1', 9, 18, 'theme', (ICE, VIOLET)),
    ('build1', 18, 20, 'build', (CYAN, VIOLET)),
    ('theme2', 20, 29, 'theme', (CYAN, MAGENTA)),
    ('hit', 29, 30, 'hit', (ICE, MAGENTA)),
    ('piano1', 30, 32, 'stops', (ICE, CYAN)),
    ('whirl', 32, 36, 'whirl', (AURORA, VIOLET)),
    ('lead1', 36, 44, 'lead', (AURORA, VIOLET)),
    ('stops2', 44, 46, 'stops', (ICE, CYAN)),
    ('build2', 46, 48, 'build', (AURORA, BLUE)),
    ('theme3', 48, 58, 'theme', (BLUE, MAGENTA)),
    ('snow', 58, 62, 'snow', (WHITE, ICE)),
    ('drive', 62, 66, 'drive', (VIOLET, CYAN)),
    ('lead2', 66, 78, 'lead', (MAGENTA, AURORA)),
    ('stops3', 78, 80, 'stops', (ICE, CYAN)),
    ('build3', 80, 82, 'build', (MAGENTA, CYAN)),
    ('theme4', 82, 92, 'theme', (ICE, MAGENTA)),
    ('launch', 92, 93, 'launch', (WHITE, CYAN)),
    ('rainbow', 93, 97, 'rainbow', (AURORA, MAGENTA)),
    ('finale', 97, 111, 'finale', (CYAN, MAGENTA)),
    ('ending', 111, None, 'ending', (WHITE, ICE)),
]
SPAN = {n: (B(a), B(b) if b else DUR) for n, a, b, *_ in SECTIONS}
SEC_START = [B(a) for _, a, *_ in SECTIONS]
section = lambda t: SECTIONS[max(bisect.bisect_right(SEC_START, t + 0.001) - 1, 0)]
bar_of = lambda t: int((t - B(1) + 0.001) // BAR) + 1
is_stop = lambda t: bar_of(t) in STOPS
HAMMER = sorted({q(t): t for t in KICKS + SNARES if 174.0 <= t < 179.0}.values())
LAST_HIT = next(t for t in KICKS if t > 181.0)
ENDING0 = HAMMER[0] - 0.05
STORY, ORB_TRACK = [], []
def story(label, a, b): STORY.append((label, a, b))
def band_on(t):
    return not is_stop(t) and section(t)[3] not in ('snow', 'whirl', 'rainbow', 'hit') and t < ENDING0

# ================================================================ pixel art (6x44 PNG pictures, one per Vert)
IMAGES = {}
def image(name, rows, colors):
    IMAGES[name] = (rows, colors)
    return f'{IMG_REMOTE}/{name}.png'

def write_images():
    from PIL import Image
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for name, (rows, colors) in IMAGES.items():
        im = Image.new('RGBA', (6, 44), (0, 0, 0, 0)); px = im.load()
        for y, row in enumerate(rows[:44]):
            for x, ch in enumerate(row):
                c = colors.get(ch)
                if c: px[x, y] = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        im.save(IMG_DIR / f'{name}.png')

def pad(bm, top):
    top = max(0, min(top, 44 - len(bm)))
    return ['......'] * top + list(bm) + ['......'] * (44 - top - len(bm))

def pic(el, layer, t0, t1, path, fadein=0.0, fadeout=0.0, minlen=25):
    st = {'E_CHECKBOX_Pictures_PixelOffsets': 0, 'E_CHECKBOX_Pictures_Shimmer': 0,
          'E_CHECKBOX_Pictures_TransparentBlack': 0, 'E_CHECKBOX_Pictures_WrapX': 0,
          'E_CHOICE_Pictures_Direction': 'none', 'E_CHOICE_Scaling': 'No Scaling', 'E_SLIDER_PicturesXC': 0,
          'E_SLIDER_PicturesYC': 0, 'E_SLIDER_Pictures_EndScale': 100, 'E_SLIDER_Pictures_StartScale': 100,
          'E_TEXTCTRL_Pictures_Filename': path, 'E_TEXTCTRL_Pictures_FrameRateAdj': '1.0',
          'E_TEXTCTRL_Pictures_Speed': '1.0', 'E_TEXTCTRL_Pictures_TransparentBlack': 0}
    if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
    if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
    sq.add(el, layer, 'Pictures', t0, t1, st, [WHITE], minlen=minlen)

FLAKE_A = ['i.ii.i', '.iWWi.', 'iWWWWi', '.iWWi.', 'i.ii.i']     # a six-armed flake
FLAKE_B = ['..ii..', '..WW..', 'iWWWWi', '..WW..', '..ii..']     # turned: the plus
FLAKE_COL = {'W': WHITE, 'i': ICE}
def flake_img(shape, top):
    return image(f'wiz_flake{shape}_{top:02d}', pad(FLAKE_A if shape == 'A' else FLAKE_B, top), FLAKE_COL)

def snowflake(el, t0, t1, top, layer=0, fall=0.14, spin=0.11):
    """a spinning snowflake on one Vert: appears at row `top` (from the top), turns between its two shapes every
    `spin` s and drifts down a row every `fall` s until t1"""
    t, k = t0, 0
    while t < t1 - 0.02:
        e = min(t + spin, t1)
        row = min(39, top + int((t - t0) / fall))
        pic(el, layer, t, e, flake_img('A' if k % 2 == 0 else 'B', row))
        t, k = e, k + 1

# the big snowflake across the five centre Verts (centre on Vert-8, row 22); built in parts so it can grow
def _big():
    P = {m: {} for m in CENTRE5}
    def blank(): return ['......'] * 44
    c = blank()                                     # Vert-8: the vertical arm, forks, the hexagon heart
    for i in range(3, 42): c[i] = '..WW..'
    for i in (6, 37): c[i] = '#.WW.#'
    for i in (7, 36): c[i] = '.#WW#.'
    for i in range(19, 26): c[i] = '#WWWW#' if i in (19, 25) else 'WWWWWW'
    P['Vert-8']['core'] = c
    h = blank()                                     # Vert-1 (and mirrored Vert-2): the horizontal arm
    for i in (21, 22, 23): h[i] = 'WWWWWW'
    h[19] = '..#...'; h[20] = '..#...'; h[24] = '..#...'; h[25] = '..#...'
    P['Vert-1']['arm'] = h
    d = blank()                                     # Vert-1: the two diagonal arms
    for i, s in zip(range(9, 14), ('W#....', '.W#...', '..W#..', '...W#.', '....WW')): d[i] = s
    for i, s in zip(range(31, 36), ('....WW', '...W#.', '..W#..', '.W#...', 'W#....')): d[i] = s
    P['Vert-1']['diag'] = d
    o = blank()                                     # Vert-7 (and mirrored Vert-9): arm tips and diagonal tips
    for i in (21, 22, 23): o[i] = 'WWWWWW'
    o[18] = '#.....'; o[19] = '.#....'; o[20] = '..#...'; o[24] = '..#...'; o[25] = '.#....'; o[26] = '#.....'
    for i, s in zip(range(3, 9), ('#.....', 'W#....', '.W#...', '..W#..', '...W#.', '....WW')): o[i] = s
    for i, s in zip(range(36, 42), ('....WW', '...W#.', '..W#..', '.W#...', 'W#....', '#.....')): o[i] = s
    P['Vert-7']['tips'] = o
    mirror = lambda rows: [r[::-1] for r in rows]
    P['Vert-2']['arm'] = mirror(h); P['Vert-2']['diag'] = mirror(d); P['Vert-9']['tips'] = mirror(o)
    return P
BIG = _big()
BIG_COL = {'W': WHITE, '#': ICE}
BIG_IMG = {(m, part): image(f'wiz_big_{m}_{part}', rows, BIG_COL) for m, parts in BIG.items() for part, rows in parts.items()}

def big_flake(t0, t1, parts=('core', 'arm', 'diag', 'tips'), fadein=0.4, fadeout=0.6, layer=3):
    for (m, part), path in BIG_IMG.items():
        if part in parts:
            L = layer + (1 if part == 'diag' else 0)
            pic(m, L, t0, t1, path, fadein, fadeout)

# ================================================================ helpers
def orb(path, t0, t1, grad=ORB, layer=1, rx=6.0, ry=22.0, step=0.05, bright=100, label=None):
    """the orb: path(f, t) -> (x %, y %[, size]) across the AllModels buffer, drawn every `step` s"""
    t = t0
    while t < t1 - 0.02:
        e = min(t + step, t1)
        p = path((t - t0) / max(t1 - t0, 1e-6), t)
        x, y = p[0], p[1]; s = p[2] if len(p) > 2 else 1.0
        sq.on('AllModels', layer, t, e, grad, bright, bright, blend='Additive', minlen=25,
              subbuf=sub(x - rx * s, y - ry * s, x + rx * s, y + ry * s))
        t = e
    if label: ORB_TRACK.append((label, t0, t1))

def hops(points, y0=Y_ARCH, h=26):
    """path through landing points [(t, x)]: an arc between each pair"""
    ts = [p[0] for p in points]
    def f(_, t):
        i = max(0, min(bisect.bisect_right(ts, t) - 1, len(points) - 2))
        (ta, xa), (tb, xb) = points[i], points[i + 1]
        u = min(max((t - ta) / max(tb - ta, 1e-6), 0), 1)
        return xa + (xb - xa) * u, y0 + h * 4 * u * (1 - u)
    return f

def ring(t, dur, cols, cx=50, cy=50, r_end=120, w_end=25, layer=0, el='Verts'):
    sq.shockwave(el, layer, t, t + dur, list(cols), cx=cx, cy=cy, r_end=r_end, w_end=w_end)

def tree_ring(k, t, dur=0.45, color=ICE, layer=0):
    sq.morph(TREES[k], layer, t, t + dur, [WHITE, color], *DIAG['up'], tail_start=10, tail_end=45)

def stars(s0, s1, bright=70):
    sq.twinkle('Verts', 1, s0, s1, [WHITE, ICE], count=12, steps=40, bright=bright, subbuf=sub(0, 62, 100, 100))

def night(s0, s1, c=NIGHT, bright=35):
    sq.on('Verts', 15, s0, s1, Grad(BLUE, c, mode='down'), bright, bright)

def snowfall(els, s0, s1, bright=70, count=4, speed=5, layer=1, falling='Falling', fadeout=0):
    """gentle snow: xLights' Snowflakes (single-pixel flakes), each model its own snowfall.
    falling='Falling & Accumulating' piles it up at the bottom."""
    st = {'B_CHOICE_BufferStyle': 'Per Model Default', 'E_CHOICE_Falling': falling, 'E_SLIDER_Snowflakes_Count': count,
          'E_SLIDER_Snowflakes_Speed': speed, 'E_SLIDER_Snowflakes_Type': 1, 'E_SLIDER_Snowflakes_WarmupFrames': 40}
    if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
    sq.add(els, layer, 'Snowflakes', s0, s1, st, [WHITE, ICE], bright)

# ================================================================ the band (everything but the stops, breakdown and moments)
kn = 0
for i, t in enumerate(KICKS):
    if not band_on(t): continue
    cols = section(t)[4]
    d = max(min(nxt(KICKS, i, 0.3), 0.3), 0.1)
    sq.on(ARCHES, 0, t, t + d, Grad(cols[kn % 2], cols[(kn + 1) % 2], mode='right'), 90, 0, blend='Additive')
    kn += 1

sn = 0
for i, t in enumerate(SNARES):
    if not band_on(t) and section(t)[3] != 'whirl': continue
    if i + 1 < len(SNARES) and SNARES[i + 1] - t < PER * 0.6: continue
    tree_ring(sn % len(TREES), t, 0.45, section(t)[4][sn % 2])
    if section(t)[3] == 'drive':
        ring(t, PER * 1.5, (WHITE, section(t)[4][sn % 2]), cx=VERT_X[pingpong(sn, 9)], cy=30 if sn % 2 else 70,
             r_end=40, w_end=18, layer=0)
    sn += 1

bt_ = [t for t, _ in BASS]
for i, (t, p) in enumerate(BASS):
    if not band_on(t): continue
    pos = 5 + (min(max(p, 28), 52) - 28) / 24 * 90
    sq.flash(FENCE, 0, t, max(nxt(bt_, i, 2 * PER), 0.1), Grad(WHITE, CYAN), bright=85,
             subbuf=sub(max(pos - 3, 0), 0, min(pos + 3, 100), 100), end_level=25)

# the theme: a frozen xylophone on the 29 sticks; the spiral trees glow to the note's height
LO_T, HI_T = 64, 88
for i, (t, p, d) in enumerate(THEME):
    if not band_on(t) or section(t)[3] not in ('theme', 'finale', 'night'): continue
    g = min(THEME[i + 1][0] - t, PER) if i + 1 < len(THEME) else min(d, PER)
    k = round((min(max(p, LO_T), HI_T) - LO_T) / (HI_T - LO_T) * (len(STICKS) - 1))
    sq.bounce(STICKS[k], 0, t, t + max(min(g * 1.6, 0.5), 0.2), [tip(pc(p))], height=100)
    h = 20 + (min(max(p, LO_T), HI_T) - LO_T) / (HI_T - LO_T) * 80
    sq.on(SPIRAL, 0, t, t + max(g, 0.1), tip(CYAN), 100, 60, subbuf=sub(0, 0, 100, h), perModel=True)

# the lead: northern lights gliding across the wall
lead_notes = [(t, p, min(d, PER), [WHITE, pc(p)], 95) for t, p, d in LEAD
              if section(t)[3] == 'lead' and not is_stop(t)]
placed = sq.melody_scroll('Verts', lead_notes, None, travel=BAR, lo=60, hi=80, layers=range(3, 15))
for i, (t, p, d) in enumerate(LEAD):
    if section(t)[3] != 'lead' or is_stop(t): continue
    h = 20 + (min(max(p, 60), 80) - 60) / 20 * 80
    sq.on(SPIRAL, 0, t, t + max(min(d, PER), 0.1), tip(pc(p) if pc(p) not in (BLUE, '#4B3CFF') else CYAN), 100, 60,
          subbuf=sub(0, 0, 100, h), perModel=True)

# ================================================================ section backgrounds
for name, a, b, kind, cols in SECTIONS:
    s0, s1 = B(a), (B(b) if b else DUR)
    c0, c1 = cols
    if kind in ('night', 'theme'):
        night(s0, s1)
    if kind in ('night', 'theme', 'finale'):
        stars(s0, s1)
        snowfall('Verts', s0, s1, bright=75, count=3 if kind == 'night' else 4, layer=2)
    if kind in ('theme',):              # a winter wind: slow swinging 3D spirals in the section's colours
        sq.spirals('Verts', 14, s0, s1, [c0, c1], count=2, thickness=45, movement=1.0, bright=38, three_d=True,
                   swing=True)
    if kind in ('lead', 'finale'):
        sq.butterfly('Verts', 15, s0, s1, [AURORA, TEAL, VIOLET, BLUE], style=1, chunks=1,
                     skip=2, speed=8, bright=38)
    if kind in ('night', 'theme', 'lead', 'finale', 'drive'):
        sq.spirals(TRUNKS, 1, s0, s1, [c0, c1], count=2, rotation=15, thickness=45,
                   movement=1.5 if kind != 'drive' else 3.0, bright=50, perModel=True)
        sq.on(FENCE, 2, s0, s1, rich(NIGHT, 'right'), 40, 40)
        for k in range(int(round((s1 - s0) / (2 * PER)))):
            t = s0 + k * 2 * PER
            c = cols[(k // 2) % 2]
            sq.on(HOUSE_ALL, 1, t, min(t + 2 * PER, s1), c, 20 if k % 2 == 0 else 75, 75 if k % 2 == 0 else 20)
        if kind != 'lead':
            sq.spirals(SPIRAL, 1, s0, s1, [WHITE, CYAN], count=2, rotation=25, thickness=35, movement=1.2, bright=55,
                       perModel=True)
        if kind in ('theme', 'finale'):
            for k in range(b - a):
                t = B(a + k)
                sq.wave(FOREST[k % 2], 0, t, t + 2 * PER, None, 35, waves=900, speed=10, kind='Sine', fill='None',
                        thickness=50, height=50, direction='Right to Left' if k % 2 == 0 else 'Left to Right',
                        colors=[WHITE, cols[k % 2]])
        sq.on(ARCHES, 1, s0, s1, rich(c0, 'right'), 22, 22)
    if kind == 'drive':                 # bands swap direction every bar
        for k in range(b - a):
            sq.bars('Verts', 2, B(a + k), B(a + k + 1), 'Left' if k % 2 else 'Right', [tip(cols[k % 2]), BLACK], 2, 1, 45)
    if kind == 'build':                 # the wall and trunks fill with colour from the ground
        sq.fill('Verts', 0, s0, s1, [Grad(c0, c1, WHITE, mode='up')], 0, 100)
        sq.fill(TRUNKS, 0, s0, s1, [Grad(c0, c1, mode='up')], 0, 100, per_model=True)
        sq.on(HOUSE_ALL, 1, s0, s1, Grad(c0, c1, mode='right'), 10, 100)
        sq.twinkle(FOREST, 0, s0, s1, [WHITE, c0, c1], count=20, steps=20, bright=60)
        story(f'{name}: the wall and trunks fill with colour from the ground; the orb spirals up', s0, s1)

# ================================================================ the stops: the stab freezes the yard, the piano answers in snow
P_LO, P_HI = 60, 90
for si, bar in enumerate(STOPS):
    a, b = B(bar), B(bar + 1)
    sq.cut(q(a - 0.03), q(b), [r for r in ROWS if r != 'AllModels'])
    stab = next((t for t in KICKS + SNARES if a - 0.08 <= t < a + 0.25), a)
    c = [ICE, CYAN, VIOLET, MAGENTA, AURORA][si % 5]
    sq.shockwave('AllModels', 0, stab, stab + 0.7, [WHITE, c], cx=[50, 20, 80][si % 3], cy=30, r_end=300, w_end=70)
    sq.on(HOUSE_ALL + ['Nativity Spot'], 0, stab, stab + 0.6, ICE, 100, 0)
    sq.fill(TRUNKS, 0, stab, stab + 0.6, [tip(ICE)], 100, 0, per_model=True)
    for m in VERTS:                     # icicles: they drop from the top of every Vert and melt through the bar
        L = random.choice((14, 18, 23, 27, 32, 36))
        sq.fill(m, 2, stab, stab + 0.18, [Grad(BLUE, ICE, WHITE, mode='up')], 0, L, direction='Down')
        sq.on(m, 2, stab + 0.18, b - 0.02, Grad(BLUE, ICE, WHITE, mode='up'), 85, 0,
              subbuf=sub(-0.01, 100 - L - 0.01, 99.99, 99.99))
    run = [n for n in PIANO if a + 0.2 * PER <= n[0] < b - 0.1 * PER]
    if not run: run = [(a + j * PER * 0.75, 72 + 3 * j, PER / 2) for j in range(1, 5)]
    rightward = si % 2 == 0
    n = len(run)
    pl, ph = min(p for _, p, _ in run), max(p for _, p, _ in run)
    for j, (t, p, d) in enumerate(run):
        k = round(j * 8 / max(n - 1, 1)) if n > 1 else 4
        k = k if rightward else 8 - k
        top = 18 if ph == pl else 6 + int((1 - (p - pl) / (ph - pl)) * 24)      # high notes high on the wall
        snowflake(VERTS[k], t, min(t + 1.0, b - 0.02), top, layer=j % 2)
    story(f'stop {bar}: the stab freezes the yard; {n} piano notes = snowflakes dancing {"->" if rightward else "<-"}',
          a, b)

# ================================================================ moments
h0, h1 = SPAN['hit']                    # the band hits: ice rings across the yard from alternating sides
hit = [t for t in KICKS if h0 - 0.05 <= t < h1 - 0.1]
def draw_hit(a, b):
    for j, t in enumerate(hit):
        sq.shockwave('AllModels', j % 3, t, min(t + 0.9, b), [WHITE, [ICE, MAGENTA, CYAN][j % 3]],
                     cx=[20, 80, 50][j % 3], cy=30, r_end=300, w_end=70)
sq.moment(h0, h1, draw_hit, ICE)
story('the band hits: ice rings across the yard from alternating sides', h0, h1)

w0, w1 = SPAN['whirl']                  # the heavy riff: an aurora wheel over the whole yard; the orb circles it
sq.moment(w0, w1, lambda a, b: sq.whirl('AllModels', 0, a, b, [AURORA, TEAL, CYAN, BLUE, VIOLET, MAGENTA], xc=0),
          VIOLET, 30, fade_from=80)
orb(lambda f, t: (50 + 36 * math.cos(2 * math.pi * 2 * f), 50 + 30 * math.sin(2 * math.pi * 2 * f)), w0, w1,
    label='whirl: circles the yard twice')
story('the whirl: an aurora wheel over the whole yard, the orb circling it', w0, w1)

s0, s1 = SPAN['snow']                   # the piano breakdown: snow on the whole yard, the big snowflake grows
def draw_snow(a, b):
    snowfall('AllModels', a, b, bright=70, count=3, speed=4, layer=3)
sq.moment(s0, s1, draw_snow, ICE, 10, fade_from=25)
snowfall('Verts', s0, s1 + 0.6, bright=80, count=6, speed=4, layer=1, falling='Falling & Accumulating', fadeout=0.6)
big_flake(B(58), s1 + 0.6, parts=('core',), fadein=0.8, fadeout=0.6)
big_flake(B(59), s1 + 0.6, parts=('arm',), fadein=0.6, fadeout=0.6)
big_flake(B(60), s1 + 0.6, parts=('diag',), fadein=0.6, fadeout=0.6)
big_flake(B(61), s1 + 0.6, parts=('tips',), fadein=0.5, fadeout=0.6)
for j, (t, p, d) in enumerate([n for n in PIANO if s0 <= n[0] < s1 - 0.1]):
    top = 4 + int((1 - (min(max(p, P_LO), P_HI) - P_LO) / (P_HI - P_LO)) * 28)
    snowflake(OUTER4[j % 4], t, min(t + 1.4, s1), top, layer=j // 4 % 2)
orb(lambda f, t: (8 + 84 * f, 55 + 18 * math.sin(2 * math.pi * 1.5 * f)), s0 + 0.3, s1 - 0.1, rx=5, ry=18,
    bright=80, label='breakdown: drifts through the snow')
story('piano breakdown: snow on the whole yard; a big snowflake crystallises, one arm per bar; the orb drifts', s0, s1)

r0, r1 = SPAN['rainbow']                # the finale kicks in: a spinning aurora over everything
sq.moment(r0, r1, lambda a, b: sq.pinwheel('AllModels', 0, a, b, AUR[::2], arms=6, speed=14, twist=90, size=100,
                                           thickness=60, style3d='3D', clockwise=True), MAGENTA, 40)
story('the finale kicks in: a spinning 3D aurora wheel over the whole yard', r0, r1)

# ================================================================ the orb's other dances
# intro: in from the left over the arches on the beat, then back from the right
ax = [ALLX(m) for m in ARCHS]
pts = [(bt(1, 0), -6)] + [(bt(1, 1 + j), ax[j]) for j in range(10)] + [(bt(1, 11), ax[9] + 6)]
orb(hops(pts), pts[0][0], B(4) - 0.05, label='intro: bounces in over the arches')
pts = [(bt(5, 0), 106)] + [(bt(5, 1 + j), ax[9 - j]) for j in range(10)] + [(bt(5, 11), ax[0] - 6)]
orb(hops(pts), pts[0][0], B(8) - 0.05, label='intro: and back')
story('intro: a winter night; the orb bounces in over the arches on the beat, and back', B(1), B(9))
# the builds: spiral up the wall and burst
for name in ('build1', 'build2', 'build3'):
    a, b = SPAN[name]
    orb(lambda f, t: (50 + 22 * math.sin(2 * math.pi * 2 * f) * (1 - f), 6 + 84 * f), a, b - 0.05,
        label=f'{name}: spirals up the wall')
    sq.shockwave('AllModels', 0, b, b + 1.0, [WHITE, CYAN], cx=50, cy=90, r_end=200, w_end=60)
# the drive: bounces off the snare across the arches and back
d0, d1 = SPAN['drive']
dsn = [t for t in SNARES if d0 <= t < d1 - 0.1]
dsn = [t for i, t in enumerate(dsn) if i == 0 or t - dsn[i - 1] > PER * 0.6]
xs = [ax[pingpong(j, 10)] for j in range(len(dsn))]
orb(hops(list(zip(dsn, xs)), h=34), dsn[0], dsn[-1], label='drive: bounces off the snare')
# the launch: rockets up and bursts into the aurora wheel
l0, l1 = SPAN['launch']
orb(lambda f, t: (50, 4 + 92 * f ** 1.6, 1 + 0.6 * f), l0, l1 - 0.03, label='launch: rockets up')
sq.fill('Verts', 0, l0, l1, [Grad(CYAN, MAGENTA, WHITE, mode='up')], 0, 100)
story('launch: the orb rockets up into the aurora', l0, l1)
# the finale: twin orbs, cyan and magenta, dance mirror-image (now and then)
for n0 in (97, 101, 105):
    a = B(n0)
    beats = [bt(n0, j) for j in range(9)]
    xs = [8, 22, 36, 48, 36, 22, 8, 22, 36]
    orb(hops(list(zip(beats, xs)), y0=20, h=40), beats[0], beats[-1], label=f'finale bar {n0}: twin orbs')
    orb(hops(list(zip(beats, [100 - x for x in xs])), y0=20, h=40), beats[0], beats[-1], grad=ORB_M, layer=2)
story('finale: aurora and snow; the xylophone; twin orbs dance mirror-image', SPAN['finale'][0], SPAN['finale'][1])

# ================================================================ the ending
sq.cut(q(ENDING0), q(DUR))
for j, t in enumerate(HAMMER):          # ice cracking on the hammer hits
    sq.shockwave('AllModels', j % 3, t, t + 0.8, [WHITE, [ICE, CYAN, MAGENTA][j % 3]], cx=20 if j % 2 == 0 else 80,
                 cy=30, r_end=300, w_end=70)
    sq.on([el for el in NON_MEMBERS if el != 'trees'], 0, t, t + 0.6, ICE, 100, 0)
    sq.fill(TRUNKS, 0, t, t + 0.6, [tip(ICE)], 100, 0, per_model=True)
story('ending: ice cracks on the hammer hits', HAMMER[0], HAMMER[-1] + 0.8)
quiet0 = HAMMER[-1] + 0.8                # the silence: the orb alone in the middle, swelling
orb(lambda f, t: (50, 50, 0.4 + 1.2 * f), quiet0, LAST_HIT - 0.02, bright=90, label='the silence: alone, swelling')
story('the silence: the orb alone in the middle, swelling', quiet0, LAST_HIT)
sq.shockwave('AllModels', 0, LAST_HIT, LAST_HIT + 1.6, [WHITE, CYAN, MAGENTA], cx=50, cy=50, r_end=400, w_end=120)
snowfall('AllModels', LAST_HIT + 0.2, DUR, bright=80, count=4, speed=4, layer=3, fadeout=1.5)
sq.twinkle('AllModels', 2, LAST_HIT, DUR, [WHITE, ICE], count=15, steps=30, bright=70)
big_flake(LAST_HIT, DUR, fadein=0.05, fadeout=min(2.5, DUR - LAST_HIT - 0.2))
sq.on([el for el in NON_MEMBERS if el not in ('trees', 'Nativity Spot')], 0, LAST_HIT, LAST_HIT + 2.5, WHITE, 100, 0)
sq.fill(TRUNKS, 0, LAST_HIT, LAST_HIT + 2.5, [tip(ICE)], 100, 0, per_model=True)
sq.on('Nativity Spot', 0, LAST_HIT, DUR, ICE, 100, 20)
story('the last hit: the orb bursts into snow, the big snowflake flashes, the manger spot is the last light', LAST_HIT,
      DUR)

# ================================================================ timing tracks + write
if '--no-images' not in sys.argv:
    write_images()
st = sorted(STORY, key=lambda x: x[1])
nbars = next(n for n in range(1, 2000) if B(n) > END)
ob = sorted(ORB_TRACK, key=lambda x: x[1])
sq.tracks = [
    ('Sections', marks([SPAN[n][0] for n, *_ in SECTIONS], [n for n, *_ in SECTIONS], end=DUR)),
    ('Story', [(lab, q(s), q(min(e, st[i + 1][1]) if i + 1 < len(st) else e)) for i, (lab, s, e) in enumerate(st)
               if q(min(e, st[i + 1][1]) if i + 1 < len(st) else e) > q(s)]),
    ('Orb', [(lab, q(s), q(e)) for lab, s, e in ob]),
    ('Stops (call & response)', [(f'stop {n}', q(B(n)), q(B(n + 1))) for n in STOPS]),
    ('Bars', marks([B(n) for n in range(1, nbars)], [str(n) for n in range(1, nbars)], end=END)),
    ('Beats', marks(BEATS, [str((i - PH) % M + 1) for i in range(len(BEATS))], end=END)),
    ('Kick', marks(KICKS, maxlen=PER / 2)), ('Snare', marks(SNARES, maxlen=PER / 2)),
    ('Theme', marks([t for t, p, d in THEME], maxlen=PER / 2)),
    ('Piano', marks([t for t, p, d in PIANO], maxlen=PER / 2)),
]
sq.write(OUT, dict(song='Wizards in Winter', artist='Trans-Siberian Orchestra', album='',
                   media=f'{MEDIA_ROOT}/seq2026/{SONG}/{MP3}',
                   comment='Generated from stem-separated audio analysis: winter that dances.'),
         DUR, timeline=ARGS[1] if len(ARGS) > 1 else None)
print(f'lead scroll: {placed} of {len(lead_notes)} notes placed; images: {len(IMAGES)}')
