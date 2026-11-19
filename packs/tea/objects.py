# -*- coding: utf-8 -*-
"""packs/tea/objects.py — 宋代茶器（半写实矢量插画）。

每件器物用六层绘制，而不是单色平涂：
    投影 → 底色 → 暗部 → 亮部 → 高光 → 结构线

目标是「产品插画级」——能认出器型与材质（紫砂壶、建盏、竹茶筅），
不是照片级。几何能力上限见 refs/styles.md 的能力边界。

约定：cy 一律是器物的**底面中心**，w 是最大宽度。
"""

import math

from engine import geometry as G
from engine.path import Path


# ---------------------------------------------------------------- 色彩工具
def _mix(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t + 0.5),
            int(a[1] + (b[1] - a[1]) * t + 0.5),
            int(a[2] + (b[2] - a[2]) * t + 0.5))


def dark(c, t=0.32):
    return _mix(c, (0, 0, 0), t)


def light(c, t=0.28):
    return _mix(c, (255, 255, 255), t)


def _shadow(cv, cx, cy, rx, ry, a=0.14):
    cv.fill(G.ellipse(cx, cy, rx, ry), (0, 0, 0), alpha=a)


def _seg(x0, y0, x1, y1):
    p = Path()
    p.move_to(x0, y0).line_to(x1, y1)
    return p


