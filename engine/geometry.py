# -*- coding: utf-8 -*-
"""geometry.py — 参数化图元库。

约定
----
- 全部返回 Path：后端无关、自适应细分、SVG/PDF 无损。
- 只接受解析参数。调用方**不需要也不能**手写点列（直边多边形除外，用 polygon()）。
- 所有图元先在局部坐标系构造，再按 angle / (cx,cy) 放置。

这条约定是「一眼看出多边形凑数」的制度性解法：形状质量集中在库里，
而不是散落在每个调用点。
"""

import math

from .path import Path

PI = math.pi
TAU = PI * 2.0


def _join(p, q):
    """把 q 接到 p 之后（去掉 q 的首个 M，视为同一条子路径的延续）。"""
    cmds = q.cmds
    if not cmds:
        return p
    i = 1 if cmds[0][0] == "M" else 0
    p.cmds.extend(cmds[i:])
    p._invalidate()
    return p


def _place(p, cx, cy, angle=0.0):
    if angle:
        p = p.rotated(angle)
    return p.translated(cx, cy)


# ================================================================ 基础几何
def circle(cx, cy, r):
    return Path.circle(cx, cy, r)


def ellipse(cx, cy, rx, ry=None, rot=0.0):
    return Path.ellipse(cx, cy, rx, ry, rot)


def arc(cx, cy, r, a0, a1, rx=None, ry=None):
    return Path.arc(cx, cy, r, a0, a1, rx, ry)


def ring(cx, cy, r_out, r_in):
    """圆环（evenodd 挖洞）。"""
    p = Path.circle(cx, cy, r_out)
    p.extend(Path.circle(cx, cy, r_in))
    return p


def pie(cx, cy, r, a0, a1, rx=None, ry=None):
    """扇形（含圆心）。"""
    rx = r if rx is None else rx
    ry = r if ry is None else ry
    p = Path()
    p.move_to(cx, cy)
    p.line_to(cx + rx * math.cos(a0), cy + ry * math.sin(a0))
    _join(p, Path.arc(cx, cy, r, a0, a1, rx, ry))
    p.close()
    return p


def donut_sector(cx, cy, r_out, r_in, a0, a1):
    """环扇形。"""
    p = Path()
    p.move_to(cx + r_out * math.cos(a0), cy + r_out * math.sin(a0))
    _join(p, Path.arc(cx, cy, r_out, a0, a1))
    p.line_to(cx + r_in * math.cos(a1), cy + r_in * math.sin(a1))
    _join(p, Path.arc(cx, cy, r_in, a1, a0))
    p.close()
    return p


def rrect(x0, y0, x1, y1, r):
    return Path.rrect(x0, y0, x1, y1, r)


def capsule(x0, y0, x1, y1, r):
    """胶囊：线段 + 两端半圆。"""
    ang = math.atan2(y1 - y0, x1 - x0)
    ca, sa = math.cos(ang), math.sin(ang)
    p = Path()
    p.move_to(x0 - sa * r, y0 + ca * r)
    p.line_to(x1 - sa * r, y1 + ca * r)
    _join(p, Path.arc(x1, y1, r, ang + PI / 2, ang - PI / 2))
    p.line_to(x0 + sa * r, y0 - ca * r)
    _join(p, Path.arc(x0, y0, r, ang - PI / 2, ang - PI * 1.5))
    p.close()
    return p


def polygon(pts, closed=True):
    """直边多边形（逃生舱：只用于本来就是直边的形状）。"""
    return Path.from_polygon(pts, closed=closed)


def regular_polygon(cx, cy, r, n, rot=0.0):
    pts = [(cx + r * math.cos(rot + TAU * i / n),
            cy + r * math.sin(rot + TAU * i / n)) for i in range(n)]
    return Path.from_polygon(pts)


def star(cx, cy, r_out, r_in, points=5, rot=-PI / 2, round_tips=0.0):
    """n 角星。round_tips>0 时用贝塞尔把尖角磨圆。"""
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + PI * i / points
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if round_tips <= 0:
        return Path.from_polygon(pts)
    # 尖角圆化：在每段直线间插入一小段曲线
    p = Path()
    n = len(pts)
    p.move_to(*pts[0])
    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        k = round_tips
        p.cubic_to(a[0] + dx * k, a[1] + dy * k,
                   b[0] - dx * k, b[1] - dy * k, b[0], b[1])
    p.close()
    return p


# ================================================================ 自然形
def leaf(cx, cy, length, width=None, angle=0.0, bend=0.16, waist=0.55):
    """叶片：叶柄在 (0,0)，尖端在 (length,0)。bend 让叶子弯。"""
    L = float(length)
    W = float(width if width is not None else L * 0.42)
    p = Path()
    p.move_to(0, 0)
    p.cubic_to(L * 0.18, -W * 1.05 + bend * W,
               L * 0.66, -W * 0.92 + bend * W, L, 0)
    p.cubic_to(L * 0.66, W * 0.92 + bend * W,
               L * 0.18, W * 1.05 + bend * W, 0, 0)
    p.close()
    return _place(p, cx, cy, angle)


