"""Render the app icon as PNG, ICO and ICNS. Run after changing the design (needs Pillow)."""

import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024
U = 4  # supersampling factor
FULL = SIZE * U


def layer():
    return Image.new("RGBA", (FULL, FULL), (0, 0, 0, 0))


def mask_of(draw_fn):
    m = Image.new("L", (FULL, FULL), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def fill(mask, top, bottom, box=None):
    """Vertical gray gradient clipped to `mask`, spanning `box` (y0, y1)."""
    y0, y1 = box or (0, FULL)
    grad = Image.new("L", (1, FULL))
    for y in range(FULL):
        t = min(1.0, max(0.0, (y - y0) / max(1, y1 - y0)))
        grad.putpixel((0, y), int(top + (bottom - top) * t))
    grad = grad.resize((FULL, FULL))
    out = layer()
    out.paste(Image.merge("RGBA", (grad, grad, grad, mask)), (0, 0))
    return out


def shadow(mask, offset, blur, opacity):
    m = mask.point(lambda v: int(v * opacity))
    m = ImageChops.offset(m, 0, offset).filter(ImageFilter.GaussianBlur(blur))
    out = layer()
    out.putalpha(m)
    return out


def page_shape(x, y, w, h, fold, r):
    def draw(d):
        d.rounded_rectangle((x, y, x + w, y + h), radius=r, fill=255)
        d.polygon([(x + w - fold, y - 2), (x + w + 2, y - 2), (x + w + 2, y + fold)], fill=0)
    return draw


def arrowhead(d, cx, cy, radius, angle_deg, size, color):
    a = math.radians(angle_deg)
    px, py = cx + radius * math.cos(a), cy + radius * math.sin(a)
    dx, dy = -math.sin(a), math.cos(a)  # clockwise tangent (y axis points down)
    nx, ny = math.cos(a), math.sin(a)
    tip = (px + dx * size * 0.75, py + dy * size * 0.75)
    base = (px - dx * size * 0.25, py - dy * size * 0.25)
    left = (base[0] + nx * size * 0.62, base[1] + ny * size * 0.62)
    right = (base[0] - nx * size * 0.62, base[1] - ny * size * 0.62)
    d.polygon([tip, left, right], fill=color)


def render() -> Image.Image:
    canvas = layer()

    # Tile on the macOS icon grid (824 of 1024).
    inset, radius = 100 * U, 186 * U
    tile_box = (inset, inset, FULL - inset, FULL - inset)
    tile = mask_of(lambda d: d.rounded_rectangle(tile_box, radius=radius, fill=255))
    canvas.alpha_composite(shadow(tile, 14 * U, 22 * U, 0.55))
    canvas.alpha_composite(fill(tile, 34, 4, (inset, FULL - inset)))

    # Soft glow from the top of the tile.
    glow = mask_of(lambda d: d.ellipse((FULL * 0.12, -FULL * 0.28, FULL * 0.88, FULL * 0.42), fill=70))
    glow = ImageChops.multiply(glow.filter(ImageFilter.GaussianBlur(90 * U)), tile)
    g = layer()
    g.paste(Image.new("RGBA", (FULL, FULL), (255, 255, 255, 255)), (0, 0), glow)
    canvas.alpha_composite(g)

    # Hairline rim, brighter along the top edge.
    rim = mask_of(lambda d: d.rounded_rectangle(tile_box, radius=radius, outline=255, width=3 * U))
    rim_fade = fill(rim, 150, 40, (inset, FULL - inset))
    rim_fade.putalpha(ImageChops.multiply(rim, rim_fade.getchannel("R")))
    canvas.alpha_composite(rim_fade)

    # Back page: outline only.
    bx, by, bw, bh, fold, pr = 282 * U, 236 * U, 340 * U, 440 * U, 96 * U, 26 * U
    back = page_shape(bx, by, bw, bh, fold, pr)
    back_fill = mask_of(back)
    inner = mask_of(page_shape(bx + 7 * U, by + 7 * U, bw - 14 * U, bh - 14 * U, fold - 3 * U, pr - 7 * U))
    outline = ImageChops.subtract(back_fill, inner)
    ol = layer()
    ol.paste(Image.new("RGBA", (FULL, FULL), (150, 150, 150, 255)), (0, 0), outline)
    canvas.alpha_composite(ol)

    # Front page: solid white with a fold.
    fx, fy, fw, fh = 392 * U, 330 * U, 350 * U, 456 * U
    front = mask_of(page_shape(fx, fy, fw, fh, fold, pr))
    canvas.alpha_composite(shadow(front, 18 * U, 26 * U, 0.7))
    canvas.alpha_composite(fill(front, 255, 226, (fy, fy + fh)))
    corner = mask_of(lambda d: d.polygon([(fx + fw - fold, fy), (fx + fw - fold, fy + fold - 10 * U),
                                          (fx + fw, fy + fold)], fill=255))
    corner_shadow = shadow(corner, 6 * U, 10 * U, 0.35)
    corner_shadow.putalpha(ImageChops.multiply(corner_shadow.getchannel("A"), front))
    canvas.alpha_composite(corner_shadow)
    canvas.alpha_composite(fill(corner, 206, 168, (fy, fy + fold)))

    d = ImageDraw.Draw(canvas)
    for i, width in enumerate((196, 236, 168, 214, 120)):
        y = (448 + i * 58) * U
        d.rounded_rectangle((fx + 58 * U, y, fx + (58 + width) * U, y + 20 * U), radius=10 * U,
                            fill=(28, 28, 28, 255) if i else (10, 10, 10, 255))

    # Convert badge overlapping the page corner.
    cx, cy, br = 700 * U, 704 * U, 132 * U
    badge = mask_of(lambda dd: dd.ellipse((cx - br, cy - br, cx + br, cy + br), fill=255))
    canvas.alpha_composite(shadow(badge, 14 * U, 22 * U, 0.75))
    canvas.alpha_composite(fill(badge, 40, 6, (cy - br, cy + br)))
    d = ImageDraw.Draw(canvas)
    d.ellipse((cx - br, cy - br, cx + br, cy + br), outline=(245, 245, 245, 255), width=9 * U)
    ar, stroke = 70 * U, 17 * U
    white = (250, 250, 250, 255)
    d.arc((cx - ar, cy - ar, cx + ar, cy + ar), 196, 318, fill=white, width=stroke)
    d.arc((cx - ar, cy - ar, cx + ar, cy + ar), 16, 138, fill=white, width=stroke)
    arrowhead(d, cx, cy, ar - stroke / 2, 318, 46 * U, white)
    arrowhead(d, cx, cy, ar - stroke / 2, 138, 46 * U, white)

    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def main():
    icon = render()
    assets = ROOT / "src" / "document_converter" / "assets"
    packaging = ROOT / "packaging"
    assets.mkdir(parents=True, exist_ok=True)
    packaging.mkdir(parents=True, exist_ok=True)
    icon.resize((512, 512), Image.LANCZOS).save(assets / "icon.png")
    icon.save(packaging / "icon.png")
    icon.save(packaging / "icon.ico",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon.save(packaging / "icon.icns")
    print("Icons written to", assets, "and", packaging)


if __name__ == "__main__":
    main()
