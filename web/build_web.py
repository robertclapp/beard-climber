"""web/build_web.py - pack the rendered Blender layers into ONE self-contained index.html.

  blender -b --python web/render_web_assets.py      # once (renders web/build/wizard/raw)
  blender -b --python web/render_web_assets.py -- --level grandpa   # World 1-1 (web/build/grandpa/raw)
  python3 web/build_web.py [--level wizard]          # -> web/index.html

Steps: quantise every raw render to the level's 16-colour palette (+1px black
outline on sprites, exactly like postprocess.py), shelf-pack sprites into one
atlas PNG, add the two level images (closed mouth + open-mouth crop), the
WAV sound effects, the 5x7 pixel font and the tile map, base64-embed it all
as a JSON blob into web/src/index.template.html (which inlines web/src/game.js).
"""
import argparse, base64, io, json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from common import palette_rgb, with_roles
from postprocess import quantize, outline
import levels, sfx, pixfont

POSES = ["c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "fall", "brace", "hold", "dyno"]


def png_bytes(img):
    """PNG, as an indexed (palette) image when that is lossless - every sprite / level image is already quantised to a
    few colours, so this is ~2-3x smaller than RGBA and decodes to exactly the same pixels."""
    b = io.BytesIO()
    img.save(b, "PNG", optimize=True)
    best = b.getvalue()
    try:
        rgba = img.convert("RGBA")
        cols = rgba.getcolors(256)
        if cols:
            pal = [c for _, c in sorted(cols, key=lambda kc: kc[1][3])]          # transparent entries first (short tRNS)
            idx = {c: i for i, c in enumerate(pal)}
            q = Image.new("P", rgba.size)
            q.putpalette([v for c in pal for v in c[:3]])
            q.putdata([idx[c] for c in (rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata())])
            alpha = bytes(c[3] for c in pal)
            b2 = io.BytesIO()
            q.save(b2, "PNG", optimize=True, **({"transparency": alpha} if any(a_ < 255 for a_ in alpha) else {}))
            if Image.open(io.BytesIO(b2.getvalue())).convert("RGBA").tobytes() == rgba.tobytes() and len(b2.getvalue()) < len(best):
                best = b2.getvalue()
    except Exception:
        pass
    return best


def data_uri(raw, mime):
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def pack(sprites, width=512):
    """Simple shelf packer. sprites: {name: (img, anchor)} -> atlas img, {name: [x,y,w,h,ax,ay]}"""
    order = sorted(sprites, key=lambda n: -sprites[n][0].height)
    x = y = shelf = 0
    pos = {}
    for n in order:
        im = sprites[n][0]
        if x + im.width > width:
            x, y, shelf = 0, y + shelf + 1, 0
        pos[n] = (x, y)
        x += im.width + 1
        shelf = max(shelf, im.height)
    atlas = Image.new("RGBA", (width, y + shelf), (0, 0, 0, 0))
    meta = {}
    for n, (px, py) in pos.items():
        im, (ax, ay) = sprites[n]
        atlas.alpha_composite(im, (px, py))
        meta[n] = [px, py, im.width, im.height, ax, ay]
    return atlas, meta


DEFAULT_LOOK = {"k_skin": "#c88058", "k_skin_shade": "#985838", "k_hair": "#382018", "k_hair_shade": "#583828",
                "k_shirt": "#e83828", "k_shirt_shade": "#a02018", "k_pants": "#2848b8",
                "k_gear": "#f8b800", "k_gear_shade": "#b87800", "k_hat": "#8840c8", "k_hat_shade": "#582890"}


def compose_default(keyed, key_hex, cell):
    """Default Pip (boy, short hair, beanie, pack + cat), climb pose c0 - for the home-screen icon."""
    from common import hex_rgb
    out = Image.new("RGBA", (cell, cell))
    for l in ("boy", "short", "pack", "cat", "hh0"):
        k = keyed.get(f"p_{l}_c0")
        if k: out.alpha_composite(k[0], k[1])
    px = out.load()
    mp = {hex_rgb(key_hex[r]): hex_rgb(c) for r, c in DEFAULT_LOOK.items()}
    for y in range(cell):
        for x in range(cell):
            p = px[x, y]
            if p[3] and p[:3] in mp: px[x, y] = mp[p[:3]] + (255,)
    return outline(out)


EXTRA_LEVELS = ["grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa",
                "gnome", "rumpel", "rapunzel", "dwarf"]
# Worlds after World 1 are split out of index.html into assets/world<N>.js (loaded on demand by game.js
# ensureWorld() with a same-origin <script> tag; World 1 + the Wizard + Pip/props/cinematic stay in index.html).
WORLD_OF = {"elf": 2, "rudolph": 2, "ice": 2, "yeti": 2, "santa": 2, "gnome": 3, "rumpel": 3, "rapunzel": 3, "dwarf": 3}   # more playable climbs (World 1-1 Grandpa ...); the Wizard stays the top-level/default data


WIDE_PROPS = {"turnip", "stack", "compass", "selfie", "clover", "leaf", "feather", "berries",
              "hammer", "lantern", "mitten", "cocoa", "cookie", "gingerbread", "star", "snowflake", "crystal", "letter",
              "mushroom", "nametag", "hairbrush", "kingcrown", "ladybug", "spool", "rose", "gem"}   # World 1+2 props: Wizard + Pip colours


def level_block(lid, sprites, prefix=""):
    """Everything that differs per playable level: level image, open-mouth band, happy faces, tile map,
    hazard sprites (atlas names prefixed '<lid>/'), how-to tiles, extras (Grandpa's waving hand)."""
    L = levels.load(lid)
    raw = os.path.join(HERE, "build", lid, "raw")
    m = json.load(open(os.path.join(raw, "manifest.json")))
    pal_lv = palette_rgb(L["palette"])
    ld = lambda n: Image.open(os.path.join(raw, n + ".png"))
    spr = lambda n: outline(quantize(ld(n), pal_lv))
    for i, spins in enumerate(m["hazards"]):
        im = ld(spins[0]).convert("RGBA"); im = im.crop(im.getbbox())
        im = outline(quantize(im.resize((max(1, im.width * 3 // 5), max(1, im.height * 3 // 5)), Image.LANCZOS), pal_lv))
        sprites[f"{prefix}mini_haz{i}"] = (im, (im.width // 2, im.height // 2))
        for f, n in enumerate(spins):
            im = spr(n)
            sprites[f"{prefix}haz{i}_{f}"] = (im, (im.width // 2, im.height // 2))
    for i, n in enumerate(m["tiles"]):                                # used by the how-to screen
        sprites[f"{prefix}tile_{n.split('_', 2)[2]}"] = (quantize(ld(n), pal_lv), (0, 0))
    for f in range(2):
        if os.path.exists(os.path.join(raw, f"hand_{f}.png")):
            im = spr(f"hand_{f}"); im = im.crop(im.getbbox())
            sprites[f"{prefix}hand_{f}"] = (im, (im.width // 2, im.height))
    closed = quantize(ld("level_closed"), pal_lv)
    opened = quantize(ld("level_open"), pal_lv)
    diff = [y for y in range(closed.height) if closed.crop((0, y, closed.width, y + 1)).tobytes()
            != opened.crop((0, y, opened.width, y + 1)).tobytes()]
    y0, y1 = max(0, diff[0] - 2), min(closed.height, diff[-1] + 3)
    mouth = opened.crop((0, y0, opened.width, y1))
    faces = {}
    for nm in ("smile", "sleep"):
        v = quantize(ld("level_" + nm), pal_lv)
        d = [y for y in range(260) if closed.crop((0, y, closed.width, y + 1)).tobytes() != v.crop((0, y, v.width, y + 1)).tobytes()]
        faces[nm] = (v, d[0], d[-1] + 1)
    fy0, fy1 = min(f[1] for f in faces.values()), max(f[2] for f in faces.values())
    face_imgs = {nm: f[0].crop((0, fy0, 224, fy1)) for nm, f in faces.items()}
    return {
        "level": lid, "title": L.get("title", lid.upper()), "start_x": L["start_x"], "start_z": L["start_z"],
        "rows": m["rows"], "top": m["top"], "x_left": m["x_left"], "level_h": m["level_h"],
        "tilemap": m["tilemap"], "col_min_z": m["col_min_z"], "hazard_names": [h[0] for h in L["hazards"]],
        "colors": dict(with_roles(L["palette"], L.get("climber_roles"))),
        "bg": data_uri(png_bytes(closed), "image/png"),
        "mouth": data_uri(png_bytes(mouth), "image/png"), "mouth_y": y0, "mouth_h": y1 - y0,
        "face_smile": data_uri(png_bytes(face_imgs["smile"]), "image/png"),
        "face_sleep": data_uri(png_bytes(face_imgs["sleep"]), "image/png"), "face_y": fy0,
    }, (closed, y0, y1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", default="wizard")
    a = ap.parse_args()
    L = levels.load(a.level)
    raw = os.path.join(HERE, "build", a.level, "raw")
    m = json.load(open(os.path.join(raw, "manifest.json")))
    pal_lv = palette_rgb(L["palette"])
    pal_cl = palette_rgb(with_roles(L["palette"], L.get("climber_roles")))
    ld = lambda n: Image.open(os.path.join(raw, n + ".png"))
    spr = lambda n, pal=pal_lv: outline(quantize(ld(n), pal))

    sprites = {}
    ppu, cc, cell = m["ppu"], m["climber_center"], m["climber_cell"]
    root_anchor = (cell // 2, round(cell / 2 + cc * ppu))            # climber root in the cell
    fall_anchor = (round(cell / 2 + 0.25 * ppu), round(cell / 2 + (cc - 0.17) * ppu))
    pm = json.load(open(os.path.join(raw, "pip_manifest.json")))
    gm = json.load(open(os.path.join(raw, "giants_manifest.json")))

    # ---- Pip + townsfolk + keyed props: KEY colours, no outline (game.js recolours, composes, outlines)
    key_hex = {**pm["fixed"], **pm["keys"]}
    pal_key = palette_rgb(key_hex)
    mask = tuple(int(pm["keys"]["k_mask"][i:i + 2], 16) for i in (1, 3, 5))
    keyed = {}
    def keyed_layer(n):
        im = quantize(ld(n), pal_key)
        px = im.load()
        for y in range(im.height):
            for x in range(im.width):
                if px[x, y][:3] == mask:
                    px[x, y] = (0, 0, 0, 0)
        bb = im.getbbox()
        return (im.crop(bb), bb[:2]) if bb else None
    for n in pm["pip"] + pm["town"]:
        r = keyed_layer(n)
        if r: keyed[n] = r
    prop_anchor = {"gpack": "bottom", "gpack_cat": "bottom", "canopy": "bottom", **{"canopy_" + c: "bottom" for c in pm.get("chutes", [])}}
    for n, k in pm["props"].items():
        if k:
            im = ld("s_" + n)
            r = keyed_layer("s_" + n)
            keyed["s_" + n] = (r[0], (r[1][0] - im.width // 2, r[1][1] - (im.height if prop_anchor.get(n) == "bottom" else im.height // 2)))
        else:
            im = spr("s_" + n, pal_lv + [c for c in palette_rgb(pm["fixed"]) if c not in pal_lv] if n in WIDE_PROPS else pal_lv)
            bb = im.getbbox(); im = im.crop(bb)
            sprites[n] = (im, (im.width // 2, im.height // 2))
    katlas, kmeta_raw = pack({n: (im, (0, 0)) for n, (im, off) in keyed.items()})
    kmeta = {n: v[:4] + list(keyed[n][1]) for n, v in kmeta_raw.items()}   # [x, y, w, h, offx, offy]

    # ---- other giants: portraits (own palette), tossed things + treasures (outlined)
    giants, gimgs = {}, []
    for lid, g in gm.items():
        GL = levels.load(lid)
        gp = palette_rgb(with_roles(GL["palette"], GL.get("climber_roles")))
        cl_ = quantize(ld(f"giant_{lid}_closed"), gp); op_ = quantize(ld(f"giant_{lid}_open"), gp)
        rows_ = [y for y in range(cl_.height) if cl_.crop((0, y, cl_.width, y + 1)).tobytes() != op_.crop((0, y, op_.width, y + 1)).tobytes()]
        gy0, gy1 = max(0, rows_[0] - 1), min(cl_.height, rows_[-1] + 2)
        sprites[f"g_{lid}_mouth"] = (op_.crop((0, gy0, op_.width, gy1)), (0, 0))
        gimgs.append(cl_)
        for k in range(g["toss"]):
            im = outline(quantize(ld(f"toss_{lid}_{k}"), gp)); im = im.crop(im.getbbox())
            sprites[f"toss_{lid}_{k}"] = (im, (im.width // 2, im.height // 2))
        im = outline(quantize(ld(f"treasure_{lid}"), gp)); im = im.crop(im.getbbox())
        sprites[f"treasure_{lid}"] = (im, (im.width // 2, im.height // 2))
        giants[lid] = {"bg": GL["palette"]["bg"], "mouth_y": gy0, "toss": g["toss"], "hair": GL["palette"]["hair2"]}
    gh = gimgs[0].height
    gsheet = Image.new("RGBA", (224, gh * len(gimgs)))
    for i, im in enumerate(gimgs):
        gsheet.paste(im, (0, i * gh))
    for f in range(4):
        im = spr(f"hatitem_{f}", pal_cl)
        sprites[f"hat_{f}"] = (im, (im.width // 2, im.height // 2))
    im = spr("hattangled", pal_cl)
    sprites["hattangled"] = (im, (im.width // 2, im.height // 2))
    wiz, (closed, y0, y1) = level_block(a.level, sprites)
    lvls = {lid: level_block(lid, sprites, lid + "/")[0] for lid in EXTRA_LEVELS if lid != a.level and lid not in WORLD_OF}
    atlas, meta = pack(sprites)
    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    pack_sizes = {}
    for w in sorted(set(WORLD_OF.values())):
        ws = {}
        wl = {lid: level_block(lid, ws, lid + "/")[0] for lid in EXTRA_LEVELS if WORLD_OF.get(lid) == w}
        watlas, wmeta = pack(ws)
        body = {"world": w, "levels": wl, "atlas": data_uri(png_bytes(watlas), "image/png"), "frames": wmeta}
        fn = os.path.join(HERE, "assets", f"world{w}.js")
        open(fn, "w").write("window.BC_PACK(" + json.dumps(body, separators=(",", ":")) + ");\n")
        pack_sizes[w] = os.path.getsize(fn)

    sfx_data = {}
    for k in ("pickup", "clink", "pop", "hurt", "spit", "spit_hat"):
        p = os.path.join(HERE, "build", "sfx", f"{k}.wav")
        if not os.path.exists(p):
            sfx.write_all(os.path.dirname(p))
        sfx_data[k] = data_uri(open(p, "rb").read(), "audio/wav")

    # home-screen icon 180x180: hard-hat climber on the beard
    icon = Image.new("RGBA", (60, 60), tuple(int(L["palette"]["bg"][i:i + 2], 16) for i in (1, 3, 5)) + (255,))
    tile = quantize(ld(m["tiles"][0]), pal_lv)
    for ty in range(0, 60, 32):
        for tx in range(-2, 60, 32):
            icon.alpha_composite(tile, (tx, ty))
    cl = compose_default(keyed, key_hex, cell)
    icon.alpha_composite(cl.crop((10, 4, 62, 70)).resize((40, 50), Image.NEAREST), (10, 6))
    icon = icon.resize((180, 180), Image.NEAREST)

    assets = dict(wiz)
    assets.update({
        "ppu": ppu, "cols": m["cols"],
        "atlas": data_uri(png_bytes(atlas), "image/png"), "frames": meta,
        "sfx": sfx_data,
        "pip": data_uri(png_bytes(katlas), "image/png"), "pframes": kmeta, "keys": key_hex,
        "pip_cell": cell, "pip_anchor": list(root_anchor), "fall_anchor": list(fall_anchor),
        "town_cell": 56, "town_anchor": [28, round(28 + 0.8 * ppu)],
        "hairs": pm["hairs"], "hats": pm["hats"], "bodies": pm["bodies"],
        "patterns": pm["patterns"], "packs": pm["packs"], "chutes": pm["chutes"],
        "giants": giants, "giant_img": data_uri(png_bytes(gsheet), "image/png"), "giant_h": gh,
        "font": {k: v for k, v in pixfont._G.items()},
        "levels": lvls,          # extra playable levels; game.js loadLevel() swaps them in
        "world_of": WORLD_OF,    # level -> world pack (assets/world<N>.js), loaded on demand
    })
    js = open(os.path.join(HERE, "src", "game.js")).read()
    html = open(os.path.join(HERE, "src", "index.template.html")).read()
    html = html.replace("/*ICON*/", data_uri(png_bytes(icon), "image/png"))
    html = html.replace("/*ASSETS*/", "window.ASSETS = " + json.dumps(assets, separators=(",", ":")) + ";")
    html = html.replace("/*GAME*/", js)
    out = os.path.join(HERE, "index.html")
    open(out, "w").write(html)
    icon.save(os.path.join(HERE, "build", "icon180.png"))
    atlas.save(os.path.join(HERE, "build", "atlas.png"))
    katlas.save(os.path.join(HERE, "build", "pip_atlas.png"))
    print(f"wrote {out}: {os.path.getsize(out) / 1024:.0f} KB (atlas {atlas.size}, {len(meta)} sprites, levels {[a.level] + list(lvls)}); packs {pack_sizes}")


if __name__ == "__main__":
    main()