def petal(cx, cy, length, width=None, angle=0.0):
    """花瓣：底部圆润、顶部收尖。"""
    L = float(length)
    W = float(width if width is not None else L * 0.46)
    p = Path()
    p.move_to(0, 0)
    p.cubic_to(L * 0.16, -W * 0.98, L * 0.88, -W * 0.62, L, 0)
    p.cubic_to(L * 0.88, W * 0.62, L * 0.16, W * 0.98, 0, 0)
    p.close()
    return _place(p, cx, cy, angle)


def flower(cx, cy, r, petals=5, angle=0.0, petal_width=None, center_r=0.0):
    """多花瓣花。

    花瓣是**多个独立子路径叠加**，请用 rule="nonzero" 填充：
    evenodd 会把瓣与瓣的重叠区挖成镂空（镂空花也是一种可选风格）。
    """
    p = Path()
    pw = petal_width if petal_width else r * math.sin(PI / petals) * 0.72
    for i in range(petals):
        a = angle + TAU * i / petals
        q = petal(0, 0, r, pw, angle=a)
        q = q.translated(cx, cy)
        p.extend(q)
    if center_r > 0:
        p.extend(circle(cx, cy, center_r))
    return p


def drop(cx, cy, r, tip=2.15):
    """水滴：圆底 + 尖顶，尖点在上方。"""
    t = -r * (tip - 1.0)
    p = Path()
    p.move_to(0, t)
    p.cubic_to(r * 0.52, t * 0.48, r * 1.02, -r * 0.42, r * 0.866, r * 0.5)
    p.cubic_to(r * 0.866, r * 0.93, r * 0.30, r, 0, r)
    p.cubic_to(-r * 0.30, r, -r * 0.866, r * 0.93, -r * 0.866, r * 0.5)
    p.cubic_to(-r * 1.02, -r * 0.42, -r * 0.52, t * 0.48, 0, t)
    p.close()
    return _place(p, cx, cy)


def cloud(cx, cy, w, h=None, bumps=4, angle=0.0):
    """云：两端半圆收口 + 上缘大波浪 + 下缘小波浪（标准矢量云画法）。

    关键：左右两端各用一个半圆从下缘绕到上缘，轮廓不会在基线上相交，
    所以不会出现尖角；上缘凸起控制点与端点同高，避免拉出「尾巴」。
    """
    h = float(h if h is not None else w * 0.46)
    n = max(2, int(bumps))
    base = h * 0.50          # 下缘基准线
    r = h * 0.205            # 端帽半径
    top = base - 2.0 * r     # 上缘基准线
    bump = h * 0.165         # 上缘凸起高度（平缓）
    x0, x1 = -w / 2, w / 2
    k = 0.5523 * r           # 四分之一圆的贝塞尔系数

    p = Path()
    # 左下起点 → 左端半圆（左侧绕到顶部）
    p.move_to(x0, base - r)
    p.cubic_to(x0, base - r - k, x0 + r - k, top, x0 + r, top)
    # 上缘：n 个大小错落的凸起（等宽等高的鼓包看起来像毛毛虫）
    inner = x1 - r - (x0 + r)
    weights = [0.62 + 0.38 * math.sin(PI * (i + 0.5) / n) for i in range(n)]
    wsum = sum(weights)
    cursor = x0 + r
    for i in range(n):
        seg = inner * weights[i] / wsum
        ax = cursor
        bx = cursor + seg
        cursor = bx
        hh = bump * (0.62 + 0.38 * math.sin(PI * (i + 0.5) / n))
        # 峰处切线水平（圆顶），谷处控制点抬高减少，夹角更钝
        p.cubic_to(ax + seg * 0.30, top - hh * 0.72,
                   bx - seg * 0.30, top - hh * 0.72,
                   bx, top)
    # 右端半圆（顶部绕到右下）
    p.cubic_to(x1 - r + k, top, x1, base - r - k, x1, base - r)
    # 下缘：从右到左的浅波浪
    nb = max(2, n - 1)
    span = (x1 - x0) / nb
    for i in range(nb):
        ax = x1 - i * span
        bx = ax - span
        dip = h * (0.022 + 0.014 * math.sin(PI * (i + 0.5) / nb))
        p.cubic_to(ax - span * 0.34, base - r + dip,
                   bx + span * 0.34, base - r + dip,
                   bx, base - r)
    p.close()
    return _place(p, cx, cy, angle)


