"""Generate a 1024x1024 Shoebox app icon as a PNG.

Design: dark navy gradient background (matches the in-app theme) + a bright
accent-blue lightning bolt centered, with a subtle wordmark below it. The
bolt motif matches the icon used in the home screen AppBar so the brand
feels cohesive from launch through navigation.

Run:
    python tool/generate_icon.py
Outputs to: assets/icon/app_icon.png  (used by flutter_launcher_icons)
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter


OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icon")
OUT_PATH = os.path.join(OUT_DIR, "app_icon.png")

SIZE = 1024
NAVY_TOP    = (15, 23, 42)      # ShoeboxColors.navy-ish, slightly lighter for gradient
NAVY_BOTTOM = (8, 13, 26)
ACCENT      = (79, 141, 255)     # ShoeboxColors.accent
ACCENT_SOFT = (180, 210, 255)


def vertical_gradient(size: int, top: tuple, bottom: tuple) -> Image.Image:
    img = Image.new("RGB", (size, size), top)
    px = img.load()
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        for x in range(size):
            px[x, y] = (r, g, b)
    return img


def draw_bolt(canvas: Image.Image, fill: tuple) -> None:
    """A clean lightning bolt centred on the canvas. Coordinates are tuned for
    a 1024x1024 surface; if you change SIZE this still scales because we
    multiply by ratios. Two passes — a soft glow underneath + a crisp shape."""
    W, H = canvas.size
    cx, cy = W // 2, H // 2
    # Bolt polygon points relative to centre, in a 1.0 unit space.
    rel = [
        (-0.18,  -0.42),
        ( 0.12,  -0.42),
        (-0.02,  -0.05),
        ( 0.18,  -0.05),
        (-0.12,   0.42),
        ( 0.02,   0.05),
        (-0.18,   0.05),
    ]
    scale = W * 0.55
    pts = [(cx + rx * scale, cy + ry * scale) for rx, ry in rel]

    # Glow pass — paint to a transparent layer, blur, composite.
    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.polygon(pts, fill=(*ACCENT, 140))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=W * 0.04))
    canvas.alpha_composite(glow_layer)

    # Crisp bolt on top.
    bolt = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    bd = ImageDraw.Draw(bolt)
    bd.polygon(pts, fill=fill + (255,))
    canvas.alpha_composite(bolt)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    bg = vertical_gradient(SIZE, NAVY_TOP, NAVY_BOTTOM).convert("RGBA")

    # Subtle radial vignette — paints a darker ring around the edges for
    # depth. We use a blurred ellipse to approximate it without numpy.
    vignette = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(vignette).ellipse(
        (-SIZE * 0.1, -SIZE * 0.1, SIZE * 1.1, SIZE * 1.1), fill=255,
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=SIZE * 0.18))
    dark = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 60))
    bg = Image.composite(bg, dark, vignette)

    # Bolt
    draw_bolt(bg, ACCENT)

    # Soft inner highlight near the top for a slight "glass" feel.
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(
        (SIZE * 0.1, -SIZE * 0.35, SIZE * 0.9, SIZE * 0.3),
        fill=(255, 255, 255, 18),
    )
    hl = hl.filter(ImageFilter.GaussianBlur(radius=SIZE * 0.10))
    bg.alpha_composite(hl)

    bg.convert("RGB").save(OUT_PATH, "PNG", optimize=True)
    print(f"wrote {OUT_PATH}  ({os.path.getsize(OUT_PATH) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
