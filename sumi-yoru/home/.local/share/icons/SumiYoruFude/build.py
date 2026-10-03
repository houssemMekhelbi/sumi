#!/usr/bin/env python3
"""Generate the SumiYoruFude cursor theme (Sumi yoru) next to this file.

The pointer is a brush arrow: a loaded head with curved flanks and a tail that
runs dry. Links add a small vermilion ring; busy is an open ensō turning;
progress is the arrow with a small vermilion ensō; not-allowed is an ensō with
a vermilion slash; grab / grabbing are a seal outline / a pressed seal.
Every shape sits on a thin halo (ink halo) so it reads on paper and on ink.

Writes two formats from the same SVGs:
  hyprcursors/ + manifest.hl*   hyprcursor (Hyprland draws it; SVG, any size)
  cursors/                      XCursor 24/32/48 (GTK3, XWayland, anything else)
Shapes not drawn here fall back to Adwaita (index.theme Inherits).
Needs rsvg-convert and hyprcursor-util. Run: python3 build.py
"""

import math
import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "SumiYoruFude"
INK, HALO, SHU = "#E9E2D4", "#15130F", "#E0583C"
XSIZES = (24, 32, 48)

ROUGH = ('<filter id="rough" x="-10%" y="-10%" width="120%" height="120%">'
         '<feTurbulence type="fractalNoise" baseFrequency="0.22" numOctaves="2" seed="4" result="e"/>'
         '<feDisplacementMap in="SourceGraphic" in2="e" scale="1.2" xChannelSelector="R" yChannelSelector="G"/></filter>')


def poly(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d
                 for a, b, c, d in zip(p0, p1, p2, p3))


def taper(p0, p1, p2, p3, w0, w1, n=40):
    pts = [bez(p0, p1, p2, p3, k / n) for k in range(n + 1)]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        s = i / n
        w = max(0.15, w0 + (w1 - w0) * s) * (min(1, s / 0.08) ** 0.4)
        left.append((x - dy / L * w, y + dx / L * w))
        right.append((x + dy / L * w, y - dx / L * w))
    return poly(left + right[::-1])


def line(a, b, w0, w1):
    return taper(a, (a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3),
                 (a[0] + 2 * (b[0] - a[0]) / 3, a[1] + 2 * (b[1] - a[1]) / 3), b, w0, w1)


def arc(cx, cy, r, a0, a1, w0, w1, n=80):
    pts = [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        s = i / n
        w = max(0.2, w0 + (w1 - w0) * s) * (min(1, s / 0.06) ** 0.4)
        nx, ny = (x - cx) / r, (y - cy) / r
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return poly(left + right[::-1])


def cur(paths, accent=()):
    ds = "".join(f'<path d="{d}"/>' for d in paths)
    acc = "".join(f'<path d="{d}"/>' for d in accent)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><defs>{ROUGH}</defs>'
            f'<g fill="{HALO}" stroke="{HALO}" stroke-width="2.4" stroke-linejoin="round">{ds}{acc}</g>'
            f'<g fill="{INK}" filter="url(#rough)">{ds}</g>'
            f'<g fill="{SHU}" filter="url(#rough)">{acc}</g></svg>\n')


# a brush arrow: blunt loaded head, curved flanks, a tail that runs dry
HEAD = "M3 2 C8 7 14 12 21 17.5 C17 18 14.5 18.6 12.8 19.5 C11 21.5 9.2 24.5 7.5 28 C6 20 4.6 11 3 2 Z"
ARROW = [HEAD, taper((11.5, 18.5), (14, 22), (16.5, 25.5), (19, 29), 1.7, 0.6)]
ENSO = lambda cx, cy, r, turn, w0, w1: arc(cx, cy, r, 110 + turn, 420 + turn, w0, w1)
FRAMES = 8


def arrows(pairs, w=1.4):
    return [line(a, b, w, w * 0.85) for a, b in pairs]


