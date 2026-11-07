"""web/pip.py - Pip (the hero), the Whiskerton townsfolk and the story props, for the web game.

Imported by web/render_web_assets.py (inside Blender). Nothing here changes the prototype
pipeline (climber.py stays as it was); Pip reuses climber.py's object rig and poses.

Pip is built from LAYERS (body, hair, headgear, backpack, cat) so the web game can mix and
recolour them for the character creator. Recolourable parts use KEY colours (roles k_*), which
web/build_web.py maps to exact key RGBs and web/src/game.js palette-swaps at runtime.
Each layer is rendered with the always-present body visible in a MASK colour, so the body
correctly hides the parts of that layer that are behind it (e.g. back hair seen from the front).
"""
import math, os
import bpy
import climber
from common import MeshBuilder, new_collection, setup_workbench, ortho_camera

# ---------------------------------------------------------------- key palette (recolour roles)
KEYS = {   # role -> exact key colour (unique, far apart). k_cat* / black / white / hardhat are fixed.
    "k_skin": "#ff80c0", "k_skin_shade": "#c04080",
    "k_hair": "#00ff00", "k_hair_shade": "#008000",
    "k_shirt": "#ff0000", "k_shirt_shade": "#800000",
    "k_pants": "#0000ff",
    "k_gear": "#00ffff", "k_gear_shade": "#008080",
    "k_hat": "#ff8000", "k_hat_shade": "#804000",
    "k_cat": "#505870", "k_cat_light": "#b8c0d8", "k_nose": "#a04048", "k_eye": "#f8e848",
    "k_mask": "#ff00ff",
}
FIXED = {"black": "#000000", "white": "#f8f8f8", "hardhat": "#f8e848", "hardhat_shade": "#f8b800"}

EXTRA_FRAMES = {"stand": 14, "wave": 15, "cheer": 16, "para": 17, "duck": 18}
BACK_POSES = [("c0", 1), ("c1", 2), ("c2", 3), ("c3", 4), ("c4", 5), ("c5", 6), ("c6", 7), ("c7", 8),
              ("fall", climber.FALL_FRAME), ("brace", climber.BRACE_FRAME), ("hold", climber.HOLD_FRAME),
              ("dyno", climber.DYNO_FRAME), ("stand", 14), ("wave", 15), ("cheer", 16), ("para", 17)]
GAME_POSES = [p for p, _ in BACK_POSES[:12]]
FRONT_POSES = [("f_stand", 14), ("f_wave", 15), ("f_cheer", 16)]
TOWN_POSES = [("stand", 14), ("cheer", 16), ("duck", 18)]

BODIES = ["boy", "girl"]
HAIRS = ["short", "curly", "bunches", "long"]
HATS = ["beanie", "cap", "bow"]           # + "none" (no layer). Free in the creator.
# ---- coin-shop cosmetics (web/src/game.js CATALOG): extra hats, outfit patterns, backpack styles, parachutes
SHOP_HATS = ["party", "propeller", "crown", "wizard", "trapper", "viking", "santa", "tricorn", "goathorns", "coonskin", "furhood", "elfhat", "antlers", "icecrown", "earmuffs", "gnomehat", "featherhat", "tiara", "dwarfhelm"]
PATTERNS = ["stripes", "overalls", "robe", "plaid", "vest", "suit", "sash", "bandana", "buckskin", "furcoat", "tunic", "jumper", "frostcape", "scarf", "gnomevest", "goldvest", "gown", "chainmail"]
PACK_STYLES = ["teddy", "rocket", "wings"]
CHUTES = ["dots", "stars", "checker", "rainbow"]
# fixed (not recoloured) colours used by the themed items; quantised exactly like the key colours
EXTRA = {
    "f_purple": "#7838c0", "f_purple_d": "#502890", "f_gold": "#f8c830", "f_gold_d": "#c08818",
    "f_red": "#d82830", "f_red_d": "#901820", "f_silver": "#c8d0e0", "f_silver_d": "#8890a8",
    "f_brown": "#7c4c28", "f_brown_d": "#4c2c18", "f_dark": "#282830", "f_cream": "#f0e0c0",
    "f_flame": "#f87818", "f_green": "#2ca048", "f_green_d": "#186830", "f_ice": "#98d8f8", "f_ice_d": "#4c98d0",
    "r1": "#f05050", "r2": "#f8a040", "r3": "#f8e060", "r4": "#60d060", "r5": "#5090f0", "r6": "#a060e0",
}
FIXED.update(EXTRA)


def _stand():
    return {"sh_L": 10, "el_L": 4, "sh_R": -10, "el_R": -4, "hip_L": 4, "kn_L": 0, "hip_R": -4, "kn_R": 0,
            "hips_rot": 0, "hips_x": 0, "hips_z": 0, "neck": 0}


def extra_poses():
    st = _stand()
    wave = dict(st, sh_R=-150, el_R=-35, neck=-4)
    cheer = dict(st, sh_L=150, el_L=12, sh_R=-150, el_R=-12, hip_L=9, hip_R=-9, hips_z=0.03)
    para = {"sh_L": 162, "el_L": -28, "sh_R": -162, "el_R": 28, "hip_L": 14, "kn_L": -18, "hip_R": -8, "kn_R": 24,
            "hips_rot": 0, "hips_x": 0, "hips_z": 0, "neck": 0}
    duck = {"sh_L": 160, "el_L": 120, "sh_R": -160, "el_R": -120, "hip_L": 62, "kn_L": -118, "hip_R": -62, "kn_R": 118,
            "hips_rot": 0, "hips_x": 0, "hips_z": -0.17, "neck": 8}
    return {"stand": st, "wave": wave, "cheer": cheer, "para": para, "duck": duck}


# ---------------------------------------------------------------- model
def _pivot(name, loc, parent, coll):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location, e.parent = loc, parent
    coll.objects.link(e)
    return e


