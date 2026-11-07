"""climber.py - the shared Beard Climber hero: blocky low-poly figure seen from
BEHIND (beanie + pompom, ears and neck only - no face), on a simple object rig.

Run stand-alone:  blender -b --python climber.py -- [--out out/climber/climber.blend]

Rig: Empties ("pivots") in a hierarchy; every joint rotates about world Y
(in the picture plane), so a pose is just {joint: degrees}. Easy to script or
let an AI author poses.  Frames 1-8 = looping climb cycle, frame 10 = fall pose.
Keys are CONSTANT so every frame is a crisp sprite pose.
Model height ~1.25 units before SCALE; SCALE=1.5 -> ~1.85 units = ~59 px at 32 px/tile.
"""
import argparse, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from common import MeshBuilder, clear_scene, new_collection, set_palette, CLIMBER_PALETTE

CYCLE = 8
FALL_FRAME = 10
BRACE_FRAME, HOLD_FRAME, DYNO_FRAME = 11, 12, 13   # extra poses used by the web game
SCALE = 1.5


def _pivot(name, loc, parent, coll):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.05
    e.location, e.parent = loc, parent
    coll.objects.link(e)
    return e


def _part(name, parent, coll, build):
    """Make a mesh part from a MeshBuilder callback, parented to a pivot."""
    mb = MeshBuilder()
    build(mb)
    ob = mb.to_object(name, coll)
    ob.parent = parent
    return ob


def build_climber(coll=None):
    """Build the character. Returns (root, joints)."""
    coll = coll or new_collection("Climber")
    root = _pivot("climber_root", (0, 0, 0), None, coll)
    root.scale = (SCALE,) * 3
    hips = _pivot("hips", (0, 0, 0.5), root, coll)
    neck = _pivot("neck", (0, 0, 0.36), hips, coll)

    def torso(mb):
        mb.box((0.26, 0.16, 0.12), (0, 0, 0.0), "pants")            # seat
        mb.box((0.30, 0.18, 0.30), (0, 0, 0.2), "shirt")            # back
        mb.box((0.28, 0.19, 0.04), (0, 0, 0.06), "black")           # belt
        mb.box((0.2, 0.08, 0.17), (0, -0.12, 0.22), "cap")          # small backpack = back-view cue
        mb.box((0.2, 0.09, 0.03), (0, -0.125, 0.27), "black")       # backpack flap
    _part("torso", hips, coll, torso)

    def head(mb):
        mb.box((0.08, 0.08, 0.06), (0, 0, 0.02), "skin")            # neck
        mb.box((0.18, 0.18, 0.17), (0, 0, 0.12), "skin")            # head
        mb.box((0.03, 0.06, 0.06), (-0.1, 0, 0.12), "skin")         # ears
        mb.box((0.03, 0.06, 0.06), (0.1, 0, 0.12), "skin")
        mb.box((0.185, 0.19, 0.1), (0, -0.003, 0.08), "black")      # back of the hair: no face visible
    _part("head", neck, coll, head)

    def beanie(mb):
        mb.box((0.19, 0.19, 0.12), (0, -0.004, 0.19), "beanie")
        mb.box((0.08, 0.08, 0.07), (0, 0, 0.27), "white")           # pompom
    j = {"root": root, "hips": hips, "neck": neck}
    j["beanie"] = _part("beanie", neck, coll, beanie)
    for crack in range(3):                                          # hard hat power-up states
        hat = _part(f"hardhat_{crack}", neck, coll, lambda mb, c=crack: build_hardhat(mb, c, z=0.13))
        hat.hide_render = True
        j[f"hardhat_{crack}"] = hat
    for side, s in (("L", -1), ("R", 1)):
        sh = _pivot(f"shoulder_{side}", (s * 0.19, 0, 0.32), hips, coll)
        _part(f"uarm_{side}", sh, coll, lambda mb: mb.box((0.09, 0.09, 0.2), (0, 0, -0.1), "shirt"))
        el = _pivot(f"elbow_{side}", (0, 0, -0.2), sh, coll)
        def farm(mb):
            mb.box((0.07, 0.08, 0.15), (0, 0, -0.075), "skin")
            mb.box((0.10, 0.09, 0.08), (0, 0, -0.19), "skin")       # hand / glove
        _part(f"farm_{side}", el, coll, farm)
        hp = _pivot(f"hip_{side}", (s * 0.08, 0, -0.04), hips, coll)
        _part(f"thigh_{side}", hp, coll, lambda mb: mb.box((0.12, 0.12, 0.24), (0, 0, -0.12), "pants"))
        kn = _pivot(f"knee_{side}", (0, 0, -0.24), hp, coll)
        def shin(mb):
            mb.box((0.10, 0.11, 0.2), (0, 0, -0.1), "pants")
            mb.box((0.13, 0.14, 0.07), (0, -0.01, -0.22), "white")  # shoe sole seen from behind
        _part(f"shin_{side}", kn, coll, shin)
        j.update({f"sh_{side}": sh, f"el_{side}": el, f"hip_{side}": hp, f"kn_{side}": kn})
    return root, j


