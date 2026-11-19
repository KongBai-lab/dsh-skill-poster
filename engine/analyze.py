# -*- coding: utf-8 -*-
"""analyze.py — 参考图 → theme 草稿（配色/明暗/版心/密度）。

用法
----
    python -m engine.analyze ref.jpg --out themes/ref.json
    python -m engine.analyze ref.png            # 只打印报告

它不能「复制风格」，但能省掉最费时的三件事：取色、判断亮底/暗底、估算版心留白。
拿到草稿后套一个最接近的内置主题（extends），再微调几个值即可。
"""

import argparse
import json
import os
import sys

from . import imaging


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 5.0) / (lo + 5.0)


def _sat(c):
    mx, mn = max(c), min(c)
    return (mx - mn) / 255.0 if mx else 0.0


def _hex(c):
    return "#%02X%02X%02X" % (int(c[0]), int(c[1]), int(c[2]))


def _mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def analyze(path, max_side=160):
    w, h, px = imaging.load_small(path, max_side)
    n = w * h
    counts = {}
    for i in range(n):
        c = (px[i * 3] & 0xF8, px[i * 3 + 1] & 0xF8, px[i * 3 + 2] & 0xF8)
        counts[c] = counts.get(c, 0) + 1
    top = sorted(counts.items(), key=lambda kv: -kv[1])
    total = float(n)

    bg = top[0][0]
    bg_lum = _lum(bg)
    dark = bg_lum < 110

    # 候选色：占比够、且与背景有明显差异（排除背景的明暗抖动）
    def far(c, ref, thr=60):
        return sum(abs(c[i] - ref[i]) for i in range(3)) > thr

    cands = [(c, cnt) for c, cnt in top[:220]
             if cnt / total >= 0.0012 and far(c, bg, 70)]
    if not cands:
        cands = top[:10]

    # 前景：取亮度极值（细文字在 DC 下会被冲淡，按对比度选会选到中间调）
    fg = max(cands, key=lambda kv: _lum(kv[0]))[0] if dark \
        else min(cands, key=lambda kv: _lum(kv[0]))[0]

    # 强调色：候选里饱和度最高、且与 fg/bg 都拉得开的色
    accent, best_sat = fg, -1.0
    for c, cnt in cands:
        if not far(c, fg, 45):
            continue
        s = _sat(c)
        if s > best_sat:
            best_sat, accent = s, c
    if best_sat < 0.14:
        accent = fg

    # 次要色：与 accent 色相差得开、占比次高的色
    accent2 = accent
    for c, cnt in cands:
        if sum(abs(c[i] - accent[i]) for i in range(3)) > 70 and far(c, bg, 70):
            accent2 = c
            break
            accent2 = c
            break

    muted = _mix(bg, fg, 0.45)
    line = _mix(bg, fg, 0.22)
    soft = _mix(bg, fg, 0.06)

    # 版心：非背景像素的外接框
    thr = 30
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            i = (y * w + x) * 3
            d = abs(px[i] - bg[0]) + abs(px[i + 1] - bg[1]) + abs(px[i + 2] - bg[2])
            if d > thr:
                xs.append(x)
                ys.append(y)
    if xs:
        margin = (min(xs) / float(w) + (1.0 - max(xs) / float(w)) +
                  min(ys) / float(h) + (1.0 - max(ys) / float(h))) / 4.0
    else:
        margin = 0.05

    # 密度：平均梯度
    s = 0.0
    cnt = 0
    for y in range(1, h):
        i0 = y * w * 3
        for x in range(1, w):
            i = i0 + x * 3
            s += (abs(px[i] - px[i - 3]) + abs(px[i] - px[i - w * 3]))
            cnt += 2
    grad = s / max(1, cnt)

    # dark 已在上方计算
    extends = "tech" if dark else ("guofeng" if accent[0] > accent[2] + 30 else "minimal")
    line_height = 1.62 if grad > 12 else (1.78 if grad > 7 else 1.92)

    theme = {
        "extends": extends,
        "palette": {
            "bg": _hex(bg), "fg": _hex(fg), "accent": _hex(accent),
            "accent2": _hex(accent2), "muted": _hex(muted),
            "line": _hex(line), "soft": _hex(soft),
        },
        "density": {"line_height": round(line_height, 2)},
        "_analysis": {
            "source": os.path.basename(path),
            "size": [w, h],
            "dark": dark,
            "margin": round(margin, 4),
            "gradient": round(grad, 2),
            "contrast_fg_bg": round(_contrast(fg, bg), 2),
            "top_colors": [{"color": _hex(c), "share": round(v / total, 4)}
                           for c, v in top[:8]],
        },
    }
    return theme


def report(theme):
    a = theme["_analysis"]
    p = theme["palette"]
    print("参考图分析：%s  %dx%d" % (a["source"], a["size"][0], a["size"][1]))
    print("  明暗      : %s（背景亮度倾向 %s）" % ("暗底" if a["dark"] else "亮底",
                                            "深" if a["dark"] else "浅"))
    print("  对比度    : fg/bg = %.2f:1" % a["contrast_fg_bg"])
    print("  版心留白  : %.1f%%（短边）" % (a["margin"] * 100))
    print("  密度梯度  : %.1f" % a["gradient"])
    print("  建议 extends: %s" % theme["extends"])
    print("  色板:")
    for k in ("bg", "fg", "accent", "accent2", "muted", "line", "soft"):
        print("    %-8s %s" % (k, p[k]))
    print("  主色占比:")
    for t in a["top_colors"]:
        print("    %s  %.1f%%" % (t["color"], t["share"] * 100))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="poster-analyze",
                                 description="参考图 → theme 草稿")
    ap.add_argument("image", help="参考图（PNG 或 JPEG）")
    ap.add_argument("--out", default=None, help="输出 theme.json 路径")
    ap.add_argument("--json", action="store_true", help="只输出 JSON")
    ap.add_argument("--size", type=int, default=160, help="分析用缩略图边长")
    args = ap.parse_args(argv)

    theme = analyze(args.image, args.size)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(theme, fh, ensure_ascii=False, indent=2)
    if args.json:
        print(json.dumps(theme, ensure_ascii=False, indent=2))
    else:
        report(theme)
        if args.out:
            print("\n已写入 %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