class Pip:
    """Rig identical to climber.build_climber (same joint names), parts grouped by layer."""

    def __init__(self, coll, prefix, scale, hardhats=True):
        self.coll, self.prefix, self.layers = coll, prefix, {}
        P = prefix
        root = self.root = _pivot(P + "root", (0, 0, 0), None, coll)
        root.scale = (scale,) * 3
        hips = _pivot(P + "hips", (0, 0, 0.5), root, coll)
        neck = _pivot(P + "neck", (0, 0, 0.36), hips, coll)
        j = self.j = {"root": root, "hips": hips, "neck": neck}
        for side, s in (("L", -1), ("R", 1)):
            j[f"sh_{side}"] = _pivot(P + f"sh_{side}", (s * 0.19, 0, 0.32), hips, coll)
            j[f"el_{side}"] = _pivot(P + f"el_{side}", (0, 0, -0.2), j[f"sh_{side}"], coll)
            j[f"hip_{side}"] = _pivot(P + f"hip_{side}", (s * 0.08, 0, -0.04), hips, coll)
            j[f"kn_{side}"] = _pivot(P + f"kn_{side}", (0, 0, -0.24), j[f"hip_{side}"], coll)
        # ---- body (always present). Camera looks from -Y: the BACK faces -Y, the face is at +Y.
        for body in BODIES:
            girl = body == "girl"
            def torso(mb):
                mb.box((0.26, 0.16, 0.12), (0, 0, 0.0), "k_pants")
                mb.box((0.30, 0.18, 0.30), (0, 0, 0.2), "k_shirt")
                mb.box((0.30, 0.185, 0.04), (0, 0, 0.33), "k_shirt_shade")      # collar
                if girl:
                    mb.box((0.36, 0.22, 0.13), (0, 0, 0.03), "k_shirt_shade")     # skirt
                    mb.box((0.38, 0.23, 0.04), (0, 0, -0.02), "k_shirt")          # skirt hem
                else:
                    mb.box((0.28, 0.19, 0.04), (0, 0, 0.06), "black")           # belt
                    mb.box((0.06, 0.195, 0.035), (0, 0, 0.06), "white")          # buckle
            self.part(body, "torso", hips, torso)
            def head(mb):
                mb.box((0.08, 0.08, 0.06), (0, 0, 0.02), "k_skin")
                mb.box((0.18, 0.18, 0.17), (0, 0, 0.12), "k_skin")
                for s in (-1, 1):
                    mb.box((0.03, 0.06, 0.06), (s * 0.1, 0, 0.12), "k_skin")
                    mb.box((0.06, 0.02, 0.06), (s * 0.048, 0.092, 0.135), "white")   # eyes (front)
                    mb.box((0.03, 0.02, 0.045), (s * 0.04, 0.095, 0.13), "black")
                    mb.box((0.035, 0.02, 0.025), (s * 0.068, 0.092, 0.085), "k_skin_shade")  # cheeks
                mb.box((0.07, 0.02, 0.02), (0, 0.093, 0.075), "black")              # smile
                mb.box((0.03, 0.02, 0.02), (-0.045, 0.093, 0.085), "black")
                mb.box((0.03, 0.02, 0.02), (0.045, 0.093, 0.085), "black")
                if girl:
                    for s in (-1, 1):
                        mb.box((0.012, 0.02, 0.02), (s * 0.07, 0.094, 0.165), "black")  # lashes
            self.part(body, "head", neck, head)
            for side in ("L", "R"):
                self.part(body, f"uarm_{side}", j[f"sh_{side}"],
                          lambda mb: mb.box((0.09, 0.09, 0.2), (0, 0, -0.1), "k_shirt"))
                def farm(mb):
                    mb.box((0.07, 0.08, 0.15), (0, 0, -0.075), "k_skin")
                    mb.box((0.10, 0.09, 0.08), (0, 0, -0.19), "k_skin")
                self.part(body, f"farm_{side}", j[f"el_{side}"], farm)
                self.part(body, f"thigh_{side}", j[f"hip_{side}"],
                          lambda mb: mb.box((0.12, 0.12, 0.24), (0, 0, -0.12), "k_skin" if False else "k_pants"))
                def shin(mb):
                    mb.box((0.10, 0.11, 0.2), (0, 0, -0.1), "k_pants")
                    mb.box((0.13, 0.14, 0.07), (0, 0.0, -0.22), "white")
                    mb.box((0.135, 0.145, 0.025), (0, 0.0, -0.25), "k_hat_shade")      # sole
                self.part(body, f"shin_{side}", j[f"kn_{side}"], shin)
        # ---- hair styles (on the neck pivot, like the head)
        def short(mb):
            mb.box((0.195, 0.195, 0.07), (0, 0, 0.19), "k_hair")                 # top
            mb.box((0.195, 0.04, 0.12), (0, -0.085, 0.13), "k_hair")              # back
            mb.box((0.04, 0.17, 0.08), (-0.093, -0.01, 0.16), "k_hair")           # sides
            mb.box((0.04, 0.17, 0.08), (0.093, -0.01, 0.16), "k_hair")
            mb.box((0.17, 0.03, 0.04), (0, 0.088, 0.185), "k_hair")               # fringe
            mb.box((0.06, 0.03, 0.03), (-0.04, -0.105, 0.17), "k_hair_shade")     # tuft
        self.part("short", "hair", neck, short)
        def curly(mb):
            mb.box((0.23, 0.22, 0.1), (0, 0, 0.2), "k_hair")
            mb.box((0.23, 0.05, 0.16), (0, -0.09, 0.12), "k_hair")
            for x, z in ((-0.11, 0.25), (0.0, 0.27), (0.11, 0.25), (-0.13, 0.15), (0.13, 0.15), (-0.12, 0.07), (0.12, 0.07)):
                mb.sphere(0.055, (x, 0, z), "k_hair", seg=6, rings=4)
            for x, z in ((-0.06, 0.2), (0.07, 0.16), (-0.02, 0.1)):
                mb.box((0.035, 0.03, 0.03), (x, -0.12, z), "k_hair_shade")
            mb.box((0.18, 0.03, 0.05), (0, 0.09, 0.19), "k_hair")
        self.part("curly", "hair", neck, curly)
        def bunches(mb):
            short(mb)
            for s in (-1, 1):
                mb.sphere(0.065, (s * 0.15, 0, 0.13), "k_hair", seg=6, rings=4)
                mb.box((0.06, 0.05, 0.1), (s * 0.18, 0, 0.07), "k_hair")
                mb.box((0.04, 0.06, 0.04), (s * 0.11, 0, 0.15), "k_hat")             # hair ties
        self.part("bunches", "hair", neck, bunches)
        def long_(mb):
            short(mb)
            mb.box((0.22, 0.04, 0.26), (0, -0.095, 0.03), "k_hair")              # down the back
            mb.box((0.05, 0.12, 0.22), (-0.1, 0.03, 0.04), "k_hair")             # side locks
            mb.box((0.05, 0.12, 0.22), (0.1, 0.03, 0.04), "k_hair")
            mb.box((0.05, 0.03, 0.18), (0.04, -0.12, 0.06), "k_hair_shade")
        self.part("long", "hair", neck, long_)
        # ---- headgear
        def beanie(mb):
            mb.box((0.205, 0.205, 0.12), (0, -0.004, 0.2), "k_hat")
            mb.box((0.21, 0.21, 0.04), (0, -0.004, 0.15), "k_hat_shade")
            mb.box((0.08, 0.08, 0.07), (0, 0, 0.28), "white")
        self.part("beanie", "hat", neck, beanie)
        def cap(mb):
            mb.box((0.205, 0.205, 0.09), (0, 0, 0.215), "k_hat")
            mb.box((0.15, 0.15, 0.03), (0, 0, 0.27), "k_hat")
            mb.box((0.04, 0.04, 0.025), (0, 0, 0.29), "k_hat_shade")              # button
            mb.box((0.21, 0.08, 0.025), (0, 0.13, 0.18), "k_hat_shade")           # brim (front)
            mb.box((0.06, 0.02, 0.03), (0, -0.104, 0.19), "k_hat_shade")          # strap at the back
        self.part("cap", "hat", neck, cap)
        def bow(mb):
            mb.box((0.2, 0.2, 0.03), (0, 0, 0.22), "k_hat")                       # headband
            mb.box((0.11, 0.06, 0.09), (0.05, -0.04, 0.27), "k_hat", ry=30)
            mb.box((0.11, 0.06, 0.09), (0.15, -0.04, 0.27), "k_hat", ry=-30)
            mb.box((0.05, 0.07, 0.05), (0.1, -0.05, 0.27), "k_hat_shade")
        self.part("bow", "hat", neck, bow)
        if hardhats:
            for c in range(3):
                self.part(f"hh{c}", "hardhat", neck, lambda mb, c=c: climber.build_hardhat(mb, c, z=0.13))
        # ---- backpack (gear colour) + straps seen from the front
        def pack(mb):
            mb.box((0.22, 0.09, 0.19), (0, -0.125, 0.21), "k_gear")
            mb.box((0.22, 0.1, 0.05), (0, -0.13, 0.285), "k_gear_shade")       # flap
            mb.box((0.06, 0.02, 0.04), (0, -0.18, 0.25), "k_hat")              # buckle
            mb.box((0.16, 0.02, 0.07), (0, -0.172, 0.16), "k_gear_shade")      # pocket
            for s in (-1, 1):
                mb.box((0.04, 0.02, 0.24), (s * 0.08, 0.095, 0.2), "k_gear_shade")   # straps (front)
        self.part("pack", "pack", hips, pack)
        def cathead(mb):                                   # sleepy cat peeking out of the pack
            x, y, z = 0.07, -0.15, 0.33
            mb.box((0.15, 0.06, 0.11), (x, y, z), "k_cat")
            for s in (-1, 1):
                mb.box((0.045, 0.05, 0.05), (x + s * 0.05, y, z + 0.07), "k_cat", ry=45)
                mb.box((0.035, 0.02, 0.012), (x + s * 0.035, y - 0.035, z + 0.01), "black")   # closed eyes
            mb.box((0.06, 0.02, 0.035), (x, y - 0.035, z - 0.03), "k_cat_light")
            mb.box((0.02, 0.02, 0.015), (x, y - 0.04, z - 0.017), "k_nose")
            mb.box((0.06, 0.03, 0.04), (x - 0.12, y, z - 0.03), "k_cat")              # a paw over the edge
        self.part("cat", "cat", hips, cathead)
        if hardhats:
            self.shop_parts()

    # ---------------------------------------------------------------- coin-shop cosmetics
    def shop_parts(self):
        j = self.j
        hips, neck = j["hips"], j["neck"]
        def P(variant, name, parent, fn): self.part(variant, name, parent, fn)
        # ---- hats (neck pivot; the head top is at z ~0.2, hair top ~0.225)
        def party(mb):
            for i, (w, z) in enumerate(((0.16, 0.25), (0.12, 0.3), (0.085, 0.35), (0.05, 0.395))):
                mb.box((w, w, 0.055), (0.0, 0, z), "k_hat" if i % 2 == 0 else "f_gold")
            mb.box((0.06, 0.06, 0.05), (0, 0, 0.44), "white")
            mb.box((0.2, 0.2, 0.02), (0, 0, 0.215), "k_hat_shade")
        P("party", "hat", neck, party)
        def propeller(mb):
            mb.box((0.205, 0.205, 0.1), (0, 0, 0.21), "k_hat")
            for k, r in enumerate(("f_red", "r3", "r5", "r4")):
                mb.box((0.052, 0.21, 0.1), (-0.077 + k * 0.051, 0, 0.215), r)     # segments
            mb.box((0.02, 0.02, 0.06), (0, 0, 0.29), "f_dark")
            mb.box((0.32, 0.03, 0.025), (0, 0, 0.32), "f_red")                   # blades
            mb.box((0.04, 0.04, 0.03), (0, -0.01, 0.32), "f_gold")
        P("propeller", "hat", neck, propeller)
        def crown(mb):
            mb.box((0.21, 0.21, 0.06), (0, 0, 0.235), "f_gold")
            for x in (-0.08, 0.0, 0.08):
                mb.box((0.045, 0.21, 0.07), (x, 0, 0.29), "f_gold")
            mb.box((0.215, 0.215, 0.015), (0, 0, 0.21), "f_gold_d")
            for y in (-0.106, 0.106):
                mb.box((0.04, 0.01, 0.03), (0, y, 0.235), "f_red")
                mb.box((0.03, 0.01, 0.03), (-0.06, y, 0.235), "r5")
                mb.box((0.03, 0.01, 0.03), (0.06, y, 0.235), "r4")
        P("crown", "hat", neck, crown)
        def wizard(mb):
            mb.box((0.32, 0.27, 0.035), (0, 0, 0.215), "f_purple_d")
            for i, (w, z) in enumerate(((0.2, 0.26), (0.15, 0.32), (0.105, 0.38), (0.07, 0.43))):
                mb.box((w, w, 0.065), (0.01 * i, 0, z), "f_purple")
            mb.box((0.06, 0.06, 0.05), (0.07, 0, 0.47), "f_purple")                 # floppy tip
            mb.box((0.2, 0.205, 0.03), (0, 0, 0.245), "f_gold")                    # band
            for y in (-0.105, 0.105):
                mb.box((0.06, 0.01, 0.02), (0.02, y * 0.8, 0.33), "f_gold")
                mb.box((0.02, 0.01, 0.06), (0.02, y * 0.8, 0.33), "f_gold")
        P("wizard", "hat", neck, wizard)
        def trapper(mb):
            mb.box((0.205, 0.205, 0.1), (0, 0, 0.215), "f_red")
            for x in (-0.06, 0.04):
                mb.box((0.025, 0.21, 0.1), (x, 0, 0.215), "f_dark")                 # plaid lines
            mb.box((0.21, 0.21, 0.02), (0, 0, 0.23), "f_dark")
            for s in (-1, 1):
                mb.box((0.04, 0.1, 0.13), (s * 0.11, 0, 0.14), "f_cream")           # ear flaps
            mb.box((0.215, 0.215, 0.035), (0, 0, 0.175), "f_cream")
        P("trapper", "hat", neck, trapper)
        def viking(mb):
            mb.box((0.21, 0.21, 0.09), (0, 0, 0.22), "f_silver")
            mb.box((0.15, 0.16, 0.04), (0, 0, 0.28), "f_silver")
            mb.box((0.215, 0.215, 0.03), (0, 0, 0.18), "f_silver_d")
            mb.box((0.03, 0.22, 0.12), (0, 0, 0.23), "f_silver_d")
            for s in (-1, 1):                                                       # soft, rounded horns
                mb.bar((s * 0.1, 0.23), (s * 0.18, 0.3), 0.05, 0, "f_cream")
                mb.bar((s * 0.18, 0.3), (s * 0.19, 0.39), 0.04, 0, "f_cream")
                mb.box((0.035, 0.035, 0.03), (s * 0.19, 0, 0.41), "white")
        P("viking", "hat", neck, viking)
        def santa(mb):
            mb.box((0.2, 0.2, 0.08), (0, 0, 0.24), "f_red")
            mb.box((0.15, 0.15, 0.06), (0.04, 0, 0.3), "f_red")
            mb.box((0.09, 0.09, 0.05), (0.1, 0, 0.34), "f_red")
            mb.box((0.06, 0.06, 0.05), (0.15, 0, 0.32), "f_red_d")
            mb.box((0.07, 0.07, 0.06), (0.19, 0, 0.29), "white")                    # pompom
            mb.box((0.225, 0.225, 0.05), (0, 0, 0.195), "white")                    # fur trim
        P("santa", "hat", neck, santa)
        def tricorn(mb):
            mb.box((0.19, 0.19, 0.08), (0, 0, 0.24), "f_dark")
            mb.box((0.34, 0.27, 0.035), (0, 0, 0.21), "f_dark")
            for s in (-1, 1):
                mb.bar((s * 0.12, 0.215), (s * 0.19, 0.29), 0.04, 0, "f_dark")      # turned-up sides
            mb.box((0.345, 0.275, 0.012), (0, 0, 0.228), "f_gold")
            for y in (-0.097, 0.097):
                mb.box((0.05, 0.01, 0.05), (0, y, 0.255), "f_gold")                 # badge
        P("tricorn", "hat", neck, tricorn)
        def goathorns(mb):                                                          # Goat set: horns headband
            mb.box((0.215, 0.215, 0.03), (0, 0, 0.215), "f_cream")
            for sd in (-1, 1):
                mb.bar((sd * 0.07, 0.22), (sd * 0.13, 0.31), 0.045, 0, "f_silver")
                mb.bar((sd * 0.13, 0.31), (sd * 0.2, 0.33), 0.04, 0, "f_silver_d")
                mb.box((0.06, 0.03, 0.035), (sd * 0.13, 0, 0.17), "f_cream", ry=sd * 30)   # little ears
        P("goathorns", "hat", neck, goathorns)
        def coonskin(mb):                                                           # Mountain Man set: fur cap + tail
            mb.box((0.215, 0.215, 0.11), (0, 0, 0.225), "f_brown")
            mb.box((0.22, 0.22, 0.03), (0, 0, 0.18), "f_brown_d")
            for k in range(4):
                mb.box((0.05, 0.05, 0.06), (0.08 + k * 0.012, 0.09, 0.17 - k * 0.055), "f_brown_d" if k % 2 else "f_cream")
        P("coonskin", "hat", neck, coonskin)
        def furhood(mb):                                                            # Bigfoot set: furry hood with ears
            mb.box((0.23, 0.23, 0.12), (0, 0, 0.22), "f_brown_d")
            for sd in (-1, 1):
                mb.box((0.05, 0.05, 0.05), (sd * 0.09, 0, 0.3), "f_brown_d")
                mb.box((0.04, 0.24, 0.16), (sd * 0.115, 0, 0.14), "f_brown_d")
            for x in (-0.06, 0.0, 0.06):
                mb.box((0.03, 0.235, 0.03), (x, 0, 0.285), "f_brown")
        P("furhood", "hat", neck, furhood)
        def elfhat(mb):                                                             # Elf set: floppy pointy hat + bell
            mb.box((0.225, 0.225, 0.05), (0, 0, 0.195), "f_red")
            for k in range(5):
                w = 0.2 * (1 - k / 5.5)
                mb.box((w, w, 0.05), (0.02 * k, 0, 0.24 + k * 0.045), "f_green" if k % 2 else "f_green_d")
            mb.box((0.06, 0.06, 0.06), (0.12, 0, 0.44), "f_gold")
        P("elfhat", "hat", neck, elfhat)
        def antlers(mb):                                                            # Rudolph set: antler headband
            mb.box((0.215, 0.215, 0.03), (0, 0, 0.215), "f_brown_d")
            for sd in (-1, 1):
                mb.bar((sd * 0.07, 0.22), (sd * 0.15, 0.36), 0.035, 0, "f_brown")
                mb.bar((sd * 0.11, 0.29), (sd * 0.05, 0.36), 0.03, 0, "f_brown")
                mb.bar((sd * 0.14, 0.33), (sd * 0.21, 0.37), 0.03, 0, "f_brown")
        P("antlers", "hat", neck, antlers)
        def icecrown(mb):                                                           # Ice Giant set: crown of icicles
            mb.box((0.225, 0.225, 0.04), (0, 0, 0.21), "f_ice_d")
            for k, x in enumerate((-0.09, -0.045, 0.0, 0.045, 0.09)):
                h = 0.06 + 0.04 * (k % 2 == 0) + 0.03 * (k == 2)
                for y in (-0.1, 0.1):
                    mb.box((0.03, 0.02, h), (x, y, 0.23 + h / 2), "f_ice" if k % 2 else "white")
        P("icecrown", "hat", neck, icecrown)
        def earmuffs(mb):                                                           # Yeti set: fluffy earmuffs
            mb.box((0.03, 0.2, 0.03), (0, 0, 0.255), "f_ice_d")
            for sd in (-1, 1):
                mb.box((0.03, 0.03, 0.1), (sd * 0.1, 0, 0.21), "f_ice_d")
                mb.box((0.07, 0.11, 0.11), (sd * 0.125, 0, 0.15), "white")
        P("earmuffs", "hat", neck, earmuffs)
        def gnomehat(mb):                                                           # Gnome set: tall red pointy hat
            for k in range(6):
                w = 0.23 * (1 - k / 6.3)
                mb.box((w, w, 0.06), (0, 0, 0.2 + k * 0.055), "f_red" if k % 2 else "f_red_d")
        P("gnomehat", "hat", neck, gnomehat)
        def featherhat(mb):                                                         # Rumpelstiltskin set: crumpled hat + feather
            mb.box((0.23, 0.23, 0.1), (0, 0, 0.23), "f_brown")
            mb.box((0.17, 0.17, 0.06), (0.02, 0, 0.3), "f_brown")
            mb.box((0.235, 0.235, 0.03), (0, 0, 0.2), "f_gold")
            mb.bar((0.1, 0.25), (0.2, 0.38), 0.03, 0.08, "f_red")
        P("featherhat", "hat", neck, featherhat)
        def tiara(mb):                                                              # Rapunzel set: gold tiara
            mb.box((0.215, 0.215, 0.03), (0, 0, 0.22), "f_gold")
            for x, h in ((-0.06, 0.04), (0.0, 0.07), (0.06, 0.04)):
                mb.box((0.03, 0.02, h), (x, -0.1, 0.235 + h / 2), "f_gold")
            mb.box((0.03, 0.02, 0.03), (0, -0.112, 0.27), "f_purple")
        P("tiara", "hat", neck, tiara)
        def dwarfhelm(mb):                                                          # Dwarf King set: horned iron helm
            mb.box((0.23, 0.23, 0.1), (0, 0, 0.23), "f_silver_d")
            mb.box((0.235, 0.235, 0.03), (0, 0, 0.19), "f_gold")
            mb.box((0.03, 0.02, 0.08), (0, -0.12, 0.2), "f_silver")
            for sd in (-1, 1):
                mb.bar((sd * 0.11, 0.25), (sd * 0.18, 0.33), 0.035, 0, "f_cream")
        P("dwarfhelm", "hat", neck, dwarfhelm)
        # ---- outfit patterns (over the body, under hair / pack)
        sh = {s: j[f"sh_{s}"] for s in "LR"}
        def sleeves(variant, roles, bands=()):
            for s in "LR":
                def fn(mb):
                    mb.box((0.098, 0.098, 0.205), (0, 0, -0.1), roles)
                    for z, r in bands:
                        mb.box((0.1, 0.1, 0.03), (0, 0, z), r)
                P(variant, "sleeve_" + s, sh[s], fn)
        def stripes(mb):
            for z in (0.1, 0.18, 0.26):
                mb.box((0.31, 0.19, 0.035), (0, 0, z), "white")
        P("stripes", "torso", hips, stripes)
        for s in "LR":
            P("stripes", "arm_" + s, sh[s], lambda mb: [mb.box((0.1, 0.1, 0.03), (0, 0, z), "white") for z in (-0.06, -0.14)])
        def overalls(mb):
            for y in (-0.093, 0.093):
                mb.box((0.2, 0.012, 0.17), (0, y, 0.15), "k_pants")
                for x in (-0.08, 0.08):
                    mb.box((0.04, 0.012, 0.12), (x, y, 0.29), "k_pants")
                    mb.box((0.03, 0.014, 0.03), (x, y, 0.235), "f_gold")
            mb.box((0.28, 0.17, 0.08), (0, 0, 0.06), "k_pants")
            mb.box((0.08, 0.014, 0.05), (0, 0.094, 0.15), "k_shirt_shade")        # pocket
        P("overalls", "torso", hips, overalls)
        def robe(mb):
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_purple")
            mb.box((0.36, 0.22, 0.2), (0, 0, -0.03), "f_purple")
            mb.box((0.37, 0.225, 0.03), (0, 0, -0.12), "f_gold")
            mb.box((0.31, 0.195, 0.03), (0, 0, 0.34), "f_gold")
            for x, z in ((-0.09, 0.22), (0.07, 0.12), (0.1, 0.27), (-0.05, 0.02)):
                for y in (-0.112, 0.112):
                    mb.box((0.035, 0.01, 0.035), (x, y, z), "f_gold")
        P("robe", "torso", hips, robe)
        sleeves("robe", "f_purple", ((-0.19, "f_gold"),))
        def plaid(mb):
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_red")
            for x in (-0.09, 0.0, 0.09):
                mb.box((0.025, 0.195, 0.3), (x, 0, 0.2), "f_dark")
            for z in (0.12, 0.24):
                mb.box((0.315, 0.195, 0.025), (0, 0, z), "f_dark")
        P("plaid", "torso", hips, plaid)
        sleeves("plaid", "f_red", ((-0.06, "f_dark"), (-0.14, "f_dark")))
        def vest(mb):
            mb.box((0.31, 0.19, 0.27), (0, 0, 0.19), "f_brown")
            mb.box((0.12, 0.02, 0.27), (0, 0.093, 0.19), "k_shirt")                # open front
            mb.box((0.32, 0.2, 0.05), (0, 0, 0.06), "f_cream")                      # fur trim
            mb.box((0.32, 0.2, 0.05), (0, 0, 0.33), "f_cream")
            mb.box((0.05, 0.01, 0.05), (0, -0.1, 0.2), "f_gold")
        P("vest", "torso", hips, vest)
        def bandana(mb):                                                            # Goat set: farm bandana + bell
            mb.box((0.32, 0.2, 0.06), (0, 0, 0.32), "f_red")
            mb.box((0.12, 0.02, 0.1), (0, 0.1, 0.27), "f_red")
            mb.box((0.06, 0.02, 0.06), (0, 0.105, 0.21), "f_gold")
        P("bandana", "torso", hips, bandana)
        def buckskin(mb):                                                           # Mountain Man set: fringed jacket
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_cream")
            for x in (-0.12, -0.06, 0.0, 0.06, 0.12):
                mb.box((0.02, 0.2, 0.06), (x, 0, 0.06), "f_brown")
            mb.box((0.315, 0.195, 0.03), (0, 0, 0.28), "f_brown")
        P("buckskin", "torso", hips, buckskin)
        sleeves("buckskin", "f_cream", ((-0.16, "f_brown"),))
        def furcoat(mb):                                                            # Bigfoot set: shaggy fur suit
            mb.box((0.32, 0.2, 0.31), (0, 0, 0.2), "f_brown_d")
            for x, z in ((-0.1, 0.1), (0.04, 0.16), (0.11, 0.26), (-0.04, 0.3), (0.08, 0.06)):
                for y in (-0.1, 0.1):
                    mb.box((0.03, 0.01, 0.07), (x, y, z), "f_brown")
        P("furcoat", "torso", hips, furcoat)
        sleeves("furcoat", "f_brown_d")
        def tunic(mb):                                                              # Elf set: green tunic, zigzag hem, belt
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_green")
            for k in range(6):
                mb.box((0.05, 0.2, 0.05), (-0.13 + k * 0.052, 0, 0.03), "f_red" if k % 2 else "f_green_d")
            mb.box((0.315, 0.195, 0.04), (0, 0, 0.12), "f_dark")
            mb.box((0.06, 0.2, 0.05), (0, 0, 0.12), "f_gold")
        P("tunic", "torso", hips, tunic)
        sleeves("tunic", "f_green", ((-0.17, "f_red"),))
        def jumper(mb):                                                             # Rudolph set: reindeer jumper
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_red_d")
            for z in (0.08, 0.3):
                mb.box((0.315, 0.195, 0.03), (0, 0, z), "white")
            for x in (-0.09, 0.0, 0.09):
                mb.box((0.03, 0.195, 0.03), (x, 0, 0.19), "white")
            mb.box((0.04, 0.2, 0.04), (0, 0, 0.19), "f_red")
        P("jumper", "torso", hips, jumper)
        sleeves("jumper", "f_red_d", ((-0.08, "white"),))
        def frostcape(mb):                                                          # Ice Giant set: frosty cape
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_ice_d")
            mb.box((0.33, 0.21, 0.06), (0, 0, 0.32), "white")
            for k in range(5):
                mb.box((0.04, 0.2, 0.06 + 0.03 * (k % 2)), (-0.12 + k * 0.06, 0, 0.04), "f_ice")
        P("frostcape", "torso", hips, frostcape)
        sleeves("frostcape", "f_ice_d", ((-0.17, "white"),))
        def scarf(mb):                                                              # Yeti set: long striped scarf
            mb.box((0.32, 0.2, 0.07), (0, 0, 0.32), "f_red")
            for k in range(4):
                mb.box((0.07, 0.02, 0.06), (0.08, 0.1, 0.26 - k * 0.06), "f_red" if k % 2 else "white")
        P("scarf", "torso", hips, scarf)
        def gnomevest(mb):                                                          # Gnome set: blue tunic + belt
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "r5")
            mb.box((0.315, 0.195, 0.04), (0, 0, 0.1), "f_dark")
            mb.box((0.06, 0.2, 0.05), (0, 0, 0.1), "f_gold")
        P("gnomevest", "torso", hips, gnomevest)
        sleeves("gnomevest", "r5")
        def goldvest(mb):                                                           # Rumpelstiltskin set: gold-spun vest
            mb.box((0.31, 0.19, 0.27), (0, 0, 0.19), "f_gold")
            for z in (0.1, 0.2, 0.3):
                mb.box((0.315, 0.195, 0.02), (0, 0, z), "f_gold_d")
            mb.box((0.1, 0.02, 0.27), (0, 0.093, 0.19), "k_shirt")
        P("goldvest", "torso", hips, goldvest)
        def gown(mb):                                                               # Rapunzel set: purple gown
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_purple")
            mb.box((0.36, 0.22, 0.2), (0, 0, -0.03), "f_purple")
            mb.box((0.315, 0.195, 0.04), (0, 0, 0.12), "f_gold")
        P("gown", "torso", hips, gown)
        sleeves("gown", "f_purple", ((-0.18, "f_gold"),))
        def chainmail(mb):                                                          # Dwarf King set: chainmail + gold belt
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_silver")
            for z in (0.08, 0.16, 0.24, 0.32):
                mb.box((0.315, 0.195, 0.02), (0, 0, z), "f_silver_d")
            mb.box((0.315, 0.195, 0.05), (0, 0, 0.1), "f_gold")
        P("chainmail", "torso", hips, chainmail)
        sleeves("chainmail", "f_silver", ((-0.1, "f_silver_d"),))
        def suit(mb):
            mb.box((0.31, 0.19, 0.3), (0, 0, 0.2), "f_red")
            mb.box((0.315, 0.195, 0.05), (0, 0, 0.07), "f_dark")                    # belt
            mb.box((0.07, 0.2, 0.055), (0, 0, 0.07), "f_gold")
            mb.box((0.32, 0.2, 0.04), (0, 0, 0.0), "white")
            mb.box((0.05, 0.01, 0.3), (0, 0.096, 0.2), "white")                     # fur front
        P("suit", "torso", hips, suit)
        sleeves("suit", "f_red", ((-0.17, "white"),))
        def sash(mb):
            for y in (-0.1, 0.1):
                mb.bar((-0.16, 0.33), (0.16, 0.08), 0.06, y, "f_red", depth=0.01)
            mb.box((0.315, 0.195, 0.045), (0, 0, 0.06), "f_dark")
            mb.box((0.06, 0.2, 0.05), (0, 0, 0.06), "f_gold")
        P("sash", "torso", hips, sash)
        # ---- backpack styles (replace the classic pack; straps on the front)
        def straps(mb, role):
            for s in (-1, 1):
                mb.box((0.04, 0.02, 0.24), (s * 0.08, 0.095, 0.2), role)
        def teddy(mb):
            mb.box((0.22, 0.09, 0.2), (0, -0.125, 0.2), "f_brown")
            mb.box((0.18, 0.1, 0.03), (0, -0.125, 0.315), "f_brown")
            for s in (-1, 1):
                mb.box((0.065, 0.07, 0.065), (s * 0.085, -0.13, 0.33), "f_brown")       # ears
                mb.box((0.03, 0.02, 0.03), (s * 0.085, -0.17, 0.33), "f_cream")
                mb.box((0.025, 0.02, 0.025), (s * 0.05, -0.172, 0.25), "black")        # eyes
            mb.box((0.09, 0.02, 0.06), (0, -0.172, 0.19), "f_cream")
            mb.box((0.03, 0.02, 0.02), (0, -0.18, 0.205), "black")
            straps(mb, "f_brown_d")
        P("teddy", "pack", hips, teddy)
        def rocket(mb):
            for s in (-1, 1):
                mb.box((0.085, 0.09, 0.22), (s * 0.055, -0.125, 0.2), "f_silver")
                mb.box((0.06, 0.08, 0.04), (s * 0.055, -0.125, 0.33), "f_red")
                mb.box((0.05, 0.07, 0.04), (s * 0.055, -0.125, 0.07), "f_dark")
                mb.box((0.04, 0.06, 0.05), (s * 0.055, -0.125, 0.03), "f_flame")
                mb.box((0.02, 0.05, 0.04), (s * 0.055, -0.125, -0.005), "r3")
                mb.box((0.03, 0.02, 0.1), (s * 0.055, -0.175, 0.2), "f_silver_d")
            mb.box((0.04, 0.08, 0.16), (0, -0.12, 0.2), "f_dark")
            straps(mb, "f_dark")
        P("rocket", "pack", hips, rocket)
        def wings(mb):
            for s in (-1, 1):
                mb.bar((s * 0.04, 0.26), (s * 0.3, 0.4), 0.13, -0.12, "k_gear", depth=0.03)
                mb.bar((s * 0.04, 0.2), (s * 0.24, 0.1), 0.1, -0.12, "k_gear", depth=0.03)
                mb.box((0.05, 0.02, 0.05), (s * 0.2, -0.14, 0.36), "white")
                mb.box((0.04, 0.02, 0.04), (s * 0.17, -0.14, 0.13), "white")
            mb.box((0.06, 0.08, 0.18), (0, -0.13, 0.22), "k_gear_shade")
            straps(mb, "k_gear_shade")
        P("wings", "pack", hips, wings)

    def part(self, variant, name, parent, build):
        mb = MeshBuilder()
        build(mb)
        ob = mb.to_object(f"{self.prefix}{variant}_{name}", self.coll)
        ob.parent = parent
        self.layers.setdefault(variant, []).append(ob)
        return ob

    def animate(self):
        climber.animate(self.root, self.j)
        for name, pose in extra_poses().items():
            climber.set_pose(self.j, EXTRA_FRAMES[name], pose)
        for ob in self.j.values():
            if ob.animation_data and ob.animation_data.action:
                for fc in ob.animation_data.action.fcurves:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"

    # ---- layer rendering
    def show(self, layer, body, mask_mat):
        """Show `layer` in its colours and `body` (+ pack for the cat) in the mask colour."""
        maskers = list(self.layers[body]) + (self.layers["pack"] if layer == "cat" else [])
        for v, obs in self.layers.items():
            for ob in obs:
                on = v == layer or ob in maskers
                ob.hide_render = not on
                masked = on and v != layer
                for s in ob.material_slots:
                    if masked:
                        s.link = "OBJECT"
                        s.material = mask_mat
                    else:
                        s.link = "DATA"


