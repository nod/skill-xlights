"""Shared building blocks for generating xLights .xsq sequences.

A Seq holds effects per element per layer (layer 0 = top). Helpers add common effects with settings strings
copied from real user sequences (xLights 2026.19 format). The show's own layout (group names, where props sit,
where the show folder lives on the machine running xLights) comes from show_config.py next to this file -
draft one with `layout_report.py --draft-config`.
"""
import csv, hashlib, json, os, re, sys
from pathlib import Path
from xml.sax.saxutils import quoteattr, escape

TOOLING = Path(__file__).resolve().parent
SHOW = Path(os.environ.get('XLIGHTS_SHOW', TOOLING.parent))     # the xLights show folder (tooling/ lives inside it)

# ---------------------------------------------------------------- the show's layout (show_config.py)
from show_config import *       # ELEMENTS, ALL, CANVAS, TRUNKS, ARCHES, FOREST, HOUSE, FLOODS, NON_MEMBERS, *_X ...
# effects that reference files (media, shaders) need the path as xLights sees it: the show folder on the machine
# that runs xLights. Override with XLIGHTS_MEDIA_ROOT; default is show_config's MEDIA_ROOT, else this folder.
MEDIA_ROOT = os.environ.get('XLIGHTS_MEDIA_ROOT') or globals().get('MEDIA_ROOT') or str(SHOW)

RED, GREEN, WHITE, GOLD, BLACK = '#FF0A1E', '#00E040', '#FFFFFF', '#FFAA00', '#000000'
DEEP_RED, AMBER, LIME = '#8C0010', '#FF6A00', '#9DFF3A'


