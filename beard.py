"""beard.py - procedural giant-beard level: tapering beard tip at the bottom, many
rows of modular beard tiles, and the giant's face (level goal) at the very top.

Run stand-alone:  blender -b --python beard.py -- --level viking [--rows 24 --seed 3]

Layout (units; 1 tile = 1 unit = 32 px by default):
  z = 0              lowest point of the beard tip (open background below)
  z in [0, taper]    tip zone: each strand ends at tip_end(x) -> pointed/ragged/forked/round tip
  z in [0, rows]     beard tiles, x in [0, cols]
  z = rows           mouth; mustache, nose, eyes, brows, headwear up to rows + FACE_H
  front faces point at -Y (camera side).
Tile kinds: normal, normal2 (curl lock), knot (good hold), hold (theme hold),
sparse (slippery bald patch), decor.  Strands are continuous across tiles.
The mouth is a separate object (closed / open variants) so it can animate.
"""
import argparse, math, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MeshBuilder

TILE_KINDS = ["normal", "normal2", "knot", "hold", "sparse", "decor"]
STRANDS = 4          # strands per tile
FACE_H = 3.9         # face height above the beard (mouth at rows, hat brim at rows+FACE_H)


# ------------------------------------------------------------------ tip silhouette
def _jit(g):
    """Deterministic 0..1 jitter per strand index (so tips are ragged but reproducible)."""
    return ((g * 7919 + 13) % 17) / 16.0


def tip_end(L, xg, cols):
    """Lowest z where hair exists at global x (strand centre). Shapes per level 'tip'."""
    T = L["taper_rows"]
    u = min(1.0, abs(xg - cols / 2) / (cols / 2))
    j = _jit(int(xg * STRANDS))
    shape = L["tip"]
    if shape == "point":          # long wizard point
        return T * u ** 1.25 + 0.35 * j
    if shape == "ragged":         # broad shaggy bottom
        return T * 0.45 * u ** 2 + 1.1 * j
    if shape == "round":          # big round santa bottom
        return T * (1 - math.sqrt(max(0.0, 1 - u * u))) + 0.25 * j
    if shape == "fork":           # pirate: two points tied with ribbons
        pts = L.get("fork_x", (0.32, 0.68))
        d = min(abs(xg - p * cols) for p in pts) / (cols * 0.3)
        return T * min(1.0, d) ** 1.1 + 0.3 * j
    if shape == "braids":         # viking: rounded bottom, braids hang lower (see build_beard)
        return T * 0.3 + T * 0.7 * u ** 2 + 0.5 * j
    return 0.0


# ------------------------------------------------------------------ strands
def _wave(L, xg, zg, k):
    """x-offset of a strand at global height zg (continuous across tiles)."""
    return L["wave_amp"] * math.sin(2 * math.pi * zg / L["wave_period"] + k * 1.3 + xg * 0.7)


def strands(mb, L, x0, z0, gcol, density=1.0, width=0.19, zcut=None):
    """Vertical wavy hair strands for one tile. zcut(x) -> z where hair starts (tip zone)."""
    pattern = L["strand_pattern"]
    n = max(1, int(STRANDS * density))
    seg = 4
    w = width * (1.0 if density >= 1 else 0.55)
    for i in range(n):
        g = gcol * STRANDS + i
        role = pattern[g % len(pattern)]
        xc = x0 + (i + 0.5) / n
        ze = zcut(xc) if zcut else -1e9
        if ze >= z0 + 1:
            continue
        if zcut:                         # per-strand dark backing strip in the tip zone
            zb0 = max(z0, ze)
            mb.box((1.0 / n, 0.06, z0 + 1 - zb0), (xc, 0.03, (z0 + 1 + zb0) / 2), "hair1")
        for s in range(seg):
            za, zb = z0 + s / seg, z0 + (s + 1) / seg
            if zb <= ze:
                continue
            za = max(za, ze)
            xa, xb = xc + _wave(L, g, za, g), xc + _wave(L, g, zb, g)
            mb.bar((xa, za), (xb, zb), w, -0.05, role, depth=0.06)
            if role == pattern[0] and s % 2 == 0 and zb - za > 0.15:
                mb.bar((xa - 0.05, za + 0.03), (xb - 0.05, zb - 0.03), 0.045, -0.085, "hair4", depth=0.02)
        if z0 <= ze < z0 + 1:            # pointed strand end hanging below the cut
            xt = xc + _wave(L, g, ze, g)
            mb.bar((xt, ze + 0.12), (xt + 0.04 * (1 if g % 2 else -1), ze - 0.18), w * 0.45, -0.05, role, depth=0.06)


