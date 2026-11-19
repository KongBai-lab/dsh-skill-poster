# -*- coding: utf-8 -*-
"""theme.py — 主题（皮肤）与画布预设（尺寸）。

字号用「占短边的比例」而不是像素：同一 theme 换到 A4 或方图，
字号层级自动等比，不会出现「在小红书合适、到 A4 像小字报」。
"""

import copy

from .canvas import parse_color


# ---------------------------------------------------------------- 预设
# mode=screen: pt = px * 0.75（96dpi 基准）；mode=print: pt = mm/25.4*72
PRESETS = {
    "xhs-3x4":      {"mode": "screen", "px": (1080, 1440), "safe": 0.045, "fmt": ("png",)},
    "sq-1x1":       {"mode": "screen", "px": (1080, 1080), "safe": 0.045, "fmt": ("png",)},
    "story-9x16":   {"mode": "screen", "px": (1080, 1920), "safe": 0.042, "fmt": ("png",)},
    "wechat-cover": {"mode": "screen", "px": (900, 383),   "safe": 0.030, "fmt": ("png",)},
    "video-16x9":   {"mode": "screen", "px": (1920, 1080), "safe": 0.040, "fmt": ("png",)},
    "info-long":    {"mode": "screen", "px": (1080, 2160), "safe": 0.040, "fmt": ("png", "pdf")},
    "a4-portrait":  {"mode": "print", "mm": (210, 297), "ppi": 300,
                     "safe": 0.057, "bleed": 0.0143, "fmt": ("pdf", "png")},
    "a3-portrait":  {"mode": "print", "mm": (297, 420), "ppi": 300,
                     "safe": 0.050, "bleed": 0.0143, "fmt": ("pdf", "png")},
    "rollup-85x200": {"mode": "print", "mm": (850, 2000), "ppi": 100,
                      "safe": 0.050, "bleed": 0.0, "fmt": ("pdf", "png")},
}


def resolve_preset(name):
    """把预设展开成统一结构：px / pt / safe_px / dpi。"""
    if name not in PRESETS:
        raise KeyError("未知 preset: %r（可选：%s）" % (name, ", ".join(sorted(PRESETS))))
    p = copy.deepcopy(PRESETS[name])
    if p["mode"] == "print":
        mm_w, mm_h = p["mm"]
        ppi = p.get("ppi", 300)
        px_w = int(round(mm_w / 25.4 * ppi))
        px_h = int(round(mm_h / 25.4 * ppi))
        pt_w = mm_w / 25.4 * 72.0
        pt_h = mm_h / 25.4 * 72.0
        dpi = ppi
    else:
        px_w, px_h = p["px"]
        pt_w, pt_h = px_w * 0.75, px_h * 0.75
        dpi = 96
    p.update({"px": (px_w, px_h), "pt": (pt_w, pt_h), "dpi": dpi,
              "safe_px": p["safe"] * min(px_w, px_h)})
    return p


# ---------------------------------------------------------------- 主题
BASE_THEME = {
    "palette": {
        "bg": "#F7F5F0", "fg": "#1E1E1E", "accent": "#C0392B",
        "accent2": "#8C5C34", "muted": "#8A8578", "line": "#D9D4C7",
        "soft": "#EDE9E0",
    },
    "type": {
        "title":    {"family": "song", "weight": "regular", "size": 0.088, "tracking": 0.02, "line": 1.12},
        "subtitle": {"family": "kai", "weight": "regular", "size": 0.030, "tracking": 0.06, "line": 1.5},
        "body":     {"family": "fang", "weight": "regular", "size": 0.0215, "tracking": 0.0, "line": 1.75},
        "caption":  {"family": "hei", "weight": "regular", "size": 0.015, "tracking": 0.0, "line": 1.6},
        "label":    {"family": "hei", "weight": "bold", "size": 0.018, "tracking": 0.02, "line": 1.4},
        "num":      {"family": "yuan", "weight": "bold", "size": 0.052, "tracking": 0.0, "line": 1.1},
    },
    "space": {"margin": 0.055, "gutter": 0.022},
    "deco": {"grain": 0.0, "vignette": 0.0, "level": 0, "pattern": None},
    # ---- 风格参数（模仿一套设计语言时，改这些而不是改区块代码）----
    "shape": {
        "radius": 0.012,      # 圆角半径（相对短边）；0 = 硬朗，0.03+ = 柔和
        "line_width": 0.0011, # 默认描边线宽（相对短边）
        "cap": "butt",        # 描边端点：butt / round / square
        "join": "miter",      # 描边拐角：miter / round / bevel
        "pill": False,        # cta 是否用胶囊形（覆盖 radius）
    },
    "depth": {"shadow": 0.0, "shadow_dy": 0.004},
    "ornament": {"divider": "line", "corner": False, "border": False},
    "density": {"line_height": None, "block_gap": 1.0, "text_max_width": 0.62},
}

