#!/usr/bin/env python3
"""Logo de Martinet : UNE source SVG (logo.svg), tout le reste en est rendu.

    QT_QPA_PLATFORM=offscreen python make_logo.py      (PyQt6 + Pillow)

Un martinet blanc, ailes en faux, dans la flèche circulaire d'une mise à
jour, sur fond bleu ciel. Sorties : logo.svg (la source),
logo_{16,32,64,128,256,512}.png, logo.png (= 256) et logo.ico (installeur
Windows, multi-tailles).
"""
import math
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
CIEL_CLAIR, CIEL, CIEL_NUIT, BLANC = "#3A93DD", "#1C6DB4", "#123F6B", "#FFFFFF"


def _arc(cx, cy, r, debut, fin):
    def pt(a):
        return cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
    (x1, y1), (x2, y2) = pt(debut), pt(fin)
    grand = 1 if (fin - debut) % 360 > 180 else 0
    return f"M{x1:.1f},{y1:.1f} A{r},{r} 0 {grand} 1 {x2:.1f},{y2:.1f}"


def _pointe(cx, cy, r, angle, taille):
    """Pointe de flèche au bout de l'arc, dans le sens de rotation."""
    a = math.radians(angle)
    x, y = cx + r * math.cos(a), cy + r * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)          # tangente (sens horaire)
    nx, ny = math.cos(a), math.sin(a)           # normale
    p1 = (x + tx * taille, y + ty * taille)
    p2 = (x - tx * taille * 0.15 + nx * taille * 0.75, y - ty * taille * 0.15 + ny * taille * 0.75)
    p3 = (x - tx * taille * 0.15 - nx * taille * 0.75, y - ty * taille * 0.15 - ny * taille * 0.75)
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in (p1, p2, p3))


MARTINET = ("M256,176 C271,176 281,192 282,214 C338,220 404,256 452,322 "
            "C396,286 330,272 278,282 L284,356 L256,322 L228,356 L234,282 "
            "C182,272 116,286 60,322 C108,256 174,220 230,214 C231,192 241,176 256,176 Z")


def construire_svg() -> str:
    n, cx, cy, r = 512, 256, 262, 186
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{n}" height="{n}" viewBox="0 0 {n} {n}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="fond" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{CIEL_CLAIR}"/>
      <stop offset="0.55" stop-color="{CIEL}"/>
      <stop offset="1" stop-color="{CIEL_NUIT}"/>
    </linearGradient>
  </defs>
  <rect x="16" y="16" width="480" height="480" rx="104" fill="url(#fond)"/>
  <path d="{_arc(cx, cy, r, 200, 500)}" fill="none" stroke="{BLANC}" stroke-opacity="0.92"
        stroke-width="30" stroke-linecap="round"/>
  <polygon points="{_pointe(cx, cy, r, 500 - 360 + 6, 52)}" fill="{BLANC}" fill-opacity="0.92"/>
  <path d="{MARTINET}" fill="{BLANC}" transform="translate(0,6)"/>
</svg>
'''


def rendre(svg: Path, sortie: Path, taille: int) -> None:
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    from PyQt6.QtSvg import QSvgRenderer
    img = QImage(taille, taille, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    QSvgRenderer(str(svg)).render(p, QRectF(0, 0, taille, taille))
    p.end()
    img.save(str(sortie), "PNG")


def main():
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)  # noqa: F841 — requis pour le rendu
    svg = ICI / "logo.svg"
    svg.write_text(construire_svg(), encoding="utf-8")
    for taille in (16, 32, 64, 128, 256, 512):
        rendre(svg, ICI / f"logo_{taille}.png", taille)
    (ICI / "logo.png").write_bytes((ICI / "logo_256.png").read_bytes())
    from PIL import Image
    img = Image.open(ICI / "logo_512.png").convert("RGBA")
    img.save(ICI / "logo.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                                      (64, 64), (128, 128), (256, 256)])
    print("logo.svg -> logo_*.png, logo.png, logo.ico")


if __name__ == "__main__":
    main()
