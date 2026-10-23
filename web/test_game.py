"""web/test_game.py - headless Playwright test of web/index.html under iPhone 14 emulation.

  python3 web/test_game.py            (needs: pip install playwright; uses /usr/bin/google-chrome)

Drives the game with REAL touch events (CDP Input.dispatchTouchEvent: taps, double taps,
two-finger taps, long presses), reads state from the window.BC test hook, writes
screenshots to web/shots/ and a bot-played gameplay GIF to web/shots/gameplay.gif.
Exits non-zero if any check fails.
"""
import base64, io, json, os, subprocess, sys, time
from playwright.sync_api import sync_playwright
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "shots")
URL_FILE = "file://" + os.path.join(HERE, "index.html")
URL = URL_FILE + "?controls=two"     # the classic suites pin TWO HANDS (touch devices now default to ONE HAND)
URL_ONE = URL_FILE                   # no override: touch default (= ONE HAND) / saved setting
URL_W = URL_FILE + "?level=wizard&controls=two"        # the Wizard climb (World 3 boss); plain URL = World 1-1 Grandpa (tutorial)
os.makedirs(SHOTS, exist_ok=True)
results = []


def check(name, ok, info=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (f"  [{info}]" if info else ""), flush=True)


class Touch:
    """Real touch input through the Chrome DevTools protocol."""
    def __init__(self, page):
        self.pg, self.cdp = page, page.context.new_cdp_session(page)
        vp = page.viewport_size
        self.L, self.R, self.Y = vp["width"] * 0.22, vp["width"] * 0.78, vp["height"] * 0.6

    def start(self, pts): self.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": pts})
    def end(self): self.cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})

    def tap(self, side, hold_ms=40):
        self.start([{"x": self.L if side == "L" else self.R, "y": self.Y, "id": 1}])
        if hold_ms: self.pg.wait_for_timeout(hold_ms)
        self.end()

    def two_finger(self):
        self.start([{"x": self.L, "y": self.Y, "id": 1}, {"x": self.R, "y": self.Y, "id": 2}])
        self.pg.wait_for_timeout(50); self.end()

    def swipe(self, dx, dy, ms=120, x=None, y=None, steps=5):
        """One-finger swipe from (x, y) (default: screen centre) by (dx, dy) CSS px over ms."""
        x = self.pg.viewport_size["width"] / 2 if x is None else x; y = self.Y if y is None else y
        self.start([{"x": x, "y": y, "id": 1}])
        for i in range(1, steps + 1):
            self.pg.wait_for_timeout(ms / steps)
            self.cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x + dx * i / steps, "y": y + dy * i / steps, "id": 1}]})
        self.end()

    def press(self, side="L"): self.start([{"x": self.L if side == "L" else self.R, "y": self.Y, "id": 1}])


def ev(pg, js): return pg.evaluate(js)


def canvas_xy(pg, x, y):
    """Native canvas pixel (x, y) -> CSS page coordinates."""
    r = pg.evaluate("(() => { const r = document.getElementById('game').getBoundingClientRect(); return [r.left, r.top, r.width, r.height, document.getElementById('game').height]; })()")
    return r[0] + x / 224 * r[2], r[1] + y / r[4] * r[3]


def tap_rect(pg, t, rect):
    """Touch-tap the centre of a native-canvas rect {x, y, w, h}."""
    cx, cy = canvas_xy(pg, rect["x"] + rect["w"] / 2, rect["y"] + rect["h"] / 2)
    t.start([{"x": cx, "y": cy, "id": 1}]); pg.wait_for_timeout(40); t.end()


def count_color(pg, hexcol):
    """How many canvas pixels have exactly this colour (proves the creator look is drawn)."""
    return pg.evaluate("""(h) => { const c = document.getElementById('game'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
      const r = parseInt(h.slice(1, 3), 16), g = parseInt(h.slice(3, 5), 16), b = parseInt(h.slice(5, 7), 16); let n = 0;
      for (let i = 0; i < d.length; i += 4) if (d[i] === r && d[i + 1] === g && d[i + 2] === b) n++; return n; }""", hexcol)


def native_frame(pg, scale=2):
    uri = ev(pg, "BC.frame()")
    im = Image.open(io.BytesIO(base64.b64decode(uri.split(",")[1]))).convert("RGB")
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def shot(pg, name):
    pg.screenshot(path=os.path.join(SHOTS, name + ".png"))


def para_bot(pg, t, until=("para",)):
    """Steer toward the next coin until the parachute bonus is over."""
    while ev(pg, "BC.screen") in until:
        s = ev(pg, """(() => { if (BC.screen !== 'para') return null; const c = BC.S.cl, it = BC.Para.items.filter(i => !i.got && i.z < c.z + 1.5).sort((a, b) => b.z - a.z)[0];
            return [c.x, it ? it.x : c.x]; })()""")
        if s and abs(s[1] - s[0]) > 0.25: t.tap("R" if s[1] > s[0] else "L", 25)
        pg.wait_for_timeout(110)


def shop_open(pg, t, rect):
    tap_rect(pg, t, rect); pg.wait_for_timeout(450)


def shop_buy(pg, t, tab, row, yes=True, shot_name=None):
    """Real taps: tab, row (select), BUY, then YES/NO on the confirm."""
    L = ev(pg, "BC.shopLayout()")
    tap_rect(pg, t, L["tabs"][tab]); pg.wait_for_timeout(120)
    L = ev(pg, "BC.shopLayout()")
    tap_rect(pg, t, L["rows"][row]); pg.wait_for_timeout(120)
    tap_rect(pg, t, L["buy"] if tab == 4 else L["act"]); pg.wait_for_timeout(250)
    opened = ev(pg, "!!BC.Shop.confirm")
    if opened:
        if shot_name: shot(pg, shot_name)
        tap_rect(pg, t, L["yes"] if yes else L["no"]); pg.wait_for_timeout(250)
    return opened


def climb_frame_count(pg, hexcol, look=None):
    """Start a calm climb (optionally with a look) and count a colour on the canvas."""
    if look is not None: ev(pg, f"BC.setLook(Object.assign({{}}, BC.look, {look}))")
    ev(pg, "BC.start(); BC.calm(); BC.S.items.length = 0; BC.set({col: 2, x: 2.5, z: 3, arm: null})"); pg.wait_for_timeout(1900)  # after "GO!"
    return count_color(pg, hexcol)


