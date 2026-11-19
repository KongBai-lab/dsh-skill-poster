# -*- coding: utf-8 -*-
"""backends/pdf.py — 显示列表 → 矢量 PDF（字形路径化，文字不可选）。

要点
----
- 复用同一份 display list：fill 走路径填充（evenodd→f*，nonzero→f），
  stroke 走 PDF 原生描边（w/J/j + S），所以 PDF 里的线是真正矢量，不是折线。
- 文字：字形已经是 Path，直接输出曲线命令；好处是零字体嵌入、零编码问题，
  代价是文字不可选、不可搜（P0 的明确取舍）。
- 坐标：画布原点左上、y 向下；PDF 原点左下、y 向上 → 输出时 y 取反。
- 仅 RGB；不支持 CMYK（印前需自行转换）。
"""

import zlib

from ..path import _quad_to_cubic


def _n(v):
    s = "%.3f" % float(v)
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _path_ops(path, h, out):
    x = y = 0.0
    for c in path.cmds:
        k = c[0]
        if k == "M":
            x, y = c[1], c[2]
            out.append("%s %s m" % (_n(x), _n(h - y)))
        elif k == "L":
            x, y = c[1], c[2]
            out.append("%s %s l" % (_n(x), _n(h - y)))
        elif k == "C":
            out.append("%s %s %s %s %s %s c" % (
                _n(c[1]), _n(h - c[2]), _n(c[3]), _n(h - c[4]), _n(c[5]), _n(h - c[6])))
            x, y = c[5], c[6]
        elif k == "Q":
            p0 = (x, y)
            p3 = (c[3], c[4])
            p1, p2 = _quad_to_cubic(p0, (c[1], c[2]), p3)
            out.append("%s %s %s %s %s %s c" % (
                _n(p1[0]), _n(h - p1[1]), _n(p2[0]), _n(h - p2[1]),
                _n(p3[0]), _n(h - p3[1])))
            x, y = p3
        elif k == "Z":
            out.append("h")
    return out


_CAP = {"butt": 0, "round": 1, "square": 2}
_JOIN = {"miter": 0, "round": 1, "bevel": 2}


