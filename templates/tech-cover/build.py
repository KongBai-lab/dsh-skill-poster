# -*- coding: utf-8 -*-
"""templates/tech-cover/build.py — C 模式示例：科技/物理风格封面（自绘）。

不需要骨架：这张图的版式是一次性的，直接用 Canvas 画。
配色走 theme 的 tech 一套，文字走 typography，输出走同一条三后端管线。
"""
import math
import os
import sys

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE)

from engine.canvas import Canvas
from engine import geometry as G
from engine import typography as T
from engine.path import Path
from engine.backends.pdf import render_pdf
from engine.backends.svg import render_svg

W, H, SS = 1920, 1080, 3

BG = (8, 11, 18)
FG = (230, 237, 245)
BLUE = (77, 157, 224)
CYAN = (95, 211, 196)
MUTED = (107, 122, 140)
GRID = (26, 38, 54)
GRID2 = (40, 58, 82)


def build():
    cv = Canvas(W, H, ss=SS, bg=BG)

    # ---------- 1. 背景：网格 + 渐隐 ----------
    for x in range(0, W + 1, 48):
        cv.line(x, 0, x, H, GRID, width=0.7)
    for y in range(0, H + 1, 48):
        cv.line(0, y, W, y, GRID, width=0.7)
    # 主轴线更亮
    cv.line(W * 0.72, 0, W * 0.72, H, GRID2, width=1.2)
    cv.line(0, H * 0.44, W, H * 0.44, GRID2, width=1.2)

    # ---------- 2. 极坐标网格（右半）----------
    cx, cy = W * 0.72, H * 0.44
    for r, a in ((130, 0.30), (200, 0.24), (270, 0.18), (340, 0.12)):
        cv.stroke(G.ellipse(cx, cy, r, r * 0.60, rot=0.30), BLUE,
                  width=0.9, alpha=a)
    for k in range(16):
        ang = 2 * math.pi * k / 16 + 0.18
        cv.line(cx + math.cos(ang) * 120, cy + math.sin(ang) * 72,
                cx + math.cos(ang) * 350, cy + math.sin(ang) * 210,
                BLUE, width=0.6)

    # ---------- 3. 轨道 + 粒子 ----------
    orbits = [(-0.55, 150, 92), (0.28, 215, 128), (0.92, 280, 168)]
    for tilt, rx, ry in orbits:
        cv.stroke(G.ellipse(cx, cy, rx, ry, rot=tilt), CYAN, width=1.6, alpha=0.55)
        # 轨道上的粒子
        for k, t in enumerate((0.15, 0.52, 0.78)):
            a = 2 * math.pi * t
            px = cx + math.cos(a) * rx * math.cos(tilt) - math.sin(a) * ry * math.sin(tilt)
            py = cy + math.cos(a) * rx * math.sin(tilt) + math.sin(a) * ry * math.cos(tilt)
            for rr, aa in ((14, 0.08), (9, 0.20), (5, 0.55), (2.6, 0.95)):
                cv.fill(G.circle(px, py, rr), CYAN if rr > 4 else (255, 255, 255), alpha=aa)

    # ---------- 4. 中心核（多层发光）----------
    for rr, aa, c in ((46, 0.06, CYAN), (32, 0.10, CYAN), (20, 0.22, CYAN),
                      (12, 0.45, (255, 255, 255)), (6, 0.95, (255, 255, 255))):
        cv.fill(G.circle(cx, cy, rr), c, alpha=aa)

    # ---------- 5. 波函数示意（右下）----------
    def wave(x0, y0, length, amp, periods, phase, color, alpha, width=2.0):
        """连续正弦：每半周期一段三次贝塞尔，控制点按正弦导数取。"""
        n = max(1, int(round(periods * 2)))
        seg = length / n
        pts = Path()
        pts.move_to(x0, y0 + amp * math.sin(phase))
        for i in range(n):
            a0 = phase + math.pi * i
            a1 = a0 + math.pi
            ya = y0 + amp * math.sin(a0)
            yb = y0 + amp * math.sin(a1)
            c1 = ya + amp * math.cos(a0) * math.pi / 3.0
            c2 = yb - amp * math.cos(a1) * math.pi / 3.0
            xa = x0 + i * seg
            pts.cubic_to(xa + seg / 3.0, c1, xa + 2 * seg / 3.0, c2,
                         xa + seg, yb)
        cv.stroke(pts, color, width=width, alpha=alpha, cap="round")

    wave(1150, 940, 660, 30, 5, 0.0, CYAN, 0.55, 2.2)
    wave(1150, 940, 660, 19, 7, 1.6, BLUE, 0.45, 1.6)
    # 波峰标注点
    for k in range(5):
        x = 1150 + 660 * (k + 0.25) / 5
        cv.fill(G.circle(x, 940 - 30, 2.4), CYAN, alpha=0.9)
        cv.line(x, 940 - 30, x, 940 - 58, CYAN, width=0.6, alpha=0.35)

    # ---------- 6. 左侧文字 ----------
    x0 = 120
    # 竖线装饰
    cv.rect(x0 - 28, 250, x0 - 24, 330, CYAN, alpha=0.9)

    cv.fill(T.text_path("场的语言", x0, 352, 96, "hei", "bold", tracking=0.02),
            FG, rule="evenodd")
    cv.fill(T.text_path("THE LANGUAGE OF FIELDS", x0, 410, 26, "hei", "regular",
                        tracking=0.18), BLUE, rule="evenodd")
    cv.rect(x0, 452, x0 + 470, 453.2, BLUE, alpha=0.55)

    # 公式行
    cv.fill(T.text_path("dψ/dt = iHψ", x0, 520, 36, "hei", "light",
                        tracking=0.02), CYAN, rule="evenodd")
    cv.fill(T.text_path("场是空间的属性，粒子是场的激发。", x0, 580, 26, "hei", "regular"),
            MUTED, rule="evenodd")
    cv.fill(T.text_path("每一条轨道，都是某个对称性留下的痕迹。", x0, 622, 26, "hei", "regular"),
            MUTED, rule="evenodd")

    # ---------- 7. 底部数据 ----------
    labels = [("3", "种基本相互作用"), ("1e-35", "米：普朗克尺度"), ("1e-43", "秒：最短时间")]
    for i, (num, lab) in enumerate(labels):
        bx = x0 + i * 280
        cv.fill(T.text_path(num, bx, 900, 44, "deng", "bold"), FG, rule="evenodd")
        cv.fill(T.text_path(lab, bx, 940, 20, "hei", "regular"), MUTED, rule="evenodd")
        if i:
            cv.rect(bx - 44, 874, bx - 43, 950, GRID2, alpha=0.9)

    # 右下角坐标刻度
    for k in range(9):
        x = 1180 + k * 77.5
        cv.rect(x, H - 62, x + 0.8, H - 62 + (10 if k % 2 == 0 else 5), GRID2, alpha=0.9)

    return cv


if __name__ == "__main__":
    cv = build()
    OUT = os.path.join(BASE, "out")
    png = os.path.join(OUT, "tech_cover.png")
    cv.to_png(png, dpi=96 * SS)
    render_pdf(cv, os.path.join(OUT, "tech_cover.pdf"), (W * 0.75, H * 0.75))
    render_svg(cv, os.path.join(OUT, "tech_cover.svg"))
    print("saved", png, "%.0fKB  ops=%d" % (os.path.getsize(png) / 1024.0, cv.op_count()))
