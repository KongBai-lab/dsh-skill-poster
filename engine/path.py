# -*- coding: utf-8 -*-
"""path.py — 后端无关的贝塞尔路径模型。

设计原则
--------
1. 所有图元（圆、弧、圆角、叶片、云…）都构造 Path，而不是手写点列。
2. 曲线在「光栅化时」才按屏幕误差自适应细分；SVG / PDF 后端直接输出曲线命令。
   这样精细度由渲染端统一保证，矢量格式无损且文件更小。
3. 坐标一律是**逻辑坐标**（与画布 W×H 同单位）。细分容差 tol 也以逻辑像素计：
   调用方通常传 0.5 / ss，即「半个采样像素」。
"""

import math

MAX_DEPTH = 14          # 递归细分上限，防病态曲线炸栈
_EPS = 1e-9


# ---------------------------------------------------------------- 工具
def _mid(a, b):
    return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _flat3(p0, p1, p2, p3):
    """三次贝塞尔的平直度：两个控制点到弦的距离取大者。

    曲线实际偏离弦 <= (3/4)·max(d1,d2)，这里取 max 作保守上界，
    因此 `tol` 是保证值而不是估计值。
    """
    dx, dy = p3[0] - p0[0], p3[1] - p0[1]
    L = math.hypot(dx, dy)
    if L < _EPS:
        return max(_dist(p1, p0), _dist(p2, p0))
    d1 = abs((p1[0] - p0[0]) * dy - (p1[1] - p0[1]) * dx) / L
    d2 = abs((p2[0] - p0[0]) * dy - (p2[1] - p0[1]) * dx) / L
    return d1 if d1 > d2 else d2


def _subdiv3(p0, p1, p2, p3, tol, depth, out):
    """de Casteljau 自适应细分，把终点追加进 out。"""
    if depth >= MAX_DEPTH or _flat3(p0, p1, p2, p3) <= tol:
        out.append(p3)
        return
    p01 = _mid(p0, p1)
    p12 = _mid(p1, p2)
    p23 = _mid(p2, p3)
    p012 = _mid(p01, p12)
    p123 = _mid(p12, p23)
    m = _mid(p012, p123)
    _subdiv3(p0, p01, p012, m, tol, depth + 1, out)
    _subdiv3(m, p123, p23, p3, tol, depth + 1, out)


def _quad_to_cubic(p0, p1, p2):
    """二次贝塞尔升阶为三次。"""
    c1 = (p0[0] + 2.0 / 3.0 * (p1[0] - p0[0]), p0[1] + 2.0 / 3.0 * (p1[1] - p0[1]))
    c2 = (p2[0] + 2.0 / 3.0 * (p1[0] - p2[0]), p2[1] + 2.0 / 3.0 * (p1[1] - p2[1]))
    return c1, c2


