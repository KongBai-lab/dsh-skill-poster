# API 速查

## Canvas（显示列表，后端无关）

```python
cv = Canvas(w, h, ss=3, bg="#F7F5F0")
cv.fill(path, color, alpha=None, rule="evenodd|nonzero", bleed=False)
cv.stroke(path, color, width=1.0, cap="butt|round|square", join="miter|round|bevel", alpha=None)
cv.rect(x0, y0, x1, y1, color)      # 其余便捷方法：circle / ellipse / line / polyline / rrect
cv.to_png(path, exact=False, dpi=96)   # → backends/raster（dpi 已随 ss 自动放大）

# 贴图（背景素材）：src 可以是路径，(w,h,rgb) 元组，或对话里发的图片附件
cv.image("photo.png", 0, 0, 1920, 1080, alpha=1.0)
cv.image("photo.jpg", 96, 700, 480, 270)     # 局部贴图
cv.use_layer("static"|"dynamic")    # 图层标签（为静态层缓存预留）
cv.bbox() / cv.op_count() / cv.path_points()

# 裁剪：块内所有绘制都被限制在 path 内
with cv.clip(shape_path):
    cv.fill(highlight_ellipse, (255, 255, 255), alpha=0.5)   # 高光自动贴合形状
    cv.rect(...)                                              # 渐变条带也被裁切
```

**裁剪是插画质量的关键**：球体渐变、器身高光、盏内暗部、场景雾带都靠它。
实现方式是「临时副本上绘制 + 掩码合成」，所以块内的 alpha 叠加仍然正确。


颜色接受 `"#RRGGBB"`、`(r,g,b)`、`(r,g,b,a)`；`theme.color(name)` 返回 `(rgb, alpha)` 可直接传入。

## Path

```python
p = Path()
p.move_to(x, y).line_to(x, y).cubic_to(c1x,c1y, c2x,c2y, x,y).quad_to(cx,cy, x,y).close()
Path.circle(cx, cy, r); Path.ellipse(...); Path.arc(...); Path.rrect(...)
Path.from_polygon(pts, closed=True)
p.flatten(tol)        # 自适应细分 → 多边形轮廓（tol = 0.5/ss）
p.bbox(); p.translated(dx,dy); p.scaled(...); p.rotated(ang,cx,cy); p.extend(q)
```

细分规则：控制点到弦距离 ≤ tol 即停。**不要自己算坐标点列来逼近曲线。**

## geometry（24 个参数化图元，全部返回 Path）

| 类别 | 函数 |
|---|---|
| 基础 | `circle ellipse arc ring pie donut_sector rrect capsule polygon regular_polygon star` |
| 自然 | `leaf petal flower drop cloud wave mountains heart sparkle` |
| 装饰 | `seal_frame corner_ornament divider_wave` |

关键参数：`leaf(cx,cy,length,width,angle,bend)`、`petal(cx,cy,length,width,angle)`、
`cloud(cx,cy,w,h,bumps)`、`wave(x0,y0,x1,y1,amp,periods,taper)`、
`mountains(x0,y0,x1,y1,peaks,seed,jitter)`、`star(cx,cy,r_out,r_in,points,round_tips)`。

> `flower()` 是多子路径叠加，必须 `rule="nonzero"`。

## typography

```python
measure(s, size, family, weight, tracking=0, squeeze=False) -> 宽度
wrap(text, max_w, size, family, ..., squeeze=True, indent=0) -> [行]
text_path(s, x, y, size, family, ..., align="left|center|right", tracking, baseline=True) -> Path
para_path(text, x, y_top, max_w, size, line_height, ..., first_indent) -> Path
para_lines(...) -> [行]
vtext_path(s, x, y_top, size, family, ..., tracking) -> Path   # 竖排，y 向下
spaced_path(s, x, y, size, gap, family, ...) -> Path          # 字距
text_block_size(...) -> (w, h)
```

- `align="center"` 时传入的是**中心 x**；`baseline=False` 时 y 是行顶边。
- 避头尾常量：`PUNCT_HEAD`（行首禁则）、`PUNCT_TAIL`（行尾禁则）、`PUNCT_SQUEEZE`（可挤压）。

## fonts

```python
find_file(family, weight) -> 路径或 None
load(family, weight) -> FontInfo(path, font, glyphset, cmap, upm)
glyph_path(ch, size, family, weight, x, y) -> Path 或 None
advance(ch, size, family, weight) -> 宽度
missing(text, family, weight) -> [缺字]
```

家族：`hei kai fang li xingkai song yuan deng miao shou shu xinwei`（见 `FAMILIES`）。
字体目录：`POSTER_FONT_DIR` → `/system/fonts` → 各平台常见目录。

## 扩展方式

- 新形状 → 在 `geometry.py` 加一个返回 `Path` 的函数（用 cubic，不要手写折线）。
- 新区块 → `@block("name")` 装饰函数，签名 `fn(cv, box, params, th, ctx)`。
- 新骨架 → 在 `layouts.SKELETONS` 加一组 `(name, start_ratio, end_ratio)`。
- 新皮肤 → 在 `theme.THEMES` 加一个 dict（可 `extends` 已有主题）。
- 新素材 → 新建 `packs/<name>/`，写 `pack.json` 与 `motifs.py`（只依赖 geometry + Canvas）。

## 图片素材（cv.image）

| 格式 | PNG 输出 | PDF 输出 | 说明 |
|---|---|---|---|
| PNG | 全质量 | Flate 嵌入（解压为 RGB） | 解码走 `imaging.load_png` |
| JPEG | **DC 解码，8× 缩略（像素化）** | **DCT 直嵌，原图质量** | PNG 输出为了快只解 DC 系数 |

- 贴图会按目标矩形最近邻缩放；大面积背景图约 2–3s（`ss=3`）
- 想保证 PNG 输出清晰：**优先用 PNG 素材**；JPEG 素材的高质量出口是 PDF
- SVG 输出把原文件 base64 内嵌，不重新编码
- 素材文件没有扩展名也能识别（按文件签名判断）