def shop_tests(br, p, errors):
    """Coin shop: earning, buying, not-enough-coins, persistence, cosmetics in climb + parachute, boosts, Wizard set."""
    ctx = br.new_context(**p.devices["iPhone 14"])
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(URL_W); pg.wait_for_timeout(700)
    t = Touch(pg)
    cat = {c["id"]: c for c in ev(pg, "BC.CATALOG")}
    hat_opt = ev(pg, "BC.OPTS.findIndex(o => o.k === 'hat')")
    hats = ev(pg, "window.ASSETS.hats")
    crown_i, wiz_i = 1 + hats.index("crown"), 1 + hats.index("wizard")
    check("shop: new wallet starts at 0", ev(pg, "BC.wallet") == 0)
    # --- creator arrows are >= 44 CSS px on iPhone
    lay = ev(pg, "BC.creatorLayout()"); k = ev(pg, "BC.cssScale")
    aw, ah = lay["rows"][0]["L"]["w"] * k, lay["rows"][0]["L"]["h"] * k
    check("creator arrows >= 44x44 CSS px (iPhone 14)", aw >= 44 and ah >= 44, f"{aw:.0f}x{ah:.0f} css px")
    check("Wizard set locked before cheering him up", wiz_i not in ev(pg, f"BC.optValues(BC.OPTS[{hat_opt}])")
          and crown_i not in ev(pg, f"BC.optValues(BC.OPTS[{hat_opt}])"))
    # --- title SHOP, not enough coins
    shop_open(pg, t, ev(pg, "BC.TITLE_SHOP_BTN()"))
    check("title: SHOP opens the shop", ev(pg, "BC.screen") == "shop")
    opened = shop_buy(pg, t, 0, 2)            # crown, 300
    check("shop: not enough coins -> gentle message, nothing bought",
          not opened and ev(pg, "BC.wallet") == 0 and "crown" not in ev(pg, "BC.owned") and "NOT ENOUGH" in ev(pg, "BC.Shop.toast[0]"))
    shot(pg, "20_shop_not_enough_coins")
    L = ev(pg, "BC.shopLayout()"); tap_rect(pg, t, L["rows"][4]); pg.wait_for_timeout(300)   # trapper (Lumberjack set)
    shot(pg, "21_shop_locked_lumberjack_set")
    check("shop: giant sets show their lock reason", ev(pg, "BC.CATALOG.find(c => c.id === 'trapper').set") == "lumberjack")
    tap_rect(pg, t, L["back"]); pg.wait_for_timeout(400)
    check("shop: BACK returns to the title", ev(pg, "BC.screen") == "title")
    # --- earn coins with a real win (ending -> parachute -> bird -> results)
    ev(pg, "BC.start(); BC.S.pages = 3; BC.set({col: 2, x: 2.5, z: BC.GOAL_Z - 0.4}); BC.calm()"); pg.wait_for_timeout(300)
    ev(pg, "BC.win()"); pg.wait_for_timeout(700); t.tap("R"); pg.wait_for_timeout(1500)
    rainbow0 = count_color(pg, "#60d060")
    para_bot(pg, t)
    pg.wait_for_function("BC.screen === 'results'", timeout=8000); pg.wait_for_timeout(1400)
    r = ev(pg, "BC.S.result"); T = ev(pg, "BC.T")
    expect = r["coins"] * T["EARN_COIN"] + r["stars"] * T["EARN_STAR"] + 3 * T["EARN_PAGE"] + T["EARN_WIN"]
    check("earning: a win banks chute coins + stars + pages + bonus", r["earned"] == expect and ev(pg, "BC.wallet") == expect
          and ev(pg, "+localStorage.getItem('bc_coins')") == expect, f"earned {r['earned']} (coins {r['coins']} stars {r['stars']})")
    check("Wizard set unlocks after the win", "wizard" in ev(pg, "BC.cheered") and wiz_i in ev(pg, f"BC.optValues(BC.OPTS[{hat_opt}])"))
    shot(pg, "18_results_coins_wizard_set")
    earned = expect
    shop_open(pg, t, ev(pg, "BC.resultsLayout()")["shop"])
    check("results: SHOP opens the shop", ev(pg, "BC.screen") == "shop")
    L = ev(pg, "BC.shopLayout()"); tap_rect(pg, t, L["back"]); pg.wait_for_timeout(400)
    check("shop BACK -> results", ev(pg, "BC.screen") == "results")
    # --- ?debug=1&coins=N grants coins
    pg.goto(URL_W + "&debug=1&coins=500"); pg.wait_for_timeout(700); t = Touch(pg)
    check("?debug=1&coins=500 grants coins", ev(pg, "BC.wallet") == earned + 500, str(ev(pg, "BC.wallet")))
    w0 = ev(pg, "BC.wallet")
    shop_open(pg, t, ev(pg, "BC.TITLE_SHOP_BTN()"))
    L = ev(pg, "BC.shopLayout()"); tap_rect(pg, t, L["tabs"][0]); pg.wait_for_timeout(100); tap_rect(pg, t, L["rows"][2]); pg.wait_for_timeout(100)
    tap_rect(pg, t, L["act"]); pg.wait_for_timeout(250)
    shot(pg, "22_shop_purchase_confirm")
    tap_rect(pg, t, L["no"]); pg.wait_for_timeout(200)
    check("shop: NO on the confirm keeps the coins", ev(pg, "BC.wallet") == w0 and "crown" not in ev(pg, "BC.owned"))
    shop_buy(pg, t, 0, 2)
    check("shop: buying deducts coins, saves, and wears it", ev(pg, "BC.wallet") == w0 - cat["crown"]["price"] and "crown" in ev(pg, "BC.owned")
          and ev(pg, "BC.look.hat") == crown_i and "crown" in ev(pg, "localStorage.getItem('bc_owned')"), str(ev(pg, "BC.wallet")))
    pg.wait_for_timeout(500); shot(pg, "23_shop_hats_crown")
    # --- reload: everything persists
    pg.goto(URL_W); pg.wait_for_timeout(700); t = Touch(pg)       # plain reload (no coin grant)
    check("reload: wallet, purchases, look persist", ev(pg, "BC.wallet") == w0 - cat["crown"]["price"] and "crown" in ev(pg, "BC.owned")
          and ev(pg, "BC.look.hat") == crown_i and "wizard" in ev(pg, "BC.cheered"))
    check("creator HAT row now cycles the owned crown + Wizard hat", {crown_i, wiz_i} <= set(ev(pg, f"BC.optValues(BC.OPTS[{hat_opt}])")))
    # --- cosmetics render in the climb (pixel check: crown gold)
    GOLD = "#f8c830"
    n_beanie = climber = climb_frame_count(pg, GOLD, "{hat: 1, outfit: 0, gear: 2}")
    n_crown = climb_frame_count(pg, GOLD, f"{{hat: {crown_i}}}")
    shot(pg, "24_climb_wearing_crown")
    check("equipped crown renders in the climb (gold pixels)", n_crown > n_beanie + 15, f"{n_beanie} -> {n_crown} gold px")
    n_wiz = climb_frame_count(pg, "#7838c0", f"{{hat: {wiz_i}}}")
    check("Wizard hat renders in the climb (purple pixels)", n_wiz > 15, f"{n_wiz} purple px")
    # --- parachute pattern: buy RAINBOW and check it in the parachute bonus
    ev(pg, "BC.setLook(Object.assign({}, BC.look, {hat: %d}))" % crown_i)
    ev(pg, "BC.openShop('title')"); pg.wait_for_timeout(450)
    shop_buy(pg, t, 3, 4)
    check("shop: rainbow parachute bought + worn", "rainbow" in ev(pg, "BC.owned") and ev(pg, "BC.look.chute") == 1 + ev(pg, "window.ASSETS.chutes.indexOf('rainbow')"))
    pg.wait_for_timeout(500); shot(pg, "25_shop_chutes_rainbow")
    ev(pg, "BC.start(); BC.calm(); BC.win()"); pg.wait_for_timeout(700); t.tap("R"); pg.wait_for_timeout(2600)
    n_rb = count_color(pg, "#60d060")
    shot(pg, "26_parachute_rainbow")
    check("equipped parachute pattern renders in the bonus (rainbow pixels)", n_rb > rainbow0 + 30, f"{rainbow0} -> {n_rb} px")
    para_bot(pg, t, ("para", "bird")); pg.wait_for_timeout(1000)
    # --- boosts: buy, limits, applied + consumed
    ev(pg, "BC.openShop('title')"); pg.wait_for_timeout(450)
    shop_buy(pg, t, 4, 0)        # hard hat start
    shop_buy(pg, t, 4, 2)        # coin magnet
    shop_buy(pg, t, 4, 1)        # extra life (bought, but a 2nd helper can't be switched on)
    L = ev(pg, "BC.shopLayout()"); tap_rect(pg, t, L["use"]); pg.wait_for_timeout(200)
    check("boosts: max 2 per climb, only 1 helper", ev(pg, "BC.boostEq") == ["b_hardhat", "b_magnet"] and ev(pg, "BC.boosts.b_life") == 1
          and "ONE HELPER" in ev(pg, "BC.Shop.toast[0]"), str(ev(pg, "BC.boostEq")))
    tap_rect(pg, t, L["rows"][0]); pg.wait_for_timeout(500); shot(pg, "27_shop_boosts")
    tap_rect(pg, t, L["back"]); pg.wait_for_timeout(400)
    ev(pg, "BC.start()"); pg.wait_for_timeout(300)
    st = ev(pg, "[BC.S.hat, BC.S.boosts, BC.S.magnet, BC.boosts.b_hardhat, BC.boosts.b_magnet, BC.boostEq, BC.S.lives]")
    check("boost applied in the run: starting hard hat (2 hits) + magnet", st[0] == T["START_HAT_HITS"] and st[1] == ["b_hardhat", "b_magnet"] and st[2] and st[6] == 3, str(st))
    check("boosts consumed (inventory -1, switched off when empty)", st[3] == 0 and st[4] == 0 and st[5] == [], str(st))
    ev(pg, "BC.calm(); BC.set({col: 2, x: 2.5, z: 6, arm: null})"); pg.wait_for_timeout(1700); shot(pg, "28_hud_boosts")
    ev(pg, "BC.spawn(0, 2, BC.S.cl.z + 3)"); pg.wait_for_timeout(1200)
    check("starting hard hat absorbs a hit", ev(pg, "[BC.S.hat, BC.S.lives]") == [1, 3], str(ev(pg, "[BC.S.hat, BC.S.lives]")))
    ev(pg, "BC.win()"); pg.wait_for_timeout(700); t.tap("R"); pg.wait_for_timeout(600)
    ev(pg, "BC.Para.items.forEach(i => { if (i.kind === 'coin') { i.x = BC.S.cl.x + 1.2; } })"); pg.wait_for_timeout(2500)
    check("coin magnet pulls parachute coins", ev(pg, "BC.Para.items.some(i => i.pulled)") and ev(pg, "BC.Para.coins") > 0, str(ev(pg, "BC.Para.coins")))
    para_bot(pg, t, ("para", "bird")); pg.wait_for_timeout(500)
    ev(pg, "BC.start()")
    check("next run has no boost left", ev(pg, "[BC.S.hat, BC.S.boosts.length, BC.S.magnet]") == [0, 0, False])
    ev(pg, "BC.setBoosts({b_life: 1}, ['b_life']); BC.start()")
    check("extra life: 4 hearts, once", ev(pg, "[BC.S.lives, BC.S.maxLives, BC.boosts.b_life]") == [4, 4, 0])
    ev(pg, "BC.calm(); BC.set({col: 2, x: 2.5, z: 6, arm: null})"); pg.wait_for_timeout(300)
    # --- Pip wearing the new hats: try-on lineup from the shop preview (native pixels)
    ev(pg, "BC.openShop('title')"); pg.wait_for_timeout(450)
    L = ev(pg, "BC.shopLayout()"); tap_rect(pg, t, L["tabs"][0]); pg.wait_for_timeout(100)
    pv = L["preview"]; tiles = []
    for i in range(len(L["rows"])):
        ev(pg, f"BC.Shop.sel[0] = {i}"); pg.wait_for_timeout(250)
        im = native_frame(pg, 1).crop((pv["x"], pv["y"], pv["x"] + pv["w"], pv["y"] + pv["h"]))
        tiles.append(im)
    sheet = Image.new("RGB", (len(tiles) * pv["w"], pv["h"]))
    for i, im in enumerate(tiles): sheet.paste(im, (i * pv["w"], 0))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(os.path.join(SHOTS, "29_pip_new_hats.png"))
    for tab, name in ((1, "30_shop_outfits"), (2, "31_shop_packs")):
        tap_rect(pg, t, L["tabs"][tab]); pg.wait_for_timeout(120); tap_rect(pg, t, ev(pg, "BC.shopLayout()")["rows"][4 if tab == 1 else 3]); pg.wait_for_timeout(500); shot(pg, name)
    # --- creator SHOP link + cinematic only the first time ever
    pg.goto(URL_W); pg.wait_for_timeout(700); t = Touch(pg)
    t.tap("R"); pg.wait_for_timeout(400); t.tap("R"); pg.wait_for_timeout(450)
    shop_open(pg, t, ev(pg, "BC.creatorLayout()")["shop"])
    check("creator: SHOP link opens the shop", ev(pg, "BC.screen") == "shop")
    tap_rect(pg, t, ev(pg, "BC.shopLayout()")["back"]); pg.wait_for_timeout(400)
    check("shop BACK -> creator", ev(pg, "BC.screen") == "creator")
    shot(pg, "12c_creator_shop_button")
    tap_rect(pg, t, ev(pg, "BC.creatorLayout()")["start"]); pg.wait_for_timeout(300)
    first = ev(pg, "BC.screen")
    pg.goto(URL_W); pg.wait_for_timeout(700); t = Touch(pg)
    t.tap("R"); pg.wait_for_timeout(400); t.tap("R"); pg.wait_for_timeout(450)
    tap_rect(pg, t, ev(pg, "BC.creatorLayout()")["start"]); pg.wait_for_timeout(300)
    check("opening cinematic plays by itself only the first time ever", first == "cine" and ev(pg, "BC.screen") == "intro"
          and ev(pg, "localStorage.getItem('bc_cine')") == "1", f"{first} then {ev(pg, 'BC.screen')}")
    # --- longer beard + shelters
    T = ev(pg, "BC.T")
    climb = ev(pg, "BC.GOAL_Z - BC.START_Z")
    check("the climb is ~CLIMB_LENGTH x the original (22.75 units)", abs(climb / 22.75 - T["CLIMB_LENGTH"]) < 0.05, f"{climb:.2f} units = {climb / 22.75:.2f}x")
    ev(pg, "BC.start(); BC.calm()")
    pz = sorted(ev(pg, "BC.S.items.filter(i => i.kind === 'page').map(i => i.z)"))
    check("5 pages spread over the whole climb", len(pz) == 5 and pz[0] < climb * 0.3 and pz[-1] > climb * 0.75, str(pz))
    shs = ev(pg, "BC.S.shelters")
    check("2-3 shelters per climb, spread out", T["SHELTER_MIN"] <= len(shs) <= T["SHELTER_MAX"] and all(b["z"] - a["z"] > 4 for a, b in zip(shs, shs[1:])), str([s["z"] for s in shs]))
    sh = shs[0]
    ev(pg, f"BC.set({{col: {int(sh['x'])}, x: {sh['x']}, z: {sh['z']} - 1.0, arm: null}})"); pg.wait_for_timeout(1700)
    check("climbing into a shelter turns it on", ev(pg, "BC.S.shelters[0].state") == "on" and ev(pg, "BC.shelterNow"))
    ev(pg, f"BC.spawn(1, {int(sh['x'])}, BC.S.cl.z + 3)"); pg.wait_for_timeout(450); shot(pg, "32_shelter_boing")
    pg.wait_for_timeout(400)
    check("falling hazards bounce off Pip in a shelter", ev(pg, "[BC.S.lives, BC.S.shelterBlocks]") == [3, 1], str(ev(pg, "[BC.S.lives, BC.S.shelterBlocks]")))
    pg.wait_for_timeout(int(T["SHELTER_S"] * 1000))
    check("the shelter unravels after SHELTER_S and can't be reused", ev(pg, "[BC.S.shelters[0].state, BC.shelterNow]") == ["gone", False])
    ev(pg, f"BC.spawn(1, {int(sh['x'])}, BC.S.cl.z + 3)"); pg.wait_for_timeout(900)
    check("after it unravels hazards hit again", ev(pg, "BC.S.lives") == 2)
    pg.goto(URL_W + "&shelters=0"); pg.wait_for_timeout(600)
    ev(pg, "BC.start()")
    check("?shelters=0 turns shelters off", ev(pg, "BC.S.shelters.length") == 0)
    ctx.close()


REQUESTS = []          # every request that is not the local file or an embedded data: URI (must stay empty)


def watch_net(ctx):
    """Playwright request listener: the game must never touch the network."""
    ctx.on("request", lambda r: REQUESTS.append(r.url) if not r.url.startswith(("file://", "data:", "blob:")) else None)
    return ctx


BOT_JS = """(() => { const S = BC.S, c = S.cl, row = Math.floor(c.z + BC.T.STEP + BC.T.HAND);
  const A = window.ASSETS, bald = (col) => col < 0 || col > 5 || (A.tilemap[row] || [])[col] === 'sparse' || c.z < Math.max(BC.START_Z - 0.4, A.col_min_z[col] - 0.6);
  return {scr: BC.screen, mode: c.mode, col: c.col, z: c.z, baldUp: bald(c.col), okL: !bald(c.col - 1), okR: !bald(c.col + 1),
          tut: BC.tutStep, safe: BC.shelterNow}; })()"""


def tut_bot(pg, t, until_js, max_steps=80, keyboard=False, onehand=False):
    """Climb with real input (touch, or keyboard arrows) until until_js is true. Leaps round bald patches."""
    side = "L"
    def press(sd):
        if keyboard: pg.keyboard.press("ArrowLeft" if sd == "L" else "ArrowRight")
        else: t.tap(sd, 30)
    for _ in range(max_steps):
        if ev(pg, until_js): return True
        s = ev(pg, BOT_JS)
        if s["scr"] != "play": return ev(pg, until_js)
        if s["mode"] != "climb": pg.wait_for_timeout(120); continue
        if s["safe"] and s["tut"] == "shelter": pg.wait_for_timeout(150); continue      # sit in the tangle
        if s["tut"] == "down":                                                         # the climb-down lesson
            if keyboard: pg.keyboard.press("x")
            else: t.swipe(0, 90)
            pg.wait_for_timeout(300); continue
        if s["baldUp"] or s["tut"] == "dyno":
            d = "L" if s["okL"] and (not s["okR"] or s["col"] > 2) else "R"
            if onehand: t.swipe(-90 if d == "L" else 90, 0); side = "L"; pg.wait_for_timeout(380); continue
            press(d); pg.wait_for_timeout(70); press(d); side = "L"; pg.wait_for_timeout(380); continue
        if onehand: t.tap("L", 30); pg.wait_for_timeout(110); continue                # one hand: tap anywhere
        press(side); side = "R" if side == "L" else "L"
        pg.wait_for_timeout(110)
    return ev(pg, until_js)


