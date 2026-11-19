# -*- coding: utf-8 -*-
"""tests/debug_edges.py — 定位 cap 尖刺、描边缺口、竖线不渲染。"""
import os, sys, math

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine.path import Path
from engine.offset import stroke_path

SS = 4
TOL = 0.5 / SS
OUT = os.path.join(BASE, "out")

print("--- 诊断：竖线描边 ---")
for cap in ("butt", "round", "square"):
    pl = Path()
    pl.move_to(60, 360).line_to(60, 260)
    sp = stroke_path(pl, 13, cap, "round", TOL)
    print("  cap=%-6s contours=%s bbox=(%.1f,%.1f,%.1f,%.1f)"
          % (cap, [len(c) for c in sp.flatten(TOL)], *sp.bbox()))

print("--- 诊断：圆填充 ---")
c = Path.circle(120, 120, 90)
cs = c.flatten(TOL)
print("  circle contours=%d first=%s" % (len(cs), cs[0][:2]))

print("--- 诊断：椭圆描边 ---")
e = Path.ellipse(360, 120, 90, 55, rot=0.5)
sp = stroke_path(e, 8, "butt", "round", TOL)
print("  contours=%s bbox=(%.1f,%.1f,%.1f,%.1f)"
      % ([len(q) for q in sp.flatten(TOL)], *sp.bbox()))

print("--- 诊断：圆弧 round cap ---")
arc = Path.arc(360, 300, 70, 0.6, 3.0)
sp = stroke_path(arc, 10, "round", "round", TOL)
print("  contours=%s bbox=(%.1f,%.1f,%.1f,%.1f)"
      % ([len(q) for q in sp.flatten(TOL)], *sp.bbox()))

# ---------------- 出图 ----------------
cv = Canvas(480, 480, ss=SS, bg=(250, 248, 244))
INK = (30, 40, 35)
RED = (170, 60, 45)
MOSS = (58, 84, 66)

cv.fill(Path.circle(120, 120, 90), MOSS)

cv.stroke(Path.ellipse(360, 120, 90, 55, rot=0.5), INK, width=8)

for i, cap in enumerate(("butt", "round", "square")):
    x = 60 + i * 70
    pl = Path()
    pl.move_to(x, 360).line_to(x, 260)
    cv.stroke(pl, RED, width=13, cap=cap)

cv.stroke(Path.arc(360, 300, 70, 0.6, 3.0), RED, width=10, cap="round")

p = os.path.join(OUT, "debug_edges.png")
cv.to_png(p)
print("saved", p, os.path.getsize(p) // 1024, "KB")
