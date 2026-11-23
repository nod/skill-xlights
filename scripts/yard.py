"""The whole yard from the street at given times in a saved render: every model drawn at its layout position (front
view: WorldPosX, WorldPosY; each model's nodes spread over its scaled size), coloured as rendered. Approximate
geometry (enough to see what lights where), exact colours.

usage: yard.py --fseq <song.fseq> --at t1,t2,... [--out yard.png] [--width 1600] [--models a,b,...]
"""
import argparse, sys
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import snap
from fseq import FSEQ
from layout import Layout

SHOW = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--fseq', required=True); ap.add_argument('--at', required=True)
ap.add_argument('--out', default='yard.png'); ap.add_argument('--width', type=int, default=1600)
ap.add_argument('--models', default='')
a = ap.parse_args()
root = ET.parse(SHOW / 'xlights_rgbeffects.xml').getroot()
lay = Layout(SHOW); fs = FSEQ(a.fseq)
want = set(a.models.split(',')) if a.models else None
SKIP = {'roofline-1', 'window-char', 'window-master'}          # the house is far back; drawn as a strip on top
items = []
for m in root.find('models'):
    name = m.get('name')
    if want and name not in want: continue
    if not want and name in SKIP: continue
    try:
        pos, _ = snap.positions(m)
    except Exception:
        continue
    if not pos or name not in lay.start: continue
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    w0, w1, h0, h1 = min(xs), max(xs), min(ys), max(ys)
    sx, sy = float(m.get('ScaleX', 1)), float(m.get('ScaleY', 1))
    d = m.get('DisplayAs')
    if d == 'Matrix': W, H = sx * (w1 - w0 + 1), sy * (h1 - h0 + 1)
    elif d == 'Custom': W, H = sx * float(m.get('CustomWidth', 1)), sy * float(m.get('CustomHeight', 1))
    elif d == 'Single Line' and len(pos) <= 10: W, H = 6, 40              # pixel sticks: short verticals
    elif d == 'Arches': W, H = 110, 55
    elif d == 'Single Line': W, H = sx * 100, 4
    else: W, H = max(sx * (w1 - w0 + 1), 4), max(sy * (h1 - h0 + 1), 4)
    cx, cy = float(m.get('WorldPosX', 0)), float(m.get('WorldPosY', 0))
    vertical_stick = d == 'Single Line' and len(pos) <= 10
    items.append((name, m, pos, (w0, w1, h0, h1), (cx, cy, W, H), vertical_stick))
X0 = min(c[0] - c[2] / 2 for *_, c, _ in items); X1 = max(c[0] + c[2] / 2 for *_, c, _ in items)
Y0 = min(c[1] - c[3] / 2 for *_, c, _ in items); Y1 = max(c[1] + c[3] / 2 for *_, c, _ in items)
S = (a.width - 20) / (X1 - X0); Hpx = int((Y1 - Y0) * S) + 40
rows = []
for t in a.at.split(','):
    t = float(t); fno = min(int(t * 1000 / fs.step), fs.frames - 1)
    im = Image.new('RGB', (a.width, Hpx), (0, 0, 0)); dr = ImageDraw.Draw(im)
    for name, m, pos, (w0, w1, h0, h1), (cx, cy, W, H), vs in items:
        base, stride, order = lay.start[name], lay.stride[name], lay.order[name]
        cols = snap.decode(fs, fno, base, stride, len(pos), order)
        for n, (px, py) in pos.items():
            if vs: fx, fy = 0.5, (n - 1) / max(len(pos) - 1, 1)            # stick: node 1 at the bottom
            else:
                fx = (px - w0) / max(w1 - w0, 1e-9) if w1 > w0 else 0.5
                fy = 1 - ((py - h0) / max(h1 - h0, 1e-9) if h1 > h0 else 0.5)   # snap y=0 is the top
            wx = cx - W / 2 + fx * W; wy = cy - H / 2 + fy * H
            x = 10 + (wx - X0) * S; y = Hpx - 20 - (wy - Y0) * S
            c = cols.get(n, (0, 0, 0)); c = c if max(c) > 8 else (28, 28, 28)
            r = 2 if max(c) > 8 else 1
            dr.rectangle([x - r, y - r, x + r, y + r], fill=c)
    dr.text((4, 2), f't={t:.2f}', fill=(255, 255, 0)); rows.append(im)
out = Image.new('RGB', (a.width, Hpx * len(rows)))
for i, r in enumerate(rows): out.paste(r, (0, i * Hpx))
out.save(a.out); print(a.out, out.size)
