"""World 2-3 - THE ICE GIANT: a long pale-blue icicle beard (slippery, and it melts as you climb)."""
import math


def headwear(mb, cx, z, cols):
    """A jagged crown of ice spikes + frosty eyebrows of snow."""
    mb.box((cols - 0.2, 0.1, 0.4), (cx, -0.45, z - 0.3), "hair3")
    for k in range(9):
        x = cx - 2.4 + k * 0.6
        h = 0.6 + 0.5 * (k % 3 == 1) + 0.25 * (k % 2)
        mb.bar((x - 0.15, z - 0.2), (x, z - 0.2 + h), 0.26, -0.48, "hair4" if k % 2 else "white")
        mb.bar((x - 0.05, z - 0.15), (x, z - 0.25 + h * 0.8), 0.08, -0.52, "acc2")


def face_extra(mb, cx, ez, cols):
    """Frosty blue cheeks and little icicles hanging off the brows."""
    for s in (-1, 1):
        mb.disc(0.34, (cx + s * 1.45, -0.04, ez - 0.85), "acc2", depth=0.04)
        for k in range(3):
            x = cx + s * (0.85 + k * 0.28)
            mb.bar((x, ez + 0.35), (x + 0.02, ez + 0.05 - 0.08 * k), 0.08, -0.13, "white")


def icicle(mb):
    mb.bar((0, 0.36), (0.02, -0.4), 0.2, 0, "hair4")
    mb.bar((0.04, 0.32), (0.03, -0.1), 0.07, -0.08, "white")
    mb.box((0.34, 0.2, 0.08), (0, 0, 0.36), "hair3")


def snowball(mb):
    mb.disc(0.28, (0, 0, 0), "white", seg=12, depth=0.3)
    mb.disc(0.2, (0.06, -0.12, -0.06), "hair4", seg=10, depth=0.04)
    for x, z in ((-0.12, 0.12), (0.1, 0.04), (-0.04, -0.12)):
        mb.box((0.05, 0.02, 0.05), (x, -0.16, z), "acc2")


def frost_puff(mb):
    """A puff of frosty breath: a swirly little cloud with sparkles."""
    for x, z, r in ((0, 0, 0.2), (-0.18, 0.04, 0.15), (0.18, 0.06, 0.15), (0.06, 0.18, 0.13), (-0.08, -0.14, 0.12)):
        mb.disc(r, (x, 0, z), "hair4", seg=10, depth=0.18)
    mb.disc(0.12, (0, -0.1, 0.02), "white", seg=8, depth=0.03)
    for x, z in ((-0.3, 0.26), (0.32, -0.2), (0.0, 0.36)):
        mb.box((0.05, 0.03, 0.12), (x, -0.06, z), "white")
        mb.box((0.12, 0.03, 0.05), (x, -0.06, z), "white")


def ice_cube(mb):
    mb.box((0.46, 0.4, 0.42), (0, 0, 0), "hair3", ry=12)
    mb.box((0.34, 0.02, 0.06), (-0.02, -0.21, 0.1), "white", ry=12)
    mb.box((0.06, 0.02, 0.2), (-0.12, -0.21, -0.04), "white", ry=12)


LEVEL = {
    "title": "2-3 THE ICE GIANT",
    "seed": 61,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#c8e0f0", "skin_shade": "#88b0d0",
        "lips": "#5878b0", "shirt": "#e83828", "pants": "#203880", "cap": "#f8c830",
        "bg": "#0c1c34",
        "hair1": "#3c6c9c", "hair2": "#68a0cc", "hair3": "#98cce8", "hair4": "#cceaf8",
        "acc1": "#4c6c94", "acc2": "#7cb8e8", "acc3": "#e8f4fc",
    },
    "style": "wavy", "wave_amp": 0.03, "wave_period": 2.0,
    "strand_pattern": ["hair3", "hair4", "hair2", "hair3", "white", "hair2"],
    "tile_weights": {"normal": 0.5, "normal2": 0.12, "knot": 0.12, "hold": 0.0, "sparse": 0.08, "decor": 0.18},
    "holds": ["knot"], "decor": "snow",
    "mustache": "droop", "brows": "bushy",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("icicle", icicle), ("snowball", snowball), ("frost_puff", frost_puff), ("ice_cube", ice_cube)],
    "enemy": None, "fx": None,
    "rows": 24, "tip": "point", "taper_rows": 4.0, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "shirt", "hardhat": "cap", "hardhat_shade": "acc1"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
