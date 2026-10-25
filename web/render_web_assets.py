"""web/render_web_assets.py - Blender: render everything the web game needs.

Run:  blender -b --python web/render_web_assets.py -- [--level wizard] [--skip-level]
      blender -b --python web/render_web_assets.py -- --level grandpa     (level, faces, waving hand)

1. render_levels.render_level(): the whole Wizard level image (mouth closed / open), tile map,
   hazards, hard-hat items, manifest.
2. Wizard face variants for the ending: level_smile.png (smiling) and level_sleep.png (eyes
   closed + smile), re-rendered from the saved wizard.blend with extra eyelid / smile objects.
3. Pip (web/pip.py): layered, key-coloured sprites for the character creator
   (2 bodies x 4 hair styles x 3 hats + backpack + cat, 16 back-view poses + 3 front-view poses,
   hard hat states for the 12 gameplay poses), the townsfolk (3 front-view poses),
   and story props (spell book, page, sleeping cat, backpack, parachute, bird, coin).
4. The other four giants for the opening cinematic: a face portrait (mouth closed / open),
   one or two kid-friendly things they toss, and their lost treasure, each in its own palette.
Output: web/build/<level>/raw/ (processed by web/build_web.py).
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import bpy
import beard, climber, levels, render_levels as RL
import pip
from common import MeshBuilder, new_collection, set_palette, setup_workbench, ortho_camera, with_roles, clear_scene

GIANTS = {   # cinematic: level -> (things tossed (hazard indices, kid-friendly ones only), treasure builder name)
    "grandpa": ([0, 2], "phone"), "goat": ([1, 3], "turnip"), "lumberjack": ([2, 0], "pancakes"),
    "mountain": ([1, 3], "compass"), "bigfoot": ([0, 1], "selfie"),
    "elf": ([0, 2], "hammer"), "rudolph": ([1, 2], "lantern"), "ice": ([1, 2], "mitten"),
    "yeti": ([0, 2], "cocoa"), "santa": ([0, 1], "plate"),
    "gnome": ([1, 2], "mushroom"), "rumpel": ([0, 1], "nametag"), "rapunzel": ([0, 3], "hairbrush"), "dwarf": ([2, 3], "kingcrown"),
}
# (viking / pirate portraits come back with their worlds; their level files are still in levels/)
PORTRAIT_H = 208        # px: hat brim + face + ~2.5 rows of beard


# ---------------------------------------------------------------- wizard face variants
def eyelids(mb, cols, rows):
    """Closed, happy eyes drawn in front of the open ones."""
    cx, ez = cols / 2, rows + 2.55
    for s in (-1, 1):
        ex = cx + s * 1.2
        mb.box((0.78, 0.05, 0.46), (ex, -0.16, ez), "skin")
        mb.bar((ex - 0.34, ez + 0.06), (ex - 0.14, ez - 0.07), 0.09, -0.19, "black", depth=0.03)
        mb.bar((ex - 0.14, ez - 0.07), (ex + 0.14, ez - 0.07), 0.09, -0.19, "black", depth=0.03)
        mb.bar((ex + 0.14, ez - 0.07), (ex + 0.34, ez + 0.06), 0.09, -0.19, "black", depth=0.03)


def smile(mb, cols, rows):
    cx, z = cols / 2, rows
    mb.box((1.7, 0.05, 0.75), (cx, -0.28, z + 0.32), "skin")             # cover the closed mouth
    pts = [(-0.72, 0.6), (-0.42, 0.36), (0.42, 0.36), (0.72, 0.6)]
    for p0, p1 in zip(pts, pts[1:]):
        mb.bar((cx + p0[0], z + p0[1]), (cx + p1[0], z + p1[1]), 0.12, -0.305, "black", depth=0.03)
    mb.box((0.7, 0.05, 0.14), (cx, -0.3, z + 0.24), "lips")


def wizard_faces(L, a):
    path = os.path.join(a.out, L["id"], f"{L['id']}.blend")
    bpy.ops.wm.open_mainfile(filepath=path)
    set_palette(with_roles(L["palette"], L.get("climber_roles")))
    sc = bpy.context.scene
    coll = new_collection("FaceVariants")
    rows = L["rows"]
    mb = MeshBuilder(); eyelids(mb, a.cols, rows); lids = mb.to_object("eyelids", coll)
    mb = MeshBuilder(); smile(mb, a.cols, rows); sm = mb.to_object("smile", coll)
    raw = os.path.join(a.out, L["id"], "raw")
    lids.hide_render = True
    RL.render(os.path.join(raw, "level_smile.png"))
    lids.hide_render = False
    RL.render(os.path.join(raw, "level_sleep.png"))


# ---------------------------------------------------------------- other giants (cinematic)
def plate(mb):
    mb.disc(0.42, (0, 0, 0), "white", seg=12, sz=1.0)
    mb.box((0.86, 0.1, 0.22), (0, 0.02, -0.02), "hair2")
    mb.box((0.78, 0.1, 0.16), (0, -0.04, 0.02), "white")
    for x, z in ((-0.15, 0.05), (0.1, 0.0), (0.22, 0.06), (-0.02, 0.08)):
        mb.box((0.05, 0.02, 0.04), (x, -0.1, z), "acc3")                  # crumbs


def pancakes(mb):
    mb.box((0.9, 0.1, 0.1), (0, 0, -0.3), "white")                         # plate
    for i in range(4):
        z = -0.2 + i * 0.12
        mb.box((0.7 - 0.04 * (i % 2), 0.2, 0.11), (0.02 * (i % 2), 0, z), "hair1")
        mb.box((0.5, 0.02, 0.03), (0, -0.11, z + 0.03), "black")          # burnt
    for x in (-0.15, 0.12):
        mb.box((0.08, 0.03, 0.05), (x, -0.12, 0.2), "black")


def horn(mb):
    pts = [(-0.4, -0.25), (-0.2, -0.05), (0.05, 0.08), (0.3, 0.12), (0.45, 0.28)]
    th = [0.1, 0.14, 0.18, 0.22]
    for (p0, p1), t in zip(zip(pts, pts[1:]), th):
        mb.bar(p0, p1, t, 0, "hair4")
    for p, t in ((pts[1], 0.17), (pts[3], 0.27)):
        mb.box((0.06, 0.06, t), (p[0], -0.06, p[1]), "acc1", ry=-35)
    mb.disc(0.13, (0.47, -0.02, 0.3), "acc2", seg=8, depth=0.05)
    mb.box((0.08, 0.06, 0.08), (-0.42, -0.04, -0.27), "acc3")


def treasure_map(mb):
    mb.box((0.8, 0.04, 0.56), (0, 0, 0), "pants")
    mb.box((0.06, 0.06, 0.6), (-0.42, 0, 0), "hair4")                       # rolled ends
    mb.box((0.06, 0.06, 0.6), (0.42, 0, 0), "hair4")
    for x, z in ((-0.25, -0.15), (-0.12, -0.05), (0.0, 0.0), (0.1, 0.08)):
        mb.box((0.06, 0.02, 0.03), (x, -0.03, z), "lips")                   # dotted path
    mb.box((0.14, 0.02, 0.04), (0.22, -0.035, 0.14), "acc1", ry=45)          # X marks the spot
    mb.box((0.14, 0.02, 0.04), (0.22, -0.035, 0.14), "acc1", ry=-45)
    mb.box((0.14, 0.02, 0.1), (-0.2, -0.03, 0.15), "acc2")                  # island


def giant_hand(mb):
    """Grandpa's big friendly hand (waving), cardigan cuff at the bottom."""
    mb.disc(0.42, (0, 0, 0), "skin", seg=12, depth=0.2)
    for k, (x, ln) in enumerate(((-0.27, 0.42), (-0.09, 0.52), (0.09, 0.5), (0.26, 0.4))):
        mb.bar((x, 0.25), (x * 1.15, 0.25 + ln), 0.17, -0.02, "skin")
        mb.bar((x * 1.15 - 0.03, 0.25 + ln - 0.04), (x * 1.15 - 0.03, 0.25 + ln - 0.12), 0.05, -0.12, "skin_shade", depth=0.02)
    mb.bar((0.35, -0.05), (0.62, 0.22), 0.18, -0.02, "skin")             # thumb
    mb.box((0.5, 0.04, 0.05), (-0.02, -0.12, -0.08), "skin_shade")
    mb.box((0.9, 0.26, 0.36), (0, 0, -0.55), "acc1")                     # cardigan cuff
    for x in (-0.3, -0.1, 0.1, 0.3):
        mb.box((0.05, 0.28, 0.32), (x, -0.01, -0.55), "hair1")


