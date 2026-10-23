"""web/balance_check.py - quick difficulty / boost balance check with the test bot (headless, iPhone 14).

  python3 web/balance_check.py [config ...]      configs: grandpa orig none noshelter hardhat life slowmo hardhat_noshelter ...
                                                 (default: all Wizard configs; "grandpa" = the World 1-1 tutorial;
                                                 "goat" "lumberjack" "mountain" "bigfoot" = the rest of World 1)

Plays real-touch climbs with two bot skill levels and prints clear time, hits taken (hearts lost),
hits blocked by hard hats, win/loss and coins banked (wins finish the parachute bonus with a steering bot).
"orig" = the original short beard with the pre-shop difficulty numbers and no shelters (the baseline);
"old" = pre-shop numbers on the new long beard. Results are appended to build/balance.jsonl.
"""
import json, os, random, sys, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_game import Touch, ev, URL_FILE, para_bot, HERE
from browser_config import browser_executable

OLD = {"AIM": 0.5, "THROW_SLOW": 2.0, "THROW_FAST": 0.85, "FALL_SLOW": 3.6, "FALL_FAST": 5.2, "AIM_TOP": 0.5,
       "UPPER_THROW_K": 1, "UPPER_FALL_K": 1, "UPPER_PAIR": 0, "DEF_BOOST_K": 1}
W1_LEVELS = ("grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa",
             "gnome", "rumpel", "rapunzel", "dwarf")   # World 1 + 2 climbs (own tuning, no T overrides)
SEEDS = [int(x) for x in os.environ.get("SEEDS", "3,11,23,37").split(",")]
SKILL = {"good": (0.75, 150), "casual": (0.45, 210)}     # chance to dodge a hazard in your column, ms between taps


