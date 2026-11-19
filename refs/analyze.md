# 参考图分析（analyze）

把一张参考图变成可用的 theme 草稿：配色、明暗、版心留白、密度。

```bash
python -m engine.analyze ref.jpg --out themes/ref.json
python -m engine.analyze ref.png --json      # 只输出 JSON
```

## 输出什么

```json
{
  "extends": "guofeng",
  "palette": {"bg": "#E8E8C8", "fg": "#181808", "accent": "#284800", ...},
  "density": {"line_height": 1.78},
  "_analysis": {
    "dark": false, "margin": 0.002, "gradient": 11.7,
    "contrast_fg_bg": 8.59, "top_colors": [...]
  }
}
```

拿到后直接 `render(layout, content, theme=theme_dict)`，或存成 `themes/*.json` 复用。

## 原理：本机没有 PIL，自己解

`engine/imaging.py` 是一个极简解码器：

| 格式 | 做法 | 成本 |
|---|---|---|
| PNG | zlib 解压 + 反 filter（8bit RGB/RGBA/灰度） | 全分辨率，慢一些 |
| **JPEG** | **只解 DC 系数**，跳过 AC、不做 IDCT | 1/8 尺寸，快一个数量级 |

JPEG 的关键细节（踩过的坑）：
- DC 是差分编码，要逐块累加预测值
- DC 系数 = 8 × 均值，重建要 `pred × 量化步长 / 8 + 128`
- 色度块按采样因子扩展填格，否则颜色错乱

分析只需要缩略图，所以 DC-only 解码完全够用。

## 配色判定规则

1. 5bit/通道量化 + 频次统计
2. `bg` = 最高频色
3. `fg` = **亮度极值**（暗底取最亮、亮底取最暗）——不能按对比度选，DC 平均会让细文字变淡、对比度最高的反而落在中间调
4. `accent` = 候选里饱和度最高、且与 fg/bg 都拉得开的色
5. `accent2` = 与 accent 色相差得开的次高频色
6. `muted` / `line` / `soft` = bg→fg 的插值

## 版心与密度

- 版心留白：非背景像素的外接框，四边平均
- 密度：相邻像素平均梯度 → `line_height`（1.62 / 1.78 / 1.92 三档）

## 局限（如实说明）

- **密集插画图**（插画铺满、文字很细）DC 平均会把文字冲淡，`fg` 偏亮、对比度偏低。
  这类图建议只取 `bg` / `accent`，`fg` 手动定。
- 只支持 **8bit PNG** 与 **基线 JPEG**；渐进式 JPEG、调色板 PNG 不支持。
- 色板是「起手式」，不是终稿——模仿风格的最后一步仍然是人工微调。

## 典型工作流

```
参考图 → analyze → theme.json
      → 选最接近的骨架 + 写 layout
      → 渲染 → 与参考图并排看 → 只调 theme 数值
      → 独有装饰/插画 → 写 packs/<name>/
```
