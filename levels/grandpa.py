"""World 1, level 1 - GRANDPA (Whiskerton Woods): soft, scruffy grey-white beard, round glasses,
a tweed flat cap. The tutorial climb: gentle hazards from his pocket-and-pantry (candies, silly
dentures, knitting yarn, reading glasses, a slipper). He's grumpy because the grandkids haven't called."""
import math


def headwear(mb, cx, z, cols):
    """Tweed flat cap: a wide soft crown with a short peak and a stitched band (fits under the image top, z+0.6)."""
    mb.box((cols + 0.4, 0.1, 0.62), (cx, -0.45, z + 0.27), "acc1")
    for k in range(int(cols + 1) * 2):                       # tweed flecks
        mb.box((0.08, 0.12, 0.08), (cx - (cols + 0.4) / 2 + 0.3 + k * 0.5, -0.52, z + 0.2 + 0.14 * (k % 3)), "skin_shade")
    mb.box((cols + 0.5, 0.12, 0.08), (cx, -0.53, z + 0.0), "black")       # band stitch
    mb.box((2.8, 0.16, 0.2), (cx, -0.6, z - 0.1), "acc1")                 # short peak
    mb.box((2.6, 0.18, 0.05), (cx, -0.63, z - 0.2), "black")
    mb.box((0.3, 0.14, 0.12), (cx, -0.56, z + 0.52), "skin_shade")        # button on top


def glasses(mb, cx, ez, cols):
    """Round reading glasses over the eyes (drawn in front of the eyes, no lens fill)."""
    for s in (-1, 1):
        ex = cx + s * 1.2
        n = 12
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            mb.bar((ex + 0.48 * math.cos(a0), ez + 0.4 * math.sin(a0)),
                   (ex + 0.48 * math.cos(a1), ez + 0.4 * math.sin(a1)), 0.09, -0.22, "acc3", depth=0.04)
        mb.bar((ex + s * 0.48, ez + 0.05), (ex + s * 0.95, ez + 0.2), 0.08, -0.2, "acc3", depth=0.04)   # temples
        mb.box((0.14, 0.02, 0.08), (ex - 0.22, -0.23, ez + 0.2), "white")                             # glint
    mb.bar((cx - 0.72, ez + 0.08), (cx + 0.72, ez + 0.08), 0.08, -0.22, "acc3", depth=0.04)          # bridge


def candy(mb):
    mb.disc(0.22, (0, 0, 0), "shirt", seg=10)
    for x in (-0.1, 0.05):
        mb.bar((x - 0.06, -0.18), (x + 0.1, 0.18), 0.06, -0.06, "white", depth=0.02)
    for s in (-1, 1):                                           # twisted wrapper ends
        mb.bar((s * 0.2, 0), (s * 0.42, 0.14), 0.12, 0, "acc3")
        mb.bar((s * 0.2, 0), (s * 0.42, -0.14), 0.12, 0, "acc3")
    mb.box((0.07, 0.02, 0.05), (-0.08, -0.12, 0.1), "white")


def dentures(mb):
    mb.box((0.66, 0.24, 0.16), (0, 0, 0.13), "lips")            # pink gums, upper
    mb.box((0.66, 0.24, 0.16), (0, 0, -0.17), "lips")           # lower
    for k in range(5):
        x = -0.24 + k * 0.12
        mb.box((0.1, 0.05, 0.12), (x, -0.13, 0.03), "white")
        mb.box((0.1, 0.05, 0.11), (x, -0.13, -0.08), "white")
    mb.box((0.62, 0.04, 0.03), (0, -0.15, -0.025), "black")
    mb.box((0.08, 0.02, 0.05), (-0.22, -0.16, 0.16), "white")