# ---------------------------------------------------------------- 执壶
def kettle(cv, cx, cy, w, color=(112, 72, 54), ink=(44, 32, 26), gloss=True):
    """执壶：梨形壶身 + 盖钮 + 曲流 + 提梁 + 圈足。"""
    h = w * 0.78
    base = color
    # 投影
    _shadow(cv, cx, cy + h * 0.015, w * 0.36, w * 0.055, 0.15)
    # 圈足
    cv.fill(G.ellipse(cx, cy, w * 0.235, w * 0.052), dark(base, 0.30))
    cv.rect(cx - w * 0.195, cy - h * 0.075, cx + w * 0.195, cy, dark(base, 0.12))
    # 壶身（梨形）：底窄、腹鼓、肩收、口小
    body = Path()
    body.move_to(cx - w * 0.215, cy)
    body.cubic_to(cx - w * 0.430, cy - h * 0.10, cx - w * 0.505, cy - h * 0.36,
                  cx - w * 0.360, cy - h * 0.575)
    body.cubic_to(cx - w * 0.285, cy - h * 0.675, cx - w * 0.200, cy - h * 0.730,
                  cx - w * 0.155, cy - h * 0.760)
    body.line_to(cx + w * 0.155, cy - h * 0.760)
    body.cubic_to(cx + w * 0.200, cy - h * 0.730, cx + w * 0.285, cy - h * 0.675,
                  cx + w * 0.360, cy - h * 0.575)
    body.cubic_to(cx + w * 0.505, cy - h * 0.36, cx + w * 0.430, cy - h * 0.10,
                  cx + w * 0.215, cy)
    body.close()
    cv.fill(body, base)
    # 暗部 / 亮部：沿轮廓内缩的「月牙」，而不是叠椭圆（椭圆会像贴片）
    moon_l = Path()
    moon_l.move_to(cx - w * 0.215, cy)
    moon_l.cubic_to(cx - w * 0.430, cy - h * 0.10, cx - w * 0.505, cy - h * 0.36,
                    cx - w * 0.360, cy - h * 0.575)
    moon_l.cubic_to(cx - w * 0.285, cy - h * 0.675, cx - w * 0.200, cy - h * 0.730,
                    cx - w * 0.155, cy - h * 0.760)
    moon_l.line_to(cx - w * 0.030, cy - h * 0.760)
    moon_l.cubic_to(cx - w * 0.075, cy - h * 0.730, cx - w * 0.160, cy - h * 0.675,
                    cx - w * 0.235, cy - h * 0.575)
    moon_l.cubic_to(cx - w * 0.380, cy - h * 0.36, cx - w * 0.305, cy - h * 0.10,
                    cx - w * 0.090, cy)
    moon_l.close()
    cv.fill(moon_l, dark(base, 0.26), alpha=0.82)
    moon_l2 = Path()
    moon_l2.move_to(cx - w * 0.150, cy - h * 0.040)
    moon_l2.cubic_to(cx - w * 0.350, cy - h * 0.14, cx - w * 0.400, cy - h * 0.38,
                     cx - w * 0.300, cy - h * 0.555)
    moon_l2.cubic_to(cx - w * 0.240, cy - h * 0.640, cx - w * 0.180, cy - h * 0.690,
                     cx - w * 0.145, cy - h * 0.720)
    moon_l2.line_to(cx - w * 0.075, cy - h * 0.720)
    moon_l2.cubic_to(cx - w * 0.115, cy - h * 0.690, cx - w * 0.180, cy - h * 0.640,
                     cx - w * 0.245, cy - h * 0.555)
    moon_l2.cubic_to(cx - w * 0.345, cy - h * 0.38, cx - w * 0.290, cy - h * 0.14,
                     cx - w * 0.115, cy - h * 0.040)
    moon_l2.close()
    cv.fill(moon_l2, dark(base, 0.14), alpha=0.55)
    moon_r = Path()
    moon_r.move_to(cx + w * 0.215, cy)
    moon_r.cubic_to(cx + w * 0.430, cy - h * 0.10, cx + w * 0.505, cy - h * 0.36,
                    cx + w * 0.360, cy - h * 0.575)
    moon_r.cubic_to(cx + w * 0.285, cy - h * 0.675, cx + w * 0.200, cy - h * 0.730,
                    cx + w * 0.155, cy - h * 0.760)
    moon_r.line_to(cx + w * 0.135, cy - h * 0.760)
    moon_r.cubic_to(cx + w * 0.180, cy - h * 0.730, cx + w * 0.265, cy - h * 0.675,
                    cx + w * 0.340, cy - h * 0.575)
    moon_r.cubic_to(cx + w * 0.480, cy - h * 0.36, cx + w * 0.405, cy - h * 0.10,
                    cx + w * 0.195, cy)
    moon_r.close()
    cv.fill(moon_r, light(base, 0.26), alpha=0.72)
    if gloss:
        # 高光：细长条 + 低透明度，避免"贴片"感
        for k, (dx, dy, rx, ry, a) in enumerate((
                (w * 0.285, h * 0.470, w * 0.020, h * 0.130, 0.30),
                (w * 0.265, h * 0.560, w * 0.012, h * 0.055, 0.42),
                (w * 0.300, h * 0.395, w * 0.014, h * 0.040, 0.20))):
            cv.fill(G.ellipse(cx + dx, cy - dy, rx, ry), (255, 255, 255), alpha=a)
    # 结构线：肩线、腹线、口沿
    cv.stroke(G.arc(cx, cy - h * 0.60, w * 0.335, 0.28, math.pi - 0.28),
              dark(base, 0.45), width=max(1.0, w * 0.006), alpha=0.55)
    cv.stroke(G.arc(cx, cy - h * 0.20, w * 0.455, 0.30, math.pi - 0.30),
              dark(base, 0.50), width=max(1.0, w * 0.005), alpha=0.35)
    # 壶嘴（曲流，右侧）
    spout = Path()
    spout.move_to(cx + w * 0.290, cy - h * 0.520)
    spout.cubic_to(cx + w * 0.455, cy - h * 0.560, cx + w * 0.585, cy - h * 0.665,
                   cx + w * 0.630, cy - h * 0.775)
    spout.cubic_to(cx + w * 0.578, cy - h * 0.705, cx + w * 0.478, cy - h * 0.600,
                   cx + w * 0.385, cy - h * 0.428)
    spout.close()
    cv.fill(spout, base)
    # 嘴的明暗：沿嘴走向的细条，而不是竖直椭圆（椭圆会跑到嘴外面）
    shade = Path()
    shade.move_to(cx + w * 0.330, cy - h * 0.455)
    shade.cubic_to(cx + w * 0.430, cy - h * 0.490, cx + w * 0.530, cy - h * 0.590,
                   cx + w * 0.585, cy - h * 0.690)
    cv.stroke(shade, dark(base, 0.26), width=max(1.0, w * 0.020), alpha=0.45, cap="round")
    hl = Path()
    hl.move_to(cx + w * 0.405, cy - h * 0.518)
    hl.cubic_to(cx + w * 0.480, cy - h * 0.552, cx + w * 0.548, cy - h * 0.625,
                cx + w * 0.600, cy - h * 0.720)
    cv.stroke(hl, (255, 255, 255), width=max(0.8, w * 0.007), alpha=0.34, cap="round")
    cv.stroke(spout, ink, width=max(1.0, w * 0.006), alpha=0.42)
    # 提梁（拱形）
    handle = Path()
    handle.move_to(cx - w * 0.255, cy - h * 0.705)
    handle.cubic_to(cx - w * 0.235, cy - h * 1.030, cx + w * 0.235, cy - h * 1.030,
                    cx + w * 0.255, cy - h * 0.705)
    cv.stroke(handle, light(base, 0.10), width=w * 0.048, cap="round")
    cv.stroke(handle, ink, width=max(1.0, w * 0.010), alpha=0.40)
    # 盖 + 钮
    cv.fill(G.ellipse(cx, cy - h * 0.765, w * 0.175, w * 0.048), light(base, 0.16))
    cv.stroke(G.ellipse(cx, cy - h * 0.765, w * 0.175, w * 0.048),
              dark(base, 0.40), width=max(1.0, w * 0.006), alpha=0.55)
    cv.fill(G.ellipse(cx, cy - h * 0.790, w * 0.065, w * 0.022), dark(base, 0.18))
    cv.fill(G.circle(cx, cy - h * 0.825, w * 0.026), ink, alpha=0.85)
    cv.fill(G.ellipse(cx - w * 0.012, cy - h * 0.832, w * 0.010, w * 0.008),
            (255, 255, 255), alpha=0.45)
    # 口沿亮线
    cv.stroke(G.arc(cx, cy - h * 0.760, w * 0.158, 0.15, math.pi - 0.15),
              (255, 255, 255), width=max(1.0, w * 0.007), alpha=0.38)


