"""Compare two .xsq files by what they draw, not by their bytes. Read-only.

usage: xsq_compare.py <a.xsq> <b.xsq> [--frame-ms=25] [--max=20]
       exit 0 when they draw the same effects, 1 when they differ (the differences are printed)

xLights rewrites the whole file on every Save (reference/xsq-format.md, "What an xLights Save does to the file"):
times snap to the frame grid, settings and palette strings are normalised, EffectDB and ColorPalettes are re-indexed.
So a hash cannot tell a plain Save from a hand edit. This compares, per element and layer (timing tracks included),
the list of (effect, start, end), with one frame of tolerance on the times, and then each paired effect's settings
and palette as key=value maps with every number compared as a number and every colour case-folded. What a save
also does is read as the same: a value-curve point of 0 left out, an empty setting written out, a file path
inside the show folder made relative, and an older file's E_FILEPICKER_<x>_Filename renamed E_TEXTCTRL_<x>_Filename.

It errs towards "different": a key that xLights adds or drops on save, a default it writes out, reads as a change.
That makes the builder refuse and an agent ask, which is the safe way to be wrong. The <head> (media, duration)
and the element order are not compared.
"""
import re, sys
import xml.etree.ElementTree as ET

NUM = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?')
HEX = re.compile(r'#[0-9a-fA-F]{6}\b')


def _norm_value(v):
    """Numbers to one spelling (1.50 -> 1.5, 7.0 -> 7), colours to upper case."""
    parts = HEX.split(v.strip())                       # numbers between the colours, never inside one
    colours = [c.upper() for c in HEX.findall(v.strip())]
    nums = [NUM.sub(lambda m: f'{round(float(m.group(0)), 4):g}', p) for p in parts]
    return ''.join(n + (colours[i] if i < len(colours) else '') for i, n in enumerate(nums))


CURVE_ZERO = re.compile(r'^P[1-4]=0$')


def _norm_curve(v):
    """A value curve (Active=TRUE|Id=...|Type=Ramp|P1=0|...): its fields sorted, a point of 0 dropped (a save omits it)."""
    return '|'.join(sorted(p for p in v.split('|') if p and not CURVE_ZERO.match(p)))


def _settings(s):
    """key=value pairs; an empty value counts as absent (a save writes some empty settings out)."""
    out = {}
    for part in (s or '').split(','):
        if not part.strip(): continue
        k, _, v = part.partition('=')
        v = _norm_value(v)
        if not v: continue
        k = k.strip()
        if k.startswith('E_FILEPICKER_'): k = 'E_TEXTCTRL_' + k[len('E_FILEPICKER_'):]   # a 2026 save renames these
        out[k] = _norm_curve(v) if v.startswith('Active=') and '|' in v else v
    return out


def _same(key, a, b):
    """Equal values, or one file path that is the other relative to the show folder (a save shortens paths inside
    it: /Users/you/show/Shaders/x.fs -> Shaders/x.fs)."""
    if a == b: return True
    if a is None or b is None or not ('FILEPICKER' in key or key.endswith('Filename')): return False
    a, b = a.replace('\\', '/'), b.replace('\\', '/')
    return a.endswith('/' + b) or b.endswith('/' + a)


def _layers(path):
    """{(element type, element name, sub-path, layer no): [(name or label, start, end, settings, palette), ...]}"""
    r = ET.parse(path).getroot()
    db = [e.text or '' for e in (r.find('EffectDB') if r.find('EffectDB') is not None else [])]
    pals = [e.text or '' for e in (r.find('ColorPalettes') if r.find('ColorPalettes') is not None else [])]
    out = {}
    ee = r.find('ElementEffects')
    for el in (ee if ee is not None else []):
        def walk(node, sub):
            counts = {}
            for child in node:
                if child.tag == 'Effect': continue
                n = counts[child.tag] = counts.get(child.tag, -1) + 1
                ident = child.get('name') or child.get('index') or ''
                here_ = sub + ((child.tag, ident, n),)
                effects = []
                for e in child.findall('Effect'):
                    ref, pal = e.get('ref'), e.get('palette')
                    settings = db[int(ref)] if ref is not None and ref.isdigit() and int(ref) < len(db) else (e.text or '')
                    palette = pals[int(pal)] if pal is not None and pal.isdigit() and int(pal) < len(pals) else ''
                    effects.append((e.get('name') or e.get('label') or '', int(float(e.get('startTime', 0))),
                                    int(float(e.get('endTime', 0))), _settings(settings), _settings(palette)))
                if effects:
                    out[(el.get('type'), el.get('name'), here_)] = sorted(effects, key=lambda f: (f[1], f[2], f[0]))
                walk(child, here_)
        walk(el, ())
    return out


def _where(key):
    typ, name, sub = key
    path = '/'.join(f'{t}[{i or n}]' if t != 'EffectLayer' else f'layer {n}' for t, i, n in sub)
    return f'{typ} {name!r} {path}'


def _dict_diff(a, b):
    keys = sorted(set(a) | set(b))
    return [f'{k}: {a.get(k, "(none)")} -> {b.get(k, "(none)")}' for k in keys if not _same(k, a.get(k), b.get(k))]


def compare(a_path, b_path, frame_ms=25):
    """A list of human-readable differences; empty when the two files draw the same effects."""
    A, B = _layers(a_path), _layers(b_path)
    diffs = []
    for key in sorted(set(A) | set(B), key=str):
        ea, eb = A.get(key, []), B.get(key, [])
        if len(ea) != len(eb):
            diffs.append(f'{_where(key)}: {len(ea)} effects -> {len(eb)}')
            continue
        for fa, fb in zip(ea, eb):
            tag = f'{_where(key)}: {fa[0]} at {fa[1]} ms'
            if fa[0] != fb[0] or abs(fa[1] - fb[1]) > frame_ms or abs(fa[2] - fb[2]) > frame_ms:
                diffs.append(f'{tag}: {fa[0]} {fa[1]}-{fa[2]} -> {fb[0]} {fb[1]}-{fb[2]}')
                continue
            for what, da, dbb in (('settings', fa[3], fb[3]), ('palette', fa[4], fb[4])):
                d = _dict_diff(da, dbb)
                if d: diffs.append(f'{tag}: {what} ' + '; '.join(d[:3]) + (f' (+{len(d) - 3} more)' if len(d) > 3 else ''))
    return diffs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2: sys.exit(__doc__.split('\n\n')[1])
    opt = dict(a[2:].split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    diffs = compare(args[0], args[1], int(opt.get('frame-ms', 25)))
    if not diffs:
        print('same effects (times within one frame, settings and palettes equal)')
        return 0
    n = int(opt.get('max', 20))
    print(f'{len(diffs)} difference(s):')
    for d in diffs[:n]: print('  ' + d)
    if len(diffs) > n: print(f'  ... {len(diffs) - n} more (--max=N)')
    return 1


if __name__ == '__main__':
    sys.exit(main())
