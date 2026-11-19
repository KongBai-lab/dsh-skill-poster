# -*- coding: utf-8 -*-
"""tests/test_image_poster.py — 实测：参考图当背景 + 叠字海报（PNG/PDF 对比）。"""
import os
import sys
import time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.") or k.startswith("packs")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine import geometry as G, typography as T
from engine.backends.pdf import render_pdf

OUT = os.path.join(BASE, "out")
# 用任意一张图做背景；没有设置就跳过（避免把个人素材带进仓库）
REF = os.environ.get("POSTER_TEST_JPEG", "")

W, H, SS = 1080, 1440, 3
CREAM = (250, 246, 236)
INK = (40, 34, 28)
MOSS = (58, 84, 66)


def build():
    cv = Canvas(W, H, ss=SS, bg=(0, 0, 0))
    # 1. 参考图铺满（比例同为 3:4，不会变形）
    cv.image(REF, 0, 0, W, H)
    # 2. 整体压暗，保证文字可读
    cv.rect(0, 0, W, H, (0, 0, 0), alpha=0.52)
    # 3. 底部再加一层渐深（标题区）
    for i in range(10):
        y = H * 0.52 + i * H * 0.048
        cv.rect(0, y, W, y + H * 0.05, (0, 0, 0), alpha=0.05)

    # 4. 标题
    cv.fill(T.text_path("宋 韵 点 茶", W * 0.5, H * 0.735, 92, "xingkai", "regular",
                        align="center", baseline=True), CREAM, rule="evenodd")
    cv.fill(T.text_path("从采摘到啜饮 · 一杯里的四季", W * 0.5, H * 0.795, 28, "kai",
                        "regular", align="center", baseline=True), (222, 212, 192),
            rule="evenodd")
    # 5. 装饰：细线 + 印章
    cv.rect(W * 0.30, H * 0.828, W * 0.70, H * 0.828 + 1.2, (200, 190, 170), alpha=0.55)
    scx, scy = W - 96, H - 120
    cv.fill(G.seal_frame(scx, scy, 64), (150, 52, 40), rule="nonzero")
    cv.fill(T.text_path("茶事", scx, scy + 9, 24, "xingkai", "regular",
                        align="center", baseline=True), CREAM, rule="evenodd")
    return cv


if __name__ == "__main__":
    if not REF or not os.path.isfile(REF):
        print("跳过：设置 POSTER_TEST_JPEG 指向一张图片后再跑")
        sys.exit(0)
    cv = build()
    t0 = time.time()
    png = os.path.join(OUT, "image_poster.png")
    cv.to_png(png, dpi=96 * SS)
    print("PNG %.2fs %.0fKB" % (time.time() - t0, os.path.getsize(png) / 1024.0))

    t0 = time.time()
    pdf = os.path.join(OUT, "image_poster.pdf")
    render_pdf(cv, pdf, (W * 0.75, H * 0.75))
    print("PDF %.2fs %.0fKB" % (time.time() - t0, os.path.getsize(pdf) / 1024.0))