def mask_material():
    from common import hex_rgb, srgb_to_linear
    m = bpy.data.materials.new("MASK")
    r, g, b = (srgb_to_linear(v / 255) for v in hex_rgb(KEYS["k_mask"]))
    m.diffuse_color = (r, g, b, 1)
    return m


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def render_pip(raw, ppu=32, cell=72, center=1.02):
    """Pip layers: p_<layer>_<pose>.png (back view) and p_<layer>_f_<pose>.png (front view)."""
    sc = bpy.context.scene
    coll = new_collection("Pip")
    pip = Pip(coll, "pip_", climber.SCALE)
    pip.animate()
    mm = mask_material()
    pip.root.location = (2000, 0, 0)
    setup_workbench(sc, cell, cell, transparent=True)
    centers = {"fall": (2000 - 0.25, center - 0.17)}
    layers = BODIES + HAIRS + HATS + ["pack", "cat"] + SHOP_HATS + PATTERNS + PACK_STYLES
    out = []
    for view, poses in (("", BACK_POSES), ("f", FRONT_POSES)):
        pip.root.rotation_euler.z = math.pi if view else 0
        for pname, frame in poses:
            sc.frame_set(frame)
            ortho_camera(sc, centers.get(pname, (2000, center)), cell / ppu, "HORIZONTAL")
            todo = layers + ([f"hh{c}" for c in range(3)] if pname in GAME_POSES else [])
            if view:
                todo = [l for l in todo if l != "cat"]
            for layer in todo:
                pip.show(layer, layer if layer in BODIES else "boy", mm)
                n = f"p_{layer}_{pname}"
                render(os.path.join(raw, n + ".png"))
                out.append(n)
    pip.root.rotation_euler.z = 0
    for obs in pip.layers.values():
        for ob in obs:
            ob.hide_render = True
    return out


