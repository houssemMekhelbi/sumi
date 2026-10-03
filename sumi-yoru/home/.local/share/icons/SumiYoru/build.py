#!/usr/bin/env python3
"""Generate the SumiYoru icon theme (Sumi yoru) next to this file.

scalable/  64-unit SVGs drawn as ink: folders are two layers of ink wash with a
           dry-brush top edge and a paper-coloured brush mark for the special
           folders; documents are paper sheets with hand-inked edges and one ink
           mark for their type (vermilion only on PDF and image, where a seal or
           a red dot would sit); devices and trash are brush outlines on a wash.
16/        sidebar size: plain line icons in Muted, no texture (it would not read).
The texture comes from feTurbulence filters, which librsvg renders.
Anything not drawn here falls through to Adwaita.
Run: python3 build.py   (then gtk-update-icon-cache runs by itself)
"""

import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "SumiYoru"

FOLDER_BACK, FOLDER_FRONT, FOLDER_EDGE, FOLDER_MARK = "#5E594F", "#8F887C", "#E9E2D4", "#15130F"
PAPER, PAPER_FOLD, INK, TAN, WASH = "#FBF8F2", "#E4DDCF", "#3A3733", "#A39B8C", "#6E6961"
AI, SHU = "#2E4A6B", "#C8412B"
DEV_FILL, DEV_EDGE, DEV_LIGHT = "#3A362F", "#BDB6A8", "#7FA1C6"
SIDE = "#9A9386"


# ---- brush geometry ------------------------------------------------------------
def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d
                 for a, b, c, d in zip(p0, p1, p2, p3))


def poly(pts):
    return "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def taper(p0, p1, p2, p3, w0, w1, n=40):
    """Tapered stroke along one bezier: half width w0 -> w1, with a soft landing."""
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


def line(a, b, w0, w1, bend=0):
    (x0, y0), (x1, y1) = a, b
    nx, ny = -(y1 - y0), (x1 - x0)
    L = math.hypot(nx, ny) or 1
    c = ((x0 + x1) / 2 + nx / L * bend, (y0 + y1) / 2 + ny / L * bend)
    return taper(a, ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2), ((b[0] + c[0]) / 2, (b[1] + c[1]) / 2), b, w0, w1)


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


FILTERS = '''<filter id="rough" x="-10%" y="-10%" width="120%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.22" numOctaves="2" seed="4" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="1.6" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="wash" x="-10%" y="-10%" width="120%" height="120%">
  <feTurbulence type="fractalNoise" baseFrequency="0.16" numOctaves="3" seed="21" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="2.2" xChannelSelector="R" yChannelSelector="G" result="s"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="2" seed="5" result="d"/>
  <feColorMatrix in="d" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0.9 0 0 0 0.45" result="dA"/>
  <feComposite in="s" in2="dA" operator="in" result="body"/>
  <feGaussianBlur in="s" stdDeviation="0.35" result="soft"/>
  <feComposite in="soft" in2="body" operator="arithmetic" k2="0.35" k3="0.75"/>
</filter>
<filter id="dry" x="-10%" y="-30%" width="120%" height="160%">
  <feTurbulence type="fractalNoise" baseFrequency="0.25" numOctaves="2" seed="2" result="e"/>
  <feDisplacementMap in="SourceGraphic" in2="e" scale="1.2" xChannelSelector="R" yChannelSelector="G" result="s"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.03 1.1" numOctaves="2" seed="9" result="h"/>
  <feColorMatrix in="h" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  4 0 0 0 -0.9" result="hA"/>
  <feComposite in="s" in2="hA" operator="in"/>
</filter>'''


def svg64(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">'
            f'<defs>{FILTERS}</defs>{body}</svg>\n')


def ink(paths, color, filt="rough"):
    return f'<g filter="url(#{filt})" fill="{color}">' + "".join(f'<path d="{d}"/>' for d in paths) + "</g>"


def write(rel, content, names):
    for name in names:
        path = ROOT / rel / f"{name}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