def grandpa_tests(br, p, errors):
    """World 1-1 Grandpa: first-run flow, the tutorial (every prompt advances, can't be failed), story ending."""
    ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(800); t = Touch(pg)
    check("grandpa: World 1-1 Grandpa is the first level", ev(pg, "[BC.screen, BC.LEVEL, BC.isUnlocked('wizard')]") == ["title", "grandpa", False])
    lv = ev(pg, "[BC.ROWS, BC.T.TUTORIAL, BC.T.CLIMB_LENGTH, BC.GOAL_Z - BC.START_Z, window.ASSETS.hazard_names]")
    check("grandpa: his own short beard + tutorial tuning", lv[0] == 22 and lv[1] is True and lv[2] == 1 and 17 < lv[3] < 21
          and lv[4] == ["candy", "dentures", "yarn", "specs", "slipper"], str(lv))
    pg.wait_for_function("Math.floor(performance.now() / 1000 * 2.2) % 2 === 0"); shot(pg, "40_title_grandpa")
    t.tap("R"); pg.wait_for_timeout(400); t.tap("R"); pg.wait_for_timeout(450)
    tap_rect(pg, t, ev(pg, "BC.creatorLayout()")["start"]); pg.wait_for_timeout(300)
    check("grandpa: first START plays the cinematic", ev(pg, "BC.screen") == "cine")
    ev(pg, "BC.Cine.t = BC.T.CINE_PROLOGUE + 2.0"); pg.wait_for_timeout(200); shot(pg, "cinematic_1_grandpa")
    t.tap("R"); pg.wait_for_timeout(300)
    check("grandpa: skipping the cinematic -> Grandpa intro", ev(pg, "[BC.screen, BC.LEVEL]") == ["intro", "grandpa"])
    pg.wait_for_function("BC.Intro.t > 1.0"); shot(pg, "41_grandpa_intro")
    pg.wait_for_function("BC.Intro.t > 3.4"); shot(pg, "41b_grandpa_intro_take_the_phone")
    t.tap("L"); pg.wait_for_timeout(350)
    check("grandpa: tap -> climb, no cat (that's the Wizard's), no hazards yet",
          ev(pg, "[BC.screen, BC.S.catOn, BC.S.nextThrow > 1e8, BC.S.haz.length, BC.S.sneeze.next > 1e8]") == ["play", False, True, 0, True])
    pg.wait_for_timeout(1700)
    seen = [ev(pg, "BC.tutStep")]
    check("tutorial prompt 1: alternate L/R to climb", seen[0] == "climb")
    shot(pg, "42a_tutorial_climb_prompt")
    steps = [("dyno", "BC.tutStep === 'dyno'"), ("hat", "BC.tutStep === 'hat'"), ("photo", "BC.tutStep === 'photo'"),
             ("down", "BC.tutStep === 'down'"), ("shelter", "BC.tutStep === 'shelter'"), ("top", "BC.tutStep === 'top'")]
    for name, js in steps:
        ok = tut_bot(pg, t, js, 90)
        if name == "dyno":
            pg.wait_for_timeout(250); shot(pg, "42b_tutorial_dyno_prompt")
        if name == "hat":
            pg.wait_for_timeout(250); shot(pg, "42_mid_climb_tutorial_prompt")
        if name == "shelter":
            pg.wait_for_timeout(250); shot(pg, "42c_tutorial_shelter_prompt")
        check(f"tutorial prompt advances -> {name}", ok, str(ev(pg, "[BC.tutStep, BC.S.cl.z, BC.S.tut.steps]")))
    st = ev(pg, "[BC.S.hatsGot, BC.S.pages, BC.S.shelterBlocks, BC.S.tut.steps.map(s => s.step)]")
    check("tutorial: hat grabbed, photo collected, a hazard bounced off the shelter",
          st[0] >= 1 and st[1] >= 1 and st[2] >= 1 and st[3] == ["climb", "dyno", "hat", "photo", "down", "shelter"], str(st))
    # --- can't fail: a storm of hits never costs a heart or ends the climb
    ev(pg, "BC.S.nextThrow = 1e9; BC.S.haz.length = 0; BC.S.hat = 0; BC.set({col: 1, x: 1.5, z: 6, arm: null})")
    for i in range(30):
        ev(pg, "BC.S.cl.invulnUntil = 0; BC.S.hat = 0; BC.spawn(i % 5, BC.S.cl.col, BC.S.cl.z + 2.6)".replace("i % 5", str(i % 5)))
        pg.wait_for_timeout(260)
    pg.wait_for_timeout(600)
    r = ev(pg, "[BC.S.hitsTaken, BC.S.lives, !!BC.S.result, BC.screen, BC.S.cl.z >= BC.START_Z - 0.5]")
    check("tutorial is unfailable: 30 hits -> still 3 hearts, no game over", r[0] >= 20 and r[1] == 3 and r[2] is False and r[3] == "play" and r[4], str(r))
    ev(pg, "BC.set({col: 1, x: 1.5, z: 6, arm: null})"); pg.wait_for_timeout(200)
    z0 = ev(pg, "BC.S.cl.z"); ev(pg, "BC.S.cl.invulnUntil = 0; BC.spawn(0, BC.S.cl.col, BC.S.cl.z + 2.6)"); pg.wait_for_timeout(1100)
    check("tutorial hit = short knock-down only (KNOCK_HIT)", abs(z0 - ev(pg, "BC.S.cl.z") - ev(pg, "BC.T.KNOCK_HIT")) < 0.25, f"{z0:.2f} -> {ev(pg, 'BC.S.cl.z'):.2f}")
    # --- natural hazards are gentle
    pace = ev(pg, "[BC.T.THROW_SLOW, BC.T.THROW_FAST, BC.T.FALL_SLOW, BC.T.FALL_FAST, BC.T.UPPER_PAIR]")
    check("tutorial hazards slow + sparse (own T settings)", pace[0] >= 3.5 and pace[1] >= 2.4 and pace[3] <= 3.0 and pace[4] == 0, str(pace))
    # --- to the top: the phone, the grandkids, the beam
    ev(pg, "BC.S.nextThrow = 1e9; BC.S.haz.length = 0; BC.set({col: 2, x: 2.5, z: BC.GOAL_Z - 1.2, arm: null})"); pg.wait_for_timeout(300)
    tut_bot(pg, t, "BC.screen === 'ending'", 20)
    check("grandpa: reaching the top starts the ending", ev(pg, "BC.screen") == "ending")
    pg.wait_for_function("BC.Ending.t > 1.9"); shot(pg, "43_grandpa_top_phone_rings")
    pg.wait_for_function("BC.Ending.t > 4.0"); shot(pg, "44_grandpa_ending_beaming_wave")
    e = ev(pg, "[BC.face, BC.S.phoneIn, BC.S.waving, BC.S.asleep, BC.cheered.includes('grandpa'), BC.isUnlocked('goat'), BC.isUnlocked('wizard'), BC.S.unlocked]")
    check("grandpa ending: phone handed over, he beams + waves, the Goat (1-2) unlocks", e == ["sleep", True, True, False, True, True, False, "goat"], str(e))
    pg.wait_for_function("BC.screen === 'para'", timeout=6000); pg.wait_for_timeout(500)
    check("tutorial prompt: steer the parachute", ev(pg, "BC.tutStep") == "chute")
    z0 = ev(pg, "BC.S.cl.z"); pg.wait_for_timeout(1000); z1 = ev(pg, "BC.S.cl.z")
    shot(pg, "45a_tutorial_parachute_prompt")
    t.tap("R", 30); pg.wait_for_timeout(200)
    check("parachute waits (slow) until the first steer, then the lesson is done", 0 < z0 - z1 < 0.6 and ev(pg, "[BC.tutStep, BC.Para.steered]") == [None, True],
          f"sank {z0 - z1:.2f} in 1 s; {ev(pg, '[BC.tutStep, BC.Para.steered]')}")
    check("all 8 tutorial lessons done", ev(pg, "BC.S.tut.steps.map(s => s.step)") == ev(pg, "BC.TUT_STEPS"))
    para_bot(pg, t, ("para",))
    pg.wait_for_function("BC.screen === 'bird' && BC.Bird === undefined || BC.screen === 'bird'", timeout=8000); pg.wait_for_timeout(2000)
    shot(pg, "45_grandpa_bird_next_wizard")
    pg.wait_for_function("BC.screen === 'results'", timeout=6000); pg.wait_for_timeout(1400)
    shot(pg, "46_grandpa_results")
    check("grandpa results: photos counted, coins banked", ev(pg, "BC.S.result.pages >= 1 && BC.S.result.earned > 0"))
    rl = ev(pg, "BC.resultsLayout()")
    tap_rect(pg, t, rl["levels"]); pg.wait_for_timeout(400)
    check("results: LEVELS opens the world select", ev(pg, "BC.screen") == "levels")
    pg.wait_for_timeout(300); shot(pg, "47b_world_select_wizard_unlocked")
    tap_rect(pg, t, ev(pg, "BC.levelsLayout()")["back"]); pg.wait_for_timeout(400)
    check("world select BACK -> results", ev(pg, "BC.screen") == "results")
    tap_rect(pg, t, rl["play"]); pg.wait_for_timeout(400)
    check("results: NEXT: GOAT loads the Goat climb", ev(pg, "[BC.screen, BC.LEVEL, BC.ROWS, BC.T.TUTORIAL]") == ["intro", "goat", 24, False])
    ctx.close()


def world_select_tests(br, p, errors):
    ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(700); t = Touch(pg)
    tap_rect(pg, t, ev(pg, "BC.TITLE_LEVELS_BTN()")); pg.wait_for_timeout(450)
    check("title: LEVELS opens the world select", ev(pg, "BC.screen") == "levels")
    rows = ev(pg, "BC.levelsLayout().rows.map(r => [r.lv.id, r.lv.n])")
    states = ev(pg, "BC.levelsLayout().rows.map(r => window.BC.isUnlocked(r.lv.id))")
    check("world select: World 1 = Grandpa, Goat, Lumberjack, Mountain Man, Bigfoot; Wizard = World 3 boss",
          [r[0] for r in rows] == CHAIN
          and rows[-1][1] == "3-5" and rows[5][1] == "2-1" and rows[10][1] == "3-1", str(rows))
    check("world select: only Grandpa playable before cheering him up", states == [True] + [False] * 14, str(states))
    pg.wait_for_timeout(300); shot(pg, "47_world_select")
    L = ev(pg, "BC.levelsLayout()")
    tap_rect(pg, t, L["rows"][14]); pg.wait_for_timeout(300)
    check("locked Wizard: says CHEER UP THE DWARF KING TO UNLOCK", ev(pg, "BC.screen") == "levels" and "DWARF KING" in ev(pg, "BC.Levels.toast[0]"), str(ev(pg, "BC.Levels.toast[0]")))
    shot(pg, "47c_world_select_wizard_locked")
    tap_rect(pg, t, L["rows"][1]); pg.wait_for_timeout(300)
    check("locked Goat: says CHEER UP GRANDPA", "CHEER UP GRANDPA" in ev(pg, "BC.Levels.toast[0]"))
    tap_rect(pg, t, L["rows"][5]); pg.wait_for_timeout(300)
    check("locked World 2 Elf: says CHEER UP BIGFOOT", ev(pg, "BC.screen") == "levels" and "CHEER UP BIGFOOT" in ev(pg, "BC.Levels.toast[0]"))
    pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
    check("world select: Escape -> title", ev(pg, "BC.screen") == "title")
    # --- unlock flow: cheering Grandpa up opens the Goat (not the Wizard, for new players); the choice is remembered
    ev(pg, "localStorage.setItem('bc_cheered', JSON.stringify(['grandpa']))"); pg.goto(URL); pg.wait_for_timeout(700); t = Touch(pg)
    check("after Grandpa: Goat unlocked, Wizard still locked (new player)", ev(pg, "[BC.isUnlocked('goat'), BC.isUnlocked('lumberjack'), BC.isUnlocked('wizard')]") == [True, False, False])
    ev(pg, "BC.openLevels('title')"); pg.wait_for_timeout(450)
    tap_rect(pg, t, ev(pg, "BC.levelsLayout()")["rows"][1]); pg.wait_for_timeout(400)
    check("world select: tap the unlocked Goat -> Goat intro", ev(pg, "[BC.screen, BC.LEVEL]") == ["intro", "goat"])
    pg.goto(URL); pg.wait_for_timeout(700)
    check("last picked level is remembered", ev(pg, "BC.LEVEL") == "goat")
    ev(pg, "BC.openLevels('title')"); pg.wait_for_timeout(450)
    for _ in range(1): pg.keyboard.press("ArrowUp"); pg.wait_for_timeout(60)       # Goat -> row 0 (Grandpa)
    pg.wait_for_timeout(100); sel = ev(pg, "BC.Levels.sel")
    pg.keyboard.press("Enter"); pg.wait_for_timeout(400)
    check("world select: keyboard pick Grandpa", sel == 0 and ev(pg, "[BC.screen, BC.LEVEL]") == ["intro", "grandpa"], str(sel))
    ctx.close()


