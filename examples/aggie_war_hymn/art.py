"""Pixel art for the Aggie War Hymn on the lol2026 Verts (nine 6x44 vertical matrices).

Bitmaps are lists of 6-character rows, TOP row first. Characters: '.' off, '#' main colour, 'w' white accent,
'o' second colour. `draw()` turns a bitmap into On effects in pixel-exact subbuffers on one single Vert model
(rows merged into rectangles, one effect per rectangle, one layer per rectangle).
"""
from seqlib import sub

W, H = 6, 44

# ---------------------------------------------------------------- a bold 6x7 font (scaled x2 tall for big letters)
FONT = {
    'T': ['######', '######', '..##..', '..##..', '..##..', '..##..', '..##..'],
    'E': ['######', '##....', '##....', '#####.', '##....', '##....', '######'],
    'X': ['##..##', '##..##', '.####.', '..##..', '.####.', '##..##', '##..##'],
    'A': ['.####.', '##..##', '##..##', '######', '##..##', '##..##', '##..##'],
    'S': ['.#####', '##....', '##....', '.####.', '....##', '....##', '#####.'],
    '&': ['.###..', '##.##.', '.###..', '####.#', '##.###', '##..##', '.###.#'],
    'M': ['#....#', '##..##', '######', '#.##.#', '#....#', '#....#', '#....#'],
    'H': ['##..##', '##..##', '##..##', '######', '##..##', '##..##', '##..##'],
    'O': ['.####.', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.'],
    'R': ['#####.', '##..##', '##..##', '#####.', '##.##.', '##..##', '##..##'],
    'W': ['#....#', '#....#', '#....#', '#.##.#', '#.##.#', '######', '##..##'],
    'P': ['#####.', '##..##', '##..##', '#####.', '##....', '##....', '##....'],
    'G': ['.#####', '##....', '##....', '##.###', '##..##', '##..##', '.####.'],
    'I': ['######', '..##..', '..##..', '..##..', '..##..', '..##..', '######'],
    '!': ['..##..', '..##..', '..##..', '..##..', '......', '..##..', '..##..'],
    '1': ['..##..', '.###..', '..##..', '..##..', '..##..', '..##..', '.####.'],
    '2': ['.####.', '##..##', '....##', '...##.', '..##..', '.##...', '######'],
    'N': ['#....#', '##...#', '###..#', '#.##.#', '#..###', '#...##', '#....#'],
    ' ': ['......'] * 7,
}

def tall(bm, k=2):
    """stretch a bitmap k times taller"""
    return [r for r in bm for _ in range(k)]

def glyph(ch, k=2):
    return tall(FONT[ch], k)

# ---------------------------------------------------------------- the ATM logo across the five centre Verts
# panels left to right: Vert-7 (A + left block of the T bar), Vert-1 (T bar), Vert-8 (T bar, stem, foot),
# Vert-2 (T bar), Vert-9 (M + right block). Proportions follow the logo file: the T bar is thin in the middle and
# deep over the A and the M, the white bevel line runs along the bar and down the stem, A and M sit below the bar.
def _logo():
    rows = {k: ['......'] * H for k in range(5)}
    def put(k, i, s):
        rows[k][i] = s
    for k in range(5):                       # the T bar: thin in the middle, deep over A and M
        for i in range(0, 12 if k in (0, 4) else 7):
            put(k, i, '######')
    for k in range(4):                       # white bevel line along the bar
        put(k, 2, '.wwwww' if k == 0 else 'wwwwww')
    put(4, 2, 'wwww#.')
    for i in range(3, 10):                   # the right block's vertical bevel
        put(4, i, '####w#')
    put(0, 1, '#.####')                      # the notch at the bar's top-left corner
    for i in range(7, 34):                   # the stem, with its bevel line
        put(2, i, '.##w#.')
    for i in range(3, 7):
        put(2, i, '###w##')
    for i in range(34, 42):                  # the foot
        put(2, i, '######')
    for i in range(34, 38):
        put(2, i, '###w##')
    put(2, 39, '####w#'); put(2, 40, '####w#')
    A = ['######', '######', '.####.', '.####.', '.#..#.', '##..##', '##..##', '##..##', '######', '######',
         '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##']
    M = ['#....#', '#....#', '##..##', '##..##', '######', '######', '#.##.#', '#.##.#', '#.##.#', '#.##.#',
         '#....#', '#....#', '#....#', '#....#', '#....#', '#....#', '##..##', '##..##']
    for j, s in enumerate(A): put(0, 14 + j, s)
    for j, s in enumerate(M): put(4, 14 + j, s)
    return [rows[k] for k in range(5)]

LOGO = _logo()
LOGO_VERTS = ['Vert-7', 'Vert-1', 'Vert-8', 'Vert-2', 'Vert-9']


def invert_logo(panel):
    """white letters with maroon bevel lines"""
    return [r.replace('#', 'W').replace('w', '#').replace('W', 'w') for r in panel]


# ---------------------------------------------------------------- drawing
def rects(bitmap, ch):
    """rectangles (c1, c2, i1, i2) covering every `ch` pixel; i = row index from the TOP. Runs in each row are
    merged downward while the same run repeats in the next row."""
    open_, out = {}, []
    for i, row in enumerate(list(bitmap) + ['.' * W]):
        runs, c = set(), 0
        while c < W:
            if row[c] == ch:
                c2 = c
                while c2 + 1 < W and row[c2 + 1] == ch: c2 += 1
                runs.add((c, c2)); c = c2 + 1
            else:
                c += 1
        for run in list(open_):
            if run not in runs: out.append((*run, open_.pop(run), i - 1))
        for run in runs:
            open_.setdefault(run, i)
    return out


def cell(c1, c2, row_lo, row_hi):
    """subbuffer for columns c1..c2 and rows row_lo..row_hi (0 = bottom) on one 6x44 Vert, edges just below pixel
    boundaries"""
    return sub(c1 * 100 / W - 0.01, row_lo * 100 / H - 0.01, (c2 + 1) * 100 / W - 0.01, (row_hi + 1) * 100 / H - 0.01)


def draw(sq, model, layer0, bitmap, t0, t1, colors, top=H - 1, fade_in=0.0, fade_out=0.25, level=100):
    """draw `bitmap` (top row first) on a single Vert with its top row at `top`; `colors` maps bitmap characters to
    colours. Fades in over fade_in s and out over fade_out s. Returns the next free layer."""
    L = layer0
    for ch, color in colors.items():
        for c1, c2, i1, i2 in rects(bitmap, ch):
            lo, hi = top - i2, top - i1
            if hi < 0 or lo > H - 1: continue
            sb = cell(c1, c2, max(lo, 0), min(hi, H - 1))
            a, b = t0, t1
            if fade_in > 0 and a + fade_in < b - 0.05:
                sq.on(model, L, a, a + fade_in, color, 0, level, subbuf=sb); a += fade_in
            if fade_out > 0 and b - fade_out > a + 0.05:
                sq.on(model, L, a, b - fade_out, color, level, level, subbuf=sb)
                sq.on(model, L, b - fade_out, b, color, level, 0, subbuf=sb)
            else:
                sq.on(model, L, a, b, color, level, level, subbuf=sb)
            L += 1
    return L