def fluffy(mb, L, x0, z0, zcut=None):
    """Santa style: a clean global grid of large round puffs (2x2 per tile),
    each with a dark rim, mid tone and one highlight. Odd puff rows are offset."""
    for r in range(2):
        zc = z0 + 0.25 + r * 0.5
        row = int(round((zc - 0.25) / 0.5))
        off = 0.25 if row % 2 else 0.0
        for c in range(2):
            xc = x0 + 0.25 + c * 0.5 + off
            if zcut and zc < zcut(min(xc, x0 + 0.99)) + 0.1:
                continue
            mid = "hair3" if (row + c + int(x0)) % 3 else "hair2"
            mb.disc(0.3, (xc, -0.03, zc), "hair1", depth=0.05, seg=10)
            mb.disc(0.255, (xc, -0.06, zc + 0.01), mid, depth=0.03, seg=10)
            mb.disc(0.12, (xc - 0.08, -0.08, zc + 0.09), "white", depth=0.02, seg=8)


def base(mb, L, x0, z0, role="hair1"):
    mb.box((1.0, 0.06, 1.0), (x0 + 0.5, 0.03, z0 + 0.5), role)


# ------------------------------------------------------------------ hold props
def knot(mb, cx, cz):
    """Twisted tangle: the classic 'good grip' tile."""
    mb.disc(0.26, (cx, -0.12, cz), "hair1", depth=0.05)
    mb.bar((cx - 0.24, cz - 0.16), (cx + 0.22, cz + 0.18), 0.19, -0.14, "black")
    mb.bar((cx - 0.24, cz - 0.16), (cx + 0.22, cz + 0.18), 0.12, -0.16, "hair3")
    mb.bar((cx - 0.22, cz + 0.17), (cx + 0.24, cz - 0.15), 0.19, -0.17, "black")
    mb.bar((cx - 0.22, cz + 0.17), (cx + 0.24, cz - 0.15), 0.12, -0.18, "hair4")
    mb.disc(0.07, (cx, -0.21, cz), "hair1", depth=0.03)


def hold_prop(mb, kind, cx, cz):
    if kind == "knot":
        knot(mb, cx, cz)
    elif kind == "ring":            # viking metal ring
        for k in range(8):
            a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            mb.bar((cx + 0.24 * math.cos(a0), cz + 0.24 * math.sin(a0)),
                   (cx + 0.24 * math.cos(a1), cz + 0.24 * math.sin(a1)), 0.085, -0.16, "acc2")
        mb.bar((cx - 0.17, cz + 0.17), (cx - 0.05, cz + 0.22), 0.05, -0.2, "white")
    elif kind == "bead":            # gold beads strung on a strand
        for dz in (-0.25, 0.0, 0.25):
            mb.disc(0.11, (cx, -0.15, cz + dz), "acc3", depth=0.06)
            mb.box((0.04, 0.02, 0.04), (cx - 0.04, -0.19, cz + dz + 0.04), "white")
    elif kind == "ribbon":          # pirate: red bow tied around a lock of hair
        for sx in (-1, 1):
            mb.disc(0.14, (cx + sx * 0.17, -0.14, cz + 0.06), "acc1", depth=0.05)   # bow loops
            mb.disc(0.06, (cx + sx * 0.17, -0.18, cz + 0.06), "lips", depth=0.02)   # loop holes
            mb.bar((cx + sx * 0.03, cz - 0.02), (cx + sx * 0.16, cz - 0.36), 0.08, -0.15, "acc1")  # tails
        mb.box((0.12, 0.06, 0.14), (cx, -0.19, cz + 0.04), "acc1")                  # knot
        mb.box((0.04, 0.03, 0.14), (cx - 0.03, -0.23, cz + 0.04), "lips")
    elif kind == "star":            # wizard star charm tied into a knot
        knot(mb, cx, cz - 0.05)
        star(mb, cx + 0.16, cz + 0.2, 0.13, "acc3")
    elif kind == "twig":            # lumberjack: a stuck pine twig to grab
        mb.bar((cx - 0.38, cz - 0.25), (cx + 0.36, cz + 0.22), 0.08, -0.15, "hair1")
        for t in (-0.2, 0.0, 0.2):
            mb.bar((cx + t, cz + t * 0.62), (cx + t - 0.1, cz + t * 0.62 + 0.15), 0.06, -0.17, "acc2")
            mb.bar((cx + t, cz + t * 0.62), (cx + t + 0.1, cz + t * 0.62 - 0.14), 0.06, -0.17, "acc2")
    elif kind == "curl":            # santa: big snowy curl
        mb.disc(0.3, (cx, -0.12, cz), "hair2", depth=0.05)
        mb.disc(0.22, (cx + 0.03, -0.15, cz + 0.03), "white", depth=0.05)
        mb.disc(0.1, (cx + 0.06, -0.18, cz + 0.05), "hair2", depth=0.03)