def render_town(raw, ppu=32, cell=56, center=0.8):
    """Townsfolk: smaller Pip-rig kids/adults seen from the FRONT: t_<layer>_<pose>.png."""
    sc = bpy.context.scene
    coll = new_collection("Town")
    tp = Pip(coll, "town_", 1.0, hardhats=False)
    tp.animate()
    mm = mask_material()
    tp.root.location = (3000, 0, 0)
    tp.root.rotation_euler.z = math.pi
    setup_workbench(sc, cell, cell, transparent=True)
    out = []
    for pname, frame in TOWN_POSES:
        sc.frame_set(frame)
        ortho_camera(sc, (3000, center), cell / ppu, "HORIZONTAL")
        for layer in BODIES + HAIRS + HATS:
            tp.show(layer, layer if layer in BODIES else "boy", mm)
            n = f"t_{layer}_{pname}"
            render(os.path.join(raw, n + ".png"))
            out.append(n)
    for obs in tp.layers.values():
        for ob in obs:
            ob.hide_render = True
    return out


# ---------------------------------------------------------------- props (story items)
def book(mb):                       # the Wizard's spell book (closed, front cover)
    mb.box((0.62, 0.12, 0.74), (0, 0, 0), "acc1")
    mb.box((0.06, 0.13, 0.74), (-0.31, -0.005, 0), "black")             # spine
    mb.box((0.52, 0.1, 0.06), (0.04, 0.0, -0.37), "white")               # page edges
    mb.box((0.5, 0.02, 0.62), (0.03, -0.065, 0.02), "acc1")
    mb.box((0.36, 0.02, 0.06), (0.04, -0.075, 0.2), "acc3")
    mb.box((0.18, 0.02, 0.06), (0.04, -0.08, -0.04), "acc3")             # star
    mb.box((0.06, 0.02, 0.18), (0.04, -0.08, -0.04), "acc3")
    mb.box((0.12, 0.02, 0.12), (0.04, -0.078, -0.04), "acc3", ry=45)
    for z in (0.3, -0.3):
        mb.box((0.08, 0.025, 0.08), (0.28, -0.07, z), "acc3")            # corner caps


