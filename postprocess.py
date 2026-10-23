"""postprocess.py - raw Blender renders -> early-80s arcade pixel art (Python 3 + Pillow).

  python3 postprocess.py [--out out] [--levels wizard,viking] [--dither] [--no-outline] [--scale 4]

Composes every game frame, the whole-level strip and the scroll GIF from the
raw layers rendered by render_levels.py (see class Level for the timeline).
Per image: alpha threshold -> nearest colour in the LEVEL's 16-colour palette
(optional 4x4 Bayer ordered dither) -> 1px black outline around sprites ->
nearest-neighbour upscale for previews.  Also builds out/levels_overview.png.
"""
import argparse, json, math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import palette_rgb, hex_rgb, CLIMBER_PALETTE, with_roles
from pixfont import draw_text, text_width, text_image
import sfx
import levels

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def quantize(img, pal, dither=False, strength=24):
    img = img.convert("RGBA")
    px = img.load()
    cache = {}
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            if dither:
                d = (BAYER4[y % 4][x % 4] / 15.0 - 0.5) * strength
                r, g, b = (max(0, min(255, int(c + d))) for c in (r, g, b))
            c = cache.get((r, g, b))
            if c is None:
                c = min(pal, key=lambda p: 2 * (p[0] - r) ** 2 + 4 * (p[1] - g) ** 2 + 3 * (p[2] - b) ** 2)
                cache[(r, g, b)] = c
            px[x, y] = c + (255,)
    return img


def outline(img, color=(0, 0, 0)):
    """1px outline in transparent pixels 4-adjacent to opaque ones."""
    s = img.copy().load()
    d = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if s[x, y][3]:
                continue
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and s[nx, ny][3]:
                    d[x, y] = color + (255,)
                    break
    return img


def up(img, k):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def save2(img, path, k):
    """Save 1x and _x<k> versions."""
    img.save(path)
    root, ext = os.path.splitext(path)
    up(img, k).save(f"{root}_x{k}{ext}")


def sheet(rows, pad=0, bg=(0, 0, 0, 0)):
    """rows: list of lists of equal-size images -> grid image."""
    w, h = rows[0][0].size
    cols = max(len(r) for r in rows)
    out = Image.new("RGBA", (cols * (w + pad) - pad, len(rows) * (h + pad) - pad), bg)
    for j, r in enumerate(rows):
        for i, im in enumerate(r):
            out.paste(im, (i * (w + pad), j * (h + pad)), im)
    return out


def pixel_text(text, scale, color, bg):
    """Chunky pixel label: render tiny bitmap text, threshold, upscale nearest."""
    try:
        font = ImageFont.load_default(size=10)
    except TypeError:
        font = ImageFont.load_default()
    w = int(font.getlength(text)) + 4
    im = Image.new("L", (w, 14), 0)
    ImageDraw.Draw(im).text((2, 1), text, fill=255, font=font)
    im = im.point(lambda v: 255 if v > 110 else 0)
    out = Image.new("RGBA", im.size, bg)
    out.paste(Image.new("RGBA", im.size, color), (0, 0), im)
    return up(out, scale)


# ------------------------------------------------------------------ level timeline
SCROLL_FRAMES = 60      # camera pans from the beard tip to the face
END_FRAMES = 26         # hold at the top: mouth spits a hazard, then a hard hat
SPIT_AT = SCROLL_FRAMES + 6
HAT_THROW_AT = SCROLL_FRAMES + 15   # the 'good' item thrown from the mouth
AIMED_HITS = (26, 38, 50)           # throws aimed at the climber (demo of the hard hat)
FALL_SPEED = 0.26       # hazard fall speed, units per frame (constant, arcade style)
EMERGE = 3              # frames a thrown item spends emerging from the mouth
FRAME_MS = 90           # GIF / MP4 frame time
HAT_HITS = 3            # hits a hard hat absorbs
HIT_R = (0.5, 0.75)     # collision half-size around the climber's upper body (x, z)


PIP = ("..###..", ".#####.", "#######", "#######", "#########")   # 9 wide brim row (offset -1)


