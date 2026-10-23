"""World 1-4 - MOUNTAIN MAN: a huge, wild, brown beard full of twigs and snow."""
import math


def headwear(mb, cx, z, cols):
    """Chunky knit wool hat with a fold-up cuff and a big pompom."""
    mb.box((cols + 0.3, 0.1, 0.72), (cx, -0.45, z + 0.3), "acc2")
    for k in range(int(cols + 1) * 2):                                # knit ribs
        mb.box((0.1, 0.12, 0.7), (cx - (cols + 0.3) / 2 + 0.25 + k * 0.5, -0.51, z + 0.3), "pants")
    mb.box((cols + 0.5, 0.14, 0.3), (cx, -0.55, z - 0.05), "acc2")    # cuff
    mb.box((cols + 0.5, 0.15, 0.06), (cx, -0.58, z + 0.06), "white")
    mb.disc(0.34, (cx, -0.5, z + 0.82), "white", seg=10, depth=0.2)   # pompom (sits under the image top)


def rock(mb):
    mb.disc(0.3, (0, 0, 0), "acc1", seg=7, depth=0.3, sz=0.8)
    mb.disc(0.17, (-0.12, -0.12, 0.07), "white", seg=6, depth=0.04, sz=0.6)    # highlight
    mb.disc(0.12, (0.13, -0.13, -0.08), "hair1", seg=6, depth=0.04)             # dent
    mb.box((0.18, 0.02, 0.03), (0.04, -0.17, 0.12), "hair1", ry=25)             # crack


def snowball(mb):
    mb.disc(0.28, (0, 0, 0), "white", seg=12, depth=0.3)
    mb.disc(0.2, (0.06, -0.12, -0.06), "acc3", seg=10, depth=0.04)              # pale shade (lower right)
    for x, z in ((-0.12, 0.12), (0.1, 0.04), (-0.04, -0.12)):
        mb.box((0.05, 0.02, 0.05), (x, -0.16, z), "acc2")                        # icy flecks


def frying_pan(mb):
    mb.disc(0.26, (-0.12, 0, 0), "black", seg=12, depth=0.1)
    mb.disc(0.2, (-0.12, -0.05, 0), "hair1", seg=12, depth=0.02)
    mb.disc(0.1, (-0.08, -0.06, 0.02), "acc3", seg=8, depth=0.02)               # an egg yolk
    mb.disc(0.15, (-0.15, -0.055, -0.02), "white", seg=10, depth=0.015)
    mb.bar((0.12, 0.0), (0.5, 0.06), 0.09, 0, "black")                          # handle
    mb.disc(0.04, (0.46, -0.06, 0.06), "acc1", seg=6, depth=0.02)


def fish(mb):
    mb.disc(0.2, (-0.05, 0, 0), "acc2", seg=10, depth=0.16, sz=0.6)            # body
    mb.box((0.36, 0.17, 0.12), (-0.03, 0, 0), "acc2")
    mb.box((0.34, 0.18, 0.05), (-0.02, -0.01, -0.06), "white")                  # belly
    for s in (-1, 1):
        mb.bar((0.18, 0.0), (0.36, s * 0.14), 0.09, 0, "pants")                 # tail
    mb.disc(0.05, (-0.2, -0.1, 0.04), "white", seg=6, depth=0.02)               # eye
    mb.disc(0.025, (-0.21, -0.12, 0.04), "black", seg=6, depth=0.02)
    mb.box((0.12, 0.02, 0.04), (-0.27, -0.09, -0.04), "lips")                    # silly mouth


LEVEL = {
    "title": "1-4 MOUNTAIN MAN",
    "seed": 31,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#eab08c", "skin_shade": "#b8785c",
        "lips": "#a84838", "shirt": "#e83828", "pants": "#28408c", "cap": "#f8b800",
        "bg": "#1a2a3c",
        "hair1": "#3a2414", "hair2": "#6a4426", "hair3": "#946238", "hair4": "#bc8a56",
        "acc1": "#848890", "acc2": "#4c88c8", "acc3": "#cfd8e8",
    },
    "style": "wavy", "wave_amp": 0.13, "wave_period": 1.2,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair1"],
    "tile_weights": {"normal": 0.46, "normal2": 0.18, "knot": 0.11, "hold": 0.08, "sparse": 0.045, "decor": 0.12},
    "holds": ["twig"], "decor": "snow",
    "mustache": "bushy", "brows": "bushy", "cheeks": True,
    "headwear": headwear,
    "hazards": [("rock", rock), ("snowball", snowball), ("frying_pan", frying_pan), ("fish", fish)],
    "enemy": None, "fx": None,
    "rows": 28, "tip": "ragged", "taper_rows": 3.2, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "lips", "hardhat": "cap", "hardhat_shade": "hair4"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
