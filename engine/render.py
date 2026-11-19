# -*- coding: utf-8 -*-
"""render.py — 组装与命令行入口。

一份 layout + 一份 content + 一个 theme → PNG / PDF。
对外只暴露四个旋钮：preset（或 size）、format、--for（用途档）、--deco（装饰密度）。
"""

import argparse
import json
import os
import sys

from . import cache as _cache
from .backends.pdf import render_pdf
from .blocks import BLOCKS
from .canvas import Canvas
from .layouts import place, skeleton_names
from .theme import PRESETS, load_theme, resolve_preset

SS_BY_FOR = {"draft": 1, "preview": 2, "publish": 3, "print": 2}


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _deco_bg(cv, th, w, h):
    """背景装饰层（暗角 / 纸纹）。放在内容之前，允许出血。"""
    d = th.data.get("deco", {})
    vig = float(d.get("vignette", 0.0))
    if vig > 0:
        # 暗角只在四边画**一条**窄带：逐像素半透明混合是纯 Python 的主要开销，
        # 12 条全宽带实测吃掉 10 秒；一条 2.8% 短边的带足够表达压角。
        band = min(w, h) * 0.028
        ink = "#000000"          # 暗角一律压暗，不能用 fg（暗色主题会变成发光条）
        a = vig * 0.22
        cv.rect(0, 0, w, band, ink, alpha=a, bleed=True)
        cv.rect(0, h - band, w, h, ink, alpha=a, bleed=True)
        cv.rect(0, 0, band, h, ink, alpha=a, bleed=True)
        cv.rect(w - band, 0, w, h, ink, alpha=a, bleed=True)
    grain = float(d.get("grain", 0.0))
    if grain > 0:
        # 颗粒：确定性散点（不依赖 random 全局状态，可复现）
        s = 7
        n = int(2200 * grain)
        ink = th.data["palette"].get("fg", "#000000")
        for i in range(n):
            s = (s * 1103515245 + 12345) & 0x7fffffff
            x = (s >> 8) % max(1, int(w))
            s = (s * 1103515245 + 12345) & 0x7fffffff
            y = (s >> 8) % max(1, int(h))
            cv.rect(x, y, x + 1.2, y + 1.2, ink, alpha=0.10 * grain, bleed=True)


def cv_ellipse(cx, cy, rx, ry):
    from .geometry import ellipse
    return ellipse(cx, cy, rx, ry)


def build_canvas(layout, content, theme=None, preset_name=None, for_="preview", ss=None):
    """按 layout 组装画布（不输出文件）。返回 (canvas, preset, theme, ctx)。"""
    preset_name = preset_name or layout.get("preset", "xhs-3x4")
    preset = resolve_preset(preset_name)
    w, h = preset["px"]
    th = load_theme(theme or layout.get("theme", "minimal"), w, h)
    ov = layout.get("theme_overrides")
    if ov:
        from .theme import apply_overrides
        th = apply_overrides(th, ov)
    ss = int(ss if ss is not None else SS_BY_FOR.get(for_, 2))
    if preset["mode"] == "print":
        # 印刷稿本身已经是 300ppi，超采样只会成倍放大耗时（A4@ss3 实测 52s）
        ss = min(ss, 1)
    cv = Canvas(w, h, ss=ss, bg=th.color("bg")[0])
    _deco_bg(cv, th, w, h)          # 背景装饰属于静态层（由 theme 决定）
    ctx = {"content": content or {}, "preset": preset, "page": (w, h), "for": for_}
    # 版心留白取「主题意图」与「印刷安全区」的较大者
    margin = max(th.margin(), preset.get("safe_px", 0.0))
    placed = place(w, h, margin, layout.get("skeleton", "single-page"),
                   layout.get("blocks", []), th.gutter())

    # 只有排在列表最前面的静态块（scene/motifs）进入静态层：
    # 这样缓存复用时绘制顺序不变，动态内容仍然画在它们之上。
    static_types = set(_cache.STATIC_TYPES)
    n_static = 0
    for spec, _box in placed:
        if spec.get("type") in static_types:
            n_static += 1
        else:
            break

    for i, (spec, box) in enumerate(placed):
        fn = BLOCKS.get(spec.get("type"))
        if fn is None:
            continue
        cv.use_layer("static" if i < n_static else "dynamic")
        fn(cv, box, spec.get("params", {}), th, ctx)
    cv.use_layer("static")
    return cv, preset, th, ctx


