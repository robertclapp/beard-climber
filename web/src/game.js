/* Beard Climber - World 1 Whiskerton Woods (Grandpa tutorial, Goat, Lumberjack, Mountain Man, boss Bigfoot)
 * + the Wizard (World 3 boss).
 * Plain JS, no build step. All assets come from window.ASSETS (embedded by web/build_web.py).
 *
 * World units: 1 unit = 1 beard tile = 32 px. x grows right, z grows UP; the level image's
 * top row is z = A.top, its left column x = A.x_left. Columns are 1 unit wide (centre c+0.5).
 * The climber's position (x, z) is its "root" (hips/feet); hands reach ~HAND units above it.
 */
"use strict";
(function () {
const A = window.ASSETS;
const P = A.ppu, W = 224, COLS = A.cols;
let XL = A.x_left;
const params = new URLSearchParams(location.search);
const DEBUG = params.get("debug") === "1";
const SKIP_TOP = params.get("skip") === "top";
const NO_SHELTERS = params.get("shelters") === "0";
const C = A.colors;   // UI palette (the Wizard's); LC = the current level's palette (background, tangles)
let LC = C;

// ---------------------------------------------------------------- tuning
const T = {
  STEP: 0.36,          // height gained per alternating reach (units)
  CLIMB_MS: 110,       // reach tween length
  HAND: 1.7,           // hands are this far above the root (checked against bald tiles)
  DOUBLE_MS: 250,      // same side twice within this = dyno
  DYNO_MS: 260,
  BRACE_MS: 650, BRACE_CD_MS: 1100,
  LONG_MS: 280,        // touch held this long = hold tight
  SWIPE_MIN_PX: 28,    // a finger must travel this far (CSS px) ...
  SWIPE_MAX_MS: 320,   // ... within this long to be a swipe (slower drags stay taps / holds)
  SWIPE_AXIS: 1.4,     // dominant axis must beat the other by this factor (diagonals are ignored)
  DOWN_STEP: 1.0,      // swipe down: climb down this many units (about 3 reaches)
  DOWN_MS: 200,        // ... over this long
  TWO_FINGER_MS: 90,   // two touches starting this close together = brace
  KNOCK_HIT: 2.5,      // rows lost when hit
  KNOCK_SNEEZE: 2.0,   // rows lost when a sneeze shakes you off
  FALL_MS: 480, INVULN_MS: 1500,
  // ---- level length
  CLIMB_LENGTH: 1.6,   // climb height x the original Wizard beard (1 = original; 1.5-2 suggested). Pages, tangled
                       // hats, shelters and the hazard ramp are all placed by progress, so they spread with it.
  LEN_BAND: [8, 20],   // original beard rows repeated to lengthen it (rows 8..19)
  // ---- shelters: thick tangles of beard; falling hazards bounce off while Pip is in one
  SHELTERS: true,      // false (or ?shelters=0) turns them off
  SHELTER_MIN: 2, SHELTER_MAX: 3,   // how many per climb (random in this range)
  SHELTER_S: 3.0,      // seconds of protection after Pip climbs in; then it unravels (one use each, no camping)
  SHELTER_FIRST: 0.18, SHELTER_LAST: 0.9,   // spread evenly (with a little jitter) between these progress values
  // ---- difficulty. p = climb progress 0 (street) .. 1 (chin). Throws and fall speed ramp linearly with p,
  // and the top third gets an extra kick (UPPER_*). Bottom stays gentle for first-time phone players.
  THROW_SLOW: 2.4, THROW_FAST: 1.0,    // seconds between throws at bottom / top (short beard was 2.0 / 0.85;
                                       // the beard is 1.6x longer, so fewer per second keeps total hits fair)
  FALL_SLOW: 3.4, FALL_FAST: 5.2,      // hazard fall speed (units/s) at bottom / top (short beard was 3.6 / 5.2)
  AIM: 0.45, AIM_TOP: 0.55,             // chance a throw targets the climber's column, bottom -> top
  UPPER_P: 0.66,       // the "upper third" starts at this progress
  UPPER_THROW_K: 0.88, // ... throw interval x this up there (more throws)
  UPPER_FALL_K: 1.05,  // ... fall speed x this up there
  UPPER_PAIR: 0.1,     // ... chance a throw is a PAIR (second item in another column)
  DEF_BOOST_K: 1.05,   // a defensive boost (hard hat / extra life / slow-mo) makes throws + falls 5% faster that run
  HAT_THROW_CHANCE: 0.07,
  SNEEZE_FIRST: 9, SNEEZE_MIN: 11, SNEEZE_MAX: 16, SNEEZE_WARN: 1.6, SNEEZE_BLAST: 0.7,
  HAT_HITS: 3,
  PAGES: 5,            // spell-book pages tucked in the beard (collectibles)
  // story / bonus
  CINE_PROLOGUE: 2.6, CINE_VIG: 1.9, CINE_END: 3.8,   // opening cinematic (s): 15 giants -> 34.9 s (vignette beats are scaled from 3.0 s)
  INTRO_S: 5.4, ENDING_S: 5.9, BIRD_S: 4.4,
  PARA_S: 12,          // parachute descent length (s)
  STEER_TAP: 1.7, STEER_HOLD: 7, STEER_MAX: 3.4, STEER_DRAG: 2.4,
  SKIP_LOCK_MS: 350,   // ignore taps this long after a scene starts (so a tap doesn't carry over)
  // coin shop. Wallet = localStorage "bc_coins". A good win earns ~55-75 coins (24 chute coins, 4 stars,
  // 5 pages, win bonus); a loss earns a little (pages + height). Cheap items ~1 run, big ones 3-5 runs.
  EARN_COIN: 1, EARN_STAR: 5, EARN_PAGE: 3, EARN_WIN: 15, EARN_HEIGHT: 10,
  PRICES: { party: 40, propeller: 80, crown: 300, stripes: 50, overalls: 90, gold_outfit: 200, lilac_hair: 60,
            teddy: 100, rocket: 150, wings: 220, gold_gear: 150, dots: 50, stars: 70, checker: 80, rainbow: 160,
            b_hardhat: 25, b_life: 40, b_magnet: 30, b_slowmo: 35 },
  // ---- boosts: consumables, used up (and paid for) every climb they're switched on
  MAX_BOOSTS: 2,       // boosts per climb...
  MAX_DEFENSIVE: 1,    // ...but only ONE defensive one (so 2 = 1 defensive + coin magnet)
  DEFENSIVE: ["b_hardhat", "b_life", "b_slowmo"],
  START_HAT_HITS: 2,   // a bought starting hard hat blocks 2 hits (a found one blocks HAT_HITS = 3)
  EXTRA_LIVES: 1,      // extra-life boost: 3 -> 4 hearts (one per climb, never stacks)
  BOOST_STACK: 9,      // most of one boost you can hold
  MAGNET_R: 1.8,       // coin magnet pull radius (units); parachute bonus ONLY (no effect while climbing)
  SLOWMO_K: 0.6, SLOWMO_S: 15,   // slow-mo boost: hazards x0.6 speed for the first 15 s
  // ---- per-level layout (fractions of the climb) + rules
  PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85],   // where the collectibles (pages / photos) are tucked
  HAT_AT: [0.27, 0.62],                     // tangled hard hats
  PREFILL: [10, 15, 21],                    // z of hazards already falling when the climb starts
  SNEEZES: true,
  TUTORIAL: false,     // true = the unfailable World 1-1 tutorial (see T_LEVELS.grandpa)
  EVENT: "sneeze",     // the hold-tight event: "sneeze" (Wizard, Lumberjack, Elf), "gust" (Mountain Man), "stomp" (Bigfoot),
                       // "hoof" (Rudolph), "roar" (Yeti: snow shaken loose), "laugh" (Santa: HO HO HO, every other one a reindeer swoop)
  STOMP_DROP: 0,       // hazards shaken loose per stomp / roar / laugh
  SWOOP_DROP: 2,       // presents dropped by Santa's reindeer swoop
  THROW_N: 0,          // hazard kinds the mouth throws (0 = all; Santa's 4th kind is the swooping reindeer)
  SLIP: 0,             // Ice Giant: rows/s Pip slides down when not climbing (x0.35 while holding)...
  SLIP_GRACE: 0.8,     // ...after this long without a tap
  MELT_S: 0,           // Ice Giant: the beard melts away after this many seconds (0 = no timer)
  MUSH: [], MUSH_UP: 2.5, EARN_GOLD: 3,            // Gnome: climb fractions of bouncy lucky mushrooms (touch = BOING! up 2.5 rows)
  GOLD_CHANCE: 0,      // Rumpelstiltskin: chance a falling straw bundle spins into a gold coin (grab it: +coins)
  NARROW: false,       // Rapunzel: columns 0 + 5 are the tower's stone wall (a 4-column braid)
  ROCK_COLS: 2,        // Dwarf King ("rockfall" event): columns marked, then boulders rattle down them fast
  DARK: null,          // Rudolph: [[from, to], ...] climb fractions that are dark (only a small light round Pip)
};
// ---------------------------------------------------------------- per-level tuning (merged over the Wizard's T above)
const T_LEVELS = {
  // World 1-1 GRANDPA = the tutorial. It can't be lost: hits never cost hearts, they only knock Pip down a bit.
  // Short beard, slow, sparse, gentle hazards that ramp a little; big prompts teach one control at a time.
  grandpa: {
    TUTORIAL: true,
    CLIMB_LENGTH: 1,              // Grandpa's own 22-row beard (was 16: ~1.5x the climb), not lengthened
    SHELTERS: false,              // no random shelters: the tutorial places exactly one (the "use a shelter" lesson)
    SHELTER_S: 4.0,               // ... and it lasts a little longer
    SNEEZES: false,
    KNOCK_HIT: 1.0,               // rows lost when bonked (no hearts lost, ever)
    INVULN_MS: 1200,
    THROW_SLOW: 4.2, THROW_FAST: 2.8,   // seconds between throws (Wizard: 2.4 / 1.0)
    FALL_SLOW: 2.0, FALL_FAST: 2.7,     // fall speed units/s (Wizard: 3.4 / 5.2)
    AIM: 0.3, AIM_TOP: 0.4,
    UPPER_THROW_K: 1, UPPER_FALL_K: 1, UPPER_PAIR: 0, DEF_BOOST_K: 1,
    HAT_THROW_CHANCE: 0.04,
    PAGES: 4,                     // Grandpa's family photos: 1 in the lesson + 3 tucked higher up
    PAGE_AT: [0.52, 0.7, 0.86],
    HAT_AT: [],                   // the only tangled hat is the lesson's
    PREFILL: [],
    TUT_CLIMB: 1.4,               // units climbed to pass the "alternate L/R" lesson
    TUT_ITEM_UP: 1.6,             // lesson items appear this far above Pip's hands
    TUT_TOP_S: 4.5,               // the "climb to Grandpa" prompt shows this long
    TUT_PARA_SLOW: 0.2,           // parachute sinks at x0.2 until the first steer
    ENDING_S: 6.6,
  },
  // ---- World 1 after the tutorial: difficulty ramps Goat < Lumberjack < Mountain Man < Bigfoot (boss) < Wizard (World 3).
  // Every one climbs its own Blender beard (CLIMB_LENGTH 1); the rows grow 24 -> 26 -> 28 -> 30.
  goat: {
    CLIMB_LENGTH: 1, SNEEZES: false,          // just above Grandpa: no sneezes, slow + sparse, hearts count again
    THROW_SLOW: 3.5, THROW_FAST: 2.1, FALL_SLOW: 2.4, FALL_FAST: 3.3, AIM: 0.34, AIM_TOP: 0.44,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1, UPPER_PAIR: 0,
    KNOCK_HIT: 1.6, SHELTER_MIN: 2, SHELTER_MAX: 2, HAT_THROW_CHANCE: 0.06,
    PAGES: 4, PAGE_AT: [0.2, 0.42, 0.64, 0.84], HAT_AT: [0.4], PREFILL: [],
    ENDING_S: 6.4,
  },
  lumberjack: {
    CLIMB_LENGTH: 1, SNEEZES: true, SNEEZE_FIRST: 12, SNEEZE_MIN: 14, SNEEZE_MAX: 20,
    THROW_SLOW: 3.4, THROW_FAST: 1.85, FALL_SLOW: 2.5, FALL_FAST: 3.5, AIM: 0.36, AIM_TOP: 0.46,
    UPPER_THROW_K: 0.92, UPPER_FALL_K: 1.03, UPPER_PAIR: 0.04,
    KNOCK_HIT: 1.7, PAGES: 5, PAGE_AT: [0.16, 0.36, 0.52, 0.7, 0.86], HAT_AT: [0.3, 0.64], PREFILL: [12],
    ENDING_S: 6.4,
  },
  mountain: {                                  // wind gusts: hold tight or get blown a column sideways
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "gust", SNEEZE_FIRST: 15, SNEEZE_MIN: 18, SNEEZE_MAX: 25, SNEEZE_WARN: 2.0,
    THROW_SLOW: 3.5, THROW_FAST: 1.9, FALL_SLOW: 2.4, FALL_FAST: 3.5, AIM: 0.35, AIM_TOP: 0.45,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.02,
    KNOCK_HIT: 1.6, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.28, 0.62], PREFILL: [12, 18],
    ENDING_S: 6.4,
  },
  bigfoot: {                                   // BOSS: he STOMPS - the fur shakes (hold!) and pinecones rain down
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "stomp", SNEEZE_FIRST: 8, SNEEZE_MIN: 9, SNEEZE_MAX: 13, SNEEZE_WARN: 2.2, SNEEZE_BLAST: 0.8,
    STOMP_DROP: 1,                             // pinecones shaken loose per stomp (fall from just above Pip)
    THROW_SLOW: 3.0, THROW_FAST: 1.5, FALL_SLOW: 2.75, FALL_FAST: 4.0, AIM: 0.39, AIM_TOP: 0.49,
    UPPER_THROW_K: 0.9, UPPER_FALL_K: 1.04, UPPER_PAIR: 0.06,
    KNOCK_HIT: 1.9, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.27, 0.6], PREFILL: [10, 16],
    ENDING_S: 6.6,
  },
};
// ---- World 2 North Pole: restarts a little below Bigfoot, then ramps Elf < Rudolph < Ice Giant < Yeti < Santa (boss, above Bigfoot).
Object.assign(T_LEVELS, {
  elf: {
    CLIMB_LENGTH: 1, SNEEZES: true, SNEEZE_FIRST: 13, SNEEZE_MIN: 15, SNEEZE_MAX: 21, SNEEZE_WARN: 1.8,
    THROW_SLOW: 3.4, THROW_FAST: 1.85, FALL_SLOW: 2.45, FALL_FAST: 3.5, AIM: 0.36, AIM_TOP: 0.46,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03,
    KNOCK_HIT: 1.6, PAGES: 5, PAGE_AT: [0.16, 0.36, 0.52, 0.7, 0.86], HAT_AT: [0.3, 0.64], PREFILL: [12],
    ENDING_S: 6.4,
  },
  rudolph: {                                   // dark stretches: only a small light round Pip (his nose isn't glowing!)
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "hoof", SNEEZE_FIRST: 13, SNEEZE_MIN: 15, SNEEZE_MAX: 21, SNEEZE_WARN: 2.0,
    THROW_SLOW: 3.35, THROW_FAST: 1.8, FALL_SLOW: 2.5, FALL_FAST: 3.6, AIM: 0.36, AIM_TOP: 0.46,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03, DARK: [[0.3, 0.48], [0.64, 0.82]],
    KNOCK_HIT: 1.65, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.28, 0.62], PREFILL: [12],
    ENDING_S: 6.4,
  },
  ice: {                                       // slippery (keep climbing!) + the beard melts: a gentle timer
    CLIMB_LENGTH: 1, SNEEZES: false, SLIP: 0.35, SLIP_GRACE: 0.8, MELT_S: 45,
    THROW_SLOW: 3.3, THROW_FAST: 1.8, FALL_SLOW: 2.5, FALL_FAST: 3.6, AIM: 0.36, AIM_TOP: 0.46,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03,
    KNOCK_HIT: 1.65, PAGES: 5, PAGE_AT: [0.16, 0.36, 0.52, 0.7, 0.86], HAT_AT: [0.3, 0.64], PREFILL: [12],
    ENDING_S: 6.4,
  },
  yeti: {                                      // ROAR: the fur shakes (hold!) and a snowball is shaken loose
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "roar", SNEEZE_FIRST: 14, SNEEZE_MIN: 15, SNEEZE_MAX: 20, SNEEZE_WARN: 2.2, SNEEZE_BLAST: 0.8,
    STOMP_DROP: 1,
    THROW_SLOW: 3.4, THROW_FAST: 1.85, FALL_SLOW: 2.45, FALL_FAST: 3.55, AIM: 0.36, AIM_TOP: 0.46,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03,
    KNOCK_HIT: 1.6, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.27, 0.6], PREFILL: [10, 16],
    ENDING_S: 6.4,
  },
  santa: {                                     // BOSS: HO HO HO belly laughs shake the beard (hold!); every other one is a reindeer swoop
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "laugh", SNEEZE_FIRST: 8, SNEEZE_MIN: 9, SNEEZE_MAX: 13, SNEEZE_WARN: 2.2, SNEEZE_BLAST: 0.9,
    STOMP_DROP: 0, SWOOP_DROP: 2, THROW_N: 3,
    THROW_SLOW: 2.95, THROW_FAST: 1.45, FALL_SLOW: 2.8, FALL_FAST: 4.1, AIM: 0.39, AIM_TOP: 0.49,
    UPPER_THROW_K: 0.9, UPPER_FALL_K: 1.04, UPPER_PAIR: 0.06,
    KNOCK_HIT: 1.9, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.27, 0.6], PREFILL: [10, 16],
    ENDING_S: 7.4,
  },
});
// ---- The Wizard (World 3 boss): close to his original tuning (a real step up), only trimmed so a good player clears him.
T_LEVELS.wizard = { THROW_SLOW: 3.1, THROW_FAST: 1.55, FALL_SLOW: 2.65, FALL_FAST: 3.9, AIM: 0.36, AIM_TOP: 0.46,
                    UPPER_THROW_K: 0.92, UPPER_FALL_K: 1.03, UPPER_PAIR: 0.04, KNOCK_HIT: 1.6 };
// ---- World 3 Fairy-Tale Forest: restarts a little below Santa, ramps Gnome < Rumpelstiltskin < Rapunzel < Dwarf King < Wizard (boss).
Object.assign(T_LEVELS, {
  gnome: {                                     // bouncy lucky mushrooms boost Pip up
    CLIMB_LENGTH: 1, SNEEZES: true, SNEEZE_FIRST: 14, SNEEZE_MIN: 16, SNEEZE_MAX: 22, SNEEZE_WARN: 1.9, MUSH: [0.22, 0.47, 0.7],
    THROW_SLOW: 3.35, THROW_FAST: 1.8, FALL_SLOW: 2.5, FALL_FAST: 3.6, AIM: 0.37, AIM_TOP: 0.47,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03,
    KNOCK_HIT: 1.65, PAGES: 5, PAGE_AT: [0.16, 0.36, 0.52, 0.76, 0.88], HAT_AT: [0.3, 0.64], PREFILL: [12],
    ENDING_S: 6.4,
  },
  rumpel: {                                    // straw spins into gold mid-fall: grab the gold for coins
    CLIMB_LENGTH: 1, SNEEZES: true, SNEEZE_FIRST: 13, SNEEZE_MIN: 15, SNEEZE_MAX: 21, SNEEZE_WARN: 1.9, GOLD_CHANCE: 0.3,
    THROW_SLOW: 3.1, THROW_FAST: 1.6, FALL_SLOW: 2.65, FALL_FAST: 3.85, AIM: 0.38, AIM_TOP: 0.48,
    UPPER_THROW_K: 0.95, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.03,
    KNOCK_HIT: 1.65, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.28, 0.62], PREFILL: [12],
    ENDING_S: 6.4,
  },
  rapunzel: {                                  // a narrow braid up the tower: stone walls either side, nowhere to hide
    CLIMB_LENGTH: 1, SNEEZES: false, NARROW: true,
    THROW_SLOW: 3.5, THROW_FAST: 1.95, FALL_SLOW: 2.4, FALL_FAST: 3.45, AIM: 0.33, AIM_TOP: 0.42,
    UPPER_THROW_K: 0.96, UPPER_FALL_K: 1.02, UPPER_PAIR: 0.0,
    KNOCK_HIT: 1.6, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.28, 0.62], PREFILL: [12],
    ENDING_S: 6.4,
  },
  dwarf: {                                     // ROCKFALL: two columns are marked, then boulders rattle down them - move!
    CLIMB_LENGTH: 1, SNEEZES: true, EVENT: "rockfall", SNEEZE_FIRST: 10, SNEEZE_MIN: 12, SNEEZE_MAX: 17, SNEEZE_WARN: 2.0, SNEEZE_BLAST: 0.6,
    THROW_SLOW: 2.55, THROW_FAST: 1.25, FALL_SLOW: 3.0, FALL_FAST: 4.5, AIM: 0.44, AIM_TOP: 0.54,
    UPPER_THROW_K: 0.88, UPPER_FALL_K: 1.05, UPPER_PAIR: 0.08,
    KNOCK_HIT: 2.2, PAGES: 5, PAGE_AT: [0.15, 0.35, 0.5, 0.69, 0.85], HAT_AT: [0.27, 0.6], PREFILL: [10, 16],
    ENDING_S: 6.4,
  },
});
const T_BASE = JSON.parse(JSON.stringify(T));
const LEN_PARAM = params.get("len") ? Math.max(1, Math.min(3, +params.get("len") || 1)) : 0;   // ?len=1 = original beard (tests / tuning)
// ---------------------------------------------------------------- longer climb: repeat a band of beard rows
// The Blender level is 26 rows; T.CLIMB_LENGTH x the climb height is made by inserting copies of rows
// LEN_BAND[0]..LEN_BAND[1]-1 above row LEN_BAND[1] (tile map + background image). The face, mouth and the
// street stay where they are, so every z-based thing (ROWS, TOP, GOAL_Z...) just grows.
// ---------------------------------------------------------------- levels: per-level data swapped into A / F / IMG
// The Wizard's data is the top level of ASSETS; other playable levels are in A.levels (atlas sprites "<id>/...").
const LV = { wizard: {} };
for (const k of ["level", "title", "start_x", "start_z", "rows", "top", "x_left", "level_h", "tilemap", "col_min_z", "hazard_names",
                 "colors", "bg", "mouth", "mouth_y", "mouth_h", "face_smile", "face_sleep", "face_y"]) LV.wizard[k] = A[k];
Object.assign(LV, A.levels || {});
const LEVEL_NAMES = { grandpa: "1-1  GRANDPA", goat: "1-2  THE GOAT", lumberjack: "1-3  THE LUMBERJACK", mountain: "1-4  MOUNTAIN MAN",
                      bigfoot: "1-5  BIGFOOT (BOSS)", elf: "2-1  THE ELF", rudolph: "2-2  RUDOLPH", ice: "2-3  THE ICE GIANT",
                      yeti: "2-4  THE YETI", santa: "2-5  SANTA (BOSS)", gnome: "3-1  THE GARDEN GNOME", rumpel: "3-2  RUMPELSTILTSKIN",
                      rapunzel: "3-3  RAPUNZEL", dwarf: "3-4  THE DWARF KING", wizard: "3-5  THE WIZARD (BOSS)" };
let NOSE_Z = 0;
let LEVEL = "wizard", ROWS, TOP, ORIG, EXTRA_ROWS, START_X, START_Z, GOAL_Z, MOUTH_Z, MOUTH_X, BOTTOM_Z, BOOK_AT, CAT_AT, ZZZ_AT, HAND_AT;
let BGX = null;                               // the lengthened background (built once the image has loaded)
const LEVEL_FRAMES = {};                      // level id -> {plain sprite name: frame}
function levelFrames(id) {
  if (LEVEL_FRAMES[id]) return LEVEL_FRAMES[id];
  const out = {}, pre = id + "/";
  for (const k in A.frames) {
    if (id === "wizard" && /^(haz\d|mini_haz|tile_)/.test(k)) out[k] = A.frames[k];
    else if (k.startsWith(pre)) out[k.slice(pre.length)] = A.frames[k];
  }
  return (LEVEL_FRAMES[id] = out);
}
for (const k in levelFrames("wizard")) A.frames["wizard/" + k] = A.frames[k];   // the cinematic always uses the Wizard's
/** Switch the playable level: data, sprites, images, tuning (T_LEVELS[id] over the Wizard's T) and every z constant. */
// ---- Easy mode (Settings / first launch; localStorage bc_easy): slower + fewer hazards, gentler knocks, longer
// warnings, slower slides. Applies to every level; coins are a little lower (EASY_COIN_K) to keep the shop fair.
let easy = params.get("easy") ? params.get("easy") === "1" : localStorage.getItem("bc_easy") === "1";
const EASY_COIN_K = 0.8;
function applyEasy() {
  const k = (n, f) => { if (typeof T[n] === "number") T[n] *= f; };
  k("THROW_SLOW", 1.35); k("THROW_FAST", 1.45); k("FALL_SLOW", 0.78); k("FALL_FAST", 0.75);
  k("AIM", 0.7); k("AIM_TOP", 0.7); k("UPPER_PAIR", 0); k("KNOCK_HIT", 0.55); k("KNOCK_SNEEZE", 0.55);
  k("SNEEZE_WARN", 1.35); k("SNEEZE_MIN", 1.3); k("SNEEZE_MAX", 1.3); k("SLIP", 0.5); k("MELT_S", 1.4);
  k("INVULN_MS", 1.4); k("HAT_THROW_CHANCE", 1.6); k("STOMP_DROP", 0.5); T.STOMP_DROP = Math.round(T.STOMP_DROP || 0);
  T.UPPER_THROW_K = Math.max(T.UPPER_THROW_K, 1); T.EASY = true;
}
function setEasy(v) {
  easy = !!v; localStorage.setItem("bc_easy", easy ? "1" : "0");
  if (screen !== "play") loadLevel(LEVEL);
}
function loadLevel(id) {
  if (!LV[id]) id = "wizard";
  LEVEL = id;
  const d = LV[id], keep = JSON.parse(JSON.stringify(T_BASE));
  for (const k in T) delete T[k];
  Object.assign(T, keep, T_LEVELS[id] || {});
  if (LEN_PARAM) T.CLIMB_LENGTH = LEN_PARAM;
  if (easy) applyEasy();
  for (const k of ["start_x", "start_z", "rows", "top", "x_left", "level_h", "col_min_z", "hazard_names", "mouth_y", "mouth_h", "face_y", "title"]) A[k] = d[k];
  A.tilemap = d.tilemap.map((r) => r.slice());
  LC = d.colors || C; XL = d.x_left;
  Object.assign(F, levelFrames(id));
  if (IMGL[id]) Object.assign(IMG, IMGL[id]);
  // ---- longer climb: repeat a band of beard rows
  // T.CLIMB_LENGTH x the climb height is made by inserting copies of rows LEN_BAND[0]..LEN_BAND[1]-1 above row
  // LEN_BAND[1] (tile map + background image). The face, mouth and the street stay where they are, so every
  // z-based thing (ROWS, TOP, GOAL_Z...) just grows.
  ORIG = { rows: A.rows, top: A.top, level_h: A.level_h };
  EXTRA_ROWS = Math.max(0, Math.round((A.rows - 2.25 - A.start_z) * (T.CLIMB_LENGTH - 1)));
  {
    const [b0, b1] = T.LEN_BAND, band = A.tilemap.slice(b0, b1), ins = [];
    for (let i = 0; i < EXTRA_ROWS; i++) ins.push(band[i % band.length].slice());
    A.tilemap = A.tilemap.slice(0, b1).concat(ins, A.tilemap.slice(b1));
    A.rows += EXTRA_ROWS; A.top += EXTRA_ROWS; A.level_h += EXTRA_ROWS * P;
  }
  if (T.NARROW) for (const r of A.tilemap) { r[0] = "sparse"; r[COLS - 1] = "sparse"; }   // Rapunzel: tower wall
  ROWS = A.rows; TOP = A.top; BGX = null; tangleImg = null;
  START_X = Math.floor(A.start_x) + 0.5; START_Z = A.start_z;
  GOAL_Z = ROWS - 2.25;                     // hands reach the chin / mouth
  MOUTH_Z = TOP - (A.mouth_y + A.mouth_h / 2) / P;   // centre of the open-mouth band
  MOUTH_X = XL + W / 2 / P;
  BOTTOM_Z = TOP - A.level_h / P;           // lowest z of the level image
  BOOK_AT = { x: 1.55, z: ROWS - 0.3 }; CAT_AT = { x: 4.45, z: ROWS - 0.42 };   // tucked into the beard (ending)
  ZZZ_AT = { x: 4.3, z: ROWS + 2.6 };
  HAND_AT = { x: 5.05, z: ROWS + 0.15 };    // Grandpa's waving hand (bottom of the sprite)
  NOSE_Z = MOUTH_Z + 1.45;                  // Rudolph's nose (ending glow)
  face = "normal";
  setSides();
}
function levelImage() {
  if (BGX) return BGX;
  const c = document.createElement("canvas"); c.width = W; c.height = A.level_h;
  const g = c.getContext("2d"), yo = (z) => Math.round((ORIG.top - z) * P), [b0, b1] = T.LEN_BAND, n = b1 - b0;
  if (!EXTRA_ROWS) { g.drawImage(IMG.bg, 0, 0); return (BGX = c); }
  const ySplit = yo(b1), e = EXTRA_ROWS * P;
  g.drawImage(IMG.bg, 0, 0, W, ySplit, 0, 0, W, ySplit);                                   // face .. row b1
  g.drawImage(IMG.bg, 0, ySplit, W, ORIG.level_h - ySplit, 0, ySplit + e, W, ORIG.level_h - ySplit);   // row b1-1 .. street
  for (let i = 0; i < EXTRA_ROWS; i++) {                                                    // inserted rows, top first
    const v = EXTRA_ROWS - 1 - i, src = b0 + (v % n);
    g.drawImage(IMG.bg, 0, yo(src + 1), W, P, 0, ySplit + i * P, W, P);
  }
  return (BGX = c);
}
const GROUND_Z = -0.45;                     // Whiskerton's street, under the beard tip

// ---------------------------------------------------------------- canvas + integer scaling
const cv = document.getElementById("game"), wrap = document.getElementById("wrap");
const ctx = cv.getContext("2d");
let H = 256, scale = 1;
/** Integer-scaled portrait play area, centred. Phones: fills the width. Desktop / tablet landscape: the height
 *  decides (k = largest integer that fits BOTH ways), the canvas grows taller up to 420 native px, and the side
 *  bars show a themed pixel pattern (setSides) instead of black. */
function resize() {
  const dpr = window.devicePixelRatio || 1;
  const aw = wrap.clientWidth * dpr, ah = wrap.clientHeight * dpr;   // device pixels inside safe area
  const k = Math.max(1, Math.min(Math.floor(aw / W), Math.floor(ah / 256)));
  H = Math.max(256, Math.min(420, Math.floor(ah / k)));
  scale = k;
  cv.width = W; cv.height = H;
  cv.style.width = (W * k / dpr) + "px";
  cv.style.height = (H * k / dpr) + "px";
  ctx.imageSmoothingEnabled = false;
  setSides();
}
let sidesKey = "";
const W2 = ["elf", "rudolph", "ice", "yeti", "santa"];
const W3 = ["gnome", "rumpel", "rapunzel", "dwarf"];
/** Letterbox bars: a 32x32 pixel tile drawn at the game's pixel scale - pine woods (World 1) or a starry night (Wizard). */
function setSides() {
  if (!cv) return;
  const dpr = window.devicePixelRatio || 1, key = LEVEL + ":" + scale + ":" + dpr;
  if (key === sidesKey) return; sidesKey = key;
  const c = document.createElement("canvas"); c.width = c.height = 32;
  const g = c.getContext("2d"), px = (x, y, w, h, col) => { g.fillStyle = col; g.fillRect(x, y, w, h); };
  let base;
  if (W3.includes(LEVEL)) {                  // World 3: enchanted forest - dark trees, toadstools, fireflies
    base = "#1a1430"; px(0, 0, 32, 32, base);
    const tree = (x0, y0, h, col) => { for (let j = 0; j < h; j++) { const w = 3 + Math.floor(j * 0.5) * 2; px(x0 - (w >> 1), y0 + j, w, 1, col); } px(x0, y0 + h, 2, 3, "#2c1c24"); };
    tree(8, 2, 10, "#24304a"); tree(24, 14, 10, "#2a2450");
    px(3, 28, 5, 2, "#d83838"); px(5, 30, 1, 2, "#f0e0c0"); px(4, 28, 1, 1, "#f8f8f8"); px(6, 29, 1, 1, "#f8f8f8");   // toadstool
    px(19, 26, 4, 2, "#a050d0"); px(20, 28, 1, 2, "#f0e0c0");
    [[14, 9], [29, 4], [11, 22], [27, 27]].forEach(([x, y]) => px(x, y, 1, 1, "#e8f070"));
  } else if (W2.includes(LEVEL)) {                  // World 2: snowy pines + falling flakes
    base = "#101c34"; px(0, 0, 32, 32, base);
    const tree = (x0, y0, h) => {
      for (let j = 0; j < h; j++) { const w = 1 + Math.floor(j * 0.6) * 2; px(x0 - (w >> 1), y0 + j, w, 1, j % 3 === 0 ? "#d8e4f0" : "#1c3a3c"); }
      px(x0, y0 + h, 1, 2, "#2c2420");
    };
    tree(8, 4, 11); tree(24, 16, 11); tree(0, 19, 9); tree(32, 19, 9);
    px(0, 30, 32, 2, "#c8d8ec");
    [[15, 3], [3, 12], [28, 6], [19, 25], [12, 20], [27, 29]].forEach(([x, y], i) => px(x, y, 1, 1, i % 2 ? "#f8f8f8" : "#a8c0e0"));
  } else if (LEVEL === "wizard") {
    base = "#120c30"; px(0, 0, 32, 32, base);
    [[3, 4], [19, 2], [11, 13], [27, 17], [6, 24], [22, 27], [15, 21]].forEach(([x, y], i) => px(x, y, 1, 1, i % 3 ? "#6060a0" : "#c0c0e8"));
    px(26, 6, 1, 3, "#9890d0"); px(25, 7, 3, 1, "#9890d0");
  } else {
    base = "#0c2014"; px(0, 0, 32, 32, base);
    const tree = (x0, y0, h, col, trunk) => {
      for (let j = 0; j < h; j++) { const w = 1 + Math.floor(j * 0.6) * 2; px(x0 - (w >> 1), y0 + j, w, 1, col); }
      px(x0, y0 + h, 1, 2, trunk);
    };
    tree(8, 3, 11, "#163a20", "#2c2018"); tree(24, 15, 11, "#1a4426", "#2c2018"); tree(0, 18, 9, "#12301a", "#2c2018"); tree(32, 18, 9, "#12301a", "#2c2018");
    [[15, 6], [3, 29], [28, 4], [18, 29]].forEach(([x, y]) => px(x, y, 1, 1, "#3c7040"));
  }
  const st = document.body.style, sz = (32 * scale / dpr) + "px";
  st.backgroundColor = base; st.backgroundImage = "url(" + c.toDataURL() + ")";
  st.backgroundSize = sz + " " + sz; st.backgroundRepeat = "repeat"; st.imageRendering = "pixelated";
  st.backgroundPosition = "center top";
}
window.addEventListener("resize", resize);
window.addEventListener("orientationchange", () => setTimeout(resize, 200));