def run(pg, t, cfg, skill, seed):
    dodge, pace = SKILL[skill]
    rng = random.Random(seed)
    if cfg in ("old", "orig"): ev(pg, f"Object.assign(BC.T, {json.dumps(OLD)})")
    cfg = cfg.replace("_easy", "")
    boost = {"hardhat": "b_hardhat", "life": "b_life", "slowmo": "b_slowmo"}.get(cfg.replace("_noshelter", "").replace("noshelter", "none"))
    ev(pg, f"BC.setBoosts({{{boost}: 1}}, ['{boost}'])" if boost else "BC.setBoosts({}, [])")
    if cfg != "grandpa": ev(pg, f"BC.T.SHELTERS = {'false' if 'noshelter' in cfg or cfg == 'orig' else 'true'}")
    ev(pg, "BC.start()"); pg.wait_for_timeout(300)
    side, holding, t0 = "L", False, time.time()
    upper_hits = 0
    while time.time() - t0 < 150:
        s = ev(pg, """(() => { const S = BC.S, c = S.cl, row = Math.floor(c.z + BC.T.STEP + BC.T.HAND);
          const A = window.ASSETS, bald = (col) => col < 0 || col > 5 || (A.tilemap[row] || [])[col] === 'sparse' || c.z < Math.max(BC.START_Z - 0.4, A.col_min_z[col] - 0.6);
          const rf = BC.T.EVENT === 'rockfall' && S.sneeze.phase === 'warn' ? (S.sneeze.cols || []) : [];
          const danger = (col) => rf.includes(col) || S.haz.some(h => !h.good && !h.gold && !h.deflected && Math.abs(h.tx - (col + 0.5)) < 0.3 && h.z > c.z && h.z - c.z < 5);
          return {sn: BC.T.EVENT === 'rockfall' ? 'none' : S.sneeze.phase, res: !!S.result, scr: BC.screen, mode: c.mode, col: c.col, baldUp: bald(c.col),
                  dangerHere: danger(c.col), okL: !bald(c.col - 1) && !danger(c.col - 1), okR: !bald(c.col + 1) && !danger(c.col + 1),
                  cd: S.t < c.braceCdUntil, safe: BC.shelterNow, tut: BC.tutStep,
                  shel: ((S.shelters || []).find(sh => sh.state === 'ready' && sh.z - c.z > 0.3 && sh.z - c.z < 2.2 && Math.abs(sh.x - (c.col + 0.5)) === 1) || {}).x}; })()""")
        if s["res"] or s["scr"] != "play": break
        if s["sn"] != "none":
            if not holding: t.press("L"); holding = True
        elif holding:
            t.end(); holding = False
        elif s["tut"] == "down" and s["mode"] == "climb":            # the climb-down lesson
            t.swipe(0, 90); pg.wait_for_timeout(300)
        elif s["tut"] == "dyno" and s["mode"] == "climb" and (s["okL"] or s["okR"]):
            d = "L" if s["okL"] and (not s["okR"] or s["col"] > 2) else "R"   # the leap lesson
            t.tap(d, 25); pg.wait_for_timeout(70); t.tap(d, 25); side = "L"
        elif s["safe"] and (s["dangerHere"] or s["tut"] == "shelter"):
            pass                                   # sit tight in the shelter while something falls
        elif s["mode"] == "climb" and s.get("shel") is not None and (s["okL"] if s["shel"] < s["col"] + 0.5 else s["okR"]):
            d = "L" if s["shel"] < s["col"] + 0.5 else "R"   # a shelter next door: leap into its column
            t.tap(d, 25); pg.wait_for_timeout(70); t.tap(d, 25); side = "L"
        elif s["mode"] == "climb" and (s["baldUp"] or (s["dangerHere"] and rng.random() < dodge)):
            if s["okL"] or s["okR"]:
                d = "L" if s["okL"] and (not s["okR"] or s["col"] > 2) else "R"
                t.tap(d, 25); pg.wait_for_timeout(70); t.tap(d, 25); side = "L"
            elif s["dangerHere"] and not s["cd"]:
                t.two_finger()
        elif s["mode"] == "climb":
            t.tap(side, 25); side = "R" if side == "L" else "L"
        pg.wait_for_timeout(pace)
    if holding: t.end()
    r = ev(pg, "({tut: BC.S.tut ? BC.S.tut.steps : null, won: !!(BC.S.result && BC.S.result.won), t: BC.S.t, lost: BC.S.hitsTaken || 0, blocked: BC.S.hitsAbsorbed, boing: BC.S.shelterBlocks, lives: BC.S.lives, h: Math.round(Math.min(1, (BC.S.maxZ - BC.START_Z) / (BC.GOAL_Z - BC.START_Z)) * 100)})")
    if r["won"]:
        pg.wait_for_timeout(600); t.tap("R"); pg.wait_for_timeout(400)      # skip the ending
        para_bot(pg, t, ("ending", "para", "bird"))
        pg.wait_for_timeout(300)
        r["tut_done"] = ev(pg, "BC.S.tut ? BC.S.tut.i >= BC.TUT_STEPS.length : null")
    else:
        pg.wait_for_timeout(300)
    r["earned"] = ev(pg, "BC.S.result && BC.S.result.earned")
    r.update(cfg=cfg, skill=skill, seed=seed, wall=round(time.time() - t0, 1))     # wall = climb + ending + parachute (s)
    return r


def main():
    cfgs = sys.argv[1:] or ["orig", "none", "noshelter", "hardhat", "life", "slowmo"]
    os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
    out = open(os.path.join(HERE, "build", "balance.jsonl"), "a")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=browser_executable(p.chromium.executable_path), args=["--autoplay-policy=no-user-gesture-required"])
        for cfg in cfgs:
            for skill in SKILL:
                for seed in SEEDS:
                    ctx = br.new_context(**p.devices["iPhone 14"])
                    pg = ctx.new_page(); pg.on("pageerror", lambda e: print("PAGEERROR", e, flush=True)); lv = cfg.replace("_easy", ""); pg.goto(URL_FILE + "?controls=two&" + ("easy=1&" if cfg.endswith("_easy") else "easy=0&") + ("level=" + lv if lv in W1_LEVELS else "level=wizard&len=1" if lv == "orig" else "level=wizard")); pg.wait_for_function("BC.ready"); pg.wait_for_timeout(700)
                    r = run(pg, Touch(pg), cfg, skill, seed)
                    print(json.dumps(r), flush=True); out.write(json.dumps(r) + "\n"); out.flush()
                    ctx.close()
        br.close()


if __name__ == "__main__":
    main()