def build_hardhat(mb, crack=0, z=0.0, s=1.0):
    """Yellow construction hard hat (seen from behind), rim at height z.
    crack: 0 intact, 1 cracked, 2 badly cracked (1 hit left)."""
    def b(size, loc, role):
        mb.box(tuple(v * s for v in size), (loc[0] * s, loc[1] * s, z + loc[2] * s), role)
    b((0.29, 0.25, 0.035), (0, 0, 0.0), "hardhat_shade")        # brim all round
    b((0.23, 0.21, 0.06), (0, 0, 0.045), "hardhat")             # dome, stepped for a pixel-round look
    b((0.2, 0.19, 0.05), (0, 0, 0.095), "hardhat")
    b((0.14, 0.15, 0.04), (0, 0, 0.135), "hardhat")
    b((0.04, 0.22, 0.13), (0, -0.005, 0.085), "hardhat_shade")  # centre ridge
    b((0.03, 0.02, 0.03), (-0.07, -0.11, 0.1), "white")          # shine
    if crack >= 1:                                               # zig-zag crack on the visible side
        for p0, p1 in (((0.03, 0.15), (0.06, 0.1)), ((0.06, 0.1), (0.04, 0.06)), ((0.04, 0.06), (0.08, 0.03))):
            mb.bar(((0.02 + p0[0]) * s, z + p0[1] * s), ((0.02 + p1[0]) * s, z + p1[1] * s), 0.03 * s, -0.125 * s, "black", depth=0.01 * s)
    if crack >= 2:
        for p0, p1 in (((-0.03, 0.14), (-0.07, 0.09)), ((-0.07, 0.09), (-0.05, 0.05)), ((-0.05, 0.05), (-0.1, 0.03))):
            mb.bar((p0[0] * s, z + p0[1] * s), (p1[0] * s, z + p1[1] * s), 0.03 * s, -0.125 * s, "black", depth=0.01 * s)
        b((0.05, 0.02, 0.03), (0.08, -0.112, 0.12), "hardhat_shade")  # chipped bit


def set_headgear(j, state):
    """state None = beanie; 0/1/2 = hard hat with that many cracks."""
    j["beanie"].hide_render = state is not None
    for c in range(3):
        j[f"hardhat_{c}"].hide_render = state != c


def ease(s, k=0.6):
    """Signed power easing: lingers at the extremes (grip/hold), snaps through the middle."""
    return math.copysign(abs(s) ** k, s)