def star(mb, cx, cz, r, role, y=-0.2):
    """Tiny 4-point star / sparkle."""
    mb.box((r * 2, 0.03, r * 0.55), (cx, y, cz), role)
    mb.box((r * 0.55, 0.03, r * 2), (cx, y, cz), role)
    mb.box((r * 0.7, 0.03, r * 0.7), (cx, y, cz), role, ry=45)


def braid(mb, L, x0, z0):
    """Viking braid running down the tile centre: interleaved chevrons."""
    mb.box((0.5, 0.05, 1.0), (x0 + 0.5, -0.09, z0 + 0.5), "hair1")
    for k in range(4):
        z = z0 + 0.125 + k * 0.25
        mb.bar((x0 + 0.28, z + 0.07), (x0 + 0.5, z - 0.07), 0.11, -0.13, "hair3" if k % 2 else "hair4")
        mb.bar((x0 + 0.5, z - 0.07), (x0 + 0.72, z + 0.07), 0.11, -0.13, "hair4" if k % 2 else "hair3")


def decor(mb, L, x0, z0, rng):
    kind = L["decor"]
    for _ in range(4 if kind != "stars" else 2):
        x, z = x0 + rng.uniform(0.15, 0.85), z0 + rng.uniform(0.15, 0.85)
        if kind == "stars":
            star(mb, x, z, 0.09, "acc3")
        elif kind == "crumbs":          # pancake / cookie crumbs
            mb.box((0.08, 0.04, 0.07), (x, -0.13, z), L["crumb_role"], ry=rng.uniform(0, 90))
        elif kind == "coins":
            mb.disc(0.06, (x, -0.13, z), "acc3", depth=0.03)
        elif kind == "beads":
            mb.disc(0.06, (x, -0.13, z), "acc2", depth=0.03)
        elif kind == "snow":
            star(mb, x, z, 0.06, "white")


# ------------------------------------------------------------------ tiles
def build_tile(mb, L, kind, x0, z0, rng, gcol, grow, hold_kind=None, zcut=None):
    """Add one beard tile with lower-left corner (x0, z0). zcut: tip-zone clipping."""
    if zcut:
        if max(zcut(x0 + (i + 0.5) / STRANDS) for i in range(STRANDS)) <= z0:
            zcut = None                  # tile fully covered: treat as a normal tile
        else:
            kind = "normal"              # partially bald tip tile: no props
    if not zcut:
        base(mb, L, x0, z0, "hair1")
    if kind == "sparse":                 # slippery bald patch: shiny skin, a few thin strands
        mb.disc(0.42, (x0 + 0.5, -0.01, z0 + 0.5), "skin", depth=0.02, seg=10)
        strands(mb, L, x0, z0, gcol, density=0.5)
        mb.bar((x0 + 0.25, z0 + 0.72), (x0 + 0.42, z0 + 0.55), 0.05, -0.12, "white")
        mb.bar((x0 + 0.58, z0 + 0.4), (x0 + 0.68, z0 + 0.3), 0.05, -0.12, "white")
        return
    if L["style"] == "fluffy":
        if zcut:                         # puffs need a backing only where hair exists
            for i in range(STRANDS):
                xc = x0 + (i + 0.5) / STRANDS
                ze = max(z0, zcut(xc) + 0.1)
                if ze < z0 + 1:
                    mb.box((1.0 / STRANDS, 0.06, z0 + 1 - ze), (xc, 0.03, (z0 + 1 + ze) / 2), "hair1")
        fluffy(mb, L, x0, z0, zcut)
    else:
        strands(mb, L, x0, z0, gcol, zcut=zcut)
    if gcol in L.get("braid_cols", []):
        braid(mb, L, x0, z0)
    if kind == "normal2":                # a loose curl lock over the strands
        mb.bar((x0 + 0.3, z0 + 0.85), (x0 + 0.62, z0 + 0.5), 0.08, -0.11, "hair4")
        mb.bar((x0 + 0.62, z0 + 0.5), (x0 + 0.45, z0 + 0.18), 0.08, -0.11, "hair3")
    elif kind == "knot":
        knot(mb, x0 + 0.5, z0 + 0.5)
    elif kind == "hold":
        hold_prop(mb, hold_kind or L["holds"][0], x0 + 0.5, z0 + 0.5)
    elif kind == "decor":
        decor(mb, L, x0, z0, rng)


