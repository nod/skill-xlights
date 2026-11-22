# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=2,<3"]
# ///
"""An MCP server that lets an agent on another machine drive xLights, run on the machine where xLights runs.

It talks to xLights on this machine only (127.0.0.1), with the rules of xl.py (xlapi.py: one render at a time, never
discard unsaved edits, never open over a newer autosave, never work across show folders), and asks every caller for
a token. MCP tools: status, open_sequence, render, save, close, list_files. Files go over plain HTTP beside it,
because a sequence is too big to pass as a tool argument: `xl.py push` (PUT /files/<path>) puts a build into the show
folder here, and `xl.py pull` (GET /files/<path>) takes the .fseq back for snap.py.

A push never replaces a file the user changed here: it refuses unless the file is still what the server last pushed,
or an .xsq that an xLights save only normalised (xsq_compare.py: the same effects). It refuses the sequence xLights
has open, and an .xsq whose autosave is newer. force=1 replaces anyway, and every replaced file is backed up first.
Only sequence, audio, video, image and shader files can be pushed; the layout is never written.

usage (on the xLights machine, next to xlapi.py and xsq_compare.py):
    uv run xl_mcp.py [--show=<show folder>] [--port=8765] [--host=0.0.0.0]
or  python3 -m venv ~/.venvs/xl-mcp && ~/.venvs/xl-mcp/bin/pip install 'mcp>=2,<3'
    ~/.venvs/xl-mcp/bin/python xl_mcp.py ...
The show folder defaults to the one xLights has loaded. On start it prints the token and the lines to give the agent.
xLights needs its API port on (Preferences -> Output -> API Port -> Port A, 49913) and GPU rendering off.
"""
import argparse, functools, hashlib, hmac, os, secrets, shutil, socket, sys, threading, time
from pathlib import Path

import anyio, uvicorn
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from xlapi import XLights, Refused, NoAnswer, newer_autosave
from xsq_compare import compare

PUSHABLE = {'.xsq', '.mp3', '.m4a', '.wav', '.ogg', '.flac', '.mp4', '.mov', '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.fs', '.glsl', '.xtiming'}
SHOW = STATE = XL = None                               # set in main()


# Bump on every change an agent could notice: MINOR for a new tool, parameter or route, MAJOR for one removed or
# changed incompatibly, PATCH for a fix. `status`, the MCP handshake, the startup line and --version report it.
#   0.1.0  status, open_sequence, render, save, close, list_files; GET/PUT /files; push guard (xsq_compare)
#   0.1.1  fix: a push path with '..' could put the server's bookkeeping copy outside its folders; list_files
#          patterns could list files outside the show folder
#   0.1.2  fix: render refuses when no sequence is open (xLights blocks on a dialog otherwise)
VERSION = '0.1.2'
mcp = MCPServer('xlights', version=VERSION, instructions=(
    'Drives the xLights on the machine this server runs on, with safety rules (one render at a time, never discard '
    'unsaved edits). Use it only when the user has said you may drive their xLights, and not while they are working '
    'in it. Paths are relative to the show folder (seqs/<song>/<name>.xsq). Send a build over first with '
    '`xl.py push`, then open_sequence, render, save, and `xl.py pull` the .fseq for snap.py; close when done. GPU '
    'rendering must be off in xLights: ask the user before the first render.'))


# ---------------------------------------------------------------- one command at a time
BUSY, DOING = threading.Lock(), ['']


def one_at_a_time(what, fn):
    if not BUSY.acquire(blocking=False):
        raise Refused(f'busy: {DOING[0]}. One command at a time; try again when it returns.')
    DOING[0] = f'{what} (since {time.strftime("%H:%M:%S")})'
    try:
        return fn()
    finally:
        BUSY.release()


def local(rel):
    """A show-relative path -> the file in the show folder. Refuses anything outside it, and hidden files."""
    root = SHOW.resolve()
    p = (root / rel).resolve()
    if not p.is_relative_to(root) or p == root:
        raise Refused(f'{rel}: not inside the show folder ({SHOW})')
    if any(part.startswith('.') for part in p.relative_to(root).parts):
        raise Refused(f'{rel}: hidden files are not served')
    return p


