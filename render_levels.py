"""render_levels.py - build + render every Beard Climber level, then post-process.

Run:  blender -b --python render_levels.py -- [--levels wizard,viking] [--cols 6] [--no-post]

Blender only renders *layers*; postprocess.py composes all frames / strips / GIFs
from them (pixel-exact, because everything shares one orthographic pixel grid).
Per level (out/<level>/raw/):
  level_closed.png / level_open.png   the WHOLE tall level (beard tip -> face),
                                      224 px wide, mouth closed / open
  climb_XX.png, fall.png              climber sprites in this level's palette
  haz_<i>_<f>.png, enemy_<f>.png      hazard sprites (4 spin frames) / enemy frames
  tile_*.png                          beard tile variants
  manifest.json                       pixel geometry for the compositor
and out/<level>/<level>.blend (whole level; mouth_open object hidden for render).
"""
import argparse, json, math, os, shutil, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from common import (MeshBuilder, clear_scene, new_collection, set_palette, setup_workbench,
                    ortho_camera, CLIMBER_PALETTE, with_roles)
import beard, climber, levels

BOTTOM_MARGIN = 0.9      # open background below the beard tip (units)
CLIMBER_CENTER = 1.02    # climber sprite cell centre, units above the rig root


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default=",".join(levels.ORDER))
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=None, help="override every level's beard length")
    ap.add_argument("--seed", type=int, default=None, help="override every level's seed")
    ap.add_argument("--width", type=int, default=224)
    ap.add_argument("--height", type=int, default=256)
    ap.add_argument("--ppu", type=int, default=32, help="pixels per tile")
    ap.add_argument("--sprite", type=int, default=48, help="hazard sprite cell (px)")
    ap.add_argument("--climber-sprite", type=int, default=72, help="climber sprite cell (px)")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--no-post", action="store_true")
    ap.add_argument("--post-args", default="")
    return ap.parse_args(argv)


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def build_prop(fn, name, coll, loc=(0, 0, 0), **kw):
    mb = MeshBuilder()
    fn(mb, **kw)
    return mb.to_object(name, coll, loc)


def render_climber_sprites(a, raw, coll_name="Climber"):
    """Climber sprites into raw/ (active palette):
      climb_XX        climb cycle with beanie        fall      fall pose
      climbhat{c}_XX  climb cycle wearing the hard hat with c cracks (c = 0, 1, 2)
      hatmask_XX      hard hat only (alpha = where to flash the hat on a hit)
    """
    sc = bpy.context.scene
    coll = new_collection(coll_name)
    root, j = climber.build_climber(coll)
    climber.animate(root, j)
    root.location = (1000, -0.6, 0)
    setup_workbench(sc, a.climber_sprite, a.climber_sprite, transparent=True)
    cell = a.climber_sprite / a.ppu
    for state, prefix in ((None, "climb_"), (0, "climbhat0_"), (1, "climbhat1_"), (2, "climbhat2_")):
        climber.set_headgear(j, state)
        ortho_camera(sc, (1000, CLIMBER_CENTER), cell, "HORIZONTAL")
        for i in range(climber.CYCLE):
            sc.frame_set(i + 1)
            render(os.path.join(raw, f"{prefix}{i:02d}.png"))
        if state is None:
            sc.frame_set(climber.FALL_FRAME)
            ortho_camera(sc, (1000 - 0.25, CLIMBER_CENTER - 0.17), cell, "HORIZONTAL")
            render(os.path.join(raw, "fall.png"))
    # hat-only mask for the hit flash
    climber.set_headgear(j, 0)
    hidden = [ob for ob in coll.objects if ob.type == "MESH" and ob.name != "hardhat_0" and not ob.hide_render]
    for ob in hidden:
        ob.hide_render = True
    ortho_camera(sc, (1000, CLIMBER_CENTER), cell, "HORIZONTAL")
    for i in range(climber.CYCLE):
        sc.frame_set(i + 1)
        render(os.path.join(raw, f"hatmask_{i:02d}.png"))
    for ob in hidden:
        ob.hide_render = False
    climber.set_headgear(j, None)
    sc.frame_set(1)
    return coll