// ---------------------------------------------------------------- images
function loadImg(src) { const i = new Image(); i.src = src; return i; }
const IMGL = {};                             // per-level images (all decoded up front)
const levelImgs = (d) => ({ bg: loadImg(d.bg), mouth: loadImg(d.mouth), smile: loadImg(d.face_smile), sleep: loadImg(d.face_sleep) });
for (const id in LV) IMGL[id] = levelImgs(LV[id]);
// ---- world packs (World 2+): assets/world<N>.js, loaded on demand with a same-origin <script> (works from file://).
// The pack calls window.BC_PACK({world, levels, atlas, frames}); its sprites carry their own atlas image (frame[6]).
const WORLD_OF = A.world_of || {};
const Packs = {};                             // world -> { state: "loading" | "ready" | "error", cbs: [] }
const known = (id) => !!(LV[id] || WORLD_OF[id]);
window.BC_PACK = (p) => {
  const atl = loadImg(p.atlas), imgs = [atl];
  for (const k in p.frames) A.frames[k] = p.frames[k].slice(0, 6).concat([atl]);
  for (const id in p.levels) { LV[id] = p.levels[id]; IMGL[id] = levelImgs(LV[id]); imgs.push(...Object.values(IMGL[id])); }
  const pk = Packs[p.world] || (Packs[p.world] = { cbs: [] });
  Promise.all(imgs.map((i) => (i.decode ? i.decode().catch(() => {}) : null))).then(() => {
    pk.state = "ready"; const cbs = pk.cbs; pk.cbs = []; cbs.forEach((f) => f(true));
  });
};
/** Make sure a level's data is here (World 1 / Wizard: always; later worlds: load their pack once), then cb(ok). */
function ensureWorld(id, cb) {
  const w = WORLD_OF[id];
  if (!w || LV[id] && (!Packs[w] || Packs[w].state === "ready")) { cb(true); return; }
  const pk = Packs[w] || (Packs[w] = { cbs: [] });
  pk.cbs.push(cb);
  if (pk.state === "loading") return;
  pk.state = "loading";
  const sc = document.createElement("script");
  sc.src = "assets/world" + w + ".js";
  sc.onerror = () => { pk.state = "error"; const cbs = pk.cbs; pk.cbs = []; cbs.forEach((f) => f(false)); };
  document.head.appendChild(sc);
}
function prefetchWorlds() { for (const id in WORLD_OF) if (isUnlocked(id)) ensureWorld(id, () => {}); }
let loadingUntil = 0, levelRequest = 0, loadError = null;
function cancelLevelLoad() { levelRequest++; loadingUntil = 0; }
function goLevel(id, then) {
  const request = ++levelRequest;
  if (window.BC) BC.ready = true;             // explicit navigation supersedes a pending startup selection
  loadingUntil = 0; loadError = null;
  if (LV[id] && (!WORLD_OF[id] || (Packs[WORLD_OF[id]] || {}).state === "ready")) { loadLevel(id); then(); return; }
  loadingUntil = now + 1e9;
  ensureWorld(id, (ok) => {
    if (request !== levelRequest) return;      // a newer choice or navigation owns the screen now
    loadingUntil = 0;
    if (!ok) { loadError = { t: now, lines: ["COULD NOT LOAD THIS WORLD", "PLEASE TRY AGAIN"] }; return; }
    loadLevel(id); then();
  });
}
const IMG = { atlas: loadImg(A.atlas), pip: loadImg(A.pip), giants: loadImg(A.giant_img),
              wbg: IMGL.wizard.bg, wmouth: IMGL.wizard.mouth, gbg: (IMGL.grandpa || IMGL.wizard).bg };
Object.assign(IMG, IMGL.wizard);
const F = A.frames;   // name -> [x, y, w, h, anchorX, anchorY]
function spr(name, x, y, alpha) {
  const f = F[name]; if (!f) return;
  if (alpha !== undefined) ctx.globalAlpha = alpha;
  ctx.drawImage(f[6] || IMG.atlas, f[0], f[1], f[2], f[3], Math.round(x - f[4]), Math.round(y - f[5]), f[2], f[3]);
  if (alpha !== undefined) ctx.globalAlpha = 1;
}

// ---------------------------------------------------------------- 5x7 pixel font (port of pixfont.py)
const GLYPH = {};
for (const ch in A.font) GLYPH[ch] = A.font[ch].split(" ");
function textW(s, k = 1) { return s.length * 6 * k - k; }
function outlined(s, x, y, col) {           // readable on any beard colour (the Goat's is white): 1 px dark outline
  for (const [dx, dy] of [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[1,-1],[-1,1],[1,1],[0,2],[1,2]]) text(s, x + dx, y + dy, "#1a1020", 1, null);
  text(s, x, y, col, 1, null);
}
function text(s, x, y, col, k = 1, shadow = "#000") {
  s = String(s).toUpperCase().replace(/X/g, "X");
  if (shadow) drawStr(s, x + k, y + k, shadow, k);
  drawStr(s, x, y, col, k);
}
function drawStr(s, x, y, col, k) {
  ctx.fillStyle = col;
  for (let i = 0; i < s.length; i++) {
    const g = GLYPH[s[i]] || GLYPH["?"];
    if (s[i] === " ") continue;
    for (let r = 0; r < 7; r++) for (let c = 0; c < 5; c++)
      if (g[r][c] === "1") ctx.fillRect(x + (i * 6 + c) * k, y + r * k, k, k);
  }
}
function textC(s, y, col, k = 1, shadow) { text(s, Math.round((W - textW(s, k)) / 2), y, col, k, shadow); }

