# -*- coding: utf-8 -*-
"""tests/test_clip.py — 裁剪能力验收：形状内叠加光影/渐变/高光。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine import geometry as G
from engine import typography as T

OUT = os.path.join(BASE, "out")
PAPER = (246, 241, 230)

cv = Canvas(900, 380, ss=3, bg=PAPER)
MOSS = (58, 84, 66)
OCHRE = (150, 100, 58)
RED = (168, 62, 48)


def ball(cx, cy, r, base, lightc, darkc):
    """球体：底色 + 圆内渐变带 + 高光，全部靠 clip。"""
    cv.fill(G.circle(cx, cy, r), base)
    with cv.clip(G.circle(cx, cy, r)):
        # 横向渐变带（自左暗到右亮）
        steps = 44
        for i in range(steps):
            x0 = cx - r + 2 * r * i / steps
            x1 = cx - r + 2 * r * (i + 1) / steps + 0.5
            t = i / (steps - 1.0)
            c = (int(darkc[0] + (lightc[0] - darkc[0]) * t),
                 int(darkc[1] + (lightc[1] - darkc[1]) * t),
                 int(darkc[2] + (lightc[2] - darkc[2]) * t))
            cv.rect(x0, cy - r, x1, cy + r, c)
        # 底部接触阴影
        cv.fill(G.ellipse(cx, cy + r * 0.92, r * 0.95, r * 0.45), (0, 0, 0), alpha=0.22)
        # 高光（两个椭圆，被球体裁切）
        cv.fill(G.ellipse(cx + r * 0.34, cy - r * 0.38, r * 0.26, r * 0.17), (255, 255, 255), alpha=0.55)
        cv.fill(G.ellipse(cx + r * 0.28, cy - r * 0.52, r * 0.12, r * 0.08), (255, 255, 255), alpha=0.8)
        # 边缘反光
        cv.stroke(G.arc(cx, cy, r * 0.86, -0.4, 0.9), (255, 255, 255), width=r * 0.06, alpha=0.22)


ball(160, 190, 110, MOSS, (120, 160, 130), (22, 42, 32))
ball(430, 190, 110, OCHRE, (216, 168, 116), (78, 48, 24))
ball(700, 190, 110, RED, (226, 130, 114), (86, 24, 18))

label = "clip：球体渐变 + 高光 + 接触阴影"
cv.fill(T.text_path(label, 450, 345, 24, "kai", "regular", align="center"), (52, 40, 32),
        rule="evenodd")

p = os.path.join(OUT, "clip_demo.png")
t0 = time.time()
cv.to_png(p)
print("clip demo: %.2fs ops=%d %.0fKB" % (time.time() - t0, cv.op_count(),
                                          os.path.getsize(p) / 1024.0))
