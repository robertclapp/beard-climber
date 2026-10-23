"""World 3-3 - RAPUNZEL: climb her long golden braid up the tower (the braid is narrow: stone walls either side)."""
import math


def headwear(mb, cx, z, cols):
    """A little gold tiara with a pink gem, on top of golden hair."""
    mb.box((cols - 0.4, 0.1, 0.7), (cx, -0.4, z + 0.15), "hair3")
    for k in range(5):
        x = cx - 1.0 + k * 0.5
        mb.bar((x, z - 0.15), (x, z + 0.25 + 0.2 * (k == 2)), 0.14, -0.5, "cap")
    mb.box((2.4, 0.12, 0.14), (cx, -0.52, z - 0.18), "cap")
    mb.disc(0.12, (cx, -0.56, z + 0.22), "acc2", seg=8, depth=0.04)


def face_extra(mb, cx, ez, cols):
    """Long lashes, rosy cheeks, a small nose; golden hair framing the face."""
    for s in (-1, 1):
        ex = cx + s * 1.2
        for k in range(3):
            mb.bar((ex - 0.25 + k * 0.25, ez + 0.2), (ex - 0.3 + k * 0.3, ez + 0.38), 0.05, -0.12, "black")
        mb.disc(0.32, (cx + s * 1.45, -0.04, ez - 0.85), "acc2", depth=0.04)
        mb.bar((cx + s * 2.2, ez + 0.9), (cx + s * 2.4, ez - 1.6), 0.5, -0.3, "hair3")
    mb.box((1.2, 0.06, 0.18), (cx, -0.3, ez - 1.5), "lips")                         # cover the beard-man mouth top


def flowerpot(mb):
    mb.box((0.42, 0.3, 0.34), (0, 0, -0.12), "acc3")
    mb.box((0.5, 0.32, 0.08), (0, 0, 0.06), "acc3")
    for x, c in ((-0.12, "acc2"), (0.0, "cap"), (0.13, "acc2")):
        mb.bar((x * 0.5, 0.1), (x, 0.32), 0.04, 0, "acc4")
        mb.disc(0.08, (x, -0.04, 0.34), c, seg=8, depth=0.05)


def frying_pan(mb):
    mb.disc(0.26, (-0.12, 0, 0), "black", seg=12, depth=0.1)
    mb.disc(0.2, (-0.12, -0.05, 0), "hair1", seg=12, depth=0.02)
    mb.bar((0.12, 0.0), (0.5, 0.06), 0.09, 0, "black")


def teacup(mb):
    mb.box((0.36, 0.3, 0.28), (0, 0, 0), "white")
    mb.box((0.38, 0.32, 0.05), (0, 0, 0.08), "acc2")
    mb.box((0.5, 0.3, 0.05), (0, 0, -0.16), "white")                                 # saucer
    mb.bar((0.18, 0.06), (0.28, -0.04), 0.06, 0, "white")


def yarn(mb):
    mb.disc(0.26, (0, 0, 0), "acc2", seg=12, depth=0.26)
    for k in range(3):
        mb.bar((-0.2, -0.12 + k * 0.12), (0.2, 0.0 + k * 0.12), 0.03, -0.14, "white")
    mb.bar((0.2, -0.16), (0.4, -0.36), 0.03, 0, "acc2")


LEVEL = {
    "title": "3-3 RAPUNZEL",
    "seed": 77,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f8d0b8", "skin_shade": "#e89c8c",
        "lips": "#d85070", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8c830",
        "bg": "#5c5868",
        "hair1": "#b07818", "hair2": "#d8a030", "hair3": "#f0c850", "hair4": "#f8e488",
        "acc1": "#7c7888", "acc2": "#f080b0", "acc3": "#c86838", "acc4": "#4c9c50",
    },
    "style": "wavy", "wave_amp": 0.05, "wave_period": 1.6,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair3", "hair2"],
    "braid_cols": [1, 2, 3, 4],
    "tile_weights": {"normal": 0.54, "normal2": 0.12, "knot": 0.12, "hold": 0.0, "sparse": 0.04, "decor": 0.18},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "acc2",                      # flower petals
    "mustache": "none", "brows": "thin", "cheeks": False,
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("flowerpot", flowerpot), ("frying_pan", frying_pan), ("teacup", teacup), ("yarn", yarn)],
    "enemy": None, "fx": None,
    "rows": 30, "tip": "round", "taper_rows": 2.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc2", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
