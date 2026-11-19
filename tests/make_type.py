# -*- coding: utf-8 -*-
"""tests/make_type.py — P0-3 验收：中文排版样张 + 断行/缺字自检。"""
import os, sys, time

BASE = os.environ.get("POSTER_HOME") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
for _m in [k for k in sys.modules if k == "engine" or k.startswith("engine.")]:
    del sys.modules[_m]

from engine.canvas import Canvas
from engine import typography as T
from engine.fonts import missing, find_file, FAMILIES

W, H = 900, 1200
INK = (32, 44, 38)
MOSS = (58, 84, 66)
RED = (168, 62, 48)
OCHRE = (150, 100, 58)
PAPER = (249, 246, 238)

TITLE = "春江花月夜"
SUB = "春江潮水连海平　海上明月共潮生"
BODY = ("中文排版测试：断行、避头尾、标点挤压、竖排与字距都要在这里验证，"
        "再通过分次注水与高击拂，使茶汤产生绵密持久的白色沫浮。"
        "它不仅是一种技艺，更是宋代「四般雅事」之一，"
        "是当时社会风尚与美学精神的体现。")
VERT = "竖排测试：春江潮水连海平，海上明月共潮生"
ENG = "Typography Test · 中西混排 2024"
PUNCT = "注汤、击拂、粥面；沫饽咬盏，谓之「咬盏」。茶色贵白，以纯白为上。"


def build():
    cv = Canvas(W, H, ss=2, bg=PAPER)
    # 顶部细线
    cv.rect(0, 0, W, 10, MOSS)
    # 大标题（行楷）
    cv.fill(T.spaced_path(TITLE, W / 2, 150, 84, 8, "xingkai", align="center"), INK)
    # 副标（楷体）
    cv.fill(T.text_path(SUB, W / 2, 210, 25, "kai", align="center", tracking=0.04), MOSS)
    # 分隔线
    cv.line(90, 250, W - 90, 250, RED, width=1.2)
    # 正文（仿宋，自动断行）
    cv.fill(T.para_path(BODY, 90, 290, 520, 16, line_height=29,
                        family="fang", first_indent=32), INK)
    # 竖排（隶书），右侧一列
    cv.fill(T.vtext_path(VERT, W - 90, 290, 24, "li", tracking=0.06), MOSS)
    # 英文混排（黑体）
    cv.fill(T.text_path(ENG, 90, 640, 18, "hei"), OCHRE)
    # 标点挤压示例
    cv.fill(T.para_path(PUNCT, 90, 700, 520, 16, line_height=29,
                        family="fang", squeeze=True), INK)
    # 圆体标签
    cv.fill(T.text_path("排版测试 · 中文", 90, 850, 22, "yuan", weight="bold"), RED)
    # 小字注释
    cv.fill(T.para_path("注：竖排文字中的「、」「。」按竖排规范移到字框右上。",
                        90, 900, 480, 13, line_height=24, family="fang",
                        squeeze=True), (120, 118, 104))
    # 底部落款
    cv.fill(T.text_path("宋 · 四般雅事", 90, 1080, 14, "kai"), INK)
    cv.fill(T.text_path("纯 Python 矢量排版", W - 90, 1080, 13, "fang", align="right"),
            (120, 118, 104))
    return cv


if __name__ == "__main__":
    print("字体目录命中：")
    for fam in ("xingkai", "kai", "fang", "li", "hei", "yuan", "song"):
        p = find_file(fam, "regular")
        print("  %-8s %s" % (fam, os.path.basename(p) if p else "MISSING"))
    for name, txt, fam in (("标题", TITLE, "xingkai"), ("副标", SUB, "kai"),
                           ("正文", BODY, "fang"), ("竖排", VERT, "li"),
                           ("英文", ENG, "hei")):
        m = missing(txt, fam)
        print("  缺字 %s(%s): %s" % (name, fam, m if m else "无"))

    lines = T.para_lines(BODY, 520, 16, "fang", first_indent=32)
    print("正文断行：%d 行，首行宽 %.1f / 限宽 520" % (len(lines), T.measure(lines[0], 16, "fang")))
    for ln in lines[:4]:
        print("    | %s" % ln)

    t0 = time.time()
    cv = build()
    t1 = time.time()
    p = os.path.join(BASE, "out", "type.png")
    cv.to_png(p)
    t2 = time.time()
    print("type: build=%.2fs render=%.2fs total=%.2fs ops=%d %s %.0fKB"
          % (t1 - t0, t2 - t1, t2 - t0, cv.op_count(), os.path.basename(p),
             os.path.getsize(p) / 1024.0))