def hat_pip(img, x, y, fill, edge):
    """Hard-hat HUD icon: filled = hit left, outline only = used up."""
    pts = {(x + c - (1 if r == 4 else 0), y + r) for r, row in enumerate(PIP) for c, ch in enumerate(row) if ch == "#"}
    border = {(px + dx, py + dy) for (px, py) in pts for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))} - pts
    for (px, py) in (pts if fill else set()) | (border if edge else set()):
        if 0 <= px < img.width and 0 <= py < img.height:
            img.putpixel((px, py), fill if (px, py) in pts else edge)
    if not fill:                                   # empty pip: outline the shape itself
        for (px, py) in border:
            if 0 <= px < img.width and 0 <= py < img.height:
                img.putpixel((px, py), edge)


def smooth(t):
    return t * t * (3 - 2 * t)


def plus(img, x, y, col, r=1):
    for d in range(-r, r + 1):
        for (px, py) in ((x + d, y), (x, y + d)):
            if 0 <= px < img.width and 0 <= py < img.height:
                img.putpixel((px, py), col)


class Level:
    """All layers of one level + the deterministic timeline used by every output.

    Throws: every item leaves the MOUTH (L['spawn']), sits there EMERGE frames,
    then falls at FALL_SPEED with sideways drift. When the face is off-screen
    hazards simply enter from the top edge (they were thrown far above).
    A few throws are aimed at the climber so the hard-hat demo shows 3 hits.
    Hard hat: one sits tangled in the beard (picked up when the climber reaches
    it); the mouth also throws one as a 'good' item (distinct white/gold sparkle).
    Wearing it, a hit is absorbed: no knock-back, hat flashes + cracks, HUD pip
    lost; the 3rd hit pops it off. Without a hat a hit shows the 'hurt' pose.
    """

    def __init__(self, lid, a):
        self.L = L = levels.load(lid)
        self.a, self.lid = a, lid
        self.dir = os.path.join(a.out, lid)
        self.raw = os.path.join(self.dir, "raw")
        self.m = m = json.load(open(os.path.join(self.raw, "manifest.json")))
        self.pal = palette_rgb(L["palette"])
        self.colors = {k: hex_rgb(v) + (255,) for k, v in with_roles(L["palette"], L.get("climber_roles")).items()}
        q = lambda n: quantize(Image.open(os.path.join(self.raw, n + ".png")), self.pal, a.dither)
        spr = lambda n: q(n) if a.no_outline else outline(q(n))
        self.q, self.spr = q, spr
        self.bg = {False: q("level_closed"), True: q("level_open")}
        n = m["cycle"]
        self.climb = [spr(f"climb_{i:02d}") for i in range(n)]
        self.climbhat = [[spr(f"climbhat{c}_{i:02d}") for i in range(n)] for c in range(3)]
        self.hatmask = [Image.open(os.path.join(self.raw, f"hatmask_{i:02d}.png")).convert("RGBA") for i in range(n)]
        self.fall = spr("fall")
        self.hatitem = [spr(f"hatitem_{f}") for f in range(4)]
        self.hattangled = spr("hattangled")
        self.haz = [[spr(nm) for nm in row] for row in m["hazards"]]
        self.enemy = [spr(nm) for nm in m["enemy"]]
        self.ppu, self.top, self.cols, self.rows = m["ppu"], m["top"], m["cols"], m["rows"]
        self.vh = m["height"] / self.ppu
        self.zmin = -m["bottom_margin"]
        self.mouth = (self.cols / 2 + L["spawn"][0], self.rows + L["spawn"][1])
        self.total = SCROLL_FRAMES + END_FRAMES
        self._plan_throws()
        self._simulate()

    # ---------------- geometry
    def px(self, x, z):
        return (round((x - self.m["x_left"]) * self.ppu), round((self.top - z) * self.ppu))

    def climber_z(self, f):
        t = smooth(min(1.0, f / SCROLL_FRAMES))
        z0, z1 = self.L["start_z"], self.rows - 3.4
        return z0 + (z1 - z0) * t

    def climber_x(self, f):
        t = smooth(min(1.0, f / SCROLL_FRAMES))
        return self.L["start_x"] + (self.L.get("end_x", 1.9) - self.L["start_x"]) * t

    def cam_bottom(self, f):
        """Camera follows the climber; he drifts from lower-middle to lower screen."""
        off = 1.9 + (0.7 - 1.9) * smooth(min(1.0, f / SCROLL_FRAMES))
        return max(self.zmin, min(self.top - self.vh, self.climber_z(f) - off))

    # ---------------- throws
    def _plan_throws(self):
        L = self.L
        rng = __import__("random").Random(L["seed"])
        cx, cz = self.mouth
        aimed = []
        for fh in AIMED_HITS:                   # back-solve throws that meet the climber's head
            zt, xt = self.climber_z(fh) + 1.5, self.climber_x(fh) + 0.05
            fall = (cz - 0.2 - zt) / FALL_SPEED
            aimed.append({"s": fh - EMERGE - round(fall), "drift": (xt - cx) / max(1, round(fall)), "kind": "hazard"})
        good = [{"s": HAT_THROW_AT, "drift": 0.06, "kind": "hat"}]
        taken = [t["s"] for t in aimed + good]
        regular = []
        for k in range(70):
            s = SPIT_AT - k * L["throw_period"]
            if any(abs(s - t) <= 4 for t in taken):
                continue
            d = (1 if k % 2 else -1) * rng.uniform(0.5, 1.0) * L["drift"]
            # un-aimed throws are steered so they miss the climber's path (only the
            # aimed ones hit, so the demo shows exactly the 3 hard-hat hits)
            for cand in (d, -d, 1.6 * d, -1.6 * d, 0.4 * d, -0.4 * d, 0.14, -0.14):
                t = {"s": s, "drift": cand, "kind": "hazard"}
                if not self._would_hit(t):
                    regular.append(t)
                    break
        self.throws = sorted(aimed + good + regular, key=lambda t: -t["s"])
        for i, t in enumerate(self.throws):
            t["id"], t["hi"] = i, i % len(self.haz)

    def _would_hit(self, t, margin=(0.35, 0.3)):
        for f in range(SCROLL_FRAMES + END_FRAMES):
            p = self.throw_pos(t, f)
            if p and p[2] > EMERGE:
                if (abs(p[0] - self.climber_x(f)) < HIT_R[0] + margin[0]
                        and abs(p[1] - self.climber_z(f) - 1.1) < HIT_R[1] + margin[1]):
                    return True
        return False

    def throw_pos(self, t, f):
        """Undeflected position of a throw at frame f (None if not thrown yet)."""
        age = f - t["s"]
        if age < 0:
            return None
        cx, cz = self.mouth
        if age <= EMERGE:
            return cx, cz + 0.15 - 0.12 * age, age
        fall = age - EMERGE
        x = cx + t["drift"] * fall
        lo, hi = 0.6, self.cols - 0.6                # bounce off the beard edges
        span = hi - lo
        p = (x - lo) % (2 * span)
        x = lo + (p if p <= span else 2 * span - p)
        return x, cz - 0.2 - FALL_SPEED * fall, age

    def mouth_open(self, f):
        return any(t["s"] - 2 <= f <= t["s"] + EMERGE for t in self.throws)

    # ---------------- power-up / hit simulation (runs once, frame by frame)
    def _simulate(self):
        pu = self.L.get("powerup", {})
        self.pick_f = pu.get("tangled_at", 10)
        self.tangled_pos = (self.climber_x(self.pick_f) + 0.05, self.climber_z(self.pick_f) + 1.75)
        hits, flash_until, hurt_until, pop = None, -1, -1, None
        deflect, collected = {}, set()
        self.state, self.events = [], []
        for f in range(self.total):
            ccx, ccz = self.climber_x(f), self.climber_z(f) + 1.1
            if f == self.pick_f:
                hits = HAT_HITS
                self.events.append((f, "pickup"))
            for t in self.throws:
                if t["id"] in deflect or t["id"] in collected:
                    continue
                p = self.throw_pos(t, f)
                if p is None or p[2] <= EMERGE:
                    continue
                if abs(p[0] - ccx) < HIT_R[0] and abs(p[1] - ccz) < HIT_R[1]:
                    if t["kind"] == "hat":               # caught a thrown hard hat
                        collected.add(t["id"]); hits = HAT_HITS
                        self.events.append((f, "pickup"))
                        continue
                    deflect[t["id"]] = (f, p[0], p[1], 1 if p[0] >= ccx else -1)
                    if hits:
                        hits -= 1
                        flash_until = f + 2
                        self.events.append((f, "clink"))
                        if hits == 0:
                            pop = (f, ccx, self.climber_z(f) + 1.75)
                            hits = None
                            self.events.append((f, "pop"))
                    else:
                        hurt_until = f + 3
                        self.events.append((f, "hurt"))
            self.state.append({"hits": hits, "flash": f <= flash_until, "hurt": f <= hurt_until,
                               "pop": pop, "deflect": dict(deflect), "collected": set(collected)})
        for t in self.throws:
            if t["s"] >= 0 and t["s"] < self.total:
                self.events.append((t["s"], "spit_hat" if t["kind"] == "hat" else "spit"))
        self.events.sort()

    def items_at(self, f):
        """[(x, z, sprite, kind)] for every thrown item visible at frame f."""
        st = self.state[f]
        out = []
        for t in self.throws:
            if t["id"] in st["collected"]:
                continue
            p = self.throw_pos(t, f)
            if p is None:
                continue
            x, z, age = p
            spin = (age // 2) % 4 if age > EMERGE else 0
            if t["id"] in st["deflect"]:                 # bounced off the climber
                f0, x0, z0, d = st["deflect"][t["id"]]
                k = f - f0
                x, z = x0 + d * 0.28 * k, z0 + 0.2 * k - 0.05 * k * k
                spin = (k + age) % 4
            if z < self.zmin - 1:
                continue
            sp = self.hatitem[spin] if t["kind"] == "hat" else self.haz[t["hi"]][spin]
            out.append((x, z, sp, t["kind"]))
        return out

    # ---------------- drawing
    def _paste(self, img, sp, x, z):
        px, py = self.px(x, z)
        img.alpha_composite(sp, (px - sp.width // 2, py - sp.height // 2))
        return px, py

    def climber_sprite(self, f, frame_idx=None):
        st = self.state[f]
        i = (f if frame_idx is None else frame_idx) % len(self.climb)
        if st["hurt"]:
            return self.fall
        if st["hits"]:
            sp = self.climbhat[HAT_HITS - st["hits"]][i].copy()
            if st["flash"]:                              # hat flashes white on an absorbed hit
                white = Image.new("RGBA", sp.size, self.colors["white"])
                sp.paste(white, (0, 0), self.hatmask[i].getchannel("A").point(lambda v: 255 if v > 127 else 0))
            return sp
        return self.climb[i]

    def good_sparkle(self, img, px, py, f):
        """Distinct power-up sparkle: big white + gold 4-point stars blinking around it."""
        w, g = self.colors["white"], self.colors["hardhat"]
        for k in range(2):
            a = (f * 0.7 + k * math.pi)
            sx, sy = px + round(13 * math.cos(a)), py + round(9 * math.sin(a))
            plus(img, sx, sy, w if (f + k) % 2 else g, r=2 if (f + k) % 3 else 1)

    def world(self, f, climber=True, at=None):
        """Compose the full-height level image at frame f (at = override climber (x, z))."""
        st = self.state[f]
        img = self.bg[self.mouth_open(f)].copy()
        if f < self.pick_f:                              # tangled hard hat waiting in the beard
            px, py = self._paste(img, self.hattangled, *self.tangled_pos)
            self.good_sparkle(img, px, py, f)
        if climber:
            sp = self.climber_sprite(f)
            cx, cz = at or (self.climber_x(f), self.climber_z(f))
            self._paste(img, sp, cx, cz + self.m["climber_center"])
        for (x, z, sp, kind) in self.items_at(f):
            px, py = self._paste(img, sp, x, z)
            if kind == "hat":
                self.good_sparkle(img, px, py, f)
            elif self.L.get("fx") == "sparkles":
                self._sparkles(img, px, py, f)
        if st["pop"] and 0 <= f - st["pop"][0] < 16:     # hat pops off and tumbles away
            k = f - st["pop"][0]
            x0, z0 = st["pop"][1], st["pop"][2]
            self._paste(img, self.hatitem[(k // 1) % 4], x0 + 0.13 * k, z0 + 0.32 * k - 0.04 * k * k)
        return img

    def _sparkles(self, img, px, py, seed):
        cols = [self.colors[r] for r in ("acc3", "white", "acc2")]
        for i in range(3):
            h = (seed * 31 + i * 17) % 97
            plus(img, px + (h % 40) - 20, py + ((h * 7) % 40) - 22, cols[i % 3])

    def frame(self, f, hud=True):
        """224x256 game frame: crop of the composed world + screen-space effects + HUD."""
        img = self.world(f)
        cb = self.cam_bottom(f)
        y0 = round((self.top - cb - self.vh) * self.ppu)
        fr = img.crop((0, y0, self.m["width"], y0 + self.m["height"]))
        self._screen_fx(fr, f, y0)
        if hud:
            self.hud(fr, f)
        return fr

    def _screen_fx(self, fr, f, y0):
        L, st = self.L, self.state[f]
        if L.get("fx") == "snow":
            rng = __import__("random").Random(5)
            for i in range(26):
                x0_, yy = rng.randrange(fr.width), rng.randrange(fr.height)
                plus(fr, (x0_ + int(2 * math.sin(f * 0.3 + i))) % fr.width, (yy + f * 2) % fr.height, self.colors["white"])
        if self.enemy and "enemy_path" in L:
            f0, f1 = L["enemy_path"]["frames"]
            if f0 <= f <= f1:
                t = (f - f0) / (f1 - f0)
                sp = self.enemy[(f // 2) % len(self.enemy)]
                x = round((1 - t) * (fr.width + 30) - 30) - sp.width // 2
                y = fr.height - round(L["enemy_path"]["z"] * self.ppu) - sp.height // 2
                fr.alpha_composite(sp, (x, y))
        # floating pixel-text cues (stand-ins for the sound effects)
        pops = {ef for ef, kd in self.events if kd == "pop"}
        for (ef, kind) in self.events:
            k = f - ef
            if kind == "clink" and ef in pops:
                continue                                # the 3rd hit just says POP!
            if 0 <= k < 7 and kind in ("pickup", "clink", "pop", "hurt"):
                word = {"pickup": "+HARD HAT", "clink": "CLINK!", "pop": "POP!", "hurt": "OUCH!"}[kind]
                cx, cz = self.climber_x(ef), self.climber_z(ef) + 2.45
                px, py = self.px(cx, cz)
                py -= y0 + 2 * k
                col = self.colors["hardhat"] if kind != "hurt" else self.colors["white"]
                draw_text(fr, (max(1, min(fr.width - text_width(word) - 2, px - text_width(word) // 2)), py), word, col)

    def hud(self, fr, f):
        """Top-left HUD: hard-hat pips (one per remaining hit). Blinks on a hit."""
        st = self.state[f]
        recent_pop = st["pop"] and f - st["pop"][0] < 8
        if st["hits"] is None and not recent_pop:
            return
        hits = st["hits"] or 0
        for yy in range(0, 14):                         # dark HUD panel
            for xx in range(0, 56):
                fr.putpixel((xx, yy), self.colors["black"])
        draw_text(fr, (3, 4), "HAT", self.colors["white"])
        for i in range(HAT_HITS):
            x, y = 24 + i * 11, 4
            full = i < hits and not (st["flash"] and i == hits and f % 2)
            hat_pip(fr, x, y, self.colors["hardhat"] if full else None,
                    self.colors["black"] if full else self.colors["white"])


def process_level(lid, a):
    lv = Level(lid, a)
    d, k = lv.dir, a.scale
    ev = {kind: [f for f, kk in lv.events if kk == kind] for kind in ("clink", "pop", "pickup", "spit_hat", "hurt")}
    shots = {"start": 0, "mid": SCROLL_FRAMES // 2, "top": SPIT_AT + 1}
    if ev["clink"]:
        shots["hardhat_hit"] = ev["clink"][0] + 1        # hazard bouncing off, hat flashing
    if ev["pop"]:
        shots["hardhat_pop"] = ev["pop"][0] + 2
    shots["hardhat_throw"] = HAT_THROW_AT + 4
    shots["hardhat_pickup"] = max(0, lv.pick_f - 3)
    frames = {}
    for name, f in shots.items():
        fr = lv.frame(f)
        frames[name] = fr
        fr.save(os.path.join(d, f"frame_{name}.png"))
        up(fr, k).save(os.path.join(d, f"frame_{name}_x{k}.png"))
    closed = next(f for f in range(SPIT_AT - 8, SPIT_AT) if not lv.mouth_open(f))
    pair = sheet([[lv.frame(closed, hud=False).crop((40, 0, 184, 150)),
                   lv.frame(SPIT_AT + 1, hud=False).crop((40, 0, 184, 150))]], pad=4, bg=(0, 0, 0, 255))
    up(pair, k).save(os.path.join(d, f"mouth_closed_open_x{k}.png"))
    # whole level strip: mouth open, items in flight, climber at his start
    strip = lv.world(SPIT_AT + 1, at=(lv.L["start_x"], lv.L["start_z"]))
    px, py = lv._paste(strip, lv.hattangled, *lv.tangled_pos)
    lv.good_sparkle(strip, px, py, 1)
    strip.save(os.path.join(d, "level_strip_1x.png"))
    up(strip, 2).save(os.path.join(d, "level_strip.png"))
    # scroll GIF (x2) + sound events
    seq = [lv.frame(f) for f in range(lv.total)]
    pal_frames = [up(fr, 2).convert("RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
                  for fr in seq]
    pal_frames[0].save(os.path.join(d, "scroll.gif"), save_all=True, append_images=pal_frames[1:],
                       duration=FRAME_MS, loop=0, optimize=True)
    json.dump({"frame_ms": FRAME_MS, "events": [{"frame": f, "t": f * FRAME_MS / 1000, "sfx": kind}
                                                 for f, kind in lv.events if 0 <= f < lv.total]},
              open(os.path.join(d, "sfx_events.json"), "w"), indent=1)
    if a.mp4:
        sfx.make_mp4(seq, lv.events, FRAME_MS, os.path.join(d, "scroll_sfx.mp4"), os.path.join(a.out, "sfx"))
    save2(sheet([[lv.q(t) for t in lv.m["tiles"]]], pad=2), os.path.join(d, "tiles.png"), k)
    rows = [r for r in lv.haz] + ([lv.enemy] if lv.enemy else [])
    haz = sheet(rows)
    save2(haz, os.path.join(d, "hazards.png"), k)
    bgc = hex_rgb(lv.L["palette"]["bg"]) + (255,)
    up(Image.alpha_composite(Image.new("RGBA", haz.size, bgc), haz), k).save(os.path.join(d, f"hazards_on_bg_x{k}.png"))
    # hard-hat sprite sheet for this level: item spins, tangled, climber per crack state, flash
    cells = [lv.hatitem + [lv.hattangled.resize((32, 32), Image.NEAREST)]]
    up(sheet(cells, pad=2), k).save(os.path.join(d, f"hardhat_items_x{k}.png"))
    lv_states = [[lv.climb[2]] + [lv.climbhat[c][2] for c in range(3)]]
    up(Image.alpha_composite(Image.new("RGBA", sheet(lv_states, pad=2).size, bgc), sheet(lv_states, pad=2)), k).save(
        os.path.join(d, f"hardhat_states_x{k}.png"))
    return {n: frames[n] for n in frames}, lv.m["title"], lv


def process_climber(a):
    raw = os.path.join(a.out, "climber", "raw")
    d = os.path.dirname(raw)
    pal = palette_rgb(CLIMBER_PALETTE)
    n = json.load(open(os.path.join(raw, "manifest.json")))["cycle"]
    spr = lambda name: (lambda im: im if a.no_outline else outline(im))(
        quantize(Image.open(os.path.join(raw, name + ".png")), pal, a.dither))
    frames = [spr(f"climb_{i:02d}") for i in range(n)]
    save2(sheet([frames]), os.path.join(d, "climber_sheet.png"), a.scale)
    save2(spr("fall"), os.path.join(d, "climber_fall.png"), a.scale)
    bg = hex_rgb(CLIMBER_PALETTE["bg"]) + (255,)
    gif = [up(Image.alpha_composite(Image.new("RGBA", f.size, bg), f), a.scale).convert("RGB") for f in frames]
    gif[0].save(os.path.join(d, "climber_cycle.gif"), save_all=True, append_images=gif[1:], duration=100, loop=0)


def overview(frames, path, scale=2):
    gap, label_h = 8, 44
    w, h = frames[0][0].width * scale, frames[0][0].height * scale
    out = Image.new("RGBA", (len(frames) * (w + gap) + gap, h + label_h + gap), (0, 0, 0, 255))
    for i, (fr, title) in enumerate(frames):
        x = gap + i * (w + gap)
        lab = pixel_text(title, 3, (248, 224, 64, 255), (0, 0, 0, 255))
        out.paste(lab, (x + (w - lab.width) // 2, 4))
        out.paste(up(fr, scale), (x, label_h))
    out.save(path)


def howto_screen(lv, path_base, k):
    """'HOW TO PLAY' attract screen (224x256), built from the real sprites."""
    W, H = 224, 256
    c = lv.colors
    img = Image.new("RGBA", (W, H), hex_rgb("#101030") + (255,))
    title = text_image("BEARD CLIMBER", c["hardhat"])
    img.alpha_composite(up(title, 2), ((W - title.width * 2) // 2, 8))
    head = "HOW TO PLAY"
    draw_text(img, ((W - text_width(head)) // 2, 30), head, c["white"])
    for x in range(20, W - 20):
        img.putpixel((x, 40), c["hardhat"] if x % 4 < 2 else c["black"])
    tx = 60
    def section(y, icon, lines, col=c["white"]):
        if icon is not None:
            img.alpha_composite(icon, (max(0, 30 - icon.width // 2), y + 10 - icon.height // 2))
        for i, line in enumerate(lines):
            draw_text(img, (tx, y + i * 10), line, col)
    section(50, lv.climb[2].crop((12, 6, 60, 66)).resize((32, 40), Image.NEAREST),
            ["CLIMB FROM THE TIP OF", "THE BEARD UP TO THE", "GIANT'S FACE."])
    haz = Image.new("RGBA", (54, 30), (0, 0, 0, 0))
    for i in range(min(3, len(lv.haz))):
        haz.alpha_composite(lv.haz[i][0].resize((24, 24), Image.NEAREST), (i * 15, 3))
    section(92, haz, ["DODGE WHAT HE SPITS OUT", "OF HIS MOUTH. IT FALLS", "DOWN THE BEARD."])
    hat = lv.hatitem[0].copy()
    section(134, hat, ["GRAB A HARD HAT! IT", "BLOCKS THE NEXT 3 HITS,", "THEN POPS OFF."], c["hardhat"])
    lv.good_sparkle(img, 30, 144, 2)
    for i in range(3):
        hat_pip(img, tx + 28 + i * 11, 165, c["hardhat"] if i < 2 else None, c["black"] if i < 2 else c["white"])
    draw_text(img, (tx, 165), "HUD:", c["white"])
    draw_text(img, (tx + 64, 166), "= HITS LEFT", c["white"])
    knot = lv.q(lv.m["tiles"][2]).resize((24, 24), Image.NEAREST)
    section(182, knot, ["GRIP KNOTS AND HOLDS.", "BALD PATCHES SLIP!"])
    draw_text(img, ((W - text_width("< > MOVE    ^ CLIMB")) // 2, 216), "< > MOVE    ^ CLIMB", c["white"])
    draw_text(img, ((W - text_width("PUSH START")) // 2, 236), "PUSH START", c["hardhat"])
    img.save(path_base + ".png")
    up(img, k).save(path_base + f"_x{k}.png")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    ap.add_argument("--levels", default=",".join(levels.ORDER))
    ap.add_argument("--dither", action="store_true", help="4x4 ordered Bayer dither (off by default)")
    ap.add_argument("--no-outline", action="store_true")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--no-mp4", dest="mp4", action="store_false", help="skip the MP4-with-sound previews")
    a = ap.parse_args()
    process_climber(a)
    res = [process_level(lid, a) for lid in a.levels.split(",")]
    overview([(r[0]["top"], r[1]) for r in res], os.path.join(a.out, "levels_overview.png"))
    overview([(r[0]["start"], r[1]) for r in res], os.path.join(a.out, "levels_start_overview.png"))
    overview([(r[0].get("hardhat_hit", r[0]["mid"]), r[1]) for r in res], os.path.join(a.out, "levels_hardhat_overview.png"))
    howto_screen(res[0][2], os.path.join(a.out, "howto"), a.scale)
    sfx.write_all(os.path.join(a.out, "sfx"))
    print("post-process done ->", a.out)


if __name__ == "__main__":
    main()
