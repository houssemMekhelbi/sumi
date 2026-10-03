#!/usr/bin/env python3
"""Generate the ink-drawn art of the Sumi yoru theme (run from anywhere).

Everything is SVG with feTurbulence filters, rendered to PNG with rsvg-convert:
  hypr/sumi-yoru/wallpaper.svg + .png   washi paper, two ink washes, one dry-brush stroke
  hypr/sumi-yoru/lock-field.png         brush stroke behind the lock password field
  hypr/sumi-yoru/seal.png               vermilion seal imprint (lock screen, 64px)
  hypr/sumi-yoru/banner-card.png        deckle-edged paper card for the prayer banner
  hypr/sumi-yoru/banner-seal.png        seal for the banner (72px)
  waybar/sumi-yoru/band-{start,end,body}.png   the bar: dry ends + a seamless body tile
  gtk-3.0/sumi-yoru/band.png            the same stroke for Thunar's current crumb and selection
  gtk-3.0/sumi-yoru/chevron.png         path-bar separator
Deterministic: the same script always gives the same pictures. Edit and re-run.
"""

import math
import random
import subprocess
import tempfile
from pathlib import Path

CONFIG = Path.home() / ".config"
NAME = "sumi-yoru"

# ---- palette -----------------------------------------------------------------
PAPER, RAISED, INK, WASH_FAR, WASH_NEAR, FIBRE = "#15130F", "#1D1B17", "#BDB6A8", "#8A8377", "#B5AEA1", "#4A453C"
GRAIN_RGB, MOTTLE = (0.00, 0.00, 0.00), (0.7, 0.22)
WASH_OP = (0.16, 0.22)
BAND, BAND_OP = "#BDB6A8", 0.10          # the pale ink of the bar strokes
SEAL = "#D2492F"
CARD, CARD_RIM, CARD_GRAIN = "#1D1B17", "#3A362F", 0.12
CHEVRON = "#5A554C"


# ---- geometry helpers ----------------------------------------------------------------
def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d
                 for a, b, c, d in zip(p0, p1, p2, p3))


def stroke_outline(segs, width, n=120):
    """Closed outline of a brush stroke along cubic beziers; width(s) = half width, s in 0..1."""
    pts = []
    for i, seg in enumerate(segs):
        for k in range(n + (1 if i == len(segs) - 1 else 0)):
            pts.append(bez(*seg, k / n))
    m = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, m - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = width(i / (m - 1))
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in left + right[::-1]) + " Z"


def svg(w, h, defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}</defs>{body}</svg>\n')


def render(content, out, w, h, keep_svg=False):
    out.parent.mkdir(parents=True, exist_ok=True)
    if keep_svg:
        src = out.with_suffix(".svg")
        src.write_text(content)
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(out), str(src)], check=True)
        return
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(content)
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(out), f.name], check=True)
    Path(f.name).unlink()


