"""Line up a video of the real show (or an xLights export) with the sequence that played: frames labelled with every
effect running at that moment, so you can see how an effect, a colour or a brightness actually looks on a prop.

usage: footage.py <xsq> <video> <out.png> [times ...] [--offset=0] [--cols=3] [--crop=x,y,w,h] [--model=substr]
       footage.py <xsq> <video> --sync
       footage.py <xsq> <video> <out.png> --map
  times     seconds into the song (default: one frame every 10 s); 'a-b/n' = n frames evenly from a to b
  --offset  song time = video time - offset (find it with --sync, which cross-correlates the video's audio
            with the sequence's mp3; a dubbed-in soundtrack lines up to a few ms)
  --map     one heat map per element: where in the frame it lights up. Its peak r also tells whether the video
            shows this version of the sequence at all (a prop that's often on alone: ~0.9 when it does, ~0.2-0.4 when not)
  --model   only list effects on elements whose name contains this
  --crop    crop each frame (pixels of the source video) to zoom in on a prop

  ./run footage.py ../Sequences/x/x.xsq ../Sequences/x/x.mp4 /tmp/x.png --sync
  ./run footage.py ../Sequences/x/x.xsq ../Sequences/x/x.mp4 /tmp/x.png 12 40.5 60-70/6
"""
import re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = {a[2:].split('=')[0]: (a.split('=', 1)[1] if '=' in a else '1') for a in sys.argv[1:] if a.startswith('--')}
xsq, video, out = (args + [None])[:3]
root = ET.parse(xsq).getroot()
db = [e.text or '' for e in root.find('EffectDB')]
pals = [e.text or '' for e in root.find('ColorPalettes')]
dur = float(root.find('head/sequenceDuration').text)


def sync():
    import numpy as np, librosa
    mp3 = root.find('head/mediaFile').text.replace('\\', '/').split('/')[-1]
    mp3 = next(Path(xsq).parent.glob(mp3), None) or next(Path(xsq).parent.glob('*.mp3'))
    sr, hop = 11025, 128
    env = []
    for f in (video, mp3):
        y, _ = librosa.load(str(f), sr=sr, mono=True)
        o = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        env.append((o - o.mean()) / o.std())
    c = np.correlate(env[0], env[1], 'full')
    lag = (np.argmax(c) - len(env[1]) + 1) * hop / sr
    print(f'--offset={lag:.3f}  (match {c.max() / len(env[1]):.2f}; ~1.0 = same audio)')


