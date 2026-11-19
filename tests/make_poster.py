# -*- coding: utf-8 -*-
"""tests/make_poster.py — P0-5/6/7 验收：出第一张海报 + 自检 + PDF。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.")]:
    del sys.modules[_m]

from engine.check import check_canvas, report
from engine.render import build_canvas, load_json
from engine.backends.pdf import render_pdf

TPL = os.path.join(BASE, "templates", "minimal-poster")
OUT = os.path.join(BASE, "out")
layout = load_json(os.path.join(TPL, "layout.json"))
content = load_json(os.path.join(TPL, "content.json"))


def run(theme, preset, tag, for_="publish"):
    t0 = time.time()
    cv, p, th, ctx = build_canvas(layout, content, theme=theme,
                                  preset_name=preset, for_=for_)
    t1 = time.time()
    png = os.path.join(OUT, "poster_%s.png" % tag)
    cv.to_png(png)
    t2 = time.time()
    pdf = os.path.join(OUT, "poster_%s.pdf" % tag)
    render_pdf(cv, pdf, p["pt"])
    t3 = time.time()
    probs = check_canvas(cv, p, th, content, layout)
    print("%-10s preset=%-10s ss=%d  build=%.2fs png=%.2fs pdf=%.2fs  ops=%d  %dx%d"
          % (tag, preset, cv.ss, t1 - t0, t2 - t1, t3 - t2, cv.op_count(),
             p["px"][0], p["px"][1]))
    print("           png=%.0fKB pdf=%.0fKB  check=%s"
          % (os.path.getsize(png) / 1024.0, os.path.getsize(pdf) / 1024.0,
             "PASS" if not probs else "%d 问题" % len(probs)))
    for q in probs[:8]:
        print("           - " + q)
    return cv, p, th


if __name__ == "__main__":
    run("minimal", "xhs-3x4", "minimal")
    run("guofeng", "a4-portrait", "guofeng_a4")
    run("tech", "video-16x9", "tech")

    # 多档清晰度
    for for_ in ("draft", "preview", "publish"):
        t0 = time.time()
        cv, p, th, ctx = build_canvas(layout, content, theme="minimal",
                                      preset_name="xhs-3x4", for_=for_)
        pth = os.path.join(OUT, "poster_%s.png" % for_)
        cv.to_png(pth)
        print("--for %-8s ss=%d -> %dx%d  %.2fs  %.0fKB"
              % (for_, cv.ss, p["px"][0] * cv.ss, p["px"][1] * cv.ss,
                 time.time() - t0, os.path.getsize(pth) / 1024.0))