# ---- the brush filter ------------------------------------------------------------
# The shape is filled with a red gradient: red = how wet the brush is there.
# Alpha = shape x clamp(k2*hair + k3*wet + k4): wet parts stay solid, dry parts
# break into hair streaks.
def brush_filter(fid, color, opacity=1, edge=(0.03, 10), hair="0.0016 0.13", k=(7, 3.3, -4.2),
                 bend=28, seed=2, blur=0.5, stitch=False, region=None, y_only=False):
    st = ' stitchTiles="stitch"' if stitch else ""
    reg = (f'x="{region[0]}" y="{region[1]}" width="{region[2]}" height="{region[3]}" filterUnits="userSpaceOnUse"'
           if region else 'x="-5%" y="-40%" width="110%" height="180%"')
    disp = (f'<feColorMatrix in="edge" type="matrix" values="0 0 0 0 0.5  0 1 0 0 0  0 0 0 0 0  0 0 0 0 1" result="edge2"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="edge2" scale="{edge[1]}" xChannelSelector="R" yChannelSelector="G" result="shape"/>'
            if y_only else
            f'<feDisplacementMap in="SourceGraphic" in2="edge" scale="{edge[1]}" xChannelSelector="R" yChannelSelector="G" result="shape"/>')
    bendf = (f'<feTurbulence type="fractalNoise" baseFrequency="0.004" numOctaves="2" seed="{seed + 11}"{st} result="bend"/>'
             f'<feDisplacementMap in="hair0" in2="bend" scale="{bend}" xChannelSelector="R" yChannelSelector="G" result="hair1"/>'
             if bend else '<feOffset in="hair0" result="hair1"/>')
    return f'''<filter id="{fid}" {reg} color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="{edge[0]}" numOctaves="3" seed="{seed}"{st} result="edge"/>
  {disp}
  <feColorMatrix in="shape" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1 0 0 0 0" result="wetA"/>
  <feTurbulence type="fractalNoise" baseFrequency="{hair}" numOctaves="3" seed="{seed + 7}"{st} result="hair0"/>
  {bendf}
  <feColorMatrix in="hair1" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1 0 0 0 0" result="hairA"/>
  <feComposite in="hairA" in2="wetA" operator="arithmetic" k2="{k[0]}" k3="{k[1]}" k4="{k[2]}" result="mixA"/>
  <feComposite in="mixA" in2="shape" operator="in" result="cut"/>
  <feFlood flood-color="{color}" flood-opacity="{opacity}"/>
  <feComposite in2="cut" operator="in" result="ink"/>
  <feGaussianBlur in="ink" stdDeviation="{blur}"/>
</filter>'''


def wet_gradient(gid, stops, x1=0, x2=1, units="objectBoundingBox"):
    s = "".join(f'<stop offset="{o}" stop-color="#{int(255 * w):02x}0000"/>' for o, w in stops)
    if units == "userSpaceOnUse":
        return f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="0">{s}</linearGradient>'
    return f'<linearGradient id="{gid}" x1="{x1}" y1="0" x2="{x2}" y2="0">{s}</linearGradient>'


