# -*- coding: utf-8 -*-
"""backends/raster.py — 显示列表 → 位图。

要点
----
1. 两种填充规则：
   - evenodd：字形孔洞、圆环（多轮廓 even-odd 合并，历史踩坑的解法）
   - nonzero：描边轮廓（同一笔画内的重叠区不会互相挖空）
2. 默认**不降采样**：ss 倍像素直接输出（2160 宽而不是 1080）。
   实测降采样占总耗时的 77%，跳过它时间砍半且清晰度更高；exact=True 才降。
3. 扫描线一律行切片赋值，而不是逐像素写 3 字节（实测快 15%）。
"""

import math
import struct
import zlib

from .. import offset as _offset

# 单色叠加的 256 项映射表缓存（(灰度值, alpha) -> bytes）
_GRAY_LUT = {}


_RGB_LUT = {}


def _rgb_luts(color, alpha):
    """任意颜色的三张 256 项混合表（按颜色与 alpha 缓存）。"""
    key = (int(color[0]), int(color[1]), int(color[2]),
           int(round(alpha * 1000)))
    tabs = _RGB_LUT.get(key)
    if tabs is None:
        a = key[3] / 1000.0
        ia = 1.0 - a
        tabs = tuple(bytes(int(x * ia + key[c] * a + 0.5) for x in range(256))
                     for c in range(3))
        _RGB_LUT[key] = tabs
    return tabs


def _gray_lut(v, alpha):
    key = (int(v), int(round(alpha * 1000)))
    lut = _GRAY_LUT.get(key)
    if lut is None:
        a = key[1] / 1000.0
        ia = 1.0 - a
        lut = bytes(int(x * ia + v * a + 0.5) for x in range(256))
        _GRAY_LUT[key] = lut
    return lut