// ---------------------------------------------------------------- audio (WebAudio, unlocked on first gesture)
const Snd = {
  ctx: null, buf: {}, muted: localStorage.getItem("bc_mute") === "1",
  unlock() {
    if (this.ctx) { if (this.ctx.state === "suspended") this.ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    const c = this.ctx = new AC();
    const s = c.createBufferSource(); s.buffer = c.createBuffer(1, 1, 22050); s.connect(c.destination); s.start(0);
    this.master = c.createGain(); this.master.gain.value = this.muted ? 0 : 0.8; this.master.connect(c.destination);
    for (const k in A.sfx) {
      const b64 = A.sfx[k].split(",")[1], bin = atob(b64), u = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
      c.decodeAudioData(u.buffer, (b) => { this.buf[k] = b; }, () => {});
    }
  },
  play(k, vol = 1) {                      // one of the embedded WAVs
    if (!this.ctx || !this.buf[k]) return;
    const s = this.ctx.createBufferSource(), g = this.ctx.createGain();
    s.buffer = this.buf[k]; g.gain.value = vol; s.connect(g); g.connect(this.master); s.start();
  },
  tone(freq, dur, vol = 0.12, type = "square", slideTo, delay = 0) {   // tiny synth for UI blips
    if (!this.ctx) return;
    const c = this.ctx, t = c.currentTime + delay, o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.001, t + dur);
    o.connect(g); g.connect(this.master); o.start(t); o.stop(t + dur + 0.02);
  },
  noise(dur, vol = 0.2, freq = 1200, delay = 0) {
    if (!this.ctx) return;
    const c = this.ctx, n = Math.floor(c.sampleRate * dur), b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n);
    const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain();
    f.type = "bandpass"; f.frequency.value = freq; g.gain.value = vol;
    s.buffer = b; s.connect(f); f.connect(g); g.connect(this.master); s.start(c.currentTime + delay);
  },
  toggle() {
    this.muted = !this.muted; localStorage.setItem("bc_mute", this.muted ? "1" : "0");
    if (this.master) this.master.gain.value = this.muted ? 0 : 0.8;
  },
};
const sfx = {
  reach: () => Snd.tone(660 + Math.random() * 60, 0.03, 0.05),
  slip: () => Snd.tone(220, 0.15, 0.12, "square", 110),
  dyno: () => { Snd.noise(0.18, 0.25, 900); Snd.tone(300, 0.16, 0.06, "square", 900); },
  brace: () => Snd.tone(150, 0.08, 0.12),
  block: () => { Snd.play("clink", 0.7); Snd.tone(1200, 0.05, 0.05); },
  warn: () => { Snd.tone(880, 0.08, 0.08); Snd.tone(660, 0.08, 0.08, "square", null, 0.12); },
  sneeze: () => { Snd.noise(0.6, 0.5, 600); Snd.tone(400, 0.4, 0.08, "sawtooth", 80); },
  held: () => { Snd.tone(523, 0.07, 0.07); Snd.tone(784, 0.1, 0.07, "square", null, 0.07); },
  win: () => [523, 659, 784, 1047, 784, 1047].forEach((f, i) => Snd.tone(f, 0.14, 0.09, "square", null, i * 0.11)),
  over: () => [392, 330, 262, 196].forEach((f, i) => Snd.tone(f, 0.22, 0.09, "square", null, i * 0.2)),
  crowd: (n = 8) => { for (let i = 0; i < n; i++) { const d = i * 0.08 + Math.random() * 0.06;
    Snd.noise(0.22, 0.05, 1300 + Math.random() * 1000, d); Snd.tone(480 + Math.random() * 320, 0.16, 0.025, "triangle", 900 + Math.random() * 500, d + 0.04); } },
  page: () => [880, 1175, 1568].forEach((f, i) => Snd.tone(f, 0.07, 0.06, "triangle", null, i * 0.06)),
  coin: () => { Snd.tone(988, 0.05, 0.06); Snd.tone(1319, 0.1, 0.06, "square", null, 0.05); },
  star: () => [1047, 1319, 1568, 2093].forEach((f, i) => Snd.tone(f, 0.08, 0.06, "square", null, i * 0.05)),
  pop: () => { Snd.noise(0.12, 0.2, 2200); Snd.tone(700, 0.08, 0.06, "square", 1400); },
  toss: () => { Snd.tone(500, 0.12, 0.05, "square", 200); },
  hmph: () => { Snd.tone(196, 0.18, 0.09, "sawtooth", 165); Snd.tone(175, 0.3, 0.09, "sawtooth", 131, 0.2); },
  eek: () => { Snd.tone(1300, 0.08, 0.04, "square", 1800); Snd.tone(1500, 0.08, 0.04, "square", 2000, 0.1); },
  yawn: () => { Snd.tone(330, 0.9, 0.06, "triangle", 150); Snd.noise(0.8, 0.04, 500); },
  lullaby: () => [659, 587, 523, 587, 659, 659, 659].forEach((f, i) => Snd.tone(f, 0.32, 0.05, "triangle", null, i * 0.3)),
  tweet: () => { Snd.tone(2000, 0.07, 0.04, "sine", 2700); Snd.tone(2200, 0.09, 0.04, "sine", 3000, 0.11); },
  flap: () => Snd.noise(0.09, 0.08, 700),
  whoosh: () => Snd.noise(0.5, 0.12, 500),
  jingle: () => [523, 659, 784, 659, 880, 784].forEach((f, i) => Snd.tone(f, 0.16, 0.06, "triangle", null, i * 0.14)),
  toot: () => { Snd.tone(220, 0.15, 0.06, "sawtooth", 200); Snd.noise(0.3, 0.06, 300, 0.15); },
  ring: () => { for (let i = 0; i < 8; i++) Snd.tone(i % 2 ? 1175 : 1480, 0.05, 0.045, "square", null, i * 0.06); },
  laugh: () => [392, 440, 392, 494, 440, 523].forEach((f, i) => Snd.tone(f, 0.1, 0.07, "triangle", f * 0.9, i * 0.13)),
  stomp: () => { Snd.tone(70, 0.35, 0.16, "sawtooth", 40); Snd.noise(0.3, 0.12, 200); },
  munch: () => { for (let i = 0; i < 3; i++) Snd.noise(0.07, 0.07, 1800, i * 0.18); },
  flash: () => { Snd.tone(2400, 0.05, 0.05, "square"); Snd.noise(0.12, 0.06, 4000, 0.03); },
  hoho: () => [196, 175, 196, 175, 196, 147].forEach((f, i) => Snd.tone(f, 0.16, 0.09, "square", f * 0.85, i * 0.17)),
  jig: () => [784, 988, 1175, 988, 784, 988, 1175, 1568].forEach((f, i) => Snd.tone(f, 0.08, 0.05, "square", null, i * 0.1)),
  glow: () => [523, 784, 1047, 1568].forEach((f, i) => Snd.tone(f, 0.25, 0.05, "sine", null, i * 0.09)),
  roar: () => { Snd.tone(110, 0.5, 0.14, "sawtooth", 70); Snd.noise(0.45, 0.1, 400); },
  bleat: () => { Snd.tone(330, 0.5, 0.07, "sawtooth", 300); Snd.tone(345, 0.5, 0.03, "square", 310); },
};
// ---------------------------------------------------------------- per-level story bits
// item = what Pip packs and carries up; eat = it goes in his mouth (else it's tucked into the beard);
// page/pageSpr = the level's collectible (in place of the Wizard's pages); next = the giant the bird flies Pip to.
const STORIES = {
  wizard: { name: "THE WIZARD", short: "WIZARD", page: "PAGE", pages: "PAGES", pageSpr: "page", plus: "LOST PAGE", happy: "THE WIZARD IS HAPPY AGAIN", item: "book" },
  grandpa: { name: "GRANDPA", short: "GRANDPA", page: "PHOTO", pages: "PHOTOS", pageSpr: "photo", plus: "FAMILY PHOTO", happy: "GRANDPA IS HAPPY AGAIN", item: "phone",
    intro: [["GRANDPA IS GRUMPY...", "THE GRANDKIDS HAVEN'T CALLED!"], ["TAKE HIM THIS TOY PHONE, PIP!", "THE GRANDKIDS ARE ON THE LINE!"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "HERE, GRANDPA - IT'S FOR YOU!"], [1.5, "RING! RING!"], [2.3, "IT'S THE GRANDKIDS!"],
           [3.4, "GRANDPA IS BEAMING!"], [4.7, "HEH HEH! HELLO, MY DEARS!"]], shout: "HEH HEH!", next: "goat" },
  goat: { name: "THE GOAT", short: "GOAT", page: "CLOVER", pages: "CLOVERS", pageSpr: "clover", plus: "LUCKY CLOVER", happy: "THE GOAT IS HAPPY AGAIN", item: "turnip", eat: true,
    intro: [["THE GOAT IS GRUMPY...", "HIS TURNIP PATCH IS BARE!"], ["TAKE HIM THIS BIG TURNIP, PIP!", "(GOATS LOVE TURNIPS)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "A BIG TURNIP, JUST FOR YOU!"], [1.6, "MUNCH... MUNCH... MUNCH..."], [3.4, "THE GOAT IS SO HAPPY!"],
           [4.7, "MEHHH-HEH-HEH!"]], shout: "MEHHH!", next: "lumberjack" },
  lumberjack: { name: "THE LUMBERJACK", short: "LUMBERJACK", page: "MAPLE LEAF", pages: "LEAVES", pageSpr: "leaf", plus: "MAPLE LEAF", happy: "THE LUMBERJACK IS HAPPY AGAIN", item: "stack", eat: true,
    intro: [["THE LUMBERJACK IS GRUMPY...", "HE HASN'T HAD HIS BREAKFAST!"], ["TAKE HIM THESE PANCAKES, PIP!", "(EXTRA SYRUP!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "BREAKFAST IS SERVED!"], [1.6, "CHOMP! CHOMP! GULP!"], [3.4, "WHAT A BIG BELLY LAUGH!"],
           [4.7, "HO HO! BEST PANCAKES EVER!"]], shout: "HAW HAW!", next: "mountain" },
  mountain: { name: "MOUNTAIN MAN", short: "MOUNTAIN", page: "FEATHER", pages: "FEATHERS", pageSpr: "feather", plus: "FEATHER", happy: "MOUNTAIN MAN IS HAPPY AGAIN", item: "compass",
    intro: [["MOUNTAIN MAN IS GRUMPY...", "HE LOST HIS TRUSTY COMPASS!"], ["YOU FOUND IT, PIP!", "TAKE IT BACK - MIND THE WIND!"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "HERE'S YOUR COMPASS!"], [1.6, "IT STILL POINTS NORTH!"], [3.4, "MOUNTAIN MAN IS BEAMING!"],
           [4.7, "HAR HAR! THANK YE, PIP!"]], shout: "HAR HAR!", next: "bigfoot" },
  bigfoot: { name: "BIGFOOT", short: "BIGFOOT", page: "BERRY BUNCH", pages: "BERRIES", pageSpr: "berries", plus: "BERRY BUNCH", happy: "BIGFOOT HAS A FRIEND NOW", item: "selfie", selfie: true,
    intro: [["BIGFOOT IS GRUMPY...", "NOBODY EVER STAYS TO SAY HI!"], ["BE HIS FRIEND, PIP!", "TAKE A SELFIE TOGETHER!"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "HI, BIGFOOT! SAY CHEESE!"], [2.4, "*CLICK!*"], [3.4, "BIGFOOT GRINS!"],
           [4.7, "BEST FRIENDS FOREVER!"]], shout: "HOO HOO!", next: "elf" },
  elf: { name: "THE ELF", short: "ELF", page: "GINGERBREAD", pages: "GINGERBREADS", pageSpr: "gingerbread", plus: "GINGERBREAD FRIEND", happy: "THE ELF IS HAPPY AGAIN", item: "hammer", jig: true,
    intro: [["THE ELF IS GRUMPY...", "THE TOY WORKSHOP IS BEHIND!"], ["YOU FOUND HIS LOST HAMMER, PIP!", "TAKE IT UP TO HIM!"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "HERE'S YOUR TOY HAMMER!"], [1.6, "TAP-TAP-TAP! TOYS DONE!"], [3.4, "THE ELF DOES A HAPPY JIG!"],
           [4.7, "TEE-HEE! THANK YOU, PIP!"]], shout: "TEE-HEE!", next: "rudolph" },
  rudolph: { name: "RUDOLPH", short: "RUDOLPH", page: "STAR", pages: "STARS", pageSpr: "star", plus: "GOLD STAR", happy: "RUDOLPH IS GLOWING AGAIN", item: "lantern", glow: true,
    intro: [["RUDOLPH IS SAD...", "HIS NOSE HAS STOPPED GLOWING!"], ["TAKE HIM THIS WARM LANTERN, PIP!", "(IT'S DARK UP THERE!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "A LITTLE GLOW, JUST FOR YOU!"], [1.6, "AND A BIG WARM HUG!"], [3.4, "HIS NOSE LIGHTS UP!"],
           [4.7, "RUDOLPH IS SHINING BRIGHT!"]], shout: "HEE-HAW-HO!", next: "ice" },
  ice: { name: "THE ICE GIANT", short: "ICE GIANT", page: "SNOWFLAKE", pages: "SNOWFLAKES", pageSpr: "snowflake", plus: "SNOWFLAKE", happy: "THE ICE GIANT IS WARM AGAIN", item: "mitten",
    intro: [["THE ICE GIANT IS GRUMPY...", "HE'S COLD AND LONELY!"], ["TAKE HIM THIS WARM MITTEN, PIP!", "HURRY - HIS BEARD IS MELTING!"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "A COSY MITTEN FOR YOU!"], [1.6, "NICE AND WARM!"], [3.4, "THE ICE GIANT IS BEAMING!"],
           [4.7, "BRRR-HA-HA! THANK YOU!"]], shout: "BRRR-HA!", next: "yeti" },
  yeti: { name: "THE YETI", short: "YETI", page: "ICE CRYSTAL", pages: "CRYSTALS", pageSpr: "crystal", plus: "ICE CRYSTAL", happy: "THE YETI IS HAPPY AGAIN", item: "cocoa",
    intro: [["THE YETI IS GRUMPY...", "HIS COCOA RAN OUT!"], ["TAKE HIM COCOA AND A SCARF, PIP!", "(MIND THE ROARS!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "HOT COCOA + A COSY SCARF!"], [1.6, "THE YETI HUGS IT TIGHT!"], [3.4, "THE YETI IS SO HAPPY!"],
           [4.7, "ROOO-HOO-HOO!"]], shout: "ROO-HOO!", next: "santa" },
  santa: { name: "SANTA", short: "SANTA", page: "LETTER", pages: "LETTERS", pageSpr: "letter", plus: "LETTER TO SANTA", happy: "SANTA IS FAST ASLEEP", item: "cookie", eat: true, sleep: true,
    intro: [["SANTA IS GRUMPY...", "HE'S HUNGRY AND UP PAST BEDTIME!"], ["TAKE HIM THIS BIG COOKIE, PIP!", "(WATCH OUT FOR THE REINDEER!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "ONE BIG COOKIE - CATCH!"], [1.6, "MUNCH... MUNCH... MUNCH..."], [3.2, "SANTA SMILES..."],
           [4.1, "...AND YAWNS..."], [5.0, "SHHH! SANTA IS FAST ASLEEP."]], shout: "HO HO HO!", next: "gnome" },
  gnome: { name: "THE GARDEN GNOME", short: "GNOME", page: "LADYBUG", pages: "LADYBUGS", pageSpr: "ladybug", plus: "LADYBUG", happy: "THE GNOME IS HAPPY AGAIN", item: "mushroom",
    intro: [["THE GNOME IS GRUMPY...", "HE LOST HIS LUCKY MUSHROOM!"], ["YOU FOUND IT, PIP!", "(BOUNCE ON THE RED ONES!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "YOUR LUCKY MUSHROOM!"], [1.6, "BACK WHERE IT BELONGS!"], [3.4, "THE GNOME IS BEAMING!"],
           [4.7, "HO-HUM-HOORAY!"]], shout: "HOORAY!", next: "rumpel" },
  rumpel: { name: "RUMPELSTILTSKIN", short: "RUMPEL", page: "GOLD SPOOL", pages: "SPOOLS", pageSpr: "spool", plus: "SPOOL OF GOLD", happy: "RUMPELSTILTSKIN IS HAPPY", item: "nametag", jig: true,
    intro: [["RUMPELSTILTSKIN IS GRUMPY...", "NOBODY REMEMBERS HIS NAME!"], ["TAKE HIM THIS NAME BADGE, PIP!", "(GRAB THE GOLD!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "A BADGE WITH YOUR NAME ON!"], [1.6, "R-U-M-P-E-L...!"], [3.4, "HE DANCES WITH JOY!"],
           [4.7, "EVERYONE KNOWS MY NAME!"]], shout: "HEE HEE!", next: "rapunzel" },
  rapunzel: { name: "RAPUNZEL", short: "RAPUNZEL", page: "ROSE", pages: "ROSES", pageSpr: "rose", plus: "ROSE", happy: "RAPUNZEL IS HAPPY AGAIN", item: "hairbrush",
    intro: [["RAPUNZEL IS GRUMPY...", "HER BRAID IS ALL TANGLED!"], ["TAKE HER THIS GOLDEN BRUSH, PIP!", "(CLIMB THE BRAID UP THE TOWER)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "A GOLDEN HAIRBRUSH!"], [1.6, "BRUSH... BRUSH... SHINY!"], [3.4, "RAPUNZEL IS BEAMING!"],
           [4.7, "TEE-HEE! THANK YOU, PIP!"]], shout: "LA LA LA!", next: "dwarf" },
  dwarf: { name: "THE DWARF KING", short: "DWARF KING", page: "GEM", pages: "GEMS", pageSpr: "gem", plus: "GEM", happy: "THE DWARF KING IS HAPPY", item: "kingcrown",
    intro: [["THE DWARF KING IS GRUMPY...", "HE LOST HIS CROWN!"], ["YOU FOUND IT, PIP!", "(WATCH FOR ROCKFALLS!)"]],
    caps: [[0, "YOU MADE IT, PIP!"], [0.8, "YOUR CROWN, YOUR MAJESTY!"], [1.6, "A KING AGAIN!"], [3.4, "THE DWARF KING BEAMS!"],
           [4.7, "HAR HAR! A FEAST FOR PIP!"]], shout: "HAR HAR!", next: "wizard" },
};
function STORY() { return STORIES[LEVEL] || STORIES.wizard; }
/** Unlock chain: World 1 in order (Grandpa -> Goat -> Lumberjack -> Mountain Man -> Bigfoot), Bigfoot opens World 2
 *  (Elf -> Rudolph -> Ice Giant -> Yeti -> Santa), Santa opens the World 3 Wizard path. Players who had the Wizard
 *  before (old saves, or Bigfoot cheered while he unlocked the Wizard) keep him (bc_wiz_open, see below). */
const CHAIN = ["grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa",
               "gnome", "rumpel", "rapunzel", "dwarf", "wizard"];
const UNLOCK_BY = { goat: "grandpa", lumberjack: "goat", mountain: "lumberjack", bigfoot: "mountain",
                    elf: "bigfoot", rudolph: "elf", ice: "rudolph", yeti: "ice", santa: "yeti",
                    gnome: "santa", rumpel: "gnome", rapunzel: "rumpel", dwarf: "rapunzel", wizard: "dwarf" };
function isUnlocked(id) {
  if (id === "grandpa") return true;
  if (!UNLOCK_BY[id]) return false;
  if (cheered.has(id) || cheered.has(UNLOCK_BY[id])) return true;
  return id === "wizard" && localStorage.getItem("bc_wiz_open") === "1";
}
// ---------------------------------------------------------------- optional Poki SDK adapter (no network: only used
// if a portal page has ALREADY loaded window.PokiSDK; this file never loads anything itself)
const Poki = {
  sdk: null, on: false, loadedSent: false,
  init() { try { if (window.PokiSDK && typeof window.PokiSDK.init === "function") { this.sdk = window.PokiSDK; const r = this.sdk.init(); if (r && r.catch) r.catch(() => {}); } } catch (e) { this.sdk = null; } },
  call(fn) { try { if (this.sdk && typeof this.sdk[fn] === "function") this.sdk[fn](); } catch (e) {} },
  loaded() { if (!this.loadedSent) { this.loadedSent = true; this.call("gameLoadingFinished"); } },
  screen(s) {                                  // gameplay = climbing or steering the parachute
    const play = s === "play" || s === "para";
    if (play && !this.on) { this.on = true; this.call("gameplayStart"); }
    else if (!play && this.on) { this.on = false; this.call("gameplayStop"); }
  },
};
Poki.init();

// ---------------------------------------------------------------- level data helpers
const tileAt = (col, row) => (row < 0 || row >= ROWS || col < 0 || col >= COLS) ? (row >= ROWS ? "face" : "none") : A.tilemap[row][col];
const colOf = (x) => Math.floor(x - 0);            // columns: [c, c+1) in world x
const minZ = (col) => Math.max(START_Z - 0.4, A.col_min_z[col] - 0.6);   // lowest root z still on hair
const rand = (a, b) => a + Math.random() * (b - a);

// ---------------------------------------------------------------- game state
let S;          // whole run state, reset by newGame()
let screen = "title", screenT = 0, now = 0, lastFrame = 0, inputLockUntil = 0;
let hiscore = +localStorage.getItem("bc_hi") || 0;

function newGame() {
  const z0 = SKIP_TOP ? GOAL_Z - 5 : START_Z;
  S = {
    motionVersion: 0,                         // invalidates a speculative touch after another movement
    t: 0,                                    // play time (s)
    cl: { col: Math.floor(START_X), x: START_X, z: z0, arm: null, tw: null, mode: "climb",
          modeT: 0, modeDur: 0, fromX: 0, toX: 0, fromZ: 0, toZ: 0, invulnUntil: 0,
          braceUntil: -1, braceCdUntil: -1, hold: false, slipT: -9, lastSide: null, lastTapT: -9 },
    lives: 3, maxLives: 3, boosts: [], magnet: false, slowUntil: 0, hat: 0, hatFlashUntil: 0, score: 0, maxZ: z0, hatsGot: 0, hitsAbsorbed: 0,
    haz: [], items: [], fx: [], texts: [],
    nextThrow: 1.2, mouthOpenUntil: -1,
    sneeze: { next: T.SNEEZES ? T.SNEEZE_FIRST : 1e9, phase: "none", t0: 0, judged: false },
    shake: 0, camZ: z0 - 1.3, result: null, lastHatThrow: -99, seenSneeze: false,
    pages: 0, catOn: LEVEL === "wizard", bookIn: false, catIn: false, asleep: false, phoneIn: false, waving: false,
    tut: T.TUTORIAL ? { i: 0, t0: 0, dyno: false, item: null, shelter: null, demo: false, steps: [] } : null,
  };
  face = "normal";
  // hard hats tangled in hand-holds / knots, roughly 1/3 and 2/3 up the beard
  for (const target of T.HAT_AT.map((f) => Math.round(f * ROWS))) {
    let best = null;
    for (let r = target; r < target + 4 && !best; r++)
      for (const c of [2, 3, 1, 4, 0, 5])
        if ((tileAt(c, r) === "knot" || tileAt(c, r) === "hold") && r + 0.5 - T.HAND > minZ(c)) { best = { c, r }; break; }
    if (best) S.items.push({ kind: "tangled", x: best.c + 0.5, z: best.r + 0.5, t: 0 });
  }
  // loose spell-book pages tucked into the beard (a bit to the side, so some need a leap)
  const taken = S.items.map((i) => Math.floor(i.z));
  T.PAGE_AT.map((f) => Math.round(f * ROWS)).slice(0, T.PAGES - (T.TUTORIAL ? 1 : 0)).forEach((target, k) => {
    for (let r = target; r < target + 3; r++) {
      if (taken.includes(r)) continue;
      const order = k % 2 ? [3, 1, 4, 2, 0, 5] : [2, 4, 1, 3, 5, 0];
      const c = order.find((c) => tileAt(c, r) !== "sparse" && r + 0.5 - T.HAND > minZ(c));
      if (c !== undefined) { S.items.push({ kind: "page", x: c + 0.5, z: r + 0.5, t: Math.random() * 3 }); return; }
    }
  });
  // Gnome: bouncy lucky mushrooms growing out of the beard (touch one = BOING! up ~2.5 rows)
  for (const f of T.MUSH || []) {
    const target = Math.round(f * ROWS), used = S.items.map((i) => Math.floor(i.z));
    for (let r = target; r < target + 4; r++) {
      if (used.includes(r)) continue;
      const c = [1, 4, 2, 3, 0, 5].find((c) => tileAt(c, r) !== "sparse" && r + 0.5 - T.HAND > minZ(c));
      if (c !== undefined) { S.items.push({ kind: "mush", x: c + 0.5, z: r + 0.5, t: 0 }); break; }
    }
  }
  if (SKIP_TOP) S.items = S.items.filter((i) => i.z > z0 - 1);
  // a few hazards already in flight (thrown before you looked up), so the first ones arrive soon
  for (const z of T.PREFILL) spawnHazard(randCol(), z, Math.floor(Math.random() * 3), true);
  placeShelters();
  if (SKIP_TOP) S.haz.length = 0;
  applyBoosts();
  if (S.tut) S.nextThrow = 1e9;               // tutorial: nothing falls until the hard-hat lesson is done
  S.camZ = camTarget();
}

const progress = () => Math.max(0, Math.min(1, (S.cl.z - START_Z) / (GOAL_Z - START_Z)));
const randCol = () => T.NARROW ? 1 + Math.floor(Math.random() * (COLS - 2)) : Math.floor(Math.random() * COLS);

// ---------------------------------------------------------------- player actions
function setMode(m, dur) { const cl = S.cl; S.motionVersion++; cl.mode = m; cl.modeT = S.t; cl.modeDur = dur / 1000; }
function finishTween() { const cl = S.cl; if (cl.tw) { cl.z = cl.tw.toZ; cl.tw = null; } }
function busy() { const m = S.cl.mode; return m === "dyno" || m === "fall"; }

const canPlay = () => !!S && screen === "play" && !S.result && !paused;

/** Tap/press of one arm. Registers immediately; alternating sides climb; same side twice fast = dyno. */
function reach(side) {
  if (!canPlay()) return;
  const cl = S.cl, tms = S.t * 1000;
  if (busy()) return;
  S.motionVersion++;
  const dbl = cl.lastSide === side && tms - cl.lastTapT < T.DOUBLE_MS;
  cl.lastSide = side; cl.lastTapT = tms;
  if (cl.braceUntil > S.t) cl.braceUntil = S.t;           // reaching ends a brace early
  if (dbl) { cl.lastSide = null; dyno(side); return; }
  finishTween();
  const climbs = cl.arm !== side;
  cl.arm = side;
  sfx.reach();
  if (!climbs) { cl.tw = { side, fromZ: cl.z, toZ: cl.z, t0: S.t }; return; }   // same arm again: just re-grip
  let toZ = Math.min(GOAL_Z, cl.z + T.STEP);
  const row = Math.floor(toZ + T.HAND);
  if (tileAt(cl.col, row) === "sparse") {              // bald patch: hand slips off
    cl.slipT = S.t; sfx.slip(); popText("SLIP!", cl.x, cl.z + 2.2, C.white);
    cl.tw = { side, fromZ: cl.z, toZ: cl.z, t0: S.t }; return;
  }
  cl.tw = { side, fromZ: cl.z, toZ, t0: S.t };
  if (toZ > S.maxZ + 0.01) { S.score += Math.round((toZ - S.maxZ) * 25); S.maxZ = toZ; }
}

/** Sideways leap one column (towards the double-tapped side). */
function dyno(side) {
  if (!canPlay() || busy()) return;
  const cl = S.cl, nc = cl.col + (side === "L" ? -1 : 1);
  finishTween();
  const ok = nc >= 0 && nc < COLS && cl.z >= minZ(nc) && tileAt(nc, Math.floor(cl.z + T.HAND)) !== "sparse";
  if (!ok) { cl.slipT = S.t; sfx.slip(); popText(nc < 0 || nc >= COLS || cl.z < minZ(nc) ? "NO HAIR!" : "BALD!", cl.x, cl.z + 2.2, C.white); return; }
  cl.fromX = cl.x; cl.toX = nc + 0.5; cl.col = nc; cl.fromZ = cl.z; cl.toZ = cl.z; cl.dynoSide = side;
  setMode("dyno", T.DYNO_MS); cl.arm = null; sfx.dyno();
  if (S.tut) S.tut.dyno = true;
}

function brace() {
  if (!canPlay()) return;
  const cl = S.cl;
  if (S.t < cl.braceCdUntil || cl.mode === "fall") return;
  S.motionVersion++; finishTween();
  cl.braceUntil = S.t + T.BRACE_MS / 1000; cl.braceCdUntil = S.t + (T.BRACE_MS + T.BRACE_CD_MS) / 1000;
  sfx.brace();
}
function setHold(on) { if (S && (!on || canPlay())) S.cl.hold = on; }

/** Climb DOWN one notch (swipe down, both control modes; X key). Lets players go back for something missed. */
function climbDown() {
  if (!canPlay()) return false;
  const cl = S.cl;
  if (busy()) return false;
  finishTween();
  const toZ = Math.max(minZ(cl.col), START_Z, cl.z - T.DOWN_STEP);
  if (toZ > cl.z - 0.05) { popText("BOTTOM!", cl.x, cl.z + 2.2, C.white); return false; }
  S.motionVersion++;
  const side = cl.arm === "L" ? "R" : "L";
  cl.arm = side; cl.tw = { side, fromZ: cl.z, toZ, t0: S.t, ms: T.DOWN_MS, down: true };
  if (cl.braceUntil > S.t) cl.braceUntil = S.t;
  Snd.tone(420, 0.05, 0.05); popText("DOWN", cl.x, cl.z + 2.2, C.hair3, 0.5);
  S.downs = (S.downs || 0) + 1;
  if (S.tut) S.tut.down = true;
  return true;
}
/** One-hand mode: the arm the next tap moves (always the other one, so tapping anywhere climbs). */
const nextArm = () => (S && S.cl.arm === "L" ? "R" : "L");
/** A touch reaches instantly; if it then turns into a swipe, the reach is taken back (a swipe never counts as a tap). */
const REACH_FIELDS = ["col", "x", "z", "arm", "tw", "mode", "modeT", "modeDur", "fromX", "toX", "fromZ", "toZ", "dynoSide", "lastSide", "lastTapT", "slipT"];
function snapClimb() {
  if (!canPlay()) return null;
  const cl = Object.fromEntries(REACH_FIELDS.map((k) => [k, S.cl[k]]));
  if (cl.tw) cl.tw = Object.assign({}, cl.tw);
  return { run: S, cl, maxZ: S.maxZ, score: S.score, version: S.motionVersion, reachScore: 0 };
}
function finishSnap(sn) { if (sn && sn.run === S) { sn.version = S.motionVersion; sn.reachScore = S.score - sn.score; } }
function undoClimb(sn) {
  if (!sn || sn.run !== S || !canPlay() || sn.version !== S.motionVersion) return false;
  Object.assign(S.cl, sn.cl); S.maxZ = sn.maxZ;
  S.score -= sn.reachScore;                    // keep points from hats / collectibles acquired after the tap
  S.motionVersion++;
  S.texts = S.texts.filter((t) => t.s !== "SLIP!");
  return true;
}

// ---------------------------------------------------------------- controls setting (ONE HAND / TWO HANDS)
const IS_TOUCH = "ontouchstart" in window || navigator.maxTouchPoints > 0;
let controls = ["one", "two"].includes(params.get("controls")) ? params.get("controls")
  : ["one", "two"].includes(localStorage.getItem("bc_controls")) ? localStorage.getItem("bc_controls") : (IS_TOUCH ? "one" : "two");
function setControls(m) { controls = m === "one" ? "one" : "two"; localStorage.setItem("bc_controls", controls); }

/** Knock the climber down `rows` (fall pose), clamped to the hair that is there. */
function knockDown(rows) {
  const cl = S.cl; finishTween();
  cl.fromZ = cl.z; cl.toZ = Math.max(minZ(cl.col), cl.z - rows); cl.fromX = cl.toX = cl.x;
  setMode("fall", T.FALL_MS); cl.arm = null;
}

// ---------------------------------------------------------------- shelters (thick tangles)
function placeShelters() {
  S.shelters = []; S.shelterBlocks = 0;
  if (!T.SHELTERS || NO_SHELTERS) return;
  const n = T.SHELTER_MIN + Math.floor(Math.random() * (T.SHELTER_MAX - T.SHELTER_MIN + 1)), span = T.SHELTER_LAST - T.SHELTER_FIRST;
  const taken = S.items.map((i) => Math.floor(i.z));
  for (let i = 0; i < n; i++) {
    const f = T.SHELTER_FIRST + span * (i + 0.5 + rand(-0.25, 0.25)) / n;
    const r0 = Math.floor(START_Z + f * (GOAL_Z - START_Z) + 1.0);           // tangle at Pip's chest height
    for (let r = r0; r < r0 + 3; r++) {
      if (taken.includes(r)) continue;
      const order = [0, 1, 2, 3, 4, 5].sort(() => Math.random() - 0.5);
      const c = order.find((c) => tileAt(c, r) !== "sparse" && tileAt(c, r - 1) !== "sparse" && r - 1 > minZ(c));
      if (c !== undefined) { S.shelters.push({ x: c + 0.5, z: r + 0.5, state: "ready", t0: 0 }); break; }
    }
  }
}
const inShelterBox = (sh, cl) => Math.abs(cl.x - sh.x) < 0.45 && sh.z - cl.z > 0.3 && sh.z - cl.z < 1.7;
function shelterNow() { const cl = S.cl; return S.shelters && S.shelters.find((sh) => sh.state === "on" && inShelterBox(sh, cl)); }
function updateShelters() {
  const cl = S.cl;
  for (const sh of S.shelters || []) {
    if (sh.state === "ready" && cl.mode !== "fall" && inShelterBox(sh, cl)) {
      sh.state = "on"; sh.t0 = S.t; sfx.held(); popText("SAFE SPOT!", cl.x, cl.z + 2.4, C.acc2, 1.0);
    } else if (sh.state === "on" && S.t - sh.t0 >= T.SHELTER_S) {
      sh.state = "gone"; sh.t0 = S.t; Snd.tone(500, 0.2, 0.05, "triangle", 250);
      if (inShelterBox(sh, cl)) popText("IT UNRAVELLED!", cl.x, cl.z + 2.4, C.white, 1.0);
      sparkle(sh.x, sh.z, 10, C.hair3);
    }
  }
}
function bounceOff(h) {
  const cl = S.cl;
  h.deflected = true; h.vx = (h.x < cl.x ? -1 : 1) * rand(2.5, 3.5); h.vz = 4;
  S.shelterBlocks++; S.score += 25; sfx.block(); popText("BOING!", cl.x, cl.z + 2.6, C.acc2); sparkle(h.x, h.z, 6, C.hair3);
}
let tangleImg = null;
function tangleSprite() {                     // a thick knotted nest of beard hair, 46x36, pixel-drawn once
  if (tangleImg) return tangleImg;
  const c = document.createElement("canvas"); c.width = 46; c.height = 36;
  const g = c.getContext("2d"), cols = [LC.hair2, LC.hair3, LC.hair4, LC.hair3];
  const cx0 = 23, cy0 = 18, mask = [];
  const ell = (x, y, rx, ry) => ((x - cx0) / rx) ** 2 + ((y - cy0) / ry) ** 2 <= 1;
  for (let y = 0; y < 36; y++) for (let x = 0; x < 46; x++) if (ell(x, y, 21, 16)) { g.fillStyle = (x + y) % 5 ? LC.hair1 : "#3a4058"; g.fillRect(x, y, 1, 1); }
  const loops = [[23, 18, 18, 13], [13, 13, 9, 7], [33, 13, 9, 7], [14, 23, 9, 7], [32, 23, 9, 7], [23, 10, 10, 6], [23, 26, 10, 6], [23, 18, 7, 5]];
  loops.forEach(([cx, cy, rx, ry], k) => {
    for (let a = 0; a < 360; a += 3) {
      const t = a * Math.PI / 180, x = Math.round(cx + Math.cos(t) * rx), y = Math.round(cy + Math.sin(t) * ry);
      if (!ell(x, y, 21, 16)) continue;
      g.fillStyle = cols[(k + Math.floor(a / 60)) % 4]; g.fillRect(x, y, 2, 2);
    }
  });
  const d = g.getImageData(0, 0, 46, 36); outlineData(d.data, 46, 36);           // same 1px black outline as the sprites
  for (let i = 0; i < d.data.length; i += 4) if (d.data[i + 3] && d.data[i] === 0 && d.data[i + 1] === 0 && d.data[i + 2] === 0) d.data[i + 3] = 255;
  g.putImageData(d, 0, 0);
  for (let i = 0; i < 12; i++) { g.fillStyle = C.white; g.fillRect(9 + ((i * 7) % 28), 7 + ((i * 11) % 22), 1, 1); }   // glints
  return (tangleImg = c);
}
function drawShelters(front) {
  for (const sh of S.shelters || []) {
    const x = sx(sh.x), y = sy(sh.z); if (y < -30 || y > H + 30) continue;
    const age = S.t - sh.t0;
    if (sh.state === "gone") {                // unravelled: a few loose strands drift down, then nothing
      if (front || age > 0.9) continue;
      ctx.globalAlpha = 1 - age / 0.9;
      for (let i = 0; i < 6; i++) { ctx.fillStyle = i % 2 ? C.hair3 : C.hair2; ctx.fillRect(x - 14 + i * 5, y - 6 + Math.round(age * 30) + (i % 3) * 3, 1, 6); }
      ctx.globalAlpha = 1; continue;
    }
    const img = tangleSprite();
    if (!front) {
      if (sh.state === "on") {                // protected: a blinking ring round the tangle
        ctx.fillStyle = Math.floor(S.t * 8) % 2 ? C.acc2 : C.white;
        for (let i = 0; i < 28; i++) { const t = i / 28 * Math.PI * 2 + S.t * 2; ctx.fillRect(x + Math.round(Math.cos(t) * 25) - 1, y + Math.round(Math.sin(t) * 20) - 1, 2, 2); }
      }
      ctx.drawImage(img, x - 23, y - 18);
      if (sh.state === "ready") goodSparkle(x, y, S.t);
    } else if (sh.state === "on" && inShelterBox(sh, S.cl)) {
      ctx.drawImage(img, 0, 20, 46, 16, x - 23, y + 2, 46, 16);   // the lower curls wrap round Pip
    }
    if (front && sh.state === "on") {          // time left
      const k = Math.max(0, 1 - age / T.SHELTER_S), w = Math.round(28 * k);
      ctx.fillStyle = "#000"; ctx.fillRect(x - 15, y - 24, 30, 4);
      ctx.fillStyle = k > 0.35 ? C.acc2 : C.shirt; ctx.fillRect(x - 14, y - 23, w, 2);
    }
  }
}

// ---------------------------------------------------------------- hazards / items / effects
function spawnHazard(col, z, kind, silent) {
  const fromMouth = z >= MOUTH_Z - 0.01;
  S.haz.push({ kind, good: kind === "hat", x: fromMouth ? MOUTH_X : col + 0.5, x0: MOUTH_X, tx: col + 0.5,
               z, z0: z, vx: 0, vz: 0, emerge: fromMouth ? 0.22 : 0, dead: false, deflected: false, spin: Math.random() * 4 });
  if (!silent) { S.mouthOpenUntil = S.t + 0.45; Snd.play(kind === "hat" ? "spit_hat" : "spit", 0.8); }
}
const throwKind = () => Math.floor(Math.random() * (T.THROW_N || A.hazard_names.length));
function throwSomething() {
  const p = progress();
  const pace = hazardPace(p);
  let col = Math.random() < pace.aim ? S.cl.col : randCol();
  const hatOk = S.hat === 0 && S.t - S.lastHatThrow > 15 && !S.haz.some((h) => h.good);
  if (hatOk && Math.random() < T.HAT_THROW_CHANCE + p * 0.05) {
    S.lastHatThrow = S.t; spawnHazard(randCol(), MOUTH_Z, "hat");
  } else {
    spawnHazard(col, MOUTH_Z, throwKind());
    if (Math.random() < pace.pair) {                    // upper third: sometimes two at once (never both on you)
      let c2 = randCol(); if (c2 === col) c2 = (col + 2 + Math.floor(Math.random() * (COLS - 3))) % COLS;
      spawnHazard(c2, MOUTH_Z + 0.3, throwKind(), true);
    }
  }
  S.nextThrow = S.t + rand(0.8, 1.2) * (T.THROW_SLOW + (T.THROW_FAST - T.THROW_SLOW) * p) * pace.throwK;
}
/** Gnome: a lucky mushroom bounces Pip up the beard. */
function mushBoost(it) {
  S.motionVersion++;
  const cl = S.cl; finishTween();
  const toZ = Math.min(GOAL_Z, cl.z + T.MUSH_UP);
  cl.tw = { fromZ: cl.z, toZ, t0: S.t, ms: 420, side: cl.arm === "L" ? "R" : "L" };
  S.mushes = (S.mushes || 0) + 1; S.score += 75; Snd.play("pickup");
  popText("BOING!", cl.x, cl.z + 2.3, "#ff6060", 1.0); sparkle(it.x, it.z, 10, "#ff6060");
}
function popText(s, x, z, col, dur = 0.8) { S.texts = S.texts.filter((t) => t.s !== s); S.texts.push({ s, x, z, col, t0: S.t, dur }); }
function sparkle(x, z, n, col) { for (let i = 0; i < n; i++) S.fx.push({ x, z, vx: rand(-2, 2), vz: rand(-1, 3), t0: S.t, dur: rand(0.3, 0.6), col }); }

function getHat(from) {
  S.hat = T.HAT_HITS; S.hatsGot++; S.score += 200; Snd.play("pickup");
  popText("HARD HAT!", S.cl.x, S.cl.z + 2.3, C.hardhat, 1.2); sparkle(S.cl.x, S.cl.z + 1.6, 10, C.hardhat);
}

/** A hazard reached the climber. Order: brace deflects > hard hat absorbs > lose a life. */
function hit(h) {
  const cl = S.cl;
  h.deflected = true; h.vx = (h.x < cl.x ? -1 : 1) * rand(2, 3.5); h.vz = 3;
  if (S.t < cl.braceUntil) {
    S.score += 25; sfx.block(); popText("BLOCK!", cl.x, cl.z + 2.3, C.acc2); sparkle(h.x, h.z, 6, C.white); return "brace";
  }
  if (S.hat > 0) {
    S.hat--; S.hitsAbsorbed++; S.score += 100; S.hatFlashUntil = S.t + 0.3; S.shake = Math.max(S.shake, 2);
    sparkle(h.x, h.z, 6, C.hardhat);
    if (S.hat === 0) {                                  // third hit: the hat pops off
      Snd.play("pop"); popText("POP!", cl.x, cl.z + 2.3, C.hardhat);
      S.fx.push({ hat: true, x: cl.x, z: cl.z + 1.7, vx: (h.vx > 0 ? -1 : 1) * 2.2, vz: 5, t0: S.t, dur: 1.2 });
    } else { Snd.play("clink"); popText("CLINK!", cl.x, cl.z + 2.3, C.hardhat); }
    return "hat";
  }
  if (T.TUTORIAL) {                                     // tutorial: a bonk only knocks you down a little
    S.hitsTaken = (S.hitsTaken || 0) + 1; Snd.play("hurt", 0.6); S.shake = 3;
    popText("BONK! NO HARM DONE", cl.x, cl.z + 2.3, C.white, 1.0);
    knockDown(T.KNOCK_HIT); cl.invulnUntil = S.t + T.INVULN_MS / 1000;
    return "bonk";
  }
  S.lives--; S.hitsTaken = (S.hitsTaken || 0) + 1; Snd.play("hurt"); S.shake = 4;
  popText(S.lives > 0 ? "OUCH!" : "OH NO!", cl.x, cl.z + 2.3, C.shirt);
  knockDown(T.KNOCK_HIT); cl.invulnUntil = S.t + T.INVULN_MS / 1000;
  return "life";
}

// ---------------------------------------------------------------- update
function camTarget() {
  const vh = H / P, bottom = TOP - A.level_h / P;
  return Math.max(bottom, Math.min(TOP - vh, S.cl.z - 1.4));
}

function update(dt) {
  S.t += dt;
  const cl = S.cl, p = progress();
  // --- climber tweens
  if (cl.tw) {
    const k = Math.min(1, (S.t - cl.tw.t0) * 1000 / (cl.tw.ms || T.CLIMB_MS));
    cl.z = cl.tw.fromZ + (cl.tw.toZ - cl.tw.fromZ) * k;
    if (k >= 1) { cl.z = cl.tw.toZ; cl.tw.done = true; }
  }
  if (cl.mode === "dyno" || cl.mode === "fall") {
    const k = Math.min(1, (S.t - cl.modeT) / cl.modeDur);
    const e = k * k * (3 - 2 * k);
    cl.x = cl.fromX + (cl.toX - cl.fromX) * e;
    cl.z = cl.fromZ + (cl.toZ - cl.fromZ) * (cl.mode === "fall" ? k * k : e) + (cl.mode === "dyno" ? Math.sin(k * Math.PI) * 0.35 : 0);
    if (k >= 1) {
      cl.z = cl.toZ; cl.x = cl.toX; cl.mode = "climb";
      if (S.lives <= 0 && !T.TUTORIAL) endGame(false);
    }
  }
  if (!S.result && cl.mode === "climb" && cl.z >= GOAL_Z - 1e-3 && (!cl.tw || cl.tw.done)) endGame(true);
  if (T.SLIP && !S.result && cl.mode === "climb" && (!cl.tw || cl.tw.done) && S.t - cl.lastTapT / 1000 > T.SLIP_GRACE) {   // icy: slide down
    const lo = minZ(cl.col);
    if (cl.z > lo + 0.01) {
      cl.tw = null; cl.z = Math.max(lo, cl.z - T.SLIP * (cl.hold ? 0.35 : 1) * dt);
      if (Math.random() < dt * 8) S.fx.push({ x: cl.x + rand(-0.3, 0.3), z: cl.z + 0.3, vx: 0, vz: -1, t0: S.t, dur: 0.4, col: "#cceaf8" });
      if (S.t - (S.slideTxt || -9) > 2.5) { S.slideTxt = S.t; popText("SLIDING! KEEP CLIMBING!", cl.x, cl.z + 2.3, "#cceaf8", 1.0); }
    }
  }
  if (T.MELT_S && !S.result && S.t >= T.MELT_S) { S.melted = true; popText("IT MELTED!", cl.x, cl.z + 2.3, C.white, 1.5); endGame(false); }
  // --- throws
  if (!S.result && S.t >= S.nextThrow) throwSomething();
  // --- hazards
  const fallV = (T.FALL_SLOW + (T.FALL_FAST - T.FALL_SLOW) * p) * hazardPace(p).fallK;
  for (const h of S.haz) {
    if (h.emerge > 0) { h.emerge -= dt; continue; }
    if (h.deflected) { h.vz -= 14 * dt; h.x += h.vx * dt; h.z += h.vz * dt; h.spin += dt * 20; }
    else {
      h.z -= fallV * dt * (h.good ? 0.75 : 1) * (h.fast || 1);
      if (T.GOLD_CHANCE && h.kind === 0 && !h.goldRoll && h.z0 - h.z > 2.4) {   // Rumpelstiltskin: straw spun into gold
        h.goldRoll = true;
        if (Math.random() < T.GOLD_CHANCE) { h.gold = true; sparkle(h.x, h.z, 8, C.hardhat); }
      }
      const d = Math.min(1, (h.z0 - h.z) / 2.2);          // drift from the mouth into its column
      h.x = h.x0 + (h.tx - h.x0) * d * d * (3 - 2 * d);
      if (h.z0 < MOUTH_Z - 0.01) h.x = h.tx;
      h.spin += dt * 7;
      // collision with the climber (body + raised arms box)
      if (!S.result && !window.BC.ghost && Math.abs(h.x - cl.x) < 0.55 && h.z > cl.z - 0.1 && h.z < cl.z + 2.1) {
        if (h.good) { h.dead = true; getHat(); }
        else if (h.gold) { h.dead = true; S.goldGot = (S.goldGot || 0) + 1; S.score += 100; Snd.play("pickup");
                           popText("GOLD! +" + T.EARN_GOLD, cl.x, cl.z + 2.3, C.hardhat, 0.9); sparkle(h.x, h.z, 8, C.hardhat); }
        else if (S.t >= cl.invulnUntil) { if (shelterNow()) bounceOff(h); else hit(h); }
      }
    }
    if (h.z < S.camZ - 3 || h.z < -3) h.dead = true;
  }
  S.haz = S.haz.filter((h) => !h.dead);
  // --- tangled hats
  for (const it of S.items) {
    it.t += dt;
    if (!it.dead && Math.abs(it.x - cl.x) < 0.5 && Math.abs(cl.z + T.HAND - it.z) < 0.7) {
      it.dead = true;
      if (it.kind === "page") { S.pages++; S.score += 150; sfx.page(); popText(STORY().page + " " + S.pages + "/" + T.PAGES, cl.x, cl.z + 2.3, C.white, 1.1); sparkle(it.x, it.z, 8, C.white); }
      else if (it.kind === "mush") { if (cl.mode === "climb" && !S.result) mushBoost(it); else it.dead = false; }
      else getHat();
    }
  }
  S.items = S.items.filter((i) => !i.dead);
  updateShelters();
  if (S.tut && !S.result) updateTutorial(dt);
  // --- sneeze event
  const sn = S.sneeze;
  if (!S.result) {
    if (sn.phase === "none" && S.t >= sn.next) {
      sn.phase = "warn"; sn.t0 = S.t; sn.dir = Math.random() < 0.5 ? "L" : "R"; sfx.warn();
      sn.swoop = T.EVENT === "laugh" && (sn.n = (sn.n || 0) + 1) % 2 === 0;      // Santa: every other event is a reindeer swoop
      if (T.EVENT === "rockfall") {                      // Dwarf King: mark the columns the boulders will come down
        const c1 = Math.random() < 0.7 ? cl.col : randCol(); let c2 = randCol();
        if (c2 === c1) c2 = T.NARROW ? c1 : (c1 + 1 + Math.floor(Math.random() * (COLS - 1))) % COLS;
        sn.cols = T.ROCK_COLS > 1 ? [c1, c2] : [c1];
      }
    }
    else if (sn.phase === "warn") {
      if (Math.floor((S.t - sn.t0) / 0.4) !== Math.floor((S.t - dt - sn.t0) / 0.4)) sfx.warn();
      if (S.t - sn.t0 >= T.SNEEZE_WARN) {
        sn.phase = "blast"; sn.t0 = S.t; sn.judged = false;
        if (sn.swoop) { sfx.whoosh(); sfx.jingle(); sn.judged = true; swoopDrop(sn.dir); }
        else if (T.EVENT === "rockfall") { sfx.stomp(); sn.judged = true; rockfall(sn.cols); }
        else if (T.EVENT === "gust") sfx.whoosh();
        else if (SHAKY[T.EVENT]) { (T.EVENT === "laugh" ? sfx.hoho : T.EVENT === "roar" ? sfx.roar : sfx.stomp)(); stompDrop(); }
        else { sfx.sneeze(); S.mouthOpenUntil = S.t + T.SNEEZE_BLAST; }
      }
    } else if (sn.phase === "blast") {
      S.shake = Math.max(S.shake, sn.swoop ? 0 : T.EVENT === "rockfall" ? 3 : SHAKY[T.EVENT] || (T.EVENT === "gust" ? 2 : 4));
      if (!sn.judged && S.t - sn.t0 > 0.15) {           // small grace window to start holding
        sn.judged = true;
        if (cl.hold) { S.score += 50; sfx.held(); popText("HELD ON!", cl.x, cl.z + 2.3, C.acc2, 1.1); }
        else if (cl.mode !== "fall") {
          S.eventsLost = (S.eventsLost || 0) + 1;
          if (T.EVENT === "gust") gustPush(sn.dir);
          else { popText("SHAKEN OFF!", cl.x, cl.z + 2.3, C.white, 1.1); knockDown(T.KNOCK_SNEEZE); Snd.play("hurt", 0.6); }
        }
      }
      if (S.t - sn.t0 >= T.SNEEZE_BLAST) {
        sn.phase = "none"; S.seenSneeze = true;
        sn.next = S.t + rand(T.SNEEZE_MIN, T.SNEEZE_MAX) * (1 - 0.25 * p);
      }
    }
  }
  // --- fx, texts, camera
  for (const f of S.fx) { f.vz -= (f.hat ? 14 : 6) * dt; f.x += f.vx * dt; f.z += f.vz * dt; }
  S.fx = S.fx.filter((f) => S.t - f.t0 < f.dur);
  S.texts = S.texts.filter((t) => S.t - t.t0 < t.dur);
  S.shake = Math.max(0, S.shake - dt * 10);
  S.camZ += (camTarget() - S.camZ) * Math.min(1, dt * 7);
}

/** Mountain Man's gust: not holding = blown one column sideways (or off a bit, if there's no hair to land on). */
function gustPush(dir) {
  const cl = S.cl, nc = cl.col + (dir === "L" ? -1 : 1);
  finishTween();
  if (nc >= 0 && nc < COLS && cl.z >= minZ(nc) && tileAt(nc, Math.floor(cl.z + T.HAND)) !== "sparse") {
    cl.fromX = cl.x; cl.toX = nc + 0.5; cl.col = nc; cl.fromZ = cl.z; cl.toZ = cl.z; cl.dynoSide = dir;
    setMode("dyno", T.DYNO_MS * 1.4); cl.arm = null; popText("WHOOSH!", cl.x, cl.z + 2.3, C.white, 1.1);
  } else { popText("BLOWN OFF!", cl.x, cl.z + 2.3, C.white, 1.1); knockDown(T.KNOCK_SNEEZE); Snd.play("hurt", 0.6); }
}
/** Bigfoot's stomp shakes a few pinecones loose from the fur above Pip (never two in Pip's own column). */
function stompDrop() {
  const cl = S.cl, cols = [];
  for (let i = 0; i < T.STOMP_DROP; i++) {
    let c = randCol(); if (cols.includes(c) || (c === cl.col && cols.includes(cl.col))) c = (c + 2) % COLS;
    if (T.EVENT === "roar" && c === cl.col) c = (c + 1 + Math.floor(Math.random() * (COLS - 1))) % COLS;   // the Yeti never aims at Pip
    cols.push(c); spawnHazard(c, Math.min(MOUTH_Z - 0.5, cl.z + 5.2 + i * 0.8), 0, true);
  }
}
/** Dwarf King's rockfall: fast boulders rattle down the marked columns (dodge sideways; holding won't help). */
function rockfall(cols) {
  const cl = S.cl;
  cols.forEach((c, i) => { for (let k = 0; k < 2; k++) {
    spawnHazard(c, Math.min(MOUTH_Z - 0.5, cl.z + 5 + k * 1.3 + i * 0.4), 2, true);
    S.haz[S.haz.length - 1].fast = 1.7;
  } });
}
const EVENT_TXT = { rockfall: "!! ROCKFALL! MOVE !!", sneeze: "!! SNEEZE !!", gust: "!! WIND GUST !!", stomp: "!! STOMP !!", hoof: "!! HOOF STOMP !!", roar: "!! YETI ROAR !!",
                    laugh: "!! HO HO HO !!", swoop: "!! REINDEER SWOOP !!" };
const SHAKY = { stomp: 7, hoof: 5, roar: 6, laugh: 6 };     // events that shake the beard (hold!) + their screen shake
/** Santa's reindeer swoops across the top of the screen and drops presents (no holding needed: dodge them). */
function swoopDrop(dir) {
  const cl = S.cl, cols = [];
  S.swoop = { t0: S.t, dir, z: Math.min(MOUTH_Z - 0.5, cl.z + 6.2) };
  for (let i = 0; i < T.SWOOP_DROP; i++) {
    let c = randCol(); while (cols.includes(c) || (cols.length && c === cl.col)) c = (c + 1) % COLS;
    cols.push(c);
    const h = { kind: 0, good: false, x: c + 0.5, x0: c + 0.5, tx: c + 0.5, z: S.swoop.z, z0: S.swoop.z, vx: 0, vz: 0,
                emerge: 0.25 + i * 0.35, dead: false, deflected: false, spin: Math.random() * 4 };
    S.haz.push(h);
  }
}

// ---------------------------------------------------------------- World 1-1 tutorial (Grandpa)
// One lesson at a time; each waits until the player has done it once. Lesson items (hat, photo, shelter)
// follow Pip's column and re-appear above if Pip climbs past them, so nothing can be missed.
const TUT_STEPS = ["climb", "dyno", "hat", "photo", "down", "shelter", "top", "chute"];
const TUT_TEXT = {
  climb: [["TAP LEFT, RIGHT,", "LEFT, RIGHT..."], "TO CLIMB!  (KEYS: < > OR A D)"],
  dyno: [["BALD PATCH!", "DOUBLE-TAP"], "ONE SIDE TO LEAP AROUND IT"],
  hat: [["GRAB THE", "HARD HAT!"], "CLIMB UP TO IT - IT BLOCKS HITS"],
  photo: [["GRAB THE PHOTO!"], "GRANDPA'S FAMILY PHOTOS"],
  down: [["SWIPE DOWN TO", "CLIMB DOWN"], "ONE FINGER - OR THE X KEY"],
  shelter: [["CLIMB INTO", "THE TANGLE!"], "A SAFE SPOT: THINGS BOUNCE OFF"],
  shelter_on: [["STAY PUT!"], "WATCH IT BOUNCE OFF!"],
  top: [["NOW CLIMB TO", "GRANDPA!"], "DODGE WHAT HE DROPS"],
  chute: [["TAP LEFT / RIGHT", "TO STEER!"], "CATCH THE COINS"],
};
const TUT_TEXT_ONE = {        // one-hand mode prompts (others shared)
  climb: [["TAP TO CLIMB!"], "TAP AGAIN AND AGAIN - ANYWHERE"],
  dyno: [["BALD PATCH!", "SWIPE TO HOP"], "SWIPE LEFT OR RIGHT AROUND IT"],
  down: [["SWIPE DOWN TO", "CLIMB DOWN"], "GO BACK FOR THINGS YOU MISSED"],
  chute: [["SWIPE OR HOLD", "TO STEER!"], "LEFT / RIGHT - CATCH THE COINS"],
};
const tutText = (st) => (controls === "one" && TUT_TEXT_ONE[st]) || TUT_TEXT[st];
const tutStep = () => S && S.tut ? TUT_STEPS[S.tut.i] : null;
function tutNext() {
  const u = S.tut; u.steps.push({ step: TUT_STEPS[u.i], t: +S.t.toFixed(2) }); u.i++; u.t0 = S.t;
  if (screen === "play") { sfx.held(); popText("NICE!", S.cl.x, S.cl.z + 2.9, C.acc2, 0.9); }
  const st = TUT_STEPS[u.i];
  if (st === "dyno") u.dyno = false;
  if (st === "down") u.down = false;                    // a leap counts only after the prompt
  if (st === "hat" || st === "photo") u.item = tutItem(st === "hat" ? "tangled" : "page");
  if (st === "photo") S.nextThrow = S.t + 2.5;          // hazards start after the hard-hat lesson
  if (st === "shelter") u.shelter = tutShelter();
}
function tutColFor(z0, z1) {                  // Pip's column, or a neighbour, with no bald tile between z0..z1
  const cl = S.cl, clear = (c) => { for (let r = Math.floor(z0); r <= Math.floor(z1) + 1; r++) if (tileAt(c, r) === "sparse") return false; return true; };
  return [cl.col, cl.col + 1, cl.col - 1, cl.col + 2, cl.col - 2].find((c) => c >= 0 && c < COLS && clear(c));
}
function tutItem(kind) {
  const cl = S.cl, z = Math.min(GOAL_Z + T.HAND - 0.4, cl.z + T.HAND + T.TUT_ITEM_UP), c = tutColFor(cl.z + T.HAND, z);
  const it = { kind, x: (c === undefined ? cl.col : c) + 0.5, z, t: 0, tut: true };
  S.items.push(it); return it;
}
function tutShelter() {
  const cl = S.cl, r = Math.min(ROWS - 4, Math.floor(cl.z + 1.0) + 2), c = tutColFor(cl.z, r + 1);
  const sh = { x: (c === undefined ? cl.col : c) + 0.5, z: r + 0.5, state: "ready", t0: 0, tut: true };
  S.shelters = (S.shelters || []).filter((x) => !x.tut).concat([sh]); return sh;
}
function updateTutorial(dt) {
  const u = S.tut, cl = S.cl, st = TUT_STEPS[u.i];
  if (st === "climb" && cl.z - START_Z >= T.TUT_CLIMB) tutNext();
  else if (st === "dyno" && u.dyno) tutNext();
  else if (st === "down" && u.down) tutNext();
  else if (st === "hat" || st === "photo") {
    const it = u.item;
    if (st === "hat" ? S.hatsGot > 0 : S.pages > 0) { tutNext(); return; }
    if (!it || it.dead) { u.item = tutItem(st === "hat" ? "tangled" : "page"); return; }
    if (cl.mode === "climb") it.x += (cl.col + 0.5 - it.x) * Math.min(1, dt * 4);   // drifts to Pip's column
    if (it.z < cl.z + T.HAND - 0.8) { it.z = Math.min(GOAL_Z + T.HAND - 0.4, cl.z + T.HAND + T.TUT_ITEM_UP); sparkle(it.x, it.z, 6, C.white); }
  } else if (st === "shelter") {
    const sh = u.shelter;
    if (!sh) { u.shelter = tutShelter(); return; }
    if (sh.state === "on" && !u.demo) {                 // drop something on Pip to show the bounce
      u.demo = true; spawnHazard(Math.floor(sh.x), cl.z + 4.6, Math.floor(Math.random() * A.hazard_names.length));
      S.nextThrow = Math.max(S.nextThrow, S.t + T.SHELTER_S + 1.5);
    }
    if (u.demo && (S.shelterBlocks > 0 || sh.state === "gone")) { tutNext(); return; }
    if (sh.state === "ready" && cl.mode === "climb") {
      if (sh.z - cl.z < 0.3) u.shelter = tutShelter();              // climbed past it: a new one above
      else if (Math.abs(sh.x - cl.x) > 0.5) sh.x = cl.col + 0.5;      // leapt sideways: it follows
    }
  }
}
function drawTutPrompt() {
  if (!S || !S.tut) return;
  let st = tutStep(); if (!st) return;
  if (screen === "play" && st === "chute") return;
  if (screen === "para" && st !== "chute") return;
  if (st === "top" && S.t - S.tut.t0 > T.TUT_TOP_S) return;
  if (st === "shelter" && S.tut.shelter && S.tut.shelter.state === "on") st = "shelter_on";
  const [big, small] = tutText(st), h = big.length * 16 + 18, y = screen === "para" ? 46 : 22;
  ctx.fillStyle = "rgba(0,0,0,0.62)"; ctx.fillRect(4, y, W - 8, h);
  ctx.fillStyle = Math.floor(now / 300) % 2 ? C.hardhat : C.acc2;
  ctx.fillRect(4, y, W - 8, 1); ctx.fillRect(4, y + h - 1, W - 8, 1); ctx.fillRect(4, y, 1, h); ctx.fillRect(W - 5, y, 1, h);
  big.forEach((l, i) => textC(l, y + 4 + i * 16, C.hardhat, 2));
  textC(small, y + 6 + big.length * 16, C.white);
  const n = TUT_STEPS.length;                          // lesson dots
  for (let i = 0; i < n; i++) { ctx.fillStyle = i < S.tut.i ? C.acc2 : i === S.tut.i ? C.white : "#504870"; ctx.fillRect(W / 2 - n * 4 + i * 8, y + h + 2, 5, 3); }
}

function endGame(won) {
  const cl = S.cl;
  if (won) {
    const timeBonus = Math.max(0, Math.round(3000 - S.t * 30 / T.CLIMB_LENGTH)), lifeBonus = S.lives * 500, hatBonus = S.hat * 150 + S.hitsAbsorbed * 50;
    S.result = { won, height: S.score, timeBonus, lifeBonus, hatBonus };
    S.score += timeBonus + lifeBonus + hatBonus;
    sfx.win(); cl.arm = "L";
    if (S.score > hiscore) { hiscore = S.score; localStorage.setItem("bc_hi", hiscore); }
    S.resultT = S.t; startEnding(); return;
  } else { S.result = { won }; Loss.sel = 0; sfx.over(); bank(false); }
  if (S.score > hiscore) { hiscore = S.score; localStorage.setItem("bc_hi", hiscore); }
  S.resultT = S.t; inputLockUntil = now + 900;
}

// ---------------------------------------------------------------- rendering
let camPx = 0, shakeX = 0, shakeY = 0;
const sx = (x) => Math.round((x - XL) * P) + shakeX;
const sy = (z) => Math.round((TOP - z) * P) - camPx + shakeY;

let face = "normal";     // the Wizard's face: normal / smile / yawn / sleep
function drawLevel(camZ, mouthOpen) {
  const vh = H / P;
  camPx = Math.round((TOP - (camZ + vh)) * P);
  ctx.fillStyle = LC.bg; ctx.fillRect(0, 0, W, H);
  const y0 = Math.max(0, camPx), y1 = Math.min(A.level_h, camPx + H);
  if (y1 > y0) ctx.drawImage(levelImage(), 0, y0, W, y1 - y0, shakeX, y0 - camPx + shakeY, W, y1 - y0);
  if (face !== "normal" && A.face_y - camPx < H) ctx.drawImage(face === "smile" ? IMG.smile : IMG.sleep, shakeX, A.face_y - camPx + shakeY);
  if (mouthOpen || face === "yawn") ctx.drawImage(IMG.mouth, shakeX, A.mouth_y - camPx + shakeY);
  if (T.NARROW) drawTowerWall();
  drawGround(sy(GROUND_Z));
}
/** Rapunzel: the stone tower either side of her braid. */
function drawTowerWall() {
  for (const c of [0, COLS - 1]) {
    const x0 = sx(c), w = P;
    ctx.fillStyle = "#6c6478"; ctx.fillRect(x0, 0, w, H);
    ctx.fillStyle = "#4a4458";
    const off = (camPx + shakeY) % 8;
    for (let y = -off - 8; y < H; y += 8) {
      ctx.fillRect(x0, y, w, 1);
      const j = Math.floor((y + camPx) / 8) % 2 ? 0 : w / 2;
      ctx.fillRect(x0 + j, y, 1, 8);
    }
    ctx.fillStyle = "#8a8296"; ctx.fillRect(c === 0 ? x0 + w - 2 : x0, 0, 2, H);
  }
}

function climberSprite() {
  const cl = S.cl, tag = S.hat === 3 ? "h0" : S.hat === 2 ? "h1" : S.hat === 1 ? "h2" : "b";
  let pose;
  if (cl.mode === "fall") pose = "fall";
  else if (cl.mode === "dyno") pose = "dyno";
  else if (S.t < cl.braceUntil) pose = "brace";
  else if (cl.tw && !cl.tw.done && cl.tw.toZ !== cl.tw.fromZ) {
    // play the in-between cycle frames: reaching LEFT ends on c0, reaching RIGHT ends on c4
    const k = Math.min(0.999, (S.t - cl.tw.t0) * 1000 / (cl.tw.ms || T.CLIMB_MS));
    const seq = cl.tw.side === "L" ? ["c5", "c6", "c7", "c0"] : ["c1", "c2", "c3", "c4"];
    pose = seq[Math.floor(k * 4)];
  } else if (cl.hold && cl.mode === "climb") pose = "hold";
  else pose = cl.arm === "R" ? "c4" : "c0";
  return { tag, pose };
}

function drawClimber() {
  const cl = S.cl;
  if (S.t < cl.invulnUntil && cl.mode !== "fall" && Math.floor(S.t * 12) % 2) return;  // blink
  const { tag, pose } = climberSprite();
  let x = sx(cl.x), y = sy(cl.z);
  if (S.t - cl.slipT < 0.25) x += Math.round(Math.sin((S.t - cl.slipT) * 60) * 2);
  if (S.sneeze.phase === "blast" && cl.hold) x += (Math.floor(S.t * 30) % 2) ? 1 : -1;
  const head = tag === "b" ? "own" : +tag[1];
  drawPip(x, y, pose, { head, pack: true, cat: S.catOn });
  if (S.t < S.hatFlashUntil && Math.floor(S.t * 20) % 2 === 0) drawPip(x, y, pose, { flash: true });   // hat flashes on a hit
  if (S.t < cl.braceUntil) {                              // brace aura
    ctx.fillStyle = C.acc2;
    for (let i = 0; i < 8; i++) { const a = i / 8 * Math.PI * 2 + S.t * 6; ctx.fillRect(x + Math.round(Math.cos(a) * 20), y - 30 + Math.round(Math.sin(a) * 26), 2, 2); }
  }
  if (DEBUG) { ctx.strokeStyle = "#0f0"; ctx.strokeRect(sx(cl.x - 0.55) + 0.5, sy(cl.z + 2.1) + 0.5, 1.1 * P, 2.2 * P); }
}

function goodSparkle(x, y, t) {    // 4-point twinkles around "good" items (matches the preview art)
  const pts = [[-10, -8], [11, -4], [-6, 10], [9, 9]];
  pts.forEach(([dx, dy], i) => {
    const on = Math.floor(t * 8 + i * 1.7) % 3;
    if (!on) return;
    ctx.fillStyle = i % 2 ? C.white : C.hardhat;
    const r = on === 2 ? 2 : 1;
    ctx.fillRect(x + dx - r, y + dy, 2 * r + 1, 1); ctx.fillRect(x + dx, y + dy - r, 1, 2 * r + 1);
  });
}

function drawWorld() {
  shakeX = S.shake > 0.3 ? Math.round(rand(-S.shake, S.shake)) : 0;
  shakeY = S.shake > 0.3 ? Math.round(rand(-S.shake, S.shake) * 0.5) : 0;
  if (screen === "ending" && S.jigX) shakeX += S.jigX;          // the Elf's happy jig
  drawLevel(S.camZ, S.t < S.mouthOpenUntil);
  drawTownWorld();
  for (const it of S.items) {
    const x = sx(it.x), y = sy(it.z);
    if (y < -30 || y > H + 30) continue;
    if (it.kind === "page") { spr(STORY().pageSpr, x, y + Math.round(Math.sin(it.t * 3) * 1.5)); goodSparkle(x, y, it.t); }
    else if (it.kind === "mush") spr("mushroom", x, y + Math.round(Math.abs(Math.sin(it.t * 4)) * -2));
    else { spr("hattangled", x, y); goodSparkle(x, y, it.t); }
  }
  drawBeardGifts();
  if (screen === "play") { drawShelters(false); drawClimber(); drawShelters(true); } else drawStoryPip();
  for (const h of S.haz) {
    const x = sx(h.x), y = sy(h.z);
    if (y < -30 || y > H + 30) continue;
    if (h.good) { spr("hat_" + (Math.floor(h.spin) % 4), x, y); goodSparkle(x, y, S.t); }
    else if (h.gold) {                                        // spun gold coin
      const w = Math.max(1, Math.round(6 * Math.abs(Math.cos(h.spin))));
      ctx.fillStyle = "#7a5410"; ctx.fillRect(x - w - 1, y - 7, w * 2 + 2, 14);
      ctx.fillStyle = C.hardhat; ctx.fillRect(x - w, y - 6, w * 2, 12); goodSparkle(x, y, S.t);
    }
    else spr("haz" + h.kind + "_" + (Math.floor(h.spin) % 4), x, y);
    if (DEBUG) { ctx.strokeStyle = h.good ? "#ff0" : "#f00"; ctx.strokeRect(x - 10.5, y - 10.5, 21, 21); }
  }
  if (screen === "play") { drawSwoop(); drawDark(); drawRockWarn(); }
  // warning arrows for hazards about to drop in from above the screen
  const topZ = S.camZ + H / P;
  for (const h of S.haz) if (!h.deflected && h.emerge <= 0 && h.z > topZ && h.z < topZ + 4 && Math.floor(S.t * 8) % 2) {
    const x = sx(h.tx); ctx.fillStyle = h.good ? C.hardhat : C.shirt;
    for (let i = 0; i < 4; i++) ctx.fillRect(x - 3 + i, 14 + i, 7 - 2 * i, 1);
  }
  for (const f of S.fx) {
    if (f.hat) spr("hat_" + (Math.floor((S.t - f.t0) * 14) % 4), sx(f.x), sy(f.z));
    else { ctx.fillStyle = f.col; ctx.fillRect(sx(f.x), sy(f.z), 2, 2); }
  }
  for (const t of S.texts) {
    const k = (S.t - t.t0) / t.dur, w = textW(t.s);
    const x = Math.max(2, Math.min(W - w - 8, sx(t.x) - (w >> 1)));
    text(t.s, x, sy(t.z + k * 0.8), t.col);
  }
  if (DEBUG) drawDebug();
}

/** Rudolph: dark stretches of mane - only a small warm light round Pip (fades in/out at the edges). */
function darkness() {
  if (!T.DARK || S.result) return 0;
  const p = progress(); let a = 0;
  for (const [f0, f1] of T.DARK) a = Math.max(a, Math.min(1, (p - f0) / 0.04, (f1 - p) / 0.04));
  return Math.max(0, a);
}
/** Dwarf King: flashing red columns where the rockfall is about to come down. */
function drawRockWarn() {
  const sn = S.sneeze;
  if (T.EVENT !== "rockfall" || sn.phase !== "warn" || !sn.cols) return;
  ctx.globalAlpha = 0.2 + 0.15 * (Math.floor(S.t * 6) % 2); ctx.fillStyle = "#ff3020";
  for (const c of sn.cols) ctx.fillRect(sx(c) + 1, 0, P - 2, H);
  ctx.globalAlpha = 1;
  for (const c of sn.cols) textC2("V", sx(c + 0.5), 52, "#ff5040");
}
function drawDark() {
  const a = darkness(); if (a <= 0) return;
  const x = sx(S.cl.x), y = sy(S.cl.z + 1.0), r = 54;
  ctx.save(); ctx.fillStyle = "rgba(4,6,22," + (0.9 * a).toFixed(2) + ")";
  ctx.beginPath(); ctx.rect(0, 0, W, H); ctx.arc(x, y, r, 0, Math.PI * 2, true); ctx.fill("evenodd");
  ctx.fillStyle = "rgba(4,6,22," + (0.45 * a).toFixed(2) + ")";
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.arc(x, y, r - 12, 0, Math.PI * 2, true); ctx.fill("evenodd");
  ctx.restore();
  if (a > 0.5 && Math.floor(S.t * 2) % 2) textC("IT'S DARK! CAREFUL...", 24, "#f0a0a0");
}
function drawSwoop() {
  const sw = S.swoop; if (!sw) return;
  const k = (S.t - sw.t0) / 1.4; if (k > 1) { S.swoop = null; return; }
  const d = sw.dir === "L" ? -1 : 1, x = d > 0 ? -30 + k * (W + 60) : W + 30 - k * (W + 60);
  ctx.save(); if (d > 0) { ctx.translate(Math.round(x) * 2, 0); ctx.scale(-1, 1); }
  spr("haz3_0", Math.round(x), sy(sw.z) + Math.round(Math.sin(k * 12) * 3));
  ctx.restore();
  ctx.fillStyle = C.hardhat;
  for (let i = 1; i < 6; i++) ctx.fillRect(Math.round(x - d * (i * 9 + 10)), sy(sw.z) + 4 + Math.round(Math.sin(k * 12 + i) * 2), 2, 2);   // jingly trail
}

function drawDebug() {
  ctx.globalAlpha = 0.5;
  for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) {
    const k = tileAt(c, r); if (k !== "sparse" && k !== "knot" && k !== "hold") continue;
    ctx.strokeStyle = k === "sparse" ? "#f00" : "#0f0"; ctx.strokeRect(sx(c) + 0.5, sy(r + 1) + 0.5, P - 1, P - 1);
  }
  ctx.globalAlpha = 1;
  text("Z " + S.cl.z.toFixed(2) + " C" + S.cl.col + " FPS " + fps, 2, H - 26, "#0f0");
}

const PAGE_ICON = ["11110", "10011", "11111", "10001", "11111", "10001", "11111"];
const HEART = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"];
const PIP = ["0011100", "0111110", "1111111"];
function bitmap(rows, x, y, col, edge) {
  if (edge) { ctx.fillStyle = edge; ctx.fillRect(x - 1, y - 1, rows[0].length + 2, rows.length + 2); }
  ctx.fillStyle = col;
  rows.forEach((r, j) => { for (let i = 0; i < r.length; i++) if (r[i] === "1") ctx.fillRect(x + i, y + j, 1, 1); });
}
const MUTE = { x: W - 17, y: () => H - 15, w: 15, h: 13 };
function drawMute() {
  const x = MUTE.x, y = MUTE.y();
  ctx.fillStyle = "rgba(0,0,0,0.55)"; ctx.fillRect(x, y, MUTE.w, MUTE.h);
  ctx.fillStyle = C.white;
  ctx.fillRect(x + 3, y + 5, 2, 3); ctx.fillRect(x + 5, y + 4, 1, 5); ctx.fillRect(x + 6, y + 3, 1, 7);
  if (Snd.muted) { ctx.fillStyle = C.shirt; for (let i = 0; i < 5; i++) { ctx.fillRect(x + 8 + i, y + 4 + i, 1, 1); ctx.fillRect(x + 12 - i, y + 4 + i, 1, 1); } }
  else { ctx.fillRect(x + 8, y + 5, 1, 3); ctx.fillRect(x + 10, y + 4, 1, 5); }
}

function drawHUD() {
  ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(0, 0, W, 11);
  text(String(S.score).padStart(6, "0"), 3, 2, C.white);
  const ml = S.maxLives || 3, hx = ml > 3 ? 88 : 84;
  for (let i = 0; i < ml; i++) bitmap(HEART, 48 + i * (ml > 3 ? 8 : 9), 3, i < S.lives ? C.shirt : "#3a2a50");
  if (S.hat > 0) {                                     // hard-hat pips = hits left
    text("HAT", hx, 2, C.hardhat);
    for (let i = 0; i < 3; i++) bitmap(PIP, hx + 20 + i * 9, 5, i < S.hat ? C.hardhat : "#3a2a50");
  }
  drawBoostHUD();
  bitmap(PAGE_ICON, 137, 2, C.white, "#000"); text(S.pages + "/" + T.PAGES, 145, 2, C.white);
  const best = "HI " + String(Math.max(hiscore, S.score)).padStart(6, "0");
  text(best, W - textW(best) - 3, 2, C.acc2);
  if (easy) { ctx.fillStyle = "#2a8a3a"; ctx.fillRect(2, 13, textW("EASY") + 4, 9); text("EASY", 4, 14, C.white); }
  // height meter (right edge)
  const mx = W - 6, m0 = 16, m1 = H - 22;
  ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(mx - 1, m0 - 1, 4, m1 - m0 + 2);
  ctx.fillStyle = C.hair1; ctx.fillRect(mx, m0, 2, m1 - m0);
  const my = Math.round(m1 - (m1 - m0) * progress());
  ctx.fillStyle = C.hardhat; ctx.fillRect(mx, my, 2, m1 - my);
  ctx.fillStyle = C.skin; ctx.fillRect(mx - 1, m0 - 3, 4, 3);
  ctx.fillStyle = C.white; ctx.fillRect(mx - 2, my - 1, 6, 2);
  // sneeze warning
  const sn = S.sneeze;
  if (sn.phase === "warn" && Math.floor(S.t * 6) % 2 === 0) {
    ctx.fillStyle = "rgba(0,0,0,0.7)"; ctx.fillRect(20, 36, W - 40, S.seenSneeze ? 14 : 24);
    textC(T.EVENT === "gust" ? (sn.dir === "L" ? "<<< WIND GUST <<<" : ">>> WIND GUST >>>") : sn.swoop ? EVENT_TXT.swoop : EVENT_TXT[T.EVENT] || EVENT_TXT.sneeze, 40, C.hardhat);
    if (!S.seenSneeze) textC(sn.swoop ? "DODGE THE PRESENTS!" : "PRESS + HOLD TO HOLD TIGHT", 50, C.white);
  }
  if (T.EVENT === "gust" && sn.phase !== "none") {     // wind streaks blowing across the screen
    const d = sn.dir === "L" ? -1 : 1, k = sn.phase === "blast" ? 2.2 : 1;
    ctx.fillStyle = "rgba(255,255,255,0.75)";
    for (let i = 0; i < 9 * k; i++) {
      const y = 30 + ((i * 67) % (H - 60)), x = ((S.t * 260 * k * d + i * 97) % (W + 40) + W + 40) % (W + 40) - 20;
      ctx.fillRect(Math.round(x), y, 10 + (i % 3) * 6, 1);
    }
  }
  if (T.MELT_S) {                                       // Ice Giant: a gentle melt timer (bar under the HUD)
    const k = Math.max(0, 1 - S.t / T.MELT_S), w = Math.round((W - 60) * k), low = k < 0.25;
    ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(28, 13, W - 56, 7);
    ctx.fillStyle = low && Math.floor(S.t * 4) % 2 ? C.white : "#7cc8f0"; ctx.fillRect(30, 15, w, 3);
    text("MELT", 2, 13, "#a8d8f8");
    if (low && !S.result) textC("HURRY! IT'S MELTING!", 24, Math.floor(S.t * 4) % 2 ? C.white : "#7cc8f0");
  }
  if (S.t < 1.6 && !S.result) textC("GO!", 60, C.hardhat, 3);
  if (!S.result) drawButton(PAUSE_BTN(), "PAUSE", false);
  drawMute();
}

function panel(y, h) { ctx.fillStyle = "rgba(0,0,0,0.72)"; ctx.fillRect(8, y, W - 16, h); ctx.fillStyle = C.hardhat; ctx.fillRect(8, y, W - 16, 1); ctx.fillRect(8, y + h - 1, W - 16, 1); }

function drawResult() {
  const r = S.result, cy = r.won ? H - 124 : Math.round(H / 2) - 54;   // keep the face + climber visible on a win
  panel(cy, r.won ? 108 : 132);
  if (r.won) {
    textC("LEVEL COMPLETE!", cy + 8, C.hardhat, 2);
    const lines = [["HEIGHT", r.height], ["TIME BONUS", r.timeBonus], ["LIVES BONUS", r.lifeBonus], ["HAT BONUS", r.hatBonus]];
    lines.forEach(([l, v], i) => { if (k > 0.3 + i * 0.25) { text(l, 30, cy + 32 + i * 11, C.white); const s = String(v); text(s, W - 30 - textW(s), cy + 32 + i * 11, C.white); } });
    if (k > 1.4) { text("SCORE", 30, cy + 80, C.acc2); const s = String(S.score); text(s, W - 30 - textW(s), cy + 80, C.acc2); }
  } else {
    textC(S.melted ? "IT MELTED!" : "GAME OVER", cy + 14, C.shirt, 2);
    textC("SCORE " + S.score, cy + 44, C.white);
    textC("HEIGHT " + Math.round(progress() * 100) + "%", cy + 58, C.white);
  }
  if (!r.won && r.earned !== undefined) textC("+" + r.earned + " COINS   WALLET " + wallet, cy + 74, C.hardhat);
  if (!r.won) { const L = lossLayout(); ["retry", "levels", "settings"].forEach((id, i) => drawButton(L[id], id.toUpperCase(), Loss.sel === i)); }
}

const Loss = { sel: 0 };
function lossLayout() {
  const y = Math.round(H / 2) + 40;
  return { retry: { x: 10, y, w: 64, h: 26 }, levels: { x: 80, y, w: 64, h: 26 }, settings: { x: 150, y, w: 64, h: 26 } };
}
function lossAct(i) {
  if (i === 0) { newGame(); setScreen("play"); }
  else if (i === 1) openLevels("loss");
  else openSettings("loss");
}
function lossKey(code) {
  if (now < inputLockUntil) return;
  if (["ArrowLeft", "ArrowUp", "KeyA", "KeyW"].includes(code)) Loss.sel = (Loss.sel + 2) % 3;
  else if (["ArrowRight", "ArrowDown", "KeyD", "KeyS"].includes(code)) Loss.sel = (Loss.sel + 1) % 3;
  else if (code === "Enter" || code === "Space") lossAct(Loss.sel);
  else if (code === "Escape" || code === "Backspace") setScreen("title");
}

// title / how-to screens --------------------------------------------------------------
function drawTitle() {
  const t = now / 1000, vh = H / P, bottom = TOP - A.level_h / P;
  // slow pan up the beard, face at the top
  const span = TOP - vh - bottom, ph = (t * 0.06) % 2, k = ph < 1 ? ph : 2 - ph;
  shakeX = shakeY = 0;
  drawLevel(bottom + span * (k * k * (3 - 2 * k)), Math.floor(t * 1.2) % 3 === 0);
  ctx.fillStyle = "rgba(0,0,0,0.45)"; ctx.fillRect(0, 0, W, H);
  const y = Math.round(H * 0.24);
  textC("BEARD", y, C.hardhat, 4); textC("CLIMBER", y + 34, C.hardhat, 4);
  textC("LEVEL " + LEVEL_NAMES[LEVEL], y + 72, C.acc2);
  drawPip(W / 2, y + 160, "c" + (Math.floor(t * 6) % 8), { head: 0, pack: true, cat: true });
  if (Math.floor(t * 2.2) % 2 === 0) textC("TAP TO START", y + 172, C.white, 2);
  drawButton(TITLE_INTRO_BTN(), "WATCH INTRO", false);
  drawButton(TITLE_LEVELS_BTN(), "LEVELS", false);
  drawButton(TITLE_SHOP_BTN(), "SHOP", false, C.acc2);
  drawWallet(4, 4);
  drawGear(TITLE_GEAR_BTN());
  textC("HI " + String(hiscore).padStart(6, "0"), H - 12, C.white);
  drawMute();
}

function drawHowto() {
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H);
  const oy = Math.max(0, Math.round((H - 300) / 2));
  textC("HOW TO PLAY", oy + 6, C.hardhat, 2);
  for (let x = 12; x < W - 12; x++) if (x % 4 < 2) { ctx.fillStyle = C.hardhat; ctx.fillRect(x, oy + 24, 1, 1); }
  let y = oy + 32;
  const t = now / 1000, tx = 48;
  const row = (icon, lines, col = C.white) => {
    icon(26, y + 9);
    lines.forEach((l, i) => text(l, tx, y + i * 9, i === 0 ? col : C.hair3));
    y += Math.max(30, lines.length * 9 + 6);
  };
  const cycle = Math.floor(t * 2) % 2;
  if (controls === "one") {
    row((x, yy) => miniPip(cycle ? "c4" : "c0", x, yy + 2), ["ONE HAND: TAP ANYWHERE", "EACH TAP MOVES THE NEXT ARM", "TAP, TAP, TAP TO CLIMB"]);
    row((x, yy) => miniPip("dyno", x, yy + 2), ["SWIPE LEFT / RIGHT: HOP", "SWIPE DOWN: CLIMB DOWN", "SWIPE UP: QUICK DOUBLE REACH"]);
  } else {
    row((x, yy) => miniPip(cycle ? "c4" : "c0", x, yy + 2),
        ["TAP LEFT / RIGHT HALF", "ALTERNATE L-R-L-R TO CLIMB", "(SAME ARM TWICE: NO CLIMB)"]);
    row((x, yy) => miniPip("dyno", x, yy + 2), ["DOUBLE-TAP ONE SIDE", "LEAP ONE COLUMN SIDEWAYS", "SWIPE DOWN: CLIMB DOWN"]);
  }
  row((x, yy) => miniPip("hold", x, yy + 2), ["PRESS + HOLD: HOLD TIGHT", "TWO-FINGER TAP: BRACE (1 HIT)"]);
  row((x, yy) => { for (let i = 0; i < 3; i++) spr("mini_haz" + i, x - 13 + i * 13, yy + 3 + (Math.floor(t * 3 + i) % 2)); },
      ["DODGE WHAT HE SPITS OUT:", A.hazard_names.map((n) => n.replace(/_/g, " ")).join(", ")]);
  row((x, yy) => { spr("hat_" + (Math.floor(t * 4) % 4), x, yy + 2); goodSparkle(x, yy + 2, t); },
      ["GRAB A HARD HAT!", "IT BLOCKS 3 HITS, THEN POPS"], C.hardhat);
  row((x, yy) => { const f = F["tile_sparse"]; ctx.drawImage(IMG.atlas, f[0], f[1], 32, 32, x - 12, yy - 10, 24, 24); },
      ["BALD PATCHES: NO GRIP!", "LEAP AROUND THEM"]);
  text("KEYS: <  > ARMS   DOWN/SPACE BRACE", 8, y + 2, C.hair3);
  text("HOLD ^ = HOLD TIGHT  X DOWN  M MUTE", 8, y + 12, C.hair3);
  if (Math.floor(t * 2.2) % 2 === 0) textC(SKIP_TOP ? "TAP TO CLIMB!" : "TAP TO MAKE YOUR PIP!", Math.min(H - 14, y + 30), C.hardhat);
}

let fps = 0, fpsN = 0, fpsT = 0;
function frame(ts) {
  requestAnimationFrame(frame);
  const dt = Math.min(0.05, Math.max(0, (ts - (lastFrame || ts)) / 1000));
  lastFrame = ts; now = ts;
  fpsN++; if (ts - fpsT > 1000) { fps = fpsN; fpsN = 0; fpsT = ts; }
  for (const k in IMG) if (!IMG[k].complete) return;
  if (screen === "title") drawTitle();
  else if (screen === "howto") drawHowto();
  else if (screen === "creator") drawCreator();
  else if (screen === "cine") { if (!paused) Cine.t += dt; drawCine(); }
  else if (screen === "intro") { if (!paused) updateIntro(dt); drawIntro(); }
  else if (screen === "play") {
    if (!paused) update(dt);
    if (screen === "play") { drawWorld(); drawHUD(); drawTutPrompt(); if (S.result) drawResult(); }
    else { drawWorld(); }
  }
  else if (screen === "ending") { if (!paused) updateEnding(dt); drawWorld(); drawEnding(); }
  else if (screen === "para") { if (!paused) updatePara(dt); drawWorld(); drawPara(); }
  else if (screen === "bird") { if (!paused) updateBird(dt); drawWorld(); drawBird(); }
  else if (screen === "results") drawResults();
  else if (screen === "shop") drawShop();
  else if (screen === "levels") drawLevels();
  else if (screen === "settings") drawSettings();
  else if (screen === "choose") drawChoose();
  if (paused) drawPaused();
  if (loadError && now - loadError.t < 3000) { panel(H / 2 - 20, 40); loadError.lines.forEach((l, i) => textC(l, H / 2 - 10 + i * 12, C.hardhat)); }
  if (loadingUntil > now) { ctx.fillStyle = "rgba(10,8,30,0.85)"; ctx.fillRect(0, H / 2 - 14, W, 28); textC("LOADING" + ".".repeat(1 + Math.floor(now / 300) % 3), H / 2 - 4, C.hardhat); }
  Poki.loaded();
}

// ================================================================ Pip: layered, palette-swapped sprites
// The Blender layers in A.pip use KEY colours (A.keys). A look maps each key role to a colour from
// the curated preset lists below, the layers are stacked (body, hair, backpack, cat, headgear),
// recoloured and given the same 1px black outline as postprocess.py. Results are cached.
const SKINS = [["#fce0cc", "#e8b4a0"], ["#f0c0a0", "#d09078"], ["#e0a878", "#b87c58"], ["#c88058", "#985838"],
               ["#9c5c38", "#744028"], ["#6c3c24", "#4c2818"]];
const HAIR_COLS = [["BLACK", "#282028", "#484050"], ["BROWN", "#5c3418", "#7c4c28"], ["GINGER", "#c05c20", "#e08038"],
                   ["BLONDE", "#e8c050", "#f8e090"], ["GREY", "#a8a8b8", "#d0d0dc"], ["BLUE", "#3c70e0", "#70a0f8"],
                   ["PINK", "#e060a8", "#f898d0"]];
const OUTFITS = [["RED", "#e83828", "#a82018", "#2848b8"], ["BLUE", "#3870e8", "#2048a8", "#283878"],
                 ["GREEN", "#40b048", "#287830", "#5c4030"], ["PURPLE", "#9048d0", "#603090", "#383058"],
                 ["ORANGE", "#f88828", "#c05818", "#2848b8"], ["PINK", "#f070b0", "#c04888", "#5048a0"],
                 ["TEAL", "#20b0a8", "#187c78", "#304060"]];
const GEARS = [["YELLOW", "#f8b800", "#b87800"], ["GREEN", "#58c838", "#358020"], ["BLUE", "#40a0f0", "#2068b0"],
               ["RED", "#e04040", "#a02828"], ["ORANGE", "#f88820", "#b85810"], ["PURPLE", "#a060e0", "#6838a0"]];
const HAT_NAMES = ["NONE"].concat(A.hats.map((h) => h.toUpperCase()));   // NONE + 3 free hats + shop hats
const DEFAULT_LOOK = { body: 0, hair: 0, hairCol: 1, skin: 3, outfit: 0, gear: 2, hat: 1, pattern: 0, pack: 0, chute: 0 };
function lookColors(lk) {
  const sk = SKINS[lk.skin], hc = HAIR_COLS[lk.hairCol], o = OUTFITS[lk.outfit], g = GEARS[lk.gear];
  return { k_skin: sk[0], k_skin_shade: sk[1], k_hair: hc[1], k_hair_shade: hc[2], k_shirt: o[1], k_shirt_shade: o[2],
           k_pants: o[3], k_gear: g[1], k_gear_shade: g[2], k_hat: g[1], k_hat_shade: g[2] };
}
function loadLook() {
  try { const l = JSON.parse(localStorage.getItem("bc_look")); if (l && typeof l === "object") return sanitizeLook(l); } catch (e) {}
  return Object.assign({}, DEFAULT_LOOK);
}
function sanitizeLook(l) {
  const n = { body: 2, hair: A.hairs.length, hairCol: HAIR_COLS.length, skin: SKINS.length, outfit: OUTFITS.length, gear: GEARS.length,
              hat: HAT_NAMES.length, pattern: A.patterns.length + 1, pack: A.packs.length + 1, chute: A.chutes.length + 1 };
  const out = {};
  for (const k in n) {
    out[k] = Number.isInteger(l[k]) && l[k] >= 0 && l[k] < n[k] ? l[k] : DEFAULT_LOOK[k];
    if (!valueOk(k, out[k])) out[k] = DEFAULT_LOOK[k];     // shop items you don't own come off
  }
  return out;
}
// ================================================================ coin shop: wallet, catalogue, ownership, boosts
// Everything is earned in-game (no real money, ads or links). All state lives in localStorage:
// bc_coins (wallet), bc_owned (bought item ids), bc_cheered (giants cheered up -> their free set),
// bc_boosts (boost id -> count), bc_boost_eq (boosts switched on for the next climb).
const BASE_N = { hairCol: HAIR_COLS.length, outfit: OUTFITS.length, gear: GEARS.length };
HAIR_COLS.push(["LILAC", "#b088e8", "#d0b0f8"]);                 // premium colours (shop only)
OUTFITS.push(["GOLD", "#f8c830", "#c08818", "#7c4c28"]);
GEARS.push(["GOLD", "#f8c830", "#c08818"]);
const GIANT_NAMES = { grandpa: "GRANDPA", goat: "GOAT", lumberjack: "LUMBERJACK", mountain: "MOUNTAIN MAN", bigfoot: "BIGFOOT",
                      elf: "ELF", rudolph: "RUDOLPH", ice: "ICE GIANT", yeti: "YETI",
                      gnome: "GNOME", rumpel: "RUMPELSTILTSKIN", rapunzel: "RAPUNZEL", dwarf: "DWARF KING",
                      wizard: "WIZARD", viking: "VIKING", santa: "SANTA", pirate: "PIRATE" };
const THE_NAMES = { grandpa: "GRANDPA", goat: "THE GOAT", lumberjack: "THE LUMBERJACK", mountain: "MOUNTAIN MAN", bigfoot: "BIGFOOT",
                    elf: "THE ELF", rudolph: "RUDOLPH", ice: "THE ICE GIANT", yeti: "THE YETI",
                    gnome: "THE GNOME", rumpel: "RUMPELSTILTSKIN", rapunzel: "RAPUNZEL", dwarf: "THE DWARF KING",
                    wizard: "THE WIZARD", viking: "THE VIKING", santa: "SANTA", pirate: "THE PIRATE" };
const SHOP_TABS = [["hats", "HATS"], ["outfits", "OUTFIT"], ["packs", "PACKS"], ["chutes", "CHUTES"], ["boosts", "BOOSTS"]];
const CATALOG = [];
function item(tab, id, name, key, val, extra) { CATALOG.push(Object.assign({ tab, id, name, key, val, price: T.PRICES[id] || 0 }, extra)); }
{
  const hat = (n) => 1 + A.hats.indexOf(n), pat = (n) => 1 + A.patterns.indexOf(n), pk = (n) => 1 + A.packs.indexOf(n), ch = (n) => 1 + A.chutes.indexOf(n);
  item("hats", "party", "PARTY HAT", "hat", hat("party"));
  item("hats", "propeller", "PROPELLER CAP", "hat", hat("propeller"));
  item("hats", "crown", "GOLD CROWN", "hat", hat("crown"));
  item("hats", "wizard", "WIZARD HAT", "hat", hat("wizard"), { set: "wizard" });
  item("hats", "trapper", "TRAPPER HAT", "hat", hat("trapper"), { set: "lumberjack" });
  item("hats", "viking", "VIKING HELMET", "hat", hat("viking"), { set: "viking" });
  item("hats", "santa", "SANTA HAT", "hat", hat("santa"), { set: "santa" });
  item("hats", "tricorn", "PIRATE HAT", "hat", hat("tricorn"), { set: "pirate" });
  item("hats", "goathorns", "GOAT HORNS", "hat", hat("goathorns"), { set: "goat" });
  item("hats", "coonskin", "FUR CAP", "hat", hat("coonskin"), { set: "mountain" });
  item("hats", "furhood", "BIGFOOT HOOD", "hat", hat("furhood"), { set: "bigfoot" });
  item("hats", "elfhat", "ELF HAT", "hat", hat("elfhat"), { set: "elf" });
  item("hats", "antlers", "ANTLER HEADBAND", "hat", hat("antlers"), { set: "rudolph" });
  item("hats", "icecrown", "ICE CROWN", "hat", hat("icecrown"), { set: "ice" });
  item("hats", "earmuffs", "YETI EARMUFFS", "hat", hat("earmuffs"), { set: "yeti" });
  item("hats", "gnomehat", "GNOME HAT", "hat", hat("gnomehat"), { set: "gnome" });
  item("hats", "featherhat", "FEATHER HAT", "hat", hat("featherhat"), { set: "rumpel" });
  item("hats", "tiara", "GOLD TIARA", "hat", hat("tiara"), { set: "rapunzel" });
  item("hats", "dwarfhelm", "DWARF HELM", "hat", hat("dwarfhelm"), { set: "dwarf" });
  item("outfits", "stripes", "STRIPY TOP", "pattern", pat("stripes"));
  item("outfits", "overalls", "OVERALLS", "pattern", pat("overalls"));
  item("outfits", "gold_outfit", "GOLD OUTFIT", "outfit", BASE_N.outfit);
  item("outfits", "lilac_hair", "LILAC HAIR", "hairCol", BASE_N.hairCol);
  item("outfits", "robe", "WIZARD ROBE", "pattern", pat("robe"), { set: "wizard" });
  item("outfits", "plaid", "LUMBERJACK PLAID", "pattern", pat("plaid"), { set: "lumberjack" });
  item("outfits", "vest", "VIKING VEST", "pattern", pat("vest"), { set: "viking" });
  item("outfits", "suit", "SANTA SUIT", "pattern", pat("suit"), { set: "santa" });
  item("outfits", "sash", "PIRATE SASH", "pattern", pat("sash"), { set: "pirate" });
  item("outfits", "bandana", "FARM BANDANA", "pattern", pat("bandana"), { set: "goat" });
  item("outfits", "buckskin", "BUCKSKIN JACKET", "pattern", pat("buckskin"), { set: "mountain" });
  item("outfits", "furcoat", "SHAGGY FUR SUIT", "pattern", pat("furcoat"), { set: "bigfoot" });
  item("outfits", "tunic", "ELF TUNIC", "pattern", pat("tunic"), { set: "elf" });
  item("outfits", "jumper", "REINDEER JUMPER", "pattern", pat("jumper"), { set: "rudolph" });
  item("outfits", "frostcape", "FROST CAPE", "pattern", pat("frostcape"), { set: "ice" });
  item("outfits", "scarf", "YETI SCARF", "pattern", pat("scarf"), { set: "yeti" });
  item("outfits", "gnomevest", "GNOME TUNIC", "pattern", pat("gnomevest"), { set: "gnome" });
  item("outfits", "goldvest", "SPUN-GOLD VEST", "pattern", pat("goldvest"), { set: "rumpel" });
  item("outfits", "gown", "TOWER GOWN", "pattern", pat("gown"), { set: "rapunzel" });
  item("outfits", "chainmail", "CHAINMAIL", "pattern", pat("chainmail"), { set: "dwarf" });
  item("packs", "classic", "CLASSIC PACK", "pack", 0, { free: true });
  item("packs", "teddy", "TEDDY PACK", "pack", pk("teddy"));
  item("packs", "rocket", "ROCKET PACK", "pack", pk("rocket"));
  item("packs", "wings", "WING PACK", "pack", pk("wings"));
  item("packs", "gold_gear", "GOLD GEAR", "gear", BASE_N.gear);
  item("chutes", "chute_classic", "CLASSIC STRIPES", "chute", 0, { free: true });
  item("chutes", "dots", "POLKA DOTS", "chute", ch("dots"));
  item("chutes", "stars", "STARRY", "chute", ch("stars"));
  item("chutes", "checker", "CHECKERS", "chute", ch("checker"));
  item("chutes", "rainbow", "RAINBOW", "chute", ch("rainbow"));
  item("boosts", "b_hardhat", "HARD HAT START", null, null, { info: ["START WITH A HARD HAT", "(BLOCKS " + T.START_HAT_HITS + " HITS) - HELPER"] });
  item("boosts", "b_life", "EXTRA LIFE", null, null, { info: [(3 + T.EXTRA_LIVES) + " HEARTS FOR ONE CLIMB", "HELPER BOOST"] });
  item("boosts", "b_magnet", "COIN MAGNET", null, null, { info: ["PULLS NEARBY COINS TO YOU", "IN THE PARACHUTE BONUS"] });
  item("boosts", "b_slowmo", "SLOW-MO", null, null, { info: ["SLOWER HAZARDS FOR THE", "FIRST " + T.SLOWMO_S + " S - HELPER BOOST"] });
}
const CAT_BY_ID = Object.fromEntries(CATALOG.map((i) => [i.id, i]));
function stored(k, d, ok) { try { const v = JSON.parse(localStorage.getItem(k)); return v !== null && ok(v) ? v : d; } catch (e) { return d; } }
let wallet = Math.max(0, Math.floor(+localStorage.getItem("bc_coins") || 0));
let owned = new Set(stored("bc_owned", [], Array.isArray).filter((id) => CAT_BY_ID[id]));
let cheered = new Set(stored("bc_cheered", [], Array.isArray).filter((g) => GIANT_NAMES[g]));
// World 1 grew in front of the Wizard: anyone who had him open before (cheered Grandpa in the old build) keeps him.
if (localStorage.getItem("bc_w1") !== "1") {
  if (cheered.has("grandpa") || cheered.has("wizard")) localStorage.setItem("bc_wiz_open", "1");
  localStorage.setItem("bc_w1", "1");
}
// World 2 grew in front of the Wizard: anyone who cheered Bigfoot (who used to unlock him) keeps him.
if (localStorage.getItem("bc_w2") !== "1") {
  if (cheered.has("bigfoot") || cheered.has("wizard")) localStorage.setItem("bc_wiz_open", "1");
  localStorage.setItem("bc_w2", "1");
}
// World 3 grew in front of the Wizard: anyone who cheered Santa (who used to unlock him) keeps him.
if (localStorage.getItem("bc_w3") !== "1") {
  if (cheered.has("santa") || cheered.has("wizard")) localStorage.setItem("bc_wiz_open", "1");
  localStorage.setItem("bc_w3", "1");
}
let boosts = {};
{ const b = stored("bc_boosts", {}, (v) => typeof v === "object"); for (const i of CATALOG) if (i.tab === "boosts") boosts[i.id] = Math.max(0, Math.min(T.BOOST_STACK, Math.floor(+b[i.id] || 0))); }
let boostEq = stored("bc_boost_eq", [], Array.isArray).filter((id) => boosts[id] > 0)
  .filter((id, i, a) => a.indexOf(id) === i && !(T.DEFENSIVE.includes(id) && a.slice(0, i).some((x) => T.DEFENSIVE.includes(x)))).slice(0, T.MAX_BOOSTS);
function saveShop() {
  localStorage.setItem("bc_coins", String(wallet)); localStorage.setItem("bc_owned", JSON.stringify([...owned]));
  localStorage.setItem("bc_cheered", JSON.stringify([...cheered])); localStorage.setItem("bc_boosts", JSON.stringify(boosts));
  localStorage.setItem("bc_boost_eq", JSON.stringify(boostEq));
}
if (DEBUG && params.get("coins")) { wallet += Math.max(0, Math.floor(+params.get("coins") || 0)); saveShop(); }   // ?debug=1&coins=500
function isOwned(it) { return !!it && (it.free || owned.has(it.id) || (!!it.set && cheered.has(it.set))); }
function itemFor(key, val) { return CATALOG.find((i) => i.key === key && i.val === val); }
function valueOk(key, val) { const it = itemFor(key, val); return !it || isOwned(it); }
function lockText(it) { return "CHEER UP " + THE_NAMES[it.set] + " TO UNLOCK"; }
/** Coins for a finished run go into the wallet once. Win: chute coins + stars + pages + bonus; loss: pages + height. */
function bank(won) {
  const r = S.result; if (!r || r.banked) return;
  r.earned = won ? Para.coins * T.EARN_COIN + Para.stars * T.EARN_STAR + S.pages * T.EARN_PAGE + T.EARN_WIN
                 : S.pages * T.EARN_PAGE + Math.floor(progress() * T.EARN_HEIGHT);
  r.earned += (S.goldGot || 0) * T.EARN_GOLD;
  if (easy) r.earned = Math.round(r.earned * EASY_COIN_K);
  r.banked = true; wallet += r.earned; saveShop();
}
/** Boosts switched on are used up when a climb starts. */
function applyBoosts() {
  S.boosts = [];
  for (const id of boostEq) {
    if (!(boosts[id] > 0) || S.boosts.length >= T.MAX_BOOSTS || (isDef(id) && S.boosts.some(isDef))) continue;
    boosts[id]--; S.boosts.push(id);
    if (id === "b_hardhat") S.hat = T.START_HAT_HITS;
    else if (id === "b_life") { S.lives = 3 + T.EXTRA_LIVES; S.maxLives = S.lives; }
    else if (id === "b_magnet") S.magnet = true;
    else if (id === "b_slowmo") S.slowUntil = T.SLOWMO_S;
  }
  boostEq = boostEq.filter((id) => boosts[id] > 0);
  if (S.boosts.length) saveShop();
}
function slowK() { return S && S.t < S.slowUntil ? T.SLOWMO_K : 1; }
const isDef = (id) => T.DEFENSIVE.includes(id);
/** Hazard pacing at progress p: {throwK: interval multiplier, fallK: speed multiplier, aim}. */
function hazardPace(p) {
  const up = p >= T.UPPER_P, def = S && S.boosts && S.boosts.some(isDef) ? T.DEF_BOOST_K : 1;
  return { throwK: (up ? T.UPPER_THROW_K : 1) / def / slowK(), fallK: (up ? T.UPPER_FALL_K : 1) * def * slowK(),
           aim: T.AIM + (T.AIM_TOP - T.AIM) * p, pair: up ? T.UPPER_PAIR : 0 };
}
let look = loadLook();
function saveLook() { localStorage.setItem("bc_look", JSON.stringify(look)); }
// townsfolk of Whiskerton (same rig, front view, smaller)
const TOWN = [
  { x: -0.12, look: { body: 1, hair: 3, hairCol: 3, skin: 1, outfit: 5, gear: 2, hat: 0 } },
  { x: 0.72, look: { body: 0, hair: 1, hairCol: 0, skin: 5, outfit: 2, gear: 0, hat: 2 } },
  { x: 1.5, look: { body: 1, hair: 2, hairCol: 1, skin: 3, outfit: 3, gear: 3, hat: 3 } },
  { x: 4.62, look: { body: 0, hair: 0, hairCol: 4, skin: 2, outfit: 1, gear: 4, hat: 1 } },
  { x: 5.5, look: { body: 1, hair: 1, hairCol: 2, skin: 4, outfit: 6, gear: 1, hat: 0 } },
];

const PF = A.pframes;
let keyPx = null;
function keyPixels() {
  if (keyPx) return keyPx;
  const c = document.createElement("canvas"); c.width = IMG.pip.width; c.height = IMG.pip.height;
  const g = c.getContext("2d"); g.drawImage(IMG.pip, 0, 0);
  keyPx = { w: c.width, d: g.getImageData(0, 0, c.width, c.height).data };
  return keyPx;
}
const hexN = (h) => parseInt(h.slice(1), 16);
const mapCache = new Map();
function colorMap(lk) {
  const key = JSON.stringify(lk);
  let m = mapCache.get(key); if (m) return m;
  m = new Map(); const cols = lookColors(lk);
  for (const role in cols) m.set(hexN(A.keys[role]), hexN(cols[role]));
  mapCache.set(key, m); return m;
}
function outlineData(o, w, h) {
  const a = new Uint8Array(w * h);
  for (let i = 0; i < w * h; i++) a[i] = o[i * 4 + 3] ? 1 : 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x; if (a[i]) continue;
    if ((x > 0 && a[i - 1]) || (x < w - 1 && a[i + 1]) || (y > 0 && a[i - w]) || (y < h - 1 && a[i + w])) { o[i * 4 + 3] = 255; }
  }
}
const spriteCache = new Map();
/** Stack keyed layers (names in A.pframes) into one outlined canvas. offs: frames are [x,y,w,h,offx,offy]. */
function compose(names, w, h, ox, oy, lk, flash) {
  const ck = names.join("|") + (flash ? "#F" : JSON.stringify(lk));
  let c = spriteCache.get(ck); if (c) return c;
  if (spriteCache.size > 600) spriteCache.clear();
  const K = keyPixels(), out = new ImageData(w, h), o = out.data, mp = colorMap(lk);
  for (const n of names) {
    const f = PF[n]; if (!f) continue;
    for (let y = 0; y < f[3]; y++) for (let x = 0; x < f[2]; x++) {
      const si = ((f[1] + y) * K.w + f[0] + x) * 4; if (K.d[si + 3] < 128) continue;
      const dx = f[4] + x + ox, dy = f[5] + y + oy; if (dx < 0 || dy < 0 || dx >= w || dy >= h) continue;
      const di = (dy * w + dx) * 4;
      let v = (K.d[si] << 16) | (K.d[si + 1] << 8) | K.d[si + 2];
      if (flash) v = 0xf8f8f8; else { const m = mp.get(v); if (m !== undefined) v = m; }
      o[di] = v >> 16; o[di + 1] = (v >> 8) & 255; o[di + 2] = v & 255; o[di + 3] = 255;
    }
  }
  if (!flash) outlineData(o, w, h);
  c = document.createElement("canvas"); c.width = w; c.height = h; c.getContext("2d").putImageData(out, 0, 0);
  spriteCache.set(ck, c); return c;
}
function pipLayers(pose, o, lk) {
  const P = (l) => "p_" + l + "_" + pose, front = pose.startsWith("f_");
  if (o.flash) return [P("hh0")];
  const L = [P(A.bodies[lk.body])];
  if (lk.pattern > 0) L.push(P(A.patterns[lk.pattern - 1]));      // shop outfit pattern over the body
  L.push(P(A.hairs[lk.hair]));
  if (o.pack) L.push(P(lk.pack > 0 ? A.packs[lk.pack - 1] : "pack"));
  if (o.cat && !front) L.push(P("cat"));
  if (typeof o.head === "number") L.push(P("hh" + o.head));
  else if (o.head !== "none" && lk.hat > 0) L.push(P(A.hats[lk.hat - 1]));
  return L;
}
/** Draw Pip with its root (feet) at (x, y). o: {head: "own"|0|1|2, pack, cat, flash, look, scale}. */
function pipCanvas(pose, o = {}) {
  const lk = o.look || look, cell = A.pip_cell;
  return compose(pipLayers(pose, o, lk), cell + 2, cell + 2, 1, 1, lk, o.flash);
}
function drawPip(x, y, pose, o = {}) {
  const c = pipCanvas(pose, o), an = pose === "fall" ? A.fall_anchor : A.pip_anchor, k = o.scale || 1;
  ctx.drawImage(c, Math.round(x - (an[0] + 1) * k), Math.round(y - (an[1] + 1) * k), c.width * k, c.height * k);
}
const miniCache = {};
function miniPip(pose, x, y) {              // half-size icons for the how-to screen
  const key = pose + JSON.stringify(look);
  let m = miniCache[key];
  if (!m) {
    const c = pipCanvas(pose, { head: "own", pack: true, cat: true });
    const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;   // crop to the opaque bounds
    let x0 = c.width, y0 = c.height, x1 = 0, y1 = 0;
    for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) if (d[(y * c.width + x) * 4 + 3]) {
      x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
    m = document.createElement("canvas"); m.width = (x1 - x0 + 2) >> 1; m.height = (y1 - y0 + 2) >> 1;
    const g = m.getContext("2d"); g.imageSmoothingEnabled = false;
    g.drawImage(c, x0, y0, x1 - x0 + 1, y1 - y0 + 1, 0, 0, m.width, m.height);
    miniCache[key] = m;
  }
  ctx.drawImage(m, Math.round(x - m.width / 2), Math.round(y - m.height / 2));
}
function drawTownie(i, x, y, pose) {
  const lk = TOWN[i].look, cell = A.town_cell, an = A.town_anchor;
  const L = ["t_" + A.bodies[lk.body] + "_" + pose, "t_" + A.hairs[lk.hair] + "_" + pose];
  if (lk.hat > 0) L.push("t_" + A.hats[lk.hat - 1] + "_" + pose);
  const c = compose(L, cell + 2, cell + 2, 1, 1, lk);
  ctx.drawImage(c, Math.round(x - an[0] - 1), Math.round(y - an[1] - 1));
}
/** A keyed story prop (backpack, parachute, sleeping cat), recoloured with Pip's look. */
function drawProp(name, x, y, lk) {
  const f = PF["s_" + name]; if (!f) return;
  const c = compose(["s_" + name], f[2] + 2, f[3] + 2, -f[4] + 1, -f[5] + 1, lk || look);
  ctx.drawImage(c, Math.round(x + f[4] - 1), Math.round(y + f[5] - 1));
}
function sprRot(name, x, y, q) {             // atlas sprite rotated by q quarter turns (pixel exact)
  const f = F[name]; if (!f) return;
  ctx.save(); ctx.translate(Math.round(x), Math.round(y)); ctx.rotate((q % 4) * Math.PI / 2);
  ctx.drawImage(f[6] || IMG.atlas, f[0], f[1], f[2], f[3], -f[4], -f[5], f[2], f[3]); ctx.restore();
}

// ================================================================ Whiskerton: ground + townsfolk
const GRASS_W1 = ["#58b848", "#38883c", "#285c30", "#5c3c28", "#3c2818"];
const SNOW = ["#f8f8f8", "#d8e4f0", "#b8c8e0", "#8ca0c0", "#a8bcd8"];
function drawGround(y) {
  if (y >= H) return;
  const GRASS = screen !== "cine" && W2.includes(LEVEL) ? SNOW : GRASS_W1;   // World 2: snowy ground
  ctx.fillStyle = GRASS[1]; ctx.fillRect(0, y, W, H - y);
  ctx.fillStyle = GRASS[0]; ctx.fillRect(0, y, W, 2);
  ctx.fillStyle = GRASS[2]; for (let x = 0; x < W; x += 7) ctx.fillRect(x + ((x * 13) % 5), y + 4 + ((x * 7) % 4), 2, 1);
  ctx.fillStyle = GRASS[3]; ctx.fillRect(0, y + 11, W, H - y - 11);
  ctx.fillStyle = GRASS[4]; for (let x = 0; x < W; x += 9) ctx.fillRect(x + ((x * 5) % 4), y + 14 + ((x * 3) % 6), 3, 2);
}
function townPose(i, t, mode) {             // mode: cheer / duck / stand
  if (mode === "duck") return "duck";
  if (mode === "stand") return "stand";
  return Math.floor(t * 3.2 + i * 0.7) % 2 ? "cheer" : "stand";
}
function drawTownWorld() {                  // the crowd at the foot of the beard (intro, climb start, bird)
  const y = sy(GROUND_Z) + 1;
  if (y < -10 || y > H + 70) return;
  const t = now / 1000, mode = screen === "intro" && Intro.t < 0.4 ? "stand" : "cheer";
  TOWN.forEach((p, i) => {
    const pose = townPose(i, t, mode), hop = pose === "cheer" ? (Math.floor(t * 6.4 + i) % 2 ? 2 : 1) : 0;
    drawTownie(i, sx(p.x), y - hop, pose);
  });
}

// ================================================================ captions + buttons
function caption(lines, t, y) {
  if (typeof lines === "string") lines = [lines];
  const h = lines.length * 10 + 6; y = y === undefined ? H - h - 4 : y;
  ctx.fillStyle = "rgba(0,0,0,0.78)"; ctx.fillRect(4, y, W - 8, h);
  ctx.fillStyle = C.hardhat; ctx.fillRect(4, y, W - 8, 1); ctx.fillRect(4, y + h - 1, W - 8, 1);
  let n = Math.floor(t * 45);                 // typewriter
  lines.forEach((l, i) => { const s = l.slice(0, Math.max(0, n)); n -= l.length; text(s, Math.round((W - textW(l)) / 2), y + 4 + i * 10, C.white); });
}
function skipHint() { if (Math.floor(now / 500) % 2 === 0) text("TAP TO SKIP", W - textW("TAP TO SKIP") - 3, 3, "#a0a0c0"); }
function drawButton(b, label, hot, col) {
  ctx.fillStyle = hot ? C.hardhat : "rgba(0,0,0,0.65)"; ctx.fillRect(b.x, b.y, b.w, b.h);
  ctx.fillStyle = col || C.hardhat; ctx.fillRect(b.x, b.y, b.w, 1); ctx.fillRect(b.x, b.y + b.h - 1, b.w, 1);
  ctx.fillRect(b.x, b.y, 1, b.h); ctx.fillRect(b.x + b.w - 1, b.y, 1, b.h);
  text(label, b.x + Math.round((b.w - textW(label)) / 2), b.y + Math.round((b.h - 7) / 2), hot ? "#000" : C.white, 1, hot ? null : "#000");
}
const inRect = (p, b) => p.x >= b.x && p.x < b.x + b.w && p.y >= b.y && p.y < b.y + b.h;
const TITLE_INTRO_BTN = () => ({ x: 6, y: H - 44, w: 68, h: 22 });
const TITLE_LEVELS_BTN = () => ({ x: 78, y: H - 44, w: 68, h: 22 });
const TITLE_SHOP_BTN = () => ({ x: 150, y: H - 44, w: 68, h: 22 });
const TITLE_GEAR_BTN = () => ({ x: W - 24, y: 3, w: 21, h: 19 });
function drawGear(b) {
  ctx.fillStyle = "rgba(0,0,0,0.65)"; ctx.fillRect(b.x, b.y, b.w, b.h);
  ctx.fillStyle = C.hardhat; ctx.fillRect(b.x, b.y, b.w, 1); ctx.fillRect(b.x, b.y + b.h - 1, b.w, 1); ctx.fillRect(b.x, b.y, 1, b.h); ctx.fillRect(b.x + b.w - 1, b.y, 1, b.h);
  const cx = b.x + b.w / 2, cy = b.y + b.h / 2;
  ctx.fillStyle = C.white;
  for (let a = 0; a < 8; a++) { const x = Math.round(cx + Math.cos(a * Math.PI / 4) * 5.5), y = Math.round(cy + Math.sin(a * Math.PI / 4) * 5.5); ctx.fillRect(x - 1, y - 1, 3, 3); }
  for (let y = -4; y <= 4; y++) for (let x = -4; x <= 4; x++) { const d = x * x + y * y; if (d <= 18 && d > 3) ctx.fillRect(Math.floor(cx) + x, Math.floor(cy) + y, 1, 1); }
}
// First launch on a touch device (no saved controls, no ?controls=): "HOW DO YOU WANT TO PLAY?" before the how-to.
const needsChoose = () => IS_TOUCH && !params.get("controls") && !["one", "two"].includes(localStorage.getItem("bc_controls"));
const Choose = { sel: 0 };
function chooseLayout() {
  const y = Math.round(H * 0.3);
  return { one: { x: 14, y, w: W - 28, h: 62 }, two: { x: 14, y: y + 74, w: W - 28, h: 62 }, easy: { x: 30, y: y + 150, w: W - 60, h: 24 }, y };
}
function choosePick(m) { setControls(m); Snd.tone(880, 0.05, 0.06); setScreen("howto"); }
function chooseTap(p) { const L = chooseLayout(); if (inRect(p, L.easy)) { setEasy(!easy); Snd.tone(660, 0.04, 0.05); } else if (inRect(p, L.one)) choosePick("one"); else if (inRect(p, L.two)) choosePick("two"); }
function chooseKey(code) {
  if (["ArrowUp", "ArrowDown", "KeyW", "KeyS", "ArrowLeft", "ArrowRight", "KeyA", "KeyD"].includes(code)) Choose.sel = 1 - Choose.sel;
  else if (code === "Enter" || code === "Space") choosePick(Choose.sel ? "two" : "one");
  else if (code === "KeyE") setEasy(!easy);
}
function drawChoose() {
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H);
  const L = chooseLayout(), t = now / 1000;
  textC("HOW DO YOU", L.y - 52, C.hardhat, 2); textC("WANT TO PLAY?", L.y - 34, C.hardhat, 2);
  const card = (b, hot, title, desc, icon) => {
    drawButton(b, "", hot);
    text(title, b.x + 48, b.y + 12, hot ? "#000" : C.hardhat, 2, hot ? null : "#000");      // no shadow on the lit card
    desc.forEach((l, i) => text(l, b.x + 48, b.y + 34 + i * 10, hot ? "#000" : C.white, 1, hot ? null : "#000"));
    icon(b.x + 24, b.y + b.h / 2);
  };
  const hand = (x, y, col) => { ctx.fillStyle = col; ctx.fillRect(x - 3, y - 2, 7, 8); ctx.fillRect(x - 1, y - 9, 3, 8); };   // pointing finger
  const tapK = Math.floor(t * 3) % 2;
  card(L.one, Choose.sel === 0, "ONE HAND", ["TAP TO CLIMB,", "SWIPE TO HOP"], (x, y) => {
    miniPip(tapK ? "c4" : "c0", x, y - 6); hand(x + 8 + (Math.floor(t * 1.5) % 2) * 4, y + 14, C.skin || "#f4c4a4");
  });
  card(L.two, Choose.sel === 1, "TWO HANDS", ["TAP LEFT AND RIGHT,", "DOUBLE-TAP TO HOP"], (x, y) => {
    miniPip(tapK ? "c4" : "c0", x, y - 6); hand(x - 10, y + 14 - tapK * 2, "#f4c4a4"); hand(x + 10, y + 12 + tapK * 2, "#f4c4a4");
  });
  drawButton(L.easy, easy ? "EASY MODE: ON" : "EASY MODE: OFF", easy);
  textC(easy ? "GENTLER GIANTS, A FEW LESS COINS" : "TAP FOR GENTLER GIANTS", L.easy.y + 30, C.hair3);
  textC("YOU CAN CHANGE THIS IN SETTINGS", H - 20, C.hair3);
}
// Settings screen: controls (ONE HAND / TWO HANDS) + sound. Opened from the title gear (or G key).
const Settings = { sel: 0, from: "title" };
function settingsLayout() {
  const y = 18 + Math.round((H - 256) / 2);
  return { controls: { x: 24, y: y + 22, w: W - 48, h: 24 }, sound: { x: 24, y: y + 98, w: W - 48, h: 24 }, easy: { x: 24, y: y + 150, w: W - 48, h: 24 }, back: { x: W / 2 - 40, y: H - 32, w: 80, h: 24 }, y };
}
function openSettings(from) { Settings.from = from || "title"; Settings.sel = 0; setScreen("settings"); }
function settingsAct(i) {
  if (i === 0) { setControls(controls === "one" ? "two" : "one"); Snd.tone(760, 0.04, 0.05); }
  else if (i === 1) Snd.toggle();
  else if (i === 2) { setEasy(!easy); Snd.tone(660, 0.04, 0.05); }
  else settingsBack();
}
function settingsBack() { setScreen(Settings.from === "loss" ? "play" : Settings.from); }
function settingsTap(p) {
  const L = settingsLayout(), i = [L.controls, L.sound, L.easy, L.back].findIndex((b) => inRect(p, b));
  if (i >= 0) { Settings.sel = i; settingsAct(i); }
}
function settingsKey(code) {
  if (code === "Escape" || code === "Backspace" || code === "KeyG") { settingsBack(); return; }
  if (code === "ArrowUp" || code === "KeyW") Settings.sel = (Settings.sel + 3) % 4;
  else if (code === "ArrowDown" || code === "KeyS") Settings.sel = (Settings.sel + 1) % 4;
  else if (["Enter", "Space", "ArrowLeft", "ArrowRight", "KeyA", "KeyD"].includes(code)) settingsAct(Settings.sel);
}
function drawSettings() {
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H);
  const L = settingsLayout();
  textC("SETTINGS", L.y - 8, C.hardhat, 2);
  text("CONTROLS", L.controls.x, L.controls.y - 11, C.acc2);
  drawButton(L.controls, controls === "one" ? "< ONE HAND >" : "< TWO HANDS >", Settings.sel === 0);
  const help = controls === "one" ? ["TAP ANYWHERE: CLIMB", "SWIPE LEFT/RIGHT: HOP", "SWIPE DOWN: CLIMB DOWN", "HOLD: HOLD TIGHT"]
    : ["TAP LEFT/RIGHT HALF: ARMS", "DOUBLE-TAP ONE SIDE: LEAP", "SWIPE DOWN: CLIMB DOWN", "HOLD: HOLD TIGHT"];
  help.forEach((l, i) => text(l, L.controls.x + 4, L.controls.y + 29 + i * 9, C.hair3));
  text("SOUND", L.sound.x, L.sound.y - 11, C.acc2);
  drawButton(L.sound, Snd.muted ? "< OFF >" : "< ON >", Settings.sel === 1);
  text("KEYBOARD WORKS IN BOTH MODES", L.sound.x + 4, L.sound.y + 29, C.hair3);
  text("DIFFICULTY", L.easy.x, L.easy.y - 11, C.acc2);
  drawButton(L.easy, easy ? "< EASY >" : "< NORMAL >", Settings.sel === 2);
  text(easy ? "SLOWER HAZARDS, SOFTER BUMPS," : "THE GIANTS GET TOUGHER AS YOU GO", L.easy.x + 4, L.easy.y + 29, C.hair3);
  if (easy) text("A FEW LESS COINS (X0.8)", L.easy.x + 4, L.easy.y + 39, C.hair3);
  drawButton(L.back, "BACK", Settings.sel === 3);
}
let sceneStart = 0;                          // performance.now() when the current scene began
function setScreen(s) { cancelLevelLoad(); paused = false; screen = s; sceneStart = now; inputLockUntil = now + T.SKIP_LOCK_MS; Poki.screen(s); }

// ================================================================ level / world select
const WORLDS = [
  { name: "WORLD 1: WHISKERTON WOODS", col: "#58b848", levels: [
    { id: "grandpa", n: "1-1", name: "GRANDPA" }, { id: "goat", n: "1-2", name: "THE GOAT" },
    { id: "lumberjack", n: "1-3", name: "THE LUMBERJACK" }, { id: "mountain", n: "1-4", name: "MOUNTAIN MAN" },
    { id: "bigfoot", n: "1-5", name: "BIGFOOT", boss: true }] },
  { name: "WORLD 2: NORTH POLE", col: "#60b8f8", levels: [
    { id: "elf", n: "2-1", name: "THE ELF" }, { id: "rudolph", n: "2-2", name: "RUDOLPH" }, { id: "ice", n: "2-3", name: "THE ICE GIANT" },
    { id: "yeti", n: "2-4", name: "THE YETI" }, { id: "santa", n: "2-5", name: "SANTA", boss: true }] },
  { name: "WORLD 3: FAIRY-TALE FOREST", col: "#c080f0", levels: [
    { id: "gnome", n: "3-1", name: "THE GARDEN GNOME" }, { id: "rumpel", n: "3-2", name: "RUMPELSTILTSKIN" },
    { id: "rapunzel", n: "3-3", name: "RAPUNZEL" }, { id: "dwarf", n: "3-4", name: "THE DWARF KING" },
    { id: "wizard", n: "3-5", name: "THE WIZARD", boss: true }] },
];
const LV_ROWS = WORLDS.reduce((a, w) => a.concat(w.levels), []);
function levelState(id) { return !known(id) ? "soon" : isUnlocked(id) ? "open" : "locked"; }
const Levels = { sel: 0, from: "title", toast: null, toastT: 0 };
function saveLevel() { localStorage.setItem("bc_level", LEVEL); }
function openLevels(from) {
  Levels.from = from; Levels.toast = null; Levels.sel = Math.max(0, LV_ROWS.findIndex((l) => l.id === LEVEL));
  setScreen("levels"); Snd.tone(700, 0.06, 0.05);
}
function levelsLayout() {
  const top = 22, bh = H > 300 ? 30 : 26, back = { x: 4, y: H - bh - 4, w: 60, h: bh }, play = { x: 68, y: H - bh - 4, w: W - 72, h: bh };
  const avail = back.y - 4 - top - WORLDS.length * 10, rh = Math.max(11, Math.min(32, Math.floor(avail / LV_ROWS.length)));
  const rows = [], heads = []; let y = top;
  WORLDS.forEach((w) => { heads.push({ y, w }); y += 10; w.levels.forEach((lv) => { rows.push({ x: 6, y, w: W - 12, h: rh - 2, lv }); y += rh; }); });
  return { rows, heads, back, play, rh };
}
function levelsAct(i) {
  const lv = LV_ROWS[i]; if (!lv) return;
  Levels.sel = i;
  const st = levelState(lv.id);
  if (st === "open") { sfx.held(); goLevel(lv.id, () => { saveLevel(); startIntro(); }); }
  else if (st === "locked") { Levels.toast = ["CHEER UP " + THE_NAMES[UNLOCK_BY[lv.id]], "TO UNLOCK " + THE_NAMES[lv.id] + "!"]; Levels.toastT = now; Snd.tone(330, 0.08, 0.05); }
  else { Levels.toast = [lv.name + " IS COMING SOON!"]; Levels.toastT = now; Snd.tone(392, 0.08, 0.05, "triangle"); }
}
function levelsBack() { setScreen(Levels.from === "results" ? "results" : Levels.from === "loss" ? "play" : "title"); }
function levelsTap(p) {
  const L = levelsLayout();
  for (let i = 0; i < L.rows.length; i++) if (inRect(p, L.rows[i])) { levelsAct(i); return; }
  if (inRect(p, L.back)) levelsBack();
  else if (inRect(p, L.play)) levelsAct(Levels.sel);
}
function levelsKey(code) {
  const n = LV_ROWS.length;
  if (code === "ArrowUp" || code === "KeyW" || KEY_LEFT.includes(code)) { Levels.sel = (Levels.sel + n - 1) % n; Snd.tone(760, 0.03, 0.04); }
  else if (code === "ArrowDown" || code === "KeyS" || KEY_RIGHT.includes(code)) { Levels.sel = (Levels.sel + 1) % n; Snd.tone(760, 0.03, 0.04); }
  else if (code === "Enter" || code === "Space") levelsAct(Levels.sel);
  else if (code === "Escape" || code === "Backspace") levelsBack();
}
function drawLevels() {
  const L = levelsLayout(), t = now / 1000;
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H); stars(t, 24);
  textC("SELECT LEVEL", 4, C.hardhat, 2);
  for (const h of L.heads) { ctx.fillStyle = h.w.col; ctx.fillRect(6, h.y + 9, W - 12, 1); text(h.w.name, 8, h.y + 1, h.w.col); }
  L.rows.forEach((r, i) => {
    const lv = r.lv, st = levelState(lv.id), hot = i === Levels.sel, two = r.h >= 20;
    ctx.fillStyle = hot ? "rgba(248,232,72,0.18)" : st === "open" ? "rgba(0,0,0,0.45)" : "rgba(0,0,0,0.25)"; ctx.fillRect(r.x, r.y, r.w, r.h);
    if (hot) { ctx.fillStyle = C.hardhat; ctx.fillRect(r.x, r.y, r.w, 1); ctx.fillRect(r.x, r.y + r.h - 1, r.w, 1); ctx.fillRect(r.x, r.y, 1, r.h); ctx.fillRect(r.x + r.w - 1, r.y, 1, r.h); }
    const ty = r.y + (two && st === "locked" ? 3 : Math.round((r.h - 7) / 2)), dim = st === "open" ? C.white : "#8080a0";
    ctx.fillStyle = st === "open" ? C.hardhat : "#504870"; ctx.fillRect(r.x + 3, ty - 2, 22, 11);
    text(lv.n, r.x + 5, ty, st === "open" ? "#000" : "#a0a0c0", 1, null);
    text(lv.name, r.x + 30, ty, dim);
    if (lv.boss) text("BOSS", r.x + 30 + textW(lv.name) + 6, ty, st === "open" ? C.shirt : "#a06070");
    const rx = r.x + r.w - 4;
    if (st === "open") {
      if (cheered.has(lv.id)) bitmap(STAR, rx - 40, ty, C.hardhat);
      text("PLAY", rx - textW("PLAY"), ty, Math.floor(t * 2) % 2 && hot ? C.hardhat : C.acc2);
    } else if (st === "locked") {
      bitmap(LOCK, rx - 6, ty, "#a0a0c0");
      if (two) text("CHEER UP " + GIANT_NAMES[UNLOCK_BY[lv.id]] + " FIRST", r.x + 30, ty + 9, C.hair3);
    } else text("SOON", rx - textW("SOON"), ty, "#706890");
  });
  const sel = LV_ROWS[Levels.sel], sst = levelState(sel.id);
  drawButton(L.back, "BACK", false);
  drawButton(L.play, sst === "open" ? "PLAY " + sel.name : sst === "locked" ? "LOCKED" : "COMING SOON", sst === "open" && Math.floor(t * 2) % 2 === 0, sst === "open" ? null : "#605878");
  if (Levels.toast && now - Levels.toastT < 2400) {
    const n = Levels.toast.length, h = n * 10 + 8, y = Math.round(H / 2) - h;
    ctx.fillStyle = "rgba(20,10,40,0.94)"; ctx.fillRect(6, y, W - 12, h);
    ctx.fillStyle = C.acc2; ctx.fillRect(6, y, W - 12, 1); ctx.fillRect(6, y + h - 1, W - 12, 1);
    Levels.toast.forEach((l, i) => textC(l, y + 5 + i * 10, i ? C.hair3 : C.white));
  }
  drawMute();
}

// ================================================================ opening cinematic (Donkey Kong style attract story)
const CINE = [
  { id: "grandpa", cap: ["GRANDPA'S PHONE NEVER RINGS..."] },
  { id: "goat", cap: ["THE GOAT ATE HIS LAST TURNIP!"] },
  { id: "lumberjack", cap: ["THE LUMBERJACK'S PANCAKES BURNED!"] },
  { id: "mountain", cap: ["MOUNTAIN MAN'S COMPASS BLEW AWAY!"] },
  { id: "bigfoot", cap: ["BIGFOOT HAS NOBODY TO SMILE WITH..."] },
  { id: "elf", cap: ["THE ELF LOST HIS TOY HAMMER!"] },
  { id: "rudolph", cap: ["RUDOLPH'S NOSE WON'T GLOW..."] },
  { id: "ice", cap: ["THE ICE GIANT IS COLD + LONELY..."] },
  { id: "yeti", cap: ["THE YETI'S COCOA RAN OUT!"] },
  { id: "santa", cap: ["SANTA'S COOKIES ARE ALL GONE!"] },
  { id: "gnome", cap: ["THE GNOME LOST HIS LUCKY MUSHROOM!"] },
  { id: "rumpel", cap: ["NOBODY REMEMBERS RUMPEL'S NAME..."] },
  { id: "rapunzel", cap: ["RAPUNZEL'S BRAID IS ALL TANGLED!"] },
  { id: "dwarf", cap: ["THE DWARF KING LOST HIS CROWN!"] },
  { id: "wizard", cap: ["THE WIZARD'S SPELL BOOK FLEW OFF,", "AND HIS CAT WON'T SETTLE DOWN!"] },
];
const Cine = { t: 0, then: "intro", cues: {} };
let cineSeen = localStorage.getItem("bc_cine") === "1";   // the opening plays by itself only the first time ever
const VK = () => T.CINE_VIG / 3.0;          // vignette beats are authored for 3 s; scaled to T.CINE_VIG
function cineLength() { return T.CINE_PROLOGUE + CINE.length * T.CINE_VIG + T.CINE_END; }
function startCine(then) { Cine.t = 0; Cine.then = then; Cine.cues = {}; cineSeen = true; localStorage.setItem("bc_cine", "1"); setScreen("cine"); }
function endCine() {
  if (Cine.then === "title") setScreen("title");
  else if (Cine.then === "results") setScreen("results");
  else startIntro();
}
function cue(name, at, t, fn) { if (t >= at && !Cine.cues[name]) { Cine.cues[name] = 1; fn(); } }
function drawCine() {
  const t = Cine.t;
  if (t >= cineLength()) { endCine(); if (screen !== "cine") return; }
  ctx.imageSmoothingEnabled = false; shakeX = shakeY = 0;
  if (t < T.CINE_PROLOGUE) drawPrologue(t);
  else if (t < T.CINE_PROLOGUE + CINE.length * T.CINE_VIG) {
    const k = Math.floor((t - T.CINE_PROLOGUE) / T.CINE_VIG);
    drawVignette(k, (t - T.CINE_PROLOGUE - k * T.CINE_VIG) / VK());
  } else drawPipStepsUp(t - T.CINE_PROLOGUE - CINE.length * T.CINE_VIG);
  skipHint();
}
function stars(t, n = 40) {
  for (let i = 0; i < n; i++) {
    const x = (i * 97) % W, y = (i * 53) % Math.max(60, H - 70);
    ctx.fillStyle = Math.floor(t * 3 + i) % 5 ? "#8890b0" : C.white; ctx.fillRect(x, y, 1, 1);
  }
}
function drawTownRow(y, mode, t) {           // screen-space crowd for the vignettes
  [20, 50, 82, 142, 174, 204].forEach((x, i) => {
    const pose = townPose(i, t, mode), hop = pose === "cheer" ? Math.floor(t * 6 + i) % 2 : 0;
    drawTownie(i % TOWN.length, x, y - hop, pose);
  });
}
function drawPrologue(t) {
  cue("jingle", 0.05, t, sfx.jingle);
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H);
  stars(t);
  const gy = H - 40;
  for (let i = 0; i < 9; i++) {              // little Whiskerton houses
    const x = i * 26 - 4, h = 14 + (i * 7) % 10;
    ctx.fillStyle = ["#3c2848", "#2c2040", "#483058"][i % 3]; ctx.fillRect(x, gy - h, 22, h);
    ctx.fillStyle = "#583860"; for (let j = 0; j < 11; j++) ctx.fillRect(x + j, gy - h - 1 - Math.min(j, 10 - j) / 2 * 1.2, 1, 6);
    ctx.fillStyle = Math.floor(t * 2 + i) % 3 ? C.hardhat : "#806020"; ctx.fillRect(x + 7, gy - h + 5, 4, 4);
  }
  drawGround(gy);
  const y = Math.round(H * 0.22);
  textC("WHISKERTON", y, C.hardhat, 3);
  if (t > 0.5) textC("HOME OF MANY FRIENDLY GIANTS...", y + 32, C.white);
  if (t > 1.3) textC("BUT TODAY THEY ARE ALL GRUMPY!", y + 46, C.acc2);
  drawTownRow(gy + 1, "stand", t);
}
function drawGiantFace(id, mouthOpen, dx) {
  const gh = A.giant_h;
  if (id === "wizard") {
    ctx.drawImage(IMG.wbg, 0, 0, W, gh, dx, 0, W, gh);
    if (mouthOpen) ctx.drawImage(IMG.wmouth, dx, LV.wizard.mouth_y);
    return LV.wizard.mouth_y + LV.wizard.mouth_h / 2;
  }
  const i = Object.keys(A.giants).indexOf(id), g = A.giants[id];
  ctx.drawImage(IMG.giants, 0, i * gh, W, gh, dx, 0, W, gh);
  if (mouthOpen) spr("g_" + id + "_mouth", dx, g.mouth_y);
  const f = F["g_" + id + "_mouth"];
  return g.mouth_y + f[3] / 2;
}
function drawVignette(k, u) {
  const v = CINE[k], id = v.id, gh = A.giant_h, gy = H - 34;
  const bg = id === "wizard" ? C.bg : A.giants[id].bg;
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
  const frown = u > 1.35, shake = u > 1.35 && u < 1.7 ? (Math.floor(u * 30) % 2 ? 2 : -2) : 0;
  const tossT = [1.7, 2.3], mouthOpen = tossT.some((a) => u > a - 0.1 && u < a + 0.3);
  // beard continues down to the town: repeat the last two beard rows of the portrait
  const src = id === "wizard" ? IMG.wbg : IMG.giants, sy0 = id === "wizard" ? 0 : Object.keys(A.giants).indexOf(id) * gh;
  for (let y = gh; y < gy; y += 64) ctx.drawImage(src, 0, sy0 + gh - 64, W, 64, shake, y, W, 64);
  const my = drawGiantFace(id, mouthOpen, shake);
  // the lost treasure
  const tx = 180, ty = gh - 34;
  if (id === "santa") {
    const wob = u < 1.3 ? Math.round(Math.sin(u * 12) * 1) : 0;
    spr("treasure_santa", tx, ty + wob);
    if (u < 1.3 && Math.floor(u * 6) % 2) { ctx.fillStyle = "#a06030"; ctx.fillRect(tx - 4, ty + 10 + Math.floor(u * 20) % 12, 2, 2); }
    if (u > 0.4 && u < 1.4) text("ALL GONE!", tx - 26, ty - 22, C.white);
  } else if (id === "lumberjack") {
    const fall = Math.max(0, u - 1.0), y = ty + fall * fall * 140;
    if (y < gy) spr("treasure_lumberjack", tx, y);
    for (let i = 0; i < 4; i++) {               // smoke
      const p = (u * 1.4 + i / 4) % 1;
      ctx.fillStyle = i % 2 ? "#606060" : "#909090"; ctx.fillRect(tx - 6 + i * 4 + Math.round(Math.sin(p * 6) * 2), y - 10 - p * 26, 3, 3);
    }
    cue("burn", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.2 * VK(), Cine.t, () => Snd.noise(0.5, 0.08, 3000));
  } else if (id === "viking") {
    spr("treasure_viking", tx, ty);
    cue("toot", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.3 * VK(), Cine.t, sfx.toot);
    if (u > 0.3 && u < 1.3) text(u < 0.8 ? "TOO..." : "...PFFT", tx - 10, ty - 22 - Math.round((u - 0.3) * 6), C.white);
  } else if (id === "grandpa") {              // the toy phone that never rings
    spr("treasure_grandpa", tx, ty + (u > 0.6 && u < 0.9 ? -1 : 0));
    if (u > 0.3 && u < 1.4) text(u < 0.85 ? "..." : "NO CALLS", tx - (u < 0.85 ? 8 : 24), ty - 22, C.white);
  } else if (id === "goat") {                 // the last turnip: crunch... gone
    const bite = Math.min(3, Math.floor(Math.max(0, u - 0.3) / 0.3));
    if (bite < 3) { spr("treasure_goat", tx, ty); ctx.fillStyle = A.giants.goat.bg; for (let b = 0; b < bite; b++) ctx.fillRect(tx + 4 - b * 5, ty - 12 + b * 6, 9, 9); }
    cue("crunch", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.35 * VK(), Cine.t, sfx.munch);
    if (u > 0.3 && u < 1.4) text(bite < 3 ? "CRUNCH!" : "ALL GONE!", tx - 26, ty - 24, C.white);
  } else if (id === "mountain") {             // the compass whisked off by the mountain wind
    const fly = Math.max(0, u - 0.4);
    spr("treasure_mountain", tx + fly * 60, ty - fly * 50 + Math.sin(fly * 8) * 4);
    if (u > 0.3 && u < 1.6) for (let i = 0; i < 5; i++) { ctx.fillStyle = C.white; ctx.fillRect(((u * 170 + i * 53) % W), ty - 24 + i * 8, 14, 1); }
    cue("wind", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.4 * VK(), Cine.t, sfx.whoosh);
  } else if (W3.includes(id)) {                // World 3: the lost treasure wobbles, then a puzzled "?"
    spr("treasure_" + id, tx + (u > 0.3 && u < 1.3 && Math.floor(u * 8) % 2 ? 1 : 0), ty);
    if (u > 0.3 && u < 1.4) text(id === "rumpel" ? "WHO AM I?" : "WHERE?", tx - 24, ty - 24, C.white);
  } else if (id === "elf") {                  // the toy hammer is lost: the workshop stands still
    const look = Math.floor(u * 2) % 2;
    spr("treasure_elf", tx + (look ? 2 : -2) * (u > 0.3 && u < 1.3 ? 1 : 0), ty);
    if (u > 0.3 && u < 1.4) text(u < 0.85 ? "TAP... TAP..." : "NO HAMMER!", tx - 34, ty - 24, C.white);
  } else if (id === "rudolph") {              // the lantern and the nose go dark
    spr("treasure_rudolph", tx, ty);
    if (u > 0.3 && u < 1.4) text(u < 0.85 ? "BLINK..." : "...OFF", tx - 22, ty - 24, C.white);
  } else if (id === "ice") {                  // one lonely mitten, shivering
    spr("treasure_ice", tx + (Math.floor(u * 20) % 2 && u < 1.4 ? 1 : 0), ty);
    if (u > 0.3 && u < 1.4) text("BRRR!", tx - 14, ty - 24, C.white);
  } else if (id === "yeti") {                 // the cocoa mug is empty
    spr("treasure_yeti", tx, ty);
    if (u > 0.3 && u < 1.4) text(u < 0.85 ? "SLURP..." : "EMPTY!", tx - 20, ty - 24, C.white);
  } else if (id === "bigfoot") {              // a camera and nobody to take a picture with
    spr("treasure_bigfoot", tx, ty);
    if (u > 0.3 && u < 1.4) text(u < 0.85 ? "HELLO?" : "...", tx - (u < 0.85 ? 18 : 8), ty - 24, C.white);
  } else if (id === "pirate") {
    const fly = Math.max(0, u - 0.3);
    spr("treasure_pirate", tx + fly * 70, ty - fly * 40 + Math.sin(fly * 9) * 4);
    if (u > 0.3 && u < 1.6) for (let i = 0; i < 4; i++) { ctx.fillStyle = C.white; ctx.fillRect(((u * 160 + i * 61) % W), ty - 20 + i * 9, 12, 1); }
    cue("wind", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.3 * VK(), Cine.t, sfx.whoosh);
  } else {                                     // wizard: book swept away, cat can't settle
    const fly = Math.max(0, u - 0.3);
    spr("book", 60 - fly * 80, ty - fly * 50 + Math.sin(fly * 10) * 3);
    if (u > 0.3 && u < 1.5) for (let i = 0; i < 4; i++) { ctx.fillStyle = C.white; ctx.fillRect(W - ((u * 160 + i * 61) % W), ty - 20 + i * 9, 12, 1); }
    const cx = tx + Math.round(Math.sin(u * 5) * 18), hop = Math.abs(Math.sin(u * 7)) * 10;
    spr("wizard/haz1_" + (Math.floor(u * 6) % 2 ? 0 : 2), cx, ty + 4 - hop);
    if (u > 0.5 && u < 1.6) text("MEOW!", cx - 14, ty - 26, C.white);
    cue("wind", T.CINE_PROLOGUE + k * T.CINE_VIG + 0.3 * VK(), Cine.t, sfx.whoosh);
  }
  if (frown) {
    if (u < 2.1) { ctx.fillStyle = C.white; ctx.fillRect(10, my - 30, 38, 13); ctx.fillRect(40, my - 18, 4, 3); text("HMPH!", 15, my - 27, "#000", 1, null); }
    cue("hmph" + k, T.CINE_PROLOGUE + k * T.CINE_VIG + 1.35 * VK(), Cine.t, sfx.hmph);
  }
  // tossing things down the beard
  tossT.forEach((a, j) => {
    const dt = u - a; if (dt < 0) return;
    cue("toss" + k + j, T.CINE_PROLOGUE + k * T.CINE_VIG + a * VK(), Cine.t, sfx.toss);
    const name = id === "wizard" ? "wizard/haz" + (j ? 2 : 0) + "_0" : "toss_" + id + "_" + (j % A.giants[id].toss);
    const x = W / 2 + (j ? 34 : -30) * Math.min(1, dt * 1.5), y = my + dt * dt * 260 + dt * 30;
    if (y < gy - 8) sprRot(name, x, y, Math.floor(dt * 8));
    else if (dt < 1.4) { const b = y - (gy - 8); sprRot(name, x + (j ? 1 : -1) * b * 0.4, gy - 8 - Math.abs(Math.sin(b / 30)) * 12, Math.floor(dt * 8)); }
  });
  ctx.fillStyle = "rgba(0,0,0,0)";
  drawGround(gy);
  const duck = u > 1.6 && u < 3.1;
  cue("eek" + k, T.CINE_PROLOGUE + k * T.CINE_VIG + 1.65 * VK(), Cine.t, sfx.eek);
  drawTownRow(gy + 1, duck ? "duck" : "stand", u);
  if (duck && u < 2.4) text("EEK!", 8, gy - 44, C.white);
  if (u < 0.25) { ctx.fillStyle = "rgba(0,0,0," + (1 - u / 0.25).toFixed(2) + ")"; ctx.fillRect(0, 0, W, H); }
  caption(v.cap, u, H < 300 ? 16 : gh + 4);
}
function drawPipStepsUp(u) {                // Pip steps forward: "Pip will cheer them up!"
  const vh = H / P, cam = BOTTOM_Z - 1.2;
  drawLevel(cam, false);
  const gy = sy(GROUND_Z);
  drawTownWorld();
  const walk = Math.min(1, u / 1.5), x = -0.6 + (START_X - -0.6) * walk;
  const pose = walk < 1 ? "f_stand" : u < 2.6 ? "f_wave" : "f_cheer";
  drawPip(sx(x), gy + 1 - (walk < 1 ? Math.floor(u * 8) % 2 : 0), pose, { head: "own" });
  if (walk >= 1) goodSparkle(sx(x), gy - 30, u);
  cue("crowd", T.CINE_PROLOGUE + CINE.length * T.CINE_VIG + 1.6, Cine.t, () => sfx.crowd(10));
  if (u < 0.25) { ctx.fillStyle = "rgba(0,0,0," + (1 - u / 0.25).toFixed(2) + ")"; ctx.fillRect(0, 0, W, H); }
  if (u < 1.6) caption("BUT ONE BRAVE KID HAS AN IDEA...", u, 30);
  else { caption("PIP WILL CHEER THEM UP!", u - 1.6, 30); if (u > 2.0) textC("PIP!", 52, C.hardhat, 3); }
}

// ================================================================ Wizard level intro (base of the beard)
const Intro = { t: 0, cues: {} };
const PACK_X = 3.45, BOOK_FROM = 0.72, CAT_FROM = 4.62;
function startIntro() { Intro.t = 0; Intro.cues = {}; face = "normal"; setScreen("intro"); }
function introCam() { return BOTTOM_Z - 1.2; }
function playCam(z) { const vh = H / P; return Math.max(BOTTOM_Z, Math.min(TOP - vh, z - 1.4)); }
function updateIntro(dt) {
  const t = Intro.t += dt, c = (n, at, fn) => { if (t >= at && !Intro.cues[n]) { Intro.cues[n] = 1; fn(); } };
  c("crowd", 0.15, () => sfx.crowd(6));
  c("book", 1.25, () => { sfx.pop(); });
  if (LEVEL === "wizard") c("cat", 2.15, () => { Snd.tone(900, 0.12, 0.04, "triangle", 600); });
  else if (LEVEL === "grandpa") c("ring", 1.6, () => sfx.ring());
  else if (LEVEL === "goat") c("bleat", 1.6, () => sfx.bleat());
  c("packon", 3.0, () => sfx.pop());
  c("cheer", 3.1, () => sfx.crowd(12));
  c("jump", 4.5, () => sfx.dyno());
  if (t >= T.INTRO_S) startPlayFromIntro();
}
function startPlayFromIntro() { newGame(); setScreen("play"); inputLockUntil = now + 150; }
const arc = (a, b, k, h) => a + (b - a) * k + Math.sin(k * Math.PI) * h;
function drawIntro() {
  const t = Intro.t, wiz = LEVEL === "wizard";
  const camZ = t < 4.5 ? introCam() : introCam() + (playCam(START_Z) - introCam()) * Math.min(1, (t - 4.5) / 0.8);
  shakeX = shakeY = 0;
  drawLevel(camZ, false);
  drawTownWorld();
  const gz = GROUND_Z;
  // backpack on the ground; the book and the cat hop in
  const packOn = t >= 3.0;
  if (!packOn) {
    const k = Math.max(0, Math.min(1, (t - 2.6) / 0.4));
    const px = PACK_X + (START_X - PACK_X) * k, pz = gz + Math.sin(k * Math.PI) * 0.8 + k * 0.7;
    drawProp(t >= 2.15 && wiz ? "gpack_cat" : "gpack", sx(px), sy(pz) + 1);
  }
  if (t > 0.5 && t < 1.25) { const k = (t - 0.5) / 0.75; spr(STORY().item, sx(arc(BOOK_FROM, PACK_X, k, 0)), sy(arc(gz + 1.1, gz + 0.5, k, 1.6))); }
  if (wiz && t > 1.35 && t < 2.15) { const k = (t - 1.35) / 0.8; drawProp("sleepcat", sx(arc(CAT_FROM, PACK_X, k, 0)), sy(arc(gz + 1.0, gz + 0.6, k, 1.4))); }
  if (wiz && t > 2.15 && t < 2.8) text("MEW...", sx(PACK_X) - 8, sy(gz + 1.6), C.white);
  if (LEVEL === "grandpa" && t > 1.6 && t < 2.6 && Math.floor(t * 8) % 2) text("RING!", sx(PACK_X) - 12, sy(gz + 1.7), C.white);
  if (!wiz && t > 3.1 && t < 4.4 && Math.floor(t * 4) % 2) text("HOORAY!", sx(1.0) - 10, sy(gz + 2.4), C.hardhat);
  // Pip
  let pz = gz, pose;
  if (t < 3.0) pose = t > 0.5 && t < 1.3 ? "f_wave" : "f_stand";
  else if (t < 4.5) pose = Math.floor((t - 3.0) * 3) % 2 ? "wave" : "cheer";
  else { const k = Math.min(1, (t - 4.5) / 0.6); pz = arc(gz, START_Z, k, 0.5); pose = k < 1 ? "dyno" : "c0"; }
  drawPip(sx(START_X), sy(pz) + 1, pose, { head: "own", pack: packOn, cat: packOn && wiz });
  if (t >= 3.0 && t < 3.4) sparkleRing(sx(START_X), sy(gz + 1.2), t - 3.0);
  if (wiz) {
    if (t < 2.9) caption("THE WIZARD LOST HIS SPELL BOOK!", t - 0.2, 26);
    else caption(["BRING IT BACK, PIP!", "(AND TUCK IN HIS SLEEPY CAT)"], t - 2.9, 26);
  } else {
    const st = STORY();
    if (t < 2.9) caption(st.intro[0], t - 0.2, 26);
    else caption(st.intro[1], t - 2.9, 26);
  }
  textC(wiz ? "WHISKERTON" : W2.includes(LEVEL) ? "THE NORTH POLE" : W3.includes(LEVEL) ? "FAIRY-TALE FOREST" : "WHISKERTON WOODS", 14, C.hardhat);
  skipHint();
  drawMute();
}
function sparkleRing(x, y, k) {
  ctx.fillStyle = C.hardhat;
  for (let i = 0; i < 10; i++) { const a = i / 10 * Math.PI * 2, r = 6 + k * 50; ctx.fillRect(x + Math.round(Math.cos(a) * r), y + Math.round(Math.sin(a) * r * 0.7), 2, 2); }
}

// ================================================================ ending at the top
const Ending = { t: 0, cues: {}, pages: [] };
function startEnding() {
  for (const h of S.haz) sparkle(h.x, h.z, 6, C.white);       // every hazard goes 'poof': throwing stops
  S.haz.length = 0; S.sneeze.phase = "none"; S.cl.hold = false; S.mouthOpenUntil = -1;
  for (const it of S.items) sparkle(it.x, it.z, 4, C.white);   // leftover hats / pages twinkle away
  S.items.length = 0;
  Ending.t = 0; Ending.cues = {}; Ending.pages = [];
  if (!cheered.has(LEVEL)) {                  // first cheer-up: the giant's shop set is free + the next level unlocks
    const nxt = CHAIN[CHAIN.indexOf(LEVEL) + 1], was = !!nxt && isUnlocked(nxt);
    cheered.add(LEVEL);
    if (CATALOG.some((i) => i.set === LEVEL)) S.newSet = LEVEL;
    if (nxt && !was && isUnlocked(nxt)) S.unlocked = nxt;
    saveShop();
  }
  setScreen("ending"); inputLockUntil = now + 500;
}
function storyFx(dt) {
  S.t += dt;
  const cl = S.cl;
  if (cl.tw) { const k = Math.min(1, (S.t - cl.tw.t0) * 1000 / (cl.tw.ms || T.CLIMB_MS)); cl.z = cl.tw.fromZ + (cl.tw.toZ - cl.tw.fromZ) * k; if (k >= 1) cl.tw = null; }
  for (const f of S.fx) { f.vz -= (f.hat ? 14 : 6) * dt; f.x += f.vx * dt; f.z += f.vz * dt; }
  S.fx = S.fx.filter((f) => S.t - f.t0 < f.dur);
  S.texts = S.texts.filter((t) => S.t - t.t0 < t.dur);
  S.shake = Math.max(0, S.shake - dt * 10);
  for (const it of S.items) it.t += dt;
}
function updateEnding(dt) {
  storyFx(dt);
  const t = Ending.t += dt, cl = S.cl, c = (n, at, fn) => { if (t >= at && !Ending.cues[n]) { Ending.cues[n] = 1; fn(); } };
  S.camZ += (camTarget() - S.camZ) * Math.min(1, dt * 7);
  for (let i = 0; i < S.pages; i++) c("pg" + i, 1.5 + i * 0.12, () => { sparkle(BOOK_AT.x, BOOK_AT.z, 4, C.white); Snd.tone(1200 + i * 150, 0.06, 0.05); });
  if (LEVEL === "grandpa") {                  // the phone rings: it's the grandkids! He beams, waves and laughs
    c("phone", 0.8, () => sfx.whoosh());
    c("phonein", 1.5, () => { S.phoneIn = S.itemIn = true; sparkle(BOOK_AT.x, BOOK_AT.z, 12, C.hardhat); sfx.ring(); });
    c("ring2", 2.05, () => sfx.ring());
    c("smile", 2.5, () => { face = "smile"; sfx.held(); });
    c("beam", 3.4, () => { face = "sleep"; S.waving = true; sfx.laugh(); sparkle(HAND_AT.x, HAND_AT.z + 1, 12, C.hardhat); });
    c("laugh2", 4.7, () => sfx.laugh());
    if (t >= T.ENDING_S) startPara();
    return;
  }
  if (LEVEL !== "wizard") {                   // World 1: the gift goes up (eaten / tucked in / a selfie), a smile, a big happy laugh
    const st = STORY(), tg = itemTarget();
    if (st.selfie) {
      c("pose", 0.8, () => sfx.tweet());
      c("flash", 2.4, () => { S.flashT = t; sfx.flash(); face = "smile"; S.selfieTaken = true; });
      c("itemin", 2.9, () => { S.itemIn = true; sparkle(tg.x, tg.z, 12, C.hardhat); sfx.page(); });
    } else {
      c("item", 0.8, () => sfx.whoosh());
      c("itemin", 1.5, () => { S.itemIn = true; sparkle(tg.x, tg.z, 12, C.hardhat); if (st.eat) sfx.munch(); else sfx.page(); });
      if (st.eat) { c("munch2", 1.95, () => { sfx.munch(); sparkle(tg.x, tg.z - 0.3, 6, LC.acc3); }); c("munch3", 2.4, () => { sfx.munch(); sparkle(tg.x, tg.z - 0.3, 6, LC.acc3); }); }
      c("smile", st.sleep ? 3.2 : 2.6, () => { face = "smile"; sfx.held(); });
    }
    if (st.sleep) {                           // Santa: munch, smile, a big yawn... fast asleep
      c("yawn", 4.1, () => { face = "yawn"; sfx.yawn(); });
      c("sleep", 5.0, () => { face = "sleep"; S.asleep = true; sfx.lullaby(); });
      if (t >= T.ENDING_S) startPara();
      return;
    }
    if (st.jig) S.jigX = S.beaming ? Math.round(Math.sin(t * 14) * 2) : 0;
    if (st.glow) c("glow", 3.4, () => { S.glowT = t; sfx.glow(); });
    c("beam", 3.4, () => { face = "sleep"; S.beaming = true; if (LEVEL === "goat") sfx.bleat(); else if (st.jig) sfx.jig(); else sfx.laugh(); if (LEVEL === "lumberjack") S.shake = 3; });
    c("laugh2", 4.7, () => { sfx.laugh(); if (LEVEL === "lumberjack") S.shake = 3; });
    if (t >= T.ENDING_S) startPara();
    return;
  }
  c("book", 0.8, () => sfx.whoosh());
  c("bookin", 1.5, () => { S.bookIn = true; sparkle(BOOK_AT.x, BOOK_AT.z, 12, C.hardhat); sfx.page(); });
  c("cat", 2.1, () => { S.catOn = false; Snd.tone(900, 0.12, 0.04, "triangle", 600); });
  c("catin", 2.8, () => { S.catIn = true; sparkle(CAT_AT.x, CAT_AT.z, 8, C.white); });
  c("smile", 3.1, () => { face = "smile"; sfx.held(); });
  c("yawn", 3.8, () => { face = "yawn"; sfx.yawn(); });
  c("sleep", 4.5, () => { face = "sleep"; S.asleep = true; sfx.lullaby(); });
  if (t >= T.ENDING_S) startPara();
}
function drawZzz(t) {
  if (!S.asleep) return;
  for (let i = 0; i < 3; i++) {
    const p = (t * 0.45 + i / 3) % 1, x = sx(ZZZ_AT.x) + Math.round(p * 18 + Math.sin(p * 9) * 3), y = sy(ZZZ_AT.z) - Math.round(p * 34);
    if (y > -10 && y < H) text("Z", x, y, p < 0.8 ? C.white : C.hair3, p > 0.5 ? 2 : 1);
  }
}
/** Where the gift ends up: in the giant's mouth (eat) or tucked into his beard. */
function itemTarget() { return STORY().eat ? { x: MOUTH_X, z: MOUTH_Z } : BOOK_AT; }
function drawBeardGifts() {                 // book + pages + sleeping cat, back in the Wizard's beard
  const t = now / 1000;
  if (LEVEL !== "wizard" && LEVEL !== "grandpa") {         // World 1: the gift + a happy laugh
    const st = STORY();
    if (S.itemIn && !st.eat) spr(st.item, sx(BOOK_AT.x), sy(BOOK_AT.z));
    if (screen === "ending" && st.eat && Ending.t > 1.5 && Ending.t < 3.0 && Math.floor(t * 5) % 2)
      outlined(LEVEL === "goat" ? "MUNCH!" : "CHOMP!", sx(MOUTH_X) + 22, sy(MOUTH_Z) - 6, C.white);
    if (screen === "ending" && S.beaming && Math.floor(t * 3) % 3)
      outlined(st.shout, 8, sy(ROWS - 0.7) - Math.round((Ending.t % 1) * 4), C.white);
    if (st.glow && (S.glowT !== undefined || (screen !== "ending" && S.beaming))) drawNoseGlow(t);
    if (st.jig && S.beaming && screen === "ending") for (let i = 0; i < 3; i++) {      // musical notes for the jig
      const p = (t * 0.8 + i / 3) % 1; outlined(i % 2 ? "#" : "&", sx(MOUTH_X) - 40 + i * 36 + Math.round(Math.sin(p * 8) * 4), sy(ROWS + 1) - Math.round(p * 30), C.hardhat);
    }
    drawZzz(t);
    return;
  }
  if (LEVEL === "grandpa") {                  // the toy phone tucked in Grandpa's beard + his waving hand
    if (S.phoneIn) {
      spr("phone", sx(BOOK_AT.x), sy(BOOK_AT.z));
      if (screen === "ending" && Ending.t < 2.6 && Math.floor(t * 8) % 2) text("RING!", sx(BOOK_AT.x) - 14, sy(BOOK_AT.z) - 20, C.white);
    }
    if (S.waving) {
      spr("hand_" + (Math.floor(t * 4) % 2), sx(HAND_AT.x), sy(HAND_AT.z));
      if (screen === "ending" && Ending.t > 3.4 && Math.floor(t * 3) % 3) text("HEH HEH!", 8, sy(ROWS - 0.7) - Math.round((Ending.t % 1) * 4), C.white);
    }
    return;
  }
  if (S.bookIn) { spr("book", sx(BOOK_AT.x), sy(BOOK_AT.z)); }
  if (S.catIn) { drawProp("sleepcat", sx(CAT_AT.x), sy(CAT_AT.z)); if (Math.floor(t * 1.5) % 2) text("Z", sx(CAT_AT.x) + 12, sy(CAT_AT.z) - 16, C.white); }
  drawZzz(t);
}
/** Rudolph's nose lights up again: a pulsing red glow with a soft halo. */
function drawNoseGlow(t) {
  const x = sx(MOUTH_X), y = sy(NOSE_Z), k = S.glowT !== undefined && screen === "ending" ? Math.min(1, (Ending.t - S.glowT) / 0.6) : 1;
  const r = 14 + Math.sin(t * 5) * 1.5;
  ctx.save();
  for (let i = 3; i >= 1; i--) { ctx.fillStyle = "rgba(255,60,60," + (0.12 * k).toFixed(2) + ")"; ctx.beginPath(); ctx.arc(x, y, r + i * 9 * k, 0, Math.PI * 2); ctx.fill(); }
  ctx.fillStyle = "rgba(255,40,40," + (0.95 * k).toFixed(2) + ")"; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = "rgba(255,200,200," + (0.9 * k).toFixed(2) + ")"; ctx.fillRect(x - 6, y - 7, 4, 3);
  ctx.restore();
}
function drawStoryPip() {
  if (screen === "ending") drawEndingPip();
  else if (screen === "para") drawParaPip();
  else if (screen === "bird") drawBirdPip();
}
function drawEndingPip() {
  const t = Ending.t, cl = S.cl, x = sx(cl.x), y = sy(cl.z), wiz = LEVEL === "wizard";
  const pose = wiz ? (t < 0.8 ? "hold" : t < 2.1 ? "cheer" : t < 2.9 ? "wave" : "cheer") : (t < 0.8 ? "hold" : t < 3.4 ? "cheer" : Math.floor(t * 3) % 2 ? "wave" : "cheer");
  drawPip(x, y, pose, { head: "own", pack: true, cat: S.catOn });
  const st = STORY(), tg = itemTarget();
  if (st.selfie) {                           // Pip holds the camera up high: say cheese!
    if (t > 0.8 && t < 2.9) spr(st.item, x + 10, y - 66 + (t > 2.3 && t < 2.5 ? -1 : 0));
  } else if (t > 0.8 && t < 1.5) {           // the gift floats up (book / toy phone / turnip / pancakes / compass)
    const k = (t - 0.8) / 0.7; spr(st.item, sx(arc(cl.x, tg.x, k, 0)), sy(arc(cl.z + 1.4, tg.z, k, 0.8)));
  }
  for (let i = 0; i < S.pages; i++) {        // collected pages / photos flutter after it
    const k = (t - 1.0 - i * 0.12) / 0.5; if (k <= 0 || k >= 1) continue;
    spr(STORY().pageSpr, sx(arc(cl.x, BOOK_AT.x, k, 0)) + Math.round(Math.sin(k * 12) * 3), sy(arc(cl.z + 1.4, BOOK_AT.z, k, 1.0)));
  }
  if (wiz && t > 2.1 && t < 2.8) { const k = (t - 2.1) / 0.7; drawProp("sleepcat", sx(arc(cl.x + 0.2, CAT_AT.x, k, 0)), sy(arc(cl.z + 1.3, CAT_AT.z, k, 1.2))); }
}
function drawEnding() {
  const t = Ending.t;
  const st = STORY(), caps = st.caps
    || [[0, "YOU MADE IT, PIP!"], [0.8, "HERE'S YOUR SPELL BOOK!"], [2.0, "AND YOUR SLEEPY KITTY..."],
       [3.1, "THE WIZARD SMILES..."], [3.8, "...AND YAWNS..."], [4.5, "SHHH! HE'S FAST ASLEEP."]];
  if (S.flashT !== undefined && t - S.flashT < 0.35) {     // the selfie flash
    ctx.fillStyle = "rgba(255,255,255," + (1 - (t - S.flashT) / 0.35).toFixed(2) + ")"; ctx.fillRect(0, 0, W, H);
  }
  let ci = 0; for (let i = 0; i < caps.length; i++) if (t >= caps[i][0]) ci = i;
  const lines = [caps[ci][1]];
  if (ci === 1 && S.pages) lines.push("+ " + S.pages + " " + (S.pages > 1 ? st.pluses || st.plus + "S" : st.plus) + "!");
  caption(lines, t - caps[ci][0], H - 34);
  skipHint();
  drawMute();
}

// ================================================================ parachute bonus
const Para = { t: 0, vx: 0, coins: 0, stars: 0, items: [], z0: 0, z1: 2.4, hold: 0 };
function startPara() {
  face = "sleep";
  if (LEVEL === "wizard") { S.asleep = true; S.bookIn = true; S.catIn = true; S.catOn = false; }
  else { S.itemIn = true; if (LEVEL === "grandpa") { S.phoneIn = true; S.waving = true; } else if (STORY().sleep) S.asleep = true; else S.beaming = true; }
  if (S.tut) {                                 // reached the top: the "climb to Grandpa" lesson is done
    const u = S.tut; while (u.i < TUT_STEPS.indexOf("chute")) { u.steps.push({ step: TUT_STEPS[u.i], t: +S.t.toFixed(2) }); u.i++; }
    u.t0 = 0;
  }
  Para.steered = false;
  const cl = S.cl; cl.tw = null; cl.mode = "climb";
  Para.t = 0; Para.vx = 0; Para.coins = 0; Para.stars = 0; Para.hold = 0; Para.z0 = cl.z; Para.z1 = 2.4;
  Para.items = [];
  const span = Para.z0 - Para.z1, cstep = Math.max(0.78, (span - 3) / 24), sstep = Math.max(4.2, (span - 6) / 4.4);
  for (let z = Para.z0 - 2.4, i = 0; z > Para.z1 + 0.6; z -= cstep, i++) Para.items.push({ kind: "coin", x: 2.5 + 1.9 * Math.sin(z * 0.42), z, t: i * 0.3 });
  for (let z = Para.z0 - 4.5; z > Para.z1 + 1.5; z -= sstep) Para.items.push({ kind: "star", x: 2.5 - 2.0 * Math.sin(z * 0.42), z, t: 0 });
  setScreen("para"); sfx.pop(); sfx.whoosh();
}
function steer(side) {
  if (screen !== "para" || paused) return;
  Para.steered = true;
  if (tutStep() === "chute") tutNext();
  Para.vx = Math.max(-T.STEER_MAX, Math.min(T.STEER_MAX, Para.vx + (side === "L" ? -1 : 1) * T.STEER_TAP));
}
function updatePara(dt) {
  storyFx(dt);
  const cl = S.cl, t = Para.t += dt;
  const open = Math.min(1, t / 0.6);
  const v = (Para.z0 - Para.z1) / (T.PARA_S - 0.3);
  const slow = S.tut && !Para.steered ? T.TUT_PARA_SLOW : 1;   // tutorial: hang in the air until the first steer
  if (slow < 1) Para.t -= dt * (1 - slow);
  cl.z = Math.max(Para.z1, cl.z - v * dt * open * slow);
  Para.vx += Para.hold * T.STEER_HOLD * dt;
  Para.vx *= Math.exp(-T.STEER_DRAG * dt);
  cl.x = Math.max(0.15, Math.min(COLS - 0.15, cl.x + Para.vx * dt));
  if (cl.x <= 0.15 || cl.x >= COLS - 0.15) Para.vx = 0;
  for (const it of Para.items) {
    it.t += dt;
    if (S.magnet && !it.got && it.kind === "coin") {     // coin magnet boost
      const dx = cl.x - it.x, dz = cl.z + 1.0 - it.z, d = Math.hypot(dx, dz);
      if (d < T.MAGNET_R && d > 0.01) { const v = Math.min(d, 7 * dt); it.x += dx / d * v; it.z += dz / d * v; it.pulled = true; }
    }
    if (!it.got && Math.abs(it.x - cl.x) < 0.6 && Math.abs(it.z - (cl.z + 1.0)) < 1.0) {
      it.got = true;
      if (it.kind === "coin") { Para.coins++; S.score += 10; sfx.coin(); sparkle(it.x, it.z, 4, C.hardhat); }
      else { Para.stars++; S.score += 100; sfx.star(); sparkle(it.x, it.z, 12, C.white); popText("STAR!", cl.x, cl.z + 3, C.hardhat); }
    }
  }
  const vh = H / P;
  S.camZ = Math.max(BOTTOM_Z, Math.min(TOP - vh, cl.z + 2.4 - vh * 0.62));
  if (cl.z <= Para.z1 + 1e-3 && t > 1) startBird();
}
const STAR = ["0001000", "0001000", "0011100", "1111111", "0111110", "0110110", "1100011"];
function drawParaItems() {
  for (const it of Para.items) {
    if (it.got) continue;
    const x = sx(it.x), y = sy(it.z); if (y < -20 || y > H + 20) continue;
    if (it.kind === "coin") spr("coin_" + (Math.floor(it.t * 8) % 4), x, y);
    else { bitmap(STAR, x - 3, y - 3, Math.floor(it.t * 6) % 2 ? C.hardhat : C.white, "#000"); goodSparkle(x, y, it.t); }
  }
}
function lineP(x0, y0, x1, y1, col) {        // 1px pixel line
  ctx.fillStyle = col; const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0), 1);
  for (let i = 0; i <= n; i++) ctx.fillRect(Math.round(x0 + (x1 - x0) * i / n), Math.round(y0 + (y1 - y0) * i / n), 1, 1);
}
function drawChute(x, y, sway, open, lk) {
  if (open <= 0) return;
  const cy = y - 62 - Math.round(4 * (1 - open));
  const cx = x + sway;
  lineP(cx - 30, cy, x - 8, y - 56, "#e0e0f0"); lineP(cx + 30, cy, x + 8, y - 56, "#e0e0f0");
  lineP(cx - 12, cy, x - 6, y - 56, "#e0e0f0"); lineP(cx + 12, cy, x + 6, y - 56, "#e0e0f0");
  lk = lk || look;
  drawProp(lk.chute > 0 ? "canopy_" + A.chutes[lk.chute - 1] : "canopy", cx, cy + 2, lk);
}
function drawParaPip() {
  drawParaItems();
  const cl = S.cl, x = sx(cl.x), y = sy(cl.z), sway = Math.round(-Para.vx * 2);
  drawChute(x, y, sway, Math.min(1, Para.t / 0.4));
  drawPip(x, y, "para", { head: "own", pack: true });
}
function drawPara() {
  ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(0, 0, W, 11);
  text(String(S.score).padStart(6, "0"), 3, 2, C.white);
  spr("coin_0", 60, 6); text("X " + Para.coins, 68, 2, C.hardhat);
  bitmap(STAR, 104, 2, C.hardhat); text("X " + Para.stars, 114, 2, C.hardhat);
  const left = Math.max(0, Math.ceil(T.PARA_S - Para.t));
  text("BONUS", W - 54, 2, C.acc2); text(String(left), W - 14, 2, C.white);
  drawBoostHUD();
  if (Para.t < 3.2) caption(["PARACHUTE BONUS!", "TAP LEFT / RIGHT TO STEER"], Para.t, H - 34);
  drawTutPrompt();
  drawButton(PAUSE_BTN(), "PAUSE", false);
  drawMute();
}

