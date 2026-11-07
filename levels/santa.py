"""World 2-5 (BOSS) - SANTA: a huge fluffy white beard. HO HO HO belly laughs shake it; a reindeer swoops by."""


def headwear(mb, cx, z, cols):
    """Red hat with a fluffy white fur trim."""
    mb.box((cols + 1.2, 0.1, 0.8), (cx, -0.45, z + 0.75), "acc1")
    for k in range(15):
        x = cx - 3.5 + k * 0.5
        mb.disc(0.28, (x, -0.55 - 0.01 * (k % 2), z + 0.3 + 0.06 * (k % 2)), "white" if k % 2 else "hair3", seg=8)


def present(mb):
    mb.box((0.5, 0.3, 0.42), (0, 0, -0.06), "acc1")
    mb.box((0.09, 0.32, 0.42), (0, -0.01, -0.06), "acc4")
    mb.box((0.5, 0.32, 0.08), (0, -0.01, -0.06), "acc4")
    mb.box((0.18, 0.1, 0.14), (-0.1, -0.02, 0.2), "acc4", ry=25)       # bow
    mb.box((0.18, 0.1, 0.14), (0.1, -0.02, 0.2), "acc4", ry=-25)
    mb.box((0.08, 0.12, 0.08), (0, -0.04, 0.18), "acc2")


def cookie(mb):
    mb.disc(0.27, (0, 0, 0), "acc3", seg=10)
    mb.disc(0.21, (0.01, -0.06, 0.01), "acc4", seg=10, depth=0.02)
    for x, z in ((-0.1, 0.08), (0.09, 0.1), (0.0, -0.08), (-0.12, -0.1), (0.12, -0.05)):
        mb.box((0.06, 0.03, 0.06), (x, -0.08, z), "black")


def coal(mb):
    for (x, z, s, a) in ((0, 0, 0.3, 20), (-0.14, -0.08, 0.2, 50), (0.14, 0.08, 0.2, 10), (0.06, -0.12, 0.18, 35)):
        mb.box((s, 0.25, s * 0.85), (x, 0, z), "black", ry=a)
    for (x, z) in ((-0.05, 0.08), (0.1, 0.12), (-0.15, -0.04)):
        mb.box((0.06, 0.02, 0.04), (x, -0.16, z), "hair1")
    mb.box((0.04, 0.02, 0.04), (0.02, -0.17, 0.02), "acc1")           # ember


def reindeer(mb, frame=0):
    """Cross-screen enemy (faces left). frame 0/1 = legs gallop."""
    mb.box((0.5, 0.2, 0.22), (0.05, 0, 0), "acc3")                    # body
    mb.box((0.36, 0.05, 0.06), (0.05, -0.11, -0.08), "white")         # belly
    mb.bar((-0.15, 0.06), (-0.28, 0.22), 0.12, 0, "acc3")              # neck
    mb.box((0.22, 0.18, 0.15), (-0.34, 0, 0.26), "acc3")              # head
    mb.disc(0.05, (-0.46, -0.1, 0.24), "acc1", seg=6)                 # red nose
    mb.box((0.04, 0.04, 0.04), (-0.32, -0.1, 0.29), "black")          # eye
    for s in (0, 1):                                                   # antlers
        x = -0.3 + s * 0.1
        mb.bar((x, 0.32), (x + 0.06, 0.5), 0.04, -0.01, "white")
        mb.bar((x + 0.03, 0.42), (x - 0.06, 0.48), 0.04, -0.01, "white")
    sw = 0.12 if frame == 0 else -0.12
    for x in (-0.12, 0.22):
        mb.bar((x, -0.08), (x - sw - 0.1, -0.3), 0.06, 0, "acc3")
        mb.bar((x, -0.08), (x + sw, -0.3), 0.06, 0.02, "acc3")
    mb.box((0.08, 0.06, 0.08), (0.32, 0, 0.08), "white")              # tail


LEVEL = {
    "title": "2-5 SANTA",
    "seed": 47,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f8c0a0", "skin_shade": "#e86860",
        "lips": "#c03038", "shirt": "#3060e8", "pants": "#204898", "cap": "#f8c800",
        "bg": "#101848",
        "hair1": "#7888a8", "hair2": "#b0bcd0", "hair3": "#d8e0ec", "hair4": "#f8f8f8",
        "acc1": "#d82028", "acc2": "#209840", "acc3": "#a06030", "acc4": "#f0c860",
    },
    "style": "fluffy", "wave_amp": 0.04, "wave_period": 1.5,
    "strand_pattern": ["hair3", "hair2", "white", "hair3", "hair2"],
    "tile_weights": {"normal": 0.5, "normal2": 0.14, "knot": 0.12, "hold": 0.0, "sparse": 0.06, "decor": 0.18},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "acc3",
    "mustache": "curl", "brows": "bushy", "cheeks": True,
    "headwear": headwear,
    "hazards": [("present", present), ("cookie", cookie), ("coal", coal), ("reindeer", reindeer)],   # reindeer = the swoop (never thrown)
    "enemy": ("reindeer", reindeer), "fx": "snow",
    "rows": 32, "tip": "round", "taper_rows": 3.5, "start_x": 2.8, "start_z": 1.0,
    # hard-hat power-up: climber colour aliases, where it sits tangled in the beard
    # (frame of the climb when he reaches it) and when the mouth throws one as a 'good' item
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 10, "drift": 0.09,
    "enemy_path": {"frames": (12, 40), "z": 5.0},   # reindeer crosses right->left (screen units above frame bottom)
}
