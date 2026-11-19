# -*- coding: utf-8 -*-
"""tests/make_shapes.py — P0-2 验收：全部图元一张样张 + 几何断言。"""
import os, sys, math, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine.geometry import (
    circle, ellipse, arc, ring, pie, donut_sector, rrect, capsule,
    regular_polygon, star, polygon,
    leaf, petal, flower, drop, cloud, wave, mountains, heart, sparkle,
    seal_frame, corner_ornament, divider_wave,
)
from engine.path import Path, chord_error

W, H = 1400, 1020
INK = (32, 44, 38)
MOSS = (58, 84, 66)
OCHRE = (150, 100, 58)
RED = (168, 62, 48)
PAPER = (250, 248, 244)
LINE = (228, 224, 213)


def build():
    cv = Canvas(W, H, ss=2, bg=PAPER)
    for x in range(0, W, 50):
        cv.line(x, 0, x, H, LINE, width=0.5)
    for y in range(0, H, 50):
        cv.line(0, y, W, y, LINE, width=0.5)

    # ---- 行 1：叶 / 花瓣 / 花 ----
    for i, (bend, ang) in enumerate(((0.0, 0.0), (0.5, 0.35), (-0.4, -0.5))):
        cv.fill(leaf(120 + i * 210, 200, 150, 58, angle=ang, bend=bend), MOSS, alpha=0.9)
    for i, wdt in enumerate((0.42, 0.62, 0.86)):
        cv.fill(petal(90 + i * 150, 340, 120, 120 * wdt, angle=-0.15 + i * 0.12), RED, alpha=0.85)
    cv.fill(flower(640, 340, 78, petals=6, center_r=22), OCHRE, rule="nonzero", alpha=0.9)
    cv.fill(flower(830, 340, 70, petals=5, angle=0.3), MOSS, rule="nonzero", alpha=0.85)

    cv.fill(drop(1030, 300, 62), RED, alpha=0.85)
    cv.fill(cloud(1220, 320, 210, 96, bumps=4), MOSS, alpha=0.55)
    cv.fill(heart(1210, 470, 150, angle=0.08), RED, alpha=0.9)
    cv.fill(sparkle(1050, 470, 72, points=4), OCHRE, alpha=0.95)
    cv.fill(sparkle(1110, 480, 38, points=6, inner=0.34), OCHRE, alpha=0.7)

    # ---- 行 2：山 / 波 / 星 ----
    cv.fill(mountains(80, 560, 620, 760, peaks=4, seed=7), MOSS, alpha=0.45)
    cv.stroke(wave(80, 840, 620, 840, 34, periods=3, taper=0.5), OCHRE, width=5, cap="round")
    for i, n in enumerate((5, 6, 8)):
        cv.fill(star(760 + i * 150, 640, 76, 76 * 0.44, points=n), OCHRE, alpha=0.9)
    cv.fill(regular_polygon(1210, 640, 74, 6, rot=-1.57), MOSS, alpha=0.8)

    # ---- 行 3：几何 ----
    cv.fill(circle(110, 940, 52), MOSS)
    cv.fill(ellipse(240, 940, 62, 38, rot=0.5), OCHRE)
    cv.fill(ring(380, 940, 54, 32), INK)
    cv.fill(pie(510, 940, 58, -1.2, 1.1), RED, alpha=0.9)
    cv.fill(donut_sector(650, 940, 60, 32, -1.0, 1.4), MOSS, alpha=0.9)
    cv.fill(capsule(720, 940, 830, 940, 26), OCHRE)
    cv.fill(rrect(860, 900, 990, 985, 18), RED, alpha=0.85)
    cv.fill(polygon([(1030, 985), (1070, 900), (1110, 985)]), MOSS, alpha=0.8)

    # ---- 行 4：装饰（描边）----
    cv.stroke(seal_frame(1220, 940, 96, r=8, pad=7), RED, width=2.4)
    cv.stroke(corner_ornament(60, 1010, 90, "bl"), OCHRE, width=2.4, cap="round")
    cv.stroke(corner_ornament(310, 1010, 90, "br"), OCHRE, width=2.4, cap="round")
    cv.stroke(divider_wave(400, 700, 1000, amp=7, periods=5), MOSS, width=2.0, cap="round")
    return cv


if __name__ == "__main__":
    t0 = time.time()
    cv = build()
    t1 = time.time()
    p = os.path.join(BASE, "out", "shapes.png")
    cv.to_png(p)
    t2 = time.time()
    print("shapes: build=%.3fs render=%.3fs total=%.3fs ops=%d %s %.0fKB"
          % (t1 - t0, t2 - t1, t2 - t0, cv.op_count(), os.path.basename(p),
             os.path.getsize(p) / 1024.0))

    tol = 0.25
    cases = [
        ("leaf", leaf(0, 0, 150, 58, bend=0.5)),
        ("petal", petal(0, 0, 120, 74)),
        ("drop", drop(0, 0, 62)),
        ("cloud", cloud(0, 0, 210, 96)),
        ("heart", heart(0, 0, 150)),
        ("mountains", mountains(0, 0, 300, 160, peaks=4, seed=7)),
        ("wave", wave(0, 0, 400, 0, 34, periods=3)),
        ("star r", star(0, 0, 76, 33, points=8, round_tips=0.06)),
    ]
    print("几何断言（tol=%.2f）" % tol)
    for name, path in cases:
        n = path.point_count(tol)
        err = chord_error(path, tol)
        print("  %-10s points=%4d  chord_err=%.4f  %s"
              % (name, n, err, "OK" if err <= tol * 1.35 else "FAIL"))