THEMES = {
    "minimal": {},
    "guofeng": {
        "palette": {"bg": "#F2ECDD", "fg": "#2C3A32", "accent": "#A03C2C",
                    "accent2": "#8C5C34", "muted": "#7C7A66", "line": "#D6CCB4",
                    "soft": "#E7DFC9"},
        "type": {
            "title": {"family": "xingkai", "size": 0.105, "tracking": 0.05},
            "subtitle": {"family": "kai", "size": 0.032, "tracking": 0.10},
            "body": {"family": "fang", "size": 0.0225, "line": 1.8},
            "caption": {"family": "fang", "size": 0.016},
            "label": {"family": "li", "size": 0.019},
            "num": {"family": "yuan", "size": 0.050},
        },
        "deco": {"grain": 0.35, "vignette": 0.16, "level": 2},
    },
    "tech": {
        "palette": {"bg": "#0E1116", "fg": "#E8EDF2", "accent": "#3C7DBF",
                    "accent2": "#5FD3C4", "muted": "#7A8794", "line": "#26303A",
                    "soft": "#161C23"},
        "type": {
            "title": {"family": "hei", "weight": "bold", "size": 0.075, "tracking": 0.0},
            "subtitle": {"family": "hei", "size": 0.028},
            "body": {"family": "hei", "weight": "light", "size": 0.021},
            "caption": {"family": "hei", "size": 0.014},
            "label": {"family": "hei", "weight": "bold", "size": 0.016},
            "num": {"family": "deng", "weight": "bold", "size": 0.048},
        },
        "deco": {"grain": 0.0, "vignette": 0.3, "level": 1},
    },
    "commerce": {
        "palette": {"bg": "#FFF7EE", "fg": "#2B2118", "accent": "#E4572E",
                    "accent2": "#F2A541", "muted": "#8C7B6B", "line": "#EFDCC8",
                    "soft": "#FCEBD8"},
        "type": {
            "title": {"family": "yuan", "weight": "bold", "size": 0.092, "tracking": 0.01},
            "subtitle": {"family": "hei", "size": 0.028},
            "body": {"family": "hei", "size": 0.022},
            "caption": {"family": "hei", "size": 0.014},
            "label": {"family": "hei", "weight": "bold", "size": 0.018},
            "num": {"family": "yuan", "weight": "bold", "size": 0.056},
        },
        "deco": {"grain": 0.0, "vignette": 0.0, "level": 1},
    },
    # 瑞士国际主义：无圆角、细线、强对比、左对齐、极简
    "swiss": {
        "palette": {"bg": "#F4F3EF", "fg": "#141414", "accent": "#E2231A",
                    "accent2": "#141414", "muted": "#8C8C88", "line": "#D8D6D0",
                    "soft": "#E9E7E1"},
        "type": {
            "title": {"family": "hei", "weight": "bold", "size": 0.082, "tracking": -0.01},
            "subtitle": {"family": "hei", "size": 0.026, "tracking": 0.0},
            "body": {"family": "hei", "size": 0.0205, "line": 1.65},
            "caption": {"family": "hei", "size": 0.014},
            "label": {"family": "hei", "weight": "bold", "size": 0.016},
            "num": {"family": "hei", "weight": "bold", "size": 0.062},
        },
        "shape": {"radius": 0.0, "line_width": 0.0016, "cap": "butt",
                  "join": "miter", "pill": False},
        "depth": {"shadow": 0.0},
        "deco": {"grain": 0.0, "vignette": 0.0, "level": 0},
        "density": {"line_height": 1.65, "block_gap": 1.0, "text_max_width": 0.58},
    },
    # 日式侘寂：大留白、极细线、低对比、纸感
    "wabi": {
        "palette": {"bg": "#EDEAE2", "fg": "#3A3A36", "accent": "#7A6A52",
                    "accent2": "#8C7B5E", "muted": "#8F8C82", "line": "#D5D1C6",
                    "soft": "#E4E0D5"},
        "type": {
            "title": {"family": "song", "size": 0.070, "tracking": 0.10},
            "subtitle": {"family": "kai", "size": 0.024, "tracking": 0.14},
            "body": {"family": "fang", "size": 0.0205, "line": 1.95},
            "caption": {"family": "fang", "size": 0.0135},
            "label": {"family": "kai", "size": 0.016},
            "num": {"family": "song", "size": 0.044},
        },
        "shape": {"radius": 0.0, "line_width": 0.0008, "cap": "butt",
                  "join": "miter", "pill": False},
        "deco": {"grain": 0.18, "vignette": 0.08, "level": 1},
        "density": {"line_height": 1.95, "block_gap": 1.25, "text_max_width": 0.52},
    },
}


