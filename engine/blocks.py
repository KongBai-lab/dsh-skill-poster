# -*- coding: utf-8 -*-
"""blocks.py — 声明式区块库。

每个区块是一个函数：fn(cv, box, params, theme, ctx)
    box    = (x, y, w, h) 绝对坐标
    params = 区块参数（slot、scale、align…）
    ctx    = {"content": 文案槽, "preset": 预设, "page": (w, h)}

区块只负责「在一个盒子里把一件事画好」，不关心自己在哪里——
位置由 layouts.py 的骨架决定。这样同一个区块能出现在任何骨架里。
"""

from . import geometry as G
from . import typography as T

BLOCKS = {}


def block(name):
    def deco(fn):
        BLOCKS[name] = fn
        return fn
    return deco


# ---------------------------------------------------------------- 工具
def _slot(ctx, params, default=""):
    slots = ctx.get("content", {}).get("slots", {})
    return slots.get(params.get("slot", ""), default)


def _text(cv, text, box, th, role, align="left", valign="center",
          scale=1.0, color="fg", tracking=None, max_lines=None):
    if not text:
        return 0.0
    x, y, w, h = box
    size = th.fs(role, scale)
    fam, wt = th.font(role)
    tr = th.tracking(role) if tracking is None else tracking
    lines = T.wrap(text, w, size, fam, wt, tr, squeeze=True)
    if max_lines:
        lines = lines[:max_lines]
    lh = size * th.line(role)
    block_h = lh * len(lines)
    if valign == "center":
        ty = y + (h - block_h) * 0.5
    elif valign == "bottom":
        ty = y + h - block_h
    else:
        ty = y
    for ln in lines:
        if align == "center":
            tx = x + w * 0.5
        elif align == "right":
            tx = x + w
        else:
            tx = x
        cv.fill(T.text_path(ln, tx, ty, size, fam, wt, tr, align=align,
                            squeeze=True, baseline=False), th.color(color),
                rule="evenodd")
        ty += lh
    return block_h


def _centered_x(box, text, size, fam, wt, tr=0.0):
    return box[0] + (box[2] - T.measure(text, size, fam, wt, tr, True)) * 0.5


# ---------------------------------------------------------------- 区块
@block("motifs")
def motifs_block(cv, box, params, th, ctx):
    """从素材包（packs/<name>/motifs.py）调用装饰函数。

    items: [{"fn": "mountains_soft", "args": [x,y,w,h], "color": "accent2", "alpha": 0.2}]
    """
    import importlib
    pack = params.get("pack")
    if not pack:
        return
    try:
        mod = importlib.import_module("packs.%s.motifs" % pack)
    except Exception:
        return
    for spec in params.get("items", []):
        fn = getattr(mod, spec.get("fn", ""), None)
        if fn is None:
            continue
        color = th.rgb(spec.get("color", "accent2"))
        kw = {"alpha": spec.get("alpha", 0.3)}
        kw.update(spec.get("kwargs", {}))
        cv.bleed_mode(True)          # 背景装饰允许出血，越过安全线不算错
        try:
            fn(cv, *spec.get("args", []), color=color, **kw)
        finally:
            cv.bleed_mode(False)


@block("hero")
def hero(cv, box, params, th, ctx):
    text = _slot(ctx, params)
    if not text:
        return
    x, y, w, h = box
    size = th.fs("title", params.get("scale", 1.0))
    fam, wt = th.font("title")
    tr = th.tracking("title")
    align = params.get("align", "center")
    color = th.color(params.get("color", "fg"))
    gap = params.get("gap", 0.0)

    # 支持显式换行：标题按 \n 拆成多行，整块垂直居中
    # 总高按「字形 ascent + 行距」算，不能按 line_height*n，否则首行会顶出安全区
    lines = text.split("\n") if "\n" in text else [text]
    line_h = size * (params.get("line_height", 1.12))
    asc = size * 0.88
    total = line_h * (len(lines) - 1) + asc
    ty = y + (h - total) * 0.5 + asc

    for ln in lines:
        if gap:
            tw = T.measure(ln, size, fam, wt, 0.0, False) + gap * size * max(0, len(ln) - 1)
            ax = x + (w - tw) * 0.5 if align == "center" else (x + w - tw if align == "right" else x)
            path = T.spaced_path(ln, ax, ty, size,
                                 gap * size, fam, wt, align="left")
        else:
            path = T.text_path(ln, x if align == "left" else x + w * 0.5,
                               ty, size, fam, wt, tr, align=align, baseline=True)
        cv.fill(path, color, rule="evenodd")
        ty += line_h


