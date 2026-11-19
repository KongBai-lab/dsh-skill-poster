# -*- coding: utf-8 -*-
"""tests/test_styles.py — 风格参数化 + theme_overrides 验收。"""
import os, sys, time, json

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.render import build_canvas, load_json
from engine.check import check_canvas
from engine.theme import THEMES, apply_overrides, load_theme

OUT = os.path.join(BASE, "out")
TPL = os.path.join(BASE, "templates", "minimal-poster")
base_layout = load_json(os.path.join(TPL, "layout.json"))
content = load_json(os.path.join(TPL, "content.json"))

print("内置风格:", ", ".join(sorted(THEMES)))

# 1) 同一套 layout，只换风格（含两个新增：swiss / wabi）
for name in ("minimal", "guofeng", "tech", "commerce", "swiss", "wabi"):
    lay = dict(base_layout)
    lay["theme"] = name
    t0 = time.time()
    cv, p, th, ctx = build_canvas(lay, content, for_="preview")
    cv.to_png(os.path.join(OUT, "style_%s.png" % name))
    probs = check_canvas(cv, p, th, content, lay)
    print("  %-9s radius=%.1f line_w=%.2f pill=%-5s divider=%-5s  %.2fs  %s"
          % (name, th.radius(), th.line_w(), th.pill(), th.divider_style(),
             time.time() - t0, "PASS" if not probs else probs[:2]))

# 2) theme_overrides：不动主题文件，只覆盖三个值
lay = dict(base_layout)
lay["theme"] = "swiss"
lay["theme_overrides"] = {
    "palette.accent": "#1B5E4B",
    "shape.radius": 0.02,
    "density.line_height": 1.85,
    "shape.pill": True,
}
cv, p, th, ctx = build_canvas(lay, content, for_="preview")
cv.to_png(os.path.join(OUT, "style_swiss_override.png"))
print("  override: accent=%s radius=%.1f line=%.2f pill=%s"
      % (th.rgb("accent"), th.radius(), th.line("body"), th.pill()))

# 3) 回归：现有模板不受影响
for tpl in ("poster-promo", "poster-showcase"):
    d = os.path.join(BASE, "templates", tpl)
    lay = load_json(os.path.join(d, "layout.json"))
    con = load_json(os.path.join(d, "content.json"))
    cv, p, th, ctx = build_canvas(lay, con, for_="preview")
    probs = check_canvas(cv, p, th, con, lay)
    print("  回归 %-15s %s" % (tpl, "PASS" if not probs else probs[:2]))