def toy_phone_t(mb):
    pip.toy_phone(mb)


def turnip_t(mb):                     # the Goat's (last) turnip - level roles only
    mb.disc(0.3, (0, 0, -0.06), "white", seg=12, depth=0.3)
    mb.disc(0.27, (0, -0.02, 0.06), "lips", seg=12, depth=0.28, sz=0.6)
    mb.bar((0, -0.34), (0.02, -0.48), 0.05, 0, "skin_shade")
    for x, a_ in ((-0.12, -0.18), (0.0, 0.0), (0.12, 0.18)):
        mb.bar((x * 0.5, 0.2), (x + a_, 0.62), 0.12, 0, "acc2")


def compass_t(mb):                    # Mountain Man's lost compass
    mb.disc(0.3, (0, 0, 0), "cap", seg=14, depth=0.1)
    mb.disc(0.23, (0, -0.06, 0), "white", seg=14, depth=0.02)
    mb.bar((0, -0.18), (0, 0.18), 0.07, -0.08, "black")
    mb.bar((0, 0.02), (0, 0.18), 0.07, -0.09, "lips")
    mb.box((0.12, 0.08, 0.1), (0, 0, 0.33), "cap")


def selfie_t(mb):                     # Bigfoot's camera (nobody to take a picture with)
    mb.box((0.66, 0.3, 0.46), (0, 0, 0), "acc1")
    mb.box((0.66, 0.31, 0.12), (0, 0, -0.18), "white")
    mb.disc(0.16, (0, -0.16, 0.03), "black", seg=12, depth=0.05)
    mb.disc(0.09, (0, -0.2, 0.03), "acc2", seg=10, depth=0.03)
    mb.box((0.14, 0.02, 0.09), (0.21, -0.16, 0.15), "acc3")


