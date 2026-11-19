# -*- coding: utf-8 -*-
"""offset.py — 描边：把路径折线扩成描边轮廓，交给 nonzero 填充。

为什么单独一层
--------------
「一眼看出是简单多边形」的两个主要来源是：
1. 曲线分段太粗（path.py 的自适应细分解决）
2. 线条是等宽硬折线、拐角是尖折角（本模块解决）

这里支持：cap = butt/square/round；join = miter/bevel/round。
轮廓用 nonzero 规则填充，所以同一笔画的重叠区不会互相挖空。
"""

import math

from .path import Path, _EPS

_DIST_EPS = 0.01


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _arc_pts(cx, cy, r, a0, a1, tol):
    """按弦高容差生成圆弧点列（含两端点）。"""
    da = a1 - a0
    if abs(da) < 1e-12 or r <= _EPS:
        return [(cx + r * math.cos(a0), cy + r * math.sin(a0))]
    if r <= tol:
        steps = 1
    else:
        cosv = max(-1.0, min(1.0, 1.0 - tol / r))
        dth = 2.0 * math.acos(cosv)
        steps = max(1, int(math.ceil(abs(da) / dth)))
    out = []
    for i in range(steps + 1):
        a = a0 + da * i / steps
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def _join(p, n0, n1, half, join, tol, miter_limit):
    """在顶点 p 处生成 join 点（不含两侧端点本身）。"""
    if join == "bevel":
        return [(p[0] + n0[0] * half, p[1] + n0[1] * half),
                (p[0] + n1[0] * half, p[1] + n1[1] * half)]
    if join == "miter":
        ux, uy = n0[0] + n1[0], n0[1] + n1[1]
        L = math.hypot(ux, uy)
        if L < 1e-6:                      # 180° 折返
            return [(p[0] + n0[0] * half, p[1] + n0[1] * half),
                    (p[0] + n1[0] * half, p[1] + n1[1] * half)]
        ux /= L; uy /= L
        cosh = ux * n0[0] + uy * n0[1]
        if cosh < 1.0 / miter_limit:
            return [(p[0] + n0[0] * half, p[1] + n0[1] * half),
                    (p[0] + n1[0] * half, p[1] + n1[1] * half)]
        m = half / cosh
        return [(p[0] + ux * m, p[1] + uy * m)]
    # round
    a0 = math.atan2(n0[1], n0[0])
    a1 = math.atan2(n1[1], n1[0])
    da = a1 - a0
    while da > math.pi:
        da -= 2.0 * math.pi
    while da < -math.pi:
        da += 2.0 * math.pi
    return _arc_pts(p[0], p[1], half, a0, a0 + da, tol)


def _offset_open(pts, half, side, join, tol, miter_limit):
    n = len(pts)
    if n < 2:
        return []
    segn = []
    for i in range(n - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        L = math.hypot(dx, dy)
        segn.append(None if L < _EPS else (-dy / L * side, dx / L * side))
    # 首个有效法线
    first = next((s for s in segn if s), None)
    if first is None:
        return []
    res = [(pts[0][0] + first[0] * half, pts[0][1] + first[1] * half)]
    for i in range(1, n - 1):
        n0, n1 = segn[i - 1], segn[i]
        if n0 is None:
            n0 = n1
        if n1 is None:
            n1 = n0
        if n0 is None:
            continue
        res.extend(_join(pts[i], n0, n1, half, join, tol, miter_limit))
    last = segn[-1] or first
    res.append((pts[-1][0] + last[0] * half, pts[-1][1] + last[1] * half))
    return res


def _offset_loop(pts, half, side, join, tol, miter_limit):
    """闭合环的偏移（每个顶点都做 join，首尾衔接）。"""
    n = len(pts)
    if n < 3:
        return []
    segn = []
    for i in range(n):
        j = (i + 1) % n
        dx = pts[j][0] - pts[i][0]
        dy = pts[j][1] - pts[i][1]
        L = math.hypot(dx, dy)
        segn.append(None if L < _EPS else (-dy / L * side, dx / L * side))
    res = []
    for i in range(n):
        n0 = segn[(i - 1) % n]
        n1 = segn[i]
        if n0 is None:
            n0 = n1
        if n1 is None:
            n1 = n0
        if n0 is None:
            continue
        res.extend(_join(pts[i], n0, n1, half, join, tol, miter_limit))
    return res


def _cap(p, a, b, direction, half, cap, tol):
    """端点 cap：返回从 a 到 b 的中间点列（不含 a、b 自身）。

    round 的关键是旋转方向：圆弧必须经过 `direction`（笔画外侧）。
    取错方向会让圆弧穿进笔画内部、与轮廓自交，渲染出「尖刺」。
    """
    if cap == "butt":
        return []
    if cap == "square":
        dx, dy = direction
        return [(a[0] + dx * half, a[1] + dy * half),
                (b[0] + dx * half, b[1] + dy * half)]
    a0 = math.atan2(a[1] - p[1], a[0] - p[0])
    a1 = math.atan2(b[1] - p[1], b[0] - p[0])
    da = a1 - a0
    while da <= -math.pi:
        da += 2.0 * math.pi
    while da > math.pi:
        da -= 2.0 * math.pi
    # a、b 大致关于 p 对称，短弧方向有二义性 → 用 direction 消歧
    ae = math.atan2(direction[1], direction[0])
    mid = a0 + da * 0.5
    if math.cos(mid - ae) < 0.0:
        da = da - 2.0 * math.pi if da > 0 else da + 2.0 * math.pi
    mids = _arc_pts(p[0], p[1], half, a0, a0 + da, tol)
    return mids[1:-1]


def stroke_path(path, width, cap="butt", join="round", tol=0.25, miter_limit=4.0):
    """把一条 Path 的每一段折线扩成描边轮廓，返回新的 Path（多为多轮廓）。"""
    half = float(width) * 0.5
    out = Path()
    if half <= 0:
        return out
    for pts in path.flatten(tol):
        if len(pts) < 2:
            continue
        closed = _dist(pts[0], pts[-1]) <= max(tol * 2.0, _DIST_EPS)
        if closed and len(pts) >= 4:
            loop = pts[:-1]
            if len(loop) < 3:
                continue
            outer = _offset_loop(loop, half, +1.0, join, tol, miter_limit)
            inner = _offset_loop(loop, half, -1.0, join, tol, miter_limit)
            inner.reverse()
            if len(outer) >= 3:
                out.move_to(*outer[0])
                for q in outer[1:]:
                    out.line_to(*q)
                out.close()
            if len(inner) >= 3:
                out.move_to(*inner[0])
                for q in inner[1:]:
                    out.line_to(*q)
                out.close()
        else:
            left = _offset_open(pts, half, +1.0, join, tol, miter_limit)
            right = _offset_open(pts, half, -1.0, join, tol, miter_limit)
            if len(left) < 2 or len(right) < 2:
                continue
            right.reverse()
            d_end = _norm(pts[-1], pts[-2])
            d_start = _norm(pts[0], pts[1])
            contour = list(left)
            contour += _cap(pts[-1], left[-1], right[0], d_end, half, cap, tol)
            contour += right
            contour += _cap(pts[0], right[-1], left[0], d_start, half, cap, tol)
            if len(contour) >= 3:
                out.move_to(*contour[0])
                for q in contour[1:]:
                    out.line_to(*q)
                out.close()
    return out


def _norm(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    L = math.hypot(dx, dy)
    if L < _EPS:
        return (0.0, 0.0)
    return (dx / L, dy / L)
