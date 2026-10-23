"""World 3-1 - THE GARDEN GNOME: a giant garden gnome with a red pointy hat and a big white bushy beard."""
import math


def headwear(mb, cx, z, cols):
    """The red pointy gnome hat, pulled low over the brows."""
    for k in range(7):
        w = (cols + 0.6) * (1 - k / 7.5)
        mb.box((w, 0.1, 0.34), (cx, -0.45, z - 0.25 + k * 0.32), "acc1" if k % 2 else "lips")
    mb.box((cols + 0.8, 0.12, 0.22), (cx, -0.5, z - 0.32), "lips")


def face_extra(mb, cx, ez, cols):
    """A round red button nose + rosy cheeks."""
    mb.disc(0.5, (cx, -0.34, ez - 0.7), "skin_shade", seg=12, depth=0.12)
    mb.disc(0.14, (cx - 0.15, -0.46, ez - 0.55), "white", seg=6, depth=0.02)


def watering_can(mb):
    mb.box((0.42, 0.3, 0.34), (0, 0, -0.04), "acc2")
    mb.bar((0.2, 0.0), (0.46, 0.24), 0.08, 0, "acc2")                              # spout
    mb.box((0.12, 0.1, 0.06), (0.48, 0, 0.27), "acc3")
    mb.bar((-0.2, 0.1), (-0.12, 0.3), 0.06, 0, "acc2"); mb.bar((-0.12, 0.3), (0.12, 0.3), 0.06, 0, "acc2")
    mb.box((0.3, 0.02, 0.06), (0, -0.16, -0.04), "white")
    for k in range(3):
        mb.box((0.04, 0.02, 0.06), (0.52 + k * 0.04, -0.02, 0.34 + k * 0.06), "acc3")   # water drops


def snail(mb):
    mb.disc(0.24, (0.04, 0, 0.06), "acc3", seg=12, depth=0.24)                     # shell
    mb.disc(0.15, (0.04, -0.12, 0.06), "hair1", seg=10, depth=0.02)
    mb.disc(0.07, (0.04, -0.14, 0.06), "acc3", seg=8, depth=0.02)
    mb.bar((-0.34, -0.2), (0.3, -0.2), 0.12, 0, "skin")                            # body
    for x in (-0.3, -0.22):
        mb.bar((x, -0.14), (x - 0.04, 0.04), 0.03, -0.02, "skin")                  # eye stalks
        mb.box((0.05, 0.03, 0.05), (x - 0.04, -0.05, 0.05), "black")


def acorn(mb):
    mb.disc(0.2, (0, 0, -0.08), "acc3", seg=10, depth=0.24, sz=1.3)
    mb.box((0.46, 0.26, 0.16), (0, 0, 0.14), "hair1")                              # cap
    for x in (-0.12, 0.0, 0.12):
        mb.box((0.06, 0.02, 0.04), (x, -0.14, 0.15), "acc1")
    mb.bar((0, 0.22), (0.06, 0.34), 0.05, 0, "hair1")
    mb.box((0.06, 0.02, 0.12), (-0.08, -0.14, -0.06), "white")


def trowel(mb):
    mb.bar((-0.34, -0.3), (-0.06, -0.02), 0.09, 0, "lips")                         # handle
    mb.disc(0.18, (0.14, 0, 0.16), "hair3", seg=8, depth=0.05, sz=1.4)
    mb.box((0.04, 0.02, 0.18), (0.14, -0.04, 0.16), "white", ry=45)


LEVEL = {
    "title": "3-1 THE GARDEN GNOME",
    "seed": 71,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f8c8a0", "skin_shade": "#e07060",
        "lips": "#b82028", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#183018",
        "hair1": "#8890a0", "hair2": "#b8c0cc", "hair3": "#dce2ea", "hair4": "#f8f8f8",
        "acc1": "#e83030", "acc2": "#4c9c50", "acc3": "#c08840",
    },
    "style": "fluffy", "wave_amp": 0.05, "wave_period": 1.4,
    "strand_pattern": ["hair3", "hair2", "white", "hair3", "hair2"],
    "tile_weights": {"normal": 0.52, "normal2": 0.14, "knot": 0.12, "hold": 0.0, "sparse": 0.05, "decor": 0.17},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "acc2",                      # bits of grass + leaves
    "mustache": "bushy", "brows": "bushy", "cheeks": True,
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("watering_can", watering_can), ("snail", snail), ("acorn", acorn), ("trowel", trowel)],
    "enemy": None, "fx": None,
    "rows": 26, "tip": "round", "taper_rows": 3.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
