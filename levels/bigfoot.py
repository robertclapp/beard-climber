"""World 1-5 (BOSS) - BIGFOOT: climb his shaggy chest fur up to a big, shy, furry face."""
import math


def headwear(mb, cx, z, cols):
    """A shaggy fur crown: pointed tufts all over the top of his head, little round ears."""
    mb.box((cols - 0.4, 0.1, 0.9), (cx, -0.4, z + 0.25), "hair2")
    for k in range(9):                                              # tufts
        x = cx - 2.1 + k * 0.52
        h = 0.45 + 0.2 * ((k * 5) % 3)
        mb.bar((x - 0.2, z + 0.2), (x + 0.05, z + 0.2 + h), 0.22, -0.46, "hair3" if k % 2 else "hair4")
        mb.bar((x, z + 0.1), (x + 0.12, z + 0.1 + h * 0.6), 0.12, -0.5, "hair2")
    for s in (-1, 1):
        mb.disc(0.3, (cx + s * 2.55, -0.3, z - 0.9), "hair2", seg=8, depth=0.12)
        mb.disc(0.16, (cx + s * 2.55, -0.36, z - 0.9), "skin_shade", seg=8, depth=0.04)


def face_extra(mb, cx, ez, cols):
    """Heavy fur brow ridge + a wide flat nose (he's a big softie)."""
    mb.box((3.6, 0.08, 0.32), (cx, -0.16, ez + 0.5), "hair2")
    mb.box((1.3, 0.1, 0.4), (cx, -0.32, ez - 0.62), "skin_shade")
    for s in (-1, 1):
        mb.box((0.22, 0.05, 0.14), (cx + s * 0.3, -0.38, ez - 0.7), "black")


def pinecone(mb):
    for k in range(5):
        w = 0.24 + 0.22 * math.sin(math.pi * (k + 0.5) / 5)
        z = -0.24 + k * 0.12
        mb.box((w, 0.24, 0.11), (0, 0, z), "hair1" if k % 2 else "hair3")
        for s in (-1, 1):
            mb.box((0.07, 0.02, 0.05), (s * w * 0.3, -0.13, z + 0.02), "hair4")
    mb.bar((0, 0.34), (0.05, 0.46), 0.05, 0, "acc2")


def marshmallow(mb):
    """A toasty campfire marshmallow on a stick."""
    mb.bar((-0.4, -0.3), (0.05, 0.05), 0.05, 0, "hair2")                  # stick
    mb.box((0.3, 0.26, 0.34), (0.16, 0, 0.16), "white")
    mb.box((0.3, 0.27, 0.1), (0.16, 0, 0.3), "acc3")                       # toasted top
    mb.box((0.06, 0.02, 0.18), (0.08, -0.14, 0.12), "acc3")


def camera(mb):
    mb.box((0.62, 0.26, 0.38), (0, 0, 0), "acc1")
    mb.box((0.22, 0.26, 0.1), (-0.14, 0, 0.23), "acc1")                    # viewfinder hump
    mb.disc(0.15, (0.04, -0.14, -0.02), "black", seg=10, depth=0.06)       # lens
    mb.disc(0.09, (0.04, -0.18, -0.02), "acc2", seg=10, depth=0.03)
    mb.box((0.04, 0.02, 0.04), (0.0, -0.21, 0.02), "white")
    mb.box((0.12, 0.02, 0.08), (0.2, -0.14, 0.12), "white")                 # flash
    mb.box((0.1, 0.1, 0.05), (0.2, 0, 0.21), "black")                      # shutter button


def tent_pole(mb):
    mb.bar((-0.45, -0.3), (0.45, 0.3), 0.07, 0, "acc1")
    for t in (-0.15, 0.15):
        mb.bar((t * 3 - 0.03, t * 2 - 0.02), (t * 3 + 0.03, t * 2 + 0.02), 0.11, -0.01, "black")   # joints
    mb.box((0.1, 0.1, 0.1), (0.46, 0, 0.31), "acc3")                       # end caps
    mb.box((0.1, 0.1, 0.1), (-0.46, 0, -0.31), "acc3")


LEVEL = {
    "title": "1-5 BIGFOOT",
    "seed": 44,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#a88a78", "skin_shade": "#7a5e52",
        "lips": "#5c3030", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#0e2216",
        "hair1": "#2a1a12", "hair2": "#4c3020", "hair3": "#6e4a30", "hair4": "#946a44",
        "acc1": "#c84032", "acc2": "#3c7c42", "acc3": "#e8a868",
    },
    "style": "wavy", "wave_amp": 0.15, "wave_period": 1.0,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair1"],
    "tile_weights": {"normal": 0.47, "normal2": 0.2, "knot": 0.1, "hold": 0.07, "sparse": 0.05, "decor": 0.11},
    "holds": ["twig"], "decor": "crumbs", "crumb_role": "acc2",          # leaves caught in the fur
    "mustache": "bushy", "brows": "bushy",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("pinecone", pinecone), ("marshmallow", marshmallow), ("camera", camera), ("tent_pole", tent_pole)],
    "enemy": None, "fx": None,
    "rows": 30, "tip": "ragged", "taper_rows": 3.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 8, "drift": 0.09,
}