def render_hat_items(a, raw):
    """Hard-hat pick-up sprites: 4 spin frames (thrown / popping off) + 'tangled in a knot'."""
    sc = bpy.context.scene
    coll = new_collection("HatItems")
    S = 2.6                                            # item is drawn larger than on the head
    mb = MeshBuilder(); climber.build_hardhat(mb, 0, z=-0.085 * S, s=S)
    item = mb.to_object("hardhat_item", coll, (500, 0, 0))
    setup_workbench(sc, 32, 32, transparent=True)
    ortho_camera(sc, (500, 0), 1.0, "HORIZONTAL")
    for f in range(4):
        item.rotation_euler.y = math.radians(-90 * f)
        render(os.path.join(raw, f"hatitem_{f}.png"))
    mb = MeshBuilder(); climber.build_hardhat(mb, 0, z=-0.085 * S, s=S)
    mb.disc(0.42, (0, 0.3, 0.0), "hair1", depth=0.04, seg=10)          # knot behind the hat
    for p0, p1, r in (((-0.55, -0.4), (0.5, 0.4), "hair3"), ((-0.5, 0.42), (0.55, -0.38), "hair4")):
        mb.bar(p0, p1, 0.16, 0.22, "black", depth=0.04)                 # strands behind
        mb.bar(p0, p1, 0.1, 0.18, r, depth=0.04)
    mb.bar((-0.5, -0.14), (0.52, -0.08), 0.11, -0.4, "black", depth=0.04)  # one strand looped over the brim
    mb.bar((-0.5, -0.14), (0.52, -0.08), 0.06, -0.45, "hair4", depth=0.04)
    mb.to_object("hardhat_tangled", coll, (520, 0, 0))
    setup_workbench(sc, 40, 40, transparent=True)
    ortho_camera(sc, (520, 0), 1.25, "HORIZONTAL")
    render(os.path.join(raw, "hattangled.png"))
    coll.hide_render = True


