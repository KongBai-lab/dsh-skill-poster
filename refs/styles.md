# 风格：参数、覆盖与模仿流程

## 一套风格 = 五组数据

| 组 | 字段 | 作用 |
|---|---|---|
| `palette` | bg / fg / accent / accent2 / muted / line / soft | 配色 |
| `type` | title / subtitle / body / caption / label / num（family, weight, size, tracking, line） | 字体气质与层级 |
| `shape` | radius / line_width / cap / join / pill | 形状语言（最影响“像不像”） |
| `depth` | shadow / shadow_dy | 层次（0 = 完全扁平） |
| `ornament` | divider / corner / border | 装饰语言（line / wave / thick） |
| `density` | line_height / block_gap / text_max_width | 疏密 |
| `deco` | grain / vignette / pattern | 质感 |

字号与圆角都存**相对短边的比例**，所以换尺寸时层级自动等比。

## 内置风格指纹

| 风格 | 特征 | radius | line_w | 字体 | 密度 |
|---|---|---|---|---|---|
| `minimal` | 中性、克制、纸白 | 0.012 | 0.0011 | 小标宋 + 仿宋 | 1.75 |
| `guofeng` | 宣纸、朱砂、行楷、颗粒 | 0.012 | 0.0011 | 行楷 + 楷 + 隶 | 1.8 |
| `tech` | 暗色、冷蓝、无衬线、暗角 | 0.012 | 0.0011 | 黑体 + 等线 | 1.7 |
| `commerce` | 暖橘、圆体、圆角胶囊 | 0.012（pill） | 0.0011 | 圆体 + 黑体 | 1.65 |
| **`swiss`** | 国际主义：**无圆角**、粗黑体、红、紧字距 | **0** | 0.0016 | 黑体 Bold | 1.65 |
| **`wabi`** | 侘寂：**极细线**、大留白、低对比、纸感 | **0** | 0.0008 | 小标宋 + 楷 | 1.95 |

## theme_overrides：不改主题文件也能微调

```json
{
  "theme": "swiss",
  "theme_overrides": {
    "palette.accent": "#1B5E4B",
    "shape.radius": 0.02,
    "shape.pill": true,
    "density.line_height": 1.85
  }
}
```

支持任意点路径。模仿一个风格时先套最接近的内置主题，再用它微调 3–5 个值。

## 模仿一套风格的流程

1. **匹配**：看参考图，从上面的指纹表选最接近的风格（先定 radius / 字体 / 明暗）。
2. **取色**：取 5–7 个十六进制值，填进 `palette`（bg/fg/accent/muted/line）。
3. **写主题**：`{"extends": "swiss", "palette": {...}, "shape": {...}}` 存成 `themes/<name>.json`。
4. **套骨架**：选一个最接近的骨架，写 `layout.json`；结构差异大时用 `"box"` 逃生舱。
5. **并排对比**：渲染后与参考图并排看，**只调 theme 数值**（不要改区块代码）。
6. **补装饰**：如果参考图有独特纹样/插画，写 `packs/<name>/motifs.py`。

## 风格调配速查

| 想要 | 调什么 |
|---|---|
| 更柔和 | `shape.radius` ↑（0.02–0.05）、`shape.pill: true`、`join: round` |
| 更硬朗 | `shape.radius: 0`、`line_width` ↑、`cap: butt`、`join: miter` |
| 更精致 | `line_width` ↓（0.0008）、`type.caption.size` ↓、`deco.grain` ↑ |
| 更现代 | 黑体、`tracking` 负值、无纹理、高对比 |
| 更复古 | 楷/仿宋、`deco.grain` ↑、低饱和 accent、圆角小 |
| 更贵气 | 行楷/隶、大字号、`density.line_height` ↑、留白多 |
| 更拥挤 | `density.block_gap` ↓、字号层级压缩、`text_max_width` ↑ |

## 已知边界

- `depth.shadow` 字段已定义，P0 尚未在所有区块生效（目前只影响预留接口）。
- `ornament.corner` / `border` 同样只占位，需要配 `packs` 里的花边素材。
- 独特的插画/器物不在 theme 能力内——那属于 pack。
