# -*- coding: utf-8 -*-
"""
Super Hi Vision 应用图标生成脚本（AI 辅助设计）
==============================================
用 Pillow 程序化绘制一个"高清录屏 / 摄像头"主题的现代图标：
  - 蓝紫渐变圆角方块背景
  - 白色摄像机图形（机身 + 顶部凸起 + 镜头）
  - 右下角红色录制点徽标
输出多分辨率 icon.ico（16/24/32/48/64/128/256）与预览 PNG。

用法：
  python generate_icon.py
"""
import os
from PIL import Image, ImageDraw

BASE = 1024          # 基础画布（正方形）
SS = 4               # 超采样倍数（抗锯齿）
CANVAS = BASE * SS   # 实际绘制尺寸


def lerp(a, b, t):
    return a + (b - a) * t


def diag_gradient(size, c1, c2):
    """对角线渐变：左上 c1 -> 右下 c2"""
    img = Image.new("RGBA", (size, size))
    px = img.load()
    denom = max(1.0, (2 * size - 2))
    for y in range(size):
        for x in range(size):
            t = (x + y) / denom
            c = (
                int(lerp(c1[0], c2[0], t)),
                int(lerp(c1[1], c2[1], t)),
                int(lerp(c1[2], c2[2], t)),
                255,
            )
            px[x, y] = c
    return img


def rounded_bg(size, radius, c1, c2):
    """渐变背景 + 圆角蒙版"""
    grad = diag_gradient(size, c1, c2)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=radius, fill=255
    )
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def draw_icon(d, S):
    """在尺寸 S 的画布上绘制图标（坐标基于 S=1024 缩放）"""
    k = S / 1024.0
    cx = cy = S / 2

    # ---- 背景圆角方块 ----
    bg = rounded_bg(S, int(190 * k), (63, 94, 251), (0, 200, 255))
    d._image.paste(bg, (0, 0), bg)  # 用传入 draw 关联的 image 直接贴

    # 高光（顶部圆弧，轻微提亮，增强立体感）
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse(
        [-S * 0.35, -S * 0.55, S * 1.35, S * 0.45], fill=(255, 255, 255, 46)
    )
    d._image.paste(hl, (0, 0), hl)

    # ---- 摄像机主体 ----
    body_w, body_h = 620 * k, 440 * k
    bx0, by0 = cx - body_w / 2, cy - body_h / 2
    bx1, by1 = cx + body_w / 2, cy + body_h / 2
    # 机身阴影
    d.rounded_rectangle(
        [bx0, by0 + 14 * k, bx1, by1 + 14 * k],
        radius=int(76 * k), fill=(20, 40, 90, 70),
    )
    d.rounded_rectangle(
        [bx0, by0, bx1, by1], radius=int(76 * k), fill=(255, 255, 255, 255)
    )

    # ---- 顶部凸起（取景天线）----
    nub_w, nub_h = 190 * k, 110 * k
    nx0, nx1 = cx - nub_w / 2, cx + nub_w / 2
    ny0, ny1 = by0 - nub_h + 8 * k, by0 + 30 * k
    d.rounded_rectangle(
        [nx0, ny0, nx1, ny1], radius=int(40 * k), fill=(255, 255, 255, 255)
    )

    # ---- 镜头外环 ----
    r1 = 150 * k
    d.ellipse([cx - r1, cy - r1, cx + r1, cy + r1], fill=(40, 66, 148, 255))
    # 镜头内圈（深蓝黑）
    r2 = 108 * k
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(12, 22, 58, 255))
    # 镜头底部反光弧
    d.pieslice(
        [cx - r2, cy - r2, cx + r2, cy + r2],
        start=200, end=340, fill=(80, 130, 220, 110),
    )
    # 镜头左上高光点
    hr = 34 * k
    hx, hy = cx - 46 * k, cy - 52 * k
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=(190, 220, 255, 130))

    # ---- 右下角红色录制点 ----
    dot_r = 66 * k
    dx, dy = bx1 - 62 * k, by1 - 62 * k
    d.ellipse(
        [dx - dot_r - 16 * k, dy - dot_r - 16 * k,
         dx + dot_r + 16 * k, dy + dot_r + 16 * k],
        fill=(255, 255, 255, 255),
    )
    d.ellipse([dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r],
              fill=(255, 59, 48, 255))


def build(sizes=(16, 24, 32, 48, 64, 128, 256)):
    # 超采样绘制
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    cd = ImageDraw.Draw(canvas)
    draw_icon(cd, CANVAS)
    canvas = canvas.resize((BASE, BASE), Image.LANCZOS)

    # 预览大图
    canvas.save("icon_preview.png")

    # 生成多尺寸 ico
    canvas.save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
    )
    print("已生成 icon.ico:", [f"{s}x{s}" for s in sizes])
    print("已生成 icon_preview.png")


if __name__ == "__main__":
    build()
