"""World 2-1 - THE ELF: a giant toy-workshop elf with a small curly ginger beard, pointy hat and pointy ears."""
import math


def headwear(mb, cx, z, cols):
    """Tall green pointy hat with a red-and-white cuff, flopping over to one side, with a jingle bell."""
    mb.box((cols + 0.2, 0.1, 0.5), (cx, -0.5, z - 0.2), "acc4")                      # cuff
    for k in range(int(cols + 1) * 2):
        mb.box((0.22, 0.12, 0.48), (cx - (cols + 0.2) / 2 + 0.25 + k * 0.5, -0.55, z - 0.2), "acc1" if k % 2 else "white")
    for k in range(6):                                                               # cone, leaning right
        w = (cols - 0.2) * (1 - k / 6.5)
        mb.box((w, 0.1, 0.32), (cx + k * 0.22, -0.45, z + 0.2 + k * 0.3), "acc2" if k % 2 else "pants")
    mb.disc(0.3, (cx + 1.6, -0.5, z + 2.1), "cap", seg=10, depth=0.2)                # bell
    mb.box((0.2, 0.05, 0.06), (cx + 1.6, -0.62, z + 2.0), "black")


def face_extra(mb, cx, ez, cols):
    """Big pointy elf ears + rosy cheeks + freckles."""
    for s in (-1, 1):
        mb.bar((cx + s * 2.0, ez - 0.5), (cx + s * 2.9, ez + 0.5), 0.45, -0.5, "skin")
        mb.bar((cx + s * 2.1, ez - 0.4), (cx + s * 2.75, ez + 0.35), 0.18, -0.53, "skin_shade")
        for k in range(3):
            mb.box((0.08, 0.05, 0.08), (cx + s * (1.0 + k * 0.2), -0.2, ez - 0.75 - (k % 2) * 0.12), "acc3")


def present(mb):
    mb.box((0.5, 0.3, 0.42), (0, 0, -0.06), "acc1")
    mb.box((0.09, 0.32, 0.42), (0, -0.01, -0.06), "cap")
    mb.box((0.5, 0.32, 0.08), (0, -0.01, -0.06), "cap")
    mb.box((0.18, 0.1, 0.14), (-0.1, -0.02, 0.2), "cap", ry=25)
    mb.box((0.18, 0.1, 0.14), (0.1, -0.02, 0.2), "cap", ry=-25)


def jingle_bell(mb):
    mb.disc(0.27, (0, 0, -0.03), "cap", seg=12, depth=0.28)
    mb.box((0.36, 0.02, 0.04), (0, -0.15, -0.02), "acc3")                             # slot
    mb.disc(0.05, (0, -0.16, -0.12), "black", seg=6, depth=0.02)
    mb.box((0.1, 0.1, 0.1), (0, 0, 0.28), "acc3")                                    # loop
    mb.box((0.06, 0.02, 0.06), (-0.1, -0.16, 0.1), "white")
    mb.bar((0.05, 0.33), (0.3, 0.42), 0.08, 0, "acc1")                               # ribbon


def toy_train(mb):
    mb.box((0.52, 0.28, 0.24), (0.04, 0, -0.06), "acc1")                             # body
    mb.box((0.22, 0.28, 0.24), (0.2, 0, 0.16), "pants")                              # cab
    mb.box((0.1, 0.1, 0.16), (-0.12, 0, 0.14), "black")                              # chimney
    mb.box((0.14, 0.12, 0.05), (-0.12, 0, 0.23), "cap")
    for x in (-0.12, 0.08, 0.24):
        mb.disc(0.08, (x, -0.15, -0.2), "black", seg=8, depth=0.04)
        mb.disc(0.03, (x, -0.18, -0.2), "cap", seg=6, depth=0.02)
    mb.box((0.04, 0.02, 0.1), (0.2, -0.15, 0.16), "white")                           # window


def candy_cane(mb):
    pts = [(0.0, -0.4), (0.0, 0.1), (0.04, 0.24), (0.14, 0.32), (0.26, 0.3), (0.32, 0.18)]
    for i, (p0, p1) in enumerate(zip(pts, pts[1:])):
        mb.bar(p0, p1, 0.13, 0, "white")
    for z in (-0.32, -0.16, 0.0):
        mb.bar((-0.06, z), (0.06, z + 0.08), 0.06, -0.07, "acc1")
    mb.bar((0.1, 0.3), (0.16, 0.34), 0.07, -0.07, "acc1")
    mb.bar((0.27, 0.27), (0.32, 0.2), 0.07, -0.07, "acc1")


LEVEL = {
    "title": "2-1 THE ELF",
    "seed": 52,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f8c8a8", "skin_shade": "#e08878",
        "lips": "#c04048", "shirt": "#e83828", "pants": "#186830", "cap": "#f8c830",
        "bg": "#14203c",
        "hair1": "#7c3014", "hair2": "#b04c1c", "hair3": "#d8702c", "hair4": "#f09848",
        "acc1": "#d82830", "acc2": "#2ca048", "acc3": "#b86830", "acc4": "#f8f8f8",
    },
    "style": "wavy", "wave_amp": 0.2, "wave_period": 0.7,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair3", "hair1"],
    "tile_weights": {"normal": 0.47, "normal2": 0.24, "knot": 0.1, "hold": 0.0, "sparse": 0.05, "decor": 0.14},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "cap",                     # glitter + sawdust from the workshop
    "mustache": "thin_curl", "brows": "thin", "cheeks": True,
    "headwear": headwear, "face_extra": face_extra,
    "hazards": [("present", present), ("jingle_bell", jingle_bell), ("toy_train", toy_train), ("candy_cane", candy_cane)],
    "enemy": None, "fx": None,
    "rows": 26, "tip": "round", "taper_rows": 2.6, "start_x": 2.6, "start_z": 1.2,
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