// ================================================================ the friendly bird carries Pip off
const Bird = { t: 0, cues: {}, x: 0, z: 0 };
function startBird() { Bird.t = 0; Bird.cues = {}; setScreen("bird"); inputLockUntil = now + 500; }
function birdPos() {
  const cl = S.cl, t = Bird.t, hand = { x: cl.x + 0.05, z: cl.z + 1.78 + 0.5 };
  if (t < 1.0) { const k = t / 1.0, e = 1 - (1 - k) * (1 - k); return { x: COLS + 1.5 + (hand.x - COLS - 1.5) * e, z: hand.z + 2.2 * (1 - e) }; }
  return hand;
}
function updateBird(dt) {
  storyFx(dt);
  const t = Bird.t += dt, cl = S.cl, c = (n, at, fn) => { if (t >= at && !Bird.cues[n]) { Bird.cues[n] = 1; fn(); } };
  c("tweet", 0.1, sfx.tweet); c("tweet2", 0.7, sfx.tweet);
  c("grab", 1.0, () => { sfx.pop(); sparkle(cl.x, cl.z + 3.2, 14, C.white); sfx.crowd(10); });
  c("next", 1.3, () => sfx.jingle());
  if (t < 1.0) cl.z = Math.max(Para.z1 - 0.3, cl.z - 0.3 * dt);
  else { const k = t - 1.0; cl.x -= (0.6 + k * 1.6) * dt; cl.z += (0.6 + k * 1.4) * dt; }
  if (Math.floor(t * 8) !== Math.floor((t - dt) * 8) && Math.floor(t * 8) % 3 === 0) sfx.flap();
  if (t >= T.BIRD_S) showResults();
}
function drawBirdPip() {
  const cl = S.cl, x = sx(cl.x), y = sy(cl.z), t = Bird.t;
  if (t < 1.0) { drawChute(x, y, 0, 1); drawPip(x, y, "para", { head: "own", pack: true }); }
  else drawPip(x, y, "cheer", { head: "own", pack: true });
  const b = birdPos();
  spr("bird_" + [0, 1, 2, 1][Math.floor(t * 10) % 4], sx(b.x), sy(b.z));
}
function drawBird() {
  const t = Bird.t;
  if (t > 1.2) { caption(nextText(), t - 1.2, 40); if (t > 1.8) textC("WHEEE!", 70, C.hardhat, 2); }
  else caption("HERE COMES A FRIEND!", t, 40);
  skipHint();
}