class Grad:
    """A colour curve on a palette slot: colours blended over the effect's time (mode='time') or across the
    buffer ('right', 'left', 'up', 'down', 'radial-in', 'radial-out', 'cw', 'ccw').
    Grad(RED, GOLD, mode='up') spaces colours evenly; Grad((0, RED), (0.8, GOLD)) places them."""
    MODES = {'time': 0, 'right': 1, 'down': 2, 'left': 3, 'up': 4, 'radial-in': 5, 'radial-out': 6, 'cw': 7, 'ccw': 8}

    def __init__(self, *stops, mode='time'):
        if all(isinstance(x, str) for x in stops):
            stops = [(i / (len(stops) - 1), c) for i, c in enumerate(stops)]
        self.stops, self.mode = list(stops), mode

    def curve(self, slot):
        tc = self.MODES[self.mode]
        values = ';'.join(f'x={x:.3f}^c={c.lower()}' for x, c in self.stops)
        return f'Active=TRUE|Id=ID_BUTTON_Palette{slot}|' + (f'Timecurve={tc}|' if tc else '') + f'Values={values}|'

    def preview(self):
        return self.stops[len(self.stops) // 2][1]


def preview_color(c):
    return c.preview() if isinstance(c, Grad) else c

# line endpoints for Morph sweeps (x1, y1, x2, y2 in % of the buffer)
DIAG = {'up-right': ((0, 50, 50, 0), (50, 100, 100, 50)), 'up-left': ((100, 50, 50, 0), (50, 100, 0, 50)),
        'down-right': ((0, 50, 50, 100), (50, 0, 100, 50)), 'down-left': ((100, 50, 50, 100), (50, 0, 0, 50)),
        'right': ((0, 0, 0, 100), (100, 0, 100, 100)), 'left': ((100, 0, 100, 100), (0, 0, 0, 100)),
        'up': ((0, 0, 100, 0), (0, 100, 100, 100)), 'down': ((0, 100, 100, 100), (0, 0, 100, 0))}

q = lambda s: int(round(s * 40)) * 25          # seconds -> ms on the 25 ms frame grid
sub = lambda x1=0, y1=0, x2=100, y2=100: f'{x1:.2f}x{y1:.2f}x{x2:.2f}x{y2:.2f}'


def layout_x():
    """{model name: world X} from the show layout - left-to-right order of the props as seen from the street"""
    import xml.etree.ElementTree as ET
    models = ET.parse(SHOW / 'xlights_rgbeffects.xml').getroot().find('models')
    return {m.get('name'): float(m.get('WorldPosX', 0)) for m in models}


def song_dir(song):
    return TOOLING / 'songs' / song


def media_path(song, mp3):
    return f'{MEDIA_ROOT}/seqs/{song}/{mp3}'


NOTE_NAMES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def midi(name):
    """'F#4' -> 66"""
    m = re.match(r'([A-G]#?)(-?\d)$', name); return NOTE_NAMES[m.group(1)] + 12 * (int(m.group(2)) + 1)


def load_notes(path):
    """Basic Pitch note-event CSV -> sorted [(start, end, midi_pitch, velocity)]"""
    return sorted((float(r[0]), float(r[1]), int(r[2]), int(r[3])) for r in csv.reader(open(path))
                  if r and not r[0].startswith('start'))


def nxt(times, i, cap):
    """gap to the next event, capped"""
    return min(times[i + 1] - times[i], cap) if i + 1 < len(times) else cap


def pingpong(i, n):
    """0,1,..,n-1,n-2,..,1,0,1,.. — a light bouncing across n props"""
    k = i % (2 * n - 2); return k if k < n else 2 * n - 2 - k


def marks(points, labels=None, maxlen=None, end=None, per=0.5):
    """timing marks (label, start_ms, end_ms) from points in seconds; contiguous unless maxlen"""
    seen = {}
    for i, p in enumerate(points): seen.setdefault(q(p), labels[i] if labels else '')
    pts = sorted(seen); res = []
    for i, s in enumerate(pts):
        e = pts[i + 1] if i + 1 < len(pts) else q(end if end is not None else s / 1000 + (maxlen or per))
        if maxlen: e = min(e, s + q(maxlen))
        if e > s: res.append((seen[s], s, e))
    return res


HASHES = TOOLING / '.build_hashes.json'

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unchanged_since_build(path):
    """True if `path` is byte for byte what the builder last wrote (or recorded) there"""
    path = Path(path).resolve()
    known = json.loads(HASHES.read_text()) if HASHES.exists() else {}
    return path.exists() and known.get(str(path)) == _sha(path)


def check_overwrite(path, force=False):
    """True if it's safe to write `path`: it doesn't exist, it's unchanged since our last build, or force"""
    path = Path(path).resolve()
    if not path.exists() or force: return True
    if unchanged_since_build(path): return True
    print(f'NOT WRITING {path}: it changed since the last build (edited in xLights?).\n'
          f'Back it up or pass --force to overwrite.', file=sys.stderr)
    return False


def record_build(path):
    path = Path(path).resolve()
    known = json.loads(HASHES.read_text()) if HASHES.exists() else {}
    known[str(path)] = _sha(path)
    HASHES.write_text(json.dumps(known, indent=1))


def cli_args():
    """positional command-line arguments, ignoring --flags"""
    return [a for a in sys.argv[1:] if not a.startswith('--')]


class Seq:
    def __init__(self, elements, nlayers=3):
        self.elements, self.nlayers = elements, nlayers
        self.fx = {el: [[] for _ in range(nlayers)] for el in elements}
        self.palettes, self.effectdb, self.tracks = [], [], []

    # ------------------------------------------------------------ core
    @staticmethod
    def _idx(lst, s):
        if s not in lst: lst.append(s)
        return lst.index(s)

    @staticmethod
    def palette(colors, bright=100, sparkles=0):
        kv = {}
        for i, c in enumerate(colors):
            kv[f'C_BUTTON_Palette{i + 1}'] = c.curve(i + 1) if isinstance(c, Grad) else c
            kv[f'C_CHECKBOX_Palette{i + 1}'] = '1'
        if bright != 100: kv['C_SLIDER_Brightness'] = str(bright)
        if sparkles:
            kv['C_COLOURPICKERCTRL_SparklesColour'] = '#FFFFFF'; kv['C_SLIDER_SparkleFrequency'] = str(sparkles)
        return ','.join(f'{k}={v}' for k, v in sorted(kv.items()))

    def add(self, els, layer, name, start, end, settings, colors, bright=100, sparkles=0, prio=0, minlen=50):
        s, e = q(start), q(end)
        if e - s < minlen: e = s + minlen          # minlen=25 for frame-by-frame animation
        if layer < self.nlayers - 1 and 'T_CHOICE_LayerMethod' not in settings and settings.get('_blend', 'Max'):
            settings = dict(settings, T_CHOICE_LayerMethod=settings.get('_blend', 'Max'))
        settings = {k: v for k, v in settings.items() if k != '_blend'}
        sett = ','.join(f'{k}={v}' for k, v in sorted(settings.items()))
        for el in ([els] if isinstance(els, str) else els):
            self.fx[el][layer].append(dict(s=s, e=e, name=name, ref=self._idx(self.effectdb, sett),
                                           pal=self._idx(self.palettes, self.palette(colors, bright, sparkles)),
                                           prio=prio, colors=[preview_color(c) for c in colors], bright=bright))

    # ------------------------------------------------------------ effects
    def on(self, els, layer, start, end, color, a=100, b=100, bright=100, subbuf=None, blend='Max', perModel=False,
           sparkles=0, prio=0, minlen=50):
        st = {'E_TEXTCTRL_Eff_On_Start': a, 'E_TEXTCTRL_Eff_On_End': b, '_blend': blend}
        if subbuf: st['B_CUSTOM_SubBuffer'] = subbuf
        if perModel: st['B_CHOICE_BufferStyle'] = 'Per Model Default'
        self.add(els, layer, 'On', start, end, st, [color], bright, sparkles, prio, minlen)

    def flash(self, els, layer, t, dur, color, bright=100, subbuf=None, end_level=0, perModel=False, sparkles=0, prio=0):
        self.on(els, layer, t, t + dur, color, 100, end_level, bright, subbuf, perModel=perModel, sparkles=sparkles, prio=prio)

    def bars(self, els, layer, start, end, direction, colors, count=1, cycles=1, bright=100, perModel=False):
        st = {'E_CHECKBOX_Bars_3D': 0, 'E_CHECKBOX_Bars_Gradient': 0, 'E_CHECKBOX_Bars_Highlight': 0,
              'E_CHOICE_Bars_Direction': direction, 'E_SLIDER_Bars_BarCount': count, 'E_TEXTCTRL_Bars_Cycles': cycles}
        if perModel: st['B_CHOICE_BufferStyle'] = 'Per Model Default'
        self.add(els, layer, 'Bars', start, end, st, colors, bright)

    def morph(self, els, layer, start, end, colors, a, b, dur=100, tail_start=1, tail_end=30, bright=100, sparkles=0,
              extra=None):
        """line a=(x1,y1,x2,y2) travels to line b over `dur` % of the effect"""
        st = {'E_CHECKBOX_Morph_AutoRepeat': 0, 'E_CHECKBOX_Morph_End_Link': 0, 'E_CHECKBOX_Morph_Start_Link': 0,
              'E_CHECKBOX_ShowHeadAtStart': 0, 'E_NOTEBOOK_Morph': 'Start', 'E_SLIDER_MorphAccel': 0,
              'E_SLIDER_MorphDuration': dur, 'E_SLIDER_MorphStartLength': tail_start, 'E_SLIDER_MorphEndLength': tail_end,
              'E_SLIDER_Morph_Repeat_Count': 0, 'E_SLIDER_Morph_Repeat_Skip': 1, 'E_SLIDER_Morph_Stagger': 0,
              'E_SLIDER_Morph_Start_X1': a[0], 'E_SLIDER_Morph_Start_Y1': a[1], 'E_SLIDER_Morph_Start_X2': a[2],
              'E_SLIDER_Morph_Start_Y2': a[3], 'E_SLIDER_Morph_End_X1': b[0], 'E_SLIDER_Morph_End_Y1': b[1],
              'E_SLIDER_Morph_End_X2': b[2], 'E_SLIDER_Morph_End_Y2': b[3]}
        st.update(extra or {})
        self.add(els, layer, 'Morph', start, end, st, colors, bright, sparkles)

    def shockwave(self, els, layer, start, end, colors, sparkles=0, cx=50, cy=40, r_end=250, w_end=60, r_start=1,
                  w_start=10):
        """a ring growing from r_start to r_end (% of the buffer); r_start > r_end makes it collapse inward"""
        st = {'E_CHECKBOX_Shockwave_Blend_Edges': 1, 'E_CHECKBOX_Shockwave_Scale': 0, 'E_NOTEBOOK_Shockwave': 'Position',
              'E_SLIDER_Shockwave_Accel': 2, 'E_SLIDER_Shockwave_CenterX': cx, 'E_SLIDER_Shockwave_CenterY': cy,
              'E_SLIDER_Shockwave_End_Radius': r_end, 'E_SLIDER_Shockwave_End_Width': w_end,
              'E_SLIDER_Shockwave_Start_Radius': r_start, 'E_SLIDER_Shockwave_Start_Width': w_start}
        self.add(els, layer, 'Shockwave', start, end, st, colors, 100, sparkles)

    def pinwheel(self, els, layer, start, end, colors, arms=4, speed=12, twist=60, size=300, thickness=40, offset=0,
                 xc=0, yc=0, clockwise=True, fadein=0, style3d='None', bright=100):
        st = {'E_CHECKBOX_Pinwheel_Rotation': int(clockwise), 'E_CHOICE_Pinwheel_3D': style3d,
              'E_CHOICE_Pinwheel_Style': 'New Render Method', 'E_SLIDER_PinwheelXC': xc, 'E_SLIDER_PinwheelYC': yc,
              'E_SLIDER_Pinwheel_ArmSize': size, 'E_SLIDER_Pinwheel_Arms': arms, 'E_SLIDER_Pinwheel_Offset': offset,
              'E_SLIDER_Pinwheel_Speed': speed, 'E_SLIDER_Pinwheel_Thickness': thickness, 'E_SLIDER_Pinwheel_Twist': twist}
        if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
        self.add(els, layer, 'Pinwheel', start, end, st, colors, bright)

    def whirl(self, els, layer, start, end, colors, xc=-28, arms=6, thickness=32, twist=144):
        """the rotating wheel from DreamsOfFireflies: a 3D-shaded swirled pinwheel in four equal parts -
        slow, fast, then reversed slow, reversed fast (the swirl flips with the direction)"""
        seg = (end - start) / 4
        for k, (cw, speed) in enumerate(((False, 5), (False, 15), (True, 5), (True, 15))):
            self.pinwheel(els, layer, start + k * seg, start + (k + 1) * seg, colors, arms=arms, speed=speed,
                          twist=twist if not cw else -twist, size=100, thickness=thickness, xc=xc, clockwise=cw,
                          style3d='3D')

    def peppermint(self, els, layer, start, end, clockwise=True, bold=False, colors=('#D0D0D0', RED)):
        """the big spinning peppermint from punk-joy: white/red swirl arms across the buffer.
        bold=False: 8 thin swirled arms turning slowly; bold=True: 4 fat, heavily twisted arms turning fast"""
        if bold:
            self.pinwheel(els, layer, start, end, list(colors), arms=4, speed=14, twist=-133, size=37, thickness=100,
                          offset=51, xc=6, clockwise=clockwise)
        else:
            self.pinwheel(els, layer, start, end, list(colors), arms=8, speed=5, twist=74, size=100, thickness=0,
                          xc=6, clockwise=clockwise)

    def wave(self, els, layer, start, end, color, bright=100, waves=720, speed=20, direction='Left to Right',
             kind='Triangle', fill='Palette', thickness=25, height=70, colors=None, fadein=0):
        """Wave across the buffer. kind: Sine/Triangle/Square/Decaying Sine; fill: None draws just the line"""
        st = {'E_CHECKBOX_Mirror_Wave': 0, 'E_CHOICE_Fill_Colors': fill, 'E_CHOICE_Wave_Direction': direction,
              'E_CHOICE_Wave_Type': kind, 'E_SLIDER_Number_Waves': waves, 'E_SLIDER_Thickness_Percentage': thickness,
              'E_SLIDER_Wave_Height': height, 'E_SLIDER_Wave_YOffset': 0, 'E_TEXTCTRL_Wave_Speed': speed}
        if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
        self.add(els, layer, 'Wave', start, end, st, colors or [color], bright)

    def shader(self, els, layer, start, end, shader_path, params=None, bools=None, colors=(WHITE,), bright=100,
               speed=100, fadein=0, fadeout=0, overscan=True):
        """an ISF shader (.fs) from the show folder, e.g. 'Shaders/Sleepy Rays.fs'. `params` are the shader's float
        inputs in its own units (xLights stores them x100); `bools` its checkbox inputs. Rendered with OpenGL by
        xLights. `overscan` renders a little past the buffer edges so the props don't show the shader's border."""
        st = {'E_0FILEPICKERCTRL_IFS': f'{MEDIA_ROOT}/{shader_path}', 'E_SLIDER_Shader_Speed': speed,
              'E_TEXTCTRL_Shader_LeadIn': 0, 'E_TEXTCTRL_Shader_Offset_X': 0, 'E_TEXTCTRL_Shader_Offset_Y': 0,
              'E_TEXTCTRL_Shader_Zoom': 0}
        for k, v in (params or {}).items(): st[f'E_SLIDER_SHADERXYZZY_{k}'] = int(round(v * 100))
        for k, v in (bools or {}).items(): st[f'E_CHECKBOX_SHADERXYZZY_{k}'] = int(bool(v))
        if overscan: st['B_CUSTOM_SubBuffer'] = '-20.00x-20.00x120.00x120.00x0.00x0.00'
        if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
        if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
        self.add(els, layer, 'Shader', start, end, st, list(colors), bright)

    def fill(self, els, layer, start, end, colors, p_from=0, p_to=100, per_model=False, bright=100, fadeout=0,
             direction='Up'):
        """light fills the buffer from the bottom, its top edge moving smoothly from p_from to p_to %.
        per_model renders each model on its own in its real orientation (pixel sticks, tree trunks).
        direction='Down' hangs it from the top instead."""
        st = {'E_CHECKBOX_Fill_Color_Time': 0, 'E_CHECKBOX_Fill_Offset_In_Pixels': 1, 'E_CHECKBOX_Fill_Wrap': 0,
              'E_CHOICE_Fill_Direction': direction, 'E_SLIDER_Fill_Band_Size': 0, 'E_SLIDER_Fill_Offset': 0,
              'E_SLIDER_Fill_Skip_Size': 0,
              'E_VALUECURVE_Fill_Position': f'Active=TRUE|Id=ID_VALUECURVE_Fill_Position|Type=Ramp|Min=0.00|'
                                            f'Max=100.00|P1={p_from:.2f}|P2={p_to:.2f}|RV=TRUE|'}
        if per_model: st['B_CHOICE_BufferStyle'] = 'Per Model Per Preview'
        if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
        self.add(els, layer, 'Fill', start, end, st, colors, bright)

    def melody_scroll(self, el, notes, colors, travel, lo, hi, layers, bright=100):
        """each note (start, pitch, length[, colours, brightness]) becomes a dash at a height set by its pitch, gliding right to left
        across the whole canvas in `travel` seconds, so the tune draws itself across the wall. Notes are spread
        over the given layers (they overlap while crossing); a note with no free layer is skipped."""
        free = {L: -1.0 for L in layers}
        placed = 0
        for note in sorted(notes):
            t, p, d = note[:3]
            cols, br = (note[3], note[4]) if len(note) > 3 else (colors, bright)   # per-note colours/brightness
            L = next((L for L in layers if free[L] <= t), None)
            if L is None: continue
            y = 8 + (min(max(p, lo), hi) - lo) / (hi - lo) * 84
            tail = max(4, min(40, d / travel * 100))
            end = t + travel * (1 + tail / 100)
            self.morph(el, L, t, end, cols, (100, y, 100, y), (0, y, 0, y), dur=round(100 / (1 + tail / 100)),
                       tail_start=tail, tail_end=tail, bright=br)
            free[L] = end; placed += 1
        return placed

    def ripple(self, els, layer, t, dur, colors, cx, cy, radius=45, width=18):
        """a ring expanding from (cx, cy) % across the canvas - a hit you watch travel, not a panel flash"""
        self.shockwave(els, layer, t, t + dur, colors, cx=round(cx), cy=round(cy), r_end=radius, w_end=width)

    def trunk_ring(self, t, dur, color, tree=None, bright=100, layer=0):
        """a band of light racing up one of the TRUNKS matrices (index left to right; None = all of them)"""
        sb = None if tree is None else sub(max(TREE_X[tree] - 8, 0), 0, min(TREE_X[tree] + 8, 100), 100)
        st_extra = {'B_CUSTOM_SubBuffer': sb} if sb else {}
        a, b = DIAG['up']
        self.morph(TRUNKS, layer, t, t + dur, [WHITE, color], a, b, tail_start=10, tail_end=45, bright=bright,
                   extra=st_extra)

    def trunk_rise(self, t, dur, color, bright=100, layer=0):
        """every trunk fills from the roots up, then fades - the trunks' way of joining a big moment"""
        self.fill(TRUNKS, layer, t, t + dur, [Grad(color, WHITE, mode='up')], 0, 100, per_model=True,
                  bright=bright, fadeout=dur * 0.4)

    def bounce(self, els, layer, start, end, colors, height=100, bright=100, direction='Up'):
        """each model fills from the bottom to `height` % and drains back down over the effect - a drum hit.
        Uses Fill with a falling position curve, rendered per model in its real orientation (pixel sticks).
        direction='Down' hangs the light from the top of each model."""
        st = {'B_CHOICE_BufferStyle': 'Per Model Per Preview', 'E_CHECKBOX_Fill_Color_Time': 0,
              'E_CHECKBOX_Fill_Offset_In_Pixels': 1, 'E_CHECKBOX_Fill_Wrap': 0, 'E_CHOICE_Fill_Direction': direction,
              'E_SLIDER_Fill_Band_Size': 0, 'E_SLIDER_Fill_Offset': 0, 'E_SLIDER_Fill_Skip_Size': 0,
              'E_VALUECURVE_Fill_Position': f'Active=TRUE|Id=ID_VALUECURVE_Fill_Position|Type=Ramp|Min=0.00|'
                                            f'Max=100.00|P1={height:.2f}|P2=0.00|RV=TRUE|'}
        self.add(els, layer, 'Fill', start, end, st, colors, bright)

    def waveform(self, els, layer, start, end, colors, bars=6, bright=100):
        """VU Meter 'Waveform': the song's audio drawn across the buffer, rendered by xLights from the music"""
        st = {'E_CHOICE_VUMeter_Type': 'Waveform', 'E_SLIDER_VUMeter_Bars': bars, 'E_SLIDER_VUMeter_Gain': 0,
              'E_SLIDER_VUMeter_YOffset': 0, 'E_TEXTCTRL_VUMeter_Gain': 0}
        self.add(els, layer, 'VU Meter', start, end, st, colors, bright)

    def meteors(self, els, layer, start, end, colors, direction='Down', count=25, speed=12, sparkles=0, bright=100,
                perModel=False):
        st = {'E_CHECKBOX_Meteors_UseMusic': 0, 'E_CHOICE_Meteors_Effect': direction, 'E_CHOICE_Meteors_Type': 'Palette',
              'E_SLIDER_Meteors_Count': count, 'E_SLIDER_Meteors_Length': 30, 'E_SLIDER_Meteors_Speed': speed,
              'E_SLIDER_Meteors_Swirl_Intensity': 0}
        if perModel: st['B_CHOICE_BufferStyle'] = 'Per Model Per Preview'
        self.add(els, layer, 'Meteors', start, end, st, colors, bright, sparkles)

    def twinkle(self, els, layer, start, end, colors, count=40, steps=30, bright=100, subbuf=None):
        st = {'E_CHECKBOX_Twinkle_ReRandom': 0, 'E_CHECKBOX_Twinkle_Strobe': 0, 'E_CHOICE_Twinkle_Style': 'New Render Method',
              'E_SLIDER_Twinkle_Count': count, 'E_SLIDER_Twinkle_Steps': steps}
        if subbuf: st['B_CUSTOM_SubBuffer'] = subbuf
        self.add(els, layer, 'Twinkle', start, end, st, colors, bright)

    def butterfly(self, els, layer, start, end, colors, style=1, chunks=1, skip=2, speed=10, bright=100, subbuf=None,
                  fadein=0, fadeout=0):
        """Butterfly: a slowly churning plasma of the palette colours - water, caustics, aurora
        (settings as in the user's aggie-hymn2 / for_king_ocome)"""
        st = {'E_CHOICE_Butterfly_Colors': 'Palette', 'E_CHOICE_Butterfly_Direction': 'Normal',
              'E_SLIDER_Butterfly_Chunks': chunks, 'E_SLIDER_Butterfly_Skip': skip, 'E_SLIDER_Butterfly_Speed': speed,
              'E_SLIDER_Butterfly_Style': style}
        if subbuf: st['B_CUSTOM_SubBuffer'] = subbuf
        if fadein: st['T_TEXTCTRL_Fadein'] = f'{fadein:.2f}'
        if fadeout: st['T_TEXTCTRL_Fadeout'] = f'{fadeout:.2f}'
        self.add(els, layer, 'Butterfly', start, end, st, colors, bright)

    def bubbles(self, els, layer, start, end, colors, count=6, size=4, speed=8, bright=100, subbuf=None):
        """Circles in bubble mode: little rings drifting up through the buffer"""
        st = {'E_CHECKBOX_Circles_Bounce': 0, 'E_CHECKBOX_Circles_Bubbles': 1, 'E_CHECKBOX_Circles_Collide': 0,
              'E_CHECKBOX_Circles_Linear_Fade': 1, 'E_CHECKBOX_Circles_Plasma': 0, 'E_CHECKBOX_Circles_Radial': 0,
              'E_CHECKBOX_Circles_Radial_3D': 0, 'E_CHECKBOX_Circles_Random_m': 0, 'E_SLIDER_Circles_Count': count,
              'E_SLIDER_Circles_Size': size, 'E_SLIDER_Circles_Speed': speed}
        if subbuf: st['B_CUSTOM_SubBuffer'] = subbuf
        self.add(els, layer, 'Circles', start, end, st, colors, bright)

    def spirals(self, els, layer, start, end, colors, count=2, rotation=20, thickness=40, movement=2.0, bright=100,
                perModel=False, three_d=False, swing=False):
        """Spirals; swing=True makes the twist rock back and forth on a sine (DreamsOfFireflies)"""
        st = {'E_CHECKBOX_Spirals_3D': int(three_d), 'E_CHECKBOX_Spirals_Blend': 0, 'E_CHECKBOX_Spirals_Grow': 0,
              'E_CHECKBOX_Spirals_Shrink': 0, 'E_SLIDER_Spirals_Count': count, 'E_SLIDER_Spirals_Rotation': rotation,
              'E_SLIDER_Spirals_Thickness': thickness, 'E_TEXTCTRL_Spirals_Movement': movement}
        if swing:
            del st['E_SLIDER_Spirals_Rotation']
            st['E_VALUECURVE_Spirals_Rotation'] = ('Active=TRUE|Id=ID_VALUECURVE_Spirals_Rotation|Type=Sine|'
                                                   'Min=-300.00|Max=300.00|P2=47.00|P3=40.00|TO=75|RV=TRUE|')
        if perModel: st['B_CHOICE_BufferStyle'] = 'Per Model Default'
        self.add(els, layer, 'Spirals', start, end, st, colors, bright)

    def matrix_slice_flash(self, t, dur, color, k6, y1=0, y2=100, bright=100, layer=0):
        """light just canvas panel k6 (left to right) and the matching trunk, between heights y1..y2 %
        (an old helper: panel flashes are usually the wrong call - see the canvas rules in SKILL.md)"""
        vx, tx = VERT_X[k6], TREE_X[k6 * len(TREE_X) // len(VERT_X)]
        self.flash(CANVAS, layer, t, dur, color, bright=bright, subbuf=sub(max(vx - 8, 0), y1, min(vx + 8, 100), y2))
        self.flash(TRUNKS, layer, t, dur, color, bright=bright, subbuf=sub(max(tx - 8, 0), y1, min(tx + 8, 100), y2))

    def moment(self, a, b, draw, color, fade_to=0, fade_from=100):
        """a whole-yard moment (draw it on ALL): clear everything in [a, b), draw the yard-wide effect; the non-member props go
        along in `color`, from `fade_from` to `fade_to` % (a flash by default, a gentle ramp for slow moments)"""
        self.cut(q(a), q(b))
        draw(a, b)
        self.on([el for el in NON_MEMBERS if el != TRUNKS], 0, a, b, color, fade_from, fade_to)
        if TRUNKS in self.elements: self.trunk_rise(a, b - a, color, bright=max(fade_from, 40))

    # ------------------------------------------------------------ editing
    def cut(self, a_ms, b_ms, els=None, layers=None):
        """clear [a, b) on the given elements and layers (all by default), trimming/splitting effects that straddle it"""
        for el in (els or self.elements):
            for L in (layers if layers is not None else range(self.nlayers)):
                out = []
                for f in self.fx[el][L]:
                    if f['e'] <= a_ms or f['s'] >= b_ms: out.append(f); continue
                    if f['s'] < a_ms: out.append(dict(f, e=a_ms))
                    if f['e'] > b_ms: out.append(dict(f, s=b_ms))
                self.fx[el][L] = [f for f in out if f['e'] - f['s'] >= 25]

    def resolve(self):
        """make each layer non-overlapping: a later effect clips the one before it"""
        for el in self.elements:
            for L in range(self.nlayers):
                lst = sorted(self.fx[el][L], key=lambda x: (x['s'], -x['prio']))
                out = []
                for f in lst:
                    if out and f['s'] < out[-1]['e']:
                        if f['s'] == out[-1]['s']: continue
                        out[-1]['e'] = f['s']
                        if out[-1]['e'] - out[-1]['s'] < 25: out.pop()
                    out.append(f)
                self.fx[el][L] = out

    # ------------------------------------------------------------ output
    def write(self, path, head, dur, timeline=None, force=None):
        """write the .xsq; refuses to overwrite a file that changed since the last build (e.g. edited in
        xLights) unless --force is on the command line"""
        force = ('--force' in sys.argv) if force is None else force
        if not check_overwrite(path, force): sys.exit(2)
        self.resolve()
        last = q(dur)               # nothing may run past the end of the audio
        for el in self.elements:
            for L in range(self.nlayers):
                self.fx[el][L] = [dict(f, e=min(f['e'], last)) for f in self.fx[el][L] if f['s'] < last - 25]
        self.tracks = [(n, [(lab, s, min(e, last)) for lab, s, e in ms if s < last - 25]) for n, ms in self.tracks]
        L = []; w = L.append
        w('<?xml version="1.0"?>')
        w('<xsequence BaseChannel="0" ChanCtrlBasic="0" ChanCtrlColor="0" FixedPointTiming="1" ModelBlending="true">')
        w('  <head>')
        w('    <version>2026.19</version>')
        for tag in ('author', 'author-email', 'author-website'): w(f'    <{tag}></{tag}>')
        for tag in ('song', 'artist', 'album'): w(f'    <{tag}>{escape(head.get(tag, ""))}</{tag}>')
        w('    <MusicURL></MusicURL>')
        w(f'    <comment>{escape(head.get("comment", ""))}</comment>')
        w('    <sequenceTiming>25 ms</sequenceTiming>')
        w('    <sequenceType>Media</sequenceType>')
        w(f'    <mediaFile>{escape(head["media"])}</mediaFile>')
        w(f'    <sequenceDuration>{dur}</sequenceDuration>')
        w('    <imageDir></imageDir>')
        w('  </head>')
        w('  <ColorPalettes>')
        for p in self.palettes: w(f'    <ColorPalette>{escape(p)}</ColorPalette>')
        w('  </ColorPalettes>')
        w('  <EffectDB>')
        for s in self.effectdb: w(f'    <Effect>{escape(s)}</Effect>')
        w('  </EffectDB>')
        w('  <SequenceMedia />')
        w('  <DataLayers>')
        w('    <DataLayer lor_params="0" channel_offset="0" num_channels="0" num_frames="0" data="&lt;rendered: erase-mode>" source="&lt;auto-generated>" name="Nutcracker" />')
        w('  </DataLayers>')
        w('  <DisplayElements>')
        for i, (n, _) in enumerate(self.tracks):
            w(f'    <Element collapsed="false" type="timing" name={quoteattr(n)} visible="true" views="" active="{"true" if i == 0 else "false"}" />')
        for m in self.elements:
            w(f'    <Element collapsed="false" type="model" name={quoteattr(m)} visible="true" />')
        w('  </DisplayElements>')
        w('  <ElementEffects>')
        for n, ms in self.tracks:
            w(f'    <Element type="timing" name={quoteattr(n)}>')
            w('      <EffectLayer>')
            for lab, s, e in ms: w(f'        <Effect label={quoteattr(lab)} startTime="{s}" endTime="{e}" />')
            w('      </EffectLayer>')
            w('    </Element>')
        for m in self.elements:
            w(f'    <Element type="model" name={quoteattr(m)}>')
            layers = self.fx[m]
            while len(layers) > 1 and not layers[-1]: layers = layers[:-1]
            for lay in layers:
                if not lay: w('      <EffectLayer />'); continue
                w('      <EffectLayer>')
                for f in lay:
                    w(f'        <Effect ref="{f["ref"]}" name="{f["name"]}" startTime="{f["s"]}" endTime="{f["e"]}" palette="{f["pal"]}" />')
                w('      </EffectLayer>')
            w('    </Element>')
        w('  </ElementEffects>')
        w('  <lastView>0</lastView>')
        w('  <TimingTags>')
        for i in range(10): w(f'    <Tag number="{i}" position="-1" />')
        w('  </TimingTags>')
        w('</xsequence>')
        open(path, 'w').write('\n'.join(L) + '\n')
        record_build(path)
        total = sum(len(x) for el in self.elements for x in self.fx[el])
        print(f'effects: {total}  palettes: {len(self.palettes)}  effectdb: {len(self.effectdb)}')
        for el in self.elements: print(f'  {el:14}', [len(x) for x in self.fx[el]])
        if timeline:
            json.dump({el: [[dict(s=f['s'], e=f['e'], name=f['name'], colors=f['colors'], bright=f['bright']) for f in lay]
                            for lay in self.fx[el]] for el in self.elements}, open(timeline, 'w'))