def footprint():
    """correlate each element's 'has an effect' timeline with every cell's brightness: where it is in the frame,
    and (peak r) whether the video really shows this version of the sequence (~0.9 yes, ~0.2 no)"""
    import numpy as np
    fps, w, h = 4, 192, 108
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', f'fps={fps},scale={w}:{h}', '-f', 'rawvideo',
                          '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    lum = v.max(axis=3).reshape(-1, h // 2, 2, w // 2, 2).max(axis=(2, 4)).astype(np.float32)
    t = np.arange(len(lum)) / fps - offset
    L = (lum - lum.mean(0)) / (lum.std(0) + 1e-6)
    bg = Image.fromarray(v.max(axis=0)).convert('L').resize((w * 2, h * 2)).convert('RGB')
    tiles = []
    for el in root.find('ElementEffects'):
        if el.get('type') == 'timing':
            continue
        on = np.zeros(len(t))
        for e in el.iter('Effect'):
            if e.get('name') != 'Off':
                on[(t >= int(e.get('startTime')) / 1000) & (t < int(e.get('endTime')) / 1000)] = 1
        if on.sum() < 8:
            continue
        c = np.einsum('t,tij->ij', (on - on.mean()) / on.std(), L) / len(t)
        hot = Image.fromarray((np.clip(c, 0, 0.6) / 0.6 * 255).astype(np.uint8)).resize(bg.size, Image.NEAREST)
        tile = Image.blend(bg, Image.merge('RGB', (hot, hot.point(lambda x: x // 3), Image.new('L', bg.size, 0))), 0.7)
        ImageDraw.Draw(tile).text((4, 4), f"{el.get('name')}  on {on.mean():.0%}  peak r={c.max():.2f}", fill='yellow')
        tiles.append(tile)
        print(f"  {el.get('name'):30} on {on.mean():4.0%}  peak r={c.max():.2f}")
    return tiles


if 'sync' in opts:
    sync()
    sys.exit()
offset = float(opts.get('offset', 0))
if 'map' in opts:
    tiles = footprint()
    cols = int(opts.get('cols', 4))
    w, h = tiles[0].size
    sheet = Image.new('RGB', (w * cols, h * ((len(tiles) + cols - 1) // cols)))
    for i, t in enumerate(tiles):
        sheet.paste(t, (w * (i % cols), h * (i // cols)))
    sheet.save(out)
    print('wrote', out)
    sys.exit()

times = []
for a in args[3:]:
    m = re.fullmatch(r'([\d.]+)-([\d.]+)/(\d+)', a)
    times += [float(m[1]) + (float(m[2]) - float(m[1])) * i / max(int(m[3]) - 1, 1) for i in range(int(m[3]))] if m \
        else [float(a)]
times = times or [float(t) for t in range(5, int(dur), 10)]


def colours(p):
    return [v for k, v in re.findall(r'C_BUTTON_Palette(\d+)=(#[0-9A-Fa-f]{6})', pals[p] if p < len(pals) else '')
            if f'C_CHECKBOX_Palette{k}=1' in pals[p]]


def active(t):
    ms = t * 1000
    rows = []
    for el in root.find('ElementEffects'):
        if el.get('type') == 'timing' or opts.get('model', '') not in el.get('name'):
            continue
        layers = [(f'L{i}', l) for i, l in enumerate(el.findall('EffectLayer'))]
        for sub in el.findall('SubModelEffectLayer') + el.findall('Strand'):
            layers.append((sub.get('name') or f"s{sub.get('index')}", sub))
        for ln, l in layers:
            for e in l.iter('Effect'):
                if int(e.get('startTime')) <= ms < int(e.get('endTime')):
                    s = db[int(e.get('ref', 0))] if e.get('ref') else ''
                    b = re.search(r'C_SLIDER_Brightness=(\d+)', pals[int(e.get('palette', -1))] if e.get('palette') else '')
                    extra = ' '.join(f'{k.split("_", 2)[-1]}={v}' for k, v in re.findall(r'(E_CHOICE_[^=]+)=([^,]+)', s))[:60]
                    rows.append(f"{el.get('name')[:22]} {ln}: {e.get('name')} {'/'.join(colours(int(e.get('palette', 0))))}"
                                f"{' br' + b[1] if b else ''} {extra}")
    return rows


font = ImageFont.load_default(size=14)
crop = [int(v) for v in opts['crop'].split(',')] if 'crop' in opts else None
tiles = []
with tempfile.TemporaryDirectory() as tmp:
    for i, t in enumerate(times):
        f = f'{tmp}/{i}.png'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t + offset:.3f}', '-i', video, '-frames:v', '1', f],
                       check=True)
        im = Image.open(f).convert('RGB')
        if crop:
            im = im.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
        im.thumbnail((640, 640))
        rows = active(t)
        print(f'--- {t:.2f}s')
        print('\n'.join('  ' + r for r in rows) or '  (nothing)')
        lines = [f'{t:.2f}s'] + rows[:14] + ([f'... +{len(rows) - 14}'] if len(rows) > 14 else [])
        tile = Image.new('RGB', (im.width, im.height + 17 * len(lines) + 6), 'black')
        tile.paste(im, (0, 0))
        d = ImageDraw.Draw(tile)
        for j, line in enumerate(lines):
            d.text((4, im.height + 3 + 17 * j), line, fill='white' if j else 'yellow', font=font)
        tiles.append(tile)
cols = int(opts.get('cols', 3))
w, h = max(t.width for t in tiles), max(t.height for t in tiles)
sheet = Image.new('RGB', (w * min(cols, len(tiles)), h * ((len(tiles) + cols - 1) // cols)), 'black')
for i, t in enumerate(tiles):
    sheet.paste(t, (w * (i % cols), h * (i // cols)))
sheet.save(out)
print('wrote', out)