def page(mb):
    mb.box((0.42, 0.04, 0.52), (0, 0, 0), "hair4")
    mb.box((0.34, 0.02, 0.46), (0, -0.03, 0), "white")
    for i, z in enumerate((0.15, 0.06, -0.03, -0.12)):
        mb.box((0.24 - 0.06 * (i % 2), 0.02, 0.03), (-0.02, -0.045, z), "hair2")
    mb.box((0.07, 0.02, 0.07), (0.1, -0.05, -0.17), "acc1", ry=45)        # tiny star


def toy_phone(mb):                   # Grandpa level: the toy phone Pip carries up (the grandkids are on the line)
    mb.box((0.62, 0.3, 0.3), (0, 0, -0.14), "shirt")                     # base
    mb.box((0.5, 0.3, 0.1), (0, 0, 0.04), "shirt")
    mb.disc(0.17, (0, -0.16, -0.12), "white", seg=10, depth=0.03)        # dial
    for k in range(6):
        a = 2 * math.pi * k / 6
        mb.disc(0.03, (0.11 * math.cos(a), -0.19, -0.12 + 0.11 * math.sin(a)), "acc3", seg=6, depth=0.02)
    mb.box((0.74, 0.3, 0.12), (0, -0.02, 0.2), "shirt")                  # handset
    for s in (-1, 1):
        mb.box((0.18, 0.32, 0.14), (s * 0.33, -0.02, 0.15), "shirt")
    mb.box((0.5, 0.02, 0.04), (0, -0.18, 0.24), "white")                 # shine
    for k in range(4):                                                   # curly cord
        mb.disc(0.05, (0.36 + 0.02 * k, -0.1, -0.02 - 0.08 * k), "black", seg=6, depth=0.03)
    for x in (-0.22, 0.22):
        mb.box((0.1, 0.3, 0.06), (x, 0, -0.32), "black")                 # wheels (it's a pull toy)


