# -*- coding: utf-8 -*-
"""imaging.py — 极简图片解码，给 analyze.py 用（本机没有 PIL）。

为什么只解 DC 系数
------------------
分析配色/明暗/版心不需要全分辨率。JPEG 一个 8×8 块的 DC 系数就是该块的平均色，
只解 DC、跳过 AC，就能得到 1/8 尺寸的缩略图，比完整解码快一个数量级，也不需要 IDCT。

能力边界
--------
- PNG：8bit，颜色类型 0/2/6（灰度/RGB/RGBA）；不支持调色板与 16bit。
- JPEG：基线（SOF0），任意采样因子；渐进式（SOF2）不支持。
"""

import struct
import zlib


# ================================================================ PNG
def _paeth(a, b, c):
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def load_png(path):
    """返回 (w, h, rgb_bytes)，rgb 为 w*h*3。"""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG")
    i = 8
    idat = bytearray()
    w = h = None
    bitdepth = 8
    ctype = 2
    while i < len(data):
        ln = struct.unpack(">I", data[i:i + 4])[0]
        tag = data[i + 4:i + 8]
        body = data[i + 8:i + 8 + ln]
        if tag == b"IHDR":
            w, h, bitdepth, ctype = struct.unpack(">IIBB", body[:10])
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break
        i += 12 + ln
    if bitdepth != 8 or ctype not in (0, 2, 6):
        raise ValueError("只支持 8bit 灰度/RGB/RGBA PNG（ctype=%d bit=%d）"
                         % (ctype, bitdepth))
    ch = {0: 1, 2: 3, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = w * ch
    prev = bytearray(stride)
    out = bytearray(w * h * 3)
    pos = 0
    for y in range(h):
        f = raw[pos]
        pos += 1
        row = bytearray(raw[pos:pos + stride])
        pos += stride
        if f == 1:
            for x in range(ch, stride):
                row[x] = (row[x] + row[x - ch]) & 255
        elif f == 2:
            for x in range(stride):
                row[x] = (row[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = row[x - ch] if x >= ch else 0
                row[x] = (row[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = row[x - ch] if x >= ch else 0
                c = prev[x - ch] if x >= ch else 0
                row[x] = (row[x] + _paeth(a, prev[x], c)) & 255
        prev = row
        o = y * w * 3
        if ch == 3:
            out[o:o + w * 3] = row
        elif ch == 4:
            for x in range(w):
                out[o + x * 3:o + x * 3 + 3] = row[x * 4:x * 4 + 3]
        else:
            for x in range(w):
                v = row[x]
                out[o + x * 3] = v
                out[o + x * 3 + 1] = v
                out[o + x * 3 + 2] = v
    return w, h, out


# ================================================================ JPEG (DC only)
def _huff_table(bits, vals):
    """从 BITS/HUFFVAL 构建 (code_len, code) -> value 的查找表。"""
    table = {}
    code = 0
    k = 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            table[(length, code)] = vals[k]
            k += 1
            code += 1
        code <<= 1
    return table


class _BitReader(object):
    __slots__ = ("data", "pos", "bitbuf", "bitcnt")

    def __init__(self, data, pos):
        self.data = data
        self.pos = pos
        self.bitbuf = 0
        self.bitcnt = 0

    def bit(self):
        if self.bitcnt == 0:
            b = self.data[self.pos]
            if b == 0xFF:
                # 字节填充：跳过 0x00
                if self.pos + 1 < len(self.data) and self.data[self.pos + 1] == 0:
                    self.pos += 1
                else:
                    raise EOFError
            self.pos += 1
            self.bitbuf = b
            self.bitcnt = 8
        self.bitcnt -= 1
        return (self.bitbuf >> self.bitcnt) & 1

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v

    def huff(self, table):
        code = 0
        for length in range(1, 17):
            code = (code << 1) | self.bit()
            v = table.get((length, code))
            if v is not None:
                return v
        raise ValueError("坏霍夫曼码")

    def restart(self):
        self.bitcnt = 0


def _extend(v, n):
    return v - (1 << n) + 1 if v < (1 << (n - 1)) else v


def load_jpeg_dc(path):
    """只解 DC 系数，返回 (bw, bh, rgb)，每像素对应一个 8×8 块的平均色。"""
    data = open(path, "rb").read()
    if data[:2] != b"\xff\xd8":
        raise ValueError("不是 JPEG")
    i = 2
    qt = {}
    huff_dc = {}
    huff_ac = {}
    comps = []
    width = height = 0
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        i += 2
        if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
            continue
        ln = struct.unpack(">H", data[i:i + 2])[0]
        seg = data[i + 2:i + ln]
        if m == 0xDB:      # DQT
            p = 0
            while p < len(seg):
                pq, tq = seg[p] >> 4, seg[p] & 15
                p += 1
                n = 64 * (2 if pq else 1)
                qt[tq] = seg[p:p + n]
                p += n
        elif m == 0xC4:    # DHT
            p = 0
            while p < len(seg):
                tc, th = seg[p] >> 4, seg[p] & 15
                p += 1
                bits = list(seg[p:p + 16])
                p += 16
                nv = sum(bits)
                vals = list(seg[p:p + nv])
                p += nv
                if tc == 0:
                    huff_dc[th] = _huff_table(bits, vals)
                else:
                    huff_ac[th] = _huff_table(bits, vals)
        elif m in (0xC0, 0xC1):   # SOF0/1
            height, width = struct.unpack(">HH", seg[1:5])
            nc = seg[5]
            comps = []
            p = 6
            for _ in range(nc):
                cid = seg[p]
                hv = seg[p + 1]
                tq = seg[p + 2]
                comps.append({"id": cid, "h": hv >> 4, "v": hv & 15, "tq": tq,
                              "td": 0, "ta": 0, "pred": 0})
                p += 3
        elif m == 0xDA:    # SOS
            ns = seg[0]
            p = 1
            for _ in range(ns):
                cid = seg[p]
                td, ta = seg[p + 1] >> 4, seg[p + 1] & 15
                for c in comps:
                    if c["id"] == cid:
                        c["td"], c["ta"] = td, ta
                p += 2
            return _decode_scan(data, i + ln, width, height, comps, qt,
                                huff_dc, huff_ac)
        i += ln
    raise ValueError("找不到 SOS（可能是渐进式 JPEG）")


def _decode_scan(data, pos, width, height, comps, qt, huff_dc, huff_ac):
    hmax = max(c["h"] for c in comps)
    vmax = max(c["v"] for c in comps)
    mcux = (width + 8 * hmax - 1) // (8 * hmax)
    mcuy = (height + 8 * vmax - 1) // (8 * vmax)
    bw = mcux * hmax
    bh = mcuy * vmax
    # 每分量一个 bw×bh 的 DC 网格
    grids = {}
    for c in comps:
        grids[c["id"]] = [[0.0] * bw for _ in range(bh)]
    br = _BitReader(data, pos)
    for my in range(mcuy):
        for mx in range(mcux):
            for c in comps:
                sx = hmax // c["h"]
                sy = vmax // c["v"]
                q = qt.get(c["tq"])
                step = q[0] if q is not None else 1
                for by in range(c["v"]):
                    for bx in range(c["h"]):
                        n = br.huff(huff_dc[c["td"]])
                        diff = _extend(br.bits(n), n) if n else 0
                        c["pred"] += diff
                        # DC 是「像素值-128」的 DCT 均值，重建要乘量化步长再加 128
                        val = c["pred"] * step / 8.0 + 128.0   # DC 系数 = 8×均值
                        gx0 = mx * hmax + bx * sx
                        gy0 = my * vmax + by * sy
                        for ddy in range(sy):
                            for ddx in range(sx):
                                gy = gy0 + ddy
                                gx = gx0 + ddx
                                if 0 <= gy < bh and 0 <= gx < bw:
                                    grids[c["id"]][gy][gx] = val
                        # 跳过 AC
                        k = 1
                        while k < 64:
                            rs = br.huff(huff_ac[c["ta"]])
                            r, s = rs >> 4, rs & 15
                            if s == 0:
                                if r == 15:
                                    k += 16
                                    continue
                                break
                            k += r
                            br.bits(s)
                            k += 1
    # 拼 RGB
    out = bytearray(bw * bh * 3)
    ys = comps[0]["id"]
    for y in range(bh):
        for x in range(bw):
            Y = grids[ys][y][x]
            if len(comps) >= 3:
                cb = grids[comps[1]["id"]][y][x] - 128
                cr = grids[comps[2]["id"]][y][x] - 128
            else:
                cb = cr = 0
            r = Y + 1.402 * cr
            g = Y - 0.344136 * cb - 0.714136 * cr
            b = Y + 1.772 * cb
            o = (y * bw + x) * 3
            out[o] = max(0, min(255, int(r)))
            out[o + 1] = max(0, min(255, int(g)))
            out[o + 2] = max(0, min(255, int(b)))
    return bw, bh, out


# ================================================================ 统一入口
def load_small(path, max_side=160):
    """解码为不超过 max_side 的小图，返回 (w, h, rgb)。"""
    low = path.lower()
    if low.endswith(".png"):
        w, h, rgb = load_png(path)
    elif low.endswith((".jpg", ".jpeg")):
        w, h, rgb = load_jpeg_dc(path)
    else:
        sig = open(path, "rb").read(8)
        if sig[:8] == b"\x89PNG\r\n\x1a\n":
            w, h, rgb = load_png(path)
        elif sig[:2] == b"\xff\xd8":
            w, h, rgb = load_jpeg_dc(path)
        else:
            raise ValueError("不认识的图片格式")
    if max(w, h) <= max_side:
        return w, h, rgb
    step = max(1, int(max(w, h) / float(max_side)))
    nw, nh = max(1, w // step), max(1, h // step)
    out = bytearray(nw * nh * 3)
    for y in range(nh):
        sy = min(h - 1, y * step)
        for x in range(nw):
            sx = min(w - 1, x * step)
            si = (sy * w + sx) * 3
            di = (y * nw + x) * 3
            out[di:di + 3] = rgb[si:si + 3]
    return nw, nh, out