# ---- folder marks (paper-coloured brush on the front of the folder) -----------------
def mark(kind):
    m = {
        "home": [line((22, 45), (32, 36), 1.6, 1.2), line((32, 36), (42, 45), 1.4, 0.6), line((26, 48), (38, 48), 1.3, 0.5)],
        "downloads": [line((32, 33), (32, 47), 1.7, 0.8), line((26, 42), (32, 48), 1.4, 1.0), line((38, 42), (32, 48), 1.4, 1.0)],
        "documents": [line((23, 36), (41, 36), 1.4, 0.5), line((23, 42), (41, 42), 1.4, 0.5), line((23, 48), (35, 48), 1.4, 0.5)],
        "pictures": [poly([(21, 49), (29, 39), (34, 44), (38, 40), (44, 49)]), arc(39, 34, 2.2, 0, 350, 1.2, 1.0)],
        "music": [taper((21, 42), (25, 34), (29, 50), (33, 42), 1.5, 1.1), taper((33, 42), (37, 34), (41, 50), (44, 41), 1.1, 0.4)],
        "videos": [line((26, 35), (26, 49), 1.5, 1.2), line((26, 35), (40, 42), 1.4, 1.1), line((40, 42), (26, 49), 1.2, 0.5)],
        "desktop": [line((22, 36), (42, 36), 1.4, 1.1), line((42, 36), (42, 45), 1.3, 1.1), line((42, 45), (22, 45), 1.2, 0.9),
                    line((22, 45), (22, 36), 1.0, 0.8), line((28, 49), (36, 49), 1.3, 0.5)],
        "templates": [line((24, 35), (29, 35), 1.2, 0.6), line((35, 35), (40, 35), 1.2, 0.6), line((40, 38), (40, 43), 1.2, 0.6),
                      line((40, 47), (35, 47), 1.2, 0.6), line((29, 47), (24, 47), 1.2, 0.6), line((24, 44), (24, 39), 1.2, 0.6)],
        "share": [line((24, 47), (32, 35), 1.5, 1.1), line((32, 35), (40, 47), 1.3, 0.9), line((40, 47), (24, 47), 1.1, 0.5)],
        "remote": [arc(32, 41, 7.5, -80, 280, 1.3, 0.6), line((24.5, 41), (39.5, 41), 1.0, 0.4), line((32, 33.5), (32, 48.5), 1.0, 0.4)],
    }[kind]
    return ink(m, FOLDER_MARK)


def folder(kind=None):
    top = taper((5, 25.5), (22, 24), (42, 25), (59, 24), 1.9, 0.6)
    body = (f'<g filter="url(#wash)"><path d="M6 14 L24 14 L28 19 L58 19 L58 54 L6 54 Z" fill="{FOLDER_BACK}"/></g>'
            f'<g filter="url(#wash)"><path d="M4 25 L60 24 L58 56 L6 56 Z" fill="{FOLDER_FRONT}"/></g>'
            f'<g filter="url(#dry)"><path d="{top}" fill="{FOLDER_EDGE}"/></g>' + (mark(kind) if kind else ""))
    return svg64(body)


FOLDERS = {
    None: ["folder", "inode-directory", "folder-open", "folder-drag-accept", "folder-visiting"],
    "home": ["user-home", "folder-home"],
    "documents": ["folder-documents"],
    "downloads": ["folder-download"],
    "music": ["folder-music"],
    "pictures": ["folder-pictures"],
    "videos": ["folder-videos"],
    "templates": ["folder-templates"],
    "share": ["folder-publicshare"],
    "desktop": ["user-desktop"],
    "remote": ["folder-remote", "network-workgroup"],
}
for kind, names in FOLDERS.items():
    write("scalable/places", folder(kind), names)
    if kind is None:
        write("scalable/mimetypes", folder(kind), names)


# ---- documents -------------------------------------------------------------------------
def sheet():
    strokes = [line((14.5, 4.5), (41.5, 5.2), 1.3, 0.8), line((41, 4.6), (52.6, 16.2), 1.1, 0.8),
               line((52.2, 15.5), (52.4, 59.4), 1.5, 0.7), line((52.8, 59.2), (13.6, 59.6), 1.6, 0.9),
               line((14.2, 60), (14.4, 4.2), 1.7, 1.0), line((41.3, 5.5), (41.3, 16.3), 0.9, 0.5),
               line((41, 16.1), (52.2, 16.1), 0.9, 0.4)]
    return (f'<g filter="url(#wash)"><path d="M14 5 L41 5 L52 16 L52 59 L14 59 Z" fill="{PAPER}"/>'
            f'<path d="M41 5 L41 16 L52 16 Z" fill="{PAPER_FOLD}"/></g>' + ink(strokes, INK))


