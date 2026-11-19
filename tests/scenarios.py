# -*- coding: utf-8 -*-
"""tests/scenarios.py — 5 个不同场景的压测（覆盖骨架/尺寸/输出/主题）。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.render import build_canvas, render
from engine.check import check_canvas

OUT = os.path.join(BASE, "out")

SCENES = []


def scene(name, preset, theme, skeleton, blocks, slots, for_="preview", fmt="png"):
    SCENES.append(dict(name=name, preset=preset, theme=theme, skeleton=skeleton,
                       blocks=blocks, content={"slots": slots}, for_=for_, fmt=fmt))


# A. 咖啡店开业海报（A4 印刷）
scene("A4 咖啡店海报", "a4-portrait", "commerce", "single-page", [
    {"type": "hero", "params": {"slot": "title", "scale": 1.05}},
    {"type": "subtitle", "params": {"slot": "subtitle"}},
    {"type": "divider", "params": {}},
    {"type": "body", "params": {"slot": "body"}},
    {"type": "bullets", "params": {"slot": "info"}},
    {"type": "stat_row", "params": {"slot": "stats"}},
    {"type": "cta", "params": {"slot": "cta"}},
], {
    "title": "山野咖啡",
    "subtitle": "开 业 限 定 · 第 一 杯 半 价",
    "body": "我们把烘焙机搬进了老巷子。每周三烘一次豆，当天磨、当天冲；豆单只有三支，但每一支都试过至少二十种冲法。",
    "info": ["地址：老城西街 27 号（巷口第三家）", "营业：周二至周日 08:00–19:00",
             "开业周：手冲第二杯半价，豆子可代磨"],
    "stats": [{"num": "3", "unit": "支", "label": "在架豆单"},
              {"num": "20", "label": "种冲法测试"},
              {"num": "8", "label": "点开门"}],
    "cta": {"text": "开业周见"},
}, for_="print", fmt="pdf")

# B. 小红书知识卡（1:1）
scene("方图知识卡", "sq-1x1", "minimal", "card-grid", [
    {"type": "hero", "params": {"slot": "title", "align": "left", "scale": 0.82}},
    {"type": "section_title", "params": {"slot": "kicker"}},
    {"type": "bullets", "params": {"slot": "tips"}},
    {"type": "icon_grid", "params": {"slot": "tags", "cols": 4}},
    {"type": "footer", "params": {"slot": "footer", "align": "left"}},
], {
    "title": "专注力\n是可以练的",
    "kicker": "五个小动作",
    "tips": [
        "把手机放到看不见的地方，而不是静音",
        "开始前先写下「下一步做什么」",
        "用 25 分钟为单位，但允许自己提前停",
        "困的时候先站起来走两分钟",
        "每天留一段完全不安排的时间",
    ],
    "tags": [{"label": "环境", "shape": "cloud"}, {"label": "启动", "shape": "star"},
              {"label": "节奏", "shape": "sparkle"}, {"label": "身体", "shape": "heart"}],
    "footer": "专注不是意志力，是设计。",
})

# C. 公众号首图（900×383 极宽横幅）
scene("公众号首图", "wechat-cover", "tech", "banner", [
    {"type": "hero", "params": {"slot": "title", "align": "left", "scale": 1.0}},
    {"type": "subtitle", "params": {"slot": "subtitle", "align": "left"}},
    {"type": "cta", "params": {"slot": "cta"}},
    {"type": "shape_row", "params": {"slot": "deco"}},
], {
    "title": "一个人也能做完的\niOS 独立开发",
    "subtitle": "从想法到上架：47 个真实踩坑记录",
    "cta": {"text": "阅读全文"},
    "deco": [{"shape": "sparkle", "label": ""}],
})

# D. 视频封面（16:9）
scene("视频封面", "video-16x9", "tech", "cover", [
    {"type": "hero", "params": {"slot": "title", "gap": 0.04, "align": "left",
                                "scale": 0.92}},
    {"type": "subtitle", "params": {"slot": "subtitle", "align": "left"}},
    {"type": "seal", "params": {"slot": "seal"}},
    {"type": "shape_row", "params": {"slot": "deco", "scale": 0.55, "fill": False}},
    {"type": "footer", "params": {"slot": "footer", "align": "center"}},
], {
    "title": "重力是幻觉",
    "subtitle": "广义相对论 · 第一讲",
    "seal": "物理",
    "deco": [{"shape": "sparkle", "label": ""}, {"shape": "star", "label": ""},
              {"shape": "ring", "label": ""}],
    "footer": "EP.01 · 时长 18:42",
})

# E. 信息长图（1080×2160）
scene("信息长图", "info-long", "guofeng", "long-flow", [
    {"type": "hero", "params": {"slot": "title", "align": "left", "scale": 0.9}},
    {"type": "section_title", "params": {"slot": "s1"}},
    {"type": "body", "params": {"slot": "p1"}},
    {"type": "gallery", "params": {"slot": "items", "cols": 4}},
    {"type": "divider", "params": {"style": "wave"}},
    {"type": "section_title", "params": {"slot": "s2"}},
    {"type": "microchart", "params": {"slot": "chart", "label_w": 0.26}},
    {"type": "timeline", "params": {"slot": "history"}},
    {"type": "quote", "params": {"slot": "quote"}},
    {"type": "footer", "params": {"slot": "footer", "align": "center"}},
], {
    "title": "一杯咖啡的旅程",
    "s1": "从种子到杯",
    "p1": "咖啡樱桃采摘后去果肉、发酵、干燥，变成生豆；再经烘焙、研磨、萃取，才成为杯中的风味。每一步都在改变最终的味道。",
    "items": ["采收", "发酵", "干燥", "烘焙"],
    "s2": "风味轮",
    "chart": [{"label": "酸质", "value": 78}, {"label": "甜感", "value": 64},
              {"label": "醇厚", "value": 52}, {"label": "余韵", "value": 41}],
    "history": [{"date": "9世纪", "text": "埃塞俄比亚"}, {"date": "15世纪", "text": "也门"},
                {"date": "17世纪", "text": "欧洲"}, {"date": "19世纪", "text": "全球"}],
    "quote": "风味不是玄学，是处理法与烘焙度的函数。",
    "footer": "coffee · 从种子到杯",
})


def run_one(s):
    layout = {"preset": s["preset"], "theme": s["theme"], "skeleton": s["skeleton"],
              "blocks": s["blocks"]}
    ext = "pdf" if s["fmt"] == "pdf" else "png"
    out = os.path.join(OUT, "scene_%s.%s" % (s["name"].replace(" ", "_"), ext))
    t0 = time.time()
    render(layout, s["content"], for_=s["for_"], fmt=s["fmt"], out=out)
    dt = time.time() - t0
    cv, preset, th, ctx = build_canvas(layout, s["content"], for_=s["for_"])
    probs = check_canvas(cv, preset, th, s["content"], layout)
    size = os.path.getsize(out) / 1024.0
    print("%-14s %-6s %-12s %dx%d  %5.2fs  %5.0fKB  %s"
          % (s["name"], s["for_"], s["preset"], preset["px"][0], preset["px"][1],
             dt, size, "PASS" if not probs else "%d 问题" % len(probs)))
    for q in probs[:4]:
        print("      - " + q)
    return not probs


if __name__ == "__main__":
    ok = 0
    for s in SCENES:
        if run_one(s):
            ok += 1
    print("\n%d/%d 场景通过" % (ok, len(SCENES)))
