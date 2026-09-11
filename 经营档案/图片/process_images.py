#!/usr/bin/env python3
"""批量处理网络素材图 → 1024x1024 白底成品图（商品详情/内容素材用）"""
import os
from PIL import Image, ImageEnhance

SRC = "/workspace/经营档案/图片/网络素材"
OUT = os.path.join(SRC, "成品")
SIZE = 1024
os.makedirs(OUT, exist_ok=True)

SKIP = {"成品"}
count = 0
for f in sorted(os.listdir(SRC)):
    if f in SKIP or not f.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    src = os.path.join(SRC, f)
    try:
        im = Image.open(src).convert("RGB")
    except Exception as e:
        print(f"SKIP {f}: {e}")
        continue
    # contain 模式：等比缩放到 1024 以内，白底画布填充
    im.thumbnail((SIZE, SIZE), Image.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    x = (SIZE - im.width) // 2
    y = (SIZE - im.height) // 2
    canvas.paste(im, (x, y))
    # 微提亮度让画面更干净（白底产品图风格）
    canvas = ImageEnhance.Brightness(canvas).enhance(1.04)
    name = os.path.splitext(f)[0]
    out = os.path.join(OUT, f"{name}_1024.jpg")
    canvas.save(out, "JPEG", quality=90)
    count += 1
    print(f"OK {name} {canvas.size}")

print(f"TOTAL {count}")