@block("subtitle")
def subtitle(cv, box, params, th, ctx):
    _text(cv, _slot(ctx, params), box, th, "subtitle",
          align=params.get("align", "center"), color=params.get("color", "accent"),
          tracking=params.get("tracking"), max_lines=params.get("max_lines", 2))


@block("section_title")
def section_title(cv, box, params, th, ctx):
    text = _slot(ctx, params)
    if not text:
        return
    x, y, w, h = box
    size = th.fs("label", params.get("scale", 1.0))
    fam, wt = th.font("label")
    cv.fill(G.circle(x + size * 0.30, y + size * 0.52, size * 0.20), th.color("accent"))
    cv.fill(T.text_path(text, x + size * 0.82, y + size * 0.16, size, fam, wt,
                        th.tracking("label"), squeeze=True), th.color("fg"),
            rule="evenodd")
    if params.get("rule", True):
        ly = y + size * 1.30
        cv.rect(x, ly, x + w, ly + max(1.0, th.line_w()), th.color("line")[0])
    return


@block("body")
def body(cv, box, params, th, ctx):
    _text(cv, _slot(ctx, params), box, th, "body",
          align=params.get("align", "left"), color=params.get("color", "fg"),
          scale=params.get("scale", 1.0), max_lines=params.get("max_lines"))


@block("bullets")
def bullets(cv, box, params, th, ctx):
    items = _slot(ctx, params, [])
    if isinstance(items, str):
        items = [items]
    if not items:
        return
    x, y, w, h = box
    size = th.fs("body", params.get("scale", 1.0))
    n = len(items)
    gap = h / n
    for i, it in enumerate(items):
        cy = y + i * gap
        cv.fill(G.circle(x + size * 0.34, cy + size * 0.68, size * 0.15), th.color("accent"))
        _text(cv, it, (x + size * 1.0, cy, w - size * 1.0, gap), th, "body",
              align="left", valign="top", scale=params.get("scale", 1.0),
              max_lines=params.get("max_lines", 2))


@block("summary")
def summary(cv, box, params, th, ctx):
    text = _slot(ctx, params)
    if not text:
        return
    x, y, w, h = box
    pad = h * 0.16
    r = h * 0.5 if th.pill() else min(h * 0.5, th.radius())
    cv.fill(G.rrect(x, y, x + w, y + h, r),
            th.color("soft")[0], alpha=0.85)
    _text(cv, text, (x + pad, y, w - pad * 2, h), th, "body",
          align=params.get("align", "left"))


@block("stat_row")
def stat_row(cv, box, params, th, ctx):
    stats = _slot(ctx, params, [])
    if not stats:
        return
    x, y, w, h = box
    n = len(stats)
    gap = params.get("gap", 0.04) * w
    cw = (w - gap * (n - 1)) / n
    for i, it in enumerate(stats):
        cx = x + i * (cw + gap)
        num = str(it.get("num", ""))
        unit = str(it.get("unit", ""))
        label = str(it.get("label", ""))
        size = th.fs("num", params.get("scale", 1.0))
        fam, wt = th.font("num")
        cv.fill(T.text_path(num, cx + cw * 0.5, y + h * 0.42, size, fam, wt,
                            align="center"), th.color("accent"), rule="evenodd")
        if unit:
            us = size * 0.42
            cv.fill(T.text_path(unit, cx + cw * 0.5 + T.measure(num, size, fam, wt) * 0.5 + us * 0.2,
                                y + h * 0.42, us, fam, wt), th.color("accent"), rule="evenodd")
        cs = th.fs("caption")
        cfam, cwt = th.font("caption")
        cv.fill(T.text_path(label, cx + cw * 0.5, y + h * 0.42 + cs * 1.9, cs, cfam, cwt,
                            align="center"), th.color("muted"), rule="evenodd")