def pick_kind(L, rng):
    r, acc = rng.random(), 0.0
    for k, w in L["tile_weights"].items():
        acc += w
        if r < acc:
            return k
    return "normal"


def fringe(mb, L, x, z0, z1, side, rng):
    """Wispy beard edge so the outline is not a straight wall."""
    z = z0
    while z < z1:
        ln = rng.uniform(0.15, 0.35)
        mb.bar((x, z + 0.25), (x + side * ln, z - 0.05), 0.12, -0.03, L["strand_pattern"][int(z * 3) % len(L["strand_pattern"])], depth=0.05)
        z += rng.uniform(0.22, 0.4)


# ------------------------------------------------------------------ face (goal)
def mustache(mb, L, cx, zm):
    styles = {
        "droop":     ([(0.05, 0.95), (0.8, 0.85), (1.5, 0.6), (2.0, 0.15), (2.25, -0.45), (2.3, -1.0)], 0.55, 0.28),
        "bushy":     ([(0.05, 0.9), (1.0, 0.88), (1.9, 0.72), (2.6, 0.45)], 0.75, 0.55),
        "curl":      ([(0.05, 0.9), (0.9, 0.82), (1.7, 0.78), (2.3, 0.98), (2.5, 1.35)], 0.6, 0.4),
        "thin_curl": ([(0.05, 0.95), (0.8, 0.88), (1.5, 0.82), (2.0, 0.98), (2.1, 1.28), (1.88, 1.4)], 0.32, 0.16),
    }
    if L["mustache"] == "none":                 # e.g. the Goat: just a chin beard
        return
    pts, t0, t1 = styles[L["mustache"]]
    for s in (-1, 1):
        n = len(pts) - 1
        for i in range(n):
            th = t0 + (t1 - t0) * i / max(1, n - 1)
            p0 = (cx + s * pts[i][0], zm + pts[i][1] - 0.9)
            p1 = (cx + s * pts[i + 1][0], zm + pts[i + 1][1] - 0.9)
            mb.bar(p0, p1, th + 0.08, -0.32, "hair1", depth=0.08)      # dark edge
            mb.bar(p0, p1, th, -0.38, "hair3", depth=0.06)
            mb.bar((p0[0], p0[1] + th * 0.2), (p1[0], p1[1] + th * 0.2), th * 0.35, -0.42, "hair4", depth=0.03)


def face(mb, L, cols, rows, rng):
    """Static part of the giant's face (everything except the mouth)."""
    cx, z = cols / 2, rows
    mb.box((cols - 1.2, 0.05, FACE_H + 0.6), (cx, 0.04, z + FACE_H / 2 + 0.2), "skin")
    for c in (0, 1, cols - 2, cols - 1):                    # cheek beard
        build_tile(mb, L, "normal", c, z, rng, c, rows)
    for r in range(1, 4):                                   # sideburns
        for c in (0, cols - 1):
            build_tile(mb, L, "normal", c, z + r, rng, c, rows + r)
    fringe(mb, L, 1.0, z + 1, z + FACE_H, 1, rng)
    fringe(mb, L, cols - 1.0, z + 1, z + FACE_H, -1, rng)
    mustache(mb, L, cx, z + 0.9)
    mb.box((1.1, 0.1, 1.05), (cx, -0.2, z + 1.95), "skin_shade")   # nose
    mb.box((0.94, 0.1, 0.92), (cx, -0.24, z + 2.02), "skin")
    mb.box((0.6, 0.05, 0.08), (cx, -0.3, z + 1.62), "skin_shade")
    for s in (-1, 1):
        mb.box((0.16, 0.05, 0.1), (cx + s * 0.3, -0.3, z + 1.52), "black")
    if L.get("cheeks"):
        for s in (-1, 1):
            mb.disc(0.38, (cx + s * 1.45, -0.02, z + 1.7), "skin_shade", depth=0.04)
    ez = z + 2.55                                           # eyes looking DOWN at the climber
    for s in (-1, 1):
        ex = cx + s * 1.2
        if L.get("eyepatch") and s == 1:
            mb.box((0.8, 0.05, 0.6), (ex, -0.12, ez), "black")
            mb.bar((ex - 0.4, ez + 0.2), (cx - 2.4, ez + 1.0), 0.08, -0.12, "black")
            mb.bar((ex + 0.4, ez + 0.2), (cx + 2.4, ez + 0.7), 0.08, -0.12, "black")
            continue
        mb.box((0.72, 0.05, 0.4), (ex, -0.06, ez), "black")
        mb.box((0.62, 0.05, 0.3), (ex, -0.08, ez), "white")
        mb.box((0.24, 0.05, 0.2), (ex - s * 0.05, -0.1, ez - 0.05), "black")
        bz = ez + 0.42
        bw = 1.0 if L.get("brows") == "bushy" else 0.8
        bt = 0.3 if L.get("brows") == "bushy" else 0.16
        mb.bar((ex - s * bw / 2, bz - 0.06), (ex + s * bw / 2, bz + 0.08), bt, -0.1, "hair3")
    if L.get("face_extra"):                                 # e.g. Grandpa's glasses
        L["face_extra"](mb, cx, ez, cols)
    L["headwear"](mb, cx, z + 3.3, cols)


