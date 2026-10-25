"""Level 3 - THE VIKING: braided copper/blond beard with iron rings as hand-holds."""


def headwear(mb, cx, z, cols):
    """Iron helmet rim with rivets and a nose guard."""
    mb.box((cols + 1.2, 0.1, 0.4), (cx, -0.5, z + 0.3), "acc1")
    mb.box((cols + 1.2, 0.12, 0.08), (cx, -0.55, z + 0.12), "acc2")
    for k in range(9):
        mb.box((0.08, 0.04, 0.08), (cx - 3.2 + k * 0.8, -0.58, z + 0.32), "acc2")
    mb.box((0.32, 0.1, 1.15), (cx, -0.55, z - 0.35), "acc1")           # nose guard
    mb.box((0.1, 0.12, 1.1), (cx - 0.06, -0.6, z - 0.35), "acc2")
    mb.box((cols + 1.2, 0.1, 0.6), (cx, -0.45, z + 0.8), "acc1")


def axe(mb):
    mb.box((0.07, 0.08, 0.84), (0, 0, -0.02), "hair1")                # handle
    mb.box((0.09, 0.09, 0.08), (0, 0, -0.4), "acc1")
    mb.box((0.2, 0.08, 0.2), (0.1, 0, 0.27), "acc1")                  # head
    mb.box((0.14, 0.08, 0.38), (0.25, 0, 0.27), "acc1")
    mb.box((0.06, 0.09, 0.44), (0.33, -0.01, 0.27), "acc2")           # bright edge
    mb.box((0.1, 0.08, 0.12), (-0.07, 0, 0.27), "acc1")


def helmet(mb):
    for k, w in enumerate((0.54, 0.48, 0.38, 0.22)):
        mb.box((w, 0.4, 0.09), (0, 0, -0.08 + k * 0.09), "acc1")       # stepped dome
    mb.box((0.58, 0.42, 0.08), (0, -0.01, -0.13), "acc2")             # band
    for x in (-0.18, 0.0, 0.18):
        mb.box((0.05, 0.03, 0.05), (x, -0.23, -0.13), "black")
    for s in (-1, 1):                                                  # curved horns
        pts = [(0.26, 0.0), (0.38, 0.08), (0.44, 0.22), (0.42, 0.38)]
        for i, th in enumerate((0.13, 0.1, 0.07)):
            mb.bar((s * pts[i][0], pts[i][1]), (s * pts[i + 1][0], pts[i + 1][1]), th, 0, "white")


def mead_mug(mb):
    mb.box((0.36, 0.3, 0.42), (-0.04, 0, -0.06), "hair2")             # wooden mug
    for x in (-0.13, -0.04, 0.05):
        mb.box((0.02, 0.05, 0.42), (x, -0.16, -0.06), "hair1")
    for z in (-0.22, 0.1):
        mb.box((0.38, 0.32, 0.05), (-0.04, -0.01, z), "acc1")          # iron bands
    for x in (-0.16, -0.04, 0.08):
        mb.disc(0.09, (x, -0.1, 0.19), "white")                        # foam
    mb.box((0.12, 0.05, 0.08), (0.06, -0.12, 0.08), "white")          # foam drip
    mb.bar((0.14, 0.08), (0.27, 0.06), 0.06, 0, "acc1")               # handle
    mb.bar((0.27, 0.06), (0.27, -0.16), 0.06, 0, "acc1")
    mb.bar((0.27, -0.16), (0.14, -0.18), 0.06, 0, "acc1")


LEVEL = {
    "title": "3 VIKING",
    "seed": 33,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f0b088", "skin_shade": "#c07058",
        "lips": "#983838", "shirt": "#2850d8", "pants": "#601830", "cap": "#e82840",
        "bg": "#203860",
        "hair1": "#783818", "hair2": "#b86028", "hair3": "#e0a040", "hair4": "#f8d880",
        "acc1": "#687080", "acc2": "#c8d0d8", "acc3": "#f8c018",
    },
    "style": "braided", "wave_amp": 0.05, "wave_period": 2.0,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2"],
    "braid_cols": [1, 4],
    "tile_weights": {"normal": 0.5, "normal2": 0.1, "knot": 0.08, "hold": 0.16, "sparse": 0.035, "decor": 0.10},
    "holds": ["ring", "ring", "bead"], "decor": "beads",
    "mustache": "droop", "brows": "normal",
    "headwear": headwear,
    "hazards": [("axe", axe), ("helmet", helmet), ("mead_mug", mead_mug)],
    "enemy": None, "fx": None,
    "rows": 24, "tip": "braids", "taper_rows": 4.0, "start_x": 1.5, "start_z": 0.8,
    # hard-hat power-up: climber colour aliases, where it sits tangled in the beard
    # (frame of the climb when he reaches it) and when the mouth throws one as a 'good' item
    "climber_roles": {"beanie": "cap", "hardhat": "acc3", "hardhat_shade": "hair3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 10, "drift": 0.09,
}