# name: (frames, hotspot (x, y) in 32-unit space, frame delay ms, aliases)
SHAPES = {
    "left_ptr": ([cur(ARROW)], (3, 2), 0,
                 ["default", "arrow", "top_left_arrow", "left_arrow", "context-menu", "copy", "alias",
                  "dnd-copy", "dnd-link", "dnd-none", "dnd-ask", "help", "question_arrow", "whats_this"]),
    "hand2": ([cur(ARROW, [arc(21.5, 24.5, 2.4, 0, 355, 1.3, 1.3)])], (3, 2), 0,
              ["pointer", "hand1", "hand", "pointing_hand", "e29285e634086352946a0e7090d73106"]),
    "xterm": ([cur([line((16, 5), (16, 27), 1.2, 1.0), line((11, 4.5), (21, 5.5), 1.2, 0.4), line((11, 27), (21, 27.5), 1.2, 0.4)])],
              (16, 16), 0, ["text", "ibeam"]),
    "vertical-text": ([cur([line((5, 16), (27, 16), 1.2, 1.0), line((4.5, 11), (5.5, 21), 1.2, 0.4), line((27, 11), (27.5, 21), 1.2, 0.4)])],
                      (16, 16), 0, []),
    "watch": ([cur([ENSO(16, 16, 10, k * 360 / FRAMES, 2.6, 0.4)]) for k in range(FRAMES)], (16, 16), 90, ["wait"]),
    "left_ptr_watch": ([cur(ARROW, [ENSO(24, 24, 5, k * 360 / FRAMES, 1.6, 0.3)]) for k in range(FRAMES)], (3, 2), 90,
                       ["progress", "half-busy", "00000000000000020006000e7e9ffc3f",
                        "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"]),
    "crosshair": ([cur([line((16, 3), (16, 29), 1.1, 0.6), line((3, 16), (29, 16), 1.1, 0.6)])], (16, 16), 0,
                  ["cross", "tcross", "cell", "plus", "color-picker"]),
    "not-allowed": ([cur([arc(16, 16, 10, 120, 480, 2.0, 1.2)], [line((9, 9), (23, 23), 1.6, 0.8)])], (16, 16), 0,
                    ["no-drop", "forbidden", "circle", "crossed_circle", "dnd-no-drop"]),
    "grab": ([cur([line((8.5, 8.5), (23.5, 8.2), 1.5, 1.1), line((23.4, 7.8), (23.2, 23.6), 1.4, 1.0),
                   line((23.6, 23.4), (8.3, 23.2), 1.4, 0.9), line((8.6, 23.6), (8.4, 8.0), 1.4, 0.8)])], (16, 16), 0,
             ["openhand", "hand-grab"]),
    "grabbing": ([cur([poly([(8.5, 8.5), (23.5, 8), (23, 23.5), (8.5, 23)])])], (16, 16), 0,
                 ["closedhand", "dnd-move", "hand-grabbing"]),
    "fleur": ([cur(arrows([((16, 4), (16, 28)), ((4, 16), (28, 16)), ((12, 8), (16, 3.5)), ((20, 8), (16, 3.5)),
                           ((12, 24), (16, 28.5)), ((20, 24), (16, 28.5)), ((8, 12), (3.5, 16)), ((8, 20), (3.5, 16)),
                           ((24, 12), (28.5, 16)), ((24, 20), (28.5, 16))], 1.3))], (16, 16), 0,
              ["move", "all-scroll", "size_all", "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"]),
    "sb_h_double_arrow": ([cur(arrows([((4, 16), (28, 16)), ((9, 11), (3.5, 16)), ((9, 21), (3.5, 16)),
                                       ((23, 11), (28.5, 16)), ((23, 21), (28.5, 16))], 1.5))], (16, 16), 0,
                          ["ew-resize", "col-resize", "e-resize", "w-resize", "h_double_arrow", "left_side",
                           "right_side", "size_hor", "split_h", "14fef782d02440884392942c11205230",
                           "028006030e0e7ebffc7f7070c0600140"]),
    "sb_v_double_arrow": ([cur(arrows([((16, 4), (16, 28)), ((11, 9), (16, 3.5)), ((21, 9), (16, 3.5)),
                                       ((11, 23), (16, 28.5)), ((21, 23), (16, 28.5))], 1.5))], (16, 16), 0,
                          ["ns-resize", "row-resize", "n-resize", "s-resize", "v_double_arrow", "top_side",
                           "bottom_side", "size_ver", "split_v", "2870a09082c103050810ffdffffe0204",
                           "00008160000006810000408080010102"]),
    "bd_double_arrow": ([cur(arrows([((6, 6), (26, 26)), ((6, 13), (5.5, 5.5)), ((13, 6), (5.5, 5.5)),
                                     ((26, 19), (26.5, 26.5)), ((19, 26), (26.5, 26.5))], 1.5))], (16, 16), 0,
                        ["nwse-resize", "nw-resize", "se-resize", "top_left_corner",
                         "bottom_right_corner", "size_fdiag", "c7088f0f3e6c8088236ef8e1e3e70000"]),
    "fd_double_arrow": ([cur(arrows([((26, 6), (6, 26)), ((26, 13), (26.5, 5.5)), ((19, 6), (26.5, 5.5)),
                                     ((6, 19), (5.5, 26.5)), ((13, 26), (5.5, 26.5))], 1.5))], (16, 16), 0,
                        ["nesw-resize", "ne-resize", "sw-resize", "top_right_corner",
                         "bottom_left_corner", "size_bdiag", "fcf1c3c7cd4491d801f1e1c78f100000"]),
}


