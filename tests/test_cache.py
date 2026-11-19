# -*- coding: utf-8 -*-
"""tests/test_cache.py — 静态层缓存验收：冷/热/改文案三种情况计时。"""
import copy
import json
import os
import sys
import time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine import cache
from engine.render import load_json, render

TPL = os.path.join(BASE, "templates", "mural-long")
layout = load_json(os.path.join(TPL, "layout.json"))
content = load_json(os.path.join(TPL, "content.json"))
OUT = os.path.join(BASE, "out")

print("cache dir:", cache.CACHE_DIR)
print("清掉旧缓存:", cache.clear(), "个文件")

t0 = time.time()
render(layout, content, for_="publish", out=os.path.join(OUT, "cache_test.png"))
t_cold = time.time() - t0
print("冷启动（静态层未缓存）: %.2fs  static=%d ops  dynamic=%d ops"
      % (t_cold,
         len(cache.static_ops(__import__("engine.render", fromlist=["x"])
                              .build_canvas(layout, content, for_="publish")[0].ops)),
         len(cache.dynamic_ops(__import__("engine.render", fromlist=["x"])
                               .build_canvas(layout, content, for_="publish")[0].ops))))

t0 = time.time()
render(layout, content, for_="publish", out=os.path.join(OUT, "cache_test.png"))
t_hot = time.time() - t0
print("热态（静态层命中，文案不变）: %.2fs" % t_hot)

# 改文案：静态层应该继续命中
content2 = copy.deepcopy(content)
content2["slots"]["process_1"][0]["desc"] = "改用文火慢焙，让茶香更透，同时避免茶饼焦苦。"
content2["slots"]["title"] = "一盏茶"
content2["slots"]["teas"][0]["value"] = 96
t0 = time.time()
render(layout, content2, for_="publish", out=os.path.join(OUT, "cache_edit.png"))
t_edit = time.time() - t0
print("改文案（静态层仍命中）: %.2fs" % t_edit)

print("\n对比：冷启动 %.2fs → 改文案 %.2fs（-%.0f%%）"
      % (t_cold, t_edit, (1 - t_edit / t_cold) * 100))
