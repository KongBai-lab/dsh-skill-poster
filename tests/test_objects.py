# -*- coding: utf-8 -*-
"""tests/test_objects.py — 茶器半写实插画验收（大图看细节）。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine import typography as T
from packs.tea import objects as O

W, H = 1200, 460
PAPER = (246, 241, 230)
INK = (52, 40, 32)

cv = Canvas(W, H, ss=3, bg=PAPER)

# 一排四件器物，宽度 170
items = [
    ("执壶", lambda cx: O.kettle(cv, cx, 360, 170)),
    ("建盏", lambda cx: O.cup(cv, cx, 360, 165)),
    ("茶筅", lambda cx: O.whisk(cv, cx, 360, 150)),
    ("盏托", lambda cx: O.saucer(cv, cx, 360, 180)),
]
for i, (label, fn) in enumerate(items):
    cx = 160 + i * 290
    fn(cx)

# 器物下的标签
for i, (label, _) in enumerate(items):
    cx = 160 + i * 290
    cv.fill(T.text_path(label, cx, 405, 30, "kai", "regular", align="center"),
            INK, rule="evenodd")
    cv.fill(T.text_path("· 六层绘制 ·", cx, 438, 17, "fang", "regular", align="center"),
            (140, 128, 108), rule="evenodd")

p = os.path.join(BASE, "out", "tea_objects.png")
t0 = time.time()
cv.to_png(p)
print("tea objects: %.2fs ops=%d %.0fKB" % (time.time() - t0, cv.op_count(),
                                            os.path.getsize(p) / 1024.0))
