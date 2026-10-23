"""Level 1 - THE WIZARD: long straight silver beard with tiny stars."""


def headwear(mb, cx, z, cols):
    """Purple pointy-hat brim + band with a star, at the top of the frame."""
    mb.box((cols + 1.2, 0.1, 0.32), (cx, -0.5, z + 0.25), "acc1")
    mb.box((cols - 1.0, 0.1, 0.6), (cx, -0.45, z + 0.65), "acc1")
    mb.box((cols - 1.0, 0.12, 0.1), (cx, -0.55, z + 0.45), "acc3")
    for dx in (-1.6, 0.0, 1.6):
        mb.box((0.22, 0.03, 0.06), (cx + dx, -0.62, z + 0.66), "acc3")
        mb.box((0.06, 0.03, 0.22), (cx + dx, -0.62, z + 0.66), "acc3")


def crystal_ball(mb):
    mb.disc(0.3, (0, 0, 0.07), "acc2", seg=12)
    mb.disc(0.2, (0.04, -0.06, 0.04), "hair3", seg=10, depth=0.02)
    mb.disc(0.13, (0.06, -0.08, 0.02), "acc2", seg=8, depth=0.02)
    mb.box((0.09, 0.02, 0.07), (-0.13, -0.1, 0.2), "white")
    mb.box((0.4, 0.2, 0.08), (0, 0, -0.25), "acc3")
    mb.box((0.3, 0.2, 0.08), (0, 0, -0.32), "acc1")


def cat(mb):
    mb.box((0.32, 0.2, 0.3), (0, 0, -0.06), "black")                  # body
    mb.box((0.16, 0.05, 0.18), (0, -0.11, -0.06), "hair2")             # belly
    mb.box((0.3, 0.2, 0.24), (0, 0, 0.22), "black")                    # head
    for s in (-1, 1):
        mb.box((0.11, 0.18, 0.11), (s * 0.1, 0, 0.35), "black", ry=45)  # ears
        mb.box((0.07, 0.04, 0.06), (s * 0.07, -0.11, 0.24), "acc3")     # eyes
        mb.bar((s * 0.15, 0.0), (s * 0.34, 0.14), 0.08, 0, "black")     # front legs flailing
        mb.bar((s * 0.12, -0.18), (s * 0.3, -0.36), 0.08, 0, "black")   # hind legs
        mb.box((0.06, 0.05, 0.05), (s * 0.34, -0.03, 0.14), "white")    # paws
    mb.box((0.05, 0.04, 0.04), (0, -0.12, 0.18), "lips")               # nose
    mb.bar((0.15, -0.15), (0.36, -0.05), 0.07, 0.02, "black")         # tail
    mb.bar((0.36, -0.05), (0.38, 0.14), 0.07, 0.02, "black")


def potion(mb):
    mb.disc(0.24, (0, 0, -0.1), "hair3", seg=10)                       # glass flask
    mb.disc(0.19, (0, -0.06, -0.14), "acc1", seg=10, depth=0.02)        # purple potion
    mb.box((0.36, 0.02, 0.06), (0, -0.07, -0.02), "acc1")
    mb.box((0.12, 0.12, 0.22), (0, 0, 0.22), "hair3")                   # neck
    mb.box((0.15, 0.14, 0.09), (0, 0, 0.36), "lips")                   # cork
    mb.box((0.06, 0.02, 0.06), (-0.1, -0.09, -0.1), "white")
    for x, z in ((0.12, 0.45), (-0.05, 0.52)):
        mb.box((0.05, 0.02, 0.05), (x, 0, z), "acc2")


LEVEL = {
    "title": "1 WIZARD",
    "seed": 11,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f0b898", "skin_shade": "#c07868",
        "lips": "#a04048", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#181040",
        "hair1": "#505870", "hair2": "#8890b0", "hair3": "#b8c0d8", "hair4": "#e0e4f0",
        "acc1": "#8840c8", "acc2": "#40d8e8", "acc3": "#f8e848",
    },
    "style": "straight", "wave_amp": 0.03, "wave_period": 3.0,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair2"],
    "tile_weights": {"normal": 0.465, "normal2": 0.12, "knot": 0.1, "hold": 0.1, "sparse": 0.07, "decor": 0.12},
    "holds": ["star"], "decor": "stars",
    "mustache": "droop", "brows": "bushy",
    "headwear": headwear,
    "hazards": [("crystal_ball", crystal_ball), ("cat", cat), ("potion", potion)],
    "enemy": None, "fx": "sparkles",
    # level shape + throwing (see README "Level config")
    "rows": 26, "tip": "point", "taper_rows": 6.0, "start_x": 2.7, "start_z": 1.0,
    # hard-hat power-up: climber colour aliases, where it sits tangled in the beard
    # (frame of the climb when he reaches it) and when the mouth throws one as a 'good' item
    "climber_roles": {"beanie": "acc1", "hardhat": "acc3", "hardhat_shade": "cap"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 10, "drift": 0.09,
}