@block("quote")
def quote(cv, box, params, th, ctx):
    text = _slot(ctx, params)
    if not text:
        return
    x, y, w, h = box
    q = params.get("mark", "「")
    ms = th.fs("title", 0.42)
    mfam, mwt = th.font("title")
    cv.fill(T.text_path(q, x, y + ms * 0.85, ms, mfam, mwt), th.color("line"), rule="evenodd")
    _text(cv, text, (x + ms * 0.55, y + h * 0.16, w - ms * 0.7, h * 0.7),
          th, "body", align="left", scale=params.get("scale", 1.25),
          color=params.get("color", "fg"))


@block("cta")
def cta(cv, box, params, th, ctx):
    text = _slot(ctx, params, {})
    if isinstance(text, dict):
        text = text.get("text", "")
    if not text:
        return
    x, y, w, h = box
    # 可选限宽：横幅/宽屏里按钮不该占满整行（会像进度条）
    mw = float(params.get("max_width", 1.0)) * w
    if mw < w:
        x += (w - mw) * 0.5
        w = mw
    pad = h * 0.22
    # 圆角由 theme 决定：pill=True 即胶囊，否则用主题圆角（瑞士风为 0）
    r = h * 0.5 if th.pill() else min(h * 0.5, th.radius())
    cv.fill(G.rrect(x, y, x + w, y + h, r), th.color("accent")[0])
    # 文字颜色按 accent 明度自动取反，暗色主题上不会出现「深字压暗底」
    acc = th.rgb("accent")
    lum = 0.299 * acc[0] + 0.587 * acc[1] + 0.114 * acc[2]
    ink = "bg" if lum > 150 else "fg"
    _text(cv, text, (x + pad, y, w - pad * 2, h), th, "label",
          align="center", color=ink, tracking=0.10)


@block("divider")
def divider(cv, box, params, th, ctx):
    x, y, w, h = box
    cy = y + h * 0.5
    style = params.get("style") or th.divider_style()
    if style == "wave":
        cv.stroke(G.divider_wave(x, x + w, cy, amp=h * 0.22, periods=params.get("periods", 5)),
                  th.color("line"), width=max(1.0, th.line_w()), cap="round")
    elif style == "thick":
        cv.rect(x, cy, x + w, cy + max(1.0, th.line_w(4.0)), th.color("fg")[0])
    else:
        cv.rect(x, cy, x + w, cy + max(1.0, th.line_w()), th.color("line")[0])


@block("footer")
def footer(cv, box, params, th, ctx):
    _text(cv, _slot(ctx, params), box, th, "caption",
          align=params.get("align", "left"), color="muted")


@block("seal")
def seal(cv, box, params, th, ctx):
    text = _slot(ctx, params)
    x, y, w, h = box
    s = min(w, h) * 0.8
    cx, cy = x + w * 0.5, y + h * 0.5
    cv.fill(G.rrect(cx - s * 0.5, cy - s * 0.5, cx + s * 0.5, cy + s * 0.5, s * 0.09),
            th.color("accent")[0])
    size = s * 0.34
    fam, wt = th.font("label")
    path = T.vtext_path(text, cx, cy - s * 0.28, size, fam, wt, tracking=0.08)
    cv.fill(path, th.color("bg"), rule="evenodd")