def climb_pose(i):
    """Joint angles for climb frame i (0..CYCLE-1).

    Convention: a limb hanging down rotated by +a about Y swings toward
    screen-left, so screen-left limbs use positive angles, right ones negative.
    Overlap: elbows lag shoulders, knees lag hips; hips sway, head counter-sways.
    """
    t = 2 * math.pi * i / CYCLE
    pose = {}
    for side, sgn, ph in (("L", 1, 0.0), ("R", -1, math.pi)):
        reach = ease(math.cos(t + ph))                    # +1 hand high, -1 hand low
        reach_lag = ease(math.cos(t + ph - 0.8))          # elbow follows later
        lift = (1 - ease(math.cos(t + ph - 0.5))) / 2      # knee up while same-side hand low
        lift_lag = (1 - ease(math.cos(t + ph - 1.0))) / 2
        pose[f"sh_{side}"] = sgn * (150 + 27 * reach)
        pose[f"el_{side}"] = sgn * (10 + 60 * (1 - reach_lag) / 2)
        pose[f"hip_{side}"] = sgn * (8 + 58 * lift)
        pose[f"kn_{side}"] = -sgn * (10 + 95 * lift_lag)
    pose["hips_rot"] = 7 * math.sin(t)                       # sway toward reaching side
    pose["hips_x"] = 0.035 * math.cos(t)
    pose["hips_z"] = 0.04 * (0.5 - 0.5 * math.cos(2 * t - 0.6))  # rise after each push
    pose["neck"] = -5 * math.sin(t - 0.6)                    # head counter-sway, delayed
    return pose


def fall_pose():
    return {"sh_L": 115, "el_L": -45, "sh_R": -135, "el_R": 30, "hip_L": 45, "kn_L": 35,
            "hip_R": -25, "kn_R": -70, "hips_rot": 0, "hips_x": 0, "hips_z": 0, "neck": 15}


def brace_pose():
    """Arms folded over the head, knees tucked: braced against a hit."""
    return {"sh_L": 165, "el_L": 115, "sh_R": -165, "el_R": -115, "hip_L": 30, "kn_L": -70,
            "hip_R": -30, "kn_R": 70, "hips_rot": 0, "hips_x": 0, "hips_z": -0.02, "neck": 0}


def hold_pose():
    """Holding tight: both hands high and close, legs pulled up and gripping."""
    return {"sh_L": 172, "el_L": 18, "sh_R": -172, "el_R": -18, "hip_L": 45, "kn_L": -85,
            "hip_R": -45, "kn_R": 85, "hips_rot": 0, "hips_x": 0, "hips_z": 0.06, "neck": 0}


def dyno_pose():
    """Sideways leap: arms flung wide, legs spread."""
    return {"sh_L": 120, "el_L": 0, "sh_R": -120, "el_R": 0, "hip_L": 50, "kn_L": -20,
            "hip_R": -50, "kn_R": 20, "hips_rot": 0, "hips_x": 0, "hips_z": 0.05, "neck": 0}


def set_pose(j, frame, pose):
    for name, v in pose.items():
        if name == "hips_rot":
            j["hips"].rotation_euler.y = math.radians(v)
            j["hips"].keyframe_insert("rotation_euler", index=1, frame=frame)
        elif name == "hips_x":
            j["hips"].location.x = v
            j["hips"].keyframe_insert("location", index=0, frame=frame)
        elif name == "hips_z":
            j["hips"].location.z = 0.5 + v
            j["hips"].keyframe_insert("location", index=2, frame=frame)
        else:
            j[name].rotation_euler.y = math.radians(v)
            j[name].keyframe_insert("rotation_euler", index=1, frame=frame)


def animate(root, j):
    for i in range(CYCLE):
        set_pose(j, i + 1, climb_pose(i))
    set_pose(j, FALL_FRAME, fall_pose())
    set_pose(j, BRACE_FRAME, brace_pose())
    set_pose(j, HOLD_FRAME, hold_pose())
    set_pose(j, DYNO_FRAME, dyno_pose())
    for f, tilt in ((1, 0), (FALL_FRAME - 1, 0), (FALL_FRAME, -28), (BRACE_FRAME, 0)):
        root.rotation_euler.y = math.radians(tilt)
        root.keyframe_insert("rotation_euler", index=1, frame=f)
    for ob in j.values():
        if ob.type == "EMPTY" and ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end, sc.render.fps = 1, CYCLE, 12


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "climber", "climber.blend"))
    a = ap.parse_args(argv)
    clear_scene()
    set_palette(CLIMBER_PALETTE)
    root, j = build_climber()
    animate(root, j)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out))