def lines(ys, color=INK, x0=20, x1=45):
    return ink([line((x0, y), (x1 - (8 if i == len(ys) - 1 else 0), y), 1.3, 0.35) for i, y in enumerate(ys)], color, "dry")


DOC_MARKS = {
    None: "",
    "text": lines([26, 32, 38, 44, 50]),
    "script": ink([line((21, 28), (28, 33), 1.5, 1.0), line((28, 33), (21, 38), 1.2, 0.5), line((31, 39), (42, 39), 1.3, 0.4)], AI)
              + lines([47, 53], TAN, 20, 44),
    "code": ink([line((27, 29), (20, 37), 1.4, 1.0), line((20, 37), (27, 45), 1.2, 0.5),
                 line((38, 29), (45, 37), 1.4, 1.0), line((45, 37), (38, 45), 1.2, 0.5)], AI) + lines([52], TAN, 20, 44),
    "exec": ink([poly([(33, 27), (41, 36), (33, 45), (25, 36)])], INK) + lines([51], TAN, 20, 44),
    "image": f'<g filter="url(#wash)"><path d="M17 52 L27 36 L33 44 L38 38 L49 52 Z" fill="{WASH}"/></g>'
             f'<g filter="url(#rough)"><circle cx="40" cy="27" r="3.2" fill="{SHU}"/></g>',
    "pdf": lines([24, 30, 36, 42]) + f'<g filter="url(#rough)"><rect x="37" y="46" width="9" height="9" fill="{SHU}"/></g>',
    "audio": ink([taper((18, 38), (24, 22), (30, 54), (34, 38), 1.6, 1.2), taper((34, 38), (38, 24), (44, 52), (48, 36), 1.2, 0.4)], INK),
    "video": ink([line((24, 27), (24, 49), 1.6, 1.3), line((24, 27), (43, 38), 1.5, 1.2), line((43, 38), (24, 49), 1.3, 0.5)], INK),
    "archive": f'<g filter="url(#wash)"><rect x="29" y="5" width="8" height="54" fill="{TAN}"/></g>'
               + ink([line((27, 30), (39, 30), 1.2, 1.0), line((39, 30), (39, 39), 1.2, 1.0), line((39, 39), (27, 39), 1.2, 1.0),
                      line((27, 39), (27, 30), 1.2, 0.7)], INK),
    "grid": ink([line((19, 26), (47, 26), 1.2, 0.5), line((19, 35), (47, 35), 1.2, 0.5), line((19, 44), (47, 44), 1.2, 0.5),
                 line((28, 22), (28, 50), 1.1, 0.5), line((37, 22), (37, 50), 1.1, 0.5)], INK, "dry"),
    "slide": f'<g filter="url(#wash)"><rect x="19" y="24" width="28" height="18" fill="{TAN}"/></g>'
             + ink([line((33, 42), (33, 51), 1.3, 0.5)], INK),
    "font": ink([line((22, 50), (32, 25), 1.6, 1.1), line((32, 25), (43, 50), 1.5, 0.7), line((26, 41), (39, 41), 1.2, 0.5)], INK),
}
DOCUMENTS = {
    None: ["application-x-generic", "unknown", "empty"],
    "text": ["text-x-generic", "text-plain", "x-office-document", "text-markdown", "text-x-readme"],
    "script": ["text-x-script", "application-x-shellscript", "text-x-python", "text-x-makefile"],
    "exec": ["application-x-executable", "application-x-sharedlib"],
    "image": ["image-x-generic"],
    "audio": ["audio-x-generic"],
    "video": ["video-x-generic"],
    "archive": ["package-x-generic", "application-x-archive", "application-zip", "application-x-compressed-tar", "application-x-tar"],
    "pdf": ["application-pdf"],
    "code": ["text-html", "application-json", "text-x-csrc", "text-x-c++src", "text-x-javascript"],
    "grid": ["x-office-spreadsheet"],
    "slide": ["x-office-presentation"],
    "font": ["font-x-generic"],
}
for kind, names in DOCUMENTS.items():
    write("scalable/mimetypes", svg64(sheet() + DOC_MARKS[kind]), names)


