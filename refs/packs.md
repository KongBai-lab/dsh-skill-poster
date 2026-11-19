# 素材包（packs）

## 为什么要有这一层

引擎必须对题材无感知（core 里不能出现 `moss` / `茶事` / `茶`）。题材相关的图形、
色板、装饰语言全部放在 pack 里，按需加载。这样扩一个新领域只是加一个目录，
`SKILL.md` 一个字都不用改。

## 目录协议

```
packs/<name>/
  pack.json      # 元数据：provides / requires / targets
  motifs.py      # 素材函数：fn(cv, ..., color, alpha=...) → 直接画到 cv
```

`pack.json` 示例（`packs/guofeng/pack.json`）：

```json
{
  "name": "guofeng", "version": "0.1.0", "kind": "motifs",
  "provides": {"motifs": ["mountains_soft", "cloud_soft", "waves", "seal_red", "bamboo"],
                "raster_only": []},
  "requires": {"theme": "guofeng"},
  "targets": ["single-page", "cover", "long-flow"]
}
```

- `raster_only`：用了像素级优化、只能在 PNG 后端使用的函数（PDF/SVG 会被跳过或降级）。
  新写的 pack 应尽量留空——只用 `fill/stroke`，三后端就都可用。
- 颜色由调用方传入，**pack 内不写品牌色**，这样同一个 pack 能配多个主题。

## 在 layout 里使用

```json
{"type": "motifs", "overlay": true, "params": {
   "pack": "guofeng",
   "items": [
     {"fn": "mountains_soft", "args": [60, 760, 960, 300], "color": "accent2", "alpha": 0.16},
     {"fn": "cloud_soft", "args": [220, 300, 240], "color": "soft", "alpha": 0.55}
   ]}}
```

`overlay: true` 表示不参与骨架区域分配，铺满画布（背景层），要放在 blocks 列表最前面。

## 按需求打包（harvest）

每做完一个领域，把这次新画的东西回收成 pack：

1. **扫描**：本次脚本里新增的、只依赖 `geometry` + `Canvas` 的绘制函数。
2. **判定**（人来定，几十秒）：这个函数是「跨项目通用素材」还是「本次专用版式」？
   - 通用素材 → 进 `packs/<name>/motifs.py`
   - 本次专用版式 → 进 `templates/<name>/`（配方），不进 pack
3. **入库门禁**：
   - 不 import 引擎私有属性（`cv.buf` / `cv.cw` 等）
   - 三后端各出一张小图不报错
   - `pack.json` 的 `provides` 与实际函数一致
4. **登记**：`refs/canvas-api.md` 的素材索引加一行（用途 → 文件名 → 函数）。

不要全自动收割：`scene.py` 里「楼阁画法」只对某一张图成立，自动收进 pack 会污染复用性。