def layout_tests(br, p, errors):
    """Desktop + iPad letterbox: integer-scaled, centred portrait play area; themed side bars; keyboard + mouse."""
    cases = [("desktop 1280x720", {"viewport": {"width": 1280, "height": 720}}, None),
             ("desktop 1920x1080", {"viewport": {"width": 1920, "height": 1080}}, "48_desktop_1920x1080"),
             ("iPad portrait", dict(p.devices["iPad Pro 11"]), "49b_ipad_portrait"),
             ("iPad landscape", dict(p.devices["iPad Pro 11 landscape"]), "49_ipad_landscape")]
    for name, kw, shot_name in cases:
        ctx = watch_net(br.new_context(**kw))
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL); pg.wait_for_timeout(700)
        g = ev(pg, """(() => { const r = document.getElementById('game').getBoundingClientRect(), d = devicePixelRatio;
            return {l: r.left, t: r.top, w: r.width, h: r.height, vw: innerWidth, vh: innerHeight, d, k: BC.scale, H: BC.H,
                    bg: getComputedStyle(document.body).backgroundImage.slice(0, 15)}; })()""")
        kpx = g["w"] * g["d"] / 224
        centred = abs(g["l"] - (g["vw"] - g["w"]) / 2) <= 1 and abs(g["t"] - (g["vh"] - g["h"]) / 2) <= 1
        check(f"{name}: play area centred + integer scaled", centred and abs(kpx - round(kpx)) < 0.01 and round(kpx) == g["k"]
              and g["w"] <= g["vw"] and g["h"] <= g["vh"] + 0.5, f"k={g['k']} H={g['H']} canvas {g['w']:.0f}x{g['h']:.0f} at {g['l']:.0f},{g['t']:.0f} in {g['vw']}x{g['vh']}")
        check(f"{name}: fills the height (portrait, up to 420 native px)", g["h"] * g["d"] >= min(420 * g["k"], g["vh"] * g["d"]) - g["k"], f"H {g['H']}")
        # keyboard: Enter through the menus, arrows climb, double press = dyno (the tutorial advances)
        for _ in range(5):
            if ev(pg, "BC.screen") == "play": break
            pg.keyboard.press("Enter"); pg.wait_for_timeout(450)
        ok = ev(pg, "BC.screen") == "play"
        pg.wait_for_timeout(1200)
        if ok: ok = tut_bot(pg, None, "BC.tutStep === 'hat'", 60, keyboard=True)
        check(f"{name}: keyboard plays (Enter, arrows, double press) - tutorial reaches the hat lesson", ok, str(ev(pg, "[BC.screen, BC.tutStep]")))
        if g["w"] < g["vw"] - 20:                       # side bars: themed pixel pattern, not flat black
            pg.screenshot(path="/tmp/_side.png"); im = Image.open("/tmp/_side.png").convert("RGB")
            sw = int((g["l"] - 2) * g["d"]); strip = im.crop((0, 0, max(1, sw), im.height))
            cols = strip.getcolors(1 << 16) or []
            dark = all(c[1] == (0, 0, 0) for c in cols)
            check(f"{name}: side bars are a themed pattern (not plain black)", g["bg"].startswith("url(") and len(cols) >= 3 and not dark, f"{len(cols)} colours")
        if shot_name: pg.wait_for_timeout(300); shot(pg, shot_name)
        ctx.close()
    # --- clicks on every menu button (desktop) + window resizing
    ctx = watch_net(br.new_context(viewport={"width": 1280, "height": 720}))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(700)
    def click(rect):
        x, y = canvas_xy(pg, rect["x"] + rect["w"] / 2, rect["y"] + rect["h"] / 2); pg.mouse.click(x, y); pg.wait_for_timeout(450)
    click(ev(pg, "BC.TITLE_LEVELS_BTN()")); a = ev(pg, "BC.screen")
    click(ev(pg, "BC.levelsLayout().back")); b = ev(pg, "BC.screen")
    click(ev(pg, "BC.TITLE_SHOP_BTN()")); c = ev(pg, "BC.screen")
    click(ev(pg, "BC.shopLayout().back")); d = ev(pg, "BC.screen")
    click(ev(pg, "BC.TITLE_INTRO_BTN()")); e = ev(pg, "BC.screen")
    pg.mouse.click(640, 360); pg.wait_for_timeout(450); f = ev(pg, "BC.screen")
    check("mouse clicks work for the menu buttons", [a, b, c, d, e, f] == ["levels", "title", "shop", "title", "cine", "title"], str([a, b, c, d, e, f]))
    pg.mouse.click(640, 360); pg.wait_for_timeout(450); pg.mouse.click(640, 360); pg.wait_for_timeout(450)
    click(ev(pg, "BC.creatorLayout().start")); g1 = ev(pg, "BC.screen")
    check("mouse: how-to -> creator START", g1 in ("cine", "intro"), g1)
    for vw, vh in ((1000, 700), (700, 1000), (1600, 600)):
        pg.set_viewport_size({"width": vw, "height": vh}); pg.wait_for_timeout(400)
        r = ev(pg, "(() => { const r = document.getElementById('game').getBoundingClientRect(); return [r.left, r.top, r.width, r.height, BC.scale, BC.H]; })()")
        ok = abs(r[0] - (vw - r[2]) / 2) <= 1 and abs(r[1] - (vh - r[3]) / 2) <= 1 and r[2] <= vw and r[3] <= vh and abs(r[2] / 224 - r[4]) < 0.01
        check(f"window resize {vw}x{vh}: re-centred + re-scaled", ok, str(r))
    ctx.close()


def onehand_tests(br, p, errors):
    """ONE HAND controls + the Settings screen (touch default, saved), swipes, climb down, per-mode tutorial text."""
    ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(URL_ONE); pg.wait_for_timeout(800); t = Touch(pg)
    check("one-hand: touch devices default to ONE HAND", ev(pg, "BC.controls") == "one")
    tap_rect(pg, t, ev(pg, "BC.TITLE_GEAR_BTN()")); pg.wait_for_timeout(400)
    check("settings: title gear opens Settings", ev(pg, "BC.screen") == "settings")
    shot(pg, "50_settings_one_hand")
    L = ev(pg, "BC.settingsLayout()")
    tap_rect(pg, t, L["controls"]); pg.wait_for_timeout(250)
    check("settings: CONTROLS toggles to TWO HANDS", ev(pg, "[BC.controls, localStorage.getItem('bc_controls')]") == ["two", "two"])
    shot(pg, "50b_settings_two_hands")
    m0 = ev(pg, "BC.Snd.muted"); tap_rect(pg, t, L["sound"]); pg.wait_for_timeout(250)
    check("settings: SOUND toggle (saved)", ev(pg, "[BC.Snd.muted, localStorage.getItem('bc_mute')]") == [not m0, "1" if not m0 else "0"])
    tap_rect(pg, t, L["sound"]); pg.wait_for_timeout(250)
    pg.reload(); pg.wait_for_timeout(800); t = Touch(pg)
    check("settings: controls choice survives a reload", ev(pg, "BC.controls") == "two")
    howto2 = ev(pg, "BC.tutText('climb')[0][0]")
    check("tutorial text (two hands): TAP LEFT, RIGHT", howto2.startswith("TAP LEFT"), howto2)
    ev(pg, "BC.openSettings('title')"); pg.wait_for_timeout(400)
    tap_rect(pg, t, ev(pg, "BC.settingsLayout()")["controls"]); pg.wait_for_timeout(200)
    tap_rect(pg, t, ev(pg, "BC.settingsLayout()")["back"]); pg.wait_for_timeout(400)
    check("settings: BACK -> title, ONE HAND again", ev(pg, "[BC.screen, BC.controls]") == ["title", "one"])
    txt = ev(pg, "['climb', 'dyno', 'down', 'chute'].map(s => BC.tutText(s)[0].join(' '))")
    check("tutorial text (one hand): TAP TO CLIMB / SWIPE TO HOP / SWIPE DOWN / SWIPE OR HOLD",
          txt[0] == "TAP TO CLIMB!" and "SWIPE TO HOP" in txt[1] and txt[2] == "SWIPE DOWN TO CLIMB DOWN" and txt[3].startswith("SWIPE OR HOLD"), str(txt))
    t.tap("R"); pg.wait_for_timeout(450); shot(pg, "50c_howto_one_hand")
    # --- the Grandpa tutorial in ONE HAND mode: tap anywhere, swipe to hop, swipe down
    ev(pg, "BC.loadLevel('grandpa'); BC.start()"); pg.wait_for_timeout(1500)
    check("one-hand tutorial: first prompt", ev(pg, "BC.tutStep") == "climb")
    for name in ("dyno", "hat", "photo", "down", "shelter"):
        ok = tut_bot(pg, t, f"BC.tutStep === '{name}'", 90, onehand=True)
        if name == "dyno": pg.wait_for_timeout(250); shot(pg, "51_one_hand_tutorial_swipe_to_hop")
        if name == "down": pg.wait_for_timeout(250); shot(pg, "51b_one_hand_tutorial_swipe_down")
        check(f"one-hand tutorial advances -> {name}", ok, str(ev(pg, "[BC.tutStep, BC.S.cl.z]")))
    # --- mechanics on a calm Wizard beard
    ev(pg, "BC.loadLevel('wizard'); BC.start(); BC.S.nextThrow = 1e9; BC.S.sneeze.next = 1e9")
    calm = "BC.S.haz.length = 0; BC.S.nextThrow = 1e9; BC.S.sneeze.next = 1e9; BC.S.cl.invulnUntil = 1e9"
    def put(col, z): ev(pg, f"{calm}; BC.set({{col: {col}, x: {col} + 0.5, z: {z}, arm: null, mode: 'climb', tw: null}})"); pg.wait_for_timeout(150)
    def safe_col():
        return ev(pg, "(() => { for (let z = 8; z < 20; z += 0.5) for (const c of [2, 3]) { let ok = true; for (let r = Math.floor(z) - 2; r <= Math.floor(z) + 4; r++) for (const cc of [c - 1, c, c + 1]) if (BC.tileAt(cc, r) === 'sparse') ok = false; if (ok) return [c, z]; } return [2, 10]; })()")
    c0, z0 = safe_col(); put(c0, z0)
    arms = []
    for i in range(6):
        t.tap("L", 30); pg.wait_for_timeout(140); arms.append(ev(pg, "BC.S.cl.arm"))
    z1 = ev(pg, "BC.S.cl.z")
    check("one-hand: taps on the SAME spot alternate arms and climb", arms == ["L", "R"] * 3 and abs(z1 - z0 - 6 * ev(pg, "BC.T.STEP")) < 0.05, f"{arms} dz={z1 - z0:.2f}")
    put(c0, z0); sc = ev(pg, "[BC.S.cl.arm, BC.S.score, BC.S.maxZ]")
    t.swipe(90, 0); pg.wait_for_timeout(450)
    r = ev(pg, "[BC.S.cl.col, BC.S.cl.z, BC.lastSwipe && BC.lastSwipe.d]")
    check("one-hand: swipe right = hop one column", r[0] == c0 + 1 and r[2] == "R", str(r))
    check("one-hand: a swipe is NOT also a tap (no climb, score unchanged)", abs(r[1] - z0) < 0.01 and ev(pg, "BC.S.score") == sc[1], f"z {z0} -> {r[1]}")
    t.swipe(-90, 0); pg.wait_for_timeout(450)
    check("one-hand: swipe left = hop back", ev(pg, "BC.S.cl.col") == c0 and abs(ev(pg, "BC.S.cl.z") - z0) < 0.01)
    put(c0, z0)
    t.swipe(0, 100); pg.wait_for_timeout(90); shot(pg, "52_swipe_down_climbing_down"); pg.wait_for_timeout(300)
    zd = ev(pg, "BC.S.cl.z")
    check("one-hand: swipe down climbs DOWN one notch", abs(z0 - zd - ev(pg, "BC.T.DOWN_STEP")) < 0.05, f"{z0} -> {zd}")
    put(c0, z0); t.swipe(0, -100); pg.wait_for_timeout(400)
    check("one-hand: swipe up = quick double reach", abs(ev(pg, "BC.S.cl.z") - z0 - 2 * ev(pg, "BC.T.STEP")) < 0.05, str(ev(pg, "BC.S.cl.z") - z0))
    put(c0, z0); t.swipe(12, 8, 80); pg.wait_for_timeout(250)
    check("one-hand: a tiny wobble stays a tap", abs(ev(pg, "BC.S.cl.z") - z0 - ev(pg, "BC.T.STEP")) < 0.05 and ev(pg, "BC.S.cl.col") == c0)
    put(c0, z0); t.swipe(90, 0, 1200, steps=8); pg.wait_for_timeout(250)
    check("one-hand: a slow drag (> SWIPE_MAX_MS) is no swipe", ev(pg, "BC.S.cl.col") == c0)
    put(c0, z0); t.press("R"); pg.wait_for_timeout(450)
    check("one-hand: press + hold anywhere = hold tight", ev(pg, "BC.S.cl.hold") is True); t.end(); pg.wait_for_timeout(100)
    check("one-hand: release = let go", ev(pg, "BC.S.cl.hold") is False)
    put(c0, z0); t.two_finger(); pg.wait_for_timeout(100)
    check("one-hand: two-finger tap still braces", ev(pg, "BC.S.cl.braceUntil > BC.S.t"))
    # --- two hands: unchanged, plus swipe down
    ev(pg, "BC.setControls('two')"); put(c0, z0)
    t.tap("L", 30); pg.wait_for_timeout(140); t.tap("L", 30); pg.wait_for_timeout(450)
    check("two-hand: same side twice = dyno (unchanged)", ev(pg, "BC.S.cl.col") == c0 - 1, str(ev(pg, "BC.S.cl.col")))
    put(c0, z0); t.tap("L", 30); pg.wait_for_timeout(140); t.tap("R", 30); pg.wait_for_timeout(140)
    check("two-hand: L then R climbs two steps (unchanged)", abs(ev(pg, "BC.S.cl.z") - z0 - 2 * ev(pg, "BC.T.STEP")) < 0.05)
    put(c0, z0); t.swipe(90, 0); pg.wait_for_timeout(400)
    check("two-hand: a sideways swipe is no hop (still a tap)", ev(pg, "BC.S.cl.col") == c0)
    put(c0, z0); t.swipe(0, 100); pg.wait_for_timeout(400)
    check("two-hand: swipe down climbs down too", abs(z0 - ev(pg, "BC.S.cl.z") - ev(pg, "BC.T.DOWN_STEP")) < 0.05)
    put(c0, z0); pg.keyboard.press("x"); pg.wait_for_timeout(400)
    check("keyboard: X climbs down", abs(z0 - ev(pg, "BC.S.cl.z") - ev(pg, "BC.T.DOWN_STEP")) < 0.05)
    put(c0, 0.6); t.swipe(0, 100); pg.wait_for_timeout(300)
    check("climb down stops at the bottom of the beard", ev(pg, "BC.S.cl.z") >= min(0.6, ev(pg, "BC.START_Z")) - 0.01)
    ctx.close()


