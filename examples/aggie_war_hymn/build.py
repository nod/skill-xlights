"""Aggie War Hymn (the Fightin' Texas Aggie Band) -> seq2026/aggie_war_hymn/aggie_war_hymn.xsq

The recording is the band alone (no singing; 111 BPM, B-flat major, the last strain lifts to E-flat), so the words
are placed by the tune: every verse line is one 8-beat phrase. The crowd knows the words; the yard shows them.
Maroon and white all song, burnt orange only for t.u. (it always loses), gold only for the Aggie Ring.

STORY
- Fanfare (bars 1-4): Kyle Field lights up. The four spiral trees are the light towers: each fanfare note switches
  one on. On the B-flat chord the field fills maroon: arches from the outside in, the wall and trunks rise from the
  ground. Drums enter (bar 5): a white ring across the whole yard.
- "Hullabaloo, Caneck! Caneck!" x2 (bars 5-6): "Hullabaloo" runs a white streak across the arches (left, then
  right); each "Caneck!" bursts white from the middle of the wall outward, and the trunks fire up.
- Verse 1, "All hail" (bars 7-23) builds Aggieland on a living maroon wall:
    "All hail to dear old Texas A&M" - the ATM logo glows onto the five centre Verts (drawn from the logo file:
    the T's bar spans all five, A and M sit under it, white bevel lines).
    "Rally around Maroon and White" - maroon and white bands rally to the centre of the wall; two lights run the
    fence from both ends to the middle.
    "Good luck to dear old Texas Aggies" - the Aggie Ring: a gold ring opens from the middle of the wall.
    "They are the boys that show the real old fight" - ranks of maroon and white march across the wall.
    "That good old Aggie spirit thrills us" - the Spirit: white ghosts rise up the wall, spirals and trunks.
    "And makes us yell and yell and yell" - three white bursts, left, centre, right; the house yells with them.
    "So let's fight for dear old Texas A&M" - diagonal charges across the wall on every beat.
- Every verse ends the same way (the tag):
    "We're goin' to beat you all to" - the wall fills from the ground, white on top.
    "Chig-gar-roo-gar-rem! Chig-gar-roo-gar-rem!" - a white light hops a syllable at a time across the ten arches
    and across the wall.
    "Rough! Tough! Real stuff!" - the whole yard slams maroon, white, maroon-and-white.
    "Texas A&M!" - T-E-X-A-S A-&-M, one letter per Vert across all nine, white on maroon.
- Verse 2, "Good-bye" (bars 24-40) is the rivalry:
    "Good-bye to texas university" - burnt orange appears in the far-right corner (tree-4, the two right Verts)
    and waves good-bye.
    "So long to the orange and the white" - orange-and-white stripes cover the wall, then maroon sweeps them off
    to the right, and an orange light is pushed off the end of the fence.
    "Good luck..." / "...the real old fight" - the Aggie Ring and the marching ranks again.
    "The eyes of Texas are upon you" - the wall goes dark and orange eyes open on it, one pair per beat; the
    house windows glow orange too (the house is watching).
    "That is the song they sing so well (sounds like hell!)" - the eyes blink along, then flames roar up the wall
    and the trunks and burn the eyes away.
    "So good-bye to texas university" - embers float up; one last orange ember on tree-4 blinks out; maroon returns.
    Then the tag: fill, chig-gar-roo-gar-rem, Rough! Tough! Real stuff! TEXAS A&M.
- "Saw Varsity's horns off!" x3, SHORT! (bars 41-47): a burnt-orange longhorn spans the whole wall (head on the
  middle Vert, horns out to the end Verts). The whole yard SWAYS like the student section, a stroke every two
  beats (sticks, arches, fence, roof, trunks, spirals). A white saw cuts back and forth through the horns with
  sparks; at the end of each chant a piece falls off, tips first. SHORT! (the band's last stab, 1:40.2): the stubs
  snap off in a white flash, then the band's silence is black except SHORT in white across the centre Verts.
- "Varsity's horns are sawed off!" x3, SHORT! (bars 48-54): the yard keeps swaying; maroon sweeps the fallen
  pieces off the wall, left then right; then the hornless head drops away and the ATM logo takes its place.
  SHORT! again, the same way.
- Interlude (bars 55-66): the 12th Man. "12TH MAN" spells across the wall and the 29 pixel sticks stand up one by
  one, left to right, until the whole crowd is up. The Fightin' Texas Aggie Band forms the Block T on the wall
  (maroon dots march in along the top, the stem drops down the middle) while the arches do the band's four-way
  cross-through. Bars 65-66 build into the key change.
- Final strain in E-flat (bars 67-82): the lift - a wave up the whole yard and a ring. Strain 1: the ATM logo in
  the middle of the wall with maroon and white fireworks around it; the trunks become maroon-and-white barber
  poles, the spirals swirl. Strain 2: TEXAS A&M across all nine Verts, pulsing on the downbeats. The last chord:
  a white flash across the yard, then the ATM logo in white and maroon is what's left, with the manger spot as
  the last light.

THE BAND (constant, from bar 5): the 29 pixel sticks are the Corps marching - evens on one beat, odds on the next,
maroon with a white plume on top. Snare = white rings racing up the trunks, one tree at a time. Bass drum (the
strong beats) = the arches pulse maroon. Tubas = a white dot on the fence, positioned by pitch. Brass melody = how
high the spiral trees glow. The house breathes maroon and white.

Layer blending: this xLights (2026.19) shows only the top layer when a layer is set to Max, so every layer here
blends Normal (lit pixels cover, unlit show through) and flashes over a background use Additive.

usage: ./run songs/aggie_war_hymn/build.py [out.xsq] [timeline.json] [--force] [--no-images]
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seqlib import *
from art import FONT, LOGO, LOGO_VERTS, tall, rects, cell

SONG = 'aggie_war_hymn'
WAV = 'trimmed-hymn.wav'
HERE = song_dir(SONG)
ARGS = cli_args()
OUT = ARGS[0] if ARGS else str(SHOW / 'seqs' / SONG / f'{SONG}.xsq')
IMG_DIR = SHOW / 'seqs' / SONG / 'Images'
IMG_REMOTE = f'{MEDIA_ROOT}/seq2026/{SONG}/Images'
ev = json.load(open(HERE / 'events.json'))
BEATS, PH, PER = ev['beats'], ev['phase'], ev['per']
M = ev.get('meter', 4)
DUR, END = round(ev['dur'], 3), min(ev['end'], ev['dur'])


def bt(n, k=0.0):
    """time of beat k (0-based, fractional ok, may run past the bar) of 1-based bar n"""
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
VERTS = VERTS_LR                       # 3, 4, 7, 1, 8, 2, 9, 5, 6 (left to right from the street)
CENTRE5 = ['Vert-7', 'Vert-1', 'Vert-8', 'Vert-2', 'Vert-9']
HOUSE_ALL = ['roofline-1', 'window-master', 'window-char', 'grinch-1']
ROWS = (['AllModels', 'Verts'] + VERTS + ['trees'] + TREES + ['arches_big'] + ARCHS + ['pix-evens', 'pix-odds'] + STICKS
        + ['Spiral Trees'] + SPIRALS + ['fenceline', 'roofline-1', 'window-master', 'window-char', 'grinch-1',
                                         'Nativity Spot'])
assert set(ROWS) >= set(ELEMENTS), set(ELEMENTS) - set(ROWS)


class NSeq(Seq):
    """every layer blends Normal (xLights' default): lit pixels cover, unlit pixels show the layers below.
    (Max, seqlib's default, blanks the lower layers on this xLights.) blend='Additive' adds light instead."""
    def add(self, els, layer, name, start, end, settings, colors, *a, **k):
        settings = dict(settings)
        if settings.get('_blend', 'Max') == 'Max': settings['_blend'] = None
        return super().add(els, layer, name, start, end, settings, colors, *a, **k)

sq = NSeq(ROWS, nlayers=8)
# Verts group:   0 bursts / sweeps / ghosts   1 rings, hops   2 fire, ranks, fireworks   3 fills   5 background
# single Verts:  0 pictures (logo, letters, horns)   1 saw, eyes   2 sparks, falling pieces
# trees group:   0 rises / fire   1 barber poles      single trees: 0 snare rings
# arches group:  0 kick pulse (Additive)   1 sway / background      single arches: 0 chases
# sticks groups: 0 march   1 sway                      single sticks: 0 the standing crowd
# spirals group: 0 melody  1 swirl / background        single spirals: 0 the light towers
# fence:         0 tuba dot   1 runs   2 background     house: 0 flashes  1 breathing

# ---------------------------------------------------------------- colour (no amber; gold only for the Ring)
MAROON, CRIMSON, DEEP = '#A0001C', '#D2002A', '#5A000E'
GOLD, ORANGE, BLACK = '#FFC832', '#E85A00', '#000000'
SPIRAL_RED = '#FF0028'      # the spiral trees carry a -70 % dimming curve: maroon vanishes there, red reads
TU_WHITE = '#FFFFFF'
maroon_g = lambda mode='up': Grad(MAROON, CRIMSON, mode=mode)            # a maroon that moves, not a flat one
plume = Grad((0, MAROON), (0.72, MAROON), (0.8, WHITE), (1, WHITE), mode='up')   # maroon with a white tip
tip = lambda c=MAROON: Grad((0, c), (0.8, c), (0.88, WHITE), (1, WHITE), mode='up')

# ---------------------------------------------------------------- notes and hits
def mono(stem, lo, hi, minv=40, gap=0.06):
    ns = [n for n in load_notes(HERE / 'midi' / f'{stem}_basic_pitch.csv') if n[3] >= minv and lo <= n[2] <= hi
          and n[0] < END]
    out, cl = [], []
    for n in ns:
        if cl and n[0] - cl[0][0] > gap: out.append(max(cl, key=lambda x: x[2])); cl = []
        cl.append(n)
    if cl: out.append(max(cl, key=lambda x: x[2]))
    return [(s, p, e - s) for s, e, p, v in out]
MELODY = mono('other', 58, 84, minv=45)
KICKS, SNARES = ev['kick'], ev['snare']
BASS = [(t, midi(nm)) for t, e, nm in ev['bass']]

# ---------------------------------------------------------------- structure (bars of summary.txt)
SECTIONS = [('fanfare', 1, 5), ('hullabaloo', 5, 7), ('verse1', 7, 24), ('verse2', 24, 41), ('saw1', 41, 48),
            ('saw2', 48, 55), ('interlude', 55, 67), ('final1', 67, 75), ('final2', 75, None)]
SPAN = {n: (B(a) if a > 1 else 0.0, B(b) if b else DUR) for n, a, b in SECTIONS}
section = lambda t: next((n for n, (a, b) in SPAN.items() if a <= t < b), SECTIONS[-1][0])
SHORT_STAB = {1: B(47), 2: B(54)}                   # the band's last stab before each silence
SILENCE = {1: (B(47) + 0.42, B(48)), 2: (B(54) + 0.42, B(55))}
LAST_CHORD = B(82)
STORY, WORDS = [], []

def story(label, a, b): STORY.append((label, a, b))

# the words, placed by the tune (one 8-beat phrase per line)
VERSE1 = ['All hail to dear old Texas A&M', 'Rally around Maroon and White', 'Good luck to dear old Texas Aggies',
          'They are the boys that show the real old fight', 'That good old Aggie spirit thrills us',
          'And makes us yell and yell and yell', "So let's fight for dear old Texas A&M"]
VERSE2 = ['Good-bye to texas university', 'So long to the orange and the white', 'Good luck to dear old Texas Aggies',
          'They are the boys that show the real old fight', 'The eyes of Texas are upon you',
          'That is the song they sing so well (sounds like hell!)', 'So good-bye to texas university']
TAG = ["We're goin' to beat you all to", 'Chig-gar-roo-gar-rem! Chig-gar-roo-gar-rem!',
       'Rough! Tough! Real stuff! Texas A&M!']

# ================================================================ pixel art -> pictures (one PNG per Vert)
IMAGES = {}
def image(name, rows, colors):
    """a 6x44 PNG from a bitmap (top row first); `colors` maps characters to colours ('.' transparent unless
    '.' is given). Returns the path xLights reads it from."""
    IMAGES[name] = (rows, colors)
    return f'{IMG_REMOTE}/{name}.png'

def write_images():
    from PIL import Image
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    for name, (rows, colors) in IMAGES.items():
        im = Image.new('RGBA', (6, 44), (0, 0, 0, 0)); px = im.load()
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                c = colors.get(ch)
                if c: px[x, y] = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
        im.save(IMG_DIR / f'{name}.png')

def pad(bm, top):
    """a bitmap placed with its first row at row-index `top` (from the top) on a 44-row panel"""
    return ['......'] * top + list(bm) + ['......'] * (44 - top - len(bm))

def pic(el, layer, t0, t1, path, fadein=0.0, fadeout=0.0):
    st = {'E_CHECKBOX_Pictures_PixelOffsets': 0, 'E_CHECKBOX_Pictures_Shimmer': 0,
          'E_CHECKBOX_Pictures_TransparentBlack': 0, 'E_CHECKBOX_Pictures_WrapX': 0,
          'E_CHOICE_Pictures_Direction': 'none', 'E_CHOICE_Scaling': 'No Scaling', 'E_SLIDER_PicturesXC': 0,
          'E_SLIDER_PicturesYC': 0, 'E_SLIDER_Pictures_EndScale': 100, 'E_SLIDER_Pictures_StartScale': 100,
          'E_TEXTCTRL_Pictures_Filename': path, 'E_TEXTCTRL_Pictures_FrameRateAdj': '1.0',
          'E_TEXTCTRL_Pictures_Speed': '1.0', 'E_TEXTCTRL_Pictures_TransparentBlack': 0}
    if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
    if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
    sq.add(el, layer, 'Pictures', t0, t1, st, [WHITE])

GLYPH_TOP = 15
def glyph_img(ch, color=WHITE, tag='w'):
    name = {'&': 'amp', '!': 'bang', ' ': 'space'}.get(ch, ch)
    return image(f'awh_{name}_{tag}', pad(tall(FONT[ch]), GLYPH_TOP), {'#': color})

def spell(text, t0, t1, verts=VERTS, color=WHITE, stagger=0.0, fadein=0.08, fadeout=0.5, layer=0):
    """one letter per Vert, left to right (spaces skipped); `stagger` s between letters appearing"""
    for k, ch in enumerate(text):
        if ch == ' ': continue
        pic(verts[k], layer, t0 + k * stagger, t1, glyph_img(ch, color), fadein, fadeout)

LOGO_IMG = {m: image(f'awh_logo_{m}', LOGO[k], {'#': MAROON, 'w': WHITE, '.': BLACK})
            for k, m in enumerate(LOGO_VERTS)}
LOGO_IMG_W = {m: image(f'awh_logow_{m}', LOGO[k], {'#': WHITE, 'w': MAROON, '.': BLACK})
              for k, m in enumerate(LOGO_VERTS)}

def logo(t0, t1, fadein=0.6, fadeout=0.6, white=False, layer=0):
    for m in LOGO_VERTS:
        pic(m, layer, t0, t1, (LOGO_IMG_W if white else LOGO_IMG)[m], fadein, fadeout)

# the longhorn: head on Vert-8, horns out to the end Verts, tips curling up (row-index from the top)
def _longhorn():
    p = {m: ['......'] * 44 for m in VERTS}
    def put(m, i, s): p[m][i] = s
    for i, s in enumerate(['######', '######', '.####.', '.####.', '.####.', '..##..', '..##..', '..##..',
                           '.####.', '.#..#.']):
        put('Vert-8', 13 + i, s)
    for m in ('Vert-1', 'Vert-2'):
        for i in (12, 13, 14, 15): put(m, i, '######')
    for m in ('Vert-7', 'Vert-9'):
        for i in (12, 13, 14, 15): put(m, i, '######')
    for m in ('Vert-4', 'Vert-5'):
        for i in (11, 12, 13, 14): put(m, i, '######')
    tipl = [(4, '##....'), (5, '##....'), (6, '###...'), (7, '###...'), (8, '.###..'), (9, '.####.'),
            (10, '..####'), (11, '...###'), (12, '....##'), (13, '....##')]
    for i, s in tipl:
        put('Vert-3', i, s); put('Vert-6', i, s[::-1])
    return p
HORN = _longhorn()
HORN_IMG = {m: image(f'awh_horn_{m}', HORN[m], {'#': ORANGE}) for m in VERTS}
HORN_ROW = {m: next(i for i, r in enumerate(HORN[m]) if '#' in r) for m in VERTS}   # topmost horn row

# ================================================================ helpers
def vglow(k, y, t, dur, c, layer=1, h=5, a=100, b=0):
    """a soft spark on Vert k (left-to-right index) at height y % of the Verts canvas"""
    vx = VERT_X[k]
    sq.on('Verts', layer, t, t + dur, Grad(WHITE, c, mode='radial-out'), a, b,
          subbuf=sub(max(vx - 6, -0.01), max(y - h, 0), min(vx + 6, 99.99), min(y + h, 100)))

def ring(t, dur, cols, cx=50, cy=50, r_end=120, w_end=25, layer=1, el='Verts'):
    sq.shockwave(el, layer, t, t + dur, list(cols), cx=cx, cy=cy, r_end=r_end, w_end=w_end)

def burst(t, dur=0.9, cols=(WHITE, MAROON), layer=0):
    """white bursting from the middle of the wall outward (H-expand bar)"""
    sq.bars('Verts', layer, t, t + dur, 'H-expand', list(cols), count=1, cycles=1)

def tree_ring(k, t, dur=0.45, color=MAROON, layer=0, down=False):
    sq.morph(TREES[k], layer, t, t + dur, [WHITE, color], *DIAG['down' if down else 'up'], tail_start=10, tail_end=45)

def arch_run(k, t, dur, rightward=True, color=MAROON, layer=0):
    a, b = (0, 0, 0, 100), (100, 0, 100, 100)
    sq.morph(ARCHS[k], layer, t, t + dur, [WHITE, color], *((a, b) if rightward else (b, a)), tail_start=5, tail_end=45)

def sweep(el, t, dur, rightward, cols=(WHITE, MAROON), layer=1, tail=35):
    a, b = (0, 0, 0, 100), (100, 0, 100, 100)
    sq.morph(el, layer, t, t + dur, list(cols), *((a, b) if rightward else (b, a)), tail_start=3, tail_end=tail)

def house_flash(t, dur=0.5, color=WHITE, a=100):
    sq.on(HOUSE_ALL, 0, t, t + dur, color, a, 0)

def breathe(s0, s1, cols_, lo=35, hi=90, els=HOUSE_ALL, layer=1, period=None):
    period = period or M * PER
    k, t = 0, s0
    while t < s1 - 0.05:
        e = min(t + period, s1)
        sq.on(els, layer, t, e, cols_[(k // 2) % len(cols_)], lo if k % 2 == 0 else hi, hi if k % 2 == 0 else lo)
        t, k = e, k + 1

def slam(t, dur, color, label):
    """a whole-yard slam (Rough! Tough!)"""
    sq.moment(t, t + dur, lambda a, b: sq.on(ALL, 0, a, b, color, 100, 25), color, fade_to=20)
    story(label, t, t + dur)

def wall_bg(s0, s1, bright=40, layer=5):
    """the living maroon wall"""
    sq.butterfly('Verts', layer, s0, s1, [MAROON, DEEP, CRIMSON], style=1, chunks=1, skip=2, speed=6, bright=bright)

def fire(els, t0, t1, height=60, layer=2, per_model=False):
    st = {'E_CHECKBOX_Fire_GrowWithMusic': 0, 'E_CHOICE_Fire_Location': 'Bottom', 'E_SLIDER_Fire_Height': height,
          'E_SLIDER_Fire_HueShift': 97, 'E_TEXTCTRL_Fire_GrowthCycles': '0.0'}
    if per_model: st['B_CHOICE_BufferStyle'] = 'Per Model Default'
    sq.add(els, layer, 'Fire', t0, t1, st, [WHITE])

def fireworks(els, t0, t1, cols, layer=2, count=40, explosions=40):
    st = {'E_CHECKBOX_FIRETIMING': 0, 'E_CHECKBOX_Fireworks_Gravity': 1, 'E_CHECKBOX_Fireworks_HoldColour': 1,
          'E_CHECKBOX_Fireworks_UseMusic': 0, 'E_SLIDER_Fireworks_Count': count,
          'E_SLIDER_Fireworks_Explosions': explosions, 'E_SLIDER_Fireworks_Fade': 49, 'E_SLIDER_Fireworks_Velocity': 5,
          'E_SLIDER_Fireworks_XLocation': -1, 'E_SLIDER_Fireworks_XVelocity': 0, 'E_SLIDER_Fireworks_YLocation': -1,
          'E_SLIDER_Fireworks_YVelocity': 0, 'E_TEXTCTRL_Fireworks_XLocation': -1,
          'E_TEXTCTRL_Fireworks_XVelocity': 0, 'E_TEXTCTRL_Fireworks_YLocation': -1,
          'E_TEXTCTRL_Fireworks_YVelocity': 0}
    sq.add(els, layer, 'Fireworks', t0, t1, st, list(cols))

# ================================================================ the band (constant from bar 5)
BAND_FROM = B(5)
def band_on(t):
    if t < BAND_FROM or t >= LAST_CHORD: return False
    return not any(a - 0.05 <= t < b for a, b in SILENCE.values())

# the Corps marching: evens on one beat, odds on the next, maroon with a white plume
for i in range(PH, len(BEATS)):
    t = BEATS[i]
    if not band_on(t) or SPAN['interlude'][0] <= t < SPAN['interlude'][1] - 2 * M * PER: continue
    down = (i - PH) % M == 0
    sq.bounce(FOREST[(i - PH) % 2], 0, t, t + min(PER * 0.95, 0.5), [plume], height=100 if down else 78)

# snare: white rings racing up the trunks, one tree at a time
sn = 0
for i, t in enumerate(SNARES):
    if not band_on(t): continue
    if i + 1 < len(SNARES) and SNARES[i + 1] - t < PER * 0.6: continue
    tree_ring(sn % len(TREES), t, 0.45, MAROON if sn % 2 else CRIMSON)
    sn += 1

# bass drum on the strong beats: the arches pulse maroon (Additive: it lifts whatever the arches are doing)
strong = [BEATS[i] for i in range(PH, len(BEATS), 2)]
for i, t in enumerate(KICKS):
    if not band_on(t): continue
    if not any(abs(t - s) < 0.09 for s in strong): continue
    sq.on(ARCHES, 0, t, t + 0.35, maroon_g('right'), 85, 0, blend='Additive')

# tubas: a white dot on the fence, positioned by pitch, over a maroon fence
bt_ = [t for t, _ in BASS]
for i, (t, p) in enumerate(BASS):
    if not band_on(t): continue
    pos = 5 + (min(max(p, 34), 58) - 34) / 24 * 90
    sq.flash(FENCE, 0, t, max(nxt(bt_, i, 2 * PER), 0.1), WHITE, bright=90,
             subbuf=sub(max(pos - 3, 0), 0, min(pos + 3, 100), 100), end_level=25)
sq.on(FENCE, 2, BAND_FROM, LAST_CHORD, maroon_g('right'), 38, 38)

# brass melody: how high the spiral trees glow
for i, (t, p, d) in enumerate(MELODY):
    if not band_on(t): continue
    g = min(MELODY[i + 1][0] - t, 2 * PER) if i + 1 < len(MELODY) else min(d, 2 * PER)
    h = 20 + (min(max(p, 60), 80) - 60) / 20 * 80
    sq.on(SPIRAL, 0, t, t + max(g, 0.1), tip(SPIRAL_RED), 100, 55, subbuf=sub(0, 0, 100, h), perModel=True)

# the house breathes maroon and white
breathe(BAND_FROM, LAST_CHORD, [MAROON, MAROON, WHITE], lo=30, hi=85)

# a dim maroon base under the arches and trunks through the verses and the interlude, so they never sit black
for a, b in ((B(7), B(21)), (B(24), B(38)), (B(55), B(65))):
    sq.on(ARCHES, 2, a, b, maroon_g('right'), 28, 28)
    sq.spirals(TRUNKS, 1, a, b, [MAROON, DEEP], count=2, rotation=15, thickness=50, movement=0.6, bright=40,
               perModel=True)

# ================================================================ fanfare: Kyle Field lights up (bars 1-4)
for k, sp in enumerate(SPIRALS):           # the light towers switch on, one every two beats of the fanfare
    t = bt(1, 2 * k)
    sq.on(sp, 0, t, t + 0.3, WHITE, 100, 85)
    sq.on(sp, 0, t + 0.3, B(5), WHITE, 85, 100)
story('fanfare: the light towers (spiral trees) switch on, one per note', B(1), B(3))
for j in range(5):                         # the field fills maroon: arches from the outside in
    t = bt(3, j * 1.5)
    for k in (j, 9 - j):
        sq.on(ARCHS[k], 0, t, B(5), maroon_g('up'), 60, 80)
sq.fill('Verts', 3, B(3), B(5), [maroon_g('up')], 0, 35)
sq.fill(TRUNKS, 0, B(3), B(5), [maroon_g('up')], 0, 60, per_model=True)
sq.on(HOUSE_ALL, 1, B(3), B(5), MAROON, 0, 70)
sq.on(FENCE, 1, B(3), B(5), maroon_g('right'), 0, 40)
story('B-flat chord: the field fills maroon from the outside in', B(3), B(5))
sq.moment(B(5), B(5) + 1.2, lambda a, b: sq.shockwave(ALL, 0, a, b, [WHITE, MAROON], cx=50, cy=20, r_end=260,
                                                       w_end=70), WHITE, fade_to=0)
story('drums in: a white ring across the whole yard', B(5), B(5) + 1.2)

# ================================================================ Hullabaloo, Caneck! Caneck! (bars 5-6)
for n, right in ((5, True), (6, False)):
    a = bt(n, 0) if n == 6 else bt(n, 0) + 0.3
    sweep(ARCHES, a, bt(n, 2) - a, right, (WHITE, CRIMSON), layer=1, tail=50)
    for kk, (beat, cx) in enumerate(((2, 50), (3, 50))):
        t = bt(n, beat)
        burst(t, 0.8, (WHITE, CRIMSON) if kk == 0 else (WHITE, MAROON))
        sq.fill(TRUNKS, 0, t, t + 0.6, [tip(CRIMSON)], 100, 0, per_model=True)
    story(f'Hullabaloo (streak {"->" if right else "<-"} the arches), Caneck! Caneck! (two bursts)', B(n), B(n + 1))
wall_bg(B(5) + 1.2, B(7), bright=30)

# ================================================================ the verses
def verse_lines(v0, lines):
    for j, line in enumerate(lines):
        WORDS.append((line, B(v0 + 2 * j), B(v0 + 2 * j + 2)))
    for j, line in enumerate(TAG):
        WORDS.append((line, B(v0 + 14 + j), B(v0 + 15 + j)))

def aggie_ring(n):
    """'Good luck to dear old Texas Aggies': the Aggie Ring opens in gold from the middle of the wall"""
    t = B(n)
    ring(t, 2.2, (GOLD, WHITE), cx=50, cy=50, r_end=160, w_end=18, layer=1)
    ring(t + 1.0, 2.0, (GOLD, WHITE), cx=50, cy=50, r_end=160, w_end=12, layer=0)
    sq.twinkle(SPIRAL, 1, t, B(n + 2), [GOLD, WHITE], count=20, steps=40, bright=70)
    story('Good luck to dear old Texas Aggies: the gold Aggie Ring', t, B(n + 2))

def ranks(n):
    """'...the real old fight': ranks of maroon and white march across the wall"""
    sq.bars('Verts', 2, B(n), B(n + 2), 'Right', [MAROON, WHITE, MAROON, DEEP], count=2, cycles=2)
    for i in range(8):
        sq.on(STICKS[::2] if i % 2 else STICKS[1::2], 0, bt(n, i), bt(n, i) + 0.3, WHITE, 60, 0, blend='Additive')
    story('...show the real old fight: ranks march across the wall', B(n), B(n + 2))

def tag(v0, label):
    n = v0 + 14
    # "We're goin' to beat you all to": the wall fills from the ground, white on top
    sq.cut(q(B(n)), q(B(n + 1)), ['Verts'], [5])
    sq.fill('Verts', 3, B(n), B(n + 1), [tip(CRIMSON)], 0, 100)
    sq.fill(TRUNKS, 0, B(n), B(n + 1), [tip(MAROON)], 0, 100, per_model=True)
    story(f'{label}: the wall fills from the ground', B(n), B(n + 1))
    # "Chig-gar-roo-gar-rem! Chig-gar-roo-gar-rem!": a light hops syllable by syllable across the arches and wall
    n += 1
    sq.cut(q(B(n)), q(B(n + 1)), ['arches_big'], [0, 1])
    for j in range(10):
        t = bt(n, (j // 5) * 2 + (j % 5) * 0.4)
        sq.on(ARCHS[j], 0, t, t + 0.45, tip(CRIMSON), 100, 30)
        k = min(j, 8) if j < 9 else 4
        vglow(k, 50, t, 0.45, CRIMSON, layer=1 + j % 2, h=8)
    story('Chig-gar-roo-gar-rem x2: a light hops across the arches and the wall', B(n), B(n + 1))
    # "Rough! Tough! Real stuff! Texas A&M!"
    n += 1
    slam(bt(n, 0), bt(n, 1) - bt(n, 0) - 0.03, MAROON, 'ROUGH! (maroon)')
    slam(bt(n, 1), bt(n, 2) - bt(n, 1) - 0.03, WHITE, 'TOUGH! (white)')
    t = bt(n, 2)
    sq.moment(t, bt(n, 3) - 0.03, lambda a, b: sq.shockwave(ALL, 0, a, b, [WHITE, MAROON], cx=50, cy=30, r_end=240,
                                                              w_end=90), MAROON, fade_to=30)
    story('REAL STUFF! (maroon and white ring)', t, bt(n, 3))
    t = bt(n, 3)
    spell('TEXAS A&M', t, t + 2.6, fadein=0.05, fadeout=0.7)
    sq.cut(q(t), q(t + 2.6), ['Verts'], [0, 1, 2, 3, 5])
    sq.on('Verts', 5, t, t + 2.6, MAROON, 70, 35)
    ring(t, 1.4, (WHITE, MAROON), cx=50, cy=50, r_end=200, w_end=30, layer=1, el='AllModels')
    house_flash(t, 1.2)
    story('TEXAS A&M! one letter per Vert', t, t + 2.6)

# ---------------------------------------------------------------- verse 1: "All hail" builds Aggieland
V = 7
verse_lines(V, VERSE1)
wall_bg(B(V), B(V + 14))
logo(B(V) + 0.2, B(V + 2) + 0.4, fadein=0.9, fadeout=0.7)
sq.cut(q(B(V)), q(B(V + 2) + 0.4), ['Verts'], [5])
wall_bg(B(V), B(V + 2) + 0.4, bright=22)
story('All hail to dear old Texas A&M: the ATM logo glows on', B(V), B(V + 2))
# Rally around Maroon and White
sq.bars('Verts', 2, B(V + 2), B(V + 4), 'H-compress', [MAROON, WHITE], count=2, cycles=2)
for j in range(2):
    t = B(V + 2) + j * 2 * M * PER / 2
    sweep(FENCE, t, M * PER, True, (WHITE, MAROON)); sweep(FENCE, t, M * PER, False, (WHITE, MAROON), layer=3)
story('Rally around Maroon and White: bands rally to the centre', B(V + 2), B(V + 4))
aggie_ring(V + 4)
ranks(V + 6)
# That good old Aggie spirit thrills us: white ghosts rise
for j in range(8):
    t = bt(V + 8, j)
    k = [4, 2, 6, 0, 8, 3, 5, 1][j]
    vx = VERT_X[k]
    sq.morph('Verts', j % 4, t, t + 1.6, [WHITE, MAROON], (0, -10, 100, -10), (0, 110, 100, 110),
             tail_start=10, tail_end=60, extra={'B_CUSTOM_SubBuffer': sub(max(vx - 6, -0.01), 0, min(vx + 6, 99.99), 100)})
sq.fill(SPIRAL, 1, B(V + 8), B(V + 10), [tip(SPIRAL_RED)], 0, 100, per_model=True, fadeout=0.6)
sq.fill(TRUNKS, 0, B(V + 8), B(V + 10), [tip(MAROON)], 0, 100, per_model=True, fadeout=0.6)
story('That good old Aggie spirit thrills us: white ghosts rise', B(V + 8), B(V + 10))
# And makes us yell and yell and yell
for k, (beat, vk) in enumerate(((2, 1), (4, 4), (6, 7))):
    t = bt(V + 10, beat)
    ring(t, 1.1, (WHITE, CRIMSON), cx=VERT_X[vk], cy=50, r_end=60, w_end=30, layer=0)
    house_flash(t, 0.6)
    sq.on(SPIRAL, 1, t, t + 0.5, WHITE, 90, 0)
story('...yell and yell and yell: three white bursts, left, centre, right', B(V + 10), B(V + 12))
# So let's fight for dear old Texas A&M: diagonal charges every beat
for j in range(8):
    t = bt(V + 12, j)
    sq.morph('Verts', 0, t, t + PER * 1.2, [WHITE, CRIMSON], *DIAG['up-right' if j % 2 == 0 else 'up-left'],
             tail_start=5, tail_end=40)
story("So let's fight for dear old Texas A&M: diagonal charges", B(V + 12), B(V + 14))
tag(V, 'verse 1 tag')

# ---------------------------------------------------------------- verse 2: "Good-bye" - the rivalry
V = 24
verse_lines(V, VERSE2)
wall_bg(B(V) + 2.0, B(V + 8))
# Good-bye to texas university: orange appears in the far-right corner and waves good-bye
sq.on('tree-4', 1, B(V), B(V + 4), ORANGE, 0, 90)
for j in range(8):
    t = bt(V, j)
    for m in ('Vert-5', 'Vert-6'):
        sq.bars(m, 2, t, t + PER, 'Left' if j % 2 else 'Right', [ORANGE, TU_WHITE], count=2, cycles=0.5)
story('Good-bye to texas university: burnt orange waves from the far-right corner', B(V), B(V + 2))
# So long to the orange and the white: stripes cover the wall, maroon sweeps them off to the right
sq.bars('Verts', 3, B(V + 2), B(V + 4), 'Right', [ORANGE, TU_WHITE], count=3, cycles=1)
sq.morph('Verts', 2, bt(V + 2, 1), B(V + 4), [CRIMSON, MAROON], (0, 0, 0, 100), (100, 0, 100, 100),
         tail_start=100, tail_end=100)
sq.morph(FENCE, 1, B(V + 2), B(V + 4), [ORANGE, ORANGE], (60, 0, 60, 100), (115, 0, 115, 100), tail_start=8, tail_end=8)
sq.on('tree-4', 1, B(V + 4) - 0.6, B(V + 4), ORANGE, 90, 0)
story('So long to the orange and the white: maroon sweeps the orange off the wall', B(V + 2), B(V + 4))
aggie_ring(V + 4)
ranks(V + 6)
# The eyes of Texas are upon you: darkness, orange eyes open one pair per beat
EYES = [(4, 12), (1, 20), (7, 9), (2, 28), (6, 24), (0, 14), (8, 30), (3, 8), (5, 18)]   # (Vert k, row from top)
eye_l, eye_r = (0, 1), (4, 5)
def eyes(k, row, t0, t1, blink=()):
    """a pair of 2x2 orange eyes on Vert k; `blink` = times they close for 0.15 s"""
    spans, a = [], t0
    for bl in sorted(blink):
        if a < bl < t1: spans.append((a, bl)); a = bl + 0.15
    spans.append((a, t1))
    for L, (c1, c2) in ((1, eye_l), (2, eye_r)):
        sb = cell(c1, c2, 43 - row - 1, 43 - row)
        for s, e in spans:
            sq.on(VERTS[k], L, s, e, ORANGE, 100, 100, subbuf=sb)
n = V + 8
sq.cut(q(B(n)), q(B(n + 2)), ['Verts'], [5])
sq.cut(q(B(n)), q(B(n + 4)), ['arches_big', 'trees'], [1, 2])          # the eyes get the dark
sq.on('Verts', 5, B(n), B(n + 4), DEEP, 18, 18)
fire_at = bt(n + 3, 0)
for j, (k, row) in enumerate(EYES[:8]):
    t0 = bt(n, j)
    blinks = [bt(n + 2, 1 + (j % 3)), bt(n + 2, 3 + (j % 2) * 0.5)]
    eyes(k, row, t0, fire_at + 0.2 + 0.04 * (44 - row), blinks)
sq.on(['window-master', 'window-char'], 0, B(n), fire_at + 0.5, ORANGE, 30, 90)
story('The eyes of Texas are upon you: orange eyes open on the dark wall; the windows watch', B(n), B(n + 2))
# That is the song they sing so well (sounds like hell!): the eyes blink along, then flames burn them away
fire('Verts', fire_at, bt(n + 4, 1), height=75, layer=2)
fire(TRUNKS, fire_at, bt(n + 4, 1), height=80, layer=0, per_model=True)
sq.on(['window-master', 'window-char'], 0, fire_at + 0.5, bt(n + 4, 1), CRIMSON, 100, 0)
sq.on('roofline-1', 0, fire_at, bt(n + 4, 1), Grad(CRIMSON, ORANGE, mode='right'), 80, 0)
story('...sounds like hell!: flames roar up the wall and trunks and burn the eyes away', fire_at, bt(n + 4, 1))
# So good-bye to texas university: embers float up, the last orange ember blinks out, maroon returns
n = V + 12
sq.meteors('Verts', 2, bt(n, 1), B(n + 2), [ORANGE, CRIMSON], direction='Up', count=8, speed=6, bright=70)
for j, t in enumerate((bt(n, 2), bt(n, 4), bt(n, 6))):
    sq.on('tree-4', 1, t, t + 0.4, ORANGE, 100 - 30 * j, 0)
sq.fill('Verts', 3, bt(n, 2), B(n + 2), [maroon_g('up')], 0, 45)
story('So good-bye to texas university: embers float off, the last orange ember blinks out', B(n), B(n + 2))
wall_bg(bt(n, 4), B(n + 2), bright=30)
tag(V, 'verse 2 tag')

# ================================================================ Saw Varsity's horns off! (bars 41-54)
CUTS = [('Vert-3', 'Vert-6'), ('Vert-4', 'Vert-5'), ('Vert-7', 'Vert-9'), ('Vert-1', 'Vert-2')]
cut_t = {}

def sway(n0, n1):
    """the whole yard sways like the student section: a stroke every two beats"""
    for j in range(int(round((B(n1) - B(n0)) / (2 * PER)))):
        t0, t1 = bt(n0, 2 * j), bt(n0, 2 * j + 2)
        if t0 >= B(n1) - 0.1: break
        right = j % 2 == 0
        sweep(ARCHES, t0, t1 - t0, right, (WHITE, MAROON), layer=1, tail=60)
        sweep(FENCE, t0, t1 - t0, right, (WHITE, MAROON), layer=1, tail=40)
        sweep('roofline-1', t0, t1 - t0, right, (WHITE, MAROON), layer=0, tail=50)
        for g, d in zip(FOREST, (right, not right)):
            sq.wave(g, 1, t0, t1, MAROON, bright=80, waves=180, speed=10, kind='Sine', fill='None', thickness=40,
                    height=60, direction='Left to Right' if d else 'Right to Left', colors=[WHITE, MAROON])
    sq.spirals(TRUNKS, 1, B(n0), B(n1), [MAROON, WHITE], count=2, thickness=45, movement=1.5, bright=70,
               perModel=True, swing=True)
    sq.spirals(SPIRAL, 1, B(n0), B(n1), [SPIRAL_RED, WHITE], count=2, thickness=40, movement=1.2, bright=90,
               perModel=True, swing=True)

def saw_strokes(pair, n, label):
    """a white saw blade cuts back and forth through this pair of horn pieces for 2 bars, sparks flying; at the end
    the pieces fall"""
    for m in pair:
        r = HORN_ROW[m]
        y = (43 - r) / 44 * 100
        for j in range(4):
            t0, t1 = bt(n, 2 * j), bt(n, 2 * j + 2)
            a, b = ((0, y - 9, 0, y + 9), (100, y - 9, 100, y + 9)) if j % 2 == 0 else \
                   ((100, y - 9, 100, y + 9), (0, y - 9, 0, y + 9))
            sq.morph(m, 1, t0, t1, [WHITE, WHITE], a, b, tail_start=1, tail_end=12)
        sq.meteors(m, 2, B(n), B(n + 2) - 0.2, [WHITE, GOLD], direction='Down', count=6, speed=14, bright=80)
    story(label, B(n), B(n + 2))

# the longhorn appears as the chant starts; pieces come off chant by chant
T_HORN = B(41)
for p, n in zip(CUTS[:3], (41, 43, 45)):
    cut_t[p] = B(n + 2) - 0.05
cut_t[CUTS[3]] = SHORT_STAB[1]
for pair, t_off in cut_t.items():
    for m in pair:
        pic(m, 0, T_HORN, t_off, HORN_IMG[m], fadein=0.4 if t_off != SHORT_STAB[1] else 0.4)
        # the piece falls to the ground and lies there, dim
        r = HORN_ROW[m]; y = (43 - r) / 44 * 100
        if pair != CUTS[3]:
            sq.morph(m, 2, t_off, t_off + 0.7, [ORANGE, ORANGE], (0, y, 100, y), (0, 3, 100, 3), tail_start=8,
                     tail_end=8)
            sq.on(m, 3, t_off + 0.7, (B(50) if m in VERTS[:4] else B(52)) - 0.6, ORANGE, 40, 30,
                  subbuf=cell(0, 5, 0, 1))
pic('Vert-8', 0, T_HORN, B(53), HORN_IMG['Vert-8'], fadein=0.4)          # the head stays (hornless) a while
sq.cut(q(B(41)), q(B(55)), ['Verts'], [5])
sq.on('Verts', 5, B(41), B(55), DEEP, 20, 20)
sway(41, 47)
for pair, n, lab in zip(CUTS[:3], (41, 43, 45), ('Saw varsity\'s horns off! (1): the saw cuts the tips',
                                                 'Saw varsity\'s horns off! (2): the next pieces',
                                                 'Saw varsity\'s horns off! (3): almost to the head')):
    saw_strokes(pair, n, lab)

def short(k):
    t = SHORT_STAB[k]; s0, s1 = SILENCE[k]
    sq.moment(t, s0, lambda a, b: sq.on(ALL, 0, a, b, WHITE, 100, 40), WHITE, fade_to=0)
    sq.cut(q(s0), q(s1))                                                   # the band's silence: black
    spell('SHORT', s0, s1 - 0.05, verts=CENTRE5, fadein=0.05, fadeout=0.3)
    story(f'SHORT! ({k}): white flash, then black and SHORT in the silence', t, s1)

short(1)
# Varsity's horns are sawed off! x3: sway on; maroon sweeps the pieces off, left then right; the head drops
sway(48, 54)
for j, n in enumerate((48, 50)):
    sq.morph('Verts', 2, B(n + 2) - 1.2, B(n + 2), [CRIMSON, MAROON],
             *(((50, 0, 50, 100), (-10, 0, -10, 100)) if j == 0 else ((50, 0, 50, 100), (110, 0, 110, 100))),
             tail_start=40, tail_end=60)
    story(f"Varsity's horns are sawed off! ({j + 1}): maroon sweeps the {'left' if j == 0 else 'right'} pieces off",
          B(n), B(n + 2))
sq.morph('Vert-8', 2, B(53), B(53) + 1.0, [ORANGE, ORANGE], (0, 70, 100, 70), (0, -20, 100, -20), tail_start=40,
         tail_end=40)
logo(B(53) + 0.3, SHORT_STAB[2], fadein=0.8, fadeout=0.1)
story("Varsity's horns are sawed off! (3): the head drops away, the ATM logo takes its place", B(52), B(54))
short(2)

# ================================================================ interlude: the 12th Man, the Block T (bars 55-66)
I0 = 55
wall_bg(B(I0), B(I0 + 4), bright=35)
spell('12TH MAN', B(I0), B(I0 + 4), verts=VERTS[:8], stagger=PER, fadein=0.1, fadeout=0.6)
story('12TH MAN spells across the wall', B(I0), B(I0 + 4))
stand_end = B(65)
for i, s in enumerate(STICKS):            # the crowd stands, left to right
    t = B(I0) + i * (B(I0 + 8) - B(I0)) / len(STICKS)
    sq.fill(s, 0, t, t + 0.4, [plume], 0, 100)
    sq.on(s, 0, t + 0.4, stand_end, plume, 85, 60)
story('the 12th Man stands: the pixel sticks stand up one by one', B(I0), B(I0 + 8))
# the Block T: dots march in along the top, the stem drops down the middle Vert
TB = sub(-0.01, 77.26, 99.99, 99.99)
for j in range(4):
    t0 = B(I0 + 4) + j * (B(I0 + 8) - B(I0 + 4)) / 4
    for L, (x0, x1) in enumerate(((-5, 48), (105, 52))):
        sq.morph('Verts', L, t0, t0 + 2.0, [WHITE, MAROON], (x0, 0, x0, 100), (x1, 0, x1, 100), tail_start=4,
                 tail_end=25, extra={'B_CUSTOM_SubBuffer': TB})
sq.on('Verts', 2, B(I0 + 6), B(I0 + 8), maroon_g('right'), 0, 90, subbuf=TB)
sq.on('Verts', 2, B(I0 + 8), B(65), maroon_g('right'), 90, 90, subbuf=TB)
sq.morph('Vert-8', 1, B(I0 + 8), B(I0 + 9), [WHITE, MAROON], (0, 100, 100, 100), (0, 0, 100, 0), tail_start=5,
         tail_end=100)
sq.on('Vert-8', 1, B(I0 + 9), B(65), maroon_g('up'), 90, 90, subbuf=cell(1, 4, 0, 33))
for t in (B(I0 + 9), B(I0 + 10)):
    sq.on('Verts', 1, t, t + 0.6, WHITE, 80, 0, subbuf=TB, blend='Additive')
story('the Fightin\' Texas Aggie Band forms the Block T', B(I0 + 4), B(65))
for j in range(int((B(65) - B(I0 + 4)) / (2 * PER))):     # the four-way cross-through on the arches
    t = B(I0 + 4) + j * 2 * PER
    for k in range(10):
        arch_run(k, t, 2 * PER, rightward=(k + j) % 2 == 0, color=MAROON if k % 2 else CRIMSON)
sq.cut(q(B(I0 + 4)), q(B(65)), ['arches_big'], [1])
story('the arches do the band\'s four-way cross-through', B(I0 + 4), B(65))
# bars 65-66: the build into the key change
sq.fill('Verts', 3, B(65), B(67), [tip(CRIMSON)], 0, 100)
sq.fill(TRUNKS, 0, B(65), B(67), [tip(MAROON)], 0, 100, per_model=True)
sq.fill(FOREST, 1, B(65), B(67), [plume], 0, 100, per_model=True)
sq.cut(q(B(65)), q(B(67)), FOREST, [0])
story('build into the key change', B(65), B(67))

# ================================================================ the final strain in E-flat (bars 67-82)
F0 = 67
sq.moment(B(F0), B(F0) + 2 * PER, lambda a, b: sq.bars(ALL, 0, a, b, 'up', [Grad(WHITE, CRIMSON, MAROON, mode='up')],
                                                        count=1, cycles=1), WHITE, fade_to=40)
ring(B(F0) + 0.3, 1.6, (WHITE, MAROON), cx=50, cy=20, r_end=260, w_end=70, layer=1, el='AllModels')
story('the key change: a wave up the whole yard and a ring', B(F0), B(F0) + 2 * PER)
# strain 1: the logo in the middle, fireworks around it, barber poles, swirling spirals
logo(B(F0) + 2 * PER, B(75), fadein=0.5, fadeout=0.4)
for m in ('Vert-3', 'Vert-4', 'Vert-5', 'Vert-6'):
    fireworks(m, B(F0) + 2 * PER, B(75), [WHITE, MAROON, CRIMSON], layer=2, count=30, explosions=35)
wall_bg(B(F0) + 2 * PER, B(75), bright=30)
sq.spirals(TRUNKS, 1, B(F0), B(75), [MAROON, WHITE], count=3, rotation=20, thickness=50, movement=2.5, bright=80,
           perModel=True)
sq.spirals(SPIRAL, 1, B(F0), END, [SPIRAL_RED, WHITE], count=2, thickness=45, movement=2.0, bright=90, perModel=True,
           three_d=True)
for j in range(int((B(75) - B(F0)) / (2 * PER))):
    sweep(ARCHES, B(F0) + j * 2 * PER, 2 * PER, j % 2 == 0, (WHITE, CRIMSON), layer=1, tail=40)
story('strain 1: the logo with maroon and white fireworks around it', B(F0), B(75))
# strain 2: TEXAS A&M across the wall, pulsing on the downbeats
F2 = 75
spell('TEXAS A&M', B(F2), LAST_CHORD, stagger=PER / 2, fadein=0.15, fadeout=0.1)
wall_bg(B(F2), LAST_CHORD, bright=40)
for n in range(F2, 82):
    sq.on('Verts', 1, B(n), B(n) + 0.5, CRIMSON, 70, 0, blend='Additive')
sq.spirals(TRUNKS, 1, B(F2), LAST_CHORD, [MAROON, WHITE], count=3, rotation=-20, thickness=50, movement=-2.5,
           bright=85, perModel=True)
for j in range(int((LAST_CHORD - B(F2)) / PER)):
    sweep(ARCHES, B(F2) + j * PER, PER, j % 2 == 0, (WHITE, CRIMSON), layer=1, tail=40)
sq.twinkle(FENCE, 1, B(F2), LAST_CHORD, [WHITE, CRIMSON], count=25, steps=20, bright=80)
story('strain 2: TEXAS A&M across all nine Verts', B(F2), LAST_CHORD)
# the last chord: a white flash across the yard, then the logo, then the manger spot last
sq.moment(LAST_CHORD, LAST_CHORD + 0.8, lambda a, b: sq.shockwave(ALL, 0, a, b, [WHITE, MAROON], cx=50, cy=30,
                                                                    r_end=300, w_end=100), WHITE, fade_to=0)
sq.cut(q(LAST_CHORD + 0.8), q(DUR))
logo(LAST_CHORD + 0.1, DUR, fadein=0.3, fadeout=0.9, white=False)
sq.on(ARCHES, 1, LAST_CHORD + 0.8, DUR, maroon_g('right'), 70, 0)
sq.on('Nativity Spot', 0, LAST_CHORD + 0.3, DUR, WHITE, 60, 25)
story('the last chord: a white flash, then the ATM logo and the manger spot', LAST_CHORD, DUR)

# ================================================================ timing tracks + write
if '--no-images' not in sys.argv:
    write_images()
st = sorted(STORY, key=lambda x: x[1])
nbars = next(n for n in range(1, 2000) if B(n) > END)
sq.tracks = [
    ('Sections', marks([SPAN[n][0] for n, _, _ in SECTIONS], [n for n, _, _ in SECTIONS], end=DUR)),
    ('Story', [(lab, q(s), q(min(e, st[i + 1][1]) if i + 1 < len(st) else e)) for i, (lab, s, e) in enumerate(st)
               if q(min(e, st[i + 1][1]) if i + 1 < len(st) else e) > q(s)]),
    ('Words', [(w, q(s), q(e)) for w, s, e in WORDS]),
    ('Bars', marks([B(n) for n in range(1, nbars)], [str(n) for n in range(1, nbars)], end=END)),
    ('Beats', marks(BEATS, [str((i - PH) % M + 1) for i in range(len(BEATS))], end=END)),
    ('Kick', marks(KICKS, maxlen=PER / 2)), ('Snare', marks(SNARES, maxlen=PER / 2)),
]
sq.write(OUT, dict(song='Aggie War Hymn', artist='Fightin\' Texas Aggie Band', album='',
                   media=f'{MEDIA_ROOT}/seq2026/{SONG}/{WAV}',
                   comment='Generated from stem-separated audio analysis. Gig em!'),
         DUR, timeline=ARGS[1] if len(ARGS) > 1 else None)
print('images:', len(IMAGES), '->', IMG_DIR)