@block("icon_grid")
def icon_grid(cv, box, params, th, ctx):
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    cols = params.get("cols", min(4, len(items)))
    rows = int((len(items) + cols - 1) // cols)
    cw, ch = w / cols, h / max(1, rows)
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        cx = x + c * cw + cw * 0.5
        cy = y + r * ch + ch * 0.40
        rr = min(cw, ch) * 0.20
        if isinstance(it, dict):
            lab = str(it.get("label", ""))
            shape = it.get("shape", "circle")
        else:
            lab = str(it)
            shape = "circle"
        path, rule = _shape(shape, cx, cy, rr)
        cv.fill(path, th.color("accent"), alpha=0.9, rule=rule)
        size = th.fs("caption")
        fam, wt = th.font("caption")
        cv.fill(T.text_path(lab, cx, cy + rr * 1.9 + size * 0.9, size, fam, wt,
                            align="center"),
                th.color("fg"), rule="evenodd")


@block("timeline")
def timeline(cv, box, params, th, ctx):
    events = _slot(ctx, params, [])
    if not events:
        return
    x, y, w, h = box
    axis_y = y + h * 0.42
    n = len(events)
    cv.rect(x, axis_y, x + w, axis_y + max(1.0, h * 0.012), th.color("line")[0])
    for i, ev in enumerate(events):
        cx = x + w * (i + 0.5) / n
        cv.fill(G.circle(cx, axis_y + h * 0.006, h * 0.030), th.color("accent"))
        size = th.fs("caption")
        fam, wt = th.font("caption")
        cv.fill(T.text_path(str(ev.get("date", "")), cx, axis_y - h * 0.10, size, fam, wt,
                            align="center"), th.color("muted"), rule="evenodd")
        cv.fill(T.text_path(str(ev.get("text", "")), cx, axis_y + h * 0.16, size, fam, wt,
                            align="center"), th.color("fg"), rule="evenodd")


@block("microchart")
def microchart(cv, box, params, th, ctx):
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    label_w = params.get("label_w", 0.28) * w
    bar_area = w - label_w
    n = len(items)
    bh = min(h / n * 0.5, th.fs("caption") * 1.1)
    gap = (h - bh * n) / max(1, n + 1)
    vmax = max([float(it.get("value", 0)) for it in items] or [1.0]) or 1.0
    size = th.fs("caption")
    fam, wt = th.font("caption")
    for i, it in enumerate(items):
        label = str(it.get("label", ""))
        val = float(it.get("value", 0))
        by = y + gap + i * (bh + gap)
        cv.fill(T.text_path(label, x, by + bh * 0.82, size, fam, wt),
                th.color("fg"), rule="evenodd")
        bw = bar_area * (val / vmax) * 0.94
        cv.fill(G.rrect(x + label_w, by, x + label_w + bw, by + bh, bh * 0.5),
                th.color("accent"), alpha=0.9)
        cv.fill(T.text_path("%g" % val, x + label_w + bw + size * 0.4, by + bh * 0.82,
                            size * 0.92, fam, wt), th.color("muted"), rule="evenodd")


@block("shape_row")
def shape_row(cv, box, params, th, ctx):
    """图元陈列：按名字画真实图元（展示引擎能力）。"""
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    n = len(items)
    cw = w / n
    size = th.fs("caption")
    fam, wt = th.font("caption")
    scale = float(params.get("scale", 1.0))
    filled = params.get("fill", True)
    for i, it in enumerate(items):
        name = it.get("shape", "circle") if isinstance(it, dict) else str(it)
        label = it.get("label", "") if isinstance(it, dict) else str(it)
        cx = x + i * cw + cw * 0.5
        cy = y + h * 0.42
        r = min(cw * 0.34, h * 0.32) * scale
        path, rule = _shape(name, cx, cy, r)
        if filled:
            cv.fill(path, th.color("accent"), alpha=0.90, rule=rule)
        else:
            # 线框模式：科技风用得到，避免大色块像贴纸
            cv.stroke(path, th.color("accent"),
                      width=max(1.6, r * 0.05), alpha=0.85)
            cv.stroke(path, th.color("accent"),
                      width=max(0.8, r * 0.012), alpha=0.22)
        if label:
            cv.fill(T.text_path(label, cx, cy + r * 1.55 + size * 0.9, size,
                                fam, wt, align="center"),
                    th.color("muted"), rule="evenodd")


def _shape(name, cx, cy, r):
    if name == "leaf":
        return G.leaf(cx - r, cy + r * 0.55, r * 2.0, r * 0.9, angle=-0.35, bend=0.18), "evenodd"
    if name == "cloud":
        return G.cloud(cx, cy, r * 2.5, r * 1.05), "evenodd"
    if name == "star":
        return G.star(cx, cy, r, r * 0.44, points=5), "evenodd"
    if name == "drop":
        return G.drop(cx, cy, r * 0.78), "evenodd"
    if name == "flower":
        return G.flower(cx, cy, r * 1.05, petals=6, petal_width=r * 0.54), "nonzero"
    if name == "heart":
        return G.heart(cx, cy, r * 2.0), "evenodd"
    if name == "sparkle":
        return G.sparkle(cx, cy, r, points=4), "evenodd"
    return G.circle(cx, cy, r), "evenodd"


@block("gallery")
def gallery(cv, box, params, th, ctx):
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    cols = params.get("cols", len(items))
    cw = w / cols
    for i, it in enumerate(items):
        label = it if isinstance(it, str) else str(it.get("label", ""))
        cx = x + i * cw + cw * 0.5
        cy = y + h * 0.42
        r = min(cw, h * 0.6) * 0.26
        cv.fill(G.leaf(cx - r * 0.8, cy + r * 0.6, r * 1.9, r * 1.1, bend=0.1),
                th.color("accent"), alpha=0.85)
        cv.fill(G.circle(cx + r * 0.7, cy - r * 0.5, r * 0.55), th.color("accent2"), alpha=0.8)
        size = th.fs("caption")
        fam, wt = th.font("caption")
        cv.fill(T.text_path(label, cx, cy + r * 2.1, size, fam, wt, align="center"),
                th.color("fg"), rule="evenodd")


# ================================================================ 场景长图专用区块
@block("process_list")
def process_list(cv, box, params, th, ctx):
    """工序列表：序号圆 + 名称 + 两行说明。"""
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    n = len(items)
    row = h / max(1, n)
    name_s = th.fs("body", 1.02)
    fam, wt = th.font("body")
    cfam, cwt = th.font("caption")
    nfam, nwt = th.font("num")
    for i, it in enumerate(items):
        cy = y + i * row + row * 0.16
        rr = min(row * 0.15, th.fs("caption") * 1.05)
        cx = x + rr * 1.5
        cv.fill(G.circle(cx, cy + rr * 0.3, rr), th.color("accent"), alpha=0.88)
        cv.fill(T.text_path(str(it.get("num", "")), cx, cy + rr * 1.05,
                            rr * 1.02, nfam, nwt, align="center"),
                (255, 255, 255), rule="evenodd")
        tx = x + rr * 3.3
        cv.fill(T.text_path(it.get("name", ""), tx, cy + name_s * 0.62,
                            name_s, fam, wt, tracking=0.03),
                th.color("fg"), rule="evenodd")
        desc = it.get("desc", "")
        if desc:
            _text(cv, desc, (tx, cy + name_s * 0.95, w - (tx - x), row * 0.9),
                  th, "caption", align="left", valign="top",
                  max_lines=2, color="muted")


@block("donut")
def donut(cv, box, params, th, ctx):
    """环形图 + 右侧图例。"""
    import math
    items = _slot(ctx, params, [])
    if not items:
        return
    x, y, w, h = box
    cx, cy = x + w * 0.34, y + h * 0.50
    r = min(w * 0.28, h * 0.42)
    total = sum(float(it.get("value", 0)) for it in items) or 1.0
    base = [th.rgb("accent"), th.rgb("accent2"), th.rgb("muted"), th.rgb("fg")]
    a0 = -math.pi / 2
    for i, it in enumerate(items):
        da = 2 * math.pi * float(it.get("value", 0)) / total
        alpha = max(0.42, 0.92 - 0.16 * (i // len(base)))
        cv.fill(G.donut_sector(cx, cy, r, r * 0.58, a0, a0 + da),
                base[i % len(base)], alpha=alpha)
        a0 += da
    cfam, cwt = th.font("caption")
    size = th.fs("caption", 0.98)
    for i, it in enumerate(items):
        ly = y + h * (0.12 + 0.17 * i)
        cv.fill(G.circle(x + w * 0.68, ly, r * 0.085), base[i % len(base)], alpha=0.9)
        cv.fill(T.text_path("%s %g%%" % (it.get("label", ""), float(it.get("value", 0))),
                            x + w * 0.76, ly + size * 0.36, size, cfam, cwt),
                th.color("fg"), rule="evenodd")


@block("scene")
def scene(cv, box, params, th, ctx):
    """主场景（几何化重建）：远山 + 云 + 楼阁 + 茶席 + 竹。"""
    x, y, w, h = box
    ink = th.rgb("fg")
    moss = th.rgb("accent")
    ochre = th.rgb("accent2")
    cv.bleed_mode(True)          # 场景装饰允许越过安全线（竹叶、山体边缘）
    try:
        cv.fill(G.mountains(x, y + h * 0.16, x + w, y + h * 0.56, peaks=3, seed=5, jitter=0.5),
                moss, alpha=0.18)
        cv.fill(G.mountains(x, y + h * 0.30, x + w, y + h * 0.62, peaks=4, seed=11, jitter=0.4),
                moss, alpha=0.12)
        cv.fill(G.cloud(x + w * 0.28, y + h * 0.26, w * 0.40, h * 0.075), (255, 255, 255), alpha=0.55)
        cv.fill(G.cloud(x + w * 0.74, y + h * 0.35, w * 0.28, h * 0.060), (255, 255, 255), alpha=0.45)
        _bamboo(cv, x + w * 0.07, y + h * 0.06, y + h * 0.78, moss, 0.28)
        _bamboo(cv, x + w * 0.93, y + h * 0.10, y + h * 0.72, moss, 0.20)
        _pavilion(cv, x + w * 0.50, y + h * 0.615, w * 0.40, ink, ochre)
        # 茶席：若指定了 objects_pack，用素材包里的半写实器皿；否则用内置简笔
        pack = params.get("objects_pack")
        used_pack = False
        if pack:
            try:
                import importlib
                mod = importlib.import_module("packs.%s.objects" % pack)
                _tea_table_pack(cv, x + w * 0.50, y + h * 0.845, w * 0.66, ochre, mod)
                used_pack = True
            except Exception:
                used_pack = False
        if not used_pack:
            _tea_table(cv, x + w * 0.50, y + h * 0.845, w * 0.66, ochre, ink)
    finally:
        cv.bleed_mode(False)


def _bamboo(cv, x, y0, y1, color, alpha):
    """竹：略弯的粗竿 + 节 + 几簇下垂的叶。"""
    from .path import Path
    p = Path()
    p.move_to(x, y0)
    p.cubic_to(x - 10, y0 + (y1 - y0) * 0.35, x + 10, y0 + (y1 - y0) * 0.70, x + 2, y1)
    cv.stroke(p, color, width=max(2.0, (y1 - y0) * 0.011), alpha=alpha)
    for i in range(4):
        cy = y0 + (y1 - y0) * (0.22 + 0.18 * i)
        cv.stroke(_seg(x - (y1 - y0) * 0.012, cy, x + (y1 - y0) * 0.012, cy),
                  color, width=max(0.8, (y1 - y0) * 0.004), alpha=alpha * 0.7)
        # 每节出一小簇叶（两侧交替，向下垂）
        side = -1 if i % 2 else 1
        for k in range(2):
            cv.fill(G.leaf(x + side * (y1 - y0) * (0.01 + 0.02 * k),
                           cy + (y1 - y0) * 0.01,
                           (y1 - y0) * (0.13 - 0.02 * k), (y1 - y0) * 0.032,
                           angle=(-0.35 if side > 0 else -2.8) + k * 0.18,
                           bend=0.25),
                    color, alpha=alpha * (0.9 - 0.15 * k))


def _pavilion(cv, cx, base_y, w, ink, accent):
    """三层歇山楼阁：尖屋顶 + 浅色层身 + 立柱 + 台基（几何化，但保持建筑结构）。"""
    paper = (250, 246, 238)
    tiers = 3
    for i in range(tiers):
        tw = w * (1.0 - i * 0.16)
        ty = base_y - i * (w * 0.185)
        body_top = ty - w * 0.125
        # 层身
        cv.rect(cx - tw * 0.30, body_top, cx + tw * 0.30, ty, paper, alpha=0.92)
        # 立柱
        for k in (-1.0, 0.0, 1.0):
            px = cx + k * tw * 0.25
            cv.rect(px - w * 0.005, body_top, px + w * 0.005, ty, ink, alpha=0.55)
        # 尖屋顶（歇山）
        cv.fill(G.polygon([(cx - tw * 0.50, body_top),
                           (cx - tw * 0.56, body_top - w * 0.012),
                           (cx, body_top - w * 0.115),
                           (cx + tw * 0.56, body_top - w * 0.012),
                           (cx + tw * 0.50, body_top)]), ink, alpha=0.88)
        # 屋脊与飞檐
        cv.stroke(_seg(cx - tw * 0.56, body_top - w * 0.012,
                       cx + tw * 0.56, body_top - w * 0.012),
                  ink, width=max(1.0, w * 0.006), alpha=0.9)
    # 台基
    cv.rect(cx - w * 0.40, base_y, cx + w * 0.40, base_y + w * 0.032, ink, alpha=0.72)


def _seg(x0, y0, x1, y1):
    from .path import Path
    p = Path()
    p.move_to(x0, y0).line_to(x1, y1)
    return p


def _tea_table(cv, cx, cy, w, base, ink):
    """茶席：桌面 + 壶 + 盏 + 茶筅。"""
    import math
    cv.fill(G.ellipse(cx, cy, w * 0.50, w * 0.135), base, alpha=0.92)
    cv.stroke(G.ellipse(cx, cy, w * 0.50, w * 0.135), ink,
              width=max(1.0, w * 0.004), alpha=0.30)
    # 壶（左）：水滴身 + 壶嘴 + 提梁
    px = cx - w * 0.27
    cv.fill(G.drop(px, cy - w * 0.075, w * 0.040, tip=1.5), ink, alpha=0.85)
    cv.stroke(_seg(px + w * 0.030, cy - w * 0.085, px + w * 0.090, cy - w * 0.125),
              ink, width=max(1.0, w * 0.006), alpha=0.8)
    cv.stroke(G.arc(px, cy - w * 0.105, w * 0.045, 3.4, 6.0), ink,
              width=max(1.0, w * 0.005), alpha=0.6)
    # 盏（中）：碗形
    cv.fill(G.pie(cx, cy - w * 0.045, w * 0.075, 0.15, math.pi - 0.15), ink, alpha=0.80)
    # 茶筅（右）：细线束
    sx = cx + w * 0.25
    for k in range(5):
        a = -0.55 + k * 0.28
        cv.stroke(_seg(sx, cy - w * 0.145,
                       sx + math.sin(a) * w * 0.042, cy - w * 0.015),
                  ink, width=max(0.8, w * 0.0035), alpha=0.70)


def _tea_table_pack(cv, cx, cy, w, base, mod):
    """用 packs 里的半写实器皿布置茶席（桌面 + 壶 + 盏 + 筅 + 托）。"""
    cv.fill(G.ellipse(cx, cy, w * 0.50, w * 0.135), base, alpha=0.92)
    cv.stroke(G.ellipse(cx, cy, w * 0.50, w * 0.135), (60, 46, 36),
              width=max(1.0, w * 0.004), alpha=0.30)
    ow = w * 0.17
    mod.kettle(cv, cx - w * 0.24, cy - w * 0.020, ow * 1.15)
    mod.cup(cv, cx + w * 0.02, cy - w * 0.012, ow * 0.92)
    mod.whisk(cv, cx + w * 0.24, cy - w * 0.006, ow * 0.62)
