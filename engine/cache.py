# -*- coding: utf-8 -*-
"""cache.py — 静态层位图缓存。

思路
----
场景、装饰这类「只由 layout/theme 决定、与文案无关」的内容，光栅化一次就够。
把它的位图按 hash 缓存到磁盘，改文案重出图时直接复用，只重绘文字层。

约定
----
- 只有 blocks 列表**最前面**的静态块（scene / motifs）会被缓存，保证绘制顺序不变。
- 缓存键包含：静态块配置 + 主题完整数据 + 画布尺寸 + ss。content 不参与。
- 缓存是可再生的，用 zlib level 1 压缩（快，体积略大）。
"""

import hashlib
import json
import os
import tempfile
import zlib

CACHE_DIR = os.environ.get("POSTER_CACHE") or os.path.join(tempfile.gettempdir(),
                                                           "poster-cache")

STATIC_TYPES = ("scene", "motifs")


def static_ops(ops):
    return [op for op in ops if op.get("layer") == "static"]


def dynamic_ops(ops):
    return [op for op in ops if op.get("layer") != "static"]


def static_key(layout, theme_data, preset, ss):
    payload = {
        "preset": list(preset.get("px", ())),
        "ss": ss,
        "skeleton": layout.get("skeleton"),
        "blocks": [b for b in layout.get("blocks", [])
                   if b.get("type") in STATIC_TYPES],
        "theme": theme_data,
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha1(blob).hexdigest()[:20]


def _path(key):
    return os.path.join(CACHE_DIR, key + ".z")


def load_into(key, buf):
    """把缓存解压进 buf；命中返回 True。"""
    p = _path(key)
    try:
        if not os.path.isfile(p):
            return False
        raw = zlib.decompress(open(p, "rb").read())
        if len(raw) != len(buf):
            return False
        buf[:] = raw
        return True
    except Exception:
        return False


def save(key, buf):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        data = zlib.compress(bytes(buf), 0)   # store：解压是 memcpy 级，比压缩省的时间更值
        tmp = _path(key) + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, _path(key))
        return len(data)
    except Exception:
        return 0


def clear():
    n = 0
    if os.path.isdir(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            try:
                os.remove(os.path.join(CACHE_DIR, f))
                n += 1
            except OSError:
                pass
    return n
