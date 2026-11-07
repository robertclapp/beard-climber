"""World 3-2 - RUMPELSTILTSKIN: a cranky little-big man with a long wiry straw-gold beard (it spins into gold)."""
import math


def headwear(mb, cx, z, cols):
    """A tall crumpled brown hat with a long feather."""
    mb.box((cols + 0.2, 0.1, 0.55), (cx, -0.45, z - 0.05), "acc1")
    mb.box((cols - 0.8, 0.1, 0.6), (cx + 0.3, -0.45, z + 0.5), "acc1")
    mb.box((cols + 0.25, 0.12, 0.12), (cx, -0.52, z - 0.18), "acc3")
    mb.bar((cx + 1.6, z - 0.1), (cx + 3.0, z + 0.9), 0.22, -0.55, "acc2")              # feather
    mb.bar((cx + 1.7, z - 0.05), (cx + 2.9, z + 0.85), 0.06, -0.58, "white")


def face_extra(mb, cx, ez, cols):
    """A long pointy nose and big pointy ears."""
    mb.bar((cx, ez - 0.35), (cx + 0.55, ez - 1.05), 0.42, -0.32, "skin_shade")
    for s in (-1, 1):
        mb.bar((cx + s * 2.0, ez - 0.4), (cx + s * 2.9, ez + 0.4), 0.4, -0.5, "skin")


def straw(mb):
    for k, a in enumerate((-0.3, -0.15, 0.0, 0.15, 0.3)):
        mb.bar((a * 0.4, -0.36), (a, 0.36), 0.06, -0.01 * k, "hair3" if k % 2 else "hair4")
    mb.box((0.3, 0.2, 0.08), (0, 0, -0.06), "acc1")                                 # twine


def spindle(mb):
    mb.bar((0, -0.42), (0, 0.42), 0.07, 0, "acc1")
    mb.disc(0.16, (0, 0, 0.04), "hair2", seg=10, depth=0.18, sz=1.5)               # thread wound on it
    mb.box((0.36, 0.02, 0.04), (0, -0.14, 0.04), "hair4")
    mb.box((0.14, 0.12, 0.06), (0, 0, -0.36), "acc3")


def stool(mb):
    mb.box((0.56, 0.3, 0.1), (0, 0, 0.18), "acc1")
    for s in (-1, 1):
        mb.bar((s * 0.18, 0.14), (s * 0.28, -0.32), 0.07, 0, "acc3")
    mb.box((0.4, 0.04, 0.04), (0, -0.04, -0.12), "acc3")


def spinning_wheel(mb):
    mb.disc(0.3, (0, 0, 0.08), "acc1", seg=12, depth=0.04)
    mb.disc(0.24, (0, -0.03, 0.08), "bg", seg=12, depth=0.02)
    for k in range(4):
        a = k * math.pi / 4
        mb.bar((-0.24 * math.cos(a), 0.08 - 0.24 * math.sin(a)), (0.24 * math.cos(a), 0.08 + 0.24 * math.sin(a)), 0.04, -0.05, "acc3")
    mb.bar((-0.2, -0.36), (0.2, -0.36), 0.07, 0, "acc1")
    mb.disc(0.06, (0, -0.06, 0.08), "hair4", seg=6, depth=0.04)


LEVEL = {
    "title": "3-2 RUMPELSTILTSKIN",
    "seed": 74,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#e8b090", "skin_shade": "#c07860",
        "lips": "#9c3c38", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#24183a",
        "hair1": "#8c6418", "hair2": "#c08c28", "hair3": "#e0b848", "hair4": "#f8e078",
        "acc1": "#7c4a24", "acc2": "#d83838", "acc3": "#b88848",
    },
    "style": "wavy", "wave_amp": 0.16, "wave_period": 0.55,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair3", "hair1", "hair2"],
    "tile_weights": {"normal": 0.48, "normal2": 0.2, "knot": 0.12, "hold": 0.0, "sparse": 0.05, "decor": 0.15},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "cap",                       # gold glitter
    "mustache": "thin_curl", "brows": "bushy",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("straw", straw), ("spindle", spindle), ("stool", stool), ("spinning_wheel", spinning_wheel)],
    "enemy": None, "fx": None,
    "rows": 28, "tip": "point", "taper_rows": 3.4, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc2", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