def photo(mb):                       # Grandpa level: a family photo (replaces the spell-book pages)
    mb.box((0.5, 0.04, 0.56), (0, 0, 0), "white")
    mb.box((0.4, 0.02, 0.32), (0, -0.03, 0.06), "pants")                  # sky
    mb.box((0.4, 0.02, 0.1), (0, -0.035, -0.06), "acc2")                  # grass
    for x, h, col in ((-0.1, 0.2, "skin"), (0.08, 0.14, "skin")):         # two little grandkids
        mb.box((0.08, 0.02, 0.08), (x, -0.045, -0.02 + h), col)
        mb.box((0.1, 0.02, 0.1), (x, -0.045, -0.06 + h * 0.4), "shirt" if x < 0 else "acc1")
    mb.box((0.06, 0.02, 0.05), (0.14, -0.04, -0.2), "acc1")               # heart doodle



# ---------------------------------------------------------------- World 1 story props (Pip carries one up; collectibles)
def turnip(mb):                      # the Goat: a big juicy turnip
    mb.disc(0.3, (0, 0, -0.06), "white", seg=12, depth=0.3)
    mb.disc(0.27, (0, -0.02, 0.06), "f_purple", seg=12, depth=0.28, sz=0.6)      # purple shoulders
    mb.bar((0, -0.34), (0.02, -0.48), 0.05, 0, "f_cream")                       # root tail
    for x, a in ((-0.12, -0.18), (0.0, 0.0), (0.12, 0.18)):
        mb.bar((x * 0.5, 0.2), (x + a, 0.62), 0.12, 0, "r4")                     # leafy top
    mb.box((0.08, 0.02, 0.12), (-0.12, -0.16, -0.02), "f_cream")                 # shine


def pancake_stack(mb):               # the Lumberjack: a tall syrupy pancake stack with butter
    mb.box((0.84, 0.3, 0.05), (0, 0, -0.34), "white")                          # plate
    for k in range(4):
        z = -0.26 + k * 0.13
        mb.box((0.62, 0.3, 0.12), (0, 0, z), "f_brown")
        mb.box((0.64, 0.3, 0.04), (0, -0.02, z + 0.02), "f_gold")
    mb.box((0.62, 0.3, 0.07), (0, -0.03, 0.27), "f_flame")                     # syrup
    for x, ln in ((-0.24, 0.24), (0.04, 0.34), (0.26, 0.16)):
        mb.box((0.06, 0.05, ln), (x, -0.17, 0.27 - ln / 2), "f_flame")          # drips
    mb.box((0.18, 0.12, 0.1), (0.02, -0.05, 0.35), "r3")                       # butter


def compass(mb):                     # Mountain Man: his trusty brass compass
    mb.disc(0.3, (0, 0, 0), "f_gold", seg=14, depth=0.1)
    mb.disc(0.23, (0, -0.06, 0), "white", seg=14, depth=0.02)
    mb.bar((0, -0.18), (0, 0.18), 0.07, -0.08, "f_dark")
    mb.bar((0, 0.02), (0, 0.18), 0.07, -0.09, "f_red")                         # north needle
    mb.disc(0.04, (0, -0.1, 0), "f_gold", seg=6, depth=0.02)
    mb.box((0.12, 0.08, 0.1), (0, 0, 0.33), "f_gold")                          # ring
    mb.box((0.04, 0.02, 0.04), (0.12, -0.08, 0.12), "white")


def selfie_cam(mb):                  # Bigfoot: an instant camera for the selfie
    mb.box((0.66, 0.3, 0.46), (0, 0, 0), "r5")
    mb.box((0.66, 0.31, 0.12), (0, 0, -0.18), "white")                         # photo slot
    mb.disc(0.16, (0, -0.16, 0.03), "f_dark", seg=12, depth=0.05)              # lens
    mb.disc(0.09, (0, -0.2, 0.03), "r6", seg=10, depth=0.03)
    mb.box((0.14, 0.02, 0.09), (0.21, -0.16, 0.15), "r3")                       # flash
    mb.box((0.1, 0.1, 0.05), (-0.22, 0, 0.25), "f_red")                         # button
    for k, c in enumerate(("f_red", "r2", "r3", "r4")):
        mb.box((0.04, 0.02, 0.2), (-0.26 + k * 0.045, -0.16, 0.0), c)          # rainbow stripe


def clover(mb):                      # Goat collectible: a lucky four-leaf clover
    for a in range(4):
        ang = a * math.pi / 2 + math.pi / 4
        mb.disc(0.13, (0.15 * math.cos(ang), 0, 0.05 + 0.15 * math.sin(ang)), "r4", seg=8, depth=0.05)
    mb.disc(0.05, (0, -0.03, 0.05), "white", seg=6, depth=0.02)
    mb.bar((0, -0.04), (0.06, -0.3), 0.05, 0, "r4")


def maple_leaf(mb):                  # Lumberjack collectible
    pts = [(0, 0.3), (-0.12, 0.12), (-0.28, 0.16), (-0.2, -0.02), (-0.26, -0.12), (0, -0.08), (0.26, -0.12), (0.2, -0.02), (0.28, 0.16), (0.12, 0.12)]
    for p in pts:
        mb.bar((0, 0.04), p, 0.13, 0, "f_flame")
    mb.disc(0.12, (0, 0, 0.06), "f_red", seg=8, depth=0.06)
    mb.bar((0, -0.08), (0.02, -0.32), 0.04, -0.02, "f_brown")


def feather(mb):                     # Mountain Man collectible
    mb.bar((-0.06, -0.32), (0.08, 0.32), 0.04, -0.02, "white")
    for k in range(7):
        t = -0.24 + k * 0.08
        w = 0.15 * math.sin(math.pi * (k + 1) / 8)
        mb.bar((t * 0.22, t), (t * 0.22 - w, t + 0.08), 0.07, 0, "r5" if k % 3 else "f_gold")
        mb.bar((t * 0.22, t), (t * 0.22 + w, t + 0.08), 0.07, 0, "r5" if k % 3 else "f_gold")


def berries(mb):                     # Bigfoot collectible: a bunch of wild blueberries
    for x, z in ((-0.12, 0.0), (0.12, 0.0), (0.0, -0.17), (0.0, 0.14)):
        mb.disc(0.12, (x, 0, z), "r6", seg=10, depth=0.2)
        mb.box((0.04, 0.02, 0.04), (x - 0.04, -0.12, z + 0.04), "white")
    mb.bar((0, 0.22), (0.12, 0.38), 0.12, 0, "r4")                              # leaf

# ---------------------------------------------------------------- World 2 story props + collectibles
def hammer(mb):                      # the Elf: the lost toy-maker's hammer
    mb.bar((-0.05, -0.42), (0.03, 0.18), 0.09, 0, "f_brown")
    mb.box((0.42, 0.18, 0.18), (0.03, 0, 0.24), "f_silver")
    mb.box((0.1, 0.19, 0.19), (0.2, 0, 0.24), "f_silver_d")
    mb.box((0.1, 0.02, 0.05), (-0.06, -0.1, 0.28), "white")
    mb.box((0.11, 0.1, 0.06), (-0.04, 0, -0.38), "f_red")


def lantern(mb):                     # Rudolph: a warm glowing lantern
    mb.box((0.36, 0.3, 0.44), (0, 0, -0.04), "f_dark")
    mb.box((0.28, 0.31, 0.34), (0, 0, -0.04), "r3")
    mb.box((0.14, 0.32, 0.2), (0, 0, -0.06), "f_flame")
    mb.box((0.42, 0.32, 0.06), (0, 0, 0.2), "f_red")
    mb.box((0.42, 0.32, 0.06), (0, 0, -0.28), "f_red")
    mb.bar((-0.1, 0.24), (0, 0.36), 0.05, 0, "f_dark")
    mb.bar((0.1, 0.24), (0, 0.36), 0.05, 0, "f_dark")


def mitten(mb):                      # the Ice Giant: a warm knitted mitten
    mb.disc(0.24, (0, 0, 0.04), "f_red", seg=12, depth=0.22, sz=1.25)
    mb.disc(0.1, (-0.24, 0, 0.0), "f_red", seg=8, depth=0.2, sz=1.4)                 # thumb
    mb.box((0.5, 0.24, 0.14), (0, 0, -0.3), "white")                                 # cuff
    for x in (-0.12, 0.0, 0.12):
        mb.box((0.06, 0.02, 0.06), (x, -0.13, 0.12), "white")                       # snowflake knit dots
    mb.box((0.2, 0.02, 0.04), (0, -0.13, 0.0), "white")


def cocoa(mb):                       # the Yeti: a big mug of cocoa + a cosy scarf
    mb.box((0.4, 0.32, 0.44), (-0.04, 0, -0.04), "r5")
    mb.box((0.34, 0.3, 0.06), (-0.04, 0, 0.2), "f_brown")
    mb.box((0.1, 0.1, 0.08), (-0.1, -0.03, 0.25), "white")
    for z in (-0.14, 0.08):
        mb.bar((0.16, z), (0.28, z), 0.07, 0, "r5")
    mb.bar((0.28, -0.14), (0.28, 0.08), 0.07, 0, "r5")
    mb.bar((-0.36, -0.3), (0.3, -0.26), 0.12, -0.18, "f_red")                         # the scarf, draped round
    for x in (-0.2, 0.04, 0.24):
        mb.box((0.05, 0.02, 0.13), (x, -0.25, -0.28), "white")
    for k in range(3):
        mb.bar((-0.06 + k * 0.08, 0.34), (-0.02 + k * 0.08, 0.46), 0.03, 0, "white")  # steam


