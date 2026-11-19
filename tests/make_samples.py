# -*- coding: utf-8 -*-
"""tests/make_samples.py — P0 第 1 步验收：图元样张 + 弦高实测 + 耗时。"""
import sys, os, time, math

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
# python 工具的解释器跨请求共享，必须清掉本地模块缓存，否则改代码不生效
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine.path import Path, chord_error

OUT = os.path.join(BASE, "out")
os.makedirs(OUT, exist_ok=True)

INK = (34, 46, 40)
MOSS = (58, 84, 66)
OCHRE = (150, 100, 58)
RED = (168, 62, 48)
PAPER = (250, 248, 244)
LINE = (226, 222, 211)

W, H = 1200, 840


def make_main():
    cv = Canvas(W, H, ss=2, bg=PAPER)
    # 顶栏
    cv.rect(0, 0, W, 46, INK)
    # 网格
    for x in range(0, W, 40):
        cv.line(x, 46, x, H, LINE, width=0.6)
    for y in range(46, H, 40):
        cv.line(0, y, W, y, LINE, width=0.6)

    # ---- 行 1：基本图元 ----
    cv.circle(140, 170, 70, MOSS)
    cv.ellipse(400, 170, 90, 52, OCHRE, rot=0.45)
    cv.rrect(620, 100, 800, 240, 26, RED)
    cv.fill(Path.ring(920, 170, 70, 44), INK)                 # evenodd 孔洞
    star = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = 66 if i % 2 == 0 else 26
        star.append((1100 + r * math.cos(a), 170 + r * math.sin(a)))
    cv.stroke(Path.from_polygon(star), MOSS, width=3, join="miter")

    # ---- 行 2：曲线 ----
    p = Path()
    p.move_to(100, 420)
    p.cubic_to(220, 290, 330, 530, 470, 400)
    cv.stroke(p, INK, width=7, cap="round")
    cv.stroke(Path.arc(650, 400, 90, -0.9, 1.9), OCHRE, width=8, cap="round")
    # 自造贝塞尔叶形（验证曲线闭合 + 尖角）
    leaf = Path()
    leaf.move_to(900, 470)
    leaf.cubic_to(940, 330, 1090, 330, 1130, 470)
    leaf.cubic_to(1090, 430, 940, 430, 900, 470)
    leaf.close()
    cv.fill(leaf, MOSS, alpha=0.85)

    # ---- 行 3：join / cap ----
    spike = [(100, 610), (160, 530), (220, 610)]
    cv.stroke(Path.from_polygon(spike, closed=False), RED, width=14, join="miter")
    spike2 = [(360, 610), (420, 530), (480, 610)]
    cv.stroke(Path.from_polygon(spike2, closed=False), RED, width=14, join="round")
    spike3 = [(620, 610), (680, 530), (740, 610)]
    cv.stroke(Path.from_polygon(spike3, closed=False), RED, width=14, join="bevel")

    for i, cap in enumerate(("butt", "round", "square")):
        x = 900 + i * 90
        pl = Path()
        pl.move_to(x, 610).line_to(x, 540)
        cv.stroke(pl, INK, width=13, cap=cap)

    # ---- 行 4：alpha / 细线梯度 ----
    for i in range(3):
        cv.circle(180 + i * 46, 740, 58, RED, alpha=0.45)
    for i, w in enumerate((0.6, 1.0, 1.6, 2.4, 4.0, 8.0)):
        y = 690 + i * 22
        cv.line(420, y, 760, y, INK, width=w, cap="round")
    # 描边圆（nonzero 环）
    cv.stroke(Path.circle(980, 740, 62), OCHRE, width=6)
    cv.stroke(Path.circle(1100, 740, 62), MOSS, width=2, cap="round")
    return cv


def make_zoom():
    """6× 放大：只看边缘与棱角。"""
    Wz, Hz = 320, 320
    cv = Canvas(Wz, Hz, ss=6, bg=PAPER)
    cv.circle(90, 90, 66, MOSS)
    cv.stroke(Path.arc(240, 90, 66, 0.4, 3.4), RED, width=5, cap="round")
    cv.stroke(Path.ellipse(90, 240, 74, 46, rot=0.5), INK, width=4, join="round")
    p = Path()
    p.move_to(160, 300)
    p.cubic_to(190, 190, 280, 200, 310, 290)
    cv.stroke(p, OCHRE, width=6, cap="round")
    return cv


def _mk_cubic():
    p = Path()
    p.move_to(100, 420)
    p.cubic_to(220, 290, 330, 530, 470, 400)
    return p


if __name__ == "__main__":
    t0 = time.time()
    cv = make_main()
    t1 = time.time()
    p1 = os.path.join(OUT, "samples.png")
    cv.to_png(p1)
    t2 = time.time()
    print("main: build=%.3fs render=%.3fs total=%.3fs ops=%d %s %.0fKB"
          % (t1 - t0, t2 - t1, t2 - t0, cv.op_count(), os.path.basename(p1),
             os.path.getsize(p1) / 1024.0))

    z = make_zoom()
    t3 = time.time()
    p2 = os.path.join(OUT, "zoom.png")
    z.to_png(p2)
    t4 = time.time()
    print("zoom: %.3fs ops=%d %s %.0fKB"
          % (t4 - t3, z.op_count(), os.path.basename(p2),
             os.path.getsize(p2) / 1024.0))

    # ---- 弦高实测 ----
    tol = 0.25                      # 0.5 / ss, ss=2
    for name, path in (("circle r=70", Path.circle(0, 0, 70)),
                       ("ellipse 90x52", Path.ellipse(0, 0, 90, 52)),
                       ("arc r=90", Path.arc(0, 0, 90, -0.9, 1.9)),
                       ("cubic", _mk_cubic()),
                       ("rrect r=26", Path.rrect(0, 0, 180, 140, 26))):
        pts = sum(len(c) for c in path.flatten(tol))
        err = chord_error(path, tol)
        print("  %-14s points=%4d  chord_err=%.4f px  (tol=%.3f)  %s"
              % (name, pts, err, tol, "OK" if err <= tol * 1.35 else "FAIL"))


def _mk_cubic():
    p = Path()
    p.move_to(100, 420)
    p.cubic_to(220, 290, 330, 530, 470, 400)
    return p