def choose_tests(br, p, errors):
    """First launch on touch: HOW DO YOU WANT TO PLAY? (once), choice saved + applied; desktop skips it."""
    for pick in ("one", "two"):
        ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL_ONE); pg.wait_for_timeout(800); t = Touch(pg)
        t.tap("R"); pg.wait_for_timeout(450)
        check(f"choose[{pick}]: first launch shows HOW DO YOU WANT TO PLAY?", ev(pg, "BC.screen") == "choose")
        if pick == "one": shot(pg, "53_choose_controls")
        tap_rect(pg, t, ev(pg, "BC.chooseLayout()")[pick]); pg.wait_for_timeout(450)
        want = "TAP TO CLIMB!" if pick == "one" else "TAP LEFT, RIGHT,"
        check(f"choose[{pick}]: saved + applied, then the how-to", ev(pg, "[BC.screen, BC.controls, localStorage.getItem('bc_controls'), BC.tutText('climb')[0][0]]") == ["howto", pick, pick, want])
        pg.reload(); pg.wait_for_timeout(800); t = Touch(pg)
        t.tap("R"); pg.wait_for_timeout(450)
        check(f"choose[{pick}]: never shown again after reload", ev(pg, "[BC.screen, BC.controls]") == ["howto", pick])
        ctx.close()
    ctx = br.new_context(viewport={"width": 1280, "height": 800}); pg = ctx.new_page(); pg.goto(URL_ONE); pg.wait_for_timeout(700)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(450)
    check("choose: desktop (no touch) skips it", ev(pg, "BC.screen") == "howto"); ctx.close()
    ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page(); pg.goto(URL_FILE + "?controls=one"); pg.wait_for_timeout(700)
    Touch(pg).tap("R"); pg.wait_for_timeout(450)
    check("choose: ?controls= skips it", ev(pg, "BC.screen") == "howto"); ctx.close()


W1 = [("goat", "lumberjack", ["goathorns", "bandana"]), ("lumberjack", "mountain", ["trapper", "plaid"]),
      ("mountain", "bigfoot", ["coonskin", "buckskin"]), ("bigfoot", "elf", ["furhood", "furcoat"])]
W2 = [("elf", "rudolph", ["elfhat", "tunic"]), ("rudolph", "ice", ["antlers", "jumper"]), ("ice", "yeti", ["icecrown", "frostcape"]),
      ("yeti", "santa", ["earmuffs", "scarf"]), ("santa", "gnome", ["santa", "suit"])]
W3 = [("gnome", "rumpel", ["gnomehat", "gnomevest"]), ("rumpel", "rapunzel", ["featherhat", "goldvest"]),
      ("rapunzel", "dwarf", ["tiara", "gown"]), ("dwarf", "wizard", ["dwarfhelm", "chainmail"])]
CHAIN = ["grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa",
         "gnome", "rumpel", "rapunzel", "dwarf", "wizard"]


def world1_tests(br, p, errors):
    world_tests(br, p, errors, W1, 6, "63_world_select_world1", "mountain")
    world_events(br, p, errors, (("mountain", "gust"), ("bigfoot", "stomp")))
    # --- old saves keep the Wizard; new players must beat Santa now
    ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page()
    pg.goto(URL); ev(pg, "localStorage.clear(); localStorage.setItem('bc_cheered', JSON.stringify(['grandpa']))")
    pg.goto(URL); pg.wait_for_timeout(600)
    check("old save (Grandpa cheered before World 1 grew): Wizard stays open", ev(pg, "[BC.isUnlocked('wizard'), BC.isUnlocked('goat')]") == [True, True])
    ctx.close()


def world2_tests(br, p, errors):
    """World 2 North Pole: Elf, Rudolph, Ice Giant, Yeti, Santa (boss) + their mechanics."""
    world_tests(br, p, errors, W2, 7, "73_world_select_world2", "ice")
    world_events(br, p, errors, (("rudolph", "hoof"), ("yeti", "roar"), ("santa", "laugh")))
    ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    # Santa: every other event is a reindeer swoop that drops presents (dodge, no hold)
    pg.goto(URL + "&level=santa"); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(600)
    ev(pg, "BC.start(); BC.calm(); BC.S.cl.invulnUntil = 1e9; BC.set({col: 2, x: 2.5, z: 9, arm: null})"); pg.wait_for_timeout(1700)
    ev(pg, "BC.S.sneeze.n = 1; BC.S.sneeze.next = BC.S.t"); pg.wait_for_timeout(int(1000 * ev(pg, "BC.T.SNEEZE_WARN")) - 400)
    shot(pg, "76_santa_swoop_warning")
    pg.wait_for_timeout(1000); shot(pg, "76b_santa_reindeer_swoop")
    r = ev(pg, "[!!BC.swoop, BC.S.haz.length, BC.S.eventsLost || 0, BC.S.sneeze.swoop]")
    check("santa: reindeer swoop flies by and drops presents (no hold needed)", r[0] and r[1] >= 2 and r[2] == 0 and r[3] is True, str(r))
    # Ice Giant: slippery (slides down without climbing), melting timer ends the climb
    pg.goto(URL + "&level=ice"); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(600)
    ev(pg, "BC.start(); BC.calm(); BC.S.cl.invulnUntil = 1e9; BC.set({col: 2, x: 2.5, z: 9, arm: null})"); pg.wait_for_timeout(2200)
    z = ev(pg, "BC.S.cl.z")
    check("ice: Pip slowly slides down when not climbing", 7.6 < z < 8.9, f"z {z:.2f}")
    shot(pg, "77_ice_sliding_melt_timer")
    t = Touch(pg); t.press("R"); pg.wait_for_timeout(1200); z2 = ev(pg, "BC.S.cl.z"); t.end()
    check("ice: holding tight slows the slide", z - z2 < 0.25, f"{z:.2f} -> {z2:.2f}")
    ev(pg, "BC.S.t = BC.T.MELT_S - 0.2"); pg.wait_for_timeout(1300)
    r = ev(pg, "[!!BC.S.melted, BC.S.result && BC.S.result.won]")
    check("ice: the melt timer runs out -> IT MELTED (lost)", r == [True, False], str(r))
    shot(pg, "77b_ice_melted")
    # Rudolph: dark stretches of mane (only a light round Pip)
    pg.goto(URL + "&level=rudolph"); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(600)
    ev(pg, "BC.start(); BC.calm(); BC.S.cl.invulnUntil = 1e9")
    zd = ev(pg, "BC.START_Z + 0.4 * (BC.GOAL_Z - BC.START_Z)")
    ev(pg, f"BC.set({{col: 2, x: 2.5, z: {zd}, arm: null}})"); pg.wait_for_timeout(1800)
    check("rudolph: dark stretch of mane", ev(pg, "BC.darkness()") > 0.9, str(ev(pg, "BC.darkness()")))
    shot(pg, "78_rudolph_dark_stretch")
    ctx.close()
    # --- saves: Bigfoot cheered before World 2 existed keeps the Wizard; new players must beat Santa
    ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page()
    pg.goto(URL); ev(pg, "localStorage.clear(); localStorage.setItem('bc_w1', '1'); localStorage.setItem('bc_cheered', JSON.stringify(['grandpa','goat','lumberjack','mountain','bigfoot']))")
    pg.goto(URL); pg.wait_for_timeout(600)
    check("old save (Bigfoot cheered before World 2): Wizard stays open, Elf open", ev(pg, "[BC.isUnlocked('wizard'), BC.isUnlocked('elf')]") == [True, True])
    ev(pg, "localStorage.clear()"); pg.goto(URL); pg.wait_for_timeout(500)
    ev(pg, "localStorage.setItem('bc_cheered', JSON.stringify(['grandpa','goat','lumberjack','mountain','bigfoot']))"); pg.goto(URL); pg.wait_for_timeout(600)
    check("new player after Bigfoot: Elf open, Wizard locked until Santa", ev(pg, "[BC.isUnlocked('elf'), BC.isUnlocked('wizard'), BC.isUnlocked('santa')]") == [True, False, False])
    ctx.close()


def world3_tests(br, p, errors):
    """World 3 Fairy-Tale Forest: Gnome, Rumpelstiltskin, Rapunzel, Dwarf King (+ the Wizard boss) and their mechanics."""
    world_tests(br, p, errors, W3, 8, "83_world_select_world3", "rapunzel")
    ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    def go(lv):
        pg.goto(URL + "&level=" + lv); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(600)
        ev(pg, "BC.start(); BC.calm(); BC.S.cl.invulnUntil = 1e9")
    # Gnome: lucky mushroom bounces Pip up ~2.5 rows
    go("gnome")
    m = ev(pg, "(() => { const m = BC.S.items.find(i => i.kind === 'mush'); return m && [m.x, m.z]; })()")
    check("gnome: lucky mushrooms grow in the beard", m is not None, str(m))
    if m:
        ev(pg, f"BC.set({{col: {int(m[0])}, x: {m[0]}, z: {m[1]} - BC.T.HAND - 1.2, arm: null}})"); pg.wait_for_timeout(250)
        shot(pg, "84_gnome_lucky_mushroom")
        z0 = ev(pg, "BC.S.cl.z"); ev(pg, f"BC.set({{z: {m[1]} - BC.T.HAND}})"); pg.wait_for_timeout(250); shot(pg, "84b_gnome_mushroom_boing")
        pg.wait_for_timeout(500); z1 = ev(pg, "BC.S.cl.z")
        check("gnome: touching a mushroom = BOING! up the beard", ev(pg, "BC.S.mushes") == 1 and z1 - (m[1] - ev(pg, "BC.T.HAND")) > 2.0, f"{z0:.2f} -> {z1:.2f}")
    # Rumpelstiltskin: falling straw spins into gold; catching it pays coins (not a hit)
    go("rumpel")
    ev(pg, "BC.set({col: 2, x: 2.5, z: 9, arm: null}); BC.T.GOLD_CHANCE = 1; BC.spawnHazard(2, 15, 0, true)")
    pg.wait_for_function("BC.S.haz.some(h => h.gold)", timeout=4000); shot(pg, "85_rumpel_straw_to_gold")
    pg.wait_for_timeout(2200)
    r = ev(pg, "[BC.S.goldGot || 0, BC.S.lives, BC.S.hitsTaken || 0]")
    check("rumpel: straw spun into gold -> caught for coins, no hit", r == [1, 3, 0], str(r))
    # Rapunzel: narrow braid - the tower wall fills the outer columns, nothing falls there
    go("rapunzel")
    ev(pg, "BC.set({col: 2, x: 2.5, z: 12, arm: null}); BC.S.cl.invulnUntil = 1e9; BC.S.nextThrow = BC.S.t")
    cols = set()
    for _ in range(10):
        ev(pg, "BC.S.nextThrow = Math.min(BC.S.nextThrow, BC.S.t + 0.3)"); pg.wait_for_timeout(350)
        cols |= set(ev(pg, "BC.S.haz.map(h => Math.floor(h.tx))"))
    tm = ev(pg, "window.ASSETS.tilemap.every(r => r[0] === 'sparse' && r[5] === 'sparse')")
    check("rapunzel: tower wall on the outer columns, hazards only down the braid", tm and cols and cols <= {1, 2, 3, 4}, str(sorted(cols)))
    shot(pg, "86_rapunzel_tower_braid")
    # Dwarf King: rockfall - columns marked, then fast boulders (dodge; holding doesn't help)
    go("dwarf")
    ev(pg, "BC.set({col: 2, x: 2.5, z: 9, arm: null}); BC.S.sneeze.next = BC.S.t"); pg.wait_for_timeout(int(1000 * ev(pg, "BC.T.SNEEZE_WARN")) - 500)
    cs = ev(pg, "BC.S.sneeze.cols")
    shot(pg, "87_dwarf_rockfall_warning")
    safe = [c for c in range(1, 5) if c not in cs][0]
    ev(pg, f"BC.S.cl.invulnUntil = 0; BC.set({{col: {safe}, x: {safe} + 0.5}})"); pg.wait_for_timeout(900)
    shot(pg, "87b_dwarf_rockfall")
    r = ev(pg, "[BC.S.haz.filter(h => h.fast).length, BC.S.eventsLost || 0]")
    pg.wait_for_timeout(1800)
    check("dwarf: rockfall marks 2 columns, fast boulders fall there, dodging = safe", len(cs) == 2 and r[0] >= 2 and r[1] == 0 and ev(pg, "BC.S.lives") == 3, f"{cs} {r}")
    # the Wizard is World 3's boss now
    pg.goto(URL); ev(pg, "localStorage.clear(); localStorage.setItem('bc_w1','1'); localStorage.setItem('bc_w2','1'); localStorage.setItem('bc_cheered', JSON.stringify(" + json.dumps(CHAIN[:10]) + "))")
    pg.goto(URL); pg.wait_for_timeout(600)
    check("old save (Santa cheered before World 3): Wizard stays open, Gnome open", ev(pg, "[BC.isUnlocked('wizard'), BC.isUnlocked('gnome'), BC.isUnlocked('rumpel')]") == [True, True, False])
    ev(pg, "localStorage.clear()"); pg.goto(URL); pg.wait_for_timeout(500)
    ev(pg, "localStorage.setItem('bc_cheered', JSON.stringify(" + json.dumps(CHAIN[:10]) + "))"); pg.goto(URL); pg.wait_for_timeout(600)
    check("new player after Santa: Gnome open, Wizard locked until the Dwarf King", ev(pg, "[BC.isUnlocked('gnome'), BC.isUnlocked('wizard')]") == [True, False])
    ev(pg, "BC.openLevels('title')"); pg.wait_for_timeout(500); shot(pg, "88_world_select_forest_open")
    ctx.close()