def hammer_t(mb):                     # the Elf's lost hammer (the workshop stands still)
    mb.bar((-0.05, -0.42), (0.03, 0.18), 0.09, 0, "acc3")
    mb.box((0.42, 0.18, 0.18), (0.03, 0, 0.24), "hair2")
    mb.box((0.1, 0.02, 0.05), (-0.06, -0.1, 0.28), "white")


def lantern_t(mb):                    # Rudolph: a lantern gone dark
    mb.box((0.36, 0.3, 0.44), (0, 0, -0.04), "black")
    mb.box((0.28, 0.31, 0.34), (0, 0, -0.04), "hair1")
    mb.box((0.42, 0.32, 0.06), (0, 0, 0.2), "acc1")
    mb.box((0.42, 0.32, 0.06), (0, 0, -0.28), "acc1")


def mitten_t(mb):                     # the Ice Giant: a single lonely mitten
    mb.disc(0.24, (0, 0, 0.04), "shirt", seg=12, depth=0.22, sz=1.25)
    mb.disc(0.1, (-0.24, 0, 0.0), "shirt", seg=8, depth=0.2, sz=1.4)
    mb.box((0.5, 0.24, 0.14), (0, 0, -0.3), "white")


def cocoa_t(mb):                      # the Yeti: an empty cocoa mug
    mb.box((0.4, 0.32, 0.44), (-0.04, 0, -0.04), "acc1")
    mb.box((0.34, 0.3, 0.06), (-0.04, 0, 0.2), "black")
    for z in (-0.14, 0.08):
        mb.bar((0.16, z), (0.28, z), 0.07, 0, "acc1")
    mb.bar((0.28, -0.14), (0.28, 0.08), 0.07, 0, "acc1")


def mushroom_t(mb):                   # the Gnome's lucky mushroom
    mb.disc(0.34, (0, 0, 0.12), "acc1", seg=14, depth=0.2, sz=0.6)
    for x, z in ((-0.16, 0.16), (0.12, 0.2), (0.22, 0.08)):
        mb.disc(0.05, (x, -0.11, z), "white", seg=6, depth=0.02)
    mb.box((0.18, 0.16, 0.3), (0, 0, -0.16), "skin")


def nametag_t(mb):                    # Rumpelstiltskin: a blank name badge
    mb.box((0.62, 0.06, 0.34), (0, 0, 0), "cap")
    mb.box((0.54, 0.07, 0.26), (0, -0.01, 0), "white")


def hairbrush_t(mb):                  # Rapunzel's hairbrush
    mb.disc(0.2, (0, 0, 0.14), "cap", seg=12, depth=0.08, sz=1.3)
    mb.disc(0.15, (0, -0.05, 0.14), "acc2", seg=10, depth=0.02, sz=1.3)
    mb.bar((0, -0.08), (0, -0.42), 0.1, 0, "cap")


def kingcrown_t(mb):                  # the Dwarf King's crown
    mb.box((0.56, 0.3, 0.22), (0, 0, -0.08), "cap")
    for x in (-0.22, 0.0, 0.22):
        mb.bar((x, 0.02), (x, 0.24), 0.12, 0, "cap")
    mb.disc(0.05, (0, -0.16, -0.08), "acc2", seg=6, depth=0.03)


TREASURES = {"phone": toy_phone_t, "plate": plate, "pancakes": pancakes, "horn": horn, "map": treasure_map,
             "turnip": turnip_t, "compass": compass_t, "selfie": selfie_t,
             "hammer": hammer_t, "lantern": lantern_t, "mitten": mitten_t, "cocoa": cocoa_t,
             "mushroom": mushroom_t, "nametag": nametag_t, "hairbrush": hairbrush_t, "kingcrown": kingcrown_t}