# ---------------------------------------------------------------- 建盏
def cup(cv, cx, cy, w, color=(62, 60, 56), inner=(40, 38, 36), ink=(36, 30, 27),
        hare_fur=True):
    """建盏：敞口斜腹 + 内壁 + 口沿 + 兔毫釉纹。"""
    h = w * 0.62
    _shadow(cv, cx, cy, w * 0.37, w * 0.058, 0.15)
    # 外壁
    body = Path()
    body.move_to(cx - w * 0.440, cy - h * 0.860)
    body.cubic_to(cx - w * 0.420, cy - h * 0.520, cx - w * 0.330, cy - h * 0.190,
                  cx - w * 0.205, cy)
    body.cubic_to(cx - w * 0.085, cy + h * 0.030, cx + w * 0.085, cy + h * 0.030,
                  cx + w * 0.205, cy)
    body.cubic_to(cx + w * 0.330, cy - h * 0.190, cx + w * 0.420, cy - h * 0.520,
                  cx + w * 0.440, cy - h * 0.860)
    body.close()
    cv.fill(body, color)
    # 内壁
    cv.fill(G.ellipse(cx, cy - h * 0.862, w * 0.415, w * 0.105), inner)
    # 外壁明暗：沿外壁轮廓内缩的月牙
    moon_l = Path()
    moon_l.move_to(cx - w * 0.440, cy - h * 0.860)
    moon_l.cubic_to(cx - w * 0.420, cy - h * 0.520, cx - w * 0.330, cy - h * 0.190,
                    cx - w * 0.205, cy)
    moon_l.line_to(cx - w * 0.105, cy)
    moon_l.cubic_to(cx - w * 0.212, cy - h * 0.220, cx - w * 0.278, cy - h * 0.540,
                    cx - w * 0.330, cy - h * 0.860)
    moon_l.close()
    cv.fill(moon_l, dark(color, 0.34), alpha=0.80)
    moon_r = Path()
    moon_r.move_to(cx + w * 0.440, cy - h * 0.860)
    moon_r.cubic_to(cx + w * 0.420, cy - h * 0.520, cx + w * 0.330, cy - h * 0.190,
                    cx + w * 0.205, cy)
    moon_r.line_to(cx + w * 0.135, cy)
    moon_r.cubic_to(cx + w * 0.245, cy - h * 0.220, cx + w * 0.318, cy - h * 0.540,
                    cx + w * 0.372, cy - h * 0.860)
    moon_r.close()
    cv.fill(moon_r, light(color, 0.22), alpha=0.62)
    for rx, ry, xoff, yo, a in ((w * 0.017, h * 0.140, 0.352, 0.520, 0.26),
                                 (w * 0.010, h * 0.060, 0.372, 0.610, 0.34)):
        cv.fill(G.ellipse(cx + w * xoff, cy - h * yo, rx, ry), (255, 255, 255), alpha=a)
    # 兔毫：从口沿向底放射的细纹
    if hare_fur:
        for i in range(9):
            t = (i + 1) / 10.0
            x0 = cx - w * 0.36 + w * 0.72 * t
            p = Path()
            p.move_to(x0, cy - h * 0.845)
            p.cubic_to(x0 * 0.98 + cx * 0.02, cy - h * 0.60,
                       cx + (x0 - cx) * 0.45, cy - h * 0.32,
                       cx + (x0 - cx) * 0.22, cy - h * 0.10)
            cv.stroke(p, light(color, 0.55), width=max(0.7, w * 0.004),
                      alpha=0.22)
    # 口沿亮环
    cv.stroke(G.ellipse(cx, cy - h * 0.862, w * 0.420, w * 0.108),
              light(color, 0.52), width=w * 0.016, alpha=0.85)
    cv.stroke(G.ellipse(cx, cy - h * 0.862, w * 0.400, w * 0.100),
              dark(color, 0.40), width=max(1.0, w * 0.005), alpha=0.35)
    # 圈足
    cv.fill(G.ellipse(cx, cy, w * 0.195, w * 0.045), dark(color, 0.22))
    cv.fill(G.ellipse(cx, cy - h * 0.012, w * 0.205, w * 0.040), dark(color, 0.10))