# ---- devices and trash -----------------------------------------------------------------
def box(x0, y0, x1, y1):
    return [line((x0, y0), (x1, y0 + 0.4), 1.5, 1.0), line((x1, y0), (x1 + 0.3, y1), 1.4, 0.9),
            line((x1, y1), (x0, y1 + 0.3), 1.5, 0.9), line((x0, y1), (x0 - 0.2, y0), 1.3, 0.8)]


def wash_rect(x0, y0, x1, y1, color=DEV_FILL):
    return f'<g filter="url(#wash)"><rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{color}"/></g>'


DRIVE = wash_rect(9, 22, 55, 44) + ink(box(9, 22, 55, 44), DEV_EDGE) + ink([line((15, 33), (36, 33), 1.2, 0.4)], DEV_EDGE, "dry") \
    + f'<g filter="url(#rough)"><circle cx="46" cy="33" r="2.6" fill="{DEV_LIGHT}"/></g>'
write("scalable/devices", svg64(DRIVE), ["drive-harddisk", "drive-harddisk-system", "drive-multidisk"])
REMOVABLE = wash_rect(19, 20, 45, 56) + ink(box(19, 20, 45, 56) + box(24, 9, 40, 20), DEV_EDGE) \
    + f'<g filter="url(#rough)"><circle cx="32" cy="40" r="2.6" fill="{DEV_LIGHT}"/></g>'
write("scalable/devices", svg64(REMOVABLE), ["drive-removable-media", "drive-harddisk-usb", "media-removable", "media-flash"])
OPTICAL = f'<g filter="url(#wash)"><circle cx="32" cy="32" r="21" fill="{DEV_FILL}"/></g>' \
    + ink([arc(32, 32, 21, 120, 460, 2.0, 0.6), arc(32, 32, 5, 0, 350, 1.2, 0.9)], DEV_EDGE)
write("scalable/devices", svg64(OPTICAL), ["drive-optical", "media-optical"])
COMPUTER = wash_rect(10, 11, 54, 42) + ink(box(10, 11, 54, 42) + [line((24, 54), (40, 54), 1.5, 0.6), line((32, 43), (32, 54), 1.4, 1.0)], DEV_EDGE)
write("scalable/devices", svg64(COMPUTER), ["computer", "video-display"])
BIN = ink([line((13, 18), (51, 18.5), 1.6, 0.8), line((26, 18), (27, 11), 1.2, 0.9), line((27, 11), (38, 11.3), 1.2, 0.9),
           line((38, 11), (38, 18), 1.2, 0.7), line((17, 22), (21, 56), 1.5, 1.1), line((21, 56), (43, 56), 1.5, 1.0),
           line((43, 56), (47, 22), 1.4, 0.8)], DEV_EDGE)
write("scalable/places", svg64(f'<g filter="url(#wash)"><path d="M17 22 L47 22 L43 56 L21 56 Z" fill="{DEV_FILL}"/></g>' + BIN
                               + ink([line((27, 30), (28, 48), 1.1, 0.5), line((37, 30), (36, 48), 1.1, 0.5)], DEV_EDGE, "dry")),
      ["user-trash"])
write("scalable/places", svg64(f'<g filter="url(#wash)"><path d="M17 22 L47 22 L43 56 L21 56 Z" fill="{DEV_FILL}"/>'
                               f'<path d="M20 22 C22 12 30 16 33 13 C37 10 44 14 45 22 Z" fill="{PAPER}"/></g>' + BIN),
      ["user-trash-full"])