class RasterBackend(object):
    def __init__(self, w, h, ss, bg):
        self.w = int(w)
        self.h = int(h)
        self.ss = int(ss)
        self.cw = self.w * self.ss
        self.ch = self.h * self.ss
        self.tol = 0.5 / self.ss          # 细分容差：半个采样像素
        self.buf = bytearray(self.cw * self.ch * 3)
        r, g, b = bg if bg else (255, 255, 255)
        self.buf[:] = bytes((r, g, b)) * (self.cw * self.ch)

    # ---------------- 扫描线（活动边表） ----------------
    def _scan(self, contours, color, alpha, rule):
        s = self.ss
        cw, ch = self.cw, self.ch
        # 边表：(ymin, ymax, x_at_ymin, dx/dy, winding)
        edges = []
        for pts in contours:
            n = len(pts)
            if n < 3:
                continue
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                X0, Y0 = x0 * s, y0 * s
                X1, Y1 = x1 * s, y1 * s
                if Y0 == Y1:
                    continue
                if Y0 < Y1:
                    edges.append((Y0, Y1, X0, (X1 - X0) / (Y1 - Y0), 1))
                else:
                    edges.append((Y1, Y0, X1, (X0 - X1) / (Y0 - Y1), -1))
        if not edges:
            return
        edges.sort(key=lambda e: e[0])
        ymin = max(0, int(math.floor(edges[0][0])))
        ymax = min(ch - 1, int(math.ceil(max(e[1] for e in edges))))
        if ymax < ymin:
            return
        col = bytes(color)
        buf = self.buf
        opaque = alpha >= 0.999
        ei = 0
        ne = len(edges)
        active = []
        for y in range(ymin, ymax + 1):
            yc = y + 0.5
            # 活动边表：只维护与当前扫描线相交的边
            while ei < ne and edges[ei][0] <= yc:
                active.append(edges[ei])
                ei += 1
            active = [e for e in active if e[1] > yc]
            if len(active) < 2:
                continue
            xs = [(e[2] + (yc - e[0]) * e[3], e[4]) for e in active]
            xs.sort()
            spans = []
            if rule == "nonzero":
                wind = 0
                start = None
                for x, d in xs:
                    prev = wind
                    wind += d
                    if prev == 0 and wind != 0:
                        start = x
                    elif prev != 0 and wind == 0 and start is not None:
                        spans.append((start, x))
                        start = None
            else:
                i = 0
                while i + 1 < len(xs):
                    spans.append((xs[i][0], xs[i + 1][0]))
                    i += 2
            base = y * cw * 3
            for a, b in spans:
                if b <= 0.0 or a >= cw:
                    continue
                if a < 0.0:
                    a = 0.0
                if b > cw:
                    b = float(cw)
                if b <= a:
                    continue
                # 亚像素覆盖：端点像素按实际覆盖比例混合。
                # 二值填充在 ss=2 下只有 5 级灰度，斜边会出现 1/4 像素阶梯；
                # 覆盖率把横向抗锯齿提到 ~256 级，成本只有每行两次混合。
                xa = int(a)
                xb = int(b)
                if xb >= cw:
                    xb = cw - 1
                if xa > xb:
                    continue
                cl = xa + 1.0 - a
                if cl > 1.0:
                    cl = 1.0
                if xa == xb:
                    self._blend_px(base + xa * 3, color, alpha * (b - a))
                    continue
                self._blend_px(base + xa * 3, color, alpha * cl)
                if xb - xa > 1:
                    off = base + (xa + 1) * 3
                    n = xb - xa - 1
                    if opaque:
                        buf[off:off + n * 3] = col * n
                    else:
                        self._blend(off, n, color, alpha)
                cr = b - xb
                if cr > 1.0:
                    cr = 1.0
                if cr > 0.0:
                    self._blend_px(base + xb * 3, color, alpha * cr)

    def _blend_px(self, off, color, a):
        if a <= 0.003:
            return
        buf = self.buf
        if a >= 0.997:
            buf[off] = color[0]
            buf[off + 1] = color[1]
            buf[off + 2] = color[2]
            return
        ia = 1.0 - a
        buf[off] = int(buf[off] * ia + color[0] * a + 0.5)
        buf[off + 1] = int(buf[off + 1] * ia + color[1] * a + 0.5)
        buf[off + 2] = int(buf[off + 2] * ia + color[2] * a + 0.5)

    def _blend(self, off, n, color, alpha):
        """半透明叠加：任何颜色都能用「逐通道 LUT + translate」在 C 层完成。

        dst = dst*(1-a) + color*a 是一次线性映射，所以对每个通道建一张 256 项表即可。
        之前只对灰/黑/白开 LUT，导致近黑色大面积压暗退化成逐像素浮点运算
        （实测 13s vs 2.6s）。
        """
        buf = self.buf
        ia = 1.0 - alpha
        tabs = _rgb_luts(color, alpha)
        seg = bytes(buf[off:off + n * 3])
        out = bytearray(len(seg))
        for c in range(3):
            out[c::3] = seg[c::3].translate(tabs[c])
        buf[off:off + n * 3] = out

    # ---------------- 执行 ----------------
    def _exec(self, op):
        if op["k"] == "fill":
            self._scan(op["path"].flatten(self.tol), op["color"],
                       op["alpha"], op["rule"])
        elif op["k"] == "image":
            self._image(op)
        else:
            sp = _offset.stroke_path(op["path"], op["width"], op["cap"],
                                     op["join"], self.tol)
            self._scan(sp.flatten(self.tol), op["color"], op["alpha"], "nonzero")

    def _image(self, op):
        """贴图：先在「逻辑分辨率」生成，再整数倍放大到 ss。

        直接在 ss 分辨率逐像素拼接会产生 9 倍于逻辑像素的 Python 循环
        （3240×4320 实测 14s）。改成两步后约 1/4 时间。
        """
        from .. import imaging
        src = op["src"]
        if isinstance(src, tuple):
            sw, sh, rgb = src
        else:
            sw, sh, rgb = imaging.load_small(src, max_side=1280)
        if sw < 1 or sh < 1:
            return
        s = self.ss
        cw, ch = self.cw, self.ch
        # 逻辑矩形（裁到画布内）
        lx0 = int(round(op["x"]))
        ly0 = int(round(op["y"]))
        lx1 = min(self.w, int(round(op["x"] + op["w"])))
        ly1 = min(self.h, int(round(op["y"] + op["h"])))
        if lx1 <= lx0 or ly1 <= ly0:
            return
        lw, lh = lx1 - lx0, ly1 - ly0
        alpha = op["alpha"]
        ia = 1.0 - alpha
        px0, py0 = lx0 * s, ly0 * s

        # 1) 逻辑分辨率生成（最近邻）
        cols = [min(sw - 1, int(tx * sw / lw)) * 3 for tx in range(lw)]
        tmp = bytearray(lw * lh * 3)
        for ty in range(lh):
            sy = min(sh - 1, int(ty * sh / lh))
            srow = rgb[sy * sw * 3:(sy + 1) * sw * 3]
            tmp[ty * lw * 3:(ty + 1) * lw * 3] = b"".join(
                srow[c:c + 3] for c in cols)

        # 2) 整数倍放大到 ss
        buf = self.buf
        s3 = s * 3
        for ty in range(lh):
            lrow = tmp[ty * lw * 3:(ty + 1) * lw * 3]
            if s == 1:
                big = lrow
            else:
                parts = [None] * lw
                for tx in range(lw):
                    p3 = tx * 3
                    parts[tx] = lrow[p3:p3 + 3] * s
                big = b"".join(parts)
            off = (py0 + ty * s) * cw * 3 + px0 * 3
            if alpha >= 0.999:
                for yy in range(s):
                    o = off + yy * cw * 3
                    buf[o:o + lw * s3] = big
            else:
                for yy in range(s):
                    o = off + yy * cw * 3
                    for i in range(lw * s3):
                        v = big[i]
                        d = o + i
                        buf[d] = int(v * alpha + buf[d] * ia)

    def run(self, ops, layers=None):
        ops = [op for op in ops
               if layers is None or op.get("layer") in layers]
        i, n = 0, len(ops)
        while i < n:
            clip = ops[i].get("clip")
            if clip is None:
                self._exec(ops[i])
                i += 1
                continue
            # 同一裁剪上下文的连续 ops 一起处理
            j = i
            group = []
            while j < n and ops[j].get("clip") is clip:
                group.append(ops[j])
                j += 1
            self._exec_clipped(group, clip)
            i = j

    def _exec_clipped(self, group, clip_path):
        """在临时副本上绘制，再用裁剪掩码合成回主画布。

        这样 clip 内的半透明叠加仍然作用在「正确的内容」上，
        只是最终按掩码替换——不需要真正的多图层合成器。
        """
        s = self.ss
        x0, y0, x1, y1 = clip_path.bbox()
        px0 = max(0, int(math.floor(x0 * s)) - 1)
        py0 = max(0, int(math.floor(y0 * s)) - 1)
        px1 = min(self.cw - 1, int(math.ceil(x1 * s)) + 1)
        py1 = min(self.ch - 1, int(math.ceil(y1 * s)) + 1)
        if px1 < px0 or py1 < py0:
            return
        # 临时副本：从当前画面开始画（保证混合结果正确）
        tmp = bytearray(self.buf)
        sub = RasterBackend.__new__(RasterBackend)
        sub.w, sub.h, sub.ss = self.w, self.h, self.ss
        sub.cw, sub.ch = self.cw, self.ch
        sub.tol = self.tol
        sub.buf = tmp
        for op in group:
            sub._exec(op)
        mask = self._mask(clip_path)
        buf = self.buf
        for y in range(py0, py1 + 1):
            row = y * self.cw
            pos = row + px0
            end = row + px1 + 1
            while pos < end:
                s0 = mask.find(1, pos, end)
                if s0 < 0:
                    break
                e0 = mask.find(0, s0, end)
                if e0 < 0:
                    e0 = end
                o0 = s0 * 3
                o1 = e0 * 3
                buf[o0:o1] = tmp[o0:o1]
                pos = e0

    def _mask(self, path):
        """把裁剪路径光栅化成 1 字节掩码（1 = 覆盖）。"""
        s = self.ss
        cw, ch = self.cw, self.ch
        mask = bytearray(cw * ch)
        edges = []
        for pts in path.flatten(self.tol):
            n = len(pts)
            if n < 3:
                continue
            for i in range(n):
                xa, ya = pts[i]
                xb, yb = pts[(i + 1) % n]
                X0, Y0 = xa * s, ya * s
                X1, Y1 = xb * s, yb * s
                if Y0 == Y1:
                    continue
                if Y0 < Y1:
                    edges.append((Y0, Y1, X0, (X1 - X0) / (Y1 - Y0)))
                else:
                    edges.append((Y1, Y0, X1, (X0 - X1) / (Y0 - Y1)))
        if not edges:
            return mask
        edges.sort(key=lambda e: e[0])
        ymin = max(0, int(math.floor(edges[0][0])))
        ymax = min(ch - 1, int(math.ceil(max(e[1] for e in edges))))
        ei, ne = 0, len(edges)
        active = []
        for y in range(ymin, ymax + 1):
            yc = y + 0.5
            while ei < ne and edges[ei][0] <= yc:
                active.append(edges[ei])
                ei += 1
            active = [e for e in active if e[1] > yc]
            if len(active) < 2:
                continue
            xs = sorted(e[2] + (yc - e[0]) * e[3] for e in active)
            row = y * cw
            i = 0
            while i + 1 < len(xs):
                a = max(0, int(math.ceil(xs[i])))
                b = min(cw - 1, int(math.floor(xs[i + 1])))
                if b >= a:
                    mask[row + a:row + b + 1] = b"\x01" * (b - a + 1)
                i += 2
        return mask

    # ---------------- 输出 ----------------
    def _downsample(self):
        ss = self.ss
        if ss == 1:
            return self.buf
        w, h, cw = self.w, self.h, self.cw
        buf = self.buf
        out = bytearray(w * h * 3)
        n = ss * ss
        stride = cw * 3
        for y in range(h):
            rows = []
            for dy in range(ss):
                b0 = (y * ss + dy) * stride
                rows.append(buf[b0:b0 + stride])
            for x in range(w):
                r = g = b = 0
                for row in rows:
                    p = x * ss * 3
                    for _ in range(ss):
                        r += row[p]
                        g += row[p + 1]
                        b += row[p + 2]
                        p += 3
                q = (y * w + x) * 3
                out[q] = r // n
                out[q + 1] = g // n
                out[q + 2] = b // n
        return out

    def png(self, path, exact=False, dpi=96):
        if exact and self.ss > 1:
            rgb = self._downsample()
            w, h = self.w, self.h
        else:
            rgb = self.buf
            w, h = self.cw, self.ch
        raw = b"".join(b"\x00" + bytes(rgb[y * w * 3:(y + 1) * w * 3]) for y in range(h))

        def chunk(tag, data):
            body = tag + data
            return (struct.pack(">I", len(data)) + body +
                    struct.pack(">I", zlib.crc32(body) & 0xffffffff))

        ppm = int(round(dpi / 0.0254))
        blob = b"\x89PNG\r\n\x1a\n"
        blob += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        blob += chunk(b"pHYs", struct.pack(">IIB", ppm, ppm, 1))
        # level 6：实测比 level 9 快一倍、文件只大 15%（纯 Python 下更划算）
        blob += chunk(b"IDAT", zlib.compress(raw, 6))
        blob += chunk(b"IEND", b"")
        with open(path, "wb") as fh:
            fh.write(blob)
        return path


def render_png(canvas, out, exact=False, ss=None, layers=None, dpi=96):
    ss = canvas.ss if ss is None else int(ss)
    be = RasterBackend(canvas.w, canvas.h, ss, canvas.bg)
    be.run(canvas.ops, layers)
    return be.png(out, exact=exact, dpi=dpi)
