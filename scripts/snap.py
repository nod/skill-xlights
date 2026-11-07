"""A still of one prop from a saved render: decode the .fseq at a timestamp, place the model's nodes from the layout,
colour each one as it was actually lit. Read-only; never talks to xLights.

usage: snap.py --fseq <song.fseq> --model <name> --at <m:ss[.t] | seconds> [--out <png>] [--show <show dir>]
               [--scale N] [--gain G] [--sub [name,name,...]] [--cone] [--max-px 2400]
       snap.py --fseq <song.fseq> --model <name> --strip <m:ss>..<m:ss> [--step 0.1]     a contact sheet

How it reads the render:
- frame index = floor(t / step), step from the fseq header (25 ms);
- channels through `layout.Layout`: per-model absolute base (controller base + offset - 1), channels per node and
  colour order from the StringType ("GRB Nodes", "RGBW Nodes", single colour; a white channel is added to R, G
  and B); `fseq.rgb` takes a 1-based node and does the channel-minus-one itself. One-node-per-string types (a
  dumb string, a strobe, a 3-channel flood) are refused;
- the model is bounded by the NEXT model's start channel: if its nodes x stride would run past it the tool
  refuses, because a frame read does no bounds checking and a wrong geometry would read the neighbour;
- sample STRICTLY INSIDE an effect's span: a boundary frame still holds the neighbour's last frame. This draws
  exactly the frame you ask for.

Node positions from the layout, per DisplayAs:
- Custom: `CustomModelCompressed` is `node,ROW,COL[,layer];...` with row 0 at the top; a `CustomModel` grid
  (rows ';', cols ',') is accepted too.
- Matrix / Tree: NumStrings x StrandsPerString strands of NodesPerString/StrandsPerString nodes, zig-zagging
  between strands of one string unless NoZig, honouring Dir (L/R) and StartSide (B/T). `--cone` fans a Tree's
  strands into a triangle (TreeDegrees, TreeBottomTopRatio).
- Single Line / Arches / Circle / Window Frame / Poly Line / anything else: a row, a half-circle per arch, rings,
  a rectangle, or the PointData polyline. Approximate, and says so on stdout.

Drawing: one filled square per node, `--scale` px (default 12, reduced so the image stays under `--max-px` wide);
colour = decoded RGB x `--gain` clamped to 255; unlit nodes (every channel <= 8) a very dark grey so the shape stays
visible; black background; caption = model, m:ss.mmm, frame index, fseq name. `--sub` outlines each submodel's
nodes in its own thin colour (name them to limit it) and prints a table: nodes, lit, mean RGB of the lit nodes,
peak RGB. `--strip a..b --step s` tiles every frame from a to b (cap 40 tiles), each captioned: how a flap, a
chase or an eye gate is checked over time.

Needs Pillow (the audio env has it through matplotlib) and zstandard (setup.sh installs it).
Deterministic: same fseq, same layout, same arguments -> byte-identical PNG.
"""
import sys, math, argparse, os
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fseq import FSEQ, rgb as _rgb
from layout import Layout, show_folder_of, single_node, channels_per_node, channel_order

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None

LIT = 8            # a node with every channel <= LIT is "unlit"
UNLIT = (30, 30, 30)
SUB_COLOURS = [(255, 64, 64), (64, 255, 64), (80, 140, 255), (255, 255, 0), (255, 0, 255),
               (0, 255, 255), (255, 140, 0), (180, 120, 255), (120, 255, 180), (255, 160, 200),
               (200, 200, 200), (140, 90, 40)]