def yarn(mb):
    mb.disc(0.27, (0, 0, 0), "acc2", seg=12)
    for a in (-35, 10, 55):
        r = math.radians(a)
        mb.bar((-0.24 * math.cos(r), -0.24 * math.sin(r)), (0.24 * math.cos(r), 0.24 * math.sin(r)), 0.04, -0.1, "hair1", depth=0.02)
    mb.bar((0.2, -0.15), (0.42, -0.32), 0.05, 0, "acc2")        # loose strand
    mb.bar((-0.12, 0.3), (0.12, 0.42), 0.06, 0, "hair3")        # knitting needle
    mb.box((0.06, 0.03, 0.06), (-0.1, -0.12, 0.12), "white")


def specs(mb):
    for s in (-1, 1):
        n = 10
        for k in range(n):
            a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
            mb.bar((s * 0.2 + 0.15 * math.cos(a0), 0.15 * math.sin(a0)), (s * 0.2 + 0.15 * math.cos(a1), 0.15 * math.sin(a1)), 0.06, 0, "black")
        mb.disc(0.11, (s * 0.2, 0.04, 0), "acc2", seg=10, depth=0.02)
        mb.box((0.05, 0.02, 0.04), (s * 0.2 - 0.04, -0.03, 0.05), "white")
        mb.bar((s * 0.35, 0.03), (s * 0.48, 0.2), 0.05, 0, "black")
    mb.bar((-0.06, 0.04), (0.06, 0.04), 0.05, 0, "black")


def slipper(mb):
    mb.box((0.7, 0.24, 0.24), (0, 0, -0.04), "acc1")            # sole + body
    mb.disc(0.13, (0.35, 0, -0.04), "acc1", seg=8, depth=0.24)
    mb.box((0.72, 0.24, 0.06), (0, 0, -0.18), "hair1")          # sole
    mb.box((0.36, 0.26, 0.12), (0.12, -0.01, 0.12), "white")    # fluffy trim
    for x in (0.0, 0.12, 0.24):
        mb.disc(0.05, (x, -0.14, 0.17), "hair4", seg=6, depth=0.02)


LEVEL = {
    "title": "1-1 GRANDPA",
    "seed": 7,
    "palette": {
        "black": "#000000", "white": "#f8f8f8", "skin": "#f4c4a4", "skin_shade": "#d08c78",
        "lips": "#e07890", "shirt": "#e83828", "pants": "#2848b8", "cap": "#f8b800",
        "bg": "#14301c",
        "hair1": "#6c6878", "hair2": "#a8a4b4", "hair3": "#d4d0dc", "hair4": "#f4f2f8",
        "acc1": "#a85c30", "acc2": "#58a048", "acc3": "#f0c848",
    },
    "style": "wavy", "wave_amp": 0.07, "wave_period": 1.7,
    "strand_pattern": ["hair3", "hair2", "hair4", "hair3", "hair2", "hair4"],
    "tile_weights": {"normal": 0.55, "normal2": 0.17, "knot": 0.12, "hold": 0.0, "sparse": 0.04, "decor": 0.12},
    "holds": ["knot"], "decor": "crumbs", "crumb_role": "acc3",
    "mustache": "bushy", "brows": "bushy", "cheeks": True,
    "headwear": headwear, "face_extra": glasses,
    "hazards": [("candy", candy), ("dentures", dentures), ("yarn", yarn), ("specs", specs), ("slipper", slipper)],
    "enemy": None, "fx": None,
    "rows": 22, "tip": "ragged", "taper_rows": 2.5, "start_x": 2.6, "start_z": 1.0,
    # tutorial: a bald patch straight above the start column (teaches the sideways hop)
    "forced_tiles": {(2, 5): "sparse", (2, 6): "sparse", (1, 5): "normal", (3, 5): "normal", (1, 6): "normal", (3, 6): "normal",
                     (1, 4): "normal", (3, 4): "normal", (2, 4): "normal", (2, 3): "normal"},
    "climber_roles": {"beanie": "acc1", "hardhat": "acc3", "hardhat_shade": "cap"},
    "powerup": {"tangled_at": 8, "throw_at": "end"},
    "spawn": (0.0, 0.0), "throw_period": 12, "drift": 0.09,
}