# ---- 16px sidebar: plain line icons ------------------------------------------------------
SYM = {
    "home": '<path d="M2 8 L8 2.5 L14 8"/><path d="M4 7 V14 H12 V7"/>',
    "desktop": '<rect x="2" y="3" width="12" height="8"/><path d="M6 14 H10"/>',
    "documents": '<path d="M4 2 H10 L13 5 V14 H4 Z"/><path d="M6.5 8 H10.5 M6.5 11 H9.5"/>',
    "downloads": '<path d="M8 2 V11"/><path d="M4 7.5 L8 11.5 L12 7.5"/><path d="M3 14 H13"/>',
    "music": '<path d="M1.5 8 C3 3 5 13 8 8 C11 3 13 13 14.5 8"/>',
    "pictures": '<path d="M2 13 L6 7 L9 10.5 L11 8.5 L14 13 Z"/><circle cx="11.5" cy="4.5" r="1.2"/>',
    "videos": '<path d="M5 3 V13 L13 8 Z"/>',
    "templates": '<rect x="2.5" y="2.5" width="11" height="11" stroke-dasharray="2.2 2"/>',
    "share": '<path d="M3 13 L8 4 L13 13 Z"/>',
    "folder": '<path d="M2 4 H6.5 L8 5.5 H14 V13 H2 Z"/>',
    "recent": '<circle cx="8" cy="8" r="6"/><path d="M8 4.5 V8 L10.5 9.5"/>',
    "trash": '<path d="M3 4.5 H13"/><path d="M6 4.5 V2.5 H10 V4.5"/><path d="M4.5 4.5 L5.5 14 H10.5 L11.5 4.5"/>',
    "bookmark": '<path d="M4 2 H12 V14 L8 10.5 L4 14 Z"/>',
    "drive": '<rect x="2" y="5" width="12" height="6"/><path d="M10.5 8 H11.5"/>',
    "removable": '<rect x="4.5" y="5" width="7" height="9"/><path d="M6 5 V2 H10 V5"/>',
    "optical": '<circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="1.5"/>',
    "computer": '<rect x="2" y="2.5" width="12" height="8"/><path d="M5 14 H11 M8 10.5 V14"/>',
    "network": '<circle cx="8" cy="3.5" r="1.5"/><circle cx="3.5" cy="12.5" r="1.5"/><circle cx="12.5" cy="12.5" r="1.5"/>'
               '<path d="M8 5 V8 M8 8 L4.5 11 M8 8 L11.5 11"/>',
}


def sym16(key):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none" '
            f'stroke="{SIDE}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">{SYM[key]}</svg>\n')


SIDEBAR = {
    "places": {
        "home": ["user-home", "folder-home", "go-home"], "desktop": ["user-desktop"], "documents": ["folder-documents"],
        "downloads": ["folder-download"], "music": ["folder-music"], "pictures": ["folder-pictures"],
        "videos": ["folder-videos"], "templates": ["folder-templates"], "share": ["folder-publicshare"],
        "folder": ["folder", "inode-directory", "folder-open", "folder-drag-accept", "folder-visiting"],
        "recent": ["document-open-recent", "folder-recent"], "trash": ["user-trash", "user-trash-full"],
        "bookmark": ["user-bookmarks", "bookmark-new"], "network": ["folder-remote", "network-workgroup", "network-server"],
    },
    "devices": {
        "drive": ["drive-harddisk", "drive-harddisk-system", "drive-multidisk"],
        "removable": ["drive-removable-media", "drive-harddisk-usb", "media-removable", "media-flash"],
        "optical": ["drive-optical", "media-optical"], "computer": ["computer", "video-display"],
    },
}
for ctx, groups in SIDEBAR.items():
    for key, names in groups.items():
        write(f"16/{ctx}", sym16(key), names)

(ROOT / "index.theme").write_text(f"""[Icon Theme]
Name={NAME}
Comment=Sumi yoru: ink-wash folders, hand-inked paper documents, plain 16px line icons
Inherits=Adwaita,hicolor
Example=folder

Directories=16/places,16/devices,scalable/places,scalable/mimetypes,scalable/devices

[16/places]
Size=16
Context=Places
Type=Fixed

[16/devices]
Size=16
Context=Devices
Type=Fixed

[scalable/places]
Size=64
MinSize=20
MaxSize=512
Context=Places
Type=Scalable

[scalable/mimetypes]
Size=64
MinSize=16
MaxSize=512
Context=MimeTypes
Type=Scalable

[scalable/devices]
Size=64
MinSize=20
MaxSize=512
Context=Devices
Type=Scalable
""")
subprocess.run(["gtk-update-icon-cache", "-f", "-t", str(ROOT)], check=False,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"{NAME} icons written to {ROOT}")