def _deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = copy.deepcopy(v)
    return dst


def load_theme(data, w, h):
    """data 可以是主题名、theme dict 或 {"extends": name, ...}。返回 Theme。"""
    if isinstance(data, str):
        base = copy.deepcopy(BASE_THEME)
        name = data
        ext = THEMES.get(name)
        if ext is None:
            raise KeyError("未知主题: %r" % (name,))
        _deep_merge(base, ext)
    else:
        base = copy.deepcopy(BASE_THEME)
        ext_name = data.get("extends")
        if ext_name:
            _deep_merge(base, copy.deepcopy(THEMES.get(ext_name, {})))
        _deep_merge(base, data)
    return Theme(base, w, h)


class Theme(object):
    def __init__(self, data, w, h):
        self.data = data
        self.w = w
        self.h = h
        self.short = min(w, h)

    # ---- 颜色 ----
    def color(self, name, alpha=None):
        c = self.data["palette"].get(name)
        if c is None:
            c = self.data["palette"]["fg"]
        rgb, a = parse_color(c)
        if alpha is not None:
            a = float(alpha)
        return rgb, a

    def rgb(self, name):
        return self.color(name)[0]

    # ---- 字号 ----
    def _role(self, role):
        return self.data["type"].get(role) or self.data["type"]["body"]

    def fs(self, role, scale=1.0):
        """字号（像素）= 比例 × 短边 × scale。"""
        return self._role(role)["size"] * self.short * scale

    def font(self, role):
        r = self._role(role)
        return r.get("family", "hei"), r.get("weight", "regular")

    def tracking(self, role):
        return self._role(role).get("tracking", 0.0)

    def line(self, role):
        lh = self.data.get("density", {}).get("line_height")
        if lh is not None:
            return lh
        return self._role(role).get("line", 1.7)

    # ---- 留白 ----
    def margin(self):
        return self.data["space"]["margin"] * self.short

    def gutter(self):
        return self.data["space"]["gutter"] * self.short

    # ---- 风格参数（shape / depth / ornament / density）----
    def radius(self, default=0.012):
        r = self.data.get("shape", {}).get("radius", default)
        return float(r) * self.short

    def pill(self):
        return bool(self.data.get("shape", {}).get("pill", False))

    def line_w(self, ratio=1.0):
        """默认描边线宽（像素）。"""
        w = self.data.get("shape", {}).get("line_width", 0.0011)
        return max(0.5, float(w) * self.short * ratio)

    def cap(self):
        return self.data.get("shape", {}).get("cap", "butt")

    def join(self):
        return self.data.get("shape", {}).get("join", "miter")

    def shadow(self):
        return float(self.data.get("depth", {}).get("shadow", 0.0))

    def divider_style(self, fallback="line"):
        return self.data.get("ornament", {}).get("divider", fallback)

    def block_gap(self):
        return float(self.data.get("density", {}).get("block_gap", 1.0))

    def text_max_width(self):
        return float(self.data.get("density", {}).get("text_max_width", 0.62))


def apply_overrides(theme, overrides):
    """用点路径覆盖主题的局部值，例如 {"palette.accent": "#2F6B5E"}。

    模仿一个风格时，就不用为三个数值新建一个主题文件。
    """
    if not overrides:
        return theme
    data = copy.deepcopy(theme.data)
    for key, val in overrides.items():
        parts = key.split(".")
        node = data
        for p in parts[:-1]:
            nxt = node.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                node[p] = nxt
            node = nxt
        node[parts[-1]] = copy.deepcopy(val)
    return Theme(data, theme.w, theme.h)