// ================================================================ results / thanks
function showResults() {
  const r = S.result || {};
  r.pages = S.pages; r.pageBonus = 0; r.coins = Para.coins; r.stars = Para.stars;
  if (!r.coinBonus) { r.coinBonus = Para.coins * 10 + Para.stars * 100; }
  S.result = r;
  if (S.score > hiscore) { hiscore = S.score; localStorage.setItem("bc_hi", hiscore); }
  bank(true); Results.sel = 0;
  setScreen("results"); inputLockUntil = now + 900; sfx.win();
}
const Results = { sel: 0 };
const RESULT_ACTIONS = ["play", "levels", "shop", "pip", "intro"];
function resultsAct(i) {
  if (i === 0) resultsPlay();
  else if (i === 1) openLevels("results");
  else if (i === 2) openShop("results");
  else if (i === 3) setScreen("creator");
  else startCine("results");
}
function resultsKey(code) {
  if (now < inputLockUntil) return;
  if (["ArrowLeft", "ArrowUp", "KeyA", "KeyW"].includes(code)) Results.sel = (Results.sel + 4) % 5;
  else if (["ArrowRight", "ArrowDown", "KeyD", "KeyS"].includes(code)) Results.sel = (Results.sel + 1) % 5;
  else if (code === "Enter" || code === "Space") resultsAct(Results.sel);
  else if (code === "Escape" || code === "Backspace") setScreen("title");
}
function resultsLayout() {
  const oy = Math.max(0, Math.round((H - 256) / 2)), bw = 103, x0 = 6, x1 = W - 6 - bw, bh = H > 300 ? 26 : 20, gap = bh + 4;
  const by = H - 20 - gap * 3 - Math.max(0, Math.round((H - 256) / 4));
  return { oy, play: { x: x0, y: by, w: bw, h: bh }, levels: { x: x1, y: by, w: bw, h: bh },
           shop: { x: x0, y: by + gap, w: bw, h: bh }, pip: { x: x1, y: by + gap, w: bw, h: bh },
           intro: { x: Math.round((W - bw) / 2), y: by + gap * 2, w: bw, h: bh } };
}
const nextLevel = () => { const n = STORY().next; return n && known(n) && isUnlocked(n) ? n : null; };
function nextText() { const n = STORY().next; return n && known(n) ? "NEXT: " + THE_NAMES[n] + "!" : "MORE GIANTS COMING SOON!"; }
function resultsPlay() { const n = nextLevel(); if (n) goLevel(n, () => { saveLevel(); startIntro(); }); else startIntro(); }
function drawResults() {
  const L = resultsLayout(), oy = L.oy, t = (now - sceneStart) / 1000, r = S.result || {};
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H); stars(t, 50);
  textC("THANK YOU, PIP!", oy + 8, C.hardhat, 2);
  textC(STORY().happy, oy + 28, C.white);
  drawPip(40, oy + 112, Math.floor(t * 2) % 2 ? "f_cheer" : "f_wave", { head: "own", pack: true });
  goodSparkle(40, oy + 70, t);
  const lines = [["HEIGHT", r.height], ["TIME", r.timeBonus], ["LIVES", r.lifeBonus], ["HAT", r.hatBonus],
                 [STORY().pages + " " + (r.pages || 0) + "/" + T.PAGES, (r.pages || 0) * 150], ["COINS " + (r.coins || 0), (r.coins || 0) * 10], ["STARS " + (r.stars || 0), (r.stars || 0) * 100]];
  lines.forEach(([l, v], i) => { if (t > 0.2 + i * 0.12) { const y = oy + 44 + i * 10; text(l, 76, y, C.hair3); const s = String(v || 0); text(s, W - 10 - textW(s), y, C.white); } });
  if (t > 1.1) { const y = oy + 44 + lines.length * 10 + 3; text("SCORE", 76, y, C.acc2); const s = String(S.score); text(s, W - 10 - textW(s), y, C.acc2); }
  if (r.earned !== undefined) {
    const s1 = "+" + r.earned + " COINS!", w1 = textW(s1) + 10, x1 = Math.round((W - w1 - 8 - textW("WALLET 0000")) / 2);
    coinIcon(x1, oy + 130); text(s1, x1 + 10, oy + 130, C.hardhat);
    text("WALLET " + wallet, x1 + w1 + 8, oy + 130, C.white);
  }
  const msgs = [];                           // new unlocks (alternating if there are two)
  if (S.unlocked) msgs.push(S.unlocked === "wizard" ? "NEW: THE WIZARD (WORLD 3) UNLOCKED!" : "NEW: " + THE_NAMES[S.unlocked] + " UNLOCKED!");
  if (S.newSet) msgs.push(GIANT_NAMES[S.newSet] + " SET UNLOCKED! SEE THE SHOP");
  if (msgs.length) { const m = msgs[Math.floor(t / 1.6) % msgs.length]; if (Math.floor(t * 2.5) % 3) textC(m, oy + 142, C.acc2); }
  else textC(nextText(), oy + 142, "#a0a0c0");
  const nl = nextLevel();
  drawButton(L.play, nl ? "NEXT: " + STORIES[nl].short : "PLAY AGAIN", Results.sel === 0); drawButton(L.levels, "LEVELS", Results.sel === 1);
  drawButton(L.shop, "SHOP", Results.sel === 2, C.acc2); drawButton(L.pip, "CHANGE PIP", Results.sel === 3); drawButton(L.intro, "WATCH INTRO", Results.sel === 4);
  drawMute();
}

