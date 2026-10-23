"""World 2-4 - THE YETI: Bigfoot's big, fluffy, frosty snow cousin. Climb his shaggy white-and-blue chest fur."""
import math


def headwear(mb, cx, z, cols):
    """A huge round fluffy white head-tuft and little icy-blue horns."""
    for k in range(11):
        x = cx - 2.5 + k * 0.5
        mb.disc(0.42 + 0.1 * (k % 2), (x, -0.45, z + 0.35 + 0.15 * (k % 3)), "white" if k % 2 else "hair4", seg=9, depth=0.18)
    for s in (-1, 1):
        mb.bar((cx + s * 1.6, z + 0.5), (cx + s * 2.0, z + 1.3), 0.24, -0.5, "acc2")
        mb.bar((cx + s * 2.0, z + 1.3), (cx + s * 1.8, z + 1.55), 0.16, -0.5, "acc2")


def face_extra(mb, cx, ez, cols):
    """Blue-grey face patch with a fluffy white brow, a big friendly dark nose, rosy-blue cheeks."""
    mb.box((3.8, 0.08, 0.36), (cx, -0.16, ez + 0.5), "white")
    mb.disc(0.42, (cx, -0.34, ez - 0.72), "black", seg=10, depth=0.1, sz=0.7)
    mb.disc(0.12, (cx - 0.14, -0.42, ez - 0.64), "skin", seg=6, depth=0.02)
    for s in (-1, 1):
        mb.disc(0.3, (cx + s * 1.45, -0.04, ez - 0.9), "acc3", depth=0.04)


def snowball(mb):
    mb.disc(0.28, (0, 0, 0), "white", seg=12, depth=0.3)
    mb.disc(0.2, (0.06, -0.12, -0.06), "hair3", seg=10, depth=0.04)


def icicle(mb):
    mb.bar((0, 0.36), (0.02, -0.4), 0.2, 0, "acc2")
    mb.bar((0.04, 0.32), (0.03, -0.1), 0.07, -0.08, "white")
    mb.box((0.34, 0.2, 0.08), (0, 0, 0.36), "hair4")


def mug(mb):
    mb.box((0.38, 0.32, 0.44), (-0.04, 0, -0.02), "acc1")
    mb.box((0.38, 0.33, 0.06), (-0.04, 0, 0.12), "white")                        # stripe
    mb.box((0.32, 0.28, 0.06), (-0.04, 0, 0.22), "lips")                         # cocoa
    for z in (-0.12, 0.08):
        mb.bar((0.15, z), (0.27, z), 0.07, 0, "acc1")
    mb.bar((0.27, -0.12), (0.27, 0.08), 0.07, 0, "acc1")
    mb.box((0.1, 0.1, 0.1), (-0.1, -0.02, 0.28), "white")                        # marshmallow


def ski(mb):
    mb.bar((-0.42, -0.34), (0.38, 0.3), 0.14, 0, "acc4")
    mb.bar((0.38, 0.3), (0.44, 0.42), 0.12, 0, "acc4")                              # curled tip
    mb.bar((-0.2, -0.16), (0.16, 0.13), 0.04, -0.08, "white")
    mb.box((0.2, 0.18, 0.12), (0.0, -0.02, 0.0), "black", ry=-38)                   # binding


LEVEL = {
    "title": "2-4 THE YETI",
    "seed": 66,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#9cb0c8", "skin_shade": "#6c8098",
        "lips": "#6c3c28", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#162a40",
        "hair1": "#788ca8", "hair2": "#a4b6cc", "hair3": "#cad8e6", "hair4": "#e8f0f8",
        "acc1": "#3878d0", "acc2": "#58c0e8", "acc3": "#88a8d8", "acc4": "#e8504c",
    },
    "style": "fluffy", "wave_amp": 0.06, "wave_period": 1.3,
    "strand_pattern": ["hair3", "hair2", "white", "hair3", "hair1"],
    "tile_weights": {"normal": 0.5, "normal2": 0.16, "knot": 0.1, "hold": 0.0, "sparse": 0.06, "decor": 0.18},
    "holds": ["knot"], "decor": "snow",
    "mustache": "none", "brows": "bushy",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("snowball", snowball), ("icicle", icicle), ("mug", mug), ("ski", ski)],
    "enemy": None, "fx": None,
    "rows": 30, "tip": "ragged", "taper_rows": 3.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc4", "hardhat": "cap", "hardhat_shade": "lips"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 8, "drift": 0.09,
}
