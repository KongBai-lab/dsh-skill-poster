# -*- coding: utf-8 -*-
"""fonts.py — 字体注册、字形轮廓 → Path、宽度度量、缺字检测。

为什么文字也要进 Path
---------------------
文字若各自成一套绘制逻辑，PNG/SVG/PDF 三个后端就要各写一遍。把字形轮廓
转成 Path 之后，文字与图形走同一条管线：光栅化自适应细分、PDF 里直接是
曲线、SVG 里是 path，天然一致。

字体不写死绝对路径：按「目录列表 + 文件名」查找，换设备只改 / 加目录。
"""

import os

from .path import Path

try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.basePen import BasePen
    HAS_FONTTOOLS = True
except Exception:      # pragma: no cover
    HAS_FONTTOOLS = False
    TTFont = None
    BasePen = object

FONT_DIRS = []
for _d in (os.environ.get("POSTER_FONT_DIR", ""),
           "/system/fonts", "/usr/share/fonts", "/usr/local/share/fonts",
           os.path.expanduser("~/.fonts"), os.path.expanduser("~/.local/share/fonts")):
    if _d and os.path.isdir(_d):
        FONT_DIRS.append(_d)

# 气质 -> {weight: 文件名}。换设备时只改这张表。
FAMILIES = {
    "hei":     {"regular": "FZHeiT-SC-Regular.ttf", "bold": "FZHeiT-SC-Bold.ttf",
                "light": "FZHeiT-SC-Light.ttf"},
    "kai":     {"regular": "FZKaiT-SC.ttf"},
    "fang":    {"regular": "FZFangS-SC.ttf"},
    "li":      {"regular": "FZLiS-SC.ttf"},
    "xingkai": {"regular": "FZXingK-SC.ttf"},
    "song":    {"regular": "FZXiaoBS-SC.ttf"},
    "yuan":    {"regular": "FZYuanT-SC-Regular.ttf", "light": "FZYuanT-SC-Light.ttf",
                "bold": "FZYuanT-SC-Bold.ttf"},
    "deng":    {"regular": "FZDengX-SC-Regular.ttf"},
    "miao":    {"regular": "FZMiaoW-SC.ttf"},
    "shou":    {"regular": "FZShouS-SC.ttf"},
    "shu":     {"regular": "FZShuS-SC.ttf"},
    "xinwei":  {"regular": "FZXinW-SC.ttf"},
}

FALLBACK = "hei"
_font_cache = {}
_glyph_cache = {}


class FontInfo(object):
    __slots__ = ("path", "font", "glyphset", "cmap", "upm")

    def __init__(self, path):
        font = TTFont(path, lazy=True, fontNumber=0)
        self.path = path
        self.font = font
        self.glyphset = font.getGlyphSet()
        self.cmap = font.getBestCmap() or {}
        self.upm = float(font["head"].unitsPerEm)


def find_file(family, weight="regular"):
    """按注册表 + 目录列表找字体文件；找不到返回 None。"""
    fam = FAMILIES.get(family)
    if not fam:
        return None
    name = fam.get(weight) or fam.get("regular")
    if not name:
        return None
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None


def load(family="hei", weight="regular"):
    """加载（并缓存）字体；缺字体时回落到 FALLBACK。"""
    if not HAS_FONTTOOLS:
        raise RuntimeError("fontTools 不可用，无法渲染文字")
    path = find_file(family, weight)
    if path is None and family != FALLBACK:
        path = find_file(FALLBACK, "regular")
    if path is None:
        raise RuntimeError("找不到字体 family=%r weight=%r（可设 POSTER_FONT_DIR）"
                           % (family, weight))
    key = (path, weight)
    info = _font_cache.get(key)
    if info is None:
        info = FontInfo(path)
        _font_cache[key] = info
    return info


def available_families():
    return {k: find_file(k, w) for k, d in FAMILIES.items() for w in d}


# ---------------------------------------------------------------- 字形
class _PathPen(BasePen):
    """把 TrueType/CFF 轮廓写成 Path（y 轴翻转、按 size 缩放）。"""

    def __init__(self, glyphSet, path, ox, oy, scale):
        BasePen.__init__(self, glyphSet)
        self.path = path
        self.ox = ox
        self.oy = oy
        self.s = scale

    def _pt(self, p):
        return (self.ox + p[0] * self.s, self.oy - p[1] * self.s)

    def _moveTo(self, p):
        self.path.move_to(*self._pt(p))

    def _lineTo(self, p):
        self.path.line_to(*self._pt(p))

    def _curveToOne(self, p1, p2, p3):
        a, b, c = self._pt(p1), self._pt(p2), self._pt(p3)
        self.path.cubic_to(a[0], a[1], b[0], b[1], c[0], c[1])

    def _qCurveToOne(self, p1, p2):
        a, b = self._pt(p1), self._pt(p2)
        self.path.quad_to(a[0], a[1], b[0], b[1])

    def _closePath(self):
        self.path.close()

    def _endPath(self):
        self.path.close()


def _glyph(family, weight, ch, size):
    """取出以 (0,0) 为基线原点的字形 Path（缓存）。"""
    key = (family, weight, ch, round(size, 3))
    g = _glyph_cache.get(key)
    if g is not None:
        return g
    info = load(family, weight)
    gname = info.cmap.get(ord(ch))
    if gname is None:                     # 缺字 → 用 fallback 再试一次
        if family != FALLBACK:
            return _glyph(FALLBACK, "regular", ch, size)
        return None
    p = Path()
    pen = _PathPen(info.glyphset, p, 0.0, 0.0, size / info.upm)
    try:
        info.glyphset[gname].draw(pen)
    except Exception:
        return None
    _glyph_cache[key] = p
    return p


def glyph_path(ch, size, family="hei", weight="regular", x=0.0, y=0.0):
    """单字字形 → Path（已平移到基线点 x,y）。缺字返回 None。"""
    g = _glyph(family, weight, ch, size)
    if g is None:
        return None
    return g.translated(x, y)


def advance(ch, size, family="hei", weight="regular"):
    """字符前进宽度（逻辑像素）。缺字返回半角宽。"""
    info = load(family, weight)
    gname = info.cmap.get(ord(ch))
    if gname is None:
        if family != FALLBACK:
            return advance(ch, size, FALLBACK, "regular")
        return size * 0.5
    try:
        return info.glyphset[gname].width * size / info.upm
    except Exception:
        return size * 0.5


def missing(text, family="hei", weight="regular"):
    """返回 text 中该字体缺字的字符列表（渲染前自检用）。"""
    info = load(family, weight)
    cmap = info.cmap
    return [ch for ch in text if not ch.isspace() and ord(ch) not in cmap]


def clear_cache():
    _font_cache.clear()
    _glyph_cache.clear()