// ================================================================ character creator
const OPTS = [
  { k: "body", label: "BODY", names: ["BOY", "GIRL"] },
  { k: "hair", label: "HAIR", names: A.hairs.map((h) => h.toUpperCase()) },
  { k: "hairCol", label: "HAIR COLOR", list: HAIR_COLS, col: 1 },
  { k: "skin", label: "SKIN", list: SKINS, col: 0 },
  { k: "outfit", label: "OUTFIT", list: OUTFITS, col: 1 },
  { k: "gear", label: "BACKPACK", list: GEARS, col: 1 },
  { k: "hat", label: "HAT", names: HAT_NAMES },
];
const Creator = { sel: 0, back: false, flash: -1, flashT: 0 };
function creatorLayout() {
  // arrow buttons are AW x (rowH-2) native px: >= 44 CSS px on iPhone (5 or 3 device px per native px)
  const top = H > 300 ? 34 : 24, bottomH = H > 300 ? 34 : 26, AW = 30;
  const rowH = Math.max(28, Math.min(36, Math.floor((H - top - bottomH - 10) / OPTS.length)));
  const oy = Math.max(top, Math.round((H - bottomH - 6 - rowH * OPTS.length + top) / 2));
  const rows = OPTS.map((o, i) => ({ y: oy + i * rowH, h: rowH - 2, L: { x: 84, y: oy + i * rowH, w: AW, h: rowH - 2 }, R: { x: W - 2 - AW, y: oy + i * rowH, w: AW, h: rowH - 2 } }));
  const by = H - bottomH - 4;
  return { rows, rowH, oy, AW, rand: { x: 6, y: by, w: 60, h: bottomH }, shop: { x: 70, y: by, w: 56, h: bottomH }, start: { x: 130, y: by, w: W - 154, h: bottomH },
           turn: { x: 10, y: oy + rowH * OPTS.length - 22, w: 64, h: 18 }, preview: { x: 0, y: oy, w: 82, h: rowH * OPTS.length - 26 } };
}
function optCount(o) { return (o.names || o.list).length; }
function optValues(o) { const v = []; for (let i = 0; i < optCount(o); i++) if (valueOk(o.k, i)) v.push(i); return v; }   // free + owned
function changeOpt(i, d) {
  const o = OPTS[i], vs = optValues(o), at = Math.max(0, vs.indexOf(look[o.k]));
  look[o.k] = vs[(at + d + vs.length) % vs.length]; Creator.sel = i; Creator.flash = i; Creator.flashT = now;
  saveLook(); Snd.tone(d > 0 ? 880 : 660, 0.05, 0.06);
}
function randomizeLook() {
  for (const o of OPTS) { const vs = optValues(o); look[o.k] = vs[Math.floor(Math.random() * vs.length)]; }
  saveLook(); Creator.flash = 99; Creator.flashT = now; sfx.star();
}
function startFromCreator() {
  saveLook(); sfx.held();
  if (!cineSeen) startCine("intro"); else startIntro();
}
function drawCreator() {
  const L = creatorLayout(), t = now / 1000;
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H); stars(t, 24);
  if (H > 300) textC("MAKE YOUR PIP!", 13, C.hardhat, 2); else textC("MAKE YOUR PIP!", 8, C.hardhat);
  drawWallet(W - 4, 3, "right");
  // live preview, 2x
  const pv = L.preview, px = pv.x + pv.w / 2, py = pv.y + pv.h - 4;
  ctx.fillStyle = "rgba(255,255,255,0.06)"; ctx.fillRect(pv.x + 6, pv.y, pv.w - 8, pv.h);
  const k = pv.h >= 150 ? 2 : pv.h >= 110 ? 2 : 1;
  const pose = Creator.back ? (Math.floor(t * 1.2) % 2 ? "stand" : "cheer") : (Math.floor(t * 0.8) % 3 === 2 ? "f_wave" : "f_stand");
  if (Creator.flash === 99 && now - Creator.flashT < 300) sparkleRing(px, py - 60, (now - Creator.flashT) / 300);
  drawPip(px, py, pose, { head: "own", pack: true, cat: true, scale: k });
  drawButton(L.turn, Creator.back ? "FRONT" : "TURN", false);
  // option rows
  L.rows.forEach((r, i) => {
    const o = OPTS[i], v = look[o.k], hot = Creator.sel === i;
    ctx.fillStyle = hot ? "rgba(248,232,72,0.14)" : "rgba(0,0,0,0.35)"; ctx.fillRect(84, r.y, W - 86, r.h);
    drawButton(r.L, "<", Creator.flash === i && now - Creator.flashT < 120); drawButton(r.R, ">", false);
    const cx = r.L.x + r.L.w + (r.R.x - r.L.x - r.L.w) / 2, ly = r.y + Math.max(2, Math.round(r.h / 2 - 9));
    text(o.label, Math.round(cx - textW(o.label) / 2), ly, C.hair3, 1, null);
    let name = o.names ? o.names[v] : o.list[v].length > 2 && typeof o.list[v][0] === "string" && o.list[v][0][0] !== "#" ? o.list[v][0] : "TONE " + (v + 1);
    const sw = o.list ? 9 : 0, wName = textW(name) + (sw ? sw + 3 : 0), nx = Math.round(cx - wName / 2), ny = ly + 10;
    if (o.list) { const colr = o.list[v][o.col]; ctx.fillStyle = "#000"; ctx.fillRect(nx - 1, ny - 1, sw + 2, 9); ctx.fillStyle = colr; ctx.fillRect(nx, ny, sw, 7); }
    text(name, nx + (sw ? sw + 3 : 0), ny, C.white);
  });
  drawButton(L.rand, "RANDOM", Creator.flash === 99 && now - Creator.flashT < 150, C.acc2);
  drawButton(L.shop, "SHOP", false, C.acc2);
  drawButton(L.start, "START!", Math.floor(t * 2) % 2 === 0);
  drawMute();
}
function creatorTap(p) {
  const L = creatorLayout();
  for (let i = 0; i < L.rows.length; i++) {
    const r = L.rows[i];
    if (inRect(p, r.L)) { changeOpt(i, -1); return; }
    if (inRect(p, r.R)) { changeOpt(i, 1); return; }
    if (p.x >= 84 && p.y >= r.y && p.y < r.y + r.h) { changeOpt(i, 1); return; }   // tapping the row also steps it
  }
  if (inRect(p, L.rand)) { randomizeLook(); return; }
  if (inRect(p, L.shop)) { openShop("creator"); return; }
  if (inRect(p, L.start)) { startFromCreator(); return; }
  if (inRect(p, L.turn) || inRect(p, L.preview)) { Creator.back = !Creator.back; Snd.tone(520, 0.05, 0.05); }
}