def bigcookie(mb):                   # Santa: a BIG chocolate-chip cookie
    mb.disc(0.36, (0, 0, 0), "f_brown", seg=14, depth=0.12)
    mb.disc(0.3, (0.02, -0.07, 0.02), "r2", seg=14, depth=0.02)
    for x, z in ((-0.14, 0.12), (0.12, 0.14), (0.0, -0.06), (-0.16, -0.12), (0.16, -0.08), (0.04, 0.24)):
        mb.box((0.08, 0.03, 0.08), (x, -0.09, z), "f_brown_d")


def gingerbread(mb):                 # Elf collectible: a gingerbread friend
    mb.disc(0.13, (0, 0, 0.22), "f_brown", seg=10, depth=0.08)
    mb.box((0.22, 0.08, 0.24), (0, 0, -0.02), "f_brown")
    for s in (-1, 1):
        mb.bar((s * 0.1, 0.06), (s * 0.24, -0.02), 0.09, 0, "f_brown")
        mb.bar((s * 0.06, -0.12), (s * 0.12, -0.3), 0.1, 0, "f_brown")
        mb.box((0.03, 0.02, 0.03), (s * 0.05, -0.05, 0.24), "white")
    mb.box((0.04, 0.02, 0.04), (0, -0.05, 0.04), "f_red")
    mb.box((0.04, 0.02, 0.04), (0, -0.05, -0.06), "r4")


def star(mb):                        # Rudolph collectible: a twinkly gold star
    for k in range(5):
        a = math.pi / 2 + k * 2 * math.pi / 5
        mb.bar((0, 0), (0.3 * math.cos(a), 0.3 * math.sin(a)), 0.15, 0, "f_gold")
    mb.disc(0.12, (0, -0.02, 0), "r3", seg=8, depth=0.04)


def snowflake(mb):                   # Ice Giant collectible
    for k in range(3):
        a = k * math.pi / 3
        mb.bar((-0.3 * math.cos(a), -0.3 * math.sin(a)), (0.3 * math.cos(a), 0.3 * math.sin(a)), 0.06, 0, "f_ice")
        for s in (-1, 1):
            p = (s * 0.18 * math.cos(a), s * 0.18 * math.sin(a))
            mb.bar(p, (p[0] + 0.08 * math.cos(a + 1.0) * s, p[1] + 0.08 * math.sin(a + 1.0) * s), 0.04, 0, "white")
    mb.disc(0.05, (0, -0.02, 0), "white", seg=6, depth=0.02)


def crystal(mb):                     # Yeti collectible: a blue ice crystal
    mb.bar((0, -0.32), (0, 0.32), 0.24, 0, "f_ice_d")
    mb.bar((0, -0.24), (0, 0.24), 0.12, -0.04, "f_ice")
    mb.box((0.04, 0.02, 0.14), (-0.04, -0.1, 0.06), "white")


def letter(mb):                      # Santa collectible: a letter to Santa
    mb.box((0.56, 0.06, 0.38), (0, 0, 0), "white")
    mb.bar((-0.27, 0.18), (0, 0.0), 0.04, -0.04, "f_silver_d")
    mb.bar((0, 0.0), (0.27, 0.18), 0.04, -0.04, "f_silver_d")
    mb.disc(0.07, (0, -0.06, 0.02), "f_red", seg=8, depth=0.02)


# ---------------------------------------------------------------- World 3 story props + collectibles
def mushroom(mb):                    # Gnome: his lost lucky mushroom (red with white spots)
    mb.disc(0.34, (0, 0, 0.12), "f_red", seg=14, depth=0.2, sz=0.6)
    for x, z in ((-0.16, 0.16), (0.12, 0.2), (0.0, 0.3), (0.22, 0.08)):
        mb.disc(0.05, (x, -0.11, z), "white", seg=6, depth=0.02)
    mb.box((0.18, 0.16, 0.3), (0, 0, -0.16), "f_cream")


def nametag(mb):                     # Rumpelstiltskin: a gold name badge (everybody always forgets his name)
    mb.box((0.62, 0.06, 0.34), (0, 0, 0), "f_gold")
    mb.box((0.54, 0.07, 0.26), (0, -0.01, 0), "white")
    for k in range(5):
        mb.box((0.06, 0.02, 0.1), (-0.18 + k * 0.09, -0.05, 0.02), "f_red")
    mb.box((0.62, 0.07, 0.05), (0, -0.01, 0.15), "f_red")


def hairbrush(mb):                   # Rapunzel: a golden hairbrush (her braid is SO tangled)
    mb.disc(0.2, (0, 0, 0.14), "f_gold", seg=12, depth=0.08, sz=1.3)
    mb.disc(0.15, (0, -0.05, 0.14), "f_purple", seg=10, depth=0.02, sz=1.3)
    for x in (-0.08, 0.0, 0.08):
        mb.box((0.03, 0.02, 0.2), (x, -0.07, 0.14), "white")
    mb.bar((0, -0.08), (0, -0.42), 0.1, 0, "f_gold")


def kingcrown(mb):                   # Dwarf King: his lost crown
    mb.box((0.56, 0.3, 0.22), (0, 0, -0.08), "f_gold")
    for x in (-0.22, 0.0, 0.22):
        mb.bar((x, 0.02), (x, 0.24), 0.12, 0, "f_gold")
        mb.disc(0.04, (x, -0.06, 0.26), "white", seg=6, depth=0.02)
    for x, c in ((-0.14, "f_red"), (0.0, "r5"), (0.14, "r4")):
        mb.disc(0.05, (x, -0.16, -0.08), c, seg=6, depth=0.03)


def ladybug(mb):                     # Gnome collectible
    mb.disc(0.22, (0, 0, 0), "f_red", seg=12, depth=0.14)
    mb.bar((0, -0.22), (0, 0.22), 0.03, -0.08, "f_dark")
    mb.disc(0.1, (0, 0, 0.22), "f_dark", seg=8, depth=0.08)
    for x, z in ((-0.1, 0.06), (0.1, 0.06), (-0.1, -0.1), (0.1, -0.1)):
        mb.disc(0.04, (x, -0.08, z), "f_dark", seg=6, depth=0.02)


def spool(mb):                       # Rumpelstiltskin collectible: a spool of spun-gold thread
    mb.box((0.36, 0.2, 0.06), (0, 0, 0.2), "f_brown")
    mb.box((0.36, 0.2, 0.06), (0, 0, -0.2), "f_brown")
    mb.box((0.26, 0.18, 0.34), (0, 0, 0), "f_gold")
    for z in (-0.1, 0.0, 0.1):
        mb.box((0.27, 0.19, 0.02), (0, 0, z), "r3")


def rose(mb):                        # Rapunzel collectible
    mb.disc(0.16, (0, 0, 0.14), "f_red", seg=10, depth=0.12)
    mb.disc(0.08, (0, -0.06, 0.16), "f_red_d", seg=8, depth=0.02)
    mb.bar((0, 0.0), (0.02, -0.36), 0.04, 0, "r4")
    mb.bar((0.01, -0.16), (0.14, -0.1), 0.08, 0, "r4")


def gem(mb):                         # Dwarf King collectible: a sparkly gem
    mb.disc(0.22, (0, 0, 0), "r5", seg=6, depth=0.16)
    mb.disc(0.12, (0, -0.06, 0.02), "f_ice", seg=6, depth=0.03)
    mb.box((0.05, 0.02, 0.05), (-0.08, -0.1, 0.08), "white")


def coin(mb):
    mb.disc(0.26, (0, 0, 0), "cap", seg=10, depth=0.06)
    mb.disc(0.19, (0, -0.035, 0), "acc3", seg=10, depth=0.02)
    mb.box((0.05, 0.02, 0.2), (0, -0.05, 0), "cap")
    mb.box((0.05, 0.02, 0.07), (-0.09, -0.05, 0.1), "white")


def sleep_cat(mb):                  # curled-up sleeping cat (front view)
    mb.disc(0.34, (0, 0, -0.04), "k_cat", seg=12, sz=1.0)
    mb.box((0.62, 0.2, 0.3), (0, 0, -0.18), "k_cat")
    mb.bar((0.3, -0.25), (-0.25, -0.33), 0.1, -0.12, "k_cat_light")       # tail wrapped around
    mb.box((0.3, 0.2, 0.22), (-0.2, -0.1, 0.06), "k_cat")                 # head
    for s in (-1, 1):
        mb.box((0.09, 0.1, 0.09), (-0.2 + s * 0.1, -0.1, 0.18), "k_cat", ry=45)
        mb.box((0.07, 0.02, 0.02), (-0.2 + s * 0.065, -0.21, 0.07), "black")      # closed eyes
    mb.box((0.12, 0.02, 0.06), (-0.2, -0.21, 0.0), "k_cat_light")
    mb.box((0.04, 0.02, 0.03), (-0.2, -0.22, 0.02), "k_nose")