def wave(x0, y0, x1, y1, amp, periods=2, taper=0.0):
    """正弦波（开放路径，用于描边）。每半周期一段三次贝塞尔。"""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-9:
        return Path()
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    p = Path()
    p.move_to(x0, y0)
    n = max(1, int(periods * 2))
    seg = L / n
    k = seg * 0.3636          # 三次贝塞尔近似半正弦的控制点系数
    for i in range(n):
        s = 1.0 if i % 2 == 0 else -1.0
        t = (i + 1) / float(n)
        taper_k = 1.0 - taper * abs(t - 0.5) * 2.0
        s *= max(0.0, taper_k)
        ax = x0 + ux * seg * i
        ay = y0 + uy * seg * i
        bx = x0 + ux * seg * (i + 1)
        by = y0 + uy * seg * (i + 1)
        p.cubic_to(ax + ux * seg / 3 + nx * amp * s,
                   ay + uy * seg / 3 + ny * amp * s,
                   bx - ux * seg / 3 + nx * amp * s,
                   by - uy * seg / 3 + ny * amp * s, bx, by)
    return p


def mountains(x0, y0, x1, y1, peaks=3, seed=1, jitter=0.35):
    """山形：确定性伪随机的连续山脉，底部闭合。"""
    w = x1 - x0
    h = y1 - y0
    rnd = _Rand(seed)
    p = Path()
    p.move_to(x0, y1)
    x = x0
    for i in range(peaks):
        seg = w / peaks
        xm = x + seg * (0.42 + 0.16 * rnd.next())
        peak_h = h * (0.55 + jitter * rnd.next())
        xr = x + seg
        # 左坡（凹）+ 右坡（凸）
        p.cubic_to(x + seg * 0.18, y1 - peak_h * 0.42,
                   xm - seg * 0.24, y1 - peak_h, xm, y1 - peak_h)
        p.cubic_to(xm + seg * 0.26, y1 - peak_h * 0.86,
                   xr - seg * 0.14, y1 - peak_h * 0.30, xr, y1 - h * 0.06)
        x = xr
    p.line_to(x1, y1)
    p.close()
    return p


def heart(cx, cy, size, angle=0.0):
    """心形（两段贝塞尔 + 底部尖角）。"""
    s = float(size) * 0.5
    p = Path()
    p.move_to(0, s * 0.92)
    p.cubic_to(-s * 1.42, s * 0.06, -s * 0.94, -s * 1.02, 0, -s * 0.34)
    p.cubic_to(s * 0.94, -s * 1.02, s * 1.42, s * 0.06, 0, s * 0.92)
    p.close()
    return _place(p, cx, cy, angle)


def sparkle(cx, cy, r, points=4, inner=0.24, angle=-PI / 2):
    """星芒（凹边），适合点缀与「闪」效果。"""
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner
        a = angle + PI * i / points
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    p = Path()
    p.move_to(*pts[0])
    for i in range(1, len(pts)):
        p.line_to(*pts[i])
    # 尖角用二次曲线微收，避免死板的直边
    p.close()
    return _place(p, cx, cy)


# ================================================================ 装饰
def seal_frame(cx, cy, size, r=5.0, pad=5.0, double=True):
    """印章方框：外框 + 内框（evenodd 双线）。"""
    s = size * 0.5
    p = Path.rrect(cx - s, cy - s, cx + s, cy + s, r)
    if double:
        q = Path.rrect(cx - s + pad, cy - s + pad, cx + s - pad, cy + s - pad, max(0.0, r - pad * 0.5))
        p.extend(q)
    return p


def corner_ornament(cx, cy, size, corner="tl", curl=0.42):
    """角饰：一段卷云纹（开放路径，描边用）。corner 决定朝向。"""
    s = float(size)
    p = Path()
    p.move_to(0, 0)
    p.cubic_to(s * 0.58, 0, s * 0.86, -s * 0.12, s * 0.96, -s * 0.46)
    p.cubic_to(s * 1.02, -s * 0.74, s * 0.72, -s * 0.94, s * 0.46, -s * 0.80)
    p.cubic_to(s * 0.28, -s * 0.70, s * 0.30, -s * 0.46, s * 0.48, -s * 0.44)
    sx = -1.0 if corner in ("tl", "bl") else 1.0
    sy = -1.0 if corner in ("tl", "tr") else 1.0
    p.transform(lambda x, y: (cx + x * sx, cy + y * sy))
    return p


def divider_wave(x0, x1, y, amp=6.0, periods=4):
    """云纹分隔线（开放路径）。"""
    return wave(x0, y, x1, y, amp, periods=periods, taper=0.9)


# ================================================================ 内部
class _Rand(object):
    """确定性伪随机（避免依赖 random 全局状态，保证可复现）。"""

    def __init__(self, seed=1):
        self.s = (seed * 1103515245 + 12345) & 0x7fffffff

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7fffffff
        return (self.s >> 8) / 16777216.0
