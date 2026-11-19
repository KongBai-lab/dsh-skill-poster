# -*- coding: utf-8 -*-
"""backends/svg.py — 显示列表 → SVG（可无损缩放、可进设计软件二次编辑）。"""


def _n(v):
    s = "%.2f" % float(v)
    s = s.rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def _d(path):
    """Path 命令 → SVG path data。曲线保持贝塞尔，不做细分。"""
    out = []
    x = y = 0.0
    for c in path.cmds:
        k = c[0]
        if k == "M":
            x, y = c[1], c[2]
            out.append("M%s %s" % (_n(x), _n(y)))
        elif k == "L":
            x, y = c[1], c[2]
            out.append("L%s %s" % (_n(x), _n(y)))
        elif k == "C":
            out.append("C%s %s %s %s %s %s" % (
                _n(c[1]), _n(c[2]), _n(c[3]), _n(c[4]), _n(c[5]), _n(c[6])))
            x, y = c[5], c[6]
        elif k == "Q":
            out.append("Q%s %s %s %s" % (
                _n(c[1]), _n(c[2]), _n(c[3]), _n(c[4])))
            x, y = c[3], c[4]
        elif k == "Z":
            out.append("Z")
    return "".join(out)


def render_svg(canvas, out):
    w, h = canvas.w, canvas.h
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (w, h, w, h)]
    if canvas.bg:
        parts.append('<rect width="%d" height="%d" fill="%s"/>'
                     % (w, h, _hex(canvas.bg)))
    for op in canvas.ops:
        if op["k"] == "image":
            parts.append(_image_tag(op))
            continue
        d = _d(op["path"])
        a = op.get("alpha", 1.0)
        opac = (' opacity="%s"' % _n(a)) if a < 0.999 else ""
        if op["k"] == "fill":
            rule = ' fill-rule="evenodd"' if op.get("rule") == "evenodd" else ""
            parts.append('<path d="%s" fill="%s"%s%s/>'
                         % (d, _hex(op["color"]), rule, opac))
        else:
            cap = {"butt": "butt", "round": "round", "square": "square"}.get(op.get("cap"), "butt")
            join = {"miter": "miter", "round": "round", "bevel": "bevel"}.get(op.get("join"), "round")
            parts.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" '
                         'stroke-linecap="%s" stroke-linejoin="%s"%s/>'
                         % (d, _hex(op["color"]), _n(op.get("width", 1.0)), cap, join, opac))
    parts.append("</svg>")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(parts))
    return out


def _image_tag(op):
    """贴图 → <image> + base64 data URI（不重新编码，直接用原文件字节）。"""
    import base64
    import os

    src = op["src"]
    x, y, w, h = op["x"], op["y"], op["w"], op["h"]
    a = op.get("alpha", 1.0)
    opac = (' opacity="%s"' % _n(a)) if a < 0.999 else ""
    if isinstance(src, tuple):
        return ""   # 元组源暂不支持 SVG
    low = str(src).lower()
    if low.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif low.endswith(".png"):
        mime = "image/png"
    else:
        return ""
    try:
        raw = open(src, "rb").read()
    except Exception:
        return ""
    b64 = base64.b64encode(raw).decode("ascii")
    return ('<image x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="none"%s '
            'href="data:%s;base64,%s"/>'
            % (_n(x), _n(y), _n(w), _n(h), opac, mime, b64))