def ground_pack(mb, with_cat=False):  # backpack standing on the ground, flap open (front view)
    mb.box((0.5, 0.25, 0.46), (0, 0, 0.23), "k_gear")
    mb.box((0.38, 0.26, 0.16), (0, -0.01, 0.14), "k_gear_shade")           # pocket
    mb.box((0.1, 0.27, 0.06), (0, -0.02, 0.2), "k_hat")                    # buckle
    mb.box((0.52, 0.12, 0.08), (0, 0.06, 0.5), "k_gear_shade")             # open flap behind
    mb.box((0.42, 0.2, 0.05), (0, -0.04, 0.47), "black")                   # opening
    if with_cat:
        y, z = -0.15, 0.6
        mb.box((0.34, 0.1, 0.24), (0, y, z), "k_cat")
        for s in (-1, 1):
            mb.box((0.1, 0.1, 0.1), (s * 0.11, y, z + 0.14), "k_cat", ry=45)
            mb.box((0.08, 0.02, 0.025), (s * 0.075, y - 0.06, z + 0.02), "black")
        mb.box((0.14, 0.02, 0.07), (0, y - 0.06, z - 0.07), "k_cat_light")
        mb.box((0.05, 0.02, 0.03), (0, y - 0.07, z - 0.045), "k_nose")
        for s in (-1, 1):
            mb.box((0.1, 0.1, 0.06), (s * 0.15, y - 0.02, 0.48), "k_cat")         # paws on the edge
    else:
        mb.box((0.2, 0.06, 0.14), (0.05, -0.1, 0.52), "acc1")              # book corner sticking out


def canopy(mb):                      # parachute dome: vertical panels, gear colour + white
    n = 9
    for i in range(n):
        x0, x1 = -1 + 2 * i / n, -1 + 2 * (i + 1) / n
        xm = (x0 + x1) / 2
        h = 0.6 * math.sqrt(max(0.0, 1 - xm * xm)) + 0.06
        role = "k_gear" if i % 2 == 0 else "white"
        mb.box((x1 - x0, 0.1, h), (xm, 0, h / 2), role)
        mb.box((x1 - x0 - 0.05, 0.11, 0.05), (xm, -0.01, 0.06), "k_gear_shade")      # scalloped rim
    mb.box((0.14, 0.12, 0.06), (0, -0.02, 0.66), "k_hat")                             # top vent
def canopy_pattern(mb, kind):
    """Parachute patterns for the shop: dots / stars / checker / rainbow."""
    n = 9
    rain = ["r1", "r2", "r3", "r4", "r5", "r6", "r5", "r4", "r3"]
    for i in range(n):
        x0, x1 = -1 + 2 * i / n, -1 + 2 * (i + 1) / n
        xm = (x0 + x1) / 2
        h = 0.6 * math.sqrt(max(0.0, 1 - xm * xm)) + 0.06
        if kind == "checker":
            for k in range(4):
                z0 = h * k / 4
                mb.box((x1 - x0, 0.1, h / 4), (xm, 0, z0 + h / 8), "k_gear" if (i + k) % 2 == 0 else "white")
        else:
            role = rain[i] if kind == "rainbow" else "k_gear"
            mb.box((x1 - x0, 0.1, h), (xm, 0, h / 2), role)
        mb.box((x1 - x0 - 0.05, 0.11, 0.05), (xm, -0.01, 0.06), "k_gear_shade" if kind != "rainbow" else "white")
    if kind == "dots":
        for x, z in ((-0.62, 0.3), (-0.3, 0.48), (0.05, 0.35), (0.38, 0.5), (0.66, 0.28), (-0.15, 0.18), (0.25, 0.18)):
            mb.disc(0.075, (x, -0.08, z), "white", seg=8, depth=0.02)
    if kind == "stars":
        for x, z in ((-0.6, 0.28), (-0.22, 0.47), (0.2, 0.42), (0.6, 0.3), (0.0, 0.2)):
            mb.box((0.14, 0.02, 0.04), (x, -0.08, z), "f_gold")
            mb.box((0.04, 0.02, 0.14), (x, -0.08, z), "f_gold")
            mb.box((0.08, 0.02, 0.08), (x, -0.085, z), "f_gold", ry=45)
    mb.box((0.14, 0.12, 0.06), (0, -0.02, 0.66), "k_hat")


def bird(mb, frame=0):               # friendly big bird, side view facing left, wings up/mid/down
    mb.sphere(0.32, (0, 0, 0), "acc2", seg=10, rings=6)                    # body
    mb.box((0.36, 0.1, 0.22), (-0.02, -0.25, -0.08), "white")              # belly
    mb.sphere(0.2, (-0.33, 0, 0.2), "acc2", seg=8, rings=6)                # head
    mb.box((0.06, 0.04, 0.06), (-0.4, -0.2, 0.25), "white")                # eye
    mb.box((0.03, 0.04, 0.03), (-0.41, -0.22, 0.25), "black")
    mb.box((0.18, 0.08, 0.08), (-0.58, 0, 0.16), "cap", ry=10)             # beak
    mb.box((0.1, 0.08, 0.05), (-0.55, -0.01, 0.11), "cap_dark" if False else "cap")
    mb.box((0.1, 0.08, 0.06), (-0.38, -0.21, 0.12), "skin_shade")          # rosy cheek
    mb.bar((0.25, 0.05), (0.55, 0.2), 0.14, 0, "acc2")                      # tail
    mb.bar((0.3, 0.0), (0.58, 0.05), 0.08, -0.02, "hair3")
    for s in (-0.05, 0.08):                                                 # legs + feet (Pip holds these)
        mb.bar((s, -0.25), (s - 0.02, -0.5), 0.05, 0, "cap")
        mb.box((0.12, 0.05, 0.04), (s - 0.05, 0, -0.52), "cap")
    ang = (55, 5, -45)[frame]
    L = 0.62
    tip = (0.05 + L * 0.35, 0.1 + L * math.sin(math.radians(ang)))
    mb.bar((0.02, 0.1), tip, 0.2, -0.3, "acc2")
    mb.bar((0.02, 0.06), (tip[0] - 0.05, tip[1] - 0.08 * (1 if ang > 0 else -1)), 0.1, -0.33, "white")
    mb.bar(tip, (tip[0] + 0.25, tip[1] + 0.05), 0.12, -0.32, "acc2")


def build_prop(fn, name, coll, loc, **kw):
    mb = MeshBuilder()
    fn(mb, **kw)
    return mb.to_object(name, coll, loc)


def render_props(raw, ppu=32):
    """Story props. Returns {name: keyed?}. Keyed ones use k_* roles (recoloured in JS)."""
    sc = bpy.context.scene
    coll = new_collection("Props")
    items = [("book", book, {}, 0.95, False), ("page", page, {}, 0.6, False), ("sleepcat", sleep_cat, {}, 0.95, True),
             ("gpack", ground_pack, {}, 0.8, True), ("gpack_cat", ground_pack, {"with_cat": True}, 0.95, True),
             ("canopy", canopy, {}, 2.1, True), ("phone", toy_phone, {}, 0.95, False), ("photo", photo, {}, 0.6, False),
             ("turnip", turnip, {}, 0.95, False), ("stack", pancake_stack, {}, 0.95, False), ("compass", compass, {}, 0.8, False),
             ("selfie", selfie_cam, {}, 0.85, False), ("clover", clover, {}, 0.6, False), ("leaf", maple_leaf, {}, 0.6, False),
             ("feather", feather, {}, 0.6, False), ("berries", berries, {}, 0.6, False),
             ("hammer", hammer, {}, 0.95, False), ("lantern", lantern, {}, 0.85, False), ("mitten", mitten, {}, 0.85, False),
             ("cocoa", cocoa, {}, 0.95, False), ("cookie", bigcookie, {}, 0.85, False), ("gingerbread", gingerbread, {}, 0.6, False),
             ("star", star, {}, 0.6, False), ("snowflake", snowflake, {}, 0.6, False), ("crystal", crystal, {}, 0.6, False),
             ("letter", letter, {}, 0.6, False),
             ("mushroom", mushroom, {}, 0.85, False), ("nametag", nametag, {}, 0.8, False), ("hairbrush", hairbrush, {}, 0.85, False),
             ("kingcrown", kingcrown, {}, 0.85, False), ("ladybug", ladybug, {}, 0.6, False), ("spool", spool, {}, 0.6, False),
             ("rose", rose, {}, 0.6, False), ("gem", gem, {}, 0.6, False)]
    items += [(f"canopy_{k}", canopy_pattern, {"kind": k}, 2.1, True) for k in CHUTES]
    items += [(f"bird_{f}", bird, {"frame": f}, 1.6, False) for f in range(3)]
    keyed = {}
    for i, (name, fn, kw, ext, k) in enumerate(items):
        ob = build_prop(fn, "prop_" + name, coll, (4000 + 4 * i, 0, 0), **kw)
        px = round(ext * ppu)
        setup_workbench(sc, px, px, transparent=True)
        cz = 0.45 if name.startswith("gpack") else 0.3 if name.startswith("canopy") else -0.05 if name.startswith("bird") else 0
        ortho_camera(sc, (ob.location.x, cz), ext, "HORIZONTAL")
        render(os.path.join(raw, f"s_{name}.png"))
        keyed[name] = k
        ob.hide_render = True
    ob = build_prop(coin, "prop_coin", coll, (4100, 0, 0))
    setup_workbench(sc, 18, 18, transparent=True)
    ortho_camera(sc, (4100, 0), 18 / ppu, "HORIZONTAL")
    for f in range(4):
        ob.rotation_euler.z = math.radians(f * 40)          # spin about the vertical axis
        render(os.path.join(raw, f"s_coin_{f}.png"))
        keyed[f"coin_{f}"] = False
    ob.hide_render = True
    return keyed