# ---------------------------------------------------------------- 茶筅
def whisk(cv, cx, cy, w, bamboo=(190, 168, 116), handle=(126, 98, 62), ink=(70, 54, 36)):
    """茶筅：竹柄 + 束箍 + 散开的细丝。"""
    h = w * 1.10
    _shadow(cv, cx, cy, w * 0.27, w * 0.050, 0.13)
    # 丝束（自柄底散开，末端收成圆弧）
    n = 34
    for i in range(n):
        t = i / (n - 1.0)
        u = (2.0 * t - 1.0)
        bx = cx + w * 0.300 * u
        end_y = cy - h * (0.058 - 0.030 * u * u)     # 中间低、两侧高的弧
        p = Path()
        p.move_to(cx, cy - h * 0.545)
        p.cubic_to(cx + (bx - cx) * 0.20, cy - h * 0.340,
                   cx + (bx - cx) * 0.62, cy - h * (0.185 + 0.02 * u * u),
                   bx, end_y)
        shade = light(bamboo, 0.14) if abs(u) < 0.5 else dark(bamboo, 0.12)
        cv.stroke(p, shade, width=max(0.8, w * 0.010), alpha=0.85)
    # 束箍
    cv.rect(cx - w * 0.105, cy - h * 0.615, cx + w * 0.105, cy - h * 0.545, handle)
    cv.rect(cx - w * 0.105, cy - h * 0.615, cx - w * 0.030, cy - h * 0.545,
            dark(handle, 0.25), alpha=0.75)
    # 柄（圆角柱 + 左右明暗）
    cv.fill(G.rrect(cx - w * 0.078, cy - h * 0.975, cx + w * 0.078, cy - h * 0.580,
                    w * 0.030), handle)
    cv.fill(G.rrect(cx - w * 0.078, cy - h * 0.975, cx - w * 0.018, cy - h * 0.580,
                    w * 0.030), dark(handle, 0.22), alpha=0.70)
    cv.fill(G.rrect(cx + w * 0.028, cy - h * 0.975, cx + w * 0.078, cy - h * 0.580,
                    w * 0.030), light(handle, 0.20), alpha=0.65)
    cv.stroke(G.rrect(cx - w * 0.078, cy - h * 0.975, cx + w * 0.078, cy - h * 0.580,
                      w * 0.030), ink, width=max(0.8, w * 0.005), alpha=0.30)
    # 柄端斜面
    cv.fill(G.polygon([(cx - w * 0.078, cy - h * 0.975),
                       (cx + w * 0.078, cy - h * 0.975),
                       (cx + w * 0.040, cy - h * 1.005),
                       (cx - w * 0.040, cy - h * 1.005)]), light(handle, 0.30), alpha=0.8)


# ---------------------------------------------------------------- 茶托 / 盏托
def saucer(cv, cx, cy, w, color=(122, 110, 92), ink=(60, 50, 40)):
    """盏托：浅盘 + 中心托圈。"""
    _shadow(cv, cx, cy, w * 0.42, w * 0.05, 0.12)
    cv.fill(G.ellipse(cx, cy, w * 0.40, w * 0.10), color)
    cv.fill(G.ellipse(cx, cy - w * 0.028, w * 0.38, w * 0.095), light(color, 0.12))
    cv.stroke(G.ellipse(cx, cy - w * 0.028, w * 0.38, w * 0.095), ink,
              width=max(0.8, w * 0.004), alpha=0.35)
    cv.fill(G.ellipse(cx, cy - w * 0.062, w * 0.155, w * 0.042), dark(color, 0.18))
    cv.fill(G.ellipse(cx, cy - w * 0.072, w * 0.140, w * 0.036), light(color, 0.22))
    cv.fill(G.ellipse(cx, cy - w * 0.060, w * 0.085, w * 0.022), (0, 0, 0), alpha=0.20)