# ---------------------------------------------------------------- Path
class Path(object):
    """路径命令流：M / L / C / Q / Z。可变换、可细分、可转多边形。"""

    __slots__ = ("cmds", "_cache", "_cache_tol")

    def __init__(self, cmds=None):
        self.cmds = list(cmds) if cmds else []
        self._cache = None
        self._cache_tol = 1e9

    # ---------------- 构造 ----------------
    @classmethod
    def from_polygon(cls, pts, closed=True):
        p = cls()
        if not pts:
            return p
        p.move_to(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.line_to(x, y)
        if closed:
            p.close()
        return p

    @classmethod
    def rect(cls, x0, y0, x1, y1):
        return cls.from_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    @classmethod
    def rrect(cls, x0, y0, x1, y1, r):
        """圆角矩形。r 会被夹到短边一半。"""
        w, h = x1 - x0, y1 - y0
        r = max(0.0, min(r, abs(w) * 0.5, abs(h) * 0.5))
        if r <= _EPS:
            return cls.rect(x0, y0, x1, y1)
        k = 0.5522847498307936 * r          # 四分之一圆弧的贝塞尔控制系数
        p = cls()
        p.move_to(x0 + r, y0)
        p.line_to(x1 - r, y0)
        p.cubic_to(x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r)
        p.line_to(x1, y1 - r)
        p.cubic_to(x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1)
        p.line_to(x0 + r, y1)
        p.cubic_to(x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r)
        p.line_to(x0, y0 + r)
        p.cubic_to(x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0)
        p.close()
        return p

    @classmethod
    def ellipse(cls, cx, cy, rx, ry=None, rot=0.0):
        if ry is None:
            ry = rx
        k = 0.5522847498307936
        pts = [(cx + rx, cy), (cx, cy + ry), (cx - rx, cy), (cx, cy - ry)]
        ctrl = [(cx + rx, cy + k * ry), (cx + k * rx, cy + ry),
                (cx - k * rx, cy + ry), (cx - rx, cy + k * ry),
                (cx - rx, cy - k * ry), (cx - k * rx, cy - ry),
                (cx + k * rx, cy - ry), (cx + rx, cy - k * ry)]
        p = cls()
        p.move_to(*pts[0])
        # 四段：每段起点->终点，两个控制点
        segs = [(0, 1), (1, 2), (2, 3), (3, 0)]
        for i, (a, b) in enumerate(segs):
            c1 = ctrl[i * 2]
            c2 = ctrl[i * 2 + 1]
            p.cubic_to(c1[0], c1[1], c2[0], c2[1], pts[b][0], pts[b][1])
        p.close()
        if rot:
            return p.rotated(rot, cx, cy)
        return p

    @classmethod
    def circle(cls, cx, cy, r):
        return cls.ellipse(cx, cy, r, r)

    @classmethod
    def arc(cls, cx, cy, r, a0, a1, rx=None, ry=None):
        """圆弧 / 椭圆弧，角度用弧度，按 <=90° 分段转贝塞尔。"""
        rx = r if rx is None else rx
        ry = r if ry is None else ry
        p = cls()
        span = a1 - a0
        n = max(1, int(math.ceil(abs(span) / (math.pi * 0.5))))
        step = span / n
        k = 4.0 / 3.0 * math.tan(step / 4.0)
        a = a0
        for _ in range(n):
            ca, sa = math.cos(a), math.sin(a)
            cb, sb = math.cos(a + step), math.sin(a + step)
            x0, y0 = cx + rx * ca, cy + ry * sa
            x3, y3 = cx + rx * cb, cy + ry * sb
            # 椭圆参数方程导数 p'(a) = (-rx·sin a, ry·cos a)
            c1 = (x0 - rx * sa * k, y0 + ry * ca * k)
            c2 = (x3 + rx * sb * k, y3 - ry * cb * k)
            if a == a0:
                p.move_to(x0, y0)
            p.cubic_to(c1[0], c1[1], c2[0], c2[1], x3, y3)
            a += step
        return p

    @classmethod
    def ring(cls, cx, cy, r_out, r_in, sides=None):
        """圆环（外圆 + 内圆，even-odd 挖洞；side 参数保留兼容）。"""
        p = cls.circle(cx, cy, r_out)
        p.extend(cls.circle(cx, cy, r_in))
        return p

    # ---------------- 编辑 ----------------
    def move_to(self, x, y):
        self.cmds.append(("M", float(x), float(y)))
        self._invalidate()
        return self

    def line_to(self, x, y):
        self.cmds.append(("L", float(x), float(y)))
        self._invalidate()
        return self

    def cubic_to(self, x1, y1, x2, y2, x3, y3):
        self.cmds.append(("C", float(x1), float(y1), float(x2), float(y2), float(x3), float(y3)))
        self._invalidate()
        return self

    def quad_to(self, x1, y1, x2, y2):
        self.cmds.append(("Q", float(x1), float(y1), float(x2), float(y2)))
        self._invalidate()
        return self

    def close(self):
        self.cmds.append(("Z",))
        self._invalidate()
        return self

    def extend(self, other):
        """拼接另一条 Path 的命令（用于多轮廓，如圆环）。"""
        self.cmds.extend(other.cmds)
        self._invalidate()
        return self

    def _invalidate(self):
        self._cache = None
        self._cache_tol = 1e9

    def copy(self):
        return Path(self.cmds)

    # ---------------- 变换 ----------------
    def transform(self, fn):
        """fn(x, y) -> (x, y)，原地变换并返回 self。"""
        out = []
        for c in self.cmds:
            k = c[0]
            if k in ("M", "L"):
                x, y = fn(c[1], c[2])
                out.append((k, x, y))
            elif k == "C":
                x1, y1 = fn(c[1], c[2])
                x2, y2 = fn(c[3], c[4])
                x3, y3 = fn(c[5], c[6])
                out.append((k, x1, y1, x2, y2, x3, y3))
            elif k == "Q":
                x1, y1 = fn(c[1], c[2])
                x2, y2 = fn(c[3], c[4])
                out.append((k, x1, y1, x2, y2))
            else:
                out.append(c)
        self.cmds = out
        self._invalidate()
        return self

    def translated(self, dx, dy):
        return self.copy().transform(lambda x, y: (x + dx, y + dy))

    def scaled(self, sx, sy=None, cx=0.0, cy=0.0):
        sy = sx if sy is None else sy
        return self.copy().transform(lambda x, y: (cx + (x - cx) * sx, cy + (y - cy) * sy))

    def rotated(self, ang, cx=0.0, cy=0.0):
        c, s = math.cos(ang), math.sin(ang)
        return self.copy().transform(
            lambda x, y: (cx + (x - cx) * c - (y - cy) * s,
                          cy + (x - cx) * s + (y - cy) * c))

    # ---------------- 几何 ----------------
    def bbox(self):
        xs, ys = [], []
        for c in self.cmds:
            if c[0] in ("M", "L"):
                xs.append(c[1]); ys.append(c[2])
            elif c[0] == "C":
                xs += [c[1], c[3], c[5]]; ys += [c[2], c[4], c[6]]
            elif c[0] == "Q":
                xs += [c[1], c[3]]; ys += [c[2], c[4]]
        if not xs:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), max(xs), max(ys))

    def flatten(self, tol=0.25):
        """自适应细分成多边形轮廓：returns [ [(x,y), ...], ... ]。

        tol 是逻辑坐标下的最大弦高误差；0.5/ss 即半个采样像素。
        """
        if self._cache is not None and tol >= self._cache_tol:
            return self._cache
        contours = []
        cur = []
        x = y = 0.0
        sx = sy = 0.0
        for c in self.cmds:
            k = c[0]
            if k == "M":
                if len(cur) > 1:
                    contours.append(cur)
                x, y = c[1], c[2]
                sx, sy = x, y
                cur = [(x, y)]
            elif k == "L":
                x, y = c[1], c[2]
                cur.append((x, y))
            elif k == "C":
                p0 = (x, y)
                p1 = (c[1], c[2]); p2 = (c[3], c[4]); p3 = (c[5], c[6])
                _subdiv3(p0, p1, p2, p3, tol, 0, cur)
                x, y = p3
            elif k == "Q":
                p0 = (x, y)
                p1 = (c[1], c[2]); p2 = (c[3], c[4])
                c1, c2 = _quad_to_cubic(p0, p1, p2)
                _subdiv3(p0, c1, c2, p2, tol, 0, cur)
                x, y = p2
            elif k == "Z":
                if len(cur) > 1:
                    if _dist(cur[0], cur[-1]) > _EPS:
                        cur.append(cur[0])
                    contours.append(cur)
                cur = []
                x, y = sx, sy
        if len(cur) > 1:
            contours.append(cur)
        # 去掉相邻重复点（扫描线会因此产生零长边）
        clean = []
        for contour in contours:
            c2 = [contour[0]]
            for pt in contour[1:]:
                if _dist(pt, c2[-1]) > _EPS:
                    c2.append(pt)
            # 保留 2 点轮廓：填充会自己跳过 <3 点，但描边（直线段）必须拿到它
            if len(c2) >= 2:
                clean.append(c2)
        self._cache = clean
        self._cache_tol = tol
        return clean

    def point_count(self, tol=0.25):
        return sum(len(c) for c in self.flatten(tol))


