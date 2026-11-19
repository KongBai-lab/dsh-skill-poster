# -*- coding: utf-8 -*-
"""tests/final_check.py — P0 收口：主题/包/PDF/自检全量验收。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.check import check_canvas
from engine.render import build_canvas, load_json, BLOCKS, PRESETS
from engine.layouts import skeleton_names
from engine.backends.pdf import render_pdf

OUT = os.path.join(BASE, "out")
TPL = os.path.join(BASE, "templates", "minimal-poster")
layout = load_json(os.path.join(TPL, "layout.json"))
content = load_json(os.path.join(TPL, "content.json"))

print("presets: %d   skeletons: %d   blocks: %d   themes: 4"
      % (len(PRESETS), len(skeleton_names()), len(BLOCKS)))

# ---- 1) tech 16:9（验证暗角修复）----
t0 = time.time()
cv, p, th, ctx = build_canvas(layout, content, theme="tech",
                              preset_name="video-16x9", for_="publish")
probs = check_canvas(cv, p, th, content, layout)
t1 = time.time()
cv.to_png(os.path.join(OUT, "poster_tech.png"))
print("tech 16:9   %.2fs  ops=%d  check=%s" % (t1 - t0, cv.op_count(),
                                               "PASS" if not probs else probs[:3]))

# ---- 2) 国风 + pack 素材包 ----
gf_layout = {
    "preset": "xhs-3x4", "theme": "guofeng", "skeleton": "single-page",
    "blocks": [
        {"type": "motifs", "overlay": True, "params": {
            "pack": "guofeng",
            "items": [
                {"fn": "mountains_soft", "args": [30, 830, 1020, 340],
                 "color": "accent2", "alpha": 0.20},
                {"fn": "cloud_soft", "args": [300, 250, 300],
                 "color": "soft", "alpha": 0.55},
                {"fn": "seal_red", "args": [1000, 1178, 58],
                 "color": "accent", "kwargs": {"text": "漫步"}},
            ]}},
        {"type": "hero", "params": {"slot": "title", "gap": 0.06}},
        {"type": "subtitle", "params": {"slot": "subtitle"}},
        {"type": "divider", "params": {"style": "wave", "periods": 6}},
        {"type": "body", "params": {"slot": "body"}},
        {"type": "stat_row", "params": {"slot": "stats"}},
        {"type": "bullets", "params": {"slot": "bullets"}},
        {"type": "cta", "params": {"slot": "cta"}},
    ],
}
t0 = time.time()
cv2, p2, th2, _ = build_canvas(gf_layout, content, for_="publish")
probs2 = check_canvas(cv2, p2, th2, content, gf_layout)
t1 = time.time()
png = os.path.join(OUT, "poster_guofeng_pack.png")
cv2.to_png(png)
pdf = os.path.join(OUT, "poster_guofeng_pack.pdf")
render_pdf(cv2, pdf, p2["pt"])
print("guofeng pack %.2fs  ops=%d  png=%.0fKB pdf=%.0fKB  check=%s"
      % (t1 - t0, cv2.op_count(), os.path.getsize(png) / 1024.0,
         os.path.getsize(pdf) / 1024.0, "PASS" if not probs2 else probs2[:5]))

# ---- 3) 印刷档 ----
t0 = time.time()
cv3, p3, th3, _ = build_canvas(layout, content, theme="guofeng",
                               preset_name="a4-portrait", for_="print")
t1 = time.time()
pdf3 = os.path.join(OUT, "poster_a4.pdf")
render_pdf(cv3, pdf3, p3["pt"])
print("A4 print    %.2fs  %.0fKB  pt=%.0fx%.0f"
      % (t1 - t0, os.path.getsize(pdf3) / 1024.0, p3["pt"][0], p3["pt"][1]))
