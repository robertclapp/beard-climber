"""World 3-4 - THE DWARF KING: a huge braided dark-red beard full of gems, deep under the mountain."""
import math


def headwear(mb, cx, z, cols):
    """No crown (he lost it!): a bald bump of a head with tufts of red hair at the sides."""
    mb.box((cols - 1.2, 0.08, 0.7), (cx, -0.3, z + 0.1), "skin")
    mb.box((0.8, 0.02, 0.12), (cx - 0.6, -0.36, z + 0.25), "white")
    for s in (-1, 1):
        for k in range(3):
            mb.bar((cx + s * (2.1 + k * 0.2), z - 0.2), (cx + s * (2.4 + k * 0.25), z + 0.4), 0.18, -0.45, "hair3" if k % 2 else "hair2")


def face_extra(mb, cx, ez, cols):
    """A big round nose and heavy brows."""
    mb.disc(0.5, (cx, -0.34, ez - 0.72), "skin_shade", seg=12, depth=0.12)


def pickaxe(mb):
    mb.bar((-0.3, -0.36), (0.2, 0.24), 0.08, 0, "acc3")
    for s in (-1, 1):
        mb.bar((0.18, 0.24), (0.18 + s * 0.3, 0.24 - 0.12 * (s + 1) * 0.5 - 0.06), 0.08, -0.02, "acc1")
    mb.box((0.1, 0.12, 0.1), (0.18, 0, 0.24), "black")


def mine_cart(mb):
    mb.box((0.56, 0.3, 0.28), (0, 0, 0.02), "acc1")
    mb.box((0.6, 0.32, 0.06), (0, 0, 0.18), "black")
    for x in (-0.18, 0.18):
        mb.disc(0.09, (x, -0.16, -0.16), "black", seg=8, depth=0.05)
    for x, c in ((-0.12, "acc2"), (0.04, "cap"), (0.16, "acc2")):
        mb.disc(0.08, (x, -0.06, 0.24), c, seg=6, depth=0.06)


def rock(mb):
    mb.disc(0.3, (0, 0, 0), "acc1", seg=7, depth=0.3, sz=0.8)
    mb.disc(0.17, (-0.12, -0.12, 0.07), "hair4", seg=6, depth=0.04, sz=0.6)


def tankard(mb):
    mb.box((0.36, 0.3, 0.44), (-0.04, 0, -0.02), "acc3")
    for z in (-0.16, 0.12):
        mb.box((0.38, 0.32, 0.04), (-0.04, 0, z), "acc1")
    mb.box((0.38, 0.32, 0.1), (-0.04, 0, 0.24), "white")                             # foam (root beer!)
    mb.bar((0.16, -0.12), (0.28, 0.1), 0.07, 0, "acc1")


LEVEL = {
    "title": "3-4 THE DWARF KING",
    "seed": 81,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#e8a888", "skin_shade": "#c06c58",
        "lips": "#8c3030", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8c830",
        "bg": "#14101c",
        "hair1": "#5c1810", "hair2": "#8c2818", "hair3": "#b84424", "hair4": "#d86c3c",
        "acc1": "#686c78", "acc2": "#40c0e0", "acc3": "#8c5c30",
    },
    "style": "wavy", "wave_amp": 0.1, "wave_period": 1.0,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair1"],
    "braid_cols": [1, 4],
    "tile_weights": {"normal": 0.47, "normal2": 0.16, "knot": 0.12, "hold": 0.08, "sparse": 0.05, "decor": 0.12},
    "holds": ["bead"], "decor": "beads",
    "mustache": "bushy", "brows": "bushy", "cheeks": True,
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("pickaxe", pickaxe), ("mine_cart", mine_cart), ("rock", rock), ("tankard", tankard)],
    "enemy": None, "fx": None,
    "rows": 30, "tip": "braids", "taper_rows": 3.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc2", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