# ---------------------------------------------------------------- 测试辅助
def chord_error(path, tol, samples=64):
    """实测 Path 细分后的最大弦高误差（check.py 几何断言用，近似值）。

    对每条曲线均匀采样 samples 个原始曲线点，量它到细分折线的最短距离。
    与参数化方式无关，因此对自适应细分也成立。
    """
    worst = 0.0
    x = y = 0.0
    for c in path.cmds:
        k = c[0]
        if k == "M":
            x, y = c[1], c[2]
        elif k == "L":
            x, y = c[1], c[2]
        elif k in ("C", "Q"):
            if k == "C":
                p0 = (x, y); p1 = (c[1], c[2]); p2 = (c[3], c[4]); p3 = (c[5], c[6])
            else:
                p0 = (x, y); p3 = (c[3], c[4])
                p1, p2 = _quad_to_cubic(p0, (c[1], c[2]), p3)
            seg = [p0]
            _subdiv3(p0, p1, p2, p3, tol, 0, seg)
            if len(seg) > 1:
                for j in range(1, samples):
                    q = _bez3(p0, p1, p2, p3, j / float(samples))
                    d = min(_point_seg_dist(q, a, b) for a, b in zip(seg[:-1], seg[1:]))
                    if d > worst:
                        worst = d
            x, y = p3
    return worst


def _point_seg_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 < _EPS:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / L2
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _bez3(p0, p1, p2, p3, t):
    u = 1.0 - t
    a = u * u * u
    b = 3 * u * u * t
    c = 3 * u * t * t
    d = t * t * t
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
            a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])
