---
name: poster
description: 在本地纯 Python 绘制宣传图与海报：单页海报、信息长图、封面、横幅、知识卡、对比单页、证书、易拉宝。声明式「骨架 + 区块 + 主题」三件套，或直接调用 Canvas 自由绘制；输出 PNG / SVG / PDF，零第三方依赖（仅 fontTools）本地光栅化。
whenToUse: 用户要做海报、宣传图、长图、封面、横幅、知识卡、活动图、易拉宝、证书、邀请函；或要求"仿这张图做一张"、把一段文案排成一张图、需要印刷稿 PDF；或需要比数据图更复杂的版式设计时。
slug: dsh-skill-poster
displayName: Poster — 宣传图与海报
version: 1.0.0
summary: 骨架 × 区块 × 主题的可插拔海报引擎，Path 图元 + 字距/竖排/避头尾，PNG/SVG/PDF 三出口。
license: MIT
tags: [dsh, skill, poster, layout, typography, png, pdf, python, fonttools]
---

# poster：宣传图 / 海报

## 边界（先看这一节）

| 需求 | 用什么 |
|---|---|
| 单张数据图（柱线饼/流程/时间轴） | `diagram`，**不要用本 skill 画** |
| 单幅视觉图：海报/长图/封面/横幅/卡片/展板 | **本 skill** |
| 多页演示文稿 | `make-ppt` |
| 带公式的文档 | `md2docx` |

本机能力边界：没有扩散模型权重、没有本地推理算力，**不能生成照片与写实插画**。
本 skill 只能做几何/矢量风格（可做到精细，但不是工笔写实）。

## 铁律

1. **不要手写点列**。形状一律用 `engine.geometry` 的参数化图元（circle/leaf/cloud/wave/heart…），
   它们内部自适应细分；手写坐标是「一眼看出多边形凑数」的根源。
2. **文字也走 Path**。不要另写一套文字绘制；`engine.typography` 负责断行/竖排/避首尾。
3. **改完代码先清模块缓存**。`python` 工具的解释器跨请求共享：
   `for m in [k for k in sys.modules if k.startswith("engine")]: del sys.modules[m]`
4. **不要靠看图验收 1–2px 级别的缺陷**。`read_image` 预览会缩放，产生假缺口；
   用 `engine.check.check_canvas()` 的断言，或做像素级统计。
5. **性能：大面积像素操作交给 C 层，先剖析再改。**
   - 半透明叠加若是单色（黑/白/灰），三通道同映射 → 256 项 LUT + `bytes.translate`。
     实测暗角逐像素混合占 71%（6.6s），改后 0.05s，且数学上完全等价。
   - 整行平涂用切片赋值，不要逐像素写 3 字节。
   - zlib 用 level 6，不是 9（快一倍，文件只大 15%）。
   - 动手前先 `cProfile`：本项目最大的坑是 alpha 混合，不是几何算法。

## 三种接入模式

| 模式 | 输入 | 适用 |
|---|---|---|
| **A 套模板** | 复制 `templates/*/`，只改 `content.json` | 常规宣传图（80% 场景） |
| **B 组装** | 写 `layout.json`（骨架 + 区块列表 + 参数） | 结构要变、元素标准 |
| **C 自绘** | `engine.canvas.Canvas` 直接写图元 | 仿参考图、版式独一无二 |

## 目录

```
engine/
  canvas.py       显示列表（Canvas.fill/stroke/clip，图层 static/dynamic）
  path.py         Path（M/L/C/Q/Z）+ 自适应细分
  geometry.py     23 个参数化图元
  fonts.py        字体注册表 + 字形→Path + 缺字检测
  typography.py   断行/避头尾/标点挤压/竖排/字距
  theme.py        主题（6 套皮肤 + 风格参数）+ 9 个画布预设
  blocks.py       21 个声明式区块
  layouts.py      9 个骨架（含左右分栏）
  render.py       组装 + CLI
  check.py        越界/对比度/字号/色数/缺字/slot 断言
  cache.py        静态层位图缓存（默认关闭，实测见 refs/workflow.md）
  backends/       raster.py（PNG）、pdf.py（矢量 PDF）、svg.py
packs/            素材包（guofeng 国风、tea 茶器），按需加载
templates/        成品配方（content + layout）
```

## 运行前提

- **装依赖**：`pip install -r requirements.txt`（只有一个依赖：fontTools）。
- **字体**：本仓库不附带字体文件，引擎读取系统已安装字体——默认扫描
  `/system/fonts`、`/usr/share/fonts`、`~/.fonts` 等常见目录；字体装在别处时用环境变量
  `POSTER_FONT_DIR` 指到字体目录。
- **无需联网、无需 Office/GUI**：光栅化、PDF、SVG 三个后端都是纯 Python 实现。

## 快速开始

