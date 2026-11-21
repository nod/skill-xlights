"""Drive the running xLights: open a sequence, render it, save it (the save is what writes the .fseq), close it.
Then read the render back with snap.py instead of asking the user what it looked like.
Read reference/pipeline.md, "Render, save, read back", before using this.

usage:  ./run xl.py status                        which show folder xLights has loaded, and what is open
        ./run xl.py open ../seqs/<song>/<name>.xsq
        ./run xl.py render                        ONE renderAll; nothing may touch the sequence while it runs
        ./run xl.py open <name>.xsq --ignore-xbkp  open although <name>.xbkp is newer (throws the autosave away)
        ./run xl.py save                          saveSequence (xLights 2026.17+), then wait for the .fseq to settle
        ./run xl.py close [--discard]             refuses while xLights reports unsaved changes, unless --discard
  with xl_mcp.py running on the xLights machine (XLIGHTS_MCP_URL and XLIGHTS_MCP_TOKEN set):
        ./run xl.py push <file>... [--force]      copy files into the show folder there (a sequence, its mp3)
        ./run xl.py pull <file>... [--force] [--out=<path>]   copy files back (the .fseq after a save)

Two ways to reach xLights. Both enforce the same rules (xlapi.py):
- Directly, through xLights' automation port: xLights -> Preferences -> Output -> API Port -> Port A (49913), or start
  xLights with -a. From another machine set XLIGHTS_HOST=<that machine> (and XLIGHTS_PORT=49914 for Port B); the
  port has no password, so the firewall must let in this machine only. Paths sent to xLights are rewritten from the
  show folder here (SHOW) to the show folder as xLights sees it (MEDIA_ROOT in show_config.py), and the .fseq and
  .xbkp checks read THIS machine's copy, so a synced folder has to have caught up first.
- Through xl_mcp.py, an MCP server run on the xLights machine: it talks to xLights on that machine only, needs a
  token, and gives an agent the same commands as MCP tools. Its files are not synced here, so `push` sends a build
  over and `pull` brings the .fseq back for snap.py.

A save rewrites the .xsq (times snap, strings normalise), so the builder would refuse the next build. When the .xsq
was the builder's own output before the save, `xl.py save` compares the two by content (xsq_compare.py) and, if they
draw the same effects, records the saved file as the build. Anything else (the user edited it in xLights) is left
for the builder to refuse. xl_mcp.py makes the same check when a push would replace a file there.

GPU rendering must be OFF in xLights (Preferences; `xLightsGPURendering`, ON by default): Metal shader effects hung
the machine under automation. The API cannot read the setting, so ask the user before the first render.
"""
import hashlib, json, os, shutil, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from seqlib import SHOW, MEDIA_ROOT, cli_args, unchanged_since_build, record_build
from xsq_compare import compare
from xlapi import XLights, Refused, settle

CACHE = Path(os.environ.get('XLIGHTS_TOOLING_CACHE', Path.home() / '.cache' / 'xlights-tooling'))


# ---------------------------------------------------------------- paths: this machine <-> the xLights machine
def there(p):
    """A path on this machine -> the same file as xLights sees it (SHOW -> MEDIA_ROOT)."""
    p = Path(p).resolve()
    try:
        rel = p.relative_to(SHOW.resolve())
    except ValueError:
        return str(p)                                   # outside the show folder: both machines must see it alike
    root = str(MEDIA_ROOT).rstrip('/\\')
    sep = '\\' if '\\' in root else '/'
    return root + sep + sep.join(rel.parts)


def here(p):
    """A path xLights reported -> the same file on this machine (MEDIA_ROOT -> SHOW)."""
    root = str(MEDIA_ROOT).replace('\\', '/').rstrip('/')
    s = str(p).replace('\\', '/').rstrip('/')
    if s == root or s.startswith(root + '/'):
        return SHOW / s[len(root):].lstrip('/')
    return Path(str(p))


XL = XLights(os.environ.get('XLIGHTS_HOST', '127.0.0.1'), os.environ.get('XLIGHTS_PORT', '49913'),
             show=MEDIA_ROOT, lock=CACHE / 'render.lock', there=there, here=here)


# ---------------------------------------------------------------- save, keeping the build record
def save():
    pre = CACHE / 'pre-save'
    kept = {}

    def keep_build(xsq):                                # keep the builder's version to compare against
        if xsq.exists() and unchanged_since_build(xsq):
            pre.mkdir(parents=True, exist_ok=True)
            shutil.copy2(xsq, pre / xsq.name)
            kept['mtime'] = xsq.stat().st_mtime

    report, xsq = XL.save(before_save=keep_build)
    print(report)
    if 'mtime' in kept:
        rebuild_record(xsq, pre / xsq.name, kept['mtime'])
    elif xsq.exists():
        print(f"{xsq.name} was not the builder's last output before this save (edited in xLights, or built "
              "elsewhere); its build record is left alone, so the builder will refuse to overwrite it.")