# ---- wallpaper ------------------------------------------------------------------------
def wallpaper():
    gr, gg, gb = GRAIN_RGB
    mot_a, mot_b = MOTTLE
    defs = f'''
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 {gr}  0 0 0 0 {gg}  0 0 0 0 {gb}  0 0 0 1.3 -0.62"/>
</filter>
<filter id="mottle" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.0022" numOctaves="4" seed="4" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 {gr}  0 0 0 0 {gg}  0 0 0 0 {gb}  0 0 0 {mot_a} -{mot_b}"/>
</filter>
<filter id="wash" x="-20%" y="-20%" width="140%" height="140%">
  <feTurbulence type="fractalNoise" baseFrequency="0.008" numOctaves="4" seed="21" result="warp"/>
  <feDisplacementMap in="SourceGraphic" in2="warp" scale="70" xChannelSelector="R" yChannelSelector="G" result="shape"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="8" result="warp2"/>
  <feDisplacementMap in="shape" in2="warp2" scale="9" xChannelSelector="R" yChannelSelector="G" result="shape2"/>
  <feGaussianBlur in="shape2" stdDeviation="7" result="soft"/>
  <feGaussianBlur in="shape2" stdDeviation="1.2" result="crisp"/>
  <feGaussianBlur in="shape2" stdDeviation="14" result="wide"/>
  <feComposite in="crisp" in2="wide" operator="arithmetic" k2="0.9" k3="-0.75" result="rim"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.004" numOctaves="3" seed="5" result="dens"/>
  <feColorMatrix in="dens" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  1.8 0 0 0 -0.45" result="densA"/>
  <feComposite in="soft" in2="densA" operator="in" result="body"/>
  <feMerge><feMergeNode in="body"/><feMergeNode in="rim"/></feMerge>
</filter>
{brush_filter("brush", INK)}
<filter id="spat" x="-50%" y="-50%" width="200%" height="200%">
  <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed="3" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="6" xChannelSelector="R" yChannelSelector="G"/>
</filter>
{wet_gradient("wet", [(0, 1), (0.25, 0.91), (0.6, 0.54), (1, 0.1)], 1850, 760, "userSpaceOnUse")}'''

    def width(s):  # blunt press at the head, then a long taper
        press = min(1, s / 0.035) ** 0.5
        body = 40 * (1 - s) ** 0.55 + 5 * s
        return max(0.5, press * body * (1 + 0.06 * math.sin(s * 23) + 0.04 * math.sin(s * 57 + 1)))
    stroke = stroke_outline([((1850, 842), (1650, 786), (1390, 800), (1160, 856)),
                             ((1160, 856), (1020, 890), (900, 904), (770, 894))], width)
    rnd = random.Random(42)
    fibres = []
    for _ in range(260):  # kozo fibres
        x, y = rnd.uniform(0, 1920), rnd.uniform(0, 1080)
        a, L = rnd.uniform(0, math.pi), rnd.uniform(25, 140)
        x2, y2 = x + math.cos(a) * L, y + math.sin(a) * L
        cx, cy = (x + x2) / 2 + rnd.uniform(-25, 25), (y + y2) / 2 + rnd.uniform(-25, 25)
        fibres.append(f'<path d="M{x:.0f} {y:.0f} Q{cx:.0f} {cy:.0f} {x2:.0f} {y2:.0f}" '
                      f'stroke-width="{rnd.uniform(0.5, 1.3):.1f}" opacity="{rnd.uniform(0.10, 0.28):.2f}"/>')
    body = f'''<rect width="1920" height="1080" fill="{PAPER}"/>
<rect width="1920" height="1080" filter="url(#mottle)"/>
<g fill="none" stroke="{FIBRE}" stroke-linecap="round">{"".join(fibres)}</g>
<rect width="1920" height="1080" filter="url(#grain)" opacity="0.8"/>
<g filter="url(#wash)" opacity="{WASH_OP[0]}"><path d="M1040 1080 C1120 950 1240 900 1370 915 C1480 790 1630 745 1760 805 C1850 845 1920 830 1920 830 L1920 1080 Z" fill="{WASH_FAR}"/></g>
<g filter="url(#wash)" opacity="{WASH_OP[1]}"><path d="M1300 1080 C1390 1005 1480 975 1580 990 C1690 940 1800 948 1920 995 L1920 1080 Z" fill="{WASH_NEAR}"/></g>
<g filter="url(#brush)"><path d="{stroke}" fill="url(#wet)"/></g>
<g filter="url(#spat)" fill="{INK}"><circle cx="1884" cy="826" r="4.5"/><circle cx="1902" cy="860" r="2.2"/><circle cx="1866" cy="884" r="1.6"/><circle cx="1908" cy="812" r="1.2"/></g>'''
    render(svg(1920, 1080, defs, body), CONFIG / "hypr" / NAME / "wallpaper.png", 1920, 1080, keep_svg=True)


# ---- strokes for the bar, GTK and the lock field ----------------------------------
def band(w, h, seed, dry_left=0.06, dry_right=0.07, pad=6, color=BAND, opacity=BAND_OP, k=(6, 3.6, -3.9)):
    """A pale ink stroke w x h: wet in the middle, dry ragged ends."""
    segs = [((pad, h / 2), (w * 0.33, h / 2 - 0.8), (w * 0.66, h / 2 + 0.8), (w - pad, h / 2))]
    half = h / 2 - 2.5

    def wd(s):
        end = min(1, s / 0.02, (1 - s) / 0.03) ** 0.35
        return half * end * (1 + 0.035 * math.sin(s * 40 + seed))
    defs = brush_filter("b", color, opacity, edge=(0.07, 4), hair="0.004 0.35", k=k, bend=0, seed=seed, blur=0.3) + \
        wet_gradient("g", [(0, 0), (dry_left, 1), (1 - dry_right, 1), (1, 0)])
    return svg(w, h, defs, f'<g filter="url(#b)"><path d="{stroke_outline(segs, wd, 300)}" fill="url(#g)"/></g>')