def mouth(mb, L, cols, rows, open_=False):
    """Mouth variants. Closed: dark line + lower lip. Open: big cavity, teeth, tongue,
    dropped lower lip - drawn in front of the chin beard (the mustache stays on top)."""
    cx, z = cols / 2, rows
    if not open_:
        mb.box((1.3, 0.05, 0.2), (cx, -0.25, z + 0.42), "black")
        mb.box((1.1, 0.05, 0.22), (cx, -0.26, z + 0.22), "lips")
        return
    mb.box((1.7, 0.05, 1.25), (cx, -0.25, z + 0.02), "lips")       # lip ring
    mb.box((1.5, 0.05, 1.05), (cx, -0.27, z + 0.04), "black")      # cavity
    mb.box((1.2, 0.05, 0.14), (cx, -0.29, z + 0.5), "white")       # upper teeth
    mb.box((0.9, 0.05, 0.26), (cx, -0.29, z - 0.32), "lips")       # tongue
    mb.box((0.04, 0.05, 0.14), (cx, -0.3, z + 0.5), "black")


def build_beard(L, cols=6, rows=None, seed=1):
    """Return a MeshBuilder holding the whole level (beard tip -> face, mouth excluded)."""
    rows = rows or L["rows"]
    rng = random.Random(seed)
    mb = MeshBuilder()
    T = L["taper_rows"]
    zcut = lambda x: tip_end(L, x, cols)
    tilemap = []                       # what each tile really is (for gameplay: holds / bald patches)
    for r in range(rows):
        row = []
        for c in range(cols):
            kind = pick_kind(L, rng)
            hold = rng.choice(L["holds"])
            tip = r < math.ceil(T + 1.2)
            if tip and max(zcut(c + (i + 0.5) / STRANDS) for i in range(STRANDS)) > r:
                kind = "normal"        # partial tip tiles never carry props (see build_tile)
            kind = L.get("forced_tiles", {}).get((c, r), kind)   # hand-placed tiles (e.g. tutorial bald patch)
            build_tile(mb, L, kind, c, r, rng, c, r, hold, zcut if tip else None)
            row.append(kind)
        tilemap.append(row)
    mb.tilemap = tilemap
    mb.col_min_z = [round(zcut(c + 0.5), 3) for c in range(cols)]
    for bc in L.get("braid_cols", []):          # viking braids hang below the beard: metal end caps
        mb.box((0.34, 0.08, 0.16), (bc + 0.5, -0.16, 0.12), "acc1")
        mb.box((0.38, 0.09, 0.05), (bc + 0.5, -0.2, 0.12), "acc2")
        for dx in (-0.12, 0.0, 0.12):
            mb.bar((bc + 0.5 + dx, 0.05), (bc + 0.5 + dx * 1.6, -0.3), 0.08, -0.1, "hair3")
    for fx in L.get("fork_x", ()) if L["tip"] == "fork" else ():   # ribbons tying the fork points
        hold_prop(mb, "ribbon", fx * cols, T * 0.18 + 0.45)
    fringe(mb, L, 0.0, zcut(0.1) + 0.3, rows, -1, rng)
    fringe(mb, L, float(cols), zcut(cols - 0.1) + 0.3, rows, 1, rng)
    face(mb, L, cols, rows, rng)
    return mb


if __name__ == "__main__":
    import bpy
    from common import clear_scene, new_collection, set_palette
    import levels
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="wizard")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    L = levels.load(a.level)
    clear_scene(); set_palette(L["palette"])
    coll = new_collection("Beard")
    rows = a.rows or L["rows"]
    build_beard(L, a.cols, rows, a.seed if a.seed is not None else L["seed"]).to_object("beard", coll)
    for flag in (False, True):
        m = MeshBuilder(); mouth(m, L, a.cols, rows, flag)
        m.to_object("mouth_open" if flag else "mouth_closed", coll).hide_render = flag
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", a.level, "beard.blend")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
