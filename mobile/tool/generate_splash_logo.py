"""Generate a transparent-background lightning bolt for the native splash.

The native splash tool centres this on the brand navy. Keeping the logo on
transparent (no background) lets the platform splash use the brand colour
as the surrounding fill, which avoids the "rectangle within rectangle"
look you get when a coloured square sits on a coloured screen.

Run:
    python tool/generate_splash_logo.py
Outputs to: assets/icon/splash_logo.png
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter


OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icon")
OUT_PATH = os.path.join(OUT_DIR, "splash_logo.png")

SIZE = 1024                      # bigger source = bigger rendered splash logo
ACCENT = (79, 141, 255)          # ShoeboxColors.accent


def draw_bolt(canvas: Image.Image, fill: tuple) -> None:
    W, H = canvas.size
    cx, cy = W // 2, H // 2
    rel = [
        (-0.18,  -0.42),
        ( 0.12,  -0.42),
        (-0.02,  -0.05),
        ( 0.18,  -0.05),
        (-0.12,   0.42),
        ( 0.02,   0.05),
        (-0.18,   0.05),
    ]
    scale = W * 0.85
    pts = [(cx + rx * scale, cy + ry * scale) for rx, ry in rel]

    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.polygon(pts, fill=(*ACCENT, 140))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=W * 0.04))
    canvas.alpha_composite(glow_layer)

    bolt = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bolt)
    bd.polygon(pts, fill=fill + (255,))
    canvas.alpha_composite(bolt)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw_bolt(img, ACCENT)
    img.save(OUT_PATH, "PNG")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
