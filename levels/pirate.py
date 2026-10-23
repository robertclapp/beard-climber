"""Level 5 - THE PIRATE: black beard with red ribbons and gold beads tied in."""


def headwear(mb, cx, z, cols):
    """Black tricorn brim with gold trim and a tiny skull; plus an eyepatch (see LEVEL)."""
    mb.box((cols + 1.2, 0.1, 0.9), (cx, -0.45, z + 0.6), "hair1")
    mb.box((cols + 1.2, 0.12, 0.1), (cx, -0.55, z + 0.18), "acc3")
    mb.disc(0.2, (cx, -0.58, z + 0.55), "white", seg=8)
    mb.box((0.06, 0.03, 0.06), (cx - 0.07, -0.62, z + 0.57), "black")
    mb.box((0.06, 0.03, 0.06), (cx + 0.07, -0.62, z + 0.57), "black")


def cannonball(mb):
    mb.disc(0.27, (0, 0, -0.03), "hair4", seg=12)
    mb.disc(0.2, (0.03, -0.06, -0.06), "hair3", seg=10, depth=0.02)
    mb.box((0.09, 0.02, 0.07), (-0.11, -0.1, 0.09), "white")
    mb.bar((0.1, 0.2), (0.18, 0.34), 0.05, 0, "pants")                # fuse
    mb.box((0.1, 0.03, 0.1), (0.19, -0.02, 0.37), "acc3", ry=45)      # spark
    mb.box((0.05, 0.03, 0.05), (0.19, -0.04, 0.37), "acc1")


def parrot(mb):
    mb.box((0.22, 0.2, 0.32), (0, 0, -0.02), "acc2")                  # body
    mb.box((0.2, 0.2, 0.18), (0, 0, 0.22), "acc1")                    # red head
    mb.box((0.08, 0.06, 0.08), (-0.12, -0.04, 0.2), "acc3", ry=45)    # beak
    mb.box((0.06, 0.04, 0.06), (-0.03, -0.11, 0.25), "white")
    mb.box((0.03, 0.04, 0.03), (-0.04, -0.13, 0.25), "black")
    for s in (-1, 1):                                                  # flapping wings
        mb.bar((s * 0.1, 0.08), (s * 0.38, 0.22), 0.12, 0, "acc2")
        mb.bar((s * 0.3, 0.19), (s * 0.42, 0.26), 0.08, -0.01, "acc1")
    mb.bar((0.0, -0.18), (0.06, -0.4), 0.08, 0, "acc1")                # tail
    mb.bar((0.04, -0.18), (0.12, -0.36), 0.06, -0.01, "shirt")


def rum_bottle(mb):
    mb.box((0.26, 0.24, 0.38), (0, 0, -0.1), "lips")                  # dark glass
    mb.box((0.2, 0.2, 0.06), (0, 0, 0.12), "lips")
    mb.box((0.1, 0.1, 0.16), (0, 0, 0.22), "lips")                    # neck
    mb.box((0.12, 0.12, 0.08), (0, 0, 0.33), "pants")                 # cork
    mb.box((0.22, 0.04, 0.16), (0, -0.12, -0.1), "white")             # label
    mb.bar((-0.06, -0.15), (0.06, -0.05), 0.03, -0.15, "black")      # X
    mb.bar((-0.06, -0.05), (0.06, -0.15), 0.03, -0.15, "black")
    mb.box((0.04, 0.03, 0.22), (-0.09, -0.13, 0.0), "acc1")          # glint


LEVEL = {
    "title": "5 PIRATE",
    "seed": 55,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#e0a078", "skin_shade": "#b06850",
        "lips": "#883020", "shirt": "#48a0f8", "pants": "#d8b878", "cap": "#f8d028",
        "bg": "#3078c0",
        "hair1": "#101018", "hair2": "#282838", "hair3": "#484860", "hair4": "#7878a0",
        "acc1": "#e02030", "acc2": "#28b048", "acc3": "#e8b830",
    },
    "style": "wavy", "wave_amp": 0.06, "wave_period": 1.8,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair2"],
    "tile_weights": {"normal": 0.5, "normal2": 0.12, "knot": 0.08, "hold": 0.14, "sparse": 0.035, "decor": 0.10},
    "holds": ["ribbon", "ribbon", "bead"], "decor": "coins",
    "mustache": "thin_curl", "brows": "normal", "eyepatch": True,
    "headwear": headwear,
    "hazards": [("cannonball", cannonball), ("parrot", parrot), ("rum_bottle", rum_bottle)],
    "enemy": None, "fx": None,
    "rows": 24, "tip": "fork", "fork_x": (0.32, 0.68), "taper_rows": 5.0, "start_x": 1.95, "start_z": 1.0,
    # hard-hat power-up: climber colour aliases, where it sits tangled in the beard
    # (frame of the climb when he reaches it) and when the mouth throws one as a 'good' item
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 10, "drift": 0.09,
}