def rel_of(p):
    return Path(p).resolve().relative_to(SHOW.resolve()).as_posix()


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------- tools
def tool(fn):
    """An MCP tool whose refusals reach the caller with their reason (other exceptions show only the tool name)."""
    @functools.wraps(fn)
    def run(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Refused as e:
            raise ToolError(str(e)) from None
    return mcp.tool()(run)


@tool
def status() -> str:
    """Which show folder xLights has loaded, what sequence is open, and whether a command is running."""
    if BUSY.locked():
        return f'xl_mcp {VERSION}\nbusy: {DOING[0]}'
    return f'xl_mcp {VERSION}\n' + one_at_a_time('status', XL.status)


@tool
def open_sequence(path: str, ignore_xbkp: bool = False) -> str:
    """Open a sequence, e.g. seqs/<song>/<name>.xsq. Closes the open one first, but refuses if it has unsaved
    changes. Refuses if <name>.xbkp (autosave) is newer, unless ignore_xbkp (that throws the autosave away)."""
    return one_at_a_time(f'open {path}', lambda: XL.open(local(path), ignore_xbkp))


@tool
def render() -> str:
    """Render the open sequence (renderAll). Takes minutes; nothing else runs meanwhile. Save afterwards: the
    render is not written to the .fseq until a save."""
    return one_at_a_time('render', XL.render)


@tool
def save() -> str:
    """Save the open sequence, which writes its .fseq, and wait until the .fseq stops growing."""
    def run():
        report, xsq = XL.save()
        return f"{report}\nfetch the render with: xl.py pull ../{rel_of(xsq.with_suffix('.fseq'))}"
    return one_at_a_time('save', run)


@tool
def close(discard: bool = False) -> str:
    """Close the open sequence. Refuses while it has unsaved changes, unless discard (they are lost: ask first)."""
    return one_at_a_time('close', lambda: XL.close(discard))


@tool
def list_files(pattern: str = 'seqs/**/*.xsq') -> str:
    """Files in the show folder matching a glob, with size and modification time (at most 200)."""
    if Path(pattern).is_absolute() or '..' in Path(pattern).parts:
        raise Refused(f'{pattern}: a pattern must stay inside the show folder (no "..", not absolute)')
    root, lines = SHOW.resolve(), []
    for p in sorted(SHOW.glob(pattern)):
        r = p.resolve()                                 # a symlink may point out of the show folder
        if p.is_file() and r.is_relative_to(root) and not any(s.startswith('.') for s in r.relative_to(root).parts):
            st = p.stat()
            lines.append(f"{rel_of(p)}  {st.st_size / 1e6:.2f} MB  "
                         f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))}")
    return '\n'.join(lines[:200] + ([f'... and {len(lines) - 200} more'] if len(lines) > 200 else [])) or 'no match'


# ---------------------------------------------------------------- files
def changed_here(p, rel):
    """'' if `p` is still what this server last pushed (or an xLights save of it that draws the same effects);
    otherwise why it must not be replaced."""
    last = STATE / 'pushed' / rel
    if not last.exists():
        return 'it is already here and did not come from a push (pull it and compare first)'
    if sha(last) == sha(p):
        return ''
    if p.suffix == '.xsq':
        diffs = compare(last, p)
        if not diffs:
            return ''                                   # an xLights save: same effects, normalised file
        return (f'it changed here since the last push and draws {len(diffs)} thing(s) differently (edited in '
                f'xLights?), e.g. {diffs[0]}')
    return 'it changed here since the last push'


def accept(p, rel, upload, force):
    if p.suffix.lower() not in PUSHABLE:
        raise Refused(f'{rel}: only {" ".join(sorted(PUSHABLE))} files can be pushed')
    try:
        open_now = XL.open_sequence().get('fullseq')
    except NoAnswer:
        open_now = ''                                   # xLights is not running: nothing is open
    if open_now and Path(open_now).resolve() == p:
        raise Refused(f'NOT REPLACING {rel}: xLights has it open, and its next save would overwrite the push. '
                      'Close it first.')
    kept = STATE / 'pushed' / rel
    if p.exists() and sha(p) == sha(upload):
        report = f'{rel}: already here, unchanged'
    else:
        backup = None
        if p.exists():
            why = changed_here(p, rel) or (newer_autosave(p) if p.suffix == '.xsq' else '')
            if why and not force:
                raise Refused(f'NOT REPLACING {rel}: {why}. Ask the user; force=1 replaces it (a backup is kept).')
            backup = STATE / 'replaced' / time.strftime('%Y%m%d-%H%M%S') / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, backup)
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(upload, p)
        report = f'pushed {rel} ({p.stat().st_size / 1e6:.2f} MB)' + (f'; the old one is in {backup}' if backup else '')
    kept.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(p, kept)
    return report


