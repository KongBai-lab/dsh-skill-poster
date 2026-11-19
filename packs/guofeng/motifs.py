# -*- coding: utf-8 -*-
"""packs/guofeng/motifs.py — 国风装饰素材包。

接口约定：fn(cv, ...坐标/尺寸..., color, alpha=...)
- 颜色由调用方传入（通常来自 theme.palette），素材本身不含品牌色
- 全部走 engine.geometry 的参数化图元，不手写点列
- 只依赖 display list API（fill/stroke），因此 PNG / SVG / PDF 三后端都可用
"""

import math

from engine import geometry as G
from engine.path import Path


def mountains_soft(cv, x, y, w, h, color, alpha=0.18, layers=3, seed=3):
    """层叠远山：越远越淡。"""
    for i in range(layers):
        t = i / float(max(1, layers - 1))
        yy = y + h * (0.34 + 0.30 * t)
        hh = h * (0.62 - 0.10 * t)
        cv.fill(G.mountains(x, yy, x + w, yy + hh, peaks=3 + (i % 2),
                            seed=seed + i * 17, jitter=0.45),
                color, alpha=alpha * (1.0 - 0.22 * i))


def cloud_soft(cv, cx, cy, w, color, alpha=0.5):
    """轻柔云带（两层错位）。"""
    cv.fill(G.cloud(cx, cy, w), color, alpha=alpha)
    cv.fill(G.cloud(cx + w * 0.22, cy + w * 0.10, w * 0.72), color, alpha=alpha * 0.7)


def waves(cv, x0, y, x1, color, alpha=0.28, amp=None):
    """水波纹（三条错位描边）。"""
    w = x1 - x0
    a = amp if amp else max(3.0, w * 0.018)
    for i in range(3):
        cv.stroke(G.wave(x0, y + i * a * 1.5, x1, y + i * a * 1.5, a,
                         periods=3 + i, taper=0.7),
                  color, width=max(1.0, a * 0.16), alpha=alpha, cap="round")


def bamboo(cv, x, y_top, y_bottom, color, alpha=0.30, stalks=2, seed=2):
    """竹：直杆 + 分节 + 几片叶。"""
    s = seed
    for k in range(stalks):
        bx = x + k * (y_bottom - y_top) * 0.055
        cv.stroke(_line(bx, y_top, bx + (k - 0.5) * 12, y_bottom),
                  color, width=max(1.5, (y_bottom - y_top) * 0.0045), alpha=alpha)
        n = max(3, int((y_bottom - y_top) / 70))
        for i in range(n):
            ty = y_top + (y_bottom - y_top) * (i + 0.5) / n
            cv.stroke(_line(bx - 10, ty, bx + 10, ty), color,
                      width=max(0.8, (y_bottom - y_top) * 0.0022), alpha=alpha * 0.8)
            s = (s * 1103515245 + 12345) & 0x7fffffff
            side = -1 if (s >> 8) % 2 else 1
            cv.fill(G.leaf(bx, ty, 42 + (s >> 10) % 26, 13,
                           angle=(-0.7 if side < 0 else -2.45)),
                    color, alpha=alpha * 0.85)


def seal_red(cv, x, y, size, color, text=None, alpha=0.92):
    """朱印：双线方框 + 可选竖排文字。"""
    cv.fill(G.seal_frame(x, y, size, r=size * 0.10, pad=size * 0.10),
            color, alpha=alpha)
    cv.stroke(G.rrect(x - size * 0.5, y - size * 0.5, x + size * 0.5, y + size * 0.5,
                      size * 0.09),
              color, width=max(1.0, size * 0.05), alpha=alpha)
    if text:
        from engine import typography as T
        from engine.fonts import advance
        s = size * 0.30
        total = len(text) * s * 1.12
        path = T.vtext_path(text, x, y - total * 0.5, s, "li", "regular",
                            tracking=0.10)
        cv.fill(path, (255, 255, 255), rule="evenodd", alpha=0.95)


def _line(x0, y0, x1, y1):
    p = Path()
    p.move_to(x0, y0).line_to(x1, y1)
    return p