// ================================================================ coin shop screen
const COIN_ICON = ["0011100", "0122210", "1221221", "1221221", "1221221", "0122210", "0011100"];
function coinIcon(x, y) {                     // 7x7 UI coin, top-left at (x, y)
  COIN_ICON.forEach((r, j) => { for (let i = 0; i < 7; i++) if (r[i] !== "0") { ctx.fillStyle = r[i] === "1" ? "#a06010" : "#f8c830"; ctx.fillRect(x + i, y + j, 1, 1); } });
  ctx.fillStyle = "#fff4b0"; ctx.fillRect(x + 2, y + 2, 1, 2);
}
function drawWallet(x, y, align) {
  const s = String(wallet), w = 10 + textW(s), x0 = align === "right" ? x - w : align === "center" ? Math.round(x - w / 2) : x;
  ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(x0 - 2, y - 2, w + 4, 11);
  coinIcon(x0, y); text(s, x0 + 10, y, C.hardhat);
}
const ICONS = {
  b_hardhat: [["0011100", "0111110", "1111111", "1111111", "0000000"], "hardhat"],
  b_life: [HEART, "shirt"],
  b_magnet: [["1100011", "1100011", "1100011", "1100011", "1110111", "0111110", "0011100"], "shirt"],
  b_slowmo: [["1111111", "0100010", "0011100", "0001000", "0011100", "0100010", "1111111"], "acc2"],
};
function bitmapK(rows, x, y, col, k) {
  ctx.fillStyle = col;
  rows.forEach((r, j) => { for (let i = 0; i < r.length; i++) if (r[i] === "1") ctx.fillRect(x + i * k, y + j * k, k, k); });
}
function boostIcon(id, x, y, k = 1, dim) {     // (x, y) = centre
  const [rows, c] = ICONS[id], w = rows[0].length * k, h = rows.length * k;
  bitmapK(rows, Math.round(x - w / 2) + k, Math.round(y - h / 2) + k, "#000", k);
  bitmapK(rows, Math.round(x - w / 2), Math.round(y - h / 2), dim ? "#605878" : C[c], k);
  if (id === "b_magnet" && !dim) { ctx.fillStyle = C.white; ctx.fillRect(Math.round(x - w / 2), Math.round(y - h / 2), 2 * k, k); ctx.fillRect(Math.round(x - w / 2) + 5 * k, Math.round(y - h / 2), 2 * k, k); }
}
function drawBoostHUD() {                     // boosts in use this run, bottom-left
  if (!S || !S.boosts || !S.boosts.length) return;
  S.boosts.forEach((id, i) => {
    const x = 3 + i * 15, y = H - 15;
    const dim = (id === "b_slowmo" && S.t >= S.slowUntil) || (id === "b_hardhat" && S.hat === 0 && screen === "play");
    ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(x, y, 13, 13);
    ctx.fillStyle = dim ? "#3a2a50" : C.acc2; ctx.fillRect(x, y, 13, 1); ctx.fillRect(x, y + 12, 13, 1);
    boostIcon(id, x + 6, y + 6, 1, dim);
  });
  if (S.t < S.slowUntil && screen === "play") text("SLOW " + Math.ceil(S.slowUntil - S.t), 3 + S.boosts.length * 15 + 2, H - 12, C.acc2);
}
const Shop = { tab: 0, sel: [0, 0, 0, 0, 0], from: "title", confirm: null, toast: null, toastT: 0, boughtT: -1e9 };
function openShop(from) { Shop.from = from; Shop.confirm = null; Shop.toast = null; setScreen("shop"); Snd.tone(700, 0.06, 0.05); }
function shopItems(tab) { const id = SHOP_TABS[tab === undefined ? Shop.tab : tab][0]; return CATALOG.filter((i) => i.tab === id); }
function shopSel() { const l = shopItems(); return l[Math.min(Shop.sel[Shop.tab], l.length - 1)]; }
function shopLayout() {
  const tabY = 18, tabH = H > 300 ? 30 : 22, barH = H > 300 ? 34 : 26, barY = H - barH - 4, infoY = barY - 22;
  const tabs = SHOP_TABS.map((t, i) => ({ x: 2 + i * 44, y: tabY, w: 44, h: tabH }));
  const list = shopItems(), ly0 = tabY + tabH + 4, avail = infoY - 3 - ly0;
  const rh = Math.max(16, Math.min(30, Math.floor(avail / list.length)));
  const rows = list.map((it, i) => ({ x: 80, y: ly0 + i * rh, w: W - 82, h: rh - 2, it }));
  const back = { x: 4, y: barY, w: 56, h: barH }, act = { x: 64, y: barY, w: W - 64 - 25, h: barH };
  const buy = { x: 64, y: barY, w: 66, h: barH }, use = { x: 134, y: barY, w: W - 134 - 25, h: barH };
  const my = Math.round(H / 2) - 44;
  return { tabs, rows, rh, back, act, buy, use, infoY, barY, preview: { x: 2, y: ly0, w: 76, h: avail },
           modal: { y: my, h: 88 }, yes: { x: 30, y: my + 54, w: 72, h: 26 }, no: { x: W - 102, y: my + 54, w: 72, h: 26 } };
}
function tryLook(it) { const l = Object.assign({}, look); if (it && it.key) l[it.key] = it.val; return l; }
function isWorn(it) { return !!it.key && look[it.key] === it.val; }
function toast(lines) { Shop.toast = lines; Shop.toastT = now; }
function itemState(it) {
  if (it.tab === "boosts") return "boost";
  if (isWorn(it)) return "worn";
  if (isOwned(it)) return "owned";
  return it.set ? "locked" : "buy";
}
function shopAction(it) {
  it = it || shopSel(); if (!it) return;
  const st = itemState(it);
  if (st === "boost" || st === "buy") return askBuy(it);
  if (st === "locked") { toast([lockText(it)]); Snd.tone(330, 0.08, 0.05); return; }
  if (st === "owned") { look[it.key] = it.val; saveLook(); sfx.held(); Shop.boughtT = now; return; }
  if (st === "worn" && !it.free) { look[it.key] = DEFAULT_LOOK[it.key]; saveLook(); Snd.tone(520, 0.05, 0.05); }   // take it off
}
function askBuy(it) {
  if (it.tab === "boosts" && boosts[it.id] >= T.BOOST_STACK) { toast(["YOU HAVE PLENTY OF THOSE!", "USE SOME ON A CLIMB FIRST."]); return; }
  if (wallet < it.price) { toast(["NOT ENOUGH COINS YET!", "KEEP CLIMBING TO EARN MORE."]); Snd.tone(392, 0.12, 0.05, "triangle"); return; }
  Shop.confirm = it; Snd.tone(660, 0.05, 0.05);
}
function confirmBuy(yes) {
  const it = Shop.confirm; Shop.confirm = null;
  if (!yes || !it) { Snd.tone(440, 0.05, 0.04); return; }
  if (wallet < it.price) { toast(["NOT ENOUGH COINS YET!", "KEEP CLIMBING TO EARN MORE."]); return; }
  wallet -= it.price;
  if (it.tab === "boosts") {
    boosts[it.id] = (boosts[it.id] || 0) + 1;
    if (canEquip(it.id)) boostEq.push(it.id);            // ready for the next climb
  } else { owned.add(it.id); look[it.key] = it.val; saveLook(); }      // wear it straight away
  saveShop(); sfx.star(); Shop.boughtT = now;
  toast([it.tab === "boosts" ? "GOT IT! " + it.name + " X" + boosts[it.id] : "YAY! NEW " + it.name + "!"]);
}
function canEquip(id) { return !boostEq.includes(id) && boostEq.length < T.MAX_BOOSTS && !(isDef(id) && boostEq.some(isDef)); }
function toggleBoost(it) {
  const i = boostEq.indexOf(it.id);
  if (i >= 0) { boostEq.splice(i, 1); Snd.tone(440, 0.05, 0.05); }
  else if (!(boosts[it.id] > 0)) { toast(["BUY ONE FIRST!"]); return; }
  else if (isDef(it.id) && boostEq.some(isDef)) { toast(["ONLY ONE HELPER BOOST PER CLIMB!", "(HARD HAT, LIFE OR SLOW-MO)"]); return; }
  else if (boostEq.length >= T.MAX_BOOSTS) { toast(["ONLY " + T.MAX_BOOSTS + " BOOSTS PER CLIMB!", "TURN ONE OFF FIRST."]); return; }
  else { boostEq.push(it.id); Snd.tone(880, 0.05, 0.05); }
  saveShop();
}
function shopBack() {
  const f = Shop.from;
  if (f === "results") setScreen("results"); else if (f === "creator") setScreen("creator"); else setScreen("title");
}
function shopTap(p) {
  const L = shopLayout(), it = shopSel();
  if (Shop.confirm) { if (inRect(p, L.yes)) confirmBuy(true); else if (inRect(p, L.no)) confirmBuy(false); return; }
  if (Shop.toast && now - Shop.toastT < 2200 && now - Shop.toastT > 250) Shop.toast = null;
  for (let i = 0; i < L.tabs.length; i++) if (inRect(p, L.tabs[i])) { Shop.tab = i; Snd.tone(620 + i * 40, 0.04, 0.05); return; }
  for (let i = 0; i < L.rows.length; i++) if (inRect(p, L.rows[i])) {
    if (Shop.sel[Shop.tab] === i) shopAction(L.rows[i].it); else { Shop.sel[Shop.tab] = i; Snd.tone(760, 0.03, 0.04); }
    return;
  }
  if (inRect(p, L.back)) { shopBack(); return; }
  if (it && it.tab === "boosts") { if (inRect(p, L.buy)) askBuy(it); else if (inRect(p, L.use)) toggleBoost(it); return; }
  if (inRect(p, L.act)) shopAction(it);
}
function shopKey(code) {
  if (Shop.confirm) { if (code === "Enter" || code === "KeyY" || code === "Space") confirmBuy(true); else if (["Escape", "KeyN", "Backspace"].includes(code)) confirmBuy(false); return; }
  const n = shopItems().length;
  if (KEY_LEFT.includes(code)) Shop.tab = (Shop.tab + SHOP_TABS.length - 1) % SHOP_TABS.length;
  else if (KEY_RIGHT.includes(code)) Shop.tab = (Shop.tab + 1) % SHOP_TABS.length;
  else if (code === "ArrowUp" || code === "KeyW") Shop.sel[Shop.tab] = (Shop.sel[Shop.tab] + n - 1) % n;
  else if (code === "ArrowDown" || code === "KeyS") Shop.sel[Shop.tab] = (Shop.sel[Shop.tab] + 1) % n;
  else if (code === "Enter" || code === "Space") shopAction();
  else if (code === "KeyU" && shopSel().tab === "boosts") toggleBoost(shopSel());
  else if (code === "Escape" || code === "Backspace") shopBack();
}
const LOCK = ["01110", "10001", "10001", "11111", "11011", "11111"];
function drawShop() {
  const L = shopLayout(), t = now / 1000, it = shopSel(), st = itemState(it);
  ctx.fillStyle = "#101030"; ctx.fillRect(0, 0, W, H); stars(t, 24);
  text("SHOP", 6, 2, C.hardhat, 2);
  drawWallet(W - 4, 4, "right");
  L.tabs.forEach((b, i) => drawButton(b, SHOP_TABS[i][1], i === Shop.tab));
  // ---- live preview: Pip wearing the selected item (boosts: the boost icon)
  const pv = L.preview;
  ctx.fillStyle = "rgba(255,255,255,0.06)"; ctx.fillRect(pv.x, pv.y, pv.w, pv.h);
  const px = pv.x + pv.w / 2, lk = tryLook(it);
  if (now - Shop.boughtT < 400) sparkleRing(px, pv.y + pv.h / 2, (now - Shop.boughtT) / 400);
  if (it.tab === "boosts") {
    boostIcon(it.id, px, pv.y + 34, 4);
    textC2("HAVE " + (boosts[it.id] || 0), px, pv.y + 66, C.white);
    const on = boostEq.includes(it.id);
    textC2(on ? "ON FOR" : "OFF", px, pv.y + 80, on ? C.acc2 : "#8080a0");
    if (on) textC2("NEXT CLIMB", px, pv.y + 90, C.acc2);
    textC2("IN USE " + boostEq.length + "/" + T.MAX_BOOSTS, px, pv.y + pv.h - 22, C.hair3);
    textC2("1 HELPER MAX", px, pv.y + pv.h - 12, C.hair3);
  } else if (it.tab === "chutes") {
    const y = pv.y + pv.h - 8, sway = Math.round(Math.sin(t * 1.6) * 3);
    drawChute(px, y, sway, 1, lk); drawPip(px, y, "para", { head: "own", pack: true, look: lk });
  } else {
    const k = pv.h >= 140 ? 2 : 1, back = it.tab === "packs" && Math.floor(t * 0.7) % 2 === 1;
    drawPip(px, pv.y + pv.h - 4, back ? "stand" : Math.floor(t * 0.8) % 3 === 2 ? "f_wave" : "f_stand", { head: "own", pack: true, look: lk, scale: k });
    if (it.tab === "packs") text(back ? "BACK" : "FRONT", pv.x + 2, pv.y + 2, "#8080a0");
  }
  // ---- item list
  L.rows.forEach((r, i) => {
    const s2 = itemState(r.it), hot = i === Shop.sel[Shop.tab], ty = r.y + Math.round((r.h - 7) / 2);
    ctx.fillStyle = hot ? "rgba(248,232,72,0.18)" : "rgba(0,0,0,0.4)"; ctx.fillRect(r.x, r.y, r.w, r.h);
    if (hot) { ctx.fillStyle = C.hardhat; ctx.fillRect(r.x, r.y, 1, r.h); ctx.fillRect(r.x + r.w - 1, r.y, 1, r.h); ctx.fillRect(r.x, r.y, r.w, 1); ctx.fillRect(r.x, r.y + r.h - 1, r.w, 1); }
    let nm = r.it.name; if (s2 === "boost" && boostEq.includes(r.it.id)) nm = ">" + nm;
    text(nm, r.x + 3, ty, s2 === "locked" ? "#8080a0" : C.white);
    const rx = r.x + r.w - 3;
    if (s2 === "locked") { bitmap(LOCK, rx - 5, ty, "#a0a0c0"); }
    else if (s2 === "worn") text("WORN", rx - textW("WORN"), ty, C.acc2);
    else if (s2 === "owned") text("OWN", rx - textW("OWN"), ty, "#a0d0a0");
    else { const ps = String(r.it.price); text(ps, rx - textW(ps), ty, wallet >= r.it.price ? C.hardhat : "#a08060"); }
  });
  // ---- info line (what it does / how to unlock)
  const info = it.tab === "boosts" ? it.info : st === "locked" ? [lockText(it), "(SHOWN ON PIP - TRY IT ON!)"]
    : st === "buy" ? [it.name + " - " + it.price + " COINS", wallet >= it.price ? "TAP BUY!" : "NEED " + (it.price - wallet) + " MORE COINS"]
    : st === "worn" ? [it.name, it.free ? "THE CLASSIC LOOK" : "YOU'RE WEARING IT!"] : [it.name, "YOURS! TAP WEAR"];
  info.forEach((l, i) => textC(l, L.infoY + i * 10, i ? C.hair3 : C.white));
  // ---- bottom bar
  drawButton(L.back, "BACK", false);
  if (it.tab === "boosts") {
    drawButton(L.buy, "BUY " + it.price, false, wallet >= it.price ? C.hardhat : "#806040");
    drawButton(L.use, boostEq.includes(it.id) ? "USE: ON" : "USE: OFF", boostEq.includes(it.id), C.acc2);
  } else {
    const lab = st === "buy" ? "BUY " + it.price : st === "locked" ? "LOCKED" : st === "owned" ? "WEAR" : it.free ? "WEARING" : "TAKE OFF";
    drawButton(L.act, lab, st === "buy" && wallet >= it.price && Math.floor(t * 2) % 2 === 0, st === "locked" ? "#605878" : null);
    if (st === "buy") coinIcon(L.act.x + 6, L.act.y + Math.round(L.act.h / 2) - 4);
  }
  // ---- toast + confirm modal
  if (Shop.toast && now - Shop.toastT < 2400) {
    const n = Shop.toast.length, h = n * 10 + 8, y = L.barY - h - 26;
    ctx.fillStyle = "rgba(20,10,40,0.92)"; ctx.fillRect(6, y, W - 12, h);
    ctx.fillStyle = C.acc2; ctx.fillRect(6, y, W - 12, 1); ctx.fillRect(6, y + h - 1, W - 12, 1);
    Shop.toast.forEach((l, i) => textC(l, y + 5 + i * 10, i ? C.hair3 : C.white));
  }
  if (Shop.confirm) {
    const c = Shop.confirm, m = L.modal;
    ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(0, 0, W, H);
    panel(m.y, m.h);
    textC("BUY " + c.name + "?", m.y + 10, C.white);
    const ps = c.price + " COINS", pw = textW(ps) + 12, x0 = Math.round((W - pw) / 2);
    coinIcon(x0, m.y + 25); text(ps, x0 + 11, m.y + 25, C.hardhat);
    textC("YOU'LL HAVE " + (wallet - c.price) + " LEFT", m.y + 38, C.hair3);
    drawButton(L.yes, "YES!", Math.floor(t * 2) % 2 === 0); drawButton(L.no, "NO", false);
  }
  drawMute();
}
function textC2(s, cx, y, col) { text(s, Math.round(cx - textW(s) / 2), y, col); }