```bash
# 出图（默认 preview 档）
python -m engine.render templates/minimal-poster/layout.json -o out.png

# 印刷稿：A4 矢量 PDF（文字不可选）
python -m engine.render templates/minimal-poster/layout.json -o out.pdf \
       --preset a4-portrait --for print

# 换主题 / 换尺寸
python -m engine.render ... --theme guofeng --preset xhs-3x4

# 列出可用预设 / 骨架 / 区块
python -m engine.render --list
```

Python 里调用：

```python
from engine.render import render, load_json
render(layout, content, theme="minimal", preset_name="xhs-3x4",
       out="out.png", for_="publish")
```

## 对外只有四个旋钮

| 旋钮 | 取值 | 说明 |
|---|---|---|
| `preset` | xhs-3x4 / sq-1x1 / story-9x16 / wechat-cover / video-16x9 / info-long / a4-portrait / a3-portrait / rollup-85x200 | 尺寸与安全区 |
| `--for` | draft / preview / publish / print | 清晰度与输出（见 refs/workflow.md） |
| `--format` | png / pdf / svg | 默认：print→pdf，其余 png |
| `--deco` | 0/1/2（theme 内） | 装饰密度；只影响观感与文件大小，几乎不影响速度 |

**没有 `quality` 参数**：质量下限由图元自适应细分 + 亚像素覆盖率 + `check.py` 保证。

## 限制（如实告知）

- 不做照片、写实插画、3D；半写实器物可以（每件约 100–200 行六层绘制），人物不建议。
- PDF 首版**文字路径化**：视觉正确但不可选、不可搜。
- PDF 仅 RGB，不支持 CMYK/专色；印前需自行转换。
- 大字标题/细线在 ss=2 下建议改用 `--for publish`（ss=3）。
- 生僻字可能缺字形；`check.py` 会报缺字，字体可用 `POSTER_FONT_DIR` 指定。
- **首次渲染另加约 6s**（解析字体文件），同进程后续渲染复用；迭代时应连续调用而不是频繁重启。
- 热态耗时参考：preview ≈1.6s、publish ≈2.7s（1080×1440 的 3240×4320 输出）。
- 竖排标点只平移不旋转，数字/英文竖排不旋转；多端字体适配未做。

## 注意事项（踩过的坑）

### 性能
- **半透明叠加**：任意颜色都走逐通道 LUT（实测 13s→2.5s）。新增「大面积逐像素」功能前，先想能不能查表。
- **大 PNG 解码**：5760×3240 全解码 10s+。背景素材建议 ≤1500px，或用 JPEG（只解 DC 系数，快一个数量级）。
- **print 档强制 ss=1**：A4@ss3 实测 52s。
- 静态层缓存实测不划算（40MB 位图 IO ≈ 渲染成本），`--cache` 默认关闭。

### 字体
- 所有 FZ 字体都缺 `∂ ħ ∇` 与上标数字 `⁻³⁵`；**缺字静默跳过，不报错**（公式会变成 `ψ/ t = i Hψ`）。
- 写公式/单位前先 `fonts.missing(text, family)`；实测可用符号只有 `ψ ∫ ≈ ∝ λ ∞ → ·`。

### 版式
- `hero` 多行需要区域高度 ≥ 行数 × 行高，否则压到下一块。
- `banner` / `card-grid` / `cover` 的比例是经验值，换内容可能要微调。
- 宽屏里的 CTA 必须设 `max_width`，否则占满整行像进度条。
- 背景图**自带的文字**会和前景打架——选无文字素材（照片/纹理/插画）。

### 图片素材
- JPEG 的 PNG 输出是 DC 版（8× 缩略、像素化）；要清晰请出 PDF 或换 PNG 素材。
- PDF 直嵌 JPEG 零重编码，质量最好。
- 素材没有扩展名也能识别（按文件签名判断）。

### 工程习惯
- `python` 工具的模块缓存**跨请求共享**，每次测试开头清 `sys.modules` 里的 `engine*` / `packs*`。
- 开发目录与安装目录分离，改完要 `copytree` 同步（忽略 `__pycache__`）。
- `scene` 的 `objects_pack` 导入失败会**静默回退**到简笔版，不报错。

## 细节文档（按需读）

| 文件 | 内容 |
|---|---|
| `refs/workflow.md` | 参考图解剖 → 灰模 → 上色 → 上字 → 验收；清晰度档位与性能实测 |
| `refs/canvas-api.md` | Canvas / Path / geometry 速查，缺失能力的补法 |
| `refs/presets.md` | 全部尺寸、安全区、印刷出血与 pt 换算 |
| `refs/packs.md` | 素材包协议与「按需求打包」的收割流程 |
| `refs/styles.md` | **风格参数、6 套内置风格指纹、theme_overrides、模仿一套风格的流程** |
| `refs/analyze.md` | **参考图分析：取色/明暗/版心/密度 → theme 草稿** |