# ---- PNG decode (8-bit RGBA from rsvg-convert) --------------------------------

def load_png(path):
    d = Path(path).read_bytes()
    pos, idat = 8, b""
    while pos < len(d):
        n, t = struct.unpack(">I4s", d[pos:pos + 8])
        body = d[pos + 8:pos + 8 + n]
        pos += 12 + n
        if t == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", body[:10])
            assert bd == 8 and ct == 6, "expected 8-bit RGBA"
        elif t == b"IDAT":
            idat += body
    raw, bpp, stride = zlib.decompress(idat), 4, w * 4
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f, line_ = raw[i], bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line_[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line_[x] = (line_[x] + a) & 255
            elif f == 2:
                line_[x] = (line_[x] + b) & 255
            elif f == 3:
                line_[x] = (line_[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line_[x] = (line_[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line_))
        prev = line_
    return w, h, rows


def argb_premultiplied(rows):
    out = bytearray()
    for r in rows:
        for x in range(0, len(r), 4):
            R, G, B, A = r[x:x + 4]
            out += struct.pack("<I", (A << 24) | ((R * A // 255) << 16) | ((G * A // 255) << 8) | (B * A // 255))
    return bytes(out)


def xcursor(images):
    """images: list of (nominal, w, h, xhot, yhot, delay, argb). Returns XCursor bytes."""
    ntoc = len(images)
    header = struct.pack("<4sIII", b"Xcur", 16, 0x10000, ntoc)
    pos = 16 + ntoc * 12
    toc, chunks = b"", b""
    for nominal, w, h, xh, yh, delay, px in images:
        toc += struct.pack("<III", 0xFFFD0002, nominal, pos)
        chunk = struct.pack("<IIIIIIIII", 36, 0xFFFD0002, nominal, 1, w, h, xh, yh, delay) + px
        chunks += chunk
        pos += len(chunk)
    return header + toc + chunks


def main():
    for d in ("hyprcursors", "cursors"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    for f in ROOT.glob("manifest.*"):
        f.unlink()
    (ROOT / "cursors").mkdir()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work"
        (work / "hyprcursors").mkdir(parents=True)
        (work / "manifest.hl").write_text(
            f"name = {NAME}\ndescription = Sumi yoru: brush-stroke pointer, ensō busy\n"
            "version = 0.1\ncursors_directory = hyprcursors\n")
        for shape, (frames, (hx, hy), delay, aliases) in SHAPES.items():
            sd = work / "hyprcursors" / shape
            sd.mkdir()
            meta = [f"resize_algorithm = bilinear", f"hotspot_x = {hx / 32:.4f}", f"hotspot_y = {hy / 32:.4f}"]
            meta += [f"define_override = {a}" for a in aliases]
            images = []
            for k, body in enumerate(frames):
                fname = f"{shape}-{k}.svg"
                (sd / fname).write_text(body)
                meta.append(f"define_size = 0, {fname}" + (f", {delay}" if delay else ""))
                for size in XSIZES:
                    png = Path(tmp) / f"{shape}-{k}-{size}.png"
                    subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size), "-o", str(png), str(sd / fname)], check=True)
                    w, h, rows = load_png(png)
                    images.append((size, w, h, round(hx * size / 32), round(hy * size / 32), delay or 0, argb_premultiplied(rows)))
            (sd / "meta.hl").write_text("\n".join(meta) + "\n")
            images.sort(key=lambda i: i[0])
            (ROOT / "cursors" / shape).write_bytes(xcursor(images))
            for a in aliases:
                link = ROOT / "cursors" / a
                if not link.exists():
                    os.symlink(shape, link)

        out = Path(tmp) / "out"
        out.mkdir()
        subprocess.run(["hyprcursor-util", "--create", str(work), "--output", str(out)], check=True,
                       stdout=subprocess.DEVNULL)
        built = next(out.iterdir())
        for item in built.iterdir():
            dest = ROOT / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    (ROOT / "index.theme").write_text(
        f"[Icon Theme]\nName={NAME}\nComment=Sumi yoru cursors: brush arrow, ensō, seal\nInherits=Adwaita\n")
    print(f"{NAME} written to {ROOT}")


if __name__ == "__main__":
    main()
