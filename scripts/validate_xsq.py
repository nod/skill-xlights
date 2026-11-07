"""Sanity-check a generated .xsq against the show layout.

usage: validate_xsq.py <file.xsq> [...]
Checks: every model/group exists in xlights_rgbeffects.xml, every row in <ElementEffects> is also listed in
<DisplayElements> (xLights silently drops a row the view list does not know, so its effects never render), effects
within a layer don't overlap, times sit on the 25 ms frame grid and inside the sequence, palette/EffectDB references
resolve. Exit code 1 on any problem. Also NOTES, which do not fail the file: an effect that holds Shimmer on for
2.5 s or longer (shimmer is flicker; a bed is calm; look at it in the render before keeping it).
"""
import sys, re, collections
import xml.etree.ElementTree as ET
from seqlib import SHOW, cli_args

layout = ET.parse(SHOW / 'xlights_rgbeffects.xml').getroot()
names = {m.get('name') for m in layout.find('models')} | {g.get('name') for g in layout.find('modelGroups')}
failed = False
for path in cli_args():
    r = ET.parse(path).getroot()
    npal, ndb = len(r.find('ColorPalettes')), len(r.find('EffectDB'))
    db = [e.text or '' for e in r.find('EffectDB')]
    view = {(e.get('type'), e.get('name')) for e in r.find('DisplayElements')}
    dur = float(r.find('head/sequenceDuration').text) * 1000
    problems, notes, kinds = [], [], collections.Counter()
    for el in r.find('ElementEffects'):
        n = el.get('name')
        if el.get('type') == 'model' and n not in names: problems.append(f'unknown model/group {n!r}')
        if (el.get('type'), n) not in view: problems.append(f'{el.get("type")} {n!r} is in ElementEffects but not DisplayElements: xLights drops it')
        for li, L in enumerate(el.findall('EffectLayer')):
            prev = -1
            for e in L.findall('Effect'):
                s, t = int(e.get('startTime')), int(e.get('endTime'))
                if s % 25 or t % 25: problems.append(f'{n} L{li}: {s}-{t} off the 25 ms grid')
                if t <= s or t > dur + 25: problems.append(f'{n} L{li}: bad span {s}-{t}')
                if s < prev: problems.append(f'{n} L{li}: {s} overlaps previous effect ending {prev}')
                prev = t
                if e.get('ref') is not None and not 0 <= int(e.get('ref')) < ndb: problems.append(f'{n}: bad ref')
                if e.get('palette') is not None and not 0 <= int(e.get('palette')) < npal: problems.append(f'{n}: bad palette')
                ref = e.get('ref')
                if ref is not None and 0 <= int(ref) < ndb and t - s >= 2500 and re.search(r'_Shimmer=1(,|$)', db[int(ref)]):
                    notes.append(f'{n} L{li}: {e.get("name")} at {s} holds Shimmer for {(t-s)/1000:g} s (shimmer is flicker; a bed is calm)')
                if el.get('type') == 'model': kinds[e.get('name')] += 1
    print(f'{path}: {sum(kinds.values())} effects {dict(kinds.most_common())}')
    for p in problems[:20]: print('  PROBLEM', p)
    for p in notes[:20]: print('  NOTE', p)
    print(f'  {len(problems)} problems' + (f', {len(notes)} notes' if notes else ''))
    failed |= bool(problems)
sys.exit(1 if failed else 0)
