# -*- coding: utf-8 -*-
"""layouts.py — 骨架：把区块分配到版面区域。

区域用「占内区高度的比例」表达（0..1），因此换尺寸只换 preset，骨架不动。
区块按 type 匹配同名区域；匹配不到就顺序消费剩余区域。
"""

SKELETONS = {
    # 单页海报：标题压顶，信息逐层下收
    "single-page": [
        ("hero", 0.000, 0.215),
        ("subtitle", 0.225, 0.280),
        ("divider", 0.300, 0.315),
        ("body", 0.345, 0.520),
        ("stats", 0.560, 0.700),
        ("bullets", 0.720, 0.860),
        ("cta", 0.900, 0.980),
    ],
    # 信息长图：纵向流，区块依次等分
    "long-flow": [
        ("hero", 0.000, 0.090),
        ("section_title", 0.105, 0.140),
        ("body", 0.145, 0.260),
        ("gallery", 0.270, 0.400),
        ("divider", 0.410, 0.425),
        ("section_title", 0.440, 0.475),
        ("microchart", 0.485, 0.640),
        ("timeline", 0.660, 0.780),
        ("quote", 0.800, 0.880),
        ("footer", 0.940, 0.980),
    ],
    # 封面：大字 + 副标 + 底部信息
    "cover": [
        ("hero", 0.170, 0.400, 0.0, 0.56),
        ("subtitle", 0.420, 0.500, 0.0, 0.56),
        ("seal", 0.640, 0.760, 0.02, 0.20),
        ("shape_row", 0.120, 0.800, 0.60, 0.98),
        ("footer", 0.890, 0.950, 0.0, 1.0),
    ],
    # 横幅：左右分栏（区块用左右两列比例表达）
    "banner": [
        ("hero", 0.08, 0.58, 0.0, 0.56),
        ("subtitle", 0.60, 0.74, 0.0, 0.56),
        ("cta", 0.76, 0.92, 0.0, 0.28),
        ("shape_row", 0.10, 0.90, 0.60, 1.0),
    ],
    # 产品/工具宣传：标题 + 数字 + 图元展示 + 特性
    "promo": [
        ("hero", 0.000, 0.165),
        ("subtitle", 0.175, 0.220),
        ("divider", 0.240, 0.250),
        ("body", 0.270, 0.420),
        ("stats", 0.450, 0.540),
        ("shape_row", 0.560, 0.650),
        ("bullets", 0.670, 0.820),
        ("cta", 0.850, 0.925),
        ("footer", 0.955, 0.995),
    ],
    # 信息长图（1:2）：多章节，展示全套区块
    "showcase": [
        ("hero", 0.000, 0.095),
        ("subtitle", 0.102, 0.128),
        ("divider", 0.140, 0.146),
        ("section_title", 0.155, 0.190),
        ("body", 0.192, 0.268),
        ("shape_row", 0.275, 0.330),
        ("divider", 0.342, 0.348),
        ("section_title", 0.357, 0.392),
        ("stats", 0.395, 0.455),
        ("microchart", 0.460, 0.545),
        ("divider", 0.557, 0.563),
        ("section_title", 0.572, 0.607),
        ("timeline", 0.610, 0.690),
        ("quote", 0.698, 0.765),
        ("icon_grid", 0.770, 0.850),
        ("divider", 0.862, 0.868),
        ("cta", 0.876, 0.930),
        ("footer", 0.955, 0.990),
    ],
    # 知识卡：标题 + 要点网格 + 出处
    "card-grid": [
        ("hero", 0.000, 0.195),
        ("section_title", 0.232, 0.268),
        ("bullets", 0.282, 0.585),
        ("icon_grid", 0.605, 0.795),
        ("footer", 0.910, 0.960),
    ],
    # 对比单页：标题 + 两栏要点
    "compare": [
        ("hero", 0.000, 0.160),
        ("divider", 0.175, 0.190),
        ("bullets", 0.210, 0.620),
        ("stat_row", 0.680, 0.800),
        ("footer", 0.910, 0.960),
    ],
    # 场景长图：左主场景 + 右工序 + 图表 + 时间轴（支持左右分栏）
    "mural": [
        ("hero", 0.012, 0.086, 0.0, 0.70),
        ("subtitle", 0.094, 0.114, 0.0, 0.70),
        ("seal", 0.014, 0.090, 0.78, 1.0),
        ("scene", 0.122, 0.560, 0.0, 0.50),
        ("process_list", 0.122, 0.560, 0.52, 1.0),
        ("donut", 0.566, 0.706, 0.0, 0.50),
        ("process_list", 0.566, 0.820, 0.52, 1.0),
        ("microchart", 0.712, 0.820, 0.0, 0.50),
        ("timeline", 0.828, 0.910, 0.0, 1.0),
        ("footer", 0.950, 0.990, 0.0, 1.0),
    ],
}