def _png_with_cache(cv, preset, layout, th, out, exact, dpi, use_cache=True):
    """分层渲染：静态层走磁盘缓存，动态层每次重画。"""
    from .backends.raster import RasterBackend
    be = RasterBackend(cv.w, cv.h, cv.ss, cv.bg)
    sops = _cache.static_ops(cv.ops)
    dops = _cache.dynamic_ops(cv.ops)
    hit = False
    if sops and use_cache:
        key = _cache.static_key(layout, th.data, preset, cv.ss)
        hit = _cache.load_into(key, be.buf)
        if not hit:
            be.run(sops)
            _cache.save(key, be.buf)
    be.run(dops)
    p = be.png(out, exact=exact, dpi=dpi)
    _png_with_cache.last_hit = hit
    return p


_png_with_cache.last_hit = False


def render(layout, content, theme=None, preset_name=None, out=None,
           for_="preview", fmt=None, ss=None, use_cache=False):
    """核心渲染函数。返回输出路径。"""
    cv, preset, th, ctx = build_canvas(layout, content, theme, preset_name, for_, ss)
    if out is None:
        out = "out." + ("pdf" if (fmt == "pdf" or (fmt is None and for_ == "print")) else "png")
    if fmt is None:
        fmt = "pdf" if for_ == "print" else "png"
    if fmt == "pdf":
        return render_pdf(cv, out, preset["pt"])
    if fmt == "svg":
        from .backends.svg import render_svg
        return render_svg(cv, out)
    # dpi 必须随超采样一起放大：输出 3× 像素时若仍写 96dpi，物理尺寸会错 3 倍
    exact = preset["mode"] == "print"
    dpi = int(round(preset.get("dpi", 96) * (1 if exact else cv.ss)))
    return _png_with_cache(cv, preset, layout, th, out, exact, dpi, use_cache)


# ---------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(prog="poster", description="宣传图/海报渲染器")
    ap.add_argument("layout", help="layout.json 路径")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--content", default=None, help="content.json（默认取 layout 同目录 content.json）")
    ap.add_argument("--theme", default=None, help="主题名或 theme.json")
    ap.add_argument("--preset", default=None, help="画布预设（可覆盖 layout.preset）")
    ap.add_argument("--for", dest="for_", default="preview",
                    choices=sorted(SS_BY_FOR), help="用途档：draft/preview/publish/print")
    ap.add_argument("--format", dest="fmt", default=None, choices=["png", "pdf", "svg"])
    ap.add_argument("--ss", type=int, default=None, help="覆盖超采样倍率（调试用）")
    ap.add_argument("--cache", action="store_true",
                    help="启用静态层位图缓存（仅当静态层很重时划算，见 refs/workflow.md）")
    ap.add_argument("--check", action="store_true",
                    help="渲染后跑自检（越界/对比度/字号/色数/缺字/slot）")
    ap.add_argument("--list", action="store_true", help="列出预设/骨架/区块后退出")
    args = ap.parse_args(argv)

    if args.list:
        print("presets:", ", ".join(sorted(PRESETS)))
        print("skeletons:", ", ".join(skeleton_names()))
        print("blocks:", ", ".join(sorted(BLOCKS)))
        return 0

    layout = load_json(args.layout)
    cpath = args.content
    if cpath is None:
        cand = os.path.join(os.path.dirname(os.path.abspath(args.layout)), "content.json")
        cpath = cand if os.path.isfile(cand) else None
    content = load_json(cpath) if cpath else {"slots": {}}
    theme = args.theme
    if theme and theme.endswith(".json"):
        theme = load_json(theme)
    out = render(layout, content, theme=theme, preset_name=args.preset,
                 out=args.out, for_=args.for_, fmt=args.fmt, ss=args.ss,
                 use_cache=args.cache)
    print(out)

    if args.check:
        from .check import check_canvas, report
        cv, preset, th, ctx = build_canvas(layout, content, theme=theme,
                                           preset_name=args.preset,
                                           for_=args.for_, ss=args.ss)
        ok = report(check_canvas(cv, preset, th, content, layout), "自检")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