// ---------------------------------------------------------------- input
/** A tap / click / Enter outside of climbing. p = canvas point (or null for keyboard). Returns true if consumed.
 *  Flow: title -> how-to -> creator -> [opening cinematic, once] -> intro -> climb -> ending -> parachute -> bird -> results */
function advance(p) {
  if (!BC.ready) return true;
  if (paused) { if (p && inRect(p, pauseLayout().resume)) togglePause(); return true; }
  if ((screen === "play" && !S.result || screen === "para") && p && inRect(p, PAUSE_BTN())) { togglePause(); return true; }
  if (screen === "play" && !S.result) return false;
  if (screen === "para") return false;
  if (now < inputLockUntil) return true;
  if (screen === "title") {
    if (p && inRect(p, TITLE_INTRO_BTN())) { startCine("title"); return true; }
    if (p && inRect(p, TITLE_SHOP_BTN())) { openShop("title"); return true; }
    if (p && inRect(p, TITLE_LEVELS_BTN())) { openLevels("title"); return true; }
    if (p && inRect(p, TITLE_GEAR_BTN())) { openSettings("title"); return true; }
    setScreen(needsChoose() ? "choose" : "howto"); return true;
  }
  if (screen === "choose") { if (p) chooseTap(p); return true; }
  if (screen === "howto") {
    if (SKIP_TOP) { newGame(); setScreen("play"); inputLockUntil = now + 200; }
    else setScreen("creator");
    return true;
  }
  if (screen === "creator") { if (p) creatorTap(p); else startFromCreator(); return true; }
  if (screen === "shop") { if (p) shopTap(p); else shopAction(); return true; }
  if (screen === "levels") { if (p) levelsTap(p); else levelsAct(Levels.sel); return true; }
  if (screen === "settings") { if (p) settingsTap(p); else settingsAct(Settings.sel); return true; }
  if (screen === "cine") { endCine(); return true; }
  if (screen === "intro") { startPlayFromIntro(); return true; }
  if (screen === "ending") { startPara(); return true; }
  if (screen === "bird") { showResults(); return true; }
  if (screen === "results") {
    const L = resultsLayout();
    const i = p ? RESULT_ACTIONS.findIndex((id) => inRect(p, L[id])) : -1;
    if (i >= 0) { Results.sel = i; resultsAct(i); }
    return true;
  }
  if (screen === "play" && S.result) {
    const L = lossLayout(), i = p ? ["retry", "levels", "settings"].findIndex((id) => inRect(p, L[id])) : -1;
    if (i >= 0) { Loss.sel = i; lossAct(i); }
    return true;
  }
  return true;
}
function paraHold() {             // held touches / keys steer continuously
  if (paused) { Para.hold = 0; return; }
  let h = 0;
  for (const r of touches.values()) h += r.side === "L" ? -1 : r.side === "R" ? 1 : 0;
  h += (keysDown.has("L") ? -1 : 0) + (keysDown.has("R") ? 1 : 0) + mouseSide;
  Para.hold = Math.max(-1, Math.min(1, h));
}
const keysDown = new Set();
let mouseSide = 0;
function canvasPoint(cx, cy) {
  const r = cv.getBoundingClientRect();
  return { x: (cx - r.left) / r.width * W, y: (cy - r.top) / r.height * H };
}
function onMute(cx, cy) {
  const p = canvasPoint(cx, cy), y = MUTE.y();
  return p.x >= MUTE.x - 6 && p.y >= y - 6 && p.y <= y + MUTE.h + 6 && p.x <= W;
}
const touches = new Map();   // id -> {t, x, y, timer, brace}
let lastTouchStart = -1e9, lastTouchEnd = -1e9;
function sideOf(clientX) { const r = cv.getBoundingClientRect(); return clientX < r.left + r.width / 2 ? "L" : "R"; }   // halves of the play area

document.addEventListener("touchstart", (e) => {
  e.preventDefault();
  Snd.unlock();
  const t0 = performance.now();
  const multi = e.changedTouches.length >= 2 || (e.touches.length >= 2 && t0 - lastTouchStart < T.TWO_FINGER_MS);
  for (const tc of e.changedTouches) {
    const rec = { t: t0, x: tc.clientX, y: tc.clientY, brace: multi, multi, timer: 0 };
    touches.set(tc.identifier, rec);
    if (onMute(tc.clientX, tc.clientY)) { Snd.toggle(); rec.brace = true; continue; }
    if (advance(canvasPoint(tc.clientX, tc.clientY))) { rec.brace = true; continue; }
    if (screen === "para") { rec.side = sideOf(tc.clientX); rec.brace = true; steer(rec.side); paraHold(); continue; }
    if (multi) continue;
    rec.snap = snapClimb();
    reach(controls === "one" ? nextArm() : sideOf(tc.clientX));
    finishSnap(rec.snap);
    rec.timer = setTimeout(() => { if (touches.has(tc.identifier) && !rec.brace) { rec.hold = true; setHold(true); } }, T.LONG_MS);
  }
  if (multi && screen === "play" && !S.result) {
    for (const r of touches.values()) { r.brace = true; clearTimeout(r.timer); }
    brace();
  }
  lastTouchStart = t0;
}, { passive: false });
function touchEnd(e) {
  e.preventDefault();
  Snd.unlock();                              // iOS: resume() must also run inside touchend
  for (const tc of e.changedTouches) { const r = touches.get(tc.identifier); if (r) clearTimeout(r.timer); touches.delete(tc.identifier); }
  if (![...touches.values()].some((r) => r.hold)) setHold(false);
  paraHold();
  lastTouchEnd = performance.now();
}
document.addEventListener("touchend", touchEnd, { passive: false });
document.addEventListener("touchcancel", touchEnd, { passive: false });
/** Swipes: >= SWIPE_MIN_PX within SWIPE_MAX_MS along a clear axis. The touch's instant reach is undone, so a swipe
 *  is never also a tap. One hand: left/right = hop (dyno), down = climb down, up = quick double reach.
 *  Two hands: only swipe down is new (left/right/up drags stay plain taps, exactly as before). Parachute: left/right steer. */
function swipeDir(rec, tc) {
  const dx = tc.clientX - rec.x, dy = tc.clientY - rec.y, ax = Math.abs(dx), ay = Math.abs(dy);
  if (performance.now() - rec.t > T.SWIPE_MAX_MS || Math.max(ax, ay) < T.SWIPE_MIN_PX) return null;
  if (ax >= ay * T.SWIPE_AXIS) return dx < 0 ? "L" : "R";
  if (ay >= ax * T.SWIPE_AXIS) return dy > 0 ? "D" : "U";
  return null;
}
document.addEventListener("touchmove", (e) => {
  e.preventDefault();
  if (paused) return;
  for (const tc of e.changedTouches) {
    const rec = touches.get(tc.identifier);
    if (!rec || rec.swiped || rec.multi) continue;
    const d = swipeDir(rec, tc);
    if (!d) continue;
    if (screen === "para") { if (d === "L" || d === "R") { rec.swiped = true; rec.side = d; steer(d); paraHold(); } continue; }
    if (screen !== "play" || rec.brace || !S || S.result) continue;
    if (controls === "two" && d !== "D") continue;
    rec.swiped = true; rec.brace = true; clearTimeout(rec.timer);
    if (rec.hold) { rec.hold = false; setHold(false); }
    if (!undoClimb(rec.snap)) continue;
    lastSwipe = { d, t: performance.now() };
    if (d === "D") climbDown();
    else if (d === "U") {
      reach(nextArm()); const run = S, version = S.motionVersion;
      setTimeout(() => { if (S === run && S.motionVersion === version && canPlay()) reach(nextArm()); }, T.CLIMB_MS + 15);
    }
    else { const cl = S.cl; cl.lastSide = null; if (!busy()) dyno(d); }
  }
}, { passive: false });
let lastSwipe = null;
document.addEventListener("gesturestart", (e) => e.preventDefault());
document.addEventListener("dblclick", (e) => e.preventDefault());
document.addEventListener("contextmenu", (e) => e.preventDefault());

// mouse (desktop): click halves like taps, ignored right after touches (emulated mouse events)
let mouseHoldTimer = 0;
document.addEventListener("mousedown", (e) => {
  if (performance.now() - lastTouchEnd < 800) return;
  Snd.unlock();
  if (onMute(e.clientX, e.clientY)) { Snd.toggle(); return; }
  if (advance(canvasPoint(e.clientX, e.clientY))) return;
  if (screen === "para") { const sd = sideOf(e.clientX); steer(sd); mouseSide = sd === "L" ? -1 : 1; paraHold(); return; }
  if (e.button === 2) { brace(); return; }
  reach(sideOf(e.clientX));
  mouseHoldTimer = setTimeout(() => setHold(true), T.LONG_MS);
});
document.addEventListener("mouseup", () => { clearTimeout(mouseHoldTimer); setHold(false); mouseSide = 0; paraHold(); });

const KEY_LEFT = ["ArrowLeft", "KeyA"], KEY_RIGHT = ["ArrowRight", "KeyD"];
document.addEventListener("keydown", (e) => {
  if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Space"].includes(e.code)) e.preventDefault();
  Snd.unlock();
  if (e.repeat) return;
  if (e.code === "KeyM") { Snd.toggle(); return; }
  if (!BC.ready) return;
  if (e.code === "KeyP" && (screen === "play" && !S.result || screen === "para")) { togglePause(); return; }
  if (paused) { if (e.code === "Escape") togglePause(); return; }
  if (screen === "results") { resultsKey(e.code); return; }
  if (screen === "play" && S.result) { lossKey(e.code); return; }
  if (DEBUG && e.code === "KeyC") { wallet += 100; saveShop(); return; }     // debug: +100 coins
  if (screen === "shop") { shopKey(e.code); return; }
  if (screen === "levels") { if (now >= inputLockUntil) levelsKey(e.code); return; }
  if (screen === "settings") { if (now >= inputLockUntil) settingsKey(e.code); return; }
  if (screen === "choose") { if (now >= inputLockUntil) chooseKey(e.code); return; }
  if (screen === "title" && e.code === "KeyL") { openLevels("title"); return; }
  if (screen === "title" && e.code === "KeyG") { openSettings("title"); return; }
  if (screen === "creator") {                 // keyboard creator: up/down pick a row, left/right change it
    if (e.code === "ArrowUp" || e.code === "KeyW") { Creator.sel = (Creator.sel + OPTS.length - 1) % OPTS.length; return; }
    if (e.code === "ArrowDown" || e.code === "KeyS") { Creator.sel = (Creator.sel + 1) % OPTS.length; return; }
    if (KEY_LEFT.includes(e.code)) { changeOpt(Creator.sel, -1); return; }
    if (KEY_RIGHT.includes(e.code)) { changeOpt(Creator.sel, 1); return; }
    if (e.code === "KeyR") { randomizeLook(); return; }
    if (e.code === "KeyT") { Creator.back = !Creator.back; return; }
    if (e.code !== "Enter" && e.code !== "Space") return;
  }
  if (screen === "title" && e.code === "KeyI") { startCine("title"); return; }
  if (screen === "para") {
    const sd = KEY_LEFT.includes(e.code) ? "L" : KEY_RIGHT.includes(e.code) ? "R" : null;
    if (sd) { steer(sd); keysDown.add(sd); paraHold(); }
    return;
  }
  if (screen !== "play" && e.code !== "Enter" && e.code !== "Space") return;
  if (advance(null)) return;
  if (KEY_LEFT.includes(e.code)) reach("L");
  else if (KEY_RIGHT.includes(e.code)) reach("R");
  else if (e.code === "ArrowDown" || e.code === "Space" || e.code === "KeyS") brace();
  else if (e.code === "KeyX" || e.code === "PageDown") climbDown();
  else if (e.code === "ArrowUp" || e.code === "KeyW") setHold(true);
});
document.addEventListener("keyup", (e) => {
  if (e.code === "ArrowUp" || e.code === "KeyW") setHold(false);
  if (KEY_LEFT.includes(e.code)) keysDown.delete("L");
  if (KEY_RIGHT.includes(e.code)) keysDown.delete("R");
  paraHold();
});
let paused = false;
const PAUSE_BTN = () => ({ x: 92, y: H - 20, w: 40, h: 18 });
function pauseLayout() { return { resume: { x: 62, y: Math.round(H / 2) + 8, w: 100, h: 26 } }; }
function togglePause() {
  paused = !paused;
  if (paused) {
    if (S) S.motionVersion++;
    setHold(false); keysDown.clear(); mouseSide = 0; clearTimeout(mouseHoldTimer);
    for (const r of touches.values()) clearTimeout(r.timer);
    touches.clear(); paraHold(); Poki.screen("paused");
  } else Poki.screen(screen);
}
function drawPaused() {
  ctx.fillStyle = "rgba(8,6,24,0.82)"; ctx.fillRect(0, 0, W, H);
  textC("PAUSED", Math.round(H / 2) - 24, C.hardhat, 2);
  drawButton(pauseLayout().resume, "RESUME", true);
  textC("P / ESC TO RESUME", Math.round(H / 2) + 44, C.white);
}
document.addEventListener("visibilitychange", () => { if (document.hidden && Snd.ctx) Snd.ctx.suspend(); else if (Snd.ctx) Snd.ctx.resume(); lastFrame = 0; });

// ---------------------------------------------------------------- test / debug hooks (used by tests/game-harness.cjs)
window.BC = {
  get S() { return S; }, get screen() { return screen; }, get paused() { return paused; }, get loading() { return loadingUntil > now; }, get loadError() { return loadError; }, Results, Loss, lossLayout, pauseLayout, PAUSE_BTN, T, get GOAL_Z() { return GOAL_Z; }, get MOUTH_Z() { return MOUTH_Z; }, get START_Z() { return START_Z; },
  get ROWS() { return ROWS; }, get LEVEL() { return LEVEL; }, loadLevel, isUnlocked, levelsLayout, openLevels, get Levels() { return Levels; },
  TITLE_LEVELS_BTN, TITLE_GEAR_BTN, settingsLayout, openSettings, get Settings() { return Settings; }, climbDown, tutText,
  get Snd() { return Snd; }, STORIES, CHAIN, nextLevel, owns(id) { return isOwned(CAT_BY_ID[id]); }, get story() { return STORY(); }, CATALOG, chooseLayout, needsChoose, get controls() { return controls; }, setControls, get lastSwipe() { return lastSwipe; }, TUT_STEPS, get tutStep() { return tutStep(); }, get H() { return H; }, get scale() { return scale; }, get poki() { return Poki.on; },
  tileAt,
  start() { newGame(); setScreen("play"); },
  get look() { return look; }, setLook(l) { look = sanitizeLook(l); saveLook(); },
  get Para() { return Para; }, get Ending() { return Ending; }, get Intro() { return Intro; }, get Cine() { return Cine; },
  get face() { return face; }, get cineSeen() { return cineSeen; }, cineLength,
  get wallet() { return wallet; }, addCoins(n) { wallet += n; saveShop(); }, get owned() { return [...owned]; },
  get cheered() { return [...cheered]; }, get boosts() { return Object.assign({}, boosts); }, get boostEq() { return boostEq.slice(); },
  get Shop() { return Shop; }, CATALOG, shopLayout, openShop, TITLE_SHOP_BTN, optValues,
  hazardPace, get EXTRA_ROWS() { return EXTRA_ROWS; }, get shelterNow() { return !!shelterNow(); }, placeShelters, setBoosts(inv, eq) { boosts = Object.assign(boosts, inv); boostEq = eq.slice(); saveShop(); },
  get cssScale() { return cv.getBoundingClientRect().width / W; },
  startCine, startIntro, startPara, startBird, showResults, steer,
  creatorLayout, resultsLayout, TITLE_INTRO_BTN, OPTS,
  win() { this.calm(); this.set({ z: GOAL_Z - 0.01 }); finishTween(); endGame(true); },
  reach, brace, setHold, dyno,
  spawn(kind, col, z) { spawnHazard(col, z === undefined ? MOUTH_Z : z, kind === "hat" ? "hat" : kind); },
  set(o) { Object.assign(S.cl, { mode: "climb", tw: null }, o); S.camZ = camTarget(); },
  sneezeNow() { S.sneeze.next = S.t; },
  calm() { S.nextThrow = 1e9; S.haz.length = 0; S.sneeze.next = 1e9; S.sneeze.phase = "none"; }, darkness, nextText, spawnHazard, setEasy, get easy() { return easy; }, get swoop() { return S.swoop; },
  frame() { return cv.toDataURL("image/png"); },
  record(ms) { this.rec = []; this.recId = setInterval(() => this.rec.push(cv.toDataURL("image/png")), ms); },
  stopRecord() { clearInterval(this.recId); return this.rec; },
  noThrows(on) { S.nextThrow = on ? 1e9 : S.t; },
  get sprite() { return S ? climberSprite() : null; },
  ready: false, ensureWorld, goLevel, get LV() { return LV; }, get frames() { return A.frames; }, get packs() { return Object.fromEntries(Object.entries(Packs).map(([w, p]) => [w, p.state])); },
};

// ---------------------------------------------------------------- start: World 1-1 Grandpa unless another unlocked
// level was picked last time (?level=wizard forces one, for tests)
{
  const want = params.get("level") || localStorage.getItem("bc_level") || "grandpa";
  const ok = known(want) && (params.get("level") || isUnlocked(want));
  if (ok && !LV[want]) {                      // a later world: start on Grandpa's data, swap in once its pack is here
    loadLevel("grandpa"); BC.ready = false; loadingUntil = now + 1e9;
    const request = ++levelRequest;
    ensureWorld(want, (good) => {
      if (request !== levelRequest) return;
      if (good) loadLevel(want);
      else loadError = { t: now, lines: ["COULD NOT LOAD SAVED WORLD", "PLEASE TRY LEVELS AGAIN"] };
      BC.ready = true; loadingUntil = 0;
    });
  } else { loadLevel(ok ? want : "grandpa"); BC.ready = true; }
  setTimeout(prefetchWorlds, 1500);           // warm up unlocked later worlds in the background
}
resize();
requestAnimationFrame(frame);
})();