def render_level(L, a):
    t0 = time.time()
    lid = L["id"]
    raw = os.path.join(a.out, lid, "raw")
    os.makedirs(raw, exist_ok=True)
    clear_scene()
    set_palette(with_roles(L["palette"], L.get("climber_roles")))
    sc = bpy.context.scene
    seed = a.seed if a.seed is not None else L["seed"]
    rows = a.rows or L["rows"]

    # --- whole level: beard tip -> face, two mouth states
    coll = new_collection("Level")
    bmb = beard.build_beard(L, a.cols, rows, seed)
    tilemap, col_min_z = bmb.tilemap, bmb.col_min_z
    bmb.to_object("beard", coll)
    mouths = {}
    for flag in (False, True):
        mb = MeshBuilder()
        beard.mouth(mb, L, a.cols, rows, flag)
        mouths[flag] = mb.to_object("mouth_open" if flag else "mouth_closed", coll)
    top = rows + beard.FACE_H
    h_px = math.ceil((top + BOTTOM_MARGIN) * a.ppu)
    setup_workbench(sc, a.width, h_px)
    ortho_camera(sc, (a.cols / 2, top - h_px / a.ppu / 2), h_px / a.ppu, "VERTICAL")
    for flag, name in ((False, "level_closed"), (True, "level_open")):
        mouths[True].hide_render, mouths[False].hide_render = not flag, flag
        render(os.path.join(raw, name + ".png"))
    mouths[True].hide_render, mouths[False].hide_render = True, False
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out, lid, f"{lid}.blend"))
    coll.hide_render = True

    # --- climber sprites in this level's palette
    render_climber_sprites(a, raw).hide_render = True
    render_hat_items(a, raw)

    # --- tile variants
    tcoll = new_collection("Tiles")
    variants = [("normal", "normal", None, 0), ("normal2", "normal2", None, 2), ("knot", "knot", None, 0)]
    variants += [(f"hold_{h}", "hold", h, 0) for h in dict.fromkeys(L["holds"])]
    if L.get("braid_cols"):
        variants.append(("braid", "normal", None, L["braid_cols"][0]))
    variants += [("sparse", "sparse", None, 0), ("decor", "decor", None, 0)]
    setup_workbench(sc, a.ppu, a.ppu)
    import random
    tiles = []
    for k, (label, kind, hold, gcol) in enumerate(variants):
        mb = MeshBuilder()
        x0 = 100 + 3 * k
        beard.build_tile(mb, L, kind, x0, 10, random.Random(k), gcol, 10, hold)
        mb.to_object(f"tile_{label}", tcoll)
        ortho_camera(sc, (x0 + 0.5, 10.5), 1.0, "HORIZONTAL")
        render(os.path.join(raw, f"tile_{k:02d}_{label}.png"))
        tiles.append(f"tile_{k:02d}_{label}")
    tcoll.hide_render = True

    # --- hazard sprites (4 spin frames) + enemy frames
    hcoll = new_collection("HazardSheet")
    setup_workbench(sc, a.sprite, a.sprite, transparent=True)
    cell = a.sprite / a.ppu
    haz = []
    for i, (name, fn) in enumerate(L["hazards"]):
        ob = build_prop(fn, f"sheet_{name}", hcoll, (200 + 3 * i, 0, 0))
        ortho_camera(sc, (ob.location.x, 0), cell, "HORIZONTAL")
        row = []
        for f in range(4):
            ob.rotation_euler.y = math.radians(-90 * f)
            render(os.path.join(raw, f"haz_{i}_{f}.png"))
            row.append(f"haz_{i}_{f}")
        haz.append(row)
    enemy = []
    if L.get("enemy"):
        for f in range(2):
            ob = build_prop(L["enemy"][1], f"enemy_{f}", hcoll, (300 + 3 * f, 0, 0), frame=f)
            ortho_camera(sc, (ob.location.x, 0.05), cell, "HORIZONTAL")
            render(os.path.join(raw, f"enemy_{f}.png"))
            enemy.append(f"enemy_{f}")
    json.dump({"title": L["title"], "tiles": tiles, "hazards": haz, "enemy": enemy,
               "ppu": a.ppu, "width": a.width, "height": a.height, "level_h": h_px,
               "cols": a.cols, "rows": rows, "top": top, "x_left": a.cols / 2 - a.width / a.ppu / 2,
               "bottom_margin": BOTTOM_MARGIN, "climber_cell": a.climber_sprite,
               "climber_center": CLIMBER_CENTER, "sprite_cell": a.sprite, "cycle": climber.CYCLE,
               "tilemap": tilemap, "col_min_z": col_min_z},
              open(os.path.join(raw, "manifest.json"), "w"), indent=1)
    print(f"[{lid}] rendered in {time.time() - t0:.1f}s")


def render_shared_climber(a):
    raw = os.path.join(a.out, "climber", "raw")
    os.makedirs(raw, exist_ok=True)
    clear_scene()
    set_palette(CLIMBER_PALETTE)
    render_climber_sprites(a, raw).hide_render = True
    render_hat_items(a, raw)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a.out, "climber", "climber.blend"))
    json.dump({"cycle": climber.CYCLE}, open(os.path.join(raw, "manifest.json"), "w"))


def main():
    a = args()
    bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups
    t0 = time.time()
    render_shared_climber(a)
    for lid in a.levels.split(","):
        render_level(levels.load(lid), a)
    print(f"Blender stage: {time.time() - t0:.1f}s")
    if not a.no_post:
        py = shutil.which("python3") or shutil.which("python")
        subprocess.run([py, os.path.join(HERE, "postprocess.py"), "--out", a.out,
                        "--levels", a.levels] + a.post_args.split(), check=True)


if __name__ == "__main__":
    main()
