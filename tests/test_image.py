# -*- coding: utf-8 -*-
"""tests/test_image.py — 图片素材（背景贴图）验收：PNG/JPEG 两路 + 三后端。"""
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
from engine.backends.svg import render_svg

OUT = os.path.join(BASE, "out")


def make_bg(path):
    """造一张测试素材（模拟用户图片）。"""
    cv = Canvas(900, 500, ss=1, bg=(18, 26, 42))
    for i in range(36):
        cv.fill(G.ellipse(-80 + i * 28, 500 - i * 11, 170, 88),
                (30 + i * 3, 60 + i * 2, 100), alpha=0.16)
    cv.fill(G.circle(700, 140, 80), (120, 200, 230), alpha=0.32)
    cv.fill(G.circle(700, 140, 44), (190, 240, 250), alpha=0.22)
    cv.to_png(path)
    return path


def check_pdf(path):
    """极简 PDF 结构校验：xref 偏移处应为 'N 0 obj'，stream 长度匹配。"""
    raw = open(path, "rb").read()
    if not raw.startswith(b"%PDF-"):
        return "不是 PDF"
    if b"/XObject" not in raw:
        return "缺 XObject"
    # 检查 xref 表里的每个偏移
    ix = raw.rfind(b"xref")
    if ix < 0:
        return "缺 xref"
    tail = raw[ix:ix + 400].split(b"\n")
    bad = 0
    for line in tail[2:]:
        if not line.strip() or line.strip() == b"trailer":
            break
        try:
            off = int(line[:10])
            expect = raw[off:off + 12]
            if b"obj" not in expect:
                bad += 1
        except Exception:
            break
    return "OK" if bad == 0 else "%d 个对象偏移异常" % bad


def main():
    bgp = make_bg(os.path.join(OUT, "test_bg.png"))
    print("素材: %s %.0fKB" % (bgp, os.path.getsize(bgp) / 1024.0))

    # PNG 背景
    cv = Canvas(1920, 1080, ss=3, bg=(0, 0, 0))
    cv.image(bgp, 0, 0, 1920, 1080)
    cv.rect(0, 0, 1920, 1080, (0, 0, 0), alpha=0.42)
    cv.fill(T.text_path("图片背景", 140, 520, 120, "hei", "bold"),
            (255, 255, 255), rule="evenodd")
    cv.fill(T.text_path("cv.image() 贴图 + 压暗 + 叠字", 144, 606, 34, "hei", "regular"),
            (200, 220, 240), rule="evenodd")

    t0 = time.time()
    cv.to_png(os.path.join(OUT, "image_bg_test.png"), dpi=96 * 3)
    print("PNG   %.2fs" % (time.time() - t0))

    t0 = time.time()
    pdf = os.path.join(OUT, "image_bg_test.pdf")
    render_pdf(cv, pdf, (1920 * 0.75, 1080 * 0.75))
    print("PDF   %.2fs  %.0fKB  %s" % (time.time() - t0,
                                       os.path.getsize(pdf) / 1024.0, check_pdf(pdf)))

    t0 = time.time()
    svg = os.path.join(OUT, "image_bg_test.svg")
    render_svg(cv, svg)
    print("SVG   %.2fs  %.0fKB" % (time.time() - t0, os.path.getsize(svg) / 1024.0))

    # JPEG 背景（DC 解码，验证不崩）
    # 可选：设置 POSTER_TEST_JPEG 指向任意 JPEG 素材来测这条路径
    ref = os.environ.get("POSTER_TEST_JPEG", "")
    if ref and os.path.isfile(ref):
        cv2 = Canvas(1280, 720, ss=2, bg=(0, 0, 0))
        cv2.image(ref, 0, 0, 1280, 720)
        cv2.rect(0, 0, 1280, 720, (0, 0, 0), alpha=0.3)
        t0 = time.time()
        cv2.to_png(os.path.join(OUT, "jpeg_bg_test.png"))
        print("JPEG  %.2fs" % (time.time() - t0))
        render_pdf(cv2, os.path.join(OUT, "jpeg_bg_test.pdf"), (1280 * 0.75, 720 * 0.75))
        print("JPEG→PDF %s" % check_pdf(os.path.join(OUT, "jpeg_bg_test.pdf")))


if __name__ == "__main__":
    main()