def lazy_load_tests(br, p, errors):
    """World 2+ art is not in index.html: it loads on demand from assets/world<N>.js (same-origin file, no other requests)."""
    ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
    reqs = []; ctx.on("request", lambda r: reqs.append(r.url))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL); pg.wait_for_timeout(300)
    r = ev(pg, "[!!BC.LV.grandpa, !!BC.LV.bigfoot, !!BC.LV.wizard, !!BC.LV.elf, Object.keys(BC.packs).length]")
    check("lazy load: World 1 + Wizard are in index.html; World 2 is not loaded for a new player", r == [True, True, True, False, 0], str(r))
    html = open(os.path.join(HERE, "index.html")).read()
    check("lazy load: index.html has no World 2/3 level art", all('"%s":{"level"' % l not in html for l, _, _ in W2 + W3)
          and all(os.path.exists(os.path.join(HERE, "assets", "world%d.js" % n)) for n in (2, 3)))
    ev(pg, "BC.ensureWorld('santa', ok => window.__ok = ok)"); pg.wait_for_function("window.__ok !== undefined", timeout=5000)
    r = ev(pg, "[window.__ok, !!BC.LV.elf, !!BC.LV.santa, BC.packs['2'], !!BC.frames['santa/haz3_0']]")
    check("lazy load: ensureWorld loads assets/world2.js (all 5 levels + sprites)", r == [True, True, True, "ready", True], str(r))
    bad = [u for u in reqs if not (u.startswith("file://") or u.startswith("data:"))]
    check("lazy load: only same-origin local files requested", not bad and any(u.endswith("assets/world2.js") for u in reqs), str([u[-40:] for u in reqs]))
    pg.goto(URL); ev(pg, "localStorage.setItem('bc_cheered', JSON.stringify(['grandpa','goat','lumberjack','mountain','bigfoot'])); localStorage.setItem('bc_level', 'elf')")
    pg.goto(URL); pg.wait_for_function("BC.ready", timeout=5000); pg.wait_for_timeout(200)
    check("lazy load: a saved World 2 level comes back after reload", ev(pg, "[BC.LEVEL, BC.ROWS > 20]") == ["elf", True], str(ev(pg, "BC.LEVEL")))
    ctx.close()


def world_tests(br, p, errors, LIST, pre, ws_shot, ws_at):
    chain = CHAIN
    for i, (lv, nxt, items) in enumerate(LIST):
        ctx = watch_net(br.new_context(**p.devices["iPhone 14"]))
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.goto(URL); pg.wait_for_timeout(500)
        ev(pg, f"localStorage.setItem('bc_cheered', JSON.stringify({json.dumps(chain[:chain.index(lv)])})); localStorage.setItem('bc_cine', '1')")
        pg.goto(URL); pg.wait_for_timeout(700); t = Touch(pg)
        st = ev(pg, f"[BC.isUnlocked('{lv}'), BC.isUnlocked('{nxt}'), BC.owns('{items[0]}'), BC.owns('{items[1]}')]")
        check(f"{lv}: unlocked by the giant before it; next locked; its shop set still locked", st == [True, False, False, False], str(st))
        ev(pg, "BC.openLevels('title')"); pg.wait_for_timeout(450)
        if lv == ws_at: shot(pg, ws_shot)
        L = ev(pg, "BC.levelsLayout()")
        tap_rect(pg, t, L["rows"][chain.index(lv)]); pg.wait_for_timeout(400)
        check(f"{lv}: world select -> its intro", ev(pg, "[BC.screen, BC.LEVEL]") == ["intro", lv])
        pg.wait_for_function("BC.Intro.t > 1.0"); shot(pg, f"{pre}0_{lv}_intro")
        pg.wait_for_function("BC.Intro.t > 3.3"); shot(pg, f"{pre}0b_{lv}_intro_packed")
        t.tap("L"); pg.wait_for_timeout(400)
        info = ev(pg, "[BC.screen, BC.ROWS, BC.T.CLIMB_LENGTH, window.ASSETS.hazard_names.length, BC.T.EVENT, BC.T.TUTORIAL, BC.S.lives]")
        check(f"{lv}: climb starts on its own beard + hazards (not a tutorial)", info[0] == "play" and info[2] == 1 and info[3] >= 4 and info[5] is False and info[6] == 3, str(info))
        ev(pg, "BC.S.cl.invulnUntil = 1e9")
        tut_bot(pg, t, "BC.S.cl.z > BC.START_Z + 4.5", 60)
        pg.wait_for_timeout(200); shot(pg, f"{pre}1_{lv}_mid_climb")
        check(f"{lv}: real touch climbing gains height", ev(pg, "BC.S.cl.z - BC.START_Z") > 3, str(ev(pg, "BC.S.cl.z")))
        ev(pg, "BC.calm(); BC.set({col: 2, x: 2.5, z: BC.GOAL_Z - 1.2, arm: null})"); pg.wait_for_timeout(300)
        tut_bot(pg, t, "BC.screen === 'ending'", 40)
        check(f"{lv}: reaches the top -> ending", ev(pg, "BC.screen") == "ending")
        pg.wait_for_function(f"BC.Ending.t > {5.6 if lv == 'santa' else 3.9}"); shot(pg, f"{pre}2_{lv}_ending")
        e = ev(pg, f"[BC.face, !!BC.S.itemIn, !!(BC.S.beaming || BC.S.asleep), BC.cheered.includes('{lv}'), BC.S.unlocked, BC.S.newSet, BC.isUnlocked('{nxt}'), BC.owns('{items[0]}'), BC.owns('{items[1]}')]")
        check(f"{lv} ending: gift delivered, he beams; unlocks {nxt} + his shop set", e == ["sleep", True, True, True, nxt, lv, True, True, True], str(e))
        if lv == "bigfoot": check("bigfoot ending: the selfie was taken", ev(pg, "BC.S.selfieTaken") is True)
        pg.wait_for_function("BC.screen === 'para'", timeout=8000)
        para_bot(pg, t, ("para",))
        pg.wait_for_function("BC.screen === 'bird'", timeout=8000); pg.wait_for_timeout(1900)
        if lv == "goat": shot(pg, "64_goat_bird_next_lumberjack")
        if lv == "bigfoot":
            shot(pg, "64b_bigfoot_bird_next_elf")
            check("bigfoot bird: NEXT: THE ELF!", ev(pg, "BC.nextText ? BC.nextText() : null") in ("NEXT: THE ELF!", None), str(ev(pg, "BC.nextText ? BC.nextText() : null")))
        if lv == "santa": shot(pg, "74_santa_bird_next_gnome")
        if lv == "dwarf": shot(pg, "89_dwarf_bird_next_wizard")
        pg.wait_for_function("BC.screen === 'results'", timeout=8000); pg.wait_for_timeout(1400)
        if lv == "bigfoot": shot(pg, "65_bigfoot_results_next_elf")
        if lv == "santa": shot(pg, "75_santa_results_gnome_unlocked")
        if lv == "dwarf": shot(pg, "89b_dwarf_results_wizard_unlocked")
        if lv == "rudolph": check("rudolph ending: his nose glows again", ev(pg, "BC.S.glowT !== undefined") is True)
        if lv == "santa": check("santa ending: cookie eaten, yawn, fast asleep", ev(pg, "[BC.S.asleep, BC.face]") == [True, "sleep"])
        check(f"{lv} results: collectibles counted, NEXT = {nxt}", ev(pg, "[BC.nextLevel(), BC.S.result.earned > 0]") == [nxt, True])
        tap_rect(pg, t, ev(pg, "BC.resultsLayout()")["play"]); pg.wait_for_timeout(400)
        check(f"{lv} results: NEXT loads {nxt}", ev(pg, "[BC.screen, BC.LEVEL]") == ["intro", nxt])
        ctx.close()


def world_events(br, p, errors, EVS):
    for lv, ev_name in EVS:
        ctx = br.new_context(**p.devices["iPhone 14"]); pg = ctx.new_page(); pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL + "&level=" + lv); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(600); t = Touch(pg)
        ev(pg, "BC.start(); BC.calm(); BC.S.cl.invulnUntil = 1e9; BC.set({col: 2, x: 2.5, z: 9, arm: null})"); pg.wait_for_timeout(1700)
        ev(pg, "BC.S.sneeze.next = BC.S.t"); pg.wait_for_timeout(int(1000 * ev(pg, "BC.T.SNEEZE_WARN")) - 300)
        shot(pg, f"66_{lv}_{ev_name}_warning")
        pg.wait_for_timeout(1100)
        r = ev(pg, "[BC.S.cl.col, BC.S.cl.z, BC.S.eventsLost || 0, BC.S.haz.length]")
        moved = r[0] != 2 or r[1] < 8.9
        check(f"{lv}: {ev_name} without holding knocks Pip about", moved and r[2] == 1 and (ev_name not in ("stomp", "roar") or r[3] >= 1), str(r))
        ev(pg, "BC.calm(); BC.S.cl.invulnUntil = 1e9; BC.set({col: 2, x: 2.5, z: 9, arm: null}); BC.S.sneeze.n = 0; BC.S.sneeze.next = BC.S.t"); t.press("R")
        pg.wait_for_timeout(int(1000 * ev(pg, "BC.T.SNEEZE_WARN")) + 600); t.end()
        r = ev(pg, "[BC.S.cl.col, BC.S.cl.z, BC.S.eventsLost || 0]")
        check(f"{lv}: {ev_name} while holding = held on", r[0] == 2 and r[2] == 1 and r[1] > 8.9, str(r))
        ctx.close()


