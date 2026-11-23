"""Several props side by side from a saved render, left to right as seen from the street (snap.py per model, tiled).
The matrix wall (show_config CANVAS) at a glance: does a word, a logo, a character land where it should?

usage: wall.py --fseq <song.fseq> --at <t>[,<t>...] [--models a,b,c] [--out wall.png] [--scale N] [--gain G]
Default models: the members of the CANVAS group, sorted by their X in the layout. Several times stack as rows.
"""
import argparse, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def canvas_members():
    from show_config import CANVAS
    root = ET.parse(HERE.parent / 'xlights_rgbeffects.xml').getroot()
    x = {m.get('name'): float(m.get('WorldPosX', 0)) for m in root.iter('model')}
    g = next(g for g in root.iter('modelGroup') if g.get('name') == CANVAS)
    return sorted((m for m in g.get('models', '').split(',') if m in x), key=x.get)


ap = argparse.ArgumentParser()
ap.add_argument('--fseq', required=True); ap.add_argument('--at', required=True)
ap.add_argument('--models', default=''); ap.add_argument('--out', default='wall.png')
ap.add_argument('--scale', default='6'); ap.add_argument('--gain', default='1')
a = ap.parse_args()
models = a.models.split(',') if a.models else canvas_members()
rows = []
with tempfile.TemporaryDirectory() as td:
    for t in a.at.split(','):
        tiles = []
        for m in models:
            p = Path(td) / f'{len(rows)}_{len(tiles)}.png'
            r = subprocess.run([sys.executable, str(HERE / 'snap.py'), '--fseq', a.fseq, '--model', m, '--at', t,
                                '--out', str(p), '--scale', a.scale, '--gain', a.gain], capture_output=True, text=True)
            if r.returncode: sys.exit(f'snap {m} @ {t}: {r.stderr or r.stdout}')
            tiles.append(Image.open(p).convert('RGB'))
        h = max(i.height for i in tiles); w = sum(i.width for i in tiles) + 8 * (len(tiles) - 1)
        row = Image.new('RGB', (w, h + 18), (0, 0, 0)); x = 0
        for i in tiles: row.paste(i, (x, 18)); x += i.width + 8
        ImageDraw.Draw(row).text((4, 2), f't={t}', fill=(255, 255, 0)); rows.append(row)
out = Image.new('RGB', (max(r.width for r in rows), sum(r.height for r in rows))); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(a.out); print(a.out, out.size)