# --------------------------------------------------------------------------- time
def mmss(t, dp=1):
    """Seconds -> 'M:SS.d'. A position on the timeline reads in minutes and seconds, as in xLights."""
    t = float(t); sign = '-' if t < 0 else ''; t = abs(t)
    m = int(t // 60); s = t - m * 60
    if dp <= 0:
        s = int(round(s))
        if s == 60: m, s = m + 1, 0
        return f'{sign}{m}:{s:02d}'
    s_str = f'{s:0{3 + dp}.{dp}f}'
    if float(s_str) >= 60.0: m, s_str = m + 1, f'{0:0{3 + dp}.{dp}f}'
    return f'{sign}{m}:{s_str}'

def mmss_ms(ms, dp=1): return mmss(float(ms) / 1000.0, dp)
def span(a, b, dp=1): return f'{mmss(a, dp)}-{mmss(b, dp)}'
def dur(seconds): return f'{float(seconds):.2f}s' if abs(float(seconds)) < 60 else mmss(seconds)

def parse_time(s):
    """'2:10.0' / '1:29.2' / '130' / '130.25' -> seconds."""
    s = s.strip()
    if ':' in s:
        m, sec = s.split(':', 1)
        return int(m) * 60 + float(sec)
    return float(s)

def frame_of(fs, t):
    n = int(round(t * 1000)) // fs.step
    if not 0 <= n < fs.frames:
        sys.exit(f'{mmss(t, 3)} is outside the render (0 .. {mmss_ms(fs.frames * fs.step, 3)}, {fs.frames} frames)')
    return n


# --------------------------------------------------------------------------- layout
def _int(m, k, default=1):
    v = m.get(k)
    try: return int(float(v))
    except (TypeError, ValueError): return default

def _bool(m, k):
    return (m.get(k) or '').strip().lower() == 'true'

def model_element(show, name):
    r = ET.parse(show / 'xlights_rgbeffects.xml').getroot()
    for m in r.iter('model'):
        if m.get('name') == name: return m, r
    names = sorted(m.get('name') for m in r.iter('model'))
    sys.exit(f"no model {name!r} in {show}/xlights_rgbeffects.xml. Models: {', '.join(names)}")

def abs_start(m, lay):
    name = m.get('name')
    if name in lay.start: return lay.start[name]
    sc = (m.get('StartChannel') or '').strip()
    if sc.isdigit(): return int(sc)
    sys.exit(f'cannot resolve StartChannel {sc!r} of {name!r} (controllers: {sorted(lay.bases)})')

def node_count(m):
    d = m.get('DisplayAs')
    if d == 'Custom':
        return len(custom_positions(m))
    if d == 'Arches': return _int(m, 'NodesPerArch') * _int(m, 'NumArches')
    if d == 'Window Frame': return _int(m, 'TopNodes') + _int(m, 'BottomNodes') + 2 * _int(m, 'SideNodes')
    if d == 'Poly Line': return _int(m, 'NodesPerString') * _int(m, 'PolyStrings')
    return _int(m, 'NodesPerString') * _int(m, 'NumStrings')

def custom_positions(m):
    """{node: (x, y)} with y=0 at the top, from CustomModelCompressed (node,row,col) or a CustomModel grid."""
    pos = {}
    cmc = m.get('CustomModelCompressed')
    if cmc:
        for t in cmc.split(';'):
            if not t.strip(): continue
            f = [int(v) for v in t.split(',')]
            node, row, col = f[0], f[1], f[2]
            if len(f) > 3 and f[3] != 0: continue          # only layer 0 of a 3D custom model
            pos[node] = (float(col), float(row))
        return pos
    cm = m.get('CustomModel') or ''
    for row, line in enumerate(cm.split(';')):
        for col, cell in enumerate(line.split(',')):
            cell = cell.strip()
            if cell.isdigit(): pos[int(cell)] = (float(col), float(row))
    return pos

def strand_positions(m, cone=False):
    """Matrix / Tree as columns (vertical) or rows (horizontal) of strands."""
    d = m.get('DisplayAs')
    strings, per_string = _int(m, 'NumStrings'), _int(m, 'NodesPerString')
    sps = max(1, _int(m, 'StrandsPerString'))
    per_strand = per_string // sps
    strands = strings * sps
    zig = not _bool(m, 'NoZig')
    vertical = d == 'Tree' or _bool(m, 'Vertical')
    left = (m.get('Dir') or 'L').upper().startswith('L')
    from_bottom = (m.get('StartSide') or 'B').upper().startswith('B')
    pos, note = {}, None
    for n in range(strings * per_string):
        s_in = (n % per_string) // per_strand                 # strand within its string
        k = (n % per_string) % per_strand                      # node along the strand
        strand = (n // per_string) * sps + s_in
        if zig and s_in % 2 == 1: k = per_strand - 1 - k
        if vertical:
            col = strand if left else strands - 1 - strand
            row = per_strand - 1 - k if from_bottom else k
        else:                                                  # horizontal matrix: strands are rows
            col = k if left else per_strand - 1 - k
            row = strands - 1 - strand if from_bottom else strand
        pos[n + 1] = (float(col), float(row))
    if cone and vertical:
        deg = float(m.get('TreeDegrees') or 180.0)
        ratio = float(m.get('TreeBottomTopRatio') or 6.0)
        width = 2.0 * strands
        cx, half = width / 2.0, width / 2.0
        for node, (col, row) in list(pos.items()):
            h = 1.0 - row / max(1, per_strand - 1)             # 0 bottom .. 1 top
            r = half * (1.0 - h * (1.0 - 1.0 / ratio))
            frac = col / max(1, strands - 1)
            theta = math.radians(-deg / 2.0 + deg * frac)      # -90..90 for a 180 tree
            pos[node] = (cx + r * math.sin(theta), row)
        note = f'cone: {strands} strands fanned over {deg:g} deg, bottom/top ratio {ratio:g} (approximate)'
    elif cone:
        note = '--cone ignored: not a vertical strand model'
    return pos, note

def fallback_positions(m):
    """Single-row (or simple polyline) geometry for everything else. Approximate."""
    d = m.get('DisplayAs')
    n = node_count(m)
    left = (m.get('Dir') or 'L').upper().startswith('L')
    pos = {}
    if d == 'Arches':
        per, arches = _int(m, 'NodesPerArch'), _int(m, 'NumArches')
        w = per * 0.7
        for a in range(arches):
            for i in range(per):
                f = i / max(1, per - 1)
                if not left: f = 1.0 - f
                th = math.pi * (1.0 - f)                        # left foot -> right foot
                pos[a * per + i + 1] = (a * (w + 2) + w / 2 + (w / 2) * math.cos(th), (w / 2) * (1 - math.sin(th)))
        return pos, f'{arches} arch(es) of {per} drawn as half-circles, StartSide/Dir approximate'
    if d == 'Circle':
        sizes = [int(x) for x in (m.get('LayerSizes') or '').split(',') if x.strip().isdigit()] or [n]
        R = max(sizes) / 2.0 + 1
        node = 1
        for li, cnt in enumerate(sizes):                        # outer ring first
            r = R * (1 - li / max(1, len(sizes)))
            for i in range(cnt):
                th = 2 * math.pi * i / cnt * (1 if left else -1)
                pos[node] = (R + r * math.sin(th), R - r * math.cos(th)); node += 1
        return pos, f'circle rings {sizes} drawn outer-first, start at 12 o\'clock (approximate)'
    if d == 'Window Frame':
        top, bot, side = _int(m, 'TopNodes'), _int(m, 'BottomNodes'), _int(m, 'SideNodes')
        ccw = (m.get('Rotation') or '').lower().startswith('counter')
        W, H = max(top, bot) + 1, side + 1
        seq = []
        if ccw:   # up the right side, across the top leftward, down the left, across the bottom rightward
            seq += [(W, H - 1 - i) for i in range(side)]
            seq += [(W - 1 - i * (W - 1) / max(1, top - 1), 0) for i in range(top)]
            seq += [(0, 1 + i) for i in range(side)]
            seq += [(1 + i * (W - 1) / max(1, bot - 1), H) for i in range(bot)]
        else:     # up the left, across the top rightward, down the right, across the bottom leftward
            seq += [(0, H - 1 - i) for i in range(side)]
            seq += [(1 + i * (W - 1) / max(1, top - 1), 0) for i in range(top)]
            seq += [(W, 1 + i) for i in range(side)]
            seq += [(W - 1 - i * (W - 1) / max(1, bot - 1), H) for i in range(bot)]
        for i, p in enumerate(seq[:n]): pos[i + 1] = (float(p[0]), float(p[1]))
        return pos, f"window frame side {side}/top {top}/bottom {bot}, {'CCW' if ccw else 'CW'} from bottom corner (approximate)"
    if d == 'Poly Line':
        pts = [float(v) for v in (m.get('PointData') or '').split(',') if v.strip()]
        P = [(pts[i], pts[i + 1]) for i in range(0, len(pts) - 2, 3)]
        segs = [_int(m, f'Seg{i}', 0) for i in range(1, len(P))]
        if len(P) >= 2 and sum(segs) > 0:
            node, xs = 1, []
            for (x0, y0), (x1, y1), cnt in zip(P, P[1:], segs):
                for i in range(cnt):
                    f = (i + 0.5) / cnt
                    xs.append((x0 + (x1 - x0) * f, y0 + (y1 - y0) * f))
            if not left: xs = xs[::-1]
            minx = min(x for x, _ in xs); maxy = max(y for _, y in xs)
            scale = (len(xs) * 0.9) / max(1e-6, max(x for x, _ in xs) - minx)
            for i, (x, y) in enumerate(xs[:n]):
                pos[i + 1] = ((x - minx) * scale, (maxy - y) * scale)
            return pos, f'poly line from PointData, {len(P)} points, segments {segs} (approximate)'
    for i in range(n):
        pos[i + 1] = (float(i if left else n - 1 - i), 0.0)
    return pos, f'{d}: {n} nodes drawn as a single row (approximate geometry)'

def positions(m, cone=False):
    d = m.get('DisplayAs')
    if d == 'Custom': return custom_positions(m), None
    if d in ('Matrix', 'Vert Matrix', 'Tree'): return strand_positions(m, cone)
    return fallback_positions(m)


# --------------------------------------------------------------------------- reading
def decode(fs, frame_no, base, stride, nodes, order=(0, 1, 2, ())):
    """{node: (r,g,b)} for 1-based nodes 1..nodes, through fseq.rgb with the model's stride and colour order."""
    fr = fs.frame(frame_no)
    return {n: _rgb(fr, base, n, stride, order) for n in range(1, nodes + 1)}

def bound_check(root, m, base, stride, nodes, lay):
    """Refuse to read past the next model's start channel."""
    end = base + nodes * stride - 1
    nxt = None
    for o in root.iter('model'):
        if o is m: continue
        try: s = abs_start(o, lay)
        except SystemExit: continue
        if s > base and (nxt is None or s < nxt[0]): nxt = (s, o.get('name'))
    if nxt and end >= nxt[0]:
        sys.exit(f"{m.get('name')!r}: {nodes} nodes x {stride} from {base} ends at {end}, past {nxt[1]!r} at {nxt[0]}: "
                 "geometry or stride is wrong, refusing")
    return end, nxt


# --------------------------------------------------------------------------- drawing
def font(size):
    try: return ImageFont.load_default(size=size)
    except TypeError: return ImageFont.load_default()

def fit_scale(pos, scale, max_px):
    w = max(x for x, _ in pos.values()) + 1
    return max(1, min(scale, int(max_px // max(1, w))))

def draw_model(pos, colours, cell, gain, subs=None, caption=None, font_px=14):
    xs = [x for x, _ in pos.values()]; ys = [y for _, y in pos.values()]
    W = int((max(xs) + 1) * cell) + 2; H = int((max(ys) + 1) * cell) + 2
    cap_h = font_px + 6 if caption else 0
    if caption:                                   # a narrow prop must not truncate its caption
        f = font(font_px)
        W = max(W, int(ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(caption, font=f)) + 8)
    img = Image.new('RGB', (W, H + cap_h), (0, 0, 0))
    dr = ImageDraw.Draw(img)
    if caption: dr.text((3, 2), caption, fill=(220, 220, 220), font=font(font_px))
    gap = 1 if cell >= 4 else 0
    for n, (x, y) in pos.items():
        c = colours.get(n)
        if c is None: continue
        lit = max(c) > LIT
        col = tuple(min(255, int(round(v * gain))) for v in c) if lit else UNLIT
        x0, y0 = int(x * cell) + 1, int(y * cell) + 1 + cap_h
        dr.rectangle([x0, y0, x0 + cell - 1 - gap, y0 + cell - 1 - gap], fill=col)
    if subs:
        for i, (name, nodes) in enumerate(subs):
            oc = SUB_COLOURS[i % len(SUB_COLOURS)]
            for n in nodes:
                if n not in pos: continue
                x, y = pos[n]
                x0, y0 = int(x * cell) + 1, int(y * cell) + 1 + cap_h
                dr.rectangle([x0, y0, x0 + cell - 1 - gap, y0 + cell - 1 - gap], outline=oc)
    return img

def sub_table(subs, colours, nodes):
    rows = []
    for name, ns in subs:
        ns = [n for n in ns if 1 <= n <= nodes]
        lit = [colours[n] for n in ns if max(colours[n]) > LIT]
        mean = tuple(int(round(sum(c[i] for c in lit) / len(lit))) for i in range(3)) if lit else (0, 0, 0)
        peak = max(lit, key=lambda c: (max(c), sum(c))) if lit else (0, 0, 0)
        rows.append((name, len(ns), len(lit), mean, peak))
    w = max([len(r[0]) for r in rows] + [8])
    print(f"{'submodel':<{w}} {'nodes':>5} {'lit':>4}  {'mean RGB':<15} {'peak RGB'}")
    for name, cnt, lit, mean, peak in rows:
        print(f'{name:<{w}} {cnt:5d} {lit:4d}  {str(mean):<15} {peak}')


# --------------------------------------------------------------------------- main
def main():
    if Image is None:
        sys.exit('Pillow is not importable here: install it into the audio env (uv pip install pillow).')
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--fseq', required=True)
    ap.add_argument('--model', required=True)
    ap.add_argument('--at', help='m:ss[.t] or seconds')
    ap.add_argument('--out', help='PNG path (default: <model>_<m-ss.mmm>.png in the cwd)')
    ap.add_argument('--show', help='show folder holding xlights_rgbeffects.xml (default: found above the fseq, else XLIGHTS_SHOW)')
    ap.add_argument('--scale', type=int, default=12, help='px per node (auto-reduced to fit --max-px)')
    ap.add_argument('--max-px', type=int, default=2400, help='max image width')
    ap.add_argument('--gain', type=float, default=1.0)
    ap.add_argument('--sub', nargs='?', const='*', help='outline submodels and print the table; optional comma list of names')
    ap.add_argument('--cone', action='store_true', help='Tree: fan the strands into a triangle')
    ap.add_argument('--strip', help='a..b (m:ss or seconds): contact sheet of frames a..b')
    ap.add_argument('--step', type=float, default=0.1, help='strip step in seconds')
    ap.add_argument('--tile-px', type=int, default=320, help='strip: max tile width')
    a = ap.parse_args()
    if not a.at and not a.strip: ap.error('--at or --strip is required')

    fpath = Path(a.fseq).expanduser()
    show = Path(a.show).expanduser() if a.show else show_folder_of(fpath) \
        or Path(os.environ.get('XLIGHTS_SHOW', Path(__file__).resolve().parent.parent))
    if not (show / 'xlights_rgbeffects.xml').exists():
        sys.exit(f'no xlights_rgbeffects.xml in {show}; pass --show')
    fs = FSEQ(fpath)
    lay = Layout(show)
    m, root = model_element(show, a.model)
    base = abs_start(m, lay)
    st = m.get('StringType') or 'RGB Nodes'
    if single_node(st):
        sys.exit(f"{a.model!r} is {st!r}: xLights drives it as one node per string, not one per pixel, and snap.py "
                 "draws per-pixel models only")
    stride, order = channels_per_node(st), channel_order(st)
    pos, note = positions(m, a.cone)
    nodes = max(pos) if pos else 0
    if not pos: sys.exit(f'{a.model!r}: no node positions could be derived')
    end, nxt = bound_check(root, m, base, stride, nodes, lay)
    print(f"{a.model}: {m.get('DisplayAs')}, {nodes} nodes, stride {stride}, abs channels {base}-{end}"
          + (f' (next model {nxt[1]!r} at {nxt[0]})' if nxt else '') + f'; fseq step {fs.step} ms, {fs.frames} frames')
    if note: print(f'geometry: {note}')
    if a.scale != fit_scale(pos, a.scale, a.max_px):
        print(f'scale reduced {a.scale} -> {fit_scale(pos, a.scale, a.max_px)} px to keep the image under {a.max_px} px wide')

    subs = []
    if a.sub:
        allsubs = lay.subnodes.get(a.model, {})
        if a.sub == '*': names = list(allsubs)
        else:
            names = [s.strip() for s in a.sub.split(',')]
            missing = [s for s in names if s not in allsubs]
            if missing: sys.exit(f"no submodel {missing} on {a.model!r}; has: {', '.join(allsubs)}")
        subs = [(nm, allsubs[nm]) for nm in names]
        if not subs: print(f'{a.model!r} has no submodels')

    if a.strip:
        lo_s, hi_s = a.strip.split('..', 1)
        lo, hi = parse_time(lo_s), parse_time(hi_s)
        if hi < lo or a.step <= 0: sys.exit('--strip needs a..b with b >= a and --step > 0')
        times = [lo + i * a.step for i in range(int(round((hi - lo) / a.step)) + 1)]
        if len(times) > 40:
            print(f'strip capped at 40 tiles ({len(times)} requested): step raised to {(hi - lo) / 39:.3f}s')
            times = [lo + i * (hi - lo) / 39 for i in range(40)]
        cell = fit_scale(pos, a.scale, a.tile_px)
        tiles = []
        for t in times:
            fno = frame_of(fs, t)
            cols = decode(fs, fno, base, stride, nodes, order)
            tiles.append(draw_model(pos, cols, cell, a.gain, subs, caption=f'{mmss(t, 1)} f{fno}', font_px=11))
        tw, th = max(t.width for t in tiles), max(t.height for t in tiles)
        per_row = max(1, a.max_px // (tw + 4))
        rows = math.ceil(len(tiles) / per_row)
        cap = f'{a.model}  {span(lo, hi, 1)} step {dur(a.step)}  {fpath.name}'
        sheet = Image.new('RGB', (min(len(tiles), per_row) * (tw + 4), rows * (th + 4) + 20), (0, 0, 0))
        ImageDraw.Draw(sheet).text((3, 2), cap, fill=(220, 220, 220), font=font(14))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % per_row) * (tw + 4), 20 + (i // per_row) * (th + 4)))
        out = Path(a.out) if a.out else Path(f"{a.model.replace('/', '_')}_strip_{mmss(lo, 1).replace(':', '-')}.png")
        out.parent.mkdir(parents=True, exist_ok=True); sheet.save(out, optimize=False)
        print(f'strip {span(lo, hi, 1)} x{len(tiles)} -> {out} ({sheet.width}x{sheet.height})')
        if subs:
            for t in times:
                cols = decode(fs, frame_of(fs, t), base, stride, nodes, order)
                lit = {nm: sum(1 for n in ns if 1 <= n <= nodes and max(cols[n]) > LIT) for nm, ns in subs}
                print(f'  {mmss(t, 1):>7}  ' + '  '.join(f'{nm}={v}' for nm, v in lit.items()))
        return

    t = parse_time(a.at)
    fno = frame_of(fs, t)
    cols = decode(fs, fno, base, stride, nodes, order)
    cell = fit_scale(pos, a.scale, a.max_px)
    cap = f'{a.model}  {mmss(t, 3)}  frame {fno}  {fpath.name}'
    img = draw_model(pos, cols, cell, a.gain, subs, caption=cap)
    out = Path(a.out) if a.out else Path(f"{a.model.replace('/', '_')}_{mmss(t, 3).replace(':', '-')}.png")
    out.parent.mkdir(parents=True, exist_ok=True); img.save(out, optimize=False)
    lit = [c for c in cols.values() if max(c) > LIT]
    peak = max(lit, key=lambda c: (max(c), sum(c))) if lit else (0, 0, 0)
    print(f'{mmss(t, 3)} frame {fno}: {len(lit)}/{nodes} nodes lit, peak {peak} -> {out} ({img.width}x{img.height})')
    if subs: sub_table(subs, cols, nodes)

if __name__ == '__main__':
    main()
