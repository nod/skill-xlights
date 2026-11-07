"""Read an xLights render (.fseq, FSEQ v2): one frame of channel bytes at a time. Read-only.

    fs = FSEQ('../seqs/song/song.fseq')   # header: fs.channels, fs.frames, fs.step (ms per frame), fs.ranges
    fr = fs.frame(n)                       # bytes laid out at ABSOLUTE channels: byte index = channel - 1
    rgb(fr, start_channel, node)           # one node's (r, g, b); start channel and node both 1-based
    rgb(fr, start, node, lay.stride[m], lay.order[m])   # any other string type (RGBW, GRB, single colour)

What this gets right, each learned from a wrong reading that looked plausible:
- the compression block count is ((byte 20 >> 4) << 8) | byte 21, not byte 21 alone; the short read decodes
  about 2% of the frames and the rest come back empty.
- the block table is padded with (0, 0) slots; a reverse search that matches one returns an empty frame.
- the file is SPARSE: xLights stores only the channels of the models used in the sequence, as (start, count)
  ranges. frame() lays them back out at absolute channels, so a model not in the sequence reads dark instead
  of shifting every later model's bytes. The laid-out frame ends at the last stored channel; rgb() reads
  anything past it as dark too.
- the byte index of channel c is c - 1. rgb() takes a 1-based start channel and a 1-based node and does the
  subtraction itself. Doing it again reads (G, B, R-of-the-next-node): pure red looks blue, and every colour
  reported from the render is shifted while still looking like a colour.

Needs `zstandard` (xLights compresses with zstd by default; setup.sh installs it). zlib and uncompressed
files are read too.
"""
import struct, zlib
try:
    import zstandard
except ImportError:
    zstandard = None


class FSEQ:
    def __init__(self, path):
        f = open(path, "rb"); self.f = f
        h = f.read(32)
        assert h[:4] == b"PSEQ", h[:4]
        self.data_off = struct.unpack("<H", h[4:6])[0]
        self.minor, self.major = h[6], h[7]
        self.var_off = struct.unpack("<H", h[8:10])[0]
        self.channels = struct.unpack("<I", h[10:14])[0]
        self.frames = struct.unpack("<I", h[14:18])[0]
        self.step = h[18]
        self.comp = h[20] & 0x0F
        self.blocks = ((h[20] >> 4) << 8) | h[21]
        self.sparse = h[22]
        assert 32 + self.blocks * 8 + self.sparse * 6 == self.var_off, \
            f"header sanity: 32+{self.blocks}*8+{self.sparse}*6 != {self.var_off}"
        tbl = f.read(self.blocks * 8)
        idx = [struct.unpack("<II", tbl[i*8:i*8+8]) for i in range(self.blocks)]
        self.index = [e for e in idx if e[1] > 0]          # drop the (0, 0) padding slots
        sp = f.read(self.sparse * 6)
        self.ranges = [(int.from_bytes(sp[i*6:i*6+3], "little"), int.from_bytes(sp[i*6+3:i*6+6], "little"))
                       for i in range(self.sparse)] or [(0, self.channels)]
        assert sum(n for _, n in self.ranges) == self.channels, "sparse ranges != channel count"
        self.span = max(s + n for s, n in self.ranges)      # highest absolute channel stored
        self._cache = {}
        if self.comp == 1 and zstandard is None:
            raise SystemExit("this .fseq is zstd-compressed and the `zstandard` module is missing: "
                             "run setup.sh again (or `uv pip install zstandard` into the audio env)")

    def _block(self, bi):
        if bi in self._cache: return self._cache[bi]
        off = self.data_off + sum(l for _, l in self.index[:bi])
        self.f.seek(off)
        raw = self.f.read(self.index[bi][1])
        if self.comp == 1:
            d = zstandard.ZstdDecompressor().decompressobj().decompress(raw)
        elif self.comp == 2:
            d = zlib.decompress(raw)
        else:
            d = raw
        self._cache = {bi: d}
        return d

    def _absolute(self, raw):
        if self.ranges == [(0, self.channels)]:
            return raw
        out = bytearray(self.span); o = 0      # channels not stored read as 0 (dark)
        for s, c in self.ranges:
            out[s:s + c] = raw[o:o + c]; o += c
        return bytes(out)

    def frame(self, n):
        """Frame n (0-based) as bytes at absolute channels."""
        if self.comp == 0 and not self.index:          # uncompressed v2: no block table
            self.f.seek(self.data_off + n * self.channels)
            return self._absolute(self.f.read(self.channels))
        for bi in range(len(self.index) - 1, -1, -1):
            if self.index[bi][0] <= n:
                d = self._block(bi)
                off = (n - self.index[bi][0]) * self.channels
                return self._absolute(d[off:off + self.channels])
        raise IndexError(n)


def rgb(frame, abs_start_channel, node, stride=3, order=(0, 1, 2, ())):
    """RGB of one node in a decoded frame. `abs_start_channel` is the model's absolute start channel, 1-based
    (controller base + StartChannel offset - 1); `node` is 1-based. `stride` and `order` come from
    `layout.Layout` (lay.stride[m], lay.order[m]): the defaults are an "RGB Nodes" model. A white channel is
    added to all three (an approximation of how it looks); a one-channel node (order None) reads as grey.
    Channels past the end of the file's data (a model above the last stored range) read dark."""
    o = (abs_start_channel - 1) + (node - 1) * stride
    raw = bytes(frame[o:o + stride]).ljust(stride, b"\0")
    if order is None:
        return (raw[0],) * 3
    ri, gi, bi, whites = order
    w = max((raw[i] for i in whites), default=0)
    return tuple(min(255, raw[i] + w) for i in (ri, gi, bi))
