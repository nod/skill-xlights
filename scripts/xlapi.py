"""The xLights automation API with the safety rules applied. Python standard library only.

xl.py (a command line, on any machine) and xl_mcp.py (an MCP server running next to xLights) both drive xLights
through this module, so the rules live in one place. Each rule was paid for with a crash or a lost evening; the
reasons are in reference/pipeline.md, "Render, save, read back":
- one render at a time, and nothing touches the sequence while it runs (a lock file);
- never discard the user's unsaved edits: close without force, and xLights itself refuses (HTTP 504) while there
  are unsaved changes;
- never open over a newer autosave (<name>.xbkp), because the API skips xLights' offer to restore it;
- never open, render or save while xLights has another show folder loaded;
- a save returns before the .fseq is written: wait until the file stops growing.

A refusal raises Refused with a message meant for the person or agent driving it. Paths: `there` turns a local path
into the path xLights should be sent, and `here` turns a path xLights reports into a local path. On the xLights
machine both are the identity; xl.py on another machine maps them through MEDIA_ROOT.
"""
import json, os, time, urllib.error, urllib.request
from pathlib import Path

STALE_LOCK_S = 1200                    # a crash leaves a lock behind; one older than this is ignored
GPU_NOTE = 'GPU rendering: the API cannot report it; it must be OFF in xLights Preferences before you render'


class Refused(Exception):
    """A rule, or xLights, said no. The message says why and what to do."""


class NoAnswer(Refused):
    """xLights did not answer at all (not running, unreachable, or still busy past the timeout)."""


def mmss(seconds):
    m, s = divmod(max(0.0, float(seconds)), 60)
    return f'{int(m)}:{s:04.1f}'


def _norm(p):
    return str(p).replace('\\', '/').rstrip('/')


def same_folder(a, b):
    """Do two folder paths name the same folder? Resolved when both exist here, compared as text otherwise."""
    a, b = Path(str(a)), Path(str(b))
    if a.exists() and b.exists():
        return a.resolve() == b.resolve()
    return _norm(a) == _norm(b)


def newer_autosave(xsq):
    """A message if <name>.xbkp (xLights' autosave) is newer than <name>.xsq, so it may hold edits never saved."""
    p = Path(xsq)
    bk = p.with_suffix('.xbkp')
    if bk.exists() and p.exists() and bk.stat().st_mtime > p.stat().st_mtime + 1:
        hm = lambda f: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(f.stat().st_mtime))
        return (f"{bk.name} (autosave {hm(bk)}) is newer than {p.name} (saved {hm(p)}), so it may hold edits that "
                "were never saved")
    return ''


def settle(path, before_mtime, appear_s=30.0, stable_s=2.0, cap_s=120.0, poll_s=0.5):
    """Block until `path` stops growing: done when its size has been unchanged for `stable_s` AFTER its mtime
    moved past `before_mtime` (so an old, untouched file is not mistaken for a finished write). Gives up if no
    write shows within `appear_s` (a synced folder may need longer), or after `cap_s`.
    Returns (size_bytes, elapsed_s, note); note is '' when it settled cleanly."""
    path = Path(path)
    t0 = time.time(); last = None; since = t0
    while True:
        now = time.time()
        st = path.stat() if path.exists() else None
        if st is not None and st.st_mtime > before_mtime:
            if st.st_size != last:
                last, since = st.st_size, now
            elif now - since >= stable_s:
                return last, now - t0, ''
        elif now - t0 >= appear_s:
            return (st.st_size if st else 0), now - t0, \
                f"{path.name} {'never appeared' if st is None else 'was not rewritten'} within {appear_s:.0f} s"
        if now - t0 >= cap_s:
            return (last or 0), now - t0, f'still growing after {cap_s:.0f} s: do not read it yet'
        time.sleep(poll_s)


