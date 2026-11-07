"""World 2-2 - RUDOLPH: climb a giant reindeer's shaggy neck mane up to his big (dim, sad) red nose."""
import math


def headwear(mb, cx, z, cols):
    """Branching antlers + furry ears (no hat)."""
    for s in (-1, 1):
        base = (cx + s * 1.2, z - 0.45)
        tip = (cx + s * 2.9, z + 0.35)
        mb.bar(base, tip, 0.28, -0.42, "acc3")
        for k, (a, b) in enumerate(((0.3, 0.9), (0.55, 1.0), (0.8, 0.75))):
            p = (base[0] + (tip[0] - base[0]) * a, base[1] + (tip[1] - base[1]) * a)
            mb.bar(p, (p[0] - s * 0.1, p[1] + b * 0.5), 0.22, -0.44, "acc4" if k % 2 else "acc3")
        mb.bar((cx + s * 2.1, z - 0.7), (cx + s * 2.9, z - 0.35), 0.4, -0.38, "hair2")   # ears
        mb.bar((cx + s * 2.15, z - 0.66), (cx + s * 2.75, z - 0.42), 0.18, -0.42, "skin_shade")


def face_extra(mb, cx, ez, cols):
    """A pale muzzle and the BIG round nose (dim dark red - it glows again in the ending)."""
    mb.disc(1.05, (cx, -0.26, ez - 1.05), "acc4", seg=14, depth=0.04, sz=0.75)         # muzzle
    mb.disc(0.62, (cx, -0.34, ez - 0.75), "acc1", seg=14, depth=0.12)                 # nose
    mb.disc(0.2, (cx - 0.2, -0.48, ez - 0.55), "skin_shade", seg=8, depth=0.02)       # dull highlight


def sleigh_bell(mb):
    for x in (-0.18, 0.18):
        mb.disc(0.17, (x, 0, -0.06), "cap", seg=10, depth=0.18)
        mb.box((0.18, 0.02, 0.03), (x, -0.1, -0.08), "black")
    mb.box((0.62, 0.12, 0.1), (0, 0, 0.14), "lips")                                  # leather strap
    for x in (-0.24, 0.0, 0.24):
        mb.box((0.04, 0.02, 0.04), (x, -0.07, 0.14), "cap")


def carrot(mb):
    mb.bar((-0.3, -0.32), (0.18, 0.22), 0.22, 0, "shirt")
    mb.bar((-0.3, -0.32), (-0.05, -0.04), 0.12, -0.02, "shirt")
    for k in range(3):
        mb.box((0.1, 0.02, 0.03), (-0.1 + k * 0.1, -0.12, -0.12 + k * 0.1), "lips", ry=40)
    for a in (-0.12, 0.0, 0.12):
        mb.bar((0.18, 0.22), (0.28 + a, 0.42 - a * 0.5), 0.07, 0, "acc2")


def snow_clump(mb):
    for x, z, r in ((0, 0, 0.24), (-0.16, -0.06, 0.16), (0.17, -0.04, 0.17), (0.04, 0.16, 0.15)):
        mb.disc(r, (x, 0, z), "white", seg=10, depth=0.24)
    mb.disc(0.12, (0.08, -0.13, -0.08), "hair4", seg=8, depth=0.03)


def hoofprint(mb):
    """A big muddy-snow hoofprint stomp (two halves of a cloven hoof)."""
    for s in (-1, 1):
        mb.disc(0.17, (s * 0.12, 0, 0.02), "hair1", seg=10, depth=0.16, sz=1.5)
        mb.disc(0.1, (s * 0.12, -0.09, 0.08), "hair2", seg=8, depth=0.02)
    for x, z in ((-0.3, 0.3), (0.32, 0.26), (0.0, -0.36)):
        mb.box((0.08, 0.06, 0.08), (x, 0, z), "white")


LEVEL = {
    "title": "2-2 RUDOLPH",
    "seed": 58,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#9c6038", "skin_shade": "#6c3c20",
        "lips": "#5c2c18", "shirt": "#f07828", "pants": "#28408c", "cap": "#f8c830",
        "bg": "#0c1430",
        "hair1": "#4a2814", "hair2": "#74421e", "hair3": "#9c6236", "hair4": "#c48c58",
        "acc1": "#8a2a30", "acc2": "#3c9a40", "acc3": "#d8c098", "acc4": "#f0dcc0",
    },
    "style": "wavy", "wave_amp": 0.11, "wave_period": 1.1,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair1"],
    "tile_weights": {"normal": 0.48, "normal2": 0.2, "knot": 0.1, "hold": 0.0, "sparse": 0.05, "decor": 0.12},
    "holds": ["knot"], "decor": "snow",
    "mustache": "none", "brows": "thin",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("sleigh_bell", sleigh_bell), ("carrot", carrot), ("snow_clump", snow_clump), ("hoofprint", hoofprint)],
    "enemy": None, "fx": None,
    "rows": 28, "tip": "ragged", "taper_rows": 2.4, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "shirt", "hardhat": "cap", "hardhat_shade": "hair4"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
