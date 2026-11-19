# -*- coding: utf-8 -*-
"""check.py — 渲染前后的硬断言。

目标：把「只有看图才发现」的问题提前到秒级。
包含几何完整性、版式安全、文字可读性、内容一致性四类。
"""

from .fonts import missing
from . import typography as T


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(rgb)


def _lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2])


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def check_canvas(cv, preset, theme, content=None, layout=None,
                 min_body_ratio=0.020, max_colors=16):
    """返回 problems 列表；空列表 = 通过。"""
    problems = []
    w, h = preset["px"]
    safe = preset.get("safe_px", 0.045 * min(w, h))

    # 1) 越界：除背景/暗角外的 op 必须在安全区内
    for i, op in enumerate(cv.ops):
        if op.get("allow_bleed"):
            continue
        x0, y0, x1, y1 = op["path"].bbox()
        pad = op.get("width", 0.0) * 0.5 if op["k"] == "stroke" else 0.0
        if (x0 - pad) < safe - 1 or (y0 - pad) < safe - 1 \
                or (x1 + pad) > w - safe + 1 or (y1 + pad) > h - safe + 1:
            problems.append("越界: op#%d bbox=(%.1f,%.1f,%.1f,%.1f) 安全区=%.1f"
                            % (i, x0, y0, x1, y1, safe))

    # 2) 对比度：正文色 vs 背景
    fg = theme.rgb("fg")
    bg = theme.rgb("bg")
    c = contrast(fg, bg)
    if c < 4.5:
        problems.append("对比度不足: fg/bg = %.2f:1（正文要求 >= 4.5，标题 >= 3）" % c)

    # 3) 最小字号
    body_px = theme.fs("body")
    ratio = body_px / min(w, h)
    if ratio < min_body_ratio - 1e-6:
        problems.append("正文字号偏小: %.4f×短边（下限 %.4f）" % (ratio, min_body_ratio))

    # 4) 色数（按色相量化：明暗变体不算新色，否则半写实插画必然超标）
    colors = set()
    for op in cv.ops:
        r, g, b = op["color"]
        colors.add((r // 56, g // 56, b // 56))
    if len(colors) > max_colors:
        problems.append("色数过多: %d（建议 <= %d）" % (len(colors), max_colors))

    # 5) 缺字（对 content 全部文案）
    if content:
        slots = content.get("slots", {})
        for key, val in slots.items():
            texts = _collect_text(val)
            for t in texts:
                miss = missing(t, theme.font("body")[0])
                if miss:
                    problems.append("缺字: slot=%s 字体=%s -> %s"
                                    % (key, theme.font("body")[0], "".join(miss)))

    # 6) slot 完整性
    if layout and content:
        slots = content.get("slots", {})
        for spec in layout.get("blocks", []):
            s = spec.get("params", {}).get("slot")
            if s and s not in slots:
                problems.append("slot 缺失: 区块 %s 引用了不存在的 slot %r"
                                % (spec.get("type"), s))
    return problems


def _collect_text(val):
    out = []
    if isinstance(val, str):
        out.append(val)
    elif isinstance(val, list):
        for v in val:
            out.extend(_collect_text(v))
    elif isinstance(val, dict):
        for v in val.values():
            out.extend(_collect_text(v))
    return out


def check_geometry(paths, tol=0.25):
    """几何断言：每条路径细分后弦高 <= tol*1.35。"""
    from .path import chord_error
    bad = []
    for name, p in paths:
        err = chord_error(p, tol)
        if err > tol * 1.35:
            bad.append("%s 弦高 %.3f > %.3f" % (name, err, tol * 1.35))
    return bad


def report(problems, title="检查"):
    if not problems:
        print("[%s] 通过" % title)
        return True
    print("[%s] %d 个问题：" % (title, len(problems)))
    for p in problems:
        print("  - " + p)
    return False