@mcp.custom_route('/files/{rel:path}', methods=['GET', 'PUT'])
async def files(request):
    rel = request.path_params['rel']
    upload = None
    try:
        p = local(rel)
        rel = rel_of(p)                                 # the checked path, with no '..': state copies use it too
        if request.method == 'GET':
            return FileResponse(p) if p.is_file() else PlainTextResponse(f'{rel}: no such file', status_code=404)
        incoming = STATE / 'incoming'
        incoming.mkdir(parents=True, exist_ok=True)
        upload = incoming / secrets.token_hex(8)
        with open(upload, 'wb') as f:
            async for chunk in request.stream():
                f.write(chunk)
        force = request.query_params.get('force') == '1'
        report = await anyio.to_thread.run_sync(
            lambda: one_at_a_time(f'push {rel}', lambda: accept(p, rel, upload, force)))
        return JSONResponse({'report': report})
    except Refused as e:
        return PlainTextResponse(str(e), status_code=409)
    finally:
        if upload is not None:
            upload.unlink(missing_ok=True)


# ---------------------------------------------------------------- start
def require_token(app, token):
    """Every request (MCP and files) must carry Authorization: Bearer <token>."""
    want = f'Bearer {token}'.encode()

    async def guarded(scope, receive, send):
        if scope['type'] == 'http' and not hmac.compare_digest(dict(scope['headers']).get(b'authorization', b''),
                                                               want):
            return await PlainTextResponse('missing or wrong token', status_code=401)(scope, receive, send)
        return await app(scope, receive, send)
    return guarded


def lan_address():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(('192.0.2.1', 9))                # sends nothing; picks the interface a LAN route would use
            return s.getsockname()[0]
        except OSError:
            return socket.gethostname()


def main():
    global SHOW, STATE, XL
    cache = Path(os.environ.get('XLIGHTS_TOOLING_CACHE', Path.home() / '.cache' / 'xlights-tooling'))
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], allow_abbrev=False)
    ap.add_argument('--show', default=os.environ.get('XLIGHTS_SHOW', ''),
                    help="the show folder (default: the one xLights has loaded)")
    ap.add_argument('--host', default='0.0.0.0', help='interface to listen on (default: all)')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--xlights-port', type=int, default=int(os.environ.get('XLIGHTS_PORT', '49913')))
    ap.add_argument('--state', type=Path, default=cache / 'mcp', help=f'token, pushes, backups (default {cache}/mcp)')
    ap.add_argument('--version', action='version', version=f'xl_mcp {VERSION}')
    a = ap.parse_args()

    STATE = a.state
    STATE.mkdir(parents=True, exist_ok=True)
    XL = XLights('127.0.0.1', a.xlights_port, show=a.show, lock=cache / 'render.lock')   # xl.py's lock, too
    if not a.show:
        try:
            XL.show = XL.show_folder()
        except Refused as e:
            sys.exit(f'{e}\nStart xLights first, or pass --show=<show folder>.')
    SHOW = Path(XL.show)
    if not SHOW.is_dir():
        sys.exit(f'{SHOW}: no such folder')

    tf = STATE / 'token'
    token = os.environ.get('XLIGHTS_MCP_TOKEN') or (tf.read_text().strip() if tf.exists() else '')
    if not token:
        token = secrets.token_urlsafe(32)
        tf.write_text(token + '\n')
        tf.chmod(0o600)

    base = f'http://{lan_address() if a.host == "0.0.0.0" else a.host}:{a.port}'
    print(f'xl_mcp {VERSION}: show folder {SHOW}; xLights at 127.0.0.1:{a.xlights_port}; listening on {a.host}:{a.port}\n'
          f'On the agent machine:\n'
          f'  claude mcp add --transport http xlights {base}/mcp --header "Authorization: Bearer {token}"\n'
          f'  export XLIGHTS_MCP_URL={base} XLIGHTS_MCP_TOKEN={token}     # for xl.py push / pull\n'
          f'The token is in {tf}; delete it to make a new one. Let only the agent machine through the firewall.',
          flush=True)
    app = require_token(mcp.streamable_http_app(host=a.host), token)
    uvicorn.run(app, host=a.host, port=a.port, log_level='warning')


if __name__ == '__main__':
    main()