def bar_pieces():
    H, CAP, TILE = 34, 30, 240
    out = CONFIG / "waybar" / NAME
    # start cap: the brush comes down dry on the left and runs off the right edge
    def cap(mirror, seed):
        segs = [((3, H / 2), (15, H / 2 - 0.6), (30, H / 2 + 0.4), (48, H / 2))]

        def wd(s):
            return 15 * min(1, s / 0.36) ** 0.35 * (1 + 0.04 * math.sin(s * 30 + seed))
        defs = brush_filter("b", BAND, BAND_OP, edge=(0.07, 3), hair="0.004 0.35", k=(6, 3.6, -4.0), bend=0,
                            seed=seed, blur=0.3, region=(0, 0, CAP, H)) + \
            wet_gradient("g", [(0, 0), (0.55, 1), (1, 1)], 0, 48, "userSpaceOnUse")
        g = f'<g filter="url(#b)"><path d="{stroke_outline(segs, wd, 200)}" fill="url(#g)"/></g>'
        if mirror:
            g = f'<g transform="translate({CAP} 0) scale(-1 1)">{g}</g>'
        return svg(CAP, H, defs, g)
    render(cap(False, 3), out / "band-start.png", CAP, H)
    render(cap(True, 17), out / "band-end.png", CAP, H)
    # body: seamless horizontally (stitched noise, vertical-only edge displacement)
    defs = brush_filter("b", BAND, BAND_OP, edge=(f"{2 / TILE:.5f} 0.09", 3), hair=f"{2 / TILE:.5f} 0.35",
                        k=(6, 3.6, -4.1), bend=0, seed=5, blur=0.3, stitch=True, region=(0, 0, TILE, H), y_only=True)
    render(svg(TILE, H, defs, f'<g filter="url(#b)"><rect x="-20" y="2" width="{TILE + 40}" height="30" fill="#ff0000"/></g>'),
           out / "band-body.png", TILE, H)


def gtk_pieces():
    out = CONFIG / "gtk-3.0" / NAME
    render(band(160, 28, 9), out / "band.png", 160, 28)
    d = stroke_outline([((3, 3), (5, 6), (7, 8), (8, 9))], lambda s: 1.1 - 0.4 * s, 30) + " " + \
        stroke_outline([((8, 9), (7, 10), (5, 12), (3, 15))], lambda s: 1.0 - 0.6 * s, 30)
    render(svg(10, 18, "", f'<path d="{d}" fill="{CHEVRON}"/>'), out / "chevron.png", 10, 18)


def seal(size, seed=31):
    return svg(size, size, f'''<filter id="s" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="{0.12 * 96 / size:.3f}" numOctaves="2" seed="{seed}" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="{3.5 * size / 96:.2f}" xChannelSelector="R" yChannelSelector="G" result="shape"/>
  <feTurbulence type="fractalNoise" baseFrequency="{0.09 * 96 / size:.3f}" numOctaves="3" seed="{seed + 3}" result="p"/>
  <feColorMatrix in="p" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  7 0 0 0 -1.3" result="pA"/>
  <feComposite in="shape" in2="pA" operator="in"/>
</filter>''', f'<g filter="url(#s)"><rect x="{size * 0.04:.1f}" y="{size * 0.04:.1f}" width="{size * 0.92:.1f}" height="{size * 0.92:.1f}" rx="2" fill="{SEAL}"/></g>')


def card(w, h, seed=17):
    return svg(w, h, f'''<filter id="c" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="3" seed="{seed}" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="7" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="gr" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.4  0 0 0 0 0.35  0 0 0 0 0.28  0 0 0 1.2 -0.6" result="g"/>
  <feComposite in="g" in2="SourceGraphic" operator="in"/>
</filter>''', f'''<g filter="url(#c)"><rect x="6" y="6" width="{w - 12}" height="{h - 12}" fill="{CARD_RIM}"/>
<rect x="7.5" y="7.5" width="{w - 15}" height="{h - 15}" fill="{CARD}"/></g>
<rect x="10" y="10" width="{w - 20}" height="{h - 20}" fill="#000" filter="url(#gr)" opacity="{CARD_GRAIN}"/>''')


def lock_and_banner():
    out = CONFIG / "hypr" / NAME
    render(band(440, 46, 21, k=(6, 3.6, -3.8)), out / "lock-field.png", 440, 46)
    render(seal(64), out / "seal.png", 64, 64)
    render(seal(72), out / "banner-seal.png", 72, 72)
    render(card(460, 150), out / "banner-card.png", 460, 150)


if __name__ == "__main__":
    wallpaper()
    bar_pieces()
    gtk_pieces()
    lock_and_banner()
    print("Sumi yoru ink written")