class XLights:
    def __init__(self, host='127.0.0.1', port=49913, show='', lock=None, there=str, here=Path):
        self.host, self.port = host, int(port)
        self.url = f'http://{host}:{self.port}/xlDoAutomation'
        self.show = str(show)                      # the show folder as xLights sees it
        self.lock = Path(lock) if lock else Path.home() / '.cache' / 'xlights-tooling' / 'render.lock'
        self.there, self.here = there, here

    # ------------------------------------------------------------ the API
    def call(self, cmd, timeout=600, allow=()):
        """Send one command. An HTTP error code in `allow` comes back as {'res': code, 'msg': ...}; any other
        error raises Refused with xLights' message. No answer raises NoAnswer."""
        req = urllib.request.Request(self.url, data=json.dumps(cmd).encode(),
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode()
        except urllib.error.HTTPError as e:
            # xLights answers 503/504 with a JSON body that says why ("Sequence not open."); report it as is
            try:
                msg = json.loads(e.read().decode()).get('msg', '')
            except Exception:
                msg = ''
            if cmd['cmd'] == 'getOpenSequence' and 'not open' in msg.lower():
                return {'res': '200', 'seq': ''}             # a normal state, not an error
            if e.code in allow:
                return {'res': e.code, 'msg': msg}
            raise Refused(f"xLights answered HTTP {e.code} to {cmd['cmd']}: {msg or '(no message)'}")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            raise NoAnswer(f"xLights automation did not answer {cmd['cmd']} at {self.host}:{self.port} "
                           f"({getattr(e, 'reason', e)}).\n"
                           "  Is xLights running there? Enable the port once: Preferences -> Output -> API Port -> "
                           "Port A (49913),\n  or start xLights with -a."
                           + ('' if self.host in ('127.0.0.1', 'localhost') else
                              f" Check that this machine can get through {self.host}'s firewall."))
        try:
            res = json.loads(body)
        except json.JSONDecodeError:
            res = {'raw': body}
        if str(res.get('res', '200')) != '200':
            hint = ' (saveSequence needs xLights 2026.17 or newer)' if cmd['cmd'] == 'saveSequence' else ''
            raise Refused(f"xLights refused {cmd['cmd']}: {res}{hint}")
        return res

    def show_folder(self):
        return self.call({'cmd': 'getShowFolder'}).get('folder', '')

    def open_sequence(self):
        """What xLights has open: {'seq': name, 'fullseq': path as xLights sees it, ...}; seq is '' if nothing."""
        return self.call({'cmd': 'getOpenSequence'})

    def assert_show(self, what):
        folder = self.show_folder()
        if not same_folder(folder, self.show):
            raise Refused(f"REFUSING {what}: xLights has the show folder {folder!r} loaded, but this show is "
                          f"{self.show!r}.\n  Models and groups are per show folder; rendering or saving across "
                          "layouts can drop every model the other layout lacks.\n  In xLights: File -> Select Show "
                          f"Folder -> {self.show}, then try again.")

    # ------------------------------------------------------------ the render lock
    def rendering(self):
        if not self.lock.exists():
            return False
        if time.time() - self.lock.stat().st_mtime > STALE_LOCK_S:
            self.lock.unlink(missing_ok=True)
            return False
        return True

    def take_lock(self):
        """Create the lock atomically: a second render started at the same moment fails here instead of both
        running."""
        self.rendering()                                # clears a stale lock
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            raise Refused('REFUSING renderAll: a render is already in flight. Two renders queued together is the '
                          'failure; wait for the first to return.')
        with os.fdopen(fd, 'w') as f:
            f.write(str(time.time()))

    def guard(self, what):
        if self.rendering():
            raise Refused(f"REFUSING {what}: a render is in flight ({self.lock}). Nothing may touch the sequence "
                          "while it runs; wait for it to return.")

    # ------------------------------------------------------------ commands; each returns a report
    def status(self):
        folder = self.show_folder()
        note = '' if same_folder(folder, self.show) else f'   (NOT this show: that is {self.show})'
        lines = [f'show folder: {folder}{note}']
        r = self.open_sequence()
        if r.get('seq'):
            lines.append(f"open: {r.get('fullseq') or r.get('seq')}   media: {Path(str(r.get('media', ''))).name}   "
                         f"length {mmss(float(r.get('len', 0)) / 1000)}")
        else:
            lines.append('no sequence open')
        if self.rendering():
            lines.append(f'a render is in flight ({self.lock})')
        lines.append(GPU_NOTE)
        return '\n'.join(lines)

    def close_clean(self, what):
        """Close the open sequence only if xLights says it has no unsaved changes (it answers 504 otherwise)."""
        r = self.call({'cmd': 'closeSequence', 'quiet': 'true'}, allow=(504,))
        if str(r.get('res')) == '504':
            st = self.open_sequence()
            raise Refused(f"REFUSING {what}: xLights has UNSAVED changes in "
                          f"{st.get('fullseq') or st.get('seq') or 'the open sequence'} (probably the user's). The "
                          "API would discard them without asking. Ask the user; then save to keep them, or close "
                          "with discard to throw them away.")
        return r

    def open(self, xsq, ignore_xbkp=False):
        """Open the local file `xsq` in xLights."""
        self.guard('loadSequence')
        self.assert_show('loadSequence')
        p = Path(xsq)
        if not p.exists():
            raise Refused(f'{xsq}: no such file')
        newer = '' if ignore_xbkp else newer_autosave(p)
        if newer:
            raise Refused(f"REFUSING open: {newer}. Opening through the API skips xLights' offer to restore it, "
                          "and the next autosave overwrites it. Ask the user to open it in xLights and choose; or "
                          "open with ignore_xbkp (throws the autosave away).")
        if self.open_sequence().get('seq'):
            self.close_clean('open')
        target = self.there(p)
        r = self.call({'cmd': 'loadSequence', 'seq': target, 'promptIssues': 'false'})
        return f"opened {target}: {r.get('msg', r)}"

    def render(self):
        if self.rendering():
            raise Refused('REFUSING renderAll: a render is already in flight. Two renders queued together is the '
                          'failure; wait for the first to return.')
        if not self.open_sequence().get('seq'):        # xLights answers a render with nothing open with a modal
            raise Refused('REFUSING renderAll: no sequence is open. xLights would answer with a "you must open a '
                          'sequence first" dialog, which blocks every later command until someone closes it.')
        self.assert_show('renderAll')
        self.take_lock()
        t0 = time.time()
        try:
            r = self.call({'cmd': 'renderAll'}, timeout=1800)
        except NoAnswer as e:
            # no answer is not "done": xLights may still be rendering, so the lock stays until it goes stale
            raise NoAnswer(f"{e}\n  The render lock stays ({self.lock}; it expires after {STALE_LOCK_S // 60} "
                           "min): xLights may still be rendering. Check xLights before sending anything else.")
        except BaseException:
            self.lock.unlink(missing_ok=True)           # xLights answered (an error): it is not rendering
            raise
        self.lock.unlink(missing_ok=True)
        return f"renderAll returned after {time.time() - t0:.1f} s: {r.get('msg', r)}"

    def save(self, timeout=180, before_save=None):
        """saveSequence, then wait for the .fseq to settle. `before_save(xsq)` runs just before the API call.
        Returns (report, local .xsq path)."""
        self.guard('saveSequence')
        st = self.open_sequence()
        if not st.get('fullseq'):
            raise Refused('REFUSING save: xLights has no sequence open.')
        self.assert_show('saveSequence')
        xsq = self.here(st['fullseq'])
        fseq = xsq.with_suffix('.fseq')
        before = fseq.stat().st_mtime if fseq.exists() else 0
        if before_save:
            before_save(xsq)
        t0 = time.time()
        r = self.call({'cmd': 'saveSequence'}, timeout=timeout)
        t_api = time.time() - t0
        size, waited, note = settle(fseq, before)
        if fseq.exists() and fseq.stat().st_mtime > before:
            report = (f"saved via API in {t_api:.1f} s: {r.get('msg', r)}  -> {fseq.name} {size / 1e6:.1f} MB, "
                      f"settled after {waited:.1f} s" + (f' ({note})' if note else ''))
        else:
            report = (f"saveSequence returned {r.get('msg', r)} in {t_api:.1f} s but {fseq} did not change after "
                      f"{waited:.1f} s ({note or 'no write seen'}). An unrendered sequence saves only the .xsq "
                      "(render first), or a synced folder has not caught up. Do not read the .fseq as if it were new.")
        return report, xsq

    def close(self, discard=False):
        self.guard('closeSequence')
        if discard:
            r = self.call({'cmd': 'closeSequence', 'quiet': 'true', 'force': 'true'})
        else:
            r = self.close_clean('close')
        return f"closed: {r.get('msg', r)}"