def rebuild_record(xsq, pre, xsq_before):
    """After a save of a file the builder wrote: record the saved file as the build if it draws the same effects."""
    _, _, note = settle(xsq, xsq_before, appear_s=15)
    if xsq.stat().st_mtime <= xsq_before:
        print(f"{xsq.name} on this machine has not changed yet ({note}); the build record is unchanged, so the next "
              "build will pass until the saved file syncs here and then refuse. Re-run `xl.py save` once it has synced.")
        return
    diffs = compare(pre, xsq)
    if not diffs:
        record_build(xsq)
        print(f"{xsq.name}: the save only normalised the file (same effects); recorded it as the build, so the "
              "builder can still overwrite it.")
    else:
        print(f"{xsq.name}: the saved file draws {len(diffs)} thing(s) differently from what the builder wrote, so "
              "xLights held edits (probably the user's). The builder will refuse to overwrite it; ask the user.")
        for d in diffs[:5]: print('  ' + d)


# ---------------------------------------------------------------- push / pull through xl_mcp.py
def server(method, rel, body=None, force=False):
    url = os.environ.get('XLIGHTS_MCP_URL', '').rstrip('/')
    token = os.environ.get('XLIGHTS_MCP_TOKEN', '')
    if not url or not token:
        raise Refused('push and pull need xl_mcp.py running on the xLights machine: set XLIGHTS_MCP_URL '
                      '(e.g. http://<that machine>:8765) and XLIGHTS_MCP_TOKEN (the server prints both).')
    q = '?force=1' if force else ''
    req = urllib.request.Request(f'{url}/files/{urllib.parse.quote(rel)}{q}', data=body, method=method,
                                 headers={'Authorization': f'Bearer {token}'})
    try:
        return urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        raise Refused(f'{method} {rel}: HTTP {e.code}: {e.read().decode(errors="replace").strip()}')
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise Refused(f'xl_mcp.py did not answer at {url} ({getattr(e, "reason", e)}). Is it running there?')


def show_relative(p):
    """A path here (../seqs/<song>/<name>.xsq from tooling/) -> its path inside the show folder."""
    try:
        return Path(p).resolve().relative_to(SHOW.resolve()).as_posix()
    except ValueError:
        raise Refused(f'{p}: not inside the show folder ({SHOW})')


def push(files, force=False):
    for f in files:
        p = Path(f)
        if not p.is_file():
            raise Refused(f'{f}: no such file here')
        rel = show_relative(p)
        with server('PUT', rel, p.read_bytes(), force) as r:
            print(json.loads(r.read()).get('report'))


def pull(files, force=False, out=None):
    if out and len(files) > 1:
        raise Refused('--out takes one file')
    for f in files:
        rel = show_relative(f)
        dest = Path(out) if out else SHOW / rel
        with server('GET', rel) as r:
            data = r.read()
        if dest.suffix == '.xsq' and dest.exists() and dest.read_bytes() != data and not force:
            raise Refused(f"NOT WRITING {dest}: it differs from the copy there, and a local .xsq is the builder's "
                          "file (its build record). Pull it with --out=<other path> to compare it "
                          "(xsq_compare.py), or --force.")
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + '.part')
        tmp.write_bytes(data)
        os.replace(tmp, dest)
        print(f'pulled {rel} -> {dest} ({len(data) / 1e6:.1f} MB, sha256 {hashlib.sha256(data).hexdigest()[:12]})')


def main():
    args = cli_args()
    cmd = args[0] if args else ''
    flags = {a.split('=', 1)[0]: (a.split('=', 1) + [''])[1] for a in sys.argv[1:] if a.startswith('--')}
    try:
        if cmd == 'status': print(XL.status())
        elif cmd == 'open' and len(args) == 2: print(XL.open(args[1], ignore_xbkp='--ignore-xbkp' in flags))
        elif cmd == 'render': print(XL.render())
        elif cmd == 'save': save()
        elif cmd == 'close': print(XL.close(discard='--discard' in flags))
        elif cmd == 'push' and len(args) > 1: push(args[1:], force='--force' in flags)
        elif cmd == 'pull' and len(args) > 1: pull(args[1:], force='--force' in flags, out=flags.get('--out'))
        else: sys.exit(__doc__.split('\n\n')[1])
    except Refused as e:
        sys.exit(str(e))


if __name__ == '__main__':
    main()
