# -*- coding: utf-8 -*-
"""tests/make_examples.py — 生成 README 用效果图（全部由引擎自绘，不含外部素材）。

输出到 examples/，用 preview 档控制体积。
"""
import os
import sys

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine.render import build_canvas, render, load_json
from engine import geometry as G, typography as T
from engine.backends.pdf import render_pdf

OUT = os.path.join(BASE, "examples")
os.makedirs(OUT, exist_ok=True)


def _tpl(name, out_name, for_="preview"):
    """跑一遍自带模板。"""
    d = os.path.join(BASE, "templates", name)
    lay = load_json(os.path.join(d, "layout.json"))
    con = load_json(os.path.join(d, "content.json"))
    out = os.path.join(OUT, out_name)
    render(lay, con, for_=for_, out=out)
    print("  %-26s %6.0fKB" % (out_name, os.path.getsize(out) / 1024.0))
    return out


def _scene(name, preset, theme, skeleton, blocks, slots, out_name):
    layout = {"preset": preset, "theme": theme, "skeleton": skeleton, "blocks": blocks}
    out = os.path.join(OUT, out_name)
    render(layout, {"slots": slots}, for_="preview", out=out)
    print("  %-26s %6.0fKB" % (out_name, os.path.getsize(out) / 1024.0))
    return out


def main():
    print("生成示例图：")
    # 1-3 自带模板
    _tpl("minimal-poster", "01-minimal-poster.png")
    _tpl("poster-promo", "02-product-promo.png")
    _tpl("poster-showcase", "03-shape-showcase.png")

    # 4 科技/物理封面（C 模式自绘）
    sys.path.insert(0, os.path.join(BASE, "templates", "tech-cover"))
    import build as tc
    cv = tc.build()
    p = os.path.join(OUT, "04-tech-cover.png")
    cv.to_png(p, dpi=96 * tc.SS)
    render_pdf(cv, p.replace(".png", ".pdf"), (tc.W * 0.75, tc.H * 0.75))
    print("  %-26s %6.0fKB" % ("04-tech-cover.png", os.path.getsize(p) / 1024.0))

    # 5 方形知识卡
    _scene("方图知识卡", "sq-1x1", "minimal", "card-grid", [
        {"type": "hero", "params": {"slot": "title", "align": "left", "scale": 0.82}},
        {"type": "section_title", "params": {"slot": "kicker"}},
        {"type": "bullets", "params": {"slot": "tips"}},
        {"type": "icon_grid", "params": {"slot": "tags", "cols": 4}},
        {"type": "footer", "params": {"slot": "footer", "align": "left"}},
    ], {
        "title": "专注力\n是可以练的",
        "kicker": "五个小动作",
        "tips": ["把手机放到看不见的地方，而不是静音",
                 "开始前先写下「下一步做什么」",
                 "用 25 分钟为单位，但允许自己提前停",
                 "困的时候先站起来走两分钟",
                 "每天留一段完全不安排的时间"],
        "tags": [{"label": "环境", "shape": "cloud"}, {"label": "启动", "shape": "star"},
                 {"label": "节奏", "shape": "sparkle"}, {"label": "身体", "shape": "heart"}],
        "footer": "专注不是意志力，是设计。",
    }, "05-square-card.png")

    # 6 信息长图
    _scene("信息长图", "info-long", "guofeng", "long-flow", [
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
        "p1": "咖啡樱桃采摘后去果肉、发酵、干燥，变成生豆；再经烘焙、研磨、萃取，才成为杯中的风味。",
        "items": ["采收", "发酵", "干燥", "烘焙"],
        "s2": "风味轮",
        "chart": [{"label": "酸质", "value": 78}, {"label": "甜感", "value": 64},
                  {"label": "醇厚", "value": 52}, {"label": "余韵", "value": 41}],
        "history": [{"date": "9世纪", "text": "埃塞俄比亚"}, {"date": "15世纪", "text": "也门"},
                    {"date": "17世纪", "text": "欧洲"}, {"date": "19世纪", "text": "全球"}],
        "quote": "风味不是玄学，是处理法与烘焙度的函数。",
        "footer": "coffee · 从种子到杯",
    }, "06-long-infographic.png")

    # 7 半写实器物（packs/tea）
    from packs.tea import objects as tea
    cv = Canvas(1400, 520, ss=2, bg=(246, 241, 230))
    for i, (fn, name) in enumerate((("kettle", "执壶"), ("cup", "建盏"),
                                    ("whisk", "茶筅"), ("saucer", "盏托"))):
        cx = 180 + i * 340
        getattr(tea, fn)(cv, cx, 230, 190)
        cv.fill(T.text_path(name, cx, 430, 30, "kai", "regular", align="center"),
                (52, 40, 32), rule="evenodd")
    p = os.path.join(OUT, "07-tea-objects.png")
    cv.to_png(p)
    print("  %-26s %6.0fKB" % ("07-tea-objects.png", os.path.getsize(p) / 1024.0))
    print("\n完成 →", OUT)


if __name__ == "__main__":
    main()
