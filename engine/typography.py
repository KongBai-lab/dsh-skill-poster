# -*- coding: utf-8 -*-
"""typography.py — 中文排版：断行、避头尾、标点挤压、竖排、字距。

设计取舍
--------
- 断行按**像素宽度**逐 token 断，而不是按字数：同一段文字换字号后行数自然不同。
- 避头尾只处理最常踩的两类（行首禁则 / 行尾禁则），足够应付海报文案。
- 标点挤压默认开启：中文句读占半角，行末不会出现「。」单独占一格的松垮感。
- 竖排使用独立于横排的基线推进，标点自动落到字框右上（竖排规范）。
- 所有输出都是 Path，与图形共用同一条渲染管线。
"""

import math

from .fonts import advance, glyph_path
from .path import Path

# 行首禁则：不能出现在行首
PUNCT_HEAD = "，。、；：？！）】》」』〕〉”’…‰℃·"
# 行尾禁则：不能出现在行尾
PUNCT_TAIL = "（【《「『〔〈“‘"
# 可挤压的全角标点
PUNCT_SQUEEZE = "，。、；：？！"
# 竖排时移到字框右上的标点
PUNCT_VERT = "，。、：；"


def _cw(ch, size, family, weight, squeeze):
    w = advance(ch, size, family, weight)
    if squeeze and ch in PUNCT_SQUEEZE:
        w *= 0.5
    return w


def measure(s, size, family="hei", weight="regular", tracking=0.0, squeeze=False):
    """单行宽度。"""
    if not s:
        return 0.0
    w = 0.0
    for ch in s:
        w += _cw(ch, size, family, weight, squeeze)
        w += tracking * size
    return w - tracking * size if len(s) else 0.0


def _tokens(s):
    """切成「中文单字 / 英文单词 / 其它符号」，英文单词不拆。"""
    out = []
    buf = ""
    for ch in s:
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ("0" <= ch <= "9") or ch in "'-_":
            buf += ch
        else:
            if buf:
                out.append(buf)
                buf = ""
            out.append(ch)
    if buf:
        out.append(buf)
    return out


def wrap(text, max_w, size, family="hei", weight="regular",
         tracking=0.0, squeeze=True, indent=0.0):
    """按像素宽度断行（含避头尾、标点挤压）。返回行列表。"""
    lines = []
    for part in text.split("\n"):
        toks = _tokens(part)
        cur = ""
        limit = max_w - indent
        first = True
        for tok in toks:
            tw = measure(tok, size, family, weight, tracking, squeeze)
            cw = measure(cur, size, family, weight, tracking, squeeze)
            room = limit if not lines or first else max_w
            if cur and cw + tw > room:
                if tok[0] in PUNCT_HEAD and len(cur) > 1:
                    # 行首禁则：把上一字带下来，与新行首组成一行
                    carry = cur[-1]
                    rest = cur[:-1]
                    if rest:
                        lines.append(rest)
                    cur = carry + tok
                elif cur[-1] in PUNCT_TAIL and len(cur) > 1:
                    # 行尾禁则：把禁则符带到下一行
                    carry = cur[-1]
                    rest = cur[:-1]
                    if rest:
                        lines.append(rest)
                    cur = carry + tok
                else:
                    lines.append(cur)
                    cur = tok
                first = False
            else:
                cur += tok
        if cur:
            lines.append(cur)
        indent = 0.0
    return lines


def text_path(s, x, y, size, family="hei", weight="regular",
              tracking=0.0, align="left", squeeze=False, baseline=True):
    """单行文字 → Path。y 是基线（baseline=True）或顶边（False）。"""
    w = measure(s, size, family, weight, tracking, squeeze)
    if align == "center":
        x -= w * 0.5
    elif align == "right":
        x -= w
    if not baseline:
        y += size * 0.86          # 近似 ascent
    p = Path()
    cur = x
    for ch in s:
        if ch != " ":
            g = glyph_path(ch, size, family, weight, cur, y)
            if g is not None:
                p.extend(g)
        cur += _cw(ch, size, family, weight, squeeze) + tracking * size
    return p


def para_path(text, x, y_top, max_w, size, line_height=None,
              family="hei", weight="regular", tracking=0.0,
              align="left", first_indent=0.0, squeeze=True):
    """多行段落 → Path。y_top 是首行顶边。"""
    lh = line_height if line_height else size * 1.72
    lines = wrap(text, max_w, size, family, weight, tracking,
                 squeeze, indent=first_indent)
    p = Path()
    y = y_top
    for i, ln in enumerate(lines):
        ix = x + (first_indent if i == 0 else 0.0)
        p.extend(text_path(ln, ix, y, size, family, weight,
                           tracking, align=align, squeeze=squeeze, baseline=False))
        y += lh
    return p


def para_lines(text, max_w, size, family="hei", weight="regular",
               tracking=0.0, squeeze=True, first_indent=0.0):
    """只要断行结果（做版式计算、行数统计、check 断言时用）。"""
    return wrap(text, max_w, size, family, weight, tracking, squeeze, first_indent)


def vtext_path(s, x, y_top, size, family="hei", weight="regular",
               tracking=0.0, squeeze=False, punct_top_right=True):
    """竖排文字 → Path。x 是列中心，y_top 是首字顶边。"""
    p = Path()
    y = y_top + size * 0.86          # 首字基线
    for ch in s:
        if ch == "\n":
            y -= size * 1.2
            continue
        if ch == " ":
            y -= size + tracking * size
            continue
        adv = advance(ch, size, family, weight)
        gx = x - adv * 0.5
        gy = y
        if punct_top_right and ch in PUNCT_VERT:
            gx += size * 0.42
            gy -= size * 0.42
        g = glyph_path(ch, size, family, weight, gx, gy)
        if g is not None:
            p.extend(g)
        step = _cw(ch, size, family, weight, squeeze)
        y += step + tracking * size          # 竖排：从上往下（画布 y 向下）
    return p


def spaced_path(s, x, y, size, gap, family="hei", weight="regular",
                align="left", squeeze=False):
    """逐字加宽字距（标题常用）。gap 为字与字之间的额外间距（逻辑像素）。"""
    w = measure(s, size, family, weight, 0.0, squeeze) + gap * max(0, len(s) - 1)
    if align == "center":
        x -= w * 0.5
    elif align == "right":
        x -= w
    p = Path()
    cur = x
    for ch in s:
        g = glyph_path(ch, size, family, weight, cur, y)
        if g is not None:
            p.extend(g)
        cur += _cw(ch, size, family, weight, squeeze) + gap
    return p


def text_block_size(text, max_w, size, family="hei", weight="regular",
                    tracking=0.0, line_height=None, squeeze=True):
    """文本块尺寸 (宽, 高)，用于版式占位与 check 越界检测。"""
    lh = line_height if line_height else size * 1.72
    lines = wrap(text, max_w, size, family, weight, tracking, squeeze)
    w = max([measure(l, size, family, weight, tracking, squeeze) for l in lines] or [0.0])
    return w, lh * len(lines)