# 横向分栏：左右两列的骨架（区块按其 type 落到左/右列）
TWO_COL = {
    "banner-left": 0.62,
}


def _inner(w, h, margin):
    return margin, margin, w - 2 * margin, h - 2 * margin


def _norm_region(r):
    """区域可以是 (name, y0, y1) 全宽，或 (name, y0, y1, x0, x1) 分栏。"""
    if len(r) == 3:
        return (r[0], r[1], r[2], 0.0, 1.0)
    return (r[0], r[1], r[2], r[3], r[4])


def place(w, h, margin, skeleton, blocks, gutter=0.0):
    """返回 [(block_spec, (x,y,w,h)), ...]。"""
    sk = SKELETONS.get(skeleton)
    if sk is None:
        raise KeyError("未知骨架: %r（可选：%s）" % (skeleton, ", ".join(sorted(SKELETONS))))
    regions = [_norm_region(r) for r in sk]
    x0, y0, iw, ih = _inner(w, h, margin)
    used = set()
    out = []
    for spec in blocks:
        # overlay：背景装饰类，不参与区域分配，直接铺满画布（或指定 box）
        if spec.get("overlay"):
            bx = spec.get("box", [0.0, 0.0, 1.0, 1.0])
            out.append((spec, (bx[0] * w, bx[1] * h, bx[2] * w, bx[3] * h)))
            continue
        want = spec.get("type")
        idx = None
        for i, reg in enumerate(regions):
            if i not in used and reg[0] == want:
                idx = i
                break
        if idx is None:
            for i in range(len(regions)):
                if i not in used:
                    idx = i
                    break
        if idx is None:
            # 区域用尽：在最后一个区域里均分剩余区块
            name, a, b, xr0, xr1 = regions[-1]
            slot_n = max(1, len(blocks) - len(out))
            k = len(out) - (len(blocks) - slot_n)
            bw = (xr1 - xr0) * iw
            box = (x0 + xr0 * iw, y0 + (a + (b - a) * k / slot_n) * ih,
                   bw, (b - a) / slot_n * ih)
            out.append((spec, box))
            continue
        used.add(idx)
        name, a, b, xr0, xr1 = regions[idx]
        bw = (xr1 - xr0) * iw
        box = (x0 + xr0 * iw, y0 + a * ih, bw, (b - a) * ih - gutter)
        # 宽屏下限制正文列宽：一行 80 个汉字没法读
        if spec.get("type") in ("body", "bullets", "quote", "summary") and bw > h * 1.5:
            tw = min(bw, h * 0.62)
            box = (box[0] + (bw - tw) * 0.5, box[1], tw, box[3])
        # 显式 box 覆盖（逃生舱，不可重排）
        if "box" in spec:
            bx = spec["box"]
            box = (x0 + bx[0] * iw, y0 + bx[1] * ih, bx[2] * iw, bx[3] * ih)
        out.append((spec, box))
    return out


def skeleton_names():
    return sorted(SKELETONS)
