"""World 1-2 - THE GOAT: a farmyard joke giant goat with a long, pointy white chin beard."""
import math


def headwear(mb, cx, z, cols):
    """Curved horns, floppy ears and a little forelock (no hat: he's a goat)."""
    for s in (-1, 1):
        for k in range(6):                                            # ridged horns curling out over the brow
            a = k / 5
            x0, z0 = cx + s * (0.55 + a * 1.5), z - 0.35 + math.sin(a * 2.4) * 0.6
            mb.disc(0.3 - a * 0.1, (x0, -0.46, z0), "hair1" if k % 2 else "acc1", seg=8, depth=0.12)
        mb.bar((cx + s * 1.9, z - 0.55), (cx + s * 2.65, z - 0.95), 0.36, -0.34, "skin_shade")   # floppy ears
        mb.bar((cx + s * 1.95, z - 0.6), (cx + s * 2.5, z - 0.9), 0.18, -0.38, "lips")
    for k in range(5):                                                # forelock tuft
        mb.bar((cx - 0.5 + k * 0.25, z + 0.1), (cx - 0.4 + k * 0.22, z - 0.35), 0.14, -0.4, "hair3" if k % 2 else "hair4")


def face_extra(mb, cx, ez, cols):
    """Goat eyes: sideways pupils. A pink muzzle with nostrils."""
    for s in (-1, 1):
        ex = cx + s * 1.2
        mb.box((0.5, 0.05, 0.22), (ex, -0.11, ez - 0.03), "acc3")            # golden iris
        mb.box((0.4, 0.05, 0.08), (ex, -0.12, ez - 0.03), "black")           # sideways pupil
    mb.box((1.1, 0.06, 0.5), (cx, -0.3, ez - 0.75), "lips")                  # muzzle
    for s in (-1, 1):
        mb.box((0.16, 0.05, 0.12), (cx + s * 0.25, -0.34, ez - 0.75), "black")


def tin_can(mb):
    mb.box((0.36, 0.3, 0.48), (0, 0, 0), "acc1")
    for z in (-0.16, 0.0, 0.16):
        mb.box((0.38, 0.32, 0.03), (0, 0, z), "hair1")                       # ribs
    mb.box((0.3, 0.02, 0.2), (0, -0.17, 0.02), "lips")                       # label
    mb.box((0.18, 0.02, 0.06), (0, -0.18, 0.04), "white")
    mb.box((0.3, 0.2, 0.04), (0.03, 0, 0.27), "white", ry=-12)               # lid, popped open


def hay_bale(mb):
    mb.box((0.72, 0.36, 0.44), (0, 0, 0), "acc3")
    for x in (-0.24, 0.02, 0.24):
        mb.box((0.03, 0.38, 0.46), (x, 0, 0), "cap")                         # straw lines
    for x in (-0.17, 0.17):
        mb.box((0.05, 0.4, 0.47), (x, 0, 0), "acc1")                         # twine
    for k in range(5):
        mb.bar((-0.3 + k * 0.15, 0.22), (-0.34 + k * 0.15, 0.32), 0.03, -0.18, "acc3")   # stray straws


def boot(mb):
    mb.box((0.32, 0.26, 0.42), (-0.1, 0, 0.1), "hair1")                      # shaft
    mb.box((0.62, 0.26, 0.22), (0.04, 0, -0.17), "hair1")                    # foot
    mb.disc(0.11, (0.34, 0, -0.17), "hair1", seg=8, depth=0.26)
    mb.box((0.66, 0.28, 0.07), (0.05, 0, -0.29), "black")                    # sole
    mb.box((0.34, 0.28, 0.06), (-0.1, 0, 0.31), "skin_shade")                # cuff
    for z in (0.02, 0.12, 0.22):
        mb.box((0.12, 0.02, 0.03), (0.03, -0.14, z), "acc3")                 # laces


def bell(mb):
    mb.disc(0.22, (0, 0, 0.06), "acc3", seg=10, depth=0.26)
    mb.box((0.52, 0.28, 0.12), (0, 0, -0.16), "acc3")                        # flared rim
    mb.box((0.56, 0.3, 0.04), (0, 0, -0.23), "cap")
    mb.disc(0.07, (0, -0.06, -0.28), "hair1", seg=6, depth=0.08)             # clapper
    mb.box((0.36, 0.1, 0.08), (0, 0, 0.3), "lips")                           # strap
    mb.box((0.06, 0.02, 0.16), (-0.1, -0.15, 0.05), "white")                 # shine


LEVEL = {
    "title": "1-2 THE GOAT",
    "seed": 12,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#efe6d4", "skin_shade": "#c4b49c",
        "lips": "#e8909c", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#1a3a1e",
        "hair1": "#8a7c6c", "hair2": "#bcb09c", "hair3": "#e0d8c8", "hair4": "#fcf8f0",
        "acc1": "#a0a4ac", "acc2": "#5aa042", "acc3": "#e8c048",
    },
    "style": "straight", "wave_amp": 0.05, "wave_period": 2.2,
    "strand_pattern": ["hair3", "hair4", "hair2", "hair3", "hair4", "hair2"],
    "tile_weights": {"normal": 0.52, "normal2": 0.18, "knot": 0.12, "hold": 0.0, "sparse": 0.05, "decor": 0.13},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "acc3",              # bits of hay
    "mustache": "none", "brows": "thin",
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("tin_can", tin_can), ("hay_bale", hay_bale), ("boot", boot), ("bell", bell)],
    "enemy": None, "fx": None,
    "rows": 24, "tip": "point", "taper_rows": 3.5, "start_x": 2.6, "start_z": 1.6,
    "climber_roles": {"beanie": "lips", "hardhat": "acc3", "hardhat_shade": "cap"},
    "powerup": {"tangled_at": 8, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 11, "drift": 0.09,
}
