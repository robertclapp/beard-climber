"""World 1-3 - THE LUMBERJACK: thick wavy ginger folk-hero beard (refit from the prototype for the web game)."""
import math


def headwear(mb, cx, z, cols):
    """Red flannel toque with black check stripes."""
    mb.box((cols + 1.0, 0.1, 0.9), (cx, -0.45, z + 0.55), "acc1")
    for k in range(int(cols + 1) * 2):
        mb.box((0.14, 0.12, 0.9), (cx - (cols + 1) / 2 + 0.25 + k * 0.5, -0.5, z + 0.55), "black")
    mb.box((cols + 1.0, 0.12, 0.12), (cx, -0.52, z + 0.55), "black")
    mb.box((cols + 1.2, 0.14, 0.25), (cx, -0.55, z + 0.12), "hair1")      # folded brim


def log(mb):
    mb.box((0.78, 0.3, 0.34), (-0.05, 0, 0), "hair1")
    for x in (-0.3, -0.05, 0.2):
        mb.box((0.03, 0.05, 0.34), (x, -0.16, 0), "black")
    mb.box((0.18, 0.05, 0.03), (-0.2, -0.16, 0.09), "hair2")
    mb.disc(0.19, (0.36, -0.1, 0), "acc3", seg=10)                   # cut end facing camera
    mb.disc(0.12, (0.36, -0.16, 0), "hair3", seg=10, depth=0.02)
    mb.disc(0.05, (0.36, -0.18, 0), "acc3", seg=6, depth=0.02)


def chainsaw(mb):
    mb.box((0.36, 0.2, 0.26), (-0.18, 0, 0), "acc1")                 # engine
    mb.box((0.2, 0.05, 0.08), (-0.18, -0.11, 0.0), "white")
    mb.box((0.5, 0.06, 0.12), (0.24, 0, 0.0), "acc2")                # bar
    mb.disc(0.06, (0.49, 0, 0), "acc2", seg=8)
    for k in range(6):
        mb.box((0.04, 0.07, 0.03), (0.04 + k * 0.08, -0.01, 0.075), "black")
        mb.box((0.04, 0.07, 0.03), (0.08 + k * 0.08, -0.01, -0.075), "black")
    mb.bar((-0.34, 0.13), (-0.26, 0.28), 0.05, 0, "black")            # handle
    mb.bar((-0.26, 0.28), (-0.04, 0.28), 0.05, 0, "black")
    mb.bar((-0.04, 0.28), (0.0, 0.13), 0.05, 0, "black")
    for k, (x, z, r) in enumerate(((-0.42, 0.18, 0.07), (-0.5, 0.3, 0.09), (-0.44, 0.44, 0.06))):   # switched OFF: sputter puffs
        mb.disc(r, (x, -0.05, z), "white" if k % 2 else "hair4", seg=8, depth=0.04)


def pancakes(mb):
    """Stack of round-edged pancakes on a plate, butter + dripping syrup."""
    mb.box((0.78, 0.3, 0.05), (0, 0, -0.3), "white")                  # plate
    mb.box((0.6, 0.3, 0.04), (0, 0, -0.34), "hair4")
    for k in range(3):
        z = -0.22 + k * 0.12
        mb.box((0.5, 0.3, 0.11), (0, 0, z), "hair3")                  # pancake edge (browned)
        for s in (-1, 1):
            mb.disc(0.055, (s * 0.25, 0, z), "hair3", seg=8, depth=0.3)
        mb.box((0.54, 0.3, 0.04), (0, -0.02, z + 0.02), "acc3")       # fluffy middle
    mb.box((0.52, 0.3, 0.06), (0, -0.03, 0.1), "hair1")               # syrup on top
    for x, ln in ((-0.2, 0.14), (0.05, 0.22), (0.24, 0.1)):
        mb.box((0.05, 0.05, ln), (x, -0.17, 0.1 - ln / 2), "hair1")   # drips
    mb.box((0.16, 0.12, 0.09), (0.02, -0.05, 0.17), "cap")            # butter pat
    mb.box((0.05, 0.02, 0.03), (-0.02, -0.12, 0.19), "white")


def axe(mb):
    """A cartoon felling axe: wooden handle, big shiny head."""
    mb.bar((-0.36, -0.3), (0.2, 0.3), 0.08, 0, "hair2")                  # handle
    mb.bar((-0.36, -0.3), (-0.3, -0.24), 0.11, 0, "hair1")               # knob
    mb.box((0.26, 0.12, 0.3), (0.26, 0, 0.3), "white", ry=-42)           # head (shiny steel)
    mb.box((0.06, 0.13, 0.34), (0.36, 0, 0.21), "acc3", ry=-42)          # edge glint
    mb.box((0.1, 0.14, 0.12), (0.17, 0, 0.38), "black", ry=-42)          # eye


def pinecone(mb):
    for k in range(5):                                                   # stacked scales
        w = 0.24 + 0.22 * math.sin(math.pi * (k + 0.5) / 5)
        z = -0.24 + k * 0.12
        mb.box((w, 0.24, 0.11), (0, 0, z), "hair1" if k % 2 else "hair2")
        for s in (-1, 1):
            mb.box((0.07, 0.02, 0.05), (s * w * 0.3, -0.13, z + 0.02), "hair3")
    mb.bar((0, 0.34), (0.05, 0.46), 0.05, 0, "acc2")                      # stalk


LEVEL = {
    "title": "1-3 THE LUMBERJACK",
    "seed": 22,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f8c098", "skin_shade": "#d07860",
        "lips": "#a83838", "shirt": "#3870e8", "pants": "#203070", "cap": "#f8e840",
        "bg": "#183828",
        "hair1": "#582010", "hair2": "#983818", "hair3": "#d06028", "hair4": "#f09848",
        "acc1": "#c82028", "acc2": "#508848", "acc3": "#f0d070",
    },
    "style": "wavy", "wave_amp": 0.09, "wave_period": 1.4,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair2", "hair3", "hair1"],
    "tile_weights": {"normal": 0.48, "normal2": 0.16, "knot": 0.12, "hold": 0.08, "sparse": 0.035, "decor": 0.10},
    "holds": ["twig"], "decor": "crumbs", "crumb_role": "acc3",
    "mustache": "bushy", "brows": "bushy",
    "headwear": headwear,
    "hazards": [("log", log), ("chainsaw", chainsaw), ("pancakes", pancakes), ("axe", axe), ("pinecone", pinecone)],
    "enemy": None, "fx": None,
    "rows": 26, "tip": "ragged", "taper_rows": 3.0, "start_x": 2.6, "start_z": 1.2,
    # hard-hat power-up: climber colour aliases, where it sits tangled in the beard
    # (frame of the climb when he reaches it) and when the mouth throws one as a 'good' item
    "climber_roles": {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "hair4"},
    "powerup": {"tangled_at": 10, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 9, "drift": 0.09,
}