def main():
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--autoplay-policy=no-user-gesture-required"])
        ctx = br.new_context(**p.devices["iPhone 14"]); watch_net(ctx)
        pg = ctx.new_page()
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(URL_W)
        pg.wait_for_timeout(900)
        t = Touch(pg)
        check("title screen shows", ev(pg, "BC.screen") == "title")
        # wait for the blinking TAP TO START to be visible
        pg.wait_for_function("Math.floor(performance.now() / 1000 * 2.2) % 2 === 0")
        shot(pg, "01_title")
        size = ev(pg, "[innerWidth, innerHeight, devicePixelRatio, getComputedStyle(document.getElementById('game')).width, document.getElementById('game').height]")
        check("integer scale canvas", True, f"viewport/dpr/css width/native H = {size}")
        t.tap("R"); pg.wait_for_timeout(400)
        check("how-to after first tap", ev(pg, "BC.screen") == "howto")
        pg.wait_for_function("Math.floor(performance.now() / 1000 * 2.2) % 2 === 0")
        shot(pg, "02_howto")
        t.tap("R"); pg.wait_for_timeout(450)
        check("character creator after how-to", ev(pg, "BC.screen") == "creator")

        # ---------------------------------------------------------------- character creator (Task 2)
        lay = ev(pg, "BC.creatorLayout()")
        look0 = ev(pg, "Object.assign({}, BC.look)")
        tap_rect(pg, t, lay["rows"][1]["R"]); pg.wait_for_timeout(250)          # HAIR >
        look1 = ev(pg, "Object.assign({}, BC.look)")
        check("creator: hair arrow changes the hair style", look1["hair"] == (look0["hair"] + 1) % 4, f"{look0['hair']}->{look1['hair']}")
        tap_rect(pg, t, lay["rows"][0]["L"]); pg.wait_for_timeout(250)          # BODY <
        check("creator: body arrow toggles boy/girl", ev(pg, "BC.look.body") != look1["body"])
        tap_rect(pg, t, lay["rand"]); pg.wait_for_timeout(250)
        rnd = ev(pg, "JSON.stringify(BC.look)")
        check("creator: randomize + saved to localStorage", ev(pg, "localStorage.getItem('bc_look')") == rnd, rnd)
        # pick a distinctive look (teal outfit is not in the Wizard palette) and set it with real taps
        target = {"body": 1, "hair": 3, "hairCol": 2, "skin": 4, "outfit": 6, "gear": 4, "hat": 3, "pattern": 0, "pack": 0, "chute": 0}
        opts = ev(pg, "BC.OPTS.map(o => [o.k, (o.names || o.list).length])")
        for i, (k, n) in enumerate(opts):
            for _ in range(n):
                if ev(pg, f"BC.look.{k}") == target[k]: break
                tap_rect(pg, t, lay["rows"][i]["R"]); pg.wait_for_timeout(60)
        check("creator: arrows reach every option", ev(pg, "JSON.stringify(BC.look)") == ev(pg, f"JSON.stringify({target})"), ev(pg, "JSON.stringify(BC.look)"))
        tap_rect(pg, t, lay["turn"]); pg.wait_for_timeout(300)
        pg.wait_for_timeout(200); shot(pg, "12_creator_back")
        tap_rect(pg, t, lay["turn"]); pg.wait_for_timeout(500)
        shot(pg, "12_creator")
        TEAL = "#20b0a8"
        check("creator: live preview uses the look", count_color(pg, TEAL) > 40, f"{count_color(pg, TEAL)} teal px")
        tap_rect(pg, t, lay["start"]); pg.wait_for_timeout(300)
        check("START opens the opening cinematic (first time)", ev(pg, "BC.screen") == "cine")

        # ---------------------------------------------------------------- opening cinematic
        pg.wait_for_function("BC.Cine.t > 1.2"); shot(pg, "cinematic_0_whiskerton")
        names = ["grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa", "wizard"]
        for k, nm in enumerate(names):            # jump through the vignettes (time-scrub, real rendering)
            ev(pg, f"BC.Cine.t = BC.T.CINE_PROLOGUE + {k} * BC.T.CINE_VIG + 2.0"); pg.wait_for_timeout(150)
            shot(pg, f"cinematic_{k + 1}_{nm}")
        ev(pg, f"BC.Cine.t = BC.T.CINE_PROLOGUE + {len(names)} * BC.T.CINE_VIG + 2.6"); pg.wait_for_timeout(200)
        shot(pg, f"cinematic_{len(names) + 1}_pip_will_cheer_them_up")
        check("cinematic length 15-36 s (15 giants)", 15 <= ev(pg, "BC.cineLength()") <= 36, f"{ev(pg, 'BC.cineLength()'):.1f} s")
        check("cinematic shows Pip in the creator look", count_color(pg, TEAL) > 20)
        ev(pg, "BC.Cine.t = 3"); pg.wait_for_timeout(500)
        t.tap("R"); pg.wait_for_timeout(250)
        check("tap skips the cinematic -> Wizard intro", ev(pg, "BC.screen") == "intro")

        # ---------------------------------------------------------------- Wizard intro at the base of the beard
        pg.wait_for_function("BC.Intro.t > 1.9"); shot(pg, "13_intro_pack_book_cat")
        check("intro: Pip in the creator look", count_color(pg, TEAL) > 20)
        pg.wait_for_function("BC.Intro.t > 3.6"); shot(pg, "13b_intro_bring_it_back")
        t.tap("L"); pg.wait_for_timeout(350)
        check("tap skips the intro -> climb", ev(pg, "BC.screen") == "play")
        check("game starts", ev(pg, "BC.screen") == "play")
        check("the cat rides in Pip's backpack", ev(pg, "BC.S.catOn") is True)
        check("climb: Pip in the creator look", count_color(pg, TEAL) > 20)
        check("pages are tucked in the beard", ev(pg, "BC.S.items.filter(i => i.kind === 'page').length") == ev(pg, "BC.T.PAGES"))

        # --- a single tap registers immediately (same event, before the next frame)
        ev(pg, "BC.calm()")
        z0 = ev(pg, "BC.S.cl.z")
        t.start([{"x": t.L, "y": t.Y, "id": 1}])
        st = ev(pg, "[BC.S.cl.arm, BC.S.cl.tw && BC.S.cl.tw.toZ]")
        t.end()
        check("single tap registers immediately", st[0] == "L" and st[1] > z0, f"arm={st[0]} target z {z0:.2f}->{st[1]:.2f}")
        pg.wait_for_timeout(60)
        check("reach pose shows the tapped arm", ev(pg, "BC.sprite.pose") in ("c6", "c7", "c0"), ev(pg, "BC.sprite.pose"))
        pg.wait_for_timeout(300)

        # --- alternating taps climb (clear column 1 has no bald patches)
        ev(pg, "BC.set({col: 1, x: 1.5, z: 3, arm: null}); BC.calm()")
        pg.wait_for_timeout(300)
        z0 = ev(pg, "BC.S.cl.z")
        for i in range(10):
            t.tap("R" if i % 2 == 0 else "L", 30); pg.wait_for_timeout(70)   # ~10 taps/s
        pg.wait_for_timeout(200)
        z1, col = ev(pg, "[BC.S.cl.z, BC.S.cl.col]")
        step = ev(pg, "BC.T.STEP")
        check("fast alternating taps all climb (no dyno stolen)", abs((z1 - z0) - 10 * step) < 0.05 and col == 1,
              f"dz={z1 - z0:.2f} expected {10 * step:.2f}, col {col}")
        shot(pg, "03_early_climb")
        # same side twice (slowly) does not climb
        z0 = ev(pg, "BC.S.cl.z")
        t.tap("L"); pg.wait_for_timeout(400); t.tap("L"); pg.wait_for_timeout(400)
        z1 = ev(pg, "BC.S.cl.z")
        check("same side twice climbs only once", abs((z1 - z0) - step) < 0.05 or abs(z1 - z0) < 0.05, f"dz={z1 - z0:.2f}")
        # --- double tap = dyno
        col0 = ev(pg, "BC.S.cl.col")
        t.tap("R", 30); pg.wait_for_timeout(110); t.tap("R", 30)
        pg.wait_for_timeout(80)
        mid_pose = ev(pg, "BC.sprite.pose")
        pg.wait_for_timeout(400)
        col1 = ev(pg, "BC.S.cl.col")
        check("double tap dynos one column", col1 == col0 + 1 and mid_pose == "dyno", f"col {col0}->{col1}, pose {mid_pose}")

        # --- hazards come from the mouth (near the top, face on screen)
        ev(pg, f"BC.set({{col: 3, x: 3.5, z: BC.GOAL_Z - 3.2, arm: null}}); BC.calm()")
        pg.wait_for_timeout(600)
        ev(pg, "BC.spawn(0, 2)")                 # a regular throw (crystal ball) aimed at column 2
        pg.wait_for_function("BC.S.haz.length && BC.S.haz[0].emerge < 0.08")
        hz = ev(pg, "BC.S.haz.map(h => [h.x, h.z, h.emerge])")
        mouth = ev(pg, "[BC.MOUTH_Z, BC.S.t < BC.S.mouthOpenUntil]")
        check("hazard thrown from the open mouth", len(hz) == 1 and abs(hz[0][1] - mouth[0]) < 0.6 and mouth[1], f"haz {hz}, mouth z {mouth}")
        shot(pg, "06_top_mouth_spitting")
        pg.wait_for_timeout(250); shot(pg, "06b_top_hazard_falling")

        # --- a hit costs a life and knocks you down
        ev(pg, "BC.set({col: 1, x: 1.5, z: 10, arm: null}); BC.calm(); BC.S.hat = 0")   # (a tangled hat may have been grabbed above)
        pg.wait_for_timeout(500)
        ev(pg, "BC.spawn(0, 1, 13.5)")
        pg.wait_for_timeout(1300)
        lives, z = ev(pg, "[BC.S.lives, BC.S.cl.z]")
        check("hit costs a life + knockdown", lives == 2 and z < 9, f"lives {lives}, z {z:.2f}")

        # --- hard hat: pick up, absorbs 3 hits
        pg.wait_for_timeout(1600)       # invulnerability over
        ev(pg, "BC.set({col: 1, x: 1.5, z: 10, arm: null}); BC.calm(); BC.spawn('hat', 1, 13)")
        pg.wait_for_timeout(1300)
        check("hard hat picked up", ev(pg, "BC.S.hat") == 3, f"hat {ev(pg, 'BC.S.hat')}")
        check("climber sprite wears hard hat", ev(pg, "BC.sprite.tag") == "h0")
        shot(pg, "04_hat_on")
        hats = []
        for i in range(3):
            ev(pg, "BC.spawn(1, 1, BC.S.cl.z + 4)")
            pg.wait_for_timeout(560 if i == 1 else 900)
            if i == 1: shot(pg, "04b_hat_cracked_flash")
            if i == 1: pg.wait_for_timeout(340)
            hats.append(ev(pg, "[BC.S.hat, BC.S.lives]"))
        check("hat absorbs 3 hits then pops", [h[0] for h in hats] == [2, 1, 0] and all(h[1] == 2 for h in hats), f"{hats}")
        pg.wait_for_timeout(200)

        # --- two-finger brace blocks a hit
        ev(pg, "BC.set({z: 10}); BC.calm(); BC.spawn(2, 1, BC.S.cl.z + 5)")
        pg.wait_for_timeout(250)
        t.two_finger()
        braced = ev(pg, "BC.S.t < BC.S.cl.braceUntil")
        pg.wait_for_timeout(120); shot(pg, "07_brace")
        pg.wait_for_timeout(700)
        check("two-finger brace blocks a hit", braced and ev(pg, "BC.S.lives") == 2, f"braced {braced}, lives {ev(pg, 'BC.S.lives')}")

        # --- sneeze: hold tight vs. shaken off
        ev(pg, "BC.set({z: 10, arm: null}); BC.calm()"); pg.wait_for_timeout(1300)
        ev(pg, "BC.sneezeNow()")
        pg.wait_for_timeout(500)
        pg.wait_for_function("Math.floor(BC.S.t * 6) % 2 === 0 && BC.S.sneeze.phase === 'warn'"); shot(pg, "08_sneeze_warning")
        t.press("L"); pg.wait_for_function("BC.S.sneeze.phase === 'blast'")
        pg.wait_for_timeout(250); shot(pg, "08b_sneeze_holding"); pg.wait_for_timeout(800)
        z0 = ev(pg, "BC.S.cl.z"); pg.wait_for_timeout(600); held = ev(pg, "[BC.S.cl.hold, BC.S.cl.z]")
        t.end()
        check("long-press holds through a sneeze", held[0] and abs(held[1] - z0) < 0.01, f"{held} z0 {z0:.2f}")
        ev(pg, "BC.S.sneeze.next = BC.S.t"); pg.wait_for_timeout(2500)
        check("sneeze without holding knocks you down", ev(pg, "BC.S.cl.z") < z0 - 1.0, f"z {ev(pg, 'BC.S.cl.z'):.2f}")

        # --- mid-level hazards (natural throws)
        ev(pg, "BC.set({col: 2, x: 2.5, z: 12, arm: null}); BC.S.nextThrow = BC.S.t; BC.S.sneeze.next = 1e9; BC.ghost = true")
        pg.wait_for_timeout(1500)
        pg.wait_for_function("BC.S.haz.filter(h => h.z < BC.S.camZ + 12 && h.z > BC.S.camZ).length >= 2", timeout=8000)
        shot(pg, "05_mid_level_hazards")
        ev(pg, "BC.ghost = false")

        # --- a page is picked up when Pip's hands reach it
        pg_ = ev(pg, "(() => { const p = BC.S.items.find(i => i.kind === 'page'); return [p.x, p.z]; })()")
        n0 = ev(pg, "BC.S.pages")
        ev(pg, f"BC.calm(); BC.set({{col: {int(pg_[0])}, x: {pg_[0]}, z: {pg_[1]} - BC.T.HAND - 0.2, arm: null}})")
        pg.wait_for_timeout(300)
        check("page collected", ev(pg, "BC.S.pages") == n0 + 1, f"pages {ev(pg, 'BC.S.pages')}")

        # --- level complete -> story ending (replaces the old win panel)
        ev(pg, "BC.set({col: 2, x: 2.5, z: BC.GOAL_Z - 1.5, arm: null}); BC.calm()")
        pg.wait_for_timeout(500)
        ev(pg, "BC.spawn(0, 5, BC.GOAL_Z + 1.5)")          # one in flight, far from Pip: it must go 'poof'
        for i in range(6):
            t.tap("L" if i % 2 == 0 else "R"); pg.wait_for_timeout(160)
        pg.wait_for_timeout(300)
        res = ev(pg, "BC.S.result")
        check("level completes at the mouth", res and res["won"], f"{res}")
        check("reaching the top starts the ending", ev(pg, "BC.screen") == "ending")
        shot(pg, "09_level_complete")
        pg.wait_for_function("BC.Ending.t > 1.25"); shot(pg, "14_ending_book_back")
        nh = ev(pg, "BC.S.haz.length")
        pg.wait_for_timeout(1200)
        check("hazards stop in the ending", nh == 0 and ev(pg, "BC.S.haz.length") == 0)
        pg.wait_for_function("BC.face === 'sleep'"); pg.wait_for_timeout(500)
        shot(pg, "14_ending_sleeping_wizard")
        check("wizard falls asleep, cat tucked in, book back", ev(pg, "[BC.face, BC.S.asleep, BC.S.catIn, BC.S.bookIn, BC.S.catOn]") == ["sleep", True, True, True, False])

        # ---------------------------------------------------------------- parachute bonus
        pg.wait_for_function("BC.screen === 'para'", timeout=5000)
        check("ending flows into the parachute bonus", True)
        lives = ev(pg, "BC.S.lives")
        x0 = ev(pg, "BC.S.cl.x")
        for _ in range(3): t.tap("R", 30); pg.wait_for_timeout(60)
        pg.wait_for_timeout(300)
        x1 = ev(pg, "BC.S.cl.x")
        for _ in range(4): t.tap("L", 30); pg.wait_for_timeout(60)
        pg.wait_for_timeout(400)
        x2 = ev(pg, "BC.S.cl.x")
        check("parachute: tap right/left steers", x1 > x0 + 0.3 and x2 < x1 - 0.3, f"x {x0:.2f} -> {x1:.2f} -> {x2:.2f}")
        shot_done = False
        while ev(pg, "BC.screen") == "para":       # steer toward the next coin like a player would
            s = ev(pg, """(() => { const c = BC.S.cl, it = BC.Para.items.filter(i => !i.got && i.z < c.z + 1.5).sort((a, b) => b.z - a.z)[0];
                return [c.x, it ? it.x : c.x, BC.Para.t]; })()""")
            if abs(s[1] - s[0]) > 0.25: t.tap("R" if s[1] > s[0] else "L", 25)
            if not shot_done and s[2] > 5: shot(pg, "15_parachute"); shot_done = True
            pg.wait_for_timeout(110)
        para = ev(pg, "[BC.Para.coins, BC.Para.stars, BC.Para.t, BC.S.lives]")
        check("parachute: coins collected, no lives lost, ~10-15 s", para[0] > 3 and para[3] == lives and 10 <= para[2] <= 15, f"coins {para[0]} stars {para[1]} t {para[2]:.1f}s lives {para[3]}")

        # ---------------------------------------------------------------- bird carries Pip off
        check("parachute ends with the bird", ev(pg, "BC.screen") == "bird")
        pg.wait_for_timeout(1900); shot(pg, "16_bird_carry_next_lumberjack")
        pg.wait_for_function("BC.screen === 'results'", timeout=6000)
        pg.wait_for_timeout(1300); shot(pg, "17_results_thanks")
        check("results / thanks screen", ev(pg, "BC.screen") == "results" and ev(pg, "BC.S.result.coins") == para[0])
        rl = ev(pg, "BC.resultsLayout()")
        tap_rect(pg, t, rl["intro"]); pg.wait_for_timeout(300)
        check("results: WATCH INTRO replays the cinematic", ev(pg, "BC.screen") == "cine")
        pg.wait_for_timeout(200); t.tap("R"); pg.wait_for_timeout(300)
        check("skipping it returns to the results", ev(pg, "BC.screen") == "results")
        pg.wait_for_timeout(1000)
        tap_rect(pg, t, rl["play"]); pg.wait_for_timeout(300)
        check("results: PLAY AGAIN -> intro (cinematic not repeated)", ev(pg, "BC.screen") == "intro")
        pg.wait_for_timeout(300); t.tap("R"); pg.wait_for_timeout(300)
        check("replay climb starts fresh", ev(pg, "[BC.screen, BC.S.pages, BC.S.catOn, BC.face]") == ["play", 0, True, "normal"])
        # --- debug params: ?debug=1 (hitboxes, tile overlay, fps) and ?skip=top
        pgd = ctx.new_page(); pgd.on("pageerror", lambda e: errors.append(str(e)))
        pgd.goto(URL_W + "&debug=1&skip=top"); pgd.wait_for_timeout(500)
        td = Touch(pgd)
        td.tap("R"); pgd.wait_for_timeout(400); td.tap("R"); pgd.wait_for_timeout(1800)
        check("?skip=top starts near the face", ev(pgd, "BC.S.cl.z") > ev(pgd, "BC.GOAL_Z") - 6)
        check("?skip=top keeps the saved look", ev(pgd, "BC.look.outfit") == 6)
        shot(pgd, "10_debug_skip_top")
        ev(pgd, "BC.calm(); BC.set({col: 2, x: 2.5, arm: null})"); pgd.wait_for_timeout(200)
        for i in range(30):                       # climb the last rows with real taps
            if ev(pgd, "BC.screen") != "play": break
            td.tap("L" if i % 2 == 0 else "R", 30); pgd.wait_for_timeout(140)
        check("?skip=top: climbing to the top reaches the ending", ev(pgd, "BC.screen") == "ending")
        pgd.wait_for_timeout(700); td.tap("R"); pgd.wait_for_timeout(300)
        check("tap skips the ending -> parachute", ev(pgd, "BC.screen") == "para" and ev(pgd, "BC.face") == "sleep")
        ev(pgd, "BC.startBird()"); pgd.wait_for_timeout(700); td.tap("R"); pgd.wait_for_timeout(300)
        check("tap skips the bird -> results", ev(pgd, "BC.screen") == "results")
        pgd.close()
        # --- title WATCH INTRO button, look persists across reloads
        pgt = ctx.new_page(); pgt.on("pageerror", lambda e: errors.append(str(e)))
        pgt.goto(URL_W); pgt.wait_for_timeout(600)
        tt = Touch(pgt)
        check("look persists across reloads", ev(pgt, "BC.look.outfit") == 6 and ev(pgt, "BC.look.hat") == 3)
        tap_rect(pgt, tt, ev(pgt, "BC.TITLE_INTRO_BTN()")); pgt.wait_for_timeout(300)
        check("title: WATCH INTRO plays the cinematic", ev(pgt, "BC.screen") == "cine")
        pgt.wait_for_timeout(200); tt.tap("L"); pgt.wait_for_timeout(300)
        check("skipping it returns to the title", ev(pgt, "BC.screen") == "title")
        pgt.close()
        # --- desktop keyboard
        dctx = br.new_context(viewport={"width": 1280, "height": 800})
        pk = dctx.new_page(); pk.on("pageerror", lambda e: errors.append(str(e)))
        pk.goto(URL_W); pk.wait_for_timeout(500)
        for scr in ("howto", "creator", "cine", "intro", "play"):
            pk.keyboard.press("Enter"); pk.wait_for_timeout(450)
            if ev(pk, "BC.screen") != scr: break
        check("keyboard: Enter goes title > how-to > creator > cinematic > intro > climb", ev(pk, "BC.screen") == "play")
        ev(pk, "BC.calm(); BC.set({col: 1, x: 1.5, z: 3, arm: null})"); pk.wait_for_timeout(200)
        z0 = ev(pk, "BC.S.cl.z")
        for i in range(6): pk.keyboard.press("ArrowRight" if i % 2 == 0 else "ArrowLeft"); pk.wait_for_timeout(120)
        pk.wait_for_timeout(150)
        check("keyboard: arrows climb", abs(ev(pk, "BC.S.cl.z") - z0 - 6 * step) < 0.05, f"dz {ev(pk, 'BC.S.cl.z') - z0:.2f}")
        pk.keyboard.press("ArrowRight"); pk.wait_for_timeout(100); pk.keyboard.press("ArrowRight"); pk.wait_for_timeout(400)
        check("keyboard: double press dynos", ev(pk, "BC.S.cl.col") == 2)
        pk.keyboard.press("ArrowDown"); b1 = ev(pk, "BC.S.t < BC.S.cl.braceUntil")
        pk.keyboard.down("ArrowUp"); pk.wait_for_timeout(100); h1 = ev(pk, "BC.S.cl.hold"); pk.keyboard.up("ArrowUp")
        check("keyboard: down = brace, hold up = hold tight", b1 and h1 and not ev(pk, "BC.S.cl.hold"))
        pk.screenshot(path=os.path.join(SHOTS, "11_desktop_letterbox.png")); dctx.close()
        check("no console errors", not errors, f"{errors[:3]}")
        check("index.html under 1 MB (budget for all the worlds)", os.path.getsize(os.path.join(HERE, "index.html")) < 1024 * 1024,
              f"{os.path.getsize(os.path.join(HERE, 'index.html')) / 1024:.0f} KB")

        # ---------------------------------------------------------------- bot-played GIF
        pg2 = ctx.new_page(); pg2.on("pageerror", lambda e: errors.append(str(e)))
        pg2.goto(URL_W); pg2.wait_for_timeout(700)
        t2 = Touch(pg2)
        GIF_MS = 100
        ev(pg2, f"BC.record({GIF_MS})")
        pg2.wait_for_timeout(1200); t2.tap("R"); pg2.wait_for_timeout(1500)
        ev(pg2, "BC.start()"); pg2.wait_for_timeout(300)
        import random; rng = random.Random(3)    # the bot sometimes misses a hazard (so hits/hat show up)
        side, holding, t_start = "L", False, time.time()
        while time.time() - t_start < 75:
            s = ev(pg2, """(() => { const S = BC.S, c = S.cl, row = Math.floor(c.z + BC.T.STEP + BC.T.HAND);
              const A = window.ASSETS, bald = (col) => col < 0 || col > 5 || (A.tilemap[row] || [])[col] === 'sparse' || c.z < Math.max(BC.START_Z - 0.4, A.col_min_z[col] - 0.6);
              const danger = (col) => S.haz.some(h => !h.good && !h.deflected && Math.abs(h.tx - (col + 0.5)) < 0.3 && h.z > c.z && h.z - c.z < 5);
              return {sn: S.sneeze.phase, res: !!S.result, mode: c.mode, col: c.col, baldUp: bald(c.col),
                      dangerHere: danger(c.col), okL: !bald(c.col - 1) && !danger(c.col - 1), okR: !bald(c.col + 1) && !danger(c.col + 1),
                      cd: S.t < c.braceCdUntil, z: c.z}; })()""")
            if s["res"]:
                pg2.wait_for_timeout(2500)
                break
            if s["sn"] != "none":
                if not holding: t2.press("L"); holding = True
            elif holding:
                t2.end(); holding = False
            elif s["mode"] == "climb" and (s["baldUp"] or (s["dangerHere"] and rng.random() < 0.75)):
                if s["okL"] or s["okR"]:
                    d = "L" if s["okL"] and (not s["okR"] or s["col"] > 2) else "R"
                    t2.tap(d, 25); pg2.wait_for_timeout(70); t2.tap(d, 25); side = "L"
                elif s["dangerHere"] and not s["cd"]:
                    t2.two_finger()
            elif s["mode"] == "climb":
                t2.tap(side, 25); side = "R" if side == "L" else "L"
            pg2.wait_for_timeout(150)          # ~5-6 taps/s, a human pace
        uris = ev(pg2, "BC.stopRecord()")
        frames = []
        if len(uris) > 220: uris = uris[:220]            # keep the GIF under 8 MB (first ~22 s of the climb)
        for u in uris:
            im = Image.open(io.BytesIO(base64.b64decode(u.split(",")[1]))).convert("RGB")
            frames.append(im.resize((im.width * 2, im.height * 2), Image.NEAREST))
        print("bot finished:", ev(pg2, "[BC.S.result, BC.S.lives, BC.S.t, BC.S.score]"))
        gif = os.path.join(SHOTS, "gameplay.gif")
        tmp = os.path.join(HERE, "build", "gif"); os.makedirs(tmp, exist_ok=True)
        for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
        for i, f in enumerate(frames): f.save(os.path.join(tmp, f"f{i:04d}.png"))
        fps = round(1000 / GIF_MS)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
                        "-vf", "split[a][b];[a]palettegen=max_colors=32:stats_mode=full[p];[b][p]paletteuse=dither=none",
                        gif], check=True)
        print(f"gameplay.gif: {len(frames)} frames @ {fps} fps, {os.path.getsize(gif) / 1e6:.2f} MB")
        check("gameplay.gif under 8 MB", os.path.getsize(gif) < 8e6)

        # ---------------------------------------------------------------- story GIF: ending -> parachute -> bird
        pg3 = ctx.new_page(); pg3.on("pageerror", lambda e: errors.append(str(e)))
        pg3.goto(URL_W); pg3.wait_for_timeout(600)
        t3 = Touch(pg3)
        ev(pg3, "BC.start(); BC.S.pages = 4; BC.set({col: 2, x: 2.5, z: BC.GOAL_Z - 0.4}); BC.calm()"); pg3.wait_for_timeout(400)
        ev(pg3, "BC.record(100)"); pg3.wait_for_timeout(300)
        ev(pg3, "BC.win()")
        while ev(pg3, "BC.screen") in ("ending", "para", "bird"):
            s = ev(pg3, """(() => { if (BC.screen !== 'para') return null; const c = BC.S.cl, it = BC.Para.items.filter(i => !i.got && i.z < c.z + 1.5).sort((a, b) => b.z - a.z)[0];
                return [c.x, it ? it.x : c.x]; })()""")
            if s and abs(s[1] - s[0]) > 0.25: t3.tap("R" if s[1] > s[0] else "L", 25)
            pg3.wait_for_timeout(120)
        pg3.wait_for_timeout(1200)
        uris = ev(pg3, "BC.stopRecord()")
        sg = os.path.join(SHOTS, "story.gif")
        for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
        for i, u in enumerate(uris):
            Image.open(io.BytesIO(base64.b64decode(u.split(",")[1]))).convert("RGB").save(os.path.join(tmp, f"f{i:04d}.png"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "10", "-i", os.path.join(tmp, "f%04d.png"),
                        "-vf", "split[a][b];[a]palettegen=max_colors=64:stats_mode=full[p];[b][p]paletteuse=dither=none",
                        sg], check=True)
        print(f"story.gif: {len(uris)} frames, {os.path.getsize(sg) / 1e6:.2f} MB")
        check("story.gif written", os.path.getsize(sg) < 8e6 and len(uris) > 150)
        check("no console errors (story pages)", not errors, f"{errors[:3]}")
        shop_tests(br, p, errors)
        check("no console errors (shop pages)", not errors, f"{errors[:3]}")
        grandpa_tests(br, p, errors)
        world_select_tests(br, p, errors)
        layout_tests(br, p, errors)
        onehand_tests(br, p, errors)
        choose_tests(br, p, errors)
        world1_tests(br, p, errors)
        lazy_load_tests(br, p, errors)
        world2_tests(br, p, errors)
        world3_tests(br, p, errors)
        check("no console errors (Grandpa / levels / layouts)", not errors, f"{errors[:3]}")
        check("no network requests at all (file:// + data: only)", not REQUESTS, f"{REQUESTS[:3]}")
        br.close()
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed" + (f"; FAILED: {failed}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
