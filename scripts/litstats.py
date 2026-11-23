"""How lit is each prop at given times in a saved render: lit nodes / all nodes, and the mean RGB of the lit ones.
Faster than pictures for "is anything happening on the arches here?", "how bright is the background really?".
Read-only. A model's dimming curve (layout) is already in the render; its controller Brightness is not.

usage: litstats.py <song.fseq> <t1,t2,...> <model1,model2,...>
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import snap
from fseq import FSEQ
from layout import Layout

fs = FSEQ(sys.argv[1]); lay = Layout(HERE.parent)
times = [float(x) for x in sys.argv[2].split(',')]; models = sys.argv[3].split(',')
els = {m: snap.model_element(HERE.parent, m)[0] for m in models}
counts = {m: snap.node_count(e) for m, e in els.items()}
print(f'{"t":>7} ' + ' '.join(f'{m[:14]:>22}' for m in models))
for t in times:
    fno = min(int(t * 1000 / fs.step), fs.frames - 1); row = []
    for m in models:
        px = snap.decode(fs, fno, lay.start[m], lay.stride[m], counts[m], lay.order[m]).values()
        lit = [p for p in px if max(p) > 8]
        mean = tuple(sum(c[i] for c in lit) // len(lit) for i in range(3)) if lit else (0, 0, 0)
        row.append(f'{len(lit):3d}/{counts[m]:<3d} {mean[0]:3d},{mean[1]:3d},{mean[2]:3d}')
    print(f'{t:7.1f} ' + ' '.join(f'{r:>22}' for r in row))
