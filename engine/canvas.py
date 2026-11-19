# -*- coding: utf-8 -*-
"""canvas.py — 后端无关的显示列表（display list）。

Canvas 只记录「画什么」，不碰像素。真正的像素由 backends/ 下某个后端消费，
因此 PNG / SVG / PDF 三个出口共享同一份绘制描述，不会出现「出 PDF 少东西」。

图层（layer）
-------------
每个操作带一个 layer 标签，默认 "static"。约定：
- "static"  ：背景、纸纹、装饰、插画 —— 只由 theme / 骨架决定
- "dynamic" ：文字、数字、图表 —— 由 content 决定
渲染时可只重绘 dynamic 层再与缓存的 static 位图合成，这是改文案后快速出图的基础。
"""

from .path import Path


# ---------------------------------------------------------------- 颜色
_NAMED = {
    "black": (0, 0, 0), "white": (255, 255, 255),
    "red": (192, 0, 0), "green": (0, 128, 0), "blue": (31, 78, 121),
    "gray": (128, 128, 128), "grey": (128, 128, 128),
}


def parse_color(c):
    """接受 '#RRGGBB' / '#RRGGBBAA' / 'RGB' / (r,g,b) / (r,g,b,a) → (rgb, alpha)。"""
    if isinstance(c, str):
        s = c.strip()
        if s.startswith("#"):
            s = s[1:]
        if s.lower() in _NAMED:
            return _NAMED[s.lower()], 1.0
        if len(s) == 3:
            s = "".join(ch * 2 for ch in s)
        if len(s) == 6:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)), 1.0
        if len(s) == 8:
            return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)), int(s[6:8], 16) / 255.0
        raise ValueError("bad color: %r" % (c,))
    if isinstance(c, (tuple, list)):
        if len(c) == 3:
            return (int(c[0]), int(c[1]), int(c[2])), 1.0
        if len(c) == 4:
            a = c[3]
            return (int(c[0]), int(c[1]), int(c[2])), (a / 255.0 if a > 1 else float(a))
        if len(c) == 2:
            rgb, a = c
            return (int(rgb[0]), int(rgb[1]), int(rgb[2])), float(a)
    raise ValueError("bad color: %r" % (c,))


# ---------------------------------------------------------------- Canvas
class Canvas(object):
    def __init__(self, w, h, ss=2, bg=(255, 255, 255), layer="static"):
        self.w = int(w)
        self.h = int(h)
        self.ss = int(ss)
        self.bg = None if bg is None else parse_color(bg)[0]   # 背景不支持 alpha（P0）
        self.ops = []
        self._layer = layer
        self._bleed = False
        self._clip = None

    # -------- 裁剪（with cv.clip(path): ...） --------
    def clip(self, path):
        """上下文管理器：块内所有绘制都被裁剪到 path 内。

        有了裁剪，高光/阴影/渐变可以在任意形状内部叠加，不用再手工造月牙。
        """
        return _ClipCtx(self, path)

    # -------- 出血模式（背景装饰/素材包用） --------
    def bleed_mode(self, on=True):
        self._bleed = bool(on)
        return self

    # -------- 图层 --------
    def use_layer(self, name):
        self._layer = name
        return self

    def _push(self, op):
        op["layer"] = self._layer
        if self._bleed:
            op["allow_bleed"] = True
        if self._clip is not None:
            op["clip"] = self._clip
        self.ops.append(op)
        return self

    # -------- 基本操作 --------
    def fill(self, path, color, alpha=None, rule="evenodd", bleed=False):
        rgb, a = parse_color(color)
        if alpha is not None:
            a = float(alpha)
        op = {"k": "fill", "path": path, "color": rgb, "alpha": a, "rule": rule}
        if bleed:
            op["allow_bleed"] = True
        return self._push(op)

    def stroke(self, path, color, width=1.0, cap="butt", join="round", alpha=None):
        rgb, a = parse_color(color)
        if alpha is not None:
            a = float(alpha)
        return self._push({"k": "stroke", "path": path, "color": rgb, "alpha": a,
                           "width": float(width), "cap": cap, "join": join})

    # -------- 便捷封装（内部仍走 Path） --------
    def rect(self, x0, y0, x1, y1, color, **kw):
        return self.fill(Path.rect(x0, y0, x1, y1), color, **kw)

    def rrect(self, x0, y0, x1, y1, r, color, **kw):
        return self.fill(Path.rrect(x0, y0, x1, y1, r), color, **kw)

    def circle(self, cx, cy, r, color, **kw):
        return self.fill(Path.circle(cx, cy, r), color, **kw)

    def ellipse(self, cx, cy, rx, ry=None, color=(0, 0, 0), rot=0.0, **kw):
        return self.fill(Path.ellipse(cx, cy, rx, ry, rot), color, **kw)

    def line(self, x0, y0, x1, y1, color, width=1.0, cap="butt", **kw):
        p = Path()
        p.move_to(x0, y0).line_to(x1, y1)
        return self.stroke(p, color, width=width, cap=cap, **kw)

    def polyline(self, pts, color, width=1.0, cap="round", join="round", **kw):
        p = Path.from_polygon(pts, closed=False)
        return self.stroke(p, color, width=width, cap=cap, join=join, **kw)

    # -------- 查询 --------
    def bbox(self):
        xs0, ys0, xs1, ys1 = [], [], [], []
        for op in self.ops:
            x0, y0, x1, y1 = op["path"].bbox()
            pad = (op.get("width", 0.0) * 0.5) if op["k"] == "stroke" else 0.0
            xs0.append(x0 - pad); ys0.append(y0 - pad)
            xs1.append(x1 + pad); ys1.append(y1 + pad)
        if not xs0:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs0), min(ys0), max(xs1), max(ys1))

    def op_count(self):
        return len(self.ops)

    def path_points(self, tol=None):
        """所有路径细分后的总点数（诊断用）。"""
        tol = tol if tol is not None else 0.5 / self.ss
        return sum(op["path"].point_count(tol) for op in self.ops)

    # -------- 贴图（背景/素材） --------
    def image(self, src, x, y, w, h, alpha=1.0):
        """把一张图贴到画布上。

        src 可以是文件路径（PNG 全质量，JPEG 目前只解 DC 系数、偏模糊），
        也可以是 (w, h, rgb_bytes) 元组（已经解码好的像素）。
        """
        self._push({"k": "image", "src": src, "x": float(x), "y": float(y),
                    "w": float(w), "h": float(h), "alpha": float(alpha)})

    # -------- 输出 --------
    def to_png(self, out, exact=False, ss=None, layers=None, dpi=96):
        from .backends.raster import render_png
        return render_png(self, out, exact=exact, ss=ss, layers=layers, dpi=dpi)


class _ClipCtx(object):
    """with cv.clip(path): ... 的上下文管理器。"""

    def __init__(self, cv, path):
        self.cv = cv
        self.path = path
        self.prev = None

    def __enter__(self):
        self.prev = self.cv._clip
        self.cv._clip = self.path
        return self.cv

    def __exit__(self, *exc):
        self.cv._clip = self.prev
        return False