def giant_pass(lid, a, raw):
    L = levels.load(lid)
    clear_scene()
    set_palette(with_roles(L["palette"], L.get("climber_roles")))
    sc = bpy.context.scene
    coll = new_collection("Giant")
    rows = 10
    beard.build_beard(L, a.cols, rows, L["seed"]).to_object("beard", coll)
    mouths = {}
    for flag in (False, True):
        mb = MeshBuilder(); beard.mouth(mb, L, a.cols, rows, flag)
        mouths[flag] = mb.to_object(f"mouth_{flag}", coll)
    top = rows + beard.FACE_H
    setup_workbench(sc, a.width, PORTRAIT_H)
    h = PORTRAIT_H / a.ppu
    ortho_camera(sc, (a.cols / 2, top - h / 2), h, "VERTICAL")
    for flag in (False, True):
        mouths[True].hide_render, mouths[False].hide_render = not flag, flag
        RL.render(os.path.join(raw, f"giant_{lid}_{'open' if flag else 'closed'}.png"))
    coll.hide_render = True
    hc = new_collection("Toss")
    setup_workbench(sc, a.sprite, a.sprite, transparent=True)
    toss, treasure = GIANTS[lid]
    for k, hi in enumerate(toss):
        ob = RL.build_prop(L["hazards"][hi][1], f"toss_{k}", hc, (200 + 3 * k, 0, 0))
        ortho_camera(sc, (ob.location.x, 0), a.sprite / a.ppu, "HORIZONTAL")
        RL.render(os.path.join(raw, f"toss_{lid}_{k}.png"))
        ob.hide_render = True
    ob = RL.build_prop(TREASURES[treasure], "treasure", hc, (300, 0, 0))
    ortho_camera(sc, (300, 0), a.sprite / a.ppu, "HORIZONTAL")
    RL.render(os.path.join(raw, f"treasure_{lid}.png"))
    return {"toss": len(toss), "treasure": treasure, "rows_top": top}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="wizard")
    ap.add_argument("--skip-level", action="store_true", help="reuse the existing level render")
    ap.add_argument("--only", default="", help="comma list of passes: level,faces,pip,giants")
    o = ap.parse_args(argv)
    lv = o.level
    only = set(o.only.split(",")) if o.only else ({"level", "faces", "pip", "giants"} if lv == "wizard" else {"level", "faces", "extras"})
    if o.skip_level:
        only.discard("level")
    sys.argv = [sys.argv[0], "--", "--out", os.path.join(HERE, "build"), "--no-post"]
    a = RL.args()
    bpy.context.preferences.filepaths.save_version = 0
    L = levels.load(lv)
    raw = os.path.join(a.out, lv, "raw")
    os.makedirs(raw, exist_ok=True)
    if "level" in only:
        RL.render_level(L, a)                     # level images, tiles, hazards, hat items, manifest (+tilemap)
    if "faces" in only:
        wizard_faces(L, a)
    if "pip" in only:
        clear_scene()
        pal = with_roles(L["palette"], L.get("climber_roles"))
        pal.update(pip.KEYS); pal.update(pip.EXTRA)
        set_palette(pal)
        RL.render_hat_items(a, raw)               # hard-hat item spins + tangled
        info = {"pip": pip.render_pip(raw), "town": pip.render_town(raw), "props": pip.render_props(raw),
                "keys": pip.KEYS, "fixed": pip.FIXED, "hairs": pip.HAIRS, "hats": pip.HATS + pip.SHOP_HATS, "bodies": pip.BODIES,
                "patterns": pip.PATTERNS, "packs": pip.PACK_STYLES, "chutes": pip.CHUTES,
                "game_poses": pip.GAME_POSES}
        json.dump(info, open(os.path.join(raw, "pip_manifest.json"), "w"), indent=1)
    if "extras" in only and lv == "grandpa":      # Grandpa's waving hand (ending), 2 frames
        clear_scene(); set_palette(with_roles(L["palette"], L.get("climber_roles")))
        hc = new_collection("Extras"); sc = bpy.context.scene
        ob = RL.build_prop(giant_hand, "hand", hc, (500, 0, 0))
        setup_workbench(sc, 72, 72, transparent=True)
        ortho_camera(sc, (500, 0.1), 72 / a.ppu, "HORIZONTAL")
        for f, ang in enumerate((-12, 14)):
            ob.rotation_euler.y = math.radians(ang)
            RL.render(os.path.join(raw, f"hand_{f}.png"))
    if "giants" in only:
        g = {lid: giant_pass(lid, a, raw) for lid in GIANTS}
        json.dump(g, open(os.path.join(raw, "giants_manifest.json"), "w"), indent=1)
    print("web assets ->", raw)


main()