class PDFBackend(object):
    def __init__(self, w_pt, h_pt):
        self.w = float(w_pt)
        self.h = float(h_pt)
        self.pages = []
        self._alphas = {}
        self._images = []      # (name, data, w, h, filter)

    # -------- 位图嵌入 --------
    def _image_ops(self, op, parts):
        """把贴图转成 XObject 引用：JPEG 直嵌（DCTDecode，无重编码），PNG 走 Flate。"""
        import struct as _struct
        from .. import imaging

        src = op["src"]
        if isinstance(src, tuple):
            sw, sh, rgb = src
            data = zlib.compress(bytes(rgb), 9)
            filt = "/FlateDecode"
            cs = "/DeviceRGB"
        else:
            # 按文件签名判断格式（素材文件常常没有扩展名）
            raw = open(src, "rb").read()
            if raw[:2] == b"\xff\xd8":
                sw, sh, nc = _jpeg_info(raw)
                data = raw
                filt = "/DCTDecode"
                cs = "/DeviceGray" if nc == 1 else "/DeviceRGB"
            elif raw[:8] == b"\x89PNG\r\n\x1a\n":
                sw, sh, rgb = imaging.load_png(src)
                data = zlib.compress(bytes(rgb), 9)
                filt = "/FlateDecode"
                cs = "/DeviceRGB"
            else:
                raise ValueError("PDF 贴图只支持 JPEG / PNG: %s" % src)

        name = "Im%d" % len(self._images)
        self._images.append((name, data, sw, sh, filt, cs))
        x, y, w, h = op["x"], op["y"], op["w"], op["h"]
        # PDF 原点在左下：y 需要翻转
        parts.append("q")
        parts.append("%s 0 0 %s %s %s cm"
                     % (_n(w), _n(h), _n(x), _n(self.h - y - h)))
        parts.append("/%s Do" % name)
        parts.append("Q")

    def _alpha_name(self, a):
        key = round(float(a), 3)
        name = self._alphas.get(key)
        if name is None:
            name = "GS%d" % len(self._alphas)
            self._alphas[key] = name
        return name

    def add_page(self, ops):
        """收集一页的 ops（先扫描 alpha，再生成内容流）。"""
        for op in ops:
            a = op.get("alpha", 1.0)
            if a < 0.999:
                self._alpha_name(a)
        parts = []
        parts.append("q")
        for op in ops:
            a = op.get("alpha", 1.0)
            if a < 0.999:
                parts.append("/%s gs" % self._alpha_name(a))
            if op["k"] == "image":
                self._image_ops(op, parts)
                continue
            path = op["path"]
            r, g, b = op["color"]
            r /= 255.0
            g /= 255.0
            b /= 255.0
            if op["k"] == "fill":
                _path_ops(path, self.h, parts)
                parts.append("%s %s %s rg" % (_n(r), _n(g), _n(b)))
                parts.append("f*" if op.get("rule") == "evenodd" else "f")
            else:
                _path_ops(path, self.h, parts)
                parts.append("%s %s %s RG" % (_n(r), _n(g), _n(b)))
                parts.append("%s w" % _n(op.get("width", 1.0)))
                parts.append("%d J" % _CAP.get(op.get("cap", "butt"), 0))
                parts.append("%d j" % _JOIN.get(op.get("join", "round"), 1))
                parts.append("S")
        parts.append("Q")
        self.pages.append("\n".join(parts))

    def save(self, path):
        n = len(self.pages)
        if n == 0:
            raise ValueError("PDF 没有页面")
        # 对象编号：1 Catalog, 2 Pages, 3+2i Page, 4+2i Contents, 之后 ExtGState
        gs_ids = {}
        gs_start = 3 + 2 * n
        for i, (alpha, name) in enumerate(sorted(self._alphas.items())):
            gs_ids[name] = gs_start + i
        img_start = gs_start + len(self._alphas)
        objs = {}

        kids = " ".join("%d 0 R" % (3 + 2 * i) for i in range(n))
        objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        objs[2] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, n)).encode("ascii")

        gs_res = " ".join("/%s %d 0 R" % (name, gid) for name, gid in gs_ids.items())
        xobj_res = " ".join("/%s %d 0 R" % (im[0], img_start + i)
                            for i, im in enumerate(self._images))
        res = "<< /ProcSet [/PDF /ImageC]"
        if gs_res:
            res += " /ExtGState << %s >>" % gs_res
        if xobj_res:
            res += " /XObject << %s >>" % xobj_res
        res += " >>"

        for i, content in enumerate(self.pages):
            page_id = 3 + 2 * i
            cont_id = 4 + 2 * i
            objs[page_id] = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %s %s] "
                             "/Contents %d 0 R /Resources %s >>"
                             % (_n(self.w), _n(self.h), cont_id, res)).encode("ascii")
            raw = content.encode("latin-1")
            comp = zlib.compress(raw, 9)
            objs[cont_id] = (("<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(comp))
                             .encode("ascii") + comp + b"\nendstream")

        for alpha, name in sorted(self._alphas.items()):
            objs[gs_ids[name]] = ("<< /Type /ExtGState /ca %s /CA %s >>"
                                  % (_n(alpha), _n(alpha))).encode("ascii")

        for i, (name, data, iw, ih, filt, cs) in enumerate(self._images):
            head = ("<< /Type /XObject /Subtype /Image /Width %d /Height %d "
                    "/ColorSpace %s /BitsPerComponent 8 %s /Length %d >>\nstream\n"
                    % (iw, ih, cs, filt, len(data)))
            objs[img_start + i] = head.encode("ascii") + data + b"\nendstream"

        out = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
        offsets = {}
        for oid in sorted(objs):
            offsets[oid] = len(out)
            out += ("%d 0 obj\n" % oid).encode("ascii")
            out += objs[oid]
            out += b"\nendobj\n"

        max_id = max(objs) + 1
        xref_pos = len(out)
        out += ("xref\n0 %d\n" % max_id).encode("ascii")
        out += b"0000000000 65535 f \n"
        for oid in range(1, max_id):
            if oid in offsets:
                out += ("%010d 00000 n \n" % offsets[oid]).encode("ascii")
            else:
                out += b"0000000000 65535 f \n"
        out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (max_id, xref_pos)).encode("ascii")
        with open(path, "wb") as fh:
            fh.write(bytes(out))
        return path


def render_pdf(canvases, out, size_pt):
    """canvases: 一个或多个 Canvas（多页 PDF）。size_pt: (w, h) 单位 pt。"""
    be = PDFBackend(size_pt[0], size_pt[1])
    if not isinstance(canvases, (list, tuple)):
        canvases = [canvases]
    for cv in canvases:
        be.add_page(cv.ops)
    return be.save(out)


def _jpeg_info(data):
    """从 JPEG 的 SOF 段读宽高与分量数（不解码像素）。"""
    import struct
    i = 2
    n = len(data)
    while i < n:
        if data[i] != 0xFF:
            i += 1
            continue
        m = data[i + 1]
        i += 2
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 3:i + 7])
            nc = data[i + 7]
            return w, h, nc
        if i + 2 > n:
            break
        ln = struct.unpack(">H", data[i:i + 2])[0]
        i += ln
    raise ValueError("JPEG 里找不到 SOF")
